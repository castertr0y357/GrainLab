import re

with open("templates/calculator.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract x-data content from line 5 (0-indexed line 4) to line 1064 (0-indexed line 1063)
# We want the string inside x-data="..."
content = "".join(lines[4:1064])

# Remove django template tags like {% ... %} and {{ ... }} to avoid syntax noise
# Replace {% ... %} with space of same length
content = re.sub(r'\{%.*?%\}', lambda m: " " * len(m.group(0)), content)
# Replace {{ ... }} with space of same length
content = re.sub(r'\{\{.*?\}\}', lambda m: " " * len(m.group(0)), content)

# Check brace matching
stack = []
for idx, char in enumerate(content):
    if char in "([{":
        stack.append((char, idx))
    elif char in ")]}":
        if not stack:
            print(f"Unmatched closing char '{char}' at index {idx}")
            # print surrounding text
            start = max(0, idx - 40)
            end = min(len(content), idx + 40)
            print("Context:", repr(content[start:end]))
        else:
            open_char, open_idx = stack.pop()
            if (open_char == "(" and char != ")") or \
               (open_char == "[" and char != "]") or \
               (open_char == "{" and char != "}"):
                print(f"Mismatch: '{open_char}' at index {open_idx} closed by '{char}' at index {idx}")
                # print context for opening
                ostart = max(0, open_idx - 40)
                oend = min(len(content), open_idx + 40)
                print("Opening Context:", repr(content[ostart:oend]))
                # print context for closing
                cstart = max(0, idx - 40)
                cend = min(len(content), idx + 40)
                print("Closing Context:", repr(content[cstart:cend]))

if stack:
    print(f"Remaining open brackets/braces: {len(stack)}")
    for open_char, open_idx in stack:
        print(f"Unclosed '{open_char}' at index {open_idx}")
        start = max(0, open_idx - 40)
        end = min(len(content), open_idx + 40)
        print("Context:", repr(content[start:end]))
else:
    print("All braces and brackets matched successfully according to stack parser!")
