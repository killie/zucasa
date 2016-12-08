import os
import sys
import subprocess
from multiprocessing import Pipe

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from photo import Photo

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

