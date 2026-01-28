"""
Embedding Index Module
Loads notifications from DB, builds embeddings, stores them in memory,
and can return top-k similar rows.
"""
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from data_layer.models import get_db_session, DailyLog
from data_layer.db_models import get_sebi_session, get_rbi_session, SEBINotification, RBINotification
import os
from dotenv import load_dotenv
 
# Load environment variables from the root directory
# Look for .env file in parent directories
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to default loading
    load_dotenv()
 
class EmbeddingIndex:
    """
    Embedding Index for semantic search over regulatory notifications
    """
   
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding index
        """
        embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", model_name)
        print(f"Loading embedding model from: {embedding_model_path}")
        # Ensure we're only loading from local path and not downloading
        if os.path.exists(embedding_model_path):
            self.model = SentenceTransformer(embedding_model_path, trust_remote_code=True)
        else:
            raise FileNotFoundError(f"Local embedding model not found at: {embedding_model_path}. Please ensure the model is downloaded locally.")
        self.notifications = []
        self.embeddings = None
        self.notification_ids = []
   
    def load_notifications(self, limit: int = None):
        """
        Load notifications from the database (DailyLogs table)
        """
        session = get_db_session()
        query = session.query(DailyLog)
       
        # Filter out NIL entries
        query = query.filter(
            ~((DailyLog.Link == "NIL") &
              (DailyLog.Nature == "NIL") &
              (DailyLog.Summary == "NIL"))
        )
       
        if limit:
            query = query.limit(limit)
           
        self.notifications = query.all()
        session.close()
       
        # Extract IDs for mapping back to notifications
        self.notification_ids = [notification.SrNo for notification in self.notifications]
       
        print(f"Loaded {len(self.notifications)} notifications from database")
   
    def build_embeddings(self):
        """
        Build embeddings for all loaded notifications
        """
        if not self.notifications:
            print("No notifications loaded. Call load_notifications() first.")
            return
       
        # Convert notifications to text chunks
        text_chunks = [self.notification_to_text_chunk(notification) for notification in self.notifications]
       
        # Generate embeddings
        self.embeddings = self.model.encode(text_chunks)
       
        print(f"Generated embeddings for {len(self.embeddings)} notifications")
   
    def notification_to_text_chunk(self, notification):
        """
        Convert DailyLog notification to text chunk for embedding
        """
        return f"EntityName: {notification.EntityName}. Date: {notification.Date}. Nature: {notification.Nature}. Summary: {notification.Summary}"
   
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for top-k similar notifications to the query
        """
        if self.embeddings is None:
            try:
                initialize_embedding_index()
            except Exception:
                return []
       
        # Generate embedding for query
        query_embedding = self.model.encode([query])
       
        # Calculate cosine similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
       
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
       
        # Return top-k notifications with similarity scores
        results = []
        for idx in top_indices:
            notification = self.notifications[idx]
            results.append({
                "notification": notification,
                "similarity": float(similarities[idx])
            })
       
        return results
   
    def get_notification_by_id(self, notification_id: int) -> DailyLog:
        """
        Get notification by ID
        """
        for notification in self.notifications:
            if notification.SrNo == notification_id:
                return notification
        return None
 
# Global instance
embedding_index = EmbeddingIndex()
 
def initialize_embedding_index():
    """
    Initialize the global embedding index
    """
    print("Loading notifications...")
    embedding_index.load_notifications()
   
    print("Building embeddings...")
    embedding_index.build_embeddings()
   
    print("Embedding index initialized!")
 
sebi_notifications = []
sebi_embeddings = None
rbi_notifications = []
rbi_embeddings = None
 
def load_sebi_notifications(limit: int = None):
    session = get_sebi_session()
    try:
        q = session.query(SEBINotification)
        if limit:
            q = q.limit(limit)
        rows = q.all()
    finally:
        session.close()
    return rows
 
def build_sebi_embeddings(model_name: str = "all-MiniLM-L6-v2"):
    global sebi_notifications, sebi_embeddings
    if not sebi_notifications:
        sebi_notifications = load_sebi_notifications()
    embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", model_name)
    # Ensure we're only loading from local path and not downloading
    if os.path.exists(embedding_model_path):
        model = SentenceTransformer(embedding_model_path, trust_remote_code=True)
    else:
        raise FileNotFoundError(f"Local embedding model not found at: {embedding_model_path}. Please ensure the model is downloaded locally.")
    texts = [f"Date: {n.date_key}. Summary: {n.summary}" for n in sebi_notifications]
    sebi_embeddings = model.encode(texts)
 
def search_sebi_similar(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    global sebi_embeddings
    if sebi_embeddings is None or not sebi_notifications:
        try:
            build_sebi_embeddings()
        except Exception:
            return []
    embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", "all-MiniLM-L6-v2")
    # Ensure we're only loading from local path and not downloading
    if os.path.exists(embedding_model_path):
        model = SentenceTransformer(embedding_model_path, trust_remote_code=True)
    else:
        raise FileNotFoundError(f"Local embedding model not found at: {embedding_model_path}. Please ensure the model is downloaded locally.")
    q_emb = model.encode([query])
    sims = cosine_similarity(q_emb, sebi_embeddings)[0]
    idxs = np.argsort(sims)[-top_k:][::-1]
    results = []
    for idx in idxs:
        results.append({"notification": sebi_notifications[idx], "similarity": float(sims[idx])})
    return results
 
def load_rbi_notifications(limit: int = None):
    session = get_rbi_session()
    try:
        q = session.query(RBINotification)
        if limit:
            q = q.limit(limit)
        rows = q.all()
    finally:
        session.close()
    return rows
 
def build_rbi_embeddings(model_name: str = "all-MiniLM-L6-v2"):
    global rbi_notifications, rbi_embeddings
    if not rbi_notifications:
        rbi_notifications = load_rbi_notifications()
    embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", model_name)
    # Ensure we're only loading from local path and not downloading
    if os.path.exists(embedding_model_path):
        model = SentenceTransformer(embedding_model_path, trust_remote_code=True)
    else:
        raise FileNotFoundError(f"Local embedding model not found at: {embedding_model_path}. Please ensure the model is downloaded locally.")
    texts = [f"Date: {n.run_date}. Summary: {n.summary}" for n in rbi_notifications]
    rbi_embeddings = model.encode(texts)
 
def search_rbi_similar(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    global rbi_embeddings
    if rbi_embeddings is None or not rbi_notifications:
        try:
            build_rbi_embeddings()
        except Exception:
            return []
    embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", "all-MiniLM-L6-v2")
    # Ensure we're only loading from local path and not downloading
    if os.path.exists(embedding_model_path):
        model = SentenceTransformer(embedding_model_path, trust_remote_code=True)
    else:
        raise FileNotFoundError(f"Local embedding model not found at: {embedding_model_path}. Please ensure the model is downloaded locally.")
    q_emb = model.encode([query])
    sims = cosine_similarity(q_emb, rbi_embeddings)[0]
    idxs = np.argsort(sims)[-top_k:][::-1]
    results = []
    for idx in idxs:
        results.append({"notification": rbi_notifications[idx], "similarity": float(sims[idx])})
    return results
 
def search_similar_notifications(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for similar notifications using the global embedding index
    """
    return embedding_index.search(query, top_k)
 