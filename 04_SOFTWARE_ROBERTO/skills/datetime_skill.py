"""
DateTimeSkill — itens 4 e 5 do enunciado.

  4) "Que horas são?"  -> fala a hora atual
  5) "Que dia é hoje?" -> fala a data atual por extenso

Armadilha evitada: locale pt-BR (`locale.setlocale(LC_TIME, "pt_BR.UTF-8")`)
falha em muita máquina porque o locale não está gerado no sistema. Em vez de
depender disso, usamos dicionários próprios de dias e meses — funciona igual
em Windows, Linux e macOS.
"""

from datetime import datetime

from skills.base import Skill

DIAS_SEMANA = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


class DateTimeSkill(Skill):
    nome = "data_hora"
    descricao = "Informa a hora atual e a data de hoje."

    padroes = [
        r"\bque horas\b",
        r"\bhoras sao\b",
        r"\bhora (atual|certa)\b",
        r"\bme (diga|fala|diz) as horas\b",
        r"\bque dia (e|eh) hoje\b",
        r"\bdata de hoje\b",
        r"\bdia atual\b",
        r"\bqual (e |eh )?a data\b",
        r"\bque dia da semana\b",
    ]

    # ------------------------------------------------------------------
    def hora_atual(self, agora: datetime = None) -> str:
        """Item 4: hora falada de forma natural ('são 14 horas e 5 minutos')."""
        agora = agora or datetime.now()
        hora, minuto = agora.hour, agora.minute
        if minuto == 0:
            return f"Agora são exatamente {hora} horas."
        return f"Agora são {hora} horas e {minuto} minuto{'s' if minuto > 1 else ''}."

    def data_atual(self, agora: datetime = None) -> str:
        """Item 5: data por extenso, sem depender de locale do sistema."""
        agora = agora or datetime.now()
        dia_semana = DIAS_SEMANA[agora.weekday()]   # weekday(): 0 = segunda
        mes = MESES[agora.month - 1]
        return f"Hoje é {dia_semana}, {agora.day} de {mes} de {agora.year}."

    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        normalizado = self.normalizar_texto(texto)
        pediu_hora = "hora" in normalizado
        pediu_data = any(p in normalizado for p in ("dia", "data", "semana"))

        if pediu_hora and pediu_data:
            return f"{self.data_atual()} {self.hora_atual()}"
        if pediu_hora:
            return self.hora_atual()
        return self.data_atual()

    # ------------------------------------------------------------------
    def ferramentas(self) -> list:
        return [
            {
                "name": "obter_hora",
                "description": "Retorna a hora atual do sistema.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "obter_data",
                "description": "Retorna a data de hoje, incluindo o dia da semana.",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome == "obter_hora":
            return self.hora_atual()
        if nome == "obter_data":
            return self.data_atual()
        raise NotImplementedError(nome)
