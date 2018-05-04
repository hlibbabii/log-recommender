#!/usr/bin/env bash

START=$(date +%s.%N)

#################### Tunable params
#==
MIN_WORD_OCCURENCIES=1000
MIN_WORD_FREQUNCY=0.0002
MIN_FOUND_IN_PROJECTS_FREQUENCY=0.5
MIN_LOG_NUMBER_PER_PROJECT=100

#==word2vec
WORD_TO_VEC_N_VECTOR_DIMENSIONS=5
MAX_ITER_RAE=10
MAX_SENTENCE_LENGTH_RAE=50

#==clusterization
DISTANCE_METRIC='word2vec' #available options: 'word2vec', 'jaccard'


################### Non tunable params
PATH_TO_PYTHON='/home/hlib/dev/bz-hackathon/env/bin/python'
PATH_TO_PROJECT="/home/hlib/thesis/log-recommender"

GENERATED_STATS_FOLDER="$PATH_TO_PROJECT/generated_stats"
PATH_TO_CACHED_PROJECTS="$PATH_TO_PROJECT/.Projects"
SPREADSHEET_OUTPUT_DIR_NAME="$PATH_TO_PROJECT/logs"

OUTPUT_CORPUS_FILE="$PATH_TO_PROJECT/../gengram/corpus.txt"
PREPROCESSED_LOG_FILE="$PATH_TO_PROJECT/pplogs.pkl"
CLASSIFIED_LOG_FILE="$PATH_TO_PROJECT/classified_logs.pkl"
LOGS_FOR_TRAINING_FILE="$PATH_TO_PROJECT/logs_for_training.pkl"

PROJECT_STATS_FILE="${GENERATED_STATS_FOLDER}/project_stats.csv"
OUTPUT_FREQUENCIES_FILE="${GENERATED_STATS_FOLDER}/frequencies.csv"
OUTPUT_CLASSES_FILE="$PATH_TO_PROJECT/classes.csv"
INTERESTING_CONTEXT_WORDS_FILE="$PATH_TO_PROJECT/context_words.csv"
OUTPUT_FIRST_WORD_FREQUENCIES_FILE="${GENERATED_STATS_FOLDER}/frequencies_first_word.csv"
OUTPUT_DISTRIBUTION_BY_LEVELS_FILE="${GENERATED_STATS_FOLDER}/level_distribution.csv"
OUTPUT_DISTRIBUTION_BY_N_VARS_FILE="${GENERATED_STATS_FOLDER}/n_vars_distribution.csv"
OUTPUT_PEARSONS_FILE="$GENERATED_STATS_FOLDER/output_pearons.csv"
K_MEANS_CLUSTERING_STATS_FILE="$GENERATED_STATS_FOLDER/k_means_clustering_stats.csv"

AUTOENCODE_LOCATION="$PATH_TO_PROJECT/../AutoenCODE"

OUTPUT_CONTEXT_CORPUS_FILE="${AUTOENCODE_LOCATION}/data/corpus.src"
AUTOENCODE_DIST_FILE="${AUTOENCODE_LOCATION}/out/rae/corpus.dist.matrix.csv"
WORD_TO_VEC_OUT_FILE="${AUTOENCODE_LOCATION}/out/word2vec/word2vec.out"

BINARY_CONTEXT_VECTOR_FILE="$PATH_TO_PROJECT/binary_context_vectors.dat"
CONTEXT_VECTOR_FILE="$PATH_TO_PROJECT/context_vectors.dat"
LOGS_FROM_MAJOR_CLASSES_FILE="$PATH_TO_PROJECT/major_classes_logs.pkl"

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

if [ ! -z "$PREPROCESS" ]; then
    LOG_PREPROCESSOR_SCRIPT="$PATH_TO_PYTHON log_recommender/log_preprocessor.py"
    LOG_PREPROCESSOR_SCRIPT="$LOG_PREPROCESSOR_SCRIPT --min-log-number-per-project $MIN_LOG_NUMBER_PER_PROJECT"
    LOG_PREPROCESSOR_SCRIPT="$LOG_PREPROCESSOR_SCRIPT --output-corpus-file $OUTPUT_CORPUS_FILE"
    LOG_PREPROCESSOR_SCRIPT="$LOG_PREPROCESSOR_SCRIPT --output-context-corpus-file $OUTPUT_CONTEXT_CORPUS_FILE"
    LOG_PREPROCESSOR_SCRIPT="$LOG_PREPROCESSOR_SCRIPT --output-preprocessed-log-file $PREPROCESSED_LOG_FILE"
    LOG_PREPROCESSOR_SCRIPT="$LOG_PREPROCESSOR_SCRIPT --output-project-stats-file $PROJECT_STATS_FILE"

    echo "Running $LOG_PREPROCESSOR_SCRIPT"
    eval "$LOG_PREPROCESSOR_SCRIPT"
    ERR_CODE=$?
    if [ $ERR_CODE -ne 0 ]; then
        exit 1
    fi
else
    echo "Skipping log preprocessing: using existing pplog file"
fi

if ! [ -d "$SPREADSHEET_OUTPUT_DIR_NAME" ]; then
    mkdir "$SPREADSHEET_OUTPUT_DIR_NAME"
fi
FREQ_SCRIPT="$PATH_TO_PYTHON $PATH_TO_PROJECT/log_recommender/freqs.py"
FREQ_SCRIPT="$FREQ_SCRIPT --write-to-classification-spreadsheet $UPLOAD_TO_GOOGLE"

FREQ_SCRIPT="$FREQ_SCRIPT --min-log-number-per-project $MIN_LOG_NUMBER_PER_PROJECT"
FREQ_SCRIPT="$FREQ_SCRIPT --min-word-occurencies $MIN_WORD_OCCURENCIES"
FREQ_SCRIPT="$FREQ_SCRIPT --min-word-frequency $MIN_WORD_FREQUNCY"
FREQ_SCRIPT="$FREQ_SCRIPT --min-found-in-projects-frequency $MIN_FOUND_IN_PROJECTS_FREQUENCY"

FREQ_SCRIPT="$FREQ_SCRIPT --input-preprocessed-log-file $PREPROCESSED_LOG_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-classified-log-file $CLASSIFIED_LOG_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --input-project-stats-file $PROJECT_STATS_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-frequencies-file $OUTPUT_FREQUENCIES_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-first-word-frequencies-file $OUTPUT_FIRST_WORD_FREQUENCIES_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-distribution-by-levels-file $OUTPUT_DISTRIBUTION_BY_LEVELS_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-distribution-by-n_vars-file $OUTPUT_DISTRIBUTION_BY_N_VARS_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-classes-file $OUTPUT_CLASSES_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --output-interesting-words-from-context-file $INTERESTING_CONTEXT_WORDS_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --spreadsheet-output-dir-name $SPREADSHEET_OUTPUT_DIR_NAME"
FREQ_SCRIPT="$FREQ_SCRIPT --binary-context-vector-file $BINARY_CONTEXT_VECTOR_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --context-vector-file $CONTEXT_VECTOR_FILE"
FREQ_SCRIPT="$FREQ_SCRIPT --logs-from-major-classes-file $LOGS_FROM_MAJOR_CLASSES_FILE"



if [ "$UPLOAD_TO_GOOGLE" -eq "1" ]; then
    echo "Uploading csvs to google..."
    UPLOAD_TO_GOOGLE_SCRIPT="$PATH_TO_PYTHON upload_to_google.py $SPREADSHEET_OUTPUT_DIR_NAME"
    eval "$UPLOAD_TO_GOOGLE_SCRIPT"
    ERR_CODE=$?
    if [ $ERR_CODE -ne 0 ]; then
        exit 1
    fi
fi

echo "Running $FREQ_SCRIPT"
eval "$FREQ_SCRIPT"
ERR_CODE=$?
if [ $ERR_CODE -ne 0 ]; then
    exit 1
fi

CLUSTER_PREP_SCRIPT="$PATH_TO_PYTHON log_recommender/cluster.py"
CLUSTER_PREP_SCRIPT="$CLUSTER_PREP_SCRIPT --logs-from-major-classes-file $LOGS_FROM_MAJOR_CLASSES_FILE"
CLUSTER_PREP_SCRIPT="$CLUSTER_PREP_SCRIPT --classes-file $OUTPUT_CLASSES_FILE"
CLUSTER_PREP_SCRIPT="$CLUSTER_PREP_SCRIPT --binary-context-vector-file $BINARY_CONTEXT_VECTOR_FILE"
CLUSTER_PREP_SCRIPT="$CLUSTER_PREP_SCRIPT --output-pearson-file $OUTPUT_PEARSONS_FILE"
CLUSTER_PREP_SCRIPT="$CLUSTER_PREP_SCRIPT --k-means-clustering-stats-file $K_MEANS_CLUSTERING_STATS_FILE"

echo "Running $CLUSTER_PREP_SCRIPT"
eval "$CLUSTER_PREP_SCRIPT"
ERR_CODE=$?
if [ $ERR_CODE -ne 0 ]; then
    exit 1
fi

if [ "$RECALCULATE_WORD2VEC" -eq "1" ] && [ "$DISTANCE_METRIC" = "word2vec" ]; then
    cd "${AUTOENCODE_LOCATION}/bin"
    CMD="./run_word2vec.sh ../data ../out/word2vec/ $WORD_TO_VEC_N_VECTOR_DIMENSIONS"
    echo "Running $CMD"
    eval "$CMD"
    ERR_CODE=$?
    if [ $ERR_CODE -ne 0 ]; then
        exit 1
    fi

    CMD="./run_postprocess.py --w2v $WORD_TO_VEC_OUT_FILE --src ../data"
    echo "Running $CMD"
    eval "$CMD"
    ERR_CODE=$?
    if [ $ERR_CODE -ne 0 ]; then
        exit 1
    fi

    cd rae
    CMD="./run_rae.sh ../../out/word2vec ../../out/rae $MAX_SENTENCE_LENGTH_RAE $MAX_ITER_RAE"
    echo "Running $CMD"
    eval "$CMD"
    ERR_CODE=$?
    if [ $ERR_CODE -ne 0 ]; then
        exit 1
    fi
else
    echo "Not recalculating word2vec distances"
fi

HCLUSTERING_SCRIPT="$PATH_TO_PYTHON log_recommender/hclustering.py --autoencode-dist-file $AUTOENCODE_DIST_FILE"
HCLUSTERING_SCRIPT="$HCLUSTERING_SCRIPT --distance-metric $DISTANCE_METRIC"
HCLUSTERING_SCRIPT="$HCLUSTERING_SCRIPT --logs-from-major-classes-file $LOGS_FROM_MAJOR_CLASSES_FILE > dendrogram.txt"

cd "$PATH_TO_PROJECT"
echo "Running $HCLUSTERING_SCRIPT"
eval "$HCLUSTERING_SCRIPT"
ERR_CODE=$?
if [ $ERR_CODE -ne 0 ]; then
    exit 1
fi

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "Execution took $DIFF"

VISUALIZE_SCRIPT="$PATH_TO_PYTHON log_recommender/visual.py --autoencode-dist-file $WORD_TO_VEC_OUT_FILE"
echo "Running $VISUALIZE_SCRIPT"
eval "$VISUALIZE_SCRIPT"
ERR_CODE=$?
if [ $ERR_CODE -ne 0 ]; then
    exit 1
fi