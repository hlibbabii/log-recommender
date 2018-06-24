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

LINES_BEFORE_TO_EXTRACT=1


CLASS='\([Ll]og\|LOG\|[Ll]ogger\|LOGGER\)'
LEVEL='\([Tt]race\|TRACE\|[Dd]ebug\|DEBUG\|[Ii]nfo\|INFO\|[Ww]arn\|WARN\|[Ee]rror\|ERROR\|[Ff]atal\|FATAL\|[Ff]inest\|FINEST\|[Ff]iner\|FINER\|[Ff]ine\|FINE\|[Cc]onfig\|CONFIG\|[Ii]nfo\|INFO\|[Ww]arning\|WARNING\|[Ss]evere\|SEVERE\)'
METHOD_CALL="\($LEVEL\|[Ll]og\|LOG\|debuglog\)$LEVEL*(.*)"
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
GREPPED_LOGS_DIR_ABSPATH=$(abspath "$GREPPED_LOGS_DIR")

cd ${PROJECT_DIR}

TOTAL_PROJECTS=$(cat ${CSV_FILE} | wc -l)
PROJECT_COUNTER=0
while IFS=, read -r PROJECT_NAME PROJECT_LINK
do
    PROJECT_COUNTER=$((PROJECT_COUNTER+1))
    echo "Project $PROJECT_COUNTER out of $TOTAL_PROJECTS..."
    FILE_FOR_OUTPUT="$GREPPED_LOGS_DIR_ABSPATH"/"${PROJECT_NAME}".grepped_logs
    if [ -f "$FILE_FOR_OUTPUT" ]; then
        echo "file ${FILE_FOR_OUTPUT} already exists. Logs have already been extracted"
        continue
    fi
    if [ -d "${PROJECT_DIR}/${PROJECT_NAME}" ]; then
         echo "${PROJECT_NAME} already exists"
    else
        echo "Getting ${PROJECT_NAME}"
        git clone ${PROJECT_LINK} ${PROJECT_NAME}
    fi
    cd ${PROJECT_NAME}
    COMMIT_HASH=$(git log -n 1 --pretty=format:"%H")

    echo grepping logs from ${PROJECT_NAME} ...

    echo ${LINES_BEFORE_TO_EXTRACT} >> ${FILE_FOR_OUTPUT}
    LOG_COUNTER=0
    grep -rn ${REGEX} | while read -r line ; do
        FILE="$(echo $line | sed -n "s/^\(\S*\.\(java\|scala\|groovy\|gradle\|aj\|kt\|py\|js\|c\|cs\|rb\|adoc\|md\|vm\|patch\|R\)\):.*$/\1/p")"
        if [ -f "${FILE}" ]; then
            LOG_COUNTER=$((LOG_COUNTER+1))
            LINE_NUMBER="$(echo $line | sed -n "s/^.*:\([1-9][0-9]*\):.*$/\1/p")"
            BASE_PROJECT_URL="$(echo $PROJECT_LINK | sed -n "s/^\(git\)\(.*\)\.git$/https\2/p")"

            echo "${BASE_PROJECT_URL}/blob/${COMMIT_HASH}/${FILE}${LINE_PREFIX}${LINE_NUMBER}" >> ${FILE_FOR_OUTPUT}

            LOG_LINE=$(sed -n "${LINE_NUMBER}p" ${FILE})

            #extracting context before
            LINES_LEFT_TO_EXTRACT=${LINES_BEFORE_TO_EXTRACT}
            CURRENT_LINE_NUMBER=$((LINE_NUMBER-1))
            for (( i=1; i<=${LINES_BEFORE_TO_EXTRACT}; i++ )); do
                LOG_CONTEXT_BEFORE[${i}]=""
            done
            while [ "${LINES_LEFT_TO_EXTRACT}" -gt "0" ] && [ "${CURRENT_LINE_NUMBER}" -gt "0" ]; do
                CURRENT_LINE=$(sed -n "${CURRENT_LINE_NUMBER}p" ${FILE} | tr -d '\n\r')
                CURRENT_LINE_NUMBER=$((CURRENT_LINE_NUMBER-1))
                if ! [[ "$CURRENT_LINE" =~ ^[[:space:]]*}?[[:space:]]*$ ]]; then
                    LOG_CONTEXT_BEFORE[${LINES_LEFT_TO_EXTRACT}]="${CURRENT_LINE}${LOG_CONTEXT_BEFORE[${LINES_LEFT_TO_EXTRACT}]}"
                    LINES_LEFT_TO_EXTRACT=$((LINES_LEFT_TO_EXTRACT-1))
                elif [[ "$CURRENT_LINE" =~ ^[[:space:]]*}[[:space:]]*$ ]]; then
                    LOG_CONTEXT_BEFORE[${LINES_LEFT_TO_EXTRACT}]="}""${LOG_CONTEXT_BEFORE[${LINES_LEFT_TO_EXTRACT}]}"
                fi
            done

            #extracting context after
            LINES_LEFT_TO_EXTRACT=${LINES_BEFORE_TO_EXTRACT}
            CURRENT_LINE_NUMBER=$((LINE_NUMBER+1))
            LINES_IN_FILE=$(wc -l < "${FILE}")
            for (( i=1; i<=${LINES_BEFORE_TO_EXTRACT}; i++ )); do
                LOG_CONTEXT_AFTER[${i}]=""
            done
            while [ "${LINES_LEFT_TO_EXTRACT}" -gt "0" ] && [ "${CURRENT_LINE_NUMBER}" -le "$LINES_IN_FILE" ]; do
                CURRENT_LINE=$(sed -n "${CURRENT_LINE_NUMBER}p" ${FILE} | tr -d '\n\r')
                CURRENT_LINE_NUMBER=$((CURRENT_LINE_NUMBER+1))
                CURRENT_INDEX=$((LINES_BEFORE_TO_EXTRACT-LINES_LEFT_TO_EXTRACT + 1))
                if ! [[ "$CURRENT_LINE" =~ ^[[:space:]]*}?[[:space:]]*$ ]]; then
                    LINES_LEFT_TO_EXTRACT=$((LINES_LEFT_TO_EXTRACT-1))
                    LOG_CONTEXT_AFTER[${CURRENT_INDEX}]="${LOG_CONTEXT_AFTER[${CURRENT_INDEX}]}${CURRENT_LINE}"
                elif [[ "$CURRENT_LINE" =~ ^[[:space:]]*}[[:space:]]*$ ]]; then
                    LOG_CONTEXT_AFTER[${CURRENT_INDEX}]="${LOG_CONTEXT_AFTER[${CURRENT_INDEX}]}""}"
                fi
            done
            for (( i=1; i<=${LINES_BEFORE_TO_EXTRACT}; i++ )); do
                printf '%s\n' "${LOG_CONTEXT_BEFORE[${i}]}" >> ${FILE_FOR_OUTPUT}
            done
            printf '%s\n'  "${LOG_LINE}" >> ${FILE_FOR_OUTPUT}
            for (( i=1; i<=${LINES_BEFORE_TO_EXTRACT}; i++ )); do
                printf '%s\n'  "${LOG_CONTEXT_AFTER[${i}]}" >> ${FILE_FOR_OUTPUT}
            done

            echo "" >> ${FILE_FOR_OUTPUT}
            echo "" >> ${FILE_FOR_OUTPUT}
        elif ! [ -n "${FILE}" ]; then
            (>&2 echo "Can't extract file name: $line")
        else
            (>&2 echo "File name was probably extracted incorrectly: $line")
        fi
    done
    echo "$LOG_COUNTER logs extracted"
    cd ..
done < ${CSV_FILE}
