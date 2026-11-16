# Roteiro final do vídeo — Maker Lab

**Duração desejada:** 4min30s a 5min30s. **Limite:** 6 minutos.

## Antes de gravar

- Fechar o Monitor Serial e o Arduino IDE.
- Ligar o Arduino por USB e a alimentação externa do servo.
- Abrir `INICIAR_ROBERTO.bat` e esperar a voz ficar pronta.
- Confirmar `ARDUINO CONECTADO`, voz Alex e alto-falante correto.
- Deixar um objeto plano disponível para o teste do HC-SR04.
- Não mostrar rostos, placas, senhas ou dados pessoais no enquadramento.
- Gravar preferencialmente na horizontal, com áudio claro.

## 0:00–0:30 — Abertura

**Imagem:** Roberto inteiro, já montado.

**Fala:**

> Olá, este é o Roberto, a evolução do nosso robô inteligente para o projeto CitizenTech da Global Solution 2026.2. O projeto foi desenvolvido por Bruno Venturi Lopes Vieira, RM 99431, Guilherme Alves de Lima, RM 550433, e Leonardo de Oliveira Ruiz, RM 98901.

## 0:30–1:00 — Problema e solução

**Imagem:** Roberto e, em seguida, aproximação da tampa frontal.

**Fala:**

> A proposta é ajudar a identificar obstáculos e condições que possam prejudicar a mobilidade em corredores, calçadas e espaços de atendimento. Para esta etapa incorporamos um sensor ultrassônico HC-SR04. O robô mede o ambiente, classifica a distância e reage sem depender de um comando manual.

## 1:00–1:35 — Hardware incorporado

**Imagem:** apontar cada componente, sem esconder o sensor com a mão.

**Fala:**

> Na parte frontal temos o sensor ultrassônico, o display LCD para informar o estado e o LED de alerta. O braço é movimentado por um servo SG90. O Arduino Uno processa os sensores e atuadores. O servo possui alimentação externa, com o terra compartilhado com o Arduino, para evitar instabilidade.

## 1:35–2:35 — Demonstração autônoma

**Imagem e ações:** filmar o LCD e o braço no mesmo enquadramento.

1. Deixar o caminho livre por dois segundos.
2. Aproximar o objeto lentamente até a faixa intermediária.
3. Aproximar para menos de 30 cm.
4. Afastar novamente.

**Fala durante o teste:**

> Com o caminho livre, o LCD informa caminho livre, o LED permanece apagado e o braço fica recolhido. Ao aproximar um objeto, o sistema entra no estado de atenção. A menos de 30 centímetros, ele identifica um obstáculo, acende o LED e levanta o braço. Quando eu retiro o objeto, ele retorna automaticamente ao estado seguro.

**Complemento:**

> A leitura ocorre a cada meio segundo, mas os atuadores só mudam quando o estado muda. Isso reduz movimentos repetidos e deixa o comportamento mais estável.

## 2:35–3:35 — IA, voz e integração física

**Imagem:** enquadrar o painel e o Roberto juntos, se possível. Mostrar no topo `ARDUINO CONECTADO`.

**Fala:**

> Além da autonomia embarcada, o Roberto possui um painel local com reconhecimento de fala e inteligência artificial. O processamento funciona localmente no notebook: o Whisper reconhece o comando, a aplicação interpreta a intenção e a voz Kokoro responde em português brasileiro. A comunicação com o Arduino acontece pela porta serial.

**Ação 1:** falar claramente e esperar a resposta:

> Roberto, qual é a distância do obstáculo?

**Ação 2:** depois que ele terminar de falar:

> Roberto, acene.

**Fala após a demonstração:**

> O painel recebeu a distância real do HC-SR04 e o segundo comando produziu uma resposta física no braço. Portanto, existe integração entre sensor, software, inteligência artificial e atuador.

## 3:35–4:15 — Projeto e fabricação

**Imagem:** mostrar brevemente o Fusion, o DXF ou fotos do corte; depois mostrar a tampa instalada.

**Fala:**

> A nova tampa frontal foi modelada para acomodar o LCD, o HC-SR04 e o LED. A peça foi exportada em DXF e fabricada por corte a laser em MDF. O repositório inclui os arquivos de fabricação, o firmware, os diagramas de ligação e as instruções necessárias para reproduzir o protótipo.

## 4:15–4:50 — Software, testes e decisão

**Imagem:** mostrar rapidamente o GitHub e o README.

**Fala:**

> O firmware possui três estados de distância e tomada de decisão autônoma. O software local também oferece comandos por texto ou voz, seleção de alto-falante e conexão automática com o Arduino. A implementação foi validada por testes automatizados e por testes físicos do sensor, LCD, LED e servo.

## 4:50–5:20 — Conclusão

**Imagem:** voltar ao Roberto inteiro; deixar o caminho livre.

**Fala:**

> Como resultado, o Roberto percebe alterações no ambiente, interpreta os dados e executa respostas contextualizadas. Como evolução futura, ele poderá enviar ocorrências diretamente ao ZelaCidade e atuar em diferentes espaços públicos. Todo o código e a documentação estão disponíveis no repositório público exibido na tela. Obrigado.

## Tela final — 5 segundos

Exibir:

- **ZelaCidade — Roberto CitizenTech**
- Bruno Venturi Lopes Vieira — RM 99431
- Guilherme Alves de Lima — RM 550433
- Leonardo de Oliveira Ruiz — RM 98901
- https://github.com/brunoventuri01/zelacidade-makerlab-roberto

## Evidências que precisam aparecer

- robô físico inteiro;
- HC-SR04 visível;
- `CAMINHO LIVRE`, `ATENCAO` e `OBSTACULO` no LCD;
- LED acendendo;
- braço reagindo automaticamente;
- painel mostrando `ARDUINO CONECTADO`;
- comando de distância usando o sensor real;
- comando de aceno acionando o braço;
- tampa frontal fabricada;
- repositório público, integrantes e RMs.

## Plano de emergência

Se o reconhecimento de voz falhar durante a gravação, pare e repita a tomada. Como alternativa, digite no painel `Roberto, qual é a distância do obstáculo?` e `Roberto, acene.`; não esconda que o comando foi digitado. O importante é demonstrar a integração real com o Arduino.
