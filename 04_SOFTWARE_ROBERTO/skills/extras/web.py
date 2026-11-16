"""
EXTRAS 5 e 6 — Abrir coisas no navegador.

  YoutubeSkill -> "Roberto, abra o YouTube e rode um vídeo sobre buracos negros"
  WebSkill     -> "Roberto, pesquisar no Google sobre redes neurais"
                  "Roberto, abrir o portal da faculdade"

Usamos apenas a biblioteca padrão (webbrowser + urllib), então não há
dependência nova nem chave de API.
"""

import re
import webbrowser
from urllib.parse import quote_plus

from skills.base import Skill

# Atalhos nomeados. Adicione aqui os sites que o grupo usa no dia a dia.
ATALHOS = {
    "portal da faculdade": "https://on.fiap.com.br/",
    "fiap": "https://on.fiap.com.br/",
    "github": "https://github.com/",
    "gmail": "https://mail.google.com/",
    "chatgpt": "https://chat.openai.com/",
}


class YoutubeSkill(Skill):
    nome = "youtube"
    descricao = "Abre o YouTube e busca um vídeo sobre o assunto pedido."

    padroes = [
        r"\b(abrir?|abra|toc(ar|a)|rod(ar|e)|coloc(ar|a))\b.*\byoutube\b",
        r"\byoutube\b.*\b(video|musica|sobre)\b",
        r"\bprocurar? no youtube\b",
    ]

    def abrir(self, busca: str) -> str:
        if not busca:
            webbrowser.open("https://www.youtube.com/")
            return "Abri o YouTube para você."
        # O parâmetro search_query já dispara a busca na página inicial.
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(busca)}")
        return f"Abri o YouTube com os resultados para {busca}."

    @staticmethod
    def _extrair_busca(normalizado: str) -> str:
        """Pega o trecho depois de 'sobre'/'de'/'do' como termo de busca."""
        achado = re.search(r"\b(?:sobre|de|do|da|com)\s+(.+)$", normalizado)
        if achado:
            return achado.group(1).strip(" ,.?")
        # Sem conectivo: remove as palavras de comando e usa o resto.
        limpo = re.sub(r"\b(abrir|abra|abre|o|a|no|na|youtube|toque|tocar|rodar|rode|"
                       r"coloque|colocar|um|uma|video|videos|musica|por favor)\b", " ", normalizado)
        return re.sub(r"\s+", " ", limpo).strip()

    def execute(self, texto: str, ctx) -> str:
        return self.abrir(self._extrair_busca(self.normalizar_texto(texto)))

    def ferramentas(self) -> list:
        return [{
            "name": "abrir_youtube",
            "description": "Abre o YouTube já buscando por um assunto, vídeo ou música.",
            "parameters": {
                "type": "object",
                "properties": {
                    "busca": {"type": "string", "description": "O que procurar no YouTube."}
                },
                "required": ["busca"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "abrir_youtube":
            raise NotImplementedError(nome)
        return self.abrir(argumentos.get("busca", ""))


class WebSkill(Skill):
    nome = "web"
    descricao = "Pesquisa no Google e abre sites conhecidos pelo nome."

    padroes = [
        r"\b(pesquis(ar|e|a)|busc(ar|e|a)|procur(ar|e|a))\b.*\b(no google|na internet|na web)\b",
        r"\b(pesquis(ar|e|a)|google)\b",
        r"\b(abrir?|abra|acess(ar|e))\b.*\b(site|portal|pagina|github|gmail|fiap)\b",
    ]

    def pesquisar(self, termo: str) -> str:
        if not termo:
            return "O que você quer que eu pesquise?"
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(termo)}")
        return f"Pesquisando por {termo} no Google."

    def abrir_atalho(self, chave: str) -> str:
        webbrowser.open(ATALHOS[chave])
        return f"Abrindo {chave}."

    def execute(self, texto: str, ctx) -> str:
        normalizado = self.normalizar_texto(texto)

        # 1) O usuário pediu um site conhecido pelo nome?
        for chave in sorted(ATALHOS, key=len, reverse=True):
            if chave in normalizado:
                return self.abrir_atalho(chave)

        # 2) Caso contrário, tratamos como busca no Google.
        #    Removemos o verbo de comando e, em seguida, TODOS os conectivos
        #    encadeados do início ("no google sobre ..." -> "...").
        #    Os \b são essenciais: sem eles, o "a" solto casaria com o "a" de
        #    "abrir" e a busca sairia truncada.
        termo = re.sub(r"^.*?\b(?:pesquis\w*|busc\w*|procur\w*|google)\b", "", normalizado)
        termo = re.sub(r"^(?:\s*\b(?:no google|na internet|na web|sobre|por|o|a)\b)+\s*", "", termo)
        return self.pesquisar(termo.strip(" ,.?"))

    def ferramentas(self) -> list:
        return [{
            "name": "pesquisar_web",
            "description": "Faz uma busca no Google no navegador padrão.",
            "parameters": {
                "type": "object",
                "properties": {"termo": {"type": "string", "description": "O que pesquisar."}},
                "required": ["termo"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "pesquisar_web":
            raise NotImplementedError(nome)
        return self.pesquisar(argumentos.get("termo", ""))
