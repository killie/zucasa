import os
import sys
from datetime import datetime
from uuid import uuid4
import subprocess
from multiprocessing import Pipe

class Photo:
    """Holds reference to a photo via user, year, month, day and uuid. 
    Has methods to get metainfo and original image."""

    FORMATS = ["jpg", "png", "gif"]

    def __init__(self, user, path):
        self.user = user
        self.path = path
        i = self.path.rfind(".")
        self.ext = self.path[i:]
        self.uuid = str(uuid4()).replace("-", "")
        self.thumbnail = self.uuid + ".jpg"
        self.camera = ""
        self.tags = []

    def __repr__(self):
        return str(self.created)
    
    def verify(self):
        # Create date is read from metainfo if file is a photo
        date_string = ""
        if self._is_photo():
            metainfo = self.load_metainfo()
            if "Create Date" in metainfo:
                date_string = metainfo["Create Date"]
            else:
                print "Could not get 'create date' from " + self.path
            if "Camera Model Name" in metainfo:
                self.camera = metainfo["Camera Model Name"]

        if not date_string:
            self.created = False
            return

        # Extract year, month and day as strings from create date
        try:
            self.created = datetime.strptime(date_string[:19], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            self.created = False
            return

        self._set_year_month_day()

        # Update thumbnail with year/month/day folder structure
        self.thumbnail = os.getcwd() + "/server/static/import/photos/" + \
            self.user + "/" + self.year + "/" + self.month + "/" + self.day + "/" + self.thumbnail

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

    def load_metainfo(self):
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

    def create_thumbnail(self, size):
        if self.rotation > 0:
            subprocess.check_output(["convert", "-rotate", str(self.rotation), "-thumbnail", "x" + str(size), self.path, self.thumbnail])
        else:
            subprocess.check_output(["convert", "-thumbnail", "x" + str(size), self.path, self.thumbnail])

    def load_photo(self):
        directory = os.getcwd() + "/server/static/cache"
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.cache = directory + "/" + self.user + self.year + self.month + self.day + self.uuid + self.ext
        subprocess.check_output(["cp", self.path, self.cache])

def delete_files():
    """Remove directories where import and cache files are stored."""
    _delete_directories()

def _delete_directories():
    _delete_directory(os.getcwd() + "/server/static/import")
    _delete_directory(os.getcwd() + "/server/static/cache")

def _delete_directory(directory):
    if os.path.exists(directory):
        subprocess.check_output(["rm", "-R", directory])

def import_photos(config, pipe):
    """Load photos from locations, reading metadata and creating thumbnails. Sending photos back over pipe continuously."""
    # Start by extracting date and time photo was taken from metainfo along with rotation
    photos = _get_photos(config, pipe)
    # When all locations have been read sort photos by creation date
    pipe.send({"status": "Preparing folder structure..."})
    grouped = group_photos(photos)
    # Save thumbnails with height equal size argument, and rotate as necessary
    pipe.send({"status": "Creating thumbnails..."})
    _create_thumbnails(grouped, config.size)
    pipe.send({"status": "Done"})

def _get_photos(config, pipe):
    photos = []
    for location in config.locations.keys():
        pipe.send({"status": "Importing " + location + "..."})
        user = config.locations[location]
        for path, dirs, filenames in os.walk(location):
            for filename in filenames:
                photo = Photo(user, path + "/" + filename)
                photo.verify()
                if photo.is_valid():
                    pipe.send({"imported": photo})
                    photos.append(photo)
                else:
                    pipe.send({"skipped": photo})

    return photos

def group_photos(photos):
    """Sort photos by ascending create date. Sort files on descending create date. Return photos grouped by day."""
    dated = _group_by_date(photos)
    for year in dated:
        for month in dated[year]:
            for day in dated[year][month]:
                dated[year][month][day].sort(key=lambda p: p.created)

    photos.sort(key=lambda p: p.created, reverse=True)
    return dated

def _group_by_date(photos):
    """Group photos in map by year, month, day and photo array."""
    dated = {}
    for photo in photos:
        if not photo.year in dated:
            dated[photo.year] = {}
        if not photo.month in dated[photo.year]:
            dated[photo.year][photo.month] = {}
        if not photo.day in dated[photo.year][photo.month]:
            dated[photo.year][photo.month][photo.day] = []
        dated[photo.year][photo.month][photo.day].append(photo)
    return dated

def _create_thumbnails(dated, size):
    """Create thumbnails in user/year/month/day hierarchy below import/photos."""
    directory = os.getcwd() + "/server/static/import"
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(directory + "/photos"):
        os.makedirs(directory + "/photos")
    for year in dated:
        for month in dated[year]:
            for day in dated[year][month]:
                for photo in dated[year][month][day]:
                    user_dir = directory + "/photos/" + photo.user
                    if not os.path.exists(user_dir):
                        os.makedirs(user_dir)
                    if not os.path.exists(user_dir + "/" + year):
                        os.makedirs(user_dir + "/" + year)
                    if not os.path.exists(user_dir + "/" + year + "/" + month):
                        os.makedirs(user_dir + "/" + year + "/" + month)
                    if not os.path.exists(user_dir + "/" + year + "/" + month + "/" + day):
                        os.makedirs(user_dir + "/" + year + "/" + month + "/" + day)
                    photo.create_thumbnail(size)

