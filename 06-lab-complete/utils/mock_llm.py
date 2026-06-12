import random
import time


MOCK_RESPONSES = {
    "default": [
        "This is a mock AI agent response. In production this would come from a real LLM.",
        "The agent is running correctly. Ask another question when you are ready.",
        "I am a cloud-deployed AI agent. Your question has been received.",
    ],
    "docker": [
        "Docker packages an app with its dependencies so it can run consistently anywhere."
    ],
    "deploy": [
        "Deployment moves code from a local machine to a server or cloud platform for users to access."
    ],
    "health": [
        "The agent is healthy and operational."
    ],
}


def ask(question: str, delay: float = 0.1) -> str:
    time.sleep(delay + random.uniform(0, 0.05))
    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])


def ask_stream(question: str):
    for word in ask(question).split():
        time.sleep(0.05)
        yield word + " "
