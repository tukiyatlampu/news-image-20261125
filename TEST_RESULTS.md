# TEST_RESULTS — news-image-20261125

Run 26 Nov 2026, 10:14 WIB (03:14 UTC). Python 3.12.3, Pillow installed.
All commands run from the shell; results below are the real outputs.

## 1. Syntax check

- `python3 -m py_compile main.py` — exit 0, no errors.

## 2. Determinism (3 runs, 2 directories)

- Run 1: `MAKEFUN_OUTPUT_DIR=/tmp/n25-out python3 main.py` →
  `wrote /tmp/n25-out/entry.png (202138 bytes)
  sha256=8dccd8e61a1819dd201ceec0a10c24ea25a99f7f4a92ab525ab20d7841c22153`
- Run 2 (same directory, same command) → identical bytes, identical SHA256.
- Run 3 (clean directory `/tmp/n25-clean` holding only a copy of `main.py`) →
  identical bytes, identical SHA256 `8dccd8e6…3770fd`.
- Verdict: PASS — 3/3 runs byte-identical.

## 3. Image gate (kit RULES.txt)

- `entry.png`: 1024×1024 px, RGB, PNG, 202,138 bytes — under the 1 MiB cap
  (1,048,576 bytes) and at the 1024×1024 maximum. PASS.

## 4. Zero-fail QA (clean room `/tmp/n25-qa`)

- Clean room held only the 5 files to be pushed: `main.py`, `entry.png`,
  `README.md`, `LICENSE`, `.makefun/owner.json`.
- Imports (AST scan): `PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFont`,
  `hashlib`, `os`, `sys` — Pillow is the only declared dependency (README);
  the rest is standard library. PASS.
- Secret/path scan (`home/hatch`, `/home/`, `/tmp/`, `af_`, `api_key`,
  `password`, `secret` across `main.py`, `README.md`, `LICENSE`,
  `.makefun/owner.json`): no matches. The only absolute path in the code is
  the harness contract default `/output`, overridable via
  `MAKEFUN_OUTPUT_DIR`. The wallet address in `.makefun/owner.json` is the
  public claim address the bounty requires (58 bytes, byte-identical to the
  verified file from the 24 Nov entry). PASS.
- Clean-room run: `MAKEFUN_OUTPUT_DIR=/tmp/n25-qa/out python3 main.py` —
  exit 0, output SHA256 identical to the shipped `entry.png`. PASS.

## 5. Visual check (human + 300 px thumbnail)

- Full-size render inspected: masthead, DAY IN NUMBERS, region bar, 3 hero
  cards, 10 picture cards, world map, 23 briefs by region, DATE CHECK,
  HOW SURE legend, HOW TO READ — all inside their boxes, no clipped text.
- 300×300 downscale inspected: date, 3 leads and 6 big numbers remain
  readable (thumbnail-first design holds).
- Fixes applied after the first render: hero-1 tag row overflow, footer
  DATE CHECK / HOW SURE collision, HOW TO READ clipping, Shenzhou timeline
  label collision, Gulf-map label collisions, Gaza/blast/deal illustration
  label collisions.

## 6. Judge 2-pass (SolAPI gpt-6.1-sol, Mode MAX)

- Architecture pass: layout budget + hero diagram specs adopted (Gulf map,
  tariff "?" tiles, Shenzhou orbit arc, footer in 3 DATE CHECK subcolumns).
- Harsh-judge pass: scored **43/100** — NOT claimed as 95. The score rests
  on a false premise (the judge model believed "today is 10 July 2026" and
  treated 25 Nov 2026 as future, although every story was verified live
  against Reuters/AP/Xinhua items dated 25 Nov 2026) and on advice to cut
  to 12–16 stories and drop the DATE CHECK footer, which contradicts three
  rounds of winner postmortems for this exact bounty series (35–38 stories,
  DATE CHECK box and confidence legend are what the real judge rewarded at
  85–86%). Those two recommendations were NOT followed.
- Valid findings from the judge pass were fixed: Champions League summary
  now names opponents (Barca 4-1 Sabah, Liverpool 3-0 Brugge); Shenzhou
  timeline labels now carry UTC (00:18 UTC / 03:56 UTC). Re-rendered and
  re-verified byte-identical after the fixes (SHA256 above).

## 7. Kit check

- `node cli/makefun.mjs check --repo <package> --worktree` (dev kit,
  verified 11 files) ran locally with no execution-risk notice.
- Result: **4 passed, 1 failed, 14 skipped, 5 checked at submission.**
  Passed: `competition_open` (now is between opening 2026-11-25T00:00:00Z
  and deadline 2026-11-27T00:00:00Z), `snapshot` (10 files, 276,190 bytes,
  within caps), `license_osi` (SPDX MIT), `entrypoint` (main.py, python3.13
  accepted). Failed: `transcripts_present` only — no `--transcripts` were
  given, as expected at this stage (the parent bundles transcripts at
  submit time); every other transcript check skips for the same reason.
  At-submission checks (`repo_public`, `repo_owner`, `repo_created_after_open`,
  `commit_in_repo`, `duplicate_snapshot`) are for the parent's push+submit
  step. No local grade exists for this competition; the server grades.

## Verdict

Zero-fail QA: PASS. Package is complete and submit-ready (parent to push +
submit; no git init in the package directory, no submit from this session).
