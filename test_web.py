from core.tool_manager import ToolManager

tools = ToolManager()

result = tools.execute(
    "web_search",
    expression="latest Ubuntu release"
)

print()
print("=" * 60)
print("WEB SEARCH TEST")
print("=" * 60)
print(result)
