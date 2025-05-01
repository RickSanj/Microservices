from flask import Flask, request, jsonify
import hazelcast
import argparse
import time

app = Flask(__name__)


def set_up_hazelcast():
    client = None
    retries = 10
    while retries > 0:
        try:
            client = hazelcast.HazelcastClient(cluster_members=["hazelcast-server"])
            break
        except Exception as e:
            print(f"+ Retrying to connect to Hazelcast: {str(e)}", flush=True)
            retries -= 1
            time.sleep(5)  # Wait for 5 seconds before retrying
    if client is None:
        raise Exception("Could not connect to Hazelcast after retries.")
    print(f"+ Connected to Hazelcast", flush=True)
    return client


client = set_up_hazelcast()
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

        if hazelcast_map.contains_key(unique_id):
            return jsonify({"status": "Duplicate message ignored", "id": unique_id}), 200

        hazelcast_map.put(unique_id, message)
        print(f"+ Message received: {message}", flush=True)

        return jsonify({"status": "Message stored", "id": unique_id}), 200

    if request.method == "GET":
        messages = ", ".join([f"{v}" for k, v in hazelcast_map.entry_set()]) if hazelcast_map.size() > 0 else "No messages stored"
        return messages, 200

    return "Error", 400


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run logging service on a specified port.")
    parser.add_argument('--port', type=int, default=8081, help="Port for the logging service")
    args = parser.parse_args()

    app.run(debug=True, host='0.0.0.0', port=args.port)

