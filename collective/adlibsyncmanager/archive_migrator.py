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

class ArchiveMigrator:
    
    def __init__(self, APIMigrator):
        self.api_migrator = APIMigrator
        self.collection_path_test = "/Users/AG/Projects/collectie-zm/single-archive-v01.xml"
        self.collection_path_stage = "/home/andre/collectie-zm-v1/xml/Archive-v01.xml"
        self.collection_path_prod = "/var/www/zm-collectie-v2/xml/Archiefstukken.xml"

    def get_object_from_instance(self, priref):
        object_folder = self.api_migrator.get_folder('nl/archiefstukken/archiefstukken')

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
        if data['archiveDetails_archiveDetails_archiveNumber'] != "":
            title = data['archiveDetails_archiveDetails_archiveNumber']

        if title != "":
            dirty_id = "%s %s" %(dirty_id, title)

        data['dirty_id'] = dirty_id
        return dirty_id


    def get_archive_details_fieldset(self, data, record):

        # 'archiveDetails_archiveDetails_archiveNumber':"",
        if record.find('number') != None:
            data['archiveDetails_archiveDetails_archiveNumber'] = self.api_migrator.trim_white_spaces(record.find('number').text)


        # 'archiveDetails_archiveDetails_preliminaryNumber':"",
        if record.find('preliminary_number') != None:
            data['archiveDetails_archiveDetails_preliminaryNumber'] = self.api_migrator.trim_white_spaces(record.find('preliminary_number').text)

        # 'archiveDetails_archiveDetails_photoNumber':"", 


        # 'archiveDetails_archiveDetails_class':[], 
        classes = []

        for c in record.findall('class'):
            if c.find('term') != None:
                classes.append({
                    "term": self.api_migrator.trim_white_spaces(c.find('term').text)
                    })

        data['archiveDetails_archiveDetails_class'] = classes

        # 'archiveDetails_archiveDetails_editorialForm':[], 
        # 'archiveDetails_archiveDetails_physicalForm':"",
        # 'archiveDetails_archiveDetails_developmentPhase':[], 

        # 'archiveDetails_archiveDetails_sender':[],
        senders = []

        for sender in record.findall('sender'):
            if sender.find('name') != None:
                senders.append({
                    "term": self.api_migrator.trim_white_spaces(sender.find('name').text)
                    })

        data['archiveDetails_archiveDetails_sender'] = senders

        # 'archiveDetails_archiveDetails_receiver':"", 
        if record.find('recipient') != None:
            if record.find('recipient').find('name') != None:
                data['archiveDetails_archiveDetails_receiver'] = self.api_migrator.trim_white_spaces(record.find('recipient').find('name').text)

        # 'archiveDetails_archiveDetails_dateExact':[],
        dateexact = []
        for date_p in record.findall('date.precise'):
            dateexact.append({
                "term": self.api_migrator.trim_white_spaces(date_p.text)
                })

        data['archiveDetails_archiveDetails_dateExact'] = dateexact
        
        # 'archiveDetails_archiveDetails_dateFree':"", 
        if record.find('date.free') != None:
            data['archiveDetails_archiveDetails_dateFree'] = self.api_migrator.trim_white_spaces(record.find('date.free').text)

        # 'archiveDetails_archiveDetails_content':[],
        contents = []

        for content in record.findall('content'):
            contents.append({
                'term': self.api_migrator.trim_white_spaces(content.text)
                })

        data['archiveDetails_archiveDetails_content'] = contents

        # 'archiveDetails_archiveDetails_keyword':[], 
        keywords = []

        for keyword in record.findall('keyword'):
            if keyword.find('term') != None:
                keywords.append({
                    'term': self.api_migrator.trim_white_spaces(keyword.find('term').text)
                    })

        data['archiveDetails_archiveDetails_keyword'] = keywords

        # 'archiveDetails_archiveDetails_notes':[],
        notes = []

        for note in record.findall('notes'):
            notes.append({
                'term': self.api_migrator.trim_white_spaces(note.text)
                })

        data['archiveDetails_archiveDetails_notes'] = notes

        return True

    def get_object(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",

            # General
            'archiveDetails_archiveDetails_archiveNumber':"",
            'archiveDetails_archiveDetails_preliminaryNumber':"",
            'archiveDetails_archiveDetails_photoNumber':"", 
            'archiveDetails_archiveDetails_class':[], 
            'archiveDetails_archiveDetails_editorialForm':[], 
            'archiveDetails_archiveDetails_physicalForm':"",
            'archiveDetails_archiveDetails_developmentPhase':[], 
            'archiveDetails_archiveDetails_sender':[],
            'archiveDetails_archiveDetails_receiver':"", 
            'archiveDetails_archiveDetails_dateExact':[],
            'archiveDetails_archiveDetails_dateFree':"", 
            'archiveDetails_archiveDetails_content':[],
            'archiveDetails_archiveDetails_keyword':[], 
            'archiveDetails_archiveDetails_notes':[],
            
            # linked objects
            'linkedObjects_linkedObjects': []
        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_archive_details_fieldset(data, record)
        except:
            raise

        try:
            self.api_migrator.get_linked_objects_fieldset_archive(data, record)
        except:
            raise

        self.create_dirty_id(data)
            
        return data

    def create_object(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/archiefstukken/archiefstukken')
        
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
                print "%s - archive already exists %s" % (timestamp, normalized_id)
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
                    if data['archiveDetails_archiveDetails_archiveNumber'] != "":
                        title = data['archiveDetails_archiveDetails_archiveNumber']
                    else:
                        title = dirty_id

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Archive",
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

                    #### Log archive added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added archive %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - archive already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_archive (" +dirty_id+ "):", sys.exc_info()[1]
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
            print "%s - Skipped archive: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def update_object(self, obj, xml):

        for key, value in xml.iteritems():
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
                print "object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] object failed unexpected" %(timestamp)
                raise

        self.success = True
        return True


    def update_objects(self):
        collection_path_test = self.collection_path_test
        collection_path_stage = self.collection_path_stage

        objects = self.api_migrator.get_zm_collection(collection_path_test)

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
