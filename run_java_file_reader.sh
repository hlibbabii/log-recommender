#!/usr/bin/env bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -r|--raw-dataset)
    RAW_DATASET="$2"
    shift 2
    ;;
    -d|--dest-dataset)
    DEST_DATASET="$2"
    shift 2
    ;;
    -f|--folder)
    FOLDER="$2"
    shift 2
    ;;
    -c|--chunk)
    CHUNK_FROM="$2"
    CHUNK_TO="$3"
    shift 3
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

cd log_recommender
PYTHON=$(which python)
echo "Using $PYTHON ..."

for (( c=$CHUNK_FROM; c<=$CHUNK_TO; c++ ))
do
    $PYTHON dataprep/read_from_java_files.py --raw-dataset $RAW_DATASET --dest-dataset $DEST_DATASET --folder $FOLDER --chunk $c &
done

cd ..