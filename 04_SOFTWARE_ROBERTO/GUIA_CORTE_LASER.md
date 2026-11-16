# Roberto — o que entregar ao operador do laser

## Antes de cortar

Esta é uma revisão nominal em MDF de **3 mm**. Ainda é necessário conferir seu servo SG90, horn, espessura real da chapa e folga dos encaixes. Nenhum arquivo foi declarado pronto para um lote sem esses ensaios.

1. Meça a espessura real da chapa com paquímetro.
2. Confira no projeto os furos do servo e do horn com os componentes reais. O desenho usou abertura de 23,5 × 12,8 mm e 28 mm entre furos de suporte como valores preliminares.
3. Corte primeiro as duas peças em `02_CORTE_LASER/TESTE_PRIMEIRO`.
4. Use o mesmo MDF, foco, potência e velocidade do lote. Valide a folga à mão, sem martelar.
5. Se precisar alterar espessura ou folga, corrija o projeto e gere os DXFs novamente antes de cortar o robô.

## Arquivo principal de corte

**`02_CORTE_LASER/ROBERTO_40_PECAS_NOMINAL.dxf`** contém as 40 placas do robô, em milímetros, escala 1:1, sem os dois corpos de prova.

As mesmas peças estão separadas em `PECAS_INDIVIDUAIS`. São uma alternativa ao arquivo principal. **Não corte o arquivo principal e a pasta inteira juntos**, pois isso duplicaria as peças.

A distribuição do arquivo principal é uma prancha de visualização, com espaço entre peças. Não representa a mesa da máquina e não é um aproveitamento definitivo de chapa. O operador deverá reorganizar as peças conforme a área útil, mantendo as medidas reais e quantidades.

## Pedido para o laboratório

“Este projeto é para MDF nominal de 3 mm, em milímetros e escala 1:1. Primeiro vamos cortar o teste de encaixe e conferir o SG90 e o horn. Depois use o arquivo ROBERTO_40_PECAS_NOMINAL.dxf, organize as peças na chapa e aplique uma única compensação de kerf no programa de corte. Não redimensione as peças. Todas as linhas da camada CORTE são cortes passantes; não há gravação nesta revisão.”

## Conferência rápida

- Frente do corpo `C_FRENTE`: **140 × 146 mm** no desenho nominal.
- Cabeça: seis painéis para um cubo externo de **100 mm**.
- Total: **40 peças do robô + 2 corpos de prova separados**.
- A lista CSV inclui todos os 42 códigos, com quantidade 1 para cada código. Algumas peças iguais têm códigos distintos para facilitar a montagem.
- Os projetos F3D são para abrir no Fusion, não para enviar diretamente ao laser.
- A vista espalhada do Fusion mostra 42 peças, pois inclui também os testes.
- Não abrir o DXF num editor de imagem e imprimir ajustando à página.
- Meça o kerf real e use compensação do operador; os contornos entregues não estão pré-compensados.

## Montagem depois do corte

Comece pelos pés laminados e pernas. Faça montagem a seco das caixas antes de colar. Mantenha a tampa traseira removível e proteja os encaixes da tampa contra cola. O guia completo está em `05_GUIAS/01_MONTAGEM_MDF.html`.

O arquivo F3D é editável por esboços/extrusões. Para alterar a geometria gerada por parâmetros, o gerador mecânico precisa ser executado novamente; editar apenas o valor de uma cota global não atualiza todos os contornos automaticamente. O grupo deve registrar sua própria modelagem conforme a exigência de autoria da faculdade.
