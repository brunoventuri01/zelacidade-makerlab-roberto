"""
EXTRAS 3 e 4 — Interação com o sistema operacional.

  ScreenshotSkill -> "Roberto, tire um print da tela"
  VolumeSkill     -> "Roberto, aumentar o volume do computador"

Os dois são multiplataforma: detectamos o SO em tempo de execução, porque o
mecanismo de volume muda completamente entre Windows, Linux e macOS.
"""

import os
import platform
import re
import subprocess
from datetime import datetime

from skills.base import Skill


class ScreenshotSkill(Skill):
    nome = "screenshot"
    descricao = "Tira uma captura de tela e salva com data e hora no nome."

    padroes = [
        r"\b(tirar?|tire|dar?|fazer?|faca|capturar?)\b.*\b(print|screenshot|captura)\b",
        r"\bprint (da|de) tela\b",
        r"\bcapturar? (a )?tela\b",
        r"\bscreenshot\b",
    ]

    def __init__(self, pasta: str = "data/screenshots"):
        super().__init__()
        self.pasta = pasta

    def capturar(self) -> str:
        os.makedirs(self.pasta, exist_ok=True)
        nome_arquivo = datetime.now().strftime("print_%Y-%m-%d_%H-%M-%S.png")
        destino = os.path.join(self.pasta, nome_arquivo)

        # Tentativa 1: mss (rápido e leve, funciona em todos os SOs).
        try:
            import mss

            with mss.mss() as capturador:
                capturador.shot(mon=-1, output=destino)  # mon=-1: todos os monitores
            return f"Print salvo em {destino}."
        except Exception as erro:
            print(f"[Screenshot] mss falhou: {erro}")

        # Tentativa 2: pyautogui (depende do Pillow).
        try:
            import pyautogui

            pyautogui.screenshot().save(destino)
            return f"Print salvo em {destino}."
        except Exception as erro:
            print(f"[Screenshot] pyautogui falhou: {erro}")

        return "Não consegui tirar o print. Instale a biblioteca mss: pip install mss"

    def execute(self, texto: str, ctx) -> str:
        return self.capturar()

    def ferramentas(self) -> list:
        return [{
            "name": "tirar_print",
            "description": "Tira uma captura da tela do computador e salva em arquivo.",
            "parameters": {"type": "object", "properties": {}},
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        return self.capturar()


class VolumeSkill(Skill):
    nome = "volume"
    descricao = "Aumenta, diminui ou silencia o volume do computador."

    padroes = [
        r"\b(aumentar?|aumente|subir?|suba|abaixar?|abaixe|diminuir?|diminua|baixar?)\b.*\bvolume\b",
        r"\bvolume\b.*\b(mais alto|mais baixo|maximo|minimo)\b",
        r"\b(mutar|mudo|silenciar|sem som)\b",
    ]

    PASSO = 10  # porcentagem por comando

    def ajustar(self, direcao: str, passo: int = None) -> str:
        """direcao: 'subir', 'baixar' ou 'mudo'."""
        passo = passo or self.PASSO
        sistema = platform.system()
        try:
            if sistema == "Linux":
                return self._linux(direcao, passo)
            if sistema == "Windows":
                return self._windows(direcao, passo)
            if sistema == "Darwin":
                return self._macos(direcao, passo)
        except Exception as erro:
            print(f"[Volume] {erro}")
        return "Não consegui alterar o volume neste sistema."

    # --- implementações por SO ----------------------------------------
    @staticmethod
    def _linux(direcao: str, passo: int) -> str:
        """PipeWire/PulseAudio via pactl; se não houver, tenta o amixer (ALSA)."""
        if direcao == "mudo":
            comandos = [["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
                        ["amixer", "-q", "set", "Master", "toggle"]]
            mensagem = "Som silenciado."
        else:
            sinal = "+" if direcao == "subir" else "-"
            comandos = [["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{sinal}{passo}%"],
                        ["amixer", "-q", "set", "Master", f"{passo}%{sinal}"]]
            mensagem = f"Volume {'aumentado' if direcao == 'subir' else 'reduzido'} em {passo} por cento."

        for comando in comandos:
            try:
                subprocess.run(comando, check=True, capture_output=True)
                return mensagem
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        return "Não encontrei pactl nem amixer para controlar o volume."

    @staticmethod
    def _windows(direcao: str, passo: int) -> str:
        """Simula as teclas de mídia do teclado — não exige biblioteca extra pesada."""
        import ctypes

        TECLAS = {"subir": 0xAF, "baixar": 0xAE, "mudo": 0xAD}
        codigo = TECLAS[direcao]
        repeticoes = 1 if direcao == "mudo" else max(1, passo // 2)  # cada passo do Windows = 2%
        for _ in range(repeticoes):
            ctypes.windll.user32.keybd_event(codigo, 0, 0, 0)  # tecla pressionada
            ctypes.windll.user32.keybd_event(codigo, 0, 2, 0)  # tecla solta
        if direcao == "mudo":
            return "Som silenciado."
        return f"Volume {'aumentado' if direcao == 'subir' else 'reduzido'}."

    @staticmethod
    def _macos(direcao: str, passo: int) -> str:
        if direcao == "mudo":
            script = "set volume output muted (not (output muted of (get volume settings)))"
            mensagem = "Som silenciado."
        else:
            operador = "+" if direcao == "subir" else "-"
            script = (f"set volume output volume (output volume of (get volume settings) "
                      f"{operador} {passo})")
            mensagem = f"Volume {'aumentado' if direcao == 'subir' else 'reduzido'}."
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return mensagem

    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        normalizado = self.normalizar_texto(texto)
        if re.search(r"\b(mutar|mudo|silenciar|sem som)\b", normalizado):
            direcao = "mudo"
        elif re.search(r"\b(abaixar|abaixe|diminuir|diminua|baixar|reduzir|mais baixo|minimo)\b", normalizado):
            direcao = "baixar"
        else:
            direcao = "subir"

        # "aumentar o volume em 30 por cento"
        achado = re.search(r"(\d{1,3})\s*(por cento|%)?", normalizado)
        passo = int(achado.group(1)) if achado else None
        return self.ajustar(direcao, passo if passo and passo <= 100 else None)

    def ferramentas(self) -> list:
        return [{
            "name": "ajustar_volume",
            "description": "Aumenta, diminui ou silencia o volume do computador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direcao": {"type": "string", "enum": ["subir", "baixar", "mudo"]},
                    "passo": {"type": "integer", "description": "Quantos por cento alterar (1 a 100)."},
                },
                "required": ["direcao"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "ajustar_volume":
            raise NotImplementedError(nome)
        return self.ajustar(argumentos.get("direcao", "subir"), argumentos.get("passo"))
