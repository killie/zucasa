import os
from shutil import copyfile
import datetime
import operator
import subprocess

class Photo:
    """Holds reference to a photo via user, year, month, day and number. 
    Has methods to get metainfo and original image."""

    def __init__(self, path, modified):
        self.path = path
        i = self.path.rfind(".")
        self.ext = self.path[i:]
        self.modified = modified
        
    def load_creation_and_rotation(self):
        self.metainfo = self._load_metainfo(self.path)
        if ("Create Date" in self.metainfo):
            self.created = self.metainfo["Create Date"]
        else:
            print "Skipping " + self.path
            self.created = False

        if ("Orientation" in self.metainfo):
            if (self.metainfo["Orientation"] == "Rotate 90 CW"):
                self.rotate = 90
            elif (self.metainfo["Orientation"] == "Rotate 270 CW"):
                self.rotate = 270
            else:
                self.rotate = 0

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
        if (self.created != False):
            print self.path + " (" + self.created + ")"
        return self.created

def import_photos(config, files, photos, progress):
    """Load photos from locations, creating thumbnails and extracting metainfo.

    Start by extracting date and time photo was taken from meta info along with rotation.
    When all locations have been read sort photos by creation date.
    Save thumbnails with height equal size argument, and rotate as necessary."""

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

        print files[user]

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

