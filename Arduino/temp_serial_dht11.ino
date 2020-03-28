#include "ArduinoJson.h" //https://arduinojson.org/v6/doc/
#include "DHT.h"

#define DHTPIN 2
#define DHTTYPE DHT11
#define DELAY_SEC 5
DHT dht(DHTPIN, DHTTYPE);
StaticJsonDocument<70> doc;

//byte subtimer = 0; // помогает считать минуты
//unsigned int uptime = 0; // 0..65535 - считает в минутах

char tempstr[100];

void setup() {
  Serial.begin(9600);
  Serial.println("oooh my");
  dht.begin();
}

void loop() {
  delay(1000 * DELAY_SEC);
//  // будет показывать от 0 до 20160 минут аптайма
//  if (uptime < 60 * 24 * 14) { // 20160 min = 2 weeks
//    subtimer += DELAY_SEC;
//    if (subtimer >= 60) {
//      uptime++;
//      subtimer = 0;
//    }
//  }
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  bool err = (isnan(h) || isnan(t));

  doc["error"] = err;
  doc["humidity"] = h;
  doc["temperature"] = t;
//  doc["uptime_min"] = uptime;
  

  serializeJson(doc, tempstr);
  Serial.println(tempstr);
}
