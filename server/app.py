from flask import Flask, render_template
import sys
from os import path, getcwd
import calendar

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from core import get_files_as_map, sort_photos_into_array, Photo

# Globals

app = Flask(__name__)
root = getcwd() + "/server/static/import"
files = get_files_as_map(root)
photos = sort_photos_into_array(files)

# Routes

@app.route("/")
def main():
    return render_template("index.html", years=files["public"])

@app.route("/<user>")
def user(user):
    return render_template("index.html", years=files[user], user=user)

@app.route("/<user>/<year>/<month>/<day>/<num>")
def view(user, year, month, day, num):
    # Create instance of Photo class and load original from disk into cache
    photo = Photo(user, year, month, day, num)
    photo.load_photo()

    # Identify photo in sorted array and add surrounding photos to thumbnails array
    thumbnails = []
    i = 0
    for p in photos[user]:
        if (p.date_taken == photo.date_taken):
            if (p.num == int(num)):
                if (i > 2):
                    thumbnails.append(photos[user][i - 2].get_thumbnail_src())
                if (i > 1):
                    thumbnails.append(photos[user][i - 1].get_thumbnail_src())
                thumbnails.append(photos[user][i].get_thumbnail_src())
                if (i + 1 < len(photos[user])):
                    thumbnails.append(photos[user][i + 1].get_thumbnail_src())
                if (i + 2 < len(photos[user])):
                    thumbnails.append(photos[user][i + 2].get_thumbnail_src())
        i += 1

    return render_template("view.html", photo=photo.original_src, thumbnails=thumbnails)

# Template helpers

def get_picture_date(year, month, day):
    return str(int(day)) + ". " + calendar.month_name[int(month)] + " " + year

def get_month_name(month):
    return calendar.month_name[int(month)]

# Startup

def get_ip(file):
    f = open(file)
    return f.readline()

if __name__ == "__main__":
    # Register template helpers
    app.jinja_env.globals.update(picture_date=get_picture_date)
    app.jinja_env.globals.update(month_name=get_month_name)

    # Start web server on local IP with default port number
    app.run(get_ip("local_ip.txt").rstrip())
