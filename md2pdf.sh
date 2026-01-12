#!/bin/bash

# Check if an input file was provided
if [ -z "$1" ]; then
  echo "Usage: ./md2pdf.sh <input_file.md>"
  exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${INPUT_FILE%.*}.pdf"

# Run pandoc command
pandoc "$INPUT_FILE" \
  -o "$OUTPUT_FILE" \
  --pdf-engine=pdflatex \
  --template=cosai-template.tex \
  --syntax-highlighting=idiomatic

if [ $? -eq 0 ]; then
  echo "Successfully converted $INPUT_FILE to $OUTPUT_FILE"
else
  echo "Error converting $INPUT_FILE to PDF"
  exit 1
fi
