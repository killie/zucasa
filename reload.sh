#!/bin/bash

# Script is executed on a dump directory to create thumbnails and extract metainfo into files
# For each run it removes temp directory and recreates thumbnails and metainfo files

# Server reads temp directory into memory and serves web pages with thumnails and links to originals

# Name and location of config file
CONFIG_FILE="zucasa.rc"

# Name of log file
LOG_FILE="zucasa.log"

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
    add_to_log "II" $1
}

# Append error $1 to log file
log_err() {
    add_to_log "EE" $1
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
	for line in "${lines[@]}"
	do
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
    for item in "${items[@]}"
    do
	IFS="," read setting value <<< $item
	
	if [[ $last_dir != "" ]]; then
	    # If next setting is not username then basedir is for all users
	    if [[ $setting == "username" ]]; then
		dirs="$dirs$value,$last_dir;"
	    else
		dirs="$dirs*,$last_dir;"
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

# Loop all files in basedir $1, create thumbnail and extract metainfo as needed


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
    echo $INPUTS
    log_info "Ready"
}

main "$@"
