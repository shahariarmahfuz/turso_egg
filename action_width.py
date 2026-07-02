import glob

for filepath in glob.glob('templates/*.html'):
    with open(filepath, 'r') as f:
        content = f.read()
        
    orig_content = content
    
    # Target exact <th>Action</th>
    # Some might be <th> Action </th>
    # We will replace them with <th style="width: 1%; white-space: nowrap;">Action</th>
    import re
    content = re.sub(r'<th>\s*Action\s*</th>', '<th style="width: 1%; white-space: nowrap;">Action</th>', content)
    
    if content != orig_content:
        with open(filepath, 'w') as f:
            f.write(content)
