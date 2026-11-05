# BAI request timeout diagnosis — 2026-11-05

Actual desktop build05 image-edit requests failed during the read-only intent
stage, before any SketchUp tool was called. Two preserved attempts each exhausted
three SDK transport attempts. No geometry write was retried or lost.

## Reproduced cause

The owner's Windows session had an enabled static HTTP proxy. The bundled
Node 24.22.1 fetch did not use the existing proxy by default. An unauthenticated
GET to the same BAI `/v1/models` endpoint failed with
`UND_ERR_CONNECT_TIMEOUT` after 10,835 ms. Enabling Node's environment proxy
support returned HTTP 401 in 306 ms. The new application helper, using the same
existing proxy, returned HTTP 401 in 282 ms. HTTP 401 here is expected because
these diagnostic probes deliberately supplied no API key. It proves transport
reachability, not paid model availability or correct billing.

## Implemented change

`app/dsh_network.py` supplies network settings only to the SDK child process:

- Honor explicit HTTP(S) proxy environment settings and an explicit Node opt-out.
- For Windows GUI launches without proxy environment settings, read the user's
  already-enabled static Windows proxy settings. No registry writes, DNS edits,
  new proxy service, hardcoded machine proxy, or disabled TLS checks.
- Enable `NODE_USE_ENV_PROXY` for the bundled Node runtime. Always keep localhost,
  IPv4 and IPv6 loopback host-tool calls outside the proxy.
- Do not reinterpret SOCKS/PAC settings as an HTTP proxy. Automatic PAC execution
  is not implemented by this helper.
- Do not put proxy credentials or API keys in public evidence.

Official behavior reference: [Node environment proxy support](https://nodejs.org/api/cli.html#node_use_env_proxy1).

Read-only intent errors now persist in the project session so a refreshed page
does not show only an old successful reply. Failed input is not inserted into
accepted model history or treated as execution authorization. The SDK's synthetic
zero-token transport failures are now recorded as unknown usage, not a zero bill.

41 focused network, Harness, architecture and connection recovery tests passed.
The full built SDK initialized its real native tool inventory without inference.
Actual paid post-fix UI results are recorded separately in the live modeling report;
the transport probe and offline tests alone do not certify modeling success.
