from flask import Flask, render_template, request, jsonify, redirect
from urllib import unquote
from multiprocessing import Process, Pipe
import sys
from os import path, getcwd
import calendar
from datetime import datetime
import shelve
from time import sleep

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from photo import Photo
from core import import_photos, group_photos, delete_files
from config import Config


# Globals

app = Flask(__name__)
rc_file = getcwd() + "/zucasa.rc"
db_file = getcwd() + "/server/zucasa.db"

# Photos in array sorted by created date (latest first)
photo_list = []

# Photos in map grouped by year, month and day
photo_map = {}

# List of user names
users = []

# List of camera models
cameras = []

# List of dictionaries where key is tag name and value is a list of photos
tags = []

# How many photos to show on a page
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
                if not args["tags"]:
                    photos.append(photo)
                else:
                    if len(args["tags"]) == 1 and args["tags"][0] == "starred":
                        if photo.starred:
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
    tags = ["starred"]
    for photo in photos:
        for tag in photo.tags:
            if not tag in tags:
                tags.append(tag)
    return tags

@app.route("/<user>/<year>/<month>/<day>/<uuid>")
def view(user, year, month, day, uuid):
    valid_args = _convert_args(request.args)
    photos = _filter_photos(valid_args)

    photo = _find_photo_by_uuid(photos, uuid)
    if not photo:
        return "This is not a photograph"

    photo.load_preview()

    # Find photo in photo list to add surrounding thumbnails
    items = _get_photos(photos, photo, -3) + [photo] + _get_photos(photos, photo, 3)
    thumbnails = map(lambda p: [p.uuid, p.thumbnail], items)

    return render_template("view.html", photo=photo, thumbnails=thumbnails)

def _find_photo_by_uuid(photos, uuid):
    for photo in photos:
        if photo.uuid == uuid:
            return photo
    return None

def _get_photos(photos, photo, count):
    asc = sorted(photos, key=lambda p: p.created)

    r = []
    if count > 0:
        r = range(1, count + 1)
    else:
        r = range(count, 0)

    items = []
    for i, p in enumerate(asc):
        if p == photo:
            for j in r:
                if j + i > -1 and j + i < len(asc):
                    items.append(asc[j + i])

    return items

@app.route("/_show_photo")
def show_photo():
    uuid = request.args["uuid"]
    photo = None
    if "source" in request.args:
        if request.args["source"] == "removed":
            db = shelve.open(db_file)
            if "removed" in db:
                removed = db["removed"]
            else:
                removed = []

            for r in removed:
                if r["photo"].uuid == uuid:
                    photo = r["photo"]
                    break

            db.close()
        else:
            return jsonify({"success": False})
    else:
        photo = _find_photo_by_uuid(photo_list, uuid)

    photo.load_photo()
    return jsonify({"src": relative_path(photo.cache)})

@app.route("/settings", methods=["GET"])
def get_settings():
    return _show_settings()

def _show_settings():
    config = Config()
    config.load(rc_file)
    return render_template("settings.html", config=config)

@app.route("/import", methods=["POST"])
def post_import():
    global photo_list, photo_map, users, cameras, tags, limit
    photo_list = []
    photo_map = {}
    users = []
    cameras = []
    tags = []

    config = Config()
    config.limit = limit
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

    return redirect("")

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

@app.route("/prefs", methods=["POST"])
def post_prefs():
    global limit
    limit = request.form["limit"]
    config = Config()
    config.load(rc_file)
    config.limit = limit
    config.save(None, rc_file)
    return redirect("")
    
@app.route("/_get_progress")
def get_progress():
    db = shelve.open(db_file)
    status = db["status"]
    db.close()
    return jsonify({"status": status})

@app.route("/_scroll_thumbnails")
def scroll_thumbnails():
    """Function takes current URL filter (users, cameras, etc.)
    and selected photo and returns +/- thumbnails."""
    args = _filter_to_args(request.args["filter"])
    valid_args = _convert_args(args)
    photos = _filter_photos(valid_args)
    uuid = request.args["uuid"]
    count = int(request.args["count"])

    photo = _find_photo_by_uuid(photos, uuid)
    if not photo:
        return "This is not a photograph"

    if count > 0:
        items = [photo] + _get_photos(photos, photo, count * 2)
    else:
        items = _get_photos(photos, photo, count * 2) + [photo]

    thumbnails = map(lambda p: p.thumbnail, items)
    return jsonify(map(relative_path, thumbnails))

def _filter_to_args(filter):
    """Converts URL arguments on the form ?a=b&c=d into {"a": "b", "c": "d"}."""
    args = {}
    pairs = filter[1:].split("&")
    for pair in pairs:
        values = pair.split("=")
        if len(values) == 2:
            args[values[0]] = unquote(values[1])
    return args

@app.route("/_get_metainfo")
def get_metainfo():
    uuid = request.args["uuid"]
    photo = _find_photo_by_uuid(photo_list, uuid)
    metainfo = photo.load_metainfo()
    return render_template("metainfo.html", metainfo=_sort_metainfo(metainfo))

def _sort_metainfo(metainfo):
    """Take metainfo map and put it into array with key, value, class."""
    less = ["Image Size", "File Size", "File Type", "Directory", "File Name", "Create Date", "Camera Model Name", "Camera ISO"]
    array = []
    for key in metainfo:
        array.append({"key": key, "value": metainfo[key], "class": "less" if key in less else "more" })

    return sorted(array, key=lambda d: d["key"])

@app.route("/_show_more")
def show_more():
    """Takes first/last date and goes back/forward x number of photos to find new date.
    This is returned to client who in turn requests to show photos from this date."""
    uuid = request.args["uuid"]
    direction = request.args["direction"]
    args = _filter_to_args(request.args["filter"])
    valid_args = _convert_args(args)
    photos = _filter_photos(valid_args)

    # Get +/- a number of filtered photos
    for index, photo in enumerate(photos):
        if photo.uuid == uuid:
            if direction == "older":
                # Show photos from this date (and backwards)
                return jsonify({"date": photo.year + photo.month + photo.day})

            # More difficult to ensure selected date is included when loading newer photos
            i = max(0, index - limit)
            break

    # Next index to show photos are now at index 'i'. Return its date.
    return jsonify({"date": photos[i].year + photos[i].month + photos[i].day})

@app.route("/_save_description")
def save_description():
    uuid = request.args["uuid"]
    description = request.args["description"]
    photo = _find_photo_by_uuid(photo_list, uuid)
    photo.description = description
    _save_photos(photo_list)
    return jsonify({"description": description})

def _save_photos(photos):
    """Save database with existing photos."""
    # TODO: Save on shutdown instead of on each modification?
    db = shelve.open(db_file)
    db["photos"] = photos
    db.sync()
    db.close()

@app.route("/_toggle_star")
def toggle_star():
    uuid = request.args["uuid"]
    photo = _find_photo_by_uuid(photo_list, uuid)
    photo.starred = not photo.starred
    _save_photos(photo_list)
    return jsonify({"starred": photo.starred})

@app.route("/_remove_photo")
def remove_photo():
    global photo_list
    uuid = request.args["uuid"]
    photo = _find_photo_by_uuid(photo_list, uuid)
    photos = filter(lambda p: p.uuid != uuid, photo_list)
    # Put path on removed list
    db = shelve.open(db_file)
    if "removed" in db:
        removed = db["removed"]
    else:
        removed = []
    removed.append({"removed": datetime.now(), "photo": photo})
    db["removed"] = removed
    # Remove photo from database. Original is not touched.
    db["photos"] = photos
    db.sync()
    db.close()
    photo_list = photos
    return jsonify({"success": True})

@app.route("/_get_removed")
def removed():
    db = shelve.open(db_file)
    if "removed" in db:
        removed = db["removed"]
    else:
        removed = []
    db.close()
    return render_template("removed.html", removed=sorted(removed, key=lambda p: p["removed"], reverse=True))

@app.route("/_recover_photo")
def recover_photo():
    global photo_list
    uuid = request.args["uuid"]
    # Find photo in list of removed photos
    db = shelve.open(db_file)
    if "removed" in db:
        removed = db["removed"]
    else:
        db.close()
        return jsonify({"success": False, "message": "Could not find photo in list of removed photos"})

    # Add photo to photo list
    found = False
    for r in removed:
        photo = r["photo"]
        if photo.uuid == uuid:
            photo_list.append(photo)
            photo_list = sorted(photo_list, key=lambda p: p.created, reverse=True)
            found = True

    if not found:
        db.close()
        return jsonify({"success": False, "message": "Could not find photo in list of removed photos"})

    # Remove photo from list of removed photos and sync db
    db["removed"] = filter(lambda r: r["photo"].uuid != uuid, removed)
    db["photos"] = photo_list
    db.sync()
    db.close()
    return jsonify({"success": True})

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

def _remove_duplicates(photos):
    duplicates = _find_duplicates(photos)
    db = shelve.open(db_file)
    if "removed" in db:
        removed = db["removed"]
    else:
        removed = []
    for uuid in duplicates:
        photo = _find_photo_by_uuid(photos, uuid)
        removed.append({"removed": datetime.now(), "photo": photo})
    db["removed"] = removed
    stripped = filter(lambda p: p.uuid not in duplicates, photos)
    db["photos"] = stripped
    db.sync()
    db.close()
    return stripped

def _find_duplicates(photos):
    """For each photo see if next photo matches current. If it does then add following photo to duplicates list."""
    duplicates = [] # List of ids
    size = len(photos)
    for i, p in enumerate(photos):
        if not p.duplicate and i + 1 < size:
            c = i
            while _is_duplicate(p, photos[c + 1]):
                photos[c + 1].duplicate = True
                duplicates.append(photos[c + 1].uuid)
                c += 1
    return duplicates

def _is_duplicate(a, b):
    """Compare photo b with a. Return True if b is duplicate of a. Otherwise False."""
    if ((a.path == b.path) or (a.created == b.created and a.camera == b.camera)) and a.user == b.user:
        return True
    else:
        return False


# Template helpers

def get_picture_date(year, month, day):
    return str(int(day)) + ". " + calendar.month_name[int(month)] + " " + year

def get_month_name(month):
    return calendar.month_name[int(month)]

def sort_asc(items):
    return sorted(items)

def sort_desc(items):
    return sorted(items, reverse=True) 

def nice_date(date):
    return str(date.day) + "-" + calendar.month_name[date.month][:3] + "-" + str(date.year)

def nice_time(date):
    return nice_date(date) + date.strftime(" %H:%M")

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
    app.jinja_env.globals.update(nice_date=nice_date)
    app.jinja_env.globals.update(nice_time=nice_time)
    app.jinja_env.globals.update(relative_path=relative_path)

    # Load photos from database, thumbnails are on disk
    photo_list = _remove_duplicates(_load_photos())
    photo_map = _group_photos(photo_list)
    users = _load_users(photo_list)
    cameras = _load_cameras(photo_list)
    tags = _load_tags(photo_list)
    if photo_map:
        print str(len(photo_list)) + " photos have been loaded and grouped by date"

    # Start web server on local IP with default port number
    app.run(sys.argv[1])

