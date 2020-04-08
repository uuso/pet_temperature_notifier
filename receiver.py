# http://www.varesano.net/blog/fabio/serial%20rs232%20connections%20python
# install pySerial

import os
import serial
from serial.tools import list_ports
import time, json, datetime

log_folder = "logs/"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_filepath = log_folder + "log.txt"

notes_in_minute = 3 # Ардуино опрашивает датчик каждые 20 секунд

def serial_port_path(default = False):
    """Функция возвращает путь для обращения к COM-порту.
    По умолчанию, выводит список доступных портов и ждёт ответа оператора 
    на запрос выбора порта. Список портов нумерован и начинается с единицы.
    
    Будет запрашивать выбор пока не выберут один из доступных портов.
    Вернёт 0/False в случаях:
        - нет портов
        - аргументом указан недопустимый порт
    """
    coms = list_ports.comports(True)
    if not len(coms):
        print("No COM-devices available.\n")
        return False

    val = 0
    while not val:
        print("Available COM-devices:")
        for _, com in zip(range(1,len(coms)+1), coms):
            print("{}: {}".format(_, com))        

        val = default if default else int(input("Select COM-device: "))

        if val-1 not in range(len(coms)):
            print("Wrong value. Please try again.")
            val = 0
            if default: # Если выбранное значение default не из списка портов
                return False
    if default:
        print("Selected COM-device (default): %d" % (default))
    print()
    return coms[val-1]
    
def serial_messaging_json(comport, delay=0.5, msec = False):
    """Функция получения генератора сообщений JSON от COM-порта по пути $comport.
    
    Каждые $delay секунд опрашивает порт на наличие данных, возвращает объект JSON формата 
    {"timestamp": <ISO8601_datetime>, <JSONReceivedData>}, 
    
    Пример:
        {"timestamp": "2020-04-08T03:48:48", "error": false, "temperature": 20.9, "humidity": 21.2}
    """
    ser = serial.Serial(port = comport.device)
    while True:        
        if ser.in_waiting:
            data = {"timestamp": datetime.datetime.now().isoformat() if msec 
                else datetime.datetime.now().isoformat().split('.')[0]}
            msg = ser.read_until()[:-2].decode('utf-8') # [:-2] - из-за последних двух байтов '\r\n'            
            try:
                temp = json.loads(msg)
                data.update(temp)                
                yield data
            except Exception as ex:
                print("Error \"{}\" at message: \"{}\"".format(ex, msg))
        time.sleep(delay)


if __name__ == "__main__":
    comport = serial_port_path(default=1)
    if comport:    
        message = serial_messaging_json(comport)
        while True:
            msg = next(message)
            with open(log_filepath, "a", encoding="utf-8") as logfile:
                logfile.write("{}\n".format(json.dumps(msg)))
                print(msg)
            
        
        