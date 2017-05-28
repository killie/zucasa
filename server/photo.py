import os
import re
from datetime import datetime
from uuid import uuid4
import subprocess

class Photo:
    """Holds reference to a photo via user, year, month, day and uuid. 
    Has methods to get metainfo and original image."""

    FORMATS = ["jpeg", "jpg", "png", "gif"]

    def __init__(self, user, path):
        self.user = user
        self.path = path
        i = self.path.rfind(".")
        self.ext = self.path[i:]
        self.uuid = str(uuid4()).replace("-", "")
        self.thumbnail = self.uuid + ".jpg"
        self.description = ""
        self.camera = ""
        self.tags = []
        self.starred = False
        self.duplicate = False

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
                date_string = self._get_date()

            if "Camera Model Name" in metainfo:
                self.camera = metainfo["Camera Model Name"]

            if "Image Height" in metainfo and "Image Width" in metainfo:
                self.height = int(metainfo["Image Height"])
                self.width = int(metainfo["Image Width"])

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

    def _get_date(self):
        """If metainfo is not found or 'Create Date' is not included, try other ways to date a photo.
        Return date string on the form "YYYY:mm:dd HH:MM:SS" (19 characters)."""

        # Check regex in filename *YYYYmmdd?HHMMSS*
        pattern = "\d{8}(.)\d{6}"
        match = re.search(pattern, self.path)
        if match:
            s = match.group(0)
            if len(s) == 15:
                s = s[:8] + s[9:]
            return s[0:4] + ":" + s[4:6] + ":" + s[6:8] + " " + s[8:10] + ":" + s[10:12] + ":" + s[12:14]

        # Use Linux mtime (returns float)
        epoch = os.path.getmtime(self.path)
        modified = datetime.utcfromtimestamp(epoch)
        return str(modified).replace("-", ":")

    def _check_thumbnail_dir(self):
        d = os.getcwd() + "/server/static/import/photos"
        if not os.path.exists(d + "/" + self.user):
            os.makedirs(d + "/" + self.user)
        d += "/" + self.user
        if not os.path.exists(d + "/" + self.year):
            os.makedirs(d + "/" + self.year)
        if not os.path.exists(d + "/" + self.year + "/" + self.month):
            os.makedirs(d + "/" + self.year + "/" + self.month)
        if not os.path.exists(d + "/" + self.year + "/" + self.month + "/" + self.day):
            os.makedirs(d + "/" + self.year + "/" + self.month + "/" + self.day)

    def create_thumbnail(self, size):
        self._check_thumbnail_dir()
        if self.rotation > 0:
            subprocess.Popen(["convert", "-rotate", str(self.rotation), "-thumbnail", "x" + str(size), self.path, self.thumbnail])
        else:
            subprocess.Popen(["convert", "-thumbnail", "x" + str(size), self.path, self.thumbnail])

    def load_photo(self):
        directory = os.getcwd() + "/server/static/cache"
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.cache = directory + "/" + self._get_temp_filename(self.ext)
        subprocess.check_output(["cp", self.path, self.cache])

    def _get_temp_filename(self, ext):
        return self.user + self.year + self.month + self.day + self.uuid + ext

    def load_preview(self):
        # Create preview directory
        directory = os.getcwd() + "/server/static/preview"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # See if preview file already exists
        self.preview = directory + "/" + self._get_temp_filename(".jpg")
        if os.path.isfile(self.preview):
            return

        # Convert original to a smaller size with lower quality
        command = ["convert", self.path, "-format", "'jpg'", "-density", "72x72", "-quality", "50"]
        command = self._add_resize_args(command)
        if self.rotation > 0:
            command.append("-rotate")
            command.append(str(self.rotation))

        command.append(self.preview)
        subprocess.check_output(command)

    def _add_resize_args(self, command):
        if self.height > 1000 or self.width > 2000:
            # Resize width and height while maintaining ratio
            width = self.width / 2
            height = self.height / 2
        else:
            width = self.width
            height = self.height

        command.append("-resize")
        if self.rotation > 0:
            command.append(str(height) + "x" + str(width))
        else:
            command.append(str(width) + "x" + str(height))

        return command

    def rotate(self, degrees):
        command = ["convert", "-rotate", degrees, self.preview, self.preview]
        subprocess.check_output(command)
        command = ["convert", "-rotate", degrees, self.thumbnail, self.thumbnail]
        subprocess.check_output(command)
