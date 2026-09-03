# ESP32 MQTT DHT22 Telemetry

Projeto educacional e de portfólio que demonstra um fluxo completo de telemetria IoT:

1. O ESP32 simula leituras de temperatura e umidade como se viessem de um DHT22.
2. Os valores são publicados em JSON via MQTT.
3. Um receptor Python assina o mesmo tópico, imprime as mensagens em tempo real e
   grava cada leitura em `telemetry.log`.

> **Aviso:** o broker público é compartilhado e serve apenas para demonstração.
> Não publique dados sensíveis nele. Para uso real, troque por um broker próprio
> com autenticação e TLS.

## Estrutura

```text
.
├── esp32/
│   ├── platformio.ini
│   └── src/
│       └── main.cpp
├── python_receiver/
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   └── receiver.py
├── .gitignore
└── README.md
```

## Arquitetura da comunicação

```text
┌────────────────────┐       MQTT publish        ┌──────────────────────┐
│ ESP32               │ ───────────────────────▶ │ Broker público       │
│ Wi-Fi + DHT22      │  esp32/dht22/telemetry   │ test.mosquitto.org   │
└────────────────────┘                           └──────────┬───────────┘
                                                            │ MQTT subscribe
                                                            ▼
                                                 ┌──────────────────────┐
                                                 │ python_receiver       │
                                                 │ console + telemetry.log│
                                                 └──────────────────────┘
```

O tópico padrão é `portfolio/esp32/dht22/telemetry`. Ele está definido nos dois
programas e pode ser alterado por configuração.

## Diagrama de conexões do DHT22

O firmware atual usa um sensor **simulado** para fins educacionais. Se você
quiser trocar a simulação por um DHT22 físico, faça as conexões abaixo:

```text
DHT22 (vista frontal, grade voltada para você)

  ┌───────────────┐
  │ 1   2   3   4 │
  └─┬───┬───┬───┬─┘
    │   │   │   │
   3V3 DATA NC  GND
        │
        └── resistor pull-up de 10 kΩ para 3V3

DATA ───────── GPIO 4 do ESP32
VCC  ───────── 3V3
GND  ───────── GND
```

Não conecte o pino NC. Alguns módulos DHT22 já incluem o resistor de pull-up;
nesse caso, não é necessário adicionar outro.

## Dependências

### Firmware ESP32

- VS Code com PlatformIO, ou PlatformIO CLI
- Placa compatível com ESP32
- Framework Arduino
- Bibliotecas PlatformIO:
  - `WiFi` (incluída no core ESP32)
  - `PubSubClient`

### Receptor Python

- Python 3.9 ou mais recente
- `paho-mqtt`, instalado com:

```bash
cd python_receiver
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

## Como executar

### 1. Inicie o receptor Python

O receptor já usa o broker e o tópico padrão do projeto:

```bash
cd python_receiver
python receiver.py
```

Para configurar via variáveis de ambiente:

```bash
cp .env.example .env
# edite .env se necessário
MQTT_HOST=test.mosquitto.org MQTT_PORT=1883 python receiver.py
```

O arquivo `telemetry.log` será criado na pasta `python_receiver/`. Pressione
`Ctrl+C` para encerrar com segurança.

Exemplo de saída:

```text
[2026-09-03 12:00:00] ESP32-SIMULATED | temperatura=24.80 °C | umidade=58.40 % | timestamp=2026-09-03T15:00:00Z
```

### 2. Configure e carregue o firmware

Edite as constantes `WIFI_SSID` e `WIFI_PASSWORD` no início de
`esp32/src/main.cpp`. Em seguida:

```bash
cd esp32
pio run --target upload
pio device monitor
```

O ESP32 publicará uma mensagem a cada 5 segundos. O payload tem este formato:

```json
{
  "device_id": "esp32-dht22-simulator",
  "temperature_c": 24.8,
  "humidity_percent": 58.4,
  "simulated": true,
  "timestamp_ms": 123456
}
```

## Boas práticas para evoluir o projeto

- Substitua o broker público por um broker próprio antes de qualquer uso
  operacional.
- Ative MQTT sobre TLS e autenticação.
- Mova SSID e senha para um mecanismo seguro de secrets em vez de versioná-los.
- Para um DHT22 real, adicione a biblioteca `DHT sensor library` e troque
  `readSimulatedSensor()` por uma leitura do GPIO.
- Considere QoS 1, retained messages e uma estratégia de reconexão adequada para
  ambientes com conectividade instável.

## Finalidade

Este repositório foi desenvolvido para **fins educacionais e de portfólio**.
Os comentários no código destacam as decisões para facilitar estudo,
apresentação técnica e futuras extensões.
