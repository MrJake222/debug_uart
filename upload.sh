#!/bin/bash

#./debug.py -p /dev/ttyACM1 -b 115200 run -n
./debug.py -p /dev/ttyACM1 -b 115200 write --ihex $1 -v
./debug.py -p /dev/ttyACM1 -b 115200 reset
#./debug.py -p /dev/ttyACM1 -b 115200 run -f
