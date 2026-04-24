# Mito-Ribosomal Protein Database

A Django + Vue web app for browsing mitochondrial- and plastid-ribosomal protein sequences, their source organisms, and their multiple-sequence alignments. Backed by the `DESIRE_mito_as1` MySQL database.

> This README is a priming doc for future development. It records the live schema, the UX model, and the gotchas so that a new contributor (human or AI) can get productive without re-deriving decisions. If a statement here goes stale, update it here first.

---

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Web framework | Django 2.2 | `DESIRE/` project, single app `alignments/` |
| ORM targets | MySQL | `default` = `DESIRE` (legacy, unused), `mito` = `DESIRE_mito_as1` (current) |
| MySQL driver | `mysql.connector.django` | |
| Frontend | Vue 2.7 (Options API) | `static/js/components/MainPage.vue` is the app root |
| Build | Webpack 4 + vue-loader 15 | entry `./static/js/index.js`, output `static/bundles/` |
| Integration | `django-webpack-loader` | `{% render_bundle 'main' %}` in `index.html` |
| MSA viewer | Compiled UMD (`MSAV.umd.js`) | React under the hood, mounted alongside Vue via `ReactDOM.render`. Wiring deferred to phase 2. |
| Python venv | `~/ncRNA/.venv` (Python 3.10) | Shared with the ncRNA sister project. **Use this venv for every Python command.** |

---

## Quick start

```bash
# clone, then
source ~/ncRNA/.venv/bin/activate
export DJANGO_SECRET_KEY='...'
export DJANGO_USERNAME='...'      # read-write access to DESIRE_mito_as1
export DJANGO_PASSWORD='...'

python manage.py check
python manage.py runserver        # localhost:8000

# in another shell:
npm install
npm run build                     # one-shot build
# or: npm run watch               # rebuild on change
```

Open `http://localhost:8000/`. The Django index view renders `alignments/templates/alignments/index.html`, which mounts `<div id="app">` with the webpack bundle.

---

## Repository layout

```
mito_ribo_proteins_db/
├── DESIRE/                         Django project (settings, urls, wsgi)
├── alignments/                     Single Django app
│   ├── models.py                   Regenerated from live mito DB (see Gotchas)
│   ├── views.py                    index + TwinCons handlers only
│   ├── mito_views.py               (new) All /api/* endpoints for this app
│   ├── ncRNA_views.py              (legacy) ncRNA sister-project endpoints
│   ├── urls.py                     Routes: index, TwinCons, mito_views, ncRNA
│   ├── Shannon.py                  Per-column entropy calc (kept for TwinCons)
│   └── templates/alignments/
│       ├── index.html              Vue mount + webpack bundle
│       └── twc_detail.html         Unused; kept as ref
├── static/
│   ├── js/
│   │   ├── index.js                Webpack entry; imports Vue, mounts MainPage
│   │   └── components/
│   │       ├── MainPage.vue        App root (Vue 2 SFC, Options API)
│   │       ├── MainPageVars.js     initialState() factory
│   │       ├── TaxTree.vue         Recursive phylo-tree component
│   │       └── (MSA chain)         MSAV.umd.js, AlignmentViewer.js,
│   │                               BarGraph.js, Sliders.js, PositionDispatch.js,
│   │                               getStructMappingAndTWC.js, msaColorSchemes/
│   │                               └─ reserved for phase-2 MSA viewer wiring
│   └── bundles/                    Webpack output (gitignored)
├── webpack.config.js
├── package.json
├── requirements.txt
├── README.md                       (this file)
└── INSTALL.md                      Server-deployment notes (WSGI, Apache)
```

---

## Live database schema

The `mito` database (`DESIRE_mito_as1` on `130.207.36.76:3306`) is the source of truth. `alignments/models.py` must be regenerated via `python manage.py inspectdb --database mito` after any schema change — it has gone stale in the past.

### Tables

| Table | Rows | Key columns |
|---|---:|---|
| `Polymer_data` | 5602 | `id` (PK), `protein_location_header`, `strain_id` → Species, `nomgd_id` → Nomenclature |
| `Polymer_metadata` | 5602 | `id` (PK), `PData_id` → Polymer_data, plus metadata cols (see below) |
| `Nomenclature` | 91 | `nom_id` (PK), **`new_name`** (only column used by UI) |
| `Species` | 115 | `strain_id` (PK), `name`, `strain`, `taxid`, `Abbreviation` |
| `TaxGroups` | 521 | `taxgroup_id` (PK), `groupLevel`, `groupName`, `parent` (self-FK hierarchy) |
| `Alignment` | 1 | `Aln_id` (PK), `Name`, `Method`, `Source` |
| `Polymer_Alignments` | 65 | `PData_id` → Polymer_data, `Aln_id` → Alignment |
| `Residues`, `Aln_Data` | — | Residue-level, phase-2 only |

### `Polymer_metadata` columns (these drive the filters)

| Column | Type | UI role |
|---|---|---|
| `prediction_type` | varchar(100) | Dropdown. Values: `de novo prediction from mitogenome`, `original prediction`, `targeted prediction` |
| `evolutionary_origin` | varchar(100) | Top-level toggle. Values: `mitochondria`, `plastid` |
| `assembly` | varchar(100) | Dropdown of distinct values |
| `sequence_location` | varchar(500) | Free-text search |
| `assembly_location` | varchar(500) | Free-text search |
| `data_location` | varchar(500) | Free-text search |
| `alternate_name` | varchar(255) | Free-text search |
| `fragment` | varchar(50) | Optional filter |
| `fullseq` | TEXT | Shown on detail pane, monospace |

### Relationship diagram

```
                         Nomenclature
                         (nom_id, new_name)
                               ▲
                               │ nomgd_id
                               │
  Species ──── strain_id ◄── Polymer_data ───► id ◄── PData_id ── Polymer_metadata
  (name,                     (id,                                  (prediction_type,
   taxid,                     protein_location_header)              evolutionary_origin,
   Abbrev)                                                          sequence_location,
    ▲                             ▲                                 assembly_location,
    │ taxid                       │ PData_id                        data_location, …)
    │ (hypothesis:                │
    │  = TaxGroups.taxgroup_id)   │
    │                             │
 TaxGroups                    Polymer_Alignments ── Aln_id ──► Alignment
 (taxgroup_id,                                                  (Aln_id, Name,
  groupLevel,                                                    Method, Source)
  groupName,
  parent ──┐ self-FK)
           │
           └──► TaxGroups (hierarchy via parent chain)
```

`TaxGroups` contains rows at every taxonomic level (superkingdom through strain). Strain-level rows like `(2762, 'strain', 'Cyanophora paradoxa', 2761)` encode individual organisms; `Species` mirrors these exactly.

**The join is `Species.strain_id = TaxGroups.taxgroup_id`** (verified: 115/115). `Species.taxid`, `Species.strain`, `Species.Abbreviation` are all NULL in current data and should be treated as unused. To walk a species up the taxonomy, recurse through `TaxGroups.parent`.

---

## Environment variables

Required at runtime (not committed). Set in shell or `.env`:

- `DJANGO_SECRET_KEY` — Django cryptographic key.
- `DJANGO_USERNAME` — MySQL user with read access to `DESIRE_mito_as1`.
- `DJANGO_PASSWORD` — corresponding password.

`DEBUG = True` is currently hard-coded in `DESIRE/settings.py`; flip to `False` and set `ALLOWED_HOSTS` for production.

---

## UX model

Top-level title: **Mito-Ribosomal Protein Database**.

Single-page layout, sidebar + main content.

**Mode switcher** — top of the sidebar, horizontal segmented bar with three inline labels:

```
Sequences  ·  Organisms  ·  Alignments
```

One label is active (solid pastel-purple); the other two fade to ~40% opacity. Clicking swaps the sidebar filter body and the main-window content.

### Modes

| Mode | Sidebar | Main window |
|---|---|---|
| **Sequences** | Evolutionary-origin toggle, prediction-type dropdown, assembly dropdown, protein-name search (`Nomenclature.new_name`), free-text (sequence/assembly/data locations) + any pinned Organism chip | Paginated table → row click opens a detail pane with full `Polymer_metadata` + `fullseq` |
| **Organisms** | Recursive `TaxGroups` phylo tree + any pinned protein-name chip | List of `Species` with protein counts → drill-down |
| **Alignments** | `TaxGroups` tree + optional protein-name filter | List of `Alignment` rows; row click opens an **empty** detail pane (MSA viewer deferred to phase 2) |

### Cross-filtering

Each mode can **pin** a selection from another mode as a filter chip.
- In Organisms, selecting a species → "Pin as filter" → switches to Sequences with a persistent "Organism: X ×" chip.
- In Sequences, selecting a protein → "Pin as filter" → adds a "Protein: X ×" chip shown in Organisms mode.
- Chips have an `×` to remove them.

---

## Backend API

All live under `/` (routed by `alignments/urls.py` → `alignments/mito_views.py`). All querysets use `.using('mito')` — no router is configured.

| Method / Route | View | Returns |
|---|---|---|
| `GET /api/taxtree/` | `taxtree_api` | Nested JSON tree built from `TaxGroups.parent` |
| `GET /api/sequences/` | `sequences_api` | Paginated list — params: `prediction_type`, `evolutionary_origin`, `assembly`, `protein_name`, `sequence_location`, `assembly_location`, `data_location`, `taxgroup_ids[]`, `page`, `page_size` |
| `GET /api/sequences/<id>/` | `sequence_detail_api` | Full record incl. `fullseq` |
| `GET /api/organisms/` | `organisms_api` | Paginated `Species` + protein-count |
| `GET /api/alignments/` | `alignments_api` | Paginated `Alignment` + member-count |

JSON responses via `JsonResponse`. No auth (matches the ncRNA endpoints).

---

## Scope: phase 1 vs phase 2

### Phase 1 (this round)
- Three-mode browser UI with cross-filtering
- All five API endpoints above
- Phylo tree rendered from TaxGroups
- Sequence detail pane
- Alignments list only, empty detail pane

### Phase 2 (deferred)
- **MSA viewer wiring** in the Alignments detail pane (reuse the old `DropDownTree.vue` pattern: ReactDOM-render `<AlnViewer>` into a `ref`'d div, expose `window.PVAlnViewer`, feed it the alignment FASTA). The UMD bundle `static/js/components/MSAV.umd.js` is already in place.
- **TwinCons overlay** on the MSA viewer — the `/twc-api/` route in `alignments/urls.py` already works.
- Residue-level queries from `Residues` / `Aln_Data`.
- Auth / write access (currently read-only).

---

## Development recipes

### Add a new filter to Sequences mode
1. Add a UI control in the sidebar section of `MainPage.vue` under the Sequences conditional.
2. Add the new state key in `MainPageVars.js` under `sequenceFilters`.
3. Include it in the query-string built by `fetchSequences()`.
4. In `mito_views.py` → `sequences_api`, read the query param and add `.filter(...)` to the queryset.
5. Verify with `curl 'localhost:8000/api/sequences/?your_param=...'`.

### Add a new API endpoint
1. Add a `def foo_api(request):` in `alignments/mito_views.py`. Use `.using('mito')` on every query.
2. Register it in `alignments/urls.py`: `path('api/foo/', mito_views.foo_api, name='foo_api')`.
3. Return a `JsonResponse({...})`.
4. Smoke-test with `curl`.

### Regenerate models.py from live DB
```bash
python manage.py inspectdb --database mito > alignments/models.py
```
Review the diff before committing — `inspectdb` drops comments, may rename columns, and always emits `managed = False`.

---

## Gotchas

1. **`alignments/models.py` goes stale.** It has historically drifted from the live DB. **Never trust it without re-running `inspectdb --database mito`.** If an ORM query raises "Unknown column", that's probably what happened.
2. **No DB router.** Every queryset against the mito database must include `.using('mito')` explicitly. The `default` DB is `DESIRE` (legacy, currently empty/unused).
3. **`Species` ↔ `TaxGroups` join is `Species.strain_id = TaxGroups.taxgroup_id`** (not `Species.taxid` — that column is entirely NULL). Verified 115/115. If strains get added without a matching `TaxGroups` row at `groupLevel='strain'`, tree drilldown will miss them.
4. **Only 1 `Alignment` row currently exists.** Paginated Alignments responses will look sparse until more rows are ingested. That's why the detail pane renders empty for now.
5. **`Nomenclature` has other columns** (`MoleculeGroup`, `PhylogeneticOccurence`, etc.) — the UI intentionally ignores them. Use only `new_name`.
6. **MSA viewer files are present but not wired.** `MSAV.umd.js` and friends are reserved for phase 2; don't delete them.
7. **Cleanup history.** A prior mass cleanup removed `react-msa-viewer/`, `pdbe-rna-viewer/`, `pdb-topology-viewer/`, `populate_db/`, `desire_api/`, `.env/` (the old Python 3.6 venv), `node_modules/`, and most of `static/alignments/`. The old frontend (`DropDownTree.vue`) is gone; `MainPage.vue` is the replacement. `alignments/templates/alignments/index.html` still has a few `{% static 'alignments/...' %}` references pointing at deleted files — strip those when you touch that template.
8. **`.env/` and `.venv/` are both absent/empty.** Use `~/ncRNA/.venv` instead. Reinstall requirements into that venv if TwinCons or other packages are missing.

---

## Licensing

Successor to RiboVision 2 (MIT). License TBD; treat as internal until decided.
