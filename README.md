# Zucasa

Get a Picasa styled photo gallery web server.

A script runs through configured photo locations and creates thumbnails and extracts metainfo without touching your files.

A server creates web pages for the thumbnails sorted by date and grouped by user, with links to original photos.

## Requirements

Runs on GNU/Linux using Bash, Python, Flask, ExifTool and ImageMagick.

## Usage

1. Point zucasa.rc to your photos
2. Run reload.sh to create thumbnails and extract metainfo (temporary files are kept in server/static/import)
3. Run server.sh to start web server

See output from server script to find where your gallery is hosted.

If you're using usernames for your photos then append username to URL, for instance http://192.168.123.123:5000/bob
