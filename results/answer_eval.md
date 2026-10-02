# Answer-quality eval

Provider `openai` · chat `gpt-4.1-mini` · judge `gpt-4.1-mini` · retrieval `vector` k=3 · MIN_SIMILARITY=0.224 · chunks 350/50

| metric | value | n |
|---|---|---|
| Answer accuracy (judge) | 94% | 40 |
| Faithfulness (judge) | 98% | 40 |
| Citation accuracy | 98% | 40 |
| False refusals | 2% | 40 |
| Correct refusals on unanswerable | 100% | 10 |
| Latency p50 / p95 | 2.6s / 5.2s | 50 |

## Failures

- **What happens to tasks nobody has touched in a month?**: refused. refused although the docs contain the answer
  > I don't know. The provided context passages do not mention what happens to tasks that nobody has touched in a month.
- **Do Zapier zaps count toward the Free plan integration limit?**: partial, unfaithful. The answer correctly states that Zapier counts as an integration for the Free plan limit but omits that the Free plan limit is two integrations and that Make also counts toward this limit, which is stated in the reference.
  > Yes, Zapier counts as an integration for the Free plan limit [1].
- **What happens when we hit the monthly automation run limit?**: partial. The answer correctly states that currents pause until the 1st of the next month and events during the pause are skipped, not queued, and that harbormasters receive an email at 80% usage, but it adds the detail that this happens when a workspace reaches its monthly automation run limit, which is implied but not explicitly stated in the reference.
  > When a workspace reaches its monthly automation run limit, currents pause until the 1st of the next month. Events during the pause are skipped and not queued. Harbormasters receive an email when 80% of the monthly runs have been used [1].
- **Can a deleted workspace be restored?**: partial. The answer correctly states the 7-day grace period for restoration but adds that data is permanently removed after that, which is implied but not explicitly stated in the reference passage.
  > Yes, a deleted workspace can be restored within a 7-day grace period after deletion. After that period, data is permanently removed and cannot be restored [1].

Per-question detail: `results/answers.jsonl`.
