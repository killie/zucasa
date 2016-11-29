from flask import Flask, render_template, request, jsonify
from multiprocessing import Process, Pipe
import sys
from os import path, getcwd
import calendar
import shelve

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from core import Photo, import_photos, group_photos, delete_files
from config import Config


# Globals

app = Flask(__name__)
rc_file = getcwd() + "/zucasa.rc"
db_file = getcwd() + "/server/zucasa.db"

# Photos in user map sorted by created date (latest first)
photo_list = {}

# Photos in user map grouped by year, month and day
photo_map = {}

# TODO: Use config value instead
# TODO: Saving config with new "limit" and no other changes should not do full import
limit = 500 

# Routes

@app.route("/")
def main():
    return _show_filtered_photos(request.args)

@app.route("/<user>")
def user(user):
    return _show_filtered_photos({"user": user})

def _show_filtered_photos(args):
    items = _filter_photos(args)
    photos = _group_photos(items)
    return render_template("index.html", photos=photos["items"])

def _filter_photos(args):
    """Filter photo_list by arguments. Return sorted list by descending date in a map with key 'items'."""
    global photo_list, photo_map
    if not photo_map:
        photo_list = _load_photos()
        photo_map = _group_photos(photo_list)

    if "date" in args:
        print "Convert " + str(args["date"]) + " to datetime and use it on photos"
    else:
        print "Use latest date in photo_list and show X photos"

    photos = []
    for user in photo_list:
        for photo in photo_list[user]:
            if "user" in args and photo.user == args["user"]:
                # TODO: Make sure all args match, not just one
                print "Adding " + str(photo.created)
                photos.append(photo)
    return {"items": photos}

@app.route("/<user>/<year>/<month>/<day>/<uuid>")
def view(user, year, month, day, uuid):
    global photo_list, photo_map
    if not photo_map:
        photo_list = _load_photos()
        photo_map = _group_photos(photo_list)

    # Find photo in photos map and copy to cache
    photo = None
    for p in photo_map[user][year][month][day]:
        if p.uuid == uuid:
            photo = p

    if not photo:
        return "This is not a photograph"

    photo.load_photo()

    # Find photo in photo list to add surrounding thumbnails
    thumbnails = []
    for i, p in enumerate(photo_list[user]):
        if (p == photo):
            if (i + 3 < len(photo_list[user])):
                thumbnails.append(photo_list[user][i + 3].thumbnail)
            if (i + 2 < len(photo_list[user])):
                thumbnails.append(photo_list[user][i + 2].thumbnail)
            if (i + 1 < len(photo_list[user])):
                thumbnails.append(photo_list[user][i + 1].thumbnail)
            thumbnails.append(p.thumbnail)
            if (i > 1):
                thumbnails.append(photo_list[user][i - 1].thumbnail)
            if (i > 2):
                thumbnails.append(photo_list[user][i - 2].thumbnail)
            if (i > 3):
                thumbnails.append(photo_list[user][i - 3].thumbnail)

    return render_template("view.html", photo=photo.cache, thumbnails=thumbnails)

@app.route("/config", methods=["GET"])
def get_config():
    config = Config()
    config.load(rc_file)
    return render_template("config.html", config=config)

@app.route("/config", methods=["POST"])
def post_config():
    config = Config()
    config.save(request.form, rc_file)

    # Clear database when doing import
    _flush_database(True, "Initializing...")

    # Import produces photos and messages sent through pipe to database writer
    p1, p2 = Pipe()
    consumer = Process(target=_db_writer, args=(p2,))
    consumer.start()
    producer = Process(target=_import_all, args=(config, p1))
    producer.start()

    # Show progress page while import runs
    return render_template("progress.html")

def _flush_database(running, status):
    db = shelve.open(db_file)
    db.clear()
    db["running"] = running
    db["status"] = status # TODO: Use string array instead to keep all log messagesp
    db["photos"] = {}
    db.close()
    db.sync()

def _import_all(config, pipe):
    delete_files()
    import_photos(config, pipe)

def _db_writer(pipe):
    photos = {}
    count = 0
    while True:
        message = pipe.recv()
        if "status" in message:
            _write_to_db({"status": message["status"]})
            if (message["status"] == "Done"):
                _write_to_db({"photos": photos})
                _sync_db()
                break
        elif "skipped" in message:
            print "Skipping " + message["skipped"].path
        elif "imported" in message:
            photo = message["imported"]
            if not photo.user in photos:
                photos[photo.user] = []
            photos[photo.user].append(photo)
            count += 1
            if count == 50:
                _write_to_db({"photos": photos})
                photos = {}
                count = 0

def _write_to_db(data):
    db = shelve.open(db_file)
    if "status" in data:
        print data["status"]
        db["status"] = data["status"]
    elif "photos" in data:
        print "Adding photos"
        new = data["photos"]
        cur = db["photos"]
        for user in new:
            if not user in cur:
                cur[user] = []
            for photo in new[user]:
                cur[user].append(photo)
        db["photos"] = cur
    db.close()
        
def _sync_db():
    db = shelve.open(db_file)
    db["running"] = False
    db.sync()
    db.close()
    
@app.route("/_get_progress")
def get_progress():
    db = shelve.open(db_file)
    status = db["status"]
    db.close()
    return jsonify({"status": status})

def _load_photos():
    """Load database with existing photos (thumbnails are on disk)."""
    photos = {}
    db = shelve.open(db_file)
    if "photos" in db:
        photos = db["photos"]
    db.close()
    return photos

def _group_photos(photos):
    return group_photos(photos)


# Template helpers

def get_picture_date(year, month, day):
    return str(int(day)) + ". " + calendar.month_name[int(month)] + " " + year

def get_month_name(month):
    return calendar.month_name[int(month)]

def sort_asc(items):
    return sorted(items)

def sort_desc(items):
    return sorted(items, reverse=True) 

def relative_path(path):
    length = len(getcwd() + "/server/")
    return path[length:]


# Startup

if __name__ == "__main__":
    # Register template helpers
    app.jinja_env.globals.update(picture_date=get_picture_date)
    app.jinja_env.globals.update(month_name=get_month_name)
    app.jinja_env.globals.update(sort_asc=sort_asc)
    app.jinja_env.globals.update(sort_desc=sort_desc)
    app.jinja_env.globals.update(relative_path=relative_path)

    # Load photos from database, thumbnails are on disk
    photo_list = _load_photos()
    for user in photo_list:
        print user + " has " + str(len(photo_list[user])) + " photos"

    photo_map = _group_photos(photo_list)
    if photo_map:
        print "Photos have been loaded and grouped"

    # Start web server on local IP with default port number
    app.run(sys.argv[1])

