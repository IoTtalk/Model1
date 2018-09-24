#include <Wire.h>
#include "Seeed_BME280.h"
#include <SoftwareSerial.h>
#include <Bridge.h>

#define windPin  A0   //風速計 
#define UVpin1   A1   // UV
#define UVpin2   A2   // 光度
#define RainPin  7    //雨量計    D3(interrupt0), D2(interrupt1), D0(interrupt2), D1(interrupt3) and D7(interrupt4).
#define SOFT_TX  10   //to CO2 RX
#define SOFT_RX  11   //to CO2 TX
SoftwareSerial mySerial(SOFT_RX, SOFT_TX); // RX, TX
BME280 bme280;        //大氣壓  D2(SDA), D3(SCL)

float RainMeter = 0.0;
long suspendTimestamp = 0;
void blink(){//rain
    if (millis()-suspendTimestamp > 200){
        RainMeter += 0.2;
        suspendTimestamp = millis();
    }
}

 unsigned int fetch_CO2_ppm(){
    unsigned char CO2_Read[]={0x42,0x4d,0xe3,0x00,0x00,0x01,0x72};
    unsigned char CO2_val[24],num=0;
    mySerial.flush();
    mySerial.write(CO2_Read,7);
    for(unsigned char i=0;i<100;i++){
        delay(1);
        if(mySerial.available()==12){
            while(mySerial.available()){
                CO2_val[num] = mySerial.read();
                num++;
            }
            break;
        }
    }
    return CO2_val[4]*256+CO2_val[5]; 
}

void setup() {
    Serial.begin(115200); //for debug message

    mySerial.begin(9600);  //for CO2 communication
    if(!bme280.init()) Serial.println("Sensor Error!");     //BME 大氣壓 D2, D3
    pinMode(windPin,INPUT);          
    pinMode(UVpin1,INPUT);           
    pinMode(UVpin2,INPUT);           
    pinMode(RainPin , INPUT_PULLUP); 
    attachInterrupt(digitalPinToInterrupt(RainPin), blink, RISING); //雨量計 register to D7 interrupt 

    pinMode(13,OUTPUT); //IoTtalk successful registration notification
    Bridge.begin();   // D0 and D1 are used by the Bridge library.
}

void loop() {
    char D13[2];
    char valueStr[23];
    unsigned int valueInt=0;
    
    Bridge.get("Reg_done",  D13, 2);
    digitalWrite(13, atoi(D13));    
      
    //風速計 A0
    float windSensorValue = float(analogRead(windPin));
    if (windSensorValue < 81.84) windSensorValue =0.0;
    else windSensorValue =  (windSensorValue-81.84) * 0.09897;
    dtostrf(windSensorValue, 10, 5, valueStr);
    Bridge.put("WindSpeed", valueStr); 
    Serial.print("Wind: ");    Serial.println(valueStr);   // unit: m/s
   
    //UV sensor A1
    valueInt = analogRead(UVpin1);     
    itoa(valueInt, valueStr, 10);
    Bridge.put("UV1", valueStr); 
    Serial.print("UV1: ");    Serial.println(valueStr);   // unit: Voltage index
        
    //UV sensor A2
    valueInt = analogRead(UVpin2);
    itoa(valueInt, valueStr, 10);    
    Bridge.put("UV2", valueStr); 
    Serial.print("UV2: ");    Serial.println(valueStr);   

    //BME 大氣壓   D2, D3
    float Temperature = bme280.getTemperature();
    uint32_t AtmosphericPressure = bme280.getPressure();
    uint32_t Humidity = bme280.getHumidity();
    dtostrf(Temperature, 6, 2, valueStr);
    Bridge.put("Temperature", valueStr); 
    dtostrf(AtmosphericPressure, 8, 0, valueStr);
    Bridge.put("AtPressure", valueStr);     
    dtostrf(Humidity, 8, 0, valueStr);
    Bridge.put("Humidity", valueStr);        
    Serial.print("Temp: ");        Serial.print(Temperature);    Serial.println(" C");// unit: C
    Serial.print("Pressure: ");    Serial.print(AtmosphericPressure);    Serial.println(" Pa");     // unit: Pa
    Serial.print("Altitude: ");    Serial.print(bme280.calcAltitude(AtmosphericPressure));    Serial.println(" m");  // unit: meter
    Serial.print("Humidity: ");    Serial.print(Humidity);    Serial.println(" %"); // unit:%

    //雨量計 D7 interrupt4   
    dtostrf(RainMeter, 6, 2, valueStr);
    Bridge.put("RainMeter", valueStr);        
    Serial.print("RainMeter: ");    Serial.println(RainMeter);   // unit:mm    

    //CO2 DS-CO2-20
    valueInt = fetch_CO2_ppm();
    itoa(valueInt, valueStr, 10);
    Bridge.put("CO2", valueStr);
    Serial.print("CO2: ");    Serial.print(valueStr);   Serial.println(" ppm"); // unit:ppm
   
    Serial.println("=========================================================================");    

    Bridge.get("resetCounter",  valueStr, 5);
    if (strcmp(valueStr,"") != 0){
        RainMeter = 0;
        Bridge.put("resetCounter", "");
    }
    
    delay(1000);
}
