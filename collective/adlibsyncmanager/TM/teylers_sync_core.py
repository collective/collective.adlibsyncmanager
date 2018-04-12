#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Adlib - Plone object

CORE = {

    "priref":"priref",

    "Title-title-value": "title",
    "Label-label.text": "text",
    "Label-label.type": "",

    "gepubliceerd": "record_published",
    "in_museum": "in_museum",
    "content.motif.general-value": "content_motif-motif",
    "collection":"",
    "content.motif.general":"",

    "Production":"repeatable-creator",
    "Production-creator-name-value":"creator-name",
    "Production-creator.qualifier":"creator-qualifier",
    "Production-creator.role-value":"creator-role",
    "Production-creator-birth.date.start":"creator-birth_date_start",
    "Production-creator-birth.date.end":"creator-birth_date_end",
    "Production-creator-death.date.start":"creator-death_date_start",
    "Production-creator-death.date.end":"creator-death_date_end",
    "Production-creator-birth.place-value":"creator-birth_place",
    "Production-creator-death.place-value":"creator-death_place",
    "Production-creator-url":"creator-url",
    "Production-creator-priref":"creator-priref",
    "Production-creator-equivalent_name-value":"creator-equivalent_name",
    "production.date.notes":"production-notes",

    "Production_date":"repeatable-production",    
    "Production_date-production.date.end": "production-date_end",
    "Production_date-production.date.end.prec": "production-date_end_precision",
    "Production_date-production.date.start": "production-date_start",
    "Production_date-production.date.start.prec": "production-date_start_precision",

    "techniek.vrije.tekst":"technique-technique",
    
    "Object_name":"repeatable-object_name",
    "Object_name-object_name-value": "object_name-name",
    "object_number":"object_number",
    "collection-value":"collection-term",

    "acquisition.method":"",
    "acquisition.method-value": "acquisition-method",
    "acquisition.date": "acquisition-date",
    "acquisition.date.precision": "acquisition-date_precision",

    "Dimension":"repeatable-dimension",
    "Dimension-dimension.value": "dimension-value",
    "Dimension-dimension.type-value": "dimension-type",
    "Dimension-dimension.unit-value": "dimension-unit",
    "Dimension-dimension.precision": "dimension-precision",
    "Dimension-dimension.notes": "dimension-notes",
    "dimension.free": "",

    #"Material-material-value":"material-material",
    "Material-material-value":"",
    "Inscription":"repeatable-inscription",
    "Inscription-inscription.content":"inscription-content",
    "Inscription-inscription.method":"inscription-method",
    "Inscription-inscription.position-value":"inscription-position",
    "Inscription-inscription.type-value":"inscription-type",
    "Inscription-inscription.description":"inscription-description",
    "Inscription-inscription.notes":"inscription-notes",
    
    "physical_description": "physical_description", 
    
    "Associated_subject":"repeatable-associated_subject",
    "Associated_subject-association.subject-value": "associated_subject-subject",
    "Associated_subject-association.subject.association-value": "associated_subject-association",
    "Associated_subject-association.subject.date.start": "associated_subject-date",
    "Associated_subject-association.subject.note": "associated_subject-notes",

    "Associated_period": "repeatable-associated_period",
    "Associated_period-association.period-value":"associated_period-period",
    "Associated_person-association.person-value": "associated_person-person",


    "notes":"notes-note",

    #TODO Locations

    "current_location.name": "current_location-name",
    "defaultlocation": "",
    "defaultlocation-location.default.name": "",
    "defaultlocation-location.default.context": "",
    

    #TODO exhibitions
    "Exhibition":"repeatable-exhibitions",

    "Exhibition-exhibition":"",
    "Exhibition-exhibition-title":"exhibitions-title",
    "Exhibition-exhibition-venue":"",
    "Exhibition-exhibition-venue-value":"exhibitions-venue",
    "Exhibition-exhibition-venue.place":"",
    "Exhibition-exhibition-venue.place-value":"exhibitions-place",
    "Exhibition-exhibition-venue.date.start":"exhibitions-date_start",
    "Exhibition-exhibition-venue.date.end":"exhibitions-date_end",
    "Exhibition-exhibition-object.object_number":"",
    "Exhibition-exhibition-priref":"",
    "Exhibition-exhibition-notes": "",
    "Exhibition-exhibition-nummer_cm": "exhibitions-nummer_cm",
    "Exhibition-exhibition-reproduction.reference":"",
    "Exhibition-exhibition-reproduction.reference-reference_number":"",
    "Exhibition-exhibition-reproduction.reference-record_access.user":"",

    #TODO objects
    "Part_of":"",
    "Part_of-part_of_reference":"",
    "Related_object":"",
    "Related_object-related_object.reference":"",

    #TODO Documentation:
    "Documentation": "",
    "Documentation-documentation.title": "",
    "Documentation-documentation.title-title": "documentation-title",
    "Documentation-documentation.title-lead_word": "",
    "Documentation-documentation.title-lead_word-value": "documentation-lead_word",
    "Documentation-documentation.title-author.name": "",
    "Documentation-documentation.title-author.name-value": "documentation-author",
    "Documentation-documentation.title-statement_of_responsibility": "",
    "Documentation-documentation.title-statement_of_responsibility-value": "documentation-statement_of_responsibility",
    "Documentation-documentation.page_reference":"documentation-page_references",
    "Documentation-documentation.title-priref": "",
    
    "Documentation-documentation.title-place_of_publication":"",
    "Documentation-documentation.title-place_of_publication-value":"documentation-place_of_publication",
    "Documentation-documentation.title-year_of_publication":"documentation-year_of_publication",

    "Documentation-documentation.title-copy.number":"",
    "Description":"",
    "Description-description":"",

    "Condition":"",
    "Condition-condition":"",
    "Condition-condition-value":"",
    "Condition-condition.notes":"",
    
    #TODO others:
    "Highres":"",
    "institution.name": "",
    "institution.name-value": "",
    "owner_hist.date.start":"",
    "owner_hist.date.start":"",
    "owner_hist.owner":"",
    "owner_hist.owner-value":"",
    "owner_hist.owner":"",
    "owner_hist.owner-value":"",
    #images
    "Reproduction":"",
    "Reproduction-reproduction.reference":"",
    "acquisition.notes":"",

    # # # # # # # # #
    # IGNORE TAGS   #
    # # # # # # # # #

    "Associated_period-association.period":"",
    "Associated_person":"repeatable-associated_person",
    "Associated_person-association.person":"",

    "Associated_subject-association.subject":"",
    "Associated_subject-association.subject.association":"",

    "Dimension-dimension.part":"",
    "Dimension-dimension.type":"",
    "Dimension-dimension.unit":"",
    "Edit":"",
    "Edit-edit.date":"",
    "Edit":"",
    "Edit-edit.date":"",
    "Edit":"",
    "Edit-edit.date":"",
    "Edit":"",
    "Edit-edit.date":"",
    "Edit":"",
    "Edit-edit.date":"",
    "input.date":"",

    "Inscription-inscription.position":"",
    "Inscription-inscription.type":"",
    "Label":"",
    "Material":"",
    "Material-material":"",
    "Object_name":"",
    "Object_name-object_name":"",
    "Production-creator":"",
    "Production-creator-name":"",
    "Production-creator-birth.place":"",
    "Production-creator-death.place":"",
    "Production-creator.role":"",
    "Production-creator-equivalent_name":"",
    "Production-creator-used_for":"",
    "Production-creator-used_for-value":"",
    "Title":"",
    "Title-title":""
} 


