#include <WiFi.h>
#include <HTTPClient.h>
#define BUZZER_PIN 27   // Buzzer connected to GPIO 27

// =========================
// WiFi Credentials
// =========================
const char* ssid = "iphone";
const char* password = "kkkkkkkk";

// =========================
// Telegram Bot Config
// =========================
String BOT_TOKEN = "8200554064:AAHzThu9q9WpHyBwGiHuJrliq3fuBY93SQo";
String CHAT_ID  = "-1003683765096";


// =========================
// TELEGRAM SEND FUNCTION
// =========================
void sendTelegramMessage(String message) {

  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;

    message.replace(" ", "%20");
    message.replace("\n", "%0A");

    String url = "https://api.telegram.org/bot" + BOT_TOKEN +
                 "/sendMessage?chat_id=" + CHAT_ID +
                 "&text=" + message;

    http.begin(url);
    int httpCode = http.GET();

    Serial.print("Telegram HTTP Code: ");
    Serial.println(httpCode);

    http.end();
  }
  else {
    Serial.println("WiFi not connected!");
  }
}


// =========================
// 🔴 RED ALERT → 15 sec continuous
// =========================
void redAlert() {

  Serial.println("🔴 RED ALERT TRIGGERED");

  digitalWrite(BUZZER_PIN, HIGH);   // ON (ACTIVE HIGH)
  delay(15000);                     // 15 seconds
  digitalWrite(BUZZER_PIN, LOW);    // OFF

  Serial.println("🔴 RED ALERT FINISHED");
}


// =========================
// 🟠 ORANGE ALERT → 3 short beeps
// =========================
void orangeAlert() {

  Serial.println("🟠 ORANGE ALERT TRIGGERED");

  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);  // ON
    delay(300);
    digitalWrite(BUZZER_PIN, LOW);   // OFF
    delay(300);
  }

  Serial.println("🟠 ORANGE ALERT FINISHED");
}


// =========================
// SETUP
// =========================
void setup() {

  Serial.begin(115200);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);   // OFF initially (ACTIVE HIGH)

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  sendTelegramMessage("✅ ESP32 Disaster Alert System Online");
}


// =========================
// LOOP
// =========================
void loop() {

  if (Serial.available()) {

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    Serial.print("Received Command: ");
    Serial.println(cmd);

    if (cmd == "BUZZ:RED") {
      redAlert();
    }
    else if (cmd == "BUZZ:ORANGE") {
      orangeAlert();
    }
  }
}