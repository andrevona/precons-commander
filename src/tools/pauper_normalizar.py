"""Normaliza as listas de Pauper raspadas (raw_pauper/) para o formato do site e confere tudo pelo Scryfall.

Entrada: raw_pauper/<slug>.txt ("qtd Nome <variante> [SET] (F)"; linha em branco; sideboard) e raw_pauper/metagame.json.
Saída (pasta pauper/ da pasta de trabalho):
  pauper/listas/<slug>.txt  "qtd Nome (SET) número"; deck principal em ordem alfabética; linha em branco; sideboard
  pauper/metagame.json      o metagame raspado, com as cores de cada deck ("ci", letras WUBRG ou "C")
  pauper/cartas.csv         uma linha por carta das listas: carta, cores, tipo, nome_pt, livre (pode ter mais de 4 cópias)
  pauper/banidas.csv        cartas banidas no Pauper segundo o Scryfall: carta, tipo, nome_pt

Edição: a que o MTGGoldfish informa ("[SET]"); o número vem do Scryfall (o da variante, quando o MTGGoldfish
informa o número; senão a impressão comum da coleção, a de número mais baixo). Para com erro se alguma carta não
existir na coleção, não for legal no Pauper, ou se o deck tiver menos de 60 cartas, mais de 15 no sideboard ou mais
de 4 cópias de uma carta (exceto terrenos básicos e cartas que permitem qualquer número de cópias).

Uso: python3 tools/pauper_normalizar.py [--cache /tmp/atributos-cache]
"""
import argparse, collections, csv, gzip, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atributos import baixar_default, pt_do_all_cards, tipo_de, colapsar, faces_de  # noqa: E402

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Códigos do MTGGoldfish que diferem dos do Scryfall
SETS = {"PLIST": "plst", "MM": "mmq", "AP": "apc", "OD": "ody", "UZ": "usg", "MI": "mir", "IN": "inv", "PS": "pls",
        "TE": "tmp", "ST": "sth", "EX": "exo", "UL": "ulg", "UD": "uds", "NE": "nem", "PR": "pcy", "VI": "vis",
        "WL": "wth", "TO": "tor", "JU": "jud", "AL": "all", "HM": "hml", "FE": "fem", "AQ": "atq", "AN": "arn",
        "LE": "leg", "DK": "drk", "P2": "p02", "PO": "por", "PK": "ptk", "CH": "chr", "IA": "ice", "MR": "mir", "7E": "7ed", "6E": "6ed", "5E": "5ed", "PC1": "hop", "PC2": "pc2"}
# Coleções do MTGGoldfish sem as cartas no Scryfall (Mystery Booster): usa a impressão do The List, se houver
TROCA = {"mb1": "plst", "fmb1": "plst"}
LINHA = re.compile(r"^(\d+) (.+?)(?: <([^>]+)>)? \[([A-Za-z0-9_]+)\](?: \(F\))?$")
WUBRG = "WUBRG"


def chave_nome(n):
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", n.lower()) if not unicodedata.combining(ch))


def cores_da_carta(c):
    s = set(c.get("colors") or [])
    for f in c.get("card_faces", []):
        s |= set(f.get("colors") or [])
    return "".join(x for x in WUBRG if x in s)


def cores_do_deck(cs):
    """Cores do deck = cores que o deck principal paga nos custos de mana e que os seus terrenos produzem.
    Assim uma carta que nunca é conjurada pelo custo (ex.: Sneaky Snacker num deck só de Montanhas) não dá cor;
    símbolos híbridos contam só se nenhuma das metades já for paga; símbolos phyrexianos não contam."""
    produz = set()
    for c in cs:
        if "Land" in (faces_de(c)[0].get("type_line") or c.get("type_line", "")):
            produz |= set(c.get("produced_mana") or [])
    produz &= set(WUBRG)
    pede, hibridos = set(), []
    for c in cs:
        if "Land" in (faces_de(c)[0].get("type_line") or ""):
            continue
        custo = "".join(f.get("mana_cost") or "" for f in faces_de(c)) or c.get("mana_cost") or ""
        for sim in re.findall(r"\{([^}]+)\}", custo):
            partes = sim.split("/")
            if "P" in partes:
                continue
            cores = [x for x in partes if x in WUBRG]
            if len(cores) == 1 and len(partes) == 1:
                pede.add(cores[0])
            elif cores:
                hibridos.append(set(cores))
    if not produz:  # sem terrenos coloridos: usa as cores das cartas
        produz = set(WUBRG)
    ci = pede & produz
    for h in hibridos:
        if not (h & ci):
            ci |= h & produz
    return "".join(x for x in WUBRG if x in ci) or "C"


def numero_chave(n):
    m = re.match(r"^(\D*)(\d+)(.*)$", n)
    return (0, m.group(1), int(m.group(2)), m.group(3)) if m else (1, n, 0, "")


def escolher(cands, variante):
    """Escolhe a impressão: número da variante, se houver; senão a impressão comum de número mais baixo."""
    if variante and re.fullmatch(r"[0-9]+[a-z]?", variante):
        c = [x for x in cands if x["collector_number"].lower() == variante.lower()]
        if c:
            return c[0]
    if variante:
        v = variante.lower()
        def casa(x):
            fe = x.get("frame_effects") or []
            return ((v == "retro" and x.get("frame") in ("1993", "1997")) or (v == "showcase" and "showcase" in fe)
                    or (v in ("borderless", "full art") and (x.get("border_color") == "borderless" or x.get("full_art")))
                    or (v.startswith("extended") and "extendedart" in fe))
        c = [x for x in cands if casa(x)]
        if c:
            cands = c
    normais = [x for x in cands if x.get("booster") and not x.get("promo")] or cands
    return min(normais, key=lambda x: numero_chave(x["collector_number"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/atributos-cache")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    raw = os.path.join(RAIZ, "raw_pauper")
    saida = os.path.join(RAIZ, "pauper")
    os.makedirs(os.path.join(saida, "listas"), exist_ok=True)
    meta = json.load(open(os.path.join(raw, "metagame.json"), encoding="utf-8"))

    por_set_nome = collections.defaultdict(list)
    por_oracle = {}
    for l in gzip.open(baixar_default(a.cache), "rt", encoding="utf-8"):
        c = json.loads(l)
        if c.get("lang", "en") != "en" or c.get("layout") in ("token", "double_faced_token", "art_series", "emblem"):
            continue
        nomes = {chave_nome(c["name"])} | {chave_nome(f["name"]) for f in c.get("card_faces", [])}
        for n in nomes:
            por_set_nome[(c["set"], n)].append(c)
        oid = c.get("oracle_id") or faces_de(c)[0].get("oracle_id")
        por_oracle.setdefault(oid, c)

    erros, cartas, trocas = [], {}, []
    for arq in meta["arquetipos"]:
        slug = arq["slug"]
        texto = open(os.path.join(raw, slug + ".txt"), encoding="utf-8").read().strip()
        blocos = re.split(r"\n\s*\n", texto)
        if len(blocos) > 2:
            erros.append(f"{slug}: mais de duas seções"); continue
        secoes = []
        for b in blocos:
            linhas = collections.OrderedDict()
            for l in b.split("\n"):
                m = LINHA.match(l.strip())
                if not m:
                    erros.append(f"{slug}: linha não reconhecida: {l!r}"); continue
                q, nome, var, s = int(m.group(1)), m.group(2), m.group(3), m.group(4)
                s = SETS.get(s, s.lower())
                cands = por_set_nome.get((s, chave_nome(nome)))
                if not cands and s in TROCA:
                    cands = por_set_nome.get((TROCA[s], chave_nome(nome)))
                    if cands:
                        trocas.append(f"{slug}: {nome} [{s.upper()}] -> {TROCA[s].upper()}")
                if not cands:
                    erros.append(f"{slug}: {nome} não existe em {s} no Scryfall"); continue
                c = escolher(cands, var)
                nm = colapsar(c["name"])
                if c["legalities"].get("pauper") != "legal":
                    erros.append(f"{slug}: {nm} não é legal no Pauper ({c['legalities'].get('pauper')})")
                chave = (nm, c["set"].upper(), c["collector_number"])
                linhas[chave] = linhas.get(chave, 0) + q
                if nm not in cartas:
                    cartas[nm] = {"c": c, "cores": cores_da_carta(c), "tipo": tipo_de(c),
                                  "oid": c.get("oracle_id") or faces_de(c)[0].get("oracle_id")}
            secoes.append(linhas)
        principal, side = secoes[0], (secoes[1] if len(secoes) > 1 else {})
        n_main, n_side = sum(principal.values()), sum(side.values())
        if n_main < 60:
            erros.append(f"{slug}: deck principal com {n_main} cartas")
        if n_side > 15:
            erros.append(f"{slug}: sideboard com {n_side} cartas")
        total = collections.Counter()
        for sec in (principal, side):
            for (nm, _, _), q in sec.items():
                total[nm] += q
        for nm, q in total.items():
            c = cartas[nm]["c"]
            livre = "Basic" in c.get("type_line", "") or "any number of cards named" in (c.get("oracle_text") or "")
            if q > 4 and not livre:
                erros.append(f"{slug}: {q} cópias de {nm}")
        arq["ci"] = cores_do_deck([cartas[nm]["c"] for (nm, _, _) in principal])
        arq["n_main"], arq["n_side"] = n_main, n_side
        fmt = lambda sec: "\n".join(f"{q} {nm} ({s}) {n}" for (nm, s, n), q in sorted(sec.items(), key=lambda kv: (kv[0][0].casefold(), kv[0][1], numero_chave(kv[0][2]))))
        open(os.path.join(saida, "listas", slug + ".txt"), "w", encoding="utf-8").write(
            fmt(principal) + ("\n\n" + fmt(side) if side else "") + "\n")
    for t in trocas:
        print("TROCA", t)
    if erros:
        print("\n".join("ERRO " + e for e in erros))
        sys.exit(1)

    # banidas no Pauper (uma por carta)
    banidas = {}
    for oid, c in por_oracle.items():
        if c["legalities"].get("pauper") == "banned":
            banidas[colapsar(c["name"])] = {"c": c, "tipo": tipo_de(c), "oid": oid}

    # nomes em português (mesma regra do tools/atributos.py)
    oid_nome = {d["oid"]: n for n, d in cartas.items()}
    oid_nome.update({d["oid"]: n for n, d in banidas.items()})
    cand = collections.defaultdict(list)
    for l in open(pt_do_all_cards(a.cache), encoding="utf-8"):
        d = json.loads(l)
        n = oid_nome.get(d["oracle_id"])
        if not n:
            continue
        faces = [x for x in d["faces"] if x]
        completo = bool(d["printed_name"]) or (bool(faces) and len(faces) == len(d["faces"]))
        nome = colapsar(d["printed_name"] or " // ".join(faces))
        if nome:
            cand[n].append((completo, nome != n, d["released_at"], nome))
    pt = {n: max(v)[3] for n, v in cand.items()}

    with open(os.path.join(saida, "cartas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["carta", "cores", "tipo", "nome_pt", "livre"])  # livre=1: terreno básico ou carta que permite qualquer número de cópias
        for n in sorted(cartas):
            c = cartas[n]["c"]
            livre = "Basic" in c.get("type_line", "") or "any number of cards named" in (c.get("oracle_text") or "")
            w.writerow([n, cartas[n]["cores"] or "C", cartas[n]["tipo"], pt.get(n, ""), "1" if livre else ""])
    with open(os.path.join(saida, "banidas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["carta", "tipo", "nome_pt"])
        for n in sorted(banidas, key=str.casefold):
            w.writerow([n, banidas[n]["tipo"], pt.get(n, "")])
    meta["scryfall_em"] = __import__("time").strftime("%Y-%m-%d")
    json.dump(meta, open(os.path.join(saida, "metagame.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(meta['arquetipos'])} listas normalizadas; {len(cartas)} cartas ({len([n for n in cartas if pt.get(n)])} com nome em português); {len(banidas)} banidas")


if __name__ == "__main__":
    main()
