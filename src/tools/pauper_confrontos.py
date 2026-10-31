"""Histórico de confrontos entre arquétipos de Pauper, para a tela "Sortear duelo" da página de Pauper.

Fonte: matriz de confrontos do DeckSnipe (https://decksnipe.com/matrix/pauper), papel e MTGO, mesmos 30 dias do
metagame, arquétipos com 0,5% ou mais de participação (os demais o DeckSnipe junta em "Everything else", que fica de
fora). Cada célula traz vitórias, derrotas e empates do arquétipo da linha contra o da coluna (espelhos ficam de fora).

Os nomes dos arquétipos do DeckSnipe são ligados aos do MTGGoldfish (pauper/metagame.json) pela tabela NOMES; um
arquétipo do DeckSnipe sem correspondência é avisado e ignorado. As definições de arquétipo dos dois sites podem
diferir um pouco.

Saída: pauper/confrontos.json
  {fonte, url, periodo {pt, en}, raspado_em, m: {"slugA|slugB": [vitórias de A, derrotas de A, empates]}, geral: {slug: [v, d, e]}}
Uso: python3 tools/pauper_confrontos.py
"""
import html, json, os, re, sys, time, urllib.request

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://decksnipe.com/matrix/pauper?platform=both&window=30&stars=1&other=share-0.5"
# DeckSnipe -> MTGGoldfish (quando o nome difere)
NOMES = {"Mono-Red Madness": "Mono Red Madness", "Mono-Blue Terror": "Blue Terror", "Mono-Green Elves": "Elves",
         "Mono-Red Rally": "Mono Red Rally", "Golgari Spy Combo": "Spy Combo", "Selesnya Bogles": "Bogles",
         "Green Tron": "Tron", "Azorius Familiars": "Familiars", "Rakdos Madness Burn": "Rakdos Madness"}


def main():
    meta = json.load(open(os.path.join(RAIZ, "pauper", "metagame.json"), encoding="utf-8"))
    slug = {a["nome"]: a["slug"] for a in meta["arquetipos"]}
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (precons-commander; projeto pessoal)"})
    s = urllib.request.urlopen(req, timeout=90).read().decode("utf-8")
    de, ate = re.search(r'name="from" value="([\d-]+)"', s).group(1), re.search(r'name="to" value="([\d-]+)"', s).group(1)
    m, geral, sem = {}, {}, set()
    for cel in s.split('<td class="mx-cell')[1:]:
        x = re.search(r"<b>(.+?) against (.+?)</b>", cel)
        n = re.search(r"([\d,]+) wins?, ([\d,]+) loss(?:es)?, ([\d,]+) draws?", cel)
        if not x or not n:
            continue  # espelho (fora) ou célula sem partidas
        a, b = html.unescape(x.group(1)), html.unescape(x.group(2))
        v = [int(y.replace(",", "")) for y in n.groups()]
        sa = slug.get(NOMES.get(a, a))
        if not sa:
            sem.add(a); continue
        if b == "the field":
            geral[sa] = v; continue
        sb = slug.get(NOMES.get(b, b))
        if not sb:
            sem.add(b); continue
        m[sa + "|" + sb] = v
    if not m:
        sys.exit("ERRO: nenhum confronto lido (a página mudou?)")
    for x in sorted(sem):
        print("AVISO: arquétipo do DeckSnipe sem correspondência no metagame do MTGGoldfish:", x)
    fmt = lambda d, l: time.strftime("%d/%m/%Y" if l == "pt" else "%m/%d/%Y", time.strptime(d, "%Y-%m-%d"))
    info = {"fonte": "DeckSnipe", "url": "https://decksnipe.com/matrix/pauper",
            "periodo": {"pt": "papel e MTGO, de %s a %s" % (fmt(de, "pt"), fmt(ate, "pt")),
                        "en": "paper and MTGO, %s to %s" % (fmt(de, "en"), fmt(ate, "en"))},
            "raspado_em": time.strftime("%Y-%m-%d"), "m": m, "geral": geral}
    json.dump(info, open(os.path.join(RAIZ, "pauper", "confrontos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    arqs = {k.split("|")[0] for k in m}
    print("%d confrontos entre %d arquétipos (%s a %s), %d partidas" % (len(m), len(arqs), de, ate, sum(sum(v) for v in m.values()) // 2))


if __name__ == "__main__":
    main()
