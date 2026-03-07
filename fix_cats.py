path = r'C:\xampp\htdocs\ThesisLibrary\main\templates\main\categories.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: The split normal-search radio tag (most critical - causes the error)
bad1 = """<input type="radio" name="search_mode" value="normal" {% if not
                                        request.GET.search_mode or request.GET.search_mode=='normal' %}checked{% endif
                                        %}>"""
good1 = """<input type="radio" name="search_mode" value="normal" {% if not request.GET.search_mode or request.GET.search_mode == 'normal' %}checked{% endif %}>"""

# Fix 2: The split deep-search radio tag inside can_full_view block
bad2 = """<input type="radio" name="search_mode" value="deep" {% if
                                        request.GET.search_mode=='deep' %}checked{% endif %}>"""
good2 = """<input type="radio" name="search_mode" value="deep" {% if request.GET.search_mode == 'deep' %}checked{% endif %}>"""

# Fix 3: sort options missing spaces
fixes = [
    ("{% if current_sort=='date-desc' %}", "{% if current_sort == 'date-desc' %}"),
    ("{% if current_sort=='date-asc' %}", "{% if current_sort == 'date-asc' %}"),
    ("{% if current_sort=='title-asc' %}", "{% if current_sort == 'title-asc' %}"),
    ("{% if current_sort=='title-desc' %}", "{% if current_sort == 'title-desc' %}"),
    ("{% if current_sort=='author-asc' %}", "{% if current_sort == 'author-asc' %}"),
    ("{% if current_sort=='author-desc' %}", "{% if current_sort == 'author-desc' %}"),
    ("request.GET.search_mode=='normal'", "request.GET.search_mode == 'normal'"),
    ("request.GET.search_mode=='deep'", "request.GET.search_mode == 'deep'"),
]

# Apply the multi-line fixes
if bad1 in content:
    content = content.replace(bad1, good1)
    print("Fixed: normal radio split tag")
else:
    print("WARNING: normal radio split tag NOT FOUND - dumping area around 'search_mode' value='normal'")
    idx = content.find("value=\"normal\"")
    print(repr(content[idx-20:idx+300]))

if bad2 in content:
    content = content.replace(bad2, good2)
    print("Fixed: deep radio split tag")
else:
    print("WARNING: deep radio split tag NOT FOUND")
    idx = content.find("value=\"deep\"")
    if idx != -1:
        print(repr(content[idx-10:idx+200]))

for bad, good in fixes:
    if bad in content:
        content = content.replace(bad, good)
        print("Fixed: " + bad)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nAll done - file saved.")
