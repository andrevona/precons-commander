"""Gera a página de Pauper (pauper_offline.html e pauper_nomes_pt.json) a partir de template_pauper.html e da pasta pauper/.

Entrada (gerada por tools/pauper_raspar.py, tools/pauper_normalizar.py e tools/pauper_confrontos.py):
  pauper/metagame.json, pauper/listas/<slug>.txt, pauper/cartas.csv, pauper/banidas.csv, pauper/confrontos.json
Saída: pauper_offline.html (vai para site/pauper/index.html) e pauper_nomes_pt.json (vai para site/pauper/nomes_pt.json).

Grupos pelo número de cores do deck (mono, duas, tres = três ou mais; incolor fica em mono; a página acrescenta o grupo
"Mais jogados", com todos os decks em ordem de participação); dentro de cada grupo, os decks
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

LINHA = re.compile(r"^(\d+)\s+(.+)$")  # "qtd Nome" (no Pauper as listas não têm edição)
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
        tipo = cartas[m.group(2)]["tipo"]
        if tipo not in cod:
            cod[tipo] = LETRAS[len(TIPOS["en"])]; TIPOS["en"].append(tipo); TIPOS["pt"].append(TIPO_PT[tipo])
        tp += cod[tipo]
    # números do deck principal para o duelo: criaturas, instantâneas e feitiços, outras mágicas, terrenos,
    # valor de mana médio (sem terrenos) e curva (0 a 5 e 6+, sem terrenos)
    st = {"cri": 0, "mag": 0, "out": 0, "ter": 0, "curva": [0] * 7}
    soma = n = 0
    for l in blocos[0].split("\n"):
        q, nome = LINHA.match(l).groups(); q = int(q); c = cartas[nome]
        if "Land" in c["tipo"]:
            st["ter"] += q; continue
        k = "cri" if "Creature" in c["tipo"] else ("mag" if c["tipo"].split()[-1] in ("Instant", "Sorcery") else "out")
        st[k] += q; mv = float(c["mv"] or 0); soma += q * mv; n += q; st["curva"][min(6, int(mv))] += q
    st["mv"] = round(soma / n, 2) if n else 0
    nc = len(a["ci"].replace("C", ""))
    g = "mono" if nc <= 1 else ("duas" if nc == 2 else "tres")
    grupos[g].append({"nome": a["nome"], "comandante": "", "arquivo": a["slug"] + ".txt", "lista": lista, "ci": a["ci"], "tp": tp,
                      "pct": round(100 * a["decks"] / total, 1), "nmeta": a["decks"], "jogador": a["jogador"],
                      "res": a.get("res", ""), "evento": a["evento"], "data": a["data"], "st": st})
data = [{"id": g, "nome": g, "ano": "", "grupo": g, "icone": "", "decks": ds} for g, ds in grupos.items() if ds]
banidas = [[r["carta"], r["nome_pt"] if r["nome_pt"] != r["carta"] else "", r["grupo"]]
           for r in csv.DictReader(open(os.path.join(P, "banidas.csv"), encoding="utf-8"))]
banidas.sort(key=lambda x: re.sub(r"^[^A-Za-z0-9]+", "", x[0]).casefold())
cob = round(100 * sum(a["decks"] for a in meta["arquetipos"]) / total, 1)
info = {"data": meta["raspado_em"], "min": meta["min_decks"], "cob": cob, "banidas_em": meta["scryfall_em"]}
# histórico de confrontos (tools/pauper_confrontos.py); sem o arquivo, o duelo diz que não há histórico
cf = os.path.join(P, "confrontos.json")
confrontos = json.load(open(cf, encoding="utf-8")) if os.path.exists(cf) else None
if confrontos:
    slugs = {a["slug"] for a in meta["arquetipos"]}
    fora = sorted({x for k in confrontos["m"] for x in k.split("|")} - slugs)
    if fora: raise SystemExit("ERRO: confrontos.json com arquétipos fora do metagame: %s" % fora)
html = (open("template_pauper.html", encoding="utf-8").read()
        .replace("__CONFRONTOS__", json.dumps(confrontos, ensure_ascii=False, sort_keys=True, separators=(",", ":")) if confrontos else "null")
        .replace("__TIPOS__", json.dumps(TIPOS, ensure_ascii=False))
        .replace("__META__", json.dumps(info))
        .replace("__BANIDAS__", json.dumps(banidas, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
open("pauper_offline.html", "w", encoding="utf-8").write(html)
pt = {n: r["nome_pt"] for n, r in cartas.items() if r["nome_pt"] and r["nome_pt"] != n}
open("pauper_nomes_pt.json", "w", encoding="utf-8").write(json.dumps(pt, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
print(len(html), "| decks:", sum(len(d) for d in grupos.values()), {g: len(d) for g, d in grupos.items()}, "| nomes em português:", len(pt), "| banidas:", len(banidas))
