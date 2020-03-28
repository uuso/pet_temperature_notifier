# http://www.varesano.net/blog/fabio/serial%20rs232%20connections%20python
# install pySerial

import serial
from serial.tools import list_ports
import time, json, datetime
# import json

def choose_comport(default = False):
    coms = list_ports.comports(True)
    if not len(coms):
        print("No COM-devices available.\n")
        return

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
                return val
    if default:
        print("Selected COM-device (default): %d" % (default))
    print()
    return coms[val-1]
    
def serial_messaging_json(comport, delay = 0.5):
    ser = serial.Serial(port = comport.device)
    while True:        
        if ser.in_waiting:
            data = {}
            msg = ser.read_until()[:-2].decode('utf-8') # [:-2] - из-за последних двух байтов '\r\n'            
            try:
                temp = json.loads(msg)
                # data["timestamp"] = datetime.datetime.now().isoformat() # не удобно - когда меняется температура едет табличка в логе
                data = {"timestamp": datetime.datetime.now().isoformat()}
                data.update(temp)                
                yield data
            except Exception as ex:
                print("Error \"{}\" at message: \"{}\"".format(ex, msg))
        time.sleep(delay)


if __name__ == "__main__":
    comport = choose_comport(1)
    if not comport:
        exit()
    
    message = serial_messaging_json(comport)
    with open("log.txt", "a", encoding="utf-8") as logfile:
        while True:
            msg = next(message)
            logfile.write("{}\n".format(json.dumps(msg)))
            print(msg)
            
        
        