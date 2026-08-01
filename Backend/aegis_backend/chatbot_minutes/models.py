from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model - stores user information"""
    __tablename__ = "chatbot_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agendas = relationship("Agenda", back_populates="user")
    decisions = relationship("Decision", back_populates="user")
    action_items = relationship("ActionItem", back_populates="user")
    documents = relationship("Document", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    entities = relationship("ConversationEntity", back_populates="user", cascade="all, delete-orphan")

class Agenda(Base):
    """Agenda model - stores meeting agenda items"""
    __tablename__ = "chatbot_agendas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('chatbot_users.id'), nullable=False)
    agenda_title = Column(String(500), nullable=False)
    agenda_content = Column(Text)
    meeting_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="agendas")

class Decision(Base):
    """Decision model - stores meeting decisions"""
    __tablename__ = "chatbot_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('chatbot_users.id'), nullable=False)
    meeting_title = Column(String(500), nullable=False)
    decision_text = Column(Text, nullable=False)
    meeting_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="decisions")

class ActionItem(Base):
    """Action Item model - stores tasks with assignees"""
    __tablename__ = "chatbot_action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('chatbot_users.id'), nullable=False)
    meeting_title = Column(String(500), nullable=False)
    task_description = Column(Text, nullable=False)
    assignee = Column(String(255))
    status = Column(String(50), default="pending")
    meeting_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="action_items")

class Attendee(Base):
    """Attendee model - stores meeting participants"""
    __tablename__ = "chatbot_attendees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('chatbot_users.id'), nullable=False)
    meeting_title = Column(String(500), nullable=False)
    attendee_name = Column(String(255), nullable=False)
    attendee_role = Column(String(255))
    meeting_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    """Document model - stores uploaded documents"""
    __tablename__ = "chatbot_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('chatbot_users.id'), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    extracted_text = Column(Text)
    processing_status = Column(String(32), default="ready", nullable=False)
    extraction_method = Column(String(100))
    extraction_metadata = Column(JSON)
    page_count = Column(Integer, default=0)
    processing_error = Column(Text)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="documents")
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")

class Embedding(Base):
    """Embedding model - stores vector embeddings for semantic search"""
    __tablename__ = "chatbot_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('chatbot_documents.id'), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    embedding_vector = Column(JSON)  # list of floats
    chunk_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="embeddings")

class ChatHistory(Base):
    """Chat History model - stores conversation history"""
    __tablename__ = "chatbot_chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('chatbot_users.id'), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    response_metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_history")


class SessionSummary(Base):
    """Compressed episodic memory; avoids sending long raw conversations to the LLM."""
    __tablename__ = "chatbot_session_summaries"
    __table_args__ = (UniqueConstraint("user_id", "session_id", name="uq_chatbot_summary_user_session"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("chatbot_users.id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    last_message_id = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreference(Base):
    """Small semantic-memory store; never stores secrets or model instructions."""
    __tablename__ = "chatbot_user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "preference_key", "preference_value", name="uq_chatbot_preference"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("chatbot_users.id"), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(String(500), nullable=False)
    weight = Column(Integer, default=1, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class ConversationEntity(Base):
    """Entity memory used as a weak retrieval preference, not an access-control rule."""
    __tablename__ = "chatbot_conversation_entities"
    __table_args__ = (UniqueConstraint("user_id", "entity_type", "entity_value", name="uq_chatbot_entity"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("chatbot_users.id"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_value = Column(String(500), nullable=False)
    mentions = Column(Integer, default=1, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="entities")
