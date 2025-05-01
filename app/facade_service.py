import uuid
import random
import requests
from kafka import KafkaProducer
from flask import Flask, request, jsonify
import json
import time
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


def discover_service(service_name):
    index, nodes = consul_client.health.service(service_name, passing=True)
    print(f"++ discover_service({service_name}) index={index} nodes={nodes}")
    if nodes:
        service = random.choice(nodes)["Service"]
        address = service["Address"]
        port = service["Port"]
        return f"http://{address}:{port}/{service_name}"
    raise Exception(f"No available instances found for {service_name}")



def wait_for_kafka():
    retries = 10
    for i in range(retries):
        try:
            producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER])
            return producer
        except Exception as e:
            print(f"+ Retry {i+1}/{retries}: Kafka not available yet... {e}", flush=True)
            time.sleep(5)
    raise Exception("Kafka did not start in time!")



def send_to_logging_service(pair):
    try:
        logging_url = discover_service("logging_service")
        response = requests.post(logging_url, json=pair)
        response.raise_for_status()
        print(f"+ Status: Message sent to logging service {logging_url}", flush=True)
        return response
    except Exception as e:
        print(f"+ Failed to send message to logging service: {e}", flush=True)
        raise


def send_to_messages_service(pair):
    try:
        producer = wait_for_kafka()
        producer.send(MESSAGES_TOPIC, json.dumps(pair).encode('utf-8'))
        producer.flush()
        print("++ Status: Message sent to Kafka.", flush=True)
        return jsonify({"status": "Message sent successfully"}), 200
    except Exception as e:
        print(f"++ Kafka error: {str(e)}", flush=True)
        return jsonify({"error": f"Kafka error: {str(e)}"}), 503


def make_pair(data):
    if not data or "msg" not in data:
        return jsonify({"error": "Message is missing"}), 400
    msg = data["msg"]
    unique_id = str(uuid.uuid4())
    return {"id": unique_id, "msg": msg}


@app.route("/health")
def health():
    return "OK", 200


@app.route("/facade_service", methods=['POST', 'GET'])
def facade_controller():
    if request.method == "POST":
        pair = make_pair(request.json)
        if isinstance(pair, tuple):
            return pair
        try:
            send_to_logging_service(pair)
            send_to_messages_service(pair)
        except Exception as e:
            return jsonify({"error": f"Error sending to services: {str(e)}"}), 503
        return jsonify({"status": "Message processed successfully"}), 200

    if request.method == "GET":
        try:
            logging_url = discover_service("logging_service")
            messages_url = discover_service("messages_service")
            response_logging = requests.get(logging_url)
            response_messages = requests.get(messages_url)

            if response_logging.status_code != 200:
                return jsonify({"error": "Logging service is unavailable"}), 500
            if response_messages.status_code != 200:
                return jsonify({"error": "Messages service is unavailable"}), 500

            return "[" + response_logging.text + "] : " + response_messages.text

        except Exception as e:
            return jsonify({"error": f"Error fetching data from services: {str(e)}"}), 503

    return "Error", 400

if __name__ == "__main__":
    register_to_consul("facade_service", "facade-service-8080", 8080)
    app.run(debug=True, host="0.0.0.0", port=8080)
