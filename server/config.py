import os

class Config:
    """Holds configuration values and supports reading and writing to resource file.
    Skips comments and replaces all locations, users, size and limit values."""

    INITIAL_COMMENT_BLOCK = [
        "# Zucasa configuration file.",
        "# Comments are ignored. Allowed keys are: location, user, size, limit.",
        "# File will be replaced when using /config from web interface.",
        "",
        "# Add location + user pairs for each photo folder to import (recursively).",
        "# If user is not set then 'public' will be used (photo are for all users).",
        "# User should be single word lower-case string."]

    SIZE_COMMENT = "# Thumbnails size in pixels (max height)."

    LIMIT_COMMENT = "# Where to split page (number of photos on page)."

    DEFAULT_SIZE = 80
    DEFAULT_LIMIT = 300

    # Public properties

    locations = {}
    size = DEFAULT_SIZE
    limit = DEFAULT_LIMIT

    # Load from resource file

    def load(self, filename):
        """Load from resource file."""
        self.locations = self._load_locations(filename)
        self.size = self._load_size(filename)
        self.limit = self._load_limit(filename)

    def _load_locations(self, filename):
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

    def _load_size(self, filename):
        """Load thumbnail size from resource file."""
        f = open(filename)
        for line in f.read().split("\n"):
            if (line[:5] == "size="):
                return int(line[5:])

        return self.DEFAULT_SIZE

    def _load_limit(self, filename):
        """Load page size from resouce file."""
        f = open(filename)
        for line in f.read().split("\n"):
            if (line[:6] == "limit="):
                return int(line[6:])

        return self.DEFAULT_LIMIT

    # Save to resource file

    def save(self, params, filename):
        """Replace public properties and overwrite resource file."""
        if params:
            self._extract_params(params)
        self._replace_file(filename)

    def _extract_params(self, params):
        """Replaces local variables with contents of params map."""
        for param in params:
            if param == "size": 
                self.size = params[param]
            elif param == "limit":
                self.limit = params[param]

        self.locations = {}
        for i in range(1, 50):
            x = str(i)
            # TODO: Check if user is blank. Then use 'public'.
            if ("location" + x in params and "user" + x in params):
                self.locations[params["location" + x]] = params["user" + x]

    def _replace_file(self, filename):
        """Replaces everything in resource file."""
        f = open(filename, "w")

        map(lambda x: f.write(x + "\n"), self.INITIAL_COMMENT_BLOCK)

        for location in self.locations:
            f.write("location=" + location + "\n")
            f.write("user=" + self.locations[location] + "\n\n")

        f.write(self.SIZE_COMMENT + "\n")
        f.write("size=" + str(self.size) + "\n\n")

        f.write(self.LIMIT_COMMENT + "\n")
        f.write("limit=" + str(self.limit) + "\n")

        f.close()
