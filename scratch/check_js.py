import re
from pathlib import Path

def check_js_brackets(file_path):
    content = Path(file_path).read_text(encoding='utf-8')
    stack = []
    brackets = {')': '(', '}': '{', ']': '['}
    lines = content.splitlines()
    
    in_str = False
    str_char = ''
    escape = False
    
    for line_num, line in enumerate(lines, 1):
        for col, char in enumerate(line, 1):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if in_str:
                if char == str_char:
                    in_str = False
                continue
            if char in ('"', "'", '`'):
                in_str = True
                str_char = char
                continue
            if char in ('//', '/*'):
                break
                
            if char in '({[':
                stack.append((char, line_num, col))
            elif char in ')}]':
                if not stack:
                    print(f"Unmatched closing '{char}' at {file_path}:{line_num}:{col}")
                    return False
                top_char, top_line, top_col = stack.pop()
                if brackets[char] != top_char:
                    print(f"Mismatched '{char}' at {file_path}:{line_num}:{col}, expected matching for '{top_char}' from {top_line}:{top_col}")
                    return False
    
    if stack:
        top_char, top_line, top_col = stack[-1]
        print(f"Unclosed '{top_char}' from {file_path}:{top_line}:{top_col}")
        return False
        
    print(f"SUCCESS: {file_path} syntax brackets are 100% valid!")
    return True

check_js_brackets("application/frontend/data.js")
check_js_brackets("application/frontend/app.js")
