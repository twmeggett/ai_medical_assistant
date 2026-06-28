import logging
import asyncpg
from backend.models.domain import ChatMessage, MessageRole

logger = logging.getLogger(__name__)

async def save_message(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    conversation_id: str,
    message: ChatMessage,
) -> None:
    logger.info("Saving message %s to conversation %s", message.id, conversation_id)

    try:
        await conn.execute(
            """
            INSERT INTO chat_messages
                (id, conversation_id, role, content, timestamp, tool_calls_made, cited_dois, position)
            VALUES ($1, $2, $3, $4, $5, $6, $7,
                COALESCE(
                    (SELECT MAX(position) + 1 FROM chat_messages WHERE conversation_id = $2),
                    0
                )
            )
            """,
            message.id,
            conversation_id,
            message.role.value,
            message.content,
            message.timestamp,
            message.tool_calls_made,
            message.cited_dois,
        )
    except asyncpg.UniqueViolationError:
        logger.exception("Message %s already exists", message.id)
        raise
    except asyncpg.ForeignKeyViolationError:
        logger.exception("Conversation %s does not exist", conversation_id)
        raise
    except asyncpg.PostgresError:
        logger.exception("Failed to save message %s", message.id)
        raise


async def get_messages(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    conversation_id: str,
) -> list[ChatMessage]:
    logger.info("Fetching messages for conversation %s", conversation_id)

    try:
        rows = await conn.fetch(
            """
            SELECT id, role, content, timestamp, tool_calls_made, cited_dois
            FROM chat_messages
            WHERE conversation_id = $1
            ORDER BY position ASC
            """,
            conversation_id,
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to fetch messages for conversation %s", conversation_id)
        raise

    return [
        ChatMessage(
            id=str(row["id"]),
            role=MessageRole(row["role"]),
            content=row["content"],
            timestamp=row["timestamp"],
            tool_calls_made=list(row["tool_calls_made"]),
            cited_dois=list(row["cited_dois"]),
        )
        for row in rows
    ]
