from .llm import call_llm

def generate_insights(text: str):
    prompt = f"""
    Extract insights (patterns, trends, key signals):

    {text}
    """

    return call_llm(prompt)
