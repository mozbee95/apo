#!/bin/bash

amixer -c 1 sset PCM 100%
aplay -D plughw:CARD=Headphones /usr/share/sounds/alsa/Front_Center.wav
date | tee /home/lilou/Documents/apo/test_son_startup.log
