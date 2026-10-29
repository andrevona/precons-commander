#!/usr/bin/env python3
"""Classifica os precons em até 2 arquétipos, por regras objetivas, e grava dados/decks.csv.

Entrada: as listas (<pasta>/<arquivo>.txt), cartas.csv e impressoes.csv, mais o texto de regras das cartas (Scryfall
"Default Cards", baixado por tools/atributos.py para /tmp/atributos-cache). Precisa de data.scryfall.io.
Saída: decks.csv com uma linha por deck: id, nome, comandante, colecao, arq1, arq2 e a contagem de evidências
de cada arquétipo (colunas n_<arquétipo>). Nada é opinião: cada arquétipo é uma contagem de cartas (nomes distintos,
terrenos fora) que casam uma regra, comparada a um limite fixo (LIMITES). O score é contagem/limite; o deck recebe os
até 2 maiores scores com score >= 1 (o 2º só se score >= 1 e >= 60% do 1º); sem nenhum, recebe "midrange".

Uso: python3 tools/arquetipos.py [--raiz PASTA] [--saida decks.csv] [--ver]   (--ver imprime as distribuições)
"""
import argparse, csv, gzip, json, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atributos

ARQS = ["tribal", "tokens", "counters", "spellslinger", "graveyard", "artifacts", "enchantments",
        "lifegain", "sacrifice", "voltron", "blink", "lands"]

# limite = nº de cartas distintas (não-terreno) para o deck "ser" daquele arquétipo
LIMITES = {"tribal": 16, "tokens": 14, "counters": 12, "spellslinger": 28, "graveyard": 14, "artifacts": 22,
           "enchantments": 17, "lifegain": 12, "sacrifice": 12, "voltron": 12, "blink": 7, "lands": 9}

TOK_FORA = r"(treasure|clue|food|blood|map|gold|powerstone|junk|shard|incubator|role)"
RX = {
    "tokens": re.compile(r"\bcreates?\b[^.]*\btokens?\b", re.I),
    "counters": re.compile(r"\+1/\+1 counter|proliferate", re.I),
    "graveyard": re.compile(r"your graveyard|from graveyards?|\\bmills?\\b|surveil|delirium|threshold|flashback|escape|disturb|unearth|embalm|eternalize", re.I),
    "lifegain": re.compile(r"gains? \d* ?x? ?life|gain life|lifelink|whenever you gain life|life you gained", re.I),
    "sacrifice": re.compile(r"sacrifice (a|an|another|two|x|any number of|up to)\b[^.]*|whenever [^.]*\bdies\b|\bdies\b,|sacrificed", re.I),
    "blink": re.compile(r"\\bblink\\b|flicker|exile (up to \\w+ )?(another |target |each )?[^.]*you control[^.]*\\. ?(then )?return|exile [^.]*, then return [^.]*to the battlefield|return (it|that card|them|those cards|the exiled card)s? to the battlefield (under|at the beginning)", re.I),
    "lands": re.compile(r"landfall|whenever a land enters|play an additional land|additional land|put[^.]*\bland card[^.]*onto the battlefield|search your library for[^.]*\bland\b|lands? you control|for each land", re.I),
    "payoff_spell": re.compile(r"whenever you cast (an? )?(instant|sorcery|noncreature)|magecraft|prowess|copy target (instant|sorcery)|instant or sorcery", re.I),
}


def carregar_oraculo(cache):
    arq = atributos.baixar_default(cache)
    por_nome = {}
    with gzip.open(arq, "rt", encoding="utf-8") as f:
        for lin in f:
            lin = lin.strip().rstrip(",")
            if len(lin) < 3 or lin in ("[", "]"):
                continue
            c = json.loads(lin)
            if c.get("lang") != "en" or c.get("layout") in ("token", "emblem", "art_series"):
                continue
            nome = atributos.colapsar(c["name"])
            fs = atributos.faces_de(c)
            txt = "\n".join((x.get("oracle_text") or "") for x in fs)
            tl = c.get("type_line") or " // ".join(x.get("type_line", "") for x in fs)
            ent = {"txt": txt, "tl": tl}
            por_nome.setdefault(nome, ent)
            for x in c.get("card_faces", []):
                por_nome.setdefault(x["name"], ent)
    return por_nome


def ler_lista(caminho):
    """-> (comandantes, [(set, numero, nome)])"""
    blocos = open(caminho, encoding="utf-8").read().split("\n\n")
    out = []
    for i, b in enumerate(blocos):
        for l in b.split("\n"):
            m = re.match(r"^(\d+)\s+(.+?)\s+\((\w+)\)\s+(\S+)$", l.strip())
            if m:
                out.append((i == 0, m.group(3).upper(), m.group(4), m.group(2)))
    return out


def subtipos(tl):
    if "—" not in tl:
        return set()
    return set(tl.split("—", 1)[1].split("//")[0].split())


def analisar(cartas, comandantes, orac):
    """cartas: nomes distintos (nome Scryfall) do deck; devolve dict de contagens."""
    n = collections.Counter()
    sub_cont = collections.Counter()
    ncriat = 0
    comandante_sub = set()
    for nm in comandantes:
        comandante_sub |= subtipos(orac[nm]["tl"])
    for nm in cartas:
        o = orac[nm]
        tl, txt = o["tl"], o["txt"]
        if "Land" in tl.split("—")[0]:
            continue
        n["nao_terreno"] += 1
        if "Creature" in tl.split("—")[0]:
            ncriat += 1
            ss = subtipos(tl)
            changeling = "Changeling" in txt
            for s in ss:
                sub_cont[s] += 1
            if changeling:
                sub_cont["__changeling__"] += 1
        tipos = tl.split("—")[0]
        if "Instant" in tipos or "Sorcery" in tipos:
            n["is"] += 1
        if "Artifact" in tipos:
            n["artifacts"] += 1
        if "Enchantment" in tipos:
            n["enchantments"] += 1
        if "Equipment" in tl or "Aura" in tl:
            n["voltron"] += 1
        # sem a linha de tipo para não contar o próprio nome da carta
        t2 = txt.replace(nm, "~")
        if RX["tokens"].search(t2):
            # só conta se algum token criado não é só Treasure/Clue/...
            frases = [m.group(0) for m in RX["tokens"].finditer(t2)]
            if any(not re.search(TOK_FORA, f, re.I) for f in frases):
                n["tokens"] += 1
        for k in ("counters", "graveyard", "lifegain", "sacrifice", "blink", "lands"):
            if RX[k].search(t2):
                n[k] += 1
        if RX["payoff_spell"].search(t2):
            n["payoff_spell"] += 1
    # tribal: maior subtipo de criatura (changelings somam a todos); vale 10+ se o comandante for do tipo
    tribo, ntribo = None, 0
    cl = sub_cont.get("__changeling__", 0)
    for s, q in sub_cont.items():
        if s == "__changeling__":
            continue
        q2 = q + cl
        if q2 > ntribo:
            tribo, ntribo = s, q2
    # tribal "reforçado": comandante da tribo diminui o limite (10 em vez de 16)
    n["tribal"] = ntribo
    n["tribo"] = tribo or ""
    n["tribal_cmd"] = 1 if tribo and tribo in comandante_sub else 0
    n["spellslinger"] = n["is"]
    return n


def pontuar(n):
    sc = {}
    for a in ARQS:
        lim = LIMITES[a]
        c = n[a]
        if a == "tribal":
            # Human é o subtipo mais comum de todos: exige 20 e não ganha desconto do comandante
            if n["tribo"] == "Human":
                lim = 20
            elif n["tribal_cmd"]:
                lim = 10
        if a == "spellslinger":
            if n["payoff_spell"] >= 4:
                lim = 22
        sc[a] = c / lim
    return sc


def classificar(sc):
    ord_ = sorted(ARQS, key=lambda a: -sc[a])
    a1 = ord_[0] if sc[ord_[0]] >= 1 else ""
    if not a1:
        return "midrange", ""
    a2 = ord_[1] if sc[ord_[1]] >= 1 and sc[ord_[1]] >= 0.6 * sc[a1] else ""
    return a1, a2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--saida", default="decks.csv")
    ap.add_argument("--cache", default="/tmp/atributos-cache")
    ap.add_argument("--ver", action="store_true")
    a = ap.parse_args()
    raiz = a.raiz
    orac = carregar_oraculo(a.cache)
    imp = {}
    for r in csv.DictReader(open(os.path.join(raiz, "impressoes.csv"), encoding="utf-8")):
        imp[(r["set"].upper(), r["numero"])] = r["carta"]
    # decks do build.py
    ns = {}
    src = open(os.path.join(raiz, "build.py"), encoding="utf-8").read()
    ini = src.index("C=[")
    fim = src.index("\nANOS=")
    exec(src[ini:fim], ns)
    ANOS = {}
    exec(src[fim:src.index("\n", src.index("ANOS={")) + 1], ANOS)
    linhas = []
    for nome_col, pasta, decks in ns["C"]:
        for dn, f in decks:
            cam = os.path.join(raiz, pasta, f + ".txt")
            ent = ler_lista(cam)
            cmds, cartas = [], []
            for ec, st, num, nm in ent:
                carta = imp.get((st, num)) or imp.get((st, num.lstrip("0"))) or nm
                carta = atributos.colapsar(carta)
                if carta not in orac:
                    sys.exit(f"{pasta}/{f}: carta sem texto de regras: {carta}")
                if ec:
                    cmds.append(carta)
                if carta not in cartas:
                    cartas.append(carta)
            n = analisar(cartas, cmds, orac)
            sc = pontuar(n)
            a1, a2 = classificar(sc)
            linhas.append({"id": f"{pasta}/{f}", "nome": dn, "comandante": " / ".join(cmds), "colecao": nome_col,
                           "arq1": a1, "arq2": a2, "tribo": n["tribo"] if "tribal" in (a1, a2) else "",
                           **{f"n_{k}": n[k] for k in ARQS}, "_sc": sc})
    if a.ver:
        for k in ARQS:
            v = sorted(l[f"n_{k}"] for l in linhas)
            print(f"{k:13} min {v[0]:3} p25 {v[len(v)//4]:3} med {v[len(v)//2]:3} p75 {v[3*len(v)//4]:3} max {v[-1]:3}  >=lim: {sum(1 for l in linhas if l['_sc'][k]>=1)}")
        c = collections.Counter()
        for l in linhas:
            c[l["arq1"]] += 1
            if l["arq2"]:
                c[l["arq2"]] += 1
        print(c.most_common())
    cols = ["id", "nome", "comandante", "colecao", "arq1", "arq2", "tribo"] + [f"n_{k}" for k in ARQS]
    with open(os.path.join(raiz, a.saida), "w", encoding="utf-8", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    print(len(linhas), "decks ->", a.saida)


if __name__ == "__main__":
    main()
