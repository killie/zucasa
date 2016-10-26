from flask import Flask, render_template
import os
import calendar

def get_file_list(root):
    """Load all known files into array reverse sorted on date.
    First level is user, second is year, month, day, photo."""

    users = {"public": {}}
    for user in os.walk(root).next()[1]:
        users[user] = {}

    for user in users.keys():
        if (os.path.isdir(root + "/" + user)):
            for year in os.walk(root + "/" + user).next()[1]:
                users[user][year] = {}
                for month in os.walk(root + "/" + user + "/" + year).next()[1]:
                    users[user][year][month] = {}
                    for day in os.walk(root + "/" + user + "/" + year + "/" + month).next()[1]:
                        users[user][year][month][day] = []
                        for path, dirs, files in os.walk(root + "/" + user + "/" + year + "/" + month + "/" + day):
                            for filename in files:
                                if (filename.endswith(".txt") == False):
                                    users[user][year][month][day].append(filename)

    return users

app = Flask(__name__)
root = os.getcwd() + "/server/static/import"
files = get_file_list(root)

@app.route("/")
def main():
    return render_template("index.html", years=files["public"])

@app.route("/<user>")
def user(user):
    return render_template("index.html", years=files[user], user=user)

def get_ip(file):
    f = open(file)
    return f.readline()

def get_picture_date(year, month, day):
    return str(int(day)) + ". " + calendar.month_name[int(month)] + " " + year

def get_month_name(month):
    return calendar.month_name[int(month)]

if __name__ == "__main__":
    print files
    app.jinja_env.globals.update(picture_date=get_picture_date)
    app.jinja_env.globals.update(month_name=get_month_name)
    app.run(get_ip("local_ip.txt").rstrip())
