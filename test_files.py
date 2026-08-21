from file_tools import write_file, read_file, append_file


# Create a file
print(
    write_file(
        "notes.txt",
        "Hello! This file was created by my agent."
    )
)


# Read the file
print("\nFile contents:")
print(
    read_file("notes.txt")
)


# Add more content
print(
    append_file(
        "notes.txt",
        "\nPython is being used to build my agent."
    )
)


# Read again
print("\nUpdated file contents:")
print(
    read_file("notes.txt")
)