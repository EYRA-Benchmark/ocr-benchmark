#!/bin/bash
set -e

INPUT_PATH=/data/input/test_data
OUTPUT_PATH=/data/output
TMP_PATH=/data/tmp
mkdir -p $TMP_PATH
mkdir -p $TMP_PATH/input
mkdir -p $TMP_PATH/output

tar -xf $INPUT_PATH -C $TMP_PATH/input

python main.py $TMP_PATH/input $TMP_PATH/output

tar cf $OUTPUT_PATH -C $TMP_PATH/output .
