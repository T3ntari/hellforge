# Learner — Interactive Tutorial

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [learner](learner.md) | [launcher](launcher.md)

---

## Overview

**LEARNER v1.0.0** (author REGAS) is the interactive CLI tutorial for
HELLFORGE/E — it teaches step by step from absolute zero to advanced
composition, executing code on the user's machine via the E compiler. It
works entirely with relative paths (auto-detects the project root and the
`py`/`python3` interpreter) and stores progress under the local identity
dir (`.e_identity/.learner_progress.json`).

## Commands

```
learner start              begin lesson 1
learner list               list all lessons
learner lesson <N>         jump to a lesson
learner progress           show progress
learner reset              reset progress
```

Aliases: `learn` (`(alias)` in help).

## Questions, quizzes & tests

```
question <N>|random|beginner|intermediate|grand    quiz questions
quiz        (alias for question)
test <beginner|intermediate|grand> [count]         timed tests
```

At boot the plugin reports the question bank size: "LEARNER: N questions
ready".
