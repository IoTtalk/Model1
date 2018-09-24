import DAN

ServerIP = 'https://farm.iottalk.tw' 
Comm_interval = 15 # unit:second

def profile_init():
    DAN.profile['dm_name']='Model1'
    DAN.profile['d_name']= 'Set1' 

def odf():  # int only
    return [
        #('LED', 0, 'LED'),
    ]

def idf():
    return [
       ('AtPressure', int),
       ('Humidity', int),
       ('Temperature', float),
       ('RainMeter', float),
       ('CO2', float),       
       ('UV1', float),
       ('UV2', float),
       ('WindSpeed', float),
    ]
