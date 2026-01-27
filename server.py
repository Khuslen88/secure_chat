from flask import Flask, render_template, request, jsonify

from chat import ChatManager

app = Flask(__name__)
chat = ChatManager()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages", methods=["GET"])
def get_messages():
    limit = request.args.get("limit", 50, type=int)
    return jsonify(chat.get_messages(limit))


@app.route("/api/messages", methods=["POST"])
def post_message():
    data = request.get_json()
    if not data or "username" not in data or "content" not in data:
        return jsonify({"error": "username and content are required"}), 400

    username = data["username"].strip()
    content = data["content"].strip()

    if not username or not content:
        return jsonify({"error": "username and content cannot be empty"}), 400

    message = chat.add_message(username, content)
    return jsonify(message), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
