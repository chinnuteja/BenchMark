# RELEASE CHECKLIST

## Data

- [x] At least 6 public-dev items
- [x] All item IDs stable
- [x] All items validate
- [x] All referenced docs exist
- [x] Demo data clearly labeled

## Grader

- [x] Strict accuracy implemented
- [x] Verdict accuracy implemented
- [x] Failure-code accuracy implemented
- [x] Clause-grounding accuracy implemented
- [x] Parse errors handled
- [x] Wrong clause can gate strict score

## Baselines

- [x] Naive prompt exists
- [x] Clause-first prompt exists
- [x] Event-graph-first prompt exists
- [x] Fake/sample outputs exist
- [x] Real outputs included only if actually run

## Report

- [x] mini_eval_report.md generated
- [x] failure_cases.md generated
- [x] Results honestly labeled
- [x] Limitations stated

## Engineering

- [x] pytest passes
- [x] make demo passes
- [x] README quickstart works
- [x] No API keys committed
- [x] .env.example exists

## Application

- [ ] Proposal linked
- [ ] Repo linked
- [ ] CONSILIUM linked
- [x] Application summary ready
