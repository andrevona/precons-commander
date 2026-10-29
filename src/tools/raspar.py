# uso: python3 -I raspar.py set slug pasta stem   -> baixa mtg.wtf/deck/set/slug e grava raw/pasta/stem.txt
import sys,re,html,subprocess,os
# Pasta de trabalho: a variável PRECONS_RAIZ, ou a pasta acima de tools/ (onde ficam build.py e as pastas dos decks).
RAIZ=os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
st,slug,pasta,stem=sys.argv[1:5]
url=f"https://mtg.wtf/deck/{st}/{slug}"
h=subprocess.run(["curl","-sS","--max-time","60",url],capture_output=True,text=True).stdout
grupos=re.split(r'<div class="card_group">',h)[1:]
cmd=[];rest=[];avisos=[]
for g in grupos:
    m=re.search(r"<h6>([^<(]+)\((\d+)\)</h6>",g)
    if not m: continue
    nome,cab=m[1].strip(),int(m[2])
    if nome.lower().startswith(("display","token","sideboard","bonus","planar","scheme")): continue
    ents=re.findall(r'<div class="card_entry">\s*(\d+)\s*<span[^>]*>\s*<a href="/card/([^/]+)/([^/"]+)/([^"]*)">([^<\n]+)',g)
    s=sum(int(q) for q,_,_,_,_ in ents)
    if s!=cab: avisos.append(f"{nome}: soma {s} != cabeçalho {cab}")
    for q,se,nu,slug,nm in ents:
        carta=html.unescape(nm).strip()
        # Nome alternativo: o mtg.wtf mostra "Nome de exibição (Carta original)"; o endstep.cc só reconhece a carta original.
        # Troca só quando o texto entre parênteses é o mesmo nome do link da carta (evita cartas com parênteses no nome real).
        m=re.match(r"^(.+?) \(([^()]+)\)$",carta)
        if m and re.sub(r"[^a-z0-9]","",m[2].lower())==re.sub(r"[^a-z0-9]","",slug.lower()): carta=m[2]
        l=f"{q} {carta} ({se.upper()}) {nu}"
        (cmd if nome.lower()=="commander" else rest).append(l)
os.makedirs(os.path.join(RAIZ,"raw",pasta),exist_ok=True)
open(os.path.join(RAIZ,"raw",pasta,stem+".txt"),"w",encoding="utf-8").write("\n".join(cmd+["--"]+rest)+"\n")
print(url,len(cmd),"cmd",sum(int(l.split()[0]) for l in cmd+rest),"cartas",avisos or "ok")
