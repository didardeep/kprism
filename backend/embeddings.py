from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_EMBEDDING_DEPLOYMENT,
)

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

BATCH_SIZE = 16


def get_embeddings(texts):
    """
    Generate embeddings for a list of texts using Azure OpenAI.
    Returns a list of embedding vectors.
    """
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(
            input=batch,
            model=AZURE_EMBEDDING_DEPLOYMENT,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def get_single_embedding(text):
    """Generate embedding for a single text."""
    response = client.embeddings.create(
        input=[text],
        model=AZURE_EMBEDDING_DEPLOYMENT,
    )
    return response.data[0].embedding
