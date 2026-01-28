import numpy as np
from sentence_transformers import SentenceTransformer
import os
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import hashlib
from dotenv import load_dotenv
 
# Load environment variables from the root directory
# Look for .env file in parent directories
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to default loading
    load_dotenv()
 
class EmbeddingModel:
    def __init__(self, model_path="all-MiniLM-L6-v2"):
        """
        Initialize the embedding model
        """
        self.model_path = model_path
        # Use the local model path from environment variables
        embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", model_path)
       
        print(f"Loading embedding model from: {embedding_model_path}")
        # Ensure we're only loading from local path and not downloading
        if os.path.exists(embedding_model_path):
            self.model = SentenceTransformer(embedding_model_path, trust_remote_code=True)
        else:
            raise FileNotFoundError(f"Local embedding model not found at: {embedding_model_path}. Please ensure the model is downloaded locally.")
       
        # Cache for embeddings
        self.embedding_cache = {}
   
    def encode(self, texts):
        """
        Encode texts into embeddings with caching
        """
        if isinstance(texts, str):
            texts = [texts]
       
        # Check cache first
        cached_embeddings = []
        texts_to_encode = []
        indices_to_encode = []
       
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.embedding_cache:
                cached_embeddings.append(self.embedding_cache[text_hash])
            else:
                cached_embeddings.append(None)
                texts_to_encode.append(text)
                indices_to_encode.append(i)
       
        # Encode missing texts
        if texts_to_encode:
            new_embeddings = self.model.encode(texts_to_encode)
            # Store in cache
            for i, text in enumerate(texts_to_encode):
                text_hash = hashlib.md5(text.encode()).hexdigest()
                self.embedding_cache[text_hash] = new_embeddings[i]
                cached_embeddings[indices_to_encode[i]] = new_embeddings[i]
       
        return np.array(cached_embeddings)
   
    def similarity(self, text1, text2):
        """
        Calculate cosine similarity between two texts
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        return cosine_similarity([emb1], [emb2])[0][0]
   
    def find_most_similar(self, query, candidates, top_k=5):
        """
        Find the most similar candidates to the query
        """
        if not candidates:
            return []
       
        query_emb = self.encode(query)
        candidate_embs = self.encode(candidates)
       
        # Reshape query_emb to 2D if it's 1D
        if len(query_emb.shape) == 1:
            query_emb = query_emb.reshape(1, -1)
       
        similarities = cosine_similarity(query_emb, candidate_embs)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
       
        results = []
        for i in top_indices:
            results.append({
                "text": candidates[i],
                "similarity": float(similarities[i])  # Convert to Python float for JSON serialization
            })
       
        return results
 
# Global instance
embedding_model = EmbeddingModel()
 
def get_embedding_model():
    """
    Get the global embedding model instance
    """
    return embedding_model
 