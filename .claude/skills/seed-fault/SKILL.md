---
name: seed-fault
description: Introduce one controlled fault, observe verification failures, record evidence, and repair the fault.
---

# Seeded fault: $ARGUMENTS

Test whether the repository's verification mechanisms detect a deliberately introduced fault.

Work through these steps in order.

1. Confirm that the current code passes the relevant tests before introducing the fault.

2. Introduce only the fault described in $ARGUMENTS using the Edit tool. Do not introduce unrelated changes.

3. Observe the PostToolUse hook response. Do not repair the fault yet. Show the exact change with git diff.

4. Run the relevant tests and report the actual output. If the hook or tests do not detect the fault, report that limitation honestly.

5. Stop and wait for the human to confirm that the evidence has been recorded.

6. After human approval, repair the fault without weakening tests, hooks, or methodological rules.

7. Run make test and confirm that all tests pass. Show the final git diff.

For each experiment, record:
- The exact faulty change.
- Actual failing test output, or state that no test failed.
- Actual hook stderr, or the absence of a hook failure.
- Number of agent turns needed to repair the fault.
- Final passing test output.

Never modify data/raw/ or run make train or make all during these experiments.

Do not fabricate evidence, automatically commit changes, or hide a fault that the verification system fails to detect.
