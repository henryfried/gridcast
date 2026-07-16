---
description: Function-level rubric review in isolation (ROADMAP 0.2b) — extracts one function plus a one-line stated purpose and reviews it via review-agent, with no surrounding file context. Fast feedback while writing; never a substitute for /review.
argument-hint: <file-path> <function-name>
allowed-tools: Read, Bash, Agent
---

Run a function-level review per ROADMAP.md task 0.2b.

Arguments: `$ARGUMENTS` — two whitespace-separated tokens, a file path and a
function name (e.g. `models/features.py build_features`). Parse them; if
either is missing, stop and ask the user for both rather than guessing.

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

- If the function has a docstring, its first line (from `<<<PURPOSE>>>`
  above) is the stated purpose.
- If it has none, say so plainly and write a one-line purpose from the
  function's name and signature alone. Do not open the rest of the file
  or any caller to infer intent — that would defeat the isolation this
  mode exists for (ROADMAP 0.2b).

## 3. Invoke review-agent in function mode

Call the Agent tool with `subagent_type: review-agent`. The prompt you give
it must contain **only**:

- An explicit statement that this is function mode (ROADMAP 0.2b /
  `/review-fn`), to be reviewed in isolation.
- The extracted function source from step 1, verbatim, in a code fence,
  labeled with the function name (and file path for reference only — not
  as an invitation to open it).
- The one-line stated purpose from step 2.
- This explicit instruction, verbatim: "Do not Read `<file-path>` or any
  project file other than `review/domain.md`, `review/leakage.md`,
  `review/intent.md`, `review/quality.md`, and ROADMAP.md. Review only the
  snippet above, in isolation — if you find yourself wanting more
  surrounding context to judge this function, that's a signal to say so
  in your findings, not a reason to go read the file."

Do not paste any other code from the file, do not summarize or paraphrase
the function, and do not tell the reviewer which task (e.g. "0.3", LEARN
vs DELEGATE) this came from unless the user told you — inferring that
from the file would mean looking beyond the function.

## 4. Relay the result

Print review-agent's full output back to the user verbatim, including its
`REVIEW SUMMARY` block. Add a one-line reminder that a clean result here
is a head start, not a sign-off — the full diff-level `/review` is still
required before merge (ROADMAP 0.2b). Don't add your own commentary on
the findings themselves.
