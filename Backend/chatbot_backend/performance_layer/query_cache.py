"""
Query Cache - LRU cache with TTL for query results
Improves response time for repeated queries
"""

from typing import Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import sqlite3
from collections import OrderedDict


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: int
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class QueryCache:
    """
    LRU cache with TTL for query results
    Stores results in memory with SQLite persistence
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,  # 5 minutes
        db_path: str = "query_cache.db"
    ):
        """
        Initialize query cache
        
        Args:
            max_size: Maximum number of entries in cache
            default_ttl: Default TTL in seconds
            db_path: Path to SQLite database for persistence
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.db_path = db_path
        
        # In-memory LRU cache
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for cache persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_cache (
                cache_key TEXT PRIMARY KEY,
                cache_value TEXT,
                created_at TEXT,
                ttl_seconds INTEGER,
                hit_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON query_cache(created_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def get(self, query: str, database: str = "all") -> Optional[Any]:
        """
        Get cached result for query
        
        Args:
            query: User query
            database: Database filter
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._generate_key(query, database)
        
        # Check in-memory cache first
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            
            # Check if expired
            if entry.is_expired():
                # Remove expired entry
                del self._cache[cache_key]
                self._remove_from_db(cache_key)
                self._misses += 1
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(cache_key)
            
            # Update hit count
            entry.hit_count += 1
            self._hits += 1
            
            return entry.value
        
        # Check database
        entry = self._load_from_db(cache_key)
        if entry and not entry.is_expired():
            # Load into memory
            self._cache[cache_key] = entry
            self._hits += 1
            return entry.value
        
        self._misses += 1
        return None
    
    def set(
        self,
        query: str,
        result: Any,
        database: str = "all",
        ttl: Optional[int] = None
    ):
        """
        Cache query result
        
        Args:
            query: User query
            result: Query result to cache
            database: Database filter
            ttl: Time-to-live in seconds (None = use default)
        """
        cache_key = self._generate_key(query, database)
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        
        entry = CacheEntry(
            key=cache_key,
            value=result,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl_seconds,
            hit_count=0
        )
        
        # Add to memory cache
        self._cache[cache_key] = entry
        self._cache.move_to_end(cache_key)
        
        # Evict oldest if over max size
        if len(self._cache) > self.max_size:
            oldest_key, _ = self._cache.popitem(last=False)
            self._remove_from_db(oldest_key)
        
        # Persist to database
        self._save_to_db(entry)
    
    def invalidate(self, query: Optional[str] = None, database: Optional[str] = None):
        """
        Invalidate cache entries
        
        Args:
            query: Specific query to invalidate (None = invalidate all)
            database: Database filter (None = all databases)
        """
        if query:
            cache_key = self._generate_key(query, database or "all")
            if cache_key in self._cache:
                del self._cache[cache_key]
            self._remove_from_db(cache_key)
        else:
            # Invalidate all
            self._cache.clear()
            self._clear_db()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.2f}%",
            "cache_size": len(self._cache),
            "max_size": self.max_size
        }
    
    def _generate_key(self, query: str, database: str) -> str:
        """Generate cache key from query and database"""
        # Normalize query (lowercase, strip whitespace)
        normalized = query.lower().strip()
        
        # Create hash
        key_string = f"{normalized}:{database}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _save_to_db(self, entry: CacheEntry):
        """Save cache entry to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serialize value to JSON
        try:
            value_json = json.dumps(entry.value)
        except:
            # If not JSON serializable, skip database persistence
            conn.close()
            return
        
        cursor.execute(
            'INSERT OR REPLACE INTO query_cache '
            '(cache_key, cache_value, created_at, ttl_seconds, hit_count) '
            'VALUES (?, ?, ?, ?, ?)',
            (
                entry.key,
                value_json,
                entry.created_at.isoformat(),
                entry.ttl_seconds,
                entry.hit_count
            )
        )
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self, cache_key: str) -> Optional[CacheEntry]:
        """Load cache entry from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT cache_value, created_at, ttl_seconds, hit_count '
            'FROM query_cache WHERE cache_key = ?',
            (cache_key,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        try:
            value = json.loads(row[0])
            created_at = datetime.fromisoformat(row[1])
            ttl_seconds = row[2]
            hit_count = row[3]
            
            return CacheEntry(
                key=cache_key,
                value=value,
                created_at=created_at,
                ttl_seconds=ttl_seconds,
                hit_count=hit_count
            )
        except:
            return None
    
    def _remove_from_db(self, cache_key: str):
        """Remove cache entry from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM query_cache WHERE cache_key = ?', (cache_key,))
        conn.commit()
        conn.close()
    
    def _clear_db(self):
        """Clear all cache entries from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM query_cache')
        conn.commit()
        conn.close()


# Global instance
_query_cache = None

def get_query_cache() -> QueryCache:
    """Get singleton instance of QueryCache"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache
