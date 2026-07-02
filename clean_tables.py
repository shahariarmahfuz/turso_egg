import re
import glob

def clean_td_classes(match):
    tag = match.group(0)
    for c in ['text-primary', 'text-success', 'text-danger', 'text-info', 'text-warning', 'fw-bold', 'font-weight-bold']:
        tag = re.sub(r'\b' + c + r'\b', '', tag)
    tag = re.sub(r'class="\s+"', '', tag)
    tag = re.sub(r'class="\s*([^"]+)\s*"', r'class="\1"', tag)
    tag = tag.replace(' class=""', '')
    return tag

def clean_action_button(match):
    full_tag = match.group(0)
    opening = match.group(1)
    icon = match.group(2)
    text = match.group(3)
    closing = match.group(4)
    
    clean_text = text.replace('&nbsp;', '').strip()
    
    if 'title="' not in opening and clean_text:
        opening = opening.replace('<a ', f'<a title="{clean_text}" ').replace('<button ', f'<button title="{clean_text}" ')
            
    return f"{opening}{icon}{closing}"

for filepath in glob.glob('templates/*.html'):
    with open(filepath, 'r') as f:
        content = f.read()
        
    orig_content = content
    
    # 1. Clean td classes
    content = re.sub(r'<td[^>]*class="[^"]*"[^>]*>', clean_td_classes, content)
    
    # 2. Clean buttons inside td
    # We will use a regex to find <td>...</td> blocks and then sub within them
    def process_td(td_match):
        td_content = td_match.group(0)
        td_content = re.sub(r'(<a[^>]+class="[^"]*btn[^"]*"[^>]*>)\s*(<i[^>]+></i>)\s*([^<]*)\s*(</a>)', clean_action_button, td_content)
        td_content = re.sub(r'(<button[^>]+class="[^"]*btn[^"]*"[^>]*>)\s*(<i[^>]+></i>)\s*([^<]*)\s*(</button>)', clean_action_button, td_content)
        return td_content
        
    content = re.sub(r'<td.*?>.*?</td>', process_td, content, flags=re.DOTALL)
    
    if content != orig_content:
        with open(filepath, 'w') as f:
            f.write(content)
