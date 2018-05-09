# OledClockService

## Description

It is an application of watch using winSTAR's OLED display (20 × 4 character) and raspberry pie, temperature sensor BME 280.
Display contents are:

* Display of date and time
* Display of temperature and humidiry (require BMW280 sensor)
* Display of ntp server name
* Display of cpu usage and cpu temperature
* Display of internet speed (download / upload) and ping response

## Require

* Raspberry pi 1 Model B+ or later.
    * python 2.7 or later. (with some library is use)
* BME280 Temperature and humidiry sensor
    * [datasheet](http://akizukidenshi.com/download/ds/bosch/BST-BME280_DS001-10.pdf)
* WinSTAR OLED Display 20x4 WEH002004A (using controller WS0010)
    * [datasheet](http://blog.digit-parts.com/pdf/ws0010.pdf)
