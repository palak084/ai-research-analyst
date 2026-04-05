from .llm import call_llm


def summarize_document(text: str, doc_name: str = "") -> str:
    prompt = f"""Summarize the following document concisely, capturing the main arguments,
key findings, methodology, and conclusions. Keep it under 300 words.

Document: {doc_name}

{text[:3000]}
"""
    return call_llm(prompt)


def compare_documents(doc_summaries: dict[str, str]) -> str:
    docs_text = ""
    for name, summary in doc_summaries.items():
        docs_text += f"\n--- Document: {name} ---\n{summary}\n"

    prompt = f"""Compare the following documents and provide a structured analysis:

{docs_text}

Provide your comparison in this format:

1. KEY THEMES: Common themes across all documents
2. SIMILARITIES: What the documents agree on or share
3. DIFFERENCES: Where the documents diverge or contradict
4. UNIQUE POINTS: Notable points unique to each document
5. OVERALL ASSESSMENT: A brief synthesis of how these documents relate to each other
"""
    return call_llm(prompt)
