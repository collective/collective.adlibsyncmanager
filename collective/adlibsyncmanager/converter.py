#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""
from Acquisition import aq_parent, aq_inner

from plone import api

from z3c.relationfield.schema import RelationList

import fnmatch
from lxml import etree
import urllib2, urllib
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
from plone.multilingual.interfaces import ITranslationManager
import datetime
import os
import csv
import unicodedata
import sys

from Products.CMFCore.utils import getToolByName
from zope.intid.interfaces import IIntIds
import re
import AccessControl
import transaction
import time
import sys
from DateTime import DateTime
from plone.i18n.normalizer import idnormalizer
from Testing.makerequest import makerequest
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from plone.dexterity.utils import createContentInContainer
from collective.leadmedia.utils import addCropToTranslation
from collective.leadmedia.utils import imageObjectCreated
from plone.app.textfield.value import RichTextValue

from z3c.relationfield import RelationValue
from zope import component


"""

["productionDating__production_productionRole",
"productionDating__production_productionPlace",
"productionDating__production_schoolStyle",

"physicalCharacteristics__technique",
"physicalCharacteristics__material",
"physicalCharacteristics__dimension",
"physicalCharacteristics__dimensions_unit",


"iconography__generalSearchCriteria_generalThemes",
"iconography__generalSearchCriteria_specificThemes",
"iconography__contentSubjects",

"inscriptionsMarkings__inscriptionsAndMarkings_type",
"inscriptionsMarkings__inscriptionsAndMarkings_role",
"inscriptionsMarkings__inscriptionsAndMarkings_script",

"associations__associatedSubjects_subject",
"associations__associatedSubjects_period",

"valueInsurance__valuations_currency",

"conditionConservation__conditions_condition",
"conditionConservation__preservationForm",

"acquisition__methods",
"acquisition__places",

"ownershipHistory__history_exchangeMethod",
"ownershipHistory__history_place",

"location__normalLocation_normalLocation",
"location__currentLocation",

"fieldCollection__fieldCollection_collector_role",
"fieldCollection__fieldCollection_method",
"fieldCollection__fieldCollection_place",
"fieldCollection__fieldCollection_placeFeature",
"fieldCollection__habitatStratigraphy_stratigraphy"]
"""

idxs = ["identification__identification_collections",
        "productionDating__production_productionRole",
        "productionDating__production_productionPlace",
        "productionDating__production_schoolStyle",
        "physicalCharacteristics__technique",
        "physicalCharacteristics__material",
        "physicalCharacteristics__dimension",
        "physicalCharacteristics__dimensions_unit",
        "iconography__generalSearchCriteria_generalThemes",
        "iconography__generalSearchCriteria_specificThemes",
        "iconography__contentSubjects",
        "inscriptionsMarkings__inscriptionsAndMarkings_type",
        "inscriptionsMarkings__inscriptionsAndMarkings_role",
        "inscriptionsMarkings__inscriptionsAndMarkings_script",
        "associations__associatedSubjects_subject",
        "associations__associatedSubjects_period",
        "valueInsurance__valuations_currency",
        "conditionConservation__conditions_condition",
        "conditionConservation__preservationForm",
        "acquisition__methods",
        "acquisition__places",
        "ownershipHistory__history_exchangeMethod",
        "ownershipHistory__history_place",
        "location__normalLocation_normalLocation",
        "location__currentLocation",
        "fieldCollection__fieldCollection_collector_role",
        "fieldCollection__fieldCollection_method",
        "fieldCollection__fieldCollection_place",
        "fieldCollection__fieldCollection_placeFeature",
        "fieldCollection__habitatStratigraphy_stratigraphy",
        "fieldCollection__fieldCollection_event",
        "identification_identification_objectNumber",
        "identification_objectName_category",
        "identification_objectName_objectname"]

class Converter:
    
    def __init__(self, APIMigrator):
        self.api = APIMigrator
        self.idxs = idxs


    def productionDating__production_periods(self, item):
        self.log("! Converting ! Identification")

        original = 'productionDating_dating_period'
        target = 'productionDating_production_periods'
        term = 'period'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    if to_convert != "":
                        converted.append(to_convert)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['productionDating__production_periods'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Identification
    def identification__identification_collections(self, item):
        self.log("! Converting ! Identification")

        original = 'identification_identification_collection'
        target = 'identification_identification_collections'
        term = 'term'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []
            t = getattr(item, target)

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    if to_convert != "":
                        converted.append(to_convert)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['identification__identification_collections'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Production dating
    def productionDating_production_productionRole_place(self, item):
        self.log("! Converting ! Production role / place")

        original = 'productionDating_production'
        target = 'productionDating_productionDating'
        term = 'role'
        extra_term = 'place'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    else:
                        to_convert = ""
                    if line[extra_term] != None:
                        to_convert_extra = line[extra_term].encode('ascii', 'ignore')
                    else:
                        to_convert_extra = ""

                    # schema dependent
                    qualifier = line['qualifier']
                    production_notes = line['production_notes']

                    schema = {
                        "makers": [],
                        "qualifier": qualifier,
                        "role": [to_convert],
                        "production_notes": production_notes,
                        "place": [to_convert_extra]
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['productionDating__production_productionRole'])
                item.reindexObject(idxs=['productionDating__production_productionPlace'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def productionDating_production_productionPlace(self, item):
        # deprecated
        item.reindexObject(idxs=['productionDating__production_productionPlace'])
        return True

    def productionDating_production_schoolStyle(self, item):
        original = 'productionDating_production_schoolStyle'
        target = 'productionDating_production_schoolstyle'
        term = 'term'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    else:
                        to_convert = ""

                    schema = {
                        "term": [to_convert]
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['productionDating__production_schoolStyle'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Physical Characteristics
    def physicalCharacteristics_technique(self, item):
        original = 'physicalCharacteristics_techniques'
        target = 'physicalCharacteristics_technique'
        term = 'technique'

        print "convert technique"
        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []
            if curr:
                for line in curr:

                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    else: 
                        to_convert = ""
                    part = line['part']

                    notes = line['notes']

                    schema = {
                        "technique": [to_convert],
                        "part": part,
                        "notes": notes
                    }

                    converted.append(schema)

                print "CONVERTED:"
                print converted

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['physicalCharacteristics__technique'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def physicalCharacteristics_material(self, item):
        original = 'physicalCharacteristics_materials'
        target = 'physicalCharacteristics_material'
        term = 'material'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    part = line['part']
                    notes = line['notes']

                    schema = {
                        "material": [to_convert],
                        "part": part,
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['physicalCharacteristics__material'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def physicalCharacteristics_dimension_unit(self, item):
        original = 'physicalCharacteristics_dimensions'
        target = 'physicalCharacteristics_dimension'
        term = 'dimension'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    
                    part = line['part']
                    notes = line['notes']
                    value = line['value']
                    unit = line['unit']
                    precision = line['precision']

                    schema = {
                        "dimension": [to_convert],
                        "part": part,
                        "notes": notes,
                        "value": value,
                        "precision": " ",
                        "units": unit
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['physicalCharacteristics__dimension'])
                #item.reindexObject(idxs=['physicalCharacteristics__dimensions_unit'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")
        
        return True

    def physicalCharacteristics_dimensions_unit(self, item):
        # deprecated
        item.reindexObject(idxs=['physicalCharacteristics__dimensions_unit'])
        return True

    # Iconography
    def iconography_generalSearchCriteria_generalThemes(self, item):

        original = 'iconography_generalSearchCriteria_generalTheme'
        target = 'iconography_generalSearchCriteria_generalThemes'
        term = 'term'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')

                    schema = {
                        "term": [to_convert],
                    }

                    converted.append(schema)


                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['iconography__generalSearchCriteria_generalThemes'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")
        
        return True

    def iconography_generalSearchCriteria_specificThemes(self, item):

        original = 'iconography_generalSearchCriteria_specificTheme'
        target = 'iconography_generalSearchCriteria_specificThemes'
        term = 'term'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []
            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')

                    schema = {
                        "term": [to_convert],
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['iconography__generalSearchCriteria_specificThemes'])
                self.log("! Converted !")
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def iconography_contentSubjects(self, item):
        original = 'iconography_contentSubject'
        target = 'iconography_contentSubjects'
        term = 'subject'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    position = line['position']
                    subjectType = line['subjectType']
                    taxonomicRank = line['taxonomicRank']
                    scientificName = line['scientificName']
                    notes = line['notes']

                    schema = {
                        "subject": [to_convert],
                        "position": position,
                        "subjectType": subjectType,
                        "taxonomicRank": taxonomicRank,
                        "scientificName": scientificName,
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['iconography__contentSubjects'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Inscriptions and markings
    def inscriptionsMarkings_inscriptionsAndMarkings_type_role_script(self, item):
        original = 'inscriptionsMarkings_inscriptionsMarkings'
        target = 'inscriptionsMarkings_inscriptionsAndMarkings'
        term = 'type'
        extraterm = 'role'
        extraextraterm = 'script'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')

                    role_convert = ""
                    if line[extraterm] != None:
                        role_convert = line[extraterm].encode('ascii', 'ignore')
                    
                    script_convert = ""
                    if line[extraextraterm] != None:
                        script_convert = line[extraextraterm].encode('ascii', 'ignore')

                    position  = line['position']
                    method = line['method']
                    date = line['date']
                    content = line['content']
                    description = line['description']
                    interpretation = line['interpretation']
                    language = line['language']
                    transliteration = line['transliteration']
                    notes = line['notes']

                    schema = {
                        "type": [to_convert],
                        "role": [role_convert],
                        "script": [script_convert],
                        "creators": [],
                        "position":position,
                        "method": method,
                        "date": date,
                        "content": content,
                        "description": description,
                        "interpretation": interpretation,
                        "language": language,
                        "transliteration": transliteration,
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)

                self.log("! Reindexing !")
                item.reindexObject(idxs=['inscriptionsMarkings__inscriptionsAndMarkings_type'])
                item.reindexObject(idxs=['inscriptionsMarkings__inscriptionsAndMarkings_role'])
                item.reindexObject(idxs=['inscriptionsMarkings__inscriptionsAndMarkings_script'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def inscriptionsMarkings_inscriptionsAndMarkings_role(self, item):
        # deprecated
        item.reindexObject(idxs=['inscriptionsMarkings__inscriptionsAndMarkings_role'])
        return True

    def inscriptionsMarkings_inscriptionsAndMarkings_script(self, item):
        # deprecated
        item.reindexObject(idxs=['inscriptionsMarkings__inscriptionsAndMarkings_script'])
        return True

    # Associations
    def associations_associatedSubjects_subject(self, item):
        original = 'associations_associatedSubject'
        target = 'associations_associatedSubjects'
        term = 'subject'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    association = line['association']
                    subjectType = line['subjectType']
                    taxonomicRank = line['taxonomicRank']
                    scientificName = line['scientificName']
                    notes = line['notes']

                    schema = {
                        "subject": [to_convert],
                        "association": association,
                        "subjectType": subjectType,
                        "taxonomicRank": taxonomicRank,
                        "scientificName": scientificName,
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)

                self.log("! Reindexing !")
                item.reindexObject(idxs=['associations__associatedSubjects_subject'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def associations_associatedSubjects_period(self, item):

        original = 'associations_associatedPeriod'
        target = 'associations_associatedPeriods'
        term = 'period'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    association = line['association']
                    startDate = line['startDate']
                    endDate = line['endDate']
                    notes = line['notes']

                    schema = {
                        "period": [to_convert],
                        "association": association,
                        "startDate": startDate,
                        "endDate": endDate,
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)

                self.log("! Reindexing !")
                item.reindexObject(idxs=['associations__associatedSubjects_period'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Value and insurance
    def valueInsurance_valuations_currency(self, item):
        #item.reindexObject(idxs=['valueInsurance_valuations_currency'])
        return True

    # Condition and conservation
    def conditionConservation_conditions_condition(self, item):
        original = 'conditionConservation_condition'
        target = 'conditionConservation_conditions'
        term = 'condition'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    part = line['part']
                    checked_by = line['checked_by']
                    date = line['date']
                    notes = line['notes']

                    schema = {
                        "condition": [to_convert],
                        "part": part,
                        "checked_by": checked_by,
                        "date": date,
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)

                self.log("! Reindexing !")
                item.reindexObject(idxs=['conditionConservation__conditions_condition'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def conditionConservation_preservationForm(self, item):
        original = 'conditionConservation_enviromental_condition'
        target = 'conditionConservation_preservationForm'
        term = 'preservation_form'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    notes = line['notes']

                    schema = {
                        "preservation_form": [to_convert],
                        "notes": notes
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['conditionConservation__preservationForm'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Acquisition
    def acquisition_methods(self, item):
        original = 'acquisition_method'
        target = 'acquisition_methods'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr:
                converted = [curr.encode('ascii', 'ignore')]
                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['acquisition__methods'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def acquisition_places(self, item):
        original = 'acquisition_place'
        target = 'acquisition_places'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr:
                converted = [curr.encode('ascii', 'ignore')]
                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['acquisition__places'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Ownership history
    def ownershipHistory_history_exchangeMethod(self, item):
        
        original = 'ownershipHistory_exchange_method'
        target = 'ownershipHistory_history_exchangeMethod'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)

            if curr:
                converted = [curr.encode('ascii', 'ignore')]
                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['ownershipHistory__history_exchangeMethod'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def ownershipHistory_history_place(self, item):
        
        
        original = 'ownershipHistory_place'
        target = 'ownershipHistory_history_place'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)

            if curr:
                converted = [curr.encode('ascii', 'ignore')]
                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['ownershipHistory__history_place'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    # Location
    def location_normalLocation_normalLocation(self, item):
        
        original = 'location_normal_location'
        target = 'location_normalLocation_normalLocation'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)

            if curr:
                converted = [curr.encode('ascii', 'ignore')]
                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['location__normalLocation_normalLocation'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")
        
        return True

    def location_currentLocation(self, item):
        original = 'location_current_location'
        target = 'location_currentLocation'
        term = 'location'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    start_date = line["start_date"]
                    end_date = line['end_date']
                    location_type = line['location_type']
                    fitness = line['fitness']
                    notes = line['notes']

                    schema = {
                        "location": [to_convert],
                        "notes": notes,
                        "start_date":start_date,
                        "end_date":end_date,
                        "location_type": location_type,
                        "fitness": fitness
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['location__currentLocation'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")
        
        return True

    # Field collection
    def fieldCollection_fieldCollection_collector_role(self, item):
        #item.reindexObject(idxs=['fieldCollection_fieldCollection_collector_role'])
        return True

    def fieldCollection_fieldCollection_method(self, item):
        original = 'fieldCollection_fieldCollection_method'
        target = 'fieldCollection_fieldCollection_methods'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr:
                new_methods = []

                for line in curr:
                    to_convert = ""
                    if line['term'] != None:
                        to_convert = line['term'].encode('ascii', 'ignore')
                    new_methods.append(to_convert)

                setattr(item, target, new_methods)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['fieldCollection__fieldCollection_method'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def fieldCollection_fieldCollection_place(self, item):
        original = 'fieldCollection_fieldCollection_place'
        target = 'fieldCollection_fieldCollection_places'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr:
                new_places = []

                for line in curr:
                    to_convert = ""
                    if line['term'] != None:
                        to_convert = line['term'].encode('ascii', 'ignore')
                    new_places.append(to_convert)

                setattr(item, target, new_places)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['fieldCollection__fieldCollection_place'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def fieldCollection_fieldCollection_placeFeature(self, item):
        original = 'fieldCollection_fieldCollection_placeFeature'
        target = 'fieldCollection_fieldCollection_placeFeatures'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []
            if curr:
                new_places = []

                for line in curr:
                    to_convert = ""
                    if line['term'] != None:
                        to_convert = line['term'].encode('ascii', 'ignore')
                    new_places.append(to_convert)

                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['fieldCollection__fieldCollection_placeFeature'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def fieldCollection_habitatStratigraphy_stratigraphy(self, item):
        #item.reindexObject(idxs=['fieldCollection_habitatStratigraphy_stratigraphy'])
        return True

    def fieldCollection__fieldCollection_event(self, item):

        original = 'fieldCollection_fieldCollection_event'
        target = 'fieldCollection_fieldCollection_events'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []
            if curr:
                new_places = []

                for line in curr:
                    to_convert = ""
                    if line['term'] != None:
                        to_convert = line['term'].encode('ascii', 'ignore')
                    new_places.append(to_convert)

                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['fieldCollection__fieldCollection_event'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True


    def numbersRelationships__relationshipsWithOtherObjects_relatedObjects_association(self, item):
        original = 'numbersRelationships_relationshipsWithOtherObjects_relatedObject'
        target = 'numbersRelationships_relationshipsWithOtherObjects_relatedObjects'
        term = 'association'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            converted = []

            if curr:
                for line in curr:
                    to_convert = ""
                    if line[term] != None:
                        to_convert = line[term].encode('ascii', 'ignore')
                    
                    relatedObject = line["relatedObject"]
                    notes = line['notes']

                    schema = {
                        "associations": [to_convert],
                        "notes": notes,
                        "relatedObject":relatedObject,
                    }

                    converted.append(schema)

                setattr(item, target, converted)
                
                self.log("! Reindexing !")
                item.reindexObject(idxs=['numbersRelationships__relationshipsWithOtherObjects_relatedObjects_association'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    ##
    ## Extras
    ##

    def fix_original_physicalCharacteristics_dimensions(self, item):
        original ='fix_original_physicalCharacteristics_dimensions'
        target = 'physicalCharacteristics_dimension'
        term = 'precision'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            t = getattr(item, target)

            if item.physicalCharacteristics_dimension:
                for index, line in enumerate(item.physicalCharacteristics_dimension):
                    print line
                    line[term] = " "
                    item.physicalCharacteristics_dimension[index] = line
                    self.log("! UPDATED ! Field dimension updated.")

            #if curr and t:
            #    length = len(t)
            #    for index, line in enumerate(curr):
            #        precision = line[term]
            #        if index < length:
            #            if precision:
            #                t[index][term] = precision
            #            else:
            #                t[index][term] = ""

            
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def transform_schoolStyle(self, item):
        original = 'productionDating_production_schoolStyle'
        target = 'productionDating_production_schoolStyles'
        term = 'term'

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            t = getattr(item, target)
            converted = []
            if curr:
                for line in curr:
                    val = line[term]
                    if val:
                        converted.append(val.encode('ascii', 'ignore'))

                setattr(item, target, converted)
                self.log("! Reindexing !")
                item.reindexObject(idxs=['productionDating__production_schoolStyle'])
                self.log("! Converted !")

        else:
            self.log("! Failed ! Attributes not found. ")

        return True


    ##
    ## UTILS
    ##
    def log(self, text=""):
        if text:
            timestamp = datetime.datetime.today().isoformat()
            print "[%s] %s" %(str(timestamp), str(text))
        else:
            pass
            #print "\n"

    ##
    ## Methods organised by tab
    ##

    def transform_identification(self, item):
        self.identification__identification_collections(item)

    def transform_production(self, item):
        self.productionDating_production_productionRole_place(item)
        #self.productionDating_production_productionPlace(item)
        self.productionDating_production_schoolStyle(item)

    def transform_physical(self, item):
        self.physicalCharacteristics_technique(item)
        self.physicalCharacteristics_material(item)
        self.physicalCharacteristics_dimension_unit(item)
        #self.physicalCharacteristics_dimensions_unit(item)

    def transform_iconography(self, item):
        self.iconography_generalSearchCriteria_generalThemes(item)
        self.iconography_generalSearchCriteria_specificThemes(item)
        self.iconography_contentSubjects(item)

    def transform_inscriptions(self, item):
        self.inscriptionsMarkings_inscriptionsAndMarkings_type_role_script(item)
        #self.inscriptionsMarkings_inscriptionsAndMarkings_role(item)
        #self.inscriptionsMarkings_inscriptionsAndMarkings_script(item)

    def transform_associations(self, item):
        self.associations_associatedSubjects_subject(item)
        self.associations_associatedSubjects_period(item)

    def transform_insurance(self, item):
        self.valueInsurance_valuations_currency(item)

    def transform_conservation(self, item):
        self.conditionConservation_conditions_condition(item)
        self.conditionConservation_preservationForm(item)

    def transform_acquisition(self, item):
        self.acquisition_methods(item)
        self.acquisition_places(item)

    def transform_ownership(self, item):
        self.ownershipHistory_history_exchangeMethod(item)
        self.ownershipHistory_history_place(item)

    def transform_location(self, item):
        self.location_normalLocation_normalLocation(item)
        self.location_currentLocation(item)

    def transform_fieldCollection(self, item):
        self.fieldCollection_fieldCollection_collector_role(item)
        self.fieldCollection_fieldCollection_method(item)
        self.fieldCollection_fieldCollection_place(item)
        self.fieldCollection_fieldCollection_placeFeature(item)
        self.fieldCollection_habitatStratigraphy_stratigraphy(item)
        self.fieldCollection__fieldCollection_event(item)

    def transform_numbersRelations(self, item):
        self.numbersRelationships__relationshipsWithOtherObjects_relatedObjects_association(item)

    def transform_all(self, item):
        self.log("! RUN ! transform_all()")

        transformers = [(self.transform_identification, "Identification"),
            (self.transform_production, "Production & Dating"), (self.transform_physical, "Physical description"),
            (self.transform_iconography, "Iconography"), (self.transform_inscriptions, "Inscriptions & Markings"),
            (self.transform_associations, "Associations"), (self.transform_insurance, "Insurance"),
            (self.transform_conservation, "Conservation & Treatment"), (self.transform_acquisition, "Acquisition"),
            (self.transform_ownership, "Ownership"), (self.transform_location, "Location"),
            (self.transform_fieldCollection, "Field Collection")]

        #
        # Custom runs
        #
        extra = [(self.productionDating__production_periods, "Periods")]

        transform_collection = [(self.identification__identification_collections, "Identification - Collection")]

        for transformer, name in transformers:
            try:
                self.log("! RUN ! Transformer '%s' starting..." %(str(name)))
                transformer(item)
            except:
                self.log("! ERROR ! Exception while converting tab %s\n" %(str(name)))
                raise

        self.log("! SUCCESS ! All tabs transformed.")
        return True

    def create_indexes(self):
        self.log("! RUN ! create_indexes()")
        container = self.api.get_container()
        catalog = getToolByName(container, 'portal_catalog')

        indexables = []
        indexes = catalog.indexes()

        meta_type = "KeywordIndex"
        for name in self.idxs:
            if name not in indexes:
                catalog.addIndex(name, meta_type)
                indexables.append(name)

        self.log("! Index creator ! Created new Indexes")

    def start(self):
        #self.log("! START ! Starting converter.")
        #self.create_indexes()
        #return True

        total = len(list(self.api.all_objects))
        curr = 0

        restriction = "rui-test"

        for obj in list(self.api.all_objects):
            curr += 1
            self.log("! STATUS ! - %s / %s" %(str(curr), str(total)))

            transaction.begin()
            item = obj.getObject()
            if item.portal_type == "Object":
                if item.identification_identification_objectNumber == restriction:
                    self.transform_all(item)
                    #item.reindexObject()
            transaction.commit()

        return True


