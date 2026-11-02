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
  Alcance do x-dano (02/11/2026, v148; sem nenhuma delas é ganho de vida, que vale contra combate e dano direto, não contra veneno):
  so-comb (só previne/pula o COMBATE: neblina, Stonehorn Dignitary), so-mag (só dano de MÁGICA: Hallow), prev (previne dano em
  geral, inclusive o de infect). O template_pauper.html pesa isso contra a forma de vitória de cada variação (VENCE no build_pauper.py).
Etiquetas de resposta, "x-<alvo>" (o que a carta enfrenta):
  x-azul, x-verm, x-art, x-enc, x-aura, x-cem, x-t1 / x-t2 (varredura que mata resistência 1 / 2), x-cri (remoção pontual),
  x-hex (sacrifício: passa por hexproof), x-dano (ganho de vida / prevenção contra dano), x-inst, x-feit, x-ncri
  (mágicas não-criatura), x-comb (descarte, contramágica ampla), x-terx (destruição de terreno), x-voo, x-neb, x-rem
  (protege das remoções do adversário).
As regras automáticas olham o texto Oracle; as listas MANUAL corrigem e completam (sempre vencem).
AUDITORIA (01/11/2026) corrige depois do MANUAL e cada entrada cita o TRECHO do Oracle que a justifica (o script para se o trecho
não estiver na carta). A trava conferir() compara as etiquetas de resposta com o texto e PARA com erro em contradições (ex. x-t1 de
área numa carta que escolhe alvo, x-cri num efeito -N/-0 ou de 1 de dano, x-enc sem "enchantment"); casos certos ficam em EXCECOES,
com o motivo. Carta nova: ler o Oracle antes de marcar (regra do usuário: "ler a carta explica a carta").
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
    "Diabolic Edict": ("x-hex x-cri", ""), "Grim Bauble": ("x-cri", "x-cem"), "Nihil Spellbomb": ("plano", ""),
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

# Auditoria de 01/11/2026 (leitura do texto Oracle de todas as cartas com resposta e das correções do MANUAL, depois do erro do
# Cast into the Fire): carta -> (etiquetas a acrescentar, a tirar, TRECHO do Oracle que justifica). Aplicada depois do MANUAL.
# O trecho tem de estar no texto da carta (minúsculas), senão o script para: correção nova SEMPRE com o trecho lido na carta.
AUDITORIA = {
    # -N/-0 não mata nada: não é remoção
    "Brinebarrow Intruder": ("", "x-cri", "gets -2/-0"), "Cogwork Wrestler": ("", "x-cri", "gets -2/-0"),
    "Humbling Elder": ("", "x-cri", "gets -2/-0"), "Dizzy Spell": ("", "x-cri", "gets -3/-0"),
    # dano pequeno COM alvo: só mata resistência 1 (ou 2) e não passa por hexproof
    "Cuombajj Witches": ("x-t1 alvo", "", "deals 1 damage to any target"), "Flame Jab": ("x-t1 alvo", "", "deals 1 damage to any target"),
    "Granger Guildmage": ("x-t1 alvo", "", "deals 1 damage to any target"), "Icatian Javelineers": ("x-t1 alvo", "", "deals 1 damage to any target"),
    "Viridian Longbow": ("x-t1 alvo", "", "deals 1 damage to any target"), "Peppersmoke": ("x-t1 alvo", "", "target creature gets -1/-1"),
    "Shambling Ghast": ("x-t1 alvo", "", "gets -1/-1"), "Piracy Charm": ("x-t1 alvo", "", "target creature gets +2/-1"),
    "Grim Bauble": ("x-t2 alvo", "", "gets -2/-2"), "Pyrite Spellbomb": ("x-t2 alvo", "", "deals 2 damage to any target"),
    "Stab": ("x-t2 alvo", "", "target creature gets -2/-2"), "Desert": ("alvo", "", "target attacking creature"),
    # contramágica de criatura: passa por hexproof (não alveja a criatura)
    "Remove Soul": ("x-hex", "", "counter target creature spell"), "Essence Scatter": ("x-cri x-hex", "", "counter target creature spell"),
    "Exclude": ("x-cri x-hex", "", "counter target creature spell"), "Preemptive Strike": ("x-cri x-hex", "", "counter target creature spell"),
    "Glorious Gale": ("x-cri x-hex", "", "counter target creature spell"), "Soul Manipulation": ("x-cri x-hex", "", "counter target creature spell"),
    # alcance real do efeito
    "Befoul": ("x-cri", "", "destroy target land or nonblack creature"), "Fire of Orthanc": ("x-terx", "", "destroy target artifact or land"),
    "Pillage": ("x-terx", "", "destroy target artifact or land"), "Kenku Artificer": ("", "x-art", "on up to one target noncreature artifact"),
    "Confound": ("x-rem", "x-comb", "counter target spell that targets a creature"),
    "Disrupt": ("x-feit", "", "instant or sorcery spell"), "Judge's Familiar": ("x-feit", "", "instant or sorcery spell"),
    "Muddle the Mixture": ("x-feit", "", "instant or sorcery spell"),
    "Pick Your Poison": ("x-art x-enc x-aura x-voo", "x-cri x-hex", "sacrifices a creature with flying"),
    "Guerrilla Gorilla": ("x-enc x-aura", "", "noncreature enchantment"), "Pinnacle Kill-Ship": ("x-cri", "", "10 damage to up to one target creature"),
    "Sagittars' Volley": ("", "x-cri x-t1", "destroy target creature with flying"), "Smash to Dust": ("", "x-cri", "target creature with defender"),
    "Spider Food": ("x-enc x-aura x-voo", "", "artifact, enchantment, or creature with flying"),
    "Stonehorn Dignitary": ("so-comb", "x-t2", "skips their next combat phase"), "Tinder Wall": ("", "x-cri", "target creature it's blocking"),
    "Tyrant's Choice": ("", "x-cri x-hex", "or the vote is tied"),  # 2 jogadores: o adversário empata e escolhe perder 4 de vida
    # respostas que a regra automática não pegou
    "Banishing Light": ("x-cri x-art x-enc x-aura", "", "exile target nonland permanent an opponent controls"),
    "Celestial Flare": ("x-cri x-hex", "", "sacrifices an attacking or blocking creature"), "Choking Sands": ("x-terx", "", "destroy target non-swamp land"),
    "Coercion": ("x-comb", "", "reveals their hand"), "Divest": ("x-comb", "", "artifact or creature card"),
    "Solve for Disappointment": ("x-comb", "", "nonland permanent card"), "Ebony Charm": ("x-cem", "", "from a single graveyard"),
    "Faerie Trickery": ("x-comb", "", "counter target non-faerie spell"), "Harsh Sustenance": ("x-cri", "", "x damage to any target"),
    "Corrupt": ("x-cri", "", "damage to any target"), "Martyr of Ashes": ("x-t1", "", "damage to each creature without flying"),
    "Rust": ("x-art", "", "from an artifact source"),
    "Grapple with Death": ("", "x-enc x-aura", "destroy target artifact or creature"),  # o MANUAL marcava encantamento por engano
    # --- 01/11/2026 (2ª leitura): as outras 672 cartas das listas, lidas uma a uma ---
    # remoção que a regra automática não pegou
    "Ashes to Ashes": ("x-cri", "", "exile two target nonartifact creatures"),
    "Bind the Monster": ("x-cri", "", "doesn't untap during its controller's untap step"),
    "Blossombind": ("x-cri", "", "can't become untapped"),
    "Cartouche of Strength": ("x-cri", "", "fight target creature an opponent controls"),
    "Debt to the Kami": ("x-cri x-hex x-enc x-aura", "", "target opponent exiles a creature they control"),
    "Galvanic Discharge": ("x-cri", "", "choose target creature or planeswalker"),
    "Oubliette": ("x-cri", "", "target creature phases out"),
    "Sunlance": ("x-cri", "", "3 damage to target nonwhite creature"),
    "Unable to Scream": ("x-cri", "", "enchanted creature loses all abilities"),
    "Utter Insignificance": ("x-cri", "", "enchanted creature loses all abilities"),
    "Rolling Thunder": ("x-cri dano", "", "x damage divided as you choose among any number of targets"),
    "Fire // Ice": ("x-t2 alvo", "", "2 damage divided as you choose among one or two targets"),
    "Fume Spitter": ("x-t1 alvo", "", "put a -1/-1 counter on target creature"),
    "Aerial Volley": ("x-voo alvo", "", "among one, two, or three target creatures with flying"),
    "Whiteout": ("x-voo", "", "all creatures lose flying"),
    "Spidersilk Armor": ("x-voo", "", "have reach"),
    # encantamentos, terrenos, cores
    "Aura Flux": ("x-enc x-aura", "", "other enchantments have"),
    "Reverent Silence": ("x-enc x-aura", "", "destroy all enchantments"),
    "Contaminated Ground": ("x-terx", "", "enchanted land is a swamp"),
    "Circle of Protection: Red": ("x-verm x-dano prev", "", "red source of your choice"),
    "Circle of Protection: Blue": ("x-azul", "", "blue source of your choice"),
    "Crimson Acolyte": ("x-verm x-rem", "", "target creature gains protection from red"),
    "Obsidian Acolyte": ("x-rem", "", "target creature gains protection from black"),
    "Shield of Duty and Reason": ("x-rem x-azul", "", "protection from green and from blue"),
    # descarte
    "Cry of Contrition": ("x-comb", "", "target player discards a card"),
    "Mind Drain": ("x-comb", "", "target opponent discards two cards"),
    "Mind Extraction": ("x-comb", "", "reveals their hand and discards all cards"),
    "Raven's Crime": ("x-comb", "", "target player discards a card"),
    # protege das remoções
    "Benevolent Blessing": ("x-rem plano", "", "protection from the chosen color"),
    "Blacksmith's Skill": ("x-rem plano", "", "gains hexproof and indestructible"),
    "Octopus Form": ("x-rem", "", "gains hexproof"),
    "Orcish Medicine": ("x-rem", "", "lifelink or indestructible"),
    "Whispersilk Cloak": ("x-rem plano", "", "has shroud"),
    "Your Temple Is Under Attack": ("x-rem", "", "creatures you control gain indestructible"),
    "Wrap in Vigor": ("x-rem", "", "regenerate each creature you control"),
    # ganho de vida / prevenção (contra dano)
    "Arashin Cleric": ("x-dano", "", "you gain 3 life"), "Aven Riftwatcher": ("x-dano", "", "you gain 2 life"),
    "Boulderbranch Golem": ("x-dano", "", "you gain life equal to its power"), "Feed the Clan": ("x-dano", "", "you gain 5 life"),
    "Lone Missionary": ("x-dano", "", "you gain 4 life"), "Orim's Cure": ("x-dano prev", "", "prevent the next 4 damage"),
    "Peach Garden Oath": ("x-dano", "", "you gain 2 life for each creature you control"), "Renewed Faith": ("x-dano", "", "you gain 6 life"),
    "Rest for the Weary": ("x-dano", "", "target player gains 4 life"), "Rhystic Circle": ("x-dano prev", "", "prevent that damage"),
    "Sunspring Expedition": ("x-dano", "", "you gain 8 life"), "Trufflesnout": ("x-dano", "", "you gain 4 life"),
    # neblinas que a regra não pegou
    "Ethereal Haze": ("neb", "", "prevent all damage that would be dealt by creatures"),
    "Moment of Silence": ("neb", "", "skips their next combat phase"),
    # perda de vida do adversário (alcance do deck, como dano direto)
    "Abundant Maw": ("dano", "", "target opponent loses 3 life"), "Alms of the Vein": ("dano", "", "target opponent loses 3 life"),
    "Bump in the Night": ("dano", "", "target opponent loses 3 life"), "Essence Harvest": ("dano", "", "target player loses x life"),
    "Foul-Tongue Shriek": ("dano", "", "target opponent loses 1 life for each attacking creature"),
    "Fruit of Tizerus": ("dano", "", "target player loses 2 life"), "Hopeless Nightmare": ("dano", "", "each opponent discards a card and loses 2 life"),
    "Rite of Consumption": ("dano", "", "power to target player or planeswalker"), "Tempting Witch": ("dano", "", "target player loses 3 life"),
    "Vampire's Kiss": ("dano", "", "target player loses 2 life"),
    # terreno que só dá 1 de dano uma vez não faz do deck um deck de dano
    "Abraded Bluffs": ("", "dano", "deals 1 damage to target opponent"), "Jagged Barrens": ("", "dano", "deals 1 damage to target opponent"),
    "Lonely Arroyo": ("", "dano", "deals 1 damage to target opponent"),
    # revisão do estrategia_pauper.md (01/11/2026): proteção só contra criaturas, não contra mágicas de remoção
    "Spare from Evil": ("", "x-rem", "protection from non-human creatures"),
    # ganho de vida pequeno (2) não conta como resposta contra dano (decisão do usuário, 01/11/2026); o MANUAL marcava x-dano
    "Primordial Pachyderm": ("", "x-dano", "you gain 2 life"),
    "Vitu-Ghazi Inspector": ("", "x-dano", "you gain 2 life"),
    # usa o cemitério
    "Exhume": ("cem comb", "", "puts a creature card from their graveyard onto the battlefield"),
    # Slivers (01/11/2026): o bônus vale para o próprio Sliver ("All Sliver creatures" inclui ele), então a resistência em jogo é maior que a impressa
    "Muscle Sliver": ("", "t1", "All Sliver creatures get +1/+1"),          # 1/1 impresso, 2/2 em jogo
    "Sinew Sliver": ("", "t1", "All Sliver creatures get +1/+1"),           # idem
    "Predatory Sliver": ("", "t1", "Sliver creatures you control get +1/+1"),  # idem
    "Plated Sliver": ("", "t1", "All Sliver creatures get +0/+1"),          # 1/1 impresso, 1/2 em jogo
    "Winged Sliver": ("voo", "", "All Sliver creatures have flying"),       # ele mesmo voa (o Scryfall não lista Flying como palavra-chave)
    "Benevolent Bodyguard": ("x-rem", "", "gains protection from the color of your choice"),  # sacrifica para proteger a criatura de remoção da cor escolhida
    # Alcance da proteção contra dano (02/11/2026, v148; caso do usuário: Moment's Peace contra o Golgari Spy Combo, que vence com o
    # dano ao entrar do Lotleth Giant, não em combate). Stonehorn Dignitary, Orim's Cure, Circle of Protection: Red e Rhystic Circle
    # já tinham entrada acima: as etiquetas novas (so-comb, prev) foram juntadas lá.
    "Moment's Peace": ("so-comb", "", "prevent all combat damage"),
    "Hallow": ("so-mag", "", "prevent all damage target spell would deal"),
    "Prismatic Strands": ("prev", "", "prevent all damage that sources of the color of your choice would deal"),
}
# Contradições que a trava (conferir) acusa mas estão certas, com o motivo
EXCECOES = {
    "Smash to Dust": "modo 3 é dano em área sem alvo; os outros modos alvejam artefato/defensor",
    "Tragic Slip": "-1/-1, mas -13/-13 com morbid",
    "Plagued Rusalka": "-1/-1 repetível (um sacrifício por ativação)",
    "Scattershot": "1 de dano por cópia, com storm",
    "Makeshift Munitions": "1 de dano repetível, um sacrifício por vez",
    "Arms of Hadar": "alveja o JOGADOR (criaturas dele ganham -2/-2): passa por hexproof",
    "Rancid Earth": "dano em área só com limiar",
    "Electrickery": "com overload não tem alvo",
    "Vandalblast": "com overload não tem alvo",
    "Swirling Sandstorm": "5 de dano em área só com limiar",
    "Martyr of Ashes": "X de dano em área, X = cartas vermelhas reveladas",
    "Crypt Rats": "X de dano em área",
    "Pestilence": "1 de dano em área repetível",
    "Krark-Clan Shaman": "1 de dano em área repetível",
    "Rolling Thunder": "X de dano dividido entre quaisquer alvos (\"any number of targets\"): mata criaturas, escolhendo alvo",
}


def conferir(n, e, txt):
    """Trava: confere as etiquetas de resposta contra o texto Oracle. Devolve a lista de problemas."""
    t, p = txt.lower(), []
    alvo_cri = re.search(r"target [\w ,-]*creatures?|any target|each of (up to )?\w+ target", t)
    area = re.search(r"(each|all) (other )?(non-?[\w-]+ )?(attacking )?creatures?|creatures [^.]*get -\d|overload", t)
    if "alvo" in e and "target" not in t: p.append("marcada com alvo, mas o texto não diz target")
    for k in ("x-t1", "x-t2"):
        if k in e and "alvo" not in e:
            if not area: p.append("%s (dano/-X em área) sem efeito em área no texto" % k)
            elif re.search(r"each of (up to )?\w+ target", t): p.append("%s: 'each of ... target' escolhe alvo (marcar alvo)" % k)
            elif alvo_cri and not re.search(r"(each|all) (other )?(non-?[\w-]+ )?creatures?|creatures [^.]*get -\d", t): p.append("%s: só efeito com alvo (marcar alvo)" % k)
    # tamanho do efeito: maior dano ou maior -X na resistência (efeito variável, "for each", ou que destrói/exila não conta)
    ks = [int(a or b) for a, b in re.findall(r"deals (\d+) damage to (?:each|all|any target|target creature|up to one target creature)|gets? -\d+/-(\d+)", t)]
    if ks and not re.search(r"for each|equal to|destroy|exile|sacrific", t):
        k = max(ks)
        if "x-t2" in e and k <= 1: p.append("x-t2, mas o efeito é de %d" % k)
        if "x-t1" in e and k >= 2 and "x-t2" not in e: p.append("x-t1, mas o efeito é de %d (x-t2?)" % k)
        if "x-cri" in e and not ({"x-t1", "x-t2", "x-hex"} & e) and k <= 1 and "morbid" not in t: p.append("x-cri com efeito de só %d (usar x-t1 alvo)" % k)
    if "x-cri" in e:
        if not (alvo_cri or re.search(r"sacrifices?|fights?|counter target creature|target (nonland )?permanent|enchant creature|"
                                       r"target creature or|up to one target creature|target opponent", t)):
            p.append("x-cri sem alvo de criatura nem sacrifício no texto")
        if re.search(r"-\d+/-0", t) and not re.search(r"-\d+/-[1-9]|destroy|damage|exile|sacrific", t): p.append("x-cri, mas só -N/-0")
    if "x-hex" in e and not re.search(r"sacrific|counter target creature spell|exiles a creature they control", t): p.append("x-hex sem sacrifício nem contramágica de criatura")
    precisa = {"x-art": r"artifact|target permanent|nonland permanent", "x-enc": r"enchantment|target permanent|nonland permanent",
               "x-aura": r"aura|enchantment|target permanent|nonland permanent", "x-cem": r"graveyard", "x-azul": r"blue|island",
               "x-verm": r"\bred\b", "x-terx": r"\bland", "x-inst": r"instant", "x-feit": r"sorcery", "x-voo": r"flying",
               "x-ncri": r"noncreature", "x-comb": r"counter target|discard|reveals|choose a nonland", "x-neb": r"prevent|can't be prevented",
               "x-dano": r"life|prevent|skips", "x-rem": r"hexproof|protection|indestructible|flagbearer|regenerate|shroud|target"}
    for k, rx in precisa.items():
        if k in e and not re.search(rx, t): p.append("%s sem '%s' no texto" % (k, rx))
    if "x-dano" in e and re.search(r"combat damage|combat phase", t) and not re.search(r"gain|lifelink", t) and "so-comb" not in e:
        p.append("x-dano que só vale no combate sem so-comb")
    if "so-comb" in e and not re.search(r"combat damage|combat phase", t): p.append("so-comb sem 'combat' no texto")
    if "prev" in e and "prevent" not in t: p.append("prev sem 'prevent' no texto")
    return p


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
    if n in AUDITORIA:
        add, tira, trecho = AUDITORIA[n]
        if trecho.lower() not in txt.lower(): raise SystemExit("ERRO: AUDITORIA de %s cita %r, que não está no texto Oracle" % (n, trecho))
        e -= set(tira.split()); e |= set(add.split())
    # plano: carta do plano (não sai por falta de alvo). Respostas estreitas (não-criatura, sem dano ao jogador) não são.
    resp = any(x.startswith("x-") for x in e)
    if not terreno and (not resp or "cri" in e or "dano" in e): e.add("plano")
    if terreno: e.discard("plano"); e.add("ter")
    elif (c.get("cmc") or 0) >= 5: e.add("mv5")
    return " ".join(sorted(e))


def chaves_repetidas():
    """Trava: chave repetida em MANUAL/AUDITORIA/EXCECOES (num dicionário do Python a última some com a anterior sem aviso)."""
    import ast
    rep = []
    for no in ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read()).body:
        if isinstance(no, ast.Assign) and isinstance(no.value, ast.Dict) and no.targets[0].id in ("MANUAL", "AUDITORIA", "EXCECOES"):
            ks = [k.value for k in no.value.keys if isinstance(k, ast.Constant)]
            rep += ["%s: %s" % (no.targets[0].id, k) for k in sorted({k for k in ks if ks.count(k) > 1})]
    if rep: raise SystemExit("ERRO: chave repetida (juntar numa entrada só):\n  " + "\n  ".join(rep))


def main():
    chaves_repetidas()
    cartas = list(csv.DictReader(open(os.path.join(P, "cartas.csv"), encoding="utf-8")))
    d = oracle([r["carta"] for r in cartas])
    sem = [r["carta"] for r in cartas if achar(d, r["carta"]) is None]
    if sem: raise SystemExit("ERRO: sem texto Oracle: %s" % sem)
    nomes = {r["carta"] for r in cartas}
    fora = sorted(k for k in MANUAL if k not in nomes and k.strip() == k)
    out = {r["carta"]: etiquetas(r["carta"], achar(d, r["carta"]), r["cores"]) for r in cartas}
    prob = [(k, x) for k in sorted(out) if k not in EXCECOES for x in conferir(k, set(out[k].split()), achar(d, k)["txt"])]
    if prob:
        raise SystemExit("ERRO: etiquetas que contradizem o texto Oracle (corrigir em MANUAL/AUDITORIA, com o trecho lido na carta, "
                         "ou justificar em EXCECOES):\n" + "\n".join("  %s: %s" % x for x in prob))
    json.dump(out, open(os.path.join(P, "funcoes.json"), "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, indent=0)
    print("%d cartas; %d com alguma resposta" % (len(out), sum(1 for v in out.values() if "x-" in v)))
    if fora: print("(MANUAL com cartas fora das listas atuais: %d)" % len(fora))
    if "--ver" in sys.argv:
        for k in sorted(out):
            if "x-" in out[k] or "comb" in out[k]: print(k, "|", out[k])


if __name__ == "__main__":
    main()
