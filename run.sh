#!/bin/sh

cd "$(dirname "$0")"
echo '\n==========\n' >> log
date >> log
/usr/local/bin/python3 script.py >> log
