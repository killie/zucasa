from flask import Flask, render_template, request
import sys
from os import path, getcwd
import calendar

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from core import Photo, import_photos, files_to_photos
from config import Config
from csv import save_files, load_files


# Globals

rc_file = getcwd() + "/zucasa.rc"
app = Flask(__name__)
root = getcwd() + "/server/static/import"
progress = "Idle"

# Map file name -> photo
files = load_files()

# Map of photos grouped by user, year, month, day
photos = files_to_photos(files)


# Routes

@app.route("/")
def main():
    if (files):
        return render_template("index.html", years=photos["public"])
    else:
        config = Config()
        config.load(rc_file)
        return render_template("config.html", config=config)

@app.route("/<user>")
def user(user):
    if (user in photos):
        return render_template("index.html", years=photos[user], user=user)
    else:
        return "Unknown user '" + user + "'. Try with '/'."

@app.route("/<user>/<year>/<month>/<day>/<num>")
def view(user, year, month, day, num):
    # Find photo in photos map and copy to cache
    for p in photos[user][year][month][day]:
        if p.num == num:
            photo = p

    photo.load_photo()

    # Find photo in files map to add surrounding thumbnails
    # TODO: Fix bug where day is sorted descending when it should be ascending
    thumbnails = []
    for i, p in enumerate(files[user]):
        if (p == photo):
            if (i + 3 < len(files[user])):
                thumbnails.append(files[user][i + 3].thumbnail)
            if (i + 2 < len(files[user])):
                thumbnails.append(files[user][i + 2].thumbnail)
            if (i + 1 < len(files[user])):
                thumbnails.append(files[user][i + 1].thumbnail)
            thumbnails.append(p.thumbnail)
            if (i > 1):
                thumbnails.append(files[user][i - 1].thumbnail)
            if (i > 2):
                thumbnails.append(files[user][i - 2].thumbnail)
            if (i > 3):
                thumbnails.append(files[user][i - 3].thumbnail)

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
    import_photos(config, files, photos, progress)
    save_files(files)
    return render_template("progress.html", progress=progress)

@app.route("/progress")
def progress():
    return render_template("progress.html", progress=progress)


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

    # Start web server on local IP with default port number
    app.run(sys.argv[1])

