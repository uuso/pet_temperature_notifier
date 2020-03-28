#include "ArduinoJson.h" //https://arduinojson.org/v6/doc/
#include "DHT.h"

#define DHTPIN 2
#define DHTTYPE DHT11
#define DELAY_SEC 20
DHT dht(DHTPIN, DHTTYPE);
StaticJsonDocument<70> doc;

char tempstr[100];

void setup() {
  Serial.begin(9600);
  Serial.println("Start Serial");
  dht.begin();
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  bool err = (isnan(h) || isnan(t));

  doc["error"] = err;
  doc["temperature"] = t;  
  doc["humidity"] = h;

  serializeJson(doc, tempstr);
  Serial.println(tempstr);
  delay(1000 * DELAY_SEC);
}
