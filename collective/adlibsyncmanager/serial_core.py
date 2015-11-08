#!/usr/bin/env python
# -*- coding: utf-8 -*-

SERIAL_CORE = {
	"priref":"priref",
	"record":"",
	"internal_link_priref":"",
    "internal_link_title":"",


    'lead_word':'titleAuthorImprintCollation_titleAuthor_leadWord', 

    'title':'titleAuthorImprintCollation_titleAuthor_title-title',#grid

    'statement_of_responsibility':'titleAuthorImprintCollation_titleAuthor_statementOfRespsib', 

    'author.name-name':"",
    'author.name':'titleAuthorImprintCollation_titleAuthor_author-authors',#grid
    "author.role":"",
    'author.role-term':'titleAuthorImprintCollation_titleAuthor_author-roles',#grid


    'corporate_author':'titleAuthorImprintCollation_titleAuthor_corpAuthors',#grid
    'corporate_author-name':'',

    'edition':'titleAuthorImprintCollation_edition_edition',

    'issues':'titleAuthorImprintCollation_issues_issues',
    
    'place_of_publication':'titleAuthorImprintCollation_imprint_place-term',#grid

    'publisher':'titleAuthorImprintCollation_imprint_publishers',#grid
    'publisher-name':'',

    'year_of_publication':'titleAuthorImprintCollation_imprint_year', 
    
    'print.place':'',
    'print.place-term':'titleAuthorImprintCollation_imprint_placesPrinted',

    'print.name':'titleAuthorImprintCollation_imprint_printers',#grid
    'print.name-name':'',

    'sort_year':'titleAuthorImprintCollation_sortYear_sortYear',
    'illustrations':'titleAuthorImprintCollation_collation_illustrations', 
    'dimensions':'titleAuthorImprintCollation_collation_dimensions', 
    'accompanying_material':'titleAuthorImprintCollation_collation_accompanyingMaterial-term',#grid

    # SERIES
    'series.title':'',
    'series.article':'seriesNotesISBN_series_series-seriesArticle',#grid
    'series.title-series':'seriesNotesISBN_series_series-series',#grid
    'series.number':'seriesNotesISBN_series_series-seriesNo',#grid
    'series.title-issn':'seriesNotesISBN_series_series-ISSNSeries',#grid

    'notes':'seriesNotesISBN_notes_bibliographicalNotes-term',# grid

    'holding':'seriesNotesISBN_notes_holding-holding',#grid
    'ISSN':'seriesNotesISBN_ISSN_ISSN-ISSN',#grid
    #FIX '':'seriesNotesISBN_conference_conference-term',#grid
    
    'serial.continued.from.recordno':'seriesNotesISBN_continuation_continuedFrom-continuedFrom',#grid 
    'serial.continued.as.recordno':'seriesNotesISBN_continuation_continuedAs-continuedAs',#grid

    # Abstract
    # Abstract and subject term fields
    'material_type':'',
    'material_type-term':'abstractAndSubjectTerms_materialType', 
    'language_code':'',
    'language_code-term':'abstractAndSubjectTerms_language', 
    'level':'abstractAndSubjectTerms_level',
    'comments':'abstractAndSubjectTerms_notes-note', 
    'class_number':'',
    'class_number-term':'abstractAndSubjectTerms_classNumber',

    'keyword.type':'',
    'keyword.type-text':'abstractAndSubjectTerms_subjectTerm-subjectTermType', 
    'keyword.contents':'',
    'keyword.contents-term':'abstractAndSubjectTerms_subjectTerm-subjectType', 
    'keyword.proper_name':'',
    'keyword.proper_name-term':'abstractAndSubjectTerms_subjectTerm-properName', 

    'person.keyword.type':'',
    'person.keyword.type-text':'abstractAndSubjectTerms_personKeywordType-personKeywordType',
    'keyword.contents-term.code':'', 
    'person.keyword.name':'abstractAndSubjectTerms_personKeywordType-name',
    'person.keyword.name-name':'',
    'person.keyword.role':'',
    'person.keyword.role-term':'abstractAndSubjectTerms_personKeywordType-role',

    'geographical_keyword':'',
    'geographical_keyword-term':'abstractAndSubjectTerms_geographicalKeyword', 
    'timeperiod':'',
    'timeperiod-term':'abstractAndSubjectTerms_period',
    'start_date':'abstractAndSubjectTerms_startDate', 
    'end_date':'abstractAndSubjectTerms_endDate',
    'digital_reference':'abstractAndSubjectTerms_digitalReferences_reference-reference', 
    'abstract':'abstractAndSubjectTerms_abstract_abstract-term',

    # Exhibitions
    'exhibition-exhibition':'exhibitionsAuctionsCollections_exhibition-exhibitionName', 
    'exhibition-exhibition.notes':'exhibitionsAuctionsCollections_exhibition-notes',

    'auction':'',
    'auction.name':'',
    'auction.name-auction':'exhibitionsAuctionsCollections_auction-auctionName',
    'auction.notes':'exhibitionsAuctionsCollections_auction-notes',
    'collection.notes':'exhibitionsAuctionsCollections_collection-notes',

    # Ignore fields from relation
    'exhibition': '',
    'exhibition-exhibition.date.start': '',
    'exhibition-exhibition.date.end':'',
    'exhibition-exhibition.organiser':'',
    'exhibition-old.exhibition.date.start':'',
    'exhibition-exhibition.venue':'',
    'exhibition-exhibition.place':'',
    'exhibition-exhibition-title':'',
    'exhibition-exhibition-date.start':'',
    'exhibition-exhibition-date.end':'',
    'exhibition-exhibition-organiser':'',
    'exhibition-exhibition-venue':'',
    'exhibition-exhibition-venue.place':'',

    # Reproductions
    'reproduction':'',
    'reproduction-reproduction.reference-reference_number': 'reproductions_reproduction-reference',
    'reproduction-reproduction.reference-image_reference': 'reproductions_reproduction-identifierURL',
    'reproduction-reproduction.notes': 'reproductions_reproduction-notes',

 	# Relations
 	'volume':'relations_volume', 
 	'use':'relations_analyticalCataloguing_partOf-partOf',
    'used_for':'relations_analyticalCataloguing_consistsOf-consistsOf',
    'object.object_number':'relations_museumobjects',

    # Ignore fields from relation with object
    'object.object_number-object_number':'',
    'object.object_number-object_name':'',
    'object.object_number-title':'',
    'object.object_number-creator':'',
    'object.title':'',
    'object.object_name':'',
    'object.creator':'',

    # Free fields
    'free_field.date':'freeFieldsAndNumbers_freeFields-date',
    'free_field.type':'freeFieldsAndNumbers_freeFields-type',
    'free_field.confidential':'freeFieldsAndNumbers_freeFields-confidential',
    'free_field.content':'freeFieldsAndNumbers_freeFields-contents',
    'old_number_type':'freeFieldsAndNumbers_otherNumber-type',
    'old_number_contents':'freeFieldsAndNumbers_otherNumber-contents',
    'PPN':'freeFieldsAndNumbers_PPN',

    # Copies and shelf marks
    'shelf_mark':'copiesAndShelfMarks_defaultShelfMark',
    'copy.number':'',
    'copy.number-copy_number':'copiesAndShelfMarks_copyDetails-copyNumber',
    'copy.number-loan_status':'',
    'copy.number-loan_status-text':'', # availability, we are not using this field
    'copy.status':'',
    'copy.status-text': '',
    'copy.number-shelfmark':'copiesAndShelfMarks_copyDetails-shelfMark',
    'loan_category':'',
    'loan_category-term':'copiesAndShelfMarks_copyDetails-loanCategory',
    'site':'',
    'site-term':'copiesAndShelfMarks_copyDetails-site',
    "copy.remarks": 'copiesAndShelfMarks_copyDetails-locationNotes',

    # Ignore fields from relation with an item from the bilbiotheek
    'copy.number-serial.holding':'',
    'copy.number-serial.missing':'',
    'copy.serial.holding':'',
    'copy.serial.missing':'',
    'copy.shelfmark': '',
    'copy.number-location.note':'', 
    'copy.number-L1':'', 
    'copy.number-la':'', 
    'source.volume':'',

    # Conference
    'child':'',
    'conference':'',
    'parent':'',
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
    'input.notes':'',
    'record':'',

    'datasets.collect':'',
	'datasets.collect-text':'',
	"datasets.document.source":"",
	"datasets.document.source-text":"",

	"source.title-lead_word":"",
	"source.title-material_type":"",
	"source.title-title":"",
	"source.month":"",
	"pagination":"",
	"source.issue":"",
	"source.publication_years":"",

	"source.title.article":"",
	"source.material_type":"",
	"source.title":"",
	"source.pagination":"",
	"series.title-lead_word":"",

    "reproduction":"",
    "reproduction-reproduction.format":"",
    "reproduction-reproduction.reference":"",
    "reproduction-reproduction.reference-format":"",
    "reproduction-reproduction.reference-production_date":"",
    "reproduction-reproduction.reference-reproduction_type":"",
    "reproduction-reproduction.reference-creator":"",
    "reproduction-reproduction.date":"",
    "reproduction-reproduction.type":"",
    "reproduction-reproduction.creator":"",
    "reproduction-reproduction.identifier_URL":"",
    "object.object_number-object_number":"",
    "object.object_number-object_name":"",
    "object.object_number-title":"",
    "object.object_number-creator":"",
    "object.object_name":"",
    "copy.serial.missing":"",
    "internal_link_priref":"",
    "internal_link_title":"",
    "object.title":"",
    "auction.place":"",
    "auction.number":"",
    "auction.auctioneer":"",
    "auction.startdate":"",
    "auction.enddate":"",
    "auction.name-place":"",
    "auction.name-auction_number":"",
    "auction.name-auctioneer":"",
    "auction.name-date_early":"",
    "auction.name-date_late":"",
    "auction.name-commissair-priseur":"",
    "auction.name-location":"",
    "auction.name-collector":"",
    "auction.commissair-priseur":"",
    "auction.location":"",
    "object.creator":"",
    "copy.status":"",

    "copy.status":"",
    "copy.status-text":"",
    "copy.number-serial.holding":"",
    "copy.number-serial.missing":"",
    "copy.number-loan_status":"",
    "copy.number-loan_status-text":"",
    "copy.number-L1":"",
    "copy.number-la":"",
    
    "keyword.contents":"",
    "keyword.contents-term.code":"",
    "auction.collector":"",

    "exhibition-exhibition.date.start":"",
    "exhibition-exhibition.date.end":"",
    "exhibition-old.exhibition.date.end":"",
    "exhibition-exhibition-date.start":"",
    "exhibition-exhibition-date.end":"",
    "exhibition-exhibition-title":"",
    "exhibition-exhibition-organiser":"",
    "exhibition-exhibition-venue":"",
    "exhibition-exhibition-venue.place":"",
    "exhibition-exhibition.organiser":"",
    "exhibition-old.exhibition.date.start":"",
    "exhibition-exhibition.venue":"",
    "exhibition-exhibition.place":"",
    "copy.serial.holding":"",

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

    'series.issn':"",
}





