import os
from shutil import copyfile
from datetime import datetime
import operator
import subprocess

class Photo:
    """Holds reference to a photo via user, year, month, day and number. 
    Has methods to get metainfo and original image."""

    FORMATS = ["jpg", "png", "gif"]

    def __init__(self, path, modified):
        self.path = path
        i = self.path.rfind(".")
        self.ext = self.path[i:]
        self.modified = modified

    def __repr__(self):
        return str(self.created)
        
    def load_creation_and_rotation(self):
        # Create date is read from metainfo if file is a photo
        date_string = ""
        if self._is_photo():
            metainfo = self._load_metainfo(self.path)
            if ("Create Date" in metainfo):
                date_string = metainfo["Create Date"]
            else:
                print "Skipping " + self.path

        if not date_string:
            self.created = False
            return

        # Extract year, month and day as strings from create date
        self.created = datetime.strptime(date_string[:19], "%Y:%m:%d %H:%M:%S")
        self.year = str(self.created.year)
        self.month = ("", "0")[self.created.month < 10] + str(self.created.month)
        self.day = ("", "0")[self.created.day < 10] + str(self.created.day)

        # Get orientation from metainfo so we're ready to rotate when creating thumbnail
        self.rotation = 0
        if ("Orientation" in metainfo):
            if (metainfo["Orientation"] == "Rotate 90 CW"):
                self.rotation = 90
            elif (metainfo["Orientation"] == "Rotate 270 CW"):
                self.rotation = 270

    def _load_metainfo(self, path):
        """Get metainfo from text file matching name of thumbnail split into map."""
        metainfo = {}
        lines = subprocess.check_output(["exiftool", self.path])
        for line in lines.split("\n"):
            if line:
                index = line.index(":")
                metainfo[line[:index].rstrip()] = line[index + 2:].rstrip()

        return metainfo

    def is_valid(self):
        return self._is_photo() and self.created

    def _is_photo(self):
        """Check extension on filename versus accepted formats."""
        return self.ext[1:].lower() in self.FORMATS

    def create_thumbnail(self, path, index, size):
        self.num = ((4 - len(str(index))) * "0") + str(index)
        self.thumbnail = path + "/" + self.num + ".jpg"
        if self.rotation > 0:
            subprocess.check_output(["convert", "-rotate", str(self.rotation), "-thumbnail", "x" + str(size), self.path, self.thumbnail])
        else:
            subprocess.check_output(["convert", "-thumbnail", "x" + str(size), self.path, self.thumbnail])


def import_photos(config, files, photos, progress):
    """Load photos from locations, creating thumbnails and extracting metainfo."""
    # Start by extracting date and time photo was taken from metainfo along with rotation
    _get_photos_and_files(config, photos, files, progress)
    # When all locations have been read sort photos by creation date
    _sort_photos_and_files(photos, files, progress)
    # Save thumbnails with height equal size argument, and rotate as necessary
    _create_thumbnails(photos, config.size, progress)
    
def _get_photos_and_files(config, photos, files, progress):
    for location in config.locations.keys():
        print "Importing " + location
        user = config.locations[location]
        if (not user in photos):
            photos[user] = {}
        if (not user in files):
            files[user] = []
        
        for path, dirs, filenames in os.walk(location):
            for filename in filenames:
                modified = os.path.getmtime(path + "/" + filename)
                photo = Photo(path + "/" + filename, modified)
                photo.load_creation_and_rotation()
                if photo.is_valid():
                    files[user].append(photo)
                    if not photo.year in photos[user]:
                        photos[user][photo.year] = {}
                    if not photo.month in photos[user][photo.year]:
                        photos[user][photo.year][photo.month] = {}
                    if not photo.day in photos[user][photo.year][photo.month]:
                        photos[user][photo.year][photo.month][photo.day] = []
                    photos[user][photo.year][photo.month][photo.day].append(photo)

        print str(len(files[user])) + " photos imported"

def _sort_photos_and_files(photos, files, progress):
    """Sort photos by ascending create date. Sort files on descending create date."""
    for user in photos:
        for year in photos[user]:
            for month in photos[user][year]:
                for day in photos[user][year][month]:
                    photos[user][year][month][day].sort(key=operator.attrgetter("created"))

    for user in files:
        files[user].sort(key=operator.attrgetter("created"), reverse=True)

def _create_thumbnails(photos, size, progress):
    """Create thumbnails in user/year/month/day hierarchy below import/photos."""
    directory = os.getcwd() + "/server/static/import" 
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(directory + "/photos"):
        os.makedirs(directory + "/photos")

    for user in photos:
        user_dir = directory + "/photos/" + user
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        for year in photos[user]:
            if not os.path.exists(user_dir + "/" + year):
                os.makedirs(user_dir + "/" + year)
            for month in photos[user][year]:
                if not os.path.exists(user_dir + "/" + year + "/" + month):
                    os.makedirs(user_dir + "/" + year + "/" + month)
                for day in photos[user][year][month]:
                    thumb_dir = user_dir + "/" + year + "/" + month + "/" + day
                    if not os.path.exists(thumb_dir):
                        os.makedirs(thumb_dir)
                    # TODO: Empty dir
                    for index, photo in enumerate(photos[user][year][month][day]):
                        photo.create_thumbnail(thumb_dir, index + 1, size)

def get_files_as_map(root):
    """Load all known image files into map with user, year, month and day as keys,
    then an array of numbers for photos taken on that day."""

    photos = {"public": {}}
    for user in os.walk(root).next()[1]:
        photos[user] = {}

    for user in photos.keys():
        if (os.path.isdir(root + "/" + user)):
            for year in os.walk(root + "/" + user).next()[1]:
                photos[user][year] = {}
                for month in os.walk(root + "/" + user + "/" + year).next()[1]:
                    photos[user][year][month] = {}
                    for day in os.walk(root + "/" + user + "/" + year + "/" + month).next()[1]:
                        photos[user][year][month][day] = []
                        for path, dirs, files in os.walk(root + "/" + user + "/" + year + "/" + month + "/" + day):
                            for filename in files:
                                if (filename.endswith(".txt") == False):
                                    photos[user][year][month][day].append(filename)
                        
                        # Sort file numbers array
                        photos[user][year][month][day].sort()

    return photos

def sort_photos_into_array(m):
    """Takes map of photos and creates instances of Photo class which are added to user map,
    where each user has an array of photos sorted by descending date."""

    photos = {"public": []}
    for user in m.keys():
        photos[user] = []
        for year in m[user].keys():
            for month in m[user][year].keys():
                for day in m[user][year][month].keys():
                    for f in m[user][year][month][day]:
                        num = f[:f.index(".")]
                        photo = Photo(user, year, month, day, num)
                        photo.ext = f[f.index(".") + 1:]
                        photos[user].append(photo)

        photos[user].sort(key=operator.attrgetter("num"))
        photos[user].sort(key=operator.attrgetter("date_taken"), reverse=True)

    return photos

