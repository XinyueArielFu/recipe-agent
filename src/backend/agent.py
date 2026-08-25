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

def handle_query(user_query: str, backend_name: str = "claude") -> str:
    backend = get_backend(backend_name)

    messages = [
        {"role": "user", "content": user_query}
    ]

    response = backend.client.messages.create(
        model=backend.model_name,
        max_tokens = 1000,
        tools=tools,
        messages=messages
    )

    if response.stop_reason == "tool_use":
        # FOR NOW: only take the first tool request
        tool_use_block = next(block for block in response.content if block.type == "tool_use") 
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input

        print(f"[Agent decided to call: {tool_name}({tool_input})]")

        tool_function = TOOL_FUNCTIONS[tool_name]
        tool_result = tool_function(**tool_input)

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user", 
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": str(tool_result)
                }
            ]
        })

        final_response = backend.client.messages.create(
            model=backend.model_name,
            max_tokens=1000,
            tools=tools,
            messages=messages
        )
        return final_response.content[0].text
    return response.content[0].text

if __name__ == "__main__":
    answer = handle_query("椰子冻需要哪些食材？")
    print("\n--- Final Answer ---")
    print(answer)