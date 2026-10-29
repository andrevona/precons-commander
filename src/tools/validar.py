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
               "sacrifice", "voltron", "blink", "lands", "midrange"}
        vistos = set()
        for r in csv.DictReader(open(tab, encoding="utf-8")):
            vistos.add(r["id"] + ".txt")
            for k in ("arq1", "arq2"):
                if r[k] and r[k] not in ARQ:
                    erros["decks.csv"].append(f"{r['id']}: {k} desconhecido: {r[k]}")
            if not r["arq1"] or r["arq2"] == r["arq1"] or (r["arq1"] == "midrange" and r["arq2"]):
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

    ruins = {k: v for k, v in erros.items() if v}
    nav = sum(len(v) for v in avisos.values())
    for k in sorted(avisos):
        for e in avisos[k]:
            print(f"AVISO {k}: {e}")
    for k in sorted(ruins):
        for e in ruins[k]:
            print(f"ERRO {k}: {e}")
    print(f"{len(esperados)} decks em {len(C)} coleções conferidos; "
          + ("nenhum erro" if not ruins else f"{sum(len(v) for v in ruins.values())} erro(s)")
          + (f"; {nav} aviso(s)" if nav else ""))
    sys.exit(1 if ruins else 0)


if __name__ == "__main__":
    main()
