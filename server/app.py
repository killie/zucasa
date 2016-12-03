from flask import Flask, render_template, request, jsonify
from multiprocessing import Process, Pipe
import sys
from os import path, getcwd
import calendar
from datetime import datetime
import shelve
from time import sleep

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from core import Photo, import_photos, group_photos, delete_files
from config import Config


# Globals

app = Flask(__name__)
rc_file = getcwd() + "/zucasa.rc"
db_file = getcwd() + "/server/zucasa.db"

# Photos in array sorted by created date (latest first)
photo_list = []

# Photos in map grouped by year, month and day
photo_map = {}

users = []
cameras = []
tags = []

# TODO: Use config value instead
# TODO: Saving config with new "limit" and no other changes should not do full import
limit = 300

# Routes

@app.route("/")
def main():
    return _show_filtered_photos(request.args)

@app.route("/<user>")
def user(user):
    return _show_filtered_photos({"users": user})

def _show_filtered_photos(args):
    valid_args = _convert_args(args)
    photos = _filter_photos(valid_args)
    dated = _group_photos(photos)
    result = _filter_on_date(dated, valid_args["date"], limit)

    user_map = {}
    for user in users:
        if not user in user_map:
            user_map[user] = False
        if user in valid_args["users"]:
            user_map[user] = True

    camera_map = {}
    for camera in cameras:
        if not camera in camera_map:
            camera_map[camera] = False
        if camera in valid_args["cameras"]:
            camera_map[camera] = True

    tag_map = {}
    for tag in tags:
        if not tag in tag_map:
            tag_map[tag] = False
        if tag in valid_args["tags"]:
            tag_map[tag] = True

    return render_template("index.html", dated=dated, users=user_map, cameras=camera_map, tags=tag_map, limited=result["limited"], has_newer=result["has_newer"], has_older=result["has_older"])

def _convert_args(args):
    valid = {"users": [], "cameras": [], "tags": [], "date": None}
    if "users" in args:
        valid["users"] = args["users"].split(",")
    if "cameras" in args:
        valid["cameras"] = args["cameras"].split(",")
    if "tags" in args:
        valid["tags"] = args["tags"].split(",")
    if "date" in args:
        s = args["date"]
        valid["date"] = datetime(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return valid

def _filter_photos(args):
    """Filter photo_list by arguments. Return sorted list by descending date in a map with key 'items'."""
    global photo_list, photo_map, users, cameras, tags
    if not photo_map:
        photo_list = _load_photos()
        photo_map = _group_photos(photo_list)
        users = _load_users(photo_list)
        cameras = _load_cameras(photo_list)
        tags = _load_tags(photo_list)

    photos = []
    for photo in photo_list:
        if not args["users"] or photo.user in args["users"]:
            if not args["cameras"] or photo.camera in args["cameras"]:
                photos.append(photo)

    return photos

def _filter_on_date(dated, from_date, max_limit):
    filtered = {}
    counter = 0
    to_date = None
    has_newer = False
    has_older = False

    for year in sort_desc(dated):
        for month in sort_desc(dated[year]):
            for day in sort_desc(dated[year][month]):
                for photo in dated[year][month][day]:
                    if to_date == None and counter >= max_limit:
                        to_date = photo.created

                    if not to_date == None and photo.created.date() < to_date.date():
                        has_older = True
                        return {"limited": filtered, "has_newer": has_newer, "has_older": has_older}

                    if not from_date == None and photo.created.date() > from_date.date():
                        has_newer = True

                    if from_date == None or photo.created.date() <= from_date.date():
                        if not year in filtered:
                            filtered[year] = {}
                        if not month in filtered[year]:
                            filtered[year][month] = {}
                        if not day in filtered[year][month]:
                            filtered[year][month][day] = []
                        filtered[year][month][day].append(photo)
                        counter += 1

    return {"limited": filtered, "has_newer": has_newer, "has_older": has_older}

def _load_users(photos):
    users = []
    for photo in photos:
        if not photo.user in users:
            users.append(photo.user)
    return users

def _load_cameras(photos):
    cameras = []
    for photo in photos:
        if photo.camera and not photo.camera in cameras:
            cameras.append(photo.camera)
    return cameras

def _load_tags(photos):
    return ["starred"]

@app.route("/<user>/<year>/<month>/<day>/<uuid>")
def view(user, year, month, day, uuid):
    global photo_list, photo_map, users, cameras, tags
    if not photo_map:
        photo_list = _load_photos()
        photo_map = _group_photos(photo_list)
        users = _load_users(photo_list)
        cameras = _load_cameras(photo_list)
        tags = _load_tags(photo_list)

    # Find photo in photos map and copy to cache
    photo = None
    for p in photo_map[year][month][day]:
        if p.uuid == uuid:
            photo = p

    if not photo:
        return "This is not a photograph"

    photo.load_photo()

    # Find photo in photo list to add surrounding thumbnails
    # TODO: Thumbnails must be selected from filtered photos

    thumbnails = []
    for i, p in enumerate(photo_list):
        if (p == photo):
            if (i + 3 < len(photo_list)):
                thumbnails.append(photo_list[i + 3].thumbnail)
            if (i + 2 < len(photo_list)):
                thumbnails.append(photo_list[i + 2].thumbnail)
            if (i + 1 < len(photo_list)):
                thumbnails.append(photo_list[i + 1].thumbnail)
            thumbnails.append(p.thumbnail)
            if (i > 1):
                thumbnails.append(photo_list[i - 1].thumbnail)
            if (i > 2):
                thumbnails.append(photo_list[i - 2].thumbnail)
            if (i > 3):
                thumbnails.append(photo_list[i - 3].thumbnail)

    return render_template("view.html", photo=photo.cache, thumbnails=thumbnails)

@app.route("/config", methods=["GET"])
def get_config():
    return _show_config()

def _show_config():
    config = Config()
    config.load(rc_file)
    return render_template("config.html", config=config)

@app.route("/config", methods=["POST"])
def post_config():
    config = Config()
    config.save(request.form, rc_file)

    # Clear database when doing import
    _flush_database(True, "Initializing...")
    sleep(2) # TODO: Add exception handling for deadlock instead

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
    db["status"] = status # TODO: Use string array instead to keep all log messages
    db["photos"] = []
    db.close()
    db.sync()

def _import_all(config, pipe):
    delete_files()
    import_photos(config, pipe)

def _db_writer(pipe):
    photos = []
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
            # TODO: Need Log class to save skipped and non photos to log-file
            print "Skipping " + message["skipped"].path
        elif "imported" in message:
            photo = message["imported"]
            photos.append(photo)
            count += 1
            if count == 50:
                _write_to_db({"photos": photos})
                photos = []
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
        for photo in new:
            cur.append(photo)
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
    photos = []
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
    photo_map = _group_photos(photo_list)
    users = _load_users(photo_list)
    cameras = _load_cameras(photo_list)
    tags = _load_tags(photo_list)
    if photo_map:
        print str(len(photo_list)) + " photos have been loaded and grouped by date"

    # Start web server on local IP with default port number
    app.run(sys.argv[1])

