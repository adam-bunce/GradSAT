#!/bin/bash


# List all courses in .csv

set -u

if [ $# -ne 2 ]; then
    echo "Usage: $0 input.csv output.txt"
    exit 1
fi

INPUT_FILE=$1
OUTPUT_FILE=$2

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE does not exist"
    exit 1
fi

# clear file
echo "" > "$OUTPUT_FILE"

while IFS="," read -r col1 col2 col3 col4
do
    echo "\"$col2$col3\"," >> "$OUTPUT_FILE"
done < "$INPUT_FILE"


