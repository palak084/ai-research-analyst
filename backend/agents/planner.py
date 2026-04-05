from .llm import call_llm

def plan_task(text: str):
    prompt = f"""
    Break this research task into steps:
    {text}
    """

    return call_llm(prompt)
