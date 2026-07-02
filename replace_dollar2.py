import os
import re

directories = ['/workspaces/egg/templates', '/workspaces/egg']

for directory in directories:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html') or file.endswith('.py'):
                if file == 'replace_dollar2.py' or file == 'replace_dollar.py':
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                
                # Replace remaining fa-hand-holding-dollar and fa-dollar-sign (just in case)
                content = content.replace('fa-hand-holding-dollar', 'fa-money-bill-wave')
                content = content.replace('fa-dollar-sign', 'fa-money-bill-wave')

                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {filepath}")
