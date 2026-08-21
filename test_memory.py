from memory import remember, recall, get_all_memory


# Save information
print(
    remember(
        "favorite_language",
        "Python"
    )
)


# Retrieve information
print(
    "\nRemembered value:"
)

print(
    recall("favorite_language")
)


# Show everything remembered
print(
    "\nAll memory:"
)

print(
    get_all_memory()
)