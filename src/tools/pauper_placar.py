"""Placar (vitórias-derrotas) das listas de Pauper que a página mostra (os destaques de pauper/variacoes.json) quando a tabela do
MTGGoldfish só traz a colocação (ex. "2nd" num Challenge). A página da lista diz "Event: Pauper Challenge 32 2026-10-18, 2nd Place, 7-2".
Pedido do usuário em 31/10/2026: no botão da lista, sempre o desempenho (placar), não a colocação.

Grava pauper/placar.json ({id: "7-2"}); o que já está lá não é baixado de novo. Lista sem placar na página fica de fora (a página
mostra a colocação). Rodar depois de tools/pauper_variacoes.py; precisa de www.mtggoldfish.com.

Uso: python3 tools/pauper_placar.py
"""
import gzip, html, json, os, re, time, importlib.util

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("pauper_raspar", os.path.join(RAIZ, "tools", "pauper_raspar.py"))
_r = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_r)
REC = re.compile(r"^\d+-\d+(?:-\d+)?$")


def main():
    var = json.load(open(os.path.join(RAIZ, "pauper", "variacoes.json"), encoding="utf-8"))
    listas = {x["id"]: x for x in json.load(gzip.open(os.path.join(RAIZ, "pauper", "listas.json.gz"), "rt", encoding="utf-8"))["listas"]}
    arq = os.path.join(RAIZ, "pauper", "placar.json")
    placar = json.load(open(arq, encoding="utf-8")) if os.path.exists(arq) else {}
    ids = [i for f in var["familias"] for v in f["variacoes"] for i, _, _ in v["destaques"]] + \
          [i for f in var["familias"] for i, _, _ in f["outras_destaques"]]
    falta = [i for i in ids if not REC.match(listas[i]["lugar"]) and i not in placar]
    print(f"{len(ids)} listas na página; sem placar na tabela: {len(falta)} a buscar")
    for i in falta:
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", _r.baixar("/deck/" + i))))
        m = re.search(r"Event: .*?, \d+(?:st|nd|rd|th) Place, (\d+-\d+(?:-\d+)?) ", t)
        if m:
            placar[i] = m.group(1)
        else:
            print("  sem placar:", i, listas[i]["evento"])
        time.sleep(0.6)
    placar = {k: placar[k] for k in sorted(placar, key=int) if k in set(ids)}  # só o que a página usa
    json.dump(placar, open(arq, "w", encoding="utf-8"), indent=0, sort_keys=False)
    print(f"{len(placar)} placares em pauper/placar.json")


if __name__ == "__main__":
    main()
