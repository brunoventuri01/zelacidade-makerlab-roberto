"""
EXTRA 1 — Cotação de moedas e criptomoedas.

"Roberto, qual o valor do dólar hoje?"
"Roberto, quanto vale um bitcoin?"

API: economia.awesomeapi.com.br — gratuita, sem cadastro, sem chave.
"""

from skills.base import Skill

# Apelidos falados -> par de moedas aceito pela API.
MOEDAS = {
    "dolar": ("USD-BRL", "dólar"),
    "dolares": ("USD-BRL", "dólar"),
    "euro": ("EUR-BRL", "euro"),
    "libra": ("GBP-BRL", "libra"),
    "peso": ("ARS-BRL", "peso argentino"),
    "bitcoin": ("BTC-BRL", "bitcoin"),
    "btc": ("BTC-BRL", "bitcoin"),
    "ethereum": ("ETH-BRL", "ethereum"),
    "iene": ("JPY-BRL", "iene"),
}


class CotacaoSkill(Skill):
    nome = "cotacao"
    descricao = "Consulta a cotação atual de moedas e criptomoedas em reais."

    padroes = [
        r"\b(cotacao|valor|preco|quanto (esta|ta|vale|custa))\b.*\b(dolar|euro|libra|bitcoin|btc|ethereum|iene|peso)\b",
        r"\b(dolar|euro|bitcoin|btc|ethereum)\b.*\b(hoje|agora|cotacao)\b",
        r"\bcotacao do\b",
    ]

    URL = "https://economia.awesomeapi.com.br/json/last/"

    def consultar(self, par: str, rotulo: str) -> str:
        """Bate na API e formata o valor em reais para leitura em voz alta."""
        try:
            import requests
        except ImportError:
            return "A biblioteca requests não está instalada."

        try:
            resposta = requests.get(self.URL + par, timeout=8)
            resposta.raise_for_status()
            dados = resposta.json()[par.replace("-", "")]
            valor = float(dados["bid"])
            variacao = float(dados.get("pctChange", 0))
        except Exception as erro:
            print(f"[Cotacao] {erro}")
            return f"Não consegui consultar a cotação do {rotulo} agora."

        # Formato brasileiro: 5.432,10
        formatado = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        sentido = "de alta" if variacao >= 0 else "de queda"
        return (f"O {rotulo} está cotado a {formatado} reais, "
                f"com variação {sentido} de {abs(variacao):.2f} por cento hoje.")

    def _detectar_moeda(self, normalizado: str):
        for apelido, (par, rotulo) in MOEDAS.items():
            if apelido in normalizado:
                return par, rotulo
        return None, None

    def execute(self, texto: str, ctx) -> str:
        par, rotulo = self._detectar_moeda(self.normalizar_texto(texto))
        if not par:
            par, rotulo = "USD-BRL", "dólar"  # padrão quando não fica claro
        return self.consultar(par, rotulo)

    def ferramentas(self) -> list:
        return [{
            "name": "consultar_cotacao",
            "description": "Consulta a cotação atual de uma moeda ou criptomoeda em reais.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moeda": {
                        "type": "string",
                        "description": "Nome da moeda: dolar, euro, libra, bitcoin, ethereum, iene.",
                    }
                },
                "required": ["moeda"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "consultar_cotacao":
            raise NotImplementedError(nome)
        par, rotulo = self._detectar_moeda(self.normalizar_texto(argumentos.get("moeda", "")))
        return self.consultar(par or "USD-BRL", rotulo or "dólar")
