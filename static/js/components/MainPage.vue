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
            </label>
            <select
              id="a-name"
              v-model="alignmentFilters.protein_name"
              :disabled="!crossFilters.taxgroup_ids.length"
              @change="onAlnFilterChange()"
            >
              <option value="">
                <template v-if="!crossFilters.taxgroup_ids.length">Select an organism first</template>
                <template v-else>All available</template>
              </option>
              <option v-for="v in filterOptions.protein_names" :key="v" :value="v">{{ v }}</option>
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
              <th>Protein</th>
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
              <th></th>
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
                <span v-for="a in r.assembly_locations || []" :key="a" class="tag tag-muted">{{ a }}</span>
                <span v-if="!(r.assembly_locations || []).length" class="muted">—</span>
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
          <h3>{{ selectedDetail.protein_location_header || '(no header)' }}</h3>
          <button type="button" class="close-btn" @click="selectedDetail = null" aria-label="Close">×</button>
        </header>
        <dl class="kv">
          <dt>Strain</dt><dd>{{ selectedDetail.strain_name }}</dd>
          <dt>Protein</dt><dd>{{ selectedDetail.protein_name || '—' }}</dd>
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

      <div
        v-show="activeMode === 'alignments' && selectedAlignment"
        class="msa-overlay"
      >
        <header class="msa-overlay-header">
          <h3>{{ selectedAlignment && selectedAlignment.name }}</h3>
          <button type="button" class="close-btn msa-close-btn" @click.stop="closeMsa" aria-label="Close">×</button>
        </header>
        <div ref="msaMount" class="msa-mount" @mousedown="msaDragStart"></div>
      </div>
    </main>
  </div>
</template>

<script>
import React from 'react';
import ReactDOM from 'react-dom';
import TaxTree from './TaxTree.vue';
import MsaViewer from './MsaViewer.js';
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
      openTaxIds: [],
      selectedAlignment: null,
      taxSearch: '',
      simplifyTree: true,            // hide 'clade' rows by default
      _fetchTimer: null,
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
    window.addEventListener('keydown', this.onMsaKeydown);
  },
  watch: {
    selectedAlignment(v) {
      document.body.style.overflow = v ? 'hidden' : '';
      this.$nextTick(() => this.renderMsa(v));
    },
  },
  beforeDestroy() {
    document.body.style.overflow = '';
    this.unmountMsa();
    window.removeEventListener('keydown', this.onMsaKeydown);
  },
  methods: {
    setMode(modeId) {
      this.activeMode = modeId;
      this.page = 1;
      this.selectedDetail = null;
      this.selectedAlignment = null;
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
        const res = await fetch('/mtProts/api/filter-options/');
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
        const res = await fetch('/mtProts/api/taxtree/');
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
          sequences: '/mtProts/api/sequences/',
          organisms: '/mtProts/api/organisms/',
          alignments: '/mtProts/api/alignments/',
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
        const res = await fetch(`/mtProts/api/sequences/${pdataId}/`);
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
      this.fetchResults();
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
    renderMsa(aln) {
      const el = this.$refs.msaMount;
      if (!el) return;
      if (!aln) {
        ReactDOM.unmountComponentAtNode(el);
        return;
      }
      const ids = this.crossFilters.taxgroup_ids;
      const taxGroupId = ids && ids.length ? ids.join(',') : '0';
      ReactDOM.render(
        React.createElement(MsaViewer, {
          alnId: aln.aln_id,
          taxGroupId,
          name: aln.name,
          onClose: this.closeMsa,
        }),
        el,
      );
    },
    unmountMsa() {
      const el = this.$refs.msaMount;
      if (el) ReactDOM.unmountComponentAtNode(el);
    },
    closeMsa() {
      this.selectedAlignment = null;
      document.body.style.overflow = '';
      this.unmountMsa();
    },
    onMsaKeydown(e) {
      if (e.key === 'Escape' && this.selectedAlignment) {
        this.closeMsa();
      }
    },
    msaDragStart(e) {
      if (e.button !== 0) return;
      const el = this.$refs.msaMount;
      if (!el) return;
      this._msaDrag = {
        startX: e.clientX,
        startY: e.clientY,
        scrollLeft: el.scrollLeft,
        scrollTop: el.scrollTop,
      };
      el.style.cursor = 'grabbing';
      window.addEventListener('mousemove', this.msaDragMove);
      window.addEventListener('mouseup', this.msaDragEnd);
      e.preventDefault();
    },
    msaDragMove(e) {
      const el = this.$refs.msaMount;
      if (!el || !this._msaDrag) return;
      el.scrollLeft = this._msaDrag.scrollLeft - (e.clientX - this._msaDrag.startX);
      el.scrollTop = this._msaDrag.scrollTop - (e.clientY - this._msaDrag.startY);
    },
    msaDragEnd() {
      const el = this.$refs.msaMount;
      if (el) el.style.cursor = '';
      this._msaDrag = null;
      window.removeEventListener('mousemove', this.msaDragMove);
      window.removeEventListener('mouseup', this.msaDragEnd);
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
/* ───────────────────────────────────────────────────────────
   MITO-RIBOSOMAL PROTEIN DATABASE — refined scientific
   publication register. Near-white paper canvas, ink body,
   hairline rules, serif display. Pastel-purple is an accent,
   never the dominant color.
   ─────────────────────────────────────────────────────────── */
.app-shell {
  --bg:          #fbfafe;
  --surface:     #ffffff;
  --ink:         #1f1b2e;
  --ink-subtle:  #6b647f;
  --ink-whisper: #a5a1b4;
  --line:        #efedf7;
  --line-strong: #e2dcef;
  --purple:      #b8a7e8;
  --purple-deep: #9d8bd4;
  --purple-ink:  #6b4fb7;
  --purple-tint: #f5f1fc;

  --font-body:    'IBM Plex Sans', ui-sans-serif, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-display: 'Fraunces', 'IBM Plex Serif', Georgia, serif;
  --font-mono:    'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

  display: grid;
  grid-template-columns: 320px 1fr;
  min-height: 100vh;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 13.5px;
  line-height: 1.55;
  font-feature-settings: 'ss01', 'cv02', 'cv11';
}

/* ─── SIDEBAR ────────────────────────────────────────────── */
.sidebar {
  border-right: 1px solid var(--line);
  padding: 30px 22px 48px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  overflow-y: auto;
  max-height: 100vh;
  position: sticky;
  top: 0;
  background: var(--surface);
}

.brand {
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
}
.brand-title {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 15.5px;
  line-height: 1.2;
  letter-spacing: -0.015em;
  color: var(--ink);
  font-variation-settings: 'opsz' 14;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-title::before {
  content: '§ ';
  color: var(--purple-deep);
  font-size: 13.5px;
  opacity: 0.75;
}

/* ─── MODE SWITCHER ──────────────────────────────────────── */
.mode-switcher {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  padding: 3px;
  background: var(--purple-tint);
  border-radius: 7px;
}
.mode-btn {
  appearance: none;
  background: transparent;
  border: none;
  padding: 8px 6px;
  font-family: var(--font-body);
  font-size: 12.5px;
  font-weight: 500;
  letter-spacing: 0.005em;
  color: var(--ink-subtle);
  opacity: 0.5;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.mode-btn:hover:not(.active) {
  opacity: 0.8;
  color: var(--ink);
}
.mode-btn.active {
  background: var(--purple);
  color: #ffffff;
  opacity: 1;
}

/* ─── FILTERS ────────────────────────────────────────────── */
.filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.filter-label {
  font-family: var(--font-body);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-subtle);
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-group input[type='text'],
.filter-group input[type='search'],
.filter-group select {
  appearance: none;
  -webkit-appearance: none;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--ink);
  padding: 8px 11px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  background: var(--surface);
  outline: none;
  transition: border-color 0.12s, box-shadow 0.12s;
}
.filter-group select {
  padding-right: 30px;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 8 8'><path d='M1 3 L4 6 L7 3' fill='none' stroke='%239d8bd4' stroke-width='1.3' stroke-linecap='round' stroke-linejoin='round'/></svg>");
  background-repeat: no-repeat;
  background-position: right 11px center;
}
.filter-group input:focus,
.filter-group select:focus {
  border-color: var(--purple-deep);
  box-shadow: 0 0 0 3px var(--purple-tint);
}
.filter-group.disabled { opacity: 0.5; }
.filter-group select:disabled {
  background-color: var(--bg);
  cursor: not-allowed;
}

/* Segmented toggle (evolutionary origin) */
.segmented {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  overflow: hidden;
  background: var(--surface);
}
.seg {
  background: transparent;
  border: none;
  padding: 7px 8px;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--ink-subtle);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  border-right: 1px solid var(--line-strong);
}
.seg:last-child { border-right: none; }
.seg:hover:not(.active) { background: var(--purple-tint); color: var(--ink); }
.seg.active {
  background: var(--purple-tint);
  color: var(--purple-ink);
  font-weight: 600;
}

/* Step number bubble (Alignments sidebar) */
.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 17px;
  height: 17px;
  font-family: var(--font-display);
  font-size: 10.5px;
  font-style: italic;
  font-weight: 500;
  background: var(--purple);
  color: #ffffff;
  border-radius: 50%;
  font-variation-settings: 'opsz' 14;
}
.filter-group.disabled .step-num { background: var(--ink-whisper); }

/* Tax tree wrapper in the sidebar — scroll in both axes so long taxon
   names and deep indentation don't get clipped. */
.filter-tree {
  max-height: 460px;
  overflow-x: auto;
  overflow-y: auto;
  padding: 0 6px 6px 0;
}
.tree-search {
  padding: 7px 11px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  font-size: 12.5px;
  margin-bottom: 2px;
}
.tree-toggle {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  color: var(--ink-subtle);
  cursor: pointer;
  user-select: none;
  padding: 4px 2px 6px;
}
.tree-toggle input[type='checkbox'] {
  accent-color: var(--purple-deep);
  margin: 0;
  width: 13px;
  height: 13px;
}

/* ─── CHIPS ───────────────────────────────────────────── */
.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 4px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  background: var(--purple-tint);
  color: var(--purple-ink);
  padding: 2px 3px 2px 10px;
  border-radius: 100px;
  font-size: 11.5px;
  font-family: var(--font-body);
  border: 1px solid var(--line-strong);
  max-width: 100%;
}
.chip-label {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chip-x {
  appearance: none;
  background: transparent;
  border: none;
  color: var(--purple-deep);
  padding: 0;
  width: 18px;
  height: 18px;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 2px;
  transition: background 0.12s, color 0.12s;
}
.chip-x:hover {
  background: var(--purple);
  color: #ffffff;
}

/* ─── MAIN CONTENT ───────────────────────────────────── */
.content {
  padding: 36px 44px 72px;
  min-width: 0;
  max-width: 1320px;
}
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-bottom: 14px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--line);
}
.content-title {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 24px;
  letter-spacing: -0.012em;
  color: var(--ink);
  font-variation-settings: 'opsz' 18;
}
.result-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-subtle);
  letter-spacing: 0.02em;
}

.error {
  background: #fdf3f3;
  color: #8a3a3a;
  border: 1px solid #f1dada;
  padding: 10px 14px;
  border-radius: 5px;
  font-size: 13px;
  margin-bottom: 14px;
}

/* ─── TABLES ─────────────────────────────────────────── */
.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: var(--font-body);
}
.results-table thead th {
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line-strong);
  font-family: var(--font-body);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--ink-subtle);
  user-select: none;
  white-space: nowrap;
}
.results-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.results-table tbody tr {
  cursor: pointer;
  transition: background 0.1s;
}
.results-table tbody tr:hover { background: var(--purple-tint); }
.results-table tbody tr.selected {
  background: var(--purple-tint);
  box-shadow: inset 2px 0 0 var(--purple-deep);
}

.mono {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: -0.005em;
}
.small { font-size: 11.5px; color: var(--ink-subtle); }
.truncate { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.truncate-wide { max-width: 460px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.muted { color: var(--ink-subtle); font-size: 12px; }
.empty {
  padding: 36px 4px;
  font-family: var(--font-display);
  font-style: italic;
  font-size: 15px;
  font-weight: 400;
  color: var(--ink-subtle);
  letter-spacing: -0.005em;
  font-variation-settings: 'opsz' 16;
}

.action-col { width: 160px; text-align: right; }
.link-btn {
  appearance: none;
  background: none;
  border: none;
  color: var(--purple-deep);
  font-family: var(--font-body);
  font-size: 12.5px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}
.link-btn:hover { color: var(--purple-ink); }

.pill-btn {
  appearance: none;
  background: var(--surface);
  border: 1px solid var(--line-strong);
  color: var(--purple-deep);
  padding: 5px 13px;
  border-radius: 100px;
  font-family: var(--font-body);
  font-size: 11.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.12s;
  letter-spacing: 0.005em;
}
.pill-btn:hover {
  border-color: var(--purple-deep);
  color: var(--purple-ink);
  background: var(--purple-tint);
}

/* Tag cells (origins / prediction types on organisms table) */
.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 280px;
}
.tag {
  display: inline-block;
  padding: 3px 9px;
  border-radius: 100px;
  font-size: 10.5px;
  font-family: var(--font-body);
  background: var(--purple-tint);
  color: var(--purple-ink);
  letter-spacing: 0.015em;
  white-space: nowrap;
  border: 1px solid var(--line-strong);
  font-weight: 500;
}
.tag-muted {
  background: var(--bg);
  color: var(--ink-subtle);
  border-color: var(--line);
  font-weight: 450;
}

/* ─── PAGINATION ─────────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 24px 0;
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--ink-subtle);
  letter-spacing: 0.02em;
}
.pagination button {
  appearance: none;
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 12px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.12s;
}
.pagination button:hover:not(:disabled) {
  border-color: var(--purple-deep);
  color: var(--purple-ink);
}
.pagination button:disabled { opacity: 0.35; cursor: default; }

/* ─── DETAIL PANE (archival "record" card) ──────────── */
.detail {
  margin-top: 30px;
  padding: 26px 30px;
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  position: relative;
}
.detail::before {
  content: 'Record';
  position: absolute;
  top: -9px;
  left: 22px;
  font-family: var(--font-display);
  font-style: italic;
  font-size: 10.5px;
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--ink-subtle);
  padding: 0 10px;
  background: var(--bg);
  font-variation-settings: 'opsz' 14;
}
.detail-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}
.detail-header h3 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 20px;
  letter-spacing: -0.012em;
  font-variation-settings: 'opsz' 16;
}
.close-btn {
  appearance: none;
  background: none;
  border: none;
  color: var(--ink-subtle);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 7px;
  border-radius: 4px;
  transition: color 0.12s, background 0.12s;
}
.close-btn:hover { color: var(--ink); background: var(--purple-tint); }

.kv {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 11px 28px;
  margin: 0;
  font-size: 13px;
}
.kv dt {
  font-family: var(--font-body);
  color: var(--ink-subtle);
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding-top: 3px;
  font-weight: 600;
  align-self: start;
}
.kv dd {
  margin: 0;
  color: var(--ink);
}

.fullseq {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}
.fullseq-label {
  font-family: var(--font-body);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-subtle);
  margin-bottom: 7px;
}
.fullseq pre {
  margin: 0;
  padding: 14px 16px;
  background: var(--purple-tint);
  border: 1px solid var(--line);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.65;
  color: var(--ink);
  white-space: pre-wrap;
  word-break: break-all;
  overflow-x: auto;
  letter-spacing: 0.015em;
}

/* ─── MSA OVERLAY ────────────────────────────────────── */
.msa-overlay {
  position: fixed;
  inset: 0;
  background: var(--surface, #ffffff);
  z-index: 50;
  display: flex;
  flex-direction: column;
}
.msa-overlay-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 18px 28px;
  border-bottom: 1px solid var(--line-strong);
  background: var(--bg);
  flex-shrink: 0;
}
.msa-close-btn {
  position: relative;
  z-index: 3;
  font-size: 24px;
  padding: 4px 12px;
}
.msa-overlay-header h3 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 20px;
  letter-spacing: -0.012em;
  color: var(--ink);
}
.msa-mount {
  flex: 1;
  overflow: auto;
  padding: 0;
  width: 100%;
  cursor: grab;
  user-select: none;
}

/* ─── ALIGNMENTS GUIDE STEPS ─────────────────────────── */
.guide-step {
  margin: 6px 0;
  font-family: var(--font-body);
  font-size: 13.5px;
  color: var(--ink-subtle);
  line-height: 1.65;
}
.guide-step:first-child { margin-top: 12px; }
</style>
