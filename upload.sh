#!/bin/bash

# exit on failing command
set -e

O=$PWD
P=`readlink "$0"`
P=`dirname "$P"`
cd "$P"

if [[ $# != 1 ]]; then
	echo "Usage: upload.sh [hex name]"
	exit 1
fi

PORT="/dev/ttyACM1"
#PORT="/dev/ttyACM2"

#BAUD=9600
#BAUD=115200
#BAUD=500000
#BAUD=650000
BAUD=1000000

OPTS="--d32 -p $PORT -b $BAUD"

#./debug.py $OPTS run -n

./debug.py $OPTS write --ihex $O/$1 -v
./debug.py $OPTS reset

#./debug.py $OPTS run -f
