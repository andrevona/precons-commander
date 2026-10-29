# Código-fonte do site

Para continuar o trabalho num novo ambiente (caminhos dos scripts assumem /home/claude):

    cp -r src/dados/* /home/claude/ && cp src/build.py src/template.html src/normalizar.py src/publicar.sh /home/claude/ && cp -r src/tools /home/claude/
    mkdir -p /home/claude/site && cp -r index.html nomes_pt.json sw.js README.md manifest.json icon.svg icon-*.png icons /home/claude/site/

- `tools/raspar.py SET slug pasta stem` baixa https://mtg.wtf/deck/SET/slug e grava raw/pasta/stem.txt (comandantes, `--`, demais cartas; ignora Display Commander e tokens; confere somas das seções).
- `normalizar.py raw/pasta/stem.txt` grava pasta/stem.txt no formato final (comandante(s), linha em branco, resto em ordem alfabética) e valida 100 cartas, duplicatas e conflitos de número.
- `tools/auditar.py` reconfere todos os decks do build.py contra o mtg.wtf.
- `build.py` (lista C de coleções, ANOS e ícones) gera precons_offline.html a partir de template.html; copiar para site/index.html; atualizar a lista de ícones e a versão em site/sw.js; publicar com `publicar.sh "mensagem"`.
- `tools/atributos.py` gera `cartas.csv` (uma linha por carta: cores, identidade de cor, custo, valor de mana, tipos, nome em português) e `impressoes.csv` (uma linha por edição+número: raridade) a partir das listas dos decks e do Scryfall. Precisa de acesso a api.scryfall.com e data.scryfall.io; roda em cerca de 1 minuto (`python3 tools/atributos.py`, cache em /tmp/atributos-cache). Rodar de novo sempre que entrar deck novo; ele para com erro se alguma carta de alguma lista não for achada no Scryfall. O `build.py` lê os dois CSV (copiados de src/dados para /home/claude) e gera `nomes_pt.json` (nome da carta na lista -> nome em português, 4.998 nomes, 79 KB gzip), que o site carrega ao tocar no filtro para buscar e sugerir em português. Também embute em cada deck o campo `ci` (identidade de cor do(s) comandante(s), para o filtro "Por cor") e para com erro se algum comandante não estiver em `impressoes.csv`. Depois de rodar `tools/atributos.py`, rodar `python3 build.py`, copiar `precons_offline.html` para `site/index.html` e `nomes_pt.json` para `site/` (o `publicar.sh` leva ao repositório).
