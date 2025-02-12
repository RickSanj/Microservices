from flask import Flask, request

app = Flask(__name__)


@app.route("/messages_service", methods=["POST", "GET"])
def messages_controller():
    """
    messages service function
    """
    if request.method == "POST":
        return "Messages-service is not implemented yet", 200
    if request.method == "GET":
        return "Messages-service is not implemented yet", 200
    return "Error", 400


if __name__ == "__main__":
    app.run(debug=True, port=8082)
