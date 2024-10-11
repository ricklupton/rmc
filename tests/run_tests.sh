#!/bin/bash

# This script is made to run from the ./src directory

# We need the directory of this script to find the test files
# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )


echo "Test the creation of Markdown files from RM files"
for FILE in $SCRIPT_DIR/rm/*.rm; do
  python3 -m rmc.cli -t markdown $FILE > /dev/null
  FAILED=$?
  if [ $FAILED -eq 1 ]; then
      echo "TEST FAILED"
      echo "python3 -m rmc.cli -t markdown $FILE > /dev/null"
      exit
  fi
done

echo "Test the creation of SVG files from RM files"
for FILE in $SCRIPT_DIR/rm/*.rm; do
  python3 -m rmc.cli -t svg $FILE > /dev/null
  FAILED=$?
  if [ $FAILED -eq 1 ]; then
      echo "TEST FAILED"
      echo "python3 -m rmc.cli -t svg $FILE > /dev/null"
      exit
  fi
done

echo "Test the creation of PDF files from RM files"
for FILE in $SCRIPT_DIR/rm/*.rm; do
  python3 -m rmc.cli -t pdf $FILE > /dev/null
  FAILED=$?
  if [ $FAILED -eq 1 ]; then
      echo "TEST FAILED"
      echo "python3 -m rmc.cli -t pdf $FILE > /dev/null"
      exit
  fi
done

