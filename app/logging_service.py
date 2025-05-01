from flask import Flask, request, jsonify
import hazelcast
import argparse
import time
import consul
import socket
import json

app = Flask(__name__)
consul_client = consul.Consul(host='consul-server', port=8500)


def get_kv_value(key):
    index, data = consul_client.kv.get(key)
    if data and 'Value' in data:
        return data['Value'].decode('utf-8') if isinstance(data['Value'], bytes) else data['Value']
    return None


def get_hazelcast_config():
    config_json = get_kv_value("hazelcast/client/config")
    if config_json:
        print(f"[+] Loaded Hazelcast config from Consul: {config_json}")
        return json.loads(config_json)
    else:
        raise RuntimeError("Hazelcast config not found in Consul.")


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


def set_up_hazelcast(cluster_name, members):
    client = None
    retries = 10
    while retries > 0:
        try:
            client = hazelcast.HazelcastClient(
                cluster_members=members
            )
            break
        except Exception as e:
            print(f"+ Retrying to connect to Hazelcast: {str(e)}", flush=True)
            retries -= 1
            time.sleep(5)  # Wait for 5 seconds before retrying
    if client is None:
        raise Exception("Could not connect to Hazelcast after retries.", flush=True)
    print(f"+ Connected to Hazelcast", flush=True)
    return client


@app.route("/health")
def health():
    return "OK", 200


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
    try:
        hazelcast_config = get_hazelcast_config()
        cluster_name = hazelcast_config["cluster_name"]
        members = hazelcast_config["members"]
        client = set_up_hazelcast(cluster_name, members)
        hazelcast_map = client.get_map("logging_map").blocking()
    except Exception as e:
        print(f"!! Failed to set up Hazelcast: {e}", flush=True)
        exit(1)

    register_to_consul("logging_service", f"logging-service-{str(args.port)[-1:]}-{args.port}", args.port)

    app.run(debug=True, host='0.0.0.0', port=args.port)

