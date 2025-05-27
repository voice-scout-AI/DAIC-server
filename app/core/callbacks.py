from langchain.callbacks.base import BaseCallbackHandler

from app.core.config import DEBUG


class PromptLoggerCallback(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.is_active = DEBUG

    def on_llm_start(self, serialized, prompts, **kwargs):
        if not self.is_active:
            return

        print(f"[🔥🔥🔥🔥LLM 호출 프롬프트🔥🔥🔥🔥]:")

        for prompt in prompts:
            print(prompt)
