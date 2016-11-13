import os
import sys
import codecs
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Photo

def _get_filename(user):
    """List of photos are stored in /static/import/photos/<user>/files.csv"""
    filename = os.getcwd() + "/server/static/import/photos/" + user + "/files.csv"
    return filename

def save_files(files):
    """Save files map to CSV file."""
    for user in files:
        csv = []
        for photo in files[user]:
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

def load_files():
    """Load all import/photos/<user>/files.csv files into map."""
    files = {}
    users = next(os.walk(os.getcwd() + "/server/static/import/photos"))[1]
    for user in users:
        files[user] = []
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
                    files[user].append(photo)

    return files
