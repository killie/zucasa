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
    _delete_directory(os.getcwd() + "/server/static/preview")
    _delete_directory(os.getcwd() + "/server/static/cache")

def _delete_directory(directory):
    if os.path.exists(directory):
        subprocess.check_output(["rm", "-R", directory])

def import_photos(config, pipe):
    """Load photos from locations, reading metadata and creating thumbnails. Sending photos back over pipe continuously."""
    _get_photos(config, pipe)
    pipe.send({"status": "Done"})

def _get_photos(config, pipe):
    _check_thumbnail_root()
    for location in config.locations.keys():
        pipe.send({"status": "Importing " + location + "..."})
        user = config.locations[location]
        for path, dirs, filenames in os.walk(location):
            for filename in filenames:
                photo = Photo(user, path + "/" + filename)
                photo.verify()
                if photo.is_valid():
                    photo.create_thumbnail(config.size)
                    pipe.send({"imported": photo})
                else:
                    pipe.send({"skipped": photo})

def _check_thumbnail_root():
    directory = os.getcwd() + "/server/static/import"
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(directory + "/photos"):
        os.makedirs(directory + "/photos")

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

