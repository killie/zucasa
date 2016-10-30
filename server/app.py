from flask import Flask, render_template
import sys
from os import path, getcwd
import calendar

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from core import get_file_list, Photo

# Globals

app = Flask(__name__)
root = getcwd() + "/server/static/import"
files = get_file_list(root)

# Routes

@app.route("/")
def main():
    return render_template("index.html", years=files["public"])

@app.route("/<user>")
def user(user):
    return render_template("index.html", years=files[user], user=user)

@app.route("/<user>/<year>/<month>/<day>/<num>")
def view(user, year, month, day, num):
    photo = Photo(user, year, month, day, num)
    photo.load_photo()
    thumbnails = [ \
        "/static/import/jonole/2006/01/21/1.jpg", \
        "/static/import/jonole/2006/01/21/2.jpg", \
        "/static/import/jonole/2006/01/21/3.jpg", \
        "/static/import/jonole/2006/01/21/4.jpg"]
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
