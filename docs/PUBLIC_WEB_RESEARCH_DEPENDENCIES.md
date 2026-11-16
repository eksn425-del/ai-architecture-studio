# Public web research adapter: integration and dependency evidence

2026-10-17. Scope: read-only public research, separate from modeling permissions.
This module does not change the model sandbox network setting or browser/security
configuration. It does not import the geometry bridge, write files, run commands,
launch browsers, use credentials, read private attachments, or call paid APIs.

## Contract

`app.public_web_research.PublicResearchPolicy(public_queries: tuple[str, ...],
allowed_domains: tuple[str, ...], seed_urls: tuple[str, ...] = (), max_requests=8)`
is **trusted host configuration**, never a tool argument. Exact query membership
is intentional: keyword matching cannot establish that appended text is public.
A normal public query such as `Hangzhou Raffles City UNStudio architecture` must
be approved verbatim. Tool schemas should enumerate the configured queries.

Create one `PublicWebResearch(policy)` per authorized project turn, then call
`search_web(query: str)` and `fetch_url(url: str)`. Keep that instance across calls:
it stores discovered URL permissions and the request budget. Do not let model
arguments create/reset policy, domains, request budgets, or transports. The current host creates one instance per conversation turn: the eight-request
limit and discovered URL set reset on the next turn. This is not a cumulative
project/session budget; a longer-lived budget is not implemented.

Seed URLs are explicitly host approved. Other source URLs must have been returned
by this instance's search and match an exact approved domain. URL query strings
are deliberately excluded from source fetching. Search follows only the fixed
DuckDuckGo HTTPS endpoint and same approved host; source redirects may go only to
approved domains. Each redirect is independently validated and DNS-resolved.

Success returns status/source_url/fetched_at/sha256/content_type, untrusted data
warning and `grants_geometry_authority=false`. Search additionally returns a fixed
provider, query, at most five title/url/snippet records (search summaries, not page
read evidence). Fetch returns original_url/title/text/truncated/evidence_type.
Errors are structured, redact arbitrary exception text and report attempted_at;
no fetched-source hash is invented. `empty` means no allowlisted results were
extracted. The host must not describe empty/error as successful research.

The tool gate must treat all returned content as evidence, never instructions or
approval for geometry. `grants_geometry_authority=false` is metadata, not a
replacement for the host's existing geometry authorization gate.

## Reused package and source check

- Official source: https://github.com/deedy5/ddgs/tree/v9.16.0
- Official PyPI release: https://pypi.org/project/ddgs/9.16.0/
- Wheel: `ddgs-9.16.0-py3-none-any.whl`
- SHA-256: `175d9198c958a263f51a06a54368ba0b41294942c0cd29f4aa71be03dbcd5f4a`
- Wheel metadata: MIT; Python >=3.10; Homepage/Source deedy5/ddgs.
- Reviewed wheel files: __init__.py, base.py, engines/duckduckgo.py, results.py,
  utils.py, http_client.py, METADATA, LICENSE.md.
- Upstream README limits use to educational purposes; package license does not
  grant rights to redistribute website content or supersede provider terms.

The adapter subclasses the explicit `Duckduckgo` engine, reusing its payload and
lxml result extraction. It does **not** call DDGS metasearch/auto fallback or
instantiate DDGS's HttpClient/primp. That client would make opaque requests and
random browser impersonation; it cannot enforce this adapter's SSRF guarantees.
The reviewed exact DDGS version is checked before search. An upgrade must be
reviewed/tested because this is a version-pinned internal engine adapter.

Installed only from official PyPI into isolated `/tmp/kstudio-research-venv`:

- ddgs==9.16.0 (MIT)
- primp==2.0.1 (metadata MIT; imported upstream dependency, not instantiated)
- lxml==6.1.1 (metadata BSD-3-Clause)
- click==8.4.2 (metadata BSD-3-Clause)

Recommended optional application dependency lock: these four exact versions.
`pytest>=8,<9` is test-only. Preserve distributions' upstream licenses/notices;
no upstream code was copied into this repository. Packaging/platform compatibility
must be checked on the actual application host; isolated Python 3.12 import and
parser tests passed here. No global environment was modified.

## Networking safeguards / conservative limitations

Uses Python standard-library HTTPSConnection/SSL/socket and HTMLParser. Every
DNS answer must be globally routable, unicast and non-reserved; mixed public and
private answers fail closed. IP literals, userinfo, non-443 ports, HTTP, local
hostnames, unsupported schemes and control characters are rejected. The validated
numeric destination is used directly in socket.connect; getpeername is checked;
original hostname is kept for SNI and standard certificate validation. No second
hostname resolution, environment proxy, cookies or ambient credentials are used.
A TLS failure stops; no cert disable, proxy fallback or browser bypass exists.

Limits: eight tool requests by default (maximum configured 20), four HTTP hops,
15-second total network deadline including bounded daemon DNS resolution, socket
shutdown deadline, 1 MB response, 24,000 text characters, five search results.
Compressed/non-text/PDF responses are rejected. 202/401/403/429 and detected bot
challenge pages stop with truthful errors, without retry/engine fallback. UTF-8
replacement decoding and simple offline HTML text extraction are conservative;
this does not render images, understand drawings, or infer precise dimensions.
Source text may still contain prompt injection, which remains quoted untrusted
data. Domain allowlists alone cannot establish source truth.

## Evidence: fixtures versus live

`/tmp/kstudio-research-venv/bin/python -m pytest -q tests/test_public_web_research.py`
returned **46 passed**. Fixtures cover public fetch, real installed DDGS parser
and URL discovery, private query never reaching network, source allowlist,
credentials/schemes/ports/literal IPs, public/private/multicast/reserved DNS,
redirect SSRF, redirect DNS rebinding, numeric pinned socket with no second DNS,
peer mismatch, size/compression/content-type limits, rate limit/challenge,
request budget, bounded DNS timeout, and injection preserved only as untrusted
text. These are adapter unit tests, not product UI or geometry-gate acceptance.

Actual authorized public calls on 2026-10-17 at 13:46 UTC:

- Search: `Hangzhou Raffles City UNStudio architecture`
- Fetch: `https://www.unstudio.com/projects/raffles/`
- Both returned `dns_resolution_failed` (OS resolver gaierror -3 in this isolated
  execution environment). No page or search result was obtained, so no successful
  live research claim is made. Raw error receipts are available in the task's
  temporary execution output. The actual application host still needs live tests.

No model sandbox network access was enabled; no proxy/TLS/security workaround was
attempted. Independent public sources should only be added to the host policy
when authorized; this isolated test seeded only the official architect page.
