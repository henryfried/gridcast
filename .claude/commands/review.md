---
description: Diff-level rubric review against stated intent — reviews the current branch's full diff since it diverged from main via review-agent, in diff mode. This is the surface a CI gate would run on every PR.
argument-hint: [--origin=human|ai] [stated intent / acceptance criteria...]
allowed-tools: Read, Bash, Agent
---

Run a diff-level review against the diff's stated intent.

`$ARGUMENTS`, if given, may start with `--origin=human` or
`--origin=ai` (case-insensitive) — pull that token out first if
present, it's the origin (see step 3). Only use it if the whole diff is
genuinely one origin; for a diff mixing human- and AI-written work, leave
it off (see step 3 for why that's the correct call, not a fallback).
Whatever's left after removing that token, if anything, is the stated
intent (task description / acceptance criteria) the diff is meant to
satisfy — see step 2.

## 1. Get the full diff, safely

The diff must include everything that would go into the PR: committed
changes since the branch diverged from main, *and* any uncommitted
working-tree changes (so this can be run before committing, and still
produce the identical diff once everything is pushed and CI runs it in a
clean checkout).

Find the base to diff against — prefer `origin/main`, fall back to local
`main` if there's no remote:

```bash
BASE_REF=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD 2>/dev/null)
```

If neither exists, stop and ask the user what to diff against rather than
guessing a ref.

Plain `git diff "$BASE_REF"` misses brand-new untracked files (git only
diffs paths already known to the index). Use a scratch copy of the index
so untracked files show up as additions, **without touching the user's
real staging area**:

```bash
GIT_DIR=$(git rev-parse --git-dir)
TMP_INDEX=$(mktemp)
cp "$GIT_DIR/index" "$TMP_INDEX"
GIT_INDEX_FILE="$TMP_INDEX" git add -N -A -- .
GIT_INDEX_FILE="$TMP_INDEX" git diff "$BASE_REF" > /tmp/review-diff.txt
rm -f "$TMP_INDEX"
```

(`git add -N` only ever adds paths git would normally track — anything
gitignored is invisible to it, so gitignored files never enter the diff.
That satisfies the "don't rely on gitignored files" constraint by
construction, not by extra filtering.)

If the resulting diff is empty, say so and stop — there's nothing to
review, and inventing findings against an empty diff would violate the
"no issues found" contract below.

## 2. Determine the stated intent

Resolve in this order — never derive the stated intent from the diff's
own content. A description reverse-engineered from the code being
reviewed is circular (the diff will always trivially "satisfy" a
description of itself), which makes `intent.md`'s checks vacuous exactly
like it would for `/review-fn`'s docstring case:

1. **Explicit argument.** If `$ARGUMENTS` is non-empty, use it verbatim.
2. **GitHub PR description.** Otherwise, if the `gh` CLI is available and
   authenticated and a PR exists for the current branch, use its title +
   body: `gh pr view --json title,body -q '.title + "\n\n" + .body'`.
   This is the real-world case for the CI job (0.6) — the PR description
   *is* the stated intent there.
3. **Commit messages.** Otherwise, use the commit messages in the diff
   range: `git log "$BASE_REF"..HEAD --format=%B`. Weaker than a PR
   description but still written independently of what a reviewer will
   check it against.
4. **Ask.** If all three are empty (e.g. only uncommitted changes, no
   commits, no PR, no argument), stop and ask the user for the stated
   intent before continuing.

## 3. Invoke review-agent in diff mode

Call the Agent tool with `subagent_type: review-agent`. The prompt you
give it must contain:

- An explicit statement that this is diff mode (`/review`).
- The full diff from step 1, verbatim (as a file/code block — do not
  summarize or truncate it).
- The stated intent from step 2, labeled with which source it came from
  (argument / PR description / commit messages), so the reviewer can
  weigh how authoritative it is.
- Origin, stated plainly: if `--origin=human` or `--origin=ai` was
  given, say "Origin: HUMAN" or "Origin: AI"; otherwise say "Origin:
  not stated." Never guess or infer this from the diff's content or a
  task ID mentioned in a commit message — only pass along what the flag
  explicitly said.
- This explicit instruction, verbatim: "Only `review/domain.md`,
  `review/leakage.md`, `review/intent.md`, and `review/quality.md` are
  needed for the rubric itself — that's the full scope of what to read
  for this review."

Do not paste your own summary of the diff in place of the diff, and do
not editorialize about which findings matter before the reviewer runs —
that's its job, not the command's.

## 4. Relay the result

Print review-agent's full output back to the user verbatim, including
its `REVIEW SUMMARY` block and every pass's explicit "clean" or finding
list — it must state "no issues found in pass X" rather than inventing
filler, so don't paraphrase passes down to just the findings. Unlike
`/review-fn`, this **is** the surface any CI gate would run on: an
`overall: FAIL` here means don't merge as-is, not just "worth a look."
