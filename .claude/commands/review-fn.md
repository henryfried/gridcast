---
description: Function-level rubric review in isolation — extracts one function plus a one-line stated purpose and reviews it via review-agent, with no surrounding file context. Fast feedback while writing; never a substitute for /review.
argument-hint: <file-path> <function-name> [--origin=human|ai] [purpose...]
allowed-tools: Read, Bash, Agent
---

Run a function-level review of one function, in isolation, against its stated purpose.

Arguments: `$ARGUMENTS` — the first two whitespace-separated tokens are the
file path and function name (e.g. `models/features.py build_features`).
Everything after that is optional. If one of the remaining tokens is
`--origin=human` or `--origin=ai` (case-insensitive, can appear
anywhere after the first two tokens), pull it out — that's the origin (see
step 3). Whatever's left after removing that token, if anything, is the
one-line purpose (e.g. `models/features.py build_features --origin=human
prepare data for training by splitting it into targets and features`). If
the path or function name is missing, stop and ask the user for both
rather than guessing. The purpose is optional — see step 2 for how it's
resolved when omitted.

## 1. Extract the function in isolation

Extract *only* the named function's source — do not read the rest of the
file for context, and do not hand the reviewer anything beyond this one
function. Use Python's `ast` module (exact, whitespace-safe) rather than a
manual text scan or grep:

```bash
python3 - "<file-path>" "<function-name>" <<'EOF'
import ast, sys
path, name = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
tree = ast.parse(src, filename=path)
node = next((n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name), None)
if node is None:
    print(f"ERROR: no function named '{name}' in {path}", file=sys.stderr)
    sys.exit(1)
lines = src.splitlines(keepends=True)
start = node.decorator_list[0].lineno if node.decorator_list else node.lineno
segment = "".join(lines[start - 1:node.end_lineno])
doc = ast.get_docstring(node, clean=True)
purpose = doc.strip().splitlines()[0] if doc else None
print("<<<SEGMENT>>>")
print(segment)
print("<<<PURPOSE>>>")
print(purpose if purpose else "(no docstring found)")
EOF
```

Substitute the real path/name for the placeholders. If the function isn't
found, report that to the user and stop — do not fall back to a
similarly-named function or the whole file.

## 2. Determine the one-line stated purpose

Resolve in this order:

1. **Explicit argument.** If the user supplied a purpose as part of
   `$ARGUMENTS` (everything after the file path and function name), use
   that verbatim — it's the freshest, most deliberate statement of intent
   available, so it wins even if the function also has a docstring.
2. **Docstring.** Otherwise, if the function has a docstring, its first
   line (from `<<<PURPOSE>>>` above) is the stated purpose.
3. **Ask.** Otherwise (no argument given, no docstring), **stop and ask
   the user** for a one-line purpose before continuing — do not invent
   one from the function's name or signature. `intent.md`'s checks only
   mean something against a purpose stated independently of the code; a
   purpose derived from the code itself is circular and would make every
   function trivially "pass" intent, which is worse than not checking it
   at all. Do not open the rest of the file or any caller to infer intent
   either, for the same reason plus the isolation this mode exists for —
   get the purpose from the user, not from more code.

## 3. Invoke review-agent in function mode

Call the Agent tool with `subagent_type: review-agent`. The prompt you give
it must contain **only**:

- An explicit statement that this is function mode (`/review-fn`), to be
  reviewed in isolation.
- The extracted function source from step 1, verbatim, in a code fence,
  labeled with the function name (and file path for reference only — not
  as an invitation to open it).
- The one-line stated purpose from step 2.
- Origin, stated plainly: if `--origin=human` or `--origin=ai` was
  given, say "Origin: HUMAN" or "Origin: AI"; otherwise say "Origin:
  not stated." Never guess or infer this from the function's style, the
  file path, or anything else — only pass along what the flag explicitly
  said, so review-agent can apply (or skip) its trust-asymmetry weighting
  on real information instead of a guess.
- This explicit instruction, verbatim: "Do not Read `<file-path>` or any
  project file other than `review/domain.md`, `review/leakage.md`,
  `review/intent.md`, `review/quality.md`. Review only the snippet above,
  in isolation — if you find yourself wanting more surrounding context to
  judge this function, that's a signal to say so in your findings, not a
  reason to go read the file."

Do not paste any other code from the file, and do not summarize or
paraphrase the function.

## 4. Relay the result

Print review-agent's full output back to the user verbatim, including its
`REVIEW SUMMARY` block. Add a one-line reminder that a clean result here
is a head start, not a sign-off — the full diff-level `/review` is still
required before merge. Don't add your own commentary on the findings
themselves.
