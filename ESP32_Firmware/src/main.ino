#include <WiFi.h>
#include <time.h>

// Definições dos pinos para o sensor ultrassônico
#define TRIG_PIN 23
#define ECHO_PIN 22

// --- Configurações para o Wokwi ---
// O Wokwi simula uma rede Wi-Fi chamada "Wokwi-GUEST" sem senha.
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

void setup() {
  Serial.begin(115200);
  // Adiciona um pequeno atraso para garantir que o Monitor Serial esteja pronto
  delay(1000); 
  Serial.println("Iniciando o setup()...");
  Serial.flush(); // Garante que a mensagem seja enviada

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.println("Pinos do sensor configurados.");
  Serial.flush();

  // --- Conexão Wi-Fi com Timeout ---
  Serial.print("Conectando à rede Wi-Fi simulada: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA); // Definir o modo Station explicitamente
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startWifi = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // Se não conectar em 15 segundos, reinicia.
    if (millis() - startWifi > 15000) { 
      Serial.println("\nFalha ao conectar ao Wi-Fi! Reiniciando...");
      delay(1000);
      ESP.restart();
    }
  }
  Serial.println("\nWi-Fi conectado com sucesso!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
  Serial.flush();

  // --- Sincronização de Horário via NTP com Timeout ---
  configTime(-3 * 3600, 0, "pool.ntp.org");

  struct tm timeinfo;
  Serial.println("Aguardando sincronização de horário (NTP)...");
  unsigned long startNtp = millis();
  while (!getLocalTime(&timeinfo)) {
    delay(1000);
    Serial.println("Falha na sincronização, tentando novamente...");
    // Se não sincronizar em 20 segundos, reinicia.
    if (millis() - startNtp > 20000) { 
        Serial.println("Falha ao sincronizar o horário via NTP. Reiniciando...");
        delay(1000);
        ESP.restart();
    }
  }
  Serial.println("Horário sincronizado com sucesso!");
  Serial.flush();

  // Imprime o cabeçalho do CSV para o script Python
  Serial.println("data_hora,distancia_cm");
}

void loop() {
  // --- Leitura do Sensor HC-SR04 ---
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  float distance_cm = duration * 0.034 / 2;

  // --- Obtenção da Data e Hora ---
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char timeString[20];
    // Formata a data e hora no padrão "AAAA-MM-DD HH:MM:SS"
    strftime(timeString, sizeof(timeString), "%Y-%m-%d %H:%M:%S", &timeinfo);
    
    // Envia os dados pela porta serial no formato CSV
    Serial.print(timeString);
    Serial.print(",");
    Serial.println(distance_cm);
  } else {
    Serial.println("Falha ao obter a hora local.");
  }

  // Aguarda um intervalo entre as leituras
  delay(500);
}

