import os
from shutil import copyfile
import datetime
import operator

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

class Photo:
    """Holds reference to a photo via user, year, month, day and number. 
    Has methods to get metainfo and original image."""

    ext="" # File extension

    def __init__(self, user, year, month, day, num):
        self.user = user
        self.year = year
        self.month = month
        self.day = day
        self.num = int(num)

        # Create datetime object to sort photos
        self.date_taken = datetime.date(int(year), int(month), int(day))

        # Where to find meta info
        self.meta_info_file = os.getcwd() + "/server/static/import/" + \
            user + "/" + year + "/" + month + "/" + day + "/" + num + ".txt"

        # Where to put original photo when copying to cache (without extension)
        self.cache_file = os.getcwd() + "/server/static/cache/" + \
            user + year + month + day + "-" + num

        # Original source relative to working directory (cache_file with extension)
        self.original_src = "" # Must call load_photo before use

    def load_photo(self):
        self.meta_info = self.get_meta_info()
        self.original_src = self.copy_to_cache(self.meta_info["Directory"], self.meta_info["File Name"])

    def get_meta_info(self):
        """Get metainfo from text file matching name of thumbnail split into map."""
        meta_info = {}
        f = open(self.meta_info_file)
        for line in f:
            index = line.index(":")
            meta_info[line[:index].rstrip()] = line[index + 2:].rstrip()
        return meta_info

    def copy_to_cache(self, directory, file_name):
        """Copy original photo into cache and return its filename, relative to working directory."""
        extension = file_name[-4:]
        self.cache_file += extension
        copyfile(directory + "/" + file_name, self.cache_file)
        return self.cache_file[self.cache_file.index("/static/cache/"):]

    def get_thumbnail_src(self):
        """Return reference to thumbnail file for this photo."""
        return "/static/import/" + self.user + "/" + self.year + "/" + self.month + "/" + self.day + \
            "/" + str(self.num) + "." + self.ext



