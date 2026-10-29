import re,subprocess,sys,time,collections,os
# Pasta de trabalho: a variável PRECONS_RAIZ, ou a pasta acima de tools/ (onde ficam build.py e as pastas dos decks).
RAIZ=os.environ.get("PRECONS_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=open(os.path.join(RAIZ,"build.py"),encoding="utf-8").read()
C=eval(src[src.index("C=")+2:src.index("ANOS=")])
SET={"c11":"cmd"}
SLUG={"heads_i_win_tails_you_lose":"heads-i-win-tails-you-lose"}
for nome,pasta,decks in C:
    for dn,stem in decks:
        st=SET.get(pasta,pasta); slug=SLUG.get(stem,stem.replace("_","-"))
        r=subprocess.run([sys.executable,"-I",os.path.join(RAIZ,"tools","raspar.py"),st,slug,"_audit",pasta+"__"+stem],capture_output=True,text=True,env={**os.environ,"PRECONS_RAIZ":RAIZ})
        novo=[l.strip() for l in open(os.path.join(RAIZ,"raw","_audit",f"{pasta}__{stem}.txt"),encoding="utf-8") if l.strip() and l.strip()!="--"]
        atual=[l.strip() for l in open(os.path.join(RAIZ,pasta,f"{stem}.txt"),encoding="utf-8") if l.strip()]
        a,b=collections.Counter(atual),collections.Counter(novo)
        so_atual=list((a-b).elements()); so_site=list((b-a).elements())
        tag="OK" if not so_atual and not so_site else "DIFERENTE"
        print(f"{tag} {pasta}/{stem} | {r.stdout.strip().split(' ',1)[1] if r.stdout else r.stderr[-200:]}")
        if tag!="OK": print("   só no meu arquivo:",so_atual,"\n   só no site:",so_site)
        time.sleep(1)
