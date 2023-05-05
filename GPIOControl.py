import wiringpi
import time
from wiringpi import GPIO

pin_num_in = 24    # onboard_pin_num 35
pin_num_out = 25    # onboard_pin_num 37
wiringpi.wiringPiSetup()


def turning_on(sec):
    wiringpi.pinMode(pin_num_out, GPIO.OUTPUT)
    wiringpi.digitalWrite(pin_num_out, GPIO.HIGH)
    time.sleep(sec)
    wiringpi.digitalWrite(pin_num_out, GPIO.LOW)
    time.sleep(2)
    status = check_status()
    return status


def check_status():
    wiringpi.pinMode(pin_num_in, GPIO.INPUT)
    if wiringpi.digitalRead(pin_num_in):
        return 'Сервер включен'
    else:
        return 'Сервер выключен'


if __name__ == '__main__':
    turning_on(0.5)
