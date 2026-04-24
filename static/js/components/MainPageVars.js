// Initial state factory for MainPage.vue.
// Keeping state shape in one place mirrors the old DropDownTree / DropDownTreeVars pattern.

export default function initialState() {
  return {
    // Which of the three top-level modes is active.
    activeMode: 'sequences',   // 'sequences' | 'organisms' | 'alignments'

    // Filter state, grouped by mode so switching modes doesn't wipe other filters.
    sequenceFilters: {
      prediction_type: '',
      evolutionary_origin: '',      // '' = both, 'mitochondria', 'plastid'
      protein_name: '',
      sequence_location: '',
      assembly_location: '',
      data_location: '',
    },
    organismFilters: {
      prediction_type: '',
      evolutionary_origin: '',
      protein_name: '',
      sequence_location: '',
      assembly_location: '',
      data_location: '',
    },
    alignmentFilters: {
      protein_name: '',
    },

    // Cross-mode filter chips. Shared across modes.
    // Keys match what the API expects; values are display-ready strings.
    crossFilters: {
      taxgroup_ids: [],             // e.g. [2762] — strain-level or any level; backend expands
      taxgroup_labels: {},          // { 2762: 'Cyanophora paradoxa' } for chip rendering
      protein_name: '',             // pinned from Sequences when filtering organisms
    },

    // Taxonomy tree loaded once on mount.
    taxTree: null,
    taxTreeLoading: false,

    // Results
    results: [],
    resultsTotal: 0,
    page: 1,
    pageSize: 50,
    loading: false,
    error: null,

    // Selected row detail
    selectedDetail: null,
    detailLoading: false,
  };
}
