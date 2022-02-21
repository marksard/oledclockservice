#!/usr/bin/bash
basedir=$(cd $(dirname $0); pwd)
sudo ln -s ${basedir}/oledclock.service /etc/systemd/system/oledclock.service
