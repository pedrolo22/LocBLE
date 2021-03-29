import socket 
import time
import signal
import argparse
import sys
import paho.mqtt.client as mqtt
import numpy

ip='127.0.0.1'
port=1883

beacons = [10,11,12,13,14,15,16,17,18,19]


parser = argparse.ArgumentParser()
parser.add_argument("-i","--ip", type=str, help="IP de server MQTT", default='127.0.0.1')
parser.add_argument("-p","--port", type=int, help="Puerto MQTT",default=1883)
args = parser.parse_args()



if(args.ip == None):
    ip=ip
else: 
    ip=args.ip

if(args.port == None):
    port=port
else: 
    port=args.port

data_send=[]



datos_mqtt=""

def on_message(client, userdata, message):
    global datos_mqtt
    global data_send
    global users
    global beacons



    datos_mqtt=message.payload
    datos_mqtt=datos_mqtt.decode("utf-8").replace('[','').replace(']','').replace("'",'').split(',')
    
    for i in beacons :
        
        if(datos_mqtt != ['']):
            data_send.append([int(datos_mqtt[0]),i,0,-100])

    beacons_detected=int(len(datos_mqtt)/5)
    for i in range(beacons_detected):
        for j in data_send:
            if (int(datos_mqtt[i*5+2])==j[1]):
                j[2]=datos_mqtt[i*5+3]
                j[3]=datos_mqtt[i*5+4]
        
    print(data_send)
    client.publish("fingerprint", str(data_send), qos=1)
    data_send=[]
    



client = mqtt.Client("Gestor de datos")
client.on_message = on_message 
client.connect(host=ip, port=port)
client.subscribe("ble_scan")
client.loop_start()

def signal_handler(signal, frame):
	print ("You pressed Ctrl+C")
	sys.exit(0)
    
signal.signal(signal.SIGINT, signal_handler)



while(True):
    a=0
