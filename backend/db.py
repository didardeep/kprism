import math
import json
import psycopg2
from psycopg2.extras import execute_values, Json
from config import DATABASE_URL


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            slide_number INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding JSONB NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


def store_embeddings(filename, chunks_with_embeddings):
    """
    chunks_with_embeddings: list of (slide_number, chunk_text, embedding)
    """
    conn = get_connection()
    cur = conn.cursor()
    values = [
        (filename, slide_num, chunk_text, Json(embedding))
        for slide_num, chunk_text, embedding in chunks_with_embeddings
    ]
    execute_values(
        cur,
        "INSERT INTO documents (filename, slide_number, chunk_text, embedding) VALUES %s",
        values
    )
    conn.commit()
    cur.close()
    conn.close()


def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def search_similar(query_embedding, top_k=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT filename, slide_number, chunk_text, embedding FROM documents;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Compute cosine similarity in Python
    scored = []
    for row in rows:
        stored_embedding = row[3]  # already parsed from jsonb
        similarity = cosine_similarity(query_embedding, stored_embedding)
        scored.append({
            "filename": row[0],
            "slide_number": row[1],
            "chunk_text": row[2],
            "similarity": similarity,
        })

    # Sort by similarity descending and return top_k
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def get_all_documents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT filename, COUNT(*) as chunk_count
        FROM documents
        GROUP BY filename
        ORDER BY filename;
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{"filename": row[0], "chunk_count": row[1]} for row in results]


def delete_document(filename):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM documents WHERE filename = %s;", (filename,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted
