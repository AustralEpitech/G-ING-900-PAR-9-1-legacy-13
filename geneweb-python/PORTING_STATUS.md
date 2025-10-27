# Porting Status: GeneWeb (OCaml) ➜ geneweb-python

Legend: [ ] TODO | [~] In Progress | [x] Done

## Commands (bin/)
- [x] gwd (web daemon) — HTTP REST API with search and filtering
- [x] gwu (utilities) — Database statistics, optimization, name export, surname list
- [x] gwb2ged (export) — GEDCOM exporter with full family linkage
- [x] ged2gwb (import) — GEDCOM importer with family linkage
- [x] check — Data consistency validation (orphans, dates, duplicates, broken links)
- [x] gwdiff (diff) — Database comparison with JSON export
- [x] gwexport (export variants) — Export to CSV, JSON, HTML formats
- [x] gwc (console) — Interactive REPL with command history and tab completion
- [ ] setup/* (setup tools)

## Core domains (lib/)
- [x] Individuals / Families / Events — Full domain model with relationships
- [~] GEDCOM support — Basic tags implemented, extended tags in progress
- [ ] Config parsing
- [ ] History & merges
- [x] Check & fixbase — Basic consistency checks implemented
- [ ] DAG & views
- [ ] Images & media

## API Features
- [x] HTTP GET endpoints (persons, families, search)
- [ ] HTTP mutations (POST/PUT/DELETE)
- [ ] Authentication & authorization

## Observability / Docs
- [x] Scaffolding
- [x] CLI parity reference
- [x] Behavior tests (23 tests covering export, import, daemon, validation, utilities, diff, multi-format export)
- [x] README & QUICKSTART guides
- [x] Wrapper script (geneweb-cli.py)

## Test Coverage Summary
```
test_check.py:            3 tests (orphans, invalid dates, duplicates)
test_ged2gwb.py:          2 tests (import, roundtrip)
test_gwb2ged.py:          2 tests (minimal export, family links)
test_gwd.py:              1 test  (HTTP daemon endpoints)
test_gwu.py:              4 tests (stats, optimize, export names, list surnames)
test_gwdiff.py:           7 tests (person/family add/remove/modify, JSON export)
test_gwexport.py:         4 tests (CSV, JSON, HTML export, empty database)
---
Total:                   23 tests passing
```

## Completed Features
### ✅ Core Commands (8/8 main commands)
1. **gwb2ged** - Export to GEDCOM format
2. **ged2gwb** - Import from GEDCOM format
3. **gwd** - HTTP REST API daemon
4. **check** - Data validation
5. **gwu** - Database utilities (stats, optimize, export-names, list-surnames)
6. **gwdiff** - Database comparison
7. **gwexport** - Multi-format export (CSV, JSON, HTML)
8. **gwc** - Interactive console

### 📝 Documentation
- Complete README with installation and usage
- QUICKSTART guide with examples
- PORTING_STATUS tracking
- Inline documentation for all modules

Notes
- We will port feature-by-feature, keeping behavior parity via tests.
- Each item links to tests that assert signatures/outputs once created.