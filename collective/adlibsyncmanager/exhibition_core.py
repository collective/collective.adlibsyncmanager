#!/usr/bin/env python
# -*- coding: utf-8 -*-


EXHIBITION_CORE = {
	'priref': 'priref',
	'date.start': 'start_date', 
	'date.end':'end_date', 
    'title': 'title',
    'alternativetitle':'',
	'alternativetitle-title.alternative':'exhibitionsDetails_exhibition_altTitle-title',
	'alternativetitle-title.alternative.type':'exhibitionsDetails_exhibition_altTitle-type',

    'notes':'exhibitionsDetails_exhibitions_notes-note', 
    'organiser':'',
    'organiser-organiser':'exhibitionsDetails_organizingInstitutions-name', # relation
    'organiser-organiser-name': '',
    
    'venue-venue.date.start':'exhibitionsDetails_itinerary-startDate',
    'venue-venue.date.end':'exhibitionsDetails_itinerary-endDate',
    'venue-venue':'exhibitionsDetails_itinerary-venue', # relation
    'venue-venue-name': '',
    'venue-venue.place-term':'exhibitionsDetails_itinerary-place', # gridlist
    'venue-venue.notes':'exhibitionsDetails_itinerary-notes',

    'documentation':'',
    'documentation-documentation.title-lead_word':'documentation_documentation-article',
    'documentation-documentation.title':'documentation_documentation-title', # relation
    'documentation-documentation.page_reference':'documentation_documentation-pageMark',
    'documentation-documentation.notes':'documentation_documentation-notes',


    'object.object_number':'linkedObjects_linkedObjects-objectNumber', # relation

    # Ignored tags

    # From relation with object
    'object.object_number-object_number':'',
    'object.object_number-object_name':'',
    'object.object_number-title':'',
    'object.object_number-creator':'',
    'object.title':'',
    'object.object_name':'',
    'object.creator':'',
    'object.object_number':'',

    # from relation with person
    'organiser-organiser-name':'',
    'organiser-organiser-address.country':'',
    'organiser-organiser-fax':'',
    'organiser-organiser-address.place':'',
    'organiser-organiser-address.postal_code':'',
    'organiser-organiser-address':'',
    'organiser-organiser-phone':'',
    'organiser-organiser.address':'',
    'organiser-organiser.country':'',
    'organiser-organiser.fax':'',
    'organiser-organiser.place':'',
    'organiser-organiser.postal_code':'',
    'organiser-organiser.telephone':'',

    # from a relation with  bibliotheek content type
    'documentation-documentation.author':'',
    'documentation-documentation.shelfmark':'',
    'documentation-documentation.title.article':'',
    'documentation-documentation.title-author.name':'',
    'documentation-documentation.title-shelf_mark':'',
    'documentation-documentation.title-title':'',

    # from a relation with person
    'venue':'',
    'venue-venue.place':'',


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

