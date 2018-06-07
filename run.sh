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

UPLOAD_TO_GOOGLE=0
RECALCULATE_WORD2VEC=0
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

PREPROCESS=""
case $key in
    -e|--extract-logs)
    PROJECT_LIST_FILE="$2"
    shift 2
    ;;
    -u|--upload-to-google)
    UPLOAD_TO_GOOGLE=1
    shift
    ;;
    -p|--preprocess)
    PREPROCESS=1
    shift
    ;;
    -r|--recalculate-word2vec)
    RECALCULATE_WORD2VEC=1
    shift
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

if [ -n "$PROJECT_LIST_FILE" ]; then
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

#if [ ! -z "$PREPROCESS" ]; then
#    LOG_PREPROCESSOR_SCRIPT="$PATH_TO_PYTHON log_recommender/log_preprocessor.py"
#    LOG_PREPROCESSOR_SCRIPT="$LOG_PREPROCESSOR_SCRIPT --min-log-number-per-project $MIN_LOG_NUMBER_PER_PROJECT"
#
#    echo "Running $LOG_PREPROCESSOR_SCRIPT\n"
#    eval "$LOG_PREPROCESSOR_SCRIPT"
#    ERR_CODE=$?
#    if [ $ERR_CODE -ne 0 ]; then
#        exit 1
#    fi
#else
#    echo "Skipping log preprocessing: using existing pplog file"
#fi

#if ! [ -d "$SPREADSHEET_OUTPUT_DIR_NAME" ]; then
#    mkdir "$SPREADSHEET_OUTPUT_DIR_NAME"
#fi
#FREQ_SCRIPT="$PATH_TO_PYTHON $PATH_TO_PROJECT/log_recommender/classify_and_select_major_logs.py"
#FREQ_SCRIPT="$FREQ_SCRIPT --write-to-classification-spreadsheet $UPLOAD_TO_GOOGLE"
#
#FREQ_SCRIPT="$FREQ_SCRIPT --min-log-number-per-project $MIN_LOG_NUMBER_PER_PROJECT"
#FREQ_SCRIPT="$FREQ_SCRIPT --min-word-occurencies $MIN_WORD_OCCURENCIES"
#FREQ_SCRIPT="$FREQ_SCRIPT --min-word-frequency $MIN_WORD_FREQUNCY"
#FREQ_SCRIPT="$FREQ_SCRIPT --min-found-in-projects-frequency $MIN_FOUND_IN_PROJECTS_FREQUENCY"
#
#FREQ_SCRIPT="$FREQ_SCRIPT --spreadsheet-output-dir-name $SPREADSHEET_OUTPUT_DIR_NAME"
#FREQ_SCRIPT="$FREQ_SCRIPT --marked_up_contexts-file $MARKED_UP_CONTEXTS_FILE"
#FREQ_SCRIPT="$FREQ_SCRIPT --context-lines-to-consider $CONTEXT_LINES_TO_CONSIDER"
#FREQ_SCRIPT="$FREQ_SCRIPT --output-corpus-file $OUTPUT_CORPUS_FILE"
#FREQ_SCRIPT="$FREQ_SCRIPT --output-context-corpus-file $OUTPUT_CONTEXT_CORPUS_FILE"
#FREQ_SCRIPT="$FREQ_SCRIPT --context-index-file $CONTEXT_INDEX_FILE"


#if [ "$UPLOAD_TO_GOOGLE" -eq "1" ]; then
#    echo "Uploading csvs to google..."
#    UPLOAD_TO_GOOGLE_SCRIPT="$PATH_TO_PYTHON $PATH_TO_PROJECT/log_recommender/upload_to_google.py $SPREADSHEET_OUTPUT_DIR_NAME"
#    eval "$UPLOAD_TO_GOOGLE_SCRIPT"
#    ERR_CODE=$?
#    if [ $ERR_CODE -ne 0 ]; then
#        exit 1
#    fi
#fi

#echo "Running $FREQ_SCRIPT"
#echo ""
#eval "$FREQ_SCRIPT"
#ERR_CODE=$?
#if [ $ERR_CODE -ne 0 ]; then
#    exit 1
#fi

#asciidoctor -b html5 "$MARKED_UP_CONTEXTS_FILE"

#CLUSTER_PREP_SCRIPT="$PATH_TO_PYTHON log_recommender/cluster.py"

#echo "Running $CLUSTER_PREP_SCRIPT"
#echo ""
#eval "$CLUSTER_PREP_SCRIPT"
#ERR_CODE=$?
#if [ $ERR_CODE -ne 0 ]; then
#    exit 1
#fi

#if [ "$RECALCULATE_WORD2VEC" -eq "1" ] && [ "$DISTANCE_METRIC" = "word2vec" ]; then
#    cd "${AUTOENCODE_LOCATION}/bin"
#    CMD="./run_word2vec.sh ../data ../out/word2vec/ $WORD_TO_VEC_N_VECTOR_DIMENSIONS"
#    echo "Running $CMD"
#    eval "$CMD"
#    ERR_CODE=$?
#    if [ $ERR_CODE -ne 0 ]; then
#        exit 1
#    fi
#
#    mv ../data/corpus.src ../data/corpus.src1
#    IFS=',' read -ra classes < "$OUTPUT_CLASSES_FILE"
#    N_CLASSES=${#classes[@]}
#    copyLines ../data/corpus.src1 ../data/corpus.src $N_LOGS_PICK_FOR_RAE_FROM_EACH_CLASS $MIN_WORD_OCCURENCIES $N_CLASSES
#
#    CMD="./run_postprocess.py --w2v $WORD_TO_VEC_OUT_FILE --src ../data"
#    echo "Running $CMD"
#    eval "$CMD"
#    ERR_CODE=$?
#    if [ $ERR_CODE -ne 0 ]; then
#        exit 1
#    fi
#
#    cd rae
#    CMD="./run_rae.sh ../../out/word2vec ../../out/rae $MAX_SENTENCE_LENGTH_RAE $MAX_ITER_RAE"
#    echo "Running $CMD"
#    eval "$CMD"
#    ERR_CODE=$?
#    if [ $ERR_CODE -ne 0 ]; then
#        exit 1
#    fi
#
#    rm ../../data/corpus.src
#    mv ../../data/corpus.src1 ../../data/corpus.src
#else
#    echo "Not recalculating word2vec distances"
#fi

#HCLUSTERING_SCRIPT="$PATH_TO_PYTHON log_recommender/hclustering.py --autoencode-dist-file $AUTOENCODE_DIST_FILE"
#HCLUSTERING_SCRIPT="$HCLUSTERING_SCRIPT --distance-metric $DISTANCE_METRIC > dendrogram.txt"
#
#cd "$PATH_TO_PROJECT"
#echo "Running $HCLUSTERING_SCRIPT"
#echo ""
#eval "$HCLUSTERING_SCRIPT"
#ERR_CODE=$?
#if [ $ERR_CODE -ne 0 ]; then
#    exit 1
#fi

#VISUALIZE_SCRIPT="$PATH_TO_PYTHON log_recommender/visual.py --autoencode-dist-file $AUTOENCODE_DIST_FILE"
#VISUALIZE_SCRIPT="$VISUALIZE_SCRIPT --logs-from-major-classes-file $LOGS_FROM_MAJOR_CLASSES_FILE"
#VISUALIZE_SCRIPT="$VISUALIZE_SCRIPT --context-corpus-file $OUTPUT_CONTEXT_CORPUS_FILE"
#VISUALIZE_SCRIPT="$VISUALIZE_SCRIPT --n-logs-pick-for-rae-from-each-class $N_LOGS_PICK_FOR_RAE_FROM_EACH_CLASS"
#VISUALIZE_SCRIPT="$VISUALIZE_SCRIPT --min-word-occurencies $MIN_WORD_OCCURENCIES"
#VISUALIZE_SCRIPT="$VISUALIZE_SCRIPT --context-index-file $CONTEXT_INDEX_FILE"
#VISUALIZE_SCRIPT="$VISUALIZE_SCRIPT --word-to-vec-out-file $WORD_TO_VEC_OUT_FILE"
#echo "Running $VISUALIZE_SCRIPT"
#echo ""
#eval "$VISUALIZE_SCRIPT"
#ERR_CODE=$?
#if [ $ERR_CODE -ne 0 ]; then
#    exit 1
#fi
