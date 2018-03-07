BASE_URL="https://github.com/apache/"
LINE_PREFIX="#L"

REGEX='\([Ll]og\|LOG\)\.\([Tt]race\|[Dd]ebug\|[Ii]nfo\|[Ww]arn\|[Ee]rror\\[Ff]atal\)(.*)'

FILE_FOR_OUTPUT=`pwd`/grepped_logs.`date "+%Y%m%d-%H%M%S"`
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
		LOG_STATEMENT="$(echo $line | sed -n "s/^.*:[0-9]*:\(.*\)$/\1/p")"

		echo -e "${LOG_STATEMENT}\n${BASE_URL}${APACHE_PROJECT_NAME}/blob/${COMMIT_HASH}/${FILE}${LINE_PREFIX}${LINE_NUMBER}\n" >> ${FILE_FOR_OUTPUT}
	done
	cd ..
done
