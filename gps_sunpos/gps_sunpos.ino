#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <TinyGPS++.h>

#include <math.h>
#include <stdio.h>

static const uint32_t GPSBaud = 9600;

// The TinyGPS++ object
TinyGPSPlus gps;

// The serial connection to the GPS device
HardwareSerial ss(2);


const char* ssid = "UPSTAIRS";
const char* password = "Recurser";

WebServer server(80);



void get_sun_pos(float latitude, float longitude, int year, int month, int day, float UTHours, float UTMinutes, float UTSeconds, float *altitude, float *azimuth) {
  float zenith;
  float pi = 3.14159265358979323;
  float twopi = (2 * pi);
  float rad = (pi / 180);
  float EarthMeanRadius = 6371.01; // In km
  float AstronomicalUnit = 149597890.; // In km
  float DecimalHours = UTHours + (UTMinutes + UTSeconds / 60.0 ) / 60.0;
  long liAux1 = (month - 14) / 12;
  long liAux2 = (1461 * (year + 4800 + liAux1)) / 4 + (367 * (month - 2 - 12 * liAux1)) / 12 - (3 * (year + 4900 + liAux1) / 100) / 4 + day - 32075;
  float JulianDate = (liAux2) - 0.5 + DecimalHours / 24.0;
  float ElapsedJulianDays = JulianDate - 2451545.0;
  float Omega = 2.1429 - 0.0010394594 * ElapsedJulianDays;
  float MeanLongitude = 4.8950630 + 0.017202791698 * ElapsedJulianDays; // Radians
  float MeanAnomaly = 6.2400600 + 0.0172019699 * ElapsedJulianDays;
  float EclipticLongitude = MeanLongitude + 0.03341607 * sin( MeanAnomaly ) + 0.00034894 * sin( 2 * MeanAnomaly ) - 0.0001134 - 0.0000203 * sin(Omega);
  float EclipticObliquity = 0.4090928 - 6.2140e-9 * ElapsedJulianDays + 0.0000396 * cos(Omega);
  float Sin_EclipticLongitude = sin( EclipticLongitude );
  float Y = cos( EclipticObliquity ) * Sin_EclipticLongitude;
  float X = cos( EclipticLongitude );
  float RightAscension = atan2( Y, X );
  if ( RightAscension < 0.0 ) RightAscension = RightAscension + twopi;
  float Declination = asin( sin( EclipticObliquity ) * Sin_EclipticLongitude );
  float GreenwichMeanSiderealTime = 6.6974243242 + 0.0657098283 * ElapsedJulianDays + DecimalHours;
  float LocalMeanSiderealTime = (GreenwichMeanSiderealTime * 15 + longitude) * rad;
  float HourAngle = LocalMeanSiderealTime - RightAscension;
  float LatitudeInRadians = latitude * rad;
  float Cos_Latitude = cos( LatitudeInRadians );
  float Sin_Latitude = sin( LatitudeInRadians );
  float Cos_HourAngle = cos( HourAngle );
  float UTSunCoordinatesZenithAngle = (acos( Cos_Latitude * Cos_HourAngle * cos(Declination) + sin( Declination ) * Sin_Latitude));
  Y = -sin( HourAngle );
  X = tan( Declination ) * Cos_Latitude - Sin_Latitude * Cos_HourAngle;
  float UTSunCoordinatesAzimuth = atan2( Y, X );
  if ( UTSunCoordinatesAzimuth < 0.0 )
    UTSunCoordinatesAzimuth = UTSunCoordinatesAzimuth + twopi;
  UTSunCoordinatesAzimuth = UTSunCoordinatesAzimuth / rad;
  float Parallax = (EarthMeanRadius / AstronomicalUnit) * sin(UTSunCoordinatesZenithAngle);
  UTSunCoordinatesZenithAngle = (UTSunCoordinatesZenithAngle + Parallax) / rad;
  *azimuth = UTSunCoordinatesAzimuth;
  zenith = UTSunCoordinatesZenithAngle;
  *altitude = 90. - UTSunCoordinatesZenithAngle;
}




void handleSun() {
  
  float alt, az;
  get_sun_pos(gps.location.lat(), gps.location.lng(), gps.date.year(), gps.date.month(), gps.date.day(), gps.time.hour(), gps.time.minute(), gps.time.second(), &alt, &az);

 String result = "Alt: " + String(alt) + " Az: " + String(az);
 server.send(200, "text/plain", result);
}

void handleRoot() {
  server.send(200, "text/plain", "hello from esp8266!");
}
void handleGPS() {

  String result = F("Location: ");
  if (gps.location.isValid())
  {
    result += gps.location.lat();
    result += ",";
    result += gps.location.lng();
  }
  else
  {
    result += "INVALID";
  }

  result += F("  Date/Time: ");
  if (gps.date.isValid())
  {
    result += gps.date.month();
    result += F("/");
    result += gps.date.day();
    result += F("/");
    result += gps.date.year();
  }
  else
  {
    result += F("INVALID");
  }

  result += F(" ");
  if (gps.time.isValid())
  {
    if (gps.time.hour() < 10) result += F("0");
    result += gps.time.hour();
    result += F(":");
    if (gps.time.minute() < 10) result += F("0");
    result += gps.time.minute();
    result += F(":");
    if (gps.time.second() < 10) result += F("0");
    result += gps.time.second();
    result += F(".");
    if (gps.time.centisecond() < 10) result += F("0");
    result += gps.time.centisecond();
  }
  else
  {
    result += F("INVALID");
  }
  server.send(200, "text/plain", result);

}

void handleNotFound() {
  server.send(404, "text/plain", "Not found");
}

void setupWifi(void) {
  Serial.println("Setup wifi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("Begin");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Setup wifi");

  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  if (MDNS.begin("gps")) {
    Serial.println("MDNS responder started");
  }
}

void setupHTTP(void) {
  server.on("/", handleRoot);
  server.on("/gps", handleGPS);
  server.on("/sun", handleSun);

  server.on("/inline", []() {
    server.send(200, "text/plain", "this works as well");
  });
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP server started");
}



void displayInfo()
{
  Serial.print(F("Location: "));
  if (gps.location.isValid())
  {
    Serial.print(gps.location.lat(), 6);
    Serial.print(F(","));
    Serial.print(gps.location.lng(), 6);
  }
  else
  {
    Serial.print(F("INVALID"));
  }

  Serial.print(F("  Date/Time: "));
  if (gps.date.isValid())
  {
    Serial.print(gps.date.month());
    Serial.print(F("/"));
    Serial.print(gps.date.day());
    Serial.print(F("/"));
    Serial.print(gps.date.year());
  }
  else
  {
    Serial.print(F("INVALID"));
  }

  Serial.print(F(" "));
  if (gps.time.isValid())
  {
    if (gps.time.hour() < 10) Serial.print(F("0"));
    Serial.print(gps.time.hour());
    Serial.print(F(":"));
    if (gps.time.minute() < 10) Serial.print(F("0"));
    Serial.print(gps.time.minute());
    Serial.print(F(":"));
    if (gps.time.second() < 10) Serial.print(F("0"));
    Serial.print(gps.time.second());
    Serial.print(F("."));
    if (gps.time.centisecond() < 10) Serial.print(F("0"));
    Serial.print(gps.time.centisecond());
  }
  else
  {
    Serial.print(F("INVALID"));
  }

  Serial.println();
}



void setup(void) {
  Serial.begin(115200);
  ss.begin(9600);
  setupWifi();
  setupHTTP();
}


void loop(void) { 

  
  server.handleClient();

  // This sketch displays information every time a new sentence is correctly encoded.
  while (ss.available() > 0) {
    int c = ss.read();
    if (gps.encode(c))
      displayInfo();
  }
  if (millis() > 5000 && gps.charsProcessed() < 10)
  {
    Serial.println(F("No GPS detected: check wiring."));
    while (true);
  }
  
}
