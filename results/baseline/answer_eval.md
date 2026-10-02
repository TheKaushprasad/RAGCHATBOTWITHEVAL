# Answer-quality eval

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=5 · MIN_SIMILARITY=0.3 · chunks 500/50

| metric | value | n |
|---|---|---|
| Answer accuracy (judge) | 82% | 40 |
| Faithfulness (judge) | 100% | 40 |
| Citation accuracy | 82% | 40 |
| False refusals | 15% | 40 |
| Correct refusals on unanswerable | 100% | 10 |
| Latency p50 / p95 | 2.7s / 5.1s | 50 |

## Failures

- **What operating systems does the desktop app support?**: refused. refused although the docs contain the answer
  > I don't know.
- **What happens to tasks nobody has touched in a month?**: partial. The answer correctly states that ripples with no updates for 30 days become 'stagnant' and can trigger automations called currents, but it omits that stagnant ripples are shown faded and are never deleted automatically.
  > Tasks (ripples) that have no updates for 30 days become "stagnant," which can trigger automations called currents based on this event [4].
- **What is the keyboard shortcut to only show tasks assigned to me?**: refused. refused although the docs contain the answer
  > I don't know.
- **Can I pay with PayPal?**: refused. refused although the docs contain the answer
  > I don't know.
- **What happens if my card payment keeps failing?**: refused. refused although the docs contain the answer
  > I don't know.
- **Does two-factor authentication support SMS codes?**: refused. refused although the docs contain the answer
  > I don't know.
- **What happens when we hit the monthly automation run limit?**: partial. The answer correctly states that currents pause until the 1st of the next month and events during the pause are skipped, not queued, but it adds that Harbormasters receive an email notification at 80% usage, which is supported by the passage; however, the question only asks what happens when the limit is hit, so the notification detail is extra but not incorrect.
  > When a workspace reaches its monthly run limit for automations ("currents"), the currents pause until the 1st of the next month. They are not queued, so events during the pause are skipped. Harbormasters receive an email notification when 80% of the monthly runs have been used [2].
- **When was the Australia data region added?**: refused. refused although the docs contain the answer
  > I don't know.

Per-question detail: `results/answers.jsonl`.
