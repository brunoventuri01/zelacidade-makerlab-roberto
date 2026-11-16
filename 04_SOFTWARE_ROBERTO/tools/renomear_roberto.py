from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for path in ROOT.rglob('*'):
    if any(p in ('.git','.venv','runtime','__pycache__') for p in path.parts): continue
    if path.suffix not in ('.py','.md','.txt','.example','.sh'): continue
    text=path.read_text(encoding='utf-8')
    changed=text.replace('Roberto','Roberto').replace('ROBERTO','ROBERTO').replace('roberto','roberto')
    if changed!=text:path.write_text(changed,encoding='utf-8')
