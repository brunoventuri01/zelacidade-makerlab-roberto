"""Orquestracao do painel reutilizando as habilidades originais do repositorio."""
import base64, concurrent.futures, contextlib, json, logging, re, threading, time
from pathlib import Path
from core.assistant import WakeWordGate
from core.local_audio import AudioLoop,WindowsVoice,PiperVoiceBackend
from core.robot import RobotController,RobotSkill
from core.llm import LLMClient
from core.router import CommandRouter
from core.text_utils import normalizar
from skills.base import Contexto
from skills.generative import GenerativeSkill,PERSONA

WAIT='AGUARDANDO "ROBERTO"'

class Camera:
    def __init__(self,runtime):
        self.r=runtime;self.lock=threading.RLock();self.paused=False;self.capture=None;self.jpeg=None;self.stop=threading.Event()
    def start(self):threading.Thread(target=self._run,daemon=True,name='Roberto-webcam').start()
    def _release(self):
        if self.capture:self.capture.release()
        self.capture=None;self.jpeg=None
    @contextlib.contextmanager
    def suspend(self):
        with self.lock:self.paused=True;self._release()
        try:yield
        finally:
            with self.lock:self.paused=False
    def _run(self):
        import cv2
        while not self.stop.wait(.1):
            with self.lock:
                if self.paused or not self.r.config['webcam_ativa']:
                    self._release();continue
                if self.capture is None:
                    self.capture=cv2.VideoCapture(int(self.r.config['indice_camera']),cv2.CAP_DSHOW)
                    self.capture.set(cv2.CAP_PROP_FRAME_WIDTH,640);self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
                if not self.capture.isOpened():
                    self.r.health['webcam']='Indisponível';self._release()
                else:
                    ok,frame=self.capture.read()
                    if ok:
                        ok,encoded=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,75])
                        if ok:self.jpeg=encoded.tobytes();self.r.health['webcam']='Ativa · imagem local'
                    else:self.r.health['webcam']='Sem imagem'
            if self.r.health.get('webcam')=='Indisponível':self.stop.wait(2)
        with self.lock:self._release()

class PanelSpeaker:
    nome_backend='Piper · Cadu masculino · pt-BR · offline'
    def __init__(self,runtime):self.runtime=runtime
    def falar(self,text):return self.runtime.speak(text)

class DesktopRuntime:
    def __init__(self,root,config=None):
        self.root=Path(root);self.config=config or json.loads((self.root/'config_roberto.json').read_text(encoding='utf-8'))
        self.lock=threading.RLock();self.processing_lock=threading.Lock();self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='Roberto-comando')
        self.busy=False;self.speaking=False;self.mic_enabled=self.config['microfone_ativo'];self.level=0;self.listening_activity=False
        self.state=WAIT;self.window_until=0;self.pending=None;self.events=[];self.sequence=0
        self.health={'microfone':'Iniciando','fala':'Iniciando','voz':'Piper · Cadu masculino · pt-BR','webcam':'Iniciando','ia':'Verificando'}
        self.audio=AudioLoop(self);self.camera=Camera(self)
        self.voice=PiperVoiceBackend(self.root/self.config['modelo_voz'],self.config.get('ritmo_voz',1.0)) if self.config.get('motor_voz','piper')=='piper' else WindowsVoice(self.config['velocidade_voz'])
        self.robot=RobotController(self.config['modo_simulacao'],self.emit)
        self.speaker=PanelSpeaker(self);self.gate=WakeWordGate(self.config['wake_word'])
        self.llm=LLMClient();self.llm.url=self.config['ollama_url'];self.llm.modelo=self.config['modelo_ia']
        self.conversation=GenerativeSkill(self.llm)
        from main import montar_skills,CAMINHOS
        self.ctx=Contexto(self,self.speaker,self.llm,CAMINHOS)
        self.skills=[RobotSkill(self.robot)]+montar_skills()
        self.router=CommandRouter(self.skills+[self.conversation],self.llm,self.conversation,usar_llm_router=True)
    def emit(self,kind,data):
        with self.lock:
            self.sequence+=1;event={'seq':self.sequence,'type':kind,'data':data,'time':time.time()}
            self.events.append(event);self.events=self.events[-150:]
        logging.info('%s %s',kind,data if kind not in ('user','assistant') else '[fala no painel]')
    def set_state(self,state):self.state=state;self.emit('state',state)
    def can_listen(self):return self.mic_enabled and not self.busy and not self.speaking
    def begin_processing(self):
        if not self.processing_lock.acquire(blocking=False):return False
        self.busy=True;self.set_state('PROCESSANDO');return True
    def finish_processing(self):
        self.audio.invalidate();self.busy=False
        self.state='OUVINDO COMANDO' if self.window_until>time.monotonic() else WAIT
        if self.processing_lock.locked():self.processing_lock.release()
        self.emit('state',self.state)
    def expire_window(self):
        if self.window_until and time.monotonic()>self.window_until and not self.busy:
            self.window_until=0;self.pending=None;self.set_state(WAIT)
    def fail(self,area,exc):
        logging.exception('%s: %s',area,exc);self.emit('error',f'{area}: {exc}')
    def speak(self,text):
        if not text:return
        self.emit('assistant',text)
        if not self.config['voz_ativa']:return
        self.speaking=True;self.audio.invalidate();self.set_state('ROBERTO FALANDO')
        try:self.voice.speak(text,self.config.get('dispositivo_saida'));self.health['voz']=self.voice.last_voice
        except Exception as exc:self.health['voz']='Falha: '+str(exc);self.fail('Voz',exc)
        finally:
            # Continue a descartar entrada enquanto reverberacao termina.
            time.sleep(self.config['cauda_voz_segundos']);self.audio.invalidate();self.speaking=False
            self.set_state('PROCESSANDO' if self.busy else WAIT)
    def process(self,text,source='texto',started_at=None,already_busy=False):
        if not already_busy:
            if not self.begin_processing():return False
        try:
            if not text:return False
            if source=='microfone' and (not self.mic_enabled or self.speaking):return False
            started_at=started_at or time.monotonic()
            extracted=self.gate.extrair_comando(text)
            waiting=bool(self.window_until and started_at<=self.window_until)
            if extracted is None and not waiting:
                self.emit('ignored','Fala sem chamada ignorada');return False
            command=extracted if extracted is not None else text
            self.emit('user',text)
            if not command:
                self.speak('Oi, estou ouvindo!')
                self.window_until=time.monotonic()+self.config['janela_comando_segundos']
                self.set_state('OUVINDO COMANDO');return True
            self.window_until=0
            callback=self.pending if waiting else None;self.pending=None
            if callback:
                response=callback(command,self.ctx)
            else:
                normalized=normalizar(command)
                if re.search(r'\b(qual (e )?(o )?seu nome|como (voce )?se chama|quem (e )?voce)\b',normalized):
                    response='Meu nome é Roberto! Sou o robô inteligente do projeto CP5.'
                elif re.search(r'\b(quem (te |o |voce )?criou|quem desenvolveu voce)\b',normalized):
                    response='Fui desenvolvido por estudantes de Engenharia de Software como parte de um projeto universitário.'
                elif re.search(r'\b(voce consegue enxergar|voce pode ver)\b',normalized):
                    response='Consigo analisar imagens usando a webcam do computador. Pode me pedir para descrever o que estou vendo.'
                elif re.search(r'\b(o que .*ve|o que .*vendo|descreva.*(imagem|camera|cena)|olhe|veja)\b',normalized):
                    response=self.describe_scene(command)
                else:
                    # No painel, as skills faciais usam o frame compartilhado, sem outra janela.
                    face=next((s for s in self.skills if s.nome in ('reconhecimento_facial','cadastro_facial') and s.matches(normalized)),None)
                    if face:
                        response=face.execute(command,self.ctx)
                    else:response=self.router.route(command,self.ctx)
            self.speak(response)
            self.pending=self.ctx.consumir_callback()
            if self.pending:
                self.window_until=time.monotonic()+self.config['janela_comando_segundos'];self.set_state('OUVINDO COMANDO')
            return True
        except Exception as exc:
            self.fail('Comando',exc);self.speak('Não consegui concluir esse pedido. Confira o aviso no painel.');return False
        finally:
            if not already_busy:self.finish_processing()
    def submit(self,text):
        if self.busy or self.speaking:return False
        self.pool.submit(self.process,text);return True
    def toggle_mic(self,enabled):
        self.mic_enabled=enabled;self.audio.invalidate();self.window_until=0;self.pending=None
        if self.audio.stream:
            try:
                if enabled and not self.audio.stream.active:self.audio.stream.start()
                if not enabled and self.audio.stream.active:self.audio.stream.stop()
                self.health['microfone']='Ativo' if enabled else 'Pausado'
            except Exception as exc:self.fail('Microfone',exc)
        self.emit('microphone',enabled)
        if not self.busy:self.set_state(WAIT)
    def describe_scene(self,question):
        import requests
        with self.camera.lock:jpeg=self.camera.jpeg
        if not self.config['webcam_ativa'] or not jpeg:return 'Não tenho uma imagem da webcam agora. Confira a câmera no painel.'
        response=requests.post(self.llm.url+'/api/chat',json={
            'model':self.llm.modelo,'stream':False,'keep_alive':'20m',
            'messages':[{'role':'system','content':PERSONA+' Descreva apenas o visível na imagem atual. Não identifique pessoas pelo nome.'},
                {'role':'user','content':question,'images':[base64.b64encode(jpeg).decode()]}],
            'options':{'num_ctx':4096,'num_predict':170,'temperature':.2}},timeout=(5,120))
        response.raise_for_status();return response.json()['message']['content']
    def camera_frame(self):
        import cv2,numpy as np
        with self.camera.lock:jpeg=self.camera.jpeg
        return cv2.imdecode(np.frombuffer(jpeg,dtype=np.uint8),cv2.IMREAD_COLOR) if jpeg else None
    def enroll_face(self,name,skill):
        import cv2
        from core.faces import carregar_detector,treinar_modelo
        if not self.config['webcam_ativa'] or self.camera_frame() is None:
            return 'A webcam não está disponível. Ative a câmera no painel antes de cadastrar o rosto.'
        detector=carregar_detector(cv2)
        self.speak(f'Certo, {name.replace("_"," ")}. Olhe para a câmera e mova a cabeça devagar. Vou capturar seu rosto pelo painel.')
        self.set_state('PROCESSANDO')
        folder=Path(skill.pasta_faces)/name;folder.mkdir(parents=True,exist_ok=True)
        count=len(list(folder.glob('*.png')));saved=0;deadline=time.monotonic()+20
        try:
            while saved<skill.fotos and time.monotonic()<deadline:
                if not self.config['webcam_ativa']:break
                frame=self.camera_frame()
                if frame is None:time.sleep(.12);continue
                gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                faces=detector.detectMultiScale(cv2.equalizeHist(gray),scaleFactor=1.12,minNeighbors=5,minSize=(60,60))
                if len(faces):
                    x,y,w,h=max(faces,key=lambda f:f[2]*f[3]);crop=cv2.resize(gray[y:y+h,x:x+w],(200,200))
                    path=folder/f'{name}_{count+saved:04d}.png'
                    if not cv2.imwrite(str(path),crop):raise RuntimeError('Não consegui salvar a amostra facial')
                    saved+=1
                    self.health['cadastro']=f'{saved}/{skill.fotos} fotos';self.emit('face_progress',{'saved':saved,'total':skill.fotos})
                time.sleep(.12)
            if saved<8:
                return f'Capturei {saved} fotos e não concluí o cadastro. Melhore a iluminação e fique de frente para a câmera; podemos tentar novamente.'
            self.set_state('PROCESSANDO')
            total,labels=treinar_modelo(skill.pasta_faces,skill.caminho_modelo,skill.caminho_rotulos)
            return f'Pronto, {name.replace("_"," ")}. Cadastrei seu rosto com {saved} fotos. Você pode perguntar: Roberto, quem sou eu?'
        finally:self.health.pop('cadastro',None)
    def recognize_face(self,skill):
        import cv2
        loaded=skill._carregar()
        if isinstance(loaded,str):return loaded
        _,detector,recognizer,labels=loaded
        best=None;deadline=time.monotonic()+4;seen=False
        while time.monotonic()<deadline:
            frame=self.camera_frame()
            if frame is None:return 'Não tenho uma imagem da webcam agora.'
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            faces=detector.detectMultiScale(cv2.equalizeHist(gray),1.12,5,minSize=(60,60))
            for x,y,w,h in faces:
                seen=True;identity,distance=recognizer.predict(cv2.resize(gray[y:y+h,x:x+w],(200,200)))
                if distance<skill.limiar and (best is None or distance<best[0]):best=(distance,labels.get(identity,'desconhecido'))
            time.sleep(.12)
        if best:return f'Você parece ser {best[1].replace("_"," ")}. O reconhecimento facial é uma estimativa.'
        return 'Detectei um rosto, mas não reconheci a pessoa.' if seen else 'Não detectei um rosto. Tente melhorar a iluminação e olhar para a câmera.'
    def check_llm(self):
        import requests
        try:
            result=requests.get(self.llm.url+'/api/tags',timeout=5);result.raise_for_status()
            models=[v['name'] for v in result.json().get('models',[])]
            if self.llm.modelo in models:
                self.health['ia']='Carregando IA local…';self.emit('health',dict(self.health))
                loaded=requests.post(self.llm.url+'/api/generate',json={'model':self.llm.modelo,'stream':False,'keep_alive':'20m','options':{'num_ctx':4096}},timeout=(5,150))
                loaded.raise_for_status();self.health['ia']=self.llm.modelo+' · local'
            else:self.health['ia']='Modelo não instalado'
        except Exception as exc:self.health['ia']='Indisponível: '+str(exc)
        self.emit('health',self.health)
    def snapshot(self,after=0):
        self.expire_window()
        with self.lock:return {'title':self.config['titulo'],'state':self.state,'mic':self.mic_enabled,'speaking':self.speaking,
            'busy':self.busy,'level':self.level,'simulated':self.robot.simulation,'arm_up':self.robot.arm_up,'led_on':self.robot.led_on,'distance_cm':self.robot.last_distance,
            'health':dict(self.health),'events':[e for e in self.events if e['seq']>after],
            'window_remaining':max(0,self.window_until-time.monotonic()),'config':{k:self.config[k] for k in ('janela_comando_segundos','voz_ativa','webcam_ativa','indice_camera')}}
    def start(self):self.camera.start();self.audio.start();threading.Thread(target=self.check_llm,daemon=True).start()
    def close(self):self.audio.close();self.camera.stop.set();self.robot.close();self.pool.shutdown(wait=False,cancel_futures=True)
