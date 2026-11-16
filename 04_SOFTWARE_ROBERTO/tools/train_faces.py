"""
Treinador do modelo de reconhecimento facial (item 7) — interface de linha
de comando.

Toda a lógica de verdade mora em `core/faces.py`, que é o MESMO código usado
pelo cadastro por voz (skills/vision.py -> CadastroFaceSkill). Este arquivo é
só a casca de linha de comando.

Etapas:
  1. CAPTURA    — abre a webcam e salva ~30 fotos em data/faces/<nome>/
  1b. IMPORTA   — extrai rostos de fotos que você já tem
  2. TREINO     — lê data/faces/, treina o LBPH e grava models/faces.yml

Uso:
    python tools/train_faces.py --capturar --nome julio
    python tools/train_faces.py --capturar --nome desconhecido --fotos 40
    python tools/train_faces.py --importar ~/Imagens/turma --nome desconhecido
    python tools/train_faces.py --treinar
    python tools/train_faces.py --listar

DICA DO ENUNCIADO: cadastre também uma classe "desconhecido" com fotos de
outras pessoas. Sem contraexemplos, o LBPH "reconhece" qualquer rosto como a
única pessoa que ele conhece.
"""

import argparse
import os
import sys

# Permite rodar o script direto de tools/ sem quebrar os imports do projeto.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from core.faces import (ErroFaces, capturar_rostos, importar_fotos,  # noqa: E402
                        treinar_modelo)

PASTA_FACES = os.path.join(RAIZ, "data", "faces")
PASTA_MODELOS = os.path.join(RAIZ, "models")
CAMINHO_MODELO = os.path.join(PASTA_MODELOS, "faces.yml")
CAMINHO_ROTULOS = os.path.join(PASTA_MODELOS, "labels.json")


def listar() -> None:
    """Mostra quem já está cadastrado e quantas amostras cada um tem."""
    if not os.path.isdir(PASTA_FACES):
        print("Nenhum rosto capturado ainda.")
        return

    pessoas = sorted(p for p in os.listdir(PASTA_FACES)
                     if os.path.isdir(os.path.join(PASTA_FACES, p)))
    if not pessoas:
        print("Nenhum rosto capturado ainda.")
        return

    print(f"\nRostos em {PASTA_FACES}:\n")
    for pessoa in pessoas:
        n = len([f for f in os.listdir(os.path.join(PASTA_FACES, pessoa))
                 if f.lower().endswith((".png", ".jpg", ".jpeg"))])
        aviso = "  ← poucas amostras (mín. recomendado: 20)" if n < 20 else ""
        print(f"  {pessoa:24} {n:4} imagens{aviso}")

    tem_desconhecido = any(p.lower().startswith("desconhecid") for p in pessoas)
    print()
    if not tem_desconhecido:
        print('  ⚠️  Falta a classe "desconhecido". Sem contraexemplos, o modelo')
        print("     classifica qualquer rosto como a única pessoa que conhece.")
    if os.path.exists(CAMINHO_MODELO):
        print(f"  Modelo treinado: {CAMINHO_MODELO} "
              f"({os.path.getsize(CAMINHO_MODELO) / 1024:.0f} KB)")
    else:
        print("  Modelo ainda não treinado. Rode: --treinar")


def main() -> int:
    parser = argparse.ArgumentParser(description="Treino do reconhecimento facial da Roberto")
    parser.add_argument("--capturar", action="store_true", help="Captura fotos pela webcam")
    parser.add_argument("--importar", metavar="PASTA", default=None,
                        help="Importa fotos de uma pasta, recortando os rostos")
    parser.add_argument("--treinar", action="store_true", help="Treina o modelo LBPH")
    parser.add_argument("--listar", action="store_true", help="Lista quem já está cadastrado")
    parser.add_argument("--nome", default=None, help="Nome da pessoa (pasta de destino)")
    parser.add_argument("--fotos", type=int, default=30, help="Quantidade de fotos (padrão 30)")
    parser.add_argument("--camera", type=int, default=0, help="Índice da webcam (padrão 0)")
    args = parser.parse_args()

    try:
        if args.listar:
            listar()
            return 0

        if args.capturar:
            if not args.nome:
                print("Informe o nome: python tools/train_faces.py --capturar --nome julio")
                return 1
            print(f"Capturando {args.fotos} fotos de '{args.nome}'.")
            print("Mexa levemente a cabeça e varie a expressão. ESC cancela.")
            salvas = capturar_rostos(
                nome=args.nome.strip().lower(), pasta_faces=PASTA_FACES,
                total_fotos=args.fotos, indice_camera=args.camera,
                segundos_max=300, ao_progredir=lambda m: print(f"  {m}"))
            print(f"\nPronto: {salvas} fotos salvas.")
            print("Agora rode: python tools/train_faces.py --treinar")
            return 0

        if args.importar:
            if not args.nome:
                print("Informe o nome: python tools/train_faces.py --importar ~/fotos --nome desconhecido")
                return 1
            salvos, sem_rosto = importar_fotos(
                origem=os.path.expanduser(args.importar), nome=args.nome.strip().lower(),
                pasta_faces=PASTA_FACES, ao_progredir=lambda m: print(f"  {m}"))
            print(f"\n  {salvos} rosto(s) importado(s).")
            if sem_rosto:
                print(f"  {sem_rosto} arquivo(s) sem rosto detectável (ignorados).")
            print("\nAgora rode: python tools/train_faces.py --treinar")
            return 0

        if args.treinar:
            total, rotulos = treinar_modelo(
                pasta_faces=PASTA_FACES, caminho_modelo=CAMINHO_MODELO,
                caminho_rotulos=CAMINHO_ROTULOS, ao_progredir=lambda m: print(f"  {m}"))
            print(f"\nModelo salvo em {CAMINHO_MODELO}")
            print(f"Rótulos salvos em {CAMINHO_ROTULOS}")
            print(f"Total: {total} imagens de {len(rotulos)} pessoa(s).")
            if not any(v.lower().startswith("desconhecid") for v in rotulos.values()):
                print('\n⚠️  Sem a classe "desconhecido", o modelo vai identificar')
                print("   qualquer pessoa como uma das cadastradas.")
            return 0

    except ErroFaces as erro:
        print(f"ERRO: {erro}")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
