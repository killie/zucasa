import os
from shutil import copyfile
from datetime import datetime
import operator
import subprocess

class Photo:
    """Holds reference to a photo via user, year, month, day and number. 
    Has methods to get metainfo and original image."""

    FORMATS = ["jpg", "png", "gif"]

    def __init__(self, user, path):
        self.user = user
        self.path = path
        i = self.path.rfind(".")
        self.ext = self.path[i:]

    def __repr__(self):
        return str(self.created)
    
    def set_creation_and_rotation(self, created, rotation):
        self.created = datetime.fromtimestamp(float(created))
        self._set_year_month_day()
        self.rotation = int(rotation)

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
        self._set_year_month_day()

        # Get orientation from metainfo so we're ready to rotate when creating thumbnail
        self.rotation = 0
        if ("Orientation" in metainfo):
            if (metainfo["Orientation"] == "Rotate 90 CW"):
                self.rotation = 90
            elif (metainfo["Orientation"] == "Rotate 270 CW"):
                self.rotation = 270

    def _set_year_month_day(self):
        """Sets string representations of year, month and day from created datetime."""
        self.year = str(self.created.year)
        self.month = ("", "0")[self.created.month < 10] + str(self.created.month)
        self.day = ("", "0")[self.created.day < 10] + str(self.created.day)        

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

    def set_thumbnail(self):
        path = os.getcwd() + "/server/static/import/photos/" + self.user + "/" + self.year + "/" + self.month + "/" + self.day + "/" + self.num + ".jpg"
        self.thumbnail = path

    def create_thumbnail(self, path, index, size):
        self.num = ((4 - len(str(index))) * "0") + str(index)
        self.thumbnail = path + "/" + self.num + ".jpg"
        if self.rotation > 0:
            subprocess.check_output(["convert", "-rotate", str(self.rotation), "-thumbnail", "x" + str(size), self.path, self.thumbnail])
        else:
            subprocess.check_output(["convert", "-thumbnail", "x" + str(size), self.path, self.thumbnail])

    def load_photo(self):
        directory = os.getcwd() + "/server/static/cache"
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.cache = directory + "/" + self.user + self.year + self.month + self.day + self.num + self.ext
        subprocess.check_output(["cp", self.path, self.cache])


def import_photos(config, photo_list, photo_map, progress):
    """Load photos from locations, creating thumbnails and extracting metainfo."""
    # Start by extracting date and time photo was taken from metainfo along with rotation
    _get_photos(config, photo_list, photo_map, progress)
    # When all locations have been read sort photos by creation date
    sort_photos(photo_list, photo_map)
    # Save thumbnails with height equal size argument, and rotate as necessary
    _create_thumbnails(photo_map, config.size, progress)

def _empty_photos(photo_list, photo_map):
    """Empty photos map and delete all instances in files map. Does not touch files on disk."""


def _get_photos(config, photo_list, photo_map, progress):
    for location in config.locations.keys():
        print "Importing " + location
        user = config.locations[location]
        if (not user in photo_list):
            photo_list[user] = []
        if (not user in photo_map):
            photo_map[user] = {}
        
        for path, dirs, filenames in os.walk(location):
            for filename in filenames:
                photo = Photo(user, path + "/" + filename)
                photo.load_creation_and_rotation()
                if photo.is_valid():
                    photo_list[user].append(photo)
                    if not photo.year in photo_map[user]:
                        photo_map[user][photo.year] = {}
                    if not photo.month in photo_map[user][photo.year]:
                        photo_map[user][photo.year][photo.month] = {}
                    if not photo.day in photo_map[user][photo.year][photo.month]:
                        photo_map[user][photo.year][photo.month][photo.day] = []
                    photo_map[user][photo.year][photo.month][photo.day].append(photo)

        print str(len(photo_list[user])) + " photos imported"

def sort_photos(photo_list, photo_map):
    """Sort photos by ascending create date. Sort files on descending create date."""
    for user in photo_map:
        for year in photo_map[user]:
            for month in photo_map[user][year]:
                for day in photo_map[user][year][month]:
                    photo_map[user][year][month][day].sort(key=operator.attrgetter("created"))

    for user in photo_list:
        photo_list[user].sort(key=operator.attrgetter("created"), reverse=True)

def _create_thumbnails(photo_map, size, progress):
    """Create thumbnails in user/year/month/day hierarchy below import/photos."""
    directory = os.getcwd() + "/server/static/import" 
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(directory + "/photos"):
        os.makedirs(directory + "/photos")

    for user in photo_map:
        user_dir = directory + "/photos/" + user
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        for year in photo_map[user]:
            if not os.path.exists(user_dir + "/" + year):
                os.makedirs(user_dir + "/" + year)
            for month in photo_map[user][year]:
                if not os.path.exists(user_dir + "/" + year + "/" + month):
                    os.makedirs(user_dir + "/" + year + "/" + month)
                for day in photo_map[user][year][month]:
                    thumb_dir = user_dir + "/" + year + "/" + month + "/" + day
                    if not os.path.exists(thumb_dir):
                        os.makedirs(thumb_dir)
                    # TODO: Empty dir
                    for index, photo in enumerate(photo_map[user][year][month][day]):
                        photo.create_thumbnail(thumb_dir, index + 1, size)


def group_by_date(photo_list):
    """Group photo_list in photo_map map by user, year, month, day and photo array."""
    photo_map = {}
    for user in photo_list:
        photo_map[user] = {}
        for photo in photo_list[user]:
            if not photo.year in photo_map[user]:
                photo_map[user][photo.year] = {}
            if not photo.month in photo_map[user][photo.year]:
                photo_map[user][photo.year][photo.month] = {}
            if not photo.day in photo_map[user][photo.year][photo.month]:
                photo_map[user][photo.year][photo.month][photo.day] = []
            photo_map[user][photo.year][photo.month][photo.day].append(photo)

    return photo_map
        
