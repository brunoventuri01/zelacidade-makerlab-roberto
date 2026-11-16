import json,time,threading
from pathlib import Path
from unittest.mock import Mock
import pytest
from core.assistant import WakeWordGate
from core.robot import RobotController,physical_intent
from core.desktop import DesktopRuntime,WAIT

ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('text,expected',[
 ('Roberto, levante o braço.','levante o braco'),
 ('Roberto, acenda a luz.','acenda a luz'),
 ('Roberto, qual é o seu nome?','qual e o seu nome'),
 ('Roberto!',''),('Oi, Roberto!',''),('Acenda a luz',None),
 ('Roberto.',''),('Roberto. Acenda a luz.','acenda a luz'),
 ('Roberta, levante o braço',None),('RobertoJunior levante o braço',None),
 ('nexo, levante o braço',None),('Eu falei com Roberto ontem',None)])
def test_wake(text,expected):assert WakeWordGate().extrair_comando(text)==expected

@pytest.mark.parametrize('text,expected',[
 ('levante o braço','ARM_UP'),('abaixe o braço','ARM_DOWN'),('acenda a luz','LED_ON'),
 ('apague o LED','LED_OFF'),('me cumprimente','WAVE'),('não levante o braço',None),
 ('qual é a distância do obstáculo','SENSOR_READ'),('o caminho está livre','SENSOR_READ'),
 ('o braço está levantado',None)])
def test_intent(text,expected):assert physical_intent(text)==expected

@pytest.fixture
def runtime():
    r=DesktopRuntime(ROOT);r.config=dict(r.config,voz_ativa=False)
    yield r
    r.close()

def test_direct_commands_and_identity(runtime):
    assert runtime.process('Roberto, levante o braço.')
    assert runtime.robot.arm_up
    runtime.process('Roberto, acenda a luz.')
    assert runtime.robot.led_on
    runtime.process('Roberto, qual é o seu nome?')
    assert any(e['type']=='assistant' and 'Meu nome é Roberto' in e['data'] for e in runtime.events)
    assert all(e['data']['simulated'] for e in runtime.events if e['type']=='action')

def test_sensor_read_classifies_distance_in_simulation(runtime):
    assert runtime.process('Roberto, qual é a distância do obstáculo?')
    assert runtime.robot.last_distance==100.0
    assert any(e['type']=='sensor' and e['data']['classification']=='caminho livre' for e in runtime.events)

def test_two_steps_and_window_expiration(runtime):
    runtime.process('Roberto!');assert runtime.state=='OUVINDO COMANDO'
    assert 6<runtime.window_until-time.monotonic()<=7
    runtime.robot.arm_up=True;runtime.process('Abaixe o braço.');assert not runtime.robot.arm_up
    assert runtime.state==WAIT
    runtime.process('Roberto!');runtime.window_until=time.monotonic()-1
    assert not runtime.process('Acenda a luz.');assert not runtime.robot.led_on

def test_ignored_without_name_and_self_voice(runtime):
    runtime.speaking=True
    assert not runtime.process('Roberto, acenda a luz',source='microfone')
    runtime.speaking=False
    assert not runtime.process('acenda a luz')
    runtime.toggle_mic(False)
    assert not runtime.process('Roberto, acenda a luz',source='microfone')
    assert not runtime.robot.led_on

def test_window_accepts_speech_started_in_time(runtime):
    runtime.process('Roberto!');start=runtime.window_until-.1
    runtime.window_until=time.monotonic()-.1
    # A captured utterance retains its original start timestamp, even after ASR latency.
    assert runtime.process('Acenda a luz',started_at=runtime.window_until-.1)
    assert runtime.robot.led_on

def test_legacy_calculator_and_agenda_callback(runtime,tmp_path):
    agenda=next(s for s in runtime.skills if s.nome=='agenda');agenda.caminho=str(tmp_path/'agenda.txt')
    runtime.process('Roberto, calcular dois mais três')
    assert any(e['type']=='assistant' and '5' in e['data'] for e in runtime.events)
    runtime.process('Roberto, cadastrar evento na agenda')
    assert runtime.pending
    runtime.process('Apresentação do projeto na sexta')
    assert 'apresentação' in Path(agenda.caminho).read_text(encoding='utf-8').lower()

def test_real_command_requires_matching_ack():
    r=RobotController(False);serial=Mock(is_open=True)
    def ack():
        sent=json.loads(serial.write.call_args.args[0]);return json.dumps({'id':sent['id'],'ok':True}).encode()
    serial.readline.side_effect=ack;r.serial=serial
    assert 'Arduino confirmou' in r.perform('ARM_UP');assert r.arm_up

def test_hardware_failure_does_not_report_success():
    r=RobotController(False)
    with pytest.raises(RuntimeError):r.perform('LED_ON')
    assert not r.led_on

def test_tts_blocks_and_flushes_input(runtime):
    runtime.config.update(voz_ativa=True,cauda_voz_segundos=0)
    runtime.voice.speak=lambda *_:assert_blocked(runtime)
    epoch=runtime.audio.epoch;runtime.speak('Meu nome é Roberto.')
    assert runtime.audio.epoch>=epoch+2;assert not runtime.speaking
def assert_blocked(runtime):
    assert runtime.speaking and not runtime.can_listen()
    assert not runtime.process('Roberto, levante o braço',source='microfone')
    assert not runtime.robot.arm_up

def test_face_enrollment_reuses_preview(runtime,tmp_path,monkeypatch):
    import cv2,numpy as np,core.faces
    skill=next(s for s in runtime.skills if s.nome=='cadastro_facial')
    skill.pasta_faces=str(tmp_path/'faces');skill.caminho_modelo=str(tmp_path/'faces.yml');skill.caminho_rotulos=str(tmp_path/'labels.json')
    runtime.camera_frame=lambda:np.zeros((180,180,3),dtype=np.uint8)
    detector=Mock();detector.detectMultiScale.return_value=[(10,10,100,100)]
    monkeypatch.setattr(core.faces,'carregar_detector',lambda _:detector)
    monkeypatch.setattr(core.faces,'treinar_modelo',lambda *_:(30,{0:'teste'}))
    monkeypatch.setattr(cv2,'VideoCapture',lambda *_:pytest.fail('Nao deve abrir segunda camera'))
    import core.desktop as module
    from types import SimpleNamespace
    monkeypatch.setattr(module,'time',SimpleNamespace(monotonic=time.monotonic,time=time.time,sleep=lambda _:None))
    response=skill.cadastrar('teste',runtime.ctx)
    assert '30 fotos' in response
    assert len(list((tmp_path/'faces'/'teste').glob('*.png')))==30

def test_llm_cannot_change_volume_from_unrelated_transcript():
    from core.router import CommandRouter
    llm=Mock(disponivel=True);llm.escolher_ferramenta.return_value=('ajustar_volume',{'direcao':'aumentar'})
    skill=Mock();skill.matches.return_value=False;skill.ferramentas.return_value=[{'name':'ajustar_volume'}]
    router=CommandRouter([skill],llm=llm)
    assert 'repetir' in router.route('quando você grau está',Mock())
    skill.executar_ferramenta.assert_not_called()
