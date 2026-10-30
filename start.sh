#!/bin/bash
sleep 7
cd /home/pi/Documents/apo
/usr/bin/python3 main.py > /home/pi/Documents/apo/apo_telephone.log 2>&1
