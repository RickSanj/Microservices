import uuid
import random
import requests
from kafka import KafkaProducer
from flask import Flask, request, jsonify
import json
import time

app = Flask(__name__)

KAFKA_BROKER = ["kafka-server:9092"]

MESSAGES_TOPIC = "messages_topic"

LOGGING_SERVICE_URLS = [
    "http://logging-service1:8081/logging_service",
    "http://logging-service2:8082/logging_service",
    "http://logging-service3:8083/logging_service",
]
MESSAGES_SERVICE_URLS = [
    "http://messages-service1:8084/messages_service",
    "http://messages-service2:8085/messages_service",
]


def wait_for_kafka():
    retries = 10
    for i in range(retries):
        try:
            producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
            return producer
        except Exception as e:
            print(
                f"+ Retry {i+1}/{retries}: Kafka not available yet... {e}", flush=True)
            time.sleep(5)
    raise Exception("Kafka did not start in time!")


def send_to_logging_service(pair):
    for logging_service_url in random.sample(LOGGING_SERVICE_URLS, len(LOGGING_SERVICE_URLS)):
        try:
            response = requests.post(logging_service_url, json=pair)
            response.raise_for_status()
            print(
                f"+ Status: Message sent to logging service {logging_service_url}", flush=True)
            return response
        except requests.exceptions.RequestException:
            print(
                f"+ Failed to send message to {logging_service_url}", flush=True)
            continue
    raise requests.exceptions.RequestException(
        "All logging service instances are unavailable.")


def send_to_messages_service(pair):
    try:
        # Ensure Kafka producer is initialized on every request
        producer = wait_for_kafka()
        producer.send(MESSAGES_TOPIC, json.dumps(pair).encode('utf-8'))
        producer.flush()
        print("+ Status: Message sent to Kafka.", flush=True)
        return jsonify({"status": "Message sent successfully"}), 200
    except Exception as e:
        print(f"+ Kafka error: {str(e)}", flush=True)
        return jsonify({"error": f"Kafka error: {str(e)}"}), 503


def make_pair(data):
    if not data or "msg" not in data:
        return jsonify({"error": "Message is missing"}), 400
    msg = data["msg"]
    unique_id = str(uuid.uuid4())
    return {"id": unique_id, "msg": msg}


@app.route("/facade_service", methods=['POST', 'GET'])
def facade_controller():
    """
    Facade service function to handle POST and GET requests.
    """
    if request.method == "POST":
        pair = make_pair(request.json)
        if isinstance(pair, tuple):  # Check for error from make_pair
            return pair

        # Send to logging and messages services
        try:
            send_to_logging_service(pair)
            send_to_messages_service(pair)
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Error sending to services: {str(e)}"}), 503

        return jsonify({"status": "Message processed successfully"}), 200

    if request.method == "GET":
        logging_url = random.choice(LOGGING_SERVICE_URLS)
        messages_url = random.choice(MESSAGES_SERVICE_URLS)

        try:
            response_logging = requests.get(logging_url)
            response_messages = requests.get(messages_url)

            if response_logging.status_code != 200:
                return jsonify({"error": "Logging service is unavailable"}), 500

            if response_messages.status_code != 200:
                return jsonify({"error": "Messages service is unavailable"}), 500

            concatenated_response = "[" + response_logging.text + \
                "] : " + response_messages.text
            return concatenated_response

        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Error fetching data from services: {str(e)}"}), 503

    return "Error", 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
