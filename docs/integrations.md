# Integrations

Integrations connect Tidepool to the other tools your team uses. Install them from **Workspace settings → Integrations**. Only Harbormasters can install or remove integrations, but any member can connect their personal account once an integration is installed. Free workspaces can have two integrations installed at a time; paid plans have no limit.

## Slack

The Slack integration posts ripple updates to a Slack channel and lets you create ripples from Slack messages.

- Link a pool to a channel with `/tidepool link <pool name>` in that channel. A pool can be linked to at most 3 Slack channels.
- To turn any Slack message into a ripple, use the message's **More actions** menu and choose **Create ripple**. The ripple's description contains a link back to the original Slack message.
- Notifications are batched: if several updates happen to the same ripple within 2 minutes, Slack receives a single combined message.
- The `/tidepool mine` command lists the ripples assigned to you that are due in the next 7 days.

The Slack integration needs the Slack workspace admin to approve the app if your Slack workspace restricts app installs.

## GitHub

The GitHub integration links pull requests and commits to ripples.

Mention a ripple's short code (for example `TP-142`) in a branch name, commit message, or pull request title, and the pull request appears on the ripple. When a linked pull request is merged, the ripple moves automatically to the pool's last column (by default, **Settled**). You can turn off auto-move per pool in **Pool settings → Automation**.

GitHub Enterprise Server is supported on the Riptide plan only, and requires version 3.9 or later.

## Google Calendar

Ripples with a due date can be shown on a Google Calendar. Each member chooses whether to sync **only ripples assigned to them** or **every ripple in the pools they follow**. Sync is one-way: moving the event in Google Calendar does not change the ripple's due date. Calendar sync refreshes every 15 minutes.

## Zapier and Make

Tidepool has official Zapier and Make apps with triggers for new ripples, moved ripples, and new comments, and actions to create or update ripples. Zapier and Make count as integrations for the Free plan limit.

## Email-in

Every pool has a private email address. Emails sent to it become ripples: the subject becomes the title, the body becomes the description, and attachments are added to the ripple (subject to the plan's attachment size limit). Emails from addresses that are not workspace members are rejected unless the Harbormaster enables **Accept email from anyone** for that pool. Email-in addresses can be regenerated at any time, which invalidates the old address immediately.

## Removing an integration

Removing an integration deletes its stored credentials immediately. Links it created (such as GitHub pull request links on ripples) remain visible but stop updating.
