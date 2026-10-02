# Tidepool REST API

The Tidepool API lets you read and write pools, ripples, and comments. The base URL is `https://api.tidepool.example/v2`. Version 1 of the API was retired and returns HTTP 410 Gone for every request.

## Authentication

Create a personal access token from **Profile → Developer → Tokens**. Send it in the `Authorization` header:

```
Authorization: Bearer tp_pat_xxxxxxxxxxxx
```

Personal access tokens expire after 90 days by default; you can choose 7, 30, 90, or 365 days when creating one. Tokens inherit the permissions of the user who created them. For server-to-server integrations, create an **OAuth app** instead; OAuth access tokens last 1 hour and refresh tokens last 60 days.

API access is available on all plans, including Free.

## Rate limits

Each token can make 120 requests per minute. Bulk endpoints (paths ending in `/bulk`) count as 5 requests each. When you exceed the limit the API returns HTTP 429 with a `Retry-After` header giving the number of seconds to wait. Free workspaces also have a daily cap of 5,000 requests per workspace.

## Pagination

List endpoints use cursor pagination. Pass `limit` (default 50, maximum 200) and the `cursor` value from the previous response's `next_cursor` field. When `next_cursor` is `null` there are no more results. Offset-based pagination is not supported.

## Core endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/pools` | List pools you can see |
| POST | `/pools` | Create a pool |
| GET | `/pools/{pool_id}/ripples` | List ripples in a pool |
| POST | `/pools/{pool_id}/ripples` | Create a ripple |
| PATCH | `/ripples/{ripple_id}` | Update a ripple |
| POST | `/ripples/bulk` | Create or update up to 100 ripples in one call |
| DELETE | `/ripples/{ripple_id}` | Move a ripple to Driftwood |

Ripple IDs are strings that start with `rp_`. Pool IDs start with `pl_`.

## Webhooks

Webhooks notify your server when something changes. Register them from **Workspace settings → Integrations → Webhooks**; each workspace can have up to 20 webhooks. Supported events include `ripple.created`, `ripple.updated`, `ripple.moved`, `ripple.deleted`, and `comment.created`.

Every webhook request includes an `X-Tidepool-Signature` header: an HMAC-SHA256 of the raw request body, using the webhook's signing secret as the key. Verify it before trusting the payload.

Your endpoint must respond with a 2xx status within 10 seconds. Failed deliveries are retried with exponential backoff up to 8 times over roughly 24 hours. A webhook that fails every delivery for 3 consecutive days is disabled automatically, and the Harbormasters are emailed.

## Errors

Errors return a JSON body with `error.code` and `error.message`. Common codes:

- `invalid_request` (400) — malformed body or unknown field
- `unauthorized` (401) — missing or expired token
- `forbidden` (403) — the token's user cannot access this resource
- `not_found` (404)
- `rate_limited` (429)
