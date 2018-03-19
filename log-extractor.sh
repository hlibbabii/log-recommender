#!/usr/bin/env bash
BASE_URL="https://github.com/apache/"
LINE_PREFIX="#L"

LINES_BEFORE_TO_EXTRACT=4

REGEX='\([Ll]og\|LOG\)\.\([Tt]race\|[Dd]ebug\|[Ii]nfo\|[Ww]arn\|[Ee]rror\\[Ff]atal\)(.*)'

FILE_FOR_OUTPUT=`pwd`/grepped_logs.`date "+%Y%m%d-%H%M%S"`
echo "Extracting logs to ${FILE_FOR_OUTPUT}"
echo ${LINES_BEFORE_TO_EXTRACT} >> ${FILE_FOR_OUTPUT}

CSV_FILE=$1
echo "Getting projects from $CSV_FILE"

#BASE_DIR=$2
#cd ${BASE_DIR}

while IFS=, read -r PROJECT_NAME PROJECT_LINK
do
    if [ -d "${PROJECT_NAME}" ]; then
         echo "${PROJECT_NAME} already exists"
    else
        echo "Getting ${PROJECT_NAME}"
        git clone ${PROJECT_LINK} ${PROJECT_NAME}
    fi
    cd ${PROJECT_NAME}
    COMMIT_HASH=`git log -n 1 --pretty=format:"%H"`

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
