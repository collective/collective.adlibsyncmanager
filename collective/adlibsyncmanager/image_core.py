#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Adlib - Plone object

IMAGE_CORE = {
	"priref":"priref",
	"record": "",

	# Reproduction details
	'reference_number':'reproductionData_identification_reproductionReference', 
	'format':'reproductionData_identification_format',
	'reproduction_type':"",
    'reproduction_type-term':'reproductionData_identification_reproductionType', 
    'copies':'reproductionData_identification_copies',

    'technique':'',
    'technique-term':'reproductionData_identification_technique', 
    'location':"",
    'location-term':'reproductionData_identification_location',
    'production_date':'reproductionData_identification_date', 
    'image_reference':'reproductionData_identification_identifierURL',

    'title':'reproductionData_descriptiveElements_title-title', 
    'creator':'reproductionData_descriptiveElements_creator',
    'creator-name':'',

    'subject':'',
    'subject-term':'reproductionData_descriptiveElements_subject', 

    'description':'reproductionData_descriptiveElements_description-description',
    'publisher':'reproductionData_descriptiveElements_publisher', 
    'publisher-name':'',
    'contributor':'reproductionData_descriptiveElements_contributor',
    'contributor-name':'',
    'source':'reproductionData_descriptiveElements_source-source', 
    'coverage-term':'reproductionData_descriptiveElements_coverage',
    'coverage':'',
    'rights':'reproductionData_descriptiveElements_rights-rights', 
    'notes':'reproductionData_descriptiveElements_notes-notes',

    "documentation":"",#parent
    "documentation-documentation.title":"documentation_documentation-title",#relation
    "documentation-documentation.title-lead_word":"documentation_documentation-article",
    "documentation-documentation.title-title":"",
    "documentation-documentation.title-author.name":"documentation_documentation-author",
    "documentation-documentation.page_reference":"documentation_documentation-pageMark",
    "documentation-documentation.notes":"documentation_documentation-notes",
    "documentation-documentation.shelfmark": "documentation_documentation-shelfMark",

    "object.object_number":"linkedObjects_linkedobjects"
}


