#!/usr/bin/python

# Product: Multi information clock
# Author: marksard
# Version: 4
# Require Device: Raspberry PI 1 Model B+ or later.
#                 Temperature and humidiry sensor BME280
#                   datasheet (http://akizukidenshi.com/download/ds/bosch/BST-BME280_DS001-10.pdf)
#                 WinSTAR OLED Display 20x4 WEH002004A (using controller WS0010)
#                   datasheet (http://blog.digit-parts.com/pdf/ws0010.pdf)


# ***************************
import RPi.GPIO as GPIO
import time
import datetime
import pytz
# import locale
import threading
import smbus
# import re
import psutil
import os
import pwd


# ***************************

# Maximum characters per line
WRITE_LINE_WIDTH = 20

# OLED RAM Line Address
WRITE_LINE_1 = 0x80
WRITE_LINE_2 = 0xC0
WRITE_LINE_3 = 0x94
WRITE_LINE_4 = 0xD4


# ***************************
# global string

NtpStatusString = ""
CpuTemperatureString = ""
SpeedTestString = ""
SpeedTestPingString = ""


# ***************************

def main():
    sec1_count = 1
    sec10_count = 1
    sec3_count = 1
    sec60_count = 1
    halfhour_count = 0
    halfhour_count2 = 0
    status_mode = 2
    fill_line(ord("-"), WRITE_LINE_2)

    while True:
        update_clock()

        sec1_count -= 1
        if sec1_count == 0:
            sec1_count = 5
            sec3_count -= 1
            sec10_count -= 1
            sec60_count -= 1
            now = datetime.datetime.today()

            if (now.minute == 25 or now.minute == 55) and sec60_count == 0:
                halfhour_count -= 1

            if (now.minute == 30 or now.minute == 0) and sec60_count == 0:
                halfhour_count2 -= 1

            if status_mode == 0:
                update_cpu_status()
            elif status_mode == 1:
                write_line(NtpStatusString, WRITE_LINE_4)
            elif status_mode == 2:
                write_line(SpeedTestString, WRITE_LINE_4)
            else:
                write_line(SpeedTestPingString, WRITE_LINE_4)

            write_now_txt()

        if sec3_count == 0:
            sec3_count = 3
            status_mode = status_mode + 1
            if status_mode > 3:
                status_mode = 0

        if sec10_count == 0:
            sec10_count = 10
            update_bme280_status()
            update_cpu_temperatur_status()

        if sec60_count == 0:
            sec60_count = 60
            update_ntp_status_thread()

        if halfhour_count <= 0:
            halfhour_count = 1
            update_speedtest_thread()

        if halfhour_count2 == 0:
            halfhour_count2 = 1
            update_write_csv()

        # print(get_chart_information())
        time.sleep(0.2)


# ***************************
# Hot all information

def write_now_txt():
    fs = open("/var/log/oledclockservice.txt", "w")
    fs.write(get_all_information())
    fs.close()


def get_all_information():
    global NtpStatusString
    global SpeedTestString
    global SpeedTestPingString
    return get_clock_csv() + "\n" + "--------------------\n" + get_bme280_status() + "\n" + get_cpu_status() + "\n" + NtpStatusString + "\n" + SpeedTestString + "\n" + SpeedTestPingString + "\n"


# ***************************
# Save the csv

def update_write_csv():
    update_write_thread = threading.Thread(
        target=write_csv, name="UpdateWriteThread")
    update_write_thread.start()


def write_csv():
    fs = open("/var/www/oledclockservice.csv", "a+")

    read = []
    for line in fs:
        read.append(line)
    read.append(get_chart_information())
    fs.close()

    fs = open("/var/www/oledclockservice.csv", "w+")
    fs.seek(0, 0)
    for i, w in enumerate(read):
        if len(read) > 24 * 2 * 7:
            if i >= 1:
                fs.write(w)
        else:
            fs.write(w)
    fs.close()
    mark = pwd.getpwnam('mark')
    os.chown('/var/www/oledclockservice.csv', mark.pw_uid, mark.pw_gid)
    os.chmod("/var/www/oledclockservice.csv", 0766)


def get_chart_information():
    global CpuTemperatureString
    global SpeedTestString
    global SpeedTestPingString
    return "'" + get_clock_csv() + "', " + get_bme280_status().replace(" ", ", ").replace("'C", "").replace("hPa", "").replace("%", "") + CpuTemperatureString.replace("'C", "") + ", " + SpeedTestString.replace("D/U: ", "").replace("Mbps", "").replace("/", ", ") + ", " + SpeedTestPingString.replace("Ping: ", "").replace("ms", "") + "\n"


def get_clock_csv():
    now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    return now.strftime("%Y/%m/%d %H:%M:%S %z")


# ***************************
# Getting various information

WeekNameString = ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."]


def get_clock():
    global WeekNameString
    now = datetime.datetime.today()
    return now.strftime("%m/%d ") + WeekNameString[now.weekday()] + " " + now.strftime("%H:%M:%S")


def update_clock():
    clock = get_clock()
    write_line(clock, WRITE_LINE_1)


def get_cpu_status():
    return str("CPU: %4.1f%% " % psutil.cpu_percent()) + CpuTemperatureString


def update_cpu_status():
    cpu = get_cpu_status()
    write_line(cpu.replace("'C", str(chr(0xdf) + "C")), WRITE_LINE_4)


def update_cpu_temperatur_status():
    global CpuTemperatureString
    CpuTemperatureString = ""
    for line in execute_command('vcgencmd measure_temp'):
        CpuTemperatureString = line.replace("temp=", "")


def update_ntp_status_thread():
    update_status_thread = threading.Thread(
        target=update_ntp_status, name="UpdateStatusThread")
    update_status_thread.start()


def update_ntp_status():
    ntp = ""
    for line in execute_command('ntpq -p'):
        if line.find('*') >= 0:
            ntp = "NTP: " + line.split(' ')[0][1:]  # <= ntp server string

    if ntp == "":
        ntp = "NTP: NG"

    global NtpStatusString
    NtpStatusString = ntp


def update_speedtest_thread():
    update_speed_thread = threading.Thread(
        target=update_speedtest, name="UpdateSpeedTestThread")
    update_speed_thread.start()


def update_speedtest():
    speed = ""
    ping = ""
    for line in execute_command('speedtest'):
        if line.find('Download: ') >= 0:
            speed = "D/U: " + line.split(' ')[1] + "/"
        if line.find('Upload: ') >= 0:
            speed = speed + line.split(' ')[1] + "Mbps"
            global SpeedTestString
            SpeedTestString = speed
        if line.find(' ms') >= 0:
            index1 = line.find(']: ') + 3
            index2 = line.find(' ms')
            ping = "Ping: " + line[index1: index2] + "ms"
            global SpeedTestPingString
            SpeedTestPingString = ping

    # print(speed)
    # print(ping)


def execute_command(cmd):
    from subprocess import Popen, PIPE

    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()

    return [s for s in out.split('\n') if s]


# ***************************
# GPIO (WinSTAR OLED Display) settings
# The wiring for the WinSTAR OLED is as follows:
# 1 : GND
# 2 : 5V
# 3 : NC
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - TO GND (It doesn't wired by WinSTAR 20x4 model.)
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: NC
# 16: NC

# Relationship wiring between GPIO pin and OLED pin.
# Pin position of OLED seen from RaspberryPi.
OLED_RS = 7
OLED_E = 8
OLED_D4 = 25
OLED_D5 = 24
OLED_D6 = 23
OLED_D7 = 18

# Constants
WRITE_MODE_CHR = True
WRITE_MODE_CMD = False


def initialize_gpio():
    GPIO.setwarnings(False)
    # Use BCM GPIO numbers
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(OLED_E, GPIO.OUT)
    GPIO.setup(OLED_RS, GPIO.OUT)
    GPIO.setup(OLED_D4, GPIO.OUT)
    GPIO.setup(OLED_D5, GPIO.OUT)
    GPIO.setup(OLED_D6, GPIO.OUT)
    GPIO.setup(OLED_D7, GPIO.OUT)
    GPIO.output(OLED_E, False)
    GPIO.output(OLED_RS, False)
    GPIO.output(OLED_D4, False)
    GPIO.output(OLED_D5, False)
    GPIO.output(OLED_D6, False)
    GPIO.output(OLED_D7, False)



def initialize_winstar_oled():
    # ws0010 4bit mode initialized
    time.sleep(0.5)

    # Synchronization function for an 4-bit use
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)

    # Function set
    set4_bit(0, 0, 1, 0, WRITE_MODE_CMD)  # start?
    set4_bit(0, 0, 1, 0, WRITE_MODE_CMD)  # 0 0 1 DL (4bit mode)
    set4_bit(1, 0, 0, 0, WRITE_MODE_CMD)  # N F FT1 FT0 (2line?, 5x8dot, english-japanese font)
    time.sleep(0.1)  # Instead of BUSY check

    # Displey mode
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)  # 0 0 0 0
    set4_bit(1, 1, 0, 0, WRITE_MODE_CMD)  # 1 D C B (Disp on, Cursor off, Blink off)
    time.sleep(0.1)  # Instead of BUSY check

    # Displey clear
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)  # 0 0 0 0
    set4_bit(0, 0, 0, 1, WRITE_MODE_CMD)  # 0 0 0 1
    time.sleep(0.1)  # Instead of BUSY check

    # Return home
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)  # 0 0 0 0
    set4_bit(0, 0, 1, 0, WRITE_MODE_CMD)  # 0 0 1 0
    time.sleep(0.1)  # Instead of BUSY check

    # Entry mode set
    set4_bit(0, 0, 0, 0, WRITE_MODE_CMD)  # 0 0 0 0
    set4_bit(0, 1, 1, 0, WRITE_MODE_CMD)  # 0 1 I/D S (Inclemental, not shift)
    time.sleep(0.1)  # Instead of BUSY check


def write_line(message, line):
    message = message.ljust(WRITE_LINE_WIDTH, " ")
    set_8bit(line, WRITE_MODE_CMD)
    for i in range(WRITE_LINE_WIDTH):
        set_8bit(ord(message[i]), WRITE_MODE_CHR)


def clear_line(line):
    set_8bit(line, WRITE_MODE_CMD)
    for _ in range(WRITE_LINE_WIDTH):
        set_8bit(0, WRITE_MODE_CHR)


def fill_line(fill, line):
    set_8bit(line, WRITE_MODE_CMD)
    for _ in range(WRITE_LINE_WIDTH):
        set_8bit(fill, WRITE_MODE_CHR)


def clear_display():
    set_8bit(0x01, WRITE_MODE_CMD)


def set_8bit(bits, mode):
    # High bits
    set4_bit(bits & 0x80 == 0x80, bits & 0x40 == 0x40,
             bits & 0x20 == 0x20, bits & 0x10 == 0x10, mode)
    # Low bits
    set4_bit(bits & 0x08 == 0x08, bits & 0x04 == 0x04,
             bits & 0x02 == 0x02, bits & 0x01 == 0x01, mode)


def set4_bit(d7, d6, d5, d4, mode):
    GPIO.output(OLED_RS, mode)

    GPIO.output(OLED_D4, False)
    GPIO.output(OLED_D5, False)
    GPIO.output(OLED_D6, False)
    GPIO.output(OLED_D7, False)

    GPIO.output(OLED_D4, d4)
    GPIO.output(OLED_D5, d5)
    GPIO.output(OLED_D6, d6)
    GPIO.output(OLED_D7, d7)

    time.sleep(0.00000006)
    GPIO.output(OLED_E, True)
    time.sleep(0.00000006)
    GPIO.output(OLED_E, False)
    time.sleep(0.00000006)

    if mode:
        time.sleep(0.00004)
    else:
        time.sleep(0.00152)


# ***************************
# I2C (BME280) Settings
# This code is used by editing the following sample code.
# https://github.com/SWITCHSCIENCE/samplecodes/tree/master/BME280

I2cBusNumber = 1    # Maybe differeced by environment(0 or 1)
I2cAddress = 0x76   # Maybe differeced by each devices
I2cBusInstance = smbus.SMBus(I2cBusNumber)
I2cCaribTemp = []
I2cCaribPress = []
I2cCaribHumi = []
I2cCaribFine = 0.0


def initialize_bme280():
    osrs_t = 1  # Temperature oversampling x 1
    osrs_p = 1  # Pressure oversampling x 1
    osrs_h = 1  # Humidity oversampling x 1
    mode = 3  # Normal mode
    t_sb = 5  # Tstandby 1000ms
    filter = 0  # Filter off
    spi3w_en = 0  # 3-wire SPI Disable

    ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
    config_reg = (t_sb << 5) | (filter << 2) | spi3w_en
    ctrl_hum_reg = osrs_h

    write_data_i2c(0xF2, ctrl_hum_reg)
    write_data_i2c(0xF4, ctrl_meas_reg)
    write_data_i2c(0xF5, config_reg)

    calibration_bme280()


def calibration_bme280():
    calib = []

    for i in range(0x88, 0x88 + 24):
        calib.append(I2cBusInstance.read_byte_data(I2cAddress, i))

    calib.append(I2cBusInstance.read_byte_data(I2cAddress, 0xA1))

    for i in range(0xE1, 0xE1 + 7):
        calib.append(I2cBusInstance.read_byte_data(I2cAddress, i))

    I2cCaribTemp.append((calib[1] << 8) | calib[0])
    I2cCaribTemp.append((calib[3] << 8) | calib[2])
    I2cCaribTemp.append((calib[5] << 8) | calib[4])
    I2cCaribPress.append((calib[7] << 8) | calib[6])
    I2cCaribPress.append((calib[9] << 8) | calib[8])
    I2cCaribPress.append((calib[11] << 8) | calib[10])
    I2cCaribPress.append((calib[13] << 8) | calib[12])
    I2cCaribPress.append((calib[15] << 8) | calib[14])
    I2cCaribPress.append((calib[17] << 8) | calib[16])
    I2cCaribPress.append((calib[19] << 8) | calib[18])
    I2cCaribPress.append((calib[21] << 8) | calib[20])
    I2cCaribPress.append((calib[23] << 8) | calib[22])
    I2cCaribHumi.append(calib[24])
    I2cCaribHumi.append((calib[26] << 8) | calib[25])
    I2cCaribHumi.append(calib[27])
    I2cCaribHumi.append((calib[28] << 4) | (0x0F & calib[29]))
    I2cCaribHumi.append((calib[30] << 4) | ((calib[29] >> 4) & 0x0F))
    I2cCaribHumi.append(calib[31])

    for i in range(1, 2):
        if I2cCaribTemp[i] & 0x8000:
            I2cCaribTemp[i] = (-I2cCaribTemp[i] ^ 0xFFFF) + 1

    for i in range(1, 8):
        if I2cCaribPress[i] & 0x8000:
            I2cCaribPress[i] = (-I2cCaribPress[i] ^ 0xFFFF) + 1

    for i in range(0, 6):
        if I2cCaribHumi[i] & 0x8000:
            I2cCaribHumi[i] = (-I2cCaribHumi[i] ^ 0xFFFF) + 1


def get_bme280_status():
    data = []
    for i in range(0xF7, 0xF7 + 8):
        data.append(I2cBusInstance.read_byte_data(I2cAddress, i))

    pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    hum_raw = (data[6] << 8) | data[7]

    return get_temperature(temp_raw) + get_humidity(hum_raw) + get_atmospheric_pressure(pres_raw)


def update_bme280_status():
    bme280 = get_bme280_status()
    write_line(bme280.replace("'C", str(chr(0xdf) + "C")), WRITE_LINE_3)


def write_data_i2c(reg_address, data):
    I2cBusInstance.write_byte_data(I2cAddress, reg_address, data)


def get_atmospheric_pressure(data):
    global I2cCaribFine

    v1 = (I2cCaribFine / 2.0) - 64000.0
    v2 = (((v1 / 4.0) * (v1 / 4.0)) / 2048) * I2cCaribPress[5]
    v2 = v2 + ((v1 * I2cCaribPress[4]) * 2.0)
    v2 = (v2 / 4.0) + (I2cCaribPress[3] * 65536.0)
    v1 = (((I2cCaribPress[2] * (((v1 / 4.0) * (v1 / 4.0)) / 8192)
            ) / 8) + ((I2cCaribPress[1] * v1) / 2.0)) / 262144
    v1 = ((32768 + v1) * I2cCaribPress[0]) / 32768

    if v1 == 0:
        return 0

    pressure = ((1048576 - data) - (v2 / 4096)) * 3125

    if pressure < 0x80000000:
        pressure = (pressure * 2.0) / v1
    else:
        pressure = (pressure / v1) * 2

    v1 = (I2cCaribPress[8] * (((pressure / 8.0)
                               * (pressure / 8.0)) / 8192.0)) / 4096
    v2 = ((pressure / 4.0) * I2cCaribPress[7]) / 8192.0
    pressure = pressure + ((v1 + v2 + I2cCaribPress[6]) / 16.0)

    return str("%3.0fhPa " % (pressure / 100))


def get_temperature(data):
    global I2cCaribFine
    v1 = (data / 16384.0 - I2cCaribTemp[0] / 1024.0) * I2cCaribTemp[1]
    v2 = (data / 131072.0 - I2cCaribTemp[0] / 8192.0) * (
        data / 131072.0 - I2cCaribTemp[0] / 8192.0) * I2cCaribTemp[2]
    I2cCaribFine = v1 + v2
    temperature = I2cCaribFine / 5120.0
    return str("%4.1f" % temperature) + "'C "


def get_humidity(data):
    global I2cCaribFine
    var_h = I2cCaribFine - 76800.0
    if var_h != 0:
        var_h = (data - (I2cCaribHumi[3] * 64.0 + I2cCaribHumi[4] / 16384.0 * var_h)) * (
            I2cCaribHumi[1] / 65536.0 * (1.0 + I2cCaribHumi[5] / 67108864.0 * var_h * (1.0 + I2cCaribHumi[2] / 67108864.0 * var_h)))
    else:
        return 0

    var_h = var_h * (1.0 - I2cCaribHumi[0] * var_h / 524288.0)

    if var_h > 100.0:
        var_h = 100.0
    elif var_h < 0.0:
        var_h = 0.0

    return str("%2.0f%% " % var_h)


# ***************************
# Run Program

if __name__ == '__main__':
    try:
        initialize_bme280()
        initialize_gpio()
        initialize_winstar_oled()
        main()
    except KeyboardInterrupt:
        pass
    finally:
        clear_display()
        time.sleep(0.1)
        write_line("Clock Process End", WRITE_LINE_1)
        GPIO.cleanup()
