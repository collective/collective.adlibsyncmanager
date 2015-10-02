#!/usr/bin/env python
# -*- coding: utf-8 -*-

BOOK_CORE = {
    
	"priref":"priref",
    "record":'',
	
    # Title and author
    'lead_word':'titleAuthorImprintCollation_titleAuthor_article', 
	'title':'titleAuthorImprintCollation_titleAuthor_title-title',
    'statement_of_responsibility':'titleAuthorImprintCollation_titleAuthor_statementOfRespsib', 
    'author.name':'titleAuthorImprintCollation_titleAuthor_author-authors',
    'author.name-name':'',
    'author.role-term': 'titleAuthorImprintCollation_titleAuthor_author-roles',
    'Illustrator':'',
    'Illustrator-illustrator.role':'',
    'Illustrator-illustrator.name':'titleAuthorImprintCollation_titleAuthor_illustrator-illustrators',
    'Illustrator-illustrator.role-term':'titleAuthorImprintCollation_titleAuthor_illustrator-roles',
    'Illustrator-illustrator.name-name':'',
    'corporate_author-name':'', 
    'corporate_author':'titleAuthorImprintCollation_titleAuthor_corpAuthor-corpAuthor',
    'edition':'titleAuthorImprintCollation_edition_edition',
    'place_of_publication':'titleAuthorImprintCollation_imprint_place-term', 
    'publisher':'titleAuthorImprintCollation_imprint_publisher-publisher',
    'publisher-name':'',
    'year_of_publication':'titleAuthorImprintCollation_imprint_year', 
    'print.place':'',
    'print.place-term':'titleAuthorImprintCollation_imprint_placesPrinted',
    'print.name':'titleAuthorImprintCollation_imprint_printer-printer', 
    'print.name-name':'',
    'sort_year':'titleAuthorImprintCollation_sortYear_sortYear',
    'pagination':'titleAuthorImprintCollation_collation_pagination', 
    'illustrations':'titleAuthorImprintCollation_collation_illustrations',
    'dimensions':'titleAuthorImprintCollation_collation_dimensions', 
    'accompanying_material':'titleAuthorImprintCollation_collation_accompanyingMaterial-term',

    # Series, Notes ISBN
    'series.article':'seriesNotesISBN_series_series-seriesArticle',
    'series.title':'',
    'series.title-series':'seriesNotesISBN_series_series-series',
    'series.number':'seriesNotesISBN_series_series-seriesNo',
    'series.issn': 'seriesNotesISBN_series_series-ISSNSeries',
    'series.title-issn':'',
    'series.title-lead_word':'',
    'subseries.article':'seriesNotesISBN_series_subseries-subseriesArticle',
    'subseries.title-series':'seriesNotesISBN_series_subseries-subseries',
    'subseries.title-issn':'',
    'subseries.title-lead_word':'',
    'subseries.number':'seriesNotesISBN_series_subseries-subseriesNo',
    'subseries.issn': 'seriesNotesISBN_series_subseries-ISSNSubseries',
	'notes':'seriesNotesISBN_notes_bibliographicalNotes-term',
    'isbn':'seriesNotesISBN_ISBN_ISBN-ISBN',
    'price':'seriesNotesISBN_ISBN_ISBN-price',
    'binding_method':'seriesNotesISBN_ISBN_ISBN-bindingMethod',
    'ISSN':'seriesNotesISBN_ISBN_ISSN-ISSN',


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
 	'use':'relations_analyticalCataloguing_partOf',
    'used_for':'relations_analyticalCataloguing_consistsOf',
    'object.object_number':'relations_museumObjects-objectNo',

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

    # Conference
    'conference':'',

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

