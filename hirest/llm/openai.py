import os
from openai import OpenAI
from dotenv import load_dotenv

from hirest.llm.llm import ChatLLM

load_dotenv(override=True)
# Load environment variables from .env file

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")


class OpenAIChatLLM(ChatLLM):
    def __init__(self, model: str):
        self.model = model

    def invoke(self, messages: list[dict[str, str]]) -> str:
        """
        Invoke the OpenAI LLM with the given messages.

        Parameters
        ----------
        messages : list[dict[str, str]]
            The messages to send to the LLM.
            e.g. [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi!"}]

        Returns
        -------
        str
            The response from the LLM.
            e.g. "Hello! How can I help you today?"
        """
        openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        response = openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
        )


        return response.choices[0].message.content
