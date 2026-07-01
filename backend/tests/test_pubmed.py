import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.models.domain import ArticleType
from backend.utils.pubmed import (
    _parse_article,
    _parse_article_type,
    _parse_pub_date,
    _get,
    format_citation,
)

MINIMAL_ARTICLE_XML = """
<PubmedArticle>
  <MedlineCitation>
    <PMID>12345678</PMID>
    <Article>
      <ArticleTitle>Effect of metformin on glycemic control</ArticleTitle>
      <Abstract>
        <AbstractText>This study examines metformin.</AbstractText>
      </Abstract>
      <Journal>
        <Title>The Lancet</Title>
        <JournalIssue>
          <PubDate><Year>2023</Year><Month>Mar</Month><Day>15</Day></PubDate>
        </JournalIssue>
      </Journal>
      <AuthorList>
        <Author>
          <LastName>Smith</LastName>
          <ForeName>John</ForeName>
        </Author>
      </AuthorList>
      <PublicationTypeList>
        <PublicationType>Journal Article</PublicationType>
      </PublicationTypeList>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""


def _article_el() -> ET.Element:
    return ET.fromstring(MINIMAL_ARTICLE_XML)


def test_parse_article_fields():
    article = _parse_article(_article_el())
    assert article.pmid == "12345678"
    assert "metformin" in article.title.lower()
    assert article.journal == "The Lancet"
    assert len(article.authors) == 1
    assert article.authors[0].name == "John Smith"
    assert article.abstract == "This study examines metformin."
    assert "12345678" in article.url


def test_parse_article_type_research():
    article_data = _article_el().find(".//Article")
    assert _parse_article_type(article_data) == ArticleType.RESEARCH


def test_parse_article_type_meta_analysis():
    xml = MINIMAL_ARTICLE_XML.replace("Journal Article", "Meta-Analysis")
    el = ET.fromstring(xml).find(".//Article")
    assert _parse_article_type(el) == ArticleType.META_ANALYSIS


def test_parse_article_type_review():
    xml = MINIMAL_ARTICLE_XML.replace("Journal Article", "Systematic Review")
    el = ET.fromstring(xml).find(".//Article")
    assert _parse_article_type(el) == ArticleType.REVIEW


def test_parse_article_type_case_study():
    xml = MINIMAL_ARTICLE_XML.replace("Journal Article", "Case Report")
    el = ET.fromstring(xml).find(".//Article")
    assert _parse_article_type(el) == ArticleType.CASE_STUDY


def test_parse_pub_date_year_month_day():
    xml = "<PubDate><Year>2022</Year><Month>Jun</Month><Day>5</Day></PubDate>"
    el = ET.fromstring(xml)
    dt = _parse_pub_date(el)
    assert dt.year == 2022
    assert dt.month == 6
    assert dt.day == 5


def test_parse_pub_date_medline_fallback():
    xml = "<PubDate><MedlineDate>2020 Jan-Feb</MedlineDate></PubDate>"
    el = ET.fromstring(xml)
    dt = _parse_pub_date(el)
    assert dt.year == 2020


def test_parse_pub_date_none_returns_now():
    dt = _parse_pub_date(None)
    assert isinstance(dt, datetime)


def test_parse_article_missing_medline_citation_raises():
    el = ET.fromstring("<PubmedArticle></PubmedArticle>")
    with pytest.raises(ValueError, match="MedlineCitation"):
        _parse_article(el)


@pytest.mark.asyncio
async def test_get_retries_on_429():
    responses = [
        MagicMock(status_code=429, headers={"Retry-After": "0"}),
        MagicMock(status_code=200, raise_for_status=MagicMock()),
    ]
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=responses)

    with patch("backend.utils.pubmed.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("backend.utils.pubmed.asyncio.sleep", new=AsyncMock()):
            result = await _get("http://example.com", {}, max_retries=3)

    assert mock_client.get.call_count == 2
    assert result.status_code == 200


def test_format_citation_vancouver():
    summary = {
        "authors": [{"name": "Smith J", "authtype": "Author"}],
        "title": "A study on X.",
        "source": "JAMA",
        "pubdate": "2023 Jan",
        "volume": "10",
        "issue": "2",
        "pages": "100-105",
        "elocationid": "doi: 10.1001/jama.2023",
    }
    citation = format_citation(summary, "Vancouver")
    assert "Smith J" in citation
    assert "JAMA" in citation
    assert "10(2):100-105" in citation


def test_format_citation_apa():
    # format_citation treats the last word as the last name; use "FirstName LastName" order
    summary = {
        "authors": [{"name": "Alice Jones", "authtype": "Author"}],
        "title": "A study on Y.",
        "source": "NEJM",
        "pubdate": "2021",
        "volume": "5",
        "issue": "1",
        "pages": "50-60",
        "elocationid": "",
    }
    citation = format_citation(summary, "APA")
    assert "Jones" in citation
    assert "NEJM" in citation
    assert "2021" in citation


def test_format_citation_mla():
    summary = {
        "authors": [{"name": "Brown Bob", "authtype": "Author"}],
        "title": "A study on Z.",
        "source": "BMJ",
        "pubdate": "2019",
        "volume": "3",
        "issue": "4",
        "pages": "200",
        "elocationid": "",
    }
    citation = format_citation(summary, "MLA")
    assert "Brown Bob" in citation
    assert "BMJ" in citation
