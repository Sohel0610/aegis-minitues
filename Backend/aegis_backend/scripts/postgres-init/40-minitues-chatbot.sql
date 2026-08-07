\connect minutes_preparation_system

CREATE TABLE IF NOT EXISTS chatbot_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_users_id ON chatbot_users (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_chatbot_users_email ON chatbot_users (email);

CREATE TABLE IF NOT EXISTS chatbot_agendas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES chatbot_users (id),
    agenda_title VARCHAR(500) NOT NULL,
    agenda_content TEXT,
    meeting_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_agendas_id ON chatbot_agendas (id);

CREATE TABLE IF NOT EXISTS chatbot_decisions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES chatbot_users (id),
    meeting_title VARCHAR(500) NOT NULL,
    decision_text TEXT NOT NULL,
    meeting_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_decisions_id ON chatbot_decisions (id);

CREATE TABLE IF NOT EXISTS chatbot_action_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES chatbot_users (id),
    meeting_title VARCHAR(500) NOT NULL,
    task_description TEXT NOT NULL,
    assignee VARCHAR(255),
    status VARCHAR(50),
    meeting_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_action_items_id ON chatbot_action_items (id);

CREATE TABLE IF NOT EXISTS chatbot_attendees (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES chatbot_users (id),
    meeting_title VARCHAR(500) NOT NULL,
    attendee_name VARCHAR(255) NOT NULL,
    attendee_role VARCHAR(255),
    meeting_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_attendees_id ON chatbot_attendees (id);

CREATE TABLE IF NOT EXISTS chatbot_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES chatbot_users (id),
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    extracted_text TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_documents_id ON chatbot_documents (id);

CREATE TABLE IF NOT EXISTS chatbot_chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES chatbot_users (id),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_chat_history_id ON chatbot_chat_history (id);
CREATE INDEX IF NOT EXISTS ix_chatbot_chat_history_session_id ON chatbot_chat_history (session_id);

CREATE TABLE IF NOT EXISTS chatbot_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES chatbot_documents (id),
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding_vector JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chatbot_embeddings_id ON chatbot_embeddings (id);
