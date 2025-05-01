import argparse
import json
import threading
from flask import Flask, jsonify
from kafka import KafkaConsumer

app = Flask(__name__)

KAFKA_BROKER = ['kafka-server:9092']
MESSAGES_TOPIC = "messages_topic"

messages = []


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


# Start Kafka consumer in a separate thread
consumer_thread = threading.Thread(target=consume_messages, daemon=True)
consumer_thread.start()


@app.route("/messages_service", methods=["GET"])
def get_messages():
    """
    Returns all stored messages for this instance.
    """
    if not messages:
        return jsonify({"message": "No messages available"}), 404

    return jsonify(messages), 200


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run messages service on a specified port.")
    parser.add_argument('--port', type=int, default=8084,
                        help="Port for the messages service")
    args = parser.parse_args()

    app.run(debug=True, host='0.0.0.0', port=args.port)
