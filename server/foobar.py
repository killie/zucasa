import os

def load_locations():
    """Load location -> user map from resource file."""
    return {"/media/loft/Camera": "jonole"}

def load_size():
    """Load thumbnail size from resource file."""
    return 100

def load_months():
    """Load page size from resouce file."""
    return 6

def import_photos(locations, size, files, photos, progress):
    """Load photos from locations. Save thumbnails with height equal size argument."""
    for location in locations.keys():
        user = locations[location]
        if (not user in photos):
            photos[user] = {}
        
        for path, dirs, filenames in os.walk(location):
            for filename in filenames:
                modified = os.path.getmtime(path + "/" + filename)
                print path + "/" + filename + " (" + str(modified) + ")"


    
