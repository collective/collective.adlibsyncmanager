#!/usr/bin/env python
# -*- coding: utf-8 -*-

TAXONOMY_CORE = {
	'priref':'priref',
	'record':'',
	'scientific_name':'taxonomicTermDetails_term_scientificName', 
	'rank':"",
	'rank-text':'taxonomicTermDetails_term_rank',
	'status':"",
    'status-text':'taxonomicTermDetails_status_status', 

    #'':'taxonomicTermDetails_status_validAcceptedName',  TODO

    'common_name':'taxonomicTermDetails_commonName-commonName', 

    #'':'taxonomicTermDetails_synonyms', TODO

    'parent_name':'taxonomicTermDetails_hierarchy_parentName', 

    #'':'taxonomicTermDetails_hierarchy_childName', TODO

    'taxon_author':'taxonomicTermDetails_sourceAndDefinition_taxonAuthor', 
    'description':'taxonomicTermDetails_sourceAndDefinition_description',
    'distribution':'taxonomicTermDetails_sourceAndDefinition_distribution', 
    'Publication':'',
    'Publication-publication':'taxonomicTermDetails_sourceAndDefinition_publication-publication',
    'Publication-original_description':'taxonomicTermDetails_sourceAndDefinition_publication-originalDescription',

    'expert':'taxonomicTermDetails_sourceAndDefinition_expert-expert', 
    'other_source':'taxonomicTermDetails_sourceAndDefinition_otherSource-otherSource',
    'notes':'taxonomicTermDetails_notes-notes',

    'Edit':'',
    'Edit-edit.name':'',
    'Edit-edit.time':'',
    'Edit-edit.date':'',
    'Edit-edit.source':'',
    'Edit-edit.notes':'',
    'input.source':'',
    'input.date':'',
    'input.name':'',
    'input.time': '',
}

