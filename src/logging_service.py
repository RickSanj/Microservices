from flask import Flask, request, jsonify

app = Flask(__name__)

hash_table = {}


@app.route("/logging_service", methods=['POST', 'GET'])
def logging_controller():
    """
    logging service function
    """
    if request.method == "POST":
        data = request.json
        if not data or "id" not in data or "msg" not in data:
            return jsonify({"error": "Missing 'id' or 'msg' field"}), 400

        unique_id = data["id"]
        message = data["msg"]
        hash_table[unique_id] = message
        print(f"Message received: {message}")

        return jsonify({"status": "Message stored", "id": unique_id}), 200

    if request.method == "GET":
        messages = ", ".join(hash_table.values()
                             ) if hash_table else "No messages stored"
        return messages, 200

    return "Error", 400


if __name__ == "__main__":
    app.run(debug=True, port=8081)
