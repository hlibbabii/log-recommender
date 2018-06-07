#!/usr/bin/env bash

function copyLines() {
    if ! [[ "$#" -eq 5 ]]; then
        echo "The number of args is $#, not 5. Terminating copyLines function"
        return 1
    fi

    FROM="$1"
    TO="$2"
    HOW_MANY="$3"
    OUT_OF="$4"
    HOW_MANY_TIMES="$5"

    rm ${TO}

    for (( i=0; i<$HOW_MANY_TIMES; i++ ))
    do
        OFFSET=$(( $i * $OUT_OF ))
        START=$(( $OFFSET + 1 ))
        END=$(( $OFFSET + $HOW_MANY ))
        less $FROM | sed -n "${START},${END}p" >> $TO
    done
}

RECALCULATE_WORD2VEC=0
DISTANCE_METRIC='jaccard'
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -r|--recalculate-word2vec)
    RECALCULATE_WORD2VEC=1
    shift
    ;;
    -d|--distance-metric)
    DISTANCE_METRIC="$2"
    shift 2
    ;;
    -a|--autoencode-location)
    AUTOENCODE_LOCATION="$2"
    shift 2
    ;;
    -n|--word2vec-n-vector-dimensions)
    WORD_TO_VEC_N_VECTOR_DIMENSIONS="$2"
    shift 2
    ;;
    -c|--classes-file)
    OUTPUT_CLASSES_FILE="$2"
    shift 2
    ;;
    -w|--word2vec-out-file)
    WORD_TO_VEC_OUT_FILE="$2"
    shift 2
    ;;
    -s|--max-sentence-length-rae)
    MAX_SENTENCE_LENGTH_RAE="$2"
    shift 2
    ;;
    -i|--max-iter-rae)
    MAX_ITER_RAE="$2"
    shift 2
    ;;
    -c|--min-word-occurencies)
    MIN_WORD_OCCURENCIES="$2"
    shift 2
    ;;
    -l|--n-logs-pick-for-rae-from-each-class)
    N_LOGS_PICK_FOR_RAE_FROM_EACH_CLASS="$2"
    shift 2
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [ "$RECALCULATE_WORD2VEC" -eq "1" ] && [ "$DISTANCE_METRIC" = "word2vec" ]; then
    cd "${AUTOENCODE_LOCATION}/bin"
    CMD="./run_word2vec.sh ../data ../out/word2vec/ $WORD_TO_VEC_N_VECTOR_DIMENSIONS"
    echo "Running $CMD"
    eval "$CMD"
    ERR_CODE=$?
    if [ $ERR_CODE -ne 0 ]; then
        exit 1
    fi
    echo "$(pwd)"
    mv ../data/corpus.src ../data/corpus.src1

    IFS=',' read -ra classes < "$OUTPUT_CLASSES_FILE"
    N_CLASSES=${#classes[@]}
    copyLines ../data/corpus.src1 ../data/corpus.src $N_LOGS_PICK_FOR_RAE_FROM_EACH_CLASS $MIN_WORD_OCCURENCIES $N_CLASSES

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

    rm ../../data/corpus.src
    mv ../../data/corpus.src1 ../../data/corpus.src
else
    echo "Not recalculating word2vec distances"
fi