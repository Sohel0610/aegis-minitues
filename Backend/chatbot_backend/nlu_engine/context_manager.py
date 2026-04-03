"""
Context Manager - Conversation history and context tracking
Manages multi-turn conversations with semantic memory
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    turn_id: int
    user_query: str
    bot_response: str
    intent: str
    entities: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context for a conversation session"""
    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    active_entities: List[str] = field(default_factory=list)
    active_database: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ContextManager:
    """
    Manages conversation context and history
    Provides pronoun resolution and multi-turn understanding
    """
    
    def __init__(self, db_path: str = "conversation_context.db", max_turns: int = 10):
        """
        Initialize context manager
        
        Args:
            db_path: Path to SQLite database for persistent storage
            max_turns: Maximum number of turns to keep in memory
        """
        self.db_path = db_path
        self.max_turns = max_turns
        self._init_database()
        
        # In-memory cache of active sessions
        self._active_sessions: Dict[str, ConversationContext] = {}
    
    def _init_database(self):
        """Initialize SQLite database for context storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                active_entities TEXT,
                active_database TEXT,
                user_preferences TEXT,
                created_at TEXT,
                last_updated TEXT
            )
        ''')
        
        # Create turns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                turn_id INTEGER,
                user_query TEXT,
                bot_response TEXT,
                intent TEXT,
                entities TEXT,
                timestamp TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_turns 
            ON conversation_turns(session_id, turn_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_context(self, session_id: str) -> ConversationContext:
        """
        Get or create conversation context for session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ConversationContext for the session
        """
        # Check in-memory cache first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        # Load from database
        context = self._load_context_from_db(session_id)
        
        if context is None:
            # Create new context
            context = ConversationContext(session_id=session_id)
        
        # Cache in memory
        self._active_sessions[session_id] = context
        
        return context
    
    def add_turn(
        self,
        session_id: str,
        user_query: str,
        bot_response: str,
        intent: str,
        entities: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Add a new turn to the conversation
        
        Args:
            session_id: Session identifier
            user_query: User's query
            bot_response: Bot's response
            intent: Detected intent
            entities: Extracted entities
            metadata: Additional metadata
        """
        context = self.get_context(session_id)
        
        turn = ConversationTurn(
            turn_id=len(context.turns) + 1,
            user_query=user_query,
            bot_response=bot_response,
            intent=intent,
            entities=entities or [],
            metadata=metadata or {}
        )
        
        context.turns.append(turn)
        context.last_updated = datetime.utcnow()
        
        # Update active entities
        if entities:
            for entity in entities:
                if entity not in context.active_entities:
                    context.active_entities.append(entity)
        
        # Keep only last N turns in memory
        if len(context.turns) > self.max_turns:
            context.turns = context.turns[-self.max_turns:]
        
        # Persist to database
        self._save_turn_to_db(session_id, turn)
        self._update_context_in_db(context)
    
    def resolve_pronouns(self, query: str, session_id: str) -> str:
        """
        Resolve pronouns in query based on conversation context
        
        Args:
            query: User query with potential pronouns
            session_id: Session identifier
            
        Returns:
            Query with pronouns resolved
        """
        context = self.get_context(session_id)
        
        if not context.active_entities:
            return query
        
        query_lower = query.lower()
        
        # Pronoun patterns to replace
        pronoun_patterns = [
            ('it', 'its', 'this', 'that', 'the company', 'the entity'),
        ]
        
        # Get most recent entity
        most_recent_entity = context.active_entities[-1] if context.active_entities else None
        
        if most_recent_entity:
            resolved_query = query
            
            # Replace pronouns with entity name
            for pronoun in pronoun_patterns[0]:
                # Simple replacement (can be enhanced with NLP)
                if f" {pronoun} " in f" {query_lower} ":
                    resolved_query = query.replace(pronoun, most_recent_entity)
                    resolved_query = resolved_query.replace(pronoun.capitalize(), most_recent_entity)
            
            return resolved_query
        
        return query
    
    def get_recent_entities(self, session_id: str, limit: int = 5) -> List[str]:
        """
        Get recently mentioned entities in conversation
        
        Args:
            session_id: Session identifier
            limit: Maximum number of entities to return
            
        Returns:
            List of recent entities
        """
        context = self.get_context(session_id)
        return context.active_entities[-limit:] if context.active_entities else []
    
    def set_active_database(self, session_id: str, database: str):
        """
        Set active database for session
        
        Args:
            session_id: Session identifier
            database: Database name (bse, sebi, rbi)
        """
        context = self.get_context(session_id)
        context.active_database = database
        context.last_updated = datetime.utcnow()
        self._update_context_in_db(context)
    
    def get_active_database(self, session_id: str) -> Optional[str]:
        """Get active database for session"""
        context = self.get_context(session_id)
        return context.active_database
    
    def clear_context(self, session_id: str):
        """Clear conversation context for session"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        # Clear from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM conversation_turns WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM conversations WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
    
    def _load_context_from_db(self, session_id: str) -> Optional[ConversationContext]:
        """Load context from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load conversation metadata
        cursor.execute(
            'SELECT active_entities, active_database, user_preferences, created_at, last_updated '
            'FROM conversations WHERE session_id = ?',
            (session_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            conn.close()
            return None
        
        active_entities = json.loads(row[0]) if row[0] else []
        active_database = row[1]
        user_preferences = json.loads(row[2]) if row[2] else {}
        created_at = datetime.fromisoformat(row[3])
        last_updated = datetime.fromisoformat(row[4])
        
        # Load recent turns
        cursor.execute(
            'SELECT turn_id, user_query, bot_response, intent, entities, timestamp, metadata '
            'FROM conversation_turns WHERE session_id = ? '
            'ORDER BY turn_id DESC LIMIT ?',
            (session_id, self.max_turns)
        )
        
        turns = []
        for row in cursor.fetchall():
            turn = ConversationTurn(
                turn_id=row[0],
                user_query=row[1],
                bot_response=row[2],
                intent=row[3],
                entities=json.loads(row[4]) if row[4] else [],
                timestamp=datetime.fromisoformat(row[5]),
                metadata=json.loads(row[6]) if row[6] else {}
            )
            turns.append(turn)
        
        turns.reverse()  # Restore chronological order
        
        conn.close()
        
        return ConversationContext(
            session_id=session_id,
            turns=turns,
            active_entities=active_entities,
            active_database=active_database,
            user_preferences=user_preferences,
            created_at=created_at,
            last_updated=last_updated
        )
    
    def _save_turn_to_db(self, session_id: str, turn: ConversationTurn):
        """Save turn to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO conversation_turns '
            '(session_id, turn_id, user_query, bot_response, intent, entities, timestamp, metadata) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                session_id,
                turn.turn_id,
                turn.user_query,
                turn.bot_response,
                turn.intent,
                json.dumps(turn.entities),
                turn.timestamp.isoformat(),
                json.dumps(turn.metadata)
            )
        )
        
        conn.commit()
        conn.close()
    
    def _update_context_in_db(self, context: ConversationContext):
        """Update context metadata in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR REPLACE INTO conversations '
            '(session_id, active_entities, active_database, user_preferences, created_at, last_updated) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (
                context.session_id,
                json.dumps(context.active_entities),
                context.active_database,
                json.dumps(context.user_preferences),
                context.created_at.isoformat(),
                context.last_updated.isoformat()
            )
        )
        
        conn.commit()
        conn.close()


# Global instance
_context_manager = None

def get_context_manager() -> ContextManager:
    """Get singleton instance of ContextManager"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
