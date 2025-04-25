from typing import Any, Generator
from pydantic import Field
from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback
import requests


class GWDGChatLLM(CustomLLM):
    model: str = Field(default="llama-3.1-8b-instruct")
    api_base: str = Field(default="https://llm.hrz.uni-giessen.de/api/")
    api_key: str = Field(default="")
    temperature: float = Field(default=0.1)
    system_prompt: str = Field(default="")

    context_window: int = 4096
    num_output: int = 512


    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }

        response = requests.post(
            f"{self.api_base}/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return CompletionResponse(text=content)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        full_response = self.complete(prompt)
        yield CompletionResponse(text=full_response.text, delta=full_response.text)
