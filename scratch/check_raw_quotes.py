with open("scratch/rendered_calculator_form.html", "r", encoding="utf-8") as f:
    content = f.read()

# Let's find the start of x-data
start_idx = content.find('x-data="{')
if start_idx == -1:
    print("Could not find x-data in rendered html!")
    exit(1)

# Now, let's parse the attribute value exactly like a browser HTML parser would.
attr_content = content[start_idx + len('x-data="'):]
end_idx = -1
for idx, char in enumerate(attr_content):
    if char == '"':
        end_idx = idx
        break

if end_idx == -1:
    print("Could not find closing quote for attribute!")
    exit(1)

value = attr_content[:end_idx]
print(f"Browser-parsed attribute value length: {len(value)}")
print("Browser-parsed value starts with:")
print(repr(value[:200]))
print("Browser-parsed value ends with:")
print(repr(value[-200:]))

# Let's run a Javascript syntax check on what the browser actually parses!
js_code = f"const xData = {value};\nmodule.exports = xData;"
with open("scratch/browser_parsed_form_xdata.js", "w", encoding="utf-8") as f:
    f.write(js_code)

import subprocess
result = subprocess.run(["node", "--check", "scratch/browser_parsed_form_xdata.js"], capture_output=True, text=True)
if result.returncode == 0:
    print("Success: Node.js verified that the browser-parsed JS is 100% syntactically correct!")
else:
    print("Syntax Error Found in Browser-parsed JS:")
    print(result.stderr)
