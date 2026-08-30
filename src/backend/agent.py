import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from backend.llm_backend import get_backend
from backend.tools import tools, convert_temperature, query_recipe_sql, search_recipe_notes

TOOL_FUNCTIONS = {
    "convert_temperature": convert_temperature,
    "query_recipe_sql": query_recipe_sql,
    "search_recipe_notes": search_recipe_notes
}

def handle_query(user_query: str, backend_name: str = "claude", max_turns=5) -> str:
    backend = get_backend(backend_name)

    messages = [
        {"role": "user", "content": user_query}
    ]

    for turn in range(max_turns):
        result = backend.generate_with_tools(messages, tools)

        if result["stop_reason"] != "tool_use":
            return result["text"]
        
        # FOR NOW: only take the first tool request
        tool_name = result["tool_name"]
        tool_input = result["tool_input"]

        print(f"[Turn {turn + 1}] Agent decided to call: {tool_name}({tool_input})")

        tool_function = TOOL_FUNCTIONS[tool_name]
        tool_result = tool_function(**tool_input)

        if "tool_use_id" in result:
            messages.append({"role": "assistant", "content": result["raw_content"]})
            messages.append({
                "role": "user", 
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": result["tool_use_id"],
                        "content": str(tool_result)
                    }
                ]
            })
        else:
            # because Ollam demand "content" has to be string instead of a dictionary object which Antheropic accepts
            messages.append({"role": "assistant", "content": "", "tool_calls": result["raw_content"].get("tool_call", [])})
            messages.append({
                "role": "tool",
                "content": str(tool_result)
            })

    return "I'm having trouble completing this request after multiple tool calls."

if __name__ == "__main__":
    # print("=== Test 1: SQL query ===")
    # answer1 = handle_query("椰子冻需要哪些食材？")
    # print(answer1)

    # print("\n=== Test 2: RAG search ===")
    # answer2 = handle_query("椰子冻要怎么做？")
    # print(answer2)

    # print("\n=== Test 3: temperature conversion ===")
    # answer3 = handle_query("350华氏度是多少摄氏度？")
    # print(answer3)

    # print("=== Claude ===")
    # print(handle_query("椰子冻需要哪些食材？", backend_name="claude"))

    print("\n=== Ollama (llama3.2:3b) ===")
    print(handle_query("椰子冻需要哪些食材？", backend_name="llama"))