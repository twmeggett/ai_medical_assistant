import logging

import asyncpg

from backend.models.domain import ChatMessage, ConversationHistory, MessageRole

logger = logging.getLogger(__name__)


async def create_conversation(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    conversation: ConversationHistory,
) -> None:
    logger.info("Creating conversation %s for user %s", conversation.conversation_id, conversation.user_id)

    try:
        await conn.execute(
            """
            INSERT INTO conversations (conversation_id, user_id, title, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            conversation.conversation_id,
            conversation.user_id,
            conversation.title,
            conversation.created_at,
            conversation.updated_at,
        )
    except asyncpg.UniqueViolationError:
        logger.exception("Conversation %s already exists", conversation.conversation_id)
        raise
    except asyncpg.ForeignKeyViolationError:
        logger.exception("User %s does not exist", conversation.user_id)
        raise
    except asyncpg.PostgresError:
        logger.exception("Failed to create conversation %s", conversation.conversation_id)
        raise

async def get_conversations_by_user(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    user_id: str,
) -> list[ConversationHistory]:
    logger.info("Fetching conversations for user %s", user_id)

    try:
        rows = await conn.fetch(
            """
            SELECT conversation_id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = $1
            ORDER BY updated_at DESC
            """,
            user_id,
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to fetch conversations for user %s", user_id)
        raise

    return [
        ConversationHistory(
            conversation_id=str(row["conversation_id"]),
            user_id=str(row["user_id"]),
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


async def get_full_conversation(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    conversation_id: str,
) -> ConversationHistory | None:
    logger.info("Fetching full conversation %s", conversation_id)

    try:
        rows = await conn.fetch(
            """
            SELECT c.conversation_id, c.user_id, c.title, c.created_at, c.updated_at,
                   m.id, m.role, m.content, m.timestamp, m.tool_calls_made, m.cited_dois
            FROM conversations c
            LEFT JOIN chat_messages m ON m.conversation_id = c.conversation_id
            WHERE c.conversation_id = $1
            ORDER BY m.position ASC
            """,
            conversation_id,
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to fetch conversation %s", conversation_id)
        raise

    if not rows:
        return None

    first = rows[0]
    messages = [
        ChatMessage(
            id=str(row["id"]),
            role=MessageRole(row["role"]),
            content=row["content"],
            timestamp=row["timestamp"],
            tool_calls_made=list(row["tool_calls_made"]),
            cited_dois=list(row["cited_dois"]),
        )
        for row in rows
        if row["id"] is not None
    ]

    return ConversationHistory(
        conversation_id=str(first["conversation_id"]),
        user_id=str(first["user_id"]),
        title=first["title"],
        created_at=first["created_at"],
        updated_at=first["updated_at"],
        messages=messages,
    )