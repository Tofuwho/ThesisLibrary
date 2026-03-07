path = r'C:\xampp\htdocs\ThesisLibrary\main\templates\main\user_list.html'
out_path = r'C:\xampp\htdocs\ThesisLibrary\ul_includes.txt'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

results = []
for i, line in enumerate(lines):
    if 'include' in line and 'admin_sidebar' not in line:
        results.append(f"Line {i+1} repr: {repr(line)}")
        if i+1 < len(lines):
            results.append(f"Line {i+2} repr: {repr(lines[i+1])}")
        results.append("")

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print("Done, check ul_includes.txt")
