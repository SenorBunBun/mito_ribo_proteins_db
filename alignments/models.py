# Auto-generated from the live `mito` database via
#   python manage.py inspectdb --database mito
# Do not edit by hand without re-running inspectdb and diffing.
# The prior hand-maintained version went stale — see README.md ("Gotchas").

from django.db import models


class Alignment(models.Model):
    aln_id = models.AutoField(db_column='Aln_id', primary_key=True)
    name = models.CharField(db_column='Name', max_length=45)
    method = models.CharField(db_column='Method', max_length=45)
    source = models.CharField(db_column='Source', max_length=10)

    class Meta:
        managed = False
        db_table = 'Alignment'
        unique_together = (('name', 'method', 'source'),)


class AlnData(models.Model):
    aln_data_id = models.AutoField(db_column='Aln_Data_id', primary_key=True)
    aln = models.ForeignKey(Alignment, models.DO_NOTHING)
    res = models.ForeignKey('Residues', models.DO_NOTHING)
    aln_pos = models.IntegerField()
    polymer_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Aln_Data'


class Nomenclature(models.Model):
    nom_id = models.AutoField(primary_key=True)
    new_name = models.CharField(max_length=45, blank=True, null=True)
    occurence = models.CharField(max_length=45, blank=True, null=True)
    new_tablecol = models.CharField(max_length=45, blank=True, null=True)
    moleculegroup = models.CharField(db_column='MoleculeGroup', max_length=45, blank=True, null=True)
    phylogeneticoccurence = models.CharField(db_column='PhylogeneticOccurence', max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Nomenclature'


class PolymerAlignments(models.Model):
    pdata = models.ForeignKey('PolymerData', models.DO_NOTHING, db_column='PData_id')
    aln = models.ForeignKey(Alignment, models.DO_NOTHING, db_column='Aln_id')

    class Meta:
        managed = False
        db_table = 'Polymer_Alignments'
        unique_together = (('pdata', 'aln'),)


class PolymerData(models.Model):
    protein_location_header = models.CharField(max_length=500)
    strain = models.ForeignKey('Species', models.DO_NOTHING)
    nomgd = models.ForeignKey(Nomenclature, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Polymer_data'
        unique_together = (('protein_location_header', 'strain', 'nomgd'),)


class PolymerMetadata(models.Model):
    pdata = models.ForeignKey(PolymerData, models.DO_NOTHING, db_column='PData_id')
    data_location = models.CharField(max_length=500, blank=True, null=True)
    fullseq = models.TextField(blank=True, null=True)
    sequence_location = models.CharField(max_length=500, blank=True, null=True)
    assembly_location = models.CharField(max_length=500, blank=True, null=True)
    assembly = models.CharField(max_length=100, blank=True, null=True)
    evolutionary_origin = models.CharField(max_length=100, blank=True, null=True)
    prediction_type = models.CharField(max_length=100, blank=True, null=True)
    alternate_name = models.CharField(max_length=255, blank=True, null=True)
    fragment = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Polymer_metadata'


class Residues(models.Model):
    resi_id = models.AutoField(primary_key=True)
    poldata = models.ForeignKey(PolymerData, models.DO_NOTHING, db_column='PolData_id')
    resnum = models.IntegerField(db_column='resNum')
    unmodresname = models.CharField(db_column='unModResName', max_length=1)
    modresname = models.CharField(db_column='modResName', max_length=1, blank=True, null=True)
    codon = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Residues'


class Species(models.Model):
    strain_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=60, blank=True, null=True)
    strain = models.CharField(max_length=100, blank=True, null=True)
    taxid = models.IntegerField(blank=True, null=True)
    abbreviation = models.CharField(db_column='Abbreviation', max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Species'


class SingletonProtein(models.Model):
    protein_id = models.SmallIntegerField(primary_key=True)
    protein_name = models.CharField(max_length=20, unique=True)

    class Meta:
        managed = False
        db_table = 'Singleton_Protein'


class SingletonStructure(models.Model):
    structure_id = models.SmallIntegerField(primary_key=True)
    pdb_id = models.CharField(max_length=4, unique=True)
    organism_name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Singleton_Structure'


class SingletonProteinChain(models.Model):
    id = models.AutoField(primary_key=True)
    protein = models.ForeignKey(SingletonProtein, models.DO_NOTHING, db_column='protein_id', related_name='chains')
    structure = models.ForeignKey(SingletonStructure, models.DO_NOTHING, db_column='structure_id', related_name='chains')
    chain_name = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'Singleton_Protein_Chain'


class Taxgroups(models.Model):
    taxgroup_id = models.IntegerField(primary_key=True)
    grouplevel = models.CharField(db_column='groupLevel', max_length=45, blank=True, null=True)
    groupname = models.CharField(db_column='groupName', max_length=100, blank=True, null=True)
    parent = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TaxGroups'
