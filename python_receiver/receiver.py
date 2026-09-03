"""
Receptor MQTT para a telemetria simulada do ESP32.

Desenvolvido para fins educacionais e de portfólio:
- demonstra assinatura de um tópico MQTT;
- transforma JSON em uma saída legível;
- registra as mensagens em um arquivo local;
- mantém a lógica pequena e fácil de adaptar para um projeto real.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt


DEFAULT_HOST = "test.mosquitto.org"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "portfolio/esp32/dht22/telemetry"
DEFAULT_CLIENT_ID = "python-telemetry-receiver"
DEFAULT_KEEPALIVE = 60
DEFAULT_LOG_FILE = "telemetry.log"


@dataclass(frozen=True)
class ReceiverConfig:
    """Configuração do receptor, centralizada para facilitar testes e uso local."""

    host: str
    port: int
    topic: str
    client_id: str
    keepalive: int
    log_file: str


def env_or_default(name: str, default: str) -> str:
    """Lê uma variável de ambiente, ignorando valores vazios."""

    return os.getenv(name, default).strip() or default


def parse_args() -> ReceiverConfig:
    """Combina argumentos de linha de comando com os padrões do projeto."""

    parser = argparse.ArgumentParser(
        description="Assina o tópico MQTT de telemetria do ESP32."
    )
    parser.add_argument("--host", default=env_or_default("MQTT_HOST", DEFAULT_HOST))
    parser.add_argument(
        "--port",
        type=int,
        default=int(env_or_default("MQTT_PORT", str(DEFAULT_PORT))),
    )
    parser.add_argument(
        "--topic", default=env_or_default("MQTT_TOPIC", DEFAULT_TOPIC)
    )
    parser.add_argument(
        "--client-id",
        default=env_or_default("MQTT_CLIENT_ID", DEFAULT_CLIENT_ID),
    )
    parser.add_argument(
        "--keepalive",
        type=int,
        default=int(env_or_default("MQTT_KEEPALIVE", str(DEFAULT_KEEPALIVE))),
    )
    parser.add_argument(
        "--log-file",
        default=env_or_default("MQTT_LOG_FILE", DEFAULT_LOG_FILE),
    )
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("--port deve estar entre 1 e 65535")
    if args.keepalive <= 0:
        parser.error("--keepalive deve ser maior que zero")

    return ReceiverConfig(
        host=args.host,
        port=args.port,
        topic=args.topic,
        client_id=args.client_id,
        keepalive=args.keepalive,
        log_file=args.log_file,
    )


def configure_logging(log_file: str) -> logging.Logger:
    """Configura o arquivo de telemetria sem duplicar mensagens no console."""

    logger = logging.getLogger("telemetry_receiver")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)
    return logger


def parse_payload(payload: bytes) -> dict[str, Any]:
    """Converte e valida o formato mínimo esperado do ESP32."""

    decoded = json.loads(payload.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("payload JSON precisa ser um objeto")

    required_fields = ("device_id", "temperature_c", "humidity_percent")
    missing_fields = [field for field in required_fields if field not in decoded]
    if missing_fields:
        raise ValueError(f"campos ausentes: {', '.join(missing_fields)}")
    return decoded


def format_reading(reading: dict[str, Any]) -> str:
    """Produz uma linha consistente para console e arquivo de log."""

    received_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    device_id = str(reading["device_id"])
    temperature = float(reading["temperature_c"])
    humidity = float(reading["humidity_percent"])
    timestamp_ms = reading.get("timestamp_ms", "n/a")
    return (
        f"{received_at} | device={device_id} | "
        f"temperatura={temperature:.2f} °C | "
        f"umidade={humidity:.2f} % | timestamp_ms={timestamp_ms}"
    )


def main() -> int:
    """Inicia o cliente, aguarda mensagens e encerra de forma previsível."""

    config = parse_args()
    logger = configure_logging(config.log_file)
    stop_requested = False

    def request_stop(_signum: int, _frame: Any) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    # Callback API v2 é explícita sobre flags e razão de desconexão.
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=config.client_id,
    )

    def on_connect(
        connected_client: mqtt.Client,
        _userdata: Any,
        _flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        if reason_code.is_failure:
            print(f"[MQTT] Falha ao conectar: {reason_code}", file=sys.stderr)
            return

        result, _mid = connected_client.subscribe(config.topic, qos=0)
        if result != mqtt.MQTT_ERR_SUCCESS:
            print(
                f"[MQTT] Falha ao assinar {config.topic}: {mqtt.error_string(result)}",
                file=sys.stderr,
            )
            return
        print(f"[MQTT] Conectado a {config.host}:{config.port}")
        print(f"[MQTT] Assinando: {config.topic}")
        print(f"[LOG] Gravando em: {config.log_file}")

    def on_message(
        _connected_client: mqtt.Client,
        _userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        try:
            reading = parse_payload(message.payload)
            formatted = format_reading(reading)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            print(f"[MQTT] Mensagem inválida ignorada: {error}", file=sys.stderr)
            return

        print(formatted, flush=True)
        logger.info(formatted)

    def on_disconnect(
        _connected_client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        if not stop_requested:
            print(
                f"[MQTT] Desconectado ({reason_code}); o cliente tentará reconectar.",
                file=sys.stderr,
            )

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print("Receptor MQTT iniciado. Pressione Ctrl+C para sair.")
    try:
        client.connect(config.host, config.port, config.keepalive)
        client.loop_start()
        while not stop_requested:
            signal.pause()
    except KeyboardInterrupt:
        pass
    except (OSError, mqtt.MqttException) as error:
        print(f"[MQTT] Não foi possível iniciar o receptor: {error}", file=sys.stderr)
        return 1
    finally:
        client.loop_stop()
        client.disconnect()
        logger.handlers[0].close()

    print("\nReceptor encerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
