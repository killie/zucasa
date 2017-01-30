# Zucasa

Get a Picasa styled photo gallery web server.

Program runs through configured photo locations and creates thumbnails and extracts metainfo without touching your files.

A server creates web pages for the thumbnails sorted by date and grouped by user, with links to original photos.

Thumbnails and temporary files are stored under `server/static/import` and `server/static/cache`. 

## Requirements

Runs on GNU/Linux using Python, Flask, ExifTool and ImageMagick.

## Usage

1. Run `zucasa.sh` to start web server
2. Go to Settings and enter your photo location(s)
3. Import process is not optimal right now, so just watch stdout until 'Done', then refresh your browser

See output from startup script to find where your gallery is hosted.
