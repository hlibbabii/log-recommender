#!/usr/bin/env bash

#source run.properties

#function copyLines() {
#    if ! [[ "$#" -eq 5 ]]; then
#        echo "The number of args is $#, not 5. Terminating copyLines function"
#        return 1
#    fi
#
#    FROM="$1"
#    TO="$2"
#    HOW_MANY="$3"
#    OUT_OF="$4"
#    HOW_MANY_TIMES="$5"
#
#    rm ${TO}
#
#    for (( i=0; i<$HOW_MANY_TIMES; i++ ))
#    do
#        OFFSET=$(( $i * $OUT_OF ))
#        START=$(( $OFFSET + 1 ))
#        END=$(( $OFFSET + $HOW_MANY ))
#        less $FROM | sed -n "${START},${END}p" >> $TO
#    done
#}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -e|--extract-logs)
    PROJECT_LIST_FILE="$2"
    shift 2
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if ! [ -d $GENERATED_STATS_FOLDER ]; then
    mkdir $GENERATED_STATS_FOLDER
fi

PATH_TO_CACHED_PROJECTS=$1

if [ -n "$PROJECT_LIST_FILE" ]; then
    cd .. #TODO !! fix pathes
    mv ../.Logs .
    SCRIPT="$(pwd)/log-extractor.sh ${PROJECT_LIST_FILE}"
    if [ -n "$PATH_TO_CACHED_PROJECTS" ]; then
        SCRIPT="$SCRIPT $PATH_TO_CACHED_PROJECTS"
    fi
    echo "Extracting logs: running $SCRIPT"
    eval "$SCRIPT"
    mv .Logs/ ..
else
    echo "Not extracting logs, working with existing ones"
fi