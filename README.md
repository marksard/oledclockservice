# OledClockService

## Description

It is an application of watch using winSTAR's OLED display (20 × 4 character) and raspberry pie, temperature sensor BME 280.
Display contents are:

* Display of date and time
* Display of temperature and humidiry (require BME280 sensor)
* Display of ntp server name
* Display of cpu usage and cpu temperature
* Display of internet speed (download / upload) and ping response

## Require

### Hardware

* Raspberry pi 1 Model B+ or later.
    * python 2.7 or later. (with some library is use)
* BME280 Temperature and humidiry sensor
    * [datasheet](http://akizukidenshi.com/download/ds/bosch/BST-BME280_DS001-10.pdf)
* WinSTAR OLED Display 20x4 WEH002004A
    * [WinSTAR page](https://www.winstar.com.tw/products/oled-module/oled-character-display/oled-20x4.html)
    * [OLED datasheet](https://www.winstar.com.tw/uploads/files/6eb7552c6c9c656f690c8206dc964e19.pdf)
    * [controller WS0010 datasheet](http://blog.digit-parts.com/pdf/ws0010.pdf)


### Software

* Python2.7 or later

You need to install the following:

```sh
pip install pytz
pip install psutil

sudo apt install -y python3-smbus
sudo apt install -y speedtest-cli
sudo apt install -y ntp
```
