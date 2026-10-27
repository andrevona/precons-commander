# uso: python3 -I raspar.py set slug pasta stem   -> baixa mtg.wtf/deck/set/slug e grava raw/pasta/stem.txt
import sys,re,html,subprocess,os
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
    ents=re.findall(r'<div class="card_entry">\s*(\d+)\s*<span[^>]*>\s*<a href="/card/([^/]+)/([^/"]+)/[^"]*">([^<\n]+)',g)
    s=sum(int(q) for q,_,_,_ in ents)
    if s!=cab: avisos.append(f"{nome}: soma {s} != cabeçalho {cab}")
    for q,se,nu,nm in ents:
        l=f"{q} {html.unescape(nm).strip()} ({se.upper()}) {nu}"
        (cmd if nome.lower()=="commander" else rest).append(l)
os.makedirs(f"/home/claude/raw/{pasta}",exist_ok=True)
open(f"/home/claude/raw/{pasta}/{stem}.txt","w",encoding="utf-8").write("\n".join(cmd+["--"]+rest)+"\n")
print(url,len(cmd),"cmd",sum(int(l.split()[0]) for l in cmd+rest),"cartas",avisos or "ok")
