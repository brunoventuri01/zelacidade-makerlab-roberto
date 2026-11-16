from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent/'ROBERTO_PARA_FACULDADE';SOFT=DEST/'04_SOFTWARE_ROBERTO'
required=['ABRA_PRIMEIRO.html','INICIAR_ROBERTO.bat','01_FUSION/ROBERTO_MONTADO.f3d','01_FUSION/ROBERTO_PECAS_ESPALHADAS.f3d','02_CORTE_LASER/ROBERTO_40_PECAS_NOMINAL.dxf','03_ARDUINO/Firmware/Roberto/Roberto.ino','03_ARDUINO/GRAVAR_ARDUINO.bat','05_GUIAS/01_MONTAGEM_MDF.html','05_GUIAS/02_ARDUINO_E_FIOS.html','05_GUIAS/ESQUEMA_FIOS.svg','04_SOFTWARE_ROBERTO/python/python.exe','04_SOFTWARE_ROBERTO/models/whisper-small/model.bin','04_SOFTWARE_ROBERTO/models/piper/pt_BR-cadu-medium.onnx','04_SOFTWARE_ROBERTO/runtime/ollama/ollama.exe','04_SOFTWARE_ROBERTO/runtime/arduino-cli/arduino-cli.exe']
for name in required:assert (DEST/name).is_file(),name
assert len(list((DEST/'02_CORTE_LASER/PECAS_INDIVIDUAIS').glob('*.dxf')))==40
assert len(list((DEST/'02_CORTE_LASER/TESTE_PRIMEIRO').glob('*.dxf')))==2
assert not (SOFT/'data/faces').exists(),'Nao distribuir cadastros faciais desta sessao'
assert not (SOFT/'models/faces.yml').exists(),'Nao distribuir modelo facial pessoal'
assert (SOFT/'data/agenda.txt').read_text(encoding='utf-8')==''
cfg=json.loads((SOFT/'config_roberto.json').read_text(encoding='utf-8'));assert cfg['modo_simulacao'] is True
assert (DEST/'03_ARDUINO/Firmware/Roberto/Roberto.ino').read_bytes()==(ROOT/'firmware/Roberto/Roberto.ino').read_bytes()
assert 'INPUT_PULLUP' in (ROOT/'firmware/Roberto/Roberto.ino').read_text()
manifest={}
for name in required:
    path=DEST/name;h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(4*1024*1024):h.update(chunk)
    manifest[name]={'bytes':path.stat().st_size,'sha256':h.hexdigest()}
(DEST/'VERIFICACAO_DO_PACOTE.json').write_text(json.dumps({'arquivos_essenciais':manifest,'pecas_robo':40,'corpos_prova':2,'modo_inicial':'simulacao','dados_pessoais_excluidos':True},indent=2,ensure_ascii=False),encoding='utf-8')
print('Pacote verificado: arquivos essenciais, 40 DXFs + 2 testes, firmware consistente e dados pessoais excluidos.')
