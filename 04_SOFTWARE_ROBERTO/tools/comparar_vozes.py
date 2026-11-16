import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core.local_audio import PiperVoiceBackend,LocalRecognizer
dest=ROOT/'data'/'testes_audio';dest.mkdir(parents=True,exist_ok=True)
recognizer=LocalRecognizer(ROOT/'models'/'whisper-small')
results=[]
for name in ['cadu','jeff']:
    backend=PiperVoiceBackend(ROOT/f'models/piper/pt_BR-{name}-medium.onnx')
    phrase='Pronto, Roberto. Vou levantar meu braço direito. Agora vou acender a luz e responder à sua pergunta.'
    output=dest/f'voz_{name}.wav';backend.synthesize_wav(phrase,output)
    transcript=recognizer.transcribe(str(output))
    results.append({'voz':name,'transcricao_teste_R':transcript})
    print(name,transcript,flush=True)
    if name=='cadu':backend.speak(phrase)
(dest/'comparacao_vozes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
