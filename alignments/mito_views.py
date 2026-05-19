"""API endpoints for the mito (DESIRE_mito_as1) database.

All querysets must pass `.using('mito')` — there is no DB router.
Join map:
    Polymer_data.strain_id -> Species.strain_id (= TaxGroups.taxgroup_id)
    Polymer_data.nomgd_id  -> Nomenclature.nom_id
    Polymer_metadata.PData_id -> Polymer_data.id
    Polymer_Alignments.PData_id/Aln_id -> Polymer_data/Alignment
"""

from collections import defaultdict

from django.http import JsonResponse, Http404
from django.db.models import Count, Q

from alignments.models import (
    Alignment,
    AlnData,
    Nomenclature,
    PolymerAlignments,
    PolymerData,
    PolymerMetadata,
    Residues,
    Species,
    Taxgroups,
)

MITO = 'mito'
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500


# --------------------------------------------------------------------------
# Helpers

def _paginate(qs, request):
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.GET.get('page_size', DEFAULT_PAGE_SIZE))))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    total = qs.count()
    start = (page - 1) * page_size
    return qs[start:start + page_size], {'total': total, 'page': page, 'page_size': page_size}


def _taxgroup_ids_param(request):
    """Parse ?taxgroup_ids=1,2,3 or ?taxgroup_ids[]=1&taxgroup_ids[]=2."""
    raw = request.GET.getlist('taxgroup_ids[]') or request.GET.getlist('taxgroup_ids')
    ids = []
    for item in raw:
        for part in str(item).split(','):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
    return ids


def _expand_taxgroups_to_strains(taxgroup_ids):
    """Given a set of TaxGroups ids (any level), return all descendant strain-level taxgroup_ids.

    If a given id is itself a strain-level row, it's included directly.
    Returns [] if taxgroup_ids is empty.
    """
    if not taxgroup_ids:
        return []
    # Load the full tree once (small — 521 rows).
    rows = Taxgroups.objects.using(MITO).values_list('taxgroup_id', 'parent', 'grouplevel')
    children = defaultdict(list)
    level = {}
    for tid, parent, lvl in rows:
        level[tid] = lvl
        if parent:
            children[parent].append(tid)
    strains = []
    stack = list(taxgroup_ids)
    seen = set()
    while stack:
        tid = stack.pop()
        if tid in seen:
            continue
        seen.add(tid)
        if level.get(tid) == 'strain':
            strains.append(tid)
        stack.extend(children.get(tid, []))
    return strains


# --------------------------------------------------------------------------
# /api/filter-options/

def filter_options_api(request):
    """Return distinct values for each categorical filter column.

    Called once on app mount; drives the sidebar dropdowns.
    """
    def distinct(model, field, using=MITO):
        return sorted(
            v for v in model.objects.using(using).values_list(field, flat=True).distinct()
            if v not in (None, '')
        )

    return JsonResponse({
        'prediction_type':     distinct(PolymerMetadata, 'prediction_type'),
        'evolutionary_origin': distinct(PolymerMetadata, 'evolutionary_origin'),
        'assembly':            distinct(PolymerMetadata, 'assembly'),
        'sequence_location':   distinct(PolymerMetadata, 'sequence_location'),
        'assembly_location':   distinct(PolymerMetadata, 'assembly_location'),
        'data_location':       distinct(PolymerMetadata, 'data_location'),
        'protein_names':       distinct(Nomenclature,    'new_name'),
    })


# --------------------------------------------------------------------------
# /api/taxtree/

def taxtree_api(request):
    """Return the full TaxGroups hierarchy as a nested JSON tree.

    Shape:
        {
          "roots": [ node, ... ],
        }
    where node = {"id": int, "level": str, "name": str, "children": [node, ...]}.
    """
    rows = list(
        Taxgroups.objects.using(MITO).values('taxgroup_id', 'parent', 'grouplevel', 'groupname')
    )
    by_id = {}
    children = defaultdict(list)
    for r in rows:
        node = {
            'id': r['taxgroup_id'],
            'level': r['grouplevel'],
            'name': r['groupname'],
            'children': [],
        }
        by_id[r['taxgroup_id']] = node
        if r['parent']:
            children[r['parent']].append(r['taxgroup_id'])

    # Attach children
    for parent_id, kids in children.items():
        if parent_id not in by_id:
            continue
        by_id[parent_id]['children'] = [by_id[k] for k in kids if k in by_id]

    roots = [by_id[r['taxgroup_id']] for r in rows if not r['parent']]
    return JsonResponse({'roots': roots})


# --------------------------------------------------------------------------
# /api/sequences/

def _build_sequences_qs(request):
    qs = PolymerData.objects.using(MITO).select_related('strain', 'nomgd')

    taxgroup_ids = _taxgroup_ids_param(request)
    if taxgroup_ids:
        strain_ids = _expand_taxgroups_to_strains(taxgroup_ids)
        if not strain_ids:
            return qs.none()
        qs = qs.filter(strain_id__in=strain_ids)

    protein_name = request.GET.get('protein_name')
    if protein_name:
        qs = qs.filter(nomgd__new_name=protein_name)

    # Metadata filters — all exact match now that the UI drives them from
    # dropdowns of distinct values.
    meta_filters = {}
    for param, col in [
        ('prediction_type', 'polymermetadata__prediction_type'),
        ('evolutionary_origin', 'polymermetadata__evolutionary_origin'),
        ('assembly', 'polymermetadata__assembly'),
        ('sequence_location', 'polymermetadata__sequence_location'),
        ('assembly_location', 'polymermetadata__assembly_location'),
        ('data_location', 'polymermetadata__data_location'),
        ('alternate_name', 'polymermetadata__alternate_name'),
    ]:
        v = request.GET.get(param)
        if v:
            meta_filters[col] = v
    if meta_filters:
        qs = qs.filter(**meta_filters)

    return qs.order_by('id').distinct()


def sequences_api(request):
    qs = _build_sequences_qs(request)
    page_qs, meta = _paginate(qs, request)

    # Pull metadata for the page in one extra query (OneToMany in principle, 1:1 in practice).
    page_ids = [p.id for p in page_qs]
    meta_by_pdata = {}
    if page_ids:
        for m in PolymerMetadata.objects.using(MITO).filter(pdata_id__in=page_ids).values(
            'pdata_id', 'prediction_type', 'evolutionary_origin', 'assembly', 'assembly_location',
            'sequence_location', 'data_location', 'alternate_name', 'fragment',
        ):
            # If multiple rows per pdata ever appear, first-win is fine for list view.
            meta_by_pdata.setdefault(m['pdata_id'], m)

    results = []
    for p in page_qs:
        md = meta_by_pdata.get(p.id, {})
        results.append({
            'id': p.id,
            'protein_name': p.nomgd.new_name if p.nomgd_id else None,
            'strain_id': p.strain_id,
            'strain_name': p.strain.name if p.strain_id else None,
            'protein_location_header': p.protein_location_header,
            'prediction_type': md.get('prediction_type'),
            'evolutionary_origin': md.get('evolutionary_origin'),
            'assembly': md.get('assembly'),
            'alternate_name': md.get('alternate_name'),
        })

    return JsonResponse({'results': results, **meta})


def sequence_detail_api(request, pdata_id):
    try:
        p = PolymerData.objects.using(MITO).select_related('strain', 'nomgd').get(id=pdata_id)
    except PolymerData.DoesNotExist:
        raise Http404
    metas = list(PolymerMetadata.objects.using(MITO).filter(pdata_id=p.id).values(
        'data_location', 'fullseq', 'sequence_location', 'assembly_location', 'assembly',
        'evolutionary_origin', 'prediction_type', 'alternate_name', 'fragment',
    ))
    return JsonResponse({
        'id': p.id,
        'protein_name': p.nomgd.new_name if p.nomgd_id else None,
        'protein_location_header': p.protein_location_header,
        'strain_id': p.strain_id,
        'strain_name': p.strain.name if p.strain_id else None,
        'metadata': metas,
    })


# --------------------------------------------------------------------------
# /api/organisms/

def organisms_api(request):
    """Paginated Species list, filtered by any of the Sequences-mode filters.

    A Species is kept iff it has at least one Polymer_data row whose joined
    Polymer_metadata satisfies every active filter. For matching strains the
    response also returns the set of origins / prediction types / data
    locations actually present, so the UI can render aggregate tags.
    """
    # Build the protein-level queryset first using the same filter semantics
    # as sequences_api, then collapse to distinct strain_ids.
    pd_qs = PolymerData.objects.using(MITO).all()

    protein_name = request.GET.get('protein_name')
    if protein_name:
        pd_qs = pd_qs.filter(nomgd__new_name=protein_name)

    meta_filters = {}
    for param, col in [
        ('prediction_type', 'polymermetadata__prediction_type'),
        ('evolutionary_origin', 'polymermetadata__evolutionary_origin'),
        ('assembly', 'polymermetadata__assembly'),
        ('sequence_location', 'polymermetadata__sequence_location'),
        ('assembly_location', 'polymermetadata__assembly_location'),
        ('data_location', 'polymermetadata__data_location'),
    ]:
        v = request.GET.get(param)
        if v:
            meta_filters[col] = v
    if meta_filters:
        pd_qs = pd_qs.filter(**meta_filters)

    taxgroup_ids = _taxgroup_ids_param(request)
    if taxgroup_ids:
        strain_ids = _expand_taxgroups_to_strains(taxgroup_ids)
        if not strain_ids:
            return JsonResponse({'results': [], 'total': 0, 'page': 1, 'page_size': DEFAULT_PAGE_SIZE})
        pd_qs = pd_qs.filter(strain_id__in=strain_ids)

    matching_strain_ids = list(pd_qs.values_list('strain_id', flat=True).distinct())

    qs = Species.objects.using(MITO).filter(strain_id__in=matching_strain_ids).order_by('name')
    page_qs, meta = _paginate(qs, request)
    page_strain_ids = [s.strain_id for s in page_qs]

    # Protein count per strain (honors the same filters via pd_qs).
    counts = dict(
        pd_qs.filter(strain_id__in=page_strain_ids)
             .values('strain_id')
             .annotate(n=Count('id'))
             .values_list('strain_id', 'n')
    )

    # Aggregate tag sets per strain: which origins / prediction types /
    # data locations are represented. One query, small result set.
    tag_rows = list(
        PolymerMetadata.objects.using(MITO)
        .filter(pdata__strain_id__in=page_strain_ids)
        .values('pdata__strain_id', 'evolutionary_origin', 'prediction_type',
                'data_location', 'assembly_location')
    )
    tags = {sid: {'origins': set(), 'prediction_types': set(),
                  'data_locations': set(), 'assembly_locations': set()}
            for sid in page_strain_ids}
    for r in tag_rows:
        sid = r['pdata__strain_id']
        bucket = tags.get(sid)
        if not bucket:
            continue
        if r['evolutionary_origin']: bucket['origins'].add(r['evolutionary_origin'])
        if r['prediction_type']:     bucket['prediction_types'].add(r['prediction_type'])
        if r['data_location']:       bucket['data_locations'].add(r['data_location'])
        if r['assembly_location']:   bucket['assembly_locations'].add(r['assembly_location'])

    results = [{
        'strain_id': s.strain_id,
        'name': s.name,
        'protein_count': counts.get(s.strain_id, 0),
        'origins':            sorted(tags[s.strain_id]['origins']),
        'prediction_types':   sorted(tags[s.strain_id]['prediction_types']),
        'data_locations':     sorted(tags[s.strain_id]['data_locations']),
        'assembly_locations': sorted(tags[s.strain_id]['assembly_locations']),
    } for s in page_qs]

    return JsonResponse({'results': results, **meta})


# --------------------------------------------------------------------------
# /api/proteins-for-taxgroups/

def proteins_for_taxgroups_api(request):
    """Distinct protein names available for the selected taxgroup(s).

    Used by the Alignments mode to populate the protein picker *after* the
    user has selected one or more organisms. Empty taxgroup list returns all
    protein names (same as filter_options_api.protein_names).
    """
    taxgroup_ids = _taxgroup_ids_param(request)
    pd_qs = PolymerData.objects.using(MITO).all()
    if taxgroup_ids:
        strain_ids = _expand_taxgroups_to_strains(taxgroup_ids)
        pd_qs = pd_qs.filter(strain_id__in=strain_ids)
    names = sorted(
        n for n in pd_qs.values_list('nomgd__new_name', flat=True).distinct()
        if n
    )
    return JsonResponse({'results': names})


# --------------------------------------------------------------------------
# /api/alignments/

def alignments_api(request):
    """Alignments narrowed by (taxgroup_ids, protein_name).

    An alignment is kept iff it has at least one Polymer_Alignments member
    whose Polymer_data row satisfies the filters. With no filters, every
    alignment is returned.
    """
    qs = Alignment.objects.using(MITO).all()

    # Build membership filter on Polymer_data + FK joins.
    pd_qs = PolymerData.objects.using(MITO).all()
    narrow = False

    taxgroup_ids = _taxgroup_ids_param(request)
    if taxgroup_ids:
        strain_ids = _expand_taxgroups_to_strains(taxgroup_ids)
        if not strain_ids:
            return JsonResponse({'results': [], 'total': 0, 'page': 1, 'page_size': DEFAULT_PAGE_SIZE})
        pd_qs = pd_qs.filter(strain_id__in=strain_ids)
        narrow = True

    protein_name = request.GET.get('protein_name')
    if protein_name:
        pd_qs = pd_qs.filter(nomgd__new_name=protein_name)
        narrow = True

    if narrow:
        pa_aln_ids = (
            PolymerAlignments.objects.using(MITO)
            .filter(pdata_id__in=pd_qs.values_list('id', flat=True))
            .values_list('aln_id', flat=True).distinct()
        )
        qs = qs.filter(aln_id__in=list(pa_aln_ids))

    qs = qs.order_by('aln_id')
    page_qs, meta = _paginate(qs, request)
    page_ids = [a.aln_id for a in page_qs]

    # Member count honors the filter narrowing so the reported count matches
    # what the user's filters would select in that alignment.
    member_qs = PolymerAlignments.objects.using(MITO).filter(aln_id__in=page_ids)
    if narrow:
        member_qs = member_qs.filter(pdata_id__in=pd_qs.values_list('id', flat=True))
    counts = dict(
        member_qs.values('aln_id').annotate(n=Count('pdata_id')).values_list('aln_id', 'n')
    )

    results = [{
        'aln_id': a.aln_id,
        'name': a.name,
        'method': a.method,
        'source': a.source,
        'member_count': counts.get(a.aln_id, 0),
    } for a in page_qs]

    return JsonResponse({'results': results, **meta})


# --------------------------------------------------------------------------
# /api/alignments/<aln_id>/<tax_group>/fasta/

def alignment_fasta_api(request, aln_id, tax_group):
    """Build an aligned FASTA for one alignment, optionally restricted by taxa.

    `tax_group` is one or more TaxGroups ids (any level), comma-separated.
    Their strain-level descendants are unioned to select which polymers
    participate. Passing `0` (or an empty/invalid value) means no taxon
    narrowing.
    """
    try:
        aln = Alignment.objects.using(MITO).get(pk=aln_id)
    except Alignment.DoesNotExist:
        raise Http404(f"Alignment {aln_id} not found")

    pa_qs = PolymerAlignments.objects.using(MITO).filter(aln_id=aln_id)
    tax_group_ints = []
    for part in str(tax_group).split(','):
        part = part.strip()
        if part.isdigit() and int(part) != 0:
            tax_group_ints.append(int(part))
    if tax_group_ints:
        strain_ids = _expand_taxgroups_to_strains(tax_group_ints)
        if not strain_ids:
            return JsonResponse({
                'aln_id': aln_id, 'name': aln.name,
                'length': 0, 'sequences': [], 'fasta': '',
            })
        member_pdata_ids = list(
            pa_qs.filter(pdata__strain_id__in=strain_ids)
            .values_list('pdata_id', flat=True)
        )
    else:
        member_pdata_ids = list(pa_qs.values_list('pdata_id', flat=True))

    if not member_pdata_ids:
        return JsonResponse({
            'aln_id': aln_id, 'name': aln.name,
            'length': 0, 'sequences': [], 'fasta': '',
        })

    pd_rows = (
        PolymerData.objects.using(MITO)
        .filter(id__in=member_pdata_ids)
        .values('id', 'strain__name', 'strain__strain', 'strain_id',
                'nomgd__new_name', 'protein_location_header')
    )
    header_by_pdata = {r['id']: r for r in pd_rows}

    res_rows = (
        AlnData.objects.using(MITO)
        .filter(aln_id=aln_id, res__poldata_id__in=member_pdata_ids)
        .values('res__poldata_id', 'aln_pos', 'res__unmodresname')
    )
    max_pos = 0
    per_pdata = defaultdict(dict)
    for r in res_rows:
        pos = r['aln_pos']
        per_pdata[r['res__poldata_id']][pos] = (r['res__unmodresname'] or '-')
        if pos > max_pos:
            max_pos = pos

    sequences = []
    fasta_chunks = []
    for pdata_id in member_pdata_ids:
        hdr = header_by_pdata.get(pdata_id) or {}
        positions = per_pdata.get(pdata_id, {})
        if not positions:
            continue
        seq = ''.join(positions.get(p, '-') for p in range(1, max_pos + 1))
        strain_name = (hdr.get('strain__name') or '').strip()
        strain_strain = (hdr.get('strain__strain') or '').strip()
        protein_name = (hdr.get('nomgd__new_name') or '').strip()
        strain_label = strain_name if not strain_strain else f"{strain_name} {strain_strain}"
        name = f"{protein_name or 'protein'}|{strain_label or ('strain_' + str(hdr.get('strain_id') or '?'))}|pdata_{pdata_id}"
        sequences.append({'name': name, 'sequence': seq})
        fasta_chunks.append(f">{name}\n{seq}")

    return JsonResponse({
        'aln_id': aln_id,
        'name': aln.name,
        'length': max_pos,
        'sequences': sequences,
        'fasta': '\n'.join(fasta_chunks) + ('\n' if fasta_chunks else ''),
    })
