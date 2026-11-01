"""Gera a página de Pauper a partir de template_pauper.html e da pasta pauper/ (reorganizada em famílias e variações em 31/10/2026).

Entrada:
  pauper/listas.json.gz   todas as listas dos últimos 30 dias, normalizadas (tools/pauper_normalizar.py)
  pauper/variacoes.json   famílias, variações, consensos e a ordem das listas (tools/pauper_variacoes.py)
  pauper/estrategias.json (textos de estratégia de cada arquétipo e variação, em pt e en)
  pauper/cartas.csv, pauper/banidas.csv, pauper/confrontos.json (DeckSnipe, tools/pauper_confrontos.py), pauper/metagame.json
Saída:
  pauper_offline.html          -> site/pauper/index.html: famílias e variações, com a lista de consenso de cada variação embutida
  pauper_nomes_pt.json         -> site/pauper/nomes_pt.json (nome da carta -> nome em português, para a busca)
  pauper_fam/<família>.json    -> site/pauper/fam/: os destaques de cada variação (até 2 listas reais, também em Outras; com diferenças relevantes
                                  do consenso; ver tools/pauper_variacoes.py), carregados quando a família é aberta

Na página: família = grupo (botão com a % das listas), variação = coleção (com as cores e o nº de listas), deck = "Consenso" da
variação e, depois, as listas reais em ordem de resultado (a variação "Outras" de cada família só tem listas reais).
Link: #<variação> (consenso) ou #<variação>-<id da lista no MTGGoldfish>.
"""
import ast, csv, gzip, json, os, re, shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))
def versao_do_site():
    """Versão publicada (ex. v117), lida do sw.js (var V = "precons-v117"): ./sw.js ou ./site/sw.js. Aparece no pé da página."""
    for c in ("sw.js", os.path.join("site", "sw.js")):
        if os.path.exists(c):
            m = re.search(r'precons-(v\d+)', open(c, encoding="utf-8").read())
            if m: return m.group(1)
    raise SystemExit("sw.js não encontrado (esperado em ./sw.js ou ./site/sw.js): sem ele o build não sabe a versão")
P = "pauper"
cartas = {r["carta"]: r for r in csv.DictReader(open(os.path.join(P, "cartas.csv"), encoding="utf-8"))}
var = json.load(open(os.path.join(P, "variacoes.json"), encoding="utf-8"))
pacote = json.load(gzip.open(os.path.join(P, "listas.json.gz"), "rt", encoding="utf-8"))
listas = {x["id"]: x for x in pacote["listas"]}
_pl = os.path.join(P, "placar.json")  # placar das listas que só têm a colocação na tabela (tools/pauper_placar.py)
PLACAR = json.load(open(_pl, encoding="utf-8")) if os.path.exists(_pl) else {}

# Tradução dos tipos: a mesma tabela do build.py (forma impressa nas cartas em português)
src = open("build.py", encoding="utf-8").read()
TIPO_PT = ast.literal_eval(re.search(r"^TIPO_PT=(\{.*?\})\n", src, re.S | re.M).group(1))
TIPO_PT.update({"Basic Snow Land": "Terreno Básico da Neve", "Kindred Creature": "Criatura de Estirpe"})
novos = sorted({c["tipo"] for c in cartas.values()} - set(TIPO_PT))
if novos:
    raise SystemExit("ERRO: tipos sem tradução (acrescentar em TIPO_PT do build.py ou aqui): %s" % novos)

LINHA = re.compile(r"^(\d+)\s+(.+)$")  # "qtd Nome" (no Pauper as listas não têm edição)
LETRAS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Códigos dos tipos em ordem fixa (por tipo, não pela ordem em que aparecem), para os arquivos das famílias não dependerem uns dos outros
TIPOS = {"en": sorted({c["tipo"] for c in cartas.values()})}
TIPOS["pt"] = [TIPO_PT[x] for x in TIPOS["en"]]
if len(TIPOS["en"]) > len(LETRAS):
    raise SystemExit("ERRO: tipos demais para uma letra cada")
cod = {x: LETRAS[i] for i, x in enumerate(TIPOS["en"])}


def montar(texto):
    """Lista para a tela ("Sideboard" antes do sideboard), tipos (uma letra por carta) e números do deck principal para o
    comparativo: criaturas, instantâneas e feitiços, outras mágicas, terrenos, valor de mana médio e curva (0–5 e 6+, sem terrenos)."""
    blocos = texto.strip().split("\n\n")
    lista = blocos[0] + ("\n\nSideboard\n" + blocos[1] if len(blocos) > 1 else "") + "\n"
    tp = "".join(cod[cartas[LINHA.match(l).group(2)]["tipo"]] for l in lista.split("\n") if LINHA.match(l))
    st = {"cri": 0, "mag": 0, "out": 0, "ter": 0, "curva": [0] * 7}
    soma = n = 0
    for l in blocos[0].split("\n"):
        q, nome = LINHA.match(l).groups(); q = int(q); c = cartas[nome]
        if "Land" in c["tipo"]:
            st["ter"] += q; continue
        k = "cri" if "Creature" in c["tipo"] else ("mag" if c["tipo"].split()[-1] in ("Instant", "Sorcery") else "out")
        st[k] += q; mv = float(c["mv"] or 0); soma += q * mv; n += q; st["curva"][min(6, int(mv))] += q
    st["mv"] = round(soma / n, 2) if n else 0
    return lista, tp, st


BASICOS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"} | {"Snow-Covered " + b for b in ("Plains", "Island", "Swamp", "Mountain", "Forest")}


def trocas(texto, cons):
    """Cartas do deck principal (sem básicos, como na contagem do pauper_variacoes.py) que entram e saem em relação ao consenso:
    [[qtd, carta]] em ordem alfabética."""
    m = {}
    for l in texto.strip().split("\n\n")[0].split("\n"):
        q, c = LINHA.match(l).groups(); m[c] = m.get(c, 0) + int(q)
    c0 = {c: q for q, c in cons}
    ks = sorted((set(m) | set(c0)) - BASICOS, key=str.casefold)
    return ([[m.get(k, 0) - c0.get(k, 0), k] for k in ks if m.get(k, 0) > c0.get(k, 0)],
            [[c0.get(k, 0) - m.get(k, 0), k] for k in ks if c0.get(k, 0) > m.get(k, 0)])


def real(x, col, dif=None, cons=None):
    lista, tp, st = montar(x["lista"])
    extra = {}
    if dif:  # cartas diferentes do consenso (nº no principal sem básicos, nº no sideboard) e quais entram e saem no principal
        ent, sai = trocas(x["lista"], cons)
        if (sum(q for q, _ in ent) + sum(q for q, _ in sai)) // 2 != dif[0]:
            raise SystemExit("ERRO: trocas da lista %s não batem com a diferença do pauper_variacoes.py" % x["id"])
        extra = {"dif": dif[0], "difs": dif[1], "ent": ent, "sai": sai}
    return dict(extra, **{"nome": col["nome"], "arquivo": col["id"] + "-" + x["id"], "real": 1, "lista": lista, "ci": x["ci"], "tp": tp, "st": st,
            "jogador": x["jogador"], "evento": x["evento"], "lugar": x["lugar"], "data": x["data"], "origem": x["origem"], "apelido": x["nome"],
                         "placar": x["lugar"] if re.match(r"^\d+-\d+(-\d+)?$", x["lugar"]) else PLACAR.get(x["id"], "")})


# Texto de estratégia de cada arquétipo e variação ([pt, en]; pauper/estrategias.json, escrito à mão): o que faltar só é avisado
# (ex. variação nova depois de raspar de novo) e a página não mostra texto para ela.
_es = os.path.join(P, "estrategias.json")
ESTRAT = json.load(open(_es, encoding="utf-8")) if os.path.exists(_es) else {"familias": {}, "variacoes": {}}
_sem = [f["slug"] for f in var["familias"] if f["slug"] not in ESTRAT["familias"]] + \
       [v["slug"] for f in var["familias"] for v in f["variacoes"] if v["slug"] not in ESTRAT["variacoes"]]
if _sem:
    print("AVISO: sem texto de estratégia em pauper/estrategias.json:", ", ".join(_sem))
colecoes, familias, por_fam = [], [], {}
pos = 0
todas_var = sorted((v for f in var["familias"] for v in f["variacoes"]), key=lambda v: -v["n"])
posicao = {v["slug"]: i + 1 for i, v in enumerate(todas_var)}  # posição da variação entre todas (mais listas = 1ª)
for f in var["familias"]:
    familias.append({"nome": f["familia"], "slug": f["slug"], "n": f["n"], "mtgo": f["mtgo"], "papel": f["papel"], "pct": f["pct"],
                     "sobre": ESTRAT["familias"].get(f["slug"])})
    reais = {}
    for v in f["variacoes"]:
        texto = "\n".join(f"{q} {c}" for q, c in v["consenso"]) + ("\n\n" + "\n".join(f"{q} {c}" for q, c, _ in v["side"]) if v["side"] else "")
        lista, tp, st = montar(texto)
        col = {"id": v["slug"], "nome": v["nome"], "grupo": f["familia"], "fam": f["slug"], "ano": "", "icone": "", "ci": v["cores"],
               "n": v["n"], "mtgo": v["mtgo"], "papel": v["papel"], "pct": v["pct"], "pos": posicao[v["slug"]],
               "sobre": ESTRAT["variacoes"].get(v["slug"])}
        col["decks"] = [{"nome": v["nome"], "arquivo": v["slug"], "lista": lista, "ci": v["cores"], "tp": tp, "st": st,
                         "n": v["n"], "mtgo": v["mtgo"], "papel": v["papel"], "bons": v["bons"], "primeiros": v["primeiros"],
                         "side": [[c, p] for q, c, p in sorted(v["side"], key=lambda t: (-t[2], t[1]))]}]  # sideboard típico: carta e % das listas
        colecoes.append(col)
        reais[v["slug"]] = [real(listas[i], col, (d, ds), v["consenso"]) for i, d, ds in v["destaques"]]  # só os destaques (até 2)
    if f["outras_destaques"]:
        col = {"id": f["slug"] + "_outras", "nome": "", "outras": 1, "grupo": f["familia"], "fam": f["slug"], "ano": "", "icone": "",
               "n": len(f["outras_ids"]), "decks": []}
        colecoes.append(col)
        reais[col["id"]] = [real(listas[i], col) for i, _, _ in f["outras_destaques"]]
    por_fam[f["slug"]] = reais

banidas = [[r["carta"], r["nome_pt"] if r["nome_pt"] != r["carta"] else "", r["grupo"]]
           for r in csv.DictReader(open(os.path.join(P, "banidas.csv"), encoding="utf-8"))]
banidas.sort(key=lambda x: re.sub(r"^[^A-Za-z0-9]+", "", x[0]).casefold())
info = {"data": var["raspado_em"], "dias": var["dias"], "total": var["total"], "mtgo": var["mtgo"], "papel": var["papel"],
        "nfam": len(familias), "nvar": sum(1 for c in colecoes if not c.get("outras")), "banidas_em": pacote["scryfall_em"]}

# Histórico de confrontos (DeckSnipe) somado por família: os arquétipos do MTGGoldfish de uma família viram um só.
cf = os.path.join(P, "confrontos.json")
confrontos = json.load(open(cf, encoding="utf-8")) if os.path.exists(cf) else None
if confrontos:
    meta = json.load(open(os.path.join(P, "metagame.json"), encoding="utf-8"))
    nome_arq = {a["slug"]: a["nome"] for a in meta["arquetipos"]}
    fam_de_arq = {}
    for f in var["familias"]:
        for a, _ in f["arquetipos"]:
            fam_de_arq[a] = f["slug"]
    fora = sorted({x for k in confrontos["m"] for x in k.split("|")} - set(nome_arq))
    if fora: raise SystemExit("ERRO: confrontos.json com arquétipos fora do metagame: %s" % fora)
    m = {}
    for k, (v, d, e) in sorted(confrontos["m"].items()):
        a, b = (fam_de_arq[nome_arq[x]] for x in k.split("|"))
        if a == b:
            continue  # dentro da mesma família (ex. Dimir x Grixis Faeries): não é um confronto entre famílias
        if (b + "|" + a) in m:  # guarda um sentido só
            a, b, v, d = b, a, d, v
        t = m.setdefault(a + "|" + b, [0, 0, 0]); t[0] += v; t[1] += d; t[2] += e
    confrontos = {k: v for k, v in confrontos.items() if k != "geral"}  # "geral" (por arquétipo) não é usado na página
    confrontos["m"] = m

html = (open("template_pauper.html", encoding="utf-8").read()
        .replace("__CONFRONTOS__", json.dumps(confrontos, ensure_ascii=False, sort_keys=True, separators=(",", ":")) if confrontos else "null")
        .replace("__TIPOS__", json.dumps(TIPOS, ensure_ascii=False))
        .replace("__META__", json.dumps(info))
        .replace("__VERSAO__", versao_do_site())
        .replace("__FAMILIAS__", json.dumps(familias, ensure_ascii=False))
        .replace("__BANIDAS__", json.dumps(banidas, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__DATA__", json.dumps(colecoes, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
open("pauper_offline.html", "w", encoding="utf-8").write(html)
shutil.rmtree("pauper_fam", ignore_errors=True); os.makedirs("pauper_fam")
for slug, reais in por_fam.items():
    open(os.path.join("pauper_fam", slug + ".json"), "w", encoding="utf-8").write(json.dumps(reais, ensure_ascii=False, separators=(",", ":")))
pt = {n: r["nome_pt"] for n, r in cartas.items() if r["nome_pt"] and r["nome_pt"] != n}
open("pauper_nomes_pt.json", "w", encoding="utf-8").write(json.dumps(pt, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
tam = sum(os.path.getsize(os.path.join("pauper_fam", x)) for x in os.listdir("pauper_fam"))
print(len(html), "| famílias:", len(familias), "| variações:", info["nvar"], "| listas:", var["total"], f"(arquivos das famílias: {tam // 1024} KB)",
      "| nomes em português:", len(pt), "| banidas:", len(banidas))
