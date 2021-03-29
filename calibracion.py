
import sys
import os
import argparse
import socket
import time
import signal
import time
import numpy as np
from datetime import datetime
import csv
import paho.mqtt.client as mqtt
import random




def signal_handler(signal, frame):
    print ("You pressed Ctrl+C")
    csvfile.close()
    #sock_rec.close()
    sys.exit(0)

#Parametros configurables -----------------------------------

ip = "127.0.0.1"
port = 1883

tiempo_cal=60 #tiempo de calibracion por zona
    
beacons=[10,11,12,13,14,15,16,17,18,19]
users=[1]

#---------------------------------------------------------------
signal.signal(signal.SIGINT, signal_handler)


parser = argparse.ArgumentParser()
parser.add_argument("-d","--device", type=str, help="dispositivo de calibracion usado (Dell, rpi, JCportatil")
parser.add_argument("-t","--tiempo_cal", type=int, help="tiempo de calibracion por zona (seg)")
args = parser.parse_args()

now=datetime.now()
now_str= now.strftime("%m_%d_%Y_%H_%M")
print(now_str)

if (args.device == None):
    filename="cal_files/fpcal"
else:
    filename="cal_files/fpcal_"+str(len(beacons))+"_"+args.device+"_"+now_str

if(args.tiempo_cal==None):
    tiempo_cal=tiempo_cal
else:
    tiempo_cal=args.tiempo_cal


os.mkdir(filename)
os.chdir(filename)

datos_mqtt=""

def on_message(client, userdata, message):
    global datos_mqtt
    datos_mqtt=message.payload.decode("utf-8")



client = mqtt.Client("Calibracion"+str(random.randrange(10)))
client.on_message = on_message 
client.connect(host=ip, port=port)
client.subscribe("fingerprint")
client.loop_start()


def nueva_zona():

    print("Se va a proceder la calbiracion del usuario " + str(id_calibracion))
    print("ID de zona en la que se encuentra: ")
    id_zona=input()
    print("----------------------------------------------------------------------")
    print("Para terminar la calibracion pulse CTRL+C")
    print("----------------------------------------------------------------------")
    time.sleep(1)
    
    calibration_process(id_calibracion,id_zona)


def calibration_process(id_calibracion,id_zona):
    #sock_rec=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #sock_rec.bind((rec_ip,rec_port))
    time_init = time.time()
    time_now = time.time()
    data_save=[]
    data_save_visibilidad=[]
    
    while time_now-time_init < tiempo_cal:

        if(datos_mqtt!=""):
                
            data = datos_mqtt
            data=np.asarray(data.replace('[','').replace(']','').replace(' ','').replace("'",'').split(','))
            data_reshape=data.reshape(len(beacons),4)
            
            for j in beacons:
                for i in data_reshape:
                    if(j==int(i[1]) and int(i[0])==int(id_calibracion)):
                        data_save.append(int(i[3]))
                        data_save_visibilidad.append(int(i[2]))
                        if(j==beacons[-1:][0]):
                            data_save.append(id_calibracion)
                            data_save.append(id_zona)
                            data_save_visibilidad.append(id_calibracion)
                            data_save_visibilidad.append(id_zona)
            
            if data_save!=[]:
                writer.writerow(data_save)
                writer2.writerow(data_save_visibilidad)
                print(data_save)
                print(data_save_visibilidad)
            time.sleep(2)
            
            data_save=[]
            data_save_visibilidad=[]
            time_now=time.time()
    #sock_rec.close()
    nueva_zona()



with open(("fingerprint_calibracion"+'.csv'), 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)

    with open(("fingerprint_visibilidad"+'.csv'),'w') as csvfile:
        writer2=csv.writer(csvfile, delimiter=',',
                                quotechar='|',quoting=csv.QUOTE_MINIMAL)
        
        print("Introduzca el ID del usuario que va a generar la calibracion:")
        id_calibracion=input()
        nueva_zona()
        
