import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER
from db import init_db, store_embeddings, get_all_documents, delete_document
from ppt_processor import process_ppt
from embeddings import get_embeddings
from rag import ask

app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"pptx", "ppt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/upload", methods=["POST"])
def upload_file():
    print("Files in request:", list(request.files.keys()))
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    print("Filename:", file.filename)
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        print("Rejected file extension:", file.filename)
        return jsonify({"error": f"Only .pptx and .ppt files are allowed. Got: '{file.filename}'"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        # Extract text and chunk
        chunks = process_ppt(file_path)
        if not chunks:
            return jsonify({"error": "No text content found in the PPT file"}), 400

        # Generate embeddings
        chunk_texts = [c["chunk_text"] for c in chunks]
        embeddings = get_embeddings(chunk_texts)

        # Store in database
        chunks_with_embeddings = [
            (chunks[i]["slide_number"], chunks[i]["chunk_text"], embeddings[i])
            for i in range(len(chunks))
        ]
        store_embeddings(filename, chunks_with_embeddings)

        return jsonify({
            "message": f"Successfully processed '{filename}'",
            "chunks_created": len(chunks),
            "filename": filename,
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "No question provided"}), 400

    question = data["question"].strip()
    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    try:
        result = ask(question)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents", methods=["GET"])
def list_documents():
    try:
        docs = get_all_documents()
        return jsonify({"documents": docs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<filename>", methods=["DELETE"])
def remove_document(filename):
    try:
        deleted = delete_document(filename)
        if deleted > 0:
            return jsonify({"message": f"Deleted {deleted} chunks for '{filename}'"}), 200
        else:
            return jsonify({"error": "Document not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
