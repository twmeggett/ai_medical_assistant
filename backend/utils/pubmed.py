import os
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from backend.models.domain import Article, ArticleType, Author

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _base_params() -> dict:
    params: dict = {"db": "pubmed"}
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key
    return params


async def esearch(
    query: str,
    max_results: int,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[str]:
    params = {
        **_base_params(),
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    if date_from or date_to:
        params["datetype"] = "pdat"
    if date_from:
        params["mindate"] = date_from.replace("-", "/")
    if date_to:
        params["maxdate"] = date_to.replace("-", "/")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ENTREZ_BASE}/esearch.fcgi", params=params)
        response.raise_for_status()

    return response.json()["esearchresult"]["idlist"]


async def efetch(pmids: list[str]) -> list[Article]:
    if not pmids:
        return []

    params = {
        **_base_params(),
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ENTREZ_BASE}/efetch.fcgi", params=params)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    articles = []
    for article_el in root.findall(".//PubmedArticle"):
        try:
            articles.append(_parse_article(article_el))
        except Exception:
            continue
    return articles


async def esummary(pmids: list[str]) -> dict:
    params = {
        **_base_params(),
        "id": ",".join(pmids),
        "retmode": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ENTREZ_BASE}/esummary.fcgi", params=params)
        response.raise_for_status()
    return response.json().get("result", {})


def _parse_article(article_el: ET.Element) -> Article:
    citation = article_el.find("MedlineCitation")
    if citation is None:
        raise ValueError("Missing MedlineCitation element")

    article_data = citation.find("Article")
    if article_data is None:
        raise ValueError("Missing Article element")

    pmid = (citation.findtext("PMID") or "").strip()
    title = (article_data.findtext("ArticleTitle") or "").strip()

    abstract_parts = [t.text or "" for t in article_data.findall(".//AbstractText")]
    abstract = " ".join(abstract_parts).strip() or "No abstract available."

    journal_el = article_data.find("Journal")
    if journal_el is not None:
        journal = journal_el.findtext("Title") or journal_el.findtext("ISOAbbreviation") or ""
        pub_date_el = journal_el.find(".//PubDate")
    else:
        journal = ""
        pub_date_el = None
    published_date = _parse_pub_date(pub_date_el)

    authors = []
    for author_el in article_data.findall(".//Author"):
        last = author_el.findtext("LastName") or ""
        fore = author_el.findtext("ForeName") or ""
        affiliation = author_el.findtext(".//Affiliation")
        name = f"{fore} {last}".strip() if fore else last
        if name:
            authors.append(Author(name=name, affiliation=affiliation))

    doi = None
    for loc_el in article_data.findall("ELocationID"):
        if loc_el.get("EIdType") == "doi":
            doi = loc_el.text
            break
    if doi is None:
        for aid in article_el.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text
                break

    article_type = _parse_article_type(article_data)
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    return Article(
        pmid=pmid,
        doi=doi,
        title=title,
        authors=authors,
        journal=journal,
        published_date=published_date,
        abstract=abstract,
        article_type=article_type,
        url=url,
    )


def _parse_pub_date(pub_date_el: ET.Element | None) -> datetime:
    if pub_date_el is None:
        return datetime.now()

    year = pub_date_el.findtext("Year")
    month = pub_date_el.findtext("Month") or "Jan"
    day = pub_date_el.findtext("Day") or "1"
    medline_date = pub_date_el.findtext("MedlineDate")

    if year:
        for fmt in ("%Y %b %d", "%Y %m %d", "%Y %B %d"):
            try:
                return datetime.strptime(f"{year} {month} {day}", fmt)
            except ValueError:
                continue
        return datetime(int(year), 1, 1)

    if medline_date:
        parts = medline_date.split()
        try:
            return datetime(int(parts[0]), 1, 1)
        except (ValueError, IndexError):
            pass

    return datetime.now()


def _parse_article_type(article_data: ET.Element) -> ArticleType:
    types = " ".join(
        (t.text or "").lower() for t in article_data.findall(".//PublicationType")
    )
    if "meta-analysis" in types:
        return ArticleType.META_ANALYSIS
    if "systematic review" in types or "review" in types:
        return ArticleType.REVIEW
    if "case report" in types:
        return ArticleType.CASE_STUDY
    return ArticleType.RESEARCH


def format_citation(summary: dict, fmt: str) -> str:
    raw_authors = [a["name"] for a in summary.get("authors", []) if a.get("authtype") == "Author"]
    title = summary.get("title", "")
    journal = summary.get("source", "")
    pub_date = summary.get("pubdate", "")
    volume = summary.get("volume", "")
    issue = summary.get("issue", "")
    pages = summary.get("pages", "")
    doi = summary.get("elocationid", "").replace("doi: ", "")
    year = pub_date.split()[0] if pub_date else ""

    if fmt == "Vancouver":
        authors = ", ".join(raw_authors[:6])
        if len(raw_authors) > 6:
            authors += " et al"
        vol_issue = f"{volume}({issue})" if volume and issue else volume or issue
        parts = filter(None, [f"{authors}.", title, f"{journal}.", f"{year};{vol_issue}:{pages}.", f"doi:{doi}"])
        return " ".join(parts)

    if fmt == "APA":
        apa = []
        for name in raw_authors[:20]:
            parts = name.split()
            if len(parts) >= 2:
                apa.append(f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}.")
        if len(apa) > 2:
            author_str = ", ".join(apa[:-1]) + ", & " + apa[-1]
        else:
            author_str = " & ".join(apa)
        vol_str = f"{volume}({issue})" if volume and issue else volume or issue
        doi_str = f"https://doi.org/{doi}" if doi else ""
        parts = filter(None, [f"{author_str} ({year}).", title, f"{journal},", f"{vol_str},", f"{pages}.", doi_str])
        return " ".join(parts)

    # MLA
    author_str = raw_authors[0] if raw_authors else ""
    if len(raw_authors) > 1:
        author_str += ", et al"
    vol_str = f"vol. {volume}" if volume else ""
    issue_str = f"no. {issue}" if issue else ""
    parts = filter(None, [f'{author_str}.', f'"{title}"', f"{journal},", vol_str, issue_str, f"{year},", f"pp. {pages}."])
    return " ".join(parts)
