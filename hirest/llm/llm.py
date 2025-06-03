from abc import ABC, abstractmethod

class ChatLLM(ABC):
    @abstractmethod
    def invoke(self, messages: list[dict[str, str]]) -> str:
        """
        Invoke the LLM with the given messages.

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
        pass