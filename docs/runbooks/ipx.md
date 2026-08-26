# Runbook — IPX

```bash
make up-ipx
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/fault
curl -s -X PUT http://127.0.0.1:8080/fault -H 'content-type: application/json' -d '{"fault":"drop_request"}'
```

PASS: fault API returns ok; DRA container up; SBI proxy `/health` shows `"sepp": false`.

freeDiameter live relay: DEFERRED-TO-UBUNTU (install freeDiameter packages, load rt_default).
