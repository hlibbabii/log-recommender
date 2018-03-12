BASE_URL="https://github.com/apache/"
LINE_PREFIX="#L"

LINES_BEFORE_TO_EXTRACT=4

REGEX='\([Ll]og\|LOG\)\.\([Tt]race\|[Dd]ebug\|[Ii]nfo\|[Ww]arn\|[Ee]rror\\[Ff]atal\)(.*)'

FILE_FOR_OUTPUT=`pwd`/grepped_logs.`date "+%Y%m%d-%H%M%S"`
echo ${LINES_BEFORE_TO_EXTRACT} >> ${FILE_FOR_OUTPUT}
BASE_DIR=$1
cd ${BASE_DIR}

for dir in *; do
	cd ${dir}
	PWD=`pwd`
	APACHE_PROJECT_NAME=`basename "${PWD}"`
	COMMIT_HASH=`git log -n 1 --pretty=format:"%H"`

	echo grepping logs from ${APACHE_PROJECT_NAME} ...
	grep -rn ${REGEX} | while read -r line ; do
		FILE="$(echo $line | sed -n "s/^\(\S*\.\(java\|py\|js\|c\|rb\)\).*$/\1/p")"
		LINE_NUMBER="$(echo $line | sed -n "s/^.*:\([0-9]*\):.*$/\1/p")"
		LOG_STATEMENT="$(echo "$line" | sed -n "s/^.*:[0-9]*:\(.*\)$/\1/p")"

		echo "${LOG_STATEMENT}" >> ${FILE_FOR_OUTPUT}
		echo "${BASE_URL}${APACHE_PROJECT_NAME}/blob/${COMMIT_HASH}/${FILE}${LINE_PREFIX}${LINE_NUMBER}" >> ${FILE_FOR_OUTPUT}
		LINES_BEFORE_RANGE_START=$((LINE_NUMBER-LINES_BEFORE_TO_EXTRACT))
		while [ ${LINES_BEFORE_RANGE_START} -lt "1" ]; do
			echo "" >> ${FILE_FOR_OUTPUT}
			LINES_BEFORE_RANGE_START=$((LINES_BEFORE_RANGE_START + 1))
		done

		LINES_BEFORE_RANGE_END=$((LINE_NUMBER-1))
		PREV_LINE=$(sed -n "${LINES_BEFORE_RANGE_START},${LINES_BEFORE_RANGE_END}p" ${FILE})
		echo -e "${PREV_LINE}\n\n" >> ${FILE_FOR_OUTPUT}
	done
	cd ..
done
