# ROBERTO | ROBÔ INTELIGENTE CP5

Aplicação local baseada em https://github.com/jzampieri/cp_04_iot . A base de habilidades foi preservada e atualizada para Roberto. As alterações estão nesta cópia local; nada foi enviado ao GitHub.

## Iniciar e testar

Dê dois cliques em **INICIAR_ROBERTO.bat**. Há um atalho desse arquivo também na pasta superior `CP6 e GS makerlab`. O inicializador sobe a IA local e o painel automaticamente e abre o navegador em http://127.0.0.1:8765 . Executar novamente reabre o painel existente, sem criar outra instância.

O modo inicial é **SIMULAÇÃO**, sem Arduino. Microfone e câmera iniciam automaticamente. O painel informa quando o Whisper terminou de carregar e a IA está disponível. O primeiro carregamento da IA pode demorar cerca de um minuto neste computador; respostas seguintes são bem mais rápidas.

Experimente uma frase por vez e aguarde terminar a resposta:

- Roberto, levante o braço.
- Roberto, abaixe o braço.
- Roberto, acenda a luz.
- Roberto, apague a luz.
- Roberto, me cumprimente.
- Roberto, qual é o seu nome?
- Roberto, quem criou você?
- Roberto, o que você está vendo?
- Roberto, me explique o que é inteligência artificial.
- Roberto, calcular dois mais três.
- Roberto, que horas são?
- Roberto, cadastrar evento na agenda.

Também funciona dizer somente **“Roberto!”**, aguardar **“Oi, estou ouvindo!”**, e dar um comando nos sete segundos seguintes. Esse tempo começa depois da resposta falada, e é configurável no painel entre 2 e 30 segundos. Pequenas pausas na mesma frase são aceitas pelo detector; se uma pausa separar a chamada do comando, a janela atende à continuação. Depois de executar o pedido, o nome volta a ser obrigatório, exceto quando uma habilidade pede uma resposta, como agenda e cadastro facial.

Use **Pausar microfone** para parar a captura. O texto e os botões continuam disponíveis. Durante a fala do Roberto o áudio de entrada é descartado e a fila é esvaziada; espere terminar a resposta para falar. Não há interrupção de fala por voz nesta revisão.

Use **Encerrar Roberto** no painel para parar a aplicação e liberar câmera/microfone. Fechar a aba do navegador não encerra o processo. O motor local de IA pode continuar em segundo plano, com o modelo descarregado após 20 minutos de inatividade.

## Recursos locais

| Recurso | Implementação |
|---|---|
| Detecção de fala | WebRTC VAD com filtro de energia e final de fala de 1 segundo |
| Transcrição | Whisper small multilíngue via faster-whisper, idioma português, CPU INT8 |
| Palavra de ativação | Token exato “Roberto”, com saudações curtas opcionais; sem aliases fonéticos |
| IA e interpretação de webcam | Gemma 3 4B, Ollama local, GPU NVIDIA quando disponível |
| Voz padrão | Piper Cadu medium, masculina, português brasileiro, aprovada no teste auditivo do usuário |
| Painel | FastAPI em 127.0.0.1:8765; somente acesso local |
| IA local | Ollama portátil em 127.0.0.1:11435, modelos guardados nesta pasta |
| Arduino | Serial USB, comandos com identificador e confirmação correspondente |

Não é um detector dedicado de wake word: o áudio passa pelo VAD e pelo reconhecedor, e só depois o nome é verificado. Não há exigência de entonação, mas ruído, distância e erros de transcrição ainda podem afetar a precisão. O prompt da transcrição não sugere “Roberto”, para reduzir confusão com “Roberta”.

Nenhum áudio ou imagem é enviado para APIs externas no modo local. A webcam usa a imagem em memória para a análise pedida. A escuta cotidiana não grava arquivos de áudio. O histórico de conversa fica em memória. Os ensaios automáticos deixaram frases sintetizadas em `data/testes_audio`, sem gravações de fala humana.

**Clima, cotação, buscas e YouTube** preservam as integrações anteriores e precisam de internet. As funções de reconhecimento de fala, nome, diálogo com a IA, análise de imagem, voz, agenda, calculadora e simulação funcionam com os modelos já instalados, sem APIs de nuvem.

## Dispositivos deste computador

Na configuração realizada, o Windows apresentou **HyperX QuadCast** como microfone padrão e **JBL Quantum 950** como saída padrão. A câmera de índice 0 abriu corretamente em 640 × 480. O aplicativo usa os padrões locais, sem mudar configurações globais do Windows. Em outro notebook, usará os dispositivos desse notebook. O painel permite alterar o índice da webcam.

Se precisar escolher um microfone específico, altere `dispositivo_microfone` em `config_roberto.json` para o índice PortAudio desejado e reinicie o Roberto. O campo `dispositivo_saida` aceita índice ou nome de dispositivo do sounddevice para a voz Piper. Nomes completos são preferíveis a índices, que podem mudar ao conectar acessórios. `null` usa o padrão.

## Configuração

`config_roberto.json` contém nome, título, intervalo da janela, modo de simulação, câmera, modelo de voz e endereços locais. O botão de configurações salva janela, voz ligada/desligada e câmera. O arquivo `.env` configura os caminhos legados de LLM, STT e TTS; não contém nenhuma chave de API nesta instalação.

O motor padrão é `piper`, com `modelo_voz=models/piper/pt_BR-cadu-medium.onnx` e `ritmo_voz=1.0`. A voz inicial do Windows e a voz Piper Faber foram substituídas após avaliação auditiva; os modelos Faber e Jeff baixados para comparação não são usados pela aplicação.

Modelos e ambiente virtual estão em `.gitignore`. Não inclua os vários GB de modelos em um commit. A pasta `.venv` pertence a este computador e não é portátil: em outra máquina, recrie-a e instale as dependências. O projeto tem 32 GB de RAM e foi testado aqui com RTX 4060 Ti de 8 GB; em máquinas menores, o desempenho muda.

## Recriar o ambiente em outro Windows

Com Python 3.12 instalado, na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/preparar_local.py all
```

O script baixa Ollama portátil, Whisper small e a voz Cadu. Na primeira configuração, baixe também a IA com o Ollama usando o diretório local de modelos:

```powershell
$env:OLLAMA_HOST='127.0.0.1:11435'
$env:OLLAMA_MODELS=Join-Path (Get-Location) 'models\ollama'
.\runtime\ollama\ollama.exe serve
```

Em outra janela PowerShell, com a mesma variável OLLAMA_HOST:

```powershell
$env:OLLAMA_HOST='127.0.0.1:11435'
.\runtime\ollama\ollama.exe pull gemma3:4b
```

Depois disso, use o arquivo BAT normalmente. Estes passos **já foram executados neste computador**; não precisam ser repetidos agora. O arquivo `requirements-local.lock.txt`, ignorado no Git, registra as versões instaladas. PyAV está limitado a versões anteriores a 17 porque a versão 19 removeu um argumento ainda usado pelo faster-whisper 1.2.

## Arduino — etapa futura

O firmware está em `firmware/Roberto/Roberto.ino`, para Uno R3/Nano clássico ATmega328P de 5 V. Servo: sinal D9, positivo 5V, negativo GND. Conforme solicitado, o LED fica entre D6 (+) e GND (-), **sem resistor externo**, limitado pelo resistor interno via `INPUT_PULLUP`: o brilho será muito fraco e pode não servir para uma apresentação iluminada. D6 nunca deve ser configurado como OUTPUT/HIGH nessa montagem. Para brilho normal, é necessário resistor externo ou módulo com resistor integrado. A opção solicitada usa USB como única alimentação; a corrente do SG90 deve ser validada sob carga. Se houver reinicializações, o conjunto não está sustentando o motor nessa alimentação. Não foi testado sem Arduino físico disponível.

Calibre os ângulos do servo **sem o braço instalado** antes de usar no robô. O firmware usa inicialmente um curso conservador de 45° e movimento gradual. A montagem e o sentido real podem exigir alteração de `ANGULO_BAIXO` e `ANGULO_ALTO`.

Após gravar o firmware, conecte a porta no painel. São enviados `ARM_UP`, `ARM_DOWN`, `LED_ON`, `LED_OFF` e `WAVE` em JSON por linha, com `id`. O firmware retorna esse mesmo `id` e `ok` depois de aplicar o comando. Sem ACK não há confirmação falada de sucesso; a ação pode ter ocorrido sem resposta. ACK confirma o programa do Arduino, **não a posição física**, pois não há sensor.

## Funções preservadas

Continuam no repositório e são acessíveis pelo roteador: agenda, data/hora, calculadora, cadastro e reconhecimento facial LBPH, clima, cotação, jogo da velha, captura de tela, volume e navegação. As habilidades faciais usam a imagem compartilhada do próprio painel, sem abrir outra janela ou disputar a câmera. O reconhecimento facial depende de cadastro/treino com pessoas reais; o painel não cadastra ninguém automaticamente.

`main.py` continua oferecendo o modo de terminal anterior (`--texto`, `--sem-voz`, etc.), agora com nome Roberto e opções locais. O ponto de entrada recomendado para o uso solicitado é **INICIAR_ROBERTO.bat**, que abre o painel e inclui os comandos físicos/simulação e a janela de ativação.

## Testes e diagnóstico

- `python -m pytest -q`: testes automatizados de roteamento, janela, bloqueio de própria fala, simulação, agenda/calculadora e confirmação serial com transporte simulado.
- `python tools/teste_local_real.py`: usa microfone real, voz local, arquivos sintetizados para STT, IA local e webcam. Rode com o painel encerrado, para não disputar microfone/câmera.
- `data/diagnostico_local.json`: resultados detalhados da última execução. A revisão de um teste pode manter uma falha antiga nesse arquivo; consulte também `TESTES_ROBERTO.md`.
- `data/logs/painel.log` e `data/logs/roberto.log`: diagnóstico do aplicativo. Falas comuns não são registradas em texto nos logs; as últimas falas aceitas aparecem no painel durante a sessão.

Referências: [repositório de origem](https://github.com/jzampieri/cp_04_iot), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [Piper](https://github.com/OHF-Voice/piper1-gpl), [modelo de voz Cadu](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/cadu/medium), [Gemma 3](https://ollama.com/library/gemma3).
