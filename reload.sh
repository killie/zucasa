#!/bin/bash

# Script is executed on a dump directory to create thumbnails and extract metainfo into files
# For each run it removes temp directory and recreates thumbnails and metainfo files

# Server reads temp directory into memory and serves web pages with thumnails and links to originals

# Name and location of config file
CONFIG_FILE="zucasa.rc"

# Name of log file
LOG_FILE="zucasa.log"

# Name of metadata file
METADATA_FILE="metadata.txt"

# Where to keep temporary files (directory is wiped between each run)
OUTPUT=""

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

# Load config file checking if directory exists and write permissions
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
	if [[ $setting == "output" ]]; then OUTPUT=$value; fi
	if [[ $setting == "size" ]]; then SIZE=$value; fi

    done

    # Check if output directory exists
    if [[ ! -d $OUTPUT ]]; then
	log_err "Cannot find output directory $OUTPUT"
	return 23
    fi

    # Check if user running script has write permissions
    if [[ ! -w $OUTPUT ]]; then
	log_err "Cannot write to directory $OUTPUT"
	return 24
    fi

    INPUTS=$dirs
}

# Loop all files in directory, create thumbnail and extract metainfo as needed
# $1 username
# $2 directory
import_dir() {
    echo "Import all photos ($1) ${@: 2}"
    for file in $(find "${@: 2}" -name "*.jpg" -or -name "*.png"); do
	local create_date=$(exiftool $file -CreateDate)
	local user=$1
	if [[ $create_date == "" ]]; then
	    # Could not get create date from EXIF metadata -- TODO: Try filename
	    log_warn "Could not get create date from $file"
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

	    # Now find a logical filename, create thumbnail and extract metainfo
	fi
    done
}

# Get metainfo for $1 saved on path $2
extract_metainfo() {
    local -i retval=0

    return $retval
}

# Create thumbnail for $1 with size $2 on path $3
# Creates directory if necessary
create_thumbnail() {
    local -i retval=0

    return $retval
}

main() {
    init_log_file
    check_dependencies
    load_config_file $CONFIG_FILE
    
    # Empty output directory
    rm -R $OUTPUT/*

    # Split inputs and import each directory in order
    IFS=";" read -a items <<< $INPUTS
    for item in "${items[@]}"; do
	IFS="," read username input <<< $item
	import_dir "$username" "$input"
    done
}

main "$@"
