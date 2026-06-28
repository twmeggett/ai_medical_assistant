search_journals_schema = {
    "name": "search_journals",
    "description": (
        "Search an internal medical literature database for peer-reviewed articles "
        "relevant to a clinical or research question. Use this when the user asks "
        "about evidence, studies, guidelines, or current literature on a medical topic. "
        "Returns a list of articles with title, authors, journal, publication year, and abstract."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 3,
                "maxLength": 500,
                "description": (
                    "A search query to run against the medical literature database. "
                    "Supports Boolean operators (AND, OR, NOT) and quoted phrases. "
                    "Example: 'metformin AND \"type 2 diabetes\"'"
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
        "Retrieve the full details of a specific medical article by its DOI. "
        "Use this when you have a DOI and need the complete article metadata "
        "including abstract, authors, journal, and publication date."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "doi": {
                "type": "string",
                "description": (
                    "The Digital Object Identifier (DOI) of the article to retrieve. "
                    "Must start with '10.'. Example: '10.1056/NEJMoa2034577'"
                ),
            },
        },
        "required": ["doi"],
        "additionalProperties": False,
    },
}

cite_sources_schema = {
    "name": "cite_sources",
    "description": (
        "Generate formatted citations for a list of articles identified by DOI. "
        "Use this after identifying relevant articles to produce a properly formatted "
        "reference list for the user."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "dois": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 10,
                "description": (
                    "List of DOIs to generate citations for. "
                    "Each DOI must start with '10.'. "
                    "Example: ['10.1056/NEJMoa2034577', '10.1001/jama.2021.1395']"
                ),
            },
            "format": {
                "type": "string",
                "enum": ["APA", "MLA", "Vancouver"],
                "default": "APA",
                "description": "Citation format to use. Defaults to APA.",
            },
        },
        "required": ["dois"],
        "additionalProperties": False,
    },
}

ALL_TOOLS = [search_journals_schema, get_article_schema, cite_sources_schema]
