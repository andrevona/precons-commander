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

As listas dos decks vêm do [mtg.wtf](https://mtg.wtf) (página de cada deck). Cada carta usa a edição e o número indicados lá; decks mais recentes misturam várias edições. Os códigos depois do nome de cada carta, como `(KHC) 81`, são a sigla da edição e o número da carta; servem para o endstep.cc localizar exatamente a versão (a arte e a edição) desejada. Cartas com nome alternativo (em decks como Teenage Mutant Ninja Turtles, Marvel e Hatsune Miku, o mtg.wtf mostra "Nome de exibição (Carta original)") aparecem com o nome da carta original, que é o que o endstep.cc reconhece; a edição e o número continuam os mesmos, então a arte é a da versão do deck. Cartas "Display Commander" (versão oversized), tokens e os baralhos extras que acompanham alguns produtos (Planar Deck, Scheme Deck), todos fora das 100 cartas, não foram incluídos. Os ícones das coleções e os símbolos de mana (no seletor Por cor) são os servidos pelo [Scryfall](https://scryfall.com) (propriedade da Wizards of the Coast). Decks Secret Lair ficam agrupados na coleção "Secret Lair", com o ano no nome do deck.

## Como usar

1. Abra um grupo (Universes Within, Universes Beyond, Starters ou Secret Lair), escolha a coleção e o deck. Ou use o campo de busca: carta, deck, comandante, coleção ou ano, em inglês ou português ("Anel Solar" acha o Sol Ring).
2. Se quiser, refine com **Por cor** (identidade de cor do comandante), **Por ano** e **Por arquétipo** (tribal, fichas, cemitério etc.; cada deck tem 1 ou 2, classificados por regra objetiva em `src/dados/decks.csv`); os filtros combinam entre si e com a busca. **Sortear deck** sorteia um deck; o botão de pessoas ao lado faz o **sorteio em grupo** (2 a 4 jogadores, nomes opcionais, free-for-all ou duplas com 4), com um deck diferente para cada um e um link para compartilhar o resultado. No quadro do sorteio, **Blacklist** tira grupos, coleções, arquétipos ou decks, um a um (valem só na aba aberta); marcando **Todos da mesma coleção**, **Todos do mesmo ano** e/ou **Todos com o mesmo arquétipo**, todos recebem decks da mesma coleção, ano ou arquétipo sorteados, mostrados acima dos cartões (coleção e ano não se combinam; uma opção fica desabilitada quando não sobram decks para todos); e, em cada cartão, o botão do dado troca só o deck daquele jogador. Cada cartão mostra o(s) arquétipo(s) do deck em etiquetas coloridas, e **Alterar regras** reabre o quadro com as opções daquele sorteio. **Limpar tudo** volta ao início.
3. Toque em **Criar no endstep.cc** (copia a lista e abre o editor; é preciso estar logado lá) ou em **Copiar lista**.
4. No endstep.cc: *Paste a list* › cole › *Apply*; em *Set format*, escolha *Commander*.

Extras: link direto por deck (por exemplo `#mkc/blame_game`), botão de compartilhar, interface em português ou inglês conforme o navegador (outros idiomas veem em inglês; nomes de decks, cartas e coleções ficam sempre em inglês) e funcionamento offline depois do primeiro acesso. No celular, use "Adicionar à tela inicial" para abrir como app. Os mesmos passos estão em "Dica de uso", no rodapé do site.

## Cobertura atual

Commander 2011 e 2013 a 2026 completos, incluindo os Starter Commander Decks de 2022, o Foundations Commander (2026, no grupo Starters) e os Secret Lair commander decks de 2021 a 2026 (174 decks, 47 coleções). O Reality Fracture Commander usa o símbolo do set Reality Fracture, pois o Scryfall ainda não tem um ícone próprio para ele. As edições Collector's Edition não são incluídas (repetem as listas dos decks normais, mudando só a aparência das cartas). O Upgrades Unleashed (Kamigawa: Neon Dynasty Commander) traz 2 Mossfire Valley porque foi impresso assim por engano (a Wizards confirmou); a lista segue o deck como foi vendido e o site mostra um aviso nesse deck.

Problemas ou sugestões: use o link "e-mail" ou "issue no GitHub" dentro da "Dica de uso" no rodapé do site, ou abra uma issue em https://github.com/andrevona/precons-commander/issues.

## Licença

O código (página, scripts e ferramentas) é distribuído sob a licença [MIT](LICENSE). Ela **não** cobre o que não é do projeto: nomes e textos de cartas, nomes de decks e coleções (Wizards of the Coast), as listas obtidas do mtg.wtf, nem os ícones e símbolos de mana do Scryfall.
