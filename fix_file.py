import os

# Read the clean code from our file
with open('clean_march_code.py', 'r', encoding='utf-8') as f:
    clean_march_code = f.read()

# Read the original tabs.py file
with open('tabs.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of MARCH_PYTHON_CODE
start_line = None
for i, line in enumerate(lines):
    if line.strip().startswith('MARCH_PYTHON_CODE ='):
        start_line = i
        break

# Find the end of MARCH_PYTHON_CODE (look for the closing triple quotes)
end_line = None
if start_line is not None:
    for i in range(start_line + 1, len(lines)):
        if lines[i].strip() == "'''":
            end_line = i
            break

# If we found both start and end, recreate the file
if start_line is not None and end_line is not None:
    # Create new content: lines before start + clean code + lines after end
    new_content = ''.join(lines[:start_line]) + clean_march_code + '\n' + ''.join(lines[end_line+1:])
    
    # Write the fixed content back to tabs.py
    with open('tabs.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('Successfully fixed tabs.py!')
else:
    print('Could not find MARCH_PYTHON_CODE in tabs.py')
