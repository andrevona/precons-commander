# Código-fonte do site

Para continuar o trabalho num novo ambiente (caminhos dos scripts assumem /home/claude):

    cp -r src/dados/* /home/claude/ && cp src/build.py src/template.html src/normalizar.py src/publicar.sh /home/claude/ && cp -r src/tools /home/claude/
    mkdir -p /home/claude/site && cp index.html sw.js README.md manifest.json icon* /home/claude/site/ && cp -r icons /home/claude/site/

- `tools/raspar.py SET slug pasta stem` baixa https://mtg.wtf/deck/SET/slug e grava raw/pasta/stem.txt (comandantes, `--`, demais cartas; ignora Display Commander e tokens; confere somas das seções).
- `normalizar.py raw/pasta/stem.txt` grava pasta/stem.txt no formato final (comandante(s), linha em branco, resto em ordem alfabética) e valida 100 cartas, duplicatas e conflitos de número.
- `tools/auditar.py` reconfere todos os decks do build.py contra o mtg.wtf.
- `build.py` (lista C de coleções, ANOS e ícones) gera precons_offline.html a partir de template.html; copiar para site/index.html; atualizar a lista de ícones e a versão em site/sw.js; publicar com `publicar.sh "mensagem"`.
- `tools/atributos.py` gera `cartas.csv` (uma linha por carta: cores, identidade de cor, custo, valor de mana, tipos, nome em português) e `impressoes.csv` (uma linha por edição+número: raridade) a partir das listas dos decks e do Scryfall. Precisa de acesso a api.scryfall.com e data.scryfall.io; roda em cerca de 1 minuto (`python3 tools/atributos.py`, cache em /tmp/atributos-cache). Rodar de novo sempre que entrar deck novo; ele para com erro se alguma carta de alguma lista não for achada no Scryfall. Os dois CSV ainda não são usados pelo site (build.py não os lê).
