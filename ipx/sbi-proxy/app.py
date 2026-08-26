"""
MOCK: SBI HTTP proxy stand-in for inter-PLMN HTTP/2 SBI relay.
Production equivalent: SEPP N32 (TS 33.501 / 29.573) between PLMNs.
per lab decision V14 — Open5GS SEPP absent.
Divergences: no N32-c negotiation, no PRINS, no IPX-provider modification tracking.
Never label this service as SEPP.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI(title="IPX SBI Proxy Stand-In (NOT SEPP)", version="0.1.0")

# Lab forwarding table — visited edge -> home UDM/AUSF via proxy
FORWARD = {
    "udm": "http://10.10.3.22:7777",
    "ausf": "http://10.10.3.21:7777",
}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "role": "sbi-proxy-stand-in", "sepp": False}


@app.api_route("/nausf-auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def nausf(path: str, request: Request) -> Response:
    """HTTP/1 debug mirror of Nausf_UEAuthentication. Open5GS SBI is HTTP/2 — use IPX dual-home, not this."""
    return await _forward(FORWARD["ausf"], f"nausf-auth/{path}", request)


@app.api_route("/n32-standin/{nf}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def relay(nf: str, path: str, request: Request) -> Response:
    base = FORWARD.get(nf)
    if not base:
        return Response(content="unknown nf", status_code=404)
    return await _forward(base, path, request)


async def _forward(base: str, path: str, request: Request) -> Response:
    url = f"{base}/{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request(
            request.method,
            url,
            content=body,
            headers={"content-type": request.headers.get("content-type", "application/json")},
        )
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))
