"""
FaceSkill — item 7 do enunciado.

"Roberto, quem sou eu?" -> abre a webcam, detecta o rosto e identifica a pessoa
usando o modelo LBPH pré-treinado (models/faces.yml).

ARMADILHA CLÁSSICA DO LBPH: o valor de `confidence` é uma DISTÂNCIA, não uma
porcentagem de certeza. MENOR é MELHOR. confidence 30 = reconhecimento ótimo;
confidence 120 = provavelmente é outra pessoa. Todo mundo erra isso e inverte
a comparação. Nosso limiar padrão é 70 (configurável no .env).

Pré-requisito: rodar `python tools/train_faces.py` antes da apresentação para
gerar models/faces.yml e models/labels.json.
"""

import json
import os
import re
import time

from skills.base import Skill


class FaceSkill(Skill):
    nome = "reconhecimento_facial"
    descricao = "Abre a webcam e reconhece quem está na frente da câmera."

    padroes = [
        r"\bquem sou eu\b",
        r"\breconhecer? (a )?face\b",
        r"\breconhecimento facial\b",
        r"\bme reconhec(e|a)\b",
        r"\bquem (esta|ta) na (frente|camera|webcam)\b",
        r"\babrir? (a )?(webcam|camera)\b",
        r"\bvoce me conhece\b",
    ]

    def __init__(self, modelo: str = "models/faces.yml", rotulos: str = "models/labels.json",
                 limiar: float = 70.0, indice_camera: int = 0, segundos: int = 6):
        super().__init__()
        self.caminho_modelo = modelo
        self.caminho_rotulos = rotulos
        self.limiar = limiar                # confidence < limiar => reconhecido
        self.indice_camera = indice_camera
        self.segundos = segundos            # tempo máximo com a webcam aberta

    # ------------------------------------------------------------------
    def _carregar(self):
        """
        Carrega OpenCV, o classificador Haar (detecção) e o LBPH (identificação).
        Devolve (cv2, detector, reconhecedor, rotulos) ou uma string de erro.
        """
        try:
            import cv2
        except ImportError:
            return "A biblioteca OpenCV não está instalada. Rode: pip install opencv-contrib-python"

        if not hasattr(cv2, "face"):
            return ("Este OpenCV não tem o módulo face. Desinstale o opencv-python "
                    "e instale o opencv-contrib-python.")

        if not os.path.exists(self.caminho_modelo):
            return ("O modelo de rostos ainda não foi treinado. "
                    "Rode o script tools/train_faces.py antes de me pedir isso.")

        # Haar cascade que já vem junto com o pacote do OpenCV.
        cascata = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        detector = cv2.CascadeClassifier(cascata)

        reconhecedor = cv2.face.LBPHFaceRecognizer_create()
        reconhecedor.read(self.caminho_modelo)

        rotulos = {}
        if os.path.exists(self.caminho_rotulos):
            with open(self.caminho_rotulos, "r", encoding="utf-8") as arquivo:
                # JSON só tem chave string; convertemos de volta para int.
                rotulos = {int(k): v for k, v in json.load(arquivo).items()}

        return cv2, detector, reconhecedor, rotulos

    # ------------------------------------------------------------------
    def reconhecer(self) -> str:
        """Abre a webcam por alguns segundos e devolve o nome de quem apareceu."""
        carregado = self._carregar()
        if isinstance(carregado, str):
            return carregado  # mensagem de erro amigável
        cv2, detector, reconhecedor, rotulos = carregado

        camera = cv2.VideoCapture(self.indice_camera)
        if not camera.isOpened():
            return "Não consegui abrir a webcam. Verifique se ela está conectada e livre."

        melhor_nome, melhor_confianca = None, float("inf")
        inicio = time.time()
        try:
            while time.time() - inicio < self.segundos:
                ok, quadro = camera.read()
                if not ok:
                    continue

                cinza = cv2.cvtColor(quadro, cv2.COLOR_BGR2GRAY)
                # scaleFactor 1.2 e minNeighbors 5: bom equilíbrio entre
                # velocidade e falsos positivos em webcam de notebook.
                faces = detector.detectMultiScale(cinza, scaleFactor=1.2,
                                                  minNeighbors=5, minSize=(80, 80))

                for (x, y, largura, altura) in faces:
                    rosto = cv2.resize(cinza[y:y + altura, x:x + largura], (200, 200))
                    id_previsto, confianca = reconhecedor.predict(rosto)

                    # LBPH: MENOR confidence = MAIS parecido. Comparação invertida!
                    reconhecido = confianca < self.limiar
                    nome = rotulos.get(id_previsto, "desconhecido") if reconhecido else "desconhecido"

                    if confianca < melhor_confianca:
                        melhor_confianca, melhor_nome = confianca, nome

                    # Feedback visual: verde = reconhecido, vermelho = desconhecido.
                    cor = (0, 200, 0) if reconhecido else (0, 0, 255)
                    cv2.rectangle(quadro, (x, y), (x + largura, y + altura), cor, 2)
                    cv2.putText(quadro, f"{nome} ({confianca:.0f})", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)

                cv2.imshow("Roberto - Reconhecimento Facial (ESC para sair)", quadro)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    break
        finally:
            camera.release()
            cv2.destroyAllWindows()

        if melhor_nome is None:
            return "Não consegui detectar nenhum rosto na frente da câmera."
        if melhor_nome == "desconhecido":
            return (f"Detectei um rosto, mas não reconheci essa pessoa. "
                    f"A distância foi {melhor_confianca:.0f}, acima do meu limiar de {self.limiar:.0f}.")
        return f"Você é {melhor_nome}. Reconheci com distância {melhor_confianca:.0f}."

    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        if hasattr(ctx.assistente, 'recognize_face'):
            return ctx.assistente.recognize_face(self)
        ctx.falar("Só um instante, vou abrir a câmera.")
        return self.reconhecer()

    def ferramentas(self) -> list:
        return [{
            "name": "reconhecer_face",
            "description": "Abre a webcam e identifica quem está na frente da câmera.",
            "parameters": {"type": "object", "properties": {}},
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "reconhecer_face":
            raise NotImplementedError(nome)
        return self.reconhecer()


class CadastroFaceSkill(Skill):
    """
    Cadastro de rostos POR VOZ — sem precisar do terminal.

    "Roberto, cadastre o meu rosto"
      -> "Qual é o seu nome?"            (abre o diálogo, igual ao item 2)
      -> "Julio"
      -> captura 30 fotos, treina o modelo e confirma falando

    Reaproveita exatamente as mesmas funções de core/faces.py que o script
    tools/train_faces.py usa: a lógica de captura e treino existe em um lugar só.
    """

    nome = "cadastro_facial"
    descricao = "Cadastra o rosto de uma pessoa na webcam e treina o modelo."

    padroes = [
        r"\bcadastr(ar|e|a)\b.*\b(rosto|face|cara)\b",
        r"\b(rosto|face)\b.*\bcadastr(ar|o|e)\b",
        r"\b(registrar?|registre|salvar?|salve|grav(ar|e))\b.*\b(rosto|face)\b",
        r"\b(aprend(a|er)|decor(e|ar)|memoriz(e|ar))\b.*\b(meu rosto|minha cara|meu nome)\b",
        r"\bme cadastr(ar|e)\b",
        r"\bnovo rosto\b",
    ]

    # Palavras que aparecem antes do nome na fala: "meu nome é Julio".
    PREFIXOS_NOME = (
        "meu nome e", "meu nome eh", "o meu nome e", "eu sou o", "eu sou a",
        "eu me chamo", "me chamo", "pode me chamar de", "sou o", "sou a", "eu sou",
    )

    def __init__(self, pasta_faces: str, modelo: str, rotulos: str,
                 fotos: int = 30, indice_camera: int = 0):
        super().__init__()
        self.pasta_faces = pasta_faces
        self.caminho_modelo = modelo
        self.caminho_rotulos = rotulos
        self.fotos = fotos
        self.indice_camera = indice_camera

    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        """Se o nome já veio na frase, cadastra direto; senão, pergunta."""
        nome = self._extrair_nome_inline(texto)
        if nome:
            return self.cadastrar(nome, ctx)

        # Mesmo mecanismo do item 2: pergunta e aguarda a próxima fala.
        ctx.aguardar_resposta(lambda fala, c: self._receber_nome(fala, c))
        return "Qual é o nome da pessoa que devo cadastrar?"

    def _receber_nome(self, fala: str, ctx) -> str:
        """Callback com a resposta do usuário à pergunta do nome."""
        nome = self.limpar_nome(fala)
        if not nome:
            ctx.aguardar_resposta(lambda f, c: self._receber_nome(f, c))
            return "Não entendi o nome. Pode repetir, por favor?"
        return self.cadastrar(nome, ctx)

    # ------------------------------------------------------------------
    def cadastrar(self, nome: str, ctx) -> str:
        """Captura as fotos, retreina o modelo e devolve a confirmação falada."""
        if hasattr(ctx.assistente, 'enroll_face'):
            return ctx.assistente.enroll_face(nome, self)
        from core.faces import ErroFaces, capturar_rostos, treinar_modelo

        ctx.falar(f"Certo, {nome}. Vou abrir a câmera e tirar {self.fotos} fotos. "
                  "Olhe para a webcam e mexa a cabeça devagar.")

        try:
            salvas = capturar_rostos(
                nome=nome,
                pasta_faces=self.pasta_faces,
                total_fotos=self.fotos,
                indice_camera=self.indice_camera,
                # Sem teclado à mão no modo voz: o limite de tempo é a saída
                # de emergência se ninguém aparecer na frente da câmera.
                segundos_max=60,
                ao_progredir=lambda m: print(f"[Cadastro] {m}"),
            )
        except ErroFaces as erro:
            return str(erro)

        if salvas == 0:
            return ("Não consegui detectar nenhum rosto. Verifique a iluminação "
                    "e fique de frente para a câmera, depois tente de novo.")

        ctx.falar(f"Capturei {salvas} fotos. Agora estou treinando o modelo, "
                  "só um instante.")

        try:
            total, rotulos = treinar_modelo(
                pasta_faces=self.pasta_faces,
                caminho_modelo=self.caminho_modelo,
                caminho_rotulos=self.caminho_rotulos,
                ao_progredir=lambda m: print(f"[Treino] {m}"),
            )
        except ErroFaces as erro:
            return f"Capturei as fotos, mas o treino falhou: {erro}"

        pessoas = list(rotulos.values())
        resposta = (f"Pronto, {nome} cadastrado com {salvas} fotos. "
                    f"O modelo agora conhece {len(pessoas)} pessoa: {', '.join(pessoas)}."
                    if len(pessoas) == 1 else
                    f"Pronto, {nome} cadastrado com {salvas} fotos. "
                    f"O modelo agora conhece {len(pessoas)} pessoas: {', '.join(pessoas)}.")

        # O aviso mais importante do item 7: sem contraexemplos, o LBPH
        # classifica QUALQUER rosto como a única pessoa que ele conhece.
        if not any(p.lower().startswith("desconhecid") for p in pessoas):
            resposta += (" Recomendo cadastrar também uma pessoa chamada desconhecido, "
                         "senão eu vou achar que todo mundo é você.")
        else:
            resposta += " Pode me perguntar: quem sou eu?"
        return resposta

    # ------------------------------------------------------------------
    def _extrair_nome_inline(self, texto: str) -> str:
        """'cadastrar o rosto do João' -> 'joao'."""
        normalizado = self.normalizar_texto(texto)
        achado = re.search(r"\b(?:rosto|face|cara)\s+(?:d[oae]s?\s+)?(.+)$", normalizado)
        if not achado:
            return ""
        return self.limpar_nome(achado.group(1))

    def limpar_nome(self, fala: str) -> str:
        """
        Extrai o nome da resposta falada.
        'meu nome é Julio César' -> 'julio cesar'  (vira o nome da pasta)
        """
        nome = self.normalizar_texto(fala)
        for prefixo in self.PREFIXOS_NOME:
            if nome.startswith(prefixo + " "):
                nome = nome[len(prefixo):].strip()
                break
        nome = re.sub(r"\b(por favor|obrigado|obrigada|ai|entao)\b", "", nome).strip()
        # Só letras, números e espaço: o nome vira nome de pasta no disco.
        nome = re.sub(r"[^a-z0-9 ]", "", nome).strip()
        nome = re.sub(r"\s+", "_", nome)
        # Nomes absurdamente longos quase sempre são erro de transcrição.
        return nome if 0 < len(nome) <= 40 else ""

    # ------------------------------------------------------------------
    def ferramentas(self) -> list:
        return [{
            "name": "cadastrar_rosto",
            "description": ("Cadastra o rosto de uma pessoa: abre a webcam, tira fotos "
                            "e treina o modelo de reconhecimento facial."),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome da pessoa a cadastrar."}
                },
                "required": ["nome"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "cadastrar_rosto":
            raise NotImplementedError(nome)
        pessoa = self.limpar_nome(argumentos.get("nome", ""))
        if not pessoa:
            ctx.aguardar_resposta(lambda f, c: self._receber_nome(f, c))
            return "Qual é o nome da pessoa que devo cadastrar?"
        return self.cadastrar(pessoa, ctx)
