"""
Utilidades de áudio compartilhadas entre o Listener (microfone) e o Speaker (voz).
"""

import contextlib
import os
import sys


@contextlib.contextmanager
def silenciar_stderr_nativo(ativo: bool = True):
    """
    Silencia mensagens que o ALSA e o JACK cospem direto no descritor 2.

    No Linux, abrir o microfone ou a saída de áudio imprime dezenas de linhas
    do tipo "ALSA lib pcm.c ... Unknown PCM cards.pcm.rear" e
    "jack server is not running". São AVISOS, não erros: o áudio funciona.
    Mas elas vêm da camada C das bibliotecas, então nem sys.stderr do Python
    nem try/except conseguem interceptar — a única saída é redirecionar o
    descritor de arquivo do sistema operacional.

    Numa demo ao vivo isso é essencial: sem o silenciamento, cada frase gera
    uma tela de log e ninguém enxerga a resposta da assistente.

    Use ativo=False (flag --debug-audio) quando estiver investigando um
    problema de áudio de verdade e precisar ver essas mensagens.
    """
    if not ativo:
        yield
        return

    devnull = os.open(os.devnull, os.O_WRONLY)
    copia_stderr = os.dup(2)
    try:
        sys.stderr.flush()
        os.dup2(devnull, 2)     # tudo que for para o fd 2 cai no /dev/null
        yield
    finally:
        # O finally garante que o stderr volta mesmo se algo lançar exceção.
        os.dup2(copia_stderr, 2)
        os.close(copia_stderr)
        os.close(devnull)
