#!/bin/bash

# Script is executed on one or more directories to create thumbnails and extract metainfo into files.
# For each run it removes temp directory (below server/static) and recreates thumbnails and metainfo.

# Server reads temp directory into memory and serves web pages with thumnails and links to original images.

# Name and location of config file
CONFIG_FILE="zucasa.rc"

# Name of log file
LOG_FILE="zucasa.log"

# Thumbnails and metainfo files are kept in server/static/import (directory is wiped between each run)
OUTPUT="server/static/import"

# Cache originals here for a limited period of time
CACHE="server/static/cache"

# Size (height) of each thumbnail
SIZE=75

# CSV of input directories on the form "user,dir;user,dir;"
INPUTS=""

# Initializing log file
init_log_file() {
    cp /dev/null $LOG_FILE
    log_info "Initializing..."
}

# Append info $1 to log file
log_info() {
    add_to_log "II" "$@"
}

# Append warning $1 to log file
log_warn() {
    add_to_log "WW" "$@"
}

# Append error $1 to log file
log_err() {
    add_to_log "EE" "$@"
}

add_to_log() {
    echo $1 $(date +%F\ %T) "${@: 2}" >> $LOG_FILE
}

# Check that dependencies exists
check_dependencies() {
    log_info "Checking dependencies..."
    local -i retval=0
    command -v exiftool >/dev/null 2>&1 || {
        log_err "Cannot find dependency 'exiftool'. Aborting."
	exit 31
    }
    command -v convert >/dev/null 2>&1 || {
	log_err "Cannot find dependency 'imagemagick'. Aborting."
	exit 32
    }
    return $retval
}

# Read config file into tuples string skipping blank lines and comments on the form 
# "setting1,value1;setting2,value2;" from file with setting1=value1\n etc.
# $1 name of config file
read_config_file() {
    local tuples=""
    declare -a lines
    if [ -e $1 ]; then
	# Link filedescriptor 10 with stdin
	exec 10<&0

	# Read file into lines array
	exec < $1
        let count=0
	while read line; do
	    lines[$count]=$line
	    ((count++))
	done

	# Restore stdin from filedescriptor 10 and close it
	exec 0<&10 10<&-

	# Run through all lines and collect config values
	for line in "${lines[@]}"; do
	    if [[ ${line:0:1} != "#" && ${line:0:1} != "" ]]; then
		IFS="=" read -r setting value <<< $line
		tuples="$tuples$setting,$value;"
	    fi
	done
    fi
    echo $tuples
    # TODO: How to handle error? Send to errout? Don't forget to log
}

# Load config file into globals
# $1 name of config file
# Returns 0 if OK, else an error code
load_config_file() {
    local config=$(read_config_file $1)
    local dirs=""
    local last_dir=""
    IFS=";" read -a items <<< $config
    for item in "${items[@]}"; do
	IFS="," read setting value <<< $item
	
	if [[ $last_dir != "" ]]; then
	    # If next setting is not username then basedir is for all users
	    if [[ $setting == "username" ]]; then
		dirs="$dirs$value,$last_dir;"
	    else
		dirs="$dirs[none],$last_dir;"
	    fi
	    last_dir=""
	fi

	# Keep basedir in temporary variable, add depending on next line
	if [[ $setting == "basedir" ]]; then last_dir=$value; fi

	# Read other values directly into globals
	if [[ $setting == "size" ]]; then SIZE=$value; fi
    done

    INPUTS=$dirs
}

# Checks if $1 file is a photo (by checking file extension)
file_is_photo() {
    if [[ $1 == *.jpg || $1 == *.JPG || $1 == *.png || $1 == *.PNG ]]; then
	echo true
    else
	echo false
    fi
}

# Loop all files in directory, create thumbnail and extract metainfo as needed
# $1 username
# $2 directory
import_dir() {
    log_info "Importing all photos in ${@: 2} (user: $1)..."
    local user=$1
    declare -i imported=0
    declare -i skipped=0
    # Find all files below directory
    while read -d $'\0' file; do
	local is_photo=$(file_is_photo "$file")
	if [[ $is_photo == false ]]; then continue; fi

	local create_date=$(exiftool "$file" -CreateDate)
	if [[ $create_date == "" ]]; then
	    # Could not get create date from EXIF metadata -- TODO: Try filename
	    log_warn "Could not get create date from $file. Skipping."
	    let skipped++
	else
	    # Split into date parts and create directory
	    local year=${create_date:34:4}
	    local month=${create_date:39:2}
	    local day=${create_date:42:2}

	    # If user is [none] create public directory, followed by year/month/day
	    if [[ $user == "[none]" ]]; then user="public"; fi
	    mkdir -p "$OUTPUT/$user"
	    mkdir -p "$OUTPUT/$user/$year"
	    mkdir -p "$OUTPUT/$user/$year/$month"
	    mkdir -p "$OUTPUT/$user/$year/$month/$day"

	    # Find logical filename by counting all files in directory excluding text files
	    local path="$OUTPUT/$user/$year/$month/$day"
	    local filename=$(create_filename $path)

	    # Create thumbnail and extract metainfo to text file
	    create_thumbnail "$file" "$path" "$filename.jpg"
	    create_metainfo "$file" "$path" "$filename.txt"
	    let imported++
	fi
    done < <(find "${@: 2}" -print0)
    log_info "Imported $imported, skipped $skipped."
}

# Count number of files in directory and increase by one, ignoring text files. Return number without extension.
create_filename() {
    local count=$(ls $1 -p | grep -v '\.txt' | wc -l)
    count=$((count + 1))
    echo $count
}

# Create thumbnail for $1 and put file in $2 with filename $3
create_thumbnail() {
    # TODO: Should rotate before creating thumbnail
    convert -thumbnail x$SIZE "$1" "$2"/$3
}

# Get metainfo for $1 saved on path $2 with filename $3
create_metainfo() {
    exiftool "$1" > "$2"/$3
}

# Get local IP and write it to local_ip.txt file, so Flask knows where to host itself
get_local_ip() {
    local local_ip=$(grep -Po 'src \K.*(?= cache)' <<< $(ip route get 1))
    # if RTNETLINK answers: Network is unreachable then use blank (localhost)
    echo $local_ip > local_ip.txt
    log_info "Local IP $local_ip written to: local_ip.txt (for hosting web server)"
}

main() {
    init_log_file
    check_dependencies
    get_local_ip
    load_config_file $CONFIG_FILE

    # Empty output directory
    mkdir -p $OUTPUT
    rm -R $OUTPUT/*

    # Empty cache directory
    mkdir -p $CACHE
    rm -R $CACHE/*

    # Split inputs and import each directory in order
    IFS=";" read -a items <<< $INPUTS
    for item in "${items[@]}"; do
	IFS="," read username input <<< $item
	import_dir "$username" "$input"
    done
}

main "$@"
