import re
from html.parser import HTMLParser

class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        # Ignore self-closing tags in HTML5
        if tag in ["img", "input", "br", "hr", "meta", "link", "col", "base", "area", "param"]:
            return
        self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in ["img", "input", "br", "hr", "meta", "link", "col", "base", "area", "param"]:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag}> at line {self.getpos()[0]}")
            return
        expected, pos = self.stack.pop()
        if expected != tag:
            self.errors.append(f"Mismatched tag: Expected </{expected}> (opened at line {pos[0]}), but found </{tag}> at line {self.getpos()[0]}")
            # Put expected back so we can keep going
            self.stack.append((expected, pos))

# Read recipe_output.html
with open("templates/partials/recipe_output.html", "r", encoding="utf-8") as f:
    content = f.read()

# Strip django template comments and tags to avoid parsing errors
# Replace {% ... %} and {{ ... }} with whitespace to preserve positions
content = re.sub(r'\{%.*?%\}', lambda m: " " * len(m.group(0)), content)
content = re.sub(r'\{\{.*?\}\}', lambda m: " " * len(m.group(0)), content)

checker = TagChecker()
checker.feed(content)

print(f"Tag matching finished. Stack size: {len(checker.stack)}")
if checker.errors:
    print("Found HTML structure errors:")
    for err in checker.errors:
        print(err)
if checker.stack:
    print("Unclosed tags remaining on stack:")
    for tag, pos in checker.stack:
        print(f"<{tag}> opened at line {pos[0]}")
else:
    print("All tags matched correctly!")
