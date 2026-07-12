import re

with open("templates/calculator.html", "r", encoding="utf-8") as f:
    content = f.read()

# Strip out scripts, comments, template tags to make parsing simpler
content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)

# Find all div tags: <div ...> (opening) and </div> (closing)
tags = re.findall(r'</?div(?:\s+[^>]*?)?>', content, re.IGNORECASE)

stack = []
for tag in tags:
    is_closing = tag.startswith('</')
    if not is_closing:
        # Opening div
        stack.append(tag)
    else:
        # Closing div
        if not stack:
            print("ERROR: Found closing </div> but div stack is empty!")
        else:
            stack.pop()

print(f"Brace matching finished. Remaining unclosed divs in stack: {len(stack)}")
if stack:
    print("Unclosed divs:")
    for tag in stack:
        print(tag[:100])
