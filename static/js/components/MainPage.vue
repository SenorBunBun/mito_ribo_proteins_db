<template>
  <div class="app-shell">
    <aside class="sidebar">
      <header class="brand">
        <h1 class="brand-title">Mito-Ribosomal Protein Database</h1>
      </header>

      <nav class="mode-switcher" role="tablist" aria-label="View mode">
        <button
          v-for="m in modes"
          :key="m.id"
          type="button"
          role="tab"
          :aria-selected="activeMode === m.id"
          class="mode-btn"
          :class="{ active: activeMode === m.id }"
          @click="setMode(m.id)"
        >{{ m.label }}</button>
      </nav>

      <section class="filters">
        <!-- Cross-filter chips visible across all modes -->
        <div v-if="chips.length" class="chip-row">
          <span
            v-for="chip in chips"
            :key="chip.key"
            class="chip"
          >
            <span class="chip-label">{{ chip.text }}</span>
            <button type="button" class="chip-x" @click="removeChip(chip)" aria-label="Remove filter">×</button>
          </span>
        </div>

        <!-- Sequences mode filters -->
        <template v-if="activeMode === 'sequences'">
          <div class="filter-group">
            <label class="filter-label">Evolutionary origin</label>
            <div class="segmented">
              <button
                v-for="v in originValues"
                :key="v.value || 'both'"
                type="button"
                class="seg"
                :class="{ active: sequenceFilters.evolutionary_origin === v.value }"
                @click="setSeqFilter('evolutionary_origin', v.value)"
              >{{ v.label }}</button>
            </div>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="f-prediction">Prediction type</label>
            <select id="f-prediction" v-model="sequenceFilters.prediction_type" @change="onSeqFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.prediction_type" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="f-name">Protein name</label>
            <select id="f-name" v-model="sequenceFilters.protein_name" @change="onSeqFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.protein_names" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="f-seqloc">Sequence location</label>
            <select id="f-seqloc" v-model="sequenceFilters.sequence_location" @change="onSeqFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.sequence_location" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="f-asmloc">Assembly location</label>
            <select id="f-asmloc" v-model="sequenceFilters.assembly_location" @change="onSeqFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.assembly_location" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="f-dataloc">Data location</label>
            <select id="f-dataloc" v-model="sequenceFilters.data_location" @change="onSeqFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.data_location" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group filter-tree">
            <label class="filter-label">Organismal filter</label>
            <input
              v-if="taxTree"
              type="search"
              class="tree-search"
              placeholder="Search taxa…"
              v-model.trim="taxSearch"
            />
            <label v-if="taxTree" class="tree-toggle">
              <input type="checkbox" v-model="simplifyTree" />
              <span>Show simplified (hide clades)</span>
            </label>
            <div v-if="taxTreeLoading" class="muted">Loading tree…</div>
            <TaxTree
              v-else-if="displayedTaxTree"
              :nodes="displayedTaxTree"
              :checked-ids="crossFilters.taxgroup_ids"
              :open-ids="effectiveOpenTaxIds"
              @check="onTaxCheck"
              @toggle="onTaxToggle"
            />
            <div v-else-if="taxSearch" class="muted">No matches.</div>
          </div>
        </template>

        <!-- Organisms mode filters (metadata filters narrow the organism list
             to strains that have at least one matching protein). -->
        <template v-if="activeMode === 'organisms'">
          <div class="filter-group">
            <label class="filter-label">Evolutionary origin</label>
            <div class="segmented">
              <button
                v-for="v in originValues"
                :key="v.value || 'both'"
                type="button"
                class="seg"
                :class="{ active: organismFilters.evolutionary_origin === v.value }"
                @click="setOrgFilter('evolutionary_origin', v.value)"
              >{{ v.label }}</button>
            </div>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="o-prediction">Prediction type</label>
            <select id="o-prediction" v-model="organismFilters.prediction_type" @change="onOrgFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.prediction_type" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="o-name">Protein name</label>
            <select id="o-name" v-model="organismFilters.protein_name" @change="onOrgFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.protein_names" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="o-seqloc">Sequence location</label>
            <select id="o-seqloc" v-model="organismFilters.sequence_location" @change="onOrgFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.sequence_location" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="o-asmloc">Assembly location</label>
            <select id="o-asmloc" v-model="organismFilters.assembly_location" @change="onOrgFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.assembly_location" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label" for="o-dataloc">Data location</label>
            <select id="o-dataloc" v-model="organismFilters.data_location" @change="onOrgFilterChange()">
              <option value="">All</option>
              <option v-for="v in filterOptions.data_location" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
          <div class="filter-group filter-tree">
            <label class="filter-label">Taxonomy</label>
            <input
              v-if="taxTree"
              type="search"
              class="tree-search"
              placeholder="Search taxa…"
              v-model.trim="taxSearch"
            />
            <label v-if="taxTree" class="tree-toggle">
              <input type="checkbox" v-model="simplifyTree" />
              <span>Show simplified (hide clades)</span>
            </label>
            <div v-if="taxTreeLoading" class="muted">Loading tree…</div>
            <TaxTree
              v-else-if="displayedTaxTree"
              :nodes="displayedTaxTree"
              :checked-ids="crossFilters.taxgroup_ids"
              :open-ids="effectiveOpenTaxIds"
              @check="onTaxCheck"
              @toggle="onTaxToggle"
            />
            <div v-else-if="taxSearch" class="muted">No matches.</div>
          </div>
        </template>

        <!-- Alignments mode filters: organism gate first, then protein. -->
        <template v-if="activeMode === 'alignments'">
          <div class="filter-group filter-tree">
            <label class="filter-label">
              <span class="step-num">1</span> Select organism
            </label>
            <input
              v-if="taxTree"
              type="search"
              class="tree-search"
              placeholder="Search taxa…"
              v-model.trim="taxSearch"
            />
            <label v-if="taxTree" class="tree-toggle">
              <input type="checkbox" v-model="simplifyTree" />
              <span>Show simplified (hide clades)</span>
            </label>
            <div v-if="taxTreeLoading" class="muted">Loading tree…</div>
            <TaxTree
              v-else-if="displayedTaxTree"
              :nodes="displayedTaxTree"
              :checked-ids="crossFilters.taxgroup_ids"
              :open-ids="effectiveOpenTaxIds"
              @check="onTaxCheck"
              @toggle="onTaxToggle"
            />
            <div v-else-if="taxSearch" class="muted">No matches.</div>
          </div>
          <div class="filter-group" :class="{ disabled: !crossFilters.taxgroup_ids.length }">
            <label class="filter-label" for="a-name">
              <span class="step-num">2</span> Protein
              <span v-if="crossFilters.taxgroup_ids.length" class="muted small">
                ({{ alignmentProteinOptions.length }} available)
              </span>
            </label>
            <select
              id="a-name"
              :key="'aln-pro-' + alignmentProteinOptions.length"
              v-model="alignmentFilters.protein_name"
              :disabled="!crossFilters.taxgroup_ids.length"
              @change="onAlnFilterChange()"
            >
              <option value="">
                <template v-if="!crossFilters.taxgroup_ids.length">Select an organism first</template>
                <template v-else-if="!alignmentProteinOptions.length">Loading…</template>
                <template v-else>All available</template>
              </option>
              <option v-for="v in alignmentProteinOptions" :key="v" :value="v">{{ v }}</option>
            </select>
          </div>
        </template>
      </section>
    </aside>

    <main class="content">
      <header class="content-header">
        <h2 class="content-title">{{ modeLabel }}</h2>
        <div class="result-meta" v-if="resultsTotal !== null">
          {{ resultsTotal.toLocaleString() }} result{{ resultsTotal === 1 ? '' : 's' }}
          <span v-if="resultsTotal > pageSize">· page {{ page }} / {{ totalPages }}</span>
        </div>
      </header>

      <div v-if="error" class="error">{{ error }}</div>

      <!-- Sequences table -->
      <section v-if="activeMode === 'sequences'" class="results">
        <table class="results-table" v-if="results.length">
          <thead>
            <tr>
              <th>Name</th>
              <th>Strain</th>
              <th>Origin</th>
              <th>Prediction</th>
              <th>Header</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in results"
              :key="r.id"
              @click="openDetail(r.id)"
              :class="{ selected: selectedDetail && selectedDetail.id === r.id }"
            >
              <td class="mono">{{ r.protein_name || '—' }}</td>
              <td>{{ r.strain_name || '—' }}</td>
              <td>{{ r.evolutionary_origin || '—' }}</td>
              <td class="small">{{ r.prediction_type || '—' }}</td>
              <td class="truncate mono small" :title="r.protein_location_header">{{ r.protein_location_header || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else-if="!loading" class="muted empty">No sequences match the current filters.</div>
      </section>

      <!-- Organisms list (aggregated by strain) -->
      <section v-if="activeMode === 'organisms'" class="results">
        <table class="results-table" v-if="results.length">
          <thead>
            <tr>
              <th>Organism</th>
              <th>Proteins</th>
              <th>Origins</th>
              <th>Prediction types</th>
              <th class="action-col"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in results" :key="r.strain_id">
              <td>{{ r.name }}</td>
              <td class="mono">{{ r.protein_count }}</td>
              <td class="tags-cell">
                <span v-for="o in r.origins || []" :key="o" class="tag">{{ o }}</span>
                <span v-if="!(r.origins || []).length" class="muted">—</span>
              </td>
              <td class="tags-cell small">
                <span v-for="p in r.prediction_types || []" :key="p" class="tag tag-muted">{{ p }}</span>
                <span v-if="!(r.prediction_types || []).length" class="muted">—</span>
              </td>
              <td class="action-col">
                <button type="button" class="pill-btn" @click.stop="pinOrganismToSequences(r)">
                  View sequences →
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else-if="!loading" class="muted empty">No organisms match the current filters.</div>
      </section>

      <!-- Alignments list (gated on organism selection) -->
      <section v-if="activeMode === 'alignments'" class="results">
        <div v-if="!crossFilters.taxgroup_ids.length" class="muted empty">
          <p class="guide-step">Step 1 · Pick one or more organisms from the taxonomy panel.</p>
          <p class="guide-step">Step 2 · The protein picker will populate with proteins available in those organisms.</p>
        </div>
        <template v-else>
          <table class="results-table" v-if="results.length">
            <thead>
              <tr>
                <th>Name</th>
                <th>Method</th>
                <th>Source</th>
                <th>Members</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in results"
                :key="r.aln_id"
                @click="selectedAlignment = r"
                :class="{ selected: selectedAlignment && selectedAlignment.aln_id === r.aln_id }"
              >
                <td>{{ r.name }}</td>
                <td>{{ r.method }}</td>
                <td>{{ r.source }}</td>
                <td class="mono">{{ r.member_count }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else-if="!loading" class="muted empty">No alignments contain a member matching the current selection.</div>
        </template>
      </section>

      <!-- Pagination -->
      <nav v-if="totalPages > 1" class="pagination">
        <button type="button" :disabled="page <= 1" @click="goPage(page - 1)">Previous</button>
        <span>Page {{ page }} of {{ totalPages }}</span>
        <button type="button" :disabled="page >= totalPages" @click="goPage(page + 1)">Next</button>
      </nav>

      <!-- Detail panes -->
      <aside v-if="activeMode === 'sequences' && selectedDetail" class="detail">
        <header class="detail-header">
          <h3>{{ selectedDetail.protein_name || '(unnamed)' }}</h3>
          <button type="button" class="close-btn" @click="selectedDetail = null" aria-label="Close">×</button>
        </header>
        <dl class="kv">
          <dt>Strain</dt><dd>{{ selectedDetail.strain_name }}</dd>
          <dt>Header</dt><dd class="mono small">{{ selectedDetail.protein_location_header }}</dd>
          <template v-if="selectedDetail.metadata && selectedDetail.metadata[0]">
            <dt>Prediction</dt><dd>{{ selectedDetail.metadata[0].prediction_type || '—' }}</dd>
            <dt>Origin</dt><dd>{{ selectedDetail.metadata[0].evolutionary_origin || '—' }}</dd>
            <dt>Assembly</dt><dd class="truncate-wide">{{ selectedDetail.metadata[0].assembly || '—' }}</dd>
            <dt>Sequence location</dt><dd class="truncate-wide">{{ selectedDetail.metadata[0].sequence_location || '—' }}</dd>
            <dt>Assembly location</dt><dd class="truncate-wide">{{ selectedDetail.metadata[0].assembly_location || '—' }}</dd>
            <dt>Data location</dt><dd class="truncate-wide">{{ selectedDetail.metadata[0].data_location || '—' }}</dd>
            <dt>Alternate name</dt><dd>{{ selectedDetail.metadata[0].alternate_name || '—' }}</dd>
            <dt>Fragment</dt><dd>{{ selectedDetail.metadata[0].fragment || '—' }}</dd>
          </template>
        </dl>
        <div v-if="selectedDetail.metadata && selectedDetail.metadata[0] && selectedDetail.metadata[0].fullseq" class="fullseq">
          <div class="fullseq-label">Sequence</div>
          <pre class="mono">{{ selectedDetail.metadata[0].fullseq }}</pre>
        </div>
      </aside>

      <aside v-if="activeMode === 'alignments' && selectedAlignment" class="detail">
        <header class="detail-header">
          <h3>{{ selectedAlignment.name }}</h3>
          <button type="button" class="close-btn" @click="selectedAlignment = null" aria-label="Close">×</button>
        </header>
        <!-- Intentionally empty: MSA viewer wiring is phase 2 (see README). -->
        <div class="muted empty">Alignment detail view is under construction.</div>
      </aside>
    </main>
  </div>
</template>

<script>
import TaxTree from './TaxTree.vue';
import initialState from './MainPageVars.js';

const MODES = [
  { id: 'sequences',  label: 'Sequences'  },
  { id: 'organisms',  label: 'Organisms'  },
  { id: 'alignments', label: 'Alignments' },
];

const ORIGIN_VALUES = [
  { label: 'Both',         value: ''             },
  { label: 'Mitochondria', value: 'mitochondria' },
  { label: 'Plastid',      value: 'plastid'      },
];

const EMPTY_FILTER_OPTIONS = {
  prediction_type: [],
  evolutionary_origin: [],
  assembly: [],
  sequence_location: [],
  assembly_location: [],
  data_location: [],
  protein_names: [],
};

export default {
  name: 'MainPage',
  components: { TaxTree },
  data() {
    return {
      ...initialState(),
      modes: MODES,
      originValues: ORIGIN_VALUES,
      filterOptions: { ...EMPTY_FILTER_OPTIONS },
      alignmentProteinOptions: [],   // populated from /api/proteins-for-taxgroups/
      openTaxIds: [],
      selectedAlignment: null,
      taxSearch: '',
      simplifyTree: true,            // hide 'clade' rows by default
      _fetchTimer: null,
      alignmentProteinsReqId: 0,
    };
  },
  computed: {
    modeLabel() {
      return (MODES.find((m) => m.id === this.activeMode) || {}).label || '';
    },
    totalPages() {
      return Math.max(1, Math.ceil((this.resultsTotal || 0) / this.pageSize));
    },
    chips() {
      const out = [];
      for (const tid of this.crossFilters.taxgroup_ids) {
        out.push({
          key: `tax:${tid}`,
          kind: 'taxgroup',
          id: tid,
          text: `Taxon: ${this.crossFilters.taxgroup_labels[tid] || tid}`,
        });
      }
      if (this.crossFilters.protein_name) {
        out.push({
          key: 'pn',
          kind: 'protein_name',
          text: `Protein: ${this.crossFilters.protein_name}`,
        });
      }
      return out;
    },
    /** Filter the tree by `taxSearch` — keep any node that matches the query
     *  OR has a descendant that matches. Returns a shallow-cloned tree whose
     *  nodes share ids but have pruned children arrays. */
    filteredTaxTree() {
      if (!this.taxTree) return null;
      const q = this.taxSearch.trim().toLowerCase();
      if (!q) return this.taxTree.roots;
      const match = (node) => {
        const selfHit = (node.name || '').toLowerCase().includes(q)
                     || (node.level || '').toLowerCase().includes(q);
        const kids = (node.children || []).map(match).filter(Boolean);
        if (selfHit || kids.length) {
          return { ...node, children: kids };
        }
        return null;
      };
      const kept = this.taxTree.roots.map(match).filter(Boolean);
      return kept.length ? kept : null;
    },
    /** Drop 'clade' rows (and any other unranked intermediates we want to
     *  skip): children of a skipped node bubble up to the skipped node's
     *  parent. Works recursively. Only kicks in when simplifyTree is true. */
    displayedTaxTree() {
      const base = this.filteredTaxTree;
      if (!base) return null;
      if (!this.simplifyTree) return base;
      const SKIP = new Set(['clade']);
      const unwrap = (node) => {
        // Recurse first so children are simplified bottom-up.
        const kids = (node.children || []).flatMap(unwrap);
        if (SKIP.has(node.level)) return kids;  // drop self, promote kids
        return [{ ...node, children: kids }];
      };
      return base.flatMap(unwrap);
    },
    /** When a search is active, auto-open every ancestor of every match
     *  so the matches are visible without clicking chevrons. */
    effectiveOpenTaxIds() {
      if (!this.taxSearch.trim() || !this.displayedTaxTree) return this.openTaxIds;
      const ids = new Set(this.openTaxIds);
      const walk = (node) => {
        if (node.children && node.children.length) {
          ids.add(node.id);
          node.children.forEach(walk);
        }
      };
      this.displayedTaxTree.forEach(walk);
      return Array.from(ids);
    },
  },
  mounted() {
    this.loadFilterOptions();
    this.loadTaxTree();
    this.fetchResults();
  },
  watch: {
    // Any change to the taxgroup selection refreshes the Alignments-mode
    // protein dropdown. Deep-watch so in-place array mutations still trigger.
    crossFilters: {
      deep: true,
      handler() {
        this.refreshAlignmentProteinOptions();
      },
    },
  },
  methods: {
    setMode(modeId) {
      this.activeMode = modeId;
      this.page = 1;
      this.selectedDetail = null;
      this.selectedAlignment = null;
      // The watcher on taxgroup_ids keeps alignmentProteinOptions in sync;
      // also refresh on every mode switch in case the options list is stale.
      if (modeId === 'alignments') this.refreshAlignmentProteinOptions();
      this.fetchResults();
    },
    setSeqFilter(key, value) {
      this.sequenceFilters[key] = value;
      this.page = 1;
      this.fetchResults();
    },
    onSeqFilterChange() {
      this.page = 1;
      this.fetchResults();
    },
    setOrgFilter(key, value) {
      this.organismFilters[key] = value;
      this.page = 1;
      this.fetchResults();
    },
    onOrgFilterChange() {
      this.page = 1;
      this.fetchResults();
    },
    onAlnFilterChange() {
      this.page = 1;
      this.fetchResults();
    },
    debouncedFetch() {
      clearTimeout(this._fetchTimer);
      this._fetchTimer = setTimeout(() => {
        this.page = 1;
        this.fetchResults();
      }, 250);
    },
    async loadFilterOptions() {
      try {
        const res = await fetch('/api/filter-options/');
        if (!res.ok) throw new Error(`filter-options HTTP ${res.status}`);
        const data = await res.json();
        this.filterOptions = { ...EMPTY_FILTER_OPTIONS, ...data };
      } catch (e) {
        console.error(e);
      }
    },
    goPage(p) {
      this.page = p;
      this.fetchResults();
    },
    async loadTaxTree() {
      this.taxTreeLoading = true;
      try {
        const res = await fetch('/api/taxtree/');
        if (!res.ok) throw new Error(`taxtree HTTP ${res.status}`);
        this.taxTree = await res.json();
        // Open the root node by default.
        if (this.taxTree.roots && this.taxTree.roots[0]) {
          this.openTaxIds = [this.taxTree.roots[0].id];
        }
      } catch (e) {
        console.error(e);
      } finally {
        this.taxTreeLoading = false;
      }
    },
    buildQuery() {
      const p = new URLSearchParams();
      p.set('page', String(this.page));
      p.set('page_size', String(this.pageSize));
      for (const tid of this.crossFilters.taxgroup_ids) p.append('taxgroup_ids[]', String(tid));
      if (this.activeMode === 'sequences') {
        const f = this.sequenceFilters;
        for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
        if (this.crossFilters.protein_name && !f.protein_name) p.set('protein_name', this.crossFilters.protein_name);
      } else if (this.activeMode === 'organisms') {
        const f = this.organismFilters;
        for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
        if (this.crossFilters.protein_name && !f.protein_name) p.set('protein_name', this.crossFilters.protein_name);
      } else if (this.activeMode === 'alignments') {
        if (this.alignmentFilters.protein_name) p.set('protein_name', this.alignmentFilters.protein_name);
      }
      return p.toString();
    },
    async fetchResults() {
      this.loading = true;
      this.error = null;
      try {
        const endpoint = {
          sequences: '/api/sequences/',
          organisms: '/api/organisms/',
          alignments: '/api/alignments/',
        }[this.activeMode];
        const res = await fetch(`${endpoint}?${this.buildQuery()}`);
        if (!res.ok) throw new Error(`${this.activeMode} HTTP ${res.status}`);
        const data = await res.json();
        this.results = data.results || [];
        this.resultsTotal = data.total ?? 0;
        this.page = data.page || 1;
        this.pageSize = data.page_size || this.pageSize;
      } catch (e) {
        console.error(e);
        this.error = `Failed to load ${this.activeMode}.`;
        this.results = [];
        this.resultsTotal = 0;
      } finally {
        this.loading = false;
      }
    },
    async openDetail(pdataId) {
      this.detailLoading = true;
      try {
        const res = await fetch(`/api/sequences/${pdataId}/`);
        if (!res.ok) throw new Error(`detail HTTP ${res.status}`);
        this.selectedDetail = await res.json();
      } catch (e) {
        console.error(e);
      } finally {
        this.detailLoading = false;
      }
    },
    onTaxToggle(id) {
      const i = this.openTaxIds.indexOf(id);
      if (i === -1) this.openTaxIds.push(id);
      else this.openTaxIds.splice(i, 1);
    },
    onTaxCheck(node) {
      const ids = this.crossFilters.taxgroup_ids.slice();
      const labels = { ...this.crossFilters.taxgroup_labels };
      const i = ids.indexOf(node.id);
      if (i === -1) {
        ids.push(node.id);
        labels[node.id] = node.name;
      } else {
        ids.splice(i, 1);
        delete labels[node.id];
      }
      this.crossFilters.taxgroup_ids = ids;
      this.crossFilters.taxgroup_labels = labels;
      this.page = 1;
      // Direct call as a belt-and-suspenders for the deep watcher on
      // crossFilters. If either fires the other is a cheap no-op thanks to
      // reqId gating.
      this.refreshAlignmentProteinOptions();
      this.fetchResults();
    },
    /** Refetch the protein dropdown for Alignments mode based on the
     *  currently-selected taxgroup(s). When nothing is selected, clear it. */
    async refreshAlignmentProteinOptions() {
      const selected = this.crossFilters.taxgroup_ids.slice();
      console.log('[alignments] refresh triggered. taxgroup_ids =', selected,
                  '(labels =', this.crossFilters.taxgroup_labels, ')');
      if (!selected.length) {
        this.alignmentProteinOptions = [];
        this.alignmentFilters.protein_name = '';
        console.log('[alignments] no organisms selected → cleared protein options');
        return;
      }
      const reqId = ++this.alignmentProteinsReqId;
      const p = new URLSearchParams();
      for (const tid of selected) p.append('taxgroup_ids[]', String(tid));

      // In parallel, also fetch the filtered polymer rows themselves so the
      // developer can inspect them in the console. Cheap (5602 max) and
      // capped at 500/page.
      const polymersPromise = fetch(`/api/sequences/?${p.toString()}&page_size=500`)
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => {
          if (!j) return;
          console.log(`[alignments] filtered polymers (${j.total} total, showing ${j.results.length}):`);
          console.table(j.results.map((r) => ({
            id: r.id,
            protein: r.protein_name,
            strain_id: r.strain_id,
            strain: r.strain_name,
            origin: r.evolutionary_origin,
          })));
        })
        .catch((e) => console.error('[alignments] polymer fetch failed:', e));

      try {
        const res = await fetch(`/api/proteins-for-taxgroups/?${p.toString()}`);
        if (!res.ok) throw new Error(`proteins-for-taxgroups HTTP ${res.status}`);
        const data = await res.json();
        if (reqId !== this.alignmentProteinsReqId) {
          console.log('[alignments] stale response, discarding');
          return;
        }
        // Use $set to guarantee reactivity even if something about the
        // property descriptor is funky.
        this.$set(this, 'alignmentProteinOptions', data.results || []);
        console.log(`[alignments] protein dropdown populated: ${this.alignmentProteinOptions.length} options →`,
                    this.alignmentProteinOptions);
        if (this.alignmentFilters.protein_name
            && !this.alignmentProteinOptions.includes(this.alignmentFilters.protein_name)) {
          this.alignmentFilters.protein_name = '';
        }
      } catch (e) {
        console.error('[alignments] protein fetch failed:', e);
      }
      await polymersPromise;
    },
    pinOrganismToSequences(row) {
      this.crossFilters.taxgroup_ids = [row.strain_id];
      this.crossFilters.taxgroup_labels = { [row.strain_id]: row.name };
      // Carry every active Organisms-mode filter across to Sequences so the
      // user stays in the same filtered context they just saw.
      for (const [k, v] of Object.entries(this.organismFilters)) {
        if (k in this.sequenceFilters) this.sequenceFilters[k] = v;
      }
      // Open the tree all the way down to the pinned strain so the chip is
      // reflected in the taxonomy panel.
      this.expandTreePathTo(row.strain_id);
      this.activeMode = 'sequences';
      this.selectedDetail = null;
      this.page = 1;
      this.fetchResults();
    },
    /** Ensure every ancestor of `targetId` is in openTaxIds so the target
     *  row is visible in the tree. */
    expandTreePathTo(targetId) {
      if (!this.taxTree || !this.taxTree.roots) return;
      const parentOf = {};
      const walk = (node) => {
        for (const c of node.children || []) {
          parentOf[c.id] = node.id;
          walk(c);
        }
      };
      for (const root of this.taxTree.roots) walk(root);
      const toOpen = new Set(this.openTaxIds);
      let cur = parentOf[targetId];
      while (cur !== undefined) {
        toOpen.add(cur);
        cur = parentOf[cur];
      }
      // Also open the target itself so its children (if any) are visible.
      toOpen.add(targetId);
      this.openTaxIds = Array.from(toOpen);
    },
    removeChip(chip) {
      if (chip.kind === 'taxgroup') {
        const ids = this.crossFilters.taxgroup_ids.filter((x) => x !== chip.id);
        const labels = { ...this.crossFilters.taxgroup_labels };
        delete labels[chip.id];
        this.crossFilters.taxgroup_ids = ids;
        this.crossFilters.taxgroup_labels = labels;
      } else if (chip.kind === 'protein_name') {
        this.crossFilters.protein_name = '';
      }
      this.page = 1;
      this.fetchResults();
    },
  },
};
</script>

<style scoped>
/* Pastel-purple scientific design tokens. */
.app-shell {
  --purple:        #b8a7e8;
  --purple-deep:   #9d8bd4;
  --purple-ink:    #1f1b2e;
  --purple-soft:   #f5f1fc;
  --ink:           #1f1b2e;
  --ink-muted:     #6b647f;
  --line:          #efedf7;
  --bg:            #fbfafe;
  --bg-hover:      #f5f1fc;
  --shadow:        0 1px 2px rgba(30, 27, 46, 0.04);

  display: flex;
  min-height: 100vh;
  background: var(--bg);
  color: var(--ink);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Inter", sans-serif;
  font-size: 14px;
  line-height: 1.5;
}

/* Sidebar */
.sidebar {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid var(--line);
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  max-height: 100vh;
  position: sticky;
  top: 0;
}

.brand-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0;
  color: var(--ink);
}

/* Mode switcher (segmented control, faded inactive) */
.mode-switcher {
  display: flex;
  gap: 2px;
  background: var(--purple-soft);
  border-radius: 8px;
  padding: 3px;
}
.mode-btn {
  flex: 1;
  padding: 7px 10px;
  border: none;
  background: transparent;
  color: var(--ink-muted);
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, opacity 0.15s;
  opacity: 0.45;
}
.mode-btn:hover { opacity: 0.8; }
.mode-btn.active {
  background: var(--purple);
  color: #fff;
  opacity: 1;
  box-shadow: var(--shadow);
}

/* Filters */
.filters { display: flex; flex-direction: column; gap: 16px; }
.filter-group { display: flex; flex-direction: column; gap: 6px; }
.filter-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink-muted);
}
.filter-group input[type='text'],
.filter-group select {
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}
.filter-group input:focus,
.filter-group select:focus {
  border-color: var(--purple-deep);
}

/* Segmented control for evolutionary_origin */
.segmented {
  display: flex;
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
}
.seg {
  flex: 1;
  padding: 6px 8px;
  background: #fff;
  border: none;
  border-right: 1px solid var(--line);
  color: var(--ink-muted);
  font-size: 12px;
  cursor: pointer;
}
.seg:last-child { border-right: none; }
.seg.active { background: var(--purple-soft); color: var(--purple-deep); font-weight: 600; }

/* Chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--purple-soft);
  color: var(--purple-deep);
  padding: 3px 4px 3px 8px;
  border-radius: 12px;
  font-size: 12px;
}
.chip-x {
  background: none;
  border: none;
  color: var(--purple-deep);
  cursor: pointer;
  padding: 0 4px;
  font-size: 14px;
  line-height: 1;
}

/* Main content */
.content {
  flex: 1;
  padding: 24px 32px;
  min-width: 0;
}
.content-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding-bottom: 12px;
  margin-bottom: 20px;
}
.content-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}
.result-meta {
  font-size: 12px;
  color: var(--ink-muted);
}

.error {
  background: #fdf4f4;
  color: #8a3a3a;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #f0dcdc;
  margin-bottom: 12px;
}

/* Results table */
.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.results-table thead th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink-muted);
}
.results-table tbody td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
}
.results-table tbody tr {
  cursor: pointer;
  transition: background 0.1s;
}
.results-table tbody tr:hover { background: var(--bg-hover); }
.results-table tbody tr.selected { background: var(--purple-soft); }

.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
.small { font-size: 12px; color: var(--ink-muted); }
.truncate { max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.truncate-wide { max-width: 440px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.muted { color: var(--ink-muted); font-size: 12px; }
.empty { padding: 24px 0; font-style: italic; }

.link-btn {
  background: none;
  border: none;
  color: var(--purple-deep);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.link-btn:hover { color: var(--purple-ink); }

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  font-size: 12px;
  color: var(--ink-muted);
}
.pagination button {
  padding: 5px 10px;
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  color: var(--ink);
  font-size: 12px;
}
.pagination button:disabled { opacity: 0.4; cursor: default; }
.pagination button:hover:not(:disabled) { border-color: var(--purple-deep); color: var(--purple-deep); }

/* Detail pane */
.detail {
  margin-top: 24px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.detail-header h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}
.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  color: var(--ink-muted);
  cursor: pointer;
}
.close-btn:hover { color: var(--ink); }

.kv {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 6px 16px;
  margin: 0;
  font-size: 13px;
}
.kv dt {
  color: var(--ink-muted);
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  align-self: start;
  padding-top: 2px;
}
.kv dd { margin: 0; }

.fullseq { margin-top: 16px; }
.fullseq-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink-muted);
  margin-bottom: 4px;
}
.fullseq pre {
  background: var(--purple-soft);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Tax tree helpers */
.filter-tree { max-height: 420px; overflow-y: auto; }
.tree-search {
  padding: 6px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink);
  font-size: 12px;
  outline: none;
  margin-bottom: 6px;
}
.tree-search:focus { border-color: var(--purple-deep); }
.tree-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ink-muted);
  margin-bottom: 8px;
  cursor: pointer;
  user-select: none;
}
.tree-toggle input[type='checkbox'] {
  accent-color: var(--purple-deep);
  margin: 0;
}

/* Organism aggregate tags */
.tags-cell { display: flex; flex-wrap: wrap; gap: 4px; max-width: 280px; }
.tag {
  display: inline-block;
  background: var(--purple-soft);
  color: var(--purple-deep);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  white-space: nowrap;
}
.tag-muted {
  background: #f4f3f8;
  color: var(--ink-muted);
}

/* Pill button (replaces link-btn in the organisms action column) */
.action-col { width: 150px; text-align: right; }
.pill-btn {
  background: #fff;
  border: 1px solid var(--line);
  color: var(--purple-deep);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.pill-btn:hover { border-color: var(--purple-deep); background: var(--purple-soft); }

/* Alignments mode: step numbers + disabled filter group */
.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--purple);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  margin-right: 6px;
  vertical-align: middle;
}
.filter-group.disabled { opacity: 0.5; }
.filter-group.disabled .step-num { background: var(--ink-muted); }
.filter-group select:disabled {
  background: #f6f4fa;
  cursor: not-allowed;
}

.guide-step {
  margin: 8px 0;
  font-style: normal;
  color: var(--ink-muted);
  font-size: 13px;
}
</style>
