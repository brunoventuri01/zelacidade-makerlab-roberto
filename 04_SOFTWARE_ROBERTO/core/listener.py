"""
Camada de entrada: microfone + STT (Speech To Text).

Duas ideias importantes aqui:

1) Backend de STT plugável — `GoogleSTT` (grátis, sem chave) e `WhisperSTT`
   (API da OpenAI, mais preciso) implementam a mesma interface `STTBackend`.
   Trocar de um para o outro é uma flag de linha de comando.

2) Listener plugável — `MicrofoneListener` usa o microfone de verdade e
   `TecladoListener` lê do input(). O Plano B da apresentação: se o microfone
   da sala falhar, `python main.py --texto` demonstra 100% da lógica.
"""

import contextlib
import os
import sys
from abc import ABC, abstractmethod


@contextlib.contextmanager
def silenciar_stderr_nativo(ativo: bool = True):
    """
    Silencia mensagens que o ALSA e o JACK cospem direto no descritor 2.

    No Linux, abrir o microfone imprime dezenas de linhas do tipo
    "ALSA lib pcm.c ... Unknown PCM cards.pcm.rear" e
    "jack server is not running". São AVISOS, não erros: o áudio funciona.
    Mas elas vêm da camada C das bibliotecas, então nem sys.stderr do Python
    nem try/except conseguem interceptar — a única saída é redirecionar o
    descritor de arquivo do sistema operacional.

    Numa demo ao vivo isso é essencial: sem o silenciamento, cada frase gera
    uma tela de log e ninguém enxerga a resposta da assistente.

    Use ativo=False (flag --debug-audio) quando estiver investigando um
    problema de áudio de verdade e precisar ver essas mensagens.
    """
    if not ativo:
        yield
        return

    devnull = os.open(os.devnull, os.O_WRONLY)
    copia_stderr = os.dup(2)
    try:
        sys.stderr.flush()
        os.dup2(devnull, 2)     # tudo que for para o fd 2 cai no /dev/null
        yield
    finally:
        # O finally garante que o stderr volta mesmo se a skill lançar exceção.
        os.dup2(copia_stderr, 2)
        os.close(copia_stderr)
        os.close(devnull)


# ---------------------------------------------------------------------------
# Backends de STT
# ---------------------------------------------------------------------------
class STTBackend(ABC):
    """Interface comum de transcrição. Recebe um AudioData e devolve texto."""

    nome = "base"

    @abstractmethod
    def transcrever(self, audio) -> str:
        ...


class GoogleSTT(STTBackend):
    """Web Speech API do Google via SpeechRecognition. Grátis e sem chave."""

    nome = "google"

    def __init__(self, recognizer, idioma: str = "pt-BR"):
        self.recognizer = recognizer
        self.idioma = idioma

    def transcrever(self, audio) -> str:
        return self.recognizer.recognize_google(audio, language=self.idioma)


class WhisperSTT(STTBackend):
    """
    Whisper via API da OpenAI. Mais preciso com ruído e sotaque, mas depende
    de rede e da OPENAI_API_KEY. Enviamos o áudio como WAV em memória.
    """

    nome = "whisper"

    def __init__(self, cliente_openai, modelo: str = "whisper-1", idioma: str = "pt"):
        self.cliente = cliente_openai
        self.modelo = modelo
        self.idioma = idioma

    def transcrever(self, audio) -> str:
        import io

        buffer = io.BytesIO(audio.get_wav_data())
        buffer.name = "audio.wav"  # a API usa a extensão para detectar o formato
        resposta = self.cliente.audio.transcriptions.create(
            model=self.modelo, file=buffer, language=self.idioma
        )
        return resposta.text


# ---------------------------------------------------------------------------
# Listeners
# ---------------------------------------------------------------------------
class BaseListener(ABC):
    """Interface de entrada do Roberto: ouvir() devolve texto ou None."""

    @abstractmethod
    def ouvir(self, prompt: str = "") -> str:
        ...

    def encerrar(self) -> None:
        """Gancho para liberar recursos (microfone). Opcional."""


class TecladoListener(BaseListener):
    """Modo --texto: substitui o microfone por input(). Plano B da demo."""

    def __init__(self):
        self.backend_nome = "teclado"

    def ouvir(self, prompt: str = "") -> str:
        try:
            texto = input(f"⌨️  {prompt or 'Digite'} > ").strip()
        except (EOFError, KeyboardInterrupt):
            return "sair"
        return texto


class MicrofoneListener(BaseListener):
    """
    Captura áudio do microfone com SpeechRecognition.
    O listen() da biblioteca já faz VAD (detecta início/fim da fala) e
    adjust_for_ambient_noise() calibra o ruído da sala.
    """

    def __init__(self, backend: str = "google", cliente_openai=None,
                 idioma: str = "pt-BR", timeout: int = 6, limite_fala: int = 12,
                 silenciar_avisos: bool = True):
        import speech_recognition as sr

        self._sr = sr
        self.silenciar = silenciar_avisos
        self.recognizer = sr.Recognizer()
        # Pausa curta = responde rápido; pausa longa = deixa a pessoa respirar.
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
        with silenciar_stderr_nativo(self.silenciar):
            self.microfone = sr.Microphone()   # aqui o ALSA enumera os devices
        self.timeout = timeout
        self.limite_fala = limite_fala
        self.backend_nome = backend
        self.stt = self._montar_backend(backend, cliente_openai, idioma)
        self._calibrar()

    def _montar_backend(self, backend: str, cliente_openai, idioma: str) -> STTBackend:
        """Escolhe o backend de STT; cai para o Google se o Whisper não puder rodar."""
        if backend == "local":
            from pathlib import Path
            from core.local_audio import LocalRecognizer
            recognizer = LocalRecognizer(Path(__file__).resolve().parents[1] / 'models' / 'whisper-small')
            class LocalSTT(STTBackend):
                nome = 'Whisper local'
                def transcrever(self, audio):
                    return recognizer.transcribe(audio.get_raw_data(convert_rate=16000, convert_width=2))
            return LocalSTT()
        if backend == "whisper":
            if cliente_openai is None:
                print("[Listener] Whisper pedido, mas sem OPENAI_API_KEY. Usando Google.")
            else:
                return WhisperSTT(cliente_openai)
        return GoogleSTT(self.recognizer, idioma)

    def _calibrar(self) -> None:
        """Mede o ruído ambiente uma vez, no boot, para o VAD acertar o corte."""
        print("[Listener] Calibrando ruído ambiente (1s). Silêncio, por favor...")
        try:
            with silenciar_stderr_nativo(self.silenciar), self.microfone as fonte:
                self.recognizer.adjust_for_ambient_noise(fonte, duration=1)
            print(f"[Listener] Pronto. Limiar de energia: {self.recognizer.energy_threshold:.0f}")
        except Exception as erro:
            print(f"[Listener] Não foi possível calibrar: {erro}")

    def ouvir(self, prompt: str = "") -> str:
        """
        Grava uma fala e devolve a transcrição.
        Devolve "" quando não houve fala ou o STT não entendeu — o loop
        principal simplesmente tenta de novo.
        """
        print(f"🎤 {prompt or 'Ouvindo...'}")
        try:
            with silenciar_stderr_nativo(self.silenciar), self.microfone as fonte:
                audio = self.recognizer.listen(
                    fonte, timeout=self.timeout, phrase_time_limit=self.limite_fala
                )
        except self._sr.WaitTimeoutError:
            return ""  # ninguém falou nada dentro do timeout
        except Exception as erro:
            print(f"[Listener] Erro no microfone: {erro}")
            return ""

        try:
            return self.stt.transcrever(audio)
        except self._sr.UnknownValueError:
            return ""  # áudio captado, mas ininteligível
        except self._sr.RequestError as erro:
            print(f"[Listener] STT indisponível (rede?): {erro}")
            return ""
        except Exception as erro:
            print(f"[Listener] Falha na transcrição: {erro}")
            return ""
