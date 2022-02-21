# Name: WEH002004 driver
# Author: marksard
# Version: 2.0
# Python 3.6 or later (maybe)
#   WinSTAR OLED Display 20x4 WEH002004A (using controller WS0010)
#   datasheet (http://blog.digit-parts.com/pdf/ws0010.pdf)
#   Use WS0010 4bit mode

# ***************************
import RPi.GPIO as GPIO
import time

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

class WEH002004A:
    # Relationship wiring between GPIO pin and OLED pin.
    # Pin position of OLED seen from RaspberryPi.
    def __init__(self, rs = 7, e = 8, d4 = 25, d5 = 24, d6 = 23, d7 = 18) -> None:
        self.__RS = rs #7
        self.__E = e #8
        self.__D4 = d4 #25
        self.__D5 = d5 #24
        self.__D6 = d6 #23
        self.__D7 = d7 #18

        self.__PULSE_TIME = 1e-6 * 50
        self.__line = [
            # OLED RAM Line Address
            0x80, # line 1
            0xC0, # line 2
            0x94, # line 1 + 20(0x80 + 0x14)
            0xD4 # line 2 + 20(0xC0 + 0x14)
        ]
        # Maximum characters per line
        self.WRITE_LINE_WIDTH = 20
        self.MODE_CHR = True
        self.MODE_CMD = False


    def initialize(self) -> None:
        GPIO.setwarnings(False)
        # Use BCM GPIO numbers
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__E, GPIO.OUT)
        GPIO.setup(self.__RS, GPIO.OUT)
        GPIO.setup(self.__D4, GPIO.OUT)
        GPIO.setup(self.__D5, GPIO.OUT)
        GPIO.setup(self.__D6, GPIO.OUT)
        GPIO.setup(self.__D7, GPIO.OUT)
        GPIO.output(self.__E, False)
        GPIO.output(self.__RS, False)
        GPIO.output(self.__D4, False)
        GPIO.output(self.__D5, False)
        GPIO.output(self.__D6, False)
        GPIO.output(self.__D7, False)

        # WEH002004 best initialize (my environment)

        # WS0010 4bit mode initialized
        time.sleep(0.5)

        # Synchronization function for an 4-bit use
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)

        # Function set
        self.set4_bit(0, 0, 1, 0, self.MODE_CMD)  # start?
        self.set4_bit(0, 0, 1, 0, self.MODE_CMD)  # 0 0 1 DL (4bit mode)
        self.set4_bit(1, 0, 0, 0, self.MODE_CMD)  # N F FT1 FT0 (2line, 5x8dot, english-japanese font)
        time.sleep(0.1)  # Instead of BUSY check

        self.clear_display()
        self.display_power(0)

        # Entry mode set
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)  # 0 0 0 0
        self.set4_bit(0, 1, 1, 0, self.MODE_CMD)  # 0 1 I/D S (Inclemental, not shift)
        time.sleep(0.1)  # Instead of BUSY check
    
        self.display_power(1)
        self.clear_display()


    def dispose(self) -> None:
        self.clear_display()
        self.write_line("Finish", 0)
        self.display_power(0)
        time.sleep(0.5)
        GPIO.setwarnings(False)
        GPIO.output(self.__E, False)
        GPIO.output(self.__RS, False)
        GPIO.output(self.__D4, False)
        GPIO.output(self.__D5, False)
        GPIO.output(self.__D6, False)
        GPIO.output(self.__D7, False)
        GPIO.cleanup()


    def clear_display(self) -> None:
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)  # 0 0 0 0
        self.set4_bit(0, 0, 0, 1, self.MODE_CMD)  # 0 0 0 1
        time.sleep(0.1)  # Instead of BUSY check


    def display_power(self, on: int) -> None:
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)  # 0 0 0 0
        self.set4_bit(on, 1, 0, 0, self.MODE_CMD)  # 1 D C B (Disp on/off, Cursor off, Blink off)
        time.sleep(0.1)  # Instead of BUSY check


    def return_home(self) -> None:
        self.set4_bit(0, 0, 0, 0, self.MODE_CMD)  # 0 0 0 0
        self.set4_bit(0, 0, 1, 0, self.MODE_CMD)  # 0 0 1 0
        time.sleep(0.1)  # Instead of BUSY check


    def write_line(self, message: str, line: int) -> None:
        message = message.ljust(self.WRITE_LINE_WIDTH, " ")
        self.set_8bit(self.__line[line], self.MODE_CMD)
        for i in range(self.WRITE_LINE_WIDTH):
            self.set_8bit(ord(message[i]), self.MODE_CHR)


    def write_bytes(self, message: bytes, line: int) -> None:
        self.set_8bit(self.__line[line], self.MODE_CMD)
        for i in range(self.WRITE_LINE_WIDTH):
            if i < len(message):
                self.set_8bit(message[i], self.MODE_CHR)
            else:
                self.set_8bit(ord(' '), self.MODE_CHR)


    def clear_line(self, line: int) -> None:
        self.set_8bit(self.__line[line], self.MODE_CMD)
        for _ in range(self.WRITE_LINE_WIDTH):
            self.set_8bit(0, self.MODE_CHR)


    def fill_line(self, fill: str, line: int) -> None:
        self.set_8bit(self.__line[line], self.MODE_CMD)
        for _ in range(self.WRITE_LINE_WIDTH):
            self.set_8bit(fill, self.MODE_CHR)


    def set_8bit(self, bits: any, mode: int) -> None:
        # High bits
        self.set4_bit(bits & 0x80 == 0x80, bits & 0x40 == 0x40,
                bits & 0x20 == 0x20, bits & 0x10 == 0x10, mode)
        # Low bits
        self.set4_bit(bits & 0x08 == 0x08, bits & 0x04 == 0x04,
                bits & 0x02 == 0x02, bits & 0x01 == 0x01, mode)


    def set4_bit(self, d7: int, d6: int, d5: int, d4: int, mode: int) -> None:
        GPIO.setwarnings(False)
        GPIO.output(self.__RS, mode)
        GPIO.output(self.__E, False)

        GPIO.output(self.__D4, False)
        GPIO.output(self.__D5, False)
        GPIO.output(self.__D6, False)
        GPIO.output(self.__D7, False)

        GPIO.output(self.__D4, d4)
        GPIO.output(self.__D5, d5)
        GPIO.output(self.__D6, d6)
        GPIO.output(self.__D7, d7)

        time.sleep(self.__PULSE_TIME)
        GPIO.output(self.__E, True)
        time.sleep(self.__PULSE_TIME)
        GPIO.output(self.__E, False)
        time.sleep(self.__PULSE_TIME)

        # As next timing adjustment
        if mode:
            time.sleep(0.00004)
        else:
            time.sleep(0.00152)
