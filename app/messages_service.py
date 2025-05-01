import argparse
import json
import threading
from flask import Flask, jsonify
from kafka import KafkaConsumer
import consul
import socket


app = Flask(__name__)
consul_client = consul.Consul(host='consul-server', port=8500)


def get_kv_value(key):
    index, data = consul_client.kv.get(key)
    if data and 'Value' in data:
        return data['Value'].decode('utf-8') if isinstance(data['Value'], bytes) else data['Value']
    return None


def get_kafka_config():
    kafka_address = get_kv_value('kafka/address')
    kafka_topic = get_kv_value('kafka/messages_topic')
    
    if not kafka_address or not kafka_topic:
        raise Exception("Kafka configuration not found in Consul.")
    return kafka_address, kafka_topic


KAFKA_BROKER, MESSAGES_TOPIC = get_kafka_config()
messages = []


def register_to_consul(service_name, service_id, port):
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"++ hostname={hostname}", flush=True)
    print(f"++ ip_address={ip_address}", flush=True)
    consul_client.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=ip_address,
        port=port,
        check={
            "http": f"http://{ip_address}:{port}/health",
            "interval": "10s"
        }
    )
    print(f"+ Registered {service_name} with ID {service_id}", flush=True)


def consume_messages():
    consumer = KafkaConsumer(
        MESSAGES_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    for message in consumer:
        messages.append(message.value)
        print(f"+ Received and stored: {message.value}", flush=True)

consumer_thread = threading.Thread(target=consume_messages, daemon=True)
consumer_thread.start()


@app.route("/health")
def health():
    return "OK", 200


@app.route("/messages_service", methods=["GET"])
def get_messages():
    """
    Returns all stored messages for this instance.
    """
    if not messages:
        return jsonify({"message": "No messages available"}), 404

    return jsonify(messages), 200


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run messages service on a specified port.")
    parser.add_argument('--port', type=int, default=8084, help="Port for the messages service")
    args = parser.parse_args()

    register_to_consul(f"messages_service", f"messages-service-{str(args.port-3)[-1:]}-{args.port}", args.port)

    app.run(debug=True, host='0.0.0.0', port=args.port)
