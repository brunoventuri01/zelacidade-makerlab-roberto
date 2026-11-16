"""
CalculatorSkill — item 6 do enunciado.

"Roberto, calcular 12 mais 8 vezes 3" -> "O resultado é 36."

SEGURANÇA: nunca usamos eval(). eval("__import__('os').system('rm -rf /')")
executaria de verdade. Em vez disso:

  1. traduzimos as palavras ("mais", "vezes", "dividido por") em operadores;
  2. fazemos ast.parse() da expressão resultante;
  3. percorremos a árvore permitindo APENAS nós aritméticos (whitelist).

Qualquer coisa fora da whitelist (nome, chamada de função, atributo) levanta
erro e a expressão é rejeitada. Se ainda assim não der para resolver, a skill
pede socorro ao LLM, que devolve a expressão em JSON — e ela passa pelo mesmo
avaliador seguro.
"""

import ast
import json
import math
import operator
import re

from core.text_utils import substituir_numeros_por_extenso
from skills.base import Skill

# Whitelist de operações. Nada além disso é executável.
OPERACOES_BINARIAS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
OPERACOES_UNARIAS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

# Funções matemáticas permitidas. A lista é fechada e mapeada na mão: só estes
# nomes viram chamada. Continua não existindo eval() nem acesso a atributo, então
# "os.system" ou "__import__" seguem impossíveis de expressar.
# Necessário porque o LLM devolve "sqrt(144)" quando pedimos a expressão em JSON.
FUNCOES = {
    "sqrt": math.sqrt, "raiz": math.sqrt, "abs": abs, "round": round,
    "pow": pow, "log": math.log, "log10": math.log10, "exp": math.exp,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "floor": math.floor, "ceil": math.ceil,
}
CONSTANTES = {"pi": math.pi, "e": math.e}

# Tradução fala -> símbolo. A ordem importa: expressões maiores primeiro,
# senão "dividido" casaria antes de "dividido por".
TRADUCOES = [
    (r"\belevado a\b", "**"),
    (r"\belevado ao quadrado\b", "**2"),
    (r"\bdividido por\b", "/"),
    (r"\bdividido pra\b", "/"),
    (r"\bdividir por\b", "/"),
    (r"\bmultiplicado por\b", "*"),
    (r"\bmultiplicar por\b", "*"),
    (r"\bresto de\b", "%"),
    (r"\bmodulo\b", "%"),
    (r"\bmais\b", "+"),
    (r"\bsomar?\b", "+"),
    (r"\bcom\b", "+"),
    (r"\bmenos\b", "-"),
    (r"\bsubtrair\b", "-"),
    (r"\bvezes\b", "*"),
    (r"\bpor\b", "*"),
    (r"\bsobre\b", "/"),
    (r"\bdividido\b", "/"),
    (r"\babre parenteses\b", "("),
    (r"\bfecha parenteses\b", ")"),
    (r"\bvirgula\b", "."),
    (r"\bponto\b", "."),
]


class CalculatorSkill(Skill):
    nome = "calculadora"
    descricao = "Resolve contas de adição, subtração, multiplicação e divisão."

    # Cuidado com gatilhos genéricos: "quanto vale um bitcoin?" NÃO é conta.
    # Por isso o "quanto é/vale" só dispara quando há um operador na frase.
    OPERADORES_FALADOS = (r"(mais|menos|vezes|dividido|dividir|multiplicado|"
                          r"multiplicar|somado|somar|subtrair|elevado|quadrado|raiz)")

    padroes = [
        r"\bcalcul(ar|e|a)\b",
        r"\bresultado de\b",
        r"\bquanto (e|eh|da|sao|vale)\b.*\b" + OPERADORES_FALADOS + r"\b",
        r"\bquanto (e|eh|sao)\b.*\d\s*[\+\*/%]",
        r"\bsom(ar|e)\b",
        r"\bmultiplic(ar|a|ue)\b",
        r"\bdivid(ir|a)\b",
        r"\bsubtrai(r)?\b",
        r"\d+\s*[\+\-\*/x]\s*\d+",
    ]

    LIMITE = 10 ** 15  # trava contra "9 elevado a 9 elevado a 9" travar a demo

    # ------------------------------------------------------------------
    # Tradução da fala para expressão matemática
    # ------------------------------------------------------------------
    def traduzir(self, texto: str) -> str:
        """Converte a fala em uma string de expressão aritmética."""
        expressao = self.normalizar_texto(texto)

        # Remove o verbo de comando ("calcular", "quanto é"...) do começo.
        expressao = re.sub(
            r"^(calcular|calcule|calcula|quanto e|quanto eh|quanto da|quanto vale|"
            r"resultado de|me diga|diga|qual e|qual eh)\s+", "", expressao)

        expressao = substituir_numeros_por_extenso(expressao)  # "dois" -> "2"

        for padrao, simbolo in TRADUCOES:
            expressao = re.sub(padrao, simbolo, expressao)

        expressao = expressao.replace("x", "*").replace("÷", "/").replace(",", ".")
        # Sobrou apenas o que compõe uma expressão válida.
        expressao = re.sub(r"[^0-9\.\+\-\*/%\(\)\s]", " ", expressao)
        return re.sub(r"\s+", "", expressao)

    # ------------------------------------------------------------------
    # Avaliador seguro (substituto do eval)
    # ------------------------------------------------------------------
    def avaliar(self, expressao: str) -> float:
        """Parseia e resolve a expressão percorrendo a AST com whitelist."""
        if not expressao:
            raise ValueError("expressão vazia")
        arvore = ast.parse(expressao, mode="eval")
        return self._resolver(arvore.body)

    def _resolver(self, no):
        """Visita recursiva. Qualquer nó fora da whitelist é recusado."""
        if isinstance(no, ast.Constant):
            if isinstance(no.value, bool) or not isinstance(no.value, (int, float)):
                raise ValueError("constante não numérica")
            return no.value

        if isinstance(no, ast.BinOp) and type(no.op) in OPERACOES_BINARIAS:
            esquerda = self._resolver(no.left)
            direita = self._resolver(no.right)
            if type(no.op) in (ast.Div, ast.FloorDiv, ast.Mod) and direita == 0:
                raise ZeroDivisionError
            if type(no.op) is ast.Pow and (abs(direita) > 100 or abs(esquerda) > 10 ** 6):
                raise ValueError("expoente grande demais")
            return OPERACOES_BINARIAS[type(no.op)](esquerda, direita)

        if isinstance(no, ast.UnaryOp) and type(no.op) in OPERACOES_UNARIAS:
            return OPERACOES_UNARIAS[type(no.op)](self._resolver(no.operand))

        # Constante nomeada: pi, e
        if isinstance(no, ast.Name) and no.id in CONSTANTES:
            return CONSTANTES[no.id]

        # Chamada de função — só as da whitelist, e só com argumentos simples.
        # func precisa ser um Name puro: isso barra "math.system" ou "().__class__".
        if (isinstance(no, ast.Call) and isinstance(no.func, ast.Name)
                and no.func.id in FUNCOES and not no.keywords):
            argumentos = [self._resolver(arg) for arg in no.args]
            if len(argumentos) > 2:
                raise ValueError("argumentos demais")
            return FUNCOES[no.func.id](*argumentos)

        raise ValueError(f"operação não permitida: {type(no).__name__}")

    @staticmethod
    def formatar(resultado: float) -> str:
        """9.0 -> '9'; 3.3333333 -> '3,33' (vírgula porque a voz é pt-BR)."""
        if isinstance(resultado, float) and resultado.is_integer():
            return str(int(resultado))
        return f"{round(resultado, 4)}".replace(".", ",")

    # ------------------------------------------------------------------
    def execute(self, texto: str, ctx) -> str:
        expressao = self.traduzir(texto)
        try:
            resultado = self.avaliar(expressao)
            if abs(resultado) > self.LIMITE:
                return "O resultado é grande demais para eu falar."
            return f"O resultado de {self._falar_expressao(expressao)} é {self.formatar(resultado)}."
        except ZeroDivisionError:
            return "Não é possível dividir por zero."
        except Exception:
            # Plano B: a expressão era complexa demais para as regras acima.
            # Pedimos ao LLM que a traduza em JSON e reavaliamos com segurança.
            return self._resolver_com_llm(texto, ctx)

    def _resolver_com_llm(self, texto: str, ctx) -> str:
        if not (ctx.llm and ctx.llm.disponivel):
            return "Não consegui entender a conta. Tente, por exemplo: calcular 12 vezes 3."

        resposta = ctx.llm.conversar(
            [
                {"role": "system", "content":
                 "Converta o pedido de cálculo em uma expressão matemática Python válida, "
                 "usando apenas números e os operadores + - * / ( ) ** %. "
                 'Responda SOMENTE com JSON no formato {"expressao": "..."}. '
                 'Se não for um cálculo, responda {"expressao": ""}.'},
                {"role": "user", "content": texto},
            ],
            temperatura=0,
            max_tokens=80,
        )
        try:
            bruto = re.search(r"\{.*\}", resposta, re.S).group(0)
            expressao = json.loads(bruto).get("expressao", "")
            resultado = self.avaliar(expressao)
            return f"O resultado é {self.formatar(resultado)}."
        except ZeroDivisionError:
            return "Não é possível dividir por zero."
        except Exception:
            return "Não consegui entender a conta. Tente, por exemplo: calcular 12 vezes 3."

    @staticmethod
    def _falar_expressao(expressao: str) -> str:
        """Deixa a expressão legível na fala: '12*3' -> '12 vezes 3'."""
        legivel = expressao
        for simbolo, palavra in (("+", " mais "), ("-", " menos "),
                                 ("*", " vezes "), ("/", " dividido por ")):
            legivel = legivel.replace(simbolo, palavra)
        return re.sub(r"\s+", " ", legivel).strip()

    # ------------------------------------------------------------------
    def ferramentas(self) -> list:
        return [{
            "name": "calcular",
            "description": "Resolve uma expressão matemática (soma, subtração, multiplicação, divisão).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expressao": {
                        "type": "string",
                        "description": "Expressão em notação matemática, ex: '(12+8)*3'",
                    }
                },
                "required": ["expressao"],
            },
        }]

    def executar_ferramenta(self, nome: str, argumentos: dict, ctx) -> str:
        if nome != "calcular":
            raise NotImplementedError(nome)
        try:
            return f"O resultado é {self.formatar(self.avaliar(argumentos.get('expressao', '')))}."
        except ZeroDivisionError:
            return "Não é possível dividir por zero."
        except Exception:
            return "Não consegui resolver essa conta."
