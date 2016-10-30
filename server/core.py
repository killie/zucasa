import os
from shutil import copyfile

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

class Photo:
    """Holds reference to a photo via user, year, month, day and number. 
    Has methods to get metainfo and original image."""

    def __init__(self, user, year, month, day, num):
        self.user = user
        self.year = year
        self.month = month
        self.day = day
        self.num = num

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






