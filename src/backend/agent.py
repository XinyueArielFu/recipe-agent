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

OLLAMA_SYSTEM_PROMPT = (
    "You are a recipe assistant. When a tool returns information about multiple recipes, "
    "you must only extract and use information about the ONE recipe the user is asking about. "
    "Completely ignore all other recipes in the tool output. "
    "Do not mention any other recipe names in your answer."
)

def handle_query(user_query: str, backend_name: str = "claude", max_turns=5) -> str:
    backend = get_backend(backend_name)

    messages = [
        {"role": "user", "content": user_query}
    ]

    if backend_name != "claude":
        messages.insert(0, {"role": "system", "content": OLLAMA_SYSTEM_PROMPT})

    for turn in range(max_turns):
        print(f"\n--- Turn {turn + 1} messages sent to model ---")
        print(messages)
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
            messages.append({"role": "assistant", "content": "", "tool_calls": result["raw_content"].get("tool_calls", [])})
            messages.append({
                "role": "tool",
                "content": str(tool_result)
            })

    return f"I'm having trouble completing this request after multiple tool calls. Exceed max turn limit {max_turns}"

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

    # print("\n=== Ollama (llama3.2:3b) ===")
    # print(handle_query("椰子冻需要哪些食材？", backend_name="llama"))

    print("=== Test 1: SQL query (llama3.2:3b) ===")
    answer1 = handle_query("椰子冻需要哪些食材？", backend_name="llama")
    print(answer1)

    print("\n=== Test 2: RAG search (llama3.2:3b) ===")
    answer2 = handle_query("椰子冻要怎么做？", backend_name="llama")
    print(answer2)

    print("\n=== Test 3: temperature conversion (llama3.2:3b) ===")
    answer3 = handle_query("350华氏度是多少摄氏度？", backend_name="llama")
    print(answer3)