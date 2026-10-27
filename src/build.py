import json
C=[("Commander (2011)","c11",[("Counterpunch","counterpunch"),("Devour for Power","devour_for_power"),("Heavenly Inferno","heavenly_inferno"),("Mirror Mastery","mirror_mastery"),("Political Puppets","political_puppets")]),
   ("Commander 2013","c13",[("Eternal Bargain","eternal_bargain"),("Evasive Maneuvers","evasive_maneuvers"),("Mind Seize","mind_seize"),("Nature of the Beast","nature_of_the_beast"),("Power Hungry","power_hungry")]),
   ("Commander 2014","c14",[("Built from Scratch","built_from_scratch"),("Forged in Stone","forged_in_stone"),("Guided by Nature","guided_by_nature"),("Peer Through Time","peer_through_time"),("Sworn to Darkness","sworn_to_darkness")]),
   ("Commander 2015","c15",[("Call the Spirits","call_the_spirits"),("Plunder the Graves","plunder_the_graves"),("Seize Control","seize_control"),("Swell the Host","swell_the_host"),("Wade into Battle","wade_into_battle")]),
   ("Commander 2016","c16",[("Breed Lethality","breed_lethality"),("Entropic Uprising","entropic_uprising"),("Invent Superiority","invent_superiority"),("Open Hostility","open_hostility"),("Stalwart Unity","stalwart_unity")]),
   ("Commander 2017","c17",[("Arcane Wizardry","arcane_wizardry"),("Draconic Domination","draconic_domination"),("Feline Ferocity","feline_ferocity"),("Vampiric Bloodlust","vampiric_bloodlust")]),
   ("Commander 2018","c18",[("Adaptive Enchantment","adaptive_enchantment"),("Exquisite Invention","exquisite_invention"),("Nature's Vengeance","natures_vengeance"),("Subjective Reality","subjective_reality")]),
   ("Commander 2019","c19",[("Faceless Menace","faceless_menace"),("Merciless Rage","merciless_rage"),("Mystic Intellect","mystic_intellect"),("Primal Genesis","primal_genesis")]),
   ("Ikoria: Lair of Behemoths Commander","c20",[("Arcane Maelstrom","arcane_maelstrom"),("Enhanced Evolution","enhanced_evolution"),("Ruthless Regiment","ruthless_regiment"),("Symbiotic Swarm","symbiotic_swarm"),("Timeless Wisdom","timeless_wisdom")]),
   ("Zendikar Rising Commander","znc",[("Land's Wrath","lands_wrath"),("Sneak Attack","sneak_attack")]),
   ("Commander Legends","cmr",[("Arm for Battle","arm_for_battle"),("Reap the Tides","reap_the_tides")]),
   ("Kaldheim Commander","khc",[("Elven Empire","elven_empire"),("Phantom Premonition","phantom_premonition")]),
   ("Strixhaven: School of Mages Commander","c21",[("Lorehold Legacies","lorehold_legacies"),("Prismari Performance","prismari_performance"),("Quantum Quandrix","quantum_quandrix"),("Silverquill Statement","silverquill_statement"),("Witherbloom Witchcraft","witherbloom_witchcraft")]),
   ("Adventures in the Forgotten Realms Commander","afc",[("Aura of Courage","aura_of_courage"),("Draconic Rage","draconic_rage"),("Dungeons of Death","dungeons_of_death"),("Planar Portal","planar_portal")]),
   ("Innistrad: Midnight Hunt Commander","mic",[("Coven Counters","coven_counters"),("Undead Unleashed","undead_unleashed")]),
   ("Innistrad: Crimson Vow Commander","voc",[("Spirit Squadron","spirit_squadron"),("Vampiric Bloodline","vampiric_bloodline")]),
   ("Kamigawa: Neon Dynasty Commander","nec",[("Buckle Up","buckle_up"),("Upgrades Unleashed","upgrades_unleashed")]),
   ("Streets of New Capenna Commander","ncc",[("Bedecked Brokers","bedecked_brokers"),("Cabaretti Cacophony","cabaretti_cacophony"),("Maestros Massacre","maestros_massacre"),("Obscura Operation","obscura_operation"),("Riveteers Rampage","riveteers_rampage")]),
   ("Commander Legends: Battle for Baldur's Gate","clb",[("Draconic Dissent","draconic_dissent"),("Exit from Exile","exit_from_exile"),("Mind Flayarrrs","mind_flayarrrs"),("Party Time","party_time")]),
   ("Dominaria United Commander","dmc",[("Legends' Legacy","legends_legacy"),("Painbow","painbow")]),
   ("Warhammer 40,000 Commander","40k",[("Forces of the Imperium","forces_of_the_imperium"),("Necron Dynasties","necron_dynasties"),("The Ruinous Powers","the_ruinous_powers"),("Tyranid Swarm","tyranid_swarm")]),
   ("The Brothers' War Commander","brc",[("Mishra's Burnished Banner","mishras_burnished_banner"),("Urza's Iron Alliance","urzas_iron_alliance")]),
   ("Starter Commander Decks","scd",[("Chaos Incarnate","chaos_incarnate"),("Draconic Destruction","draconic_destruction"),("First Flight","first_flight"),("Grave Danger","grave_danger"),("Token Triumph","token_triumph")]),
   ("Secret Lair","sld",[("Heads I Win, Tails You Lose (2021)","heads_i_win_tails_you_lose")])]
ANOS={"c11":"2011","c13":"2013","c14":"2014","c15":"2015","c16":"2016","c17":"2017","c18":"2018","c19":"2019","c20":"2020","znc":"2020","cmr":"2020","khc":"2021","c21":"2021","sld":"","afc":"2021","mic":"2021","voc":"2021","nec":"2022","ncc":"2022","clb":"2022","dmc":"2022","40k":"2022","brc":"2022","scd":"2022"}
# Grupos de topo; o resto e Universes Within.
GRUPO={"40k":"Universes Beyond","scd":"Starters","sld":"Secret Lair"}
GRUPOS=["Universes Within","Universes Beyond","Starters","Secret Lair"]
data=[]
for nome,pasta,decks in C:
    ds=[]
    for dn,f in decks:
        t=open(f"{pasta}/{f}.txt",encoding="utf-8").read()
        cmd=" / ".join(l.split(" ",1)[1].rsplit(" (",1)[0] for l in t.split("\n\n")[0].split("\n"))
        ds.append({"nome":dn,"comandante":cmd,"arquivo":f+".txt","lista":t})
    data.append({"nome":nome,"ano":ANOS[pasta],"grupo":GRUPO.get(pasta,"Universes Within"),"icone":{"c11":"cmd","sld":"star"}.get(pasta,pasta),"decks":ds})
html=open("template.html",encoding="utf-8").read().replace("__GRUPOS__",json.dumps(GRUPOS)).replace("__DATA__",json.dumps(data,ensure_ascii=False).replace("</","<\\/"))
open("precons_offline.html","w",encoding="utf-8").write(html)
print(len(html))
