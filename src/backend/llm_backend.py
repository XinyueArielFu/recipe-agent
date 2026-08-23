from abc import ABC, abstractmethod

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

################################################
import requests

class OllamaBackend(LLMBackend):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt):
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False, # set to False in order to get full response at once, otherwise defualt returns token-by-token
            }
        )
        result = response.json() # ollama returns in json, response help convert to dict
        return result["response"] # response stored in "response" attribute

if __name__ == "__main__":
    # backend = OllamaBackend("llama3.2:3b")
    backend = OllamaBackend("llama3:latest")

    # answer = backend.generate("Can you teach me how to make chiffon cake")
    answer = backend.generate("用一句话介绍一下你自己")
    print(answer)