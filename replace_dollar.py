import os
import re

directories = ['/workspaces/egg/templates', '/workspaces/egg']

for directory in directories:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html') or file.endswith('.py'):
                if file == 'replace_dollar.py':
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                
                # Replace ${{ with ৳{{
                content = content.replace('${{', '৳{{')
                
                # Replace $ {{ with ৳ {{
                content = content.replace('$ {{', '৳ {{')
                
                # Replace $ followed by digit
                content = re.sub(r'\$(?=[0-9])', '৳', content)
                
                # Replace $ followed by space and digit
                content = re.sub(r'\$\s+(?=[0-9])', '৳ ', content)
                
                # Replace fa-dollar-sign
                content = content.replace('fa-dollar-sign', 'fa-money-bill-wave')
                content = content.replace('fa-hand-holding-usd', 'fa-hand-holding-dollar') # Actually let's just use fa-money-bill
                content = content.replace('fa-file-invoice-dollar', 'fa-file-invoice')

                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {filepath}")
