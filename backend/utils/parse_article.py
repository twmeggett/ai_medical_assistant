import re
from datetime import datetime
from backend.models import CreateArticleRequest

def parse_article(article: str) -> CreateArticleRequest:
    def extract(label: str) -> str | None:
        match = re.search(rf"^{label}:\s*(.+)$", article, re.MULTILINE)
        return match.group(1).strip() if match else None

    title = extract("Title")
    journal = extract("Journal")
    published_raw = extract("Published")

    # "March 2024" -> datetime
    published_at = (
        datetime.strptime(published_raw, "%B %Y") if published_raw else None
    )

    # "Hargreaves, D.J., Patel, S.R., & Lindqvist, E." -> list
    authors_raw = extract("Authors")
    authors = (
        [a.strip().rstrip("&").strip() for a in re.split(r",\s*&?\s*", authors_raw) if a.strip()]
        if authors_raw else []
    )

    if not title:
        raise ValueError(f"Could not parse title from article")
    if not journal:
        raise ValueError(f"Could not parse journal from article")
    if not published_at:
        raise ValueError(f"Could not parse published_at from article")


    return CreateArticleRequest(
        title=title,
        authors=authors,
        journal=journal,
        published_at=published_at,
        full_text=article,
    )
