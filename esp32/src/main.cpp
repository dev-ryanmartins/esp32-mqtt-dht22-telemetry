/*
 * ESP32 MQTT DHT22 Telemetry
 *
 * Desenvolvido para fins educacionais e de portfólio.
 * Este firmware simula as leituras de um DHT22 para que o fluxo MQTT possa ser
 * estudado mesmo sem o sensor físico conectado.
 *
 * Para usar um DHT22 real:
 * 1. Instale a biblioteca "DHT sensor library".
 * 2. Conecte DATA ao GPIO 4 e faça a ligação descrita no README.md.
 * 3. Substitua readSimulatedSensor() por uma leitura da biblioteca DHT.
 */

#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>

// ---------------------------------------------------------------------------
// Configurações do projeto
// ---------------------------------------------------------------------------
// Nunca versionar credenciais reais. Para um projeto real, use um mecanismo
// seguro de secrets ou uma configuração local ignorada pelo Git.
const char *WIFI_SSID = "SUA_REDE_WIFI";
const char *WIFI_PASSWORD = "SUA_SENHA_WIFI";

// Broker público para demonstração. Use TLS + autenticação em produção.
const char *MQTT_HOST = "test.mosquitto.org";
const uint16_t MQTT_PORT = 1883;
const char *MQTT_TOPIC = "portfolio/esp32/dht22/telemetry";
const char *MQTT_CLIENT_ID = "esp32-dht22-simulator";

const unsigned long PUBLISH_INTERVAL_MS = 5000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
unsigned long lastPublishAt = 0;

struct SensorReading {
  float temperatureC;
  float humidityPercent;
};

void connectToWiFi() {
  Serial.printf("Conectando ao Wi-Fi: %s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.printf("\nWi-Fi conectado. IP: %s\n", WiFi.localIP().toString().c_str());
}

void connectToMqtt() {
  while (!mqttClient.connected()) {
    Serial.printf("Conectando ao broker MQTT %s:%u...\n", MQTT_HOST, MQTT_PORT);

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println("MQTT conectado.");
      return;
    }

    Serial.printf("Falha MQTT, estado=%d. Nova tentativa em 2 segundos.\n",
                  mqttClient.state());
    delay(2000);
  }
}

SensorReading readSimulatedSensor() {
  /*
   * Simulação determinística e suave:
   * - fmod() cria uma variação cíclica semelhante a um ambiente real;
   * - random() adiciona uma pequena oscilação;
   * - os limites mantêm os dados plausíveis para uma demonstração.
   */
  const float phase = static_cast<float>(millis() % 60000) / 60000.0f;
  const float wave = sin(phase * TWO_PI);

  SensorReading reading;
  reading.temperatureC = 24.0f + (wave * 2.0f) +
                         (static_cast<float>(random(-20, 21)) / 100.0f);
  reading.humidityPercent = 58.0f - (wave * 5.0f) +
                            (static_cast<float>(random(-50, 51)) / 100.0f);
  return reading;
}

String buildPayload(const SensorReading &reading) {
  // JSON manual mantém o exemplo simples e sem dependências extras.
  String payload = "{";
  payload += "\"device_id\":\"";
  payload += MQTT_CLIENT_ID;
  payload += "\",\"temperature_c\":";
  payload += String(reading.temperatureC, 2);
  payload += ",\"humidity_percent\":";
  payload += String(reading.humidityPercent, 2);
  payload += ",\"simulated\":true,\"timestamp_ms\":";
  payload += String(millis());
  payload += "}";
  return payload;
}

void publishReading() {
  const SensorReading reading = readSimulatedSensor();
  const String payload = buildPayload(reading);

  if (mqttClient.publish(MQTT_TOPIC, payload.c_str())) {
    Serial.printf("Publicado em %s: %s\n", MQTT_TOPIC, payload.c_str());
  } else {
    Serial.println("Falha ao publicar a leitura MQTT.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Seed simples para que cada execução varie levemente a simulação.
  randomSeed(static_cast<unsigned long>(analogRead(0)));
  connectToWiFi();

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  connectToMqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!mqttClient.connected()) {
    connectToMqtt();
  }
  mqttClient.loop();

  const unsigned long now = millis();
  if (now - lastPublishAt >= PUBLISH_INTERVAL_MS) {
    lastPublishAt = now;
    publishReading();
  }
}
