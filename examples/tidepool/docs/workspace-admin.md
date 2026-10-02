# Workspace Administration

This guide is for Harbormasters, the admins of a team workspace.

## Inviting members

Invite people from **Workspace settings → Members → Invite**. Invitations are sent by email and expire after 7 days; an expired invitation can be resent. You can also share an invite link, which can be limited to email addresses on specific domains (for example, only `@yourcompany.com`). Invite links can be disabled at any time.

On paid plans, a new member is billed from the moment they accept the invitation, not when the invitation is sent.

## Deactivating members

Deactivating a member removes their access immediately and frees their paid seat. Their ripples, comments, and attachments stay in the workspace, and their name is shown with a "deactivated" label. Ripples assigned to a deactivated member keep the assignment until you reassign them; use **Members → Reassign work** to move all of their open ripples to someone else in one step.

Deactivated members can be reactivated within 90 days with their history intact. After 90 days, reactivation creates a fresh membership.

## Transferring ownership

There is no single "owner" role. Any Harbormaster can promote another member to Harbormaster. To transfer control, promote the new admin, then have them demote you.

## Workspace time zone and locale

Each workspace has a time zone used for due-date reminders, recurring ripples, and the daily digest email. Members can override the time zone for their own display, but automations always use the workspace time zone. The workspace's week can start on Sunday or Monday.

## Daily digest

Members receive a daily digest email at 08:00 in the workspace time zone listing ripples due that day and new comments mentioning them. Each member can turn the digest off or switch it to a weekly digest sent on Mondays.

## Exporting data

Harbormasters can export the whole workspace from **Workspace settings → Export**. Exports are JSON (all data) or CSV (ripples only). Attachments are included in JSON exports as a separate ZIP file. An export link is emailed when the export is ready and stays valid for 72 hours. A workspace can run at most one full export every 24 hours.

## Deleting a workspace

Only a Harbormaster can delete a workspace, and they must type the workspace name to confirm. An active paid subscription must be cancelled first. After deletion there is a 7-day grace period during which support can restore the workspace; after that, data is permanently removed as described in the security guide.

## Custom fields

Paid plans can add custom fields to ripples: text, number, date, single-select, multi-select, and person. Each pool can have up to 30 custom fields. Custom fields can be used in automation conditions and are included in CSV exports.
