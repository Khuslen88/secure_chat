import os

from flask import Flask, render_template, request, jsonify, send_file

from ai_client import AIClient
from chat import ConversationManager
from config import Config
from file_handler import FileHandler
from knowledge_base import KnowledgeBase
from security import SecurityUtils

app = Flask(__name__)
conversations = ConversationManager()
files = FileHandler()
kb = KnowledgeBase()

try:
    ai = AIClient()
except RuntimeError as e:
    import sys
    print(f"\n⚠️  WARNING: {e}", file=sys.stderr)
    print("   The chatbot UI will load, but AI features are disabled.\n", file=sys.stderr)
    ai = None


# ── Page ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Chat ──────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat_message():
    """Send a message and get an AI response."""
    if ai is None:
        return jsonify({"error": "AI service unavailable. GROQ_API_KEY is not configured."}), 503

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "message is required."}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    conversation_id = data.get("conversation_id")

    # Create new conversation if needed
    if not conversation_id:
        conversation_id = conversations.create_conversation()

    # Verify conversation exists
    if conversations.get_full_conversation(conversation_id) is None:
        conversation_id = conversations.create_conversation()

    # Get conversation history and knowledge context
    history = conversations.get_history(conversation_id)
    knowledge_context = kb.get_relevant_context(user_message)

    # Save user message
    user_msg = conversations.add_message(conversation_id, "user", user_message)

    # Get AI response
    try:
        ai_response = ai.send_message(history, user_message, knowledge_context)
    except Exception as e:
        return jsonify({"error": f"AI service error: {e}"}), 502

    # Save assistant message
    assistant_msg = conversations.add_message(conversation_id, "assistant", ai_response)

    return jsonify({
        "conversation_id": conversation_id,
        "user_message": user_msg,
        "assistant_message": assistant_msg,
    }), 200


@app.route("/api/chat/upload", methods=["POST"])
def chat_with_document():
    """Upload a document for summarization or Q&A within a conversation."""
    if ai is None:
        return jsonify({"error": "AI service unavailable. GROQ_API_KEY is not configured."}), 503

    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    user_query = request.form.get("message", "").strip()
    conversation_id = request.form.get("conversation_id", "").strip() or None

    # Save the file
    success, result = files.save_file(file)
    if not success:
        return jsonify({"error": result}), 400

    saved_filename = result

    # Extract text from the saved file
    file_path = files.get_file_path(saved_filename)
    ext = os.path.splitext(saved_filename)[1].lower()
    try:
        document_text = kb.extract_text(file_path, ext)
    except Exception as e:
        return jsonify({"error": f"Could not read document: {e}"}), 400

    if not document_text.strip():
        return jsonify({"error": "Could not extract text from this file."}), 400

    # Create conversation if needed
    if not conversation_id:
        conversation_id = conversations.create_conversation()
    if conversations.get_full_conversation(conversation_id) is None:
        conversation_id = conversations.create_conversation()

    # Build user message description
    display_msg = user_query or f"Please summarize this document."
    user_content = f"[Uploaded: {saved_filename}] {display_msg}"
    conversations.add_message(conversation_id, "user", user_content)

    # Get AI summary/answer
    try:
        ai_response = ai.summarize_document(document_text, user_query)
    except Exception as e:
        return jsonify({"error": f"AI service error: {e}"}), 502

    assistant_msg = conversations.add_message(conversation_id, "assistant", ai_response)

    return jsonify({
        "conversation_id": conversation_id,
        "assistant_message": assistant_msg,
        "document_name": saved_filename,
    }), 200


# ── Conversations ─────────────────────────────────────────────────

@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    return jsonify(conversations.list_conversations())


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    data = conversations.get_full_conversation(conversation_id)
    if data is None:
        return jsonify({"error": "Conversation not found."}), 404
    return jsonify(data)


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    if conversations.clear_conversation(conversation_id):
        return jsonify({"success": True})
    return jsonify({"error": "Conversation not found."}), 404


# ── Knowledge Base ────────────────────────────────────────────────

@app.route("/api/knowledge-base", methods=["GET"])
def list_knowledge_base():
    return jsonify(kb.list_documents())


@app.route("/api/knowledge-base", methods=["POST"])
def upload_to_knowledge_base():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    success, result = kb.add_document(request.files["file"])
    if not success:
        return jsonify({"error": result}), 400
    return jsonify({"doc_id": result, "success": True}), 201


@app.route("/api/knowledge-base/<doc_id>", methods=["DELETE"])
def remove_from_knowledge_base(doc_id):
    if kb.remove_document(doc_id):
        return jsonify({"success": True})
    return jsonify({"error": "Document not found."}), 404


# ── File Downloads (kept from original) ───────────────────────────

@app.route("/api/files/<filename>")
def download_file(filename):
    path = files.get_file_path(filename)
    if not path:
        return jsonify({"error": "File not found."}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")
