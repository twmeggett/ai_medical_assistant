import os
import re
from anthropic import AsyncAnthropic

from backend.prompts import ACTIVE_CHUNK_CONTEXT_SYSTEM_PROMPT
from typing import TypedDict


class SectionChunk(TypedDict):
    section: str
    content: str

client = AsyncAnthropic()
model = os.getenv("CLAUDE_HAIKU_MODEL", "claude-haiku-4-5-20251001")

# Standard section headings used in medical journal articles. Passed to
# chunk_by_sections to split an article before recursive chunking.
med_article_sections = ["Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusions", "References"]


def chunk_by_len(text: str, /, *, length: int, overlap: int) -> list[str]:
    # Naive fixed-length chunker with symmetric overlap (overlap chars on each side).
    # Useful for unstructured text or as a baseline; prefer chunk_by_sections for
    # medical articles where section boundaries carry semantic meaning.
    chunks = []
    start_index = 0
    while start_index < len(text):
        start = 0 if start_index < overlap else start_index - overlap
        end = start_index + length + overlap
        chunks.append(text[start:end])
        start_index = start_index + length

    return chunks


def chunk_by_recursion(
        text: str,
        *,
        chunk_size: int,
        chunk_overlap: int = 0,
        separators: list[str] = ["\n\n", "\n", " ", ""]
    ) -> list[str]:
    # Recursively splits text using progressively finer separators, accumulating
    # splits into a buffer until the next split would exceed chunk_size, then
    # flushing. Overlap is seeded from the tail of each flushed chunk so
    # retrieved chunks retain cross-boundary context.
    # Called per-section by chunk_by_sections; can also be used standalone.
    chars_to_token_count = 4
    char_size = chunk_size * chars_to_token_count
    char_overlap = chunk_overlap * chars_to_token_count

    if not separators or len(text) <= char_size:
        return [text]

    separator = separators[0]
    splits = [s for s in text.split(separator) if s]

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    for split in splits:
        split_len = len(split)
        sep_len = len(separator) if buffer else 0

        if split_len > char_size:
            # Flush buffer before recursing on the oversized split
            if buffer:
                chunks.append(separator.join(buffer))
                buffer = []
                buffer_len = 0
            chunks.extend(
                chunk_by_recursion(
                    split,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=separators[1:]
                )
            )
            continue

        if buffer_len + sep_len + split_len > char_size:
            # Buffer is full — flush and seed next buffer with overlap
            flushed = separator.join(buffer)
            chunks.append(flushed)
            overlap_text = flushed[-char_overlap:] if char_overlap else ""
            buffer = [overlap_text] if overlap_text else []
            buffer_len = len(overlap_text)
            sep_len = len(separator) if buffer else 0

        buffer.append(split)
        buffer_len += sep_len + split_len

    if buffer:
        chunks.append(separator.join(buffer))

    return chunks


def chunk_by_sections(
        article: str,
        sections: list[str],
        chunk_size: int,
        chunk_overlap: int
    ) -> list[SectionChunk]:
    # Primary chunking strategy for structured medical articles.
    # Step 1: split the article at section headings using a zero-width lookahead
    #         so each split segment retains its own heading.
    # Step 2: recursively chunk any section that exceeds chunk_size.
    # Returns dicts with 'section' and 'content' so callers can store section
    # metadata alongside each chunk without re-parsing the text.
    chunks = []
    pattern = r"(?=" + "|".join(map(re.escape, sections)) + r")"
    article_sections = re.split(pattern, article)
    for section_text in article_sections:
        first_line = section_text.split("\n")[0].strip()
        section_name = next((s for s in sections if first_line.startswith(s)), first_line)
        section_chunks = chunk_by_recursion(section_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks += [{"section": section_name, "content": chunk} for chunk in section_chunks]

    return chunks


async def create_context_for_chunk(resource: str, chunk: str) -> str:
    # Implements contextual retrieval: generates a short (≤50 word) description
    # of how the chunk relates to the source article, then the caller prepends
    # this context to the chunk text before embedding.
    # Store context and chunk separately in the DB — context is prepended for
    # embedding but both fields are useful independently at retrieval time.
    response = await client.messages.create(
        model=model,
        max_tokens=100,
        system=ACTIVE_CHUNK_CONTEXT_SYSTEM_PROMPT.content,
        messages=[
            {
                "role": "user",
                "content": f"<resources>{resource}</resources>\n\n<chunk>{chunk}</chunk>"
            }
        ],
    )

    return response.content[0].text.strip()  # type: ignore[union-attr]

