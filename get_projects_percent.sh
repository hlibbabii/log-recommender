#!/usr/bin/env bash

function cpppp() {
    FROM="$1"
    TO="$2"
    MAX_FILES_IN_FOLDER="$3"

    CURR_NUMBER=$(ls "$TO" | wc -l)
    CURR_FOLDER="$TO/$CURR_NUMBER"

    if [ "$(ls "$CURR_FOLDER" | wc -l)" -ge  "$MAX_FILES_IN_FOLDER" ]; then
        CURR_NUMBER=$(( CURR_NUMBER+1 ))
        CURR_FOLDER="$TO/$CURR_NUMBER"
    fi
    [[ -d "$CURR_FOLDER" ]] || mkdir "$CURR_FOLDER"

    cp -r "$FROM" "$TO/$CURR_NUMBER"
}
export -f cpppp

PATH_TO_RAW_DATASET="$1"
PERCENT="$2"
PROJECTS_IN_FOLDER="$3"

DIR_TO_COPY="$PATH_TO_RAW_DATASET"/"$PERCENT"_percent
if [ -e "$DIR_TO_COPY" ]; then
    echo "Dir already exists: $DIR_TO_COPY"
    exit 0
fi
mkdir "$DIR_TO_COPY"
mkdir "$DIR_TO_COPY/train"
mkdir "$DIR_TO_COPY/train/1"
mkdir "$DIR_TO_COPY/test"
mkdir "$DIR_TO_COPY/test/1"
mkdir "$DIR_TO_COPY/valid"
mkdir "$DIR_TO_COPY/valid/1"

PATH_TO_ALL_PROJECTS="$PATH_TO_RAW_DATASET/all"

N_PROJECTS=$(ls "$PATH_TO_ALL_PROJECTS" | wc -l)
N_PROJECTS_TO_SELECT=$(( N_PROJECTS * PERCENT / 100 ))
N_TEST=$(( $N_PROJECTS_TO_SELECT / 5 ))
N_VALID=$N_TEST
N_TRAIN=$(( N_PROJECTS_TO_SELECT - N_TEST - N_VALID ))

ls "$PATH_TO_ALL_PROJECTS" | sort -R | head -$N_TRAIN | xargs -I{} bash -c "cpppp $PATH_TO_ALL_PROJECTS/{} $DIR_TO_COPY/train $PROJECTS_IN_FOLDER"
ls "$PATH_TO_ALL_PROJECTS" | sort -R | head -$((N_TRAIN + N_TEST)) | tail -$N_TEST | xargs -I{} bash -c "cpppp $PATH_TO_ALL_PROJECTS/{} $DIR_TO_COPY/test $PROJECTS_IN_FOLDER"
ls "$PATH_TO_ALL_PROJECTS" | sort -R | head -$N_PROJECTS_TO_SELECT | tail -$N_VALID | xargs -I{} bash -c "cpppp $PATH_TO_ALL_PROJECTS/{} $DIR_TO_COPY/valid $PROJECTS_IN_FOLDER"