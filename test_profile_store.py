from core.profile_store import ProfileStore


store = ProfileStore()

print("Profile file:")
print(store.path())

print("\nCurrent profile:")
print(store.get_profile())

print("\nSaving test profile...")

store.set(
    "identity.name",
    "Atlas User"
)

store.set(
    "fitness.goal",
    "general fitness"
)

store.set(
    "fitness.experience",
    "beginner"
)

store.set(
    "nutrition.diet",
    "balanced"
)

store.set(
    "nutrition.preferences",
    ["home cooked food"]
)

print("\nSaved profile:")
print(store.get_profile())

print("\nIndividual values:")
print("Name:", store.get("identity.name"))
print("Fitness goal:", store.get("fitness.goal"))
print("Experience:", store.get("fitness.experience"))
print("Diet:", store.get("nutrition.diet"))
print(
    "Food preferences:",
    store.get("nutrition.preferences")
)

print("\nConfigured:")
print(store.is_configured())

print("\nPersistence test:")
store2 = ProfileStore()

print(
    "Loaded name:",
    store2.get("identity.name")
)

print(
    "Loaded fitness goal:",
    store2.get("fitness.goal")
)

print(
    "Loaded nutrition diet:",
    store2.get("nutrition.diet")
)
