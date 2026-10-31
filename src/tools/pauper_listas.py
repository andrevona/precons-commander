"""Baixa TODAS as listas dos últimos N dias (padrão 30) de cada arquétipo do metagame de Pauper (pauper/metagame.json),
papel e MTGO, a partir da página "All <arquétipo> Decks" do MTGGoldfish (/archetype/<id>/decks?page=N, 50 por página,
mais recentes primeiro). Pedido do usuário em 31/10/2026: variações dentro de cada arquétipo (etapa 1, só dados).

Grava (na pasta de trabalho):
  raw_pauper/indice/<slug>.json   linhas da tabela: data, id da lista, nome dado pelo jogador, jogador, evento, id do evento,
                                  colocação/resultado, cores mostradas pelo MTGGoldfish e origem ("mtgo" ou "papel")
  raw_pauper/todas/<id>.txt       a lista como o MTGGoldfish exporta (/deck/download/<id>: principal, linha em branco, sideboard)
Já baixado não é baixado de novo (dá para interromper e retomar). Um pedido por vez, com pausa, para não sobrecarregar o site.

Origem: o MTGGoldfish não marca papel/MTGO na tabela; os eventos do MTGO têm nomes padronizados (Pauper Challenge NN AAAA-MM-DD,
Pauper League AAAA-MM-DD, Preliminary, Showcase, Qualifier, Premier...). Os demais são de papel.

Uso: python3 tools/pauper_listas.py [--dias 30] [--so-indice] [--arq slug,slug]
"""
import datetime, json, os, re, sys, time, importlib.util

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("pauper_raspar", os.path.join(RAIZ, "tools", "pauper_raspar.py"))
_r = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_r)
baixar = _r.baixar

DIAS = int(sys.argv[sys.argv.index("--dias") + 1]) if "--dias" in sys.argv else 30
SO_INDICE = "--so-indice" in sys.argv
SO_ARQ = sys.argv[sys.argv.index("--arq") + 1].split(",") if "--arq" in sys.argv else None
PAUSA = 0.6
D_IND = os.path.join(RAIZ, "raw_pauper", "indice")
D_LIS = os.path.join(RAIZ, "raw_pauper", "todas")
MTGO = re.compile(r"^(Pauper (Challenge \d+ \d{4}-\d\d-\d\d|League \d{4}-\d\d-\d\d|Preliminary|Showcase|Qualifier|Super Qualifier|Premier|Last Chance|Eternal Weekend Qualifier)|MTGO|MOCS|Magic Online)", re.I)


def linhas(html):
    out = []
    for data, resto in re.findall(r"<tr>\s*<td>(\d{4}-\d\d-\d\d)</td>(.*?)</tr>", html, re.S):
        d = re.search(r'href="/deck/(\d+)">([^<]*)</a>', resto)
        if not d:
            continue
        ev = re.search(r'href="/tournaments?/(\d+)">([^<]*)</a>', resto)
        jog = re.search(r'href="/player/[^"]*">([^<]*)</a>', resto)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", resto, re.S)
        lugar = re.sub(r"<[^>]+>|\s+", " ", tds[3]).strip() if len(tds) > 3 else ""
        evn = (ev.group(2) if ev else "").strip()
        out.append({"data": data, "id": d.group(1), "nome": d.group(2).strip(), "jogador": jog.group(1).strip() if jog else "",
                    "evento": evn, "evento_id": ev.group(1) if ev else "", "lugar": lugar,
                    "cores_goldfish": "".join(re.findall(r"ms-([wubrgc]) ms-cost", resto)).upper(),
                    "origem": "mtgo" if MTGO.search(evn) else "papel"})
    return out


def main():
    meta = json.load(open(os.path.join(RAIZ, "pauper", "metagame.json"), encoding="utf-8"))
    corte = (datetime.date.fromisoformat(meta["raspado_em"]) - datetime.timedelta(days=DIAS)).isoformat()
    os.makedirs(D_IND, exist_ok=True); os.makedirs(D_LIS, exist_ok=True)
    arqs = [a for a in meta["arquetipos"] if not SO_ARQ or a["slug"] in SO_ARQ]
    print(f"{len(arqs)} arquétipos, listas a partir de {corte} (exclusive)", flush=True)
    todas = []
    for k, a in enumerate(arqs, 1):
        arq_ind = os.path.join(D_IND, a["slug"] + ".json")
        if os.path.exists(arq_ind):
            rows = json.load(open(arq_ind, encoding="utf-8"))
        else:
            rows, pg = [], 1
            while True:
                novas = linhas(baixar(f"/archetype/{a['id']}/decks?page={pg}")); time.sleep(PAUSA)
                rows += [x for x in novas if x["data"] > corte]
                if not novas or novas[-1]["data"] <= corte or pg >= 40:
                    break
                pg += 1
            json.dump(rows, open(arq_ind, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        mt = sum(1 for x in rows if x["origem"] == "mtgo")
        print(f"[{k}/{len(arqs)}] {a['nome']}: {len(rows)} listas ({mt} MTGO, {len(rows) - mt} papel); metagame MTGO diz {a['decks']}", flush=True)
        todas += rows
    if SO_INDICE:
        return
    falta = [x for x in todas if not os.path.exists(os.path.join(D_LIS, x["id"] + ".txt"))]
    print(f"listas: {len(todas)}; a baixar: {len(falta)}", flush=True)
    for i, x in enumerate(falta, 1):
        try:
            txt = baixar(f"/deck/download/{x['id']}").replace("\r", "").strip() + "\n"
        except Exception as e:
            print(f"  falhou {x['id']}: {e}", flush=True); time.sleep(5); continue
        open(os.path.join(D_LIS, x["id"] + ".txt"), "w", encoding="utf-8").write(txt)
        if i % 100 == 0:
            print(f"  {i}/{len(falta)} baixadas", flush=True)
        time.sleep(PAUSA)
    print("fim", flush=True)


if __name__ == "__main__":
    main()
