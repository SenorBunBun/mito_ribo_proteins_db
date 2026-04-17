import contextlib
import re, os, warnings, io, base64, json
import datetime
import urllib.request
import shutil
from subprocess import Popen, PIPE
from pdbecif.mmcif_io import CifFileReader
from Bio import AlignIO, BiopythonDeprecationWarning, PDB
from io import StringIO

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

from alignments.models import *
from alignments.taxonomy_views import *
from alignments.residue_api import *
from alignments.structure_api import *
from alignments.fold_api import *
from alignments.runal2co import executeAl2co
import alignments.alignment_query_and_build as aqab
from twincons.TwinCons import slice_by_name
from django.db import connections
import time
from xml.dom import minidom

import plotly.express as px
import pandas as pd
import ast

import os


import numpy as np

class c:
    structureObj = None

json_query = """
    SELECT {0}->>'$."{1}"' FROM {2}
"""

def fetch_all_bed_files(request):
    path = os.getcwd() + "static/peak_bg_files"
    all_items = os.listdir('/var/www/lncRNA_RBP_webdb/static/peak_bg_files')
    context = {
        "results" : all_items
    }
    print(context)
    return JsonResponse(context)

def get_rbps(request):
    path = "/var/www/lncRNA_RBP_webdb/static/transcript_files/rbp_list_gencode.txt"
    with open(path, "r") as f:
        items_list = [line.strip() for line in f]
    context = {
        "results" : items_list
    }
    print(context)
    return JsonResponse(context)

def fetchTranscriptsFromRBP(request):
    rbp = request.POST['rbp[rbp]']
    transcriptsFromRBP = []
    print("Starting fetchTranscriptsFromRBP query")
    with connections['ncRNA'].cursor() as cursor:
        query = json_query.format("json", rbp, "rbp_to_transcripts")
        cursor.execute(query)

        for row in eval(cursor.fetchall()[0][0]):
            print(row)
            transcriptsFromRBP.append(row)
            transcriptsFromRBP.sort()
    context = {
        "results" : transcriptsFromRBP
    }
    print(context)
    return JsonResponse(context)
        

def allGencodeTranscripts(request):
    allGencodeTranscripts = []
    print("Starting transcript query")
    with connections['ncRNA'].cursor() as cursor:
        query = "select internal_id, transcript_name FROM gencode_schema_ids LIMIT 10000"
        cursor.execute(query)
        for row in cursor.fetchall():
            allGencodeTranscripts.append(row)
    context = {
        "results" : allGencodeTranscripts
    }
    print(context)
    return JsonResponse(context)

def fetchTranscriptPeak(request):
    internal_id = request.POST['internal_id[transcript_obj]']
    print(internal_id)
    with connections['ncRNA'].cursor() as cursor:
        query = json_query.format("peaks", internal_id, "gencode_json_split")
        print(query)
        cursor.execute(query)
        res = cursor.fetchall()
    context = {
        "peaks" : res
    }
    print(context)
    #return JsonResponse(context)
    return context

def get_cell_lines(request):
    """Fetch all cell lines from the encore_cell_lines table"""
    cell_lines = []
    print("Starting cell lines query")
    with connections['ncRNA'].cursor() as cursor:
        query = "SELECT cell_line_id, cell_line_name FROM encore_cell_lines"
        cursor.execute(query)
        for row in cursor.fetchall():
            cell_lines.append({"id": row[0], "name": row[1]})
    context = {
        "results": cell_lines
    }
    print(context)
    return JsonResponse(context)

def get_track_rbps(request):
    """Fetch all RBPs from the encore_rbps table"""
    cell_line_id = request.POST['cell_line_id']
    print(f"Fetching RBPs for cell line: {cell_line_id}")
    rbps = []
    with connections['ncRNA'].cursor() as cursor:
        query = "SELECT rbp_id, rbp_name FROM encore_rbps"
        cursor.execute(query)
        for row in cursor.fetchall():
            rbps.append({"id": row[0], "name": row[1]})
    context = {
        "results": rbps
    }
    print(context)
    return JsonResponse(context)

def get_schema_types(request):
    """Fetch all unique schema types from encore_schema_ids"""
    schema_types = []
    with connections['ncRNA'].cursor() as cursor:
        query = "SELECT DISTINCT type FROM encore_schema_ids ORDER BY type"
        cursor.execute(query)
        for row in cursor.fetchall():
            schema_types.append(row[0])
    context = {
        "results": schema_types
    }
    return JsonResponse(context)

def get_gene_names(request):
    """Fetch all unique gene names for a selected schema type"""
    schema_type = request.POST.get('schema_type')
    gene_names = []
    with connections['ncRNA'].cursor() as cursor:
        query = "SELECT DISTINCT gene_name FROM encore_schema_ids WHERE type = %s AND gene_name IS NOT NULL ORDER BY gene_name"
        cursor.execute(query, [schema_type])
        for row in cursor.fetchall():
            gene_names.append(row[0])
    context = {
        "results": gene_names
    }
    return JsonResponse(context)

def get_schema_transcripts(request):
    """Fetch all transcripts for a selected schema type and gene name"""
    schema_type = request.POST.get('schema_type')
    gene_name = request.POST.get('gene_name')
    transcripts = []
    with connections['ncRNA'].cursor() as cursor:
        query = "SELECT id, transcript_name FROM encore_schema_ids WHERE type = %s AND gene_name = %s ORDER BY transcript_name"
        cursor.execute(query, [schema_type, gene_name])
        for row in cursor.fetchall():
            transcripts.append({"id": row[0], "name": row[1]})
    context = {
        "results": transcripts
    }
    return JsonResponse(context)

def search_transcripts_by_internal_id(request):
    """Search transcripts by internal_id for direct search in Track View"""
    search_query = request.POST.get('query', '')

    if len(search_query) < 2:
        return JsonResponse({"results": []})

    transcripts = []
    with connections['ncRNA'].cursor() as cursor:
        # Search by internal_id (partial match)
        query = """
            SELECT id, internal_id, transcript_name, gene_name, type
            FROM encore_schema_ids
            WHERE internal_id LIKE %s
            ORDER BY internal_id
            LIMIT 50
        """
        cursor.execute(query, [f"%{search_query}%"])

        for row in cursor.fetchall():
            transcripts.append({
                "id": row[0],
                "internal_id": row[1],
                "transcript_name": row[2] or row[1],  # Use internal_id if transcript_name is null
                "gene_name": row[3] or '',
                "type": row[4] or ''
            })

    context = {
        "results": transcripts
    }
    return JsonResponse(context)

def get_transcript_track_data(request):
    """Fetch track data for a specific transcript, RBP, and cell line combination"""
    transcript_id = request.POST.get('transcript_id')
    rbp_id = request.POST.get('rbp_id')
    cell_line_id = request.POST.get('cell_line_id')

    print(f"Fetching track data for transcript_id={transcript_id}, rbp_id={rbp_id}, cell_line_id={cell_line_id}")

    try:
        with connections['ncRNA'].cursor() as cursor:
            query = "SELECT track_data FROM encore_transcript_tracks WHERE id = %s AND rbp_id = %s AND cell_line_id = %s"
            cursor.execute(query, [transcript_id, rbp_id, cell_line_id])
            result = cursor.fetchone()

            if result and result[0]:
                # Convert bytearray to a list of integers
                track_data = result[0]

                if isinstance(track_data, (bytes, bytearray)):
                    # Simple conversion to a list of integers
                    track_data = np.frombuffer(track_data).tolist()

                    print(f"Converted track data to integer list with {len(track_data)} elements")

                context = {
                    "success": True,
                    "track_data": track_data,
                    "message": "Track data retrieved successfully"
                }
            else:
                context = {
                    "success": False,
                    "message": "No track data found for the selected combination"
                }
    except Exception as e:
        print(f"Error fetching track data: {str(e)}")
        context = {
            "success": False,
            "message": f"Error retrieving track data: {str(e)}"
        }

    return JsonResponse(context)

def fetchSeqLength(request):
    internal_id = request.POST['internal_id[transcript_obj]']
    with connections['ncRNA'].cursor() as cursor:
        query = json_query.format("sequence_lengths", internal_id, "gencode_json_split")
        cursor.execute(query)
        res = cursor.fetchall()
    return res
        
def displayRBPProfile(request):
    peak_str = fetchTranscriptPeak(request)["peaks"][0][0]
    print(type(peak_str))
    peaks = ast.literal_eval(peak_str)
    print(peaks)
    
    length = int(fetchSeqLength(request)[0][0])
    
    # plot = plot_cum_RBP_profile(peaks, length)
    
    context = {
        "peaks" : peaks,
    #    "plot" : plot,
        "length" : length
    }
    
    return JsonResponse(context)

# Obselete
def plot_cum_RBP_profile(peaks, length):
    #print(request.POST)
    #res = "<p> Request Received </p>"
    #return JsonResponse({"results": res})
    
    if peaks[0] == 'None':
        return "<p> No Peaks Found </p>"

    ids = []
    strengths = []
    seqidx = []
    for p in peaks:
        if len(p) != 3:
            print("Error processing {0} and peak {1}".format(id, p))

        count = p[1][1] - p[1][0] + 1
        ids.extend([p[0]]*count)
        strengths.extend([p[2]]*count)
        seqidx.extend(list(range(p[1][0], p[1][1]+1)))

    df = pd.DataFrame(data={'id': ids, 'strength': strengths, 'seqidx': seqidx})
    fig = px.bar(df, x='seqidx', y='strength', color='id', title='RBP Profile for {0}'.format(id), range_x=[0, length])
    fig.update_layout(bargap=0, )
    fig.update_xaxes(range=[0, length])
    
    res = fig.to_html(full_html=False)
    
    return res