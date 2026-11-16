"""Reexecuta os arquivos sinteticos ja gerados, sem tocar som ou disputar a webcam."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from core.local_audio import LocalRecognizer
from core.desktop import DesktopRuntime
r=DesktopRuntime(ROOT);r.config=dict(r.config,voz_ativa=False)
asr=LocalRecognizer(ROOT/r.config['modelo_fala'])
expected=['ARM_UP','LED_ON','nome','chamada','ARM_DOWN','ignorar','ignorar']
out=[]
for i,target in enumerate(expected):
    before=r.sequence;started=time.monotonic()
    text=asr.transcribe(str(ROOT/'data'/'testes_audio'/f'frase_{i}.wav'))
    accepted=r.process(text,started_at=started)
    events=[e for e in r.events if e['seq']>before]
    passed=any(e['type']=='action' and e['data']['action']==target for e in events) if target.startswith(('ARM','LED')) else (
        any(e['type']=='assistant' and 'Meu nome é Roberto' in e['data'] for e in events) if target=='nome' else (
        r.window_until>time.monotonic() if target=='chamada' else not accepted))
    out.append(dict(arquivo=f'frase_{i}.wav',transcricao=text,esperado=target,passou=passed,segundos=round(time.monotonic()-started,2)))
    print(json.dumps(out[-1],ensure_ascii=False),flush=True)
r.close()
(ROOT/'data'/'testes_audio'/'resultado_fluxo_final.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
sys.exit(0 if all(t['passou'] for t in out) else 1)
