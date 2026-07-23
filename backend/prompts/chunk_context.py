from backend.models.prompts import PromptVersion

CHUNK_CONTEXT_SYSTEM_V1 = PromptVersion(
    content=(
        "You are a medical knowledge assistant. You will be given source resources and a text chunk "
        "extracted from one of those resources.\n\n"
        "Your task is to write 1-2 sentences (maximum 50 words) that situate the chunk within the broader "
        "context of the resources — for example, which article it comes from, which section it belongs to, "
        "and how it relates to the article's overall argument or findings. "
        "Do not summarise the chunk itself. Reply with only the context sentences, no preamble.\n\n"
        "Resources will be provided in <resources> tags. The chunk to contextualise will be in <chunk> tags."
    ),
    version="1.0",
    sprint=4,
    optimized_for="RAG chunk contextualisation for medical journal articles",
    notes=(
        "Prepend the returned context to the chunk before embedding. "
        "50-word cap keeps context from diluting the chunk's own semantic signal. "
        "Inspired by Anthropic's contextual retrieval technique."
    ),
)

ACTIVE_CHUNK_CONTEXT_SYSTEM_PROMPT = CHUNK_CONTEXT_SYSTEM_V1
