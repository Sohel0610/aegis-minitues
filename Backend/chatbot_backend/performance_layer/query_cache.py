"""PostgreSQL-backed per-user semantic query cache."""
from collections import OrderedDict
from datetime import datetime, timedelta
import hashlib
import json
from typing import Any, Dict, Optional
from sqlalchemy import text
from chatbot_backend.data_layer.models import engine

class QueryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size, self.default_ttl = max_size, default_ttl
        self._cache = OrderedDict()
        self._hits = self._misses = 0
        self._init_database()

    def _init_database(self):
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS chatbot_query_cache (
                cache_key_hash TEXT NOT NULL, user_id TEXT NOT NULL DEFAULT 'anonymous', database_scope TEXT NOT NULL,
                query_text TEXT NOT NULL, cache_value JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL, hit_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(cache_key_hash, user_id, database_scope))"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chatbot_cache_expiry ON chatbot_query_cache(expires_at)"))

    @staticmethod
    def _key(query, database, user_id):
        normal = " ".join(query.lower().split())
        return hashlib.sha256(f"{user_id}:{database}:{normal}".encode()).hexdigest()

    @staticmethod
    def _similar(a: str, b: str) -> float:
        # Token Jaccard is deterministic and works when an embedding service is unavailable.
        left, right = set(a.lower().split()), set(b.lower().split())
        return len(left & right) / len(left | right) if left or right else 0.0

    def get(self, query: str, database: str = "all", user_id: str = "anonymous") -> Optional[Any]:
        key = self._key(query, database, user_id)
        if key in self._cache:
            self._hits += 1; return self._cache[key]
        with engine.begin() as conn:
            row = conn.execute(text("SELECT cache_value FROM chatbot_query_cache WHERE cache_key_hash=:key AND user_id=:user AND database_scope=:db AND expires_at>NOW()"), {"key": key, "user": user_id, "db": database}).scalar()
            if row is None:
                # semantic dedup for rephrased requests from the same user/scope
                candidates = conn.execute(text("SELECT cache_value,query_text FROM chatbot_query_cache WHERE user_id=:user AND database_scope=:db AND expires_at>NOW() ORDER BY created_at DESC LIMIT 100"), {"user": user_id, "db": database}).mappings().all()
                row = next((candidate["cache_value"] for candidate in candidates if self._similar(query, candidate["query_text"]) >= .95), None)
            if row is None:
                self._misses += 1; return None
            self._hits += 1
            return row if isinstance(row, dict) else json.loads(row)

    def set(self, query: str, result: Any, database: str = "all", ttl: Optional[int] = None, user_id: str = "anonymous"):
        try: value = json.dumps(result)
        except (TypeError, ValueError): return
        key, seconds = self._key(query, database, user_id), ttl or self.default_ttl
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO chatbot_query_cache(cache_key_hash,user_id,database_scope,query_text,cache_value,expires_at)
                VALUES(:key,:user,:db,:query,CAST(:value AS jsonb),NOW() + (:ttl * INTERVAL '1 second'))
                ON CONFLICT(cache_key_hash,user_id,database_scope) DO UPDATE SET cache_value=EXCLUDED.cache_value,expires_at=EXCLUDED.expires_at,created_at=NOW()"""), {"key":key,"user":user_id,"db":database,"query":query,"value":value,"ttl":seconds})

    def invalidate(self, query=None, database=None, user_id="anonymous"):
        with engine.begin() as conn:
            if query: conn.execute(text("DELETE FROM chatbot_query_cache WHERE cache_key_hash=:key AND user_id=:user AND database_scope=:db"), {"key":self._key(query,database or "all",user_id),"user":user_id,"db":database or "all"})
            else: conn.execute(text("DELETE FROM chatbot_query_cache WHERE user_id=:user"), {"user":user_id})

    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {"hits":self._hits,"misses":self._misses,"hit_rate": f"{(100*self._hits/total) if total else 0:.2f}%"}

_query_cache = None
def get_query_cache() -> QueryCache:
    global _query_cache
    if _query_cache is None: _query_cache = QueryCache()
    return _query_cache
