# Name: Multi information clock main
# Author: marksard
# Version: 2.0
# Python 3.6 or later (maybe)
# Require Device: Raspberry PI 1 Model B+ or later.
#                 Temperature and humidiry sensor BME280
#                   datasheet (http://akizukidenshi.com/download/ds/bosch/BST-BME280_DS001-10.pdf)
#                 WinSTAR OLED Display 20x4 WEH002004A (using controller WS0010)
#                   datasheet (http://blog.digit-parts.com/pdf/ws0010.pdf)

# ***************************
from subprocess import Popen, PIPE
import threading
from queue import Queue
import time
import datetime
import pytz
import psutil
import os
import pwd

import bme280
import weh002004a
import bigdigit

# ***************************

disp = weh002004a.WEH002004A()
sphere = bme280.BME280()

def main():
    week_names = ['Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.']
    disp_state = 0
    cpu_temp = get_cpu_temperatur_status()
    ntp_state = Queue()
    get_ntp_status(ntp_state)
    last_ntp_string = ''

    last = datetime.datetime.min
    while True:
        now = datetime.datetime.now()
        if now.second == last.second:
            time.sleep(0.2)
            continue

        last = now

        # status change timing
        if now.second == 15 or now.second == 35 or now.second == 55:
            disp_state += 1
            if disp_state >= 2:
                disp_state = 0

        # kick thread
        if now.second == 0:
            cpu_temp = get_cpu_temperatur_status()

        if now.minute == 30 or now.minute == 0:
            get_ntp_status(ntp_state)

        if disp_state == 0:
            bigdigit.write_clock_v2(disp, now)
        elif disp_state == 1:
            # clock
            clock = f'{now.strftime("%m/%d")} {week_names[now.weekday()]} {now.strftime("%H:%M:%S")}'
            disp.write_line(clock, 0)
            # line
            disp.fill_line(ord('-'), 1)
            # room temp
            temp, hum, pres = sphere.get_status()
            disp.write_line(replace_temp_c(f'{temp} {hum} {pres}'), 2)
            if now.second & 1 == 1:
                # raspi temp
                cpu = f'CPU: {psutil.cpu_percent():4.1f}% {cpu_temp}'
                disp.write_line(replace_temp_c(cpu), 3)
            else:
                # ntp
                last_ntp_string = ntp_state.get() if ntp_state.empty() == False else last_ntp_string
                disp.write_line(last_ntp_string, 3)

        time.sleep(0.2)

def replace_temp_c(message: str):
    return message.replace("'C", str(chr(0xdf) + 'C'))

# ***************************
# Getting various information

def get_cpu_temperatur_status():
    for line in execute_command('vcgencmd measure_temp'):
        return line.replace('temp=', '')


def get_ntp_status(status: Queue):
    th = threading.Thread(target=ntp_exec, args=[status])
    th.start()


def ntp_exec(status: Queue):
    ntp = ''
    for line in execute_command('ntpq -p'):
        if line.find('*') >= 0:
            ntp = f'NTP: {line.split(" ")[0][1:]}' # <= ntp server string

    if ntp == '':
        ntp = 'NTP: NG'
    status.put(ntp)


def execute_command(cmd):
    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return [s for s in out.decode('utf-8').split('\n') if s]

# ***************************
# Run Program

if __name__ == '__main__':
    try:
        sphere.initialize()
        disp.initialize()
        main()
    except KeyboardInterrupt:
        pass
    finally:
        disp.dispose()
