# Roteiro do vídeo — até 6 minutos

## 0:00–0:35 — Problema CitizenTech

Apresentar o grupo e explicar que obstáculos em corredores, calçadas e espaços de atendimento prejudicam mobilidade e acessibilidade. Mostrar rapidamente o Roberto montado.

## 0:35–1:20 — Evolução do protótipo

Mostrar a tampa frontal e identificar HC-SR04, LCD, LED e braço com SG90. Explicar que o sensor ultrassônico foi o sensor adicional incorporado nesta etapa.

## 1:20–2:25 — Demonstração autônoma

1. Sem objeto: filmar `CAMINHO LIVRE`, LED apagado e braço recolhido.
2. Aproximar lentamente um objeto: filmar `ATENCAO`.
3. Aproximar para menos de 30 cm: filmar `OBSTACULO`, LED aceso e braço levantando.
4. Afastar: mostrar o retorno automático.

Falar que o firmware mede a cada 500 ms, classifica o contexto e só atua quando o estado muda.

## 2:25–3:35 — IA e integração

Abrir o painel local, selecionar o Arduino e demonstrar duas frases:

- “Roberto, qual é a distância do obstáculo?”
- “Roberto, me cumprimente.”

Mostrar a resposta no painel e o aceno real. Explicar Whisper para voz, Gemma 3 para interpretação/visão, Piper para resposta e serial JSON com confirmação.

## 3:35–4:20 — Hardware e software

Mostrar rapidamente o diagrama do README e citar: Arduino Uno, HC-SR04, LCD I2C, SG90, LED com resistor e alimentação externa do servo com GND comum. Mostrar o código ou a suíte com 32 testes aprovados.

## 4:20–5:05 — Fabricação e acabamento

Mostrar o Fusion, o DXF da nova tampa e a montagem em MDF. Destacar organização, fixação dos módulos e isolamento dos fios.

## 5:05–5:40 — Resultado e próximos passos

Concluir que o protótipo identifica obstáculos, informa o operador e reage autonomamente. Como evolução, citar envio de ocorrências ao ZelaCidade e uso móvel em locais públicos.

## 5:40–6:00 — Créditos

Exibir nomes, RMs, URL do GitHub e agradecimento. Não ultrapassar seis minutos.

## Evidências indispensáveis

- Robô inteiro em funcionamento;
- três estados do LCD;
- LED e braço reagindo sem clique manual;
- sensor adicional visível;
- painel/IA controlando o hardware;
- GitHub e nomes dos integrantes;
- áudio compreensível e sem rostos/placas de terceiros.
