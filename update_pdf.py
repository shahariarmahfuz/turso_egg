import glob

files = glob.glob('templates/*.html')
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    if "{ extend: 'pdfHtml5'" in content:
        # Avoid double replacing
        if "text: '<i class=\"fas fa-file-pdf\"></i>'" not in content:
            content = content.replace("{ extend: 'pdfHtml5'", "{ extend: 'pdfHtml5', text: '<i class=\"fas fa-file-pdf\"></i>', titleAttr: 'PDF'")
            with open(f, 'w') as file:
                file.write(content)
