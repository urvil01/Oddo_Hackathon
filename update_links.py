import glob
import re

for filename in glob.glob("*.html"):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace the Discover link
    # Old: <a href="#" class="nav-link" onclick="Toast.info('Coming soon! 🌍'); return false;">
    # Old: <a href="#" class="nav-link" onclick="Toast.info('Coming soon!'); return false;">
    
    new_content = re.sub(
        r'<a href="#" class="nav-link" onclick="Toast\.info\(\'Coming soon!?(?: [^\']+)?\'\); return false;">(\s*<span class="icon">🌐</span> Discover\s*)</a>',
        r'<a href="discover.html" class="nav-link">\1</a>',
        content
    )
    
    if new_content != content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
