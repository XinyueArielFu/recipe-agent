##################### LLMBackend abstract class ################
from abc import ABC, abstractmethod

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    def generate_with_tools(self, messages: list, tools: list) -> dict:
        pass

######################## OllamaBackend ########################
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

    def generate_with_tools(self, messages: list, tools: list) -> dict:
        ollama_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                }
            }
            for tool in tools
        ]

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": self.model_name,
                "messages": messages,
                "tools": ollama_tools,
                "stream": False,
            }
        )
        # print("+++++++++++ Ollam Backend 'Message' debug +++++++++++++")
        # result = response.json()
        # message = result["message"]

        result = response.json()
        print("DEBUG - Ollama raw response:", result) 
        message = result["message"]

        if message.get("tool_calls"):
            call = message["tool_calls"][0]
            return {
                        "stop_reason": "tool_use",
                        "tool_name": call["function"]["name"],
                        "tool_input": call["function"]["arguments"],
                        "raw_content": message,
                    }

        return {
            "stop_reason": "end_turn",
            "text": message["content"],
        }

######################## AnthropicBackend ###################
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

class AnthropicBackend(LLMBackend):
    def __init__(self, model_name: str = "claude-sonnet-5"):
        self.model_name = model_name
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    def generate_with_tools(self, messages: list, tools: list) -> dict:
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1000,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_block = next(block for block in response.content if block.type == "tool_use")
            return {
                "stop_reason": "tool_use",
                "tool_name": tool_block.name,
                "tool_input": tool_block.input,
                "tool_use_id": tool_block.id,
                "raw_content": response.content,
            }

        text_block = next(b for b in response.content if b.type == "text")
        return {
            "stop_reason": "end_turn",
            "text": text_block.text,
        }

def get_backend(name: str) -> LLMBackend:
    backends = {
        "llama": OllamaBackend("llama3.2:3b"),
        "llama-large": OllamaBackend("llama3:latest"),
        "deepseek": OllamaBackend("deepseek-r1:8b"),
        "claude": AnthropicBackend(),
    }

    if name not in backends:
        raise ValueError(f"Unknown backend: {name}. Available: {list(backends.keys())}")
    return backends[name]
                         


if __name__ == "__main__":
    # backend = OllamaBackend("llama3.2:3b")
    # backend = OllamaBackend("llama3:latest")
    # answer = backend.generate("Can you teach me how to make chiffon cake")
    # answer = backend.generate("用一句话介绍一下你自己")
    # print(answer)

    # backend = AnthropicBackend()
    # answer = backend.generate("用一句话介绍一下你自己")
    # print(answer)

    backend = get_backend("deepseek")
    answer = backend.generate("用一句话介绍一下你自己")
    print(answer)
    