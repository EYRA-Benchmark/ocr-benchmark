#!/bin/bash
set -e

GT_PATH=/data/input/ground_truth
ALGORITHM_OUTPUT_PATH=/data/input/algorithm_output

OUTPUT_PATH=/data/output
TMP_PATH=/data/tmp

mkdir -p $TMP_PATH
mkdir -p $TMP_PATH/ground_truth
mkdir -p $TMP_PATH/algorithm_output
mkdir -p $TMP_PATH/output

tar -xf $GT_PATH -C $TMP_PATH/ground_truth
tar -xf $ALGORITHM_OUTPUT_PATH -C $TMP_PATH/algorithm_output

python -m ocrbenchmark.evaluation.evaluate_all $TMP_PATH/ground_truth $TMP_PATH/algorithm_output > $OUTPUT_PATH
