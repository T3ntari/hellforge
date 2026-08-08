**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [trust-model](security/trust-model.md) | [strict-enforcement](security/strict-enforcement.md) | [identity-management](security/identity-management.md) | [rate-limiting](security/rate-limiting.md)

## Rate Limiting

### Client-Side Limits

The Piano DSL client enforces rate limits on outgoing requests to the configured registry (HF_VERIFY_URL):

| Endpoint | Limit | Window |
|---|---|---|
| `/verify` (registry submit) | 3 requests | 60 seconds |
| `/confirm` (registry review) | 10 requests | 60 seconds |
| `/api/v1/pkglist` | 30 requests | 60 seconds |

### Server-Side Limits

The server enforces additional limits per session token and IP address. Exceeding limits results in a `429 Too Many Requests` response with a `Retry-After` header.

### Blocks

Repeated violation of rate limits results in a temporary block:

- 1st offense: 60-second block
- 2nd offense: 5-minute block
- 3rd offense: 1-hour block
- Further offenses: 24-hour block

### Configuration

```
piano config set rate_limit.max_retries 3
piano config set rate_limit.backoff_base 2.0
```

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**