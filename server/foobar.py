import os

def load_locations(filename):
    """Load location -> user map from resource file."""
    locations = {}
    location = ""
    user = ""
    f = open(filename)
    for line in f.read().split("\n"):
        if (line[:9] == "location="):
            if (location):
                locations[location] = "public"
            location = line[9:]

        elif (line[:5] == "user="):
            user = line[5:]
            if (location):
                locations[location] = user
                location = ""

    return locations

def load_size(filename):
    """Load thumbnail size from resource file."""
    f = open(filename)
    for line in f.read().split("\n"):
        if (line[:5] == "size="):
            return int(line[5:])

    return 100

def load_months(filename):
    """Load page size from resouce file."""
    f = open(filename)
    for line in f.read().split("\n"):
        if (line[:6] == "months="):
            return int(line[6:])

    return 4

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


    
