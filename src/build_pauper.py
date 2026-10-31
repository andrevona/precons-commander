"""Gera a página de Pauper (pauper_offline.html e pauper_nomes_pt.json) a partir de template_pauper.html e da pasta pauper/.

Entrada (gerada por tools/pauper_raspar.py e tools/pauper_normalizar.py):
  pauper/metagame.json, pauper/listas/<slug>.txt, pauper/cartas.csv, pauper/banidas.csv
Saída: pauper_offline.html (vai para site/pauper/index.html) e pauper_nomes_pt.json (vai para site/pauper/nomes_pt.json).

Grupos pelo número de cores do deck (mono, duas, tres = três ou mais; incolor fica em mono); dentro de cada grupo, os decks
na ordem de participação no metagame. O link de cada deck é #<slug>.
"""
import ast, csv, json, os, re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
P = "pauper"
meta = json.load(open(os.path.join(P, "metagame.json"), encoding="utf-8"))
cartas = {r["carta"]: r for r in csv.DictReader(open(os.path.join(P, "cartas.csv"), encoding="utf-8"))}

# Tradução dos tipos: a mesma tabela do build.py (forma impressa nas cartas em português)
src = open("build.py", encoding="utf-8").read()
TIPO_PT = ast.literal_eval(re.search(r"^TIPO_PT=(\{.*?\})\n", src, re.S | re.M).group(1))
TIPO_PT.update({"Basic Snow Land": "Terreno Básico da Neve", "Kindred Creature": "Criatura de Estirpe"})
novos = sorted({c["tipo"] for c in cartas.values()} - set(TIPO_PT))
if novos:
    raise SystemExit("ERRO: tipos sem tradução (acrescentar em TIPO_PT do build.py ou aqui): %s" % novos)

LINHA = re.compile(r"^\d+\s+(.+?)\s+\(\w+\)\s+\S+$")
LETRAS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
TIPOS, cod = {"en": [], "pt": []}, {}
grupos = {"mono": [], "duas": [], "tres": []}
total = meta["total_decks"]
for a in meta["arquetipos"]:
    t = open(os.path.join(P, "listas", a["slug"] + ".txt"), encoding="utf-8").read().strip()
    blocos = t.split("\n\n")
    lista = blocos[0] + ("\n\nSideboard\n" + blocos[1] if len(blocos) > 1 else "") + "\n"
    tp = ""
    for l in lista.split("\n"):
        m = LINHA.match(l)
        if not m:
            continue
        tipo = cartas[m.group(1)]["tipo"]
        if tipo not in cod:
            cod[tipo] = LETRAS[len(TIPOS["en"])]; TIPOS["en"].append(tipo); TIPOS["pt"].append(TIPO_PT[tipo])
        tp += cod[tipo]
    nc = len(a["ci"].replace("C", ""))
    g = "mono" if nc <= 1 else ("duas" if nc == 2 else "tres")
    grupos[g].append({"nome": a["nome"], "comandante": "", "arquivo": a["slug"] + ".txt", "lista": lista, "ci": a["ci"], "tp": tp,
                      "pct": round(100 * a["decks"] / total, 1), "nmeta": a["decks"], "jogador": a["jogador"],
                      "res": a.get("res", ""), "evento": a["evento"], "data": a["data"]})
data = [{"id": g, "nome": g, "ano": "", "grupo": g, "icone": "", "decks": ds} for g, ds in grupos.items() if ds]
banidas = [[r["carta"], r["nome_pt"] if r["nome_pt"] != r["carta"] else ""]
           for r in csv.DictReader(open(os.path.join(P, "banidas.csv"), encoding="utf-8"))]
banidas.sort(key=lambda x: re.sub(r"^[^A-Za-z0-9]+", "", x[0]).casefold())
cob = round(100 * sum(a["decks"] for a in meta["arquetipos"]) / total, 1)
info = {"data": meta["raspado_em"], "min": meta["min_decks"], "cob": cob, "banidas_em": meta["scryfall_em"]}
html = (open("template_pauper.html", encoding="utf-8").read()
        .replace("__TIPOS__", json.dumps(TIPOS, ensure_ascii=False))
        .replace("__META__", json.dumps(info))
        .replace("__BANIDAS__", json.dumps(banidas, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
open("pauper_offline.html", "w", encoding="utf-8").write(html)
pt = {n: r["nome_pt"] for n, r in cartas.items() if r["nome_pt"] and r["nome_pt"] != n}
open("pauper_nomes_pt.json", "w", encoding="utf-8").write(json.dumps(pt, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
print(len(html), "| decks:", sum(len(d) for d in grupos.values()), {g: len(d) for g, d in grupos.items()}, "| nomes em português:", len(pt), "| banidas:", len(banidas))
