<template>
    <div id="phylo_tree_dropdown">
        <div class="left-sidebar">
            <div id="tree_type" class="btn-group btn-group-toggle" data-toggle="buttons">
                
                <label class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:100%; z-index: 0;" for="orthologs" @change="rerenderIGV" >
                    <input type="radio" id="orthologs" value="transcript" v-model="selected_viewer">
                    Transcript Browser
                </label>

                <label class="btn btn-outline-dark" style="margin: 0 0 0 1%;width:50%;" for="upload" @change="rerenderIGV">
                    <input type="radio" id="upload" value="genome" v-model="selected_viewer">
                    Genomic Browser
                </label>

           
                
                <!-- 
                
                 <label class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:100%; z-index: 0;" @click="selected_viewer='transcript'">
                    Transcript Viewer
                </label>

                <label class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:100%; z-index: 0;" @click="selected_viewer='genome'">
                    Genome Viewer
                </label>
                -->

                <!-- 
                <label class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:100%; z-index: 0;" for="orthologs" >
                    <input type="radio" id="orthologs" value="orth" v-model="selected_viewer" v-on:input="cleanTreeOpts()" checked>
                    Transcript Viewer
                </label>
                -->
                <!--<label class="btn btn-outline-dark" for="paralogs">
                    <input type="radio" id="paralogs" value="para" v-model="type_tree" v-on:input="cleanTreeOpts()">
                    Paralogs
                </label>-->

        
                

                <!--
                -->
            </div>
            
            
            <!-- ncRNA view all transcripts and other filterng options -->
            <p v-if="selected_viewer=='genome'" >
                <br>

                <select class="btn btn-outline-dark dropdown-toggle" id="select_genome_track" v-model="genomic_peak_file" @click.once="fetch_all_bed_files" v-on:change="rerenderPeakTrack(genomic_peak_file)" style="margin: 0 1% 0 0;width:100%;">
                    <option :value="null" selected disabled hidden>Select Peaks to Display</option>
                    <option v-for="f in genomic_peak_file_list" v-bind:key="f" :value="f">{{ f.slice(0, -17) }}</option>
                </select>
            </p>

              <!--
            <p>
                <br>
              
                <select class="btn btn-outline-dark dropdown-toggle" id="select_rbp_gencode" v-if="selected_viewer=='transcript'" v-model="rbp" @click.once="loadGencodeRBPs" style="margin: 0 1% 0 0;width:100%;">
                    <option :value="null" selected disabled hidden>Select RBP</option>
                    <option v-for="rbp in rbpList" v-bind:key="rbp" :value="rbp">{{ rbp }}</option>
                </select>
             
            </p>
               -->

            <!-- Transcript browser options - Only visible when transcript browser is selected -->
            <div v-if="selected_viewer=='transcript'">
                <p>
                    <br>
                    <br>
                    
                    <!-- Radio buttons for selecting between peak and track views -->
                    <div id="transcript_view_type" class="btn-group btn-group-toggle" data-toggle="buttons">
                        <label class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:49%;" for="peaks_view">
                            <input type="radio" id="peaks_view" value="peaks" v-model="transcript_view_mode">
                            Peaks View
                        </label>

                        <label class="btn btn-outline-dark" style="margin: 0 0 0 1%;width:49%;" for="track_view">
                            <input type="radio" id="track_view" value="track" v-model="transcript_view_mode">
                            Track View
                        </label>
                    </div>
                    
                    <br>
                    <br>
                    
                    <!-- Only display RBP and transcript selectors when peak view is selected -->
                    <div v-if="transcript_view_mode=='peaks'">
                        <select class="btn btn-outline-dark dropdown-toggle" id="select_rbp_gencode" v-model="rbp" @click="loadGencodeRBPs" v-on:change="loadTranscriptsFromRBP({rbp})" style="margin: 0 1% 0 0;width:100%;">
                            <option :value="null" selected disabled hidden>Select RBP</option>
                            <option v-for="rbp in rbpList" v-bind:key="rbp" :value="rbp">{{ rbp }}</option>
                        </select>
                        
                        <br>
                        <br>

                        <p v-if="!allGencodeTranscripts && rbp" style="text-align: center;"> Querying Transcripts, please wait </p>

                        <!-- Searchable transcript dropdown -->
                        <div v-if="allGencodeTranscripts" style="position: relative;">
                            <input
                                type="text"
                                class="btn btn-outline-dark"
                                v-model="transcriptSearchQuery"
                                @input="filterTranscripts"
                                @focus="showTranscriptDropdown = true"
                                @blur="hideTranscriptDropdown"
                                :placeholder="transcript_obj || 'Search or select transcript...'"
                                style="margin: 0 1% 0 0; width:100%; text-align: left; cursor: text;"
                            />

                            <div
                                v-if="showTranscriptDropdown && filteredTranscripts && filteredTranscripts.length > 0"
                                class="transcript-dropdown"
                                style="position: absolute; top: 100%; left: 0; right: 1%; max-height: 200px; overflow-y: auto;
                                       background: white; border: 1px solid #6c757d; border-top: none;
                                       border-radius: 0 0 0.25rem 0.25rem; z-index: 1000;"
                            >
                                <div
                                    v-for="transcript in filteredTranscripts"
                                    v-bind:key="transcript"
                                    @mousedown="selectTranscript(transcript)"
                                    style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f0f0f0; user-select: none;"
                                    :style="{ backgroundColor: transcript === transcript_obj ? '#f0f0f0' : 'white' }"
                                    @mouseover="$event.currentTarget.style.backgroundColor = '#f0f0f0'"
                                    @mouseout="$event.currentTarget.style.backgroundColor = transcript === transcript_obj ? '#f0f0f0' : 'white'"
                                >
                                    {{ transcript }}
                                </div>
                            </div>
                        </div>

                        <!-- Toggle for highlighting selected RBP -->
                        <div v-if="transcript_obj && transcript_peaks" class="checkbox" style="margin-top: 10px;">
                            <label>
                                <input type="checkbox" v-model="highlightSelectedRBP" v-on:change="replotRBPProfile()">
                                Highlight selected RBP
                            </label>
                        </div>
                    </div>

                    <!-- Track view with cell line and RBP selection -->
                    <div v-if="transcript_view_mode=='track'">
                        <!-- Toggle between browse and search modes -->
                        <div id="track_search_mode" class="btn-group btn-group-toggle" data-toggle="buttons" style="margin-bottom: 15px;">
                            <label class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:49%;" for="browse_mode">
                                <input type="radio" id="browse_mode" value="browse" v-model="trackSearchMode">
                                Browse by Filters
                            </label>

                            <label class="btn btn-outline-dark" style="margin: 0 0 0 1%;width:49%;" for="search_mode">
                                <input type="radio" id="search_mode" value="search" v-model="trackSearchMode">
                                Direct Search
                            </label>
                        </div>

                        <!-- Direct Search Mode -->
                        <div v-if="trackSearchMode === 'search'">
                            <!-- Still need Cell Line and RBP Selection -->
                            <select class="btn btn-outline-dark dropdown-toggle" id="select_cell_line_search" v-model="selectedCellLine" @click.once="loadCellLines" v-on:change="loadTrackRbps(selectedCellLine)" style="margin: 0 1% 0 0;width:100%;">
                                <option :value="null" selected disabled hidden>Select Cell Line</option>
                                <option v-for="cellLine in cellLineList" v-bind:key="cellLine.id" :value="cellLine.id">{{ cellLine.name }}</option>
                            </select>

                            <p v-if="loadingCellLines" style="text-align: center;">Loading Cell Lines, please wait</p>

                            <br v-if="selectedCellLine">
                            <br v-if="selectedCellLine">

                            <!-- RBP Selection (only shown when cell line is selected) -->
                            <div v-if="selectedCellLine">
                                <select class="btn btn-outline-dark dropdown-toggle" id="select_track_rbp_search" v-model="selectedTrackRbp" style="margin: 0 1% 0 0;width:100%;">
                                    <option :value="null" selected disabled hidden>Select RBP</option>
                                    <option v-for="rbp in trackRbpList" v-bind:key="rbp.id" :value="rbp.id">{{ rbp.name }}</option>
                                </select>

                                <p v-if="loadingTrackRbps" style="text-align: center;">Loading RBPs, please wait</p>
                            </div>

                            <br v-if="selectedTrackRbp">
                            <br v-if="selectedTrackRbp">

                            <!-- Transcript Search (only available after cell line and RBP are selected) -->
                            <div v-if="selectedCellLine && selectedTrackRbp">
                                <div style="position: relative;">
                                    <input
                                        type="text"
                                        class="btn btn-outline-dark"
                                        v-model="trackSearchQuery"
                                        @input="searchTrackTranscripts"
                                        @focus="showTrackSearchDropdown = true"
                                        @blur="hideTrackSearchDropdown"
                                        placeholder="Search by internal ID (e.g., ENST00000...)..."
                                        style="margin: 0 1% 0 0; width:100%; text-align: left; cursor: text;"
                                    />

                                    <p v-if="loadingTrackSearch" style="text-align: center;">Searching, please wait...</p>

                                    <div
                                        v-if="showTrackSearchDropdown && filteredTrackResults && filteredTrackResults.length > 0"
                                        class="track-search-dropdown"
                                        style="position: absolute; top: 100%; left: 0; right: 1%; max-height: 300px; overflow-y: auto;
                                               background: white; border: 1px solid #6c757d; border-top: none;
                                               border-radius: 0 0 0.25rem 0.25rem; z-index: 1000;"
                                    >
                                        <div
                                            v-for="result in filteredTrackResults"
                                            v-bind:key="result.id"
                                            @mousedown="selectTrackSearchResult(result)"
                                            style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f0f0f0; user-select: none;"
                                            @mouseover="$event.currentTarget.style.backgroundColor = '#f0f0f0'"
                                            @mouseout="$event.currentTarget.style.backgroundColor = 'white'"
                                        >
                                            <div style="pointer-events: none;"><strong>{{ result.internal_id }}</strong></div>
                                            <div style="font-size: 0.9em; color: #666; pointer-events: none;">
                                                <span v-if="result.transcript_name !== result.internal_id">{{ result.transcript_name }} - </span>
                                                <span v-if="result.gene_name">{{ result.gene_name }} - </span>
                                                {{ result.type }}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <p v-else-if="!selectedCellLine" style="text-align: center; color: #666; margin-top: 10px;">
                                Please select a Cell Line first
                            </p>
                            <p v-else-if="!selectedTrackRbp" style="text-align: center; color: #666; margin-top: 10px;">
                                Please select an RBP to search transcripts
                            </p>
                        </div>

                        <!-- Browse Mode (existing filters) -->
                        <div v-if="trackSearchMode === 'browse'">
                            <!-- Cell Line Selection -->
                            <select class="btn btn-outline-dark dropdown-toggle" id="select_cell_line" v-model="selectedCellLine" @click.once="loadCellLines" v-on:change="loadTrackRbps(selectedCellLine)" style="margin: 0 1% 0 0;width:100%;">
                                <option :value="null" selected disabled hidden>Select Cell Line</option>
                                <option v-for="cellLine in cellLineList" v-bind:key="cellLine.id" :value="cellLine.id">{{ cellLine.name }}</option>
                            </select>

                            <p v-if="loadingCellLines" style="text-align: center;">Loading Cell Lines, please wait</p>

                            <br>
                            <br>

                        <!-- RBP Selection (only shown when cell line is selected) -->
                        <div v-if="selectedCellLine">
                            <select class="btn btn-outline-dark dropdown-toggle" id="select_track_rbp" v-model="selectedTrackRbp" style="margin: 0 1% 0 0;width:100%;">
                                <option :value="null" selected disabled hidden>Select RBP</option>
                                <option v-for="rbp in trackRbpList" v-bind:key="rbp.id" :value="rbp.id">{{ rbp.name }}</option>
                            </select>
                            
                            <p v-if="loadingTrackRbps" style="text-align: center;">Loading RBPs, please wait</p>
                        </div>
                        
                        <br v-if="selectedTrackRbp">
                        
                        <!-- Schema Types Selection - only shown when RBP is selected -->
                        <div v-if="selectedTrackRbp">
                            <select class="btn btn-outline-dark dropdown-toggle" id="select_schema_type" v-model="selectedSchemaType" @click.once="loadSchemaTypes" v-on:change="loadGeneNames(selectedSchemaType)" style="margin: 0 1% 0 0;width:100%;">
                                <option :value="null" selected disabled hidden>Select Schema Type</option>
                                <option v-for="type in schemaTypes" v-bind:key="type" :value="type">{{ type }}</option>
                            </select>
                            
                            <p v-if="loadingSchemaTypes" style="text-align: center;">Loading Schema Types, please wait</p>
                        </div>
                        
                        <br v-if="selectedSchemaType">
                        
                        <!-- Gene Names Selection -->
                        <div v-if="selectedSchemaType">
                            <select class="btn btn-outline-dark dropdown-toggle" id="select_gene_name" v-model="selectedGeneName" v-on:change="loadSchemaTranscripts(selectedSchemaType, selectedGeneName)" style="margin: 0 1% 0 0;width:100%;">
                                <option :value="null" selected disabled hidden>Select Gene</option>
                                <option v-for="gene in geneNames" v-bind:key="gene" :value="gene">{{ gene }}</option>
                            </select>
                            
                            <p v-if="loadingGeneNames" style="text-align: center;">Loading Gene Names, please wait</p>
                        </div>
                        
                        <br v-if="selectedGeneName">
                        
                        <!-- Transcripts Selection -->
                        <div v-if="selectedGeneName">
                            <select class="btn btn-outline-dark dropdown-toggle" id="select_transcript" v-model="selectedTranscript" v-on:change="loadTrackData" style="margin: 0 1% 0 0;width:100%;">
                                <option :value="null" selected disabled hidden>Select Transcript</option>
                                <option v-for="transcript in transcripts" v-bind:key="transcript.id" :value="transcript.id">{{ transcript.name }}</option>
                            </select>
                            
                            <p v-if="loadingTranscripts" style="text-align: center;">Loading Transcripts, please wait</p>
                        </div>

                        <!-- Track Data Loading Status -->
                        <div v-if="selectedTranscript">
                            <p v-if="loadingTrackData" style="text-align: center;">Loading Track Data, please wait</p>
                            <p v-if="!loadingTrackData && trackDataMessage" style="text-align: center;">{{ trackDataMessage }}</p>
                        </div>
                        </div>  <!-- End of browse mode -->

                        <!-- Track Data Status for Search Mode -->
                        <div v-if="trackSearchMode === 'search' && selectedTranscript">
                            <p v-if="loadingTrackData" style="text-align: center;">Loading Track Data, please wait</p>
                            <p v-if="!loadingTrackData && trackDataMessage" style="text-align: center;">{{ trackDataMessage }}</p>
                        </div>
                    </div>
                </p>
            </div>
            
            <!--
            <div v-else>
                Select an alignment file:
                <p><input id="inputUploadFasta" class="btn btn-outline-dark" type = "file" accept=".fasta,.fas,.fa" ref="custom_aln_file" v-on:change="handleFileUpload()"/></p>
                <p><button id="uploadShowFasta" class="btn btn-outline-dark" v-on:click="submitCustomAlignment()" v-if="file&&type_tree=='upload'">Upload the alignment</button></p>
                <p><button id="downloadExampleFasta" class="btn btn-outline-dark" v-on:click="getExampleFile(`static/alignments/EFTU_example.fas`, `PVExampleAlignment.fas`)" v-if="!file&&type_tree=='upload'">Download example alignment</button></p>
            </div>
            ––>

            <p>
                <select class="btn btn-outline-dark dropdown-toggle" id="select_protein_type" v-if="tax_id" v-model="protein_type_obj" v-on:change="loadData(tax_id, type_tree)" style="margin: 0 1% 0 0;width:100%;">
                    <option :value="null" selected disabled hidden>Select RNA type</option>
                    <option v-for="proteinType in proteinTypes" v-bind:key="proteinType">{{ proteinType }}</option>
                </select>
            </p>
            
            <p>
                <select class="btn btn-outline-dark dropdown-toggle" id="selectaln" v-if="protein_type_obj && tax_id" v-model="alnobj" v-on:change="handleAlignChange()">
                    <option :value="null" selected disabled hidden>Select an alignment</option>
                    <option v-for="aln in alignments" v-bind:key = aln.txt v-bind:value="{ id: aln.value, text: aln.text }">{{ aln.text }}</option>
                </select>
            </p>
                <!--<span v-if="alnobj">Select/type PDB entry:</span>-->
                <div v-if="alnobj&&alnobj=='custom'&&file&&type_tree=='upload'">
                    <b>Select a format for 3D structure:</b>
                    <br/>
                    <input type="radio" id="radioCIF" name="CIF/PDB mode" value="CIF" v-model="cifPdbMode">CIF</input>
                    <input type="radio" id="radioPDB" name="CIF/PDB mode" value="PDB" v-model="cifPdbMode">PDB</input>
                    <br/>
                    <div v-if="cifPdbMode=='CIF'">
    
                        Upload a custom CIF:
                        <br/>
                        <label for="uploadCustomCIF" id="cif-upload" class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:100%;">Choose File</label>
                        <input id="uploadCustomCIF" class="btn btn-outline-dark" type="file" accept=".cif" ref="customCIFfile" v-on:change="cifFileUploadedFlag=true;" style="margin: 0 1% 0 0;width:100%;"/>
                        <div v-if="cifFileUploadedFlag">
                            <label for="provideEntityID" style="margin: 0 1% 0 0;width:100%;">Provide an Entity ID for a desired RNA chain</label>
                            <input id="provideEntityID" class="btn btn-outline-dark" type="number" ref="entity_id" v-on:change="uploadCustomCIF();" placeholder="Entity ID" style="margin: 0 1% 0 0;width:100%;"/>
                        </div>
                    </div>
                    <div v-if="cifPdbMode=='PDB'"> 
                        Upload a custom PDB:
                        <br/>
                        <label for="uploadCustomPDB" id="pdb-upload" class="btn btn-outline-dark">Choose File</label>
                        <input id="uploadCustomPDB" class="btn btn-outline-dark" type="file" accept=".pdb" ref="customPDBfile" v-on:change="pdbFileUploadedFlag = true;"/>
                        <div v-if="pdbFileUploadedFlag">
                            Upload the matching RNA sequence:
                            <br/>
                            <label for="uploadCustomFullSequence" id="full-sequence-upload" class="btn btn-outline-dark" style="margin: 0 1% 0 0;width:100%;">Choose File</label>
                            <input id="uploadCustomFullSequence" class="btn btn-outline-dark" type="file" accept=".fas,.fasta,.fa" ref="customFullSequence" v-on:change="uploadCustomFullSequence();" style="margin: 0 1% 0 0;width:100%;"/>
                        </div>
                    </div>


                </div>
                <!--
                <span v-if="alnobj">Select/type PDB entry:</span>
                <!--<select class="btn btn-outline-dark dropdown-toggle" id="pdb_input" v-if="alnobj&&alnobj!='custom'" v-model="pdbid">
                    <option :value="null" selected disabled hidden>Select PDB entry</option>
                    <option v-for="pdb in pdbs" v-bind:value="pdb.id">{{pdb.name}}</option>
                </select>
                <autocomplete isAsync:true :items="blastPDBresult" v-if="alnobj&&alnobj=='custom'" v-model="pdbid"></autocomplete>
                -->
                <p>
                <span v-if="alnobj&&alnobj!='custom'">Select/type PDB entry:</span>    
                <autocomplete id="pdb_input" isAsync:true :items="pdbs" v-if="alnobj&&alnobj!='custom'" v-model="pdbid"></autocomplete>
                </p>
                <!--
                <div id="blastingPDBsMSG" v-if="alnobj&&alnobj=='custom'&&fetchingPDBwithCustomAln&&fetchingPDBwithCustomAln==true">
                    <b>BLASTing first alignment sequence against PDB sequences</b>
                    <img src="static/img/loading.gif" alt="BLASTing available PDBs" style="height:25px;">
                </div>
                <div id="blastedPDBsNoneMSG" v-if="alnobj&&alnobj=='custom'&&fetchingPDBwithCustomAln&&fetchingPDBwithCustomAln=='none'">
                    <b>BLAST didn't match any PDBs!<br>You can still type in any PDB.</b>
                </div>
                <div id="blastedPDBsNoneMSG" v-if="alnobj&&alnobj=='custom'&&fetchingPDBwithCustomAln&&fetchingPDBwithCustomAln=='error'">
                    <b>BLAST error! Please try different alignment or refreshing the page!</b>
                </div>
                <span id="completeBLASTsMSG" v-if="alnobj&&alnobj=='custom'&&fetchingPDBwithCustomAln=='complete'"><b>Completed BLAST for similar PDBs.</b></span>
                <div v-if="hide_chains" id="onFailedChains">Looking for available polymers <img src='static/img/loading.gif' alt='Searching available polymers' style='height:25px;'></div>
                </p>-->
            <p><select multiple class="form-control btn-outline-dark" id="polymerSelect" v-bind:style="{ resize: 'both'}"  v-if="alnobj&&chains&&fasta_data&&pdbid||uploadSession" v-model="chainid" >
                <option :value ="null" selected disabled>Matching RNA chain to visualize:</option>
                <option v-for="chain in chains" v-bind:key="chain.value" v-bind:value="chain.value" @click="selectedProteins = []; postStructureData(pdbid, chainid); calculateProteinContacts(pdbid, chainid); populateECODranges(pdbid, chainid); showPDBViewer(pdbid, chainid, guideOff ? chain.entityID : RVGuideEntityId);">{{ chain.text }}</option>
                <!-- <option v-for="chain in chains" v-bind:key="chain.value" v-bind:value="chain.value" @click="postStructureData(pdbid, chainid); calculateProteinContacts(pdbid, chainid); populateECODranges(pdbid, chainid); showPDBViewer(pdbid, chainid, chain.entityID);">{{ chain.text }}</option> -->
            </select></p>
            <!-- 
            -->
            <!-- 
            -->
            <div v-if="structure_mapping&&chains&& !pdbcust && !cifcust">
                <select id="downloadDataBtn" class="btn btn-outline-dark dropdown-toggle" v-model="downloadMapDataOpt" v-if="topology_loaded">
                    <option :value="null" selected disabled>Download mapped data</option>
                    <option value='csv'>As CSV file</option>
                    <option value='pymol'>As PyMOL script</option>
                </select>
            </div>
            <div v-if="structure_mapping&& (pdbcust || cifcust) ">
                <select id="downloadDataBtn" class="btn btn-outline-dark dropdown-toggle" v-model="downloadMapDataOpt" v-if="topology_loaded">
                    <option :value="null" selected disabled>Download mapped data</option>
                    <option value='csv'>As CSV file</option>
                    <option value='pymol_custom'>As PyMOL script</option>
                </select>
            </div>
            <p><div v-if="topology_loaded&&type_tree=='orth'" class="checkbox" id="showRNAcontext">
                <label><input type="checkbox" v-model="checkedRNA" v-on:change="updateMolStarWithRibosome(checkedRNA)">
                    Show ribosomal context in 3D</label>
            </div></p>
            <div v-if="modified&&cifcust&&structure_mapping">
                <form @submit.prevent="submitModificationsCustom">
                    <label>Select modified residues to highlight</label>
                    <div
                    id="modSelectCustom"
                    class="selection-box"
                    :style="{ backgroundColor: 'white', padding: '10px', border: '1px solid #ddd', marginBottom: '10px', maxHeight: '100px', overflowY: 'auto' }"
                    >
                    
                    <div>
                        <input
                            type="checkbox"
                            id="selectAllModifiedCustom"
                            v-model="selectAllModifiedCustomChecked"
                            @change="selectAllModifiedCustomChanged"
                        />
                        <label for="selectAllModifiedCustom">Select All</label>
                        </div>
                        <div v-for="[text, k] of modified_residues.entries()" :key="k">
                        <input
                            type="checkbox"
                            :id="text"
                            :value="text"
                            v-model="selectedResiduesCustom"
                        />
                        <label :for="text">{{ text }}</label>
                        </div>
                    
                    </div>

                    <button type="submit">Submit Residues</button>
                </form>
            </div>
            
            <!--

            <div v-if="structure_mapping&&cifcust">
            <p><select multiple class="form-control btn-outline-dark" id="polymerSelect3" v-bind:style="{ resize: 'both'}" v-model="modifications" v-if="modified">
                <label>Select modified residues to highlight</label>
                <option :value ="null" selected disabled>Select modified residues to highlight</option>
                <option v-for="[text, k] of modified_residues.entries()" v-bind:value="text" v-bind:key="k" @click="showModificationsCustom();">{{ text }}</option>
                </select></p>
            </div>
            -->
            <!--
            -->
            <!--
            <div v-if="topology_loaded&&!checkedRNA&&!customPDBid&&protein_contacts">
             -->
            <div v-if="topology_loaded&&!checkedRNA">
            
            <!--
                <div id="domainSelectionSection" style="margin: 3% 0;">
                    <div>
                        <label><input type="radio" v-model="domain_or_selection" value="domain">
                        Select by ECOD domain</label>
                    </div>
                    <div v-if="selected_domain.length > 0" style="text-align: center;">
                        <a :href="'http://prodata.swmed.edu/ecod/complete/domain/' + selected_domain[0].id" target="_blank">See {{selected_domain[0].id}} on ECOD</a>
                    </div>
                    <select multiple class="form-control btn-outline-dark" id="domainSelect" v-model="selected_domain" v-bind:style="{ resize: 'both'}" style="margin: 1.5% 0;" v-if="domain_list&&checked_domain">
                        <option v-for="domain in domain_list" v-bind:value="domain">{{ domain.name }}</option>
                    </select>
                    <button id="disableDomainTruncation" class="btn btn-outline-dark" v-if="selected_domain.length > 0" type="button" v-on:click="domain_or_selection=null;" style="margin: 1.5% 0;">
                            Show the entire structure
                    </button>
                </div>
            -->
            <!--    <div id="filterSection"><p>
                    <div>
                        <label><input type="radio" v-model="domain_or_selection" value="selection">
                        Select custom range</label>
                    </div>
                    <span v-if="checked_selection"><b>Input single</b> residue range to <b>show</b>, ending with semicolon. <br> For example: 1-80;</span>
                    <input class="input-group-text" v-if="checked_selection" v-model="filter_range" v-on:input="handleFilterRange(filter_range)">
                    <p><button id="disableCutTruncation" class="btn btn-outline-dark" v-if="filter_range" type="button" v-on:click="domain_or_selection=null;" style="margin: 3% 0;">
                        Show the entire structure
                    </button></p>
                </p></div> -->
            
                <div id="maskingSection"><p>
                    <div class="checkbox">
                        <label><input type="checkbox" v-model="checked_filter" v-on:change="cleanFilter(checked_filter, masking_range)">
                        Highlight region</label>
                    </div>
                    <span v-if="checked_filter"><b>Input multiple</b> residue ranges to <b>show</b>, separated by semicolon. <br> For example: 1-80;91-111;</span>
                    <input class="input-group-text" v-if="checked_filter" v-model="masking_range" v-on:input="handleMaskingRanges(masking_range)">
                </p></div>
                <p v-if="correct_mask!=true&&masking_range!=null">Incorrect range syntax!</p>

                       
                <div id="customDataSection">
                <p><div class="checkbox">
                        <label><input type="checkbox" id="uploadCustomData"  v-model="checked_customMap" v-on:change="cleanCustomMap(checked_customMap)">
                        Upload custom mapping data</label>
                        <p><input class="btn btn-outline-dark" id="inputUploadCSV" v-if="checked_customMap" type="file" accept=".csv" ref="custom_csv_file" v-on:change="handleCustomMappingData()"/></p>
                        <p v-if="raiseCustomCSVWarn" v-html="raiseCustomCSVWarn"></p>
                        <p><button class="btn btn-outline-dark" id="downloadExampleCSV" v-if="checked_customMap&&csv_data==null" type="button" v-on:click="getExampleFile(`static/alignments/rv3_example_cusom_mapping.csv`, `RVExampleCustomMapping.csv`)">
                        Download example mapping data
                        </button></p>
                    </div>
                </p></div>
                <!--<div v-if="topology_loaded&&protein_contacts">
                    <p><select multiple class="form-control btn-outline-dark" id="polymerSelect2" v-bind:style="{ resize: 'both'}" v-model="pchainid">
                    <label>Select RNA-protein contacts to view in 3D</label>
                    <option :value ="null" selected disabled>Select RNA-protein contacts to view in 3D</option>
                    <option v-for="chain in protein_chains" v-bind:value="chain.value" v-bind:key="chain.key" v-bind:id="chain.value" @click="showContacts();">{{ chain.banname}}</option>
                    </select></p>
                </div>-->
                
  <div v-if="topology_loaded && protein_contacts">
    <form @submit.prevent="submitProteins">
      <label>Select RNA-protein contacts to view in 3D</label>
      <div
        id="proteinSelect"
        class="selection-box"
        :style="{ backgroundColor: 'white', padding: '10px', border: '1px solid #ddd', marginBottom: '10px', maxHeight: '100px', overflowY: 'auto' }"
      >
        <div>
          <input
            type="checkbox"
            id="selectAllProteins"
            v-model="selectAllProteinsChecked"
            @change="selectAllProteinsChanged"
          />
          <label for="selectAllProteins">Select All</label>
        </div>
        <div v-for="chain in protein_chains" :key="chain.key">
          <input
            type="checkbox"
            :id="chain.value"
            :value="chain.value"
            v-model="selectedProteins"
          />
          <label :for="chain.value">{{ chain.banname }}</label>
        </div>
      </div>

      <button type="submit">Submit Proteins</button>
    </form>
  </div>


              <!--  <div v-if="!cifcust">
                <p><select multiple class="form-control btn-outline-dark" id="polymerSelect3" v-bind:style="{ resize: 'both'}" v-model="modifications" v-if="modified">
                <label>Select modified residues to highlight</label>
                <option :value ="null" selected disabled>Select modified residues to highlight</option>
                <option v-for="[text, k] of modified_residues.entries()" v-bind:value="text" v-bind:key="k" @click="showModifications();">{{ text }}</option>
                </select></p>
                </div>
             -->

    <div v-if="modified&&!cifcust">
  <form @submit.prevent="submitModifications">
    <label>Select modified residues to highlight</label>
    <div
      id="modSelect"
      class="selection-box"
      :style="{ backgroundColor: 'white', padding: '10px', border: '1px solid #ddd', marginBottom: '10px', maxHeight: '100px', overflowY: 'auto' }"
    >
      
      <div>
          <input
            type="checkbox"
            id="selectAllModified"
            v-model="selectAllModifiedChecked"
            @change="selectAllModifiedChanged"
          />
          <label for="selectAllModified">Select All</label>
        </div>
        <div v-for="[text, k] of modified_residues.entries()" :key="k">
          <input
            type="checkbox"
            :id="text"
            :value="text"
            v-model="selectedResidues"
          />
          <label :for="text">{{ text }}</label>
        </div>
      
    </div>

    <button type="submit">Submit Residues</button>
  </form>
</div>
  </div>
            <!--
            <p><div v-if="alnobj" class="checkbox" id="showFrequencies">
                <label><input type="checkbox" v-model="checked_propensities" v-on:change="handlePropensities(checked_propensities)">
                Show amino acid frequencies</label>
                <select class="btn btn-outline-dark dropdown-toggle" id="propensitiesSubstructure" v-if="checked_propensities&&structure_mapping" v-model="property" v-on:change="getPropensities(property); handlePropensities(checked_propensities)">
                    <option :value="null" selected disabled hidden>Select secondary structure</option>
                    <option :value="0">All residues</option>
                    <option v-for="substructure in substructures" v-bind:value="{ id: substructure.value, text: substructure.text, indices: substructure.indices }">{{ substructure.text }}</option>
                </select>
                <p><button id="downloadFreqsBtn" class="btn btn-outline-dark" style="margin: 3% 0;" v-if="checked_propensities" type="button" v-on:click="downloadFreqsData()">
                    Download AA frequencies
                </button></p>
            </div></p>
            -->
        </div>

        <div class="alignment_section">
            
            <div id="rbp_profile" v-if="(peaks_present == true && selected_viewer=='transcript') || trackData">  </div>

            <p v-else-if="peaks_present == false && selected_viewer =='transcript'"> No Peaks Present </p>

            <div id="igvdiv" class="igvbrowser">   </div>

            
            <!-- Debug for viewing raw peak data
            <p v-if="transcript_obj && transcript_peaks">
            {{ transcript_peaks}}
            </p>
            -->


            <div id="alnif" v-if="alnobj">
                <div id="alnMenu" style="display: flex;">
                    <button id="downloadFastaBtn" class="btn btn-outline-dark" style="margin: 0 1%;" v-if="msavWillMount" type="button" v-on:click="downloadAlignmentData()">
                        Download alignment
                    </button>
                    <select id="cdHITResults" class="btn btn-outline-dark dropdown-toggle" style="margin: 0 1%;" v-model="cdhitSelectedOpt" v-if="cdHITReport">
                        <option :value="null" selected disabled>See cdhit options</option>
                        <option v-for="prop in cdhitOpts" :value="prop.value" :key="prop.Name">{{ prop.Name }}</option>
                    </select>
                    <select id="downloadAlnImageBtn" class="btn btn-outline-dark dropdown-toggle" style="margin: 0 1%;" v-model="downloadAlignmentOpt" v-if="msavWillMount">
                        <option :value="null" selected disabled>Download alignment image</option>
                        <option value='full'>Full alignment</option>
                        <option value='visible'>Visible alignment</option>
                    </select>
                    <select id="selectColorMappingProps" class="btn btn-outline-dark dropdown-toggle" style="margin: 0 1%;" v-model="selected_property" v-if="msavWillMount">
                        <option :value="null" selected disabled>Select data</option>
                        <option value="Clear data">Clear data</option>
                        <option value="Select data">Contacts</option>
                        <option v-for="prop in available_properties" :key="prop.Name">{{ prop.Name }}</option>
                    </select>
                    <select id="selectAlnColorScheme" class="btn btn-outline-dark dropdown-toggle" style="margin: 0 1%;" v-model="colorScheme" v-if="msavWillMount">
                        <option :value="null" selected disabled>Select a colorscheme</option>
                        <option v-for="colorscheme in availColorschemes" :key="colorscheme">{{ colorscheme }}</option>
                    </select>
                </div>
                <div id="alnDiv">Loading alignment <img src="static/img/loading.gif" alt="Loading alignment" style="height:25px;"></div>
            </div>
        </div>
        <div class="warningSection">
            <div id="warningCDHITtruncation" v-if="cdHITReport&&didCDHit_truncate" >
                <b>Warning, your alignment sequences were clustered by cdhit! See dropdown menu above the alignment for options.<br/>
                Original alignment had {{this.cdHITnums[0]}} sequences, which were clustered in {{this.cdHITnums[1]}} groups using threshold of 90% identity.</b>
            </div>
            <!-- <div id="warningPoorStructureAln" v-if="poor_structure_map&&poor_structure_map<60" >
                <b>No Warning, probably "good alignment" between the structure and sequences!!!<br/>
                Found {{poor_structure_map}} poorly aligned residues.
                Proceed with caution or try a different structure.</b>
            </div> -->
            <div id="warningPoorStructureAln" v-if="poor_structure_map&&poor_structure_map>=60" >
                <b>Warning, poor alignment between selected MSA and structure!!!
                    Found {{poor_structure_map}} poorly aligned residues. Consider selecting a new MSA/structure pair.
                </b>
            </div>

        </div>
        <div class="topology_section">
            <span id="topif" v-if="chainid.length>0||customPDBsuccess">
                <div v-if="!topology_loaded">
                    Wait for alignment-structure mapping <img src="static/img/loading.gif" alt="Loading topology viewer" style="height:25px;">
                </div>
                <div id="topview"></div>
            </span>
        </div>
        <div class = "gradient_section" v-if = "topology_loaded">
            <img id = 'gradientSVG' 
                v-for="prop in available_properties" 
                :key="prop.Name"
                v-if = "selected_property == prop.Name"
                :src="prop.url"
            ><!--
            <object id="gradientSVG"
                v-for="prop in available_properties" 
                v-if = "selected_property == prop.Name"
                :data="prop.url" type="image/svg+xml">
            </object>-->
        </div>
        <div class="molstar_section">
            <div v-if="PDBparsing==true">
                Parsing PDB structure <img src="static/img/loading.gif" alt="Parsing PDB structure" style="height:25px;">
            </div>
            <div v-if="PDBparsing=='error'">
                Failed to parse the PDB structure! Try a different structure.
            </div>
            <span id="molif" v-if="chainid.length>0||customPDBsuccess">
                <div id ="pdbeMolstarView">
                    Loading Molstar Component <img src="static/img/loading.gif" alt="Loading MolStar" style="height:25px;">
                </div>
            </span>
        </div>
        <!--
        <div class = "propensity_section">
            <span id="propif" v-if="checked_propensities">
                <div id = "total"></div>
            </span>
        </div>
        -->
        <footer>
            <div id="footerDiv" style="display: flex;"></div>
        </footer>
    </div>
</template>


<script>
  import {uploadCustomFullSequence} from './handleUploadCustomFullSequence.js'
  import schemes from './msaColorSchemes/index.js'
  import {ajaxProper} from './ajaxProper.js'
  import {addFooterImages} from './Footer.js'
  import {initialState} from './DropDownTreeVars.js'
  import {filterAvailablePolymers} from './filterRiboChains.js'
  import {parseRNAchains} from './handleRNAchains.js'
  import {generateChainsFromLiteMol} from './handleChainData.js'
  import {colorByMSAColorScheme} from './handleMSAbasedColoring.js'
  import {getStructMappingAndTWC} from './getStructMappingAndTWC.js'
  import {loadAlignmentViewer} from './loadAlignmentViewer.js'
  import {customCSVhandler} from './handleCSVdata.js'
  import {AlnViewer} from './AlignmentViewer.js'
  import {updateProperty} from './handleCSVdata.js'
  import {populatePDBsFromCustomAln} from './populatePDBsFromCustomAln.js'
  import {populateECODranges} from './populateECODranges.js'
  import {postCIFdata} from './postCustomStruct.js'
  //import {uploadCustomPDB} from './handleUploadPDB_RNA.js'
  import {uploadCustomPDB} from './handleUploadPDB_RNA.js'
  import {uploadCustomCIF} from "./handleUploadCIF_RNA.js"
  import {loadViewersWithCustomUploadStructure} from './handleViewersWithUploadPDB.js'
  import ReactDOM, { render } from 'react-dom';
  import React, { Component } from "react";
  import Treeselect from '@riophae/vue-treeselect'
  import Autocomplete from './Autocomplete.vue'
  import { intersection } from 'lodash';
  import {downloadPyMOLscript} from './handlePyMOLrequest.js'
  import {downloadPyMOLcustomscript} from './handlePyMOLcustomrequest.js'
  //import {parseRNAchains} from './handleRNAchains.js'

 
   export default {
      // register the component
      components: { Treeselect, Autocomplete },
      data: function () {
        return initialState();
      },
      
      watch: {
        type_tree: function (type_tree){
            if (this.type_tree == "orth"){
                document.getElementById('tree_type').children[0].click();
            }else if (this.type_tree == "upload"){
                document.getElementById('tree_type').children[1].click();
            }
        },csv_data: function(csv_data){
            customCSVhandler(csv_data);
        },alnobj: function (data){
            if (!data){return;}
            if (data == "custom"){
                this.showAlignment(null, null, vm.type_tree);
            }else{
                this.populatePDBs(data);
                this.showAlignment(data.id, vm.tax_id, vm.type_tree);
            }
        },pdbid: function (pdbid){
            if (!pdbid){return;}
            if (vm.type_tree == "upload"){
                this.getPDBchains(pdbid, null);
            }else{
                this.getPDBchains(pdbid, vm.alnobj.id);
            }
        },cif_file_path: function(cif_file_path){
            this.calculateModifiedCustom(vm.customEntity, cif_file_path);
        },
        
        unfilteredChains: function(chain_list){
            if (!chain_list){return;}
            if (this.type_tree == "para") {aln_id = aln_id.split(',')[1]}
            if (this.type_tree != "upload") {
                //parseRNAchains(chain_list);
                filterAvailablePolymers(chain_list, this.alnobj.id, this);
            } else if (vm.blastMAPresult == null){
                let chain_options = []
                for (let i = 0; i < chain_list.length; i++) {
                    let chain_listI = chain_list[i]
                    if (chain_listI["molecule_type"].toLowerCase() == "bound") {continue;}
                    if (chain_listI["molecule_type"].toLowerCase() == "water") {continue;}
                    if (typeof(chain_listI.source[0]) === "undefined") {continue;}
                    chain_options = pushChainData(chain_options, chain_listI);
                }
                if (chain_options.length === 0) {
                    chain_options.push({text: "Couldn't find polymers from this structure!", value: null})
                }
                vm.chains = chain_options;
                this.hide_chains = null;
            } else {
                let chain_options = [];
                var chainsFromBlast = vm.blastMAPresult.get(this.pdbid);
                for (let i = 0; i < chain_list.length; i++) {
                    let chain_listI = chain_list[i]
                    if (chain_listI["molecule_type"].toLowerCase() == "bound") {continue;}
                    if (chain_listI["molecule_type"].toLowerCase() == "water") {continue;}
                    if (typeof(chain_listI.source[0]) === "undefined") {continue;}
                    if (!chainsFromBlast){
                        chain_options = pushChainData(chain_options, chain_listI);
                    } else {
                        let intersectedChains = _.intersection(chainsFromBlast, chain_listI["in_chains"]);
                        intersectedChains.forEach(function(chainVal){
                            chain_options.push({
                                text: `${chainVal} ${chain_listI["molecule_name"][0]}`,
                                value: chainVal,
                                sequence: chain_listI["sequence"],
                                entityID: chain_listI["entity_id"],
                                startIndex: chain_listI.source[0].mappings[0].start.residue_number,
                                endIndex: chain_listI.source[0].mappings[0].end.residue_number
                            });
                        });
                    }
                }
                if (chain_options.length === 0) {
                    chain_options.push({text: "Couldn't find polymers from this structure!", value: null})
                }
                vm.chains = chain_options;
                this.hide_chains = null;
            }
        },colorScheme: function (scheme){
            if (window.PVAlnViewer){
                window.PVAlnViewer.setState({colorScheme:scheme});
            }
            if (this.topology_loaded == true){
                colorByMSAColorScheme(scheme, this);
            }
        },postedPDBEntities: function (successPost){
            if (successPost){
                this.showTopologyViewer(this.pdbid, this.chainid, this.fasta_data);
            } else {
                const topview_item = document.getElementById("topview");
                if (topview_item) {topview_item.remove(); create_deleted_element("topif", "topview", "Loading Structure Data ", true)}
            }
        },customPDBsuccess:function(successPost){
            if (successPost){
                this.$nextTick(function(){
                    loadViewersWithCustomUploadStructure();
                })
            }
        },topology_loaded: function(topology_loaded){
            if (window.tempCSVdata!= null && this.topology_loaded){
                vm.csv_data = window.tempCSVdata;
                window.tempCSVdata = null;
                customCSVhandler(vm.csv_data);
            }
            if (this.selected_property){
                this.$nextTick(function(){
                    recolorTopStar(this.selected_property);
                });
            }
        },downloadAlignmentOpt: function(opt){
            if (this.uploadSession){return;}
            else if (opt == 'visible'){
                downloadAlignmentImage();
            } else if (opt == 'full'){
                downloadFullAlignmentImage();
            }
            this.downloadAlignmentOpt = null;
        },downloadMapDataOpt: function(opt){
            if (this.uploadSession){return;}
            else if (opt == 'csv'){
                downloadCSVData();
                this.downloadMapDataOpt = null;
            } else if (opt == 'pymol'){
                downloadPyMOLscript();
                this.downloadMapDataOpt = null;
            } else if (opt == 'pymol_custom'){
                downloadPyMOLcustomscript();
                this.downloadMapDataOpt = null;
            }
        },domain_or_selection: function(selection){
            if (this.uploadSession){return;}
            this.checked_filter = false;
            cleanFilter(this.checked_filter, this.masking_range);
            this.masking_range = null;
            if (selection == 'domain'){
                if (vm.checked_selection){
                    cleanSelection(false, vm.filter_range);
                    vm.checked_selection = false;
                }
                vm.checked_domain = true;
                if (vm.filter_range){
                    vm.filter_range = null;
                }
            } else if (selection == 'selection'){
                if (vm.checked_domain){
                    cleanSelection(false, true)
                    vm.checked_domain = false;
                }
                vm.checked_selection = true;
                if (vm.selected_domain.length > 0){
                    vm.selected_domain = [];
                }
            } else {
                if (vm.selected_domain.length > 0){
                    vm.selected_domain = [];
                }
                vm.filter_range = null;
                vm.checked_selection = false;
                vm.checked_domain = false;
                cleanSelection(false, true);
            }
            if (vm.selected_property){
                recolorTopStar(vm.selected_property);
            }
        },selected_domain: function (domainObj){
            if(domainObj.length == 0){return}
            handleDomainRange(domainObj[0].range);
        },selected_property: function(name){
            
            if (this.uploadSession){return;}
            if (!name){return;}
            if(this.colorSchemeData){this.colorSchemeData = null;}
            var updatedBarColors = [];
            if(name == "Select data" || name == "Clear data") {
                window.aaFreqs.forEach(function(){
                        updatedBarColors.push("#808080")
                    });
            } else {
                const constants = aaPropertyConstants.get(name);
                let min = Math.min(...constants);
                let max = Math.max(...constants);
                let colormapArray = aaColorData.get(name);
                let propData = this.aa_properties.get(name);
                var separatedData = [];
                if (this.aa_properties.has(name)){
                    propData.forEach(function(data, index){
                        separatedData.push([index+1, Number(math.sum(data).toFixed(2))]);
                    })
                } else if (name == 'TwinCons'){
                    separatedData = this.unmappedTWCdata;
                // } else if (name == 'Associated Data1'){
                //     console.log('AD_name', name);
                //     if (this.aa_properties.has(name)){
                //     console.log('Prop_Data', propData);

                //     }

                //     separatedData.push([1,1]);
                //     separatedData.push([2,2]);
                //     separatedData.push([3,4]);
                //     separatedData.push([4,6]);
                //     separatedData.push([5,10]);
// 
                } else {
                    //assume custom data
                    //console.log('CD_name', name);
                    if (this.structure_mapping && window.custom_prop){
                        var customProp = window.custom_prop.get(name);
                        window.aaFreqs.forEach(function(aaFr, alnIx){
                            
                            var strucIx = vm.structure_mapping[alnIx+1];
                            
                            if (strucIx && customProp[strucIx-1]){
                                customProp.forEach(function(customData){
                                    if (customData[0] == strucIx){
                                        separatedData.push([alnIx+1, Number(customData[1])]);
                                    }
                                });
                            } else {
                                separatedData.push([alnIx+1, NaN]);
                            }
                        });
                    }
                }
                const [rgbMap, MappingData] = parsePVData(separatedData, min, max, colormapArray);
                rgbMap.forEach(function (data){
                    updatedBarColors.push(rgbToHex(...data[0]))
                })
            }
            window.barColors = updatedBarColors;
            var alnDiv = document.querySelector('#alnDiv');
            window.msaOptions.colorScheme = this.colorScheme;
            this.aaPos = window.PVAlnViewer.state.aaPos;
            this.seqPos = window.PVAlnViewer.state.seqPos;
            ReactDOM.unmountComponentAtNode(alnDiv);
            this.msavWillMount = null;
            this.$nextTick(function(){
                //const root = ReactDOM.createRoot(alnDiv)
                //root.render(<AlnViewer ref={(PVAlnViewer) => {window.PVAlnViewer = PVAlnViewer}}/>)
                ReactDOM.render(
                    <AlnViewer ref={(PVAlnViewer) => {window.PVAlnViewer = PVAlnViewer}}/>, alnDiv
                );
            });
            if (this.topology_loaded){
                recolorTopStar(name);
            }
        },cdhitSelectedOpt: function(opt){
            if (opt=="untrunc"){
                this.cdhitOpts = this.cdhitOpts.filter(function( obj ) {
                    return obj.value !== 'untrunc';
                });
                if (this.cdhitOpts.filter(e => e.value === 'trunc').length === 0) {
                    this.cdhitOpts.push({Name:'Reload truncated alignment', value:'trunc'});
                }
                cleanupOnNewAlignment(vm, "Loading alignment...");
                vm.showAlignment(null, null, "upload");
                vm.didCDHit_truncate = false;
            }
            if (opt=="trunc"){
                this.cdhitOpts = this.cdhitOpts.filter(function( obj ) {
                    return obj.value !== 'trunc';
                });
                if (this.cdhitOpts.filter(e => e.value === 'untrunc').length === 0) {
                    this.cdhitOpts.push({Name:'Reload original alignment', value:'untrunc'})
                }
                cleanupOnNewAlignment(vm, "Loading alignment...");
                vm.showAlignment(null, null, "upload");
                vm.didCDHit_truncate = true;
            }
            if (opt=="download"){
                let [month, date, year] = new Date().toLocaleDateString("en-US").split("/");
                let anchor = document.createElement('a');
                anchor.href = 'data:text;charset=utf-8,' + encodeURIComponent(vm.cdHITReport);
                anchor.target = '_blank';
                anchor.download = `PVcdhitReport-${month}-${date}-${year}.txt`;
                anchor.click();
            }
            if (!this.opt){
                this.cdhitSelectedOpt = null;
            }
        }
  
    },methods: {
       
    submitProteins() {
      vm.checked_filter = false
      this.pchainid = this.selectedProteins
      this.showContacts()
    },
    selectAllProteinsChanged() {
      if (this.selectAllProteinsChecked) {
        this.selectedProteins = this.protein_chains.map(chain => chain.value);
      } else {
        this.selectedProteins = [];
      }
    },
    submitModifications() {
      vm.checked_filter = false
      this.modifications = this.selectedResidues
      this.showModifications()
    },
    submitModificationsCustom() {
      this.modifications = this.selectedResiduesCustom
      this.showModificationsCustom()
    },
    selectAllModifiedCustomChanged() {
      if (this.selectAllModifiedCustomChecked) {
        this.selectedResiduesCustom = Array.from(this.modified_residues.keys())
      } else {
        this.selectedResiduesCustom = [];
      }
    },
    selectAllModifiedChanged() {
      if (this.selectAllModifiedChecked) {
        this.selectedResidues = Array.from(this.modified_residues.keys())
      } else {
        this.selectedResidues = [];
      }
    },
    handleAlignChange() {
        vm.pdbid = ""
    },
        uploadCustomFullSequence: function() {
            uploadCustomFullSequence();
        },
        handleFileUpload(){
            this.file = this.$refs.custom_aln_file.files[0];
            if (this.tax_id != null){this.tax_id = null;}
        },
        submitCustomAlignment(){
            if (document.querySelector("pdb-topology-viewer") || document.querySelector("pdbe-molstar")) {cleanupOnNewAlignment(this);}
            if (vm.fasta_data){
                let cleanFasta = vm.fasta_data.replace(/^>Structure sequence\n(.+\n)+?>/i, ">");
                vm.fasta_data = cleanFasta;
            }
            let formData = new FormData();
            var fr = new FileReader();
            var uploadedFile = this.file;
            fr.onload = function(){
                if (validateFasta(fr.result)){
                    vm.blastPDBresult = [];
                    vm.blastMAPresult = null;
                    let firstSeq = parseFastaString(fr.result)[1].replace(/-/g,'');
                    vm.populatePDBsFromCustomAln(firstSeq);
                    formData.append('custom_aln_file', uploadedFile)
                    cleanupOnNewAlignment(vm, "Loading alignment...");
                    $.ajax({
                        url: '/custom-aln-data',
                        data: formData,
                        cache: false,
                        contentType: false,
                        processData: false,
                        method: 'POST',
                        type: 'POST', // For jQuery < 1.9
                        success: function(data){
                            if (data == "Success!"){
                                vm.didCDHit_truncate = true;
                            } else {
                                vm.didCDHit_truncate = false;
                            }
                            vm.alnobj = "custom";
                            vm.showAlignment(null, null, "upload");
                        },
                        error: function(error) {
                            alert(`${error.responseText}`);
                        }
                    });
                }
            };
            fr.readAsText(this.file)
        },
        cleanTreeOpts() {
            if (this.uploadSession){return;}
            Object.assign(vm.$data, initialState());
            this.type_tree="upload";
            this.topology_loaded=false;
            this.schemesMgr = new schemes();
            window.viewerInstanceTop = null;
            //cleanupOnNewAlignment(this, "Select new alignment!");
            //[this.options, this.tax_id, this.alnobj, this.chainid] = [null, null, null, null];
            //var topview = document.getElementById("PdbeTopViewer");
            //var molstar = document.querySelector(".msp-plugin");
            //if (molstar) {molstar.textContent = null}
            //if (topview) {topview.textContent = null}
        }, loadOptions({ action, callback }) {
            if (this.type_tree == "orth"){
                if (action === "LOAD_CHILDREN_OPTIONS") {
                    action = "";
                    callback();
                //     When they figure out LOAD_CHILDREN_OPTIONS with async search
                //     ajax(`/alignments/showTaxonomy-api/${parentNode.id}`).then(data => {
                //         let fetched_data = [data]
                //         parentNode.children = fetched_data[0].children
                //         callback()
                //     }).catch(error => {
                //         parentNode.children = []
                //         console.log(error)
                //         callback(new Error(`Failed to load options: network error: ${error}`))
                //     })
                };
                if (action === "LOAD_ROOT_OPTIONS") {
                    ajax(`/alignments/showTaxonomy-api/0`).then(data => {
                        data.isDisabled = true;
                        this.options = [data];
                        callback();
                    }).catch(error => {
                        console.log(error)
                    })
                };
                if (action === "LOAD_ROOT_OPTIONS") {
                    ajax('/alignments/showTaxonomy').then(data => {
                        if (this.type_tree == "orth"){
                            this.options = null;
                            data.isDisabled = true;
                            this.options = [data];
                            callback();
                        }
                    }).catch(error => {
                        console.log(error)
                    })
                };
            }
            if (this.type_tree == "para"){
                loadParaOptions(action, callback, this);
            }
        }, 
        loadProteinTypes (tax_id, type_tree) {
            console.log("JS trigger loadProteinTypes");
            cleanupOnNewAlignment(this)
            vm.protein_type_obj = null
            vm.alnobj = null
            if (type_tree == "orth"){
                this.alignments = null;
                this.proteinTypes = null;
                // Ajax call to get protein types
                let taxIDs = '';
                vm.tax_id.forEach(element => {
                    taxIDs += element + ",";
                });
                taxIDs = taxIDs.substring(0, taxIDs.length - 1);
                let data = {
                    tax_id: taxIDs
                };
                var url = '/proteinTypes';
                ajax(url, data).then(data => {
                    // Populate the list of protein types
                    let results = data["proteinTypesList"];
                    let intersection = results[0];
                    for (let i = 1; i < results.length; i++) {
                        intersection = intersection.filter(value => results[i].includes(value));
                    }
                    vm.proteinTypes = intersection;
                });
            }
            if (type_tree == "para"){
                loadParaProteinTypes(tax_id, this);
            }
        },

        //ncRNA function
        rerenderPeakTrack(file) {
            console.log(file);
            let trackViews = igv.browser.trackViews;
            console.log(trackViews)
            let lastTrack = trackViews[trackViews.length - 1].track;
            igv.browser.removeTrack(lastTrack);
            console.log("Last track removed");

            igv.browser.loadTrack({
                type: "annotation",
                format: "bedGraph",
                name: file,
                url: "static/peak_bg_files/" + file,
                displayMode: "EXPANDED",
                graphType: "line"
            });

            igv.visibilityChange();
        },

        rerenderIGV() {
            console.log("Rerendering IGV")
            var igvDiv = document.getElementById("igvdiv");

            if(this.selected_viewer == 'genome') {
                //var igvDiv = this.$refs.igvdivref;
                igvDiv.className = "igvbrowser";
            } else if (this.selected_viewer == 'transcript') {
                igvDiv.className = "igvbrowser hide";
            }

            igv.visibilityChange();
        },

        fetch_all_bed_files () {
            vm.genomic_peak_file = null;

            this.genomic_peak_file_list = null;
            var url = 'lncRNA/fetch_all_bed_files';

            ajax(url).then(data => {
                let results = data["results"];
                console.log(results);

                vm.genomic_peak_file_list = results;
            });
        },

        loadGencodeRBPs () {
            if(!this.rbps_fetched) {
                vm.rbp = null;
                this.rbpList = null;
                var url = 'lncRNA/get_rbps';

                ajax(url).then(data => {
                    let results = data["results"];
                    vm.rbpList = results;
                });
                this.rbps_fetched = true;
            }
        },

        loadTranscriptsFromRBP (rbp) {
            console.log("JS trigger loadTranscriptsFromRBP");

            vm.transcript_obj = null;
            vm.transcriptSearchQuery = '';
            vm.showTranscriptDropdown = false;

            this.allGencodeTranscripts = null;
            this.filteredTranscripts = null;
            var url = 'lncRNA/fetchTranscriptsFromRBP';
            ajax(url, {rbp}).then(data => {
                let results = data["results"];
                console.log(results);
                vm.allGencodeTranscripts = results;
                vm.filteredTranscripts = results; // Initially show all transcripts
            });
        },

        filterTranscripts() {
            if (!this.allGencodeTranscripts) return;

            const query = this.transcriptSearchQuery.toLowerCase();
            if (query === '') {
                this.filteredTranscripts = this.allGencodeTranscripts;
            } else {
                this.filteredTranscripts = this.allGencodeTranscripts.filter(transcript =>
                    transcript.toLowerCase().includes(query)
                );
            }
            // Limit to 50 results for performance
            if (this.filteredTranscripts.length > 50) {
                this.filteredTranscripts = this.filteredTranscripts.slice(0, 50);
            }
        },

        selectTranscript(transcript) {
            this.transcript_obj = transcript;
            this.transcriptSearchQuery = transcript;
            this.showTranscriptDropdown = false;
            this.displayRBPProfile({transcript_obj: transcript});
        },

        hideTranscriptDropdown() {
            // Delay hiding to allow click events to fire
            setTimeout(() => {
                this.showTranscriptDropdown = false;
            }, 200);
        },

        // Track search methods
        searchTrackTranscripts() {
            const query = this.trackSearchQuery.trim();

            if (query.length < 2) {
                this.filteredTrackResults = null;
                return;
            }

            // Use the new endpoint to search by internal_id
            this.loadingTrackSearch = true;

            $.ajax({
                url: 'lncRNA/search_transcripts_by_internal_id',
                type: 'POST',
                data: { query: query },
                dataType: 'json',
                success: (data) => {
                    this.filteredTrackResults = data.results;
                    this.loadingTrackSearch = false;
                },
                error: (error) => {
                    console.error("Error searching transcripts:", error);
                    this.filteredTrackResults = null;
                    this.loadingTrackSearch = false;
                }
            });
        },

        selectTrackSearchResult(result) {
            // Set search display to show internal_id
            this.trackSearchQuery = result.internal_id;
            this.showTrackSearchDropdown = false;

            // Since cell line and RBP are already selected, we can directly load the track data
            // The id from encore_schema_ids table matches the id needed for encore_transcript_tracks
            this.selectedSchemaType = result.type;
            this.selectedGeneName = result.gene_name;
            this.selectedTranscript = result.id;  // This is the primary key that links to encore_transcript_tracks

            // Load the track data with the selected combination
            this.loadTrackData();
        },

        hideTrackSearchDropdown() {
            // Delay hiding to allow click events to fire
            setTimeout(() => {
                this.showTrackSearchDropdown = false;
            }, 200);
        },

        loadAllTranscripts () {
            console.log("JS trigger loadallTranscripts");
            if (!this.transcripts_fetched) {
                vm.transcript_obj = null;
            
                this.allGencodeTranscripts = null;
                var url = 'lncRNA/allGencodeTranscripts';
                ajax(url).then(data => {
                    let results = data["results"];
                    console.log(results);

                    vm.allGencodeTranscripts = results;
                    this.transcripts_fetched = true;
                });
            } 
        },

        // Add new methods for Track View schema types, gene names, and transcripts
        loadCellLines() {
            console.log("Loading cell lines");
            vm.loadingCellLines = true;
            var url = 'lncRNA/get_cell_lines';
            $.ajax({
                url: url,
                type: 'GET',
                success: function(data) {
                    console.log("Cell lines loaded:", data);
                    vm.cellLineList = data.results;
                    vm.loadingCellLines = false;
                },
                error: function(error) {
                    console.error("Error loading cell lines:", error);
                    vm.loadingCellLines = false;
                }
            });
        },
        
        loadTrackRbps(cellLineId) {
            console.log("Loading RBPs for cell line:", cellLineId);
            vm.loadingTrackRbps = true;
            var url = 'lncRNA/get_track_rbps';
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    cell_line_id: cellLineId
                },
                success: function(data) {
                    console.log("Track RBPs loaded:", data);
                    vm.trackRbpList = data.results;
                    vm.loadingTrackRbps = false;
                },
                error: function(error) {
                    console.error("Error loading track RBPs:", error);
                    vm.loadingTrackRbps = false;
                }
            });
        },
        
        loadSchemaTypes() {
            console.log("Loading schema types");
            vm.loadingSchemaTypes = true;
            var url = 'lncRNA/get_schema_types';
            $.ajax({
                url: url,
                type: 'GET',
                success: function(data) {
                    console.log("Schema types loaded:", data);
                    vm.schemaTypes = data.results;
                    vm.loadingSchemaTypes = false;
                },
                error: function(error) {
                    console.error("Error loading schema types:", error);
                    vm.loadingSchemaTypes = false;
                }
            });
        },
        
        loadGeneNames(schemaType) {
            console.log("Loading gene names for schema type:", schemaType);
            // Reset downstream selections
            vm.selectedGeneName = null;
            vm.transcripts = null;
            vm.selectedTranscript = null;
            
            vm.loadingGeneNames = true;
            var url = 'lncRNA/get_gene_names';
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    schema_type: schemaType
                },
                success: function(data) {
                    console.log("Gene names loaded:", data);
                    vm.geneNames = data.results;
                    vm.loadingGeneNames = false;
                },
                error: function(error) {
                    console.error("Error loading gene names:", error);
                    vm.loadingGeneNames = false;
                }
            });
        },
        
        loadSchemaTranscripts(schemaType, geneName) {
            console.log("Loading transcripts for schema type:", schemaType, "and gene:", geneName);
            // Reset transcript selection
            vm.selectedTranscript = null;
            
            vm.loadingTranscripts = true;
            var url = 'lncRNA/get_schema_transcripts';
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    schema_type: schemaType,
                    gene_name: geneName
                },
                success: function(data) {
                    console.log("Transcripts loaded:", data);
                    vm.transcripts = data.results;
                    vm.loadingTranscripts = false;
                },
                error: function(error) {
                    console.error("Error loading transcripts:", error);
                    vm.loadingTranscripts = false;
                }
            });
        },
        loadTrackData() {
            // Log selections first for debugging
            this.logTrackSelections();
            
            if (vm.selectedTranscript && vm.selectedTrackRbp && vm.selectedCellLine) {
                console.log("Loading track data for the selected combination");
                vm.loadingTrackData = true;
                vm.trackDataMessage = null;
                vm.trackData = null;
                
                // Store a reference to the Vue component
                const self = this;

                var url = 'lncRNA/get_transcript_track_data';
                $.ajax({
                    url: url,
                    type: 'POST',
                    data: {
                        transcript_id: vm.selectedTranscript,
                        rbp_id: vm.selectedTrackRbp,
                        cell_line_id: vm.selectedCellLine
                    },
                    success: function(data) {
                        console.log("Track data response:", data);
                        vm.loadingTrackData = false;
                        
                        if (data.success) {
                            // Set the track data and message
                            vm.trackData = data.track_data;
                            vm.trackDataMessage = "Track data loaded successfully";
                            
                            // Plot the track data using self (the Vue component)
                            self.plotTrackData(vm.trackData, "rbp_profile");
                        } else {
                            vm.trackDataMessage = data.message || "Failed to load track data";
                        }
                    },
                    error: function(error) {
                        console.error("Error loading track data:", error);
                        vm.loadingTrackData = false;
                        vm.trackDataMessage = "Error loading track data: " + (error.responseJSON?.message || error.statusText);
                    }
                });
            } else {
                // Reset track data if not all selections are made
                vm.trackData = null;
                vm.trackDataMessage = "Please select a cell line, RBP, and transcript to view track data";
            }
        },
        logTrackSelections() {
            if (vm.selectedTranscript) {
                console.log("Track View Selection Summary:");
                console.log("Selected Cell Line ID:", vm.selectedCellLine);
                console.log("Selected RBP ID:", vm.selectedTrackRbp);
                console.log("Selected Schema Type:", vm.selectedSchemaType);
                console.log("Selected Gene Name:", vm.selectedGeneName);
                console.log("Selected Transcript ID:", vm.selectedTranscript);
            }
        },
        plotTrackData(trackData, divId) {
            if (!trackData || trackData.length === 0) {
                console.error("No track data available to plot");
                return;
            }

            console.log("Plotting track data:", trackData);
            console.log("Track data type:", typeof trackData);
            console.log("Track data length:", trackData.length);
            
            try {
                // If trackData is a string (e.g., JSON string), try to parse it
                if (typeof trackData === 'string') {
                    try {
                        trackData = JSON.parse(trackData);
                        console.log("Parsed track data from string");
                    } catch (parseError) {
                        console.error("Error parsing track data string:", parseError);
                    }
                }
                
                // Resolution for x-axis (distance between points)
                const resolution = 1;

                // Create x-axis values based on the resolution
                const xValues = Array.from({ length: trackData.length }, (_, i) => i * resolution);
                
                // Create the trace for the line plot
                var trace = {
                    x: xValues,
                    y: trackData,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Track',
                    line: {
                        color: 'rgb(55, 128, 191)',
                        width: 2
                    }
                };
                
                var data = [trace];
                
                var layout = {
                    autosize: true,
                    title: "Track Data",
                    xaxis: {
                        title: 'Sequence Position',
                        range: [0, trackData.length * resolution]
                    },
                    yaxis: {
                        title: 'Signal Strength'
                    },
                    showlegend: true,
                    width: 1000,
                    height: 600,
                    font: {
                        size: 12
                    }
                };
                
                var config = {responsive: true};
                
                console.log("Calling Plotly.newPlot with:", divId, data, layout);
                Plotly.newPlot(divId, data, layout, config);
                console.log("Plotly chart created successfully");
            } catch (error) {
                console.error("Error plotting track data:", error);
            }
        },
        getPDBchains(pdbid, aln_id) {
            if (this.uploadSession){return;}
            if (pdbid.length === 4) {
                if (document.querySelector("pdb-topology-viewer") || document.querySelector("pdbe-molstar")) {cleanupOnNewAlignment(this);}
                this.unfilteredChains = null;
                this.PDBparsing = false;
                loadAlignmentViewer(vm.fasta_data);
                this.chains = null;
                this.chainid = [];
                this.hide_chains = true;
                generateChainsFromLiteMol(`https://coords.litemol.org/${pdbid.toLowerCase()}/assembly?id=1&lowPrecisionCoords=1&encoding=BCIF`, "unfilteredChains");
                ajax(`https://www.ebi.ac.uk/pdbe/api/pdb/entry/molecules/${pdbid.toLowerCase()}`).then(struc_data => {
                    if(vm.unfilteredChains){return;}
                    vm.unfilteredChains = struc_data[pdbid.toLowerCase()];
                    vm.unfilteredChains_orig = struc_data[pdbid.toLowerCase()];
                }).catch(error => {
                    console.log(error);
                    var elt = document.querySelector("#onFailedChains");
                    if (error.status == 404){
                        elt.innerHTML  = "Couldn't find this PDB on EBI!<br/>Try a different PDB ID."
                    } else if (error.status == 0){
                        elt.innerHTML  = "It looks like PDBe is down! Running alternative chain parser..."
                    } else {
                        elt.innerHTML  = "Problem with parsing the chains! Try a different PDB ID."
                    }
                })
            }
        },
        showAlignment(aln_id, taxid, type_tree) {
            cleanupOnNewAlignment(this, "Loading alignment...");
            this.chainid = [];
            if (type_tree == "orth"){
                var url = `/ortholog-aln-api/${aln_id}/${taxid}`}
            if (type_tree == "para"){
                var url = '/paralog-aln-api/'+aln_id.split(',')[1]}
            if (type_tree == "upload" && !this.uploadSession&& this.cdhitSelectedOpt != "untrunc"){
                var url = '/custom-aln-data'
            }
            if (type_tree == "upload" && !this.uploadSession && this.cdhitSelectedOpt == "untrunc"){
                var url = '/custom-aln-data-nocdhit'
            }
            if (this.uploadSession){
                this.$nextTick(function(){
                    loadAlignmentViewer (vm.fasta_data);
                });
                return;
            }
            ajax(url).then(fasta => {
                const alignment = fasta["Alignment"];
                const alignmentSplitBySequence = alignment.split(">").filter(function(splitSequence) {
                    return splitSequence.length > 0;
                });
                const zerothSequenceSplitByLines = alignmentSplitBySequence[0].split("\n");
                const zerothFastaSeqName = fasta['Sequence names'][0];
                // const zerothFastaSeqName = "Escherichia coli str. K-12 substr. MG1655"; //fasta['Sequence names'][0];
                const alignmentLength = zerothSequenceSplitByLines[1].length;
                const associatedDataCache = {};
                this.associatedDataCache = associatedDataCache;

                if(!(vm.alnobj == "custom")) {
                const url = `/aln-api/${vm.alnobj.id}/${taxid}`;
                ajax(url).then(aln_data => {
                    vm.associatedDataCache = aln_data;
                    // console.log("aln_data", aln_data);
                }).catch(error => {
                    console.log('No associated data');
                });
                }
                
                /*const strainQuery = '&res__poldata__strain__strain=';
                var url = `/desire-api/residue-alignment/?format=json&aln=${vm.alnobj.id}${strainQuery}${zerothFastaSeqName}`;
                let index=url.indexOf('|');
                if (index !== -1){
                    url=url.substring(0, index);
                }
                ajax(url).then(aln_data => {
                    console.log("aln_data", aln_data);
                    for (const result of aln_data.results) {
                        const url = `/resi-api/${result.res.split("/")[5]}`;
                        const aln_pos = result.aln_pos;
                        ajax(url).then(resiData => {
                            const associatedData = resiData["Associated data"];
                            associatedDataCache[aln_pos] = associatedData;
                            console.log('AD1', associatedData, "aln_pos", aln_pos);
                            window.ajaxRun = false;
                        });
                    }
                });*/
                
                /*for (let aln_pos = 1; aln_pos <= alignmentLength; aln_pos++) {
                    const strainQuery = '&res__poldata__strain__strain=';
                    var url = `/desire-api/residue-alignment/?format=json&aln_pos=${aln_pos}&aln=${vm.alnobj.id}${strainQuery}${zerothFastaSeqName}`;
                    let index=url.indexOf('|');
                    if (index !== -1){
                        url=url.substring(0, index);
                    }
                    console.log("url", url);
                    ajax(url).then(alnpos_data => {
                    console.log('alnpos_data', alnpos_data.count );
                    if (alnpos_data.count != 0){
                        ajax('/resi-api/' + alnpos_data["results"][0]["res"].split("/")[5]).then(resiData => {
                            console.log('AD1',resiData["Associated data"]);
                            window.ajaxRun = false;
                        });
                    }
                    }).catch(error => {
                    window.ajaxRun = false;
                    console.log(error);
                    })
                }*/
                if (fasta['TwinCons']){
                    this.custom_aln_twc_flag = fasta['TwinCons'];
                    fetchTWCdata(fasta['Alignment']);
                }
                this.cdHITReport = fasta["cdHitReport"]
                if (this.cdHITReport){
                    let cdNums = this.cdHITReport.split(/comparing sequences from.*\n/)[1].split(/\n/)[1].split(/ +/);
                    this.cdHITnums = [cdNums[1], cdNums[3]];
                }
                this.fastaSeqNames = fasta['Sequence names'];
                window.aaFreqs = fasta['AA frequencies'];
                var barColors = Array(aaFreqs.length).fill('#808080');
                window.barColors = barColors;
                this.fasta_data = fasta['Alignment'];
                this.aa_properties = calculateFrequencyData(fasta['AA frequencies']);
                loadAlignmentViewer (fasta['Alignment']);
            })
        }, showTopologyViewer (pdbid, chainid, fasta){
            this.topology_loaded = false;
            window.filterRange = "-10000,10000";
            if (chainid.length > 1){this.chainid = chainid[0];}
            const topview_item = document.getElementById("topview");
            if (topview_item) {topview_item.remove(); create_deleted_element("topif", "topview", "")}
            var minIndex = String(0)
            var maxIndex = String(100000)
            var pdblower = pdbid.toLocaleLowerCase();
            window.pdblower = pdblower;
            let temp = this.chains.filter(obj => {
                return obj["value"] == chainid;
            })[0];
            let ebi_sequence = temp["sequence"];
            let startIndex = temp["startIndex"];
            let stopIndex = temp["endIndex"];
            let struc_id = `${pdbid}-${temp["entityID"]}-${chainid}`
            if (!this.uploadSession){
                getStructMappingAndTWC (fasta, struc_id, startIndex, stopIndex, ebi_sequence, this);
            }
            loadAlignmentViewer (vm.fasta_data);
            var rna_url = `https://www.ebi.ac.uk/pdbe/api/pdb/entry/polymer_coverage/${pdbid}/chain/${chainid}`
            ajax(rna_url).then(data => {
                if(vm.topology_loaded){return;}
                var entityid = data[pdblower]["molecules"][0].entity_id;
                var topology_viewer = `<pdb-rna-viewer id="PdbeTopViewer" pdb-id="${pdbid}" entity-id="${entityid}" chain-id="${chainid}"></pdb-rna-viewer>`
                document.getElementById('topview').innerHTML = topology_viewer;
                window.viewerInstanceTop = document.getElementById("PdbeTopViewer");
            });
            /*var topology_url = `https://www.ebi.ac.uk/pdbe/api/topology/entry/${pdblower}/chain/${chainid}`
            
            ajax(topology_url).then(data => {
                if(vm.topology_loaded){return;}
                var entityid = Object.keys(data[pdblower])[0];
                let termStart = Number(data[pdblower][entityid][chainid]["terms"][0].resnum);
                let termEnd = Number(data[pdblower][entityid][chainid]["terms"][1].resnum);
                vm.all_residues = filterCoilResidues([{start: termStart, stop: termEnd}])
                vm.coil_residues = filterCoilResidues(data[pdblower][entityid][chainid]["coils"])
                vm.helix_residues = filterCoilResidues(data[pdblower][entityid][chainid]["helices"])
                vm.strand_residues = filterCoilResidues(data[pdblower][entityid][chainid]["strands"])
                listSecondaryStructures();
                var mapping = [];
                var range_string = minIndex.concat("-").concat(maxIndex);
                let ebiMappingURL = 'https://www.ebi.ac.uk/pdbe/api/mappings/uniprot/'+pdbid;
                ajax(ebiMappingURL).then(data=>{
                    var result = [];
                    customFilter(data, result, "chain_id", chainid);
                    result = result[0];
                    
                    if(result != null) {
                        var pdb_start = parseInt(result["start"]["residue_number"]);
                        var pdb_end = parseInt(result["end"]["residue_number"]);
                        var uniprot_start = parseInt(result["unp_start"]);
                        for (let residue_number_str in range_string.split("-")){
                            var residue_number = parseInt(residue_number_str);
                            if(residue_number >= pdb_start && residue_number <= pdb_end){
                                let offset = uniprot_start - pdb_start;
                                mapping.push(residue_number - offset);
                            }else{
                                mapping.push(residue_number);
                            }
                        }
                    }else{
                        console.log("No mapping for pdb "+pdbid+" and chain"+ chainid)
                        mapping = [range_string.split("-")[0],range_string.split("-")[1]];
                    }
                    var topology_viewer = `<pdb-topology-viewer id="PdbeTopViewer" entry-id=${pdbid} entity-id=${entityid} chain-id=${chainid} filter-range=${mapping}></pdb-topology-viewer>`
                    document.getElementById('topview').innerHTML = topology_viewer;
                    window.viewerInstanceTop = document.getElementById("PdbeTopViewer");
                }).catch(error => {
                    if (vm.topology_loaded&&vm.topology_loaded!='error'){return;}
                    mapping = [range_string.split("-")[0],range_string.split("-")[1]];
                    var topology_viewer = `<pdb-topology-viewer id="PdbeTopViewer" entry-id=${pdbid} entity-id=${entityid} chain-id=${chainid} filter-range=${mapping}></pdb-topology-viewer>`
                    document.getElementById('topview').innerHTML = topology_viewer;
                    window.viewerInstanceTop = document.getElementById("PdbeTopViewer");
                    console.log(error);
                });
            }).catch(error => {
                if (vm.topology_loaded&&vm.topology_loaded!='error'){return;}
                var topview = document.querySelector('#topview');
                console.log(error);
                this.topology_loaded = 'error';
                topview.innerHTML = "Failed to fetch the secondary structure!<br>Try another structure."
            });*/
        }, showPDBViewer(pdbid, chainid, entityid){
            showPDBHelper(pdbid, chainid, entityid)
        }, populateECODranges(pdbid, chainid) {
            populateECODranges(pdbid, chainid);
        }, calculateModifiedCustom(entity_id, filepath) {
            calculateModifiedCustom(entity_id, filepath)
        }, 
        calculateProteinContacts(pdbid, chainid) {
            vm.mapped_aa_contacts_mods = new Map();
            var url = `protein-contacts/${pdbid}/${chainid}`
            ajax(url).then(data => {
                calculateModifiedResidues(pdbid, chainid, this.entityID)
                if(data) {F
                    vm.protein_contacts = data;
                    var newContactMap;
                    var filtered_chains = vm.protein_chains.filter(e => e.value in data);
                    vm.protein_chains = filtered_chains;
                    for (let chain of vm.protein_chains){
                        chain.banname=vm.unfilteredChains_orig[chain.entityID-1].molecule_name[0].replace('Large ribosomal subunit', 'LSU').replace('Small ribosomal subunit', 'SSU')
                    } 
                    

                    var i = 1.0;
                    var colorMap = new Map();
                    vm.selectSections_proteins = new Map();
                    vm.mapped_aa_contacts_mods.set("Protein Contacts", [])
                    for (var val in vm.protein_contacts) {
                        vm.selectSections_proteins.set(val, [])
                        var color = interpolateLinearly(i/filtered_chains.length, aaColorData.get("Protein contacts")[0])
                        var rgbColor = "rgb(" + color[0][0] + "," + color[0][1] + "," + color[0][2] + ")";
                        colorMap.set(val, rgbColor);
                        //newContactMap.set(vm.protein_contacts, aaColorData.get("Shannon entropy")[0][1]
                        i = i+1;
                        for (var j in vm.protein_contacts[val]) {
                            vm.selectSections_proteins.get(val).push({
                                entity_id: "" + this.entityID,
                                residue_number: vm.protein_contacts[val][j],
                                color: color[1],
                                sideChain: false,
                            });
                            var protein_name = vm.protein_chains.filter(e => e.value === val)[0]?.text;
                            if (protein_name) {
                            vm.mapped_aa_contacts_mods.get("Protein Contacts").push([vm.protein_contacts[val][j], protein_name]);
                            }
                        }
                    }                    
                    vm.proteinColorMap = colorMap;
                }
                }).catch(error => {
                    console.log(error)
                })  
        },
        postStructureData(pdbid, chainid) {
            const topview_item = document.getElementById("topview");
            if (topview_item) {topview_item.remove(); create_deleted_element("topif", "topview", "Loading Structure Data ", true)}
            let tempEntities = this.chains.filter(obj => {
                return obj["value"] == chainid;
            });
            let entities = [];
            tempEntities.forEach(function(ent){
                entities.push({ entityID: ent["entityID"], chainID: ent["value"] })
            });
            this.entityID = tempEntities[0]["entityID"];
            postCIFdata(pdbid, entities);
        },downloadAlignmentImage() {
            downloadAlignmentImage(document.querySelector('#alnDiv'));
        },downloadAlignmentData() {
            downloadAlignmentData(vm.fasta_data);
        },downloadCSVData() {
            downloadPyMOLscript();
            downloadCSVData();
        },getExampleFile(url, name) {
            getExampleFile(url, name);
        },cleanFilter(checked_filter, masking_range){
            cleanFilter(checked_filter, masking_range);
        },handleMaskingRanges(mask_range){
            handleMaskingRanges(mask_range);
        },cleanSelection(checked_selection, filter_range){
            cleanSelection(checked_selection, filter_range);
        },cleanCustomMap(checked_customMap){
            cleanCustomMap(checked_customMap);
        },handleCustomMappingData(){
            handleCustomMappingData();
        },handleDomainRange(domain_range){
            handleDomainRange(domain_range);
        },handleFilterRange(filter_range){
            handleFilterRange(filter_range);
        },handlePropensities(checked_propensities){
            handlePropensities(checked_propensities);
        },populatePDBs(alndata){
            populatePDBs(alndata);
        },populatePDBsFromCustomAln(firstSeq){
            if (this.guideOff){
                populatePDBsFromCustomAln(firstSeq);
            }
        },getPropensities(sequence_indices) {
            getPropensities(sequence_indices);
        },listSecondaryStructures() {
            listSecondaryStructures();
        },downloadFreqsData(){
            let [month, date, year] = new Date().toLocaleDateString("en-US").split("/");
            let anchor = document.createElement('a');
            anchor.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(vm.freqCSV);
            anchor.target = '_blank';
            anchor.download = `PVfreqData-${month}-${date}-${year}.csv`;
            anchor.click();
        },flushDjangoSession(){
            ajaxProper({
                    url: `/flush-session`,
                    type: `GET`,
                    dataType: `text`,
                }).then(response => {
                if (response == 'Success!'){
                    console.log("Session flushed successfully!") 
                }
            })
        }, uploadCustomPDB(){
            uploadCustomPDB();
        }, uploadCustomCIF(){
            uploadCustomCIF();
        }, updateMolStarWithRibosome(checkRibo){
            if(checkRibo&&viewerInstance&&this.pdbid&&this.entityID){
                this.completeRiboContext = false;
                viewerInstance.visual.update({
                    moleculeId: this.pdbid, 
                    assemblyId: '1',
                    bgColor: {r:255,g:255,b:255},
                });
                viewerInstance.events.loadComplete.subscribe(function (e) {
                    let prom = viewerInstance.visual.select({ 
                        data: [{entity_id: `${vm.entityID}` }], 
                        nonSelectedColor: {r:180, g:180, b:180} 
                    });
                    prom.then(function(v){
                        viewerInstance.visual.focus([{ entity_id: `${vm.entityID}` }]);
                        if(viewerInstanceTop&&vm.selected_property){
                            viewerInstanceTop.pluginInstance.displayDomain();
                        }
                    })
                });
            }
            if (!checkRibo&&viewerInstance&&this.pdbid&&this.entityID){
                this.showPDBViewer(this.pdbid, this.chainid[0], this.entityID);
                viewerInstance.events.loadComplete.subscribe(function (e) {
                    if(viewerInstanceTop&&vm.selected_property){
                        viewerInstanceTop.pluginInstance.displayDomain();
                    }
                });
            }
        },
        loadCellLines() {
            console.log("Loading cell lines");
            var url = 'lncRNA/get_cell_lines';
            $.ajax({
                url: url,
                type: 'GET',
                success: function(data) {
                    console.log("Cell lines loaded:", data);
                    vm.cellLineList = data.results;
                },
                error: function(error) {
                    console.error("Error loading cell lines:", error);
                }
            });
        },
        loadTrackRbps(cellLineId) {
            console.log("Loading RBPs for cell line:", cellLineId);
            var url = 'lncRNA/get_track_rbps';
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    cell_line_id: cellLineId
                },
                success: function(data) {
                    console.log("Track RBPs loaded:", data);
                    vm.trackRbpList = data.results;
                },
                error: function(error) {
                    console.error("Error loading track RBPs:", error);
                }
            });
        },
        loadSchemaTypes() {
            console.log("Loading schema types");
            var url = 'lncRNA/get_schema_types';
            $.ajax({
                url: url,
                type: 'GET',
                success: function(data) {
                    console.log("Schema types loaded:", data);
                    vm.schemaTypes = data.results;
                },
                error: function(error) {
                    console.error("Error loading schema types:", error);
                }
            });
        },
        loadGeneNames(schemaType) {
            console.log("Loading gene names for schema type:", schemaType);
            // Reset downstream selections
            vm.selectedGeneName = null;
            vm.transcripts = null;
            vm.selectedTranscript = null;

            var url = 'lncRNA/get_gene_names';
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    schema_type: schemaType
                },
                success: function(data) {
                    console.log("Gene names loaded:", data);
                    vm.geneNames = data.results;
                },
                error: function(error) {
                    console.error("Error loading gene names:", error);
                }
            });
        },
        loadSchemaTranscripts(schemaType, geneName) {
            console.log("Loading transcripts for schema type:", schemaType, "and gene:", geneName);
            // Reset transcript selection
            vm.selectedTranscript = null;

            var url = 'lncRNA/get_schema_transcripts';
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    schema_type: schemaType,
                    gene_name: geneName
                },
                success: function(data) {
                    console.log("Transcripts loaded:", data);
                    vm.transcripts = data.results;
                },
                error: function(error) {
                    console.error("Error loading transcripts:", error);
                }
            });
        },
        displayRBPProfile(internal_id) {
            this.rbp_profile = null
            this.transcript_peaks = null
            this.transcript_length = null
            this.peaks_present = true

            var url = 'lncRNA/displayRBPProfile';
            ajax(url, {internal_id}).then(data => {
                // vm.rbp_profile = data['plot']
                vm.transcript_peaks = data['peaks']
                vm.transcript_length = data['length']

                this.plotCumRBPProfile(vm.transcript_peaks, vm.transcript_length, "rbp_profile", vm.rbp)
                console.log("Finished Plotting")
            })
        },

        replotRBPProfile() {
            // Replot with current data when toggle changes
            if (this.transcript_peaks && this.transcript_length) {
                this.plotCumRBPProfile(this.transcript_peaks, this.transcript_length, "rbp_profile", this.rbp)
            }
        },

        plotCumRBPProfile(peaks, length, divId, selectedRBP) {
            if (peaks[0] === 'None') {
                vm.peaks_present = false
                return;
            }

            var ids = [];
            var strengths = [];
            var seqidx = [];

            /* For displaying all as one
            for (const p of peaks) {
                if (p.length !== 3) {
                console.error(`Error processing ${id} and peak ${p}`);
                continue; // Skip this peak for error handling
                }

                const count = p[1][1] - p[1][0] + 1;
                ids.push(...Array(count).fill(p[0]));
                strengths.push(...Array(count).fill(p[2]));
                seqidx.push(...Array.from({ length: count }, (_, i) => p[1][0] + i));
            }
            */

            // Helper function to extract base RBP name
            function extractRBPName(fullName) {
                // Simply split by underscore and take the first part
                const parts = fullName.split('_');
                return parts[0];
            }

            var traces = {};

            for (const p of peaks) {
                var ids = [];
                var strengths = [];
                var seqidx = [];

                if (p.length !== 3) {
                console.error(`Error processing peak ${p}`);
                continue; // Skip this peak for error handling
                }

                var count = p[1][1] - p[1][0] + 1;

                // Extract base RBP name for grouping
                const baseName = extractRBPName(p[0]);

                if (baseName in traces) {
                    traces[baseName].x.push(...Array.from({ length: count }, (_, i) => p[1][0] + i));
                    traces[baseName].y.push(...Array(count).fill(p[2]));

                } else {
                    var temp_trace = {
                        x: Array.from({ length: count }, (_, i) => p[1][0] + i),
                        y: Array(count).fill(p[2]),
                        type: 'bar',
                        name: baseName  // Use base name in legend
                    }

                    traces[baseName] = temp_trace
                }
            }

            // Convert to array and apply styling based on selection
            var data = [];
            var selectedTrace = null;

            // Process all traces, separating selected from others
            for (const [rbpName, trace] of Object.entries(traces)) {
                if (rbpName === selectedRBP) {
                    // Always use distinct color for selected RBP
                    trace.marker = {
                        color: vm.selectedRBPColor,  // Distinct color for selected RBP
                        line: {
                            color: vm.selectedRBPBorderColor,  // Border color
                            width: vm.highlightSelectedRBP ? vm.selectedRBPBorderWidth : 0  // Bold outline only when highlighting
                        }
                    };
                    trace.opacity = 1.0;  // Always full opacity for selected
                    selectedTrace = trace;  // Save to add last (on top)
                } else {
                    // Style for non-selected RBPs
                    if (vm.highlightSelectedRBP) {
                        // Apply reduced opacity only if highlighting is enabled
                        trace.opacity = vm.unselectedRBPOpacity;  // Reduced opacity
                    } else {
                        // Full opacity when highlighting is disabled
                        trace.opacity = 1.0;
                    }
                    trace.marker = {
                        line: {
                            width: 0  // No outline for non-selected
                        }
                    };
                    data.push(trace);
                }
            }

            // Add selected trace last so it appears on top
            if (selectedTrace) {
                data.push(selectedTrace);
            }

            var layout = {
                autosize: true,

                title: `RBP Peaks for ${vm.transcript_obj || 'Transcript'}`,
                xaxis: {
                    title: 'Sequence Position',
                    range: [0, length]
                },

                yaxis: {
                    title: 'Strength'
                },

                bargap: 0,

                showlegend: true,

                width: 1000,
                height: 600,

                font: {
                    size: 12
                }

            }

            var config = {responsive: true}

            Plotly.newPlot(divId, data, layout, config); // Add the plot to the specified div
        },

    }, 
    mounted() {
        // addFooterImages("footerDiv");
        console.log("Vue mounted");
        console.log("Current directory js", process.cwd())
        var igvDiv = document.getElementById("igvdiv");
        var options =
            {
                genome: "hg38",
                //locus: "chr8:127,736,588-127,739,371",
                tracks: [
                    {
                        type: "annotation",
                        format: "gtf",
                        name: "Transcript Mapping",
                        url: "static/annotation_files/hendrix_gencodev44_annotation_sorted.gtf",
                        indexURL: "static/annotation_files/hendrix_gencodev44_annotation_sorted.gtf.idx",
                        displayMode: "EXPANDED",
                        visibilityWindow: -1, 
                    },
                ]
            };

        igv.createBrowser(igvDiv, options)
            .then(function (browser) {
                console.log("Created IGV browser");
                //browser.removeTrackByName("Refseq Curated");
                igv.browser = browser;
            })
        console.log("Created variable for browsewr")
        igv.browser.removeTrackByName("Refseq Curated");

        // Not related to igv, previously present
        this.schemesMgr = new schemes();
    },
    created() {
        $(window).bind('beforeunload', function(){
            vm.flushDjangoSession();
        });
    }
}

</script>
