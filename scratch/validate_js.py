import re
import subprocess
import os

with open("templates/calculator.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract x-data content from line 5 (0-indexed line 4) to line 1064 (0-indexed line 1063)
# We want the string inside x-data="..."
content = "".join(lines[4:1064])
content = content[content.find("{"):]

# Remove django template tags {% ... %} and {{ ... }} completely
# Replace them with valid JS syntax placeholders so that Node can parse it as valid JS
# E.g. replace {% if selected_preset %}3{% else %}1{% endif %} with 1
# Replace {{ default_flour_type|default:"all_purpose" }} with 'all_purpose'
# E.g. replace {% for wb in active_berries %} ... {% endfor %} with a sample array

# Print the line matching global_ai_enabled to inspect it
for line in content.splitlines():
    if "global_ai_enabled" in line:
        print("BEFORE REPLACEMENT LINE:", repr(line))

# Replace specific template constructs
content = re.sub(r'\{%\s*if.*?%\}\s*true\s*\{%\s*else.*?%\}\s*false\s*\{%\s*endif.*?\}', "false", content)
content = re.sub(r'\{%\s*if.*?%\}\s*3\s*\{%\s*else.*?%\}\s*1\s*\{%\s*endif.*?\}', "1", content)
content = re.sub(r'\{%\s*for.*?active_berries.*?%\}.*?\{%\s*endfor.*?\}', "[]", content, flags=re.DOTALL)

# Replace django tags wrapped in quotes first
content = re.sub(r'\'\{%.*?%\}\'', "''", content)
content = re.sub(r'\"\{%.*?%\}\"', "''", content)
content = re.sub(r'\'\{\{.*?\}\}\'', "''", content)
content = re.sub(r'\"\{\{.*?\}\}\"', "''", content)

# Replace unwrapped django tags
content = re.sub(r'\{%.*?%\}', "0", content)
content = re.sub(r'\{\{.*?\}\}', "0", content)

# Strip trailing HTML tag characters
content = content.split('">')[0].strip()

# Wrap it as a JS object module export
js_code = f"const xData = {content};\nmodule.exports = xData;"

# Write to temp file
js_temp_path = "scratch/temp_xdata.js"
with open(js_temp_path, "w", encoding="utf-8") as f:
    f.write(js_code)

print("Running Node.js validation on extracted javascript...")
result = subprocess.run(["node", "--check", js_temp_path], capture_output=True, text=True)

if result.returncode == 0:
    print("Success: Node.js verified that the syntax of x-data is 100% valid!")
else:
    print("Syntax Error Found by Node.js:")
    print(result.stderr)
    print(result.stdout)
