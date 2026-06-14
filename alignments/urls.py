from django.urls import path
from . import views
from . import ncRNA_views
from . import mito_views

app_name = 'alignments'

urlpatterns = [
    path('', views.index, name='index'),

    # Mito DB frontend APIs (see alignments/mito_views.py).
    path('api/filter-options/', mito_views.filter_options_api, name='filter_options_api'),
    path('api/taxtree/', mito_views.taxtree_api, name='taxtree_api'),
    path('api/sequences/', mito_views.sequences_api, name='sequences_api'),
    path('api/sequences/fasta/', mito_views.download_fasta_api, name='download_fasta_api'),
    path('api/sequences/<int:pdata_id>/', mito_views.sequence_detail_api, name='sequence_detail_api'),
    path('api/organisms/', mito_views.organisms_api, name='organisms_api'),
    path('api/proteins-for-taxgroups/', mito_views.proteins_for_taxgroups_api, name='proteins_for_taxgroups_api'),
    path('api/structures/filter-options/', mito_views.structure_filter_options_api, name='structure_filter_options_api'),
    path('api/structures/chains/', mito_views.chains_api, name='chains_api'),
    path('api/alignments/', mito_views.alignments_api, name='alignments_api'),
    path('api/alignments/fasta/', mito_views.download_alignments_zip_api, name='download_alignments_zip_api'),
    path('api/alignments/<int:aln_id>/<str:tax_group>/zip/', mito_views.alignment_zip_api, name='alignment_zip_api'),
    path('api/alignments/<int:aln_id>/<str:tax_group>/fasta/', mito_views.alignment_fasta_api, name='alignment_fasta_api'),

    path('orthologs/twincons/<str:anchor_structure>/<str:chain>/<str:align_name>/<int:tax_group1>/<int:tax_group2>/<int:minIndex>/<int:maxIndex>', views.twincons_handler, name='twincons'),
    path('orthologs/twincons/<str:anchor_structure>/<str:chain>/<str:align_name>/<int:tax_group1>/<int:tax_group2>', views.twincons_handler, name='twincons'),
    path('twincons/<str:anchor_structure>/<str:chain>/<str:align_name>/<int:tax_group1>/<int:tax_group2>', views.twincons_handler, name='twincons'),
    path('twc-api/<str:align_name>/<int:tax_group1>/<int:tax_group2>/<str:anchor_structure>', views.api_twc, name='api_twc'),
    path('twc-api/<str:align_name>/<int:tax_group1>/<int:tax_group2>', views.api_twc, name='api_twc_no_struc'),
    path('twc-api/', views.api_twc_parameterless, name='api_twc'),
    path('orthologs/twc-api/<str:align_name>/<int:tax_group1>/<int:tax_group2>/<str:anchor_structure>', views.api_twc, name='api_twc'),
    path('orthologs/upload/twincons/<str:anchor_structure>/<str:chain>/<int:minIndex>/<int:maxIndex>', views.twincons_handler, name='twc_with_upload'),
    path('orthologs/upload/twincons/<str:anchor_structure>/<str:chain>', views.twincons_handler, name='twc_with_upload'),
    path('upload/twc-api/<str:anchor_structure>', views.api_twc_with_upload, name='api_twc_with_upload'),

    path('allGencodeTranscripts', ncRNA_views.allGencodeTranscripts, name='allGencodeTranscripts'),
    path('fetchTranscriptPeak', ncRNA_views.fetchTranscriptPeak, name='fetchTranscriptPeak'),
    path('plot_cum_RBP_profile', ncRNA_views.plot_cum_RBP_profile, name='plot_cum_RBP_profile'),
    path('displayRBPProfile', ncRNA_views.displayRBPProfile, name='displayRBPProfile'),
    path('get_rbps', ncRNA_views.get_rbps, name='get_rbps'),
    path('fetch_all_bed_files', ncRNA_views.fetch_all_bed_files, name='fetch_all_bed_files'),
    path('fetchTranscriptsFromRBP', ncRNA_views.fetchTranscriptsFromRBP, name="fetchTranscriptsFromRBP"),
    path('get_cell_lines', ncRNA_views.get_cell_lines, name='get_cell_lines'),
    path('get_track_rbps', ncRNA_views.get_track_rbps, name='get_track_rbps'),
    path('get_schema_types', ncRNA_views.get_schema_types, name='get_schema_types'),
    path('get_gene_names', ncRNA_views.get_gene_names, name='get_gene_names'),
    path('get_schema_transcripts', ncRNA_views.get_schema_transcripts, name='get_schema_transcripts'),
    path('get_transcript_track_data', ncRNA_views.get_transcript_track_data, name='get_transcript_track_data'),
    path('search_transcripts_by_internal_id', ncRNA_views.search_transcripts_by_internal_id, name='search_transcripts_by_internal_id'),
]
