"""p50 / p95 latency per stage from the API's timing log lines.

    vercel logs <deployment-url> > logs.txt
    python scripts/latency_report.py logs.txt
    python scripts/latency_report.py < logs.txt

Reads lines like `timing streamed=True search=0.412 rerank=1.903 first_token=2.711 ... total=4.020`.
"""

import fileinput
import re
import statistics

LINE = re.compile(r"timing streamed=(\w+) (.*)")
STAGES = ["rewrite", "search", "rerank", "first_token", "answer", "save", "total"]


def pct(values: list[float], p: float) -> float:
    values = sorted(values)
    return values[min(len(values) - 1, max(0, round(p / 100 * len(values) + 0.5) - 1))]


def main() -> None:
    by_stage: dict[str, list[float]] = {}
    n = 0
    for line in fileinput.input(encoding="utf-8"):
        m = LINE.search(line)
        if not m:
            continue
        n += 1
        for key, value in re.findall(r"(\w+)=([\d.]+)", m.group(2)):
            by_stage.setdefault(key, []).append(float(value))
    if not n:
        print("No timing lines found.")
        return
    print(f"{n} answers\n\n{'stage':<12} {'n':>5} {'p50':>7} {'p95':>7} {'max':>7}")
    for stage in STAGES + sorted(set(by_stage) - set(STAGES)):
        v = by_stage.get(stage)
        if v:
            print(f"{stage:<12} {len(v):>5} {statistics.median(v):>6.2f}s {pct(v, 95):>6.2f}s {max(v):>6.2f}s")


if __name__ == "__main__":
    main()
