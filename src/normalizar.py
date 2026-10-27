import re,sys,os,collections
# uso: python3 -I normalizar.py raw/pasta/arquivo.txt ...  -> grava pasta/arquivo.txt (comandante(s) = linhas antes de "--" ou 1a linha)
for f in sys.argv[1:]:
    L=[l.strip() for l in open(f,encoding="utf-8") if l.strip()]
    if "--" in L: i=L.index("--"); cmd,rest=L[:i],L[i+1:]
    else: cmd,rest=L[:1],L[1:]
    rx=re.compile(r"(\d+) (.+) \((\w+)\) (\S+)$")
    def nm(l): return rx.match(l).group(2).casefold()
    for l in L:
        if l!="--" and not rx.match(l): print("LINHA RUIM",f,l)
    rest=sorted(rest,key=lambda l:(nm(l),l))
    out="\n".join(cmd)+"\n\n"+"\n".join(rest)+"\n"
    dst=os.path.join("/home/claude",*f.split("/")[-2:])
    os.makedirs(os.path.dirname(dst),exist_ok=True); open(dst,"w",encoding="utf-8").write(out)
    n=0;nomes=collections.Counter();sn=collections.defaultdict(set)
    for l in cmd+rest:
        m=rx.match(l); n+=int(m[1])
        if m[2] not in("Forest","Island","Plains","Swamp","Mountain","Wastes"): nomes[m[2]]+=1
        sn[(m[3],m[4])].add(m[2])
    print(dst,n,[k for k,v in nomes.items() if v>1],[k for k,v in sn.items() if len(v)>1])
