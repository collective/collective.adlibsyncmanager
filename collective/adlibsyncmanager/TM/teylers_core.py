#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Adlib - Plone object

CORE = {
    "priref":"priref",
    "Label-label.text":"text",
    "Content_person-content.person.name-name":"creator-creator",

    "Author-author.name-name": "object_author-creator",
    "Author-author.role-term": "object_author-role",

    "Production-creator-name":"creator-creator",
    "Production-creator.qualifier":"creator-qualifier",
    "Production-creator.role-term":"creator-role",
    "Production-creator-birth.date-start":"creator-date_of_birth",
    "Production-creator-death.date-start":"creator-date_of_death",
    
    "Title-title":"title",

    "administration_name":"administration_name",
    "":"author",
    "Illustrator-illustrator.name-name":"illustrator",
    "object_category":"object_category",
    "":"book_title",
    "":"translated_title",
    "Object_name-object_name-term":"object_type",

    "Production_date-production.date.end":"object_dating-end",
    "Production_date-production.date.start":"object_dating-start",
    "Production_date-production.date.start.prec":"object_dating-start_precision",
    "Production_date-production.date.end.prec":"object_dating-end_precision",

    "":"fossil_dating",

    "Production-production.place-term":"object_production_period-place",
    "production.period-term":"object_production_period-period",
    #"production.reason-term":"object_production_period-reason",
    #"production.notes":"object_production_period-notes",

    "":"production_notes",
    "":"search_year",
    "Material-material-term":"object_material-material",
    "material_type-term":"object_material-material",
    "Technique-technique-term":"technique",

    "Dimension-dimension.type-term":"object_dimension-type",
    "Dimension-dimension.unit-term":"object_dimension-unit",
    "Dimension-dimension.value":"object_dimension-value",
    "Dimension-dimension.part":"object_dimension-part",
    "Dimension-dimension.notes":"object_dimension-notes",

    "place_of_publication":"location",
    "publisher-name":"publisher",
    "Taxonomy-taxonomy.scientific_name-common_name":"common_name",
    "Taxonomy-taxonomy.scientific_name-scientific_name":"scientific_name",
    "":"chemical_composition",
    "field_coll.place-term":"field_coll_place",

    #"object_number":"object_number",
    "shelf_mark":"object_number",# BOOKS 
    "Description-description":"object_descriptions-description",

    "Inscription-inscription.content":"object_inscription-content",
    "Inscription-inscription.type-term":"object_inscription-type",

    "Acquisition_source-acquisition.source-name":"acquisition_source",
    "credit_line":"credit_line",
    "Reproduction-reproduction.reference-reference_number":"object_reproduction_reference-reference",
    "reproduction-reproduction.reference-reference_number":"object_reproduction_reference-reference",
    
    "Digital_reference-digital_reference":"object_digital_reference-reference",
    "Digital_reference-digital_reference.description":"object_digital_reference-description",
    
    "year_of_publication": "object_dating-start",

    #Ignored tags

    "Description":"",
    "Inscription":"",
    "Label":"",
    "Material":"",
    "Object_name":"",
    "Production":"",
    "Reproduction":"",
    "Technique":"",
    "Title":"",

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

    "record_number":"",
    "Label-label.date":"",
    "Label-label.type":"",
    "Label-label.type-text":"",
    "Label-label.source":"",
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
    "Illustrator":"",
    "Illustrator-illustrator.name":"",
    "Illustrator-illustrator.role":"",
    "record_access.owner":"",
    "Digital_reference":"",
    "notes":"",
    "Author":"",
    "Author-author.name":"",
    "Author-author.role":"",
} 


