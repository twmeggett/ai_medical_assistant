search_journals_schema = {
    "name": "search_journals",
    "description": (
        "Search PubMed for peer-reviewed articles relevant to a clinical or research question. "
        "Use this when the user asks about evidence, studies, guidelines, or current literature "
        "on a medical topic. Returns a list of articles with title, authors, journal, "
        "publication year, abstract, and PubMed ID (PMID)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 3,
                "maxLength": 500,
                "description": (
                    "A search query to run against PubMed. Supports Boolean operators "
                    "(AND, OR, NOT), quoted phrases, field tags (e.g. [MeSH Terms], [Title], "
                    "[Author]), and MeSH terms. "
                    "Example: 'metformin AND \"type 2 diabetes\"[MeSH Terms]'"
                ),
            },
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Maximum number of articles to return.",
            },
            "date_from": {
                "type": "string",
                "description": "Filter articles published on or after this date (YYYY-MM-DD).",
            },
            "date_to": {
                "type": "string",
                "description": "Filter articles published on or before this date (YYYY-MM-DD).",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

get_article_schema = {
    "name": "get_article",
    "description": (
        "Retrieve the full details of a specific PubMed article by its PMID. "
        "Use this when you have a PMID and need the complete article metadata "
        "including abstract, authors, journal, and publication date."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "pmid": {
                "type": "string",
                "description": (
                    "The PubMed ID (PMID) of the article to retrieve. "
                    "A numeric string assigned by PubMed. Example: '34567890'"
                ),
            },
        },
        "required": ["pmid"],
        "additionalProperties": False,
    },
}

cite_sources_schema = {
    "name": "cite_sources",
    "description": (
        "Generate formatted citations for a list of PubMed articles identified by PMID. "
        "Use this after identifying relevant articles to produce a properly formatted "
        "reference list for the user."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "pmids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 10,
                "description": (
                    "List of PubMed IDs (PMIDs) to generate citations for. "
                    "Each PMID is a numeric string assigned by PubMed. "
                    "Example: ['34567890', '33798342']"
                ),
            },
            "format": {
                "type": "string",
                "enum": ["APA", "MLA", "Vancouver"],
                "default": "APA",
                "description": "Citation format to use. Defaults to APA.",
            },
        },
        "required": ["pmids"],
        "additionalProperties": False,
    },
}

ALL_TOOLS = [search_journals_schema, get_article_schema, cite_sources_schema]
