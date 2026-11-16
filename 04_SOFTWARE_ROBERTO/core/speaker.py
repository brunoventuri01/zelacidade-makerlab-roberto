"""
Camada de saída de voz (TTS - Text To Speech), com backends plugáveis.

Mesma ideia do Listener: o resto do programa só conhece `Speaker.falar()` e
não sabe qual motor está por trás. Dois backends implementam `TTSBackend`:

  OpenAITTS  -> voz neural (gpt-4o-mini-tts). Soa natural em pt-BR, mas
                depende de rede. Usa cache em disco: frases repetidas
                ("Ok, qual evento devo cadastrar?") tocam instantaneamente.
  Pyttsx3TTS -> offline (SAPI5 no Windows, espeak no Linux). Voz robótica,
                mas zero latência e funciona sem internet.

O `Speaker` tenta o backend principal e cai no reserva sozinho se a rede
falhar no meio da apresentação. Se os dois falharem, sobra o texto na tela e
a demo continua.
"""

import hashlib
import os
from abc import ABC, abstractmethod

from core.audio_utils import silenciar_stderr_nativo


class TTSBackend(ABC):
    """Interface comum de síntese de voz."""

    nome = "base"

    @abstractmethod
    def falar(self, texto: str) -> bool:
        """Fala o texto. Devolve True se conseguiu, False para acionar o reserva."""

class PiperTTS(TTSBackend):
    nome = 'Piper Cadu masculino pt-BR'
    def __init__(self):
        from pathlib import Path
        from core.local_audio import PiperVoiceBackend
        self.backend=PiperVoiceBackend(Path(__file__).resolve().parents[1]/'models/piper/pt_BR-cadu-medium.onnx')
    def falar(self,texto):
        try:self.backend.speak(texto);return True
        except Exception as exc:print(f'[Voz] Piper indisponivel: {exc}');return False


# ---------------------------------------------------------------------------
class Pyttsx3TTS(TTSBackend):
    """Voz offline do sistema operacional. Feia, porém instantânea e confiável."""

    nome = "pyttsx3"

    def __init__(self, velocidade: int = 180, volume: float = 1.0):
        self.engine = self._iniciar(velocidade, volume)

    @property
    def disponivel(self) -> bool:
        return self.engine is not None

    def _iniciar(self, velocidade: int, volume: float):
        try:
            import pyttsx3
        except ImportError:
            print("[Speaker] pyttsx3 não instalado.")
            return None
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", velocidade)
            engine.setProperty("volume", volume)
            self._selecionar_voz_pt(engine)
            return engine
        except Exception as erro:  # engine ausente no SO (ex.: espeak não instalado)
            print(f"[Speaker] Falha ao iniciar o pyttsx3: {erro}")
            return None

    @staticmethod
    def _selecionar_voz_pt(engine) -> None:
        """Procura uma voz pt-BR; o id muda muito entre sistemas."""
        marcadores = ("brazil", "portug", "pt_br", "pt-br", "ptbr")
        try:
            for voz in engine.getProperty("voices"):
                assinatura = f"{voz.id} {getattr(voz, 'name', '')}".lower()
                if any(m in assinatura for m in marcadores):
                    engine.setProperty("voice", voz.id)
                    return
        except Exception:
            pass  # sem voz pt-BR: usa a padrão do sistema

    def falar(self, texto: str) -> bool:
        if not self.disponivel:
            return False
        try:
            self.engine.say(texto)
            self.engine.runAndWait()
            return True
        except Exception as erro:
            print(f"[Speaker] Erro no pyttsx3: {erro}")
            return False


# ---------------------------------------------------------------------------
class OpenAITTS(TTSBackend):
    """
    Voz neural da OpenAI. Bem mais natural que o espeak.

    Dois detalhes de implementação que valem a pena:

    1) Pedimos o áudio em PCM cru (24 kHz, 16 bits, mono) e tocamos direto
       pelo PyAudio, que já é dependência do projeto por causa do microfone.
       Assim não entra nenhuma biblioteca nova de reprodução.

    2) Streaming + cache. O áudio começa a tocar antes do download terminar, e
       cada frase sintetizada fica salva em disco. Como a assistente repete
       muitas frases fixas, na segunda vez a resposta é instantânea — e isso
       também economiza chamadas à API durante os ensaios.
    """

    nome = "openai"
    TAXA = 24000        # Hz — formato fixo do PCM devolvido pela API
    CANAIS = 1
    LARGURA = 2         # bytes por amostra (16 bits)

    def __init__(self, cliente, modelo: str = "gpt-4o-mini-tts", voz: str = "nova",
                 instrucoes: str = None, pasta_cache: str = None,
                 silenciar_avisos: bool = True):
        self.cliente = cliente
        self.modelo = modelo
        self.voz = voz
        # Instruções de tom são OPCIONAIS e desligadas por padrão: medimos que
        # elas custam ~1,1s a mais até o áudio começar (2,8s contra 1,65s).
        # O modelo já detecta o português pelo próprio texto. Se quiser dirigir
        # o tom, preencha TTS_INSTRUCOES no .env e aceite a latência extra.
        self.instrucoes = instrucoes or None
        self.pasta_cache = pasta_cache
        self.silenciar = silenciar_avisos
        if self.pasta_cache:
            os.makedirs(self.pasta_cache, exist_ok=True)

    @property
    def disponivel(self) -> bool:
        return self.cliente is not None

    # --- cache ---------------------------------------------------------
    def _caminho_cache(self, texto: str) -> str:
        """Uma frase idêntica, na mesma voz e modelo, reaproveita o áudio."""
        if not self.pasta_cache:
            return ""
        assinatura = f"{self.modelo}|{self.voz}|{self.instrucoes}|{texto}"
        chave = hashlib.sha256(assinatura.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.pasta_cache, f"{chave}.pcm")

    # --- reprodução ----------------------------------------------------
    def _tocar(self, blocos) -> None:
        """
        Recebe um iterável de blocos de PCM e escreve no dispositivo de saída.
        Abrimos e fechamos o stream a cada fala: custa poucos milissegundos e
        evita stream travado se outro programa pegar a placa de som no meio.
        """
        import pyaudio

        with silenciar_stderr_nativo(self.silenciar):
            audio = pyaudio.PyAudio()
            stream = audio.open(format=pyaudio.paInt16, channels=self.CANAIS,
                                rate=self.TAXA, output=True)
        try:
            for bloco in blocos:
                if bloco:
                    stream.write(bloco)
        finally:
            with silenciar_stderr_nativo(self.silenciar):
                stream.stop_stream()
                stream.close()
                audio.terminate()

    def falar(self, texto: str) -> bool:
        if not self.disponivel:
            return False

        caminho = self._caminho_cache(texto)

        # Já sintetizamos essa frase antes: toca do disco, sem rede.
        if caminho and os.path.exists(caminho):
            try:
                with open(caminho, "rb") as arquivo:
                    self._tocar(iter(lambda: arquivo.read(4096), b""))
                return True
            except Exception as erro:
                print(f"[Speaker] Falha ao tocar o cache: {erro}")

        # Sintetiza e toca em streaming, guardando o áudio para a próxima vez.
        try:
            pedaços = []
            extras = {"instructions": self.instrucoes} if self.instrucoes else {}
            with self.cliente.audio.speech.with_streaming_response.create(
                model=self.modelo,
                voice=self.voz,
                input=texto,
                response_format="pcm",
                **extras,
            ) as resposta:
                def blocos():
                    for bloco in resposta.iter_bytes(4096):
                        pedaços.append(bloco)
                        yield bloco

                self._tocar(blocos())

            if caminho and pedaços:
                with open(caminho, "wb") as arquivo:
                    arquivo.write(b"".join(pedaços))
            return True
        except Exception as erro:
            print(f"[Speaker] TTS da OpenAI falhou ({erro}). Usando a voz offline.")
            return False


# ---------------------------------------------------------------------------
class Speaker:
    """
    Fachada de voz usada por toda a aplicação.

    Recebe o backend principal e um reserva. Se o principal falhar em uma fala
    (rede caiu, cota estourou), o reserva assume dali em diante — a assistente
    nunca fica muda no meio da apresentação.
    """

    def __init__(self, backend: TTSBackend = None, reserva: TTSBackend = None,
                 ativo: bool = True):
        self.ativo = ativo
        self.backend = backend
        self.reserva = reserva

    @property
    def nome_backend(self) -> str:
        return self.backend.nome if self.backend else "texto"

    def falar(self, texto: str) -> None:
        """Fala o texto (e sempre imprime, para acompanhar a demo pelo terminal)."""
        if not texto:
            return
        print(f"🤖 Roberto: {texto}")
        if not self.ativo:
            return

        if self.backend and self.backend.falar(texto):
            return

        # O principal falhou: promove o reserva a titular e tenta de novo.
        if self.reserva and self.reserva is not self.backend:
            print(f"[Speaker] Trocando para o backend '{self.reserva.nome}'.")
            self.backend, self.reserva = self.reserva, None
            if self.backend.falar(texto):
                return

        print("[Speaker] Sem voz disponível — seguindo apenas com texto.")
        self.ativo = False
