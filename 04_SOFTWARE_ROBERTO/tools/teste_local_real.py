"""Ensaios reais de componentes. Fala sintetizada NAO substitui ensaio humano."""
import base64,json,os,sys,time,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
REPORT=[]
def test(name,fn):
    started=time.monotonic()
    try:
        value=fn();REPORT.append({'teste':name,'passou':True,'segundos':round(time.monotonic()-started,2),'resultado':value})
        print(name,'OK',str(value)[:240],flush=True)
    except Exception as exc:
        REPORT.append({'teste':name,'passou':False,'erro':repr(exc)});print(name,'FALHOU',exc,flush=True)
    (ROOT/'data'/'diagnostico_local.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')

def synth(text,path):
    import pythoncom,win32com.client
    pythoncom.CoInitialize()
    try:
        voice=win32com.client.Dispatch('SAPI.SpVoice')
        for token in voice.GetVoices():
            if '416' in token.GetAttribute('Language'):voice.Voice=token;break
        stream=win32com.client.Dispatch('SAPI.SpFileStream');stream.Open(str(path),3,False)
        voice.AudioOutputStream=stream;voice.Speak(text,0);stream.Close()
        return voice.Voice.GetDescription()
    finally:pythoncom.CoUninitialize()

def main():
    (ROOT/'data'/'testes_audio').mkdir(parents=True,exist_ok=True)
    import numpy as np,sounddevice as sd,cv2,requests
    from core.local_audio import LocalRecognizer,PiperVoiceBackend
    from core.desktop import DesktopRuntime
    def microphone():
        audio=sd.rec(2*16000,samplerate=16000,channels=1,dtype='int16');sd.wait()
        return {'dispositivo':sd.query_devices(kind='input')['name'],'rms':float(np.sqrt(np.mean(audio.astype(float)**2))),'pico':int(np.max(np.abs(audio.astype(float))))}
    test('Captura real do microfone',microphone)
    def tts():
        voice=PiperVoiceBackend(ROOT/'models/piper/pt_BR-cadu-medium.onnx');voice.speak('Olá! Eu sou o Roberto. Estou pronto para conversar com você.')
        voice.synthesize_wav('Olá! Eu sou o Roberto. Estou pronto para conversar com você.',ROOT/'data'/'testes_audio'/'voz_roberto.wav')
        return voice.last_voice
    test('Sintese pt-BR e reproducao no dispositivo de saida',tts)
    runtime=DesktopRuntime(ROOT);runtime.config=dict(runtime.config,voz_ativa=False)
    recog=LocalRecognizer(ROOT/runtime.config['modelo_fala'])
    cases=[('Roberto, levante o braço.','ARM_UP'),('Roberto, acenda a luz.','LED_ON'),('Roberto, qual é o seu nome?','nome'),('Roberto!','chamada'),('Abaixe o braço.','ARM_DOWN'),('Que horas são?','ignorar'),('Roberta, acenda a luz.','ignorar')]
    for i,(phrase,expected) in enumerate(cases):
        def stt(phrase=phrase,expected=expected,i=i):
            path=ROOT/'data'/'testes_audio'/f'frase_{i}.wav'
            runtime.voice.synthesize_wav(phrase,path)
            started_at=time.monotonic()
            text=recog.transcribe(str(path));before=runtime.sequence;accepted=runtime.process(text,started_at=started_at)
            events=[e for e in runtime.events if e['seq']>before]
            if expected.startswith(('ARM','LED')):assert any(e['type']=='action' and e['data']['action']==expected for e in events),(text,events)
            elif expected=='nome':assert any(e['type']=='assistant' and 'Meu nome é Roberto' in e['data'] for e in events),(text,events)
            elif expected=='chamada':assert runtime.window_until>time.monotonic(),text
            elif expected=='ignorar':assert not accepted,(text,events)
            return {'fala_sintetizada':phrase,'transcricao':text,'aceito':accepted,'tipo_teste':'arquivo de audio sintetico, sem locutor humano'}
        test('ASR + fluxo: '+phrase,stt)
    def llm():
        answer=runtime.conversation.responder('Me explique o que é inteligência artificial.',runtime.ctx)
        assert len(answer)>30 and 'Não consegui' not in answer,answer
        return answer
    test('IA generativa local real',llm)
    def camera():
        cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)
        try:
            ok,frame=cap.read();assert ok,'Sem imagem';ok,jpg=cv2.imencode('.jpg',frame);assert ok
            runtime.camera.jpeg=jpg.tobytes()
            answer=runtime.describe_scene('Descreva brevemente o que está vendo na imagem.')
            assert len(answer)>10,answer
            return {'resolucao':list(frame.shape),'analise_local':answer}
        finally:cap.release()
    test('Webcam real + IA visual local',camera)
    runtime.close()
if __name__=='__main__':main()
