#!/bin/bash

OPTS="--d32 -p /dev/ttyACM1 -b 1000000"

#./debug.py $OPTS run -n

./debug.py $OPTS write --ihex $1 -v
./debug.py $OPTS reset

#./debug.py $OPTS run -f
