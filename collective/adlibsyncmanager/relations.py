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

class Relations:
    
    def __init__(self, APIMigrator):
        self.api = APIMigrator
        self.all_persons = []
        self.all_incomingLoans = []
        self.all_outgoingLoans = []
        self.collection = []
        self.collection_path = "/var/www/zm-collectie-v2/xml/objectsall.xml"

    ##
    ## UTILS
    ##
    def log(self, text=""):
        
        if "STATUS" in text or "ERROR" in text:
            timestamp = datetime.datetime.today().isoformat()
            print "[%s] %s" %(str(timestamp), str(text))
        else:
            pass
            #   print "\n"

    def rel_exists(self, curr_related, to, field):
        name = getattr(to, field, None)
        if name:
            for related in curr_related:
                rel = related.to_object
                rel_name = getattr(rel, field, None)
                if rel_name:
                    if rel_name == name:
                        return True
        return False

    def get_relation(self, obj):
        intids = component.getUtility(IIntIds)
        to_id = intids.getId(obj)
        to_value = RelationValue(to_id)
        return to_value

    def create_relation(self, _from, to, field, term='nameInformation_name_name'):
        intids = component.getUtility(IIntIds) 

        if term:
            curr_related = getattr(_from, field)
            if not self.rel_exists(curr_related, to, term):
                if len(curr_related) == 0:
                    setattr(_from, field, [])

                to_id = intids.getId(to)
                to_value = RelationValue(to_id)
                curr_related.append(to_value)
                setattr(_from, field, curr_related)
                self.log("! RELATION ! Added!")
            else:
                self.log("! RELATION ! Exists!")

        return True

    ###
    ### Transformers
    ###

    def transform_identification(self, item, record=None):

        original = "identification_identification_institutionName"
        target = "identification_identification_institutionNames"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr != None:
                person = self.api.find_person(self.all_persons, curr)
                if person:
                    self.create_relation(item, person, target)
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def transform_identification_taxonomy(self, item, record=None):

        original = "identification_taxonomy_determiner"
        target = "identification_taxonomy_determiners"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            
            new_target = []
            if curr != None:
                for line in curr:
                    name = line['name']
                    date = line['date']
                    
                    person = self.api.find_person(self.all_persons, name)
                    final_name = []
                    
                    if person:
                        final_name = [person]
                    else:
                        self.log("! Failed ! Failed to get person.")

                    new_target.append({
                        "name": final_name,
                        "date": date
                    })

                setattr(item, target, new_target)
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def transform_production(self, item, record=None):
        if record:
            target = ""
            current_field = "productionDating_productionDating"
            xml_original = "creator"
            xml_attribute = "linkref"

            if hasattr(item, current_field):
                
                curr = getattr(item, current_field)
                
                if curr != None:
                    length = len(curr)
                    for slot, creator in enumerate(record.findall(xml_original)):
                        if slot < length:
                            linkref = creator.get(xml_attribute)
                            person = self.api.find_person_by_priref(self.all_persons, linkref)
                            if person:
                                if len(curr[slot]['makers']) == 0:
                                    curr[slot]["makers"] = []
                                curr[slot]['makers'].append(person)

        return True

    def transform_iconography(self, item, record=None):

        if record:
            target = ""
            current_field = "iconography_contentPersonInstitution"
            xml_original = "content.person.name"
            xml_attribute = "linkref"

            if hasattr(item, current_field):
                
                curr = getattr(item, current_field)

                if curr != None:
                    length = len(curr)
                    for slot, field in enumerate(record.findall(xml_original)):
                        if slot < length:
                            linkref = field.get(xml_attribute)
                            person = self.api.find_person_by_priref(self.all_persons, linkref)
                            if person:
                                if len(curr[slot]['names']) == 0:
                                    curr[slot]["names"] = []
                                curr[slot]['names'].append(person)
                                self.log("! RELATION ! Added.")
        return True

    def transform_inscriptions(self, item, record=None):
        if record:
            target = ""
            current_field = "inscriptionsMarkings_inscriptionsAndMarkings"
            xml_original = "inscription.maker"
            xml_attribute = "linkref"

            if hasattr(item, current_field):
                
                curr = getattr(item, current_field)

                if curr != None:
                    length = len(curr)
                    for slot, field in enumerate(record.findall(xml_original)):
                        if slot < length:
                            linkref = field.get(xml_attribute)
                            person = self.api.find_person_by_priref(self.all_persons, linkref)
                            if person:
                                if len(curr[slot]['creators']) == 0:
                                    curr[slot]["creators"] = []
                                curr[slot]['creators'].append(person)
                                self.log("! RELATION ! Added.")
        return True


    def transform_acquisition(self, item, record=None):
        if record:
            target = ""
            current_field = "acquisition_acquisition_from"
            xml_original = "acquisition.source"
            xml_attribute = "linkref"
            term = "priref"

            if hasattr(item, current_field):
                
                curr = getattr(item, current_field)
                if curr != None:

                    if record.find(xml_original) != None:
                        linkref = record.find(xml_original).get(xml_attribute)
                        person = self.api.find_person_by_priref(self.all_persons, linkref)
                        if person:
                            self.create_relation(item, person, current_field, term)
        return True

    def transform_disposal(self, item, record=None):
        original = "disposal_recipient"
        target = "disposal_disposal_recipient"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr != None:
                person = self.api.find_person(self.all_persons, curr)
                if person:
                    self.create_relation(item, person, target)
        else:
            self.log("! Failed ! Attributes not found. ")

        original = "disposal_proposed_recipient"
        target = "disposal_disposal_proposedRecipient"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr != None:
                person = self.api.find_person(self.all_persons, curr)
                if person:
                    self.create_relation(item, person, target)
        else:
            self.log("! Failed ! Attributes not found. ")

        return True

    def transform_ownership(self, item, record=None):

        original = "ownershipHistory_current_owner"
        target = "ownershipHistory_ownership_currentOwner"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr != None:
                person = self.api.find_person(self.all_persons, curr)
                if person:
                    self.create_relation(item, person, target)
        else:
            self.log("! Failed ! Attributes not found. ")

        original = "ownershipHistory_owner"
        target = "ownershipHistory_history_owner"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr != None:
                person = self.api.find_person(self.all_persons, curr)
                if person:
                    self.create_relation(item, person, target)
        else:
            self.log("! Failed ! Attributes not found. ")

        original = "ownershipHistory_acquired_from"
        target = "ownershipHistory_history_acquiredFrom"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            if curr != None:
                person = self.api.find_person(self.all_persons, curr)
                if person:
                    self.create_relation(item, person, target)
        else:
            self.log("! Failed ! Attributes not found. ")

        return True


    def transform_fieldCollection(self, item, record=None):
        
        if record:
            target = ""
            current_field = "fieldCollection_fieldCollection_collectors"
            xml_original = "Collector"
            xml_attribute = "linkref"

            if hasattr(item, current_field):
                
                curr = getattr(item, current_field)
                if curr != None:
                    length = len(curr)
                    for slot, field in enumerate(record.findall(xml_original)):
                        if slot < length:
                            if field.find('field_coll.name') != None:
                                linkref = field.find('field_coll.name').get(xml_attribute)
                                person = self.find_person_by_priref(self.all_persons, linkref)
                                if person:
                                    if len(curr[slot]['name']) == 0:
                                        curr[slot]["name"] = []
                                    curr[slot]['name'].append(person)
                                    self.log("! RELATION ! Added.")
        return True

    def transform_loans(self, item, record=None):

        """original = "loans_incomingLoans"
        target = "loans_incomingLoan"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            for line in curr:
                nr = line['loanNumber']
                if nr:
                    loan = self.find_incomingloan(self.all_incomingLoans, nr)
                    if loan:
                        self.create_relation(item, loan, target, 'loanRequest_general_loanNumber')

        original = "loans_outgoingLoans"
        target = "loans_outgoingLoan"
        term = ""

        if hasattr(item, original) and hasattr(item, target):
            curr = getattr(item, original)
            for line in curr:
                nr = line['loanNumber']
                if nr:
                    loan = self.find_incomingloan(self.all_incomingLoans, nr)
                    if loan:
                        self.create_relation(item, loan, target, 'loanRequest_general_loanNumber')
        """
        return True


    def transform_exhibitions(self, item, record=None):
        target = ""
        current_field = "exhibitions_exhibition"
        xml_original = "parts_reference"
        xml_attribute = "linkref"

        if record:

            if hasattr(item, current_field):
                
                curr = getattr(item, current_field)
                if curr != None:
                    length = len(curr)
                else:
                    length = 0

                if length > 0:
                    for slot, field in enumerate(record.findall(xml_original)):
                        if slot < length:
                            if field.find('exhibition') != None:
                                exhibition = field.find('exhibition')
                                if exhibition.find('exhibition') != None:
                                    linkref = exhibition.find('exhibition').get(xml_attribute)
                                    ex = self.api.find_exhibition_by_priref(self.all_exhibitions, linkref)
                                    if ex:
                                        if len(curr[slot]['exhibitionName']) == 0:
                                            curr[slot]["exhibitionName"] = []
                                        
                                        curr[slot]['exhibitionName'].append(ex)
                                        self.log("! RELATION ! Added.")
                else:
                    new_curr = []
                    for slot, field in enumerate(record.findall(xml_original)):
                        if field.find('exhibition') != None:
                            exhibition = field.find('exhibition')
                            if exhibition.find('exhibition') != None:
                                linkref = exhibition.find('exhibition').get(xml_attribute)
                                notes = ""
                                catObject = ""
                                
                                if exhibition.find('exhibition.notes') != None:
                                    notes = exhibition.find('exhibition.notes').text
                                if exhibition.find("exhibition.catalogue_number") != None:
                                    catObject = exhibition.find("exhibition.catalogue_number").text

                                exhibitionName = []

                                ex = self.api.find_exhibition_by_priref(self.all_exhibitions, linkref)
                                if ex:
                                    exhibitionName = [ex]

                                new_curr.append({
                                    "exhibitionName": exhibitionName,
                                    "notes": notes,
                                    "catObject": catObject
                                    })

                                self.log("! RELATION Exhibition ! Added.")

                    setattr(item, current_field, new_curr)

        return True

    def transform_associations(self, item, record=None):
        # Objects
        return True

    def transform_all(self, item, record):
        self.log("! RUN ! transform_all()")
        
        transformers = [(self.transform_identification, "Identification"), (self.transform_identification_taxonomy, "Identification taxonomy"),
            (self.transform_production, "Production & Dating"),
            (self.transform_iconography, "Iconography"), (self.transform_inscriptions, "Inscriptions & Markings"),
            (self.transform_disposal, "Disposal"), (self.transform_acquisition, "Acquisition"),
            (self.transform_ownership, "Ownership"), (self.transform_fieldCollection, "Field Collection"),
            (self.transform_exhibitions, "Exhibitions")]

        for transformer, name in transformers:
            try:
                self.log("! RUN ! Transformer '%s' starting...\nFor item: %s" %(str(name), str(item.absolute_url())))
                transformer(item, record)
            except Exception, e:
                self.log("! ERROR ! Exception while converting tab %s\nError message: %s\n"%(str(name),str(e)))
                pass

        self.log("! SUCCESS ! All tabs transformed.")
        return True

    def start(self):
        self.log("! START ! Starting creating relations.")

        ## Define util variables
        container = self.api.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        self.all_persons = catalog(portal_type='PersonOrInstitution', Language="all")
        self.all_exhibitions = catalog(portal_type='Exhibition', Language="all")
        self.collection = self.api.get_zm_collection(self.collection_path)

        total = len(list(self.api.all_objects))
        curr = 3460
        limit = -1
        restriction = "rui-test"

        ## Run for all objects
        for obj in list(self.api.all_objects)[3460:limit]:
            curr += 1
            self.log("! STATUS ! - %s / %s" %(str(curr), str(total)))

            transaction.begin()
            item = obj.getObject()
            if item.portal_type == "Object":
                if hasattr(item, 'identification_identification_objectNumber'):
                    if item.identification_identification_objectNumber:
                        if item.identification_identification_objectNumber != restriction:
                            record = self.api.find_record_by_object_number(self.collection, item.identification_identification_objectNumber)
                            self.transform_all(item, record)
                            if not record:
                                self.log("! RECORD ERROR ! record not found")
            transaction.commit()

        return True






