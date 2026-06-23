"""Claude-powered AI assistant for AI OS."""
import os
from typing import Generator
import anthropic


class AIAssistant:
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        self.history: list[dict] = []
        self.system_prompt = (
            "You are ARIA (Artificial Reasoning & Intelligence Assistant), "
            "the built-in AI of AI OS — a futuristic operating system. "
            "You help users with tasks, answer questions, write code, manage files, "
            "and generally act as a knowledgeable OS-integrated AI assistant. "
            "Be concise, helpful, and slightly futuristic in tone. "
            "When relevant, you can suggest shell commands the user can run."
        )

    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            messages=self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def stream(self, user_input: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": user_input})
        full_reply = []
        with self.client.messages.stream(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            messages=self.history,
        ) as stream:
            for text in stream.text_stream:
                full_reply.append(text)
                yield text
        self.history.append({"role": "assistant", "content": "".join(full_reply)})

    def reset(self):
        self.history.clear()
