import sys
import time
import DAN
import requests
import os
import datetime

sys.path.insert(0, '/usr/lib/python2.7/bridge/')
from bridgeclient import BridgeClient
import custom

client = BridgeClient()

custom.profile_init()
odf_list = custom.odf()
idf_list = custom.idf()

DAN.profile['df_list'] = [t[0] for t in idf_list]

for t in odf_list:
    if t[0] not in DAN.profile['df_list']:
        DAN.profile['df_list'].append(t[0])

print('Detected features:')
for f_name in DAN.profile['df_list']:
    print('    {}'.format(f_name))

DAN.device_registration_with_retry(custom.ServerIP)
#os.system(r'echo "heartbeat" > /sys/class/leds/ds:green:usb/trigger')   #For ArduinoYun Only, need to install packages. "opkg install kmod-ledtrig-heartbeat"
#os.system(r'echo "default-on" > /sys/class/leds/ds:green:usb/trigger') #For ArduinoYun Only. LED constant ON.
os.system(r'echo "timer" > /sys/class/leds/ds:green:usb/trigger')      #For ArduinoYun Only. LED Blink.
client.put('Reg_done', '1')

incomming = {}
for f_name in [t[0] for t in odf_list]:
    incomming[f_name] = 0


################################################## Open Counter storage file
previous_counter = {'Bugs':0, 'RainMeter':0}
current_counter  = {'Bugs':0, 'RainMeter':0}
f_cache_name = r'/root/previous_counter'
try:
    f_cache = open(f_cache_name, 'r+')
except:
    f_cache = open(f_cache_name, 'w+')
    timestamp = str(datetime.datetime.now())
    f_cache.write('0,0,'+ timestamp + ',')
                    
f_cache.seek(0,0)    
cache = f_cache.readline()
cache = cache.split(',')
previous_counter['Bugs'] = int(cache[0])
previous_counter['RainMeter'] = float(cache[1])
timestamp = cache[2]
print('previosu counter',previous_counter)
####################################################

isChange = 0


while True:
    try:
        cache = {}
	check_list=[t[0] for t in odf_list]
	for f_name, index, pin_name in odf_list:

            if f_name not in cache.keys():
                os.system(r'echo "default-on" > /sys/class/leds/ds:green:wlan/trigger')
  	        PIN = DAN.pull(f_name)
		cache[f_name] = PIN
            else:
	        PIN = cache[f_name]
	
            if PIN != None:
   
                check_list.remove(f_name)

                if PIN[index] != None:
                    client.put(pin_name, str(int(PIN[index])))
                else: 
                    continue
                
                if f_name not in check_list:
                    incomming[f_name] = (incomming[f_name] + 1) % 10000
                    #client.put('incomming_'+f_name, str(incomming[f_name]))
                    #print ('Bridge: change incomming state of '+f_name)

                print '{f}[{d}] -> {p} = {v}, incomming[{f}] = {i}'.format(
                        f=f_name,
                        d=index,
                        p=pin_name,
                        v=str(int(PIN[index])),
                        i=incomming[f_name],
                )
            os.system(r'echo "none" > /sys/class/leds/ds:green:wlan/trigger')


        for f_name, type_ in idf_list:
            tmp = client.get(f_name)
            if tmp is None:
                continue            
            else: 
                client.delete(f_name)    

            v = type_(tmp)
            if v is not None:
                os.system(r'echo "default-on" > /sys/class/leds/ds:green:wlan/trigger')
                
                if f_name in previous_counter:
                    v = v + previous_counter[f_name]
                    current_counter[f_name] = v
                    
                print 'DAN.push({f}, {v!r})'.format( f=f_name, v=v,)                    
                DAN.push(f_name, v)
                os.system(r'echo "none" > /sys/class/leds/ds:green:wlan/trigger')

        if (current_counter['Bugs'] != None) and (current_counter['RainMeter'] != None):
            f_cache.seek(0,0)
            f_cache.write( str(current_counter['Bugs']) +','+  str(current_counter['RainMeter']) +','+ timestamp +',')
    
    except Exception, e:
        print(e)
        client.put('Reg_done', '0')
        os.system(r'echo "none" > /sys/class/leds/ds:green:usb/trigger')
        DAN.device_registration_with_retry(custom.ServerIP)
        #os.system(r'echo "heartbeat" > /sys/class/leds/ds:green:usb/trigger')
        os.system(r'echo "timer" > /sys/class/leds/ds:green:usb/trigger')
        client.put('Reg_done', '1')
    
    
    if datetime.datetime.now().hour == 0 and not isChange:   # reset counter to zero at 00 o'clock
        client.put('resetCounter', '1')   
        previous_counter['Bugs'] = 0
        previous_counter['RainMeter'] = 0
        isChange = 1
        print ('Reset RainMeter counter.')

    if datetime.datetime.now().hour == 12:
        isChange = 0


    time.sleep(custom.Comm_interval)
