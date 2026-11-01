"""Normaliza as listas de Pauper baixadas (todas as dos últimos 30 dias de cada arquétipo, ver tools/pauper_listas.py) para o
formato do site e confere tudo pelo Scryfall. Reescrito em 31/10/2026 para a reorganização por famílias e variações.

Entrada: raw_pauper/indice/<slug>.json e raw_pauper/todas/<id>.txt (tools/pauper_listas.py) e pauper/metagame.json
         (a lista de arquétipos do MTGGoldfish, gravada por tools/pauper_raspar.py).
Saída (pasta pauper/ da pasta de trabalho):
  pauper/listas.json.gz  todas as listas válidas: {raspado_em, dias, listas: [{id, arquetipo, data, nome (dado pelo jogador),
                         jogador, evento, lugar, origem (mtgo/papel), ci (cores do deck), lista}]}, em ordem de id; a lista é
                         "qtd Nome", principal em ordem alfabética, linha em branco, sideboard em ordem alfabética
  pauper/cartas.csv      uma linha por carta das listas: carta, cores, tipo, mv (valor de mana), nome_pt,
                         livre (1 = pode ter mais de 4 cópias: terreno básico ou "any number of cards named")
  pauper/banidas.csv     banidas no Pauper segundo o Scryfall: carta, tipo, nome_pt, grupo ("unf", "conspiracy" ou vazio)

Sem edição nem número (no Pauper a edição não importa; o endstep.cc reconhece a carta pelo nome). Lista com carta que não existe
no Scryfall ou não é legal no Pauper, com menos de 60 cartas, mais de 15 no sideboard ou mais de 4 cópias de uma carta (exceto as
"livres") fica de fora, com aviso. Cartas: Scryfall "oracle cards" (uma por carta; cache/oracle.jsonl.gz); nomes em português:
impressões em português do "all cards" (cache/pt.jsonl, ver tools/atributos.py).

Uso: python3 tools/pauper_normalizar.py [--cache /home/claude/cache_scryfall]
"""
import argparse, collections, csv, gzip, html, json, os, re, sys, time, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atributos import uri_bulk, UA, pt_do_all_cards, tipo_de, colapsar, faces_de  # noqa: E402
import shutil, subprocess

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


def baixar_oracle(cache):
    dest = os.path.join(cache, "oracle.jsonl.gz")
    if not os.path.exists(dest):
        subprocess.check_call(["curl", "-sS", "-m", "580", "-H", "User-Agent: " + UA, "-o", dest, uri_bulk("oracle_cards")])
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(RAIZ, "cache_scryfall"))
    ap.add_argument("--so-arq", default=None, help="slug,slug: só normaliza esses arquétipos e MESCLA na base já publicada (listas.json.gz e cartas.csv); não mexe em banidas.csv nem no metagame.json")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    raw = os.path.join(RAIZ, "raw_pauper")
    saida = os.path.join(RAIZ, "pauper")
    os.makedirs(saida, exist_ok=True)
    meta = json.load(open(os.path.join(saida, "metagame.json"), encoding="utf-8"))

    por_nome, por_oracle = {}, {}
    for l in gzip.open(baixar_oracle(a.cache), "rt", encoding="utf-8"):
        l = l.strip().rstrip(",")
        if not l.startswith("{"):
            continue
        c = json.loads(l)
        if c.get("layout") in ("token", "double_faced_token", "art_series", "emblem"):
            continue
        oid = c.get("oracle_id") or faces_de(c)[0].get("oracle_id")
        por_oracle[oid] = c
    # Nome completo primeiro, depois o nome de cada face: "Seething Song" é a carta comum, não a face de "Blazing Firesinger // Seething Song".
    # Nome repetido: a carta "séria" ganha das coleções "funny".
    ordem = sorted(por_oracle.values(), key=lambda c: c.get("set_type") == "funny")
    for c in ordem:
        por_nome.setdefault(chave_nome(c["name"]), c)
    for c in ordem:
        for f in c.get("card_faces", []):
            por_nome.setdefault(chave_nome(f["name"]), c)

    avisos, cartas, saidas = [], {}, []
    so_arq = a.so_arq.split(",") if a.so_arq else None
    for arq in meta["arquetipos"]:
        if so_arq and arq["slug"] not in so_arq:
            continue
        for x in json.load(open(os.path.join(raw, "indice", arq["slug"] + ".json"), encoding="utf-8")):
            f = os.path.join(raw, "todas", x["id"] + ".txt")
            if not os.path.exists(f):
                avisos.append(f"{x['id']} ({arq['nome']}): lista não baixada"); continue
            texto = open(f, encoding="utf-8").read().replace("\r", "").strip()
            blocos = re.split(r"\n\s*\n", texto)
            erro, secoes, novas = None, [], {}
            for b in blocos[:2]:
                linhas = collections.Counter()
                for l in b.split("\n"):
                    m = LINHA.match(l.strip())
                    if not m:
                        erro = f"linha não reconhecida: {l!r}"; break
                    q, nome = int(m.group(1)), m.group(2)
                    c = por_nome.get(chave_nome(nome)) or por_nome.get(chave_nome(nome.split(" // ")[0])) or por_nome.get(chave_nome(nome.split("/")[0].strip()))
                    if not c:
                        erro = f"{nome} não existe no Scryfall"; break
                    nm = colapsar(c["name"])
                    if c["legalities"].get("pauper") != "legal":
                        erro = f"{nm} não é legal no Pauper ({c['legalities'].get('pauper')})"; break
                    linhas[nm] += q
                    novas[nm] = c
                secoes.append(linhas)
                if erro:
                    break
            if not erro and len(blocos) > 2:
                erro = "mais de duas seções"
            if not erro:
                principal, side = secoes[0], (secoes[1] if len(secoes) > 1 else collections.Counter())
                n_main, n_side = sum(principal.values()), sum(side.values())
                if n_main < 60: erro = f"deck principal com {n_main} cartas"
                elif n_side > 15: erro = f"sideboard com {n_side} cartas"
                else:
                    for nm, q in (principal + side).items():
                        if q > 4 and not livre(novas[nm]):
                            erro = f"{q} cópias de {nm}"; break
            if erro:
                avisos.append(f"{x['id']} ({arq['nome']}): {erro}"); continue
            for nm, c in novas.items():
                if nm not in cartas:
                    cartas[nm] = {"c": c, "cores": cores_da_carta(c), "tipo": tipo_de(c), "oid": c.get("oracle_id") or faces_de(c)[0].get("oracle_id")}
            fmt = lambda sec: "\n".join(f"{q} {nm}" for nm, q in sorted(sec.items(), key=lambda kv: kv[0].casefold()))
            un = html.unescape  # a tabela do MTGGoldfish vem com entidades HTML (ex. "&#39;")
            saidas.append({"id": x["id"], "arquetipo": arq["nome"], "data": x["data"], "nome": un(x["nome"]), "jogador": un(x["jogador"]),
                           "evento": un(x["evento"]), "lugar": un(x["lugar"]), "origem": x["origem"],
                           "ci": cores_do_deck([novas[nm] for nm in principal]),
                           "lista": fmt(principal) + ("\n\n" + fmt(side) if side else "")})
    for v in avisos:
        print("AVISO", v)

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

    linhas_cartas = {n: [n, cartas[n]["cores"] or "C", cartas[n]["tipo"], ("%g" % cartas[n]["c"].get("cmc", 0)) if not eh_terreno(cartas[n]["c"]) else "",
                         pt.get(n, ""), "1" if livre(cartas[n]["c"]) else ""] for n in cartas}
    antigo = None
    if so_arq:  # mesclar: cartas e listas já publicadas ficam como estão
        antigo = json.load(gzip.open(os.path.join(saida, "listas.json.gz"), "rt", encoding="utf-8"))
        with open(os.path.join(saida, "cartas.csv"), newline="", encoding="utf-8") as f:
            rd = csv.reader(f); cab = next(rd); ja = {r[0]: r for r in rd}
        novas_cartas = [n for n in linhas_cartas if n not in ja]
        print(f"mesclar: {len(novas_cartas)} cartas novas no cartas.csv:", "; ".join(sorted(novas_cartas)))
        ja.update({n: linhas_cartas[n] for n in novas_cartas})
        linhas_cartas = ja
    with open(os.path.join(saida, "cartas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["carta", "cores", "tipo", "mv", "nome_pt", "livre"])
        for n in sorted(linhas_cartas):
            w.writerow(linhas_cartas[n])
    if not so_arq:
        with open(os.path.join(saida, "banidas.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n"); w.writerow(["carta", "tipo", "nome_pt", "grupo"])
            for n in sorted(banidas, key=str.casefold):
                w.writerow([n, banidas[n]["tipo"], pt.get(n, ""), banidas[n]["grupo"]])
    if antigo:
        nomes_arq = {arq["nome"] for arq in meta["arquetipos"] if arq["slug"] in so_arq}
        saidas = [x for x in antigo["listas"] if x["arquetipo"] not in nomes_arq] + saidas
    saidas.sort(key=lambda x: int(x["id"]))
    pacote = {"raspado_em": antigo["raspado_em"] if antigo else meta["raspado_em"], "dias": 30, "scryfall_em": antigo["scryfall_em"] if antigo else time.strftime("%Y-%m-%d"), "listas": saidas}
    with open(os.path.join(saida, "listas.json.gz"), "wb") as f:  # mtime=0: o mesmo conteúdo gera sempre o mesmo arquivo
        with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as g:
            g.write(json.dumps(pacote, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if not so_arq:
        meta["scryfall_em"] = pacote["scryfall_em"]
        json.dump(meta, open(os.path.join(saida, "metagame.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gb = collections.Counter(d["grupo"] for d in banidas.values())
    print(f"{len(saidas)} listas normalizadas ({len(avisos)} de fora); {len(cartas)} cartas ({len([n for n in cartas if pt.get(n)])} com nome em português); "
          f"{len(banidas)} banidas ({gb['unf']} do Unfinity, {gb['conspiracy']} Conspiracy)")


def livre(c):
    return "Basic" in c.get("type_line", "") or "any number of cards named" in (c.get("oracle_text") or "")


if __name__ == "__main__":
    main()
