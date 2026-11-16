"""
AgendaSkill — itens 2, 3 e 8 do enunciado.

  2) "Roberto, cadastrar evento na agenda" -> pergunta e grava a resposta
  3) "Roberto, ler agenda"                 -> lê todos os eventos
  8) "Roberto, limpar agenda"              -> esvazia o arquivo SEM apagá-lo
"""

import os
from datetime import datetime

from skills.base import Skill


class AgendaSkill(Skill):
    nome = "agenda"
    descricao = "Cadastra, lê e limpa eventos da agenda pessoal em agenda.txt."

    # As regex rodam sobre o texto já normalizado (minúsculo e sem acento).
    padroes = [
        r"\b(cadastrar|adicionar|anotar|agendar|marcar|criar)\b.*\bagenda\b",
        r"\bagenda\b.*\b(cadastrar|adicionar|anotar|novo evento)\b",
        r"\b(ler|leia|listar|mostrar|consultar|ver)\b.*\bagenda\b",
        r"\b(limpar|apagar|esvaziar|zerar|excluir)\b.*\bagenda\b",
        r"\bagenda\b",
    ]

    def __init__(self, caminho: str = "data/agenda.txt"):
        super().__init__()
        self.caminho = caminho
        self._garantir_arquivo()

    # ------------------------------------------------------------------
    # Infraestrutura de arquivo
    # ------------------------------------------------------------------
    def _garantir_arquivo(self) -> None:
        """Cria data/agenda.txt vazio se ainda não existir."""
        pasta = os.path.dirname(self.caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        if not os.path.exists(self.caminho):
            open(self.caminho, "w", encoding="utf-8").close()

    # ------------------------------------------------------------------
    # Operações (item 2, 3 e 8)
    # ------------------------------------------------------------------
    def adicionar(self, evento: str) -> str:
        """Item 2: grava o evento com timestamp, em modo append e UTF-8."""
        evento = (evento or "").strip()
        if not evento:
            return "Não entendi o evento. Tente novamente dizendo: Roberto, cadastrar evento na agenda."
        carimbo = datetime.now().strftime("%d/%m/%Y %H:%M")
        # encoding="utf-8" é obrigatório: sem isso, acento quebra no Windows.
        with open(self.caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"[{carimbo}] {evento}\n")
        return f"Evento cadastrado na agenda: {evento}"

    def ler(self) -> str:
        """Item 3: lê todos os eventos. Fala 'agenda vazia' em vez de ficar mudo."""
        self._garantir_arquivo()
        with open(self.caminho, "r", encoding="utf-8") as arquivo:
            linhas = [linha.strip() for linha in arquivo if linha.strip()]

        if not linhas:
            return "Sua agenda está vazia. Nenhum evento cadastrado."

        partes = [f"Você tem {len(linhas)} evento{'s' if len(linhas) > 1 else ''} na agenda."]
        for i, linha in enumerate(linhas, start=1):
            partes.append(f"{i}. {linha}")
        return " ".join(partes)

    def limpar(self) -> str:
        """
        Item 8: apaga os DADOS sem apagar o arquivo.
        Abrir em modo "w" e fechar trunca o conteúdo para zero byte.
        """
        open(self.caminho, "w", encoding="utf-8").close()
        return "Agenda limpa. O arquivo agenda.txt continua existindo, agora vazio."

    # ------------------------------------------------------------------
    # Roteamento interno
    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        normalizado = self.normalizar_texto(texto)

        if any(p in normalizado for p in ("limpar", "apagar", "esvaziar", "zerar", "excluir")):
            return self.limpar()

        if any(p in normalizado for p in ("ler", "leia", "listar", "mostrar", "consultar", "ver ")):
            return self.ler()

        if any(p in normalizado for p in ("cadastrar", "adicionar", "anotar", "agendar", "marcar", "criar", "novo")):
            # Caso o usuário já tenha ditado o evento junto ("anota na agenda
            # prova de cálculo"), gravamos direto, sem perguntar.
            evento = self._extrair_evento_inline(normalizado)
            if evento:
                return self.adicionar(evento)

            # Item 2 na íntegra: pergunta e AGUARDA a resposta. O callback
            # abaixo recebe a próxima fala do usuário (sem exigir wake word).
            ctx.aguardar_resposta(lambda fala, _ctx: self.adicionar(fala))
            return "Ok, qual evento devo cadastrar?"

        # Só falou "agenda": mostramos o que tem.
        return self.ler()

    @staticmethod
    def _extrair_evento_inline(normalizado: str) -> str:
        """
        Tenta achar o evento na própria frase.
        "anotar na agenda reuniao com o cliente" -> "reuniao com o cliente"
        Devolve "" quando só houve o comando, sem conteúdo.
        """
        marcador = "agenda"
        posicao = normalizado.rfind(marcador)
        if posicao == -1:
            return ""
        resto = normalizado[posicao + len(marcador):].strip(" ,.:")
        for preposicao in ("que ", "de ", "o ", "a "):
            if resto.startswith(preposicao):
                resto = resto[len(preposicao):]
        return resto if len(resto.split()) >= 2 else ""

    # ------------------------------------------------------------------
    # Function calling (fallback do router)
    # ------------------------------------------------------------------
    def ferramentas(self) -> list:
        return [
            {
                "name": "agenda_adicionar",
                "description": "Grava um evento/compromisso/lembrete na agenda do usuário.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "evento": {
                            "type": "string",
                            "description": "Descrição do evento, ex: 'prova de cálculo na quinta-feira'",
                        }
                    },
                    "required": ["evento"],
                },
            },
            {
                "name": "agenda_ler",
                "description": "Lê em voz alta todos os eventos cadastrados na agenda.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "agenda_limpar",
                "description": "Apaga todos os eventos da agenda, mantendo o arquivo.",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome == "agenda_adicionar":
            return self.adicionar(argumentos.get("evento", ""))
        if nome == "agenda_ler":
            return self.ler()
        if nome == "agenda_limpar":
            return self.limpar()
        raise NotImplementedError(nome)
