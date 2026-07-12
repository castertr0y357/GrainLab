import re
import subprocess
import os

with open("templates/partials/calculator_form.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find the start of x-data
start_idx = content.find('x-data="{')
if start_idx == -1:
    print("No x-data found in calculator_form.html")
    exit(0)

# Extract content inside x-data="..."
content = content[start_idx + len('x-data="'):]
# Find matching quote or end
# We can just split by the closing form tag or guess the end by brace matching
stack = 0
end_idx = -1
for idx, char in enumerate(content):
    if char == '{':
        stack += 1
    elif char == '}':
        stack -= 1
        if stack == 0:
            end_idx = idx
            break

if end_idx == -1:
    print("Could not find matching closing brace for x-data in calculator_form.html")
    exit(1)

js_content = content[:end_idx + 1]

# Clean up django variables to make it valid JS for Node
# Replace specific template constructs
js_content = re.sub(r'\{%\s*if.*?%\}\s*true\s*\{%\s*else.*?%\}\s*false\s*\{%\s*endif.*?\}', "false", js_content)
js_content = re.sub(r'\'\{%\s*if.*?%\}\s*sourdough\s*\{%\s*else.*?%\}\s*yeast\s*\{%\s*endif.*?\}\'', "'yeast'", js_content)

# Replace django tags wrapped in quotes first
js_content = re.sub(r'\'\{%.*?%\}\'', "''", js_content)
js_content = re.sub(r'\"\{%.*?%\}\"', "''", js_content)
js_content = re.sub(r'\'\{\{.*?\}\}\'', "''", js_content)
js_content = re.sub(r'\"\{\{.*?\}\}\"', "''", js_content)

# Replace unwrapped template variables
js_content = re.sub(r'\{%.*?%\}', "0", js_content)
js_content = re.sub(r'\{\{.*?\}\}', "0", js_content)

js_code = f"const xData = {js_content};\nmodule.exports = xData;"

js_temp_path = "scratch/temp_form_xdata.js"
with open(js_temp_path, "w", encoding="utf-8") as f:
    f.write(js_code)

print("Running Node.js validation on calculator_form.html x-data...")
result = subprocess.run(["node", "--check", js_temp_path], capture_output=True, text=True)

if result.returncode == 0:
    print("Success: Node.js verified that the syntax of calculator_form.html x-data is 100% valid!")
else:
    print("Syntax Error Found by Node.js:")
    print(result.stderr)
    print(result.stdout)
