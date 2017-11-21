
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <WiFiUDP.h>

WiFiUDP UDP;
boolean udpConnected = false;
boolean wifiConnected = false;

const char* ssid = "Observatory";
//const char* password = "";

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);     // Initialize the LED_BUILTIN pin as an output
  Serial.begin(115200);
  Serial.println("I2C UDP Spammer");

  WiFi.begin(ssid);
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_BUILTIN, LOW);   // Turn the LED on (Note that LOW is the voltage level
    delay(250);
    digitalWrite(LED_BUILTIN, HIGH);   // Turn the LED on (Note that LOW is the voltage level
    delay(250);
    Serial.print(".");
  }
  UDP.begin(8080);

  Wire.begin(D3, D2);

}

int getOneByte(int adr){
  Wire.beginTransmission(0x68);
  Wire.write(adr);
  Wire.endTransmission();   
  Wire.requestFrom(0x68,1);
  return Wire.read();
}

int getOneWord(int adr){
  int high = getOneByte(adr);
  int low  = getOneByte(adr+1);
  int val = (high << 8) + low;
  if (val >= 0x8000){
    return -((65535 - val)+1);
  }else{
    return val;
  }
}


void loop()
{
  digitalWrite(LED_BUILTIN, LOW);   // Turn the LED on (Note that LOW is the voltage level

  byte error, address;
  int rdata;
  int nDevices;

  Serial.print("B");

  Wire.beginTransmission(0x68);
  Wire.write(0x6b);
  Wire.write(0x00);
  error = Wire.endTransmission();

  int val = 0;
  Serial.println("U");
  
  UDP.beginPacket("142.1.110.9", 8086);
  val = getOneByte(0x3b);
  UDP.write(val);
  val = getOneByte(0x3b+1);
  UDP.write(val);
  val = getOneByte(0x3d);
  UDP.write(val);
  val = getOneByte(0x3d+1);
  UDP.write(val);
  val = getOneByte(0x3f);
  UDP.write(val);
  val = getOneByte(0x3f+1);
  UDP.write(val);
   
  int z = 0;
  UDP.write(z);
  UDP.write(z);
  UDP.write(z);
  
  //val = getOneWord(0x3d);
  //UDP.write(val);
  //val = getOneWord(0x3f);
  //UDP.write(val); 
  UDP.endPacket();
  digitalWrite(LED_BUILTIN, HIGH);  // Turn the LED off by making the voltage HIGH  
  delay(100);
}
