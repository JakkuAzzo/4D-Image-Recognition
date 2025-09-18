#!/usr/bin/env python3
"""
JavaScript Brace Checker
========================
Find exact location of unmatched braces/parens
"""

def check_js_syntax():
    html_file = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/frontend/unified-pipeline.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find the script section
    script_start = -1
    script_end = -1
    
    for i, line in enumerate(lines):
        if '<script>' in line and 'Combined JavaScript functionality' in lines[i+1] if i+1 < len(lines) else False:
            script_start = i + 1  # Start after <script> line
        elif '</script>' in line and script_start != -1 and script_end == -1:
            script_end = i  # End before </script> line
            break
    
    if script_start == -1 or script_end == -1:
        print("Could not find script section")
        return
    
    print(f"Found script section: lines {script_start + 1} to {script_end + 1}")
    
    # Check syntax line by line
    brace_count = 0
    paren_count = 0
    bracket_count = 0
    
    in_string = False
    in_comment = False
    string_char = None
    
    problems = []
    
    for i in range(script_start, script_end):
        line = lines[i]
        line_num = i + 1
        
        # Track string and comment state
        j = 0
        while j < len(line):
            char = line[j]
            
            if not in_string and not in_comment:
                if char == '/' and j + 1 < len(line):
                    if line[j + 1] == '/':
                        in_comment = True
                        break
                    elif line[j + 1] == '*':
                        in_comment = True
                        j += 1
                elif char in ['"', "'", '`']:
                    in_string = True
                    string_char = char
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count < 0:
                        problems.append(f"Line {line_num}: Extra closing brace - total brace count now {brace_count}")
                elif char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count < 0:
                        problems.append(f"Line {line_num}: Extra closing paren - total paren count now {paren_count}")
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
            elif in_string:
                if char == string_char and (j == 0 or line[j-1] != '\\'):
                    in_string = False
                    string_char = None
            elif in_comment:
                if char == '*' and j + 1 < len(line) and line[j + 1] == '/':
                    in_comment = False
                    j += 1
            
            j += 1
        
        # Reset comment state at end of line for // comments
        if in_comment and '//' in line:
            in_comment = False
        
        # Check for significant imbalances every 50 lines
        if (i - script_start) % 50 == 0 and (brace_count != 0 or paren_count != 0):
            print(f"Line {line_num}: Braces: {brace_count}, Parens: {paren_count}, Brackets: {bracket_count}")
    
    print(f"\n📊 Final counts:")
    print(f"Braces: {brace_count} (should be 0)")
    print(f"Parens: {paren_count} (should be 0)")
    print(f"Brackets: {bracket_count} (should be 0)")
    
    if problems:
        print(f"\n⚠️  Found {len(problems)} syntax problems:")
        for problem in problems[:10]:  # Show first 10
            print(f"  {problem}")
    
    # Look for specific patterns that might cause issues
    print(f"\n🔍 Looking for problematic patterns...")
    
    problematic_lines = []
    for i in range(script_start, script_end):
        line = lines[i].strip()
        line_num = i + 1
        
        # Look for missing semicolons before braces
        if line.endswith('{') and not line.endswith('() {') and not line.endswith('} {') and 'function' not in line:
            if i > 0 and not lines[i-1].strip().endswith((';', '{', '}')):
                problematic_lines.append(f"Line {line_num}: Possible missing semicolon before opening brace")
        
        # Look for function syntax issues
        if 'function' in line and not line.strip().startswith('//'):
            if 'function(' in line or ')function' in line:
                problematic_lines.append(f"Line {line_num}: Suspicious function syntax: '{line}'")
    
    for problem in problematic_lines[:10]:
        print(f"  {problem}")
    
    return brace_count == 0 and paren_count == 0

if __name__ == "__main__":
    is_valid = check_js_syntax()
    print(f"\n🎯 JavaScript syntax: {'✅ VALID' if is_valid else '❌ INVALID'}")