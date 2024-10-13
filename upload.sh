#!/bin/bash

O=$PWD
P=`readlink "$0"`
P=`dirname "$P"`
cd "$P"

if [[ $# != 1 ]]; then
	echo "Usage: upload.sh [hex name]"
	exit 1
fi

OPTS="--d32 -p /dev/ttyACM1 -b 1000000"

#./debug.py $OPTS run -n

./debug.py $OPTS write --ihex $1 -v
./debug.py $OPTS reset

#./debug.py $OPTS run -f
