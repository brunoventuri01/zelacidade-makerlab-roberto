"""Pacote Windows local com Python, modelos e guias; sem dados pessoais da sessao."""
from pathlib import Path
import hashlib,html,json,os,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
DEST=WORK/'ROBERTO_PARA_FACULDADE'
DEST.mkdir(exist_ok=True)
for name in ['01_FUSION','02_CORTE_LASER','03_ARDUINO','04_SOFTWARE_ROBERTO','05_GUIAS']:(DEST/name).mkdir(exist_ok=True)
SOFT=DEST/'04_SOFTWARE_ROBERTO';MDF=WORK/'RoboMDF'

def copy(source,target):
    source=Path(source);target=Path(target)
    if target.exists() and source.stat().st_size==target.stat().st_size and int(source.stat().st_mtime)==int(target.stat().st_mtime):return
    # Ferramentas AVR possuem caminhos longos; usa a forma longa nativa do Windows.
    src='\\\\?\\'+str(source.resolve()) if os.name=='nt' else str(source)
    dst='\\\\?\\'+str(target.resolve()) if os.name=='nt' else str(target)
    Path(dst).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
def tree(source,target,exclude=()):
    source=Path(source);target=Path(target)
    for base,dirs,files in os.walk(source):
        dirs[:]=[d for d in dirs if d not in set(exclude)|{'__pycache__','.git','.cache'}]
        rel=Path(base).relative_to(source)
        for name in files:
            if name.endswith(('.pyc','.pyo')) or name in exclude:continue
            copy(Path(base)/name,target/rel/name)

copy(MDF/'CP5_Robo_Inteligente_MDF.f3d',DEST/'01_FUSION'/'ROBERTO_MONTADO.f3d')
copy(MDF/'CP5_Vista_de_Corte.f3d',DEST/'01_FUSION'/'ROBERTO_PECAS_ESPALHADAS.f3d')
copy(MDF/'montagem_Fusion.png',DEST/'01_FUSION'/'ROBERTO_MONTADO.png')
copy(MDF/'Vista_de_corte.png',DEST/'01_FUSION'/'ROBERTO_PECAS_ESPALHADAS.png')
for name in ['RoboMDF.py','RoboMDF.manifest','geometria.py','config.json','plano.py','pecas.json','plano_resultado.json']:
    copy(MDF/name,DEST/'01_FUSION'/'GERADOR_PARAMETRICO'/name)
copy(MDF/'Lista_de_pecas.csv',DEST/'02_CORTE_LASER'/'LISTA_DE_PECAS.csv')
for path in (MDF/'DXF_nominal').glob('*.dxf'):
    copy(path,DEST/'02_CORTE_LASER'/('TESTE_PRIMEIRO' if path.stem.startswith('TESTE') else 'PECAS_INDIVIDUAIS')/path.name)
sys.path.insert(0,str(MDF));import geometria
parts=json.loads((MDF/'pecas.json').read_text());pos={v['id']:v for v in json.loads((MDF/'plano_resultado.json').read_text())['posicoes']}
combined={'loops':[],'circles':[]}
for part in parts:
    if part['id'].startswith('TESTE'):continue
    points=[pt for loop in part['loops'] for pt in loop];dx=pos[part['id']]['x_mm']-min(x for x,y in points);dy=pos[part['id']]['y_mm']-min(y for x,y in points)
    combined['loops'] += [[(x+dx,y+dy) for x,y in loop] for loop in part['loops']]
    combined['circles'] += [(x+dx,y+dy,r) for x,y,r in part['circles']]
geometria.dxf(combined,DEST/'02_CORTE_LASER'/'ROBERTO_40_PECAS_NOMINAL.dxf')

for name in ['core','skills','web','tools','tests','firmware']:tree(ROOT/name,SOFT/name)
for name in ['app.py','main.py','iniciar.py','gravar_arduino.py','INICIAR_ROBERTO.bat','GRAVAR_ARDUINO.bat','requirements.txt','requirements-local.lock.txt','.env.example','LEIA_ROBERTO.md','GUIA_ARDUINO_PASSO_A_PASSO.md','GUIA_CORTE_LASER.md','TESTES_ROBERTO.md']:
    if (ROOT/name).exists():copy(ROOT/name,SOFT/name)
cfg=json.loads((ROOT/'config_roberto.json').read_text());cfg.update(modo_simulacao=True,microfone_ativo=True,webcam_ativa=True,porta_painel=8765,dispositivo_microfone=None,dispositivo_saida=None)
(SOFT/'config_roberto.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
(SOFT/'.env').write_text('LLM_BACKEND=ollama\nOLLAMA_URL=http://127.0.0.1:11435\nOLLAMA_MODEL=gemma3:4b\nWAKE_WORD=roberto\nTTS_BACKEND=piper\nSTT_BACKEND=local\nIDIOMA_STT=pt-BR\n',encoding='utf-8')
(SOFT/'data'/'logs').mkdir(parents=True,exist_ok=True)
(SOFT/'data'/'agenda.txt').write_text('',encoding='utf-8')
print('Copiando modelos locais...',flush=True)
tree(ROOT/'models'/'whisper-small',SOFT/'models'/'whisper-small')
tree(ROOT/'models'/'ollama',SOFT/'models'/'ollama')
for suffix in ['.onnx','.onnx.json']:
    copy(ROOT/'models'/'piper'/('pt_BR-cadu-medium'+suffix),SOFT/'models'/'piper'/('pt_BR-cadu-medium'+suffix))
(SOFT/'models'/'labels.json').write_text('{}',encoding='utf-8')
for name in ['ollama','arduino-cli','arduino-data','arduino-user']:
    print('Copiando ferramenta:',name,flush=True);tree(ROOT/'runtime'/name,SOFT/'runtime'/name,exclude=('firmwares','doc','docs','examples'))
print('Copiando Python portatil...',flush=True)
base=Path(sys.base_prefix)
for name in ['python.exe','pythonw.exe','python3.dll','python312.dll','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt']:copy(base/name,SOFT/'python'/name)
tree(base/'DLLs',SOFT/'python'/'DLLs')
tree(base/'Lib',SOFT/'python'/'Lib',exclude=('site-packages','test','tests','idlelib','ensurepip'))
tree(base/'tcl',SOFT/'python'/'tcl')
tree(ROOT/'.venv'/'Lib'/'site-packages',SOFT/'python'/'Lib'/'site-packages')
(SOFT/'python'/'python312._pth').write_text('.\nLib\nDLLs\nLib\\site-packages\n..\nimport site\n',encoding='utf-8')
tree(ROOT/'firmware'/'Roberto',DEST/'03_ARDUINO'/'Firmware'/'Roberto')
tree(ROOT/'firmware'/'compilado',DEST/'03_ARDUINO'/'Compilado')
for name in ['INICIAR_ROBERTO','GRAVAR_ARDUINO']:
    target=DEST/(name+'.bat') if name=='INICIAR_ROBERTO' else DEST/'03_ARDUINO'/(name+'.bat')
    rel='04_SOFTWARE_ROBERTO' if name=='INICIAR_ROBERTO' else '..\\04_SOFTWARE_ROBERTO'
    target.write_text('@echo off\ncall "%~dp0'+rel+'\\'+name+'.bat"\n',encoding='ascii')
copy(ROOT/'GUIA_ARDUINO_PASSO_A_PASSO.md',DEST/'05_GUIAS'/'02_ARDUINO_E_FIOS.md')
copy(MDF/'Manual_de_montagem.md',DEST/'05_GUIAS'/'01_MONTAGEM_MDF.md')
if (ROOT/'TESTES_ROBERTO.md').exists():copy(ROOT/'TESTES_ROBERTO.md',DEST/'05_GUIAS'/'03_TESTES_E_PENDENCIAS.md')
copy(ROOT/'LEIA_ROBERTO.md',DEST/'05_GUIAS'/'04_USAR_O_ROBERTO.md')
print('Pacote criado em',DEST,flush=True)
