from flask import Flask, render_template, request, jsonify, send_file

from chat import ChatManager
from file_handler import FileHandler
from security import SecurityUtils

app = Flask(__name__)
chat = ChatManager()
files = FileHandler()


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

    if not content:
        return jsonify({"error": "Message content cannot be empty."}), 400

    valid, err = SecurityUtils.validate_username(username)
    if not valid:
        return jsonify({"error": err}), 400

    message = chat.add_message(username, content)
    return jsonify(message), 201


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    username = request.form.get("username", "").strip()
    content = request.form.get("content", "").strip() or "(file shared)"

    valid, err = SecurityUtils.validate_username(username)
    if not valid:
        return jsonify({"error": err}), 400

    success, result = files.save_file(file)
    if not success:
        return jsonify({"error": result}), 400

    message = chat.add_message(username, content, filename=result)
    return jsonify(message), 201


@app.route("/api/files/<filename>")
def download_file(filename):
    path = files.get_file_path(filename)
    if not path:
        return jsonify({"error": "File not found."}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
