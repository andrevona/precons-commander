#!/usr/bin/env python3
"""Gera cartas.csv e impressoes.csv a partir das listas dos decks e do Scryfall (só o que o site usa: identidade de cor
dos comandantes e nome em português; também confere que toda carta das listas existe no Scryfall).

Uso:  python3 tools/atributos.py [--cache PASTA] [--pasta RAIZ]   (RAIZ padrão: PRECONS_RAIZ ou a pasta acima de tools/)

Lê todos os decks (RAIZ/<pasta>/<deck>.txt, ignorando raw, site, tools e precons-commander) e grava em RAIZ:

  impressoes.csv  uma linha por impressão (edição + número, como no mtg.wtf):
                  set, numero, nome_lista, carta (nome canônico do Scryfall)
  cartas.csv      uma linha por carta (chave = carta):
                  carta, identidade, nome_pt, origem_pt

Convenções:
  identidade:         identidade de cor, letras na ordem WUBRG (ex. "WU"); "C" = incolor.
  nome_pt / origem_pt: nome impresso em português no Scryfall ("papel"); vazio se nunca foi impresso em português.
                      (Tradução do Arena: ainda sem fonte.)

Fontes (cache em --cache): bulk "Default Cards" (inglês, 1 impressão por carta/edição) e as impressões em
português tiradas do bulk "All Cards" (~400 MB, lido em fluxo; só as linhas lang=pt ficam no cache).
Precisa de acesso a api.scryfall.com e data.scryfall.io (liberar em claude.ai > Configurações > Capacidades).
"""
import argparse, csv, glob, gzip, json, os, re, subprocess, sys, collections

UA = "precons-commander/1.0"
ORDEM = "WUBRG"


def curl_json(url):
    return json.loads(subprocess.check_output(["curl", "-sS", "-m", "60", "-H", "User-Agent: " + UA, "-H", "Accept: application/json", url]))


def uri_bulk(tipo):
    for x in curl_json("https://api.scryfall.com/bulk-data")["data"]:
        if x["type"] == tipo:
            return x["jsonl_download_uri"]
    sys.exit("bulk não encontrado: " + tipo)


def baixar_default(cache):
    dest = os.path.join(cache, "default.jsonl.gz")
    if not os.path.exists(dest):
        url = uri_bulk("default_cards")
        subprocess.check_call(["curl", "-sS", "-m", "580", "-H", "User-Agent: " + UA, "-o", dest, url])
    return dest


def pt_do_all_cards(cache):
    """Extrai do bulk All Cards só as impressões em português (fluxo, sem gravar os 400 MB)."""
    dest = os.path.join(cache, "pt.jsonl")
    if os.path.exists(dest):
        return dest
    url = uri_bulk("all_cards")
    p = subprocess.Popen(["curl", "-sS", "-m", "580", "-H", "User-Agent: " + UA, url], stdout=subprocess.PIPE)
    n = 0
    with gzip.open(p.stdout, "rt", encoding="utf-8") as f, open(dest + ".tmp", "w", encoding="utf-8") as out:
        for linha in f:
            if '"lang":"pt"' not in linha:
                continue
            c = json.loads(linha)
            if c.get("lang") != "pt":
                continue
            faces = [fc.get("printed_name") for fc in c.get("card_faces", [])]
            out.write(json.dumps({"oracle_id": c.get("oracle_id") or (c.get("card_faces") or [{}])[0].get("oracle_id"),
                                  "released_at": c.get("released_at", ""), "printed_name": c.get("printed_name"),
                                  "faces": faces}, ensure_ascii=False) + "\n")
            n += 1
    if p.wait() != 0:
        sys.exit("falha ao baixar o All Cards")
    os.replace(dest + ".tmp", dest)
    print("impressões em português encontradas:", n)
    return dest


def colapsar(nome):
    """'Sol Ring // Sol Ring' (carta reversível do Secret Lair com as duas faces iguais) vira 'Sol Ring'."""
    partes = nome.split(" // ")
    return partes[0] if len(partes) > 1 and len(set(partes)) == 1 else nome


def cores_de(letras):
    s = "".join(c for c in ORDEM if c in letras)
    return s or "C"


def faces_de(c):
    return c.get("card_faces") or [c]


def nomes_validos(c):
    s = {c["name"].lower()}
    for k in ("flavor_name", "printed_name"):
        if c.get(k):
            s.add(c[k].lower())
    for f in c.get("card_faces", []):
        for k in ("name", "flavor_name", "printed_name"):
            if f.get(k):
                s.add(f[k].lower())
    return s


def decks(raiz):
    for f in sorted(glob.glob(os.path.join(raiz, "*", "*.txt"))):
        pasta = os.path.basename(os.path.dirname(f))
        if pasta in ("raw", "site", "tools", "precons-commander"):
            continue
        yield f


def linhas_dos_decks(raiz):
    por_impressao = {}
    n = 0
    for f in decks(raiz):
        n += 1
        for l in open(f, encoding="utf-8"):
            m = re.match(r"^\d+ (.+) \(([A-Z0-9]+)\) (\S+)$", l.strip())
            if m:
                por_impressao[(m.group(2), m.group(3))] = m.group(1)
    return n, por_impressao


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/atributos-cache")
    ap.add_argument("--pasta", default=os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)

    ndecks, impr = linhas_dos_decks(a.pasta)
    print("decks lidos:", ndecks, "| impressões únicas:", len(impr))

    idx = collections.defaultdict(list)
    for l in gzip.open(baixar_default(a.cache), "rt", encoding="utf-8"):
        c = json.loads(l)
        idx[(c["set"], c["collector_number"].lower())].append(c)

    linhas_impr, cartas, sem = [], {}, []
    for (s, num), nome in sorted(impr.items()):
        cs = idx.get((s.lower(), num.lower())) or idx.get((s.lower(), re.sub(r"[ab]$", "", num.lower())))
        base = re.sub(r" \(Prepared\)$", "", nome).lower()  # "(Prepared)" é marcação do mtg.wtf (decks SOC), não faz parte do nome
        c = next((x for x in cs or [] if base in nomes_validos(x)), None)
        if not c:
            sem.append((s, num, nome))
            continue
        canon = colapsar(c["name"])
        linhas_impr.append([s, num, nome, canon])
        oid = c.get("oracle_id") or faces_de(c)[0].get("oracle_id")
        if canon in cartas:
            cartas[canon]["oids"].add(oid)
            continue
        cartas[canon] = {"oids": {oid}, "identidade": cores_de(c.get("color_identity") or [])}
    if sem:
        print("SEM CORRESPONDÊNCIA:", len(sem), sem[:10])
        sys.exit(1)

    # português: entre as impressões em português da carta, prefere a que tem todas as faces traduzidas, depois
    # a que difere do inglês (há impressões só com o nome em inglês), depois a mais recente
    oid_carta = {o: n for n, d in cartas.items() for o in d["oids"]}
    cand = collections.defaultdict(list)
    for l in open(pt_do_all_cards(a.cache), encoding="utf-8"):
        d = json.loads(l)
        n = oid_carta.get(d["oracle_id"])
        if not n:
            continue
        faces = [x for x in d["faces"] if x]
        completo = bool(d["printed_name"]) or (bool(faces) and len(faces) == len(d["faces"]))
        nome = colapsar(d["printed_name"] or " // ".join(faces))
        if nome:
            cand[n].append((completo, nome != n, d["released_at"], nome))
    pt = {n: max(v)[3] for n, v in cand.items()}

    with open(os.path.join(a.pasta, "impressoes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["set", "numero", "nome_lista", "carta"]); w.writerows(linhas_impr)
    with open(os.path.join(a.pasta, "cartas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["carta", "identidade", "nome_pt", "origem_pt"])
        for nome in sorted(cartas):
            d = cartas[nome]
            p = pt.get(nome)
            w.writerow([nome, d["identidade"], p or "", "papel" if p else ""])
    com_pt = len(pt)
    print("impressões:", len(linhas_impr), "| cartas:", len(cartas), "| com nome em português:", com_pt)


if __name__ == "__main__":
    main()
