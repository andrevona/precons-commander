# Precons Commander

**Um facilitador para quem usa o [endstep.cc](https://endstep.cc).** Página simples para consultar e copiar as listas dos decks pré-construídos (precons) de Commander de Magic: The Gathering e levá-las para o endstep.cc: com um botão, a lista é copiada no formato que o endstep.cc importa já com o nome do deck e o comandante definidos. A lista exibida usa o formato `quantidade Nome (SET) número`.

## Formato da lista

- **Na tela:** `quantidade Nome (SET) número`, com o(s) comandante(s) na primeira linha, uma linha em branco e as demais cartas em ordem alfabética.
- **Ao copiar** (botões **Copiar lista** e **Criar no endstep.cc**): a mesma lista no formato de exportação do MTG Arena, com três etiquetas a mais. `Name` dá o nome do deck no formato *Deck - Comandante (SIGLA ano)*, com a sigla de três letras da coleção e o ano de lançamento (Secret Lair: o ano do deck), e a seção `Commander` indica o comandante; colada no endstep.cc (*Paste a list* › *Apply*), o deck já fica com nome, 100 cartas e comandante. Exemplo:

```
About
Name Turtle Power! - Heroes in a Half Shell (TMC 2026)

Commander
1 Heroes in a Half Shell (TMC) 6

Deck
1 Acidic Slime (TMC) 48
1 April O'Neil, Live on the Scene (TMC) 9
...
```

Se for colar em algum lugar que não entende essas etiquetas, apague as linhas `About`, `Name …`, `Commander` e `Deck`.

## Aviso importante

- **Projeto não oficial e sem fins lucrativos.** Não é afiliado, endossado nem patrocinado pela Wizards of the Coast, pelo mtg.wtf nem pelo endstep.cc.
- *Magic: The Gathering* e os nomes de cartas, coleções e decks são marcas e propriedade da Wizards of the Coast LLC.
- **Feito com ajuda de inteligência artificial (Claude, da Anthropic).** As listas foram extraídas por IA das páginas de cada deck (a partir de 2022 por um script que lê a página diretamente; os anos anteriores foram reconferidos com esse mesmo script) e conferidas automaticamente (100 cartas por deck, sem cartas repetidas além dos terrenos básicos, sem números de coleção ligados a dois nomes). Mesmo assim, **podem existir erros**. Confira a lista antes de usar e, se achar algum problema, abra uma *issue*.

## Fonte dos dados

As listas dos decks vêm do [mtg.wtf](https://mtg.wtf) (página de cada deck). Cada carta usa a edição e o número indicados lá; decks mais recentes misturam várias edições. Os códigos depois do nome de cada carta, como `(KHC) 81`, são a sigla da edição e o número da carta; servem para o endstep.cc localizar exatamente a versão (a arte e a edição) desejada. Cartas com nome alternativo (em decks como Teenage Mutant Ninja Turtles, Marvel e Hatsune Miku, o mtg.wtf mostra "Nome de exibição (Carta original)") aparecem com o nome da carta original, que é o que o endstep.cc reconhece; a edição e o número continuam os mesmos, então a arte é a da versão do deck. Cartas "Display Commander" (versão oversized), tokens e os baralhos extras que acompanham alguns produtos (Planar Deck, Scheme Deck), todos fora das 100 cartas, não foram incluídos. Os ícones das coleções e os símbolos de mana (no seletor Decks por cores) são os servidos pelo [Scryfall](https://scryfall.com) (propriedade da Wizards of the Coast). Decks Secret Lair ficam agrupados na coleção "Secret Lair", com o ano no nome do deck.

## Como usar

A página abre mostrando só os quatro grupos (Universes Within, Universes Beyond, Starters e Secret Lair). Toque num grupo para abrir o conteúdo dele; tocar de novo no mesmo grupo recolhe tudo. Escolha a coleção (em Universes Within, com "Todos" os anos, as demais se recolhem sob ela; toque nela de novo para ver as outras) e o deck. Ou use o filtro, logo abaixo dos grupos: digite o nome de uma carta, de um deck, de um comandante, de uma coleção ou um ano (a carta pesquisada fica destacada na lista). A partir da terceira letra aparecem até 50 sugestões (coleções, decks, comandantes e cartas; a lista rola); escolha uma com o toque, o mouse ou as setas e Enter. A busca ignora maiúsculas e acentos e também entende o nome da carta em português ("Anel Solar" acha o Sol Ring; a sugestão mostra o nome original e, ao escolhê-la, o filtro passa a usá-lo). A lista na tela e a lista copiada continuam sempre com os nomes em inglês. Os nomes em português são os impressos em papel (cerca de 78% das cartas; os sets mais recentes não têm) e só são carregados quando o português está entre os idiomas do navegador. Logo abaixo do filtro, o seletor **Por cor** mostra só os decks cujo comandante tem exatamente aquelas cores (identidade de cor; cada opção mostra os símbolos de mana das cores, por exemplo Esper, Yore (quatro cores, sem verde) ou WUBRG) e combina com o texto digitado. Ao lado fica o seletor **Por ano**, com as mesmas regras: mostra só os decks lançados naquele ano (nos Secret Lair, o ano do deck), com a contagem em cada opção, e os dois filtros combinam entre si e com a busca. Para tirar um filtro, toque no × ao lado dele (ou escolha a primeira opção de novo). Com uma cor ou um ano escolhido, a separação por grupos some e todas as coleções aparecem juntas, em ordem de lançamento (o Secret Lair vira um botão de coleção, por último). Cada opção mostra quantos decks têm aquelas cores. Ao lado do seletor, o botão **Surpreenda-me** abre um deck sorteado entre todos (ele limpa a busca e os filtros), e **Limpar tudo** (que aparece quando há algo aberto ou filtrado) volta à tela inicial, sem busca nem filtros e com tudo recolhido. Os botões dos decks mostram os símbolos de mana das cores do comandante ; o deck escolhido fica com a borda, o fundo e um brilho embaixo nessas cores (uma cor, a própria cor; duas, metade de cada; três ou mais, um degradê entre todas; incolor, cinza). Sorteado um deck de Universes Within, as outras coleções se recolhem sob a dele, como num clique. Com a busca ou algum filtro ativo, as coleções não se recolhem. Depois use **Criar no endstep.cc** ou **Copiar lista**. A interface aparece no idioma do sistema ou do navegador (português, inglês ou espanhol; outros idiomas usam inglês); nomes de decks, cartas, coleções e grupos ficam sempre em inglês. No celular, use "Adicionar à tela inicial" para abrir como app. A página funciona offline depois do primeiro acesso.

Os botões indicam quantos decks há em cada grupo e coleção (com a busca ou algum filtro ativo, quantos batem). O endereço da página muda a cada deck escolhido (por exemplo `#mkc/blame_game`). **Criar no endstep.cc** copia a lista num formato próprio para importação (o do MTG Arena, com o nome do deck e a seção do comandante) e mostra os passos antes de abrir o editor de um deck novo no endstep.cc (é preciso estar logado lá): toque em *Paste a list*, cole, toque em *Apply* (o endstep.cc já dá o nome ao deck, carrega as 100 cartas e coloca o comandante no lugar) e, em *Set format*, escolha *Commander*. Marcando "Não mostrar de novo", os próximos cliques já copiam e abrem o endstep.cc direto (preferência guardada só neste aparelho). **Copiar lista** copia a lista no mesmo formato (veja "Formato da lista"), sem abrir o endstep.cc. O botão de compartilhar, ao lado do nome do deck (com o ícone do iOS ou do Android, conforme o aparelho, ou um ícone de link nos demais), abre o compartilhamento do celular com o link do deck; no computador, copia o link. O rodapé mostra a data da última conferência das listas com o mtg.wtf e, ao tocar em "Dica de uso", o passo a passo de uso (o mesmo do quadro que abre em **Criar no endstep.cc**).

## Cobertura atual

Commander 2011 e 2013 a 2026 completos, incluindo os Starter Commander Decks de 2022, o Foundations Commander (2026, no grupo Starters) e os Secret Lair commander decks de 2021 a 2026 (174 decks, 47 coleções). O Reality Fracture Commander usa o símbolo do set Reality Fracture, pois o Scryfall ainda não tem um ícone próprio para ele. As edições Collector's Edition não são incluídas (repetem as listas dos decks normais, mudando só a aparência das cartas).
