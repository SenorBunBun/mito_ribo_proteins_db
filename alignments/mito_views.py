"""API endpoints for the mito (DESIRE_mito_as1) database.

All querysets must pass `.using('mito')` — there is no DB router.
Join map:
    Polymer_data.strain_id -> Species.strain_id (= TaxGroups.taxgroup_id)
    Polymer_data.nomgd_id  -> Nomenclature.nom_id
    Polymer_metadata.PData_id -> Polymer_data.id
    Polymer_Alignments.PData_id/Aln_id -> Polymer_data/Alignment
"""

import io
import re
import zipfile
from collections import defaultdict

from django.http import JsonResponse, Http404, HttpResponse, StreamingHttpResponse
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


_PROT_RE = re.compile(r'^([A-Za-z]?)([SL])(\d+)(.*)$', re.IGNORECASE)

def _protein_sort_key(name):
    # Ribosomal-protein order: S-series first ascending, then L-series
    # ascending, then anything else alphabetic. Matches names like
    # 'S1', 'mS39', 'uS02m', 'bL07m', 'mL38'.
    m = _PROT_RE.match(name or '')
    if not m:
        return (2, 0, '', name or '')
    prefix, letter, num, rest = m.group(1), m.group(2).upper(), int(m.group(3)), m.group(4)
    bucket = 0 if letter == 'S' else 1
    return (bucket, num, prefix.lower(), rest.lower())


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
        'protein_names':       sorted(distinct(Nomenclature, 'new_name'),
                                       key=_protein_sort_key),
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

    # Order by ribosomal-protein convention (S-series ascending, then L-series
    # ascending, then anything else). Sort key is Python-side, so materialize
    # (id, new_name) for all matching rows, sort, then page in Python.
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.GET.get('page_size', DEFAULT_PAGE_SIZE))))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE

    id_name_pairs = list(qs.values_list('id', 'nomgd__new_name'))
    id_name_pairs.sort(key=lambda t: (_protein_sort_key(t[1]), t[0]))
    total = len(id_name_pairs)
    start = (page - 1) * page_size
    page_ids = [pid for pid, _ in id_name_pairs[start:start + page_size]]
    meta = {'total': total, 'page': page, 'page_size': page_size}

    # Fetch the page rows by id, preserving sorted order.
    page_rows = {
        p.id: p for p in
        PolymerData.objects.using(MITO).select_related('strain', 'nomgd').filter(id__in=page_ids)
    }
    page_qs = [page_rows[pid] for pid in page_ids if pid in page_rows]

    # Pull metadata for the page in one extra query (OneToMany in principle, 1:1 in practice).
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
# /api/sequences/fasta/

def _parse_id_list(raw):
    out = []
    for part in (raw or '').split(','):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out


def download_fasta_api(request):
    """Stream a FASTA of the rows matching the current filters.

    Accepts the same filter params as sequences_api plus optional
    `ids=` (whitelist) and `exclude_ids=` (blacklist) — both
    intersected with the filter set so the user can only download
    rows they could see.

    Header format: >{protein}_{strain_abbreviation}|{protein_location_header}
    """
    qs = _build_sequences_qs(request)

    ids = _parse_id_list(request.GET.get('ids'))
    if ids:
        qs = qs.filter(id__in=ids)
    excl = _parse_id_list(request.GET.get('exclude_ids'))
    if excl:
        qs = qs.exclude(id__in=excl)

    rows = list(qs.values(
        'id', 'protein_location_header',
        'nomgd__new_name', 'strain_id', 'strain__abbreviation',
    ))
    row_ids = [r['id'] for r in rows]
    seqs = dict(
        PolymerMetadata.objects.using(MITO)
            .filter(pdata_id__in=row_ids)
            .values_list('pdata_id', 'fullseq')
    )

    def fasta_gen():
        for r in rows:
            seq = (seqs.get(r['id']) or '').strip()
            if not seq:
                continue
            protein = (r['nomgd__new_name'] or 'unknown').strip()
            abbr    = (r['strain__abbreviation'] or 'unknown').strip()
            header  = (r['protein_location_header'] or '').strip()
            sid     = r['strain_id']
            yield f">{protein}_{sid}.0_{abbr}|{header}\n"
            for i in range(0, len(seq), 60):
                yield seq[i:i+60] + '\n'

    resp = StreamingHttpResponse(fasta_gen(), content_type='text/x-fasta; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="sequences.fasta"'
    return resp


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

    # Sequence count + distinct ribosomal-protein count per strain
    # (one query, honors the same filters via pd_qs).
    count_rows = (
        pd_qs.filter(strain_id__in=page_strain_ids)
             .values('strain_id')
             .annotate(n=Count('id'), n_proteins=Count('nomgd_id', distinct=True))
    )
    counts          = {r['strain_id']: r['n']           for r in count_rows}
    unique_proteins = {r['strain_id']: r['n_proteins']  for r in count_rows}

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
        'unique_protein_count': unique_proteins.get(s.strain_id, 0),
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
        (n for n in pd_qs.values_list('nomgd__new_name', flat=True).distinct() if n),
        key=_protein_sort_key,
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

    # Sort by protein-name order (S-series → L-series, ascending numeric),
    # same key as the Sequences view. Done Python-side; the Alignment table
    # is small (~90 rows).
    all_rows = list(qs.values('aln_id', 'name', 'method', 'source'))
    all_rows.sort(key=lambda r: (_protein_sort_key(r['name']), r['aln_id']))

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.GET.get('page_size', DEFAULT_PAGE_SIZE))))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    total = len(all_rows)
    start = (page - 1) * page_size
    page_rows = all_rows[start:start + page_size]
    page_ids = [r['aln_id'] for r in page_rows]
    meta = {'total': total, 'page': page, 'page_size': page_size}

    # Member count honors the filter narrowing so the reported count matches
    # what the user's filters would select in that alignment.
    member_qs = PolymerAlignments.objects.using(MITO).filter(aln_id__in=page_ids)
    if narrow:
        member_qs = member_qs.filter(pdata_id__in=pd_qs.values_list('id', flat=True))
    counts = dict(
        member_qs.values('aln_id').annotate(n=Count('pdata_id')).values_list('aln_id', 'n')
    )

    results = [{
        'aln_id': r['aln_id'],
        'name': r['name'],
        'method': r['method'],
        'source': r['source'],
        'member_count': counts.get(r['aln_id'], 0),
    } for r in page_rows]

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


# --------------------------------------------------------------------------
# Alignment FASTA downloads (one .fasta per protein, zipped when >1 alignment)

def _aligned_fasta_groups(aln_ids, pd_qs=None):
    """Return {protein_name: [fasta_chunks ...]} for the given alignments.

    Each entry's chunks are 60-wrapped FASTA records using the same header
    schema as the Sequences download: >{protein}_{strain_id}.0_{abbr}|{loc}.
    Bodies are the aligned residue strings filled from Aln_Data.
    """
    pa_qs = PolymerAlignments.objects.using(MITO).filter(aln_id__in=aln_ids)
    if pd_qs is not None:
        pa_qs = pa_qs.filter(pdata_id__in=pd_qs.values_list('id', flat=True))
    member_pdata_ids = list(pa_qs.values_list('pdata_id', flat=True).distinct())
    if not member_pdata_ids:
        return {}

    pd_rows = PolymerData.objects.using(MITO).filter(id__in=member_pdata_ids).values(
        'id', 'protein_location_header',
        'nomgd__new_name', 'strain_id', 'strain__abbreviation',
    )
    hdr_by_pdata = {r['id']: r for r in pd_rows}

    res_rows = AlnData.objects.using(MITO).filter(
        aln_id__in=aln_ids, res__poldata_id__in=member_pdata_ids,
    ).values('aln_id', 'res__poldata_id', 'aln_pos', 'res__unmodresname')

    aln_max = defaultdict(int)
    per_aln_pdata = defaultdict(lambda: defaultdict(dict))
    for r in res_rows:
        per_aln_pdata[r['aln_id']][r['res__poldata_id']][r['aln_pos']] = (r['res__unmodresname'] or '-')
        if r['aln_pos'] > aln_max[r['aln_id']]:
            aln_max[r['aln_id']] = r['aln_pos']

    by_protein = defaultdict(list)
    for aln_id in aln_ids:
        max_pos = aln_max.get(aln_id, 0)
        if not max_pos:
            continue
        for pdata_id, positions in per_aln_pdata[aln_id].items():
            hdr = hdr_by_pdata.get(pdata_id) or {}
            protein = (hdr.get('nomgd__new_name') or 'unknown').strip()
            abbr    = (hdr.get('strain__abbreviation') or 'unknown').strip()
            sid     = hdr.get('strain_id') or 0
            ploc    = (hdr.get('protein_location_header') or '').strip()
            seq = ''.join(positions.get(p, '-') for p in range(1, max_pos + 1))
            lines = [f">{protein}_{sid}.0_{abbr}|{ploc}"]
            for i in range(0, len(seq), 60):
                lines.append(seq[i:i+60])
            by_protein[protein].append('\n'.join(lines))
    return by_protein


def _zip_response(by_protein, zip_name):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        if by_protein:
            for protein, records in by_protein.items():
                zf.writestr(f"{protein}_filtered.fasta", '\n'.join(records) + '\n')
        else:
            zf.writestr("empty.txt", "No alignment members matched the current filters.\n")
    resp = HttpResponse(buf.getvalue(), content_type='application/zip')
    resp['Content-Disposition'] = f'attachment; filename="{zip_name}"'
    return resp


def download_alignments_zip_api(request):
    """Multi-alignment ZIP — one .fasta per protein.

    Accepts the same filter params as alignments_api (`taxgroup_ids[]`,
    `protein_name`) plus optional `ids=` / `exclude_ids=` for the
    checkbox selection.
    """
    pd_qs = PolymerData.objects.using(MITO).all()
    narrow = False
    taxgroup_ids = _taxgroup_ids_param(request)
    if taxgroup_ids:
        strain_ids = _expand_taxgroups_to_strains(taxgroup_ids)
        if not strain_ids:
            return _zip_response({}, 'alignments_export.zip')
        pd_qs = pd_qs.filter(strain_id__in=strain_ids)
        narrow = True
    protein_name = request.GET.get('protein_name')
    if protein_name:
        pd_qs = pd_qs.filter(nomgd__new_name=protein_name)
        narrow = True

    base_qs = Alignment.objects.using(MITO).all()
    if narrow:
        pa_aln_ids = (PolymerAlignments.objects.using(MITO)
                      .filter(pdata_id__in=pd_qs.values_list('id', flat=True))
                      .values_list('aln_id', flat=True).distinct())
        base_qs = base_qs.filter(aln_id__in=list(pa_aln_ids))

    ids  = _parse_id_list(request.GET.get('ids'))
    excl = _parse_id_list(request.GET.get('exclude_ids'))
    if ids:  base_qs = base_qs.filter(aln_id__in=ids)
    if excl: base_qs = base_qs.exclude(aln_id__in=excl)
    aln_ids = list(base_qs.values_list('aln_id', flat=True))

    by_protein = _aligned_fasta_groups(aln_ids, pd_qs if narrow else None)
    return _zip_response(by_protein, 'alignments_export.zip')


def alignment_zip_api(request, aln_id, tax_group):
    """Single-alignment download — emits a bare {protein}_filtered.fasta since
    every alignment here represents exactly one protein."""
    pd_qs = None
    tax_ints = [int(x) for x in str(tax_group).split(',') if x.strip().isdigit() and int(x)]
    if tax_ints:
        strain_ids = _expand_taxgroups_to_strains(tax_ints)
        if not strain_ids:
            return _zip_response({}, f'alignment_{aln_id}.zip')
        pd_qs = PolymerData.objects.using(MITO).filter(strain_id__in=strain_ids)

    by_protein = _aligned_fasta_groups([aln_id], pd_qs)
    if len(by_protein) == 1:
        protein, records = next(iter(by_protein.items()))
        body = '\n'.join(records) + '\n'
        resp = HttpResponse(body, content_type='text/x-fasta; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="{protein}_filtered.fasta"'
        return resp
    return _zip_response(by_protein, f'alignment_{aln_id}.zip')
