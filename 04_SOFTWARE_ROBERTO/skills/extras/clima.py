"""
EXTRA 2 — Previsão do tempo.

"Roberto, qual a previsão do tempo para São Paulo?"

APIs: Open-Meteo (previsão) + Open-Meteo Geocoding (nome da cidade ->
latitude/longitude). Ambas gratuitas e sem chave de API.
"""

import re

from skills.base import Skill

# Códigos WMO devolvidos pela Open-Meteo, traduzidos para fala natural.
CONDICOES = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado",
    3: "encoberto", 45: "com névoa", 48: "com névoa congelante",
    51: "com garoa fraca", 53: "com garoa", 55: "com garoa forte",
    61: "com chuva fraca", 63: "com chuva", 65: "com chuva forte",
    71: "com neve fraca", 73: "com neve", 75: "com neve forte",
    80: "com pancadas de chuva", 81: "com pancadas de chuva",
    82: "com pancadas fortes de chuva", 95: "com trovoadas",
    96: "com trovoada e granizo", 99: "com trovoada e granizo forte",
}


class ClimaSkill(Skill):
    nome = "clima"
    descricao = "Informa a previsão do tempo de uma cidade."

    padroes = [
        r"\b(previsao do tempo|previsao)\b",
        r"\bcomo (esta|ta) o tempo\b",
        r"\btempo (em|para|de|no|na)\b",
        r"\b(vai|ta|esta) chove(r|ndo)\b",
        r"\bqual a temperatura\b",
        r"\bclima (em|de|para)\b",
    ]

    URL_GEO = "https://geocoding-api.open-meteo.com/v1/search"
    URL_CLIMA = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, cidade_padrao: str = "São Paulo"):
        super().__init__()
        self.cidade_padrao = cidade_padrao

    # ------------------------------------------------------------------
    def _geocodificar(self, requests, cidade: str):
        """Converte o nome da cidade em coordenadas."""
        resposta = requests.get(
            self.URL_GEO,
            params={"name": cidade, "count": 1, "language": "pt", "country": "BR"},
            timeout=8,
        )
        resposta.raise_for_status()
        resultados = resposta.json().get("results")
        if not resultados:
            return None
        lugar = resultados[0]
        return lugar["latitude"], lugar["longitude"], lugar["name"]

    def consultar(self, cidade: str) -> str:
        try:
            import requests
        except ImportError:
            return "A biblioteca requests não está instalada."

        try:
            local = self._geocodificar(requests, cidade)
            if not local:
                return f"Não encontrei a cidade {cidade}."
            latitude, longitude, nome = local

            resposta = requests.get(
                self.URL_CLIMA,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,weather_code",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "America/Sao_Paulo",
                    "forecast_days": 1,
                },
                timeout=8,
            )
            resposta.raise_for_status()
            dados = resposta.json()
        except Exception as erro:
            print(f"[Clima] {erro}")
            return "Não consegui consultar a previsão do tempo agora."

        atual = dados["current"]
        diario = dados["daily"]
        condicao = CONDICOES.get(atual["weather_code"], "com tempo instável")
        return (
            f"Em {nome} agora estão {atual['temperature_2m']:.0f} graus, {condicao}, "
            f"e umidade de {atual['relative_humidity_2m']:.0f} por cento. "
            f"Hoje a máxima é de {diario['temperature_2m_max'][0]:.0f} e a mínima de "
            f"{diario['temperature_2m_min'][0]:.0f} graus, com "
            f"{diario['precipitation_probability_max'][0]:.0f} por cento de chance de chuva."
        )

    # ------------------------------------------------------------------
    # Palavras que aparecem no comando mas nunca são o nome da cidade.
    RUIDO = r"\b(hoje|agora|amanha|de manha|a tarde|a noite|por favor|roberto|" \
            r"tempo|clima|previsao|temperatura|semana)\b"

    def _extrair_cidade(self, texto: str) -> str:
        """
        Pega o nome da cidade depois da preposição.

        Detalhe que quebra a ingenuidade: em "previsão do tempo PARA São Paulo"
        existem DUAS preposições ("do" e "para"). Pegar a primeira devolveria
        "tempo para são paulo". Por isso priorizamos as preposições fortes
        (em/para/pra) e, entre elas, a ÚLTIMA — mas usamos a PRIMEIRA das
        fracas (de/do/da/no/na) para não quebrar "Rio de Janeiro".
        """
        normalizado = self.normalizar_texto(texto)

        fortes = list(re.finditer(r"\b(?:em|para|pra)\s+", normalizado))
        if fortes:
            cidade = normalizado[fortes[-1].end():]
        else:
            fraca = re.search(r"\b(?:de|do|da|no|na)\s+", normalizado)
            if not fraca:
                return self.cidade_padrao
            cidade = normalizado[fraca.end():]

        cidade = re.sub(self.RUIDO, " ", cidade)
        cidade = re.sub(r"^\s*(o|a|os|as)\s+", "", cidade)   # "o rio de janeiro"
        cidade = re.sub(r"\s+", " ", cidade).strip(" ,.?")
        return cidade or self.cidade_padrao

    def execute(self, texto: str, ctx) -> str:
        return self.consultar(self._extrair_cidade(texto))

    def ferramentas(self) -> list:
        return [{
            "name": "consultar_clima",
            "description": "Consulta a previsão do tempo e temperatura de uma cidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {"type": "string", "description": "Nome da cidade, ex: 'São Paulo'"}
                },
                "required": ["cidade"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "consultar_clima":
            raise NotImplementedError(nome)
        return self.consultar(argumentos.get("cidade") or self.cidade_padrao)
