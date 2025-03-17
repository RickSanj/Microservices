# from flask import Flask, request, jsonify
# import hazelcast
# import random
# import json

# app = Flask(__name__)

# client = hazelcast.HazelcastClient()
# hazelcast_map = client.get_map("logging_map").blocking()

# @app.route("/logging_service", methods=['POST', 'GET'])
# def logging_controller():
#     """
#     logging service function using Hazelcast for message storage
#     """
#     if request.method == "POST":
#         data = request.json
#         if not data or "id" not in data or "msg" not in data:
#             return jsonify({"error": "Missing 'id' or 'msg' field"}), 400

#         unique_id = data["id"]
#         message = data["msg"]
#         # Check if message already exists
#         if hazelcast_map.contains_key(unique_id):
#             return jsonify({"status": "Duplicate message ignored", "id": unique_id}), 200

#         hazelcast_map.put(unique_id, message)
#         print(f"Message received: {message}")

#         return jsonify({"status": "Message stored", "id": unique_id}), 200

#     if request.method == "GET":
#         messages = ", ".join([f"{k}: {v}" for k, v in hazelcast_map.entry_set()]) if hazelcast_map.size() > 0 else "No messages stored"
#         return messages, 200

#     return "Error", 400


# if __name__ == "__main__":
#     app.run(debug=True, port=8081)

from flask import Flask, request, jsonify
import hazelcast
import argparse

app = Flask(__name__)

# Hazelcast client setup
client = hazelcast.HazelcastClient()
hazelcast_map = client.get_map("logging_map").blocking()

@app.route("/logging_service", methods=['POST', 'GET'])
def logging_controller():
    """
    logging service function using Hazelcast for message storage
    """
    if request.method == "POST":
        data = request.json
        if not data or "id" not in data or "msg" not in data:
            return jsonify({"error": "Missing 'id' or 'msg' field"}), 400

        unique_id = data["id"]
        message = data["msg"]
        # Check if message already exists
        if hazelcast_map.contains_key(unique_id):
            return jsonify({"status": "Duplicate message ignored", "id": unique_id}), 200

        hazelcast_map.put(unique_id, message)
        print(f"Message received: {message}")

        return jsonify({"status": "Message stored", "id": unique_id}), 200

    if request.method == "GET":
        messages = ", ".join([f"{k}: {v}" for k, v in hazelcast_map.entry_set()]) if hazelcast_map.size() > 0 else "No messages stored"
        return messages, 200

    return "Error", 400


if __name__ == "__main__":
    # Parse command-line argument for the port
    parser = argparse.ArgumentParser(description="Run logging service on a specified port.")
    parser.add_argument('--port', type=int, default=8081, help="Port for the logging service")
    args = parser.parse_args()

    app.run(debug=True, port=args.port)
