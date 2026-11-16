# Roberto — testes e pendências

Data: 26/10/2026. Cópia local baseada em `jzampieri/cp_04_iot`. Modo inicial: simulação.

## Passou

- Ambiente Python instalado; dependências verificadas com `pip check`.
- **29 testes automatizados**: nome completo e limites de palavra, nome com pontuação, rejeição de nomes parecidos no texto, comandos diretos, janela de sete segundos, expiração, comandos sem nome ignorados, bloqueio de entrada durante fala, descarte de fila, LED/braço simulados, agenda/calculadora, confirmação serial com identificador, falha sem falso sucesso, cadastro usando imagem compartilhada e bloqueio de alteração de volume por transcrição sem relação com volume.
- Captura real de áudio pelo HyperX QuadCast.
- Voz neural masculina brasileira Piper Cadu instalada, sintetizada e reproduzida. Usuário confirmou que a pronúncia ficou melhor.
- Câmera índice 0: captura real de 640 × 480.
- IA Gemma 3 4B: conversa real em português, inferência local com uso da GPU RTX 4060 Ti.
- Análise real de imagem da webcam pela IA local, sem API de visão externa.
- Arquivo `INICIAR_ROBERTO.bat`: iniciou o servidor e abriu o painel; modo simulação ativo.
- Comandos humanos observados na sessão: levantar braço; acender luz; apagar luz; calcular 5 + 5; cotação; temperatura em São Paulo. Essas ações foram reconhecidas pelo microfone e encaminhadas. A cotação e o clima consultam internet.
- Firmware Arduino compilado para Uno R3, Nano clássico e Nano com bootloader antigo: 5960 bytes de programa e 322 bytes de variáveis globais. A compilação usa a montagem LED via INPUT_PULLUP, sem resistor externo.
- Cópia portátil: Python 3.12.14 executado de dentro da pasta da faculdade, sem usar a `.venv` original; imports de áudio, visão, IA e Tcl passaram. O Whisper foi carregado a partir dos modelos da cópia. Painel HTTP e comandos simulados foram exercitados por cliente de teste, sem disputar dispositivos com a sessão humana.
- DXF conjunto de 40 peças auditado novamente: unidades mm, contornos fechados e ausência de segmentos duplicados.
- Pacote: conferidos arquivos essenciais, 40 DXFs individuais mais 2 corpos de prova, firmware idêntico ao fonte, início em simulação e exclusão de agenda/rostos da sessão. Hashes dos arquivos essenciais em `VERIFICACAO_DO_PACOTE.json`.

## Fala sintetizada → reconhecimento → comando

O ensaio usa **arquivos de áudio sintetizado**, não a voz de uma pessoa. Após remover do prompt a sugestão do nome, seis de sete casos passaram:

| Caso | Resultado |
|---|---|
| “Roberto, levante o braço” | Passou: ARM_UP simulado |
| “Roberto, acenda a luz” | Passou: LED_ON simulado |
| “Roberto, qual é o seu nome?” | Texto foi transcrito como “Cobeto…” nessa amostra; ignorado, sem ação. Repetir ensaio humano |
| “Roberto!” | Passou: abre janela após responder |
| “Abaixe o braço” na janela | Passou: ARM_DOWN simulado |
| Pergunta sem Roberto | Passou: ignorada |
| “Roberta, acenda a luz” | Passou: ignorada |

O nome exato não aceita “Cobeto” de propósito. Isso evita ampliar ativações acidentais. Pode ser necessário repetir uma chamada quando o reconhecimento errar. Os testes de lógica de identidade passam; o resultado acima é uma limitação do áudio/ASR, não uma autorização para anunciar reconhecimento perfeito.

## Correções feitas nos ensaios

- Restrições da API do Fusion corrigidas durante a criação mecânica.
- Vocabulário necessário do Whisper incluído no download.
- PyAV 19 substituído por 16.1, compatível com a versão instalada do faster-whisper.
- A voz Windows Maria e a voz Piper Faber foram substituídas por Cadu após o usuário avaliar a pronúncia.
- Pontuação após o nome (“Roberto.”) passou a ser tratada corretamente.
- Removida sugestão do nome no prompt do ASR: ela convertia uma amostra “Roberta” em “Roberto”.
- Cadastro facial legado que disputava a câmera com o painel substituído por captura do frame compartilhado; tempo limitado a 20 segundos. Testado com imagens sintéticas e câmera mockada; repetir cadastro humano para validar iluminação e distância.
- Uma transcrição imprecisa de pergunta foi roteada ao volume pelo LLM; adicionada exigência de pistas explícitas para ferramentas de volume, captura de tela e navegação.

## Ainda depende de teste físico ou humano

- Precisão com vozes, distâncias e ruídos diferentes; fala rápida e pausas variadas no ambiente da apresentação.
- Não reativar com a própria voz em condições acústicas reais usando alto-falantes próximos ao microfone. O bloqueio e descarte durante a síntese passaram nos testes de lógica; o dispositivo padrão observado era uma saída JBL, portanto não se declara eco cancelado em qualquer notebook.
- Cadastro e reconhecimento facial humano depois da correção. Não é autenticação biométrica segura.
- Gravação física no Arduino, porta/driver real, ACK real do firmware.
- LED sem resistor externo: brilho muito fraco via pull-up interno; pode não servir para apresentação iluminada.
- Servo alimentado só pelo USB: corrente, quedas de tensão, sentido e curso com o braço real.
- Encaixe do SG90 e do horn, espessura do MDF, folga e kerf após corte dos corpos de prova.
- Execução da pasta portátil em um segundo computador Windows e uso da GPU/CPU desse computador. Deve ser ensaiado antes da apresentação.

Os comandos de captura de tela, alterações de volume e abertura de sites não foram exercitados indiscriminadamente. Permanecem disponíveis mediante pedido do usuário. O Arduino físico não foi simulado como se fosse uma placa real: o painel identifica todas as ações simuladas.
