#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HannibalBB — Dynamic Arsenal: CVE self-learning loop.
Pulls recent CVEs from a live feed, CLASSIFIES each into a HannibalBB bug class,
and LEARNS it (spot/exploit/bypass/chain/ceiling) into arsenal/cards.json, then
appends a short note to the matching knowledge/<class>.md card.

Run:  python3 learn_cve.py            (reads feeds, works offline with a seed fallback)
Called by the CLI via /learn.
"""
import os, sys, json, time, re, urllib.request

HOME   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS  = os.path.join(HOME, "arsenal", "cards.json")
KNOW   = os.path.join(HOME, "knowledge")

# keyword -> HannibalBB class (classification)
CLASS_MAP = [
    (r"sql injection|sqli", "sqli"), (r"cross-site scripting|xss", "xss"),
    (r"server-side request forgery|ssrf", "ssrf"),
    (r"template injection|ssti", "ssti"), (r"xxe|xml external", "xxe"),
    (r"insecure direct object|idor|broken object level|bola", "idor"),
    (r"deserial", "deserialization"), (r"path traversal|directory traversal|lfi", "lfi"),
    (r"remote code execution|rce|command injection|os command", "rce"),
    (r"authentication bypass|auth bypass|improper authentication", "auth-bypass"),
    (r"csrf|cross-site request forgery", "csrf"), (r"cors", "cors"),
    (r"open redirect", "open-redirect"), (r"prototype pollution", "prototype-pollution"),
    (r"jwt|json web token", "jwt-crypto"), (r"graphql", "graphql"),
    (r"request smuggling", "http-smuggling"), (r"race condition", "race-condition"),
    (r"privilege escalation", "privilege-escalation"), (r"file upload|arbitrary file", "file-upload"),
    (r"prompt injection|llm|language model", "prompt-injection"),
]
# per-class learning templates (what to TEST / how to CHAIN / the ceiling)
CLASS_PLAYBOOK = {
 "sqli":{"ceiling":"9.8 (auth bypass / DB dump / RCE via stacked queries)","spot":"error msgs, ORDER BY, quote-break, time delay","chain":"→ dump creds → ATO; → RCE via xp_cmdshell/INTO OUTFILE"},
 "xss":{"ceiling":"9.0 (stored admin XSS → ATO)","spot":"reflected markers in HTML/JS/attr","chain":"→ token theft → ATO → admin → RCE"},
 "ssrf":{"ceiling":"10.0 (cloud metadata → IAM creds)","spot":"url/webhook/import params","chain":"→ metadata → cloud takeover; → internal RCE"},
 "ssti":{"ceiling":"10.0 (RCE)","spot":"{{7*7}}=49","chain":"→ RCE → secrets → cloud"},
 "idor":{"ceiling":"9.8 (cross-tenant write)","spot":"swap object IDs across 2 accounts","chain":"→ mass-assign → privesc → ATO"},
 "rce":{"ceiling":"10.0","spot":"command metachars, deserial gadgets","chain":"→ full host → lateral"},
 "auth-bypass":{"ceiling":"9.8","spot":"force-browse, role tampering, logic skip","chain":"→ admin → full control"},
 "deserialization":{"ceiling":"9.8 (RCE)","spot":"base64 blobs, java/pickle/php magic bytes","chain":"→ RCE"},
 "prompt-injection":{"ceiling":"8-9 (agentic exfil / tool abuse)","spot":"LLM reads attacker-controlled text","chain":"→ indirect injection → data exfil / tool hijack"},
}
DEFAULT_PB={"ceiling":"varies — chain to max","spot":"see class card","chain":"re-score at ceiling"}

def classify(text):
    t=text.lower()
    for pat,cls in CLASS_MAP:
        if re.search(pat,t): return cls
    return "misc"

def fetch_json(url, timeout=20):
    req=urllib.request.Request(url, headers={"User-Agent":"HannibalBB-arsenal"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def pull_circl():
    data=fetch_json("https://cve.circl.lu/api/last")
    items=[]
    for e in (data if isinstance(data,list) else [])[:40]:
        # prefer the CVE- alias as the id
        cid=next((a for a in e.get("aliases",[]) if a.startswith("CVE-")), e.get("id",""))
        summ=e.get("details") or e.get("summary") or ""
        if not summ:
            try: summ=e["containers"]["cna"]["descriptions"][0]["value"]
            except Exception: summ=""
        # severity: CIRCL osv-style -> list of {score,...}; fall back to any CVSS string
        cvss=""
        sev=e.get("severity")
        if isinstance(sev,list) and sev: cvss=str(sev[0].get("score",""))
        elif sev: cvss=str(sev)
        if cid and summ: items.append((cid,summ,cvss))
    return items

SEED=[  # offline fallback so the demo always shows the learning output
 ("CVE-2026-SEED-1","Server-Side Request Forgery in webhook import allows reading cloud metadata.","9.1"),
 ("CVE-2026-SEED-2","Stored Cross-Site Scripting in profile name executes in admin dashboard.","8.2"),
 ("CVE-2026-SEED-3","Broken Object Level Authorization (IDOR) lets a user read other tenants' invoices.","7.5"),
 ("CVE-2026-SEED-4","Server-Side Template Injection in report generator leads to remote code execution.","9.8"),
]

def learn(items):
    cards=[]
    for cid,summ,cvss in items:
        cls=classify(summ); pb=CLASS_PLAYBOOK.get(cls, DEFAULT_PB)
        cards.append({
            "cve":cid, "class":cls, "cvss":cvss or "n/a",
            "summary":summ[:240],
            "severity_ceiling":pb["ceiling"],
            "spot_tests":pb["spot"], "chain_map":pb["chain"],
            "learned":time.strftime("%Y-%m-%d %H:%M"),
        })
    out={"updated":time.strftime("%Y-%m-%d %H:%M"), "count":len(cards), "cards":cards}
    json.dump(out, open(CARDS,"w"), indent=2)
    # append a learning note to the matching knowledge card
    by_class={}
    for c in cards: by_class.setdefault(c["class"],[]).append(c)
    for cls,cs in by_class.items():
        path=os.path.join(KNOW, cls+".md")
        if os.path.exists(path):
            with open(path,"a") as f:
                f.write(f"\n\n<!-- arsenal auto-learned {time.strftime('%Y-%m-%d')} -->\n")
                for c in cs[:5]:
                    f.write(f"- {c['cve']} (CVSS {c['cvss']}): {c['summary'][:120]}\n")
    return out

def main():
    try:
        items=pull_circl()
        src="live CIRCL feed"
        if not items: raise ValueError("empty")
    except Exception as e:
        items=SEED; src=f"offline seed (live feed unavailable: {e})"
    out=learn(items)
    print(f"[arsenal] learned {out['count']} CVEs from {src}")
    cls_count={}
    for c in out["cards"]: cls_count[c["class"]]=cls_count.get(c["class"],0)+1
    for cls,n in sorted(cls_count.items(), key=lambda x:-x[1]):
        print(f"   {cls:18} {n}")
    print(f"[arsenal] written to {CARDS}")

if __name__=="__main__":
    main()
