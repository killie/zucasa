import os
import sys
import codecs
import datetime
import operator

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Photo

def _get_filename(user):
    """List of photos are stored in /static/import/photos/<user>/photo_list.csv"""
    filename = os.getcwd() + "/server/static/import/photos/" + user + "/photo_list.csv"
    return filename

def save_csv(photo_list):
    """Save photo_list map to CSV file."""
    for user in photo_list:
        csv = []
        for photo in photo_list[user]:
            fields = [
                photo.user,
                photo.created.strftime("%s"),
                photo.num,
                str(photo.rotation),
                photo.path]

            csv.append(",".join(fields))
        
        filename = _get_filename(user)
        if os.path.isfile(filename):
            os.remove(filename)
        f = codecs.open(filename, "w", "utf-8")
        for line in csv:
            f.write(line + os.linesep)

        f.close()

def load_csv():
    """Load all import/photos/<user>/photo_list.csv files into user map."""
    photo_list = {}
    directory = os.getcwd() + "/server/static/import/photos"
    if os.path.exists(directory):
        users = next(os.walk(directory))[1]
        for user in users:
            photo_list[user] = []
            filename = _get_filename(user)
            if os.path.isfile(filename):
                f = codecs.open(filename, "r", "utf-8")
                for line in f.read().split(os.linesep):
                    if line:
                        values = line.split(",")
                        photo = Photo(values[0], values[4])
                        photo.set_creation_and_rotation(values[1], values[3])
                        photo.num = values[2]
                        photo.set_thumbnail()
                        photo_list[user].append(photo)

    return photo_list
