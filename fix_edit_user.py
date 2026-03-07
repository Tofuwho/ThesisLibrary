path = r'C:\xampp\htdocs\ThesisLibrary\fix_edit_user.py'
out = r'C:\xampp\htdocs\ThesisLibrary\edit_user_check.txt'
with open(r'C:\xampp\htdocs\ThesisLibrary\main\templates\main\edit_user.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
results = []
for i, line in enumerate(lines, 1):
    if 'profile.role' in line or 'role==' in line or "role ==" in line:
        results.append(f"Line {i}: {repr(line.rstrip())}")
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
print("Done")
