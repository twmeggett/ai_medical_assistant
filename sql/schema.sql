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
