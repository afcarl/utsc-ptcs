
#include <ESP8266WiFi.h>
#include <WiFiUDP.h>
//#include "adc.h"
ADC_MODE(0);


WiFiUDP UDP;
boolean udpConnected = false;
boolean wifiConnected = false;

const char* ssid = "Observatory";
const char* password = "";

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);     // Initialize the LED_BUILTIN pin as an output
  Serial.begin(115200);
  Serial.println("ADC UDP Spammer");

  WiFi.begin(ssid);
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_BUILTIN, LOW);   // Turn the LED on (Note that LOW is the voltage level
    delay(250);
    digitalWrite(LED_BUILTIN, HIGH);   // Turn the LED on (Note that LOW is the voltage level
    delay(250);
    Serial.print(".");
  }
  UDP.begin(8080);
}


void loop()
{
  digitalWrite(LED_BUILTIN, LOW);   // Turn the LED on (Note that LOW is the voltage level

  byte error, address;
  int rdata;
  int nDevices;

  Serial.print("B ");

  
  int val = analogRead(A0);
  int val1 = val >>8;
  int val2 = val;
  Serial.println(val);
  //UDP.beginPacket("142.1.110.2", 8087);
  UDP.beginPacket("142.1.110.9", 8087);
  UDP.write(val1);
  UDP.write(val2);
  
  UDP.endPacket();
  digitalWrite(LED_BUILTIN, HIGH);  // Turn the LED off by making the voltage HIGH  
  delay(100);
}
