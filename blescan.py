# BLE iBeaconScanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# JCS 06/07/14

# BLE scanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# BLE scanner, based on https://code.google.com/p/pybluez/source/browse/trunk/examples/advanced/inquiry-with-rssi.py

# https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
# https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
# https://github.com/pauloborges/bluez/blob/master/lib/hci.c#L2782 for functions used by lescan

# performs a simple device inquiry, and returns a list of ble advertizements 
# discovered device

# NOTE: Python's struct.pack() will add padding bytes unless you make the endianness explicit. Little endian
# should be used for BLE. Always start a struct.pack() format string with "<"

import paho.mqtt.client as mqtt
import blescan
import argparse
import signal
import subprocess
import random
import select
import os
import sys
import struct
import time
import datetime
import socket
import bluetooth._bluetooth as bluez
import serial
import uuid
import re
import ctypes
import array
import paho.mqtt.client as mqtt

## VARIABLES GLOBALES ##

id=0 #id de dispositivo hci a utilizar
user_id=1
window = 100
scan_window=2

#MQTT
ip = "127.0.0.1"
port = 1883
nombre_dis="JC_PORTATIL"
#

sock = 0
fingerprint=[]
n_fingerprint=0
########################

LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS=0x00
LE_RANDOM_ADDRESS=0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE=7
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_PARAMETERS=0x000B
OCF_LE_SET_SCAN_ENABLE=0x000C
OCF_LE_CREATE_CONN=0x000D
OCF_LE_SET_ADVERTISING_PARAMETERS=0x0006
OCF_LE_SET_ADVERTISING_DATA=0x0008
OCF_LE_SET_ADVERTISE_ENABLE=0x000A
OCF_LE_SET_RANDOM_MAC=0x0005

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02
EVT_LE_CONN_UPDATE_COMPLETE=0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE=0x04

# Advertisment event types
ADV_IND=0x00
ADV_DIRECT_IND=0x01
ADV_SCAN_IND=0x02
ADV_NONCONN_IND=0x03
ADV_SCAN_RSP=0x04

cmd="hciconfig"
i=0
j=0



def showAdapters():
    os.system("sudo hcitool dev")

def signal_handler(signal, frame):
    print ("You pressed Ctrl+C")
    blescan.hci_disable_le_scan(sock)
    sys.exit(0)
    

def hci_le_set_scan_parameters(sock, interval, window):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    SCAN_RANDOM = 0x01
    OWN_TYPE = SCAN_RANDOM
    SCAN_TYPE = 0x01
    interval = interval/0.625
    window = window/0.625

    cmd_pkt = struct.pack("<BHHBB",SCAN_TYPE,int(interval),int(window),0x00,0x00)


def hci_enable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x01)


def hci_toggle_le_scan(sock, enable):
    cmd_pkt = struct.pack("<BB", enable, 0x00) #ultimo parametro a 0 para quitar filtro duplicados
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)


def returnstringpacket(pkt):
    myString = "";
    for c in pkt:
        myString +=  "%02x" %struct.unpack("B",bytes([c]))[0]
    return myString 


def packed_bdaddr_to_string(bdaddr_packed):
    return ':'.join('%02x'%i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))


def returnnumberpacket(pkt):
    myInteger = 0
    multiple = 256
    for c in pkt:
        myInteger +=  struct.unpack("B",bytes([c]))[0] * multiple
        multiple = 1
    return myInteger 

def hci_disable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x00)

def se_encuentra_en_fingerprint(id):
    global fingerprint
    result = False
    for item in fingerprint:
        if item[2] == id:
            result=True
    return result

def parse_events(sock, loop_count=100, cnt=0,scanner_id=1):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)
    flt = bluez.hci_filter_new()
    bluez.hci_filter_all_events(flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, flt)
    done = False
    results = []
    myFullList = []
    clr = 0
    counter = cnt
    for i in range(0, loop_count):
        pkt = sock.recv(255)
        ptype, event, plen = struct.unpack("BBB", pkt[:3])
        if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
            i =0
        elif event == bluez.EVT_NUM_COMP_PKTS:
            i =0 
        elif event == bluez.EVT_DISCONN_COMPLETE:
            i =0 
        elif event == LE_META_EVENT:
            subevent, = struct.unpack('B', bytes([pkt[3]]))
            #subevent, = struct.unpack('B',pkt[3]) #PYTHON 2
            
            pkt = pkt[4:]
            if subevent == EVT_LE_CONN_COMPLETE:
                le_handle_connection_complete(pkt)
            elif subevent == EVT_LE_ADVERTISING_REPORT:
                num_reports = struct.unpack("B", bytes([pkt[0]]))[0]
                report_pkt_offset = 0
		#print(returnstringpacket(pkt[report_pkt_offset -27: report_pkt_offset - 25]))
        
                for i in range(0, num_reports):
                    # build the return string if iBeacon packet received
                    
                    if(returnstringpacket(pkt[report_pkt_offset -22: report_pkt_offset - 6]) == "12345678901234567890123456789012" or returnstringpacket(pkt[report_pkt_offset -22: report_pkt_offset - 6]) == "01234567890123456789012345678901" ):
                        Adstring = str(scanner_id)
                        Adstring += ";"			
                        #Counter
                        if counter > 9999:
                            Adstring += str(clr)
                            counter = 0
                        else:
                            Adstring += str(counter)
                        
                        Adstring += ";"
                        #Mac
                        Adstring += packed_bdaddr_to_string(pkt[report_pkt_offset + 3:report_pkt_offset + 9])
                        Adstring += ";"
                        
                        #Major
                        Adstring += "%i" % returnnumberpacket(pkt[report_pkt_offset -6: report_pkt_offset - 4]) 
                        Adstring += ";"
                        
                        #Minor
                        #Adstring += "%i" % returnnumberpacket(pkt[report_pkt_offset -4: report_pkt_offset - 2]) 
                        #Adstring += ";"
                        
                        #Rssi
                        Adstring += "%i" % struct.unpack("b", bytes([pkt[report_pkt_offset -1]]))
                        Adstring += ";"
                        results.append(Adstring)
                        print(Adstring)
                
                        #print Adstring
                        counter += 1
    done = True
    return counter, results
    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
    
def main():
    
    #Opciones del programa por defecto window 1000ms, ip 127.0.0.1 y port 5000
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--id", type=int, help="device id")
    parser.add_argument("-w","--window", type=int, help="window of scanning")
    parser.add_argument("-I", "--ip", help="IP server MQTT")
    parser.add_argument("-P", "--port", type=int, help="Puerto MQTT")
    parser.add_argument("-u", "--user", type=int, help="User ID")
    args = parser.parse_args()

    #Comprobaciones de parametros
    if args.window == None:
        global window
    else:
        window = args.window

    if args.ip == None:
        global ip
    else:
        ip = args.ip

    if args.port == None:
        global port
    else:
        port = args.port
        
    if args.user == None:
        global user_id
    else:
        user_id = args.user
    if args.id==None:
        global id
    else:
        id==args.id
    #Se crea el socket con el adaptador bluetooth
    global sock
    global nombre_dis
    sock=bluez.hci_open_dev(id)

    client = mqtt.Client(nombre_dis)
    client.connect(host=ip, port=port)
    client.loop_start()

    #Programa principal, se configura con los parametros y empieza a escanear.
    blescan.hci_le_set_scan_parameters(sock,window,window)
    blescan.hci_enable_le_scan(sock)
    count = 0
    
    global scan_window
    data = []
    time_init=time.time()
    time_now=time.time()
    global fingerprint
    global n_fingerprint

    while True:

        while(time_now-time_init)<scan_window:
            returnedList= blescan.parse_events(sock, 5, count, user_id)
            count = returnedList[0]
            generar_fingerprint(returnedList[1])
            data.append(returnedList[1])
            time_now=time.time()

        client.publish("ble_scan", str(fingerprint), qos=1)
        data=[]
        n_fingerprint+=1;
        print(fingerprint)
        fingerprint=[]
        time_init=time.time()
        time_now=time.time()
        


def generar_fingerprint(data):
    global fingerprint
    if data!=[]:
        for item in data:
            data_split=item.split(';')
            user_id=data_split[0]
            udp_counter=data_split[1]
            mac_beacon=data_split[2]
            id_beacon = data_split[3]
            rssi=data_split[4]
            
            if(se_encuentra_en_fingerprint(id_beacon)==False):
                fingerprint.append([user_id, n_fingerprint, id_beacon, 0, 0])
            for item2 in fingerprint:
                if item2[2]==id_beacon:
                    item2[3]+=1;
                    item2[4]=round((item2[4]*(item2[3]-1)+int(rssi))/item2[3])



    





     

main()
