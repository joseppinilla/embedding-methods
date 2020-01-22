import time
import embera

__all__ = ["embed_and_report"]

def embed_and_report(method, S, T, RNG_SEED=42):
    report = {}
    embedding = {}

    start = time.time()
    embedding = method(S,T,RNG_SEED)
    end = time.time()

    report = {"valid":bool(embedding)} # This can be more elaborate, for incomplete embeddings
    report['embedding_runtime'] = end-start
    report['embedding_method'] = method.__name__

    embedding_obj = embera.Embedding(embedding,**report)

    return embedding
