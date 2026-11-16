# CP5 — Robô inteligente em MDF

Revisão 1 · Protótipo mecânico para conferência e participação do grupo · 26/10/2026

## O que está entregue

Modelo montado no Autodesk Fusion, com esboços e extrusões separados por peça, nove grupos mecânicos e um grupo de teste. Arquivo `CP5_Robo_Inteligente_MDF.f3d`, 42 DXFs individuais nominais e lista de peças. São 40 placas no robô e dois corpos de prova. Não há distribuição de chapa porque a área útil da máquina ainda não foi informada.

O modelo apresenta as placas de MDF. Servo, horn, LED, placa eletrônica, cabos, porcas e parafusos são itens comprados; não são peças para corte nem estão representados em detalhe no 3D. O braço móvel está posicionado, sem junta cinemática do Fusion. O parâmetro de ângulo permite gerar outras posições.

## Dimensões e parâmetros

| Elemento | Dimensão nominal |
|---|---|
| MDF | 3 mm; medir a chapa real |
| Altura total | 300 mm |
| Corpo | 140 largura × 95 profundidade × 146 altura mm |
| Cabeça | cubo de 100 mm |
| Pés | 58 × 120 mm cada, duas camadas, espessura final 6 mm |
| Pernas | 38 mm entre pés e corpo; duas placas por perna |
| Pescoço | 10 mm entre corpo e cabeça |
| Braço | 100 mm do eixo à extremidade inferior; placa de 3 mm |
| LED | furo de 5,2 mm, no eixo central da frente do corpo |
| USB | janela traseira de 24 × 18 mm |
| Folga inicial | 0,10 mm total; validar com os corpos de prova |

Altura = 2 × MDF + perna_altura + corpo_altura + pescoco_altura + cabeca.

**Como alterar:** em Modificar → Alterar parâmetros, edite os parâmetros de usuário e execute `RoboMDF` novamente com esse modelo ativo. O script lê os parâmetros e cria um documento novo. Os esboços têm contornos fixados, regenerados pelo script; as extrusões usam a expressão `mdf`. As alterações de largura/folga/posição não se propagam automaticamente na linha do tempo: exigem essa regeneração. Edições manuais feitas no modelo anterior não são transferidas. Para trabalho manual do grupo, salve uma cópia e modele nela sem regenerar.

Os valores iniciais também estão em `config.json`. O parâmetro `kerf_estimado` registra uma estimativa de 0,15 mm; **não aplica compensação nos DXFs**. O operador deverá configurar a compensação no programa de corte depois de medir o kerf real.

## Corte e teste de encaixe

Todos os DXFs estão em milímetros, escala 1:1, camada CORTE, com polilinhas fechadas e círculos. Não há camada de gravação nesta revisão: os olhos e a boca são recortes. O código da peça é o nome do arquivo; não está gravado no MDF. Identifique as peças com lápis depois de cortar.

1. Meça a espessura em vários pontos da chapa com paquímetro. Atualize `mdf`.
2. Corte primeiro `TESTE_FEMEA` e `TESTE_MACHO`, usando os mesmos ajustes da fabricação.
3. As sete ranhuras, da esquerda para a direita, são MDF −0,10; −0,05; +0,00; +0,05; +0,10; +0,15; +0,20 mm. A placa macho entra de canto, de modo que sua espessura atravesse a largura da ranhura.
4. Escolha uma montagem que entre à mão e permita cola, sem martelar. Registre a folga escolhida, regenere o modelo e corte também um par pequeno de bordas do corpo para conferir o encaixe real.
5. Configure uma única compensação no CAM: contornos externos para fora; furos e ranhuras para dentro. Para kerf k, o deslocamento da trajetória é k/2. Se o programa já compensa, não aplique outra compensação ao desenho.
6. Antes de autorizar o lote, meça no programa de corte a frente `C_FRENTE`: deve ter 140 × 146 mm. Não use “ajustar à página”.

As abas têm sua largura reduzida pela folga. Os entalhes de borda recebem folga na profundidade, e os encaixes internos recebem largura MDF + folga. Os corpos de prova ensaiam a chapa e o corte, mas não substituem a montagem a seco das seis faces.

Para organizar as chapas, use a lista de dimensões e os DXFs individuais, rotacionando as peças quando útil. Confirme a área útil, o tamanho da chapa e a margem entre peças com o laboratório. Nenhum tamanho de mesa foi presumido.

## Montagem, na ordem

### 1. Pés

Separe `P_D1`, `P_D2`, `P_E1`, `P_E2`. A camada 1 é a sola inteira. A camada 2 tem ranhuras. Alinhe o contorno e cole cada par sobre superfície plana, sem preencher as ranhuras. Espere a cura conforme a cola.

### 2. Pernas

Em cada pé entram duas placas: `L_D1` e `L_D2`, ou `L_E1` e `L_E2`. As abas estreitas inferiores entram na camada superior do pé e param na sola. As superiores entrarão na base do corpo. Cole mantendo as placas paralelas e perpendiculares aos pés. Cada par fica separado ao longo da profundidade; não há articulação nas pernas.

### 3. Corpo

Separe `C_BASE`, `C_TOPO`, `C_FRENTE`, `C_DIR`, `C_ESQ` e `C_TRAS`. Direita e esquerda são as do robô: olhando de frente, o ombro direito fica à sua esquerda.

Faça primeiro uma montagem sem cola. Encaixe `C_BASE` nas quatro abas das pernas. Monte laterais, base e topo, e encaixe a frente sobre as abas alinhadas. Os entalhes são abertos nas bordas, permitindo aproximar os painéis. Use a tampa traseira temporariamente como gabarito para manter o esquadro. Confira diagonais e pés apoiados na mesa; então cole as junções permanentes. **Não cole a tampa traseira, suas abas ou os entalhes que a recebem.**

Antes de fechar a frente, instale os apoios internos e os alojamentos de porca. Cada `T_PORCA_ij` tem uma cavidade hexagonal para uma porca M3. Cole sua `T_CAPA_ij` pelo lado interno, alinhando o furo, e cole a borda externa do conjunto à lateral do corpo. A face da porca fica voltada à tampa. Use a tampa e parafusos sem cola como gabarito, com filme para impedir colagem acidental. Há quatro conjuntos. Não deixar cola entrar nas roscas.

### 4. Servo SG90

Cole `S_REFORCO` por dentro de `C_DIR`, alinhando a janela e os dois furos. A abertura nominal mede 23,5 × 12,8 mm; os furos piloto têm 2,2 mm de diâmetro e distância entre centros de 28 mm. O reforço soma 3 mm à parede e distribui a carga das orelhas de montagem.

**Conferência necessária antes do corte definitivo:** meça seu SG90, suas orelhas e o horn. Existem variantes. Insira o servo pelo interior, com eixo saindo para fora do ombro. Confira a posição do eixo: o desenho considera deslocamento de 5,5 mm na direção da frente em relação ao centro da abertura. Ajuste o desenho se o seu eixo for diferente. Use os parafusos do servo ou pequenos passantes com arruelas e porcas; não aperte a ponto de esmagar o MDF. Se as orelhas não encostarem planas ou o eixo não alcançar o braço, corrija a interface antes de fabricar.

O espaço reservado dentro do ombro deve comportar o servo e seus fios sem tocar a eletrônica. Confirme essa reserva com o componente real, pois o modelo não contém um SG90 detalhado.

### 5. Braços

**Esquerdo fixo:** `A_E_ESP` fica entre `C_ESQ` e `A_E_FIXO`. Alinhe os dois furos a 15 mm entre centros e fixe com dois M3, arruelas e porcas, com comprimento escolhido pela pilha real. Aperte apenas o suficiente para ficar fixo.

**Direito móvel:** use `A_D_MOVEL`, uma única placa. O furo central de 7 mm dá acesso ao parafuso do eixo; os furos piloto de 2 mm ficam a 7 e 14 mm do centro. Estes furos são uma interface inicial: confira sua coincidência com o horn que veio com seu servo e ajuste-os se necessário. Aparafuse o horn na face interna do braço em pelo menos dois pontos. Use o parafuso original no eixo estriado; não tente fabricar estrias em MDF, não cole o braço no eixo e não use um M3 no lugar do parafuso original.

Centralize o SG90 eletricamente com o horn solto, desligue a alimentação e monte o horn na posição planejada. Confira manualmente a folga lateral e o acesso ao parafuso. Inicie testes com pequeno curso, por exemplo 10°, e aumente aos poucos até o movimento necessário. O projeto considera levantar para a frente, com eixo transversal ao corpo. Não force o eixo com a mão e não use o limite mecânico como batente normal.

### 6. LED

Insira um LED de 5 mm em `C_FRENTE`. O furo nominal tem 5,2 mm: confira a fixação do LED escolhido ou use suporte apropriado. Isole os terminais e mantenha folga de fio para manutenção. Na versão de faculdade, a ligação sem resistor externo usa o resistor interno do Uno R3/Nano clássico via INPUT_PULLUP, com brilho muito fraco. Siga o guia elétrico do pacote. Não use uma saída OUTPUT/HIGH nem o pino 5V diretamente num LED comum sem resistor.

### 7. Arduino e fios

Cole três `I_APOIO00/01/02` em uma pilha e três `I_APOIO10/11/12` na outra, formando dois apoios de 9 mm. Eles ficam sobre a base do corpo. Cole `I_BANDEJA` em cima dos apoios; sua superfície superior fica a 15 mm acima da base de referência do corpo. As ranhuras aceitam abraçadeiras para prender um Uno ou Nano em espaçadores isolantes. Não apoie soldas diretamente na bandeja nem aperte abraçadeiras sobre componentes.

A bandeja tem 100 × 70 mm. O Arduino Uno nominal de aproximadamente 68,6 × 53,4 mm cabe em planta, com espaço restante para fios, mas o conector e o cabo reais devem ser testados. A janela traseira serve para passagem de um cabo flexível; não é um encaixe rígido alinhado ao conector USB. Mantenha uma volta de folga e passe o cabo pela janela antes de fechar. Os quatro parafusos da tampa podem ser removidos para acesso completo.

Na versão de faculdade, o USB do notebook é a única alimentação prevista, conforme solicitado. Valide um único SG90 com braço leve: os picos de corrente podem causar reinicializações. Se isso ocorrer, a alimentação não foi validada. O firmware e o guia elétrico estão na pasta de software/Arduino do pacote.

### 8. Cabeça

Encaixe `N_PESCOCO` no topo do corpo e em `H_BASE`. A aba é centralizada e as laterais largas do pescoço apoiam nas faces. Faça montagem a seco, confira o alinhamento e cole. Monte `H_FRENTE`, `H_DIR`, `H_ESQ`, `H_TRAS`, `H_TOPO` com o mesmo princípio do corpo. A cabeça é fixa e não contém LED. Olhos e boca são decorativos e vazados; pode-se colar papel escuro por dentro se desejado.

### 9. Fechamento

Confira a cura da cola, estabilidade, livre movimento do braço, fixação dos fios e acesso ao USB. Deslize `C_TRAS` sobre as abas traseiras, sem prender fios. Fixe pelos quatro furos de 3,4 mm aos alojamentos M3. M3 × 10 mm é um ponto de partida para a pilha nominal de 9 mm; confira engate e comprimento real. A tampa permanece removível.

## Verificações e limites

A auditoria dos DXFs confirmou unidades em mm, contornos fechados, polígonos válidos e ausência de segmentos repetidos. A checagem geométrica das placas na posição montada não encontrou volume sobreposto. Ela usa integração por grade para placas ortogonais e furos aproximados; não é uma análise de tolerâncias, rigidez, resistência à queda ou simulação cinemática do conjunto comprado.

Para densidade assumida de MDF de 750 kg/m³, a placa do braço tem massa estimada de 5,23 g e torque estático máximo na horizontal de 0,0245 kgf·cm, usando o centroide do contorno. Não inclui horn, parafusos, atrito, aceleração ou carga na mão. A TowerPro informa 1,8 kgf·cm a 4,8 V como torque de bloqueio do SG90, não como capacidade contínua de projeto. Fonte: https://towerpro.com.tw/product/sg90-7/ . Há margem teórica para esta placa leve, mas o ensaio físico define o curso, velocidade e confiabilidade. Não adicionar objetos à mão sem recalcular e testar.

Os pés dão uma base larga em profundidade. A estabilidade final depende de onde ficam placa, fonte e cabos, do atrito e da aceleração do braço. Coloque os itens mais pesados embaixo, mantenha o cabo sem tração e teste em superfície plana. Não foi declarada estabilidade dinâmica garantida.

## Participação efetiva do grupo — requisito de 50%

**O trabalho automático não é autoria do grupo.** A interpretação de “50%” deve ser confirmada com o professor; contagem de peças não é, por si só, o critério de avaliação. Use este modelo como referência de estudo e registre a contribuição real de cada integrante.

Roteiro sugerido para o grupo desenvolver mais da metade das 40 placas do robô, além de tomar decisões próprias:

1. Medir MDF, servo, horn e Arduino reais; registrar medidas e decidir folga após os corpos de prova.
2. Em uma cópia de trabalho, remodelar manualmente as seis faces da cabeça (6), quatro placas dos pés (4), quatro placas das pernas (4), dois braços (2), pescoço (1), reforço do servo (1), espaçador do braço fixo (1), bandeja (1) e seis lâminas de apoio (6): 26 de 40 placas. Não basta copiar os corpos do modelo gerado.
3. Para cada peça: criar componente, criar esboço no plano adequado, desenhar e cotar contorno, adicionar retângulos de abas/ranhuras, recortar os trechos necessários, desenhar círculos cotados e extrudar com a expressão `mdf`. Usar relações horizontais, verticais, coincidência, simetria e cotas ligadas aos parâmetros. Isso produz uma modelagem nativa mais fácil de editar que os contornos fixados do gerador.
4. Montar componentes usando juntas rígidas nas partes fixas. No braço direito, criar junta de revolução no eixo real do servo e definir limites após o ensaio. Inspecionar interferência em várias posições. Validar suporte e horn antes do lote.
5. Exportar cada esboço de corte ou face plana em DXF e comparar as dimensões com a lista. Documentar fotos do teste de encaixe e da montagem, capturas da linha do tempo e um diário de decisões por integrante.

O gerador permanece disponível para comparar dimensões e estudar a lógica. Para esta cópia manual, não execute o gerador novamente esperando que ele preserve a modelagem do grupo.

## Executar o script em outra sessão

Abra Utilidades → Scripts e complementos (Shift+S), use o menu + → Script ou complemento do dispositivo e selecione a pasta `RoboMDF`. Selecione RoboMDF e pressione o triângulo Executar. Mantenha `RoboMDF.py`, `RoboMDF.manifest`, `geometria.py` e `config.json` juntos. A execução cria um documento novo e exporta o F3D e os DXFs nessa pasta; não apaga o documento anterior. O F3D de saída é atualizado a cada execução, portanto copie uma revisão que desejar preservar antes de regenerar.

Referência oficial de instalação: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-install-an-ADD-IN-and-Script-in-Fusion-360.html .
