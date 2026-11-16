"""
Núcleo do reconhecimento facial (item 7): captura, importação e treino.

Este módulo existe para que a MESMA lógica sirva a dois consumidores:

  - `tools/train_faces.py`  — o script de linha de comando;
  - `skills/vision.py`      — o cadastro POR VOZ, feito dentro da conversa.

Nenhuma função aqui imprime nada por conta própria: todas recebem um
`ao_progredir(mensagem)` opcional. Assim o CLI imprime no terminal e a
assistente fala em voz alta, sem duplicar código.

Sobre o LBPH: a `confidence` que ele devolve é uma DISTÂNCIA — MENOR é MELHOR.
"""

import json
import os

TAMANHO = (200, 200)   # todo rosto é normalizado para este tamanho antes do treino


class ErroFaces(Exception):
    """Falha esperada e explicável (sem OpenCV, sem webcam, sem fotos...)."""


# ---------------------------------------------------------------------------
# Dependências
# ---------------------------------------------------------------------------
def carregar_cv2():
    """Importa o OpenCV validando que é a build *contrib* (a única com cv2.face)."""
    try:
        import cv2
    except ImportError as erro:
        raise ErroFaces(
            "A biblioteca OpenCV não está instalada. "
            "Rode: pip install opencv-contrib-python") from erro
    if not hasattr(cv2, "face"):
        raise ErroFaces(
            "Este OpenCV não tem o módulo face. Desinstale o opencv-python "
            "e instale o opencv-contrib-python.")
    return cv2


def carregar_detector(cv2):
    """Haar cascade frontal que acompanha o pacote do OpenCV."""
    caminho = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    detector = cv2.CascadeClassifier(caminho)
    if detector.empty():
        raise ErroFaces("Não encontrei o classificador de rostos do OpenCV.")
    return detector


# ---------------------------------------------------------------------------
# Captura pela webcam
# ---------------------------------------------------------------------------
def capturar_rostos(nome: str, pasta_faces: str, total_fotos: int = 30,
                    indice_camera: int = 0, segundos_max: int = 60,
                    ao_progredir=None, mostrar_janela: bool = True) -> int:
    """
    Salva `total_fotos` recortes do rosto detectado na webcam e devolve quantas
    conseguiu. `segundos_max` evita travar para sempre se ninguém aparecer —
    detalhe importante no cadastro por voz, onde não há como apertar ESC.
    """
    import time

    cv2 = carregar_cv2()
    detector = carregar_detector(cv2)

    destino = os.path.join(pasta_faces, nome)
    os.makedirs(destino, exist_ok=True)
    # Continua a numeração para não sobrescrever capturas anteriores.
    ja_existem = len([f for f in os.listdir(destino) if f.lower().endswith(".png")])

    camera = cv2.VideoCapture(indice_camera)
    if not camera.isOpened():
        raise ErroFaces("Não consegui abrir a webcam. "
                        "Verifique se ela está conectada e se nenhum outro app a ocupa.")

    salvas = 0
    inicio = time.time()
    try:
        while salvas < total_fotos and time.time() - inicio < segundos_max:
            ok, quadro = camera.read()
            if not ok:
                continue

            cinza = cv2.cvtColor(quadro, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(cinza, scaleFactor=1.2,
                                              minNeighbors=5, minSize=(100, 100))

            for (x, y, largura, altura) in faces[:1]:   # só o rosto principal
                rosto = cv2.resize(cinza[y:y + altura, x:x + largura], TAMANHO)
                cv2.imwrite(os.path.join(destino, f"{nome}_{ja_existem + salvas:03d}.png"), rosto)
                salvas += 1
                cv2.rectangle(quadro, (x, y), (x + largura, y + altura), (0, 200, 0), 2)
                if ao_progredir and salvas % 10 == 0:
                    ao_progredir(f"{salvas} de {total_fotos}")

            if mostrar_janela:
                cv2.putText(quadro, f"{salvas}/{total_fotos}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 2)
                cv2.imshow("Cadastro de rosto (ESC para cancelar)", quadro)
                if cv2.waitKey(60) & 0xFF == 27:        # ESC
                    break
            else:
                time.sleep(0.06)   # espaça os quadros para variar as fotos
    finally:
        camera.release()
        if mostrar_janela:
            cv2.destroyAllWindows()

    return salvas


# ---------------------------------------------------------------------------
# Importação de fotos existentes
# ---------------------------------------------------------------------------
def importar_fotos(origem: str, nome: str, pasta_faces: str, ao_progredir=None):
    """
    Detecta e recorta os rostos de fotos comuns de uma pasta.
    Devolve (quantos_rostos, quantos_arquivos_sem_rosto).

    Não dá para só copiar as fotos: o treino espera o rosto JÁ RECORTADO.
    Uma foto inteira redimensionada faria o LBPH aprender a cena, não a face.
    """
    cv2 = carregar_cv2()
    detector = carregar_detector(cv2)

    if not os.path.isdir(origem):
        raise ErroFaces(f"Pasta não encontrada: {origem}")

    destino = os.path.join(pasta_faces, nome)
    os.makedirs(destino, exist_ok=True)
    ja_existem = len([f for f in os.listdir(destino) if f.lower().endswith(".png")])

    extensoes = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
    arquivos = sorted(f for f in os.listdir(origem) if f.lower().endswith(extensoes))
    if not arquivos:
        raise ErroFaces(f"Nenhuma imagem em {origem}")

    salvos = sem_rosto = 0
    for arquivo in arquivos:
        imagem = cv2.imread(os.path.join(origem, arquivo), cv2.IMREAD_GRAYSCALE)
        if imagem is None:
            continue
        faces = detector.detectMultiScale(imagem, scaleFactor=1.15,
                                          minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            sem_rosto += 1
            if ao_progredir:
                ao_progredir(f"– sem rosto detectado: {arquivo}")
            continue
        # Uma foto de grupo vira várias amostras: aproveitamos todos os rostos.
        for (x, y, largura, altura) in faces:
            rosto = cv2.resize(imagem[y:y + altura, x:x + largura], TAMANHO)
            cv2.imwrite(os.path.join(destino, f"{nome}_{ja_existem + salvos:03d}.png"), rosto)
            salvos += 1

    return salvos, sem_rosto


# ---------------------------------------------------------------------------
# Treino
# ---------------------------------------------------------------------------
def treinar_modelo(pasta_faces: str, caminho_modelo: str, caminho_rotulos: str,
                   ao_progredir=None):
    """
    Lê data/faces/<pessoa>/*.png, treina o LBPH e grava o .yml + os rótulos.
    Devolve (total_de_amostras, {id: nome}).
    """
    cv2 = carregar_cv2()
    import numpy as np

    if not os.path.isdir(pasta_faces):
        raise ErroFaces(f"Pasta {pasta_faces} não existe. Capture rostos primeiro.")

    amostras, identificadores, rotulos = [], [], {}
    proximo_id = 0

    for pessoa in sorted(os.listdir(pasta_faces)):
        pasta_pessoa = os.path.join(pasta_faces, pessoa)
        if not os.path.isdir(pasta_pessoa):
            continue
        imagens = [f for f in os.listdir(pasta_pessoa)
                   if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not imagens:
            continue

        rotulos[proximo_id] = pessoa
        for arquivo in imagens:
            imagem = cv2.imread(os.path.join(pasta_pessoa, arquivo), cv2.IMREAD_GRAYSCALE)
            if imagem is None:
                continue
            if imagem.shape[:2] != TAMANHO:
                imagem = cv2.resize(imagem, TAMANHO)
            amostras.append(imagem)
            identificadores.append(proximo_id)

        if ao_progredir:
            ao_progredir(f"id {proximo_id}: {pessoa} ({len(imagens)} imagens)")
        proximo_id += 1

    if not amostras:
        raise ErroFaces("Nenhuma imagem encontrada para treinar.")

    # LBPH = Local Binary Patterns Histograms. Leve, treina em segundos e
    # funciona bem com poucas amostras — ideal para o prazo do checkpoint.
    reconhecedor = cv2.face.LBPHFaceRecognizer_create(
        radius=1, neighbors=8, grid_x=8, grid_y=8)
    reconhecedor.train(amostras, np.array(identificadores))

    os.makedirs(os.path.dirname(caminho_modelo), exist_ok=True)
    reconhecedor.write(caminho_modelo)
    with open(caminho_rotulos, "w", encoding="utf-8") as arquivo:
        json.dump(rotulos, arquivo, ensure_ascii=False, indent=2)

    return len(amostras), rotulos
