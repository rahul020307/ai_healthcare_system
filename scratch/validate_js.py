import re

def check_brackets(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    lines = content.split('\n')
    for line_no, line in enumerate(lines, 1):
        for char in line:
            if char in '({[':
                stack.append((char, line_no))
            elif char in ')}]':
                if not stack:
                    print(f"Unmatched closing '{char}' at line {line_no} in {filename}")
                    return False
                top, top_line = stack.pop()
                expected = {'(': ')', '{': '}', '[': ']'}[top]
                if char != expected:
                    print(f"Mismatch '{top}' from line {top_line} closed by '{char}' at line {line_no} in {filename}")
                    return False
    if stack:
        top, top_line = stack[-1]
        print(f"Unclosed '{top}' from line {top_line} in {filename}")
        return False
    print(f"✅ {filename} syntax brackets OK ({len(lines)} lines)")
    return True

check_brackets('application/frontend/data.js')
check_brackets('application/frontend/app.js')
