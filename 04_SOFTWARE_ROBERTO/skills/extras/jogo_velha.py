"""
EXTRA 7 — Jogo da velha por voz (o comando que exige diálogo multi-turno).

"Roberto, vamos jogar jogo da velha"
-> "Você é o X e começa. Diga a jogada, por exemplo: linha 2, coluna 3."

Este é o único extra que mantém ESTADO entre falas. Ele usa o mesmo mecanismo
do item 2 (ctx.aguardar_resposta) para reabrir o turno de diálogo a cada
jogada — enquanto a partida estiver rolando, a wake word fica dispensada.

A Roberto joga com MINIMAX, então é impossível vencê-la: o melhor resultado
possível para o humano é o empate.
"""

import re

from core.text_utils import substituir_numeros_por_extenso
from skills.base import Skill

HUMANO = "X"
MAQUINA = "O"
VAZIO = " "

# Índices do tabuleiro (0 a 8) que formam vitória.
LINHAS_VITORIA = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # linhas
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # colunas
    (0, 4, 8), (2, 4, 6),              # diagonais
]


class JogoVelhaSkill(Skill):
    nome = "jogo_da_velha"
    descricao = "Joga uma partida de jogo da velha por voz contra o usuário."

    padroes = [
        r"\bjogo da velha\b",
        r"\bjogar (uma partida|um jogo)\b",
        r"\bvamos jogar\b",
        r"\btic tac toe\b",
    ]

    def __init__(self):
        super().__init__()
        self.tabuleiro = [VAZIO] * 9
        self.em_partida = False

    # ------------------------------------------------------------------
    # Regras do jogo
    # ------------------------------------------------------------------
    @staticmethod
    def vencedor(tabuleiro: list):
        """Devolve 'X', 'O' ou None."""
        for a, b, c in LINHAS_VITORIA:
            if tabuleiro[a] != VAZIO and tabuleiro[a] == tabuleiro[b] == tabuleiro[c]:
                return tabuleiro[a]
        return None

    @staticmethod
    def livres(tabuleiro: list) -> list:
        return [i for i, casa in enumerate(tabuleiro) if casa == VAZIO]

    def minimax(self, tabuleiro: list, maximizando: bool, profundidade: int = 0):
        """
        Busca exaustiva no espaço de jogadas (são no máximo 9! = 362.880
        estados, roda instantaneamente).

        Devolve (pontuacao, jogada). Descontamos a profundidade da pontuação
        para a máquina preferir vencer RÁPIDO e perder DEVAGAR.
        """
        ganhador = self.vencedor(tabuleiro)
        if ganhador == MAQUINA:
            return 10 - profundidade, None
        if ganhador == HUMANO:
            return profundidade - 10, None
        if not self.livres(tabuleiro):
            return 0, None  # empate

        jogador = MAQUINA if maximizando else HUMANO
        melhor_pontuacao = -999 if maximizando else 999
        melhor_jogada = None

        for posicao in self.livres(tabuleiro):
            tabuleiro[posicao] = jogador
            pontuacao, _ = self.minimax(tabuleiro, not maximizando, profundidade + 1)
            tabuleiro[posicao] = VAZIO  # desfaz (backtracking)

            if maximizando and pontuacao > melhor_pontuacao:
                melhor_pontuacao, melhor_jogada = pontuacao, posicao
            elif not maximizando and pontuacao < melhor_pontuacao:
                melhor_pontuacao, melhor_jogada = pontuacao, posicao

        return melhor_pontuacao, melhor_jogada

    # ------------------------------------------------------------------
    # Apresentação
    # ------------------------------------------------------------------
    def desenhar(self) -> str:
        """
        Desenha o tabuleiro no terminal (a voz descreve só o essencial).

        Os rótulos de linha e coluna não são enfeite: como as jogadas são
        faladas ("linha 2, coluna 3"), quem assiste precisa conseguir mapear a
        fala para a posição sem contar casas de cabeça.
        """
        t = self.tabuleiro
        partes = ["", "      c1  c2  c3", "     ------------"]
        for numero, i in enumerate((0, 3, 6), start=1):
            partes.append(f" l{numero} |  {t[i]} | {t[i+1]} | {t[i+2]} |")
            partes.append("     ------------")
        return "\n".join(partes) + "\n"

    @staticmethod
    def descrever(posicao: int) -> str:
        """0 -> 'linha 1, coluna 1'."""
        return f"linha {posicao // 3 + 1}, coluna {posicao % 3 + 1}"

    def estado_falado(self) -> str:
        """Descreve as casas ocupadas para quem está só ouvindo."""
        ocupadas = [f"{self.descrever(i)} tem {casa}"
                    for i, casa in enumerate(self.tabuleiro) if casa != VAZIO]
        return "; ".join(ocupadas) if ocupadas else "tabuleiro vazio"

    # ------------------------------------------------------------------
    # Interpretação da fala
    # ------------------------------------------------------------------
    def interpretar_jogada(self, fala: str):
        """
        Aceita três formatos:
          "linha 2 coluna 3"  -> posição 5
          "casa 5" / "cinco"  -> posição 4 (numeração 1..9)
        Devolve o índice 0..8 ou None se não deu para entender.
        """
        normalizado = substituir_numeros_por_extenso(self.normalizar_texto(fala))

        achado = re.search(r"linha\s*(\d)\D+coluna\s*(\d)", normalizado)
        if achado:
            linha, coluna = int(achado.group(1)), int(achado.group(2))
            if 1 <= linha <= 3 and 1 <= coluna <= 3:
                return (linha - 1) * 3 + (coluna - 1)
            return None

        numeros = re.findall(r"\d", normalizado)
        if len(numeros) >= 2:  # "dois três" = linha 2, coluna 3
            linha, coluna = int(numeros[0]), int(numeros[1])
            if 1 <= linha <= 3 and 1 <= coluna <= 3:
                return (linha - 1) * 3 + (coluna - 1)
        if len(numeros) == 1:  # "casa 5"
            casa = int(numeros[0])
            if 1 <= casa <= 9:
                return casa - 1
        return None

    # ------------------------------------------------------------------
    # Fluxo da partida
    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        self.tabuleiro = [VAZIO] * 9
        self.em_partida = True
        print(self.desenhar())
        ctx.aguardar_resposta(self._turno)  # abre o diálogo multi-turno
        return ("Partida iniciada. Você é o X e começa. As casas vão de 1 a 9, "
                "da esquerda para a direita. Diga a sua jogada, por exemplo: "
                "linha 2, coluna 3.")

    def _turno(self, fala: str, ctx) -> str:
        """Callback chamado a cada fala do usuário enquanto a partida dura."""
        normalizado = self.normalizar_texto(fala)

        if re.search(r"\b(parar|desistir|sair|cancelar|chega)\b", normalizado):
            self.em_partida = False
            return "Partida encerrada. Quando quiser, é só chamar de novo."

        # Jogando por voz, o jogador está olhando para o microfone, não para o
        # terminal. Poder perguntar como está o tabuleiro é o que torna a
        # partida jogável sem ver a tela.
        if re.search(r"\b(tabuleiro|como (esta|ta)|situacao|onde|repet(e|ir)|de novo)\b",
                     normalizado):
            print(self.desenhar())
            ctx.aguardar_resposta(self._turno)
            return f"O tabuleiro está assim: {self.estado_falado()}. Sua vez."

        posicao = self.interpretar_jogada(fala)
        if posicao is None:
            ctx.aguardar_resposta(self._turno)  # continua esperando
            return "Não entendi a jogada. Diga, por exemplo: linha 2, coluna 3."

        if self.tabuleiro[posicao] != VAZIO:
            ctx.aguardar_resposta(self._turno)
            return f"A casa {self.descrever(posicao)} já está ocupada. Escolha outra."

        # --- jogada do humano ---
        self.tabuleiro[posicao] = HUMANO
        fim = self._checar_fim()
        if fim:
            print(self.desenhar())
            return fim

        # --- jogada da máquina (minimax) ---
        _, jogada = self.minimax(self.tabuleiro, maximizando=True)
        self.tabuleiro[jogada] = MAQUINA
        print(self.desenhar())

        fim = self._checar_fim()
        if fim:
            return f"Joguei na {self.descrever(jogada)}. {fim}"

        ctx.aguardar_resposta(self._turno)  # reabre o turno
        return f"Joguei na {self.descrever(jogada)}. Sua vez."

    def _checar_fim(self):
        """Devolve a frase final da partida ou None se o jogo continua."""
        ganhador = self.vencedor(self.tabuleiro)
        if ganhador == HUMANO:
            self.em_partida = False
            return "Você venceu! Impressionante, eu jogo com minimax."
        if ganhador == MAQUINA:
            self.em_partida = False
            return "Eu venci! Quer jogar de novo?"
        if not self.livres(self.tabuleiro):
            self.em_partida = False
            return "Deu velha, empatamos. Bom jogo!"
        return None

    # ------------------------------------------------------------------
    def ferramentas(self) -> list:
        return [{
            "name": "iniciar_jogo_da_velha",
            "description": "Inicia uma partida de jogo da velha por voz contra o usuário.",
            "parameters": {"type": "object", "properties": {}},
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "iniciar_jogo_da_velha":
            raise NotImplementedError(nome)
        return self.execute("", ctx)
