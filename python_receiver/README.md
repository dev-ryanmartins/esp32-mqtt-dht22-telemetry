# Python MQTT Receiver

Receptor educacional que assina `portfolio/esp32/dht22/telemetry`, mostra as
leituras do ESP32 em tempo real e salva as mensagens recebidas em
`telemetry.log`.

O código foi desenvolvido para fins **educacionais e de portfólio**. Ele inclui
validação básica do JSON, tratamento de reconexão e encerramento limpo com
`Ctrl+C`.

## Instalação

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

## Execução

```bash
python receiver.py
```

O broker, o tópico e o arquivo de log podem ser personalizados com variáveis de
ambiente ou argumentos:

```bash
MQTT_HOST=test.mosquitto.org \
MQTT_TOPIC=portfolio/esp32/dht22/telemetry \
python receiver.py --log-file ./telemetry.log
```

## Formato do log

Cada linha contém o horário local de recebimento, o identificador do dispositivo,
temperatura em Celsius, umidade relativa e timestamp enviado pelo ESP32:

```text
2026-09-03 12:00:00 | device=esp32-dht22-simulator | temperatura=24.80 °C | umidade=58.40 % | timestamp_ms=123456
```
