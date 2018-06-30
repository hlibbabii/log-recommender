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

LINES_BEFORE_TO_EXTRACT=2
SNIPPET_SIZE=$((LINES_BEFORE_TO_EXTRACT + LINES_BEFORE_TO_EXTRACT + 1))


CLASS='\([Ll]og\|LOG\|[Ll]ogger\|LOGGER\)'
LEVEL='\([Tt]race\|TRACE\|[Dd]ebug\|DEBUG\|[Ii]nfo\|INFO\|[Ww]arn\|WARN\|[Ee]rror\|ERROR\|[Ff]atal\|FATAL\|[Ff]inest\|FINEST\|[Ff]iner\|FINER\|[Ff]ine\|FINE\|[Cc]onfig\|CONFIG\|[Ii]nfo\|INFO\|[Ww]arning\|WARNING\|[Ss]evere\|SEVERE\)'
METHOD_CALL="\($LEVEL\|\([Ll]og\|LOG\)$LEVEL\?\|debuglog\)(.*)"
SOUT="System\.\(out\|err\)\.println(.*)"
REGEX="\($CLASS\.$METHOD_CALL\|$SOUT\|^\(\\s\)*$METHOD_CALL\)"


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
PROJECT_DIR_ABSPATH=$( abspath "$PROJECT_DIR" )

DEFAULT_GREPPED_LOGS_DIR="../.Logs"
if [ -z "$3" ]; then
    GREPPED_LOGS_DIR=${DEFAULT_GREPPED_LOGS_DIR}
else
    GREPPED_LOGS_DIR=$3
fi

echo "Extracting logs to ${GREPPED_LOGS_DIR}"
if [ -d "$GREPPED_LOGS_DIR" ]; then
    echo "Logs directory ${GREPPED_LOGS_DIR} found"
else
    echo "Logs directory ${GREPPED_LOGS_DIR} NOT found. Creating it..."
    mkdir "${GREPPED_LOGS_DIR}"
fi
GREPPED_LOGS_DIR_ABSPATH=$( abspath "$GREPPED_LOGS_DIR" )

cd ${PROJECT_DIR_ABSPATH}

TOTAL_PROJECTS=$(cat ${CSV_FILE} | wc -l)
PROJECT_COUNTER=0
GREP_LINE_REGEX="^\(\S\+\.\S\+\)[:-]\([0-9]\+\)[:-]\(.*\)\$"
GREP_RESULT_SEPARATOR_REGEX="^\-\-\$"
LINES_EXTRACTED="0"a
while IFS=, read -r PROJECT_NAME PROJECT_LINK
do
    PROJECT_COUNTER=$((PROJECT_COUNTER+1))
    echo "Project $PROJECT_COUNTER out of $TOTAL_PROJECTS..."
    FILE_FOR_OUTPUT="$GREPPED_LOGS_DIR_ABSPATH"/"${PROJECT_NAME}".grepped_logs
    if [ -f "$FILE_FOR_OUTPUT" ]; then
        echo "file ${FILE_FOR_OUTPUT} already exists. Logs have already been extracted"
        continue
    fi
    echo "Checking if dir exists: ${PROJECT_DIR_ABSPATH}/${PROJECT_NAME}"
    if [ -d "${PROJECT_DIR_ABSPATH}/${PROJECT_NAME}" ]; then
         echo "${PROJECT_NAME} already exists"
    else
        echo "Getting ${PROJECT_NAME}"
        git clone ${PROJECT_LINK} "${PROJECT_DIR_ABSPATH}/${PROJECT_NAME}"
    fi
    if [ -d "${PROJECT_DIR_ABSPATH}/${PROJECT_NAME}" ]; then
        cd ${PROJECT_NAME}
    else
        echo "Directory ${PROJECT_DIR_ABSPATH}/${PROJECT_NAME} does not exist. The project must have failed to be cloned."
        continue
    fi
    COMMIT_HASH=$(git log -n 1 --pretty=format:"%H")

    echo grepping logs from ${PROJECT_NAME} ...

    echo ${LINES_BEFORE_TO_EXTRACT} >> ${FILE_FOR_OUTPUT}
    LOG_COUNTER="0"
    grep -rn -B ${LINES_BEFORE_TO_EXTRACT} -A ${LINES_BEFORE_TO_EXTRACT} ${REGEX} | while read -r line ; do
        if [[ "$line" =~ $GREP_RESULT_SEPARATOR_REGEX ]]; then
            while [ $LINES_EXTRACTED -lt $SNIPPET_SIZE ]; do
                #add padding
                echo "" >> ${FILE_FOR_OUTPUT}
                LINES_EXTRACTED=$((LINES_EXTRACTED+1))
            done
            LINES_EXTRACTED="0"
            echo "" >> ${FILE_FOR_OUTPUT}
            echo "" >> ${FILE_FOR_OUTPUT}
            continue
        elif [[ $LINES_EXTRACTED -eq $SNIPPET_SIZE ]]; then
           #just skip
           :
        elif [[ $LINES_EXTRACTED -eq "0" ]]; then
            FILE="$(echo $line | sed -n "s/$GREP_LINE_REGEX/\1/p")"
            LOG_COUNTER=$((LOG_COUNTER+1))
            LINE_NUMBER="$(echo $line | sed -n "s/$GREP_LINE_REGEX/\2/p")"
            LOG_LINE="$(echo $line | sed -n "s/$GREP_LINE_REGEX/\3/p")"

            BASE_PROJECT_URL="$(echo $PROJECT_LINK | sed -n "s/^\(git\)\(.*\)\.git$/https\2/p")"

            echo "${BASE_PROJECT_URL}/blob/${COMMIT_HASH}/${FILE}${LINE_PREFIX}${LINE_NUMBER}" >> ${FILE_FOR_OUTPUT}
            printf '%s\n'  "${LOG_LINE}" >> ${FILE_FOR_OUTPUT}
            LINES_EXTRACTED="1"
        else
            LOG_LINE="$(echo "$line" | sed -n "s/$GREP_LINE_REGEX/\3/p")"
            printf '%s\n'  "${LOG_LINE}" >> ${FILE_FOR_OUTPUT}
            LINES_EXTRACTED=$((LINES_EXTRACTED+1))
        fi
    done
    echo "$LOG_COUNTER logs extracted"
    cd ..
done < ${CSV_FILE}
echo "" >> ${FILE_FOR_OUTPUT}
echo "" >> ${FILE_FOR_OUTPUT}
