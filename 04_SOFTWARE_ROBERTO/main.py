"""
Roberto — Assistente virtual por comandos de voz
Checkpoint 4 — 2º semestre

Ponto de entrada da aplicação: lê a configuração, monta os objetos
(Listener, Speaker, LLM, Skills, Router, Roberto) e liga o loop principal.

Uso:
    python main.py                  # microfone + voz (modo normal)
    python main.py --texto          # PLANO B: digita os comandos no teclado
    python main.py --sem-voz        # sem TTS (só texto na tela)
    python main.py --stt whisper    # troca o backend de STT para o Whisper
    python main.py --wake "sexta"   # troca a palavra de ativação
    python main.py --debug-audio    # mostra os avisos do ALSA/JACK
    python main.py --tts pyttsx3    # voz offline (sem latência de rede)
    python main.py --voz coral      # troca a voz da OpenAI
"""

import argparse
import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv ausente: seguimos com as variáveis do sistema
    def load_dotenv(*_args, **_kwargs):
        print("[Setup] python-dotenv não instalado — lendo só as variáveis de ambiente.")

from core.assistant import Roberto
from core.listener import MicrofoneListener, TecladoListener
from core.llm import LLMClient
from core.router import CommandRouter
from core.speaker import OpenAITTS, Pyttsx3TTS, PiperTTS, Speaker
from skills.agenda import AgendaSkill
from skills.calculator import CalculatorSkill
from skills.datetime_skill import DateTimeSkill
from skills.extras.clima import ClimaSkill
from skills.extras.cotacao import CotacaoSkill
from skills.extras.jogo_velha import JogoVelhaSkill
from skills.extras.sistema import ScreenshotSkill, VolumeSkill
from skills.extras.web import WebSkill, YoutubeSkill
from skills.generative import GenerativeSkill
from skills.vision import CadastroFaceSkill, FaceSkill

# Caminhos relativos à raiz do projeto (funciona de qualquer diretório).
RAIZ = os.path.dirname(os.path.abspath(__file__))
CAMINHOS = {
    "agenda": os.path.join(RAIZ, "data", "agenda.txt"),
    "modelo_faces": os.path.join(RAIZ, "models", "faces.yml"),
    "rotulos_faces": os.path.join(RAIZ, "models", "labels.json"),
    "screenshots": os.path.join(RAIZ, "data", "screenshots"),
    "cache_voz": os.path.join(RAIZ, "data", "cache_voz"),
    "faces": os.path.join(RAIZ, "data", "faces"),
}


def ler_argumentos():
    """Define as flags de linha de comando."""
    parser = argparse.ArgumentParser(description="Assistente virtual Roberto")
    parser.add_argument("--texto", action="store_true",
                        help="Plano B: lê comandos do teclado em vez do microfone")
    parser.add_argument("--sem-voz", action="store_true",
                        help="Desliga o TTS (só imprime as respostas)")
    parser.add_argument("--stt", choices=["local", "google", "whisper"], default=None,
                        help="Backend de reconhecimento de fala")
    parser.add_argument("--wake", default=None, help="Palavra de ativação")
    parser.add_argument("--sem-llm-router", action="store_true",
                        help="Desliga o fallback por function calling (só regex)")
    parser.add_argument("--debug-audio", action="store_true",
                        help="Mostra os avisos do ALSA/JACK (escondidos por padrão)")
    parser.add_argument("--tts", choices=["piper", "openai", "pyttsx3"], default=None,
                        help="Motor de voz: openai (neural) ou pyttsx3 (offline)")
    parser.add_argument("--voz", default=None,
                        help="Voz da OpenAI: nova, coral, shimmer, sage, alloy...")
    return parser.parse_args()


def montar_skills() -> list:
    """
    Registra TODAS as habilidades da assistente.

    A ordem importa: a primeira skill cuja regex casar é a que executa.
    Skills mais específicas devem vir antes das mais genéricas (por isso a
    agenda, cujo padrão final é só a palavra "agenda", fica no fim do bloco
    obrigatório, e a conversa livre fica fora da lista, como fallback).
    """
    return [
        # --- Itens obrigatórios (2 a 8) ---
        DateTimeSkill(),                                         # itens 4 e 5
        CalculatorSkill(),                                       # item 6
        FaceSkill(modelo=CAMINHOS["modelo_faces"],               # item 7
                  rotulos=CAMINHOS["rotulos_faces"],
                  limiar=float(os.getenv("LIMIAR_FACE", "70")),
                  indice_camera=int(os.getenv("INDICE_CAMERA", "0"))),
        CadastroFaceSkill(                                       # cadastro por voz
            pasta_faces=CAMINHOS["faces"],
            modelo=CAMINHOS["modelo_faces"],
            rotulos=CAMINHOS["rotulos_faces"],
            fotos=int(os.getenv("FOTOS_CADASTRO", "30")),
            indice_camera=int(os.getenv("INDICE_CAMERA", "0"))),
        AgendaSkill(caminho=CAMINHOS["agenda"]),                 # itens 2, 3 e 8

        # --- Item 10: comandos extras ---
        CotacaoSkill(),                                          # dólar / bitcoin
        ClimaSkill(cidade_padrao=os.getenv("CIDADE_PADRAO", "São Paulo")),
        JogoVelhaSkill(),                                        # diálogo multi-turno
        ScreenshotSkill(pasta=CAMINHOS["screenshots"]),
        VolumeSkill(),
        YoutubeSkill(),
        WebSkill(),
    ]


def montar_speaker(args, llm) -> Speaker:
    """
    Monta a voz da assistente com um backend principal e um reserva.

    Padrão: voz neural da OpenAI (natural) com o pyttsx3 offline de reserva.
    Se a rede cair no meio da apresentação, o Speaker troca sozinho e a
    assistente continua falando — feia, mas falando.
    """
    if args.sem_voz:
        return Speaker(ativo=False)

    escolhido = args.tts or os.getenv("TTS_BACKEND", "piper")
    if escolhido == 'piper':
        return Speaker(backend=PiperTTS())
    offline = Pyttsx3TTS(velocidade=int(os.getenv("TTS_VELOCIDADE", "180")))

    if escolhido == "openai" and llm.disponivel:
        neural = OpenAITTS(
            cliente=llm.cliente,
            modelo=os.getenv("TTS_MODELO", "gpt-4o-mini-tts"),
            voz=args.voz or os.getenv("TTS_VOZ", "nova"),
            instrucoes=os.getenv("TTS_INSTRUCOES") or None,
            pasta_cache=CAMINHOS["cache_voz"],
            silenciar_avisos=not args.debug_audio,
        )
        return Speaker(backend=neural, reserva=offline)

    if escolhido == "openai":
        print("[Setup] TTS da OpenAI pedido, mas sem OPENAI_API_KEY. Usando voz offline.")
    return Speaker(backend=offline)


def montar_listener(args, llm):
    """Escolhe entre microfone e teclado, com fallback automático."""
    if args.texto:
        print("[Setup] Modo texto ativado (Plano B da apresentação).")
        return TecladoListener()

    backend = args.stt or os.getenv("STT_BACKEND", "google")
    try:
        return MicrofoneListener(
            backend=backend,
            cliente_openai=llm.cliente if llm.disponivel else None,
            idioma=os.getenv("IDIOMA_STT", "pt-BR"),
            silenciar_avisos=not args.debug_audio,
        )
    except Exception as erro:
        # Sem PyAudio, sem microfone ou sem permissão: a demo não pode morrer aqui.
        print(f"[Setup] Não foi possível usar o microfone ({erro}).")
        print("[Setup] Caindo para o modo texto. Digite os comandos.")
        return TecladoListener()


def main() -> int:
    args = ler_argumentos()
    load_dotenv()  # carrega OPENAI_API_KEY, OPENAI_MODEL, WAKE_WORD do .env

    print("=" * 60)
    print("  Roberto — Assistente Virtual  |  Checkpoint 4")
    print("=" * 60)

    # 1) IA generativa (item 9). Sem chave, o programa roda mesmo assim.
    llm = LLMClient()
    if llm.disponivel:
        print(f"[Setup] IA generativa: modelo {llm.modelo}")

    # 2) Entrada e saída
    speaker = montar_speaker(args, llm)
    print(f"[Setup] Voz: {speaker.nome_backend}")
    listener = montar_listener(args, llm)

    # 3) Habilidades + roteador
    skills = montar_skills()
    conversa = GenerativeSkill(llm=llm)      # fallback final (item 9)
    router = CommandRouter(
        skills=skills + [conversa],
        llm=llm,
        skill_conversa=conversa,
        usar_llm_router=not args.sem_llm_router,
    )
    print(f"[Setup] {len(skills)} habilidades carregadas: "
          f"{', '.join(s.nome for s in skills)}")

    # 4) A assistente
    wake_word = args.wake or os.getenv("WAKE_WORD", "roberto")
    # Variantes extras de transcrição, descobertas com tools/testar_wake.py
    extras = [v.strip() for v in os.getenv("WAKE_WORD_VARIANTES", "").split(",") if v.strip()]
    roberto = Roberto(
        listener=listener,
        speaker=speaker,
        router=router,
        llm=llm,
        wake_word=wake_word,
        caminhos=CAMINHOS,
        variantes=extras,
    )
    print(f"[Setup] Palavra de ativação: '{wake_word}'"
          + (f" (+ variantes: {', '.join(extras)})" if extras else ""))
    print("-" * 60)

    roberto.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
