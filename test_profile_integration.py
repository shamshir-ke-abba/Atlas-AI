from core.profile_store import ProfileStore
from core.tool_manager import ToolManager


store = ProfileStore()

print("=== ProfileStore ===")
print("Path:", store.path())
print("Name:", store.get("identity.name"))

print("\n=== ToolManager ===")

tools = ToolManager(
    profile_store=store
)

print("Available tools:")
print(tools.available())

print("\n=== Profile attachment ===")

for name in ("fitness", "nutrition", "calendar"):

    plugin = tools.get(name)

    if plugin is None:
        print(f"{name}: NOT FOUND")
        continue

    attached = getattr(
        plugin,
        "profile_store",
        None,
    )

    print(
        f"{name}:",
        "CONNECTED" if attached is store else "NOT CONNECTED"
    )

print("\n=== Shared store test ===")

store.set(
    "identity.name",
    "Atlas Test User",
)

print(
    "Store:",
    store.get("identity.name")
)

print(
    "Fitness sees:",
    tools.get("fitness").profile_store.get(
        "identity.name"
    )
)

print(
    "Nutrition sees:",
    tools.get("nutrition").profile_store.get(
        "identity.name"
    )
)

print("\nIntegration test complete.")
