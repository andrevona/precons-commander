"""Etapa 1 da reorganização do Pauper por arquétipos (pedido do usuário em 31/10/2026; só dados, sem mexer no site).

Lê as listas normalizadas (pauper/listas.json.gz, de tools/pauper_normalizar.py, já com as cores de cada lista) e calcula:
  - FAMÍLIAS: os 48 arquétipos do MTGGoldfish juntados pela tabela FAMILIAS (proposta para o usuário revisar);
    para apoiar a revisão, a semelhança entre os arquétipos (cartas do deck principal, sem terrenos básicos);
  - VARIAÇÕES dentro de cada família (decisão do usuário: cores + cartas): agrupamento hierárquico (média) pela
    semelhança de Jaccard ponderada do deck principal (sem básicos), cortado em CORTE; grupos pequenos vão para "Outras";
    nome sugerido = cores (nome da guilda/trio) + o nome mais comum dado pelos jogadores;
  - para cada variação: lista de consenso (60), sideboard típico (15, com a % de listas que levam cada carta),
    nº de listas (MTGO e papel), % das listas e resultados bons (top 8 ou mais vitórias que derrotas).
Grava pauper/variacoes.json (vai para src/dados/pauper; o build_pauper.py lê) e mostra um resumo. As listas de cada
variação (e as "Outras" da família) ficam em ordem de resultado: 1º lugar, top 8, campanhas positivas, as demais; empate: mais recente.

Uso: python3 tools/pauper_variacoes.py [--corte 0.55] [--min 3]
"""
import collections, glob, gzip, json, os, re, sys, unicodedata, importlib.util
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORTE = float(sys.argv[sys.argv.index("--corte") + 1]) if "--corte" in sys.argv else 0.55
MINIMO = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 5
BASICOS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes", "Snow-Covered Plains", "Snow-Covered Island",
           "Snow-Covered Swamp", "Snow-Covered Mountain", "Snow-Covered Forest"}

# Proposta de famílias (para o usuário revisar): arquétipo do MTGGoldfish -> família. Quem não está aqui é família própria.
FAMILIAS = {  # revisada com o usuário em 31/10/2026 (semelhança medida entre arquétipos + decisões dele)
    "Mono Red Madness": "Madness", "Rakdos Madness": "Madness",
    "Blue Terror": "Terror", "Izzet Terror": "Terror", "Dimir Terror": "Terror",
    "Dimir Faeries": "Faeries", "Grixis Faeries": "Faeries",            # Mono-Blue Faeries: família própria (decisão do usuário)
    "Tron": "Tron", "Ephemerate Tron": "Tron",
    "Grixis Affinity": "Affinity", "Esper Affinity": "Affinity", "Dimir Affinity": "Affinity", "4c Affinity": "Affinity",  # Glintblade: própria
    "Grixis Control": "Control", "Dimir Control": "Control",            # semelhança 0,98
    "Golgari Gardens": "Gardens", "Food Gardens": "Gardens",
    "White Aggro": "White Aggro", "Mono-White Aggro": "White Aggro", "Boros Bully": "White Aggro",
    "Esper Ephemerate": "Ephemerate", "Jeskai Ephemerate": "Ephemerate",  # Familiars: própria (decisão do usuário)
    "Snacker Gates": "Gates", "Azorius Gates": "Gates",
    "Mardu Synthesizer": "Synthesizer", "Boros Synthesizer": "Synthesizer", "Boros Moxite": "Synthesizer",
    "Mono Red Rally": "Rally", "Burn": "Rally",                          # semelhança 0,88
    "Gruul Ponza": "Ponza", "Gruul Ramp": "Ponza",                        # semelhança 0,74
    "Jund Wildfire": "Wildfire", "Black Sacrifice": "Sacrifice",
}   # Storm NÃO é família: Ruby, Cycle e Poison Storm quase não se parecem (0,11–0,17)
NOMES_CORES = {"W": "Mono-White", "U": "Mono-Blue", "B": "Mono-Black", "R": "Mono-Red", "G": "Mono-Green", "C": "Colorless",
    "WU": "Azorius", "UB": "Dimir", "BR": "Rakdos", "RG": "Gruul", "WG": "Selesnya", "WB": "Orzhov", "UR": "Izzet",
    "BG": "Golgari", "WR": "Boros", "UG": "Simic", "WUB": "Esper", "UBR": "Grixis", "BRG": "Jund", "WRG": "Naya",
    "WUG": "Bant", "WBG": "Abzan", "WUR": "Jeskai", "UBG": "Sultai", "WBR": "Mardu", "URG": "Temur",
    "WUBR": "4c (WUBR)", "UBRG": "4c (UBRG)", "WBRG": "4c (WBRG)", "WURG": "4c (WURG)", "WUBG": "4c (WUBG)",
    "WUBRG": "5c"}
PALAVRAS_COR = {"Mono-White", "Mono-Blue", "Mono-Black", "Mono-Red", "Mono-Green", "Mono", "White", "Blue", "Black", "Red", "Green",
    "Azorius", "Dimir", "Rakdos", "Gruul", "Selesnya", "Orzhov", "Izzet", "Golgari", "Boros", "Simic", "Esper", "Grixis", "Jund",
    "Naya", "Bant", "Abzan", "Jeskai", "Sultai", "Mardu", "Temur", "4c", "5c"}


def nome_variacao(cores, fam):
    """Cores + nome da família sem as palavras de cor do início (Jund Wildfire, Mono-Blue Faeries, sem "Mono-Red Mono Red Rally")."""
    base = fam.split()
    while len(base) > 1 and base[0] in PALAVRAS_COR:
        base = base[1:]
    if fam == "White Aggro":
        base = ["Aggro"]
    nc = NOMES_CORES.get(cores, cores)
    if nc.startswith("4c (") or nc == "5c":
        return nc.split(" ")[0] + " " + " ".join(base) + (" " + nc[3:] if nc.startswith("4c (") else "")
    return nc + " " + " ".join(base)


def chave(n):
    return "".join(ch for ch in unicodedata.normalize("NFD", n.lower()) if not unicodedata.combining(ch)).strip()


def ler_lista(txt):
    blocos = txt.strip().split("\n\n")
    def ler(b):
        d = collections.Counter()
        for l in b.split("\n"):
            m = re.match(r"^(\d+)\s+(.+)$", l.strip())
            if m:
                d[m.group(2).strip()] += int(m.group(1))
        return d
    return ler(blocos[0]), (ler(blocos[1]) if len(blocos) > 1 else collections.Counter())


def bom(lugar):
    l = lugar.lower()
    m = re.match(r"^(\d+)(st|nd|rd|th)", l)
    if m:
        return int(m.group(1)) <= 8, int(m.group(1)) == 1
    m = re.match(r"^(\d+)-(\d+)(?:-(\d+))?$", l)
    if m:
        return int(m.group(1)) > int(m.group(2)), False
    return False, False


def alocar(medias, total, teto):
    """Lista de 'total' cartas a partir das médias de cópias: parte inteira e depois as maiores frações (maior resto)."""
    q = {k: min(teto(k), int(v)) for k, v in medias.items()}
    falta = total - sum(q.values())
    for k, v in sorted(medias.items(), key=lambda kv: -(kv[1] - int(kv[1]))):
        if falta <= 0:
            break
        if v - int(v) > 0 and q[k] < teto(k):
            q[k] += 1; falta -= 1
    return {k: v for k, v in q.items() if v > 0}


def ordem_resultado(x):
    """Melhores primeiro: 1º lugar; 2º–8º (pela colocação); campanhas com mais vitórias que derrotas (5-0, 4-1...);
    as demais. Empate: mais recente primeiro (a ordenação por data é feita antes, e o sort é estável)."""
    l = x["lugar"].lower()
    m = re.match(r"^(\d+)(st|nd|rd|th)", l)
    if m:
        p = int(m.group(1))
        return (0, 0, 0) if p == 1 else ((1, p, 0) if p <= 8 else (4, p, 0))
    m = re.match(r"^(\d+)-(\d+)(?:-(\d+))?$", l)
    if m:
        v, d = int(m.group(1)), int(m.group(2))
        return (2, d, -v) if v > d else (3, d - v, -v)
    return (5, 0, 0)


def ordenar(ls):
    ls = sorted(ls, key=lambda x: (x["data"], int(x["id"])), reverse=True)
    return sorted(ls, key=ordem_resultado)


# Variação: só as 2 listas de melhor resultado com 5+ cartas diferentes do consenso no principal (pedido do usuário, 01/11/2026;
# antes eram 5); "Outras" (sem consenso): as 5 melhores.
DESTAQUES, DESTAQUES_OUTRAS, DIF_MIN = 2, 5, 5


def principal_sem_basicos(x):
    return collections.Counter({c: q for c, q in x["main"].items() if c not in BASICOS})


def diferenca(a, b):
    """Nº de cartas trocadas entre dois decks (soma das diferenças de cópias / 2)."""
    return sum(abs(a[k] - b[k]) for k in set(a) | set(b)) // 2


def destaques(ordenadas, cons=None, cons_side=None):
    """Até DESTAQUES listas (DESTAQUES_OUTRAS sem consenso), na ordem de resultado: cada uma com pelo menos DIF_MIN cartas diferentes do consenso no deck
    principal (sem básicos) e das já escolhidas, e de outro jogador. Sem consenso ("Outras"): só a diferença entre elas.
    Devolve [[id, cartas diferentes no principal, no sideboard]] (as diferenças valem só com consenso)."""
    esc, jog = [], set()
    for x in ordenadas:
        m = principal_sem_basicos(x)
        d = diferenca(m, cons) if cons is not None else 0
        if cons is not None and d < DIF_MIN:
            continue
        if x["jogador"] in jog or any(diferenca(m, principal_sem_basicos(y)) < DIF_MIN for y, _, _ in esc):
            continue
        ds = diferenca(x["side"], cons_side) if cons_side is not None else 0
        esc.append((x, d, ds)); jog.add(x["jogador"])
        if len(esc) == (DESTAQUES if cons is not None else DESTAQUES_OUTRAS):
            break
    return [[x["id"], d, ds] for x, d, ds in esc]


def slug(n):
    return re.sub(r"[^a-z0-9]+", "_", chave(n).replace("'", "")).strip("_")


def main():
    pacote = json.load(gzip.open(os.path.join(RAIZ, "pauper", "listas.json.gz"), "rt", encoding="utf-8"))
    listas = []
    for x in pacote["listas"]:
        mp, sd = ler_lista(x["lista"])
        x.update(familia=FAMILIAS.get(x["arquetipo"], x["arquetipo"]), main=mp, side=sd, cores=x["ci"])
        listas.append(x)
    total = len(listas)
    print(f"{total} listas lidas")

    # Semelhança entre arquétipos (perfil = % de listas que levam cada carta do principal, sem básicos): cosseno
    perfis = collections.defaultdict(collections.Counter); nl = collections.Counter()
    for x in listas:
        nl[x["arquetipo"]] += 1
        for n in x["main"]:
            if n not in BASICOS: perfis[x["arquetipo"]][n] += 1
    arqs = sorted(perfis, key=lambda a: -nl[a]); voc = sorted({n for p in perfis.values() for n in p}); ix = {n: i for i, n in enumerate(voc)}
    M = np.zeros((len(arqs), len(voc)))
    for i, a in enumerate(arqs):
        for n, k in perfis[a].items(): M[i, ix[n]] = k / nl[a]
    M /= np.linalg.norm(M, axis=1, keepdims=True); S = M @ M.T
    semelhantes = {a: [(arqs[j], round(float(S[i, j]), 2)) for j in np.argsort(-S[i]) if j != i][:3] for i, a in enumerate(arqs)}

    # Variações dentro de cada família
    saida = []
    por_fam = collections.defaultdict(list)
    for x in listas: por_fam[x["familia"]].append(x)
    for fam, ls in sorted(por_fam.items(), key=lambda kv: -len(kv[1])):
        voc = sorted({n for x in ls for n in x["main"] if n not in BASICOS}); ix = {n: i for i, n in enumerate(voc)}
        X = np.zeros((len(ls), len(voc)))
        for i, x in enumerate(ls):
            for n, k in x["main"].items():
                if n in ix: X[i, ix[n]] = k
        if len(ls) > 1:
            D = np.zeros((len(ls), len(ls)))
            for i in range(len(ls)):
                mn = np.minimum(X[i], X).sum(1); mx = np.maximum(X[i], X).sum(1)
                D[i] = 1 - mn / np.maximum(mx, 1)
            np.fill_diagonal(D, 0); D = (D + D.T) / 2
            rot = fcluster(linkage(squareform(D, checks=False), "average"), CORTE, "distance")
        else:
            rot = np.array([1])
        grupos = collections.defaultdict(list)
        for x, r in zip(ls, rot): grupos[r].append(x)
        principais = [g for g in grupos.values() if len(g) >= MINIMO]
        outras = [x for g in grupos.values() if len(g) < MINIMO for x in g]
        pres_fam = collections.Counter(n for x in ls for n in x["main"])
        vs = []
        for g in sorted(principais, key=len, reverse=True):
            n = len(g)
            cores = collections.Counter(x["cores"] for x in g).most_common(1)[0][0]
            pres = collections.Counter(n2 for x in g for n2 in x["main"])
            fora = len(ls) - n
            assin = sorted((c for c in pres if c not in BASICOS),
                           key=lambda c: -(pres[c] / n - (pres_fam[c] - pres[c]) / max(fora, 1)))[:4] if fora else []
            nomes_j = collections.Counter(x["nome"] for x in g).most_common(3)
            med_m = collections.Counter(); med_s = collections.Counter(); pres_s = collections.Counter()
            for x in g:
                for c, k in x["main"].items(): med_m[c] += k / n
                for c, k in x["side"].items(): med_s[c] += k / n; pres_s[c] += 1
            teto = lambda c: 99 if c in BASICOS else 4
            cons = alocar(med_m, 60, teto); side = alocar(med_s, 15, teto)
            b = [bom(x["lugar"]) for x in g]
            vs.append({"nome": nome_variacao(cores, fam), "cores": cores, "n": n,
                       "mtgo": sum(1 for x in g if x["origem"] == "mtgo"), "pct": round(100 * n / total, 1),
                       "bons": sum(1 for v in b if v[0]), "primeiros": sum(1 for v in b if v[1]),
                       "cores_listas": collections.Counter(x["cores"] for x in g).most_common(4),
                       "arquetipos": collections.Counter(x["arquetipo"] for x in g).most_common(),
                       "nomes_jogadores": nomes_j, "assinatura": assin,
                       "consenso": sorted(([q, c] for c, q in cons.items()), key=lambda t: t[1]),
                       "side": sorted(([q, c, round(100 * pres_s[c] / n)] for c, q in side.items()), key=lambda t: t[1]),
                       "papel": n - sum(1 for x in g if x["origem"] == "mtgo"),
                       "listas": [x["id"] for x in ordenar(g)],
                       "destaques": destaques(ordenar(g), collections.Counter({c: q for c, q in cons.items() if c not in BASICOS}),
                                              collections.Counter(side))})
        # Família que junta vários arquétipos do MTGGoldfish: a variação que é quase toda de um deles (>= 60%) fica com o nome dele
        # (ex. "Boros Moxite" dentro de Synthesizer), se nenhuma outra variação já usou esse nome.
        usados = set()
        if len({x["arquetipo"] for x in ls}) > 1:
            for v in vs:
                arq, k = v["arquetipos"][0]
                if k >= 0.6 * v["n"] and arq not in usados and arq != fam:  # "Tron" dentro de Tron não diz nada: fica o nome pelas cores
                    v["nome"] = arq; usados.add(arq)
        vistos = collections.Counter()
        for v in vs:
            vistos[v["nome"]] += 1
            if vistos[v["nome"]] > 1 and v["assinatura"]:
                v["nome"] += " (" + v["assinatura"][0] + ")"
        for v in vs:
            v["slug"] = slug(v["nome"])
        mt = sum(1 for x in ls if x["origem"] == "mtgo")
        saida.append({"familia": fam, "slug": slug(fam), "n": len(ls), "mtgo": mt, "papel": len(ls) - mt, "pct": round(100 * len(ls) / total, 1),
                      "outras_ids": [x["id"] for x in ordenar(outras)],
                      "outras_destaques": destaques(ordenar(outras)),
                      "arquetipos": collections.Counter(x["arquetipo"] for x in ls).most_common(),
                      "variacoes": vs, "outras": len(outras), "outras_cores": collections.Counter(x["cores"] for x in outras).most_common(5)})
    dup = [k for lista in ([v["slug"] for f in saida for v in f["variacoes"]], [f["slug"] for f in saida])
           for k, n in collections.Counter(lista).items() if n > 1]  # variações e famílias: cada grupo sem repetição
    if dup:
        sys.exit(f"ERRO: identificadores repetidos: {dup}")
    mt = sum(1 for x in listas if x["origem"] == "mtgo")
    json.dump({"raspado_em": pacote["raspado_em"], "dias": pacote["dias"], "total": total, "mtgo": mt, "papel": total - mt,
               "corte": CORTE, "minimo": MINIMO, "familias": saida, "semelhantes": semelhantes},
              open(os.path.join(RAIZ, "pauper", "variacoes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for f in saida:
        print(f"\n== {f['familia']}: {f['n']} listas ({f['pct']}%) de {[a for a, _ in f['arquetipos']]}; {len(f['variacoes'])} variações + {f['outras']} em Outras")
        for v in f["variacoes"]:
            print(f"   {v['nome']:<34} {v['n']:>4} ({v['mtgo']} MTGO)  bons {v['bons']}  1º {v['primeiros']}  | jogadores: {[k for k, _ in v['nomes_jogadores']]} | assinatura: {v['assinatura']}")


if __name__ == "__main__":
    main()
