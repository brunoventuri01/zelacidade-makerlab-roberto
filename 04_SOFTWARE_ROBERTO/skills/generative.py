"""
GenerativeSkill — item 9 do enunciado.

É o fallback final do router: quando nenhuma regex e nenhuma ferramenta
atendem, a fala vira uma conversa com o modelo de IA generativa.

Duas decisões de projeto:
  - persona curta no system prompt (respostas faladas precisam ser curtas,
    ninguém quer ouvir 3 parágrafos no TTS);
  - memória das últimas ~6 mensagens, para "e o segundo?" fazer sentido
    depois de "quem foi o primeiro presidente do Brasil?".
"""

from skills.base import Skill

PERSONA = (
    "Você é Roberto, robô inteligente CP5 desenvolvido por estudantes de Engenharia de Software "
    "como projeto universitário. Usa microfone, webcam e alto-falantes do computador, "
    "um braço SG90 e um LED. Nunca afirme ter executado ações físicas: somente o controlador "
    "pode confirmá-las. Não invente o que vê sem receber uma imagem. "
    "Fale português brasileiro. Seja objetivo, cordial e levemente "
    "espirituosa. Suas respostas serão FALADAS em voz alta: use no máximo 3 "
    "frases, sem listas, sem markdown, sem emojis. Se não souber algo, diga que "
    "não sabe em vez de inventar."
)


class GenerativeSkill(Skill):
    nome = "conversa"
    descricao = "Conversa livre e perguntas gerais usando IA generativa."

    # Gatilhos explícitos; além disso, esta skill é o fallback final do router.
    padroes = [
        r"\b(pergunt(a|ar) para|conversar|me explique|explica|o que (e|eh))\b",
        r"\bme (conte|fale|diga) (sobre|uma)\b",
        r"\bqual (e|eh) (a|o) (sentido|melhor|maior)\b",
    ]

    def __init__(self, llm=None, tamanho_historico: int = 6):
        super().__init__()
        self.llm = llm
        self.tamanho_historico = tamanho_historico
        self.historico = []  # [{"role": "user"/"assistant", "content": "..."}]

    def _montar_mensagens(self, pergunta: str) -> list:
        """System prompt + janela deslizante do histórico + a pergunta atual."""
        mensagens = [{"role": "system", "content": PERSONA}]
        mensagens.extend(self.historico[-self.tamanho_historico:])
        mensagens.append({"role": "user", "content": pergunta})
        return mensagens

    def responder(self, pergunta: str, ctx=None) -> str:
        llm = self.llm or (ctx.llm if ctx else None)
        if not (llm and llm.disponivel):
            return ("Não entendi esse comando e estou sem acesso à IA generativa. "
                    "Confira se a IA local do Roberto está iniciada.")

        resposta = llm.conversar(self._montar_mensagens(pergunta))
        if not resposta:
            return "Não consegui falar com a IA agora. Tente de novo em instantes."

        # Guarda o par pergunta/resposta para dar contexto à próxima fala.
        self.historico.append({"role": "user", "content": pergunta})
        self.historico.append({"role": "assistant", "content": resposta})
        self.historico = self.historico[-2 * self.tamanho_historico:]
        return resposta

    def execute(self, texto: str, ctx) -> str:
        return self.responder(texto, ctx)

    def limpar_historico(self) -> None:
        """Zera a memória da conversa (útil entre demos)."""
        self.historico.clear()
