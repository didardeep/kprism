from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_CHAT_DEPLOYMENT,
)
from embeddings import get_single_embedding
from db import search_similar

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions ONLY based on the provided context from uploaded documents.

Rules:
1. Answer ONLY using the information provided in the context below.
2. If the answer is not found in the context, respond with: "I don't have information about that in the uploaded documents."
3. Do not make up or infer information that is not explicitly stated in the context.
4. When possible, mention which slide the information comes from.
5. Be concise and accurate in your responses."""


def retrieve(query, top_k=5):
    """Retrieve relevant chunks for a query."""
    query_embedding = get_single_embedding(query)
    results = search_similar(query_embedding, top_k=top_k)
    return results


def build_context(results):
    """Build context string from retrieved chunks."""
    if not results:
        return ""
    context_parts = []
    for r in results:
        context_parts.append(
            f"[Source: {r['filename']}, Slide {r['slide_number']}]\n{r['chunk_text']}"
        )
    return "\n\n---\n\n".join(context_parts)


def generate_answer(query, context_chunks):
    """Generate an answer using Azure OpenAI chat model."""
    context = build_context(context_chunks)

    if not context:
        return "No documents have been uploaded yet. Please upload a PPT file first."

    user_message = f"""Context from uploaded documents:

{context}

---

User Question: {query}"""

    response = client.chat.completions.create(
        model=AZURE_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def ask(query):
    """Full RAG pipeline: retrieve relevant chunks and generate answer."""
    chunks = retrieve(query)
    answer = generate_answer(query, chunks)
    sources = [
        {"filename": c["filename"], "slide_number": c["slide_number"], "similarity": round(c["similarity"], 3)}
        for c in chunks
    ]
    return {"answer": answer, "sources": sources}
