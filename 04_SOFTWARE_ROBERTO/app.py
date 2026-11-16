"""Painel local do Roberto. Somente loopback, sem servicos externos de audio/video."""
import contextlib,json,logging,os,threading,time
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import HTMLResponse,Response
from pydantic import BaseModel,Field
ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
from core.desktop import DesktopRuntime

runtime=None
@contextlib.asynccontextmanager
async def lifespan(app):
    global runtime
    (ROOT/'data'/'logs').mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=ROOT/'data'/'logs'/'roberto.log',level=logging.INFO,encoding='utf-8',format='%(asctime)s %(levelname)s %(message)s')
    runtime=DesktopRuntime(ROOT);runtime.start()
    yield
    runtime.close()
app=FastAPI(title='ROBERTO | ROBÔ INTELIGENTE CP5',lifespan=lifespan)

@app.middleware('http')
async def local_only(request,call_next):
    # Impede comandos disparados por paginas externas no navegador.
    origin=request.headers.get('origin','')
    from urllib.parse import urlparse
    if origin and urlparse(origin).netloc!=request.headers.get('host',''):
        return Response('Origem externa recusada',status_code=403)
    return await call_next(request)

class Utterance(BaseModel):text:str=Field(min_length=1,max_length=1200)
class Toggle(BaseModel):enabled:bool
class Options(BaseModel):
    janela_comando_segundos:float=Field(ge=2,le=30)
    voz_ativa:bool
    dispositivo_saida:Optional[int]=None
class SerialOptions(BaseModel):port:str=Field(min_length=1,max_length=40)

@app.get('/',response_class=HTMLResponse)
def index():return (ROOT/'web'/'index.html').read_text(encoding='utf-8')
@app.get('/api/state')
def state(after:int=0):return runtime.snapshot(after)
@app.post('/api/utterance')
def utterance(body:Utterance):
    if not runtime.submit(body.text):raise HTTPException(409,'Roberto está ocupado; aguarde a resposta.')
    return {'accepted':True}
@app.post('/api/microphone')
def microphone(body:Toggle):runtime.toggle_mic(body.enabled);return {'enabled':runtime.mic_enabled}
@app.post('/api/options')
def options(body:Options):
    runtime.config.update(body.model_dump())
    # Permite mover o notebook: salvar opcoes, mas nunca persistir hardware como padrao.
    (ROOT/'config_roberto.json').write_text(json.dumps(runtime.config,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'ok':True}
@app.get('/api/audio-outputs')
def audio_outputs():
    import sounddevice as sd
    return [{'id':index,'name':device['name']} for index,device in enumerate(sd.query_devices()) if int(device.get('max_output_channels',0))>0]
@app.get('/api/camera.jpg')
def camera():
    with runtime.camera.lock:jpeg=runtime.camera.jpeg
    if not jpeg:raise HTTPException(503,'Webcam sem imagem')
    return Response(jpeg,media_type='image/jpeg',headers={'Cache-Control':'no-store'})
@app.get('/api/ports')
def ports():
    from serial.tools import list_ports
    return [{'port':p.device,'name':p.description} for p in list_ports.comports()]
@app.post('/api/serial')
def serial_connect(body:SerialOptions):
    if runtime.busy:raise HTTPException(409,'Aguarde o comando terminar')
    try:runtime.robot.connect(body.port,runtime.config['baud_serial'])
    except Exception as exc:raise HTTPException(400,str(exc))
    return {'simulated':False}
@app.post('/api/simulation')
def simulation():
    if runtime.busy:raise HTTPException(409,'Aguarde o comando terminar')
    runtime.robot.close();runtime.robot.simulation=True;return {'simulated':True}
@app.post('/api/shutdown')
def shutdown():
    runtime.toggle_mic(False);runtime.camera.stop.set()
    threading.Timer(.5,lambda:os._exit(0)).start();return {'ok':True}

if __name__=='__main__':
    import uvicorn
    config=json.loads((ROOT/'config_roberto.json').read_text(encoding='utf-8'))
    uvicorn.run(app,host='127.0.0.1',port=config['porta_painel'],log_level='warning')
