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
   ("Phyrexia: All Will Be One Commander","onc",[("Corrupting Influence","corrupting_influence"),("Rebellion Rising","rebellion_rising")]),
   ("March of the Machine Commander","moc",[("Call for Backup","call_for_backup"),("Cavalry Charge","cavalry_charge"),("Divine Convocation","divine_convocation"),("Growing Threat","growing_threat"),("Tinker Time","tinker_time")]),
   ("Tales of Middle-earth Commander","ltc",[("Elven Council","elven_council"),("Food and Fellowship","food_and_fellowship"),("Riders of Rohan","riders_of_rohan"),("The Hosts of Mordor","the_hosts_of_mordor")]),
   ("Commander Masters","cmm",[("Eldrazi Unbound","eldrazi_unbound"),("Enduring Enchantments","enduring_enchantments"),("Planeswalker Party","planeswalker_party"),("Sliver Swarm","sliver_swarm")]),
   ("Wilds of Eldraine Commander","woc",[("Fae Dominion","fae_dominion"),("Virtue and Valor","virtue_and_valor")]),
   ("Doctor Who","who",[("Blast from the Past","blast_from_the_past"),("Masters of Evil","masters_of_evil"),("Paradox Power","paradox_power"),("Timey-Wimey","timey_wimey")]),
   ("The Lost Caverns of Ixalan Commander","lcc",[("Ahoy Mateys","ahoy_mateys"),("Blood Rites","blood_rites"),("Explorers of the Deep","explorers_of_the_deep"),("Veloci-Ramp-Tor","veloci_ramp_tor")]),
   ("Murders at Karlov Manor Commander","mkc",[("Blame Game","blame_game"),("Deadly Disguise","deadly_disguise"),("Deep Clue Sea","deep_clue_sea"),("Revenant Recon","revenant_recon")]),
   ("Fallout","pip",[("Hail, Caesar","hail_caesar"),("Mutant Menace","mutant_menace"),("Science!","science"),("Scrappy Survivors","scrappy_survivors")]),
   ("Outlaws of Thunder Junction Commander","otc",[("Desert Bloom","desert_bloom"),("Grand Larceny","grand_larceny"),("Most Wanted","most_wanted"),("Quick Draw","quick_draw")]),
   ("Modern Horizons 3 Commander","m3c",[("Creative Energy","creative_energy"),("Eldrazi Incursion","eldrazi_incursion"),("Graveyard Overdrive","graveyard_overdrive"),("Tricky Terrain","tricky_terrain")]),
   ("Bloomburrow Commander","blc",[("Animated Army","animated_army"),("Family Matters","family_matters"),("Peace Offering","peace_offering"),("Squirreled Away","squirreled_away")]),
   ("Duskmourn: House of Horror Commander","dsc",[("Death Toll","death_toll"),("Endless Punishment","endless_punishment"),("Jump Scare!","jump_scare"),("Miracle Worker","miracle_worker")]),
   ("Aetherdrift Commander","drc",[("Eternal Might","eternal_might"),("Living Energy","living_energy")]),
   ("Tarkir: Dragonstorm Commander","tdc",[("Abzan Armor","abzan_armor"),("Jeskai Striker","jeskai_striker"),("Mardu Surge","mardu_surge"),("Sultai Arisen","sultai_arisen"),("Temur Roar","temur_roar")]),
   ("Final Fantasy Commander","fic",[("Counter Blitz (FINAL FANTASY X)","counter_blitz_final_fantasy_x"),("Limit Break (FINAL FANTASY VII)","limit_break_final_fantasy_vii"),("Revival Trance (FINAL FANTASY VI)","revival_trance_final_fantasy_vi"),("Scions & Spellcraft (FINAL FANTASY XIV)","scions_spellcraft_final_fantasy_xiv")]),
   ("Edge of Eternities Commander","eoc",[("Counter Intelligence","counter_intelligence"),("World Shaper","world_shaper")]),
   ("Lorwyn Eclipsed Commander","ecc",[("Blight Curse","blight_curse"),("Dance of the Elements","dance_of_the_elements")]),
   ("Teenage Mutant Ninja Turtles Eternal","tmc",[("Turtle Power!","turtle_power")]),
   ("Secrets of Strixhaven Commander","soc",[("Lorehold Spirit","lorehold_spirit"),("Prismari Artistry","prismari_artistry"),("Quandrix Unlimited","quandrix_unlimited"),("Silverquill Influence","silverquill_influence"),("Witherbloom Pestilence","witherbloom_pestilence")]),
   ("Marvel Super Heroes Commander","msc",[("Avengers Assemble","avengers_assemble"),("Doom Prevails","doom_prevails"),("The Fantastic Four","the_fantastic_four"),("Wakanda Forever","wakanda_forever")]),
   ("Foundations Commander","fdc",[("Calling All Angels","calling_all_angels"),("Keen Engineering","keen_engineering"),("Reign of Dragons","reign_of_dragons"),("Tramplesaurus Rex","tramplesaurus_rex"),("Wretched Ranks","wretched_ranks")]),
   ("Reality Fracture Commander","frc",[("Multiverse Reforged","multiverse_reforged")]),
   ("Secret Lair","sld",[("Heads I Win, Tails You Lose (2021)","heads_i_win_tails_you_lose"),("From Cute to Brute (2023)","from_cute_to_brute"),("Angels: They're Just Like Us but Cooler and with Wings (2023)","angels_they_re_just_like_us_but_cooler_and_with_wings"),("Raining Cats and Dogs (2024)","raining_cats_and_dogs"),("20 Ways to Win (2024)","20_ways_to_win"),("Everyone's Invited! (2025)","everyones_invited"),("Goblin Storm (2026)","goblin_storm"),("Hatsune Miku (2026)","hatsune_miku"),("Odds and Ends (2026)","odds_and_ends")])]
ANOS={"c11":"2011","c13":"2013","c14":"2014","c15":"2015","c16":"2016","c17":"2017","c18":"2018","c19":"2019","c20":"2020","znc":"2020","cmr":"2020","khc":"2021","c21":"2021","sld":"","afc":"2021","mic":"2021","voc":"2021","nec":"2022","ncc":"2022","clb":"2022","dmc":"2022","40k":"2022","brc":"2022","scd":"2022","onc":"2023","moc":"2023","ltc":"2023","cmm":"2023","woc":"2023","who":"2023","lcc":"2023","mkc":"2024","pip":"2024","otc":"2024","m3c":"2024","blc":"2024","dsc":"2024","drc":"2025","tdc":"2025","fic":"2025","eoc":"2025","ecc":"2026","tmc":"2026","soc":"2026","msc":"2026","fdc":"2026","frc":"2026"}
# Grupos de topo; o resto e Universes Within.
GRUPO={"40k":"Universes Beyond","ltc":"Universes Beyond","who":"Universes Beyond","pip":"Universes Beyond","fic":"Universes Beyond","tmc":"Universes Beyond","msc":"Universes Beyond","fdc":"Starters","scd":"Starters","sld":"Secret Lair"}
GRUPOS=["Universes Within","Universes Beyond","Starters","Secret Lair"]
data=[]
for nome,pasta,decks in C:
    ds=[]
    for dn,f in decks:
        t=open(f"{pasta}/{f}.txt",encoding="utf-8").read()
        cmd=" / ".join(l.split(" ",1)[1].rsplit(" (",1)[0] for l in t.split("\n\n")[0].split("\n"))
        ds.append({"nome":dn,"comandante":cmd,"arquivo":f+".txt","lista":t})
    data.append({"id":pasta,"nome":nome,"ano":ANOS[pasta],"grupo":GRUPO.get(pasta,"Universes Within"),"icone":{"c11":"cmd"}.get(pasta,pasta),"decks":ds})
ATUALIZADO="27/10/2026"  # data da última conferência de todos os decks com o mtg.wtf (tools/auditar.py); atualizar a cada auditoria
nd=sum(len(d) for _,_,d in C)
rodape=f'{nd} decks em {len(C)} coleções · listas conferidas com o <a href="https://mtg.wtf">mtg.wtf</a> em {ATUALIZADO} · <a href="https://github.com/andrevona/precons-commander">sobre o projeto</a><br>Ao copiar, a lista sai no formato de exportação do MTG Arena, com o nome do deck e a seção do comandante: colada no endstep.cc, o deck já fica com nome e comandante.'
html=open("template.html",encoding="utf-8").read().replace("__GRUPOS__",json.dumps(GRUPOS)).replace("__RODAPE__",rodape).replace("__DATA__",json.dumps(data,ensure_ascii=False).replace("</","<\\/"))
open("precons_offline.html","w",encoding="utf-8").write(html)
print(len(html))
