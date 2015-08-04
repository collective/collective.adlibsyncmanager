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

XML_PATH = ""
TEST_OBJECT = 0

class ObjectEntryMigrator:
    
    def __init__(self, APIMigrator):
        self.api_migrator = APIMigrator
        self.collection_path_test = "/Users/AG/Projects/collectie-zm/single-object-entry-v01.xml"
        self.collection_path_stage = "/home/andre/collectie-zm-v1/xml/ObjectEntry-v01.xml"
        self.collection_path_prod = "/var/www/zm-collectie-v2/xml/objectentries.xml"

    def get_object_from_instance(self, priref):
        object_folder = self.api_migrator.get_folder('nl/collectie/binnenkomst-objecten')

        for brain in object_folder:
            item = object_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    def create_dirty_id(self, data):
        if data["priref"] != "":
            dirty_id = "%s" %(data['priref'])

        title = ""
        if data['general_entry_transportNumber'] != "":
            title = data['general_entry_transportNumber']

        if title != "":
            dirty_id = "%s %s" %(dirty_id, title)

        data['dirty_id'] = dirty_id
        return dirty_id


    def get_template_for_object_data_fieldset(self, data, record):

        # 'templateForObjectData_objectName':[], 
        names = []
        for name in record.findall('template.object_name'):
            names.append({
                "term": self.api_migrator.trim_white_spaces(name.text)
                })
            
        data['templateForObjectData_objectName'] = names


        # 'templateForObjectData_title':[],
        titles = []
        for title in record.findall('template.title'):
            titles.append({
                "title": self.api_migrator.trim_white_spaces(title.text)
                })
            
        data['templateForObjectData_title'] = titles

        # 'templateForObjectData_description':"", 
        if record.find('template.description') != None:
            data['templateForObjectData_description'] = self.api_migrator.trim_white_spaces(record.find('template.description').text)

        # 'templateForObjectData_date':[],
        dates = []
        for date in record.findall('Template_date'):
            new_date = {
                "dateEarly": "",
                "dateLate": ""
            }

            if date.find("template.date.start") != None:
                new_date['dateEarly'] = self.api_migrator.trim_white_spaces(date.find("template.date.start").text)

            if date.find("template.date.end") != None:
                new_date['dateLate'] = self.api_migrator.trim_white_spaces(date.find("template.date.end").text)

            dates.append(new_date)

        data['templateForObjectData_date'] = dates


        # 'templateForObjectData_creator':[], 
        creators = []
        for creator in record.findall('Template_production'):
            new_creator = {
                "creator": "",
                "productionPlace": ""
            }

            if creator.find("template.creator") != None:
                new_creator['creator'] = self.api_migrator.trim_white_spaces(creator.find("template.creator").text)

            if creator.find("template.production_place") != None:
                new_creator['productionPlace'] = self.api_migrator.trim_white_spaces(creator.find("template.production_place").text)

            creators.append(new_creator)

        data['templateForObjectData_creator'] = creators

        # 'templateForObjectData_material':[],
        materials = []
        for material in record.findall('template.material'):
            materials.append({
                "term": self.api_migrator.trim_white_spaces(material.text)
                })

        data['templateForObjectData_material'] = materials

        # 'templateForObjectData_technique':[], 
        techniques = []
        for technique in record.findall('template.technique'):
            techniques.append({
                "term": self.api_migrator.trim_white_spaces(technique.text)
                })

        data['templateForObjectData_technique'] = techniques

        # 'templateForObjectData_location':"",
        if record.find('template.current_location') != None:
            data['templateForObjectData_location'] = self.api_migrator.trim_white_spaces(record.find('template.current_location').text)

        # 'templateForObjectData_currentOwner':"", 
        if record.find('template.current_owner') != None:
            data['templateForObjectData_currentOwner'] = self.api_migrator.trim_white_spaces(record.find('template.current_owner').text)

        # 'templateForObjectData_notes':[],
        notes = []
        for note in record.findall('template.notes'):
            notes.append({
                "notes": self.api_migrator.trim_white_spaces(note.text)
                })

        data['templateForObjectData_notes'] = notes

        # 'templateForObjectData_createLinkedObjectRecords':""
        if record.find('template.description') != None:
            data['templateForObjectData_description'] = self.api_migrator.trim_white_spaces(record.find('template.description').text)


    def get_general_fieldset(self, data, record):
        #'general_entry_transportNumber':"", 
        if record.find('transport_number') != None:
            data['general_entry_transportNumber'] = self.api_migrator.trim_white_spaces(record.find('transport_number').text)

        #'general_entry_dateExpected':"",
        if record.find('entry_date.expected') != None:
            data['general_entry_dateExpected'] = self.api_migrator.trim_white_spaces(record.find('entry_date.expected').text)

        #'general_entry_entryDate':"",
        if record.find('entry_date') != None:
            data['general_entry_entryDate'] = self.api_migrator.trim_white_spaces(record.find('entry_date').text)

        #'general_entry_transportMethod':"", 

        #'general_entry_reason':"",
        if record.find('entry_reason') != None:
            if record.find('entry_reason').find('text') != None:
                data['general_entry_reason'] = self.api_migrator.trim_white_spaces(record.find('entry_reason').find('text').text)

        #'general_entry_currentOwner':"", 
        if record.find('template.current_owner') != None:
            data['general_entry_currentOwner'] = self.api_migrator.trim_white_spaces(record.find('template.current_owner').text)

        #'general_entry_depositor':[],
        depositors = []
        for depositor in record.findall('depositor'):
            if depositor.find('name') != None:
                depositors.append({
                    "name": self.api_migrator.trim_white_spaces(depositor.find('name').text),
                    "contact": ""
                    })

        if len(depositors) > 0:
            for slot, contact in enumerate(record.findall('depositor.contact')):
                if contact.find('name') != None:
                    depositors[slot]['contact'] = self.api_migrator.trim_white_spaces(contact.find('name').text)

        data['general_entry_depositor'] =  depositors

        #'general_entry_destination':[], 
        destinations = []

        for destination in record.findall('destination'):
            if destination.find('name') != None:
                destinations.append({
                    "term": self.api_migrator.trim_white_spaces(destination.find('name').text),
                    "contact": ""
                    })

        if len(destinations) > 0:
            for slot, contact in enumerate(record.findall('destination.contact')):
                if contact.find('name') != None:
                    destinations[slot]['contact'] = self.api_migrator.trim_white_spaces(contact.find('name').text)

        data['general_entry_destination'] = destinations


        #'general_transport_shipper':[],
        shippers = []

        for shipper in record.findall('Shipper'):
            new_shipper = {
                "term": "",
                "contact": ""
            }

            if shipper.find('shipper') != None:
                new_shipper['term'] = self.api_migrator.trim_white_spaces(shipper.find('shipper').text)

            if shipper.find('shipper.contact') != None:
                new_shipper['contact'] = self.api_migrator.trim_white_spaces(shipper.find('shipper.contact').text)

            shippers.append(new_shipper)

        data['general_transport_shipper'] = shippers

        #'general_transport_courier':"", 
        if record.find('courier') != None:
            data['general_transport_courier'] = self.api_migrator.trim_white_spaces(record.find('courier').text)


        #'general_numberOfObjects_numberInFreightLetter':"",
        if record.find('number_of_objects.stated') != None:
            data['general_numberOfObjects_numberInFreightLetter'] = self.api_migrator.trim_white_spaces(record.find('number_of_objects.stated').text)

        #'general_numberOfObjects_numberDelivered':"", 
        if record.find('number_of_objects.sent') != None:
            data['general_numberOfObjects_numberDelivered'] = self.api_migrator.trim_white_spaces(record.find('number_of_objects.sent').text)


        #'general_freightLetter_template':"",
        if record.find('freight_letter_in.template') != None:
            if record.find('freight_letter_in.template').find('text') != None:
                data['general_freightLetter_template'] = self.api_migrator.trim_white_spaces(record.find('freight_letter_in.template').find('text').text)


        #'general_freightLetter_digRef':"", 
        if record.find('freight_letter_in.reference') != None:
            data['general_freightLetter_digRef'] = self.api_migrator.trim_white_spaces(record.find('freight_letter_in.reference').text)


        #'general_totalInsuranceValue_insuranceValue':"",
        if record.find('insurance.value') != None:
            data['general_totalInsuranceValue_insuranceValue'] = self.api_migrator.trim_white_spaces(record.find('insurance.value').text)


        #'general_totalInsuranceValue_currency':"", 
        if record.find('insurance.currency') != None:
            data['general_totalInsuranceValue_currency'] = self.api_migrator.trim_white_spaces(record.find('insurance.currency').text)


        #'general_requirements_requirements':[],
        requirements = []
        for requirement in record.findall('requirements'):
            requirements.append({
                "term": self.api_migrator.trim_white_spaces(requirement.text)
                })

        data['general_requirements_requirements'] = requirements

        #'general_requirements_packingNotes':[], 
        packingnotes = []

        for packingnote in record.findall('packing_notes'):
            packingnotes.append({
                "term": self.api_migrator.trim_white_spaces(packingnote.text)
                })

        data['general_requirements_packingNotes'] = packingnotes


        #'general_requirements_digitalReferences':[],
        digrefs = []
        for digref in record.findall('Digitalreference'):
            new_ref = {
                "type": "",
                "reference": ""
            }

            if digref.find('digital_reference') != None:
                new_ref['reference'] = self.api_migrator.trim_white_spaces(digref.find('digital_reference').text)

            if digref.find('digital_reference.type') != None:
                new_ref['type'] = self.api_migrator.trim_white_spaces(digref.find('digital_reference.type').text)


            digrefs.append(new_ref)

        data['general_requirements_digitalReferences'] = digrefs
        
        #'general_notes_notes':[],
        notes = []
        for note in record.findall('notes'):
            notes.append({
                "notes": self.api_migrator.trim_white_spaces(note.text)
                })

        data['general_notes_notes'] = notes

        return True

    def get_object(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",

            # General
            'general_entry_transportNumber':"", 
            'general_entry_dateExpected':"",
            'general_entry_entryDate':"",
            'general_entry_transportMethod':"", 
            'general_entry_reason':"",
            'general_entry_currentOwner':"", 
            'general_entry_depositor':[],
            'general_entry_destination':[], 
            'general_transport_shipper':[],
            'general_transport_courier':"", 
            'general_numberOfObjects_numberInFreightLetter':"",
            'general_numberOfObjects_numberDelivered':"", 
            'general_freightLetter_template':"",
            'general_freightLetter_digRef':"", 
            'general_totalInsuranceValue_insuranceValue':"",
            'general_totalInsuranceValue_currency':"", 
            'general_requirements_requirements':[],
            'general_requirements_packingNotes':[], 
            'general_requirements_digitalReferences':[],
            'general_notes_notes':[],
            
            # Template for object data
            'templateForObjectData_objectName':[], 
            'templateForObjectData_title':[],
            'templateForObjectData_description':"", 
            'templateForObjectData_date':[],
            'templateForObjectData_creator':[], 
            'templateForObjectData_material':[],
            'templateForObjectData_technique':[], 
            'templateForObjectData_location':"",
            'templateForObjectData_currentOwner':"", 
            'templateForObjectData_notes':[],
            'templateForObjectData_createLinkedObjectRecords':""
            
            # List with linked objects


        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_general_fieldset(data, record)
        except:
            raise

        try:
            self.get_template_for_object_data_fieldset(data, record)
        except:
            raise

        self.create_dirty_id(data)
            
        return data

    def create_object(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/collectie/binnenkomst-objecten')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Object entry already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_object_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if data['general_entry_transportNumber'] != "":
                        title = data['general_entry_transportNumber']
                    else:
                        title = dirty_id

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="ObjectEntry",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_object(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Object entry %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Object entry already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_object entry (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped object entry: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def update_object(self, obj, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(obj, key):
                    setattr(obj, key, value)

        print "Object fields updated!"
        return True

    def import_objects(self):

        collection_path_test = self.collection_path_test
        collection_path_stage = self.collection_path_stage
        collection_path_prod = self.collection_path_prod

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_object(priref, obj, True)
                    # Create object
                    self.create_object(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Object entry failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object entry failed unexpected" %(timestamp)
                raise

        self.success = True
        return True


    def update_objects(self):
        collection_path_test = self.collection_path_test
        collection_path_stage = self.collection_path_stage
        collection_path_prod = self.collection_path_prod

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "Updating %s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    current_object = self.get_object_from_instance(priref)
                    if current_object != None:
                        data = self.get_object(priref, obj, False)
                        self.update_object(current_object, data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return True


    def start(self):

        self.run_type = "import_objects"

        print "\n[ Run for type: %s ]\n" %(self.run_type)

        if self.run_type == "import_objects":
            self.import_objects()

        elif self.run_type == "update_objects":
            self.update_objects()

        return True
