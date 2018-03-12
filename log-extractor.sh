BASE_URL="https://github.com/apache/"
LINE_PREFIX="#L"

LINES_BEFORE_TO_EXTRACT=4

REGEX='\([Ll]og\|LOG\)\.\([Tt]race\|[Dd]ebug\|[Ii]nfo\|[Ww]arn\|[Ee]rror\\[Ff]atal\)(.*)'

FILE_FOR_OUTPUT=`pwd`/grepped_logs.`date "+%Y%m%d-%H%M%S"`
echo "Extracting logs to ${FILE_FOR_OUTPUT}"
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
		FILE="$(echo $line | sed -n "s/^\(\S*\.\(java\|scala\|groovy\|py\|js\|c\|rb\)\).*$/\1/p")"
		if [ -n "${FILE}" ]; then
			LINE_NUMBER="$(echo $line | sed -n "s/^.*:\([1-9][0-9]*\):.*$/\1/p")"

			echo "${BASE_URL}${APACHE_PROJECT_NAME}/blob/${COMMIT_HASH}/${FILE}${LINE_PREFIX}${LINE_NUMBER}" >> ${FILE_FOR_OUTPUT}
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
done
