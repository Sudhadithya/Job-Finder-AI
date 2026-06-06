import sys, io
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import fitz
from app.services.parser import parse_resume_text_fallback

doc = fitz.open('../Sudhadithya_Resume.pdf')
text = ''
for page in doc:
    text += page.get_text('text', sort=True) + '\n'
doc.close()

result = parse_resume_text_fallback(text)

print('metrics:', result.get('metrics'))
print()
print('=== EXPERIENCE ===')
for e in result.get('experience', []):
    print('  Company :', e['company'])
    print('  Role    :', e['role'])
    print('  Dates   :', e['start_date'], '->', e['end_date'])
    print('  Bullets :', len(e['highlights']))
    print()

print('=== PROJECTS ===')
for p in result.get('projects', []):
    print('  Name  :', p['name'])
    print('  Techs :', p['technologies'])
    print('  Highlights:', len(p['highlights']))
    print()
