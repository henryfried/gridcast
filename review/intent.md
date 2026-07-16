1. Does the diff satisfy every acceptance criterion in the task description, not just the easiest ones?
2. Is there any change in the diff unrelated to the stated intent (scope creep that belongs in a separate PR)?
3. If the task description calls out specific edge cases, are they actually handled, or only the happy path?
4. Are there leftover TODOs, commented-out code, or stub logic that contradicts a claim the task is complete?
5. Does the diff's own description/commit message accurately reflect what changed (no undisclosed side effects — schema changes, config changes, new dependencies)?
6. If the acceptance criteria specifies a count or threshold (e.g. "≥6 checks"), does the diff literally meet it?