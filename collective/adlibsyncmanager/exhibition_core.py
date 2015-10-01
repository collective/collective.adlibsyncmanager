#!/usr/bin/env python
# -*- coding: utf-8 -*-


EXHIBITION_CORE = {
	'priref': 'priref',
	'date.start': 'start_date', 
	'date.end':'end_date', 
    'title': 'title',
	'alternativetitle-title.alternative':'exhibitionsDetails_exhibition_altTitle-title',
	'alternativetitle-title.alternative.type':'exhibitionsDetails_exhibition_altTitle-type',

    'notes':'exhibitionsDetails_exhibitions_notes-note', 
    'organiser-organiser':'exhibitionsDetails_organizingInstitutions-name', # relation
    'organiser-organiser-name': '',
    
    'venue-venue.date.start':'exhibitionsDetails_itinerary-startDate',
    'venue-venue.date.end':'exhibitionsDetails_itinerary-endDate',
    'venue-venue':'exhibitionsDetails_itinerary-venue', # relation
    'venue-venue-name': '',
    'venue-venue.place-term':'exhibitionsDetails_itinerary-place', # gridlist
    'venue-venue.notes':'exhibitionsDetails_itinerary-notes',

    'documentation-documentation.title-lead_word':'documentation_documentation-article',
    'documentation-documentation.title':'documentation_documentation-title', # relation
    'documentation-documentation.page_reference':'documentation_documentation-pageMark',
    'documentation-documentation.notes':'documentation_documentation-notes',

    'object.object_number':'linkedObjects_linkedObjects-objectNumber', # relation

    'Edit-edit.name':'',
    'Edit-edit.time':'',
    'Edit-edit.date':'',
    'Edit-edit.source':'',
    'Edit-edit.notes':'',
    'input.source':''
}

