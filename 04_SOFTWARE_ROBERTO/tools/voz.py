"""
Ferramentas da voz neural (TTS da OpenAI).

Dois modos:

  --amostras   Sintetiza a mesma frase em várias vozes e toca uma a uma,
               para o grupo escolher qual usar na apresentação.

  --aquecer    Pré-sintetiza as frases fixas da assistente e guarda no cache
               em disco. Depois disso elas tocam SEM chamada de rede, o que
               tira ~1,7 segundo de latência de cada resposta ensaiada.
               Rode isto na véspera da apresentação.

Uso:
    python tools/voz.py --amostras
    python tools/voz.py --amostras --vozes nova,coral,sage
    python tools/voz.py --aquecer
    python tools/voz.py --aquecer --voz coral
"""

import argparse
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from dotenv import load_dotenv  # noqa: E402

from core.llm import LLMClient  # noqa: E402
from core.speaker import OpenAITTS  # noqa: E402

PASTA_CACHE = os.path.join(RAIZ, "data", "cache_voz")

VOZES_PADRAO = ["nova", "coral", "shimmer", "sage", "alloy", "fable", "onyx", "ash"]

FRASE_AMOSTRA = ("Evento cadastrado na agenda: prova de cálculo na "
                 "quinta-feira às dezenove horas.")

# Frases que a assistente repete sempre. São exatamente as strings fixas
# espalhadas pelo código — mantenha esta lista em dia se mudar alguma.
FRASES_FIXAS = [
    "Roberto online. Diga o meu nome para começar.",
    "Pois não?",
    "Ok, qual evento devo cadastrar?",
    "Sua agenda está vazia. Nenhum evento cadastrado.",
    "Agenda limpa. O arquivo agenda.txt continua existindo, agora vazio.",
    "Só um instante, vou abrir a câmera.",
    "Não entendi. Pode repetir?",
    "Até logo!",
    "Encerrando. Até logo!",
    "Não é possível dividir por zero.",
    "Partida iniciada. Você é o X e começa. As casas vão de 1 a 9, "
    "da esquerda para a direita. Diga a sua jogada, por exemplo: linha 2, coluna 3.",
    "Não entendi a jogada. Diga, por exemplo: linha 2, coluna 3.",
    "Eu venci! Quer jogar de novo?",
    "Deu velha, empatamos. Bom jogo!",
    "Partida encerrada. Quando quiser, é só chamar de novo.",
]


def montar_tts(llm, voz: str) -> OpenAITTS:
    return OpenAITTS(
        cliente=llm.cliente,
        modelo=os.getenv("TTS_MODELO", "gpt-4o-mini-tts"),
        voz=voz,
        instrucoes=os.getenv("TTS_INSTRUCOES") or None,
        pasta_cache=PASTA_CACHE,
    )


def amostras(llm, vozes: list) -> None:
    """Toca a mesma frase em cada voz, para comparação."""
    print(f"\nFrase de teste: {FRASE_AMOSTRA!r}\n")
    for voz in vozes:
        print(f"  ▶ {voz}")
        tts = montar_tts(llm, voz)
        inicio = time.time()
        if tts.falar(FRASE_AMOSTRA):
            print(f"     ok ({time.time() - inicio:.1f}s)")
        else:
            print("     falhou")
    print("\nEscolha a que preferir e coloque no .env:  TTS_VOZ=<voz>")


def aquecer(llm, voz: str) -> None:
    """
    Sintetiza e guarda em cache todas as frases fixas.

    Não tocamos o áudio aqui — só geramos e salvamos. Por isso escrevemos o
    arquivo direto, sem passar pela reprodução.
    """
    tts = montar_tts(llm, voz)
    os.makedirs(PASTA_CACHE, exist_ok=True)
    novas = ja_existiam = falhas = 0

    print(f"\nAquecendo o cache da voz '{voz}' ({len(FRASES_FIXAS)} frases fixas)...\n")
    for frase in FRASES_FIXAS:
        caminho = tts._caminho_cache(frase)
        if os.path.exists(caminho):
            ja_existiam += 1
            print(f"  ✓ (já em cache) {frase[:58]}")
            continue
        try:
            extras = {"instructions": tts.instrucoes} if tts.instrucoes else {}
            resposta = llm.cliente.audio.speech.create(
                model=tts.modelo, voice=tts.voz, input=frase,
                response_format="pcm", **extras)
            with open(caminho, "wb") as arquivo:
                arquivo.write(resposta.content)
            novas += 1
            print(f"  ✓ {frase[:58]}")
        except Exception as erro:
            falhas += 1
            print(f"  ✗ {frase[:40]} -> {str(erro)[:50]}")

    tamanho = sum(os.path.getsize(os.path.join(PASTA_CACHE, f))
                  for f in os.listdir(PASTA_CACHE)) / 1024 / 1024
    print(f"\n  {novas} nova(s), {ja_existiam} já existia(m), {falhas} falha(s).")
    print(f"  Cache em {PASTA_CACHE} ({tamanho:.1f} MB)")
    print("  Essas frases agora tocam sem chamada de rede.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ferramentas da voz neural da Roberto")
    parser.add_argument("--amostras", action="store_true",
                        help="Toca a mesma frase em várias vozes para comparar")
    parser.add_argument("--aquecer", action="store_true",
                        help="Pré-sintetiza as frases fixas e guarda no cache")
    parser.add_argument("--vozes", default=None,
                        help="Lista separada por vírgula (padrão: as 8 principais)")
    parser.add_argument("--voz", default=None,
                        help="Voz usada no --aquecer (padrão: a do .env)")
    args = parser.parse_args()

    load_dotenv(os.path.join(RAIZ, ".env"))
    llm = LLMClient()
    if not llm.disponivel:
        print("ERRO: a voz neural precisa da OPENAI_API_KEY no .env.")
        return 1

    if args.amostras:
        vozes = [v.strip() for v in args.vozes.split(",")] if args.vozes else VOZES_PADRAO
        amostras(llm, vozes)
        return 0

    if args.aquecer:
        aquecer(llm, args.voz or os.getenv("TTS_VOZ", "nova"))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
