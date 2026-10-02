# Getting Started with Tidepool

Tidepool is a task tracker for small teams. Work is organized into **Pools** (a pool is roughly a project), and each pool contains **Ripples** (individual tasks). This guide covers installation, creating your first pool, and the keyboard shortcuts most people use daily.

## System requirements

The Tidepool desktop app runs on Windows 10 (build 19045) or later, macOS 13 Ventura or later, and Ubuntu 22.04 or later. It needs at least 4 GB of RAM and 300 MB of free disk space. The web app works in the two most recent versions of Chrome, Edge, Firefox, and Safari. Internet Explorer is not supported.

Mobile apps are available for iOS 16+ and Android 11+. The mobile apps support viewing and editing ripples but cannot create new pools or manage members; those actions are desktop and web only.

## Creating your account

Sign up at the Tidepool website with an email address or with Google single sign-on. After signing up you land in a personal workspace called **My Shore**. My Shore is private and cannot be shared; to collaborate you must create a team workspace.

To create a team workspace, open the workspace switcher in the top-left corner and choose **New team workspace**. Workspace names must be between 3 and 40 characters. The person who creates the workspace becomes its first **Harbormaster** (admin).

## Creating your first pool

Inside a team workspace, click **New pool** or press `P`. Every pool has a name, an optional emoji icon, and a **tide color** used on the board. Pools can be *open* (visible to every workspace member) or *sheltered* (visible only to invited members). You can switch a pool between open and sheltered at any time from Pool settings.

Each pool starts with three default columns: **Backlog**, **Flowing**, and **Settled**. You can rename these or add up to 12 columns per pool.

## Ripples

A ripple is a single task. Ripples have a title, a description written in markdown, an assignee, a due date, and optional labels. A ripple can have up to 50 sub-ripples (checklist items). Attachments on a ripple are limited to 25 MB per file on the Free plan and 250 MB per file on paid plans.

Ripples that have not been updated in 30 days are marked **stagnant** and shown with a faded card. Stagnant ripples are never deleted automatically; the marker is only visual.

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| New ripple | `N` |
| New pool | `P` |
| Search everything | `Ctrl+K` (Windows/Linux) or `Cmd+K` (macOS) |
| Assign to me | `I` |
| Move ripple to next column | `]` |
| Move ripple to previous column | `[` |
| Toggle focus mode | `F` |

Focus mode hides every ripple that is not assigned to you. Press `F` again to exit.

## Importing from other tools

Tidepool can import CSV files and exports from Trello and Asana. Imports are available from **Workspace settings → Import**. A single import can contain at most 10,000 ripples; larger exports must be split into multiple files. Comments are imported, but comment reactions are not.
