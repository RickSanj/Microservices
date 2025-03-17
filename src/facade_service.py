import uuid
import random
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# List of logging services running on different ports
LOGGING_SERVICE_URLS = [
    "http://localhost:8081/logging_service",
    "http://localhost:8082/logging_service",
    "http://localhost:8083/logging_service",
]

MESSAGES_SERVICE_URL = "http://localhost:8084/messages_service"


def send_to_logging_service(pair):
    for logging_service_url in random.sample(LOGGING_SERVICE_URLS, len(LOGGING_SERVICE_URLS)):
        try:
            response = requests.post(logging_service_url, json=pair)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            print(f"Failed to send message to {logging_service_url}")
            continue
    raise requests.exceptions.RequestException("All logging service instances are unavailable.")


@app.route("/facade_service", methods=['POST', 'GET'])
def facade_controller():
    """
    Facade service function to handle POST and GET requests.
    """
    if request.method == "POST":
        data = request.json
        if not data or "msg" not in data:
            return jsonify({"error": "Message is missing"}), 400

        msg = data["msg"]
        unique_id = str(uuid.uuid4())
        pair = {"id": unique_id, "msg": msg}

        try:
            send_to_logging_service(pair)
            return jsonify({"status": "Message sent successfully"}), 200
        except requests.exceptions.RequestException:
            return jsonify({"error": "Logging service is unavailable after retries"}), 503

    if request.method == "GET":
        response_logging = requests.get(LOGGING_SERVICE_URLS[0])
        response_messages = requests.get(MESSAGES_SERVICE_URL)

        if response_logging.status_code != 200 or response_messages.status_code != 200:
            return jsonify({"error": "One of the services is unavailable"}), 500

        concatenated_response = "[" + response_logging.text + \
            "]: " + response_messages.text
        return concatenated_response

    return "Error", 400


if __name__ == "__main__":
    app.run(debug=True, port=8080)
