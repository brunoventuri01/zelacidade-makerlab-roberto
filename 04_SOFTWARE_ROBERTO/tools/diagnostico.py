"""
Diagnóstico do ambiente — rode ANTES da apresentação.

Verifica, em ordem, tudo que a Roberto precisa: bibliotecas, microfone,
alto-falante, webcam, modelo de rostos, chave da OpenAI e conexão de rede.
Cada item falha de forma isolada, então você vê TODOS os problemas de uma vez
em vez de descobrir um por um.

Uso:
    python tools/diagnostico.py            # checagem completa (não faz barulho)
    python tools/diagnostico.py --falar    # inclui um teste de voz audível
    python tools/diagnostico.py --gravar   # inclui um teste de 3s do microfone
"""

import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

OK, AVISO, ERRO = "  \033[92m✅\033[0m", "  \033[93m⚠️ \033[0m", "  \033[91m❌\033[0m"
resultados = {"ok": 0, "aviso": 0, "erro": 0}


def relatar(nivel: str, titulo: str, detalhe: str = "") -> None:
    """Imprime uma linha do relatório e contabiliza o resultado."""
    marcador = {"ok": OK, "aviso": AVISO, "erro": ERRO}[nivel]
    resultados[nivel] += 1
    print(f"{marcador} {titulo}" + (f"\n       {detalhe}" if detalhe else ""))


def secao(titulo: str) -> None:
    print(f"\n\033[1m── {titulo} " + "─" * (56 - len(titulo)) + "\033[0m")


# ---------------------------------------------------------------------------
def checar_python() -> None:
    secao("Python")
    versao = sys.version_info
    texto = f"{versao.major}.{versao.minor}.{versao.micro}"
    if versao < (3, 9):
        relatar("erro", f"Python {texto}", "Muito antigo. Use 3.11 ou superior.")
    elif versao >= (3, 13):
        relatar("ok", f"Python {texto}",
                "Versão nova: exige python3-dev + portaudio19-dev para compilar o PyAudio.")
    else:
        relatar("ok", f"Python {texto}")

    dentro_venv = sys.prefix != sys.base_prefix
    if dentro_venv:
        relatar("ok", "Ambiente virtual ativo", sys.prefix)
    else:
        relatar("aviso", "Você NÃO está num ambiente virtual",
                "Rode: source venv/bin/activate")


def checar_bibliotecas() -> None:
    secao("Bibliotecas Python")
    obrigatorias = [
        ("speech_recognition", "SpeechRecognition", "captura e transcrição"),
        ("pyaudio", "PyAudio", "acesso ao microfone"),
        ("pyttsx3", "pyttsx3", "voz da assistente"),
        ("cv2", "opencv-contrib-python", "reconhecimento facial"),
        ("numpy", "numpy", "usado pelo OpenCV"),
    ]
    opcionais = [
        ("openai", "openai", "IA generativa (item 9)"),
        ("dotenv", "python-dotenv", "leitura do .env"),
        ("requests", "requests", "cotação e previsão do tempo"),
        ("mss", "mss", "print da tela"),
    ]

    for modulo, pacote, para_que in obrigatorias:
        try:
            __import__(modulo)
            relatar("ok", f"{pacote}")
        except ImportError:
            relatar("erro", f"{pacote} ausente", f"{para_que} — pip install {pacote}")

    for modulo, pacote, para_que in opcionais:
        try:
            __import__(modulo)
            relatar("ok", f"{pacote}")
        except ImportError:
            relatar("aviso", f"{pacote} ausente", f"desativa: {para_que}")


def checar_opencv_face() -> None:
    """O cv2.face só existe no pacote contrib — é o erro mais comum do item 7."""
    secao("OpenCV — módulo face (item 7)")
    try:
        import cv2
    except ImportError:
        relatar("erro", "OpenCV não instalado")
        return

    relatar("ok", f"OpenCV {cv2.__version__}")
    if hasattr(cv2, "face"):
        relatar("ok", "cv2.face disponível", "LBPHFaceRecognizer pronto para uso")
    else:
        relatar("erro", "cv2.face NÃO existe",
                "pip uninstall opencv-python && pip install opencv-contrib-python")

    cascata = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    if os.path.exists(cascata):
        relatar("ok", "Haar cascade de rostos encontrado")
    else:
        relatar("erro", "Haar cascade ausente", cascata)


def checar_microfone(gravar: bool) -> None:
    secao("Microfone")
    try:
        import speech_recognition as sr
    except ImportError:
        relatar("erro", "SpeechRecognition não instalado")
        return

    try:
        nomes = sr.Microphone.list_microphone_names()
    except Exception as erro:
        relatar("erro", "PyAudio não conseguiu listar dispositivos", str(erro))
        return

    if not nomes:
        relatar("erro", "Nenhum dispositivo de áudio encontrado")
        return

    relatar("ok", f"{len(nomes)} dispositivo(s) de áudio detectado(s)")
    for i, nome in enumerate(nomes[:6]):
        print(f"       [{i}] {nome}")
    if len(nomes) > 6:
        print(f"       ... e mais {len(nomes) - 6}")

    try:
        with sr.Microphone() as fonte:
            reconhecedor = sr.Recognizer()
            reconhecedor.adjust_for_ambient_noise(fonte, duration=1)
            relatar("ok", "Microfone padrão abriu e calibrou",
                    f"limiar de energia: {reconhecedor.energy_threshold:.0f}")
    except Exception as erro:
        relatar("erro", "Não foi possível abrir o microfone padrão", str(erro))
        return

    if gravar:
        print("\n       🎤 Fale alguma coisa agora (3 segundos)...")
        try:
            with sr.Microphone() as fonte:
                audio = sr.Recognizer().listen(fonte, timeout=5, phrase_time_limit=3)
            texto = sr.Recognizer().recognize_google(audio, language="pt-BR")
            relatar("ok", "Transcrição funcionou", f'ouvi: "{texto}"')
        except Exception as erro:
            relatar("aviso", "Não consegui transcrever", f"{type(erro).__name__}: {erro}")


def checar_voz(falar: bool) -> None:
    secao("Voz (TTS)")
    try:
        import pyttsx3
    except ImportError:
        relatar("erro", "pyttsx3 não instalado")
        return

    try:
        engine = pyttsx3.init()
    except Exception as erro:
        relatar("erro", "Engine de voz não inicializou",
                f"{erro} — no Linux: sudo apt install espeak-ng")
        return

    vozes = engine.getProperty("voices")
    relatar("ok", f"Engine iniciada com {len(vozes)} voz(es)")

    marcadores = ("brazil", "portug", "pt_br", "pt-br", "ptbr")
    pt = [v for v in vozes if any(m in f"{v.id} {getattr(v,'name','')}".lower() for m in marcadores)]
    if pt:
        relatar("ok", f"{len(pt)} voz(es) em português", f"usando: {pt[0].id}")
    else:
        relatar("aviso", "Nenhuma voz pt-BR encontrada",
                "vai falar com a voz padrão (sotaque estranho, mas funciona)")

    if falar:
        try:
            if pt:
                engine.setProperty("voice", pt[0].id)
            engine.setProperty("rate", 180)
            engine.say("Teste de voz da Roberto. Se você está ouvindo isso, está tudo certo.")
            engine.runAndWait()
            relatar("ok", "Áudio reproduzido", "você ouviu a frase?")
        except Exception as erro:
            relatar("erro", "Falha ao falar", str(erro))


def checar_webcam() -> None:
    secao("Webcam (item 7)")
    try:
        import cv2
    except ImportError:
        relatar("erro", "OpenCV não instalado")
        return

    indice = int(os.getenv("INDICE_CAMERA", "0"))
    camera = cv2.VideoCapture(indice)
    if not camera.isOpened():
        camera.release()
        relatar("erro", f"Webcam {indice} não abriu",
                "verifique se está conectada e se nenhum app (Meet/Teams/Zoom) a ocupa")
        return

    ok, quadro = camera.read()
    camera.release()
    if ok and quadro is not None:
        altura, largura = quadro.shape[:2]
        relatar("ok", f"Webcam {indice} funcionando", f"resolução {largura}x{altura}")
    else:
        relatar("erro", f"Webcam {indice} abriu mas não devolveu imagem")


def checar_modelo_faces() -> None:
    secao("Modelo de rostos treinado")
    modelo = os.path.join(RAIZ, "models", "faces.yml")
    rotulos = os.path.join(RAIZ, "models", "labels.json")

    if not os.path.exists(modelo):
        relatar("aviso", "models/faces.yml ainda não existe",
                "rode: python tools/train_faces.py --capturar --nome <seu-nome>")
        return

    tamanho = os.path.getsize(modelo) / 1024
    relatar("ok", f"models/faces.yml encontrado ({tamanho:.0f} KB)")

    if os.path.exists(rotulos):
        import json
        with open(rotulos, encoding="utf-8") as arquivo:
            pessoas = json.load(arquivo)
        nomes = list(pessoas.values())
        relatar("ok", f"{len(nomes)} pessoa(s) cadastrada(s)", ", ".join(nomes))
        if "desconhecido" not in [n.lower() for n in nomes]:
            relatar("aviso", 'Falta a classe "desconhecido"',
                    "sem contraexemplos o LBPH reconhece qualquer rosto como você")
    else:
        relatar("aviso", "models/labels.json ausente", "retreine com --treinar")


def checar_configuracao() -> None:
    secao("Configuração (.env)")
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(RAIZ, ".env"))
    except ImportError:
        relatar("aviso", "python-dotenv ausente", "lendo só variáveis de ambiente")

    if not os.path.exists(os.path.join(RAIZ, ".env")):
        relatar("aviso", "Arquivo .env não existe", "rode: cp .env.example .env")

    chave = os.getenv("OPENAI_API_KEY", "")
    if not chave or chave.startswith("sk-cole"):
        relatar("aviso", "OPENAI_API_KEY não configurada",
                "itens 9 e o function calling ficam desligados (o resto funciona)")
    else:
        relatar("ok", "OPENAI_API_KEY presente", f"{chave[:7]}...{chave[-4:]}")

    relatar("ok", f"OPENAI_MODEL = {os.getenv('OPENAI_MODEL', '(não definido)')}")
    relatar("ok", f"WAKE_WORD = {os.getenv('WAKE_WORD', 'roberto')}")


def checar_rede() -> None:
    secao("Rede (comandos que dependem de internet)")
    try:
        import requests
    except ImportError:
        relatar("aviso", "requests ausente", "cotação e clima desativados")
        return

    servicos = [
        ("STT do Google", "https://www.google.com", None),
        ("Cotação (AwesomeAPI)", "https://economia.awesomeapi.com.br/json/last/USD-BRL", None),
        ("Clima (Open-Meteo)", "https://api.open-meteo.com/v1/forecast?latitude=-23.5&longitude=-46.6&current=temperature_2m", None),
    ]
    for nome, url, _ in servicos:
        try:
            resposta = requests.get(url, timeout=8)
            resposta.raise_for_status()
            relatar("ok", nome, f"HTTP {resposta.status_code}")
        except Exception as erro:
            relatar("aviso", f"{nome} inacessível", str(erro)[:80])


def checar_skills() -> None:
    """Carrega as skills de verdade e roteia frases de exemplo (sem executar)."""
    secao("Skills e roteamento")
    try:
        from core.assistant import WakeWordGate
        from skills.agenda import AgendaSkill
        from skills.calculator import CalculatorSkill
        from skills.datetime_skill import DateTimeSkill
    except Exception as erro:
        relatar("erro", "Falha ao importar as skills", str(erro))
        return

    gate = WakeWordGate(os.getenv("WAKE_WORD", "roberto"))
    if gate.extrair_comando("Roberto que horas são") == "que horas sao":
        relatar("ok", "Wake word reconhecida e removida")
    else:
        relatar("erro", "WakeWordGate não extraiu o comando")

    if gate.extrair_comando("que horas são") is None:
        relatar("ok", "Fala sem wake word é ignorada (item 1)")
    else:
        relatar("erro", "Comando sem wake word passou pelo portão!")

    # Ruído real captado nos nossos testes: o STT transcreve conversa da sala e,
    # se a wake word puder aparecer no meio, vira comando por acidente.
    ruidos = ["temperatura Roberto temperatura",
              "eu falei com a Roberto ontem sobre isso",
              "o nexo da questão é outro"]
    vazados = [r for r in ruidos if gate.extrair_comando(r) is not None]
    if vazados:
        relatar("erro", "Ruído acionou a assistente", f"passou: {vazados[0]!r}")
    else:
        relatar("ok", "Ruído com a wake word no meio da frase é rejeitado")

    calc = CalculatorSkill()
    if calc.avaliar(calc.traduzir("calcular 12 mais 8 vezes 3")) == 36:
        relatar("ok", "Calculadora com precedência correta (item 6)")
    else:
        relatar("erro", "Calculadora devolveu resultado errado")

    agenda_path = os.path.join(RAIZ, "data", "agenda.txt")
    if os.path.exists(agenda_path):
        with open(agenda_path, encoding="utf-8") as arquivo:
            linhas = [l for l in arquivo if l.strip()]
        relatar("ok", f"data/agenda.txt existe ({len(linhas)} evento(s))")
    else:
        relatar("aviso", "data/agenda.txt não existe", "será criado no primeiro uso")

    DateTimeSkill()
    AgendaSkill(caminho=agenda_path)
    relatar("ok", "Todas as skills instanciaram sem erro")


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico do ambiente da Roberto")
    parser.add_argument("--falar", action="store_true", help="Testa a voz (faz barulho)")
    parser.add_argument("--gravar", action="store_true", help="Testa o microfone (grava 3s)")
    args = parser.parse_args()

    print("\033[1m" + "=" * 60)
    print("  DIAGNÓSTICO DO AMBIENTE — Roberto")
    print("=" * 60 + "\033[0m")

    checar_python()
    checar_bibliotecas()
    checar_opencv_face()
    checar_microfone(args.gravar)
    checar_voz(args.falar)
    checar_webcam()
    checar_modelo_faces()
    checar_configuracao()
    checar_rede()
    checar_skills()

    print("\n" + "=" * 60)
    print(f"  ✅ {resultados['ok']} OK   "
          f"⚠️  {resultados['aviso']} avisos   "
          f"❌ {resultados['erro']} erros")
    print("=" * 60)

    if resultados["erro"]:
        print("\n  Corrija os ❌ antes da apresentação.")
        print("  Consulte a tabela de solução de problemas no README.md.")
        return 1
    if resultados["aviso"]:
        print("\n  Nenhum erro grave. Os ⚠️  são recursos opcionais desligados.")
        return 0
    print("\n  Ambiente 100% pronto. Boa apresentação! 🚀")
    return 0


if __name__ == "__main__":
    sys.exit(main())
