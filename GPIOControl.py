import subprocess
import time
from clients_db import WorkWithClientDB


def turning_on(sec):
    subprocess.call('gpio mode 25 out', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call('gpio write 25 1', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(sec)
    subprocess.call('gpio write 25 0', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def check_status():
    subprocess.call('gpio mode 23 in', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if int(str(subprocess.run('gpio read 23', shell=True, stdout=subprocess.PIPE).stdout).strip("b'\\n")) == 1:
        WorkWithClientDB.update_server_status(1)
    else:
        WorkWithClientDB.update_server_status(0)


if __name__ == '__main__':
    while True:
        check_status()
        com_num = WorkWithClientDB.check_comand()
        if com_num == 1:
            turning_on(0.5)
            WorkWithClientDB.gpio_controlling(0)
        elif com_num == 2:
            turning_on(6)
            WorkWithClientDB.gpio_controlling(0)
        else:
            time.sleep(0.5)
