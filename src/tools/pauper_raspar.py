"""Raspa o metagame de Pauper do MTGGoldfish (base MTGO, últimos 30 dias, o padrão do site).

Para cada arquétipo com pelo menos MIN_DECKS decks no período, baixa a lista representativa que o
MTGGoldfish mostra na página do arquétipo (uma lista real de um jogador), só com quantidade e nome.

Saída (na pasta de trabalho):
  raw_pauper/<slug>.txt      lista como o MTGGoldfish exporta ("qtd Nome"; linha em branco; sideboard)
  raw_pauper/metagame.json   arquétipos (nome, slug, %, nº de decks, deck de origem, jogador, evento, data)

Uso: python3 tools/pauper_raspar.py [--min 5]
"""
import html, json, os, re, sys, time, urllib.request

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "raw_pauper")
BASE = "https://www.mtggoldfish.com"
MIN_DECKS = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 5
UA = {"User-Agent": "Mozilla/5.0 (precons-commander; projeto pessoal)"}


def baixar(caminho):
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + caminho, headers=UA), timeout=60) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if tentativa == 2:
                raise
            time.sleep(3)
    return ""


def slug_de(nome):
    s = re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_")
    return s


def metagame():
    arqs, pagina = [], 1
    while True:
        s = baixar("/metagame/pauper/full" + (f"?page={pagina}" if pagina > 1 else ""))
        sel = re.search(r'option selected="selected" value="(\d+)"', s)
        if not sel or sel.group(1) != "30":
            raise SystemExit("ERRO: o período padrão da página não é 30 dias (%s)" % (sel and sel.group(1)))
        for m in re.finditer(r"<div class='archetype-tile' id='(\d+)'>(.*?)(?=<div class='archetype-tile' id=|$)", s, re.S):
            t = m.group(2)
            n = re.search(r'href="/archetype/([^"#]+)#paper">([^<]+)<', t)
            pct = re.search(r"([\d.]+)%", t)
            cnt = re.search(r"\((\d+)\)", t)
            if not (n and pct and cnt):
                raise SystemExit("ERRO: não entendi o arquétipo %s" % m.group(1))
            arqs.append({"id": m.group(1), "nome": html.unescape(n.group(2)).strip(), "url": n.group(1),
                         "pct": float(pct.group(1)), "decks": int(cnt.group(1))})
        if f"full?page={pagina + 1}" not in s:
            break
        pagina += 1
        time.sleep(1)
    return arqs


def main():
    os.makedirs(SAIDA, exist_ok=True)
    arqs = metagame()
    total = sum(a["decks"] for a in arqs)
    escolhidos = [a for a in arqs if a["decks"] >= MIN_DECKS]
    print("%d arquétipos, %d decks; %d com >= %d decks (%.1f%% do metagame)" % (
        len(arqs), total, len(escolhidos), MIN_DECKS, 100 * sum(a["decks"] for a in escolhidos) / total))
    vistos = set()
    for a in escolhidos:
        time.sleep(1)
        s = baixar("/archetype/" + a["id"])
        d = re.search(r'href="(?:https://www\.mtggoldfish\.com)?/deck/(\d+)">(?:(?!</a>).)*?Deck Page', s, re.S)
        if not d:
            raise SystemExit("ERRO: sem lista na página do arquétipo " + a["nome"])
        a["deck"] = d.group(1)
        quem = re.search(r"<span class='author'>by ([^<]+)</span>", s)
        ev = re.search(r'Event:\s*<a href="[^"]*">([^<]+)</a>,?[ \t]*([^<\n]*)', s)
        dt = re.search(r"Deck Date:\s*([A-Z][a-z]{2} \d{1,2}, \d{4})", s)
        a["jogador"] = html.unescape(quem.group(1)) if quem else ""
        a["evento"] = html.unescape(ev.group(1)).strip() if ev else ""
        a["res"] = html.unescape(ev.group(2)).strip() if ev else ""  # resultado: "5-0", "6-1", "1st"...
        a["data"] = time.strftime("%Y-%m-%d", time.strptime(dt.group(1), "%b %d, %Y")) if dt else ""
        a["slug"] = slug_de(a["nome"])
        if a["slug"] in vistos:
            raise SystemExit("ERRO: slug repetido " + a["slug"])
        vistos.add(a["slug"])
        time.sleep(1)
        lista = baixar("/deck/download/%s" % a["deck"]).replace("\r", "").strip() + "\n"
        open(os.path.join(SAIDA, a["slug"] + ".txt"), "w", encoding="utf-8").write(lista)
        print("%5.1f%% %4d  %-28s deck %s  %s  %s" % (a["pct"], a["decks"], a["nome"], a["deck"], a["data"], a["jogador"]))
    info = {"fonte": BASE + "/metagame/pauper/full", "periodo_dias": 30, "base": "online (MTGO)",
            "raspado_em": time.strftime("%Y-%m-%d"), "min_decks": MIN_DECKS,
            "total_arquetipos": len(arqs), "total_decks": total, "arquetipos": escolhidos}
    json.dump(info, open(os.path.join(SAIDA, "metagame.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
