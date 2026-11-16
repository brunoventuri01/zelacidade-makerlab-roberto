"""
Roteador de comandos: decide QUEM executa a fala do usuário.

Estratégia em três camadas (da mais barata para a mais cara):

  1. Regex   -> instantâneo, offline, determinístico. Cobre as frases previstas.
  2. LLM com function calling -> quando a regex falha, o modelo recebe o
     catálogo de skills e escolhe qual chamar. É isso que faz
     "Roberto, anota aí que tenho prova de cálculo quinta" cair na agenda
     mesmo sem ninguém ter escrito essa regex.
  3. Conversa livre -> nada casou, a GenerativeSkill responde (item 9).
"""

from core.text_utils import normalizar


class CommandRouter:
    """Recebe a lista de skills e roteia cada comando para a certa."""

    # Uma fala com menos palavras que isto e que não casou com nenhuma regex é,
    # quase sempre, ruído mal transcrito ("temperatura", "ahn", "ok"). Mandar
    # isso para o LLM gera resposta aleatória e gasta chamada à toa.
    MINIMO_PALAVRAS_PARA_LLM = 2

    def __init__(self, skills: list, llm=None, skill_conversa=None, usar_llm_router: bool = True):
        self.skills = skills
        self.llm = llm
        self.skill_conversa = skill_conversa      # fallback final (GenerativeSkill)
        self.usar_llm_router = usar_llm_router
        self._catalogo, self._dono = self._montar_catalogo()

    def _montar_catalogo(self):
        """
        Junta as ferramentas declaradas por todas as skills e guarda um mapa
        nome_da_ferramenta -> skill dona, para despachar a chamada depois.
        """
        catalogo, dono = [], {}
        for skill in self.skills:
            for ferramenta in skill.ferramentas():
                catalogo.append(ferramenta)
                dono[ferramenta["name"]] = skill
        return catalogo, dono

    def route(self, texto: str, ctx) -> str:
        """Devolve a resposta da skill escolhida (string que a Roberto vai falar)."""
        normalizado = normalizar(texto)
        if not normalizado:
            return ""

        # --- Camada 1: regex ------------------------------------------------
        for skill in self.skills:
            if skill.matches(normalizado):
                print(f"[Router] regex -> {skill.nome}")
                return skill.execute(texto, ctx)

        # --- Portão anti-ruído ----------------------------------------------
        # Nenhuma regex casou. Antes de gastar uma chamada de LLM, checamos se
        # a fala tem substância: uma palavra solta é quase sempre transcrição
        # ruim de barulho da sala, não um pedido de verdade.
        if len(normalizado.split()) < self.MINIMO_PALAVRAS_PARA_LLM:
            print(f"[Router] descartado (ruído provável): {normalizado!r}")
            return "Não entendi. Pode repetir?"

        # --- Camada 2: function calling -------------------------------------
        if self.usar_llm_router and self.llm and self.llm.disponivel and self._catalogo:
            nome, argumentos = self.llm.escolher_ferramenta(texto, self._catalogo)
            # Uma transcricao ruim nao deve virar alteracao de volume/navegacao
            # so porque o classificador escolheu uma ferramenta por engano.
            pistas = {
                'ajustar_volume': ('volume', 'som', 'audio'),
                'tirar_print': ('print', 'captur', 'screenshot'),
                'abrir_youtube': ('youtube', 'video'),
                'pesquisar_web': ('pesquis', 'busc', 'google', 'site', 'portal', 'naveg'),
            }
            if nome in pistas and not any(p in normalizado for p in pistas[nome]):
                return 'Não entendi esse pedido com segurança. Pode repetir chamando Roberto?'
            skill = self._dono.get(nome) if nome else None
            if skill:
                print(f"[Router] function calling -> {nome} {argumentos}")
                try:
                    return skill.executar_ferramenta(nome, argumentos or {}, ctx)
                except Exception as erro:
                    print(f"[Router] Falha ao executar {nome}: {erro}")

        # --- Camada 3: conversa livre ---------------------------------------
        if self.skill_conversa:
            print("[Router] fallback -> conversa (LLM)")
            return self.skill_conversa.execute(texto, ctx)

        return "Desculpe, não entendi esse comando."
