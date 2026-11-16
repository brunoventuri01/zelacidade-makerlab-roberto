"""
Calibrador da palavra de ativação.

O maior risco da apresentação não é o código: é o STT transcrever "Roberto" de
um jeito que o portão não reconhece. "Roberto" não existe em português, então o
Google tende a devolver "nexo", "next", "lexus"... e isso muda de microfone
para microfone e de sotaque para sotaque.

Este script fecha esse buraco: você fala, ele mostra EXATAMENTE o que o STT
entendeu, diz se o portão aceitou, e no fim monta a linha pronta para colar no
.env com as transcrições que apareceram.

Uso:
    python tools/testar_wake.py              # 5 tentativas
    python tools/testar_wake.py --vezes 10
    python tools/testar_wake.py --frase "Roberto, que horas são?"
"""

import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from dotenv import load_dotenv  # noqa: E402

from core.assistant import WakeWordGate  # noqa: E402
from core.listener import MicrofoneListener  # noqa: E402
from core.llm import LLMClient  # noqa: E402
from core.text_utils import normalizar  # noqa: E402

VERDE, VERMELHO, AMARELO, FIM = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibra a wake word da Roberto")
    parser.add_argument("--vezes", type=int, default=5, help="Quantas tentativas (padrão 5)")
    parser.add_argument("--frase", default=None, help="Frase que você vai falar")
    parser.add_argument("--stt", choices=["google", "whisper"], default=None)
    args = parser.parse_args()

    load_dotenv(os.path.join(RAIZ, ".env"))
    wake = os.getenv("WAKE_WORD", "roberto")
    extras = [v.strip() for v in os.getenv("WAKE_WORD_VARIANTES", "").split(",") if v.strip()]
    gate = WakeWordGate(wake, extras)
    frase = args.frase or f"{wake.capitalize()}, que horas são?"

    print("=" * 62)
    print("  CALIBRAÇÃO DA PALAVRA DE ATIVAÇÃO")
    print("=" * 62)
    print(f"\n  Wake word: '{wake}'")
    print(f"  Variantes aceitas hoje: {', '.join(gate.variantes)}")
    print(f"\n  Fale {args.vezes} vezes: \"{frase}\"")
    print("  Fale como falaria na apresentação — mesma distância, mesmo tom.\n")

    llm = LLMClient()
    backend = args.stt or os.getenv("STT_BACKEND", "google")
    try:
        listener = MicrofoneListener(
            backend=backend,
            cliente_openai=llm.cliente if llm.disponivel else None,
            idioma=os.getenv("IDIOMA_STT", "pt-BR"),
        )
    except Exception as erro:
        print(f"ERRO: não consegui abrir o microfone: {erro}")
        return 1

    aceitas, recusadas, transcricoes = 0, [], []

    for tentativa in range(1, args.vezes + 1):
        print(f"\n  [{tentativa}/{args.vezes}] Fale agora...")
        texto = listener.ouvir("")
        if not texto:
            print(f"       {AMARELO}(nada captado — fale mais alto ou mais perto){FIM}")
            continue

        transcricoes.append(texto)
        normalizado = normalizar(texto)
        comando = gate.extrair_comando(texto)

        print(f"       STT entendeu: \"{texto}\"")
        print(f"       normalizado : \"{normalizado}\"")
        if comando is None:
            recusadas.append(normalizado)
            print(f"       {VERMELHO}✗ RECUSADO — o portão não viu a wake word no início{FIM}")
        else:
            aceitas += 1
            print(f"       {VERDE}✓ ACEITO — comando extraído: \"{comando}\"{FIM}")

    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    total = len(transcricoes)
    if not total:
        print("  Nenhuma fala captada. Verifique o microfone com:")
        print("     python tools/diagnostico.py --gravar")
        return 1

    print(f"  Aceitas: {aceitas}/{total}")

    if aceitas == total:
        print(f"\n  {VERDE}A wake word está confiável neste microfone. Pode apresentar.{FIM}")
        return 0

    # Sugere variantes a partir da primeira palavra do que foi recusado.
    candidatas = []
    for texto in recusadas:
        primeira = texto.split()[0] if texto.split() else ""
        duas = " ".join(texto.split()[:2])
        for c in (primeira, duas):
            if c and c not in gate.variantes and c not in candidatas:
                candidatas.append(c)

    print(f"\n  {AMARELO}O STT transcreveu de formas que o portão não conhece.{FIM}")
    if candidatas:
        atuais = os.getenv("WAKE_WORD_VARIANTES", "")
        linha = ",".join(filter(None, [atuais] + candidatas))
        print("\n  Cole esta linha no .env para ensinar as novas grafias:\n")
        print(f"     WAKE_WORD_VARIANTES={linha}\n")
        print("  Depois rode este script de novo para confirmar.")
        print(f"  {AMARELO}Cuidado:{FIM} não adicione palavras comuns do português")
        print("  (como 'e', 'de', 'para') — elas fariam a assistente disparar sozinha.")
    else:
        print("\n  As recusas não têm um padrão claro. Tente:")
        print("     - falar mais perto do microfone")
        print("     - usar o Whisper:  python tools/testar_wake.py --stt whisper")
        print("     - trocar por um nome mais fácil em pt-BR:")
        print("       WAKE_WORD=nexo   (ou 'sexta', 'jarvis', 'ana')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
