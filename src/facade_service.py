import uuid
import requests
from flask import Flask, request, jsonify


app = Flask(__name__)

LOGGING_SERVICE_URL = "http://localhost:8081/logging_service"
MESSAGES_SERVICE_URL = "http://localhost:8082/messages_service"


def send_to_logging_service(pair):
    response = requests.post(LOGGING_SERVICE_URL, json=pair)
    response.raise_for_status()
    return response


@app.route("/facade_service", methods=['POST', 'GET'])
def facade_controller():
    """
    facade service function
    """
    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({"error": "Message is missing"}), 400

        msg = data
        unique_id = str(uuid.uuid4())
        pair = {"id": unique_id, "msg": msg}

        try:
            send_to_logging_service(pair)
            return {}
        except requests.exceptions.RequestException:
            return jsonify({"error": "Logging service is unavailable after retries"}), 503

    if request.method == "GET":
        response_logging = requests.get(LOGGING_SERVICE_URL)
        response_messages = requests.get(MESSAGES_SERVICE_URL)

        if response_logging.status_code != 200 or response_messages.status_code != 200:
            return jsonify({"error": "One of the services is unavailable"}), 500

        concatenated_response = "[" + response_logging.text + \
            "]: " + response_messages.text
        return concatenated_response

    return "Error", 400


if __name__ == "__main__":
    app.run(debug=True, port=8080)
