#!/usr/bin/env python3
"""Confere as listas dos decks sem acessar a internet (é o que roda no GitHub Actions a cada push).

Uso:  python3 tools/validar.py [--raiz PASTA] [--site PASTA]

  --raiz  pasta com build.py e template.html (padrão: PRECONS_RAIZ ou a pasta acima de tools/).
          As listas ficam em RAIZ/dados/<pasta>/<deck>.txt (repositório, src/) ou em RAIZ/<pasta>/<deck>.txt (pasta de trabalho).
  --site  pasta com index.html e nomes_pt.json publicados: gera o site de novo numa pasta temporária
          e confere se sai idêntico (pega build.py, template.html ou listas não copiados para src/).

Confere em cada deck: formato "qtd Nome (SET) número"; comandante(s), uma linha em branco e o resto;
100 cartas; resto em ordem alfabética; nenhuma carta repetida além dos terrenos básicos; nenhum
SET+número ligado a dois nomes (exceções impressas assim no produto ficam em EXCECOES). Confere também: todo deck do build.py tem arquivo, todo arquivo está no
build.py, toda coleção tem ano, e todo arquivo citado no sw.js existe.
Página de Pauper (dados/pauper/, se existir): ver validar_pauper.
"""
import argparse, collections, csv, glob, os, re, shutil, subprocess, sys, tempfile

LINHA = re.compile(r"^([1-9]\d*) (\S(?:.*\S)?) \((\w+)\) (\S+)$")
# Repetições que existem no produto impresso (a lista fica fiel ao deck vendido).
EXCECOES = {
    # A Wizards confirma: o deck saiu impresso com 2 Mossfire Valley em vez de mais um terreno básico.
    # https://magic.wizards.com/en/news/feature/kamigawa-neon-dynasty-commander-decklists-2022-02-07
    "nec/upgrades_unleashed.txt": {"Mossfire Valley": 2},
}
BASICOS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes",
           "Snow-Covered Plains", "Snow-Covered Island", "Snow-Covered Swamp",
           "Snow-Covered Mountain", "Snow-Covered Forest"}


def ler_build(raiz):
    src = open(os.path.join(raiz, "build.py"), encoding="utf-8").read()
    C = eval(src[src.index("C=") + 2:src.index("ANOS=")])
    ANOS = eval(src[src.index("ANOS=") + 5:src.index("\n", src.index("ANOS="))])
    return C, ANOS


def validar_deck(caminho, rel):
    """Devolve (erros, avisos). Ordem alfabética é aviso, a não ser com --estrito."""
    erros, avisos = [], []
    t = open(caminho, encoding="utf-8").read()
    if not t.endswith("\n") or t.endswith("\n\n"):
        erros.append("o arquivo deve terminar com exatamente uma quebra de linha")
    blocos = t.rstrip("\n").split("\n\n")
    if len(blocos) != 2:
        return erros + [f"esperado comandante(s), uma linha em branco e o resto; achei {len(blocos)} bloco(s)"], avisos
    cmd, resto = blocos[0].split("\n"), blocos[1].split("\n")
    total, nomes, por_numero = 0, collections.Counter(), collections.defaultdict(set)
    for l in cmd + resto:
        m = LINHA.match(l)
        if not m:
            erros.append(f"linha fora do formato: {l!r}")
            continue
        total += int(m[1])
        if m[2] not in BASICOS:
            nomes[m[2]] += int(m[1])
        por_numero[(m[3], m[4])].add(m[2])
    if total != 100:
        erros.append(f"{total} cartas (esperado 100)")
    for n, q in nomes.items():
        if q > 1 and EXCECOES.get(rel, {}).get(n) != q:
            erros.append(f"carta repetida: {n} ({q}x)")
    for (s, n), ns in por_numero.items():
        if len(ns) > 1:
            erros.append(f"({s}) {n} ligado a nomes diferentes: {sorted(ns)}")
    chaves = [LINHA.match(l)[2].casefold() for l in resto if LINHA.match(l)]
    for a, b in zip(chaves, chaves[1:]):
        if b < a:
            avisos.append(f"fora da ordem alfabética: {b!r} depois de {a!r} (corrigir com normalizar.py)")
            break
    return erros, avisos


def gerar_site(raiz, dados, site):
    """Gera o site numa pasta temporária e compara com o publicado."""
    erros = []
    with tempfile.TemporaryDirectory() as tmp:
        for f in ("build.py", "template.html"):
            shutil.copy(os.path.join(raiz, f), tmp)
        for p in os.listdir(dados):
            orig = os.path.join(dados, p)
            if os.path.isdir(orig) and p not in ("raw", "site", "tools", "precons-commander"):
                shutil.copytree(orig, os.path.join(tmp, p))
            elif p.endswith(".csv"):
                shutil.copy(orig, tmp)
        r = subprocess.run([sys.executable, "-I", os.path.join(tmp, "build.py")], capture_output=True, text=True)
        if r.returncode != 0:
            return [f"build.py falhou: {(r.stderr or r.stdout).strip()[-500:]}"]
        for gerado, publicado in (("precons_offline.html", "index.html"), ("nomes_pt.json", "nomes_pt.json")):
            a, b = os.path.join(tmp, gerado), os.path.join(site, publicado)
            if not os.path.exists(a):
                erros.append(f"build.py não gerou {gerado}")
            elif not os.path.exists(b):
                erros.append(f"{publicado} não existe em {site}")
            elif open(a, "rb").read() != open(b, "rb").read():
                erros.append(f"{publicado} publicado difere do gerado a partir de src/ "
                             f"(build.py, template.html ou listas não copiados para src/?)")
    return erros


def validar_pauper(raiz, dados, site):
    """Página de Pauper (pasta pauper/ de dados): listas (60 ou mais + até 15, até 4 cópias, ordem alfabética em cada
    seção, metagame.json cobrindo todas) e, com --site, a página gerada de novo idêntica à publicada em SITE/pauper/."""
    erros = collections.defaultdict(list)
    P = os.path.join(dados, "pauper")
    if not os.path.isdir(P):
        return erros
    import json
    meta = json.load(open(os.path.join(P, "metagame.json"), encoding="utf-8"))
    cartas = {r["carta"]: r for r in csv.DictReader(open(os.path.join(P, "cartas.csv"), encoding="utf-8"))}
    slugs = [a["slug"] for a in meta["arquetipos"]]
    arquivos = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(P, "listas", "*.txt")))
    for x in sorted(set(slugs) ^ set(arquivos)):
        erros["pauper"].append(f"{x}: lista e metagame.json não batem")
    for slug in arquivos:
        rel = f"pauper/{slug}.txt"
        t = open(os.path.join(P, "listas", slug + ".txt"), encoding="utf-8").read()
        if not t.endswith("\n") or t.endswith("\n\n"):
            erros[rel].append("o arquivo deve terminar com exatamente uma quebra de linha")
        blocos = t.rstrip("\n").split("\n\n")
        if len(blocos) > 2:
            erros[rel].append(f"{len(blocos)} blocos (esperado deck e sideboard)"); continue
        qtd, tot = [], collections.Counter()
        for b in blocos:
            n, chaves = 0, []
            for l in b.split("\n"):
                m = LINHA.match(l)
                if not m:
                    erros[rel].append(f"linha fora do formato: {l!r}"); continue
                n += int(m[1]); tot[m[2]] += int(m[1]); chaves.append(m[2].casefold())
                if m[2] not in cartas:
                    erros[rel].append(f"{m[2]} fora de cartas.csv (rodar tools/pauper_normalizar.py)")
            if chaves != sorted(chaves):
                erros[rel].append("fora da ordem alfabética")
            qtd.append(n)
        if qtd[0] < 60:
            erros[rel].append(f"deck principal com {qtd[0]} cartas")
        if len(qtd) > 1 and qtd[1] > 15:
            erros[rel].append(f"sideboard com {qtd[1]} cartas")
        for nome, q in tot.items():
            if q > 4 and not (cartas.get(nome, {}).get("livre") or nome in BASICOS):
                erros[rel].append(f"{q} cópias de {nome}")
    if site:
        with tempfile.TemporaryDirectory() as tmp:
            for f in ("build.py", "build_pauper.py", "template_pauper.html"):
                shutil.copy(os.path.join(raiz, f), tmp)
            shutil.copytree(P, os.path.join(tmp, "pauper"))
            r = subprocess.run([sys.executable, "-I", os.path.join(tmp, "build_pauper.py")], capture_output=True, text=True)
            if r.returncode != 0:
                erros["site"].append(f"build_pauper.py falhou: {(r.stderr or r.stdout).strip()[-500:]}")
            else:
                for gerado, publicado in (("pauper_offline.html", "pauper/index.html"), ("pauper_nomes_pt.json", "pauper/nomes_pt.json")):
                    a, b = os.path.join(tmp, gerado), os.path.join(site, publicado)
                    if not os.path.exists(b):
                        erros["site"].append(f"{publicado} não existe em {site}")
                    elif open(a, "rb").read() != open(b, "rb").read():
                        erros["site"].append(f"{publicado} publicado difere do gerado a partir de src/ (build_pauper.py, template_pauper.html ou dados/pauper não copiados?)")
    return erros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=os.environ.get("PRECONS_RAIZ")
                    or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--site")
    ap.add_argument("--estrito", action="store_true", help="ordem alfabética errada também reprova")
    a = ap.parse_args()
    dados = os.path.join(a.raiz, "dados") if os.path.isdir(os.path.join(a.raiz, "dados")) else a.raiz
    C, ANOS = ler_build(a.raiz)

    erros, avisos = collections.defaultdict(list), collections.defaultdict(list)
    esperados = set()
    for _, pasta, decks in C:
        if pasta not in ANOS:
            erros["build.py"].append(f"coleção {pasta} sem ano em ANOS")
        for _, stem in decks:
            rel = f"{pasta}/{stem}.txt"
            esperados.add(rel)
            caminho = os.path.join(dados, pasta, stem + ".txt")
            if not os.path.exists(caminho):
                erros[rel].append("arquivo não existe")
            else:
                e, w = validar_deck(caminho, rel)
                erros[rel] += e
                (erros if a.estrito else avisos)[rel] += w
    pastas = {p for _, p, _ in C}
    for f in glob.glob(os.path.join(dados, "*", "*.txt")):
        rel = os.path.relpath(f, dados).replace(os.sep, "/")
        if rel.split("/")[0] in pastas and rel not in esperados:
            erros[rel].append("arquivo não está no build.py")

    tab = os.path.join(dados, "decks.csv")
    if os.path.exists(tab):  # tabela de arquétipos (tools/arquetipos.py)
        ARQ = {"tribal", "tokens", "counters", "spellslinger", "graveyard", "artifacts", "enchantments", "lifegain",
               "sacrifice", "voltron", "blink", "lands"}
        vistos = set()
        for r in csv.DictReader(open(tab, encoding="utf-8")):
            vistos.add(r["id"] + ".txt")
            for k in ("arq1", "arq2"):
                if r[k] and r[k] not in ARQ:
                    erros["decks.csv"].append(f"{r['id']}: {k} desconhecido: {r[k]}")
            if not r["arq1"] or r["arq2"] == r["arq1"]:
                erros["decks.csv"].append(f"{r['id']}: arquétipos inválidos")
        for rel in sorted(esperados - vistos):
            erros["decks.csv"].append(f"{rel} não está na tabela (rodar tools/arquetipos.py)")
        for rel in sorted(vistos - esperados):
            erros["decks.csv"].append(f"{rel} está na tabela mas não no build.py")

    if a.site:
        sw = os.path.join(a.site, "sw.js")
        if os.path.exists(sw):
            for arq in re.findall(r'"([^"]+\.(?:html|json|svg|png))"', open(sw, encoding="utf-8").read()):
                if not os.path.exists(os.path.join(a.site, arq)):
                    erros["sw.js"].append(f"cita {arq}, que não existe")
        erros["site"] += gerar_site(a.raiz, dados, a.site)

    for k, v in validar_pauper(a.raiz, dados, a.site).items():
        erros[k] += v
    npauper = len(glob.glob(os.path.join(dados, "pauper", "listas", "*.txt")))
    ruins = {k: v for k, v in erros.items() if v}
    nav = sum(len(v) for v in avisos.values())
    for k in sorted(avisos):
        for e in avisos[k]:
            print(f"AVISO {k}: {e}")
    for k in sorted(ruins):
        for e in ruins[k]:
            print(f"ERRO {k}: {e}")
    print(f"{len(esperados)} decks em {len(C)} coleções" + (f" e {npauper} decks de Pauper" if npauper else "") + " conferidos; "
          + ("nenhum erro" if not ruins else f"{sum(len(v) for v in ruins.values())} erro(s)")
          + (f"; {nav} aviso(s)" if nav else ""))
    sys.exit(1 if ruins else 0)


if __name__ == "__main__":
    main()
