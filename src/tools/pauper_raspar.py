"""Raspa o metagame de Pauper do MTGGoldfish (últimos 30 dias, o padrão do site): a lista de arquétipos.

Grava pauper/metagame.json (na pasta de trabalho) com os arquétipos que têm pelo menos MIN_DECKS decks no período
(id, nome, url, pct, decks, slug), a data da raspagem e os totais. É o primeiro passo da atualização: o
tools/pauper_listas.py lê este arquivo (a data de corte das listas sai de "raspado_em").
Desde 01/11/2026 não baixa mais a lista representativa de cada arquétipo (não era usada pela página).

Uso: python3 tools/pauper_raspar.py [--min 5]
"""
import html, json, os, re, sys, time, urllib.request

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "pauper", "metagame.json")
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
    arqs = metagame()
    total = sum(a["decks"] for a in arqs)
    escolhidos = [a for a in arqs if a["decks"] >= MIN_DECKS]
    print("%d arquétipos, %d decks; %d com >= %d decks (%.1f%% do metagame)" % (
        len(arqs), total, len(escolhidos), MIN_DECKS, 100 * sum(a["decks"] for a in escolhidos) / total))
    vistos = set()
    for a in escolhidos:
        a["slug"] = slug_de(a["nome"])
        if a["slug"] in vistos:
            raise SystemExit("ERRO: slug repetido " + a["slug"])
        vistos.add(a["slug"])
        print("%5.1f%% %4d  %s" % (a["pct"], a["decks"], a["nome"]))
    antigo = json.load(open(SAIDA, encoding="utf-8")) if os.path.exists(SAIDA) else {"arquetipos": []}
    velhos, novos = {a["nome"] for a in antigo["arquetipos"]}, {a["nome"] for a in escolhidos}
    if novos - velhos: print("ARQUÉTIPOS NOVOS (conferir FAMILIAS no pauper_variacoes.py e NOMES no pauper_confrontos.py):", sorted(novos - velhos))
    if velhos - novos: print("Arquétipos que saíram (abaixo de %d decks):" % MIN_DECKS, sorted(velhos - novos))
    info = {"fonte": BASE + "/metagame/pauper/full", "periodo_dias": 30, "base": "online (MTGO)",
            "raspado_em": time.strftime("%Y-%m-%d"), "min_decks": MIN_DECKS,
            "total_arquetipos": len(arqs), "total_decks": total, "arquetipos": escolhidos}
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(info, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
