from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
    ) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
