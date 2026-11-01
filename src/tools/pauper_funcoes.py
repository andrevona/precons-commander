#!/usr/bin/env python3
"""Funções de cada carta de Pauper, para o botão Otimizar do Comparar decks.

Lê pauper/cartas.csv (todas as cartas das listas) e o texto Oracle do Scryfall (cache em cache_scryfall/oracle_funcoes.json;
sem o cache, baixa pela API /cards/collection) e grava pauper/funcoes.json: {carta: "etiquetas separadas por espaço"}.

Etiquetas de "o que a carta é" (montam o perfil do adversário):
  cri (criatura), t1 / t2 (criatura com resistência até 1 / até 2), voo, hex (hexproof ou proteção difícil de alvejar),
  art (artefato, inclusive terreno), enc (encantamento), aura, inst, feit (feitiço), cem (usa o próprio cemitério),
  dano (dano direto no adversário), neb (neblina), terx (terreno especial: Tron, Gates), comb (peça de combo ou motor),
  ter (terreno: nunca sai), mv5 (custa 5 ou mais), azul, verm (cor), plano (carta do plano do deck: não sai por falta de alvo).
  alvo (a resposta a criaturas ESCOLHE alvo: não funciona contra hexproof; usada com x-cri e x-t1/x-t2. Dano em área sem alvo, como End the Festivities, não leva).
Etiquetas de resposta, "x-<alvo>" (o que a carta enfrenta):
  x-azul, x-verm, x-art, x-enc, x-aura, x-cem, x-t1 / x-t2 (varredura que mata resistência 1 / 2), x-cri (remoção pontual),
  x-hex (sacrifício: passa por hexproof), x-dano (ganho de vida / prevenção contra dano), x-inst, x-feit, x-ncri
  (mágicas não-criatura), x-comb (descarte, contramágica ampla), x-terx (destruição de terreno), x-voo, x-neb, x-rem
  (protege das remoções do adversário).
As regras automáticas olham o texto Oracle; as listas MANUAL corrigem e completam (sempre vencem).
Uso: python3 tools/pauper_funcoes.py [--ver]   (--ver imprime as cartas com resposta, para revisar)
"""
import csv, json, os, re, sys, time, urllib.request

RAIZ = os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(RAIZ, "pauper")
CACHE = os.path.join(RAIZ, "cache_scryfall", "oracle_funcoes.json")

# Correções à mão: carta -> (etiquetas a acrescentar, etiquetas a tirar). "*" em tirar = começa do zero (só as de acrescentar e as
# de tipo/cor). Motivo resumido no comentário quando não é óbvio.
MANUAL = {
    # cores-ódio (as regras já pegam; aqui só o plano)
    "Counterspell": ("plano x-comb", ""), "Lose Focus": ("plano x-comb", ""), "Spell Pierce": ("x-ncri", "x-comb"),
    "Force Spike": ("plano", ""), "Bring the Ending": ("plano x-comb", ""), "Arcane Denial": ("plano x-comb", ""),
    "Prohibit": ("x-comb", ""), "Metallic Rebuke": ("x-comb", ""), "Remove Soul": ("x-cri", "x-comb"),
    "Mirrorshell Crab": ("x-comb", "x-ncri"),
    "Spellstutter Sprite": ("plano", "x-comb x-cri"), "Snap": ("plano", "x-cri"),
    # descarte
    "Duress": ("x-ncri x-comb", ""), "Pilfer": ("x-comb", ""), "Mesmeric Fiend": ("x-comb", ""),
    "Thorn of the Black Rose": ("plano", "x-comb"), "Okiba-Gang Shinobi": ("plano", ""), "Dinrova Horror": ("plano", ""),
    "Refurbished Familiar": ("plano", "x-comb"), "Kitchen Imp": ("plano", ""),
    # cemitério: ódio de verdade
    "Extract a Confession": ("x-hex x-cri", "x-cem"), "Vitu-Ghazi Inspector": ("x-dano", "x-cem"),
    "Rooftop Percher": ("x-cem", ""), "Masked Vandal": ("x-art x-enc x-aura", "x-cem"), "Faerie Macabre": ("x-cem", "x-comb"),
    "Bojuka Bog": ("x-cem", ""), "Stream of Thought": ("", "x-cem"), "Barkform Harvester": ("", "x-cem"),
    "Call Damage Control": ("", "x-cem x-art x-enc x-aura"), "Momentary Blink": ("", "x-cem x-cri"),
    "Crypt Incursion": ("x-cem x-dano", "x-t1 x-t2"),
    # remoção / varredura
    "Arms of Hadar": ("x-t2", ""), "Krark-Clan Shaman": ("x-t1 plano", "x-voo"), "Scattershot Archer": ("x-voo", "x-t1 x-t2"),
    "Tithing Blade // Consuming Sepulcher": ("x-hex x-cri", "x-cem x-dano"), "Accursed Marauder": ("x-hex x-cri", ""),
    "Diabolic Edict": ("x-hex x-cri", ""), "Grim Bauble": ("x-cri", "x-cem"), "Nihil Spellbomb": ("plano", ""), "Lifelink": ("x-dano plano", ""),
    "Structural Distortion": ("x-terx", ""), "Mortician Beetle": ("", "x-cri"), "Desert": ("x-t1", "x-cri"),
    "Gut Shot": ("x-cri x-t1 alvo", ""), "Electrickery": ("x-t1", ""), "End the Festivities": ("x-t1", ""),
    "Suffocating Fumes": ("x-t1", ""), "Dry Spell": ("x-t1", ""), "Shrivel": ("x-t1", ""), "Holy Light": ("x-t1", ""),
    "Breath Weapon": ("x-t2", ""), "Fiery Cannonade": ("x-t2", ""), "Drown in Sorrow": ("x-t2", ""),
    "Swirling Sandstorm": ("x-t2", "x-cem x-voo"), "Fang Dragon // Forktail Sweep": ("x-t1 plano", ""),
    "Writhing Necromass": ("plano", "x-cem x-t1 x-t2"), "Crypt Rats": ("x-t2 plano", ""), "Pestilence": ("x-t1 plano", ""),
    "Cast into the Fire": ("x-t1 x-art alvo", "x-t2"), "Suplex": ("x-cri x-art", ""), "Searing Blaze": ("x-cri", ""),
    "Thraben Charm": ("x-cri x-enc x-aura x-cem", ""), "Destroy Evil": ("x-cri x-enc x-aura", ""),
    "Spinning Darkness": ("x-cri x-dano", "x-cem"), "Dark Withering": ("x-cri", "x-cem x-comb"),
    "Lignify": ("x-cri", ""), "Cryoshatter": ("x-cri", ""), "Ram Through": ("x-cri", ""), "Monstrous Emergence": ("x-cri", ""),
    "Journey to Nowhere": ("x-cri", ""), "Last Breath": ("x-cri", ""), "Ultimate Alliance": ("x-cri", ""),
    "Firebending Lesson": ("x-cri", ""), "Snuff Out": ("x-cri", ""), "Cast Down": ("x-cri", ""), "Cut Down": ("x-cri", ""),
    "Tragic Slip": ("x-cri", ""), "Skred": ("x-cri", ""), "Dispatch": ("x-cri", ""), "Galvanic Blast": ("plano", ""),
    "Lightning Bolt": ("plano", ""), "Chain Lightning": ("plano", ""), "Fireblast": ("plano", ""), "Lava Dart": ("plano x-t1 alvo", ""),
    "Pinnacle Kill-Ship": ("plano", ""), "Barrels of Blasting Jelly": ("plano", ""), "Baleful Strix": ("plano", ""),
    "Sleep of the Dead": ("plano", ""), "Deem Inferior": ("plano", ""), "Recoil": ("plano", ""),
    "Ice-Fang Coatl": ("plano", ""), "Defile": ("x-cri", ""), "Grapple with Death": ("x-cri x-art x-enc", ""),
    "Fungal Infection": ("x-t1 alvo", ""),
    # artefatos / encantamentos
    "Krark-Clan Grunt": ("plano", ""), "Gorilla Shaman": ("x-art", ""), "Annul": ("x-art x-enc x-aura", "x-comb"),
    "Steel Sabotage": ("x-art", ""), "Serene Heart": ("x-aura", "x-enc"), "Fangren Marauder": ("x-art x-dano", "x-cem"),
    "Troublemaker Ouphe": ("x-art x-enc x-aura", ""), "Scour from Existence": ("x-art x-enc x-cri", ""),
    "Heritage Reclamation": ("x-art x-enc x-aura x-cem", ""), "Origin of Metalbending": ("x-art x-enc x-aura", "x-hex x-rem"),
    "Cleansing Wildfire": ("plano", "x-terx"),
    # vida / anti-dano
    "Weather the Storm": ("x-dano plano", ""), "Hallow": ("x-dano", ""), "Prismatic Strands": ("x-dano plano", "x-cem x-t2"),
    "Campfire": ("x-dano plano", "x-cem"), "Navigator's Compass": ("x-dano", ""), "Martyr of Sands": ("x-dano", ""),
    "Spirit Link": ("x-dano", ""), "Healer of the Glade": ("x-dano", ""), "Nylea's Disciple": ("x-dano", ""),
    "Bramble Wurm": ("x-dano plano", "x-cem"), "Primordial Pachyderm": ("x-dano", ""), "Spinewoods Paladin": ("x-dano", ""),
    "Wellwisher": ("x-dano", ""), "Pulse of Murasa": ("x-dano", "x-cem"), "Gnaw to the Bone": ("x-dano plano", "x-cem x-t1 x-t2"),
    "Sylvok Lifestaff": ("x-dano", ""), "Unexpected Fangs": ("x-dano", ""), "Moment's Peace": ("x-dano neb plano", "x-cem"),
    "Tamiyo's Safekeeping": ("x-rem x-dano", ""), "Lifelink": ("x-dano", ""), "Union of the Third Path": ("plano", "x-dano"),
    # proteção
    "Standard Bearer": ("x-rem", ""), "Coalition Honor Guard": ("x-rem", ""), "Loran's Escape": ("x-rem plano", "x-art x-hex"),
    "Apostle's Blessing": ("x-rem plano", "x-art x-hex"), "Spare from Evil": ("x-rem", "x-hex"), "Mask of Law and Grace": ("x-rem x-verm", "x-hex"),
    "Guardian of the Guildpact": ("x-rem", "x-hex"), "Mutagenic Growth": ("plano", ""), "Seal of Strength": ("plano", ""),
    "Snakeskin Veil": ("plano", ""), "Vines of Vastwood": ("plano", ""),
    # terrenos
    "Spreading Seas": ("x-terx", ""), "Mwonvuli Acid-Moss": ("x-terx", ""), "Raze": ("x-terx", ""), "Earth Rift": ("x-terx", "x-cem"),
    "Rancid Earth": ("x-terx", "x-cem x-t1 x-t2"), "Thermokarst": ("x-terx plano", ""), "Crop Rotation": ("", ""),
    # outras de side
    "Flaring Pain": ("x-neb", "x-cem"), "Stonehorn Dignitary": ("x-t2 x-dano", ""), "Avenging Hunter": ("plano", ""),
    "Murmuring Mystic": ("plano", ""), "Writhing Chrysalis": ("plano", ""),
    # peças de combo ou motores (alvo de descarte e contramágica ampla)
    "Balustrade Spy": ("comb", ""), "Dread Return": ("comb", ""), "Lotleth Giant": ("comb", ""),
    "Inside Out": ("comb", ""), "Tireless Tribe": ("comb", ""), "Aurora Eidolon": ("comb", ""),
    "Ghostly Flicker": ("comb", ""), "Mnemonic Wall": ("comb", ""), "Archaeomancer": ("comb", ""), "Ephemerate": ("comb", ""),
    "Sunscape Familiar": ("comb", ""), "God-Pharaoh's Faithful": ("comb", ""), "Axebane Guardian": ("comb", ""),
    "Seething Song": ("comb", ""), "Desperate Ritual": ("comb", ""), "Manamorphose": ("comb", ""), "Glimpse the Impossible": ("comb", ""),
    "Goblin Anarchomancer": ("comb", ""), "Thornscape Familiar": ("comb", ""), "Seize the Storm": ("comb", ""),
    "Songs of the Damned": ("comb", ""), "Reaping the Graves": ("comb", ""), "Infectious Inquiry": ("comb", ""),
    "Guttersnipe": ("comb", ""), "Kessig Flamebreather": ("comb", ""), "Basilisk Gate": ("comb", ""),
    "Bonder's Ornament": ("comb", ""), "Tolarian Terror": ("cem", ""), "Cryptic Serpent": ("cem", ""),
    "Rally at the Hornburg": ("comb", ""), "Goblin Bushwhacker": ("comb", ""), "Crossover Collaboration": ("comb", ""),
    "Stinkweed Imp": ("comb cem", ""), "Satyr Wayfinder": ("cem", ""), "Circle of the Land Druid": ("cem", ""),
    "Armadillo Cloak": ("comb", ""), "Ancestral Mask": ("comb", ""),
}
TRON = {"Urza's Tower", "Urza's Mine", "Urza's Power Plant"}


def oracle(nomes):
    d = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    falta = [n for n in nomes if achar(d, n) is None]
    for i in range(0, len(falta), 75):
        body = json.dumps({"identifiers": [{"name": n.split(" // ")[0]} for n in falta[i:i + 75]]}).encode()
        r = urllib.request.Request("https://api.scryfall.com/cards/collection", data=body, headers={
            "Content-Type": "application/json", "Accept": "application/json", "User-Agent": "precons-commander/1.0"})
        for c in json.load(urllib.request.urlopen(r))["data"]:
            fs = c.get("card_faces") or [c]
            d[c["name"]] = {"tipo": c.get("type_line", ""), "txt": c.get("oracle_text") or " // ".join(f.get("oracle_text", "") for f in fs),
                            "p": fs[0].get("power"), "t": fs[0].get("toughness"), "kw": c.get("keywords", []),
                            "cores": c.get("colors") or fs[0].get("colors", []), "cmc": c.get("cmc")}
        time.sleep(0.15)
    if falta:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True); json.dump(d, open(CACHE, "w"), ensure_ascii=False)
    return d


def achar(d, n):
    if n in d: return d[n]
    for k in d:
        if k.split(" // ")[0] == n.split(" // ")[0]: return d[k]
    return None


def etiquetas(n, c, cores):
    tipo = c["tipo"].split(" // ")[0]; txt = c["txt"].lower(); kw = set(c["kw"]); e = set()
    alvo = re.sub(r"(up to )?(one |two )?target [\w ,/-]*? you control|you may sacrifice [^.]*|sacrifice (a|an|another) [^.:]*", "", txt)  # o que mexe nas próprias cartas não é resposta
    terreno = "Land" in tipo
    if "Creature" in tipo:
        e.add("cri")
        try: t = int(c["t"])
        except (TypeError, ValueError): t = 2
        if t <= 1: e.add("t1")
        if t <= 2: e.add("t2")
        if "Flying" in kw: e.add("voo")
        if kw & {"Hexproof", "Shroud"}: e.add("hex")
    if "Artifact" in tipo: e.add("art")
    if "Enchantment" in tipo: e.add("enc")
    if "Aura" in tipo: e.add("aura")
    if "Instant" in tipo: e.add("inst")
    if "Sorcery" in tipo: e.add("feit")
    if "Gate" in tipo or n in TRON: e.add("terx")
    if "U" in cores and not terreno: e.add("azul")
    if "R" in cores and not terreno: e.add("verm")
    if not terreno and re.search(r"flashback|escape|unearth|embalm|delve|dredge|threshold|from your graveyard|in your graveyard", txt): e.add("cem")
    if re.search(r"damage to (any target|each opponent|target player|target opponent|each player)|each opponent loses|damage to that (spell's|artifact's) controller", txt): e.add("dano")
    if "prevent all combat damage" in txt: e.add("neb")
    # respostas
    if re.search(r"if it's blue|target blue|blue permanent", alvo): e.add("x-azul")
    if re.search(r"if it's red|target red|red permanent", alvo): e.add("x-verm")
    if re.search(r"(destroy|exile) (up to \w+ )?(target|two target) (noncreature )?artifacts?|artifact or enchantment|target artifact you don't control|counter target artifact|target noncreature artifact", alvo): e.add("x-art")
    if re.search(r"(destroy|exile) target enchantment|artifact or enchantment|all auras", alvo): e.update(["x-enc", "x-aura"])
    if re.search(r"exile (target player's|each opponent's|all) graveyards?|exile all graveyards|cards? from (a|target player's) graveyards?|from graveyards", alvo): e.add("x-cem")
    m = re.search(r"(?:deals? (\d+) damage to (?:each|all)[^.]*creature|creatures?[^.]*get -(\d+)/-\d+|each creature[^.]*-(\d+)/-\d+)", alvo)
    if m and not re.search(r"target creature gets", alvo[max(0, m.start() - 20):m.end()]):
        k = int(next(x for x in m.groups() if x)); e.add("x-t1" if k <= 1 else "x-t2")
    if re.search(r"(destroy|exile) target (nonblack |nonlegendary |nonartifact |attacking )?creature|damage to (any target|target creature)|target creature (an opponent controls )?gets -\d|deals damage equal[^.]*target creature|(player|opponent|players|opponents) sacrifices? an? (nontoken )?creature|fights", alvo): e.add("x-cri")
    if re.search(r"(target player|each player|each opponent|target opponent) sacrifices? an? (nontoken )?creature", alvo): e.add("x-hex")
    if re.search(r"counter target instant", alvo): e.add("x-inst")
    if re.search(r"counter target sorcery", alvo): e.add("x-feit")
    if re.search(r"counter target noncreature|choose a noncreature, nonland", alvo): e.add("x-ncri")
    if re.search(r"counter target spell(?! if)|choose a nonland card", alvo): e.add("x-comb")
    if re.search(r"destroy target land", alvo): e.add("x-terx")
    if re.search(r"damage can't be prevented", alvo): e.add("x-neb")
    if re.search(r"each creature with flying", alvo): e.add("x-voo")
    add, tira = MANUAL.get(n, ("", ""))
    if tira == "*": e = {x for x in e if not x.startswith("x-")}
    else: e -= set(tira.split())
    e |= set(add.split())
    # plano: carta do plano (não sai por falta de alvo). Respostas estreitas (não-criatura, sem dano ao jogador) não são.
    resp = any(x.startswith("x-") for x in e)
    if not terreno and (not resp or "cri" in e or "dano" in e): e.add("plano")
    if terreno: e.discard("plano"); e.add("ter")
    elif (c.get("cmc") or 0) >= 5: e.add("mv5")
    return " ".join(sorted(e))


def main():
    cartas = list(csv.DictReader(open(os.path.join(P, "cartas.csv"), encoding="utf-8")))
    d = oracle([r["carta"] for r in cartas])
    sem = [r["carta"] for r in cartas if achar(d, r["carta"]) is None]
    if sem: raise SystemExit("ERRO: sem texto Oracle: %s" % sem)
    nomes = {r["carta"] for r in cartas}
    fora = sorted(k for k in MANUAL if k not in nomes and k.strip() == k)
    out = {r["carta"]: etiquetas(r["carta"], achar(d, r["carta"]), r["cores"]) for r in cartas}
    json.dump(out, open(os.path.join(P, "funcoes.json"), "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, indent=0)
    print("%d cartas; %d com alguma resposta" % (len(out), sum(1 for v in out.values() if "x-" in v)))
    if fora: print("(MANUAL com cartas fora das listas atuais: %d)" % len(fora))
    if "--ver" in sys.argv:
        for k in sorted(out):
            if "x-" in out[k] or "comb" in out[k]: print(k, "|", out[k])


if __name__ == "__main__":
    main()
