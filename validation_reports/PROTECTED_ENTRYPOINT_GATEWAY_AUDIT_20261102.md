# INVENTHOR protected native entrypoints — source diff audit (2026-11-02)

**Status:** SOURCE-ONLY REVIEW; native Organizer task/lease/current PC Main sources NOT RE-READ in this branch. No rollback, install, code removal, file repair, or native task dispatch occurred.

## Owner architecture requirement

- Five existing systems only: INVENTHOR, single Operator, original Organizer, existing Design Studio and SAME QA Factory.
- Core entrypoints/Main runtime should remain thin and stable. New owner-requested capabilities must use the EXISTING Gateway → Aggregator → Tree or approved extension seams; **not be repeatedly added as feature code to MainWindow / MainActivity / OperatorCoreActivity**.
- Gateway/Aggregator/Tree is a target architecture here. This source audit does NOT assert that a complete native Gateway/Aggregator/Tree implementation has been verified.
- Protect system integrity and concurrency without imposing arbitrary feature restrictions on the owner. Intent remains valid; conflicting operations are serialized, rebased or deferred, not silently discarded.
- A critical native boot/security repair MAY require a narrowly reviewed core edit; this audit never self-authorizes one, and never blindly reverts or purges working code.

## Grounded GitHub source findings

1. [Operator PR #3](https://github.com/inventhor-cloud/inventhor-operator-core/pull/3) changed **Windows native UI entrypoints** `windows/src/Inventhor.Operator.Desktop/MainWindow.xaml`, `MainWindow.xaml.cs`, and `App.xaml`. This is an observable source boundary violation *risk*, not proof that the owner's installed Main has those changes or that all edits are erroneous. Classify frozen entrypoints for manual 3-way diff and extraction of feature logic into the existing extension path.
2. [Operator PR #5](https://github.com/inventhor-cloud/inventhor-operator-core/pull/5) changed `OperatorWorker.cs`, `PluginCatalog.cs`, native core executors and transport files. Those include necessary legacy plugin decoupling work, so **do not revert these files wholesale**. Core host changes require source/runtime dependency analysis and fresh native Organizer/Codex owner lease before any installed refactor.
3. Neither PR #3 nor #5 changed `app/src/main/java/com/inventhor/operatorcore/v3/OperatorCoreActivity.java` according to their current changed-filename lists. This does not prove the native/local Android activity never changed at other times.
4. The real `Inventhor.Main.DesignStudio` Windows WPF sources and core Windows Main entrypoints are primarily on the owner's PC, not proven synchronized with these GitHub branches. Their actual current modifications/status are **UNKNOWN**, not CLEAN.
5. [Brain PR #6](https://github.com/inventhor-cloud/inventhor-brain/pull/6) contains source-only Studio semantic, concurrency and load advisory; it has no native Main deployment proof. This audit is isolated on a stacked draft branch to avoid racing the concurrently edited PR #6 head.

## Safe extraction / cleanup sequence — NOT YET EXECUTED ON PC

1. Read current original Organizer exact `PROJECT_ID + TASK_ID + revision + owner/lease/expiry`, Codex file ownership and newest task checkpoint using existing authorized Operator handoff. Never preempt or replay terminal work.
2. Record signed or hash-pinned baseline for the *exact* protected native host files, plus git status and a 3-way diff of installed/local vs base vs PR code. Capture real core call graph and feature-specific changes; no guessed broad search or mass edits.
3. Mark each core hunk as (a) essential platform lifecycle/bootstrap/security, (b) safe Gateway/Aggregator/Tree routing seam, (c) feature logic that should move behind an existing interface, or (d) unresolved/foreign-Codex-owned.
4. For (c), use the **existing** extension seam; preserve behavior, state, UI, permissions, native event ordering and user data. Do not create a second core/Studio/Operator/Organizer/Factory or restore retired plugins. Refactor one reversible, tested hunk at a time and keep native host diffs as small as possible.
5. Before writes, ensure approved capability, nonoverlapping semantic document/resource locks, revision/epoch compare-and-swap, memory/CPU/disk headroom and rollback snapshots. Another active lease or unknown task result means NO duplicate execution.
6. Existing Operator performs approved native routine work, compiles and verifies behavior. Existing QA Factory witnesses Windows and Android entrypoints where applicable, actual app build/run and Studio fail/fix/retest on exact artifact hashes. Preserve rollback and owner-present UAC gates.
7. Write and read back completion/remaining/evidence in the SAME original Organizer. No source audit or GitHub comment is a substitute.

## Source audit invocation

```bash
printf '%s\n' '["windows/src/Inventhor.Operator.Desktop/MainWindow.xaml.cs","windows/src/Inventhor.Operator.Service/OperatorWorker.cs"]' | python3 tools/audit_protected_host_diff.py
python3 -m unittest discover -s tests -v
```

`tools/audit_protected_host_diff.py` only reads explicitly supplied changed paths; source-only path classification. It does not read current files, inspect contents, authenticate owner, or grant merge/deploy rights. Reported no-match is not a clean-machine verdict. It leaves the owner's feature goals unconstrained; host integrity gates are separate from user feature approval.
