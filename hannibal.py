#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HannibalBB — Autonomous Elite Bug-Bounty Agent (provider-agnostic TUI)
----------------------------------------------------------------------
Works with ANY AI through the OpenAI-compatible chat API (API key + link via /models),
or keyless through the local Claude Code CLI (default). Rich terminal UI.

Features (school exercise): instructions, skills, tools, connectors, plugins, MCP,
knowledge base (RAG), memory (short+long term), authentication.
Run:  hannibal      (or: python3 hannibal.py)
"""
import os, sys, json, time, glob, re, subprocess, urllib.request, urllib.error

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich import box

PT_OK = False
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style as PTStyle
    PT_OK = True
except Exception:
    PT_OK = False

# ---------------------------------------------------------------- palette / paths
AMBER="#f5a623"; CRIMSON="#e23d4b"; TEAL="#2bb2a6"; SAND="#d9c6a5"; DIM="grey50"
SEV={"crit":CRIMSON,"high":"#ff8c42","med":"#f5c518","low":"#4aa3df","drop":DIM}

console = Console()

HOME     = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(HOME,"config","providers.json")
MEM_PATH = os.path.join(HOME,"memory","hannibal_memory.json")
IDENTITY = os.path.join(HOME,"core","identity","HANNIBAL.md")
KNOW_DIR = os.path.join(HOME,"knowledge")
ARSENAL  = os.path.join(HOME,"arsenal","cards.json")

SKILLS=[
 "recon (subdomains, live hosts, JS secret mining)",
 "attack-surface mapping & bug-class classification",
 "hunt: IDOR, SSRF, XSS, SQLi, SSTI, XXE, auth-bypass, CSRF, CORS, race, logic",
 "LLM/AI security (prompt injection, indirect injection, exfil, agentic ASI01-10)",
 "A→B→ceiling bug chaining",
 "WAF/filter bypass research (deep-research wall loop)",
 "finding validation (4 gates + CVSS 3.1) and report writing",
 "dynamic CVE arsenal self-learning",
]

LOGO=r"""[%s] _   _    _    _   _ _   _ ___ ____    _    _[/]
[%s]| | | |  / \  | \ | | \ | |_ _| __ )  / \  | |[/]     [bold %s]⚔  Λ  ΜΟΛΩΝ ΛΑΒΕ  Λ  ⚔[/]
[%s]| |_| | / _ \ |  \| |  \| || ||  _ \ / _ \ | |[/]     [%s]the war-elephant bug-bounty agent[/]
[%s]|  _  |/ ___ \| |\  | |\  || || |_) / ___ \| |___[/]  [%s]chain every bug to its severity ceiling[/]
[%s]|_| |_/_/   \_\_| \_|_| \_|___|____/_/   \_\_____|[/]  [%s]🐘  cross the Alps · never « defended »[/]""" % (
    CRIMSON,CRIMSON,AMBER,AMBER,SAND,AMBER,DIM,AMBER,CRIMSON)

DEFAULT_PROVIDERS={
 "active":"claude-code",
 "providers":{
  "claude-code":{"kind":"cli","cmd":"claude -p","api_key_env":"","api_key":"","model":"claude-code (local, no key)"},
  "claude":{"base_url":"https://api.anthropic.com/v1","api_key_env":"ANTHROPIC_API_KEY","api_key":"","model":"claude-opus-5-5"},
  "openai":{"base_url":"https://api.openai.com/v1","api_key_env":"OPENAI_API_KEY","api_key":"","model":"gpt-4o"},
  "deepseek":{"base_url":"https://api.deepseek.com/v1","api_key_env":"DEEPSEEK_API_KEY","api_key":"","model":"deepseek-chat"},
 }}

# ---------------------------------------------------------------- config / memory
def load_cfg():
    try:
        with open(CFG_PATH) as f: return json.load(f)
    except Exception:
        save_cfg(DEFAULT_PROVIDERS); return json.loads(json.dumps(DEFAULT_PROVIDERS))
def save_cfg(c):
    os.makedirs(os.path.dirname(CFG_PATH),exist_ok=True)
    with open(CFG_PATH,"w") as f: json.dump(c,f,indent=2)
def load_mem():
    try:
        with open(MEM_PATH) as f: return json.load(f)
    except Exception: return {"facts":[],"targets":{},"findings":[]}
def save_mem(m):
    os.makedirs(os.path.dirname(MEM_PATH),exist_ok=True)
    with open(MEM_PATH,"w") as f: json.dump(m,f,indent=2)
def resolve_key(p):
    if p.get("kind")=="cli": return "local-cli"
    return p.get("api_key") or os.environ.get(p.get("api_key_env",""),"")
def active(cfg): return cfg["providers"][cfg["active"]]

# ---------------------------------------------------------------- RAG
def knowledge_index():
    return [os.path.splitext(os.path.basename(f))[0] for f in sorted(glob.glob(os.path.join(KNOW_DIR,"*.md")))]
def retrieve_cards(query,k=2):
    terms=set(re.findall(r"[a-z0-9]+",query.lower())); scored=[]
    for f in glob.glob(os.path.join(KNOW_DIR,"*.md")):
        try: txt=open(f).read()
        except Exception: continue
        low=txt.lower(); name=os.path.basename(f)
        score=sum(low.count(t) for t in terms if len(t)>2)
        if os.path.splitext(name)[0] in terms: score+=25
        if score>0: scored.append((score,name,txt))
    scored.sort(reverse=True); return scored[:k]

# ---------------------------------------------------------------- tools
def tool_analyze_auth_log(path):
    if not os.path.isabs(path): path=os.path.join(HOME,"missions",path)
    try: lines=open(path,errors="ignore").read().splitlines()
    except Exception as e: return f"ERROR: cannot read {path}: {e}"
    ipre=re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})"); fails={}; users={}
    for ln in lines:
        if "Failed password" in ln or "authentication failure" in ln or "Invalid user" in ln:
            m=ipre.search(ln)
            if m: fails[m.group(1)]=fails.get(m.group(1),0)+1
            u=re.search(r"for (?:invalid user )?(\w+)",ln)
            if u: users[u.group(1)]=users.get(u.group(1),0)+1
    top=sorted(fails.items(),key=lambda x:-x[1])[:5]
    return json.dumps({"total_failed":sum(fails.values()),
        "suspicious_ips":[{"ip":ip,"failed":n,"verdict":"brute-force" if n>=10 else "probe"} for ip,n in top],
        "top_targeted_users":sorted(users.items(),key=lambda x:-x[1])[:5]},indent=2)
def tool_http_fingerprint(url):
    if not url.startswith("http"): url="https://"+url
    req=urllib.request.Request(url,headers={"User-Agent":"HannibalBB-recon"})
    try:
        with urllib.request.urlopen(req,timeout=12) as r:
            h={k.lower():v for k,v in r.getheaders()}
            sec=["server","x-powered-by","content-security-policy","strict-transport-security",
                 "x-frame-options","x-content-type-options","set-cookie","access-control-allow-origin"]
            return json.dumps({"url":url,"status":r.status,"headers":{k:h.get(k,"(absent)") for k in sec}},indent=2)
    except urllib.error.HTTPError as e: return json.dumps({"url":url,"status":e.code},indent=2)
    except Exception as e: return f"ERROR fetching {url}: {e}"
def tool_search_knowledge(q):
    cs=retrieve_cards(q,3)
    return "\n\n".join(f"### {n}\n{t[:1500]}" for _,n,t in cs) if cs else "No matching card."
def tool_query_arsenal(kw):
    try: d=json.load(open(ARSENAL))
    except Exception: return "Arsenal empty. Run /learn."
    kw=kw.lower(); hits=[c for c in d.get("cards",[]) if kw in json.dumps(c).lower()]
    return json.dumps(hits[:10],indent=2) if hits else f"No arsenal entry for '{kw}'."
def tool_remember(fact):
    m=load_mem(); m["facts"].append({"ts":time.strftime("%Y-%m-%d %H:%M"),"fact":fact}); save_mem(m)
    return f"Stored to long-term memory: {fact}"

TOOLS_SPEC=[
 {"type":"function","function":{"name":"analyze_auth_log","description":"Analyze auth.log for brute-force: failed logins per IP, suspicious IPs, targeted users.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
 {"type":"function","function":{"name":"http_fingerprint","description":"Fetch a URL, return status + security headers (authorized recon).","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
 {"type":"function","function":{"name":"search_knowledge","description":"Retrieve Bug Knowledge Cards for a bug class/topic.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
 {"type":"function","function":{"name":"query_arsenal","description":"Search the dynamic CVE arsenal.","parameters":{"type":"object","properties":{"keyword":{"type":"string"}},"required":["keyword"]}}},
 {"type":"function","function":{"name":"remember","description":"Persist an important fact to long-term memory.","parameters":{"type":"object","properties":{"fact":{"type":"string"}},"required":["fact"]}}},
]
TOOL_FUNCS={"analyze_auth_log":lambda a:tool_analyze_auth_log(a["path"]),
            "http_fingerprint":lambda a:tool_http_fingerprint(a["url"]),
            "search_knowledge":lambda a:tool_search_knowledge(a["query"]),
            "query_arsenal":lambda a:tool_query_arsenal(a["keyword"]),
            "remember":lambda a:tool_remember(a["fact"])}

# ---------------------------------------------------------------- system prompt
def build_system(user_msg):
    parts=[]
    try: parts.append(open(IDENTITY).read())
    except Exception: parts.append("You are HannibalBB, an elite bug-bounty agent.")
    parts.append("## YOUR SKILLS\n"+"\n".join("- "+s for s in SKILLS))
    parts.append("## KNOWLEDGE BASE (cards)\n"+", ".join(knowledge_index()))
    mem=load_mem()
    if mem["facts"]:
        parts.append("## LONG-TERM MEMORY\n"+"\n".join("- "+f["fact"] for f in mem["facts"][-15:]))
    cards=retrieve_cards(user_msg,2)
    if cards:
        parts.append("## RETRIEVED KNOWLEDGE (RAG)\n"+"\n\n".join(f"### {n}\n{t[:2500]}" for _,n,t in cards))
    parts.append("Format answers in concise Markdown. Severity emojis: 🔴crit 🟠high 🟡med 🔵low. "
                 "Always give an expected CVSS 3.1 score when you describe a finding.")
    return "\n\n".join(parts)

# ---------------------------------------------------------------- LLM backends
def call_llm_cli(cfg,messages):
    p=active(cfg); pr=[]
    for m in messages:
        r=m.get("role"); c=m.get("content","")
        pr.append({"system":"[SYSTEM INSTRUCTIONS]\n","user":"[OPERATOR]\n",
                   "assistant":"[HANNIBALBB]\n","tool":"[TOOL RESULT]\n"}.get(r,"")+str(c))
    pr.append("[HANNIBALBB] (answer as HannibalBB, applying your methodology)")
    cmd=(p.get("cmd","claude -p")).split()
    try:
        r=subprocess.run(cmd+["\n\n".join(pr)],capture_output=True,text=True,timeout=240)
    except Exception as e: return None,f"CLI backend failed: {e}"
    return {"role":"assistant","content":(r.stdout or r.stderr or "").strip()},None

def call_llm(cfg,messages,use_tools=True):
    p=active(cfg)
    if p.get("kind")=="cli": return call_llm_cli(cfg,messages)
    key=resolve_key(p)
    if not key: return None,f"No API key for '{cfg['active']}'. Run /models key {cfg['active']}"
    body={"model":p["model"],"messages":messages,"temperature":0.4}
    if use_tools: body["tools"]=TOOLS_SPEC; body["tool_choice"]="auto"
    req=urllib.request.Request(p["base_url"].rstrip("/")+"/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer "+key})
    try:
        with urllib.request.urlopen(req,timeout=180) as r: resp=json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (400,404,422) and use_tools: return call_llm(cfg,messages,False)
        return None,f"HTTP {e.code}: {e.read().decode(errors='ignore')[:300]}"
    except Exception as e: return None,f"Request failed: {e}"
    return resp["choices"][0]["message"],None

def ai_panel(text):
    console.print(Panel(Markdown(text or "_(no output)_"), title="🐘 HannibalBB",
        title_align="left", border_style=AMBER, box=box.ROUNDED, padding=(1,2)))

DEMO = os.environ.get("HANNIBAL_DEMO")=="1"
_DEMO_CACHE=None
def _demo_cache():
    global _DEMO_CACHE
    if _DEMO_CACHE is None:
        try: _DEMO_CACHE=json.load(open(os.path.join(HOME,"missions","cache","demo_answers.json")))
        except Exception: _DEMO_CACHE={}
    return _DEMO_CACHE
def think_call(cfg,history):
    if DEMO:  # smooth, short replay of pre-generated REAL answers for recording
        last=next((m["content"] for m in reversed(history) if m.get("role")=="user"),"")
        ans=_demo_cache().get(last.strip())
        with console.status(f"[{AMBER}]HannibalBB is thinking…",spinner="earth"):
            time.sleep(2.6)
        if ans is not None: return {"role":"assistant","content":ans},None
        return call_llm(cfg,history)
    with console.status(f"[{AMBER}]HannibalBB is thinking…",spinner="earth"):
        return call_llm(cfg,history)

def agent_turn(cfg,history):
    for _ in range(6):
        msg,err=think_call(cfg,history)
        if err: console.print(Panel(err,border_style=CRIMSON,title="error")); return
        history.append(msg)
        calls=msg.get("tool_calls")
        if not calls:
            ai_panel(msg.get("content","")); return
        for tc in calls:
            fn=tc["function"]["name"]
            try: args=json.loads(tc["function"].get("arguments") or "{}")
            except Exception: args={}
            console.print(f"  [{TEAL}]⚙ tool[/] [bold]{fn}[/]([dim]{json.dumps(args)[:70]}[/])")
            out=TOOL_FUNCS.get(fn,lambda a:"unknown tool")(args)
            console.print(Panel(str(out)[:4000],border_style=TEAL,box=box.MINIMAL,padding=(0,1)))
            history.append({"role":"tool","tool_call_id":tc.get("id",fn),"name":fn,"content":str(out)[:6000]})
    console.print(f"[{CRIMSON}]⚠ tool loop limit reached.[/]")

# ---------------------------------------------------------------- UI helpers
def banner(cfg):
    console.print()
    console.print(Panel(Align.left(LOGO),border_style=AMBER,box=box.DOUBLE,padding=(1,3)))
    p=active(cfg); key=resolve_key(p)
    badge=f"[{TEAL}]no key needed[/]" if p.get("kind")=="cli" else ("[green]key ✓[/]" if key else f"[{CRIMSON}]no key — /models key {cfg['active']}[/]")
    console.print(f"  [bold {AMBER}]active AI[/] [white]{cfg['active']}[/] [dim]({p['model']})[/]   {badge}")
    qs=Table.grid(padding=(0,2))
    qs.add_column(style=AMBER,no_wrap=True); qs.add_column(style="white")
    qs.add_row("/help","all commands"); qs.add_row("/mission 1","run a demo mission (real AI answer)")
    qs.add_row("/analyze auth.log","run the brute-force detection tool")
    qs.add_row("/learn","update the live CVE arsenal"); qs.add_row("/models","switch / add an AI (key + link)")
    console.print(Panel(qs,title="quick start",title_align="left",border_style=DIM,box=box.ROUNDED,padding=(1,2)))
    console.print(f"  [dim]just type a message to talk to HannibalBB · {'Tab = autocomplete · ' if PT_OK else ''}/quit to exit[/]\n")

def show_help():
    t=Table(box=box.SIMPLE_HEAVY,border_style=AMBER,title="HannibalBB — commands",title_style=f"bold {AMBER}")
    t.add_column("command",style=AMBER,no_wrap=True); t.add_column("what it does",style="white")
    rows=[("/help","this help"),("/models","list AIs + how to add one (key + link)"),
          ("/models add","add any OpenAI-compatible AI"),("/models use <name>","switch active AI"),
          ("/models key <name>","set an API key"),("/model <name>","quick-switch AI"),
          ("/skills","HannibalBB skills"),("/knowledge","list Bug Knowledge Cards"),
          ("/card <name>","print a card (e.g. /card ssrf)"),("/arsenal","dynamic CVE arsenal status"),
          ("/learn","run the CVE self-learning loop"),("/analyze <log>","log-analysis TOOL (brute-force)"),
          ("/fingerprint <url>","recon TOOL (security headers)"),("/mission <1|2|3>","load+run a demo mission"),
          ("/memory","long-term memory"),("/remember <fact>","save a fact"),("/clear","reset conversation"),
          ("/quit","exit")]
    for a,b in rows: t.add_row(a,b)
    console.print(t)

def show_providers(cfg):
    t=Table(box=box.ROUNDED,border_style=AMBER,title="configured AIs",title_style=f"bold {AMBER}")
    t.add_column(""); t.add_column("name",style="white"); t.add_column("model",style=SAND)
    t.add_column("endpoint",style="dim"); t.add_column("auth")
    for n,p in cfg["providers"].items():
        mark=f"[{AMBER}]●[/]" if n==cfg["active"] else "○"
        if p.get("kind")=="cli": where=p.get("cmd","local"); auth=f"[{TEAL}]no key[/]"
        else: where=p.get("base_url","?"); auth="[green]key ✓[/]" if resolve_key(p) else f"[{CRIMSON}]no key[/]"
        t.add_row(mark,n,p["model"],where,auth)
    console.print(t)
    console.print(f"  [dim]add any AI:[/] [{AMBER}]/models add[/]  [dim]· switch:[/] [{AMBER}]/models use <name>[/]")

# ---------------------------------------------------------------- input
_pt=None; _cmp=None; _pts=None
def _pt_init():
    global _pt,_cmp,_pts
    _pt=PromptSession()
    _cmp=WordCompleter(["/help","/models","/models add","/models use","/models key","/model",
        "/skills","/knowledge","/card","/arsenal","/learn","/analyze","/fingerprint","/mission",
        "/memory","/remember","/clear","/quit"],sentence=True,ignore_case=True)
    _pts=PTStyle.from_dict({"prompt":f"{AMBER} bold","bottom-toolbar":"bg:#222222 #d9c6a5"})
def ask(model_label):
    if sys.stdin.isatty() and PT_OK:
        if _pt is None: _pt_init()
        return _pt.prompt([("class:prompt","\nYou ▸ ")],completer=_cmp,style=_pts,
            bottom_toolbar=f" HannibalBB · AI={model_label} · Tab=commands · /help · /quit ").strip()
    return console.input(f"\n[bold {AMBER}]You ▸ [/]").strip()

def cmd_models(cfg,arg):
    sub=arg.split()
    if not sub: show_providers(cfg); return
    a=sub[0]
    if a=="add":
        console.print(f"[{AMBER}]Add an AI[/] (any OpenAI-compatible endpoint):")
        name=console.input("  name (e.g. groq): ").strip()
        base=console.input("  link / base_url: ").strip().rstrip("/")
        model=console.input("  model id: ").strip()
        key=console.input("  API key: ").strip()
        if not(name and base and model): console.print(f"[{CRIMSON}]aborted[/]"); return
        cfg["providers"][name]={"base_url":base,"api_key":key,"api_key_env":"","model":model}
        cfg["active"]=name; save_cfg(cfg); console.print(f"[green]✓ added '{name}' and set active[/]")
    elif a=="use" and len(sub)>1:
        if sub[1] in cfg["providers"]: cfg["active"]=sub[1]; save_cfg(cfg); console.print(f"[green]✓ active = {sub[1]}[/]")
        else: console.print(f"[{CRIMSON}]no such AI[/]")
    elif a=="key" and len(sub)>1:
        if sub[1] in cfg["providers"]:
            k=console.input(f"  API key for {sub[1]}: ").strip()
            cfg["providers"][sub[1]]["api_key"]=k; save_cfg(cfg); console.print("[green]✓ key saved[/]")
        else: console.print(f"[{CRIMSON}]no such AI[/]")
    else: console.print(f"[{CRIMSON}]usage: /models [add|use <name>|key <name>][/]")

def main():
    cfg=load_cfg(); banner(cfg); history=[]
    while True:
        try: line=ask(active(cfg)["model"])
        except (EOFError,KeyboardInterrupt): console.print("\n[dim]ciao.[/]"); break
        if not line: continue
        if line.startswith("/"):
            c=line[1:].split(" ",1); cmd=c[0]; arg=c[1] if len(c)>1 else ""
            if cmd in ("quit","exit","q"): console.print("[dim]ciao.[/]"); break
            elif cmd=="help": show_help()
            elif cmd=="models": cmd_models(cfg,arg)
            elif cmd=="model" and arg:
                if arg in cfg["providers"]: cfg["active"]=arg; save_cfg(cfg); console.print(f"[green]✓ active = {arg}[/]")
                else: console.print(f"[{CRIMSON}]no such AI[/]")
            elif cmd=="skills":
                console.print(Panel("\n".join(f"[{AMBER}]•[/] {s}" for s in SKILLS),title="skills",border_style=AMBER,box=box.ROUNDED))
            elif cmd=="knowledge":
                console.print(Panel("  ".join(f"[{AMBER}]{c}[/]" for c in knowledge_index()),title="Bug Knowledge Cards",border_style=AMBER,box=box.ROUNDED))
            elif cmd=="card" and arg:
                f=os.path.join(KNOW_DIR,arg.strip()+".md")
                if os.path.exists(f): console.print(Panel(Markdown(open(f).read()),title=f"card · {arg}",border_style=TEAL,box=box.ROUNDED,padding=(1,2)))
                else: console.print(f"[{CRIMSON}]no card '{arg}'[/]")
            elif cmd=="arsenal":
                try:
                    d=json.load(open(ARSENAL)); console.print(Panel(f"[white]{len(d.get('cards',[]))}[/] CVE entries · last update [dim]{d.get('updated','never')}[/]",title="dynamic arsenal",border_style=AMBER,box=box.ROUNDED))
                except Exception: console.print(f"[{CRIMSON}]arsenal empty — run /learn[/]")
            elif cmd=="learn":
                with console.status(f"[{AMBER}]pulling + classifying live CVEs…",spinner="earth"):
                    r=subprocess.run(["python3",os.path.join(HOME,"arsenal","learn_cve.py")],capture_output=True,text=True)
                console.print(Panel(r.stdout.strip() or r.stderr.strip(),title="arsenal · self-learning",border_style=TEAL,box=box.ROUNDED))
            elif cmd=="analyze" and arg:
                console.print(f"  [{TEAL}]⚙ tool[/] analyze_auth_log([dim]{arg}[/])")
                console.print(Panel(tool_analyze_auth_log(arg.strip()),border_style=TEAL,box=box.MINIMAL,padding=(0,1)))
            elif cmd=="fingerprint" and arg:
                console.print(f"  [{TEAL}]⚙ tool[/] http_fingerprint([dim]{arg}[/])")
                console.print(Panel(tool_http_fingerprint(arg.strip()),border_style=TEAL,box=box.MINIMAL,padding=(0,1)))
            elif cmd=="mission" and arg.strip() in ("1","2","3"):
                f=os.path.join(HOME,"missions",f"mission{arg.strip()}.txt")
                if os.path.exists(f):
                    txt=open(f).read()
                    console.print(Panel(txt,title=f"mission {arg.strip()}",border_style=CRIMSON,box=box.ROUNDED,padding=(1,2)))
                    sysmsg={"role":"system","content":build_system(txt)}
                    history=[sysmsg]+[m for m in history if m.get("role")!="system"]
                    history.append({"role":"user","content":txt}); agent_turn(cfg,history)
                else: console.print(f"[{CRIMSON}]mission file missing[/]")
            elif cmd=="memory":
                m=load_mem()
                console.print(Panel(json.dumps(m,indent=2) if m["facts"] else "(empty)",title="long-term memory",border_style=AMBER,box=box.ROUNDED))
            elif cmd=="remember" and arg: console.print(f"[green]✓[/] {tool_remember(arg)}")
            elif cmd=="clear": history=[]; console.print("[dim](conversation cleared)[/]")
            else: console.print(f"[{CRIMSON}]unknown command — /help[/]")
            continue
        sysmsg={"role":"system","content":build_system(line)}
        history=[sysmsg]+[m for m in history if m.get("role")!="system"]
        history.append({"role":"user","content":line})
        agent_turn(cfg,history)

if __name__=="__main__":
    main()
