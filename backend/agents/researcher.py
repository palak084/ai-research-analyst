from .llm import call_llm

def analyze_chunk(chunk: str):
    prompt = f"""
    Analyze this text and extract key points:

    {chunk}
    """

    return call_llm(prompt)
