"""Normaliza as listas de Pauper raspadas (raw_pauper/) para o formato do site e confere tudo pelo Scryfall.

Entrada: raw_pauper/<slug>.txt ("qtd Nome"; linha em branco; sideboard) e raw_pauper/metagame.json.
Saída (pasta pauper/ da pasta de trabalho):
  pauper/listas/<slug>.txt  "qtd Nome"; deck principal em ordem alfabética; linha em branco; sideboard em ordem alfabética
  pauper/metagame.json      o metagame raspado, com as cores de cada deck ("ci", letras WUBRG ou "C")
  pauper/cartas.csv         uma linha por carta das listas: carta, cores, tipo, mv (valor de mana), nome_pt,
                            livre (1 = pode ter mais de 4 cópias: terreno básico ou "any number of cards named")
  pauper/banidas.csv        banidas no Pauper segundo o Scryfall: carta, tipo, nome_pt, grupo
                            (grupo: "unf" = carta do Unfinity com adesivo ou atração; "conspiracy"; vazio = as demais)

Sem edição nem número (decisão do usuário em 31/10/2026: no Pauper a edição não importa; o endstep.cc reconhece a carta
pelo nome). Para com erro se alguma carta não existir no Scryfall, não for legal no Pauper, ou se o deck tiver menos de
60 cartas, mais de 15 no sideboard ou mais de 4 cópias de uma carta (exceto as "livres").

Uso: python3 tools/pauper_normalizar.py [--cache /tmp/atributos-cache]
"""
import argparse, collections, csv, gzip, json, os, re, sys, time, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atributos import baixar_default, pt_do_all_cards, tipo_de, colapsar, faces_de  # noqa: E402

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# "qtd Nome", aceitando também o formato com edição do MTGGoldfish ("qtd Nome <variante> [SET] (F)"), que é ignorada
LINHA = re.compile(r"^(\d+) (.+?)(?: <[^>]+>)?(?: \[[A-Za-z0-9_]+\])?(?: \(F\))?$")
WUBRG = "WUBRG"


def chave_nome(n):
    return "".join(ch for ch in unicodedata.normalize("NFD", n.lower()) if not unicodedata.combining(ch))


def cores_da_carta(c):
    s = set(c.get("colors") or [])
    for f in c.get("card_faces", []):
        s |= set(f.get("colors") or [])
    return "".join(x for x in WUBRG if x in s)


def eh_terreno(c):
    return "Land" in (faces_de(c)[0].get("type_line") or c.get("type_line", ""))


def cores_do_deck(cs):
    """Cores do deck = cores que o deck principal paga nos custos de mana e que os seus terrenos produzem.
    Assim uma carta que nunca é conjurada pelo custo (ex.: Sneaky Snacker num deck só de Montanhas) não dá cor;
    símbolos híbridos contam só se nenhuma das metades já for paga; símbolos phyrexianos não contam."""
    produz = set()
    for c in cs:
        if eh_terreno(c):
            produz |= set(c.get("produced_mana") or [])
    produz &= set(WUBRG)
    pede, hibridos = set(), []
    for c in cs:
        if eh_terreno(c):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/atributos-cache")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    raw = os.path.join(RAIZ, "raw_pauper")
    saida = os.path.join(RAIZ, "pauper")
    os.makedirs(os.path.join(saida, "listas"), exist_ok=True)
    meta = json.load(open(os.path.join(raw, "metagame.json"), encoding="utf-8"))

    # uma carta por nome (oracle); entre as impressões, a mais recente que não é de coleção "funny" (Un-sets)
    por_nome, por_oracle = {}, {}
    for l in gzip.open(baixar_default(a.cache), "rt", encoding="utf-8"):
        c = json.loads(l)
        if c.get("lang", "en") != "en" or c.get("layout") in ("token", "double_faced_token", "art_series", "emblem"):
            continue
        oid = c.get("oracle_id") or faces_de(c)[0].get("oracle_id")
        ant = por_oracle.get(oid)
        if not ant or (ant.get("set_type") == "funny" and c.get("set_type") != "funny") or \
                ((ant.get("set_type") == "funny") == (c.get("set_type") == "funny") and c.get("released_at", "") > ant.get("released_at", "")):
            por_oracle[oid] = c
    for c in por_oracle.values():
        for n in {c["name"]} | {f["name"] for f in c.get("card_faces", [])}:
            por_nome.setdefault(chave_nome(n), c)

    erros, cartas = [], {}
    for arq in meta["arquetipos"]:
        slug = arq["slug"]
        texto = open(os.path.join(raw, slug + ".txt"), encoding="utf-8").read().strip()
        blocos = re.split(r"\n\s*\n", texto)
        if len(blocos) > 2:
            erros.append(f"{slug}: mais de duas seções"); continue
        secoes = []
        for b in blocos:
            linhas = collections.Counter()
            for l in b.split("\n"):
                m = LINHA.match(l.strip())
                if not m:
                    erros.append(f"{slug}: linha não reconhecida: {l!r}"); continue
                q, nome = int(m.group(1)), m.group(2)
                c = por_nome.get(chave_nome(nome))
                if not c:
                    erros.append(f"{slug}: {nome} não existe no Scryfall"); continue
                nm = colapsar(c["name"])
                if c["legalities"].get("pauper") != "legal":
                    erros.append(f"{slug}: {nm} não é legal no Pauper ({c['legalities'].get('pauper')})")
                linhas[nm] += q
                if nm not in cartas:
                    cartas[nm] = {"c": c, "cores": cores_da_carta(c), "tipo": tipo_de(c),
                                  "oid": c.get("oracle_id") or faces_de(c)[0].get("oracle_id")}
            secoes.append(linhas)
        principal, side = secoes[0], (secoes[1] if len(secoes) > 1 else collections.Counter())
        n_main, n_side = sum(principal.values()), sum(side.values())
        if n_main < 60:
            erros.append(f"{slug}: deck principal com {n_main} cartas")
        if n_side > 15:
            erros.append(f"{slug}: sideboard com {n_side} cartas")
        for nm, q in (principal + side).items():
            c = cartas[nm]["c"]
            if q > 4 and not livre(c):
                erros.append(f"{slug}: {q} cópias de {nm}")
        arq["ci"] = cores_do_deck([cartas[nm]["c"] for nm in principal])
        arq["n_main"], arq["n_side"] = n_main, n_side
        fmt = lambda sec: "\n".join(f"{q} {nm}" for nm, q in sorted(sec.items(), key=lambda kv: kv[0].casefold()))
        open(os.path.join(saida, "listas", slug + ".txt"), "w", encoding="utf-8").write(
            fmt(principal) + ("\n\n" + fmt(side) if side else "") + "\n")
    if erros:
        print("\n".join("ERRO " + e for e in erros))
        sys.exit(1)

    # banidas no Pauper (uma por carta)
    banidas = {}
    for oid, c in por_oracle.items():
        if c["legalities"].get("pauper") == "banned":
            g = "unf" if c.get("set") == "unf" else ("conspiracy" if "Conspiracy" in c.get("type_line", "") else "")
            banidas[colapsar(c["name"])] = {"tipo": tipo_de(c), "oid": oid, "grupo": g}

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
        w = csv.writer(f, lineterminator="\n"); w.writerow(["carta", "cores", "tipo", "mv", "nome_pt", "livre"])
        for n in sorted(cartas):
            c = cartas[n]["c"]
            w.writerow([n, cartas[n]["cores"] or "C", cartas[n]["tipo"], ("%g" % c.get("cmc", 0)) if not eh_terreno(c) else "",
                        pt.get(n, ""), "1" if livre(c) else ""])
    with open(os.path.join(saida, "banidas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["carta", "tipo", "nome_pt", "grupo"])
        for n in sorted(banidas, key=str.casefold):
            w.writerow([n, banidas[n]["tipo"], pt.get(n, ""), banidas[n]["grupo"]])
    meta["scryfall_em"] = time.strftime("%Y-%m-%d")
    json.dump(meta, open(os.path.join(saida, "metagame.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gb = collections.Counter(d["grupo"] for d in banidas.values())
    print(f"{len(meta['arquetipos'])} listas normalizadas; {len(cartas)} cartas ({len([n for n in cartas if pt.get(n)])} com nome em português); "
          f"{len(banidas)} banidas ({gb['unf']} do Unfinity, {gb['conspiracy']} Conspiracy)")


def livre(c):
    return "Basic" in c.get("type_line", "") or "any number of cards named" in (c.get("oracle_text") or "")


if __name__ == "__main__":
    main()
