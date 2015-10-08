#!/usr/bin/env python
# -*- coding: utf-8 -*-

RESOURCE_CORE = {

	# General
	'priref':'priref',
	'record':'',

	'title':'resourceDublinCore_title-title', 
	'author.name':'resourceDublinCore_creator-creator',
	'author.name-name':'',
    'keyword.contents-term':'resourceDublinCore_subject', 
    'abstract':'resourceDublinCore_description-term',
    'publisher':'resourceDublinCore_publisher-publisher', 
    'publisher-name':'',
    'contributor':'resourceDublinCore_contributor-contributor',
    'contributor-name':'',
    'year_of_publication':'resourceDublinCore_date', 
    'material_type':'',
    'material_type-term':'resourceDublinCore_resourceType',
    'dimensions':'resourceDublinCore_format-term', 
    'digital_reference':'resourceDublinCore_identifier-term',
    'sort_year':'resourceDublinCore_sortYear_sortYear', 
    'source':'resourceDublinCore_source-term',
    'language_code':'',
    'language_code-term':'resourceDublinCore_language', 
    'relation':'resourceDublinCore_relation-term',
    'coverage':'resourceDublinCore_coverage-term', 
    'rights':'resourceDublinCore_rights-term',

    'reproduction-reproduction.reference-reference_number':'reproductions_reproduction-reference',
    'reproduction-reproduction.reference-image_reference':'reproductions_reproduction-identifierURL',
    'reproduction-reproduction.notes':'reproductions_reproduction-notes',
    'exhibition':'',
    'exhibition-exhibition':'exhibitionsAuctionsCollections_exhibition-exhibitionName', 
    'exhibition-exhibition.notes':'exhibitionsAuctionsCollections_exhibition-notes', 
    'auction.name':'',
    'auction.name-auction':'exhibitionsAuctionsCollections_auction-auctionName',
    'auction.notes':'exhibitionsAuctionsCollections_auction-notes',

    #'':'exhibitionsAuctionsCollections_collection-collectionName',
    'collection.notes':'exhibitionsAuctionsCollections_collection-notes',
    'object.object_number':'linkedObjects_linkedObjects-objectNumber',

    'copy.number':'',
    'copy.shelfmark':'copiesAndShelfMarks_defaultShelfMark', 
    'copy.number-copy_number':'copiesAndShelfMarks_copyDetails-copyNumber',
    'copy.number-shelfmark':'copiesAndShelfMarks_copyDetails-shelfMark',
    'loan_category':'',
    'loan_category-term':'copiesAndShelfMarks_copyDetails-loanCategory',
    'site':'',
    'site-term':'copiesAndShelfMarks_copyDetails-site',
    'copy.number-location.note':'copiesAndShelfMarks_copyDetails-locationNotes',

    'datasets.collect':'',
	'datasets.collect-text':'',

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

