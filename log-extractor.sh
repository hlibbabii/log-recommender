#!/usr/bin/env bash

#https://stackoverflow.com/questions/3915040/bash-fish-command-to-print-absolute-path-to-a-file#answer-23002317
function abspath() {
    # generate absolute path from relative path
    # $1     : relative filename
    # return : absolute path
    if [ -d "$1" ]; then
        # dir
        (cd "$1"; pwd)
    elif [ -f "$1" ]; then
        # file
        if [[ $1 = /* ]]; then
            echo "$1"
        elif [[ $1 == */* ]]; then
            echo "$(cd "${1%/*}"; pwd)/${1##*/}"
        else
            echo "$(pwd)/$1"
        fi
    fi
}

LINE_PREFIX="#L"

LINES_BEFORE_TO_EXTRACT=4

REGEX='\([Ll]og\|LOG\)\.\([Tt]race\|[Dd]ebug\|[Ii]nfo\|[Ww]arn\|[Ee]rror\\[Ff]atal\)(.*)'

FILE_FOR_OUTPUT=$(pwd)/grepped_logs.$(date "+%Y%m%d-%H%M%S")
echo "Extracting logs to ${FILE_FOR_OUTPUT}"
echo ${LINES_BEFORE_TO_EXTRACT} >> ${FILE_FOR_OUTPUT}

CSV_FILE=$( abspath "$1" )
echo "Getting projects from $CSV_FILE"

DEFAULT_PROJECT_DIR=".Projects"
if [ -z "$2" ]; then
    PROJECT_DIR=${DEFAULT_PROJECT_DIR}
else
    PROJECT_DIR=$2
fi

if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory ${PROJECT_DIR} found"
else
    echo "Project directory ${PROJECT_DIR} NOT found. Creating it..."
    mkdir "${PROJECT_DIR}"
fi
cd ${PROJECT_DIR}

while IFS=, read -r PROJECT_NAME PROJECT_LINK
do
    if [ -d "${PROJECT_NAME}" ]; then
         echo "${PROJECT_NAME} already exists"
    else
        echo "Getting ${PROJECT_NAME}"
        git clone ${PROJECT_LINK} ${PROJECT_NAME}
    fi
    cd ${PROJECT_NAME}
    COMMIT_HASH=$(git log -n 1 --pretty=format:"%H")

    echo grepping logs from ${PROJECT_NAME} ...
    grep -rn ${REGEX} | while read -r line ; do
        FILE="$(echo $line | sed -n "s/^\(\S*\.\(java\|scala\|groovy\|py\|js\|c\|rb\|adoc\|md\|vm\)\).*$/\1/p")"
        if [ -n "${FILE}" ]; then
            LINE_NUMBER="$(echo $line | sed -n "s/^.*:\([1-9][0-9]*\):.*$/\1/p")"
            BASE_PROJECT_URL="$(echo $PROJECT_LINK | sed -n "s/^\(git\)\(.*\)\.git$/https\2/p")"

            echo "${BASE_PROJECT_URL}/blob/${COMMIT_HASH}/${FILE}${LINE_PREFIX}${LINE_NUMBER}" >> ${FILE_FOR_OUTPUT}
            LINES_RANGE_START=$((LINE_NUMBER-LINES_BEFORE_TO_EXTRACT))
            while [ ${LINES_RANGE_START} -lt "1" ]; do
                echo "" >> ${FILE_FOR_OUTPUT}
                LINES_RANGE_START=$((LINES_RANGE_START + 1))
            done

            LINES=$(sed -n "${LINES_RANGE_START},${LINE_NUMBER}p" ${FILE})
            echo "${LINES}" >> ${FILE_FOR_OUTPUT}
            echo "" >> ${FILE_FOR_OUTPUT}
            echo "" >> ${FILE_FOR_OUTPUT}
        else
            echo "Can't extract file name: $line"
        fi
    done
    cd ..
done < ${CSV_FILE}