# Automations

Automations ("Currents") run actions automatically when something happens in a pool. Create them from **Pool settings → Automation → New current**. A current has one trigger, optional conditions, and one or more actions.

## Limits

| Plan | Currents per pool | Runs per month (workspace) |
|---|---|---|
| Free | 3 | 250 |
| Current | 25 | 10,000 |
| Riptide | Unlimited | 100,000 |

When a workspace reaches its monthly run limit, currents pause until the 1st of the next month. They are not queued; events during the pause are skipped. Harbormasters receive an email when 80% of the monthly runs have been used.

## Triggers

- A ripple is created
- A ripple moves into a column
- A ripple's due date is today
- A ripple becomes stagnant (no updates for 30 days)
- A label is added
- A comment contains a keyword

## Conditions

Conditions filter when a current runs. You can check the ripple's assignee, labels, column, priority, or whether it has sub-ripples. Conditions can be combined with AND only; OR conditions are not supported, so create two separate currents instead.

## Actions

- Assign the ripple to a person, or to the person who triggered the event
- Move the ripple to a column
- Add or remove a label
- Set the due date relative to today (for example, "in 3 days")
- Post a comment, which can include the ripple's title and assignee as placeholders
- Send a webhook to a URL you choose

A single current can have at most 5 actions. Actions run in the order they are listed.

## Loops and safety

To prevent infinite loops, a ripple can trigger at most 10 current runs within one minute. Further runs for that ripple are blocked for the rest of that minute and logged as **loop-protected** in the automation history.

## Automation history

Each pool keeps an automation history showing every run, the triggering event, and whether each action succeeded. History is kept for 14 days on Free and 90 days on paid plans. A failed action does not stop the remaining actions in the same run.

## Recurring ripples

Recurring ripples are created on a schedule rather than by an event. You can repeat daily, weekly on chosen weekdays, monthly on a day of the month, or every N days. Recurring ripples are created at 06:00 in the workspace's time zone. They count toward the monthly run limit like any other current.
