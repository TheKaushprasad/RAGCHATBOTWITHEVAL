# Security and Data Handling

## Encryption

All data is encrypted in transit with TLS 1.2 or higher. Data at rest is encrypted with AES-256. Attachments are stored in a separate storage bucket from ripple content, and each workspace's attachments are encrypted with a workspace-specific key.

Riptide customers can bring their own encryption key (BYOK) through AWS KMS. BYOK is not available on other plans.

## Data residency

By default, workspace data is stored in the United States (us-east-1). Riptide workspaces can choose to store data in the European Union (Frankfurt) or Australia (Sydney). The region is chosen when the workspace is created and can be changed only by contacting support; migrations take up to 5 business days and the workspace is read-only for the final hour of the move.

## Authentication

Members can sign in with email and password, Google single sign-on, or (on Riptide) SAML SSO with providers such as Okta, Azure AD, and OneLogin. Passwords must be at least 12 characters.

Two-factor authentication (2FA) supports authenticator apps and hardware security keys (WebAuthn). SMS codes are not supported. Harbormasters can require 2FA for every member of a workspace from **Workspace settings → Security**. When 2FA is required, members without it are prompted to set it up at their next sign-in and cannot access the workspace until they do.

Sessions expire after 30 days of inactivity on web and desktop. Harbormasters on Riptide can shorten this to as little as 1 hour.

## Roles

- **Harbormaster** — full admin: billing, security settings, member management, and every pool.
- **Member** — can create pools, and can see all open pools plus sheltered pools they are invited to.
- **Guest** — can see only the pools they are invited to; cannot create pools.

A workspace must always have at least one Harbormaster. The last Harbormaster cannot leave or be demoted until another member is promoted.

## Backups and retention

Tidepool takes encrypted backups every 6 hours and retains them for 35 days. Backups are stored in a different region from the primary data.

Deleted ripples go to the **Driftwood** bin, where they stay for 30 days before permanent deletion. Harbormasters can restore anything in Driftwood. Deleted pools are also kept in Driftwood for 30 days.

When a workspace is deleted, all data is permanently removed within 45 days, including from backups.

## Audit logs

Audit logs are available on Riptide only. They record sign-ins, permission changes, exports, pool deletions, and integration installs. Audit logs are retained for 2 years and can be exported as CSV or streamed to a SIEM via webhook.

## Reporting a vulnerability

Report security issues to the security team through the responsible disclosure form on the Tidepool trust page. We acknowledge reports within 2 business days. We run a private bug bounty program; researchers are invited after their first valid report.
