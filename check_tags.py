import re

path = r'C:\xampp\htdocs\ThesisLibrary\main\templates\main\categories.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
results = []
for i, line in enumerate(lines, 1):
    if '{%' in line:
        results.append(f"{i}: {line.strip()}")

with open(r'C:\xampp\htdocs\ThesisLibrary\tags_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print("Done")
