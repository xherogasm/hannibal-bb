#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HannibalBB — Connectors: push events to external services (feature #4).
Discord / Microsoft Teams webhooks + GitHub issue creation.
Usage:
  python3 notify.py discord "🔴 SS-001 confirmed: SSRF→Azure metadata (CVSS 9.1)"
  python3 notify.py teams   "New finding staged for review"
  python3 notify.py github  owner/repo "Finding: IDOR on /invoices" "body..."
Secrets come from env (never hard-coded): DISCORD_WEBHOOK, TEAMS_WEBHOOK, GITHUB_TOKEN.
"""
import os, sys, json, urllib.request

def post(url, payload, headers=None):
    data=json.dumps(payload).encode()
    h={"Content-Type":"application/json"}; h.update(headers or {})
    req=urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=15) as r: return r.status
    except Exception as e: return f"error: {e}"

def discord(msg):
    url=os.environ.get("DISCORD_WEBHOOK")
    if not url: return "DISCORD_WEBHOOK not set"
    return post(url, {"content":msg})

def teams(msg):
    url=os.environ.get("TEAMS_WEBHOOK")
    if not url: return "TEAMS_WEBHOOK not set"
    # Teams expects a MessageCard
    return post(url, {"@type":"MessageCard","@context":"http://schema.org/extensions",
                      "summary":"HannibalBB","text":msg})

def github_issue(repo, title, body):
    tok=os.environ.get("GITHUB_TOKEN")
    if not tok: return "GITHUB_TOKEN not set"
    return post(f"https://api.github.com/repos/{repo}/issues",
                {"title":title,"body":body},
                {"Authorization":"token "+tok,"Accept":"application/vnd.github+json",
                 "User-Agent":"HannibalBB"})

if __name__=="__main__":
    a=sys.argv
    if len(a)<3: print(__doc__); sys.exit(0)
    kind=a[1]
    if kind=="discord": print(discord(a[2]))
    elif kind=="teams": print(teams(a[2]))
    elif kind=="github" and len(a)>=5: print(github_issue(a[2],a[3],a[4]))
    else: print("bad args — see usage"); print(__doc__)
