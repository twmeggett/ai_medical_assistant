CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE message_role AS ENUM ('user', 'assistant');

CREATE TABLE users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL    DEFAULT NOW()
);

-- Maps to ConversationHistory
CREATE TABLE conversations (
    conversation_id  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations (user_id);

-- Maps to ChatMessage
-- `position` preserves insertion order within a conversation
CREATE TABLE chat_messages (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID         NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role             message_role NOT NULL,
    content          TEXT         NOT NULL,
    timestamp        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    tool_calls_made  TEXT[]       NOT NULL DEFAULT '{}',
    cited_dois       TEXT[]       NOT NULL DEFAULT '{}',
    position         INT          NOT NULL,

    UNIQUE (conversation_id, position)
);

CREATE INDEX idx_chat_messages_conversation ON chat_messages (conversation_id, position);

CREATE TABLE articles (
    article_id      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    full_text       TEXT          NOT NULL,
    title           TEXT          NOT NULL,
    authors         TEXT[]        NOT NULL,
    journal         TEXT          NOT NULL,
    published_at    TIMESTAMPTZ   NOT NULL,
    chunk_status    TEXT          NOT NULL DEFAULT 'pending'  -- pending | processing | complete | failed
);

CREATE TABLE article_chunks (
    chunk_id        UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id      UUID          NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    chunk_text      TEXT          NOT NULL,
    context_text    TEXT          NOT NULL,
    embedding       vector(1024)  NOT NULL,
    section         TEXT          NOT NULL,
    chunk_index     INT           NOT NULL,
    token_count     INT           NOT NULL,
    content_hash    TEXT          NOT NULL,  -- sha256(article_id + chunk_text); enforces idempotent re-ingestion
    search_vector   TSVECTOR      GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
    metadata        JSONB,

    UNIQUE (content_hash)
);

CREATE INDEX idx_article_chunks_embedding_hnsw ON article_chunks USING hnsw (embedding vector_ip_ops);
CREATE INDEX idx_article_chunks_search_vector ON article_chunks USING gin (search_vector);

-- Keep conversations.updated_at in sync whenever a message is added
CREATE OR REPLACE FUNCTION fn_touch_conversation()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NOW()
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_touch_conversation
AFTER INSERT ON chat_messages
FOR EACH ROW EXECUTE FUNCTION fn_touch_conversation();
