# Changelog

Release notes for Tidepool. Newest first. Older entries describe how things worked at the time and may be out of date; the other guides describe current behavior.

## 4.2 — August 2026

- Focus mode now also hides sub-ripples assigned to other people.
- Pool limit for columns raised from 10 to 12.
- Webhook deliveries now retry up to 8 times (previously 5).
- New `ripple.moved` webhook event.

## 4.1 — May 2026

- Riptide plan: data residency added for Australia (Sydney), in addition to the European Union.
- Personal access tokens can now be created with a 365-day expiry.
- Fixed: the daily digest was sometimes sent in UTC instead of the workspace time zone.

## 4.0 — February 2026

- Free trial of the Riptide plan extended from 14 days to 21 days, and no longer requires a credit card.
- API v1 retired. All requests to v1 now return 410 Gone. Migrate to v2.
- The Current plan's monthly price changed from $9 to $10 per member; annual billing stays at $8.
- Driftwood (deleted items bin) retention extended from 14 to 30 days.

## 3.6 — November 2025

- Hardware security keys (WebAuthn) supported for two-factor authentication.
- SMS two-factor codes removed. Members using SMS were asked to switch to an authenticator app.
- Guests can now be invited to more than one pool.

## 3.5 — August 2025

- Introduced Currents (automations) on all plans.
- Free plan member limit reduced from 10 to 5 for newly created workspaces. Existing workspaces keep their limit.
- API rate limit raised from 60 to 120 requests per minute per token.

## 3.4 — April 2025

- Mobile apps: offline mode for viewing ripples. Edits made offline sync when the device reconnects.
- New keyboard shortcut `I` to assign a ripple to yourself.
- Imports from Asana added (Trello and CSV were already supported).
