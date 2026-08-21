from python_tool import run_python


code = """
numbers = [10, 20, 30, 40, 50]

average = sum(numbers) / len(numbers)

print("Average:", average)
"""


result = run_python(code)

print(result)