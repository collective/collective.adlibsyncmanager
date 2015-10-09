#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""
from Acquisition import aq_parent, aq_inner

from plone import api
#from plone.multilingual.interfaces import ILanguage

import fnmatch
from lxml import etree
import urllib2, urllib
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
#from plone.multilingual.interfaces import ITranslationManager
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

#from .book_migrator import BookMigrator
#from .incomingloan_migrator import IncomingLoanMigrator
#from .objectentry_migrator import ObjectEntryMigrator
#from .archive_migrator import ArchiveMigrator
#from .converter import Converter
#from .relations import Relations
from .updater import Updater

ORGANIZATION = "teylers"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(shelf_mark='%s')&xmltype=structured"
API_REQUEST_URL_COLLECT = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured"

API_REQUEST_ALL_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(%s)&xmltype=structured"

XML_PATH = ""

TEST_OBJECT = 0

# Folder where the images are (Do not forget to add a trailing slash)
class ObjectItem:
    def __init__(self):
        self.title = ""
        self.description = ""
        self.identification_identification_objectNumber = ""
        self.production = ""
        self.creator = ""
        self.dirty_id = ""
        self.tags = []

class APIMigrator:
    
    def __init__(self, portal, folder, image_folder, type_to_create="art_list", set_limit=0, art_list=[]):
        self.portal = portal
        self.folder_raw_path = folder
        self.folder_path = folder.split("/")
        self.type_to_create = type_to_create
        self.art_list = art_list
        self.set_limit = set_limit
        self.image_folder = image_folder

        self.created = 0
        self.skipped = 0
        self.errors = 0
        self.success = False

        self.request_all_url = ""

        self.skipped_ids = []

        self.folder_path = "nl/intern".split('/')
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        self.portal_catalog = catalog

        all_objects = catalog(portal_type='Object', Language="all")
        all_persons = catalog(portal_type='PersonOrInstitution', Language="all")
        all_archives = catalog(portal_type='Archive', Language="all")
        all_treatments = catalog(portal_type='treatment', Language="all")
        all_exhibitions = catalog(portal_type='Exhibition', Language="all")
        all_outgoing = catalog(portal_type='OutgoingLoan', Language="all")
        all_incoming = catalog(portal_type='IncomingLoan', Language="all")
        all_articles = catalog(portal_type='Article', Language="all")
        all_objectentries = catalog(portal_type='ObjectEntry', Language="all")
        all_resources = catalog(portal_type='Resource', Language="all")

        all_taxonomies = catalog(portal_type='Taxonomie', Language="all")
        
        self.all_objects = all_objects
        self.all_persons = all_persons
        self.all_archives = all_archives
        self.all_treatments = all_treatments
        self.all_exhibitions = all_exhibitions
        self.all_outgoing = all_outgoing
        self.all_incoming = all_incoming
        self.all_articles = all_articles
        self.all_objectentries = all_objectentries
        self.all_resources = all_resources
        self.all_taxonomies = all_taxonomies

    def build_api_request_all(self):
        url = ""
        
        index = 0
        for obj in self.art_list:
            if index == 0:
                url += "object_number='%s'" % (obj)
            else:
                url += " or object_number='%s'" % (obj)
            index += 1
        return url

    def get_container(self):
        if len(self.folder_path) == 0:
            print "!=== Folder check failed ==="
            self.success = False
            return None

        container = self.portal

        for folder in self.folder_path:
            if hasattr(container, folder):
                container = container[folder]
            else:
                print ("== Chosen folder " + folder + " does not exist. Creating new folder ==")
                self.success = False
                return None

        return container

    def parse_api_doc(self, url):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        return doc

    def migrate_test_api(self):
        print "=== Sart test ==="
        quoted_query = urllib.quote(self.art_list[TEST_OBJECT])
        api_request = API_REQUEST_URL % (quoted_query)

        xml_doc = self.parse_api_doc(api_request)

        root = xml_doc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        for record in records:
            if record.find('object_number') != None:
                object_number = record.find('object_number').text
                print "TEST - Object number %s" % (str(object_number))
                if object_number.lower() == self.art_list[TEST_OBJECT]:
                    self.success = True
                    break

        print "=== Test finished ==="

    def create_object(self, obj):
        
        transaction.begin()
        
        container = self.get_container()
        dirty_id = obj.dirty_id
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        try:
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Skipped. Already exists: %s" % (timestamp, obj.identification_identification_objectNumber)
                transaction.commit()
                return True

            if not hasattr(container, normalized_id):
                
                container.invokeFactory(
                    type_name="object",
                    id=normalized_id,
                    title=obj.title,
                    description=obj.description,
                    object_number=obj.identification_identification_objectNumber,
                    production=obj.production,
                    creator=obj.creator,
                    text=obj.text
                    )

                # Get object and add tags
                created_object = container[str(normalized_id)]
                
                if len(obj.tags) > 0:
                    created_object.setSubject(obj.tags)

                created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                created_object.reindexObject()
                created_object.reindexObject(idxs=["hasMedia"])
                created_object.reindexObject(idxs=["leadMedia"])
                
                transaction.commit()

                timestamp = datetime.datetime.today().isoformat()
                print "%s - Added Object %s" % (timestamp, dirty_id)

                self.created += 1
                result = True

        except:
            self.errors += 1
            self.success = False
            print "Unexpected error on create_object (" +dirty_id+ "):", sys.exc_info()[1]
            transaction.abort()
            raise
            return result

        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            print "%s - Skipped object: %s" %(timestamp, obj.identification_identification_objectNumber)

        self.success = result
        return result

    def add_pdfs(self):
        container = self.get_container()

        for obj in self.art_list:
            object_number = obj["number"]
            pdfs = obj["pdfs"]

            object_item = self.get_object_from_instance(object_number)

            if object_item != None:
                # invoke file factory
                for pdf in pdfs:
                    file_raw_data = open(pdf, "r")
                    file_data = file_raw_data.read()
                    f = NamedBlobFile(data=file_data)
                    file_raw_data.close()

                    pdf_id = idnormalizer.normalize(pdf.split('/')[-1]) 

                    object_item.invokeFactory(type_name="File", id=pdf_id, title=pdf_id, file=f)

                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - %s: Added PDF on object %s" %(timestamp, pdf_id, object_number)

                    object_item.reindexObject()
            else:
                timestamp = datetime.datetime.today().isoformat()
                print "%s - %s: PDF Skipped. Object %s not found." % (timestamp, pdf_id, object_item.identification_identification_objectNumber)

        return True

    def create_folder_add_image(self, obj_path, object_item, folder_name, images_path, images):
        container = self.get_container()
        dirty_id = folder_name.decode('utf8')
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        
        print "try folder %s" % (dirty_id)
        try:
            if hasattr(object_item, 'slideshow'):
                slideshow = object_item['slideshow']
                
                if not hasattr(slideshow, normalized_id):
                    transaction.begin()
                    slideshow.invokeFactory(type_name="Folder", id=normalized_id, title=folder_name)
                    timestamp = datetime.datetime.today().isoformat()
                    #print "%s - %s: FOLDER added on %s" %(timestamp, folder_name, object_item.identification_identification_objectNumber)
                    new_folder = slideshow[normalized_id]
                    new_folder.portal_workflow.doActionFor(new_folder, "publish", comment="Folder inside slideshow auto published")
                    transaction.commit()

                    for img_name in images:
                        transaction.begin()
                        path = obj_path + "/" + folder_name + "/" + images_path + "/" + img_name
                        image_file = open(path, "r")
                        image_data = image_file.read()
                        img = NamedBlobImage(
                            data=image_data
                        )
                        image_file.close()

                        image_id = idnormalizer.normalize(img_name)

                        new_folder.invokeFactory(type_name="Image", id=image_id, title=img_name, image=img)

                        timestamp = datetime.datetime.today().isoformat()
                        print "%s - %s: Added on FOLDER %s" %(timestamp, img_name, folder_name)
                        transaction.commit()
                else:
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - %s: FOLDER Skipped. Already exists inside slideshow of %s" % (timestamp, folder_name, object_item.identification_identification_objectNumber)
                    new_folder = slideshow[normalized_id]
                    for img_name in images:

                        transaction.begin()

                        image_id = idnormalizer.normalize(img_name)
                        
                        if not hasattr(new_folder, image_id):
                            path = obj_path + "/" + folder_name + "/" + images_path + "/" + img_name
                            image_file = open(path, "r")
                            image_data = image_file.read()
                            img = NamedBlobImage(
                                data=image_data
                            )
                            image_file.close()

                            image_id = idnormalizer.normalize(img_name)

                            new_folder.invokeFactory(type_name="Image", id=image_id, title=img_name, image=img)

                            timestamp = datetime.datetime.today().isoformat()
                            print "%s - %s: Added on existing FOLDER %s" %(timestamp, img_name, folder_name)

                        transaction.commit()

                object_item.reindexObject()
                object_item.reindexObject(idxs=["hasMedia"])
                object_item.reindexObject(idxs=["leadMedia"])

                result = True
                
                return result
            else:
                timestamp = datetime.datetime.today().isoformat()
                print "%s - %s: Skipped on %s - No slideshow" %(timestamp, folder_name, object_item.identification_identification_objectNumber)
                return True

        except:
            transaction.abort()
            timestamp = datetime.datetime.today().isoformat()
            print "%s - %s: FOLDER Skipped on %s" %(timestamp, folder_name, object_item.identification_identification_objectNumber)
            raise

        return True 


    def add_image(self, image_name, path, object_item):
        
        container = self.get_container()
        dirty_id = image_name
        normalized_id = idnormalizer.normalize(dirty_id)
        LIMIT = 1

        transaction.begin()

        try:
            if hasattr(object_item, 'slideshow'):
                slideshow = object_item['slideshow']
                folder = slideshow

                slideshow_len = len(slideshow.contentItems())
                if slideshow_len >= LIMIT:
                    if not hasattr(object_item, 'prive'):
                        self.new_prive_folder(object_item)
                        prive = object_item['prive']
                        folder = prive
                    else:
                        prive = object_item['prive']
                        folder = prive

                if not hasattr(folder, normalized_id):
                    image_file = open(path, "r")
                    image_data = image_file.read()
                    img = NamedBlobImage(
                        data=image_data
                    )
                    image_file.close()
                    folder.invokeFactory(type_name="Image", id=normalized_id, title=image_name, image=img)
                else:
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - %s: Image skipped. Already exists %s" % (timestamp, image_name, object_item.identification_identification_objectNumber)
                    return True

                transaction.commit()
                
                object_item.reindexObject()
                object_item.reindexObject(idxs=["hasMedia"])
                object_item.reindexObject(idxs=["leadMedia"])

                result = True
                timestamp = datetime.datetime.today().isoformat()
                print "%s - %s: Image added on %s" %(timestamp, image_name, object_item.identification_identification_objectNumber)

                return result
            else:
                timestamp = datetime.datetime.today().isoformat()
                print "%s - %s: Image skipped on %s" %(timestamp, image_name, object_item.identification_identification_objectNumber)
                transaction.abort()
                pass
        except:
            transaction.abort()
            timestamp = datetime.datetime.today().isoformat()
            print "%s - %s: Image skipped on %s" %(timestamp, image_name, object_item.identification_identification_objectNumber)
            pass

    def test_add_image(self):
        print "=== Start image creation test ==="

        object_number = self.art_list[TEST_OBJECT]
        dirty_id = object_number

        imagefilename = object_number.upper().replace(' ', "-")
        imagefilename = imagefilename + ".jpg"
        path = self.image_folder + imagefilename 
        object_id = idnormalizer.normalize(dirty_id)

        self.add_image(imagefilename, path, object_id)
        self.success = True
        return


    def test_create_object(self):
        print "=== Start object creation test ==="
        quoted_query = urllib.quote(self.art_list[TEST_OBJECT])
        api_request = API_REQUEST_URL % (quoted_query)

        xml_doc = self.parse_api_doc(api_request)

        root = xml_doc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        for record in records:
            if record.find('object_number') != None:
                object_number = record.find('object_number').text
                
                current_object = ObjectItem()
                if record.find('title') != None:
                    title = record.find('title').text
                    description = title
                else:
                    title = ""
                    description = ""

                current_object.title = title
                current_object.description = description
                current_object.identification_identification_objectNumber = object_number

                self.create_object(current_object)

        return

    def transform_creators_name(self, creators):
        date_birth = ""
        for creator in creators:
            if "Instruments" in self.image_folder or "instrumenten" in self.folder_path:
                creator['name'] = creator['temp_name']
            else:
                name = creator["temp_name"]
                
                if name != "":
                    name_without_year = re.sub(r'\([^)]*\)', '', name)
                    date_birth = creator["temp_name"].replace(name_without_year, '')
                    
                    if len(date_birth) > 0:
                        if date_birth[0] == " ":
                            date_birth = date_birth[1:]
                    else:
                        date_birth = ""

                    name_separated = name_without_year.split(',')
                    if len(name_separated) > 1:
                        if name_separated[0][-1] != " " and name_separated[0][0] != " ":
                            real_name = name_separated[1] + " " + name_separated[0]
                        else:
                            real_name = name_separated[1] + name_separated[0]

                        creator['name'] = "%s %s" %(real_name, date_birth)
                    else:
                        creator['name'] = "%s %s" %(name_separated[0], date_birth) 
                else:
                    creator['name'] = "%s %s" %(name,date_birth) 

    def transform_creator_name(self, name):
        if name != "":
            name_without_year = re.sub(r'\([^)]*\)', '', name)
            
            date_birth = name.replace(name_without_year, '')


            if len(date_birth) > 0:
                if date_birth[0] == " ":
                    date_birth = date_birth[1:]
                else:
                    date_birth = date_birth[:]

            name_separated = name_without_year.split(',')
            if len(name_separated) > 1:
                if name_separated[0][-1] != " " and name_separated[0][0] != " ":
                    real_name = name_separated[1] + " " + name_separated[0]
                else:
                    real_name = name_separated[1] + name_separated[0]

                return "%s %s" %(real_name, date_birth)
            else:
                return "%s %s" %(name_separated[0], date_birth)
        else:
            return name

    def create_creators_field(self, creators):
        creators_field_list = []
        
        for details in creators:
            creator = ""
            date_of_birth = ""

            if details['date_of_birth'] != details['date_of_death']:
                date_of_birth = "%s - %s" %(details['date_of_birth'], details['date_of_death'])
            elif details['date_of_birth'] != "":
                date_of_birth = "%s" %(details['date_of_birth'])

            if date_of_birth != "":
                if details['role'] != "":
                    creator = "%s, (%s) (%s)" %(details['name'], date_of_birth, details['role'])
                else:
                    creator = "%s, (%s)" %(details['name'], date_of_birth)
            else:
                if details["role"] != "":
                    creator = "%s (%s)" %(details['name'], details["role"])
                else:
                    creator = "%s" %(details['name'])
            
            creators_field_list.append(creator)

        creators_field = ", ".join(creators_field_list)
        
        return creators_field

    def create_creator_field(self, details):
        creator = ""
        date_of_birth = ""

        if details['date_of_birth'] != details['date_of_death']:
            date_of_birth = "%s - %s" %(details['date_of_birth'], details['date_of_death'])
        elif details['date_of_birth'] != "":
            date_of_birth = "%s" %(details['date_of_birth'])

        if date_of_birth != "":
            if details['role'] != "":
                creator = "%s, (%s) (%s)" %(details['temp_name'], date_of_birth, details['role'])
            else:
                creator = "%s, (%s)" %(details['temp_name'], date_of_birth)
        else:
            if details["role"] != "":
                creator = "%s (%s)" %(details['temp_name'], details["role"])
            else:
                creator = "%s" %(details['temp_name'])

        return creator

    def create_object_dirty_id(self, object_number, title, creator):
        if creator != "" and creator != None:
            dirty_id = "%s %s %s" % (object_number, title, creator)
        else:
            dirty_id = "%s %s" % (object_number, title)
        return dirty_id

    def create_object_description(self, creator, production):
        # Trim text
        description = ""
        try:
            if creator != "":
                if creator[0] == " ":
                    creator = creator[1:]

                if creator[-1] == " ":
                    creator = creator[:-1]

            if production != "" and creator != "":
                description = "%s, %s" % (creator, production)
            elif production != "" and creator == "":
                description = "%s" % (production)
            elif production == "" and creator != "":
                description = "%s" %(creator)

            if description != "":
                # Trim description
                if description[-1] == ",":
                    description = description[:-1]
        except:
            description = ""
            pass

        return description

    def trim_white_spaces(self, text):
        if text != "" and text != None:
            if text == "\nNLG":
                return "NLG"

            if text == "\nEUR":
                return "EUR"

            if type(text) == unicode:
                if text == u'\n\u20ac':
                    return "EUR"

            if text[0] == "\n":
                text = text[1:]

            if len(text) > 0:
                if text[0] == " ":
                    text = text[1:]
                if len(text) > 0:
                    if text[-1] == " ":
                        text = text[:-1]
                return text
            else:
                return ""
        else:
            return ""

    def create_object_production(self, production_date_start, production_date_end):
        if production_date_end == production_date_start:
            production = production_date_end
        elif production_date_end == None:
            production = "%s" % (production_date_start)
        elif production_date_start == None:
            production = "%s" % (production_date_end)
        elif production_date_start != "" and production_date_end != "" and len(production_date_end) > 1:
            production = "%s - %s" % (production_date_start, production_date_end)
        elif production_date_start != "" and production_date_end == "":
            production = "%s" % (production_date_start)
        else:
            production = ""

        return production

    def create_object_productions(self, production_date_prec, production_date_start, production_date_end):
        if production_date_end == production_date_start:
            production = production_date_end
        elif production_date_end == None:
            production = "%s" % (production_date_start)
        elif production_date_start == None:
            production = "%s" % (production_date_end)
        elif production_date_start != "" and production_date_end != "" and len(production_date_end) > 1:
            production = "%s - %s" % (production_date_start, production_date_end)
        elif production_date_start != "" and production_date_end == "":
            production = "%s" % (production_date_start)
        else:
            production = ""

        if production_date_prec != "":
            date_production = "%s %s" %(production_date_prec, production)
            return date_production
        else:
            return production
    
    # # #
    # ! Deprecated
    # # #
    def create_object_data(self, record):
        # Create object data
        object_number = record.find('object_number').text
        production_date_end = ""
        production_date_start = ""
        production = ""
        creator = ""
        title = ""
        description = ""
        dirty_id = ""
        text = ""
        tags = []

        if record.find('production.date.end') != None:
            production_date_end = record.find('production.date.end').text
        if record.find('production.date.start') != None:
            production_date_start = record.find('production.date.start').text
        if record.find('creator') != None:
            creator_temp = record.find('creator').text
            creator = self.transform_creator_name(creator_temp)

        production = self.create_object_production(production_date_start, production_date_end)

        if len(record.findall('content.subject')) > 0:
            for tag in record.findall('content.subject'):
                if tag.text != None:
                    tags.append(tag.text)

        if record.find('title') != None:
            title = record.find('title').text

        current_object = ObjectItem()
        current_object.title = title
        current_object.identification_identification_objectNumber = object_number
        current_object.production = production
        current_object.creator = creator
        current_object.dirty_id = self.create_object_dirty_id(object_number, title, creator)
        current_object.description = self.create_object_description(creator, production_date_end)
        current_object.text = current_object.description
        current_object.tags = tags

        return current_object

    def get_object_from_instance(self, object_number):
        container = self.get_container()

        for obj in container:
            if hasattr(container[obj], 'identification_identification_objectNumber'):
                if container[obj].identification_identification_objectNumber == object_number:
                    print "== Found object! =="
                    return container[obj]

        return None

    def get_outgoingloan_from_instance(self, object_number):
        container = self.get_container()

        for obj in container:
            if hasattr(container[obj], 'priref'):
                if container[obj].priref == object_number:
                    print "== Found object! =="
                    return container[obj]
        return None

    #def get_object_from_instance(self, object_number):
    #    for obj in self.all_objects:
    #        item = obj.getObject()
    #        if hasattr(item, 'identification_identification_objectNumber'):
    #            if item.identification_identification_objectNumber == object_number:
    #                #print "== Found object! =="
    #                return item
    #    return None
      
    def add_images(self):
        number = 0
        self.set_limit = 1000
        for obj in self.art_list:   
            object_item = self.get_object_from_instance(obj['number'])
            if object_item != None:
                if self.is_multiple_book:
                    for folder in obj["folders"]:
                        self.create_folder_add_image(obj["path"], object_item, folder["name"], folder["images_path"], folder["images"])
                else:
                    for img in obj['images']:
                        imagefilename = img
                        if "Instruments" in self.image_folder:
                            path = self.image_folder + obj['number'] + "/" + imagefilename
                        elif "Fossils" in self.image_folder:
                            path = self.image_folder + obj['number'] + "/" + imagefilename
                        elif "books" in self.image_folder:
                            path = obj['path'] + "/" + imagefilename
                        else:
                            path = self.image_folder + imagefilename
                        self.add_image(imagefilename, path, object_item)
            else:
                timestamp = datetime.datetime.today().isoformat()
                print "%s - %s Cannot find object: %s" % (timestamp, "", obj['number'])
            #   obj_number = obj['number'] + " recto"
            #   object_item = self.get_object_from_instance(obj_number)
            #   if object_item != None:
            #       for img in obj['images']:
            #           imagefilename = img
            #           if "Instruments" in self.image_folder or "Fossils" in self.image_folder:
            #               path = self.image_folder + obj['number'] + "/" + imagefilename
            #           else:
            #               path = self.image_folder + imagefilename
            #           #path = path.replace(" recto", "")
            #           self.add_image(imagefilename, path, object_item)
            #   else:
            #       timestamp = datetime.datetime.today().isoformat()
            #       print "%s - %s Cannot find object: %s" % (timestamp, imagefilename, obj['number'])
            
            number += 1
            if number >= self.set_limit:
                self.success = True
                return

        self.success = True
        return

    def add_objects(self):
        number = 0
        for obj in self.art_list:
            quoted_query = urllib.quote(obj)
            api_request = API_REQUEST_URL % (quoted_query)
            xml_doc = self.parse_api_doc(api_request)
            root = xml_doc.getroot()
            recordList = root.find("recordList")
            records = recordList.getchildren()

            if len(records) > 0:
                record = records[0]
                if record.find('object_number') != None:
                    
                    current_object = self.create_object_data(record)
                    self.create_object(current_object)
                    
                    number += 1
                    if number >= self.set_limit:
                        self.success = True
                        return
            else:
                self.skipped += 1
                self.skipped_ids.append(obj)


        self.success = True
        return

    def create_new_object(self, obj):
        transaction.begin()
        
        container = self.get_container()
        dirty_id = obj['dirty_id']
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Object already exists %s" % (timestamp, obj["object_number"])
                transaction.commit()
                return container[normalized_id]

            if not hasattr(container, normalized_id):
                object_item = self.get_object_from_instance(obj["object_number"])
                if object_item == None:
                    text = RichTextValue(obj['text'], 'text/html', 'text/html')

                    container.invokeFactory(
                        type_name="Object",
                        id=normalized_id,
                        title=obj['title'],
                        description=obj['description'],
                        object_number=obj['object_number'],
                        object_type=obj['object_type'],
                        dating=obj['dating'],
                        artist=obj['artist'],
                        material=obj['material'],
                        technique=obj['technique'],
                        dimension=obj['dimension'],
                        credit_line=obj['credit_line'],
                        object_description=obj['object_description'],
                        translated_title=obj['translated_title'],
                        scientific_name=obj["scientific_name"],
                        production_period=obj["production_period"],
                        inscription=obj['inscription'],
                        object_category=obj['object_category'],
                        location=obj["location"],
                        publisher=obj["publisher"],
                        fossil_dating=obj["fossil_dating"],
                        illustrator=obj['illustrator'],
                        author=obj['author'],
                        digital_reference=obj['digital_reference'],
                        production_notes=obj['production_notes'],
                        text=text
                        )



                    # Get object and add tags
                    created_object = container[str(normalized_id)]
                    
                    #if len(obj['tags']) > 0:
                    #   created_object.setSubject(obj['tags'])

                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    
                    transaction.commit()

                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added object %s" % (timestamp, obj["object_number"])

                    self.created += 1
                    result = True
                else:
                    self.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Object already exists %s" % (timestamp, obj["object_number"])
                    transaction.commit()
                    return object_item

        except:
            self.errors += 1
            self.success = False
            print "Unexpected error on create_object (" +dirty_id+ "):", sys.exc_info()[1]
            result = False
            transaction.abort()
            return result

        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            print "%s - Skipped object: %s" %(timestamp, obj["object_number"])

        return created_object

    def transform_d(self, dimension_type):
        if dimension_type == "hoogte":
            return "hoogte"
        elif dimension_type == "breedte":
            return "breedte"
        elif dimension_type == "gewicht":
            return "gewicht"
        else:
            ## any other type: length, diameter
            return dimension_type

    def create_dimension_field(self, dimension_data):
        if len(dimension_data['dimensions']) > 0:

            all_dimensions = dimension_data['dimensions']
            part = all_dimensions[0]['part']
            
            if part != "":
                dimensions = ""
                number = 0
                for d in all_dimensions:
                    number += 1
                    if number != len(all_dimensions):
                        if d["part"] != "":
                            if self.transform_d(d['type']) != "":
                                if (d["part"] in ['papier', 'opzet', 'lijst']) and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s %s (%s)<p>" % (d['value'], d['unit'], d['part'])
                        else:
                            if self.transform_d(d['type']) != "":
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                            else:
                                dimensions += "%s %s<p>" % (d['value'], d['unit'])
                    else:
                        if d["part"] != "":
                            if self.transform_d(d['type']) != "":
                                if (d["part"] in ['papier', 'opzet', 'lijst']) and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s %s (%s)<p>" % (d['value'], d['unit'], d['part'])
                        else:
                            if self.transform_d(d['type']) != "":
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                            else:
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s %s<p>" % (d['value'], d['unit'])
                dimension = dimensions
            else:
                dimensions = ""
                number = 0
                for d in all_dimensions:
                    number += 1
                    if number != len(all_dimensions):
                        if self.transform_d(d['type']) != "":
                            if d["part"] != "":
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                        else:
                            dimensions += "%s %s<p>" % (d['value'], d['unit'])
                    else:
                        if self.transform_d(d['type']) != "":
                            if d["part"] != "":
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                        else:
                            if d['part'] != "":
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                elif (d["part"] in ['lijst']) and (('paintings' in self.image_folder) or ('paintings' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s %s (%s)<p>" % (d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s %s<p>" % (d['value'], d['unit'])

                dimension = "%s" %(self.trim_white_spaces(dimensions))

            return dimension
        else:
            return ""

    def create_inscription_field(self, inscription_data):
        field_inscription = ""

        if len(inscription_data) > 0:
            for inscription in inscription_data:
                field_inscription += "%s: %s <p>" %(inscription['type'], inscription['content'])

            return field_inscription
        else:
            return ""

    def fetch_object_api(self, priref, create):
        print "fetch %s from API." %(str(priref))

        API_REQ = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=priref=%s&xmltype=grouped" % (priref)
        xml_file = self.parse_api_doc(API_REQ)
        root = xml_file.getroot()

        recordList = root.find('recordList')
        records = recordList.getchildren()

        first_record = records[0]

        object_data = {
            "title": "",
            "dirty_id": "",
            "description": "",
            "artist": "",
            "text": "",
            "object_number": "",
            "object_type": "",
            "dating": "",
            "term": "",
            "material": "",
            "technique": "",
            "dimension": "",
            "credit_line": "",
            "object_description": "",
            "inscription": "",
            "scientific_name": "",
            "translated_title": "",
            "production_period": "",
            "object_category": "",
            "location": "",
            "publisher": "",
            "fossil_dating": "",
            "illustrator": "",
            "author": "",
            "digital_reference": "",
            "production_notes": "",
            "tags": []
        }

        object_temp_data = {
            "production_date_end": "",
            "production_date_start": "",
            "production_date_prec": "",
            "dimensions": []
        }

        inscription_temp_data = []

        if first_record.find('object_number') != None:
            object_data['object_number'] = self.trim_white_spaces(first_record.find('object_number').text)

        if first_record.find('Object_name') != None:
            if first_record.find('Object_name').find('object_name') != None:
                object_data['object_type'] = self.trim_white_spaces(first_record.find('Object_name').find('object_name').text)
        
        if first_record.find('Title') != None:
            if first_record.find('Title').find('title').find('value') != None:
                object_data['title'] = self.trim_white_spaces(first_record.find('Title').find('title').find('value').text)
        
        if len(first_record.findall('Technique')) > 1:
            index = 0
            for technique in first_record.findall('Technique'):
                index += 1
                if technique.find('technique') != None:
                    if index != len(first_record.findall('Technique')):
                        object_data['technique'] += "%s, " %(self.trim_white_spaces(technique.find('technique').text))
                    else:
                        object_data['technique'] += "%s" %(self.trim_white_spaces(technique.find('technique').text))

        elif len(first_record.findall('Technique')) > 0:
            if first_record.findall('Technique')[0].find('technique') != None:
                    object_data['technique'] = self.trim_white_spaces(first_record.findall('Technique')[0].find('technique').text)

        #
        # Update material
        #
        if first_record.findall('Material') != None:
            index = 0
            if len(first_record.findall('Material')) > 1:
                # Multiple material
                for material in first_record.findall('Material'):
                    index += 1
                    if material.find('material') != None:
                        if index != len(first_record.findall('Material')):
                            object_data['material'] += "%s, " %(self.trim_white_spaces(material.find('material').text))
                        else:
                            object_data['material'] += "%s" %(self.trim_white_spaces(material.find('material').text))
            # Single material
            elif len(first_record.findall('Material')) > 0:
                if first_record.findall('Material')[0].find('material') != None:
                    object_data['material'] = self.trim_white_spaces(first_record.findall('Material')[0].find('material').text)
        
        # priref
        if first_record.find('priref') != None:
            object_data['priref'] = self.trim_white_spaces(first_record.find('priref').text)

        # Creator
        creators = []

        creator_details_obj = {
            "temp_name": "",
            "name": "",
            "date_of_birth": "",
            "date_of_death": "",
            "role": ""
        }

        if first_record.findall('Production') != None:
            for production in first_record.findall('Production'):
                creator_details = {
                    "temp_name": "",
                    "name": "",
                    "date_of_birth": "",
                    "date_of_death": "",
                    "role": ""
                }
                if production.find('creator') != None:
                    creator_details["temp_name"] = self.trim_white_spaces(production.find('creator').text)
                if production.find('creator.date_of_birth') != None:
                    creator_details["date_of_birth"] = self.trim_white_spaces(production.find('creator.date_of_birth').text)
                if production.find('creator.date_of_death') != None:
                    creator_details["date_of_death"] = self.trim_white_spaces(production.find('creator.date_of_death').text)
                if production.find('creator.role') != None:
                    creator_details["role"] = self.trim_white_spaces(production.find('creator.role').text)

                creators.append(creator_details)

        if first_record.find('Production_date') != None:
            if first_record.find('Production_date').find('production.date.start') != None:
                object_temp_data['production_date_start'] = self.trim_white_spaces(first_record.find('Production_date').find('production.date.start').text) 
            if first_record.find('Production_date').find('production.date.end') != None:
                object_temp_data['production_date_end'] = self.trim_white_spaces(first_record.find('Production_date').find('production.date.end').text)
            if first_record.find('Production_date').find('production.date.start.prec') != None:
                object_temp_data['production_date_prec'] = self.trim_white_spaces(first_record.find('Production_date').find('production.date.start.prec').text)
        
        if object_temp_data['production_date_start'] == "" and object_temp_data['production_date_end'] == "" and first_record.find('Production_date') != None:
            if first_record.find('Production_date').find('production.date.start.prec') != None:
                object_temp_data['production_date_start'] = self.trim_white_spaces(first_record.find('Production_date').find('production.date.start.prec').text)
                if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path):
                    object_temp_data['production_date_prec'] = ""

        if first_record.find('production.date.notes') != None:
            object_temp_data['production_notes'] = first_record.find('production.date.notes').text

        use_label = False

        #
        # FIND ENGLISH TEXT
        #
        if self.is_en:
            label_text = ""
            if len(first_record.findall('Label')) > 0:
                for label in first_record.findall('Label'):
                    if label.find('label.type') != None:
                        if len(label.find('label.type').findall('value')) > 0:
                            for value in label.find('label.type').findall('value'):
                                if (value.text == "WEBTEXT ENG") or (value.text == "website text ENG") or (value.text == "website-tekst ENG"):
                                    use_label = True
                                    if label.find('label.text') != None:
                                        label_text = label.find('label.text').text
                                        object_data["text"] = self.trim_white_spaces(label_text)
                                    break

            if use_label and label_text == "":
                if first_record.find('Label') != None:
                    if first_record.find('Label').find('label.text') != None:
                        object_data["text"] = self.trim_white_spaces(first_record.find('Label').find('label.text').text)
        else:
            if first_record.find('Label') != None:
                if first_record.find('Label').find('label.type') != None:
                    if first_record.find('Label').find('label.type').findall('value') != None:
                        for ltype in first_record.find('Label').find('label.type').findall('value'):
                            if (ltype.text == "website-tekst") or (ltype.text == "website-tekst ENG") or (ltype.text == "WEBTEXT"):
                                use_label = True
                                break
                if use_label:
                    if first_record.find('Label') != None:
                        if first_record.find('Label').find('label.text') != None:
                            object_data["text"] = self.trim_white_spaces(first_record.find('Label').find('label.text').text)

        if first_record.findall('Dimension') != None:
            for d in first_record.findall('Dimension'):
                if d.find('dimension.part') != None:
                    new_dimension = {
                        "part": "",
                        "value": "",
                        "type": "",
                        "unit": ""
                    }

                    new_dimension['part'] = self.trim_white_spaces(d.find('dimension.part').text)

                    if d.find('dimension.value') != None:
                        new_dimension['value'] = self.trim_white_spaces(d.find('dimension.value').text)
                    if d.find('dimension.type') != None:
                        new_dimension['type'] = self.trim_white_spaces(d.find('dimension.type').text)
                    if d.find('dimension.unit') != None:
                        new_dimension['unit'] = self.trim_white_spaces(d.find('dimension.unit').text)
                    
                    object_temp_data['dimensions'].append(new_dimension)
                else:
                    new_dimension = {
                        "part": "",
                        "value": "",
                        "type": "",
                        "unit": ""
                    }

                    if d.find('dimension.value') != None:
                        new_dimension['value'] = self.trim_white_spaces(d.find('dimension.value').text)
                    if d.find('dimension.type') != None:
                        new_dimension['type'] = self.trim_white_spaces(d.find('dimension.type').text)
                    if d.find('dimension.unit') != None:
                        new_dimension['unit'] = self.trim_white_spaces(d.find('dimension.unit').text)
                    
                    object_temp_data['dimensions'].append(new_dimension)
            

        if len(first_record.findall('Content_subject')) > 0:
            for tag in first_record.findall('Content_subject'):
                if tag.find('content.subject') != None:
                    object_data['tags'].append(self.trim_white_spaces(tag.find('content.subject').text))

        # Credit line
        if first_record.find('credit_line') != None:
            object_data['credit_line'] = self.trim_white_spaces(first_record.find('credit_line').text)


        # Descriptions
        if len(first_record.findall('Description')) != None:
            for desc in first_record.findall('Description'):
                if desc.find('description') != None:
                    object_data['object_description'] += self.trim_white_spaces(desc.find('description').text)
                    object_data['object_description'] += "<p>"

        if len(first_record.findall('Inscription')) != None:
            for inscription in first_record.findall('Inscription'):
                if inscription.find('inscription.content') != None:
                    if inscription.find('inscription.content').text != "":
                        if inscription.find('inscription.type') != None:
                            inscription_temp_data.append({
                                "content": self.trim_white_spaces(inscription.find('inscription.content').text),
                                "type": self.trim_white_spaces(inscription.find('inscription.type').text)
                            })

        # Scientific name
        if first_record.find('Taxonomy') != None:
            if first_record.find('Taxonomy').find('taxonomy.scientific_name') != None:
                object_data['scientific_name'] = self.trim_white_spaces(first_record.find('Taxonomy').find('taxonomy.scientific_name').text)

        if (("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path)) and object_data["title"] != "":
            object_data["description"] = object_data["title"]

        if (("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path)) and object_data["title"] != "" and object_data['scientific_name'] != "":
            object_data["description"] = object_data["scientific_name"]

        if (("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path)) and object_data["title"] == "":
            object_data["title"] = object_data["scientific_name"]

        object_data['inscription'] = self.create_inscription_field(inscription_temp_data)
        


        ## CREATOR
        self.transform_creators_name(creators)
        object_data['artist'] = self.create_creators_field(creators)


        object_data['dimension'] = self.create_dimension_field(object_temp_data)
        
        if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path):
            object_data['dating'] = ""
            object_data['fossil_dating'] = self.create_object_productions(object_temp_data['production_date_prec'], object_temp_data['production_date_start'], object_temp_data['production_date_end'])
        else:
            object_data['dating'] = self.create_object_productions(object_temp_data['production_date_prec'], object_temp_data['production_date_start'], object_temp_data['production_date_end'])
        
        if not "Fossils" in self.image_folder:
            if len(creators) > 0:
                object_data['description'] = self.create_object_description(creators[0]["name"], object_temp_data['production_date_end'])
            else:
                object_data['description'] = self.create_object_description("", object_temp_data['production_date_end'])
        
        if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path):
            if first_record.find('title.translation') != None:
                object_data["translated_title"] = first_record.find('title.translation').text

        if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path):
            if first_record.find('production.period') != None:
                object_data["production_period"] = first_record.find('production.period').text


        if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path):
            if object_data['object_type'] != "":
                object_data["description"] += object_data["object_type"]
                if object_data["production_period"] != "":
                    object_data["description"] += ", %s" %(object_data["production_period"])
            else:
                if object_data["production_period"] != "":
                    object_data["description"] += "%s" %(object_data["production_period"])

        if self.is_en:
            if first_record.find('title.translation') != None:
                object_data["translated_title"] = first_record.find('title.translation').text


        if first_record.find('object_category') != None:
            object_data['object_category'] = first_record.find('object_category').text

        object_data['dirty_id'] = self.create_object_dirty_id(object_data['object_number'], object_data['title'], object_data['artist'])

        if create:
            result = self.create_new_object(object_data)
            return result
        else:
            return object_data

    def add_translations(self):
        print "Add translations"
        number = 0
        container = self.get_container()
        total = 0

        for obj in list(container):
            item = container[obj]
            if item.portal_type == "Object":
                try:
                    if item != None:
                        #transaction.begin()

                        if not ITranslationManager(item).has_translation('en'):
                            transaction.begin()
                            #print "Try to add translation for %s" % (item.identification_identification_objectNumber)
                            ITranslationManager(item).add_translation('en')

                            item_trans = ITranslationManager(item).get_translation('en')
                            item_trans.title = item.title
                            item_trans.text = item.text
                            item_trans.description = item.description
                            item_trans.identification_identification_objectNumber = item.identification_identification_objectNumber
                            item_trans.object_type = item.object_type
                            item_trans.artist = item.artist
                            item_trans.dating = item.dating
                            item_trans.dimension = item.dimension
                            item_trans.material = item.material
                            item_trans.technique = item.technique
                            item_trans.object_description = item.object_description
                            item_trans.credit_line = item.credit_line
                            item_trans.scientific_name = item.scientific_name
                            item_trans.translated_title = item.translated_title
                            item_trans.production_period = item.production_period
                            item_trans.object_category = item.object_category
                            item_trans.illustrator = item.illustrator
                            item_trans.author = item.author
                            #item_trans.setSubject(item.Subject())
                            item_trans.portal_workflow.doActionFor(item_trans, "publish", comment="Item published")

                            transaction.commit()

                            if hasattr(item, 'slideshow'):
                                slideshow = item['slideshow']

                                if not ITranslationManager(slideshow).has_translation('en'):
                                    transaction.begin()
                                    
                                    ITranslationManager(slideshow).add_translation('en')
                                    slideshow_trans = ITranslationManager(slideshow).get_translation('en')
                                    slideshow_trans.title = slideshow.title
                                    slideshow_trans.portal_workflow.doActionFor(slideshow_trans, "publish", comment="Slideshow published")

                                    transaction.commit()

                                s_item = 0
                                for sitem in slideshow:
                                    

                                    s_item += 1

                                    if self.is_book:
                                        if slideshow[sitem].portal_type == "Image":
                                            print "Adding image single book %s" % (sitem)
                                            if not ITranslationManager(slideshow[sitem]).has_translation('en'):
                                                transaction.begin()
                                                ITranslationManager(slideshow[sitem]).add_translation('en')
                                                trans = ITranslationManager(slideshow[sitem]).get_translation('en')
                                                trans.image = slideshow[sitem].image
                                                if s_item == 1:
                                                    addCropToTranslation(slideshow[sitem], trans)
                                                transaction.commit()

                                        elif slideshow[sitem].portal_type == "Folder":
                                            if not ITranslationManager(slideshow[sitem]).has_translation('en'):
                                                transaction.begin()
                                                print "Adding translation for book %s inside of book %s" %(sitem, item.identification_identification_objectNumber)
                                                nl_folder = slideshow[sitem]
                                                ITranslationManager(nl_folder).add_translation('en')

                                                en_folder = ITranslationManager(nl_folder).get_translation('en')
                                                en_folder.title = nl_folder.title
                                                en_folder.portal_workflow.doActionFor(en_folder, "publish", comment="Book published")
                                                transaction.commit()

                                                item_n = 0
                                                for fitem in nl_folder:
                                                    transaction.begin()
                                                    if nl_folder[fitem].portal_type == "Image":
                                                        item_n += 1
                                                        if not ITranslationManager(nl_folder[fitem]).has_translation('en'):
                                                            ITranslationManager(nl_folder[fitem]).add_translation('en')
                                                            itrans = ITranslationManager(nl_folder[fitem]).get_translation('en')
                                                            itrans.image = nl_folder[fitem].image
                                                            if item_n == 1:
                                                                addCropToTranslation(nl_folder[fitem], itrans)
                                                    transaction.commit()

                                                #print "Added translation for book %s inside of book %s" %(sitem, item.identification_identification_objectNumber)
                                            else:
                                                nl_folder = slideshow[sitem]
                                                item_n = 0
                                                for fitem in nl_folder:
                                                    transaction.begin()
                                                    item_n += 1
                                                    if nl_folder[fitem].portal_type == "Image":
                                                        if not ITranslationManager(nl_folder[fitem]).has_translation('en'):
                                                            ITranslationManager(nl_folder[fitem]).add_translation('en')
                                                            itrans = ITranslationManager(nl_folder[fitem]).get_translation('en')
                                                            itrans.image = nl_folder[fitem].image
                                                            if item_n == 1:
                                                                addCropToTranslation(nl_folder[fitem], itrans)
                                                    transaction.commit()


                                                #print "Added translation for book %s inside of book %s" %(sitem, item.identification_identification_objectNumber)

                                    else:
                                        if slideshow[sitem].portal_type == "Image":
                                            transaction.begin()
                                            
                                            ITranslationManager(slideshow[sitem]).add_translation('en')
                                            trans = ITranslationManager(slideshow[sitem]).get_translation('en')
                                            trans.image = slideshow[sitem].image

                                            addCropToTranslation(slideshow[sitem], trans)

                                            transaction.commit()

                            transaction.begin()
                            item_trans.reindexObject()
                            item_trans.reindexObject(idxs=["hasMedia"])
                            item_trans.reindexObject(idxs=["leadMedia"])
                            transaction.commit()

                            #print "Added translation for %s" % (item.identification_identification_objectNumber)
                        else:
                            print "Translation already created for %s - trying to complete" % (item.identification_identification_objectNumber)

                            item_trans = ITranslationManager(item).get_translation('en')
                            print item_trans.absolute_url()

                            total += 1

                            if hasattr(item, 'slideshow'):
                                slideshow = item['slideshow']

                                if not ITranslationManager(slideshow).has_translation('en'):
                                    transaction.begin()
                                    
                                    ITranslationManager(slideshow).add_translation('en')
                                    slideshow_trans = ITranslationManager(slideshow).get_translation('en')
                                    slideshow_trans.title = slideshow.title
                                    slideshow_trans.portal_workflow.doActionFor(slideshow_trans, "publish", comment="Slideshow published")

                                    transaction.commit()

                                s_item = 0
                                for sitem in slideshow:

                                    s_item += 1

                                    if self.is_book:
                                        if slideshow[sitem].portal_type == "Image":
                                            
                                            if not ITranslationManager(slideshow[sitem]).has_translation('en'):
                                                #print "Adding image single book %s" % (sitem)
                                                transaction.begin()
                                                ITranslationManager(slideshow[sitem]).add_translation('en')
                                                trans = ITranslationManager(slideshow[sitem]).get_translation('en')
                                                trans.image = slideshow[sitem].image
                                                if s_item == 1:
                                                    addCropToTranslation(slideshow[sitem], trans)
                                                transaction.commit()

                                        elif slideshow[sitem].portal_type == "Folder":
                                            if not ITranslationManager(slideshow[sitem]).has_translation('en'):
                                                transaction.begin()
                                                #print "Adding translation for book %s inside of book %s" %(sitem, item.identification_identification_objectNumber)
                                                nl_folder = slideshow[sitem]
                                                ITranslationManager(nl_folder).add_translation('en')

                                                en_folder = ITranslationManager(nl_folder).get_translation('en')
                                                en_folder.title = nl_folder.title
                                                en_folder.portal_workflow.doActionFor(en_folder, "publish", comment="Book published")
                                                transaction.commit()

                                                item_n = 0
                                                for fitem in nl_folder:
                                                    transaction.begin()
                                                    if nl_folder[fitem].portal_type == "Image":
                                                        item_n += 1
                                                        if not ITranslationManager(nl_folder[fitem]).has_translation('en'):
                                                            ITranslationManager(nl_folder[fitem]).add_translation('en')
                                                            itrans = ITranslationManager(nl_folder[fitem]).get_translation('en')
                                                            itrans.image = nl_folder[fitem].image
                                                            if item_n == 1:
                                                                addCropToTranslation(nl_folder[fitem], itrans)
                                                    transaction.commit()

                                                #print "Added translation for book %s inside of book %s" %(sitem, item.identification_identification_objectNumber)
                                            else:
                                                nl_folder = slideshow[sitem]
                                                item_n = 0
                                                for fitem in nl_folder:
                                                    transaction.begin()
                                                    item_n += 1
                                                    if nl_folder[fitem].portal_type == "Image":
                                                        if not ITranslationManager(nl_folder[fitem]).has_translation('en'):
                                                            ITranslationManager(nl_folder[fitem]).add_translation('en')
                                                            itrans = ITranslationManager(nl_folder[fitem]).get_translation('en')
                                                            itrans.image = nl_folder[fitem].image
                                                            if item_n == 1:
                                                                addCropToTranslation(nl_folder[fitem], itrans)
                                                    transaction.commit()


                                                #print "Added translation for book %s inside of book %s" %(sitem, item.identification_identification_objectNumber)

                                    else:
                                        if slideshow[sitem].portal_type == "Image":
                                            transaction.begin()
                                            
                                            ITranslationManager(slideshow[sitem]).add_translation('en')
                                            trans = ITranslationManager(slideshow[sitem]).get_translation('en')
                                            trans.image = slideshow[sitem].image

                                            addCropToTranslation(slideshow[sitem], trans)

                                            transaction.commit()

                            #print "Completed translation for %s" % (item.identification_identification_objectNumber)
                    
                    number += 1
                    if number >= self.set_limit:
                        self.success = True
                        return
                except:
                    number += 1
                    self.skipped += 1
                    transaction.abort()
                    raise


        print "TOTAL TRANSLATED"
        print total

        self.success = True
        return

    def convert_object_number_priref(self, object_number):
        quoted_query = urllib.quote(object_number)
        api_request = API_REQUEST_URL_COLLECT % (quoted_query)
        xml_doc = self.parse_api_doc(api_request)
        root = xml_doc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        priref = ""

        if len(records) > 0:
            record = records[0]
            if record.find('object_number') != None:
                if record.find('priref') != None:
                    priref = record.find('priref').text

        return priref

    def convert_shelf_priref(self, object_number):
        quoted_query = urllib.quote(object_number)
        api_request = API_REQUEST_URL % (quoted_query)
        print api_request
        xml_doc = self.parse_api_doc(api_request)
        root = xml_doc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        priref = ""

        if len(records) > 0:
            record = records[0]
            if record.find('shelf_mark') != None:
                if record.find('priref') != None:
                    priref = record.find('priref').text
        return priref

    def update_objects(self):
        number = 0
        for obj in self.art_list:
            # Convert object number to priref
            priref = self.convert_object_number_priref(obj['number'])
            object_data = ""
            
            if priref != "":
                object_data = self.fetch_object_api(priref, False)
            else:
                if 'drawings' in self.image_folder:
                    obj['number'] = obj['number'] + " recto"
                    priref = self.convert_object_number_priref(obj['number'])
                    if priref != "":
                        object_data = self.fetch_object_api(priref, False)
                    else:
                        self.skipped += 1
                        self.skipped_ids.append(obj['number'])
                        print "Skipped item: " + obj['number']
                elif 'Fossils' in self.image_folder:
                    if obj['number'][0] == "M":
                        obj['number'] = obj['number'][1:]
                        priref = self.convert_object_number_priref(obj['number'])
                        if priref != "":
                            object_data = self.fetch_object_api(priref, False)
                        else:
                            self.skipped += 1
                            self.skipped_ids.append(obj['number'])
                            print "Skipped item: " + obj['number']  

            # Update object
            if object_data != "":
                obj_item = None

                object_item = self.get_object_from_instance(obj['number'])
                if object_item != None:
                    obj_item = object_item
                    text = RichTextValue(object_data['text'], 'text/html', 'text/html')
                    obj_item.title = object_data['title']
                    obj_item.description = object_data['description']
                    obj_item.identification_identification_objectNumber = object_data['object_number']
                    obj_item.object_type = object_data['object_type']
                    obj_item.dating = object_data['dating']
                    obj_item.artist = object_data['artist']
                    obj_item.material = object_data['material']
                    obj_item.technique = object_data['technique']
                    obj_item.dimension = object_data['dimension']
                    obj_item.credit_line = object_data['credit_line']
                    obj_item.object_description = object_data['object_description']
                    obj_item.scientific_name = object_data['scientific_name']
                    obj_item.translated_title = object_data['translated_title']
                    obj_item.production_period = object_data['production_period']
                    obj_item.object_category = object_data['object_category']
                    obj_item.text = text

                    if len(object_data['tags']) > 0:
                        obj_item.setSubject(object_data['tags'])
                    
                    obj_item.reindexObject()

                    print "=== Object %s updated ===" %(obj_item.identification_identification_objectNumber)

            number += 1
            if number >= self.set_limit:
                self.success = True
                return

    def add_test_objects(self):
        number = 0
        for obj in self.art_list:
            try:
                transaction.begin()
        
                container = self.get_container()
                dirty_id = obj['number']
                normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                result = False

                if hasattr(container, normalized_id) and normalized_id != "":
                    self.skipped += 1
                    print "Item '%s' already exists" % (dirty_id)
                    transaction.commit()
                    return True

                if not hasattr(container, normalized_id):
                    print "New object found. Adding: %s" % (dirty_id)

                    container.invokeFactory(
                        type_name="Object",
                        id=normalized_id,
                        title=obj['number'],
                        object_number=obj['number'],
                        description=obj['number']
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")
                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    transaction.commit()
                    self.created += 1
                    result = True

                    if not result:
                        self.skipped += 1
                        transaction.abort()
                        print "Skipped item: " + dirty_id
            except:
                print "== Skipped %s ==" %(obj['number'])
                self.skipped_ids.append(obj['number'])
                pass

            number += 1
            if number >= self.set_limit:
                self.success = True
                return

    def has_object_number(self, list_of_drawings, object_number):
        result = filter(lambda obj: obj['number'] == object_number, list_of_drawings)
        return result

    def fix_drawings_from_api(self):
        list_of_drawings = [' recto', 'A 019 verso recto', 'A 027 verso_1 recto', 'A 027_1 recto', 'A 029 verso recto', 'A 029bis verso recto', 'A 029bis recto', 'A 032 verso recto', 'A 033bisR recto', 'A 033bisV recto', 'A 036 verso recto', 'A 058verso recto', 'A 084 verso recto', 'A I 003 recto', 'A I 075 recto', 'A I 076 recto', 'AA 046a verso recto', 'AA 078-2 recto', 'ATS_339-024 recto', 'B 028 verso recto', 'B 088 recto', 'B 099 HnD 161 recto', 'B 3279 recto', 'BB 030-bijlage recto', 'BB 035 met lijst recto', 'BB 078a recto', 'BB 078b recto', 'BB 078c recto', 'BB+ 044a recto', 'BB+ 044b recto', 'BRAM 001 recto', 'BRAM 006 recto', 'BRAM 007 recto', 'BRAM 008 recto', 'BRAM 009 recto', 'BRAM 010 recto', 'BRAM 012 recto', 'BRAM 013 recto', 'BRAM 015 recto', 'Brieven Maris recto', 'Brieven Maris_02 recto', 'C 0028 recto', 'C 004 verso recto', 'C 007 verso recto', 'C 010 verso recto', 'C 012 verso recto', 'C 015 verso recto', 'C 018 verso recto', 'C 022 verso recto', 'C 023 verso recto', 'C 024a verso recto', 'C 024a recto', 'C 024b verso recto', 'C 024b recto', 'C 033 verso recto', 'C 035 verso recto', 'C 048a recto', 'C 059 verso recto', 'C 061 verso recto', 'C 067 verso recto', 'C 073 verso recto', 'C 073 recto', 'C 077 verso recto', 'C 077 recto', 'C 078 verso recto', 'C 078 recto', 'C 079 verso recto', 'C 079 recto', 'C 081 verso recto', 'C 081 recto', 'C 0814 recto', 'C 082 verso recto', 'C 082 recto', 'C 0854 recto', 'C 086 recto', 'C 087 verso recto', 'C 087 recto', 'C 088 verso recto', 'C 088 recto', 'C 090 recto', 'C 091 recto', 'C 095 verso recto', 'C 095 recto', 'C 100 recto', 'C 103 recto', 'C 1032 recto', 'C 1046 recto', 'C 107 verso recto', 'C 107 recto', 'C 1088 recto', 'C 1089 recto', 'C 109 verso recto', 'C 109 recto', 'C 1091 verso recto', 'C 1091 recto', 'C 1092 verso recto', 'C 1092 recto', 'C 1101 verso recto', 'C 1101 recto', 'C 1103 verso recto', 'C 1103 recto', 'C 1109 recto', 'C 112 verso recto', 'C 112 recto', 'C 115 verso recto', 'C 115 recto', 'C 1157b recto', 'C 116 verso recto', 'C 116 recto', 'C 1187 recto', 'C 119 recto', 'C 120 verso recto', 'C 120 recto', 'C 1206 recto', 'C 121 verso recto', 'C 121 recto', 'C 1229 recto', 'C 123 verso recto', 'C 123 recto', 'C 124 verso recto', 'C 124 recto', 'C 1250 recto', 'C 1256 recto', 'C 125a verso recto', 'C 125a recto', 'C 125b verso recto', 'C 125b recto', 'C 126 verso recto', 'C 126 recto', 'C 1267 recto', 'C 127 verso recto', 'C 127 recto', 'C 1282 recto', 'C 129 verso recto', 'C 129 recto', 'C 1328 recto', 'C 1335 recto', 'C 134 recto', 'C 140 verso recto', 'C 140 recto', 'C 141 verso recto', 'C 141 recto', 'C 145 verso recto', 'C 145 recto', 'C 1459 recto', 'C 146 verso recto', 'C 146 recto', 'C 1484 verso recto', 'C 1484 recto', 'C 1496 verso recto', 'C 1496 recto', 'C 154 verso recto', 'C 154 recto', 'C 155a verso recto', 'C 155a recto', 'C 155b verso recto', 'C 155b recto', 'C 156 verso recto', 'C 156 recto', 'C 159 recto', 'C 1590 recto', 'C 1596 recto', 'C 1616 recto', 'C 1617 verso recto', 'C 1617 recto', 'C 1639 recto', 'C 1647 recto', 'C 165 verso recto', 'C 165 recto', 'C 167 verso recto', 'C 167 recto', 'C 1738 verso recto', 'C 1738 recto', 'C 179 recto', 'C 1804 verso recto', 'C 1804 recto', 'C 1837 recto', 'C 186 verso recto', 'C 186 recto', 'C 189 verso recto', 'C 189 recto', 'C 190 verso recto', 'C 190 recto', 'C 191 recto', 'C 1913 verso recto', 'C 1913 recto', 'C 192 recto', 'C 1922 recto', 'C 194 verso recto', 'C 194 recto', 'C 195 recto', 'C 196 recto', 'C 1963 verso recto', 'C 1963 recto', 'C 1966 recto', 'C 198 recto', 'C 1987 recto', 'C 199 recto', 'C 200 recto', 'C 201 recto', 'C 202 recto', 'C 204 recto', 'C 205 recto', 'C 207 recto', 'C 208 recto', 'C 209 recto', 'C 210 verso recto', 'C 210 recto', 'C 211 verso recto', 'C 211 recto', 'C 2132 recto', 'C 214 recto', 'C 216 recto', 'C 2177 recto', 'C 219 recto', 'C 2208 recto', 'C 221 recto', 'C 2247 recto', 'C 2248 recto', 'C 225 recto', 'C 226 verso recto', 'C 226 recto', 'C 227 recto', 'C 228 recto', 'C 229 recto', 'C 230 recto', 'C 231 recto', 'C 232 verso recto', 'C 232 recto', 'C 233 recto', 'C 236 recto', 'C 2367 recto', 'C 237 verso recto', 'C 237 recto', 'C 2399 recto', 'C 246 recto', 'C 247 recto', 'C 249 verso recto', 'C 249 recto', 'C 250 recto', 'C 251 verso recto', 'C 251 recto', 'C 255 recto', 'C 257 recto', 'C 3046 recto', 'C 3047 verso recto', 'C 3047 recto', 'C 3048 recto', 'C 3112 recto', 'C 3117 verso recto', 'C 3117 recto', 'C 3329 recto', 'C 3366 recto', 'C 622 recto', 'C 650 recto', 'C 658 recto', 'C 666 recto', 'C 669 recto', 'C 670 recto', 'C 671 recto', 'C 674 recto', 'C 675 verso recto', 'C 675 recto', 'C 683 verso recto', 'C 683 recto', 'C 687 recto', 'C 688 recto', 'C 698 recto', 'C 701a recto', 'C 701b recto', 'C 701c verso recto', 'C 701c recto', 'C 707 recto', 'C 709 verso recto', 'C 709 recto', 'C 710 verso recto', 'C 710 recto', 'C 711 verso recto', 'C 711 recto', 'C 714 verso recto', 'C 714 recto', 'C 718 recto', 'C 720 verso recto', 'C 720 recto', 'C 723 recto', 'C 724 recto', 'C 736 recto', 'C 748 recto', 'C 751 recto', 'C 764 verso recto', 'C 764 recto', 'C 776 recto', 'C 779b recto', 'C 788 recto', 'C 794 recto', 'C 800 recto', 'C 808 recto', 'C 835 recto', 'C 845 recto', 'C 846 recto', 'C 862 verso recto', 'C 862 recto', 'C 864 recto', 'C 866 recto', 'C 867 verso recto', 'C 867 recto', 'C 869 verso recto', 'C 869 recto', 'C 870 recto', 'C 903 recto', 'C 910 recto', 'C 926 recto', 'C 927 verso recto', 'C 927 recto', 'C 930 verso recto', 'C 930 recto', 'C 939 recto', 'C 949 recto', 'C 951b verso recto', 'C 951b recto', 'C 976 recto', 'C 982 recto', 'C Zonder nummer 001 recto', 'C Zonder nummer 002 verso recto', 'C Zonder nummer 002 recto', 'C Zonder nummer 003 recto', 'C Zonder nummer 004 recto', 'C Zonder nummer 005 verso recto', 'C Zonder nummer 005 recto', 'C Zonder nummer 006 verso recto', 'C Zonder nummer 006 recto', 'CC 021 verso recto', 'CC 021a verso recto', 'CC 021b verso recto', 'CC 042b verso recto', 'CC 055a recto', 'CC 21a recto', 'Claterbos 01 recto', 'Claterbos 02 recto', 'Claterbos 03-1 recto', 'Claterbos 03 recto', 'Claterbos 04 recto', 'Claterbos schrift-01 recto', 'Claterbos schrift-02 recto', 'Claterbos schrift-03 recto', 'Claterbos schrift-04 recto', 'Claterbos schrift-05 recto', 'Claterbos schrift-06 recto', 'Claterbos schrift-07 recto', 'Claterbos schrift-08 recto', 'Claterbos schrift-09 recto', 'Claterbos schrift-10 recto', 'DD 009a recto', 'DeClercq_001 recto', 'DeClercq_002 recto', 'DeClercq_003 recto', 'DeClercq_004 recto', 'DeClercq_005 recto', 'DeClercq_006 recto', 'DeClercq_007 recto', 'DeClercq_008 recto', 'DeClercq_009 recto', 'DeClercq_010 recto', 'DeClercq_011 recto', 'DeClercq_012 recto', 'DeClercq_013 recto', 'DeClercq_014 recto', 'DeClercq_015 recto', 'DeClercq_016 recto', 'DeClercq_017 recto', 'DeClercq_018 recto', 'DeClercq_019 recto', 'DeClercq_020 recto', 'DeClercq_021 recto', 'DeClercq_022 recto', 'DeClercq_023 recto', 'DeClercq_024 recto', 'DeClercq_025 recto', 'DeClercq_026 recto', 'DeClercq_027 recto', 'DeClercq_028 recto', 'DeClercq_029 recto', 'DeClercq_030 recto', 'DeClercq_031 recto', 'DeClercq_032 recto', 'DeClercq_033 recto', 'DeClercq_034 recto', 'DeClercq_035 recto', 'DeClercq_036 recto', 'DeClercq_037 recto', 'DeClercq_038 recto', 'DeClercq_039 recto', 'DeClercq_040 recto', 'DeClercq_041 recto', 'DeClercq_042 recto', 'Democriet _001 recto', 'Democriet _002 recto', 'Democriet _03 recto', 'Democriet_0002 recto', 'Democriet_0003 recto', 'Democriet_0004 recto', 'Democriet_0005 recto', 'Democriet_0006 recto', 'Democriet_0007 recto', 'Democriet_0008 recto', 'Democriet_0009 recto', 'Democriet_0010 recto', 'Democriet_0011 recto', 'Democriet_0012 recto', 'Democriet_0013 recto', 'Democriet_0014 recto', 'Democriet_0015 recto', 'Democriet_0016 recto', 'Democriet_0017 recto', 'Democriet_0018 recto', 'Democriet_0019 recto', 'Democriet_0020 recto', 'Democriet_0021 recto', 'Democriet_0022 recto', 'Democriet_0023 recto', 'Democriet_0024 recto', 'Democriet_1 recto', 'Devises et Inscriptions recto', 'DOOS 12 MAP ZONDER NUMMER recto', 'Dubbel genummerd KG 01299-38 recto', 'Dubbel genummerd KG 18052 recto', 'dubbel genummerd TvB G 2048 recto', 'Dubbel genummerd TvB G 3398 recto', 'dubbel nummer TvB G 2371 recto', 'dubbel nummer TvB G 2394 recto', 'Dubbel nummer TvB G 2636 recto', 'Dubbel nummer TvB G 2694 recto', 'Dubbel nummer TvB G 4028 recto', 'Dubbel nummer TvB G 4048 recto', 'EE 003 recto', 'EE 43a recto', 'Famars Testas recto', 'FF 015 recto', 'FF 021d recto', 'FF 032 recto', 'G 027 recto', 'geen coll recto', 'Geen nummer 27-03-2012 recto', 'Geen nummer TvB G recto', 'GEEN NUMMER- 001 recto', 'GEEN NUMMER-001 recto', 'GEEN NUMMER-002 recto', 'Geen nummer-01 RdW G recto', 'geen nummer recto', 'GEEN NUMMER_001 recto', 'GG 037II recto', 'GG 057 recto', 'GG 065 recto', 'GG 073 II recto', 'H 029r recto', 'H 073 verso recto', 'Hoort bij KG 01301-01302-01 recto', 'Hoort bij KG 01301-01302-02 recto', 'Hoort bij KG 01301-01302-03 recto', 'Hoort bij KG 01301-01302-04 recto', 'Hoort bij KG 01303-01 recto', 'Hoort bij KG 01303-02 recto', 'Hoort bij KG 01303-03 recto', 'Hoort bij KG 01303-04 recto', 'Hoort bij KG 01303-05 recto', 'Hoort bij KG 01303-06 recto', 'Hoort bij KG 01303-07 recto', 'Hoort bij KG 01303-08 recto', 'Hoort bij KG 01303-09 recto', 'Hoort bij KG 01303-10 recto', 'Hoort bij KG 01303-11 recto', 'Hoort bij KG 01303-12 recto', 'Hoort bij KG 01303-13 recto', 'Hoort bij KG 01303-14 recto', 'Hoort bij KG 01303-15 recto', 'Hoort bij KG 01303-16 recto', 'Hoort bij KG 01303-17 recto', 'Hoort bij KG 01303-18 recto', 'Hoort bij KG 01303-19 recto', 'Hoort bij KG 01303-20 recto', 'Hoort bij KG 01303-21 recto', 'Hoort bij KG 01304 recto recto', 'Hoort bij KG 01304 verso recto', 'Hoort bij KG 01305 recto recto', 'Hoort bij KG 01305 verso recto', 'Hoort bij KG 01306 recto recto', 'Hoort bij KG 01306 verso recto', 'HOORT BIJ KG 03159 verso recto', 'HOORT BIJ KG 03159 recto', 'HOORT BIJ KG 03187 recto', 'Hoort bij KG 07306 deel2_002 recto', 'Hoort bij KG 07306 deel2_003 recto', 'Hoort bij KG 07306 deel2_004 recto', 'Hoort bij KG 07306 deel2_005 recto', 'Hoort bij KG 07306 deel2_006 recto', 'Hoort bij KG 07306 deel2_007 recto', 'Hoort bij KG 07306 deel2_008 recto', 'Hoort bij KG 07306 deel2_009 recto', 'Hoort bij KG 07306 deel2_010 recto', 'Hoort bij KG 07306 deel2_011 recto', 'Hoort bij KG 07306 deel2_012 recto', 'Hoort bij KG 07306 deel2_013 recto', 'Hoort bij KG 07306 deel2_014 recto', 'Hoort bij KG 07306 deel2_015 recto', 'Hoort bij KG 07306 deel2_016 recto', 'Hoort bij KG 07306 deel2_017 recto', 'Hoort bij KG 07306 deel2_018 recto', 'Hoort bij KG 07306 deel2_019 recto', 'Hoort bij KG 07306 deel2_020 recto', 'Hoort bij KG 07306 deel2_021 recto', 'Hoort bij KG 07306 deel2_022 recto', 'Hoort bij KG 07306 deel2_023 recto', 'Hoort bij KG 07306 deel2_024 recto', 'Hoort bij KG 07306 deel2_025 recto', 'Hoort bij KG 07306 deel2_026 recto', 'Hoort bij KG 07306 deel2_027 recto', 'Hoort bij KG 07306 deel2_028 recto', 'Hoort bij KG 07306 deel2_029 recto', 'Hoort bij KG 07306 deel2_030 recto', 'Hoort bij KG 07306 deel2_031 recto', 'Hoort bij KG 07306 deel2_032 recto', 'Hoort bij KG 07306 deel2_033 recto', 'Hoort bij KG 07306 deel2_034 recto', 'Hoort bij KG 07306 deel2_035 recto', 'Hoort bij KG 07306 deel2_036 recto', 'Hoort bij KG 07306 deel2_037 recto', 'Hoort bij KG 07306 deel2_038 recto', 'Hoort bij KG 07306 deel2_039 recto', 'Hoort bij KG 07306 deel2_040 recto', 'Hoort bij KG 07306 deel2_041 recto', 'Hoort bij KG 07306 deel2_042 recto', 'Hoort bij KG 07306 deel2_043 recto', 'Hoort bij KG 07306 deel2_044 recto', 'Hoort bij KG 07306 deel2_045 recto', 'Hoort bij KG 07306_001 recto', 'Hoort bij KG 07306_002 recto', 'Hoort bij KG 07306_003 recto', 'Hoort bij KG 07306_004 recto', 'Hoort bij KG 07306_005 recto', 'Hoort bij KG 07306_006 recto', 'Hoort bij KG 07306_007 recto', 'Hoort bij KG 07306_008 recto', 'Hoort bij KG 07306_009 recto', 'Hoort bij KG 07306_010 recto', 'Hoort bij KG 07306_011 recto', 'Hoort bij KG 07306_012 recto', 'Hoort bij KG 07306_013 recto', 'Hoort bij KG 07306_014 recto', 'Hoort bij KG 07306_015 recto', 'Hoort bij KG 07306_016 recto', 'Hoort bij KG 07306_017 recto', 'Hoort bij KG 07306_018 recto', 'Hoort bij KG 07306_019 recto', 'Hoort bij KG 07306_020 recto', 'Hoort bij KG 07306_021 recto', 'Hoort bij KG 07306_022 recto', 'Hoort bij KG 07306_023 recto', 'Hoort bij KG 07306_024 recto', 'Hoort bij KG 07306_025 recto', 'Hoort bij KG 07306_026 recto', 'Hoort bij KG 07306_027 recto', 'Hoort bij KG 07306_028 recto', 'Hoort bij KG 07306_029 recto', 'Hoort bij KG 07306_030 recto', 'Hoort bij KG 07704 recto', 'Hoort bij KG 08249-01 recto', 'Hoort bij KG 08249-02 recto', 'Hoort bij KG 08249-03 recto', 'Hoort bij KG 08249-04 recto', 'Hoort bij KG 08249-05 recto', 'Hoort bij KG 08249-06 recto', 'Hoort bij KG 08249-07 recto', 'Hoort bij KG 08249-08 recto', 'Hoort bij KG 08249-09 recto', 'Hoort bij KG 08249-10 recto', 'Hoort bij KG 08249-11 recto', 'Hoort bij KG 08249-12 recto', 'Hoort bij KG 08250-01 recto', 'Hoort bij KG 08250-02 recto', 'Hoort bij KG 08250-03 recto', 'Hoort bij KG 08250-04 recto', 'Hoort bij KG 08250-05 recto', 'Hoort bij KG 08250-06 recto', 'Hoort bij KG 08250-07 recto', 'Hoort bij KG 08250-08 recto', 'Hoort bij KG 08250-09 recto', 'Hoort bij KG 08250-10 recto', 'Hoort bij KG 08250-11 recto', 'Hoort bij KG 08250-12 recto', 'Hoort bij KG 08375 recto', 'Hoort bij KG 09558-09562-01 recto', 'Hoort bij KG 09558-09562-02 recto', 'Hoort bij KG 09563-09600 recto', 'Hoort bij KG 09604-01 recto', 'Hoort bij KG 09604-02 recto', 'Hoort bij KG 09604-03 recto', 'Hoort bij KG 09604-04 recto', 'Hoort bij KG 09604-05 recto', 'Hoort bij KG 09604-06 recto', 'Hoort bij KG 09604-07 recto', 'Hoort bij KG 09604-08 recto', 'Hoort bij KG 09604-09 recto', 'Hoort bij KG 09604-10 recto', 'Hoort bij KG 09604-11 recto', 'Hoort bij KG 09604-12 recto', 'Hoort bij KG 09604-13 recto', 'Hoort bij KG 09604-14 recto', 'Hoort bij KG 09604-15 recto', 'Hoort bij KG 09604-16 recto', 'Hoort bij KG 09604-17 recto', 'Hoort bij KG 09620-01 recto', 'Hoort bij KG 09620-02 recto', 'Hoort bij KG 09620-03 recto', 'Hoort bij KG 09620-04 recto', 'Hoort bij KG 09620-06 recto', 'Hoort bij KG 09620-07 recto', 'Hoort bij KG 09620-08 recto', 'Hoort bij KG 09620-09 recto', 'Hoort bij KG 09620-10 recto', 'Hoort bij KG 09620-11 recto', 'Hoort bij KG 09620-12 recto', 'Hoort bij KG 09620-13 recto', 'Hoort bij KG 09620-14 recto', 'Hoort bij KG 09620-15 recto', 'Hoort bij KG 09620-16 recto', 'Hoort bij KG 09620-17 recto', 'Hoort bij KG 09620-18 recto', 'Hoort bij KG 09620-19 recto', 'Hoort bij KG 09620-20 recto', 'Hoort bij KG 09620-21 recto', 'Hoort bij KG 09620-22 recto', 'Hoort bij KG 09620-23 recto', 'hoort bij KG 09630 verso recto', 'hoort bij KG 09630 recto', 'Hoort bij KG 14027 recto', 'Hoort bij KG 14028 recto', 'Hoort bij KG 15379 recto', 'Hoort bij KG 15396-16401-01 recto', 'Hoort bij KG 15396-16401-02 recto', 'Hoort bij KG 15396-16401-03 recto', 'Hoort bij KG 15396-16401-04 recto', 'Hoort bij KG 15396-16401-05 recto', 'Hoort bij KG 15396-16401-06 recto', 'Hoort bij KG 15396-16401-07 recto', 'Hoort bij KG 15396-16401-08 recto', 'Hoort bij KG 16006 recto recto', 'Hoort bij KG 16006 verso recto', 'Hoort bij KG 16063 recto recto', 'Hoort bij KG 16063 verso recto', 'Hoort bij KG 16349-16367a 01_1 recto', 'Hoort bij KG 16349-16367a 02 recto', 'Hoort bij KG 16368-16388 01 recto', 'Hoort bij KG 16368-16388 02 recto', 'Hoort bij KG 16389-16395-01 recto', 'Hoort bij KG 16389-16395-02 recto recto', 'Hoort bij KG 16389-16395-02 verso recto', 'Hoort bij KG 16518 recto', 'Hoort bij KG 16519 recto', 'Hoort bij KG 16536 recto recto', 'Hoort bij KG 16536 verso recto', 'Hoort bij KG 16567-16576 recto', 'Hoort bij KG 18269-18270 recto', 'Hoort bij KG 1990 007a-f-01 recto', 'Hoort bij KG 1990 007a-f-02 recto', 'Hoort bij KG 1993 001a-b recto recto', 'Hoort bij KG 1993 001a-b verso recto', 'Hoort bij KG 2011 014 recto', 'Hoort bij KT 02931 recto', 'Hoort bij KT 2010 219 recto', 'hoort bij P 08a recto', 'Hoort bij PP 00179 recto', 'Hoort bij PP 00207 recto', 'Hoort bij PP 00577 recto', 'Hoort bij PP 00874 recto', 'Hoort bij PP 00892 recto', 'Hoort bij PP 1314 recto', 'Hoort bij TdM C 0074 recto', 'hoort bij TvB G 0135 recto', 'hoort bij TvB G 0622 recto', 'hoort bij TvB G 1083 recto', 'hoort bij TvB G 1325 recto', 'hoort bij TvB G 1992 recto', 'hoort bij TvB G 2062 recto', 'hoort bij TvB G 2207 recto', 'Hoort bij TvB G 2306 recto', 'Hoort bij TvB G 2615 recto', 'Hoort bij V 009c recto', 'Hoort bij verso KG 2011 014 recto', 'Hoort bij W 040b recto', 'Hoort bij-01 KG 08188-08192 recto', 'Hoort bij-01 KG 08900-08911 recto', 'Hoort bij-02 KG 08188-08192 recto', 'Hoort bij-02 KG 08900-08911 recto', 'Hoort bijTvB G 3578 recto', 'I K V 020 recto', 'J 037 recto', 'K  I 006 recto', 'K 087a recto', 'K I  063 recto', 'K I 039V recto', 'K I 047 a-b recto', 'K I 053 verso recto', 'K I 053_150% recto', 'K II 008 recto', 'K II 0107 recto', 'K II 057r recto', 'K II 057v recto', 'K II 072 recto', 'K II 090b recto', 'K II 098c recto', 'K II 098d recto', 'K III 038  verso recto', 'K IV 005-2 recto', 'K IV 051 recto', 'K IV 119 recto', 'K IV 128 recto', 'K V 0119 recto', 'K V 078 recto', 'K VI 110 recto', 'K VII 022 recto', 'K VIII 006 recto', 'K VIII 007 recto', 'K VIII 111 recto', 'K XX 058 recto', 'K XX 096 recto', 'KB 01 recto', 'KB 04 recto', 'KB 13 recto', 'KB 16 recto', 'KB 18 recto', 'KG 00250-01 recto', 'KG 00250-02 recto', 'KG 00379 recto', 'KG 00418 recto', 'KG 00430a recto', 'KG 00432 recto', 'KG 00683-00712 recto', 'KG 00754 EV recto', 'KG 00803 EV recto', 'KG 00833a recto', 'KG 00833b recto', 'KG 00858 EV recto', 'KG 00869 recto', 'KG 01034_001 recto', 'KG 01034_002 recto', 'KG 01034_003 recto', 'KG 01034_004 recto', 'KG 01034_005 recto', 'KG 01034_006 recto', 'KG 01034_007 recto', 'KG 01034_008 recto', 'KG 01034_009 recto', 'KG 01034_010 recto', 'KG 01034_011 recto', 'KG 01034_012 recto', 'KG 01034_013 recto', 'KG 01034_014 recto', 'KG 01034_015 recto', 'KG 01034_016 recto', 'KG 01034_017 recto', 'KG 01034_018 recto', 'KG 01034_019 recto', 'KG 01034_020 recto', 'KG 01034_021 recto', 'KG 01034_022 recto', 'KG 01034_023 recto', 'KG 01034_024 recto', 'KG 01034_025 recto', 'KG 01034_026 recto', 'KG 01034_027 recto', 'KG 01034_028 recto', 'KG 01034_029 recto', 'KG 01034_030 recto', 'KG 01034_031 recto', 'KG 01034_032 recto', 'KG 01034_033 recto', 'KG 01034_034 recto', 'KG 01034_035 recto', 'KG 01034_036 recto', 'KG 01034_037 recto', 'KG 01034_038 recto', 'KG 01034_039 recto', 'KG 01034_040 recto', 'KG 01034_041 recto', 'KG 01034_042 recto', 'KG 01034_043 recto', 'KG 01035 001 recto', 'KG 01035 002 recto', 'KG 01035 003 recto', 'KG 01035 004 recto', 'KG 01035 005 recto', 'KG 01035 006 recto', 'KG 01035 007 recto', 'KG 01035 008 recto', 'KG 01035 009 recto', 'KG 01035 010 recto', 'KG 01035 011 recto', 'KG 01035 012 recto', 'KG 01035 013 recto', 'KG 01035 014 recto', 'KG 01035 015 recto', 'KG 01035 016 recto', 'KG 01035 017 recto', 'KG 01035 018 recto', 'KG 01035 019 recto', 'KG 01035 020 recto', 'KG 01035 021 recto', 'KG 01035 022 recto', 'KG 01035 023 recto', 'KG 01035 024 recto', 'KG 01035 025 recto', 'KG 01035 026 recto', 'KG 01035 027 recto', 'KG 01035 028 recto', 'KG 01035 029 recto', 'KG 01035 030 recto', 'KG 01035 031 recto', 'KG 01035 032 recto', 'KG 01035 033 recto', 'KG 01035 034 recto', 'KG 01035 035 recto', 'KG 01035 036 recto', 'KG 01036 001 recto', 'KG 01036 002 recto', 'KG 01036 003 recto', 'KG 01036 004 recto', 'KG 01036 005 recto', 'KG 01036 006 recto', 'KG 01036 007 recto', 'KG 01036 008 recto', 'KG 01036 009 recto', 'KG 01036 010 recto', 'KG 01036 011 recto', 'KG 01036 012 recto', 'KG 01036 013 recto', 'KG 01036 014 recto', 'KG 01036 015 recto', 'KG 01036 016 recto', 'KG 01060 021 recto', 'KG 01060 022 recto', 'KG 01060 023 recto', 'KG 01060 024 recto', 'KG 01060 025 recto', 'KG 01060-01 recto', 'KG 01060-02 recto', 'KG 01060-03 recto', 'KG 01060-04 recto', 'KG 01060-05 recto', 'KG 01060-06 recto', 'KG 01060-07 recto', 'KG 01060-08 recto', 'KG 01060-09 recto', 'KG 01060-10 recto', 'KG 01060-11 recto', 'KG 01060-12 recto', 'KG 01060-13 recto', 'KG 01060-14 recto', 'KG 01060-15 recto', 'KG 01060-16 recto', 'KG 01060-17 recto', 'KG 01060-18 recto', 'KG 01060-19 recto', 'KG 01061_001 recto', 'KG 01061_002 recto', 'KG 01061_003 recto', 'KG 01061_004 recto', 'KG 01061_005 recto', 'KG 01061_006 recto', 'KG 01061_007 recto', 'KG 01061_008 recto', 'KG 01061_009 recto', 'KG 01061_010 recto', 'KG 01061_011 recto', 'KG 01061_012 recto', 'KG 01061_013 recto', 'KG 01061_014 recto', 'KG 01061_015 recto', 'KG 01061_016 recto', 'KG 01061_017 recto', 'KG 01061_018 recto', 'KG 01061_019 recto', 'KG 01061_020 recto', 'KG 01061_021 recto', 'KG 01061_022 recto', 'KG 01061_023 recto', 'KG 01061_024 recto', 'KG 01061_025 recto', 'KG 01061_026 recto', 'KG 01061_027 recto', 'KG 01062 0 verso recto', 'KG 01062 0 recto', 'KG 01062 00 verso recto', 'KG 01062 00 recto', 'KG 01062 001 recto', 'KG 01062 002 recto', 'KG 01062 003 recto', 'KG 01062 004 recto', 'KG 01062 005 recto', 'KG 01062 006 recto', 'KG 01062 007 recto', 'KG 01062 008 recto', 'KG 01062 009 recto', 'KG 01062 010 recto', 'KG 01062 011 recto', 'KG 01062 012 recto', 'KG 01062 013 recto', 'KG 01062 014 recto', 'KG 01062 015 recto', 'KG 01062 016 recto', 'KG 01062 017 recto', 'KG 01062 018 recto', 'KG 01062 019 recto', 'KG 01062 020 recto', 'KG 01062 021 recto', 'KG 01062 022 recto', 'KG 01062 023 recto', 'KG 01063 000 recto', 'KG 01063 001 recto', 'KG 01063 002 recto', 'KG 01063 003 recto', 'KG 01063 004 recto', 'KG 01063 005 recto', 'KG 01063 006 recto', 'KG 01063 007 recto', 'KG 01063 008 recto', 'KG 01063 401 recto', 'KG 01064 000 recto', 'KG 01064 001 recto', 'KG 01064 002 recto', 'KG 01064 003 recto', 'KG 01064 004 recto', 'KG 01064 005 recto', 'KG 01064 006 recto', 'KG 01064 007 recto', 'KG 01064 008 recto', 'KG 01064 009 recto', 'KG 01064 010 recto', 'KG 01064 011 recto', 'KG 01064 012 recto', 'KG 01064 013 recto', 'KG 01064 014 recto', 'KG 01064 015 recto', 'KG 01064 016 recto', 'KG 01064 017 recto', 'KG 01064 018 recto', 'KG 01064 019 recto', 'KG 01064 020 recto', 'KG 01064 021 recto', 'KG 01064 022 recto', 'KG 01064 023 recto', 'KG 01064 024 recto', 'KG 01064 025 recto', 'KG 01064 026 recto', 'KG 01064 027 recto', 'KG 01064 028 recto', 'KG 01064 029 recto', 'KG 01064 030 recto', 'KG 01064 031 recto', 'KG 01064 032 recto', 'KG 01064 033 recto', 'KG 01064 034 recto', 'KG 01064 035 recto', 'KG 01064 036 recto', 'KG 01064 037 recto', 'KG 01064 038 recto', 'KG 01064 039 recto', 'KG 01064 040 recto', 'KG 01067 001 recto', 'KG 01067 002 recto', 'KG 01067 003 recto', 'KG 01067 004 recto', 'KG 01068 000 recto', 'KG 01068 001 recto', 'KG 01068 002 recto', 'KG 01068 003 recto', 'KG 01068 004 recto', 'KG 01068 005 recto', 'KG 01068 006 recto', 'KG 01068 007 recto', 'KG 01068 008 recto', 'KG 01068 009 recto', 'KG 01068 010 recto', 'KG 01068 011 recto', 'KG 01068 012 recto', 'KG 01068 013 recto', 'KG 01068 014 recto', 'KG 01068 015 recto', 'KG 01068 016 recto', 'KG 01068 017 recto', 'KG 01068 018 recto', 'KG 01068 019 recto', 'KG 01068 020 recto', 'KG 01068 021 recto', 'KG 01068 022 recto', 'KG 01068 023 recto', 'KG 01068 024 recto', 'KG 01068 025 recto', 'KG 01068 026 recto', 'KG 01068 027 recto', 'KG 01068 028 recto', 'KG 01068 029 recto', 'KG 01068 030 recto', 'KG 01068 031 recto', 'KG 01068 032 recto', 'KG 01068 033 recto', 'KG 01068 034 recto', 'KG 01068 035 recto', 'KG 01068 036 recto', 'KG 01068 037 recto', 'KG 01068 038 recto', 'KG 01068 039 recto', 'KG 01068 040 recto', 'KG 01068 041 recto', 'KG 01068 042 recto', 'KG 01068 043 recto', 'KG 01068 044 recto', 'KG 01068 045 recto', 'KG 01068 046 recto', 'KG 01068 047 recto', 'KG 01068 048 recto', 'KG 01068 049 recto', 'KG 01068 050 recto', 'KG 01068 051 recto', 'KG 01068 052 recto', 'KG 01068 053 recto', 'KG 01068 054 recto', 'KG 01068 055 recto', 'KG 01068 056 recto', 'KG 01068 057 recto', 'KG 01068 058 recto', 'KG 01068 059 recto', 'KG 01068 060 recto', 'KG 01068 061 recto', 'KG 01068 062 recto', 'KG 01068 063 recto', 'KG 01068 064 recto', 'KG 01068 065 recto', 'KG 01068 066 recto', 'KG 01068 067 recto', 'KG 01068 068 recto', 'KG 01068 069 recto', 'KG 01068 070 recto', 'KG 01068 071 recto', 'KG 01068 072 recto', 'KG 01068 073 recto', 'KG 01068 074 recto', 'KG 01068 075 recto', 'KG 01068 076 recto', 'KG 01068 077 recto', 'KG 01068 078 recto', 'KG 01068 079 recto', 'KG 01068 080 recto', 'KG 01068 081 recto', 'KG 01068 082 recto', 'KG 01068 083 recto', 'KG 01068 084 recto', 'KG 01068 085 recto', 'KG 01068 086 recto', 'KG 01068 087 recto', 'KG 01068 088 recto', 'KG 01068 089 recto', 'KG 01068 090 recto', 'KG 01068 091 recto', 'KG 01068 092 recto', 'KG 01068 093 recto', 'KG 01068 094 recto', 'KG 01068 095 recto', 'KG 01068 096 recto', 'KG 01068 097 recto', 'KG 01068 098 recto', 'KG 01068 099 recto', 'KG 01068 100 recto', 'KG 01073 recto recto', 'KG 01073 verso recto', 'KG 01073-01 recto', 'KG 01073-02 recto', 'KG 01073-03 recto', 'KG 01073-04 recto', 'KG 01073-05 recto', 'KG 01073-06 recto', 'KG 01073-07 recto', 'KG 01073-08 recto', 'KG 01073-09 recto', 'KG 01073-10 recto', 'KG 01073-11 recto', 'KG 01073-12 recto', 'KG 01073-13 recto', 'KG 01073-14 recto', 'KG 01073-15 recto', 'KG 01073-16 recto', 'KG 01073-17 recto', 'KG 01073-18 recto', 'KG 01074 recto recto', 'KG 01074 verso recto', 'KG 01074-01 recto', 'KG 01074-02 recto', 'KG 01074-03 recto', 'KG 01074-04 recto', 'KG 01074-05 recto', 'KG 01074-06 recto', 'KG 01074-07 recto', 'KG 01074-08 recto', 'KG 01074-09 recto', 'KG 01074-10 recto', 'KG 01074-11 recto', 'KG 01074-12 recto', 'KG 01074-13 recto', 'KG 01074-14 recto', 'KG 01074-15 recto', 'KG 01074-16 recto', 'KG 01074-17 recto', 'KG 01074-18 recto', 'KG 01074-19 recto', 'KG 01074-20 recto', 'KG 01075 recto recto', 'KG 01075 verso recto', 'KG 01075-01 recto', 'KG 01075-02 recto', 'KG 01075-03 recto', 'KG 01075-04 recto', 'KG 01075-05 recto', 'KG 01075-06 recto', 'KG 01075-07 recto', 'KG 01075-08 recto', 'KG 01075-09 recto', 'KG 01075-10 recto', 'KG 01075-11 recto', 'KG 01075-12 recto', 'KG 01075-13 recto', 'KG 01075-14 recto', 'KG 01075-15 recto', 'KG 01075-16 recto', 'KG 01075-17 recto', 'KG 01075-18 recto', 'KG 01076 recto recto', 'KG 01076 verso recto', 'KG 01076-01 recto', 'KG 01076-02 recto', 'KG 01076-03 recto', 'KG 01076-04 recto', 'KG 01076-05 recto', 'KG 01076-06 recto', 'KG 01076-07 recto', 'KG 01076-08 recto', 'KG 01076-09 recto', 'KG 01076-10 recto', 'KG 01076-11 recto', 'KG 01076-12 recto', 'KG 01076-13 recto', 'KG 01076-14 recto', 'KG 01076-15 recto', 'KG 01076-16 recto', 'KG 01077 recto recto', 'KG 01077 verso recto', 'KG 01077-01 recto', 'KG 01077-02 recto', 'KG 01077-03 recto', 'KG 01077-04 recto', 'KG 01077-05 recto', 'KG 01077-06 recto', 'KG 01077-07 recto', 'KG 01077-08 recto', 'KG 01077-09 recto', 'KG 01077-10 recto', 'KG 01077-11 recto', 'KG 01077-12 recto', 'KG 01077-13 recto', 'KG 01077-14 recto', 'KG 01077-15 recto', 'KG 01077-16 recto', 'KG 01077-17 recto', 'KG 01077-18 recto', 'KG 01078 recto recto', 'KG 01078 verso recto', 'KG 01078-01 recto', 'KG 01078-02 recto', 'KG 01078-03 recto', 'KG 01078-04 recto', 'KG 01078-05 recto', 'KG 01078-06 recto', 'KG 01078-07 recto', 'KG 01078-08 recto', 'KG 01078-09 recto', 'KG 01078-10 recto', 'KG 01078-11 recto', 'KG 01078-12 recto', 'KG 01078-13 recto', 'KG 01078-14 recto', 'KG 01078-15 recto', 'KG 01078-16 recto', 'KG 01078-17 recto', 'KG 01078-18 recto', 'KG 01079 recto recto', 'KG 01079 verso recto', 'KG 01079-01 recto', 'KG 01079-02 recto', 'KG 01079-03 recto', 'KG 01079-04 recto', 'KG 01079-05 recto', 'KG 01079-06 recto', 'KG 01079-07 recto', 'KG 01079-08 recto', 'KG 01079-09 recto', 'KG 01079-10 recto', 'KG 01079-11 recto', 'KG 01079-12 recto', 'KG 01079-13 recto', 'KG 01079-14 recto', 'KG 01079-15 recto', 'KG 01079-16 recto', 'KG 01079-17 recto', 'KG 01079-18 recto', 'KG 01079-19 recto', 'KG 01079-20 recto', 'KG 01080 001 recto', 'KG 01080 002 recto', 'KG 01080 003 recto', 'KG 01080 004 recto', 'KG 01080 005 recto', 'KG 01081 001 recto', 'KG 01081 002 recto', 'KG 01081 003 recto', 'KG 01081 004 recto', 'KG 01082 001 recto', 'KG 01082 002 recto', 'KG 01082 003 recto', 'KG 01082 004 recto', 'KG 01082 005 recto', 'KG 01082 006 recto', 'KG 01082 007 recto', 'KG 01082 008 recto', 'KG 01083 001 recto', 'KG 01083 002 recto', 'KG 01083 003 recto', 'KG 01083 004 recto', 'KG 01084 001 recto', 'KG 01084 002 recto', 'KG 01084 003 recto', 'KG 01084 004 recto', 'KG 01084 005 recto', 'KG 01084 006 recto', 'KG 01084 007 recto', 'KG 01084 008 recto', 'KG 01084 009 recto', 'KG 01084 010 recto', 'KG 01085 001 recto', 'KG 01085 002 recto', 'KG 01085 003 recto', 'KG 01085 004 recto', 'KG 01085 005 recto', 'KG 01086 001 recto', 'KG 01086 002 recto', 'KG 01086 003 recto', 'KG 01086 004 recto', 'KG 01086 005 recto', 'KG 01086 006 recto', 'KG 01086 007 recto', 'KG 01086 008 recto', 'KG 01086 009 recto', 'KG 01086 010 recto', 'KG 01086 011 recto', 'KG 01086 012 recto', 'KG 01086 013 recto', 'KG 01086 014 recto', 'KG 01086 015 recto', 'KG 01086 016 recto', 'KG 01086 017 recto', 'KG 01086 018 recto', 'KG 01086 019 recto', 'KG 01086 020 recto', 'KG 01086 021 recto', 'KG 01086 022 recto', 'KG 01086 023 recto', 'KG 01086 024 recto', 'KG 01086 025 recto', 'KG 01086 026 recto', 'KG 01086 027 recto', 'KG 01086 028 recto', 'KG 01086 029 recto', 'KG 01086 030 recto', 'KG 01086 031 recto', 'KG 01086 032 recto', 'KG 01087 000 verso recto', 'KG 01087 000 recto', 'KG 01087 001 recto', 'KG 01087 002 recto', 'KG 01087 003 recto', 'KG 01087 004 recto', 'KG 01089 001 recto', 'KG 01089 002 recto', 'KG 01089 003 recto', 'KG 01089 004 recto', 'KG 01089 005 recto', 'KG 01089 006 recto', 'KG 01089 007 recto', 'KG 01089 008 recto', 'KG 01089 009 recto', 'KG 01089 010 recto', 'KG 01089 011 recto', 'KG 01089 012 recto', 'KG 01089 013 recto', 'KG 01089 014 recto', 'KG 01089 015 recto', 'KG 01089 016 recto', 'KG 01089 017 recto', 'KG 01089 018 recto', 'KG 01101 001 recto', 'KG 01101 002 recto', 'KG 01101 003 recto', 'KG 01101 004 recto', 'KG 01101 005 recto', 'KG 01101 006 recto', 'KG 01101 007 recto', 'KG 01101 008 recto', 'KG 01101 009 recto', 'KG 01101 010 recto', 'KG 01101 011 recto', 'KG 01101 012 recto', 'KG 01101 013 recto', 'KG 01101 014 recto', 'KG 01102 001 recto', 'KG 01102 002 recto', 'KG 01102 003 recto', 'KG 01102 004 recto', 'KG 01102 005 recto', 'KG 01102 006 recto', 'KG 01102 007 recto', 'KG 01102 008 recto', 'KG 01102 009 recto', 'KG 01102 010 recto', 'KG 01102 011 recto', 'KG 01103 001 recto', 'KG 01103 002 recto', 'KG 01103 003 recto', 'KG 01103 004 recto', 'KG 01103 005 recto', 'KG 01103 006 recto', 'KG 01103 007 recto', 'KG 01103 008 recto', 'KG 01103 009 recto', 'KG 01103 010 recto', 'KG 01103 011 recto', 'KG 01104 001 recto', 'KG 01104 002 recto', 'KG 01104 003 recto', 'KG 01104 004 recto', 'KG 01105 001 recto', 'KG 01105 002 recto', 'KG 01105 003 recto', 'KG 01105 004 recto', 'KG 01106-13 recto', 'KG 01106-14 recto', 'KG 01106-15 recto', 'KG 01106-16 recto', 'KG 01106-17 recto', 'KG 01106-18 recto', 'KG 01106-19 recto', 'KG 01106-20 recto', 'KG 01106-21 recto', 'KG 01106-22 recto', 'KG 01106-23 recto', 'KG 01106-24 recto', 'KG 01106-25 recto', 'KG 01106-26 recto', 'KG 01106-27 recto', 'KG 01106-28 recto', 'KG 01106-29 recto', 'KG 01106-30 recto', 'KG 01109 001 recto', 'KG 01109 002 recto', 'KG 01109 003 recto', 'KG 01109 004 recto', 'KG 01109 005 recto', 'KG 01109-006 recto', 'KG 01110-001 recto', 'KG 01110-002 recto', 'KG 01110-003 recto', 'KG 01110-004 recto', 'KG 01110-005 recto', 'KG 01110-006 recto', 'KG 01111-001 recto', 'KG 01111-002 recto', 'KG 01111-003 recto', 'KG 01111-004 recto', 'KG 01111-005 recto', 'KG 01111-006 recto', 'KG 01111-007 recto', 'KG 01111-008 recto', 'KG 01111-009 recto', 'KG 01111-010 recto', 'KG 01111-011 recto', 'KG 01111-012 recto', 'KG 01112-001 recto', 'KG 01112-002 recto', 'KG 01112-003 recto', 'KG 01112-004 recto', 'KG 01112-005 recto', 'KG 01112-006 recto', 'KG 01112-007 recto', 'KG 01112-008 recto', 'KG 01112-009 recto', 'KG 01112-010 recto', 'KG 01112-011 recto', 'KG 01112-012 recto', 'KG 01112-013 recto', 'KG 01112-014 recto', 'KG 01112-015 recto', 'KG 01112-016 recto', 'KG 01113-001 recto', 'KG 01113-002 recto', 'KG 01113-003 recto', 'KG 01113-004 recto', 'KG 01113-005 recto', 'KG 01113-006 recto', 'KG 01113-007 recto', 'KG 01113-008 recto', 'KG 01115-001 recto', 'KG 01115-002 recto', 'KG 01115-003 recto', 'KG 01115-004 recto', 'KG 01115-005 recto', 'KG 01115-006 recto', 'KG 01115-007 recto', 'KG 01116-001 recto', 'KG 01116-002 recto', 'KG 01116-003 recto', 'KG 01116-004 recto', 'KG 01116-005 recto', 'KG 01116-006 recto', 'KG 01116-007 recto', 'KG 01116-008 recto', 'KG 01136_001 recto', 'KG 01136_002 recto', 'KG 01136_003 recto', 'KG 01136_004 recto', 'KG 01136_005 recto', 'KG 01136_006 recto', 'KG 01136_007 recto', 'KG 01136_008 recto', 'KG 01136_009 recto', 'KG 01136_010 recto', 'KG 01136_011 recto', 'KG 01136_012 recto', 'KG 01136_013 recto', 'KG 01136_014 recto', 'KG 01136_015 recto', 'KG 01136_016 recto', 'KG 01136_017 recto', 'KG 01136_018 recto', 'KG 01136_019 recto', 'KG 01136_020 recto', 'KG 01136_021 recto', 'KG 01136_022 recto', 'KG 01136_023 recto', 'KG 01136_024 recto', 'KG 01136_025 recto', 'KG 01136_026 recto', 'KG 01136_027 recto', 'KG 01136_028 recto', 'KG 01136_029 recto', 'KG 01136_030 recto', 'KG 01136_031 recto', 'KG 01136_032 recto', 'KG 01136_033 recto', 'KG 01136_034 recto', 'KG 01136_035 recto', 'KG 01136_036 recto', 'KG 01136_037 recto', 'KG 01136_038 recto', 'KG 01136_039 recto', 'KG 01136_040 recto', 'KG 01136_041 recto', 'KG 01136_042 recto', 'KG 01136_043 recto', 'KG 01136_044 recto', 'KG 01136_045 recto', 'KG 01136_046 recto', 'KG 01136_047 recto', 'KG 01136_048 recto', 'KG 01136_049 recto', 'KG 01136_050 recto', 'KG 01136_051 recto', 'KG 01136_052 recto', 'KG 01136_053 recto', 'KG 01136_054 recto', 'KG 01136_055 recto', 'KG 01136_056 recto', 'KG 01136_057 recto', 'KG 01136_058 recto', 'KG 01136_059 recto', 'KG 01136_060 recto', 'KG 01136_061 recto', 'KG 01136_062 recto', 'KG 01136_063 recto', 'KG 01136_064 recto', 'KG 01136_065 recto', 'KG 01136_066 recto', 'KG 01136_067 recto', 'KG 01136_068 recto', 'KG 01136_069 recto', 'KG 01136_070 recto', 'KG 01136_071 recto', 'KG 01136_072 recto', 'KG 01136_073 recto', 'KG 01136_074 recto', 'KG 01136_075 recto', 'KG 01136_076 recto', 'KG 01136_077 recto', 'KG 01136_078 recto', 'KG 01136_079 recto', 'KG 01136_080 recto', 'KG 01136_081 recto', 'KG 01136_082 recto', 'KG 01136_083 recto', 'KG 01136_084 recto', 'KG 01136_085 recto', 'KG 01136_086 recto', 'KG 01136_087 recto', 'KG 01136_088 recto', 'KG 01136_089 recto', 'KG 01136_090 recto', 'KG 01136_091 recto', 'KG 01136_092 recto', 'KG 01136_093 recto', 'KG 01136_094 recto', 'KG 01137_001 recto', 'KG 01137_002 recto', 'KG 01137_003 recto', 'KG 01137_004 recto', 'KG 01137_005 recto', 'KG 01137_006 recto', 'KG 01137_007 recto', 'KG 01137_008 recto', 'KG 01137_009 recto', 'KG 01137_010 recto', 'KG 01137_011 recto', 'KG 01137_012 recto', 'KG 01137_013 recto', 'KG 01137_014 recto', 'KG 01137_015 recto', 'KG 01137_016 recto', 'KG 01137_017 recto', 'KG 01137_018 recto', 'KG 01137_019 recto', 'KG 01137_020 recto', 'KG 01137_021 recto', 'KG 01137_022 recto', 'KG 01137_023 recto', 'KG 01137_024 recto', 'KG 01137_025 recto', 'KG 01137_026 recto', 'KG 01137_027 recto', 'KG 01137_028 recto', 'KG 01137_029 recto', 'KG 01137_030 recto', 'KG 01137_031 recto', 'KG 01137_032 recto', 'KG 01137_033 recto', 'KG 01137_034 recto', 'KG 01137_035 recto', 'KG 01137_036 recto', 'KG 01137_037 recto', 'KG 01137_038 recto', 'KG 01137_039 recto', 'KG 01137_040 recto', 'KG 01137_041 recto', 'KG 01137_042 recto', 'KG 01137_043 recto', 'KG 01137_044 recto', 'KG 01137_045 recto', 'KG 01137_046 recto', 'KG 01137_047 recto', 'KG 01137_048 recto', 'KG 01137_049 recto', 'KG 01137_050 recto', 'KG 01137_051 recto', 'KG 01137_052 recto', 'KG 01137_053 recto', 'KG 01137_054 recto', 'KG 01137_055 recto', 'KG 01137_056 recto', 'KG 01137_057 recto', 'KG 01137_058 recto', 'KG 01137_059 recto', 'KG 01137_060 recto', 'KG 01137_061 recto', 'KG 01137_062 recto', 'KG 01137_063 recto', 'KG 01137_064 recto', 'KG 01137_065 recto', 'KG 01137_066 recto', 'KG 01137_067 recto', 'KG 01137_068 recto', 'KG 01137_069 recto', 'KG 01137_070 recto', 'KG 01137_071 recto', 'KG 01137_072 recto', 'KG 01137_073 recto', 'KG 01137_074 recto', 'KG 01137_075 recto', 'KG 01137_076 recto', 'KG 01137_077 recto', 'KG 01137_078 recto', 'KG 01137_079 recto', 'KG 01137_080 recto', 'KG 01137_081 recto', 'KG 01137_082 recto', 'KG 01137_083 recto', 'KG 01137_084 recto', 'KG 01137_085 recto', 'KG 01137_086 recto', 'KG 01137_087 recto', 'KG 01137_088 recto', 'KG 01137_089 recto', 'KG 01137_090 recto', 'KG 01137_091 recto', 'KG 01137_092 recto', 'KG 01137_093 recto', 'KG 01143-01 recto', 'KG 01144-001 recto', 'KG 01144-002 recto', 'KG 01144-02 recto', 'KG 01144-03 recto', 'KG 01144-04 recto', 'KG 01144-05 recto', 'KG 01148 verso recto', 'KG 01148-001 recto', 'KG 01148-002 recto', 'KG 01148-003 recto', 'KG 01148-004 recto', 'KG 01148-005 recto', 'KG 01148-006 recto', 'KG 01228 dubbel recto', 'KG 01242-01 recto', 'KG 01242-02 recto', 'KG 01242-03 recto', 'KG 01242-04 recto', 'KG 01242-05 recto', 'KG 01242-06 recto', 'KG 01242-07 recto', 'KG 01242-08 recto', 'KG 01242-09 recto', 'KG 01242-10 recto', 'KG 01242-11 recto', 'KG 01242-12 recto', 'KG 01242-13 recto', 'KG 01242-14 recto', 'KG 01242-15 recto', 'KG 01242-16 recto', 'KG 01242-17 recto', 'KG 01242-18 recto', 'KG 01242-19 recto', 'KG 01242-20 recto', 'KG 01242-21 recto', 'KG 01242-22 recto', 'KG 01242-23 recto', 'KG 01242-24 recto', 'KG 01242-25 recto', 'KG 01242-26 recto', 'KG 01242-27 recto', 'KG 01242-28 recto', 'KG 01242-29 recto', 'KG 01242-30 recto', 'KG 01242-31 recto', 'KG 01242-32 recto', 'KG 01265 recto', 'KG 01295-001 recto', 'KG 01295-002 recto', 'KG 01295-003 recto', 'KG 01295-004 recto', 'KG 01295-005 recto', 'KG 01295-006 recto', 'KG 01296-01 recto', 'KG 01296-02 recto', 'KG 01296-03 recto', 'KG 01296-04 recto', 'KG 01296-05 recto', 'KG 01296-06 recto', 'KG 01296-07 recto', 'KG 01296-08 recto', 'KG 01296-09 recto', 'KG 01296-10 recto', 'KG 01296-11 recto', 'KG 01296-12 recto', 'KG 01296-13 recto', 'KG 01296-14 recto', 'KG 01296-15 recto', 'KG 01296-16 recto', 'KG 01296-17 recto', 'KG 01296-18 recto', 'KG 01296-19 recto', 'KG 01296-20 recto', 'KG 01296-21 recto', 'KG 01296-22 recto', 'KG 01296-23 recto', 'KG 01296-24 recto', 'KG 01296-25 recto', 'KG 01296-26 recto', 'KG 01296-27 recto', 'KG 01296-28 recto', 'KG 01296-29 recto', 'KG 01296-30 recto', 'KG 01296-31 recto', 'KG 01296-32 recto', 'KG 01296-33 recto', 'KG 01296-34 recto', 'KG 01296-35 recto', 'KG 01297-01 recto', 'KG 01297-02 recto', 'KG 01297-03 recto', 'KG 01297-04 recto', 'KG 01297-05 recto', 'KG 01297-06 recto', 'KG 01297-07 recto', 'KG 01297-08 recto', 'KG 01297-09 recto', 'KG 01297-10 recto', 'KG 01297-11 recto', 'KG 01297-12 recto', 'KG 01297-13 recto', 'KG 01297-14 recto', 'KG 01297-15 recto', 'KG 01297-16 recto', 'KG 01297-17 recto', 'KG 01297-18 recto', 'KG 01297-19 recto', 'KG 01297-20 recto', 'KG 01297-21 recto', 'KG 01297-22 recto', 'KG 01297-23 recto', 'KG 01297-24 recto', 'KG 01297-25 recto', 'KG 01297-26 recto', 'KG 01297-27 recto', 'KG 01297-28 recto', 'KG 01297-29 recto', 'KG 01297-30 recto', 'KG 01297-31 recto', 'KG 01297-32 recto', 'KG 01297-33 recto', 'KG 01297-34 recto', 'KG 01297-35 recto', 'KG 01297-36 recto', 'KG 01297-37 recto', 'KG 01297-xx recto', 'KG 01298-01 recto', 'KG 01298-02 recto', 'KG 01298-03 recto', 'KG 01298-04 recto', 'KG 01298-05 recto', 'KG 01298-06 recto', 'KG 01298-07 recto', 'KG 01298-08 recto', 'KG 01298-09 recto', 'KG 01298-10 recto', 'KG 01298-11 recto', 'KG 01298-12 recto', 'KG 01298-13 recto', 'KG 01298-14 recto', 'KG 01298-15 recto', 'KG 01298-16 recto', 'KG 01298-17 recto', 'KG 01298-18 recto', 'KG 01298-19 recto', 'KG 01298-20 recto', 'KG 01298-21 recto', 'KG 01298-22 recto', 'KG 01298-23 recto', 'KG 01298-24 recto', 'KG 01298-25 recto', 'KG 01298-26 recto', 'KG 01298-27 recto', 'KG 01298-28 recto', 'KG 01298-29 recto', 'KG 01298-30 recto', 'KG 01298-31 recto', 'KG 01298-32 recto', 'KG 01298-33 recto', 'KG 01298-34 recto', 'KG 01298-35 recto', 'KG 01298-36 recto', 'KG 01298-xx recto', 'KG 01299-01 recto', 'KG 01299-02 recto', 'KG 01299-03 recto', 'KG 01299-04 recto', 'KG 01299-06 recto', 'KG 01299-07 recto', 'KG 01299-08 recto', 'KG 01299-09 recto', 'KG 01299-10 recto', 'KG 01299-11 recto', 'KG 01299-12 recto', 'KG 01299-13 recto', 'KG 01299-14 recto', 'KG 01299-15 recto', 'KG 01299-16 recto', 'KG 01299-17 recto', 'KG 01299-18 recto', 'KG 01299-19 recto', 'KG 01299-20 recto', 'KG 01299-21 recto', 'KG 01299-22 recto', 'KG 01299-23 recto', 'KG 01299-24 recto', 'KG 01299-25 recto', 'KG 01299-26 recto', 'KG 01299-27 recto', 'KG 01299-28 recto', 'KG 01299-29 recto', 'KG 01299-30 recto', 'KG 01299-31 recto', 'KG 01299-32 recto', 'KG 01299-33 recto', 'KG 01299-34 recto', 'KG 01299-35 recto', 'KG 01299-36 recto', 'KG 01299-37 recto', 'KG 01299-38 recto', 'KG 01299-39 recto', 'KG 01299-40 recto', 'KG 01299-41 recto', 'KG 01299-42 recto', 'KG 01304-01 recto', 'KG 01304-02 recto', 'KG 01304-03 recto', 'KG 01304-04 recto', 'KG 01304-05 recto', 'KG 01304-06 recto', 'KG 01304-07 recto', 'KG 01304-08 recto', 'KG 01304-09 recto', 'KG 01304-10 recto', 'KG 01304-11 recto', 'KG 01304-12 recto', 'KG 01304-13 recto', 'KG 01305-01 recto', 'KG 01305-02 recto', 'KG 01305-03 recto', 'KG 01305-04 recto', 'KG 01305-05 recto', 'KG 01305-06 recto', 'KG 01305-07 recto', 'KG 01305-08 recto', 'KG 01305-09 recto', 'KG 01305-10 recto', 'KG 01305-11 recto', 'KG 01305-12 recto', 'KG 01306-01 recto', 'KG 01306-06 recto', 'KG 01306-07 recto', 'KG 01306-08 recto', 'KG 01306-09 recto', 'KG 01306-10 recto', 'KG 01306-11 recto', 'KG 01306-12 recto', 'KG 01326-001 recto', 'KG 01326-002 recto', 'KG 01326-003 recto', 'KG 01326-004 recto', 'KG 01326-005 recto', 'KG 01326-006 recto', 'KG 01340-MAP-01 recto', 'KG 01340-MAP-02 recto', 'KG 01361-001 recto', 'KG 01361-002 recto', 'KG 01361-003 recto', 'KG 01362-001 recto', 'KG 01362-002 recto', 'KG 01362-003 recto', 'KG 01362-004 recto', 'KG 01364-001 recto', 'KG 01364-002 recto', 'KG 01364-003 recto', 'KG 01369-16 recto', 'KG 01369-17 recto', 'KG 01369-18 recto', 'KG 01369-19 recto', 'KG 01369-20 recto', 'KG 01369-21 recto', 'KG 01369-22 recto', 'KG 01369-23 recto', 'KG 01369-24 recto', 'KG 01369-25 recto', 'KG 01369-26 recto', 'KG 01369-27 recto', 'KG 01369-28 recto', 'KG 01369-29 recto', 'KG 01369-30 recto', 'KG 01369-MAP-01 recto', 'KG 01369-MAP-02 recto', 'KG 01387-kopie recto', 'KG 01516-kopie recto', 'KG 01517-kopie recto', 'KG 01556 dubbel recto', 'KG 01573 dubbel recto', 'KG 01604 dubbel recto', 'KG 01605 dubbel recto', 'KG 01606 dubbel recto', 'KG 01607 dubbel recto', 'KG 01608 dubbel recto', 'KG 01609 dubbel recto', 'KG 01621 dubbel recto', 'KG 01631 dubbel recto', 'KG 01652 dubbel recto', 'KG 01653 dubbel recto', 'KG 01654 dubbel recto', 'KG 01655 dubbel recto', 'KG 01656 dubbel recto', 'KG 01657 dubbel recto', 'KG 01673-001 recto', 'KG 01673-002 recto', 'KG 01673-003 recto', 'KG 01673-004 recto', 'KG 01673-005 recto', 'KG 01673-006 recto', 'KG 01693 dubbel recto', 'KG 01941-1952 verso recto', 'KG 01941-1952 recto', 'KG 01960_001 recto', 'KG 01960_002 recto', 'KG 01960_003 recto', 'KG 01960_004 recto', 'KG 01960_005 recto', 'KG 01960_006 recto', 'KG 01960_007 recto', 'KG 01960_008 recto', 'KG 01960_009 recto', 'KG 01960_010 recto', 'KG 01960_011 recto', 'KG 01960_012 recto', 'KG 01960_013 recto', 'KG 01960_014 recto', 'KG 01960_015 recto', 'KG 01960_016 recto', 'KG 01960_017 recto', 'KG 01960_018 recto', 'KG 01960_019 recto', 'KG 01960_020 recto', 'KG 01960_021 recto', 'KG 01960_022 recto', 'KG 01960_023 recto', 'KG 01960_024 recto', 'KG 01960_025 recto', 'KG 01960_026 recto', 'KG 01960_027 recto', 'KG 01960_028 recto', 'KG 01960_029 recto', 'KG 01960_030 recto', 'KG 01960_031 recto', 'KG 01960_032 recto', 'KG 01960_033 recto', 'KG 01960_034 recto', 'KG 01960_035 recto', 'KG 01960_036 recto', 'KG 01960_037 recto', 'KG 01960_038 recto', 'KG 01960_039 recto', 'KG 01960_040 recto', 'KG 01960_041 recto', 'KG 01960_042 recto', 'KG 01960_043 recto', 'KG 01960_044 recto', 'KG 01960_045 recto', 'KG 01960_046 recto', 'KG 01960_047 recto', 'KG 01960_048 recto', 'KG 01960_049 recto', 'KG 01960_050 recto', 'KG 01960_051 recto', 'KG 01960_052 recto', 'KG 01960_053 recto', 'KG 01960_054 recto', 'KG 01960_055 recto', 'KG 01960_056 recto', 'KG 01960_057 recto', 'KG 01960_058 recto', 'KG 01960_059 recto', 'KG 01960_060 recto', 'KG 01960_061 recto', 'KG 01960_062 recto', 'KG 01960_063 recto', 'KG 01960_064 recto', 'KG 01960_065 recto', 'KG 01960_066 recto', 'KG 01960_067 recto', 'KG 01960_068 recto', 'KG 01960_069 recto', 'KG 01960_070 recto', 'KG 01960_071 recto', 'KG 01960_072 recto', 'KG 01960_073 recto', 'KG 01960_074 recto', 'KG 01960_075 recto', 'KG 01960_076 recto', 'KG 01960_077 recto', 'KG 01960_078 recto', 'KG 01960_079 recto', 'KG 01960_080 recto', 'KG 01960_081 recto', 'KG 01960_082 recto', 'KG 01960_083 recto', 'KG 01960_084 recto', 'KG 01960_085 recto', 'KG 01960_086 recto', 'KG 01960_087 recto', 'KG 01960_088 recto', 'KG 01960_089 recto', 'KG 01960_090 recto', 'KG 01960_091 recto', 'KG 01960_092 recto', 'KG 01960_093 recto', 'KG 01960_094 recto', 'KG 01960_095 recto', 'KG 01960_096 recto', 'KG 01960_097 recto', 'KG 01960_098 recto', 'KG 01960_099 recto', 'KG 01960_100 recto', 'KG 01960_101 recto', 'KG 01960_102 recto', 'KG 01960_103 recto', 'KG 01960_104 recto', 'KG 01960_105 recto', 'KG 01960_106 recto', 'KG 01960_107 recto', 'KG 01960_108 recto', 'KG 01960_109 recto', 'KG 01960_110 recto', 'KG 01990 recto', 'KG 01991 recto', 'KG 01996-010 recto', 'KG 01996-011 recto', 'KG 01996-012 recto', 'KG 01996-013 recto', 'KG 01996-014 recto', 'KG 01996-015 recto', 'KG 01996-016 recto', 'KG 01996-017 recto', 'KG 01996-018 recto', 'KG 01996-019 recto', 'KG 01996-020 recto', 'KG 02007a recto', 'KG 02007b recto', 'KG 02037 recto', 'KG 02049 recto', 'KG 02050 recto', 'KG 02051 recto', 'KG 02052 recto', 'KG 02053 recto', 'KG 02054 recto', 'KG 02055 recto', 'KG 02056 recto', 'KG 02057 recto', 'KG 02058 recto', 'KG 02059 recto', 'KG 02060 recto', 'KG 0227 recto', 'KG 02296 verso recto', 'KG 02388 recto', 'KG 02433a recto', 'KG 02473-02475 recto', 'KG 02541b recto', 'KG 02615 recto', 'KG 02616 recto', 'KG 02617 recto', 'KG 02618 recto', 'KG 02720 recto', 'KG 03123 recto', 'KG 03124 recto', 'KG 03126 recto', 'KG 03127 recto', 'KG 03133 recto', 'KG 03134 recto', 'KG 03135 recto', 'KG 03144 recto', 'KG 03145 recto', 'KG 03146 recto', 'KG 03152 recto', 'KG 03157 recto', 'KG 03158 recto', 'KG 03159 recto', 'KG 03165 recto', 'KG 03166 recto', 'KG 03169 recto', 'KG 03170 recto', 'KG 03174 recto', 'KG 03175 recto', 'KG 03176 recto', 'KG 03177 recto', 'KG 03181 recto', 'KG 03191 recto', 'KG 03212 recto', 'KG 03213 recto', 'KG 03216 recto', 'KG 03217 recto', 'KG 03343 recto', 'KG 03344 recto', 'KG 03345 recto', 'KG 03370 recto', 'KG 03371 recto', 'KG 03372 recto', 'KG 03373 recto', 'KG 03374 recto', 'KG 03375 recto', 'KG 03376 recto', 'KG 03377 recto', 'KG 03378 recto', 'KG 03379 recto', 'KG 03525_001 recto', 'KG 03525_002 recto', 'KG 03525_003 recto', 'KG 03525_004 recto', 'KG 03525_005 recto', 'KG 03525_006 recto', 'KG 03525_007 recto', 'KG 03525_008 recto', 'KG 03525_009 recto', 'KG 03525_010 recto', 'KG 03525_011 recto', 'KG 03525_012 recto', 'KG 03525_013 recto', 'KG 03525_014 recto', 'KG 03525_015 recto', 'KG 03525_016 recto', 'KG 03525_017 recto', 'KG 03525_018 recto', 'KG 03525_019 recto', 'KG 03525_020 recto', 'KG 03525_021 recto', 'KG 03525_022 recto', 'KG 03525_023 recto', 'KG 03525_024 recto', 'KG 03525_025 recto', 'KG 03525_026 recto', 'KG 03525_027 recto', 'KG 03525_028 recto', 'KG 03525_029 recto', 'KG 03525_030 recto', 'KG 03525_031 recto', 'KG 03525_032 recto', 'KG 03525_033 recto', 'KG 03525_034 recto', 'KG 03525_035 recto', 'KG 03525_036 recto', 'KG 03525_037 recto', 'KG 03525_038 recto', 'KG 03525_039 recto', 'KG 03525_040 recto', 'KG 03525_041 recto', 'KG 03525_042 recto', 'KG 03525_043 recto', 'KG 03525_044 recto', 'KG 03525_045 recto', 'KG 03525_046 recto', 'KG 03525_047 recto', 'KG 03525_048 recto', 'KG 03525_049 recto', 'KG 03525_050 recto', 'KG 03525_051 recto', 'KG 03525_052 recto', 'KG 03525_053 recto', 'KG 03525_054 recto', 'KG 03525_055 recto', 'KG 03525_056 recto', 'KG 03525_057 recto', 'KG 03525_058 recto', 'KG 03525_059 recto', 'KG 03525_060 recto', 'KG 03525_061 recto', 'KG 03525_062 recto', 'KG 03525_063 recto', 'KG 03525_064 recto', 'KG 03525_065 recto', 'KG 03525_066 recto', 'KG 03525_067 recto', 'KG 03525_068 recto', 'KG 03525_069 recto', 'KG 03525_070 recto', 'KG 03525_071 recto', 'KG 03525_072 recto', 'KG 03525_073 recto', 'KG 03525_074 recto', 'KG 03525_075 recto', 'KG 03525_076 recto', 'KG 03525_077 recto', 'KG 03525_078 recto', 'KG 03525_079 recto', 'KG 03525_080 recto', 'KG 03525_081 recto', 'KG 03525_082 recto', 'KG 03525_083 recto', 'KG 03525_084 recto', 'KG 03525_085 recto', 'KG 03525_086 recto', 'KG 03525_087 recto', 'KG 03525_088 recto', 'KG 03525_089 recto', 'KG 03525_090 recto', 'KG 03525_091 recto', 'KG 03525_092 recto', 'KG 03525_093 recto', 'KG 03525_094 recto', 'KG 03525_095 recto', 'KG 03525_096 recto', 'KG 03525_097 recto', 'KG 03525_098 recto', 'KG 03525_099 recto', 'KG 03525_100 recto', 'KG 03525_101 recto', 'KG 03525_102 recto', 'KG 03525_103 recto', 'KG 03525_104 recto', 'KG 03525_105 recto', 'KG 03525_106 recto', 'KG 03525_107 recto', 'KG 03525_108 recto', 'KG 03525_109 recto', 'KG 03525_110 recto', 'KG 03525_111 recto', 'KG 03525_112 recto', 'KG 03525_113 recto', 'KG 03525_114 recto', 'KG 03525_115 recto', 'KG 03525_116 recto', 'KG 03525_117 recto', 'KG 03525_118 recto', 'KG 03525_119 recto', 'KG 03525_120 recto', 'KG 03525_121 recto', 'KG 03525_122 recto', 'KG 03525_123 recto', 'KG 03525_124 recto', 'KG 03525_125 recto', 'KG 03525_126 recto', 'KG 03525_127 recto', 'KG 03525_128 recto', 'KG 03525_129 recto', 'KG 03525_130 recto', 'KG 03525_131 recto', 'KG 03525_132 recto', 'KG 03525_133 recto', 'KG 03525_134 recto', 'KG 03525_135 recto', 'KG 03525_136 recto', 'KG 03525_137 recto', 'KG 03525_138 recto', 'KG 03525_139 recto', 'KG 03525_140 recto', 'KG 03525_141 recto', 'KG 03525_142 recto', 'KG 03525_143 recto', 'KG 03525_144 recto', 'KG 03525_145 recto', 'KG 03547-max recto', 'KG 03609 1 recto', 'KG 03745-max recto', 'KG 040846 recto', 'KG 04320-4326 verso recto', 'KG 04320-4326 recto', 'KG 04327-4334 verso recto', 'KG 04327-4334 recto', 'KG 04343-4349 verso recto', 'KG 04343-4349 recto', 'KG 04358-4365 verso recto', 'KG 04358-4365 recto', 'KG 04366-04371 verso recto', 'KG 04366-04371 recto', 'KG 04372-04375 verso recto', 'KG 04372-04375 recto', 'KG 04402-04421 verso recto', 'KG 04402-04421 recto', 'KG 04484-04491 verso recto', 'KG 04484-04491 recto', 'KG 04500-04511 verso recto', 'KG 04500-04511 recto', 'KG 04512 recto', 'KG 04650 recto', 'KG 04655-04661 verso recto', 'KG 04655-04661 recto', 'KG 04663-04673 verso recto', 'KG 04663-04673 recto', 'KG 04690-04693 verso recto', 'KG 04690-04693 recto', 'KG 04823 recto', 'KG 04824 recto', 'KG 04826 recto', 'KG 04827 recto', 'KG 04828 recto', 'KG 04829 recto', 'KG 04830 recto', 'KG 04831 recto', 'KG 04833 recto', 'KG 04834 recto', 'KG 04835 recto', 'KG 04836 recto', 'KG 04837 recto', 'KG 04838 recto', 'KG 04839 recto', 'KG 04840 recto', 'KG 04841 recto', 'KG 04842 recto', 'KG 04901 recto', 'KG 04903 recto', 'KG 04911 recto', 'KG 04912 recto', 'KG 04913 recto', 'KG 04914 recto', 'KG 04915 recto', 'KG 04916 recto', 'KG 04917 recto', 'KG 04918 recto', 'KG 04919 recto', 'KG 04920 recto', 'KG 04921 recto', 'KG 04922 recto', 'KG 04923 recto', 'KG 04924 recto', 'KG 04925 recto', 'KG 04926 recto', 'KG 04927 recto', 'KG 04928 recto', 'KG 04929 recto', 'KG 04930 recto', 'KG 04931 recto', 'KG 04932 recto', 'KG 04933 recto', 'KG 04934 recto', 'KG 04935 recto', 'KG 04936 recto', 'KG 04937 recto', 'KG 04938 recto', 'KG 04939 recto', 'KG 04940 recto', 'KG 04941 recto', 'KG 04942 recto', 'KG 04943 recto', 'KG 04944 recto', 'KG 04945 recto', 'KG 04946 recto', 'KG 04947 recto', 'KG 04948 recto', 'KG 04949 recto', 'KG 04950 recto', 'KG 04951 recto', 'KG 04952 recto', 'KG 04953 recto', 'KG 04954 recto', 'KG 04955 recto', 'KG 04956 recto', 'KG 04957 recto', 'KG 04958 recto', 'KG 04959 recto', 'KG 04960 recto', 'KG 04961 recto', 'KG 04962 recto', 'KG 04963 recto', 'KG 04964 recto', 'KG 04965 recto', 'KG 04966 recto', 'KG 04967 recto', 'KG 05097 1 recto', 'KG 05356-05385 verso recto', 'KG 05356-05385 recto', 'KG 05732-05755 verso recto', 'KG 05732-05755 recto', 'KG 05756-05770 verso recto', 'KG 05756-05770 recto', 'KG 05924-05969 verso recto', 'KG 05924-05969 recto', 'KG 05969-06015-23 verso recto', 'KG 05969-06015-23 recto', 'KG 05970-05975-05978 verso recto', 'KG 05970-05975-05978 recto', 'KG 05979-06014a verso recto', 'KG 05979-06014a recto', 'KG 06015-23 verso recto', 'KG 06015-23 recto', 'KG 06050 1 recto', 'KG 06123a recto', 'KG 06123b recto', 'KG 06123c recto', 'KG 06124a recto', 'KG 06124b recto', 'KG 06124c recto', 'KG 06221 recto', 'KG 06291a recto', 'KG 06364a recto', 'KG 06368a recto', 'KG 06369tekst recto', 'KG 06391a of 06392a recto', 'KG 06403a recto', 'KG 06405a recto', 'KG 06416a recto', 'KG 06419 recto', 'KG 06433a recto', 'KG 06441a recto', 'KG 06442a recto', 'KG 06443a recto', 'KG 06444a recto', 'KG 06447a recto', 'KG 06472 recto', 'KG 06472a recto', 'KG 06473 recto', 'KG 06474 recto', 'KG 06475 recto', 'KG 06476 recto', 'KG 06499a recto', 'KG 06527a recto', 'KG 06534 recto', 'KG 06549a recto', 'KG 06578a recto', 'KG 06578b recto', 'KG 06592a recto', 'KG 06593a recto', 'KG 06593b recto', 'KG 06593c recto', 'KG 06593D recto', 'KG 06596a recto', 'KG 06617a recto', 'KG 06627a recto', 'KG 06633 recto', 'KG 06682 recto', 'KG 06688a recto', 'KG 06688b recto', 'KG 06688c recto', 'KG 06688d recto', 'KG 06690A recto', 'KG 06690B recto', 'KG 06690C recto', 'KG 06690D recto', 'KG 06690E recto', 'KG 06690F recto', 'KG 06690G recto', 'KG 06690H recto', 'KG 06690I recto', 'KG 06690J recto', 'KG 06690K recto', 'KG 06690L recto', 'KG 06821a recto', 'KG 06821aa recto', 'KG 06821aaa recto', 'KG 06821b recto', 'KG 06821bb recto', 'KG 06821bbb recto', 'KG 06821c recto', 'KG 06821cc recto', 'KG 06821ccc recto', 'KG 06821d recto', 'KG 06821dd recto', 'KG 06821ddd recto', 'KG 06821e recto', 'KG 06821ee recto', 'KG 06821eee recto', 'KG 06821f recto', 'KG 06821ff recto', 'KG 06821fff recto', 'KG 06821g recto', 'KG 06821gg recto', 'KG 06821h recto', 'KG 06821hh recto', 'KG 06821i recto', 'KG 06821ii recto', 'KG 06821j recto', 'KG 06821jj recto', 'KG 06821k recto', 'KG 06821kk recto', 'KG 06821l recto', 'KG 06821ll recto', 'KG 06821m recto', 'KG 06821mm recto', 'KG 06821n recto', 'KG 06821nn recto', 'KG 06821o recto', 'KG 06821oo recto', 'KG 06821p recto', 'KG 06821pp recto', 'KG 06821q recto', 'KG 06821qq recto', 'KG 06821r recto', 'KG 06821rr recto', 'KG 06821s recto', 'KG 06821ss recto', 'KG 06821t recto', 'KG 06821tt recto', 'KG 06821u recto', 'KG 06821uu recto', 'KG 06821v recto', 'KG 06821vv recto', 'KG 06821w recto', 'KG 06821ww recto', 'KG 06821x recto', 'KG 06821xx recto', 'KG 06821y recto', 'KG 06821yy recto', 'KG 06821z recto', 'KG 06821zz recto', 'KG 06822_003 recto', 'KG 06822_004 recto', 'KG 06822_005 recto', 'KG 06822_006 recto', 'KG 06822_007 recto', 'KG 06822_008 recto', 'KG 06822_009 recto', 'KG 06822_010 recto', 'KG 06822_011 recto', 'KG 06822_012 recto', 'KG 06822_013 recto', 'KG 06822_014 recto', 'KG 06822_015 recto', 'KG 06822_016 recto', 'KG 06822_017 recto', 'KG 06822_018 recto', 'KG 06822_020 recto', 'KG 06822_021 recto', 'KG 06822_022 recto', 'KG 06822_023 recto', 'KG 06822_024 recto', 'KG 06822_025 recto', 'KG 06822_026 recto', 'KG 06822_027 recto', 'KG 06822_028 recto', 'KG 06822_029 recto', 'KG 06822_030 recto', 'KG 06822_031 recto', 'KG 06822_032 recto', 'KG 06822_033 recto', 'KG 06822_034 recto', 'KG 06822_035 recto', 'KG 06822_036 recto', 'KG 06822_037 recto', 'KG 06822_038 1 recto', 'KG 06822_038 recto', 'KG 06822_039 recto', 'KG 06822_040 recto', 'KG 06822_041 recto', 'KG 06822_042 recto', 'KG 06822_043 recto', 'KG 06822_044 recto', 'KG 06822_045 recto', 'KG 06822_046 recto', 'KG 06822_047 recto', 'KG 06822_048 recto', 'KG 06822_049 recto', 'KG 06822_050 recto', 'KG 06822_051 recto', 'KG 06822_052 recto', 'KG 06822_053 recto', 'KG 06822_054 recto', 'KG 06822_055 recto', 'KG 06822_056 recto', 'KG 06822_057 recto', 'KG 06822_058 recto', 'KG 06822_059 recto', 'KG 06822_060 recto', 'KG 06822_061 recto', 'KG 06822_062 recto', 'KG 06822_063 recto', 'KG 06822_064 recto', 'KG 06822_065 recto', 'KG 06822_066 recto', 'KG 06822_067 recto', 'KG 06822_068 recto', 'KG 06822_069 recto', 'KG 06822_070 recto', 'KG 06822_071 recto', 'KG 06822_072 recto', 'KG 06822_073 recto', 'KG 06822_074 recto', 'KG 06822_075 recto', 'KG 06822_076 recto', 'KG 06822_077 recto', 'KG 06822_078 recto', 'KG 06822_079 recto', 'KG 06822_080 recto', 'KG 06822_081 recto', 'KG 06822_082 recto', 'KG 06822_083 recto', 'KG 06822_084 recto', 'KG 06822_085 recto', 'KG 06822_086 recto', 'KG 06822_087 recto', 'KG 06822_088 recto', 'KG 07136a recto', 'KG 07147a recto', 'KG 07174-01 recto', 'KG 07176-01 recto', 'KG 07177-01 recto', 'KG 07179-01 recto', 'KG 07180-01 recto', 'KG 07183-89-01 recto', 'KG 07183-89-02 recto', 'KG 07183-89-03 recto', 'KG 07183-89-04 recto', 'KG 07183-89-05 recto', 'KG 07183-89-06 recto', 'KG 07198a recto', 'KG 07198b recto', 'KG 07198c recto', 'KG 07215a verso recto', 'KG 07215a recto', 'KG 07215b verso recto', 'KG 07215b recto', 'KG 07215c verso_1 recto', 'KG 07215c recto', 'KG 07327 recto', 'KG 07357a verso recto', 'KG 07357a recto', 'KG 07477 a-f recto', 'KG 07477-a recto', 'KG 07477-b recto', 'KG 07477-c recto', 'KG 07477-d recto', 'KG 07477-e recto', 'KG 07477-f recto', 'KG 07535a verso recto', 'KG 07535a recto', 'KG 07578_01 recto', 'KG 07578_02 recto', 'KG 07578_03 recto', 'KG 07578_04 recto', 'KG 07578_05 recto', 'KG 07681a recto', 'KG 07704a KG 07705a recto', 'KG 07723a recto', 'KG 07724a recto', 'KG 07814a recto', 'KG 07856 recto', 'KG 07872a recto', 'KG 07872b recto', 'KG 07883a recto', 'KG 07884a recto', 'KG 07911a recto', 'KG 07995 recto', 'KG 07996 recto', 'KG 08010a verso recto', 'KG 08010a recto', 'KG 08012a verso recto', 'KG 08012a recto', 'KG 08018a recto', 'KG 08034a recto', 'KG 08093 recto', 'KG 08195-a recto', 'KG 08197-A recto', 'KG 08199-A recto', 'KG 08201-A recto', 'KG 08202-A recto', 'KG 08203-A recto', 'KG 08204-A recto', 'KG 08209 recto', 'KG 08251a verso recto', 'KG 08251a recto', 'KG 08252a verso recto', 'KG 08252a recto', 'KG 08253- KG 08257 verso recto', 'KG 08253- KG 08257 recto', 'KG 08258-KG 08262 verso recto', 'KG 08258-KG 08262 recto', 'KG 08268- KG 08329 recto', 'KG 08446a verso recto', 'KG 08446a-KG 08463a recto', 'KG 08446a recto', 'KG 08448a verso recto', 'KG 08448a recto', 'KG 08449a verso recto', 'KG 08449a recto', 'KG 08451a verso recto', 'KG 08451a recto', 'KG 08452a verso recto', 'KG 08452a recto', 'KG 08454a verso recto', 'KG 08454a recto', 'KG 08455a verso recto', 'KG 08455a recto', 'KG 08457a verso recto', 'KG 08457a recto', 'KG 08459a verso recto', 'KG 08459a recto', 'KG 08461a verso recto', 'KG 08461a recto', 'KG 08462a verso recto', 'KG 08462a recto', 'KG 08464- KG 08468 recto', 'KG 08464-01-KG 08554-01 verso recto', 'KG 08464-01-KG 08554-01 recto', 'KG 08464-02-KG 08554-02 verso recto', 'KG 08464-02-KG 08554-02 recto', 'KG 08464-03-KG 08554-03 verso recto', 'KG 08464-03-KG 08554-03 recto', 'KG 08464-04-KG 08554-04 verso recto', 'KG 08464-04-KG 08554-04 recto', 'KG 08464-05-KG 08554-05 verso recto', 'KG 08464-05-KG 08554-05 recto', 'KG 08469-KG 08473 recto', 'KG 08474-KG 08478 recto', 'KG 08479-KG 08483 recto', 'KG 08484-KG 08488 recto', 'KG 08489-KG 08493 recto', 'KG 08494-KG 08498 verso recto', 'KG 08494-KG 08498 recto', 'KG 08499-KG 08503 verso recto', 'KG 08499-KG 08503 recto', 'KG 08504-KG 08508 verso recto', 'KG 08504-KG 08508 recto', 'KG 08509-KG 08513 verso recto', 'KG 08509-KG 08513 recto', 'KG 08514-KG 08518 verso recto', 'KG 08514-KG 08518 recto', 'KG 08519-KG 08523 verso recto', 'KG 08519-KG 08523 recto', 'KG 08524-KG 08528 verso recto', 'KG 08524-KG 08528 recto', 'KG 08529-KG 08533 verso recto', 'KG 08529-KG 08533 recto', 'KG 08534-KG 08538 verso recto', 'KG 08534-KG 08538 recto', 'KG 08539-KG 08543 verso recto', 'KG 08539-KG 08543 recto', 'KG 08544-KG 08648 verso recto', 'KG 08544-KG 08648 recto', 'KG 08549-KG 08653 verso recto', 'KG 08549-KG 08653 recto', 'KG 08554-KG 08664 verso recto', 'KG 08554-KG 08664 recto', 'KG 08555-01-KG 08643-01 verso recto', 'KG 08555-01-KG 08643-01 recto', 'KG 08555-02-KG 08643-02 verso recto', 'KG 08555-02-KG 08643-02 recto', 'KG 08555-03-KG 08643-03 verso recto', 'KG 08555-03-KG 08643-03 recto', 'KG 08555-04-KG 08643-04 verso recto', 'KG 08555-04-KG 08643-04 recto', 'KG 08555-05-KG 08643-05 verso recto', 'KG 08555-05-KG 08643-05 recto', 'KG 08555-06-KG 08643-06 verso recto', 'KG 08555-06-KG 08643-06 recto', 'KG 08555-KG 08559 verso recto', 'KG 08555-KG 08559 recto', 'KG 08555-KG 08643 verso recto', 'KG 08555-KG 08643 recto', 'KG 08560-KG 08566 verso recto', 'KG 08560-KG 08566 recto', 'KG 08567-KG 08569 verso recto', 'KG 08567-KG 08569 recto', 'KG 08570-KG 08572 verso recto', 'KG 08570-KG 08572 recto', 'KG 08573-KG 08577 verso recto', 'KG 08573-KG 08577 recto', 'KG 08578 verso recto', 'KG 08579-KG 08581 verso recto', 'KG 08579-KG 08581 recto', 'KG 08582-KG 08586 verso recto', 'KG 08582-KG 08586 recto', 'KG 08587-KG 08590 verso recto', 'KG 08587-KG 08590 recto', 'KG 08591-KG 08597 verso recto', 'KG 08591-KG 08597 recto', 'KG 08598-KG 08601 verso recto', 'KG 08598-KG 08601 recto', 'KG 08602-KG 08607 verso recto', 'KG 08602-KG 08607 recto', 'KG 08608-KG 08613 verso recto', 'KG 08608-KG 08613 recto', 'KG 08614-KG 08617 verso recto', 'KG 08614-KG 08617 recto', 'KG 08618-KG 08624 verso recto', 'KG 08618-KG 08624 recto', 'KG 08625-KG 08630 verso recto', 'KG 08625-KG 08630 recto', 'KG 08631-KG 08642 verso recto', 'KG 08631-KG 08642 recto', 'KG 08644-KG 08715a verso recto', 'KG 08644-KG 08715a recto', 'KG 09195-KG 09204 verso recto', 'KG 09195-KG 09204 recto', 'KG 09228-01 recto', 'KG 09228-02 recto', 'KG 09228-03 recto', 'KG 09228-04 recto', 'KG 09228-05 recto', 'KG 09228-06 recto', 'KG 09228-07 recto', 'KG 09228-08 recto', 'KG 09228-09 recto', 'KG 09228-10 recto', 'KG 09228-11 recto', 'KG 09228-12 recto', 'KG 09229-01 recto', 'KG 09229-02 recto', 'KG 09229-03 recto', 'KG 09229-04 recto', 'KG 09229-05 recto', 'KG 09229-06 recto', 'KG 09229-07 recto', 'KG 09229-08 recto', 'KG 09229-09 recto', 'KG 09229-10 recto', 'KG 09229-11 recto', 'KG 09229-12 recto', 'KG 09230-01 recto', 'KG 09230-02 recto', 'KG 09230-03 recto', 'KG 09230-04 recto', 'KG 09230-05 recto', 'KG 09230-06 recto', 'KG 09230-07 recto', 'KG 09230-08 recto', 'KG 09230-09 recto', 'KG 09230-10 recto', 'KG 09230-11 recto', 'KG 09230-12 recto', 'KG 09231-01 recto', 'KG 09231-02 recto', 'KG 09231-03 recto', 'KG 09231-04 recto', 'KG 09231-05 recto', 'KG 09231-06 recto', 'KG 09231-07 recto', 'KG 09231-08 recto', 'KG 09231-09 recto', 'KG 09231-10 recto', 'KG 09231-11 recto', 'KG 09231-12 recto', 'KG 09232-01 recto', 'KG 09232-02 recto', 'KG 09232-03 recto', 'KG 09232-04 recto', 'KG 09232-05 recto', 'KG 09232-06 recto', 'KG 09232-07 recto', 'KG 09232-08 recto', 'KG 09232-09 recto', 'KG 09232-10 recto', 'KG 09232-11 recto', 'KG 09232-12 recto', 'KG 09233-01 recto', 'KG 09233-02 recto', 'KG 09233-03 recto', 'KG 09233-04 recto', 'KG 09233-05 recto', 'KG 09233-06 recto', 'KG 09233-07 recto', 'KG 09233-08 recto', 'KG 09233-09 recto', 'KG 09233-10 recto', 'KG 09233-11 recto', 'KG 09233-12 recto', 'KG 09234-01 recto', 'KG 09234-02 recto', 'KG 09234-03 recto', 'KG 09234-04 recto', 'KG 09234-05 recto', 'KG 09234-06 recto', 'KG 09234-07 recto', 'KG 09234-08 recto', 'KG 09234-09 recto', 'KG 09234-10 recto', 'KG 09234-11 recto', 'KG 09234-12 recto', 'KG 09563_1 recto', 'KG 09573 recto', 'KG 09574 recto', 'KG 09575 recto', 'KG 09576 recto', 'KG 09577 recto', 'KG 09609 recto', 'KG 09800 9802_01 recto', 'KG 09800 9802_02 recto', 'KG 09800 A recto', 'KG 09800 A_01 recto', 'KG 09801 A recto', 'KG 09801 A_01 recto', 'KG 09801 A_02 recto', 'KG 09802 A recto', 'KG 09802 A_01 recto', 'KG 09803 9805_01 recto', 'KG 09803 9805_02 recto', 'KG 09803 A recto', 'KG 09803 A_01 recto', 'KG 09803 A_02 recto', 'KG 09804 A recto', 'KG 09804 A_01 recto', 'KG 09804 KG 9811_01 recto', 'KG 09804 KG 9811_02 recto', 'KG 09805 A recto', 'KG 09805 A_01 recto', 'KG 09806 A recto', 'KG 09806 A_01 recto', 'KG 09806 KG 09808_01 recto', 'KG 09806 KG 09808_02 recto', 'KG 09807 A recto', 'KG 09807 A_01 recto', 'KG 09808 A recto', 'KG 09808 A_01 recto', 'KG 09809 A recto', 'KG 09809 A_01 recto', 'KG 09810 A recto', 'KG 09810 A_01 recto', 'KG 09811 A recto', 'KG 09811 A_01 recto', 'KG 09812 A recto', 'KG 09812 A_01 recto', 'KG 09812 KG 09814_01 recto', 'KG 09812 KG 09814_02 recto', 'KG 09813 A recto', 'KG 09814 A recto', 'KG 09815 KG 09822_01 recto', 'KG 09815 KG 09822_02 recto', 'KG 09815 KG 09822_03 recto', 'KG 09815 KG 09822_04 recto', 'KG 09815-KG 09822_04 recto', 'KG 0986 2005 41cm recto', 'KG 0986 2006 41cm recto', 'KG 10629 01 recto', 'KG 10629 02 recto', 'KG 10629 03 recto', 'KG 10629 04 recto', 'KG 10629 05 recto', 'KG 10629 06 recto', 'KG 10630 01 recto', 'KG 10630 02 recto', 'KG 10630 03 recto', 'KG 10630 04 recto', 'KG 10630 05 recto', 'KG 10630 06 recto', 'KG 11-468 recto', 'KG 11173a recto', 'KG 11173b recto', 'KG 11269_001 recto', 'KG 11269_002 recto', 'KG 11269_003 recto', 'KG 11269_004 recto', 'KG 11269_005 recto', 'KG 11269_006 recto', 'KG 11269_007 recto', 'KG 11269_008 recto', 'KG 11269_009 recto', 'KG 11269_010 recto', 'KG 11269_011 recto', 'KG 11269_012 recto', 'KG 11269_013 recto', 'KG 11269_014 recto', 'KG 11269_015 recto', 'KG 11269_016 recto', 'KG 11269_017 recto', 'KG 11269_018 recto', 'KG 11269_019 recto', 'KG 11269_020 recto', 'KG 11269_021 recto', 'KG 11269_022 recto', 'KG 11269_023 recto', 'KG 11269_024 recto', 'KG 11269_025 recto', 'KG 11269_026 recto', 'KG 11269_027 recto', 'KG 11269_028 recto', 'KG 11269_029 recto', 'KG 11269_030 recto', 'KG 11269_031 recto', 'KG 11269_032 recto', 'KG 11269_033 recto', 'KG 11269_034 recto', 'KG 11269_035 recto', 'KG 11269_036 recto', 'KG 11269_037 recto', 'KG 11269_038 recto', 'KG 11269_039 recto', 'KG 11269_040 recto', 'KG 11269_041 recto', 'KG 11269_042 recto', 'KG 11269_043 recto', 'KG 11269_044 recto', 'KG 11269_045 recto', 'KG 11269_046 recto', 'KG 11269_047 recto', 'KG 11269_048 recto', 'KG 11269_049 recto', 'KG 11269_050 recto', 'KG 11269_051 recto', 'KG 11269_052 recto', 'KG 11269_053 recto', 'KG 11269_054 recto', 'KG 11269_055 recto', 'KG 11269_056 recto', 'KG 11269_057 recto', 'KG 11269_058 recto', 'KG 11269_059 recto', 'KG 11269_060 recto', 'KG 11269_061 recto', 'KG 11269_062 recto', 'KG 11269_063 recto', 'KG 11269_064 recto', 'KG 11269_065 recto', 'KG 11269_066 recto', 'KG 11269_067 recto', 'KG 11269_068 recto', 'KG 11269_069 recto', 'KG 11269_070 recto', 'KG 11269_071 recto', 'KG 11269_072 recto', 'KG 11269_073 recto', 'KG 11269_074 recto', 'KG 11269_075 recto', 'KG 11269_076 recto', 'KG 11269_077 recto', 'KG 11269_078 recto', 'KG 11269_079 recto', 'KG 11269_080 recto', 'KG 11269_081 recto', 'KG 11269_082 recto', 'KG 11269_083 recto', 'KG 11269_084 recto', 'KG 11269_085 recto', 'KG 11269_086 recto', 'KG 11269_087 recto', 'KG 11269_088 recto', 'KG 11269_089 recto', 'KG 11269_090 recto', 'KG 11269_091 recto', 'KG 11395-01 recto', 'KG 11395-02 recto', 'KG 11395-03 recto', 'KG 11395-04 recto', 'KG 11660 recto', 'KG 11772-KG 11777 verso recto', 'KG 11772-KG 11777 recto', 'KG 11786-KG 11800 verso recto', 'KG 11786-KG 11800 recto', 'KG 11810 - KG 11831 verso recto', 'KG 11810 - KG 11831 recto', 'KG 11832 - KG 11879 verso recto', 'KG 11832 - KG 11879 recto', 'KG 11913a recto', 'KG 11930a recto', 'KG 12188a recto', 'KG 12319 - KG 12393 verso recto', 'KG 12319 - KG 12393 recto', 'KG 12320 recto', 'KG 12321 recto', 'KG 12322 recto', 'KG 12323 recto', 'KG 12324 recto', 'KG 12325 recto', 'KG 12326 recto', 'KG 12327 recto', 'KG 12328 recto', 'KG 12329 recto', 'KG 12330 recto', 'KG 12331 recto', 'KG 12332 recto', 'KG 12333 recto', 'KG 12334 recto', 'KG 12335 recto', 'KG 12336 recto', 'KG 12337 recto', 'KG 12338 recto', 'KG 12339 recto', 'KG 12340 recto', 'KG 12342 recto', 'KG 12343 recto', 'KG 12344 recto', 'KG 12345 recto', 'KG 12346 recto', 'KG 12347 recto', 'KG 12348 recto', 'KG 12349 recto', 'KG 12349a recto', 'KG 12350 recto', 'KG 12351 recto', 'KG 12352 recto', 'KG 12353 recto', 'KG 12354 recto', 'KG 12355 recto', 'KG 12356 recto', 'KG 12357 recto', 'KG 12358 recto', 'KG 12359 recto', 'KG 12360 recto', 'KG 12362 recto', 'KG 12363 recto', 'KG 12364 recto', 'KG 12365 recto', 'KG 12366 recto', 'KG 12367 recto', 'KG 12368 recto', 'KG 12369 recto', 'KG 12370 recto', 'KG 12371 recto', 'KG 12372 recto', 'KG 12373 recto', 'KG 12374 recto', 'KG 12375 recto', 'KG 12376 recto', 'KG 12377 recto', 'KG 12378 recto', 'KG 12379 recto', 'KG 12380 recto', 'KG 12382 recto', 'KG 12383 recto', 'KG 12384 recto', 'KG 12385 recto', 'KG 12386 recto', 'KG 12387 recto', 'KG 12388 recto', 'KG 12389 recto', 'KG 12390 recto', 'KG 12391 recto', 'KG 12392 recto', 'KG 12395 recto', 'KG 12396 recto', 'KG 12397 recto', 'KG 12398 recto', 'KG 12399 recto', 'KG 12400 recto', 'KG 12401 recto', 'KG 12402 recto', 'KG 12403 recto', 'KG 12404 recto', 'KG 12405 recto', 'KG 12406 recto', 'KG 12407 recto', 'KG 12408 recto', 'KG 12409 recto', 'KG 12411 recto', 'KG 12412 recto', 'KG 12413 recto', 'KG 12414 recto', 'KG 12415 recto', 'KG 12416 recto', 'KG 12417 recto', 'KG 12418 recto', 'KG 12419 recto', 'KG 12420 recto', 'KG 12421 recto', 'KG 12422 recto', 'KG 12423 recto', 'KG 12424 recto', 'KG 12425 recto', 'KG 12427 recto', 'KG 12428 recto', 'KG 12429 recto', 'KG 12430 recto', 'KG 12431 recto', 'KG 12432 recto', 'KG 12433 recto', 'KG 12434 recto', 'KG 12435 recto', 'KG 12436 recto', 'KG 12437 recto', 'KG 12438 recto', 'KG 12439 recto', 'KG 12440 recto', 'KG 12442 recto', 'KG 12443 recto', 'KG 12444 recto', 'KG 12445 recto', 'KG 12446 recto', 'KG 12447 recto', 'KG 12448 recto', 'KG 12449 recto', 'KG 12450 recto', 'KG 12451 recto', 'KG 12452 recto', 'KG 12454 recto', 'KG 12455 recto', 'KG 12456 recto', 'KG 12458 recto', 'KG 12459 recto', 'KG 12459a recto', 'KG 12460 recto', 'KG 12461 recto', 'KG 12462 recto', 'KG 12463 recto', 'KG 12464 recto', 'KG 12465 recto', 'KG 12466 recto', 'KG 12467 recto', 'KG 12468 recto', 'KG 12469 recto', 'KG 12470 recto', 'KG 12471 recto', 'KG 12473 recto', 'KG 12474 recto', 'KG 12475 recto', 'KG 12476 recto', 'KG 12477 recto', 'KG 12478 recto', 'KG 12479 recto', 'KG 12480 recto', 'KG 12481 recto', 'KG 12482 recto', 'KG 12483 recto', 'KG 12484 recto', 'KG 12485 recto', 'KG 12487 recto', 'KG 12488 recto', 'KG 12489 recto', 'KG 12490 recto', 'KG 12491 recto', 'KG 12492 recto', 'KG 12493 recto', 'KG 12494 recto', 'KG 12495 recto', 'KG 12496 recto', 'KG 12497 recto', 'KG 12498 recto', 'KG 12499 recto', 'KG 12501 recto', 'KG 12502 recto', 'KG 12503 recto', 'KG 12504 recto', 'KG 12505 recto', 'KG 12506 recto', 'KG 12507 recto', 'KG 12509 recto', 'KG 12510 recto', 'KG 12511 recto', 'KG 12512 recto', 'KG 12513 recto', 'KG 12514 recto', 'KG 12515 recto', 'KG 12516 recto', 'KG 12517 recto', 'KG 12518 recto', 'KG 12519 recto', 'KG 12520 recto', 'KG 12522 recto', 'KG 12523 recto', 'KG 12524 recto', 'KG 12525 recto', 'KG 12526 recto', 'KG 12527 recto', 'KG 12528 recto', 'KG 12529 recto', 'KG 12530 recto', 'KG 12531 recto', 'KG 12532 recto', 'KG 12533 recto', 'KG 12534 recto', 'KG 12535 recto', 'KG 12537 recto', 'KG 12538 recto', 'KG 12539 recto', 'KG 12540 recto', 'KG 12541 recto', 'KG 12542 recto', 'KG 12543 recto', 'KG 12544 recto', 'KG 12545 recto', 'KG 12546 recto', 'KG 12547 recto', 'KG 12548 recto', 'KG 12549 recto', 'KG 12550 recto', 'KG 12551 recto', 'KG 12552 recto', 'KG 12553 recto', 'KG 12554 recto', 'KG 12555 recto', 'KG 12556 recto', 'KG 12557 recto', 'KG 12559 recto', 'KG 12560 recto', 'KG 12561 recto', 'KG 12562 recto', 'KG 12563 recto', 'KG 12564 recto', 'KG 12565 recto', 'KG 12566 recto', 'KG 12567 recto', 'KG 12568 recto', 'KG 12569 recto', 'KG 12570 recto', 'KG 12571 recto', 'KG 12843a recto', 'KG 12843b recto', 'KG 12844a recto', 'KG 12844b recto', 'KG 13157 recto', 'KG 13305a recto', 'KG 13596a recto', 'KG 13837 recto', 'KG 14103 recto', 'KG 14126 tm 14164A recto', 'KG 14164 A recto', 'KG 14164 B recto', 'KG 14164-A recto', 'KG 14164-B recto', 'KG 14165 tm 14196 recto', 'KG 14363a verso recto', 'KG 14363a recto', 'KG 14363b verso recto', 'KG 14363b recto', 'KG 14364 - KG 14425 verso recto', 'KG 14364 - KG 14425 recto', 'KG 14380a recto', 'KG 14390a recto', 'KG 14391a recto', 'KG 14392a recto', 'KG 14393a recto', 'KG 14394a recto', 'KG 14395a recto', 'KG 14396a recto', 'KG 14397a recto', 'KG 14410 detail a recto', 'KG 14410 detail b recto', 'KG 14412 detail a recto', 'KG 14412 detail b recto', 'KG 14414 detail a recto', 'KG 14416 detail a recto', 'KG 14423 detail a recto', 'KG 14423 detail b recto', 'KG 14442a recto', 'KG 14442b recto', 'KG 14442c recto', 'KG 14442d recto', 'KG 14442e recto', 'KG 14442f recto', 'KG 14464 recto', 'KG 14464a recto', 'KG 14464b verso recto', 'KG 14464b recto', 'KG 14464c-1 recto', 'KG 14464c-2 recto', 'KG 14464c-3 recto', 'KG 14464c-4 recto', 'KG 14464d-1 recto', 'KG 14464d-2 recto', 'KG 14464d-3 recto', 'KG 14464d-4 recto', 'KG 14464e-1 recto', 'KG 14464e-2 recto', 'KG 14464e-3 recto', 'KG 14464e-4 recto', 'KG 14464f-1 recto', 'KG 14464f-2 recto', 'KG 14464f-3 recto', 'KG 14464f-4 recto', 'KG 14464g verso recto', 'KG 14464g recto', 'KG 14537a recto', 'KG 14537b verso recto', 'KG 14537b recto', 'KG 14537c verso recto', 'KG 14537c recto', 'KG 14537d verso recto', 'KG 14537d recto', 'KG 14537e verso recto', 'KG 14537e recto', 'KG 14537f verso recto', 'KG 14537f recto', 'KG 14537g verso recto', 'KG 14537g recto', 'KG 14537h verso recto', 'KG 14537h recto', 'KG 14537i verso recto', 'KG 14537i recto', 'KG 14537j verso recto', 'KG 14537j recto', 'KG 14537k verso recto', 'KG 14537k recto', 'KG 14537l verso recto', 'KG 14537l recto', 'KG 14537m verso recto', 'KG 14537m recto', 'KG 14537n verso recto', 'KG 14537n recto', 'KG 14537o verso recto', 'KG 14537o recto', 'KG 14537p verso recto', 'KG 14537p recto', 'KG 14537q verso recto', 'KG 14537q recto', 'KG 14537r verso recto', 'KG 14537r recto', 'KG 14537s verso recto', 'KG 14537s recto', 'KG 14537t verso recto', 'KG 14537t recto', 'KG 14537u verso recto', 'KG 14537u recto', 'KG 14537v verso recto', 'KG 14537v recto', 'KG 14537w verso recto', 'KG 14537w recto', 'KG 14537x verso recto', 'KG 14537x recto', 'KG 14641a recto', 'KG 14641b verso recto', 'KG 14641b recto', 'KG 14641c verso recto', 'KG 14641c recto', 'KG 14641d verso recto', 'KG 14641d recto', 'KG 14641e verso recto', 'KG 14641e recto', 'KG 14641f verso recto', 'KG 14641f recto', 'KG 14641g verso recto', 'KG 14641g recto', 'KG 14641h verso recto', 'KG 14641h recto', 'KG 14641i verso recto', 'KG 14641i recto', 'KG 14735a recto', 'KG 14951 - KG 14962 verso recto', 'KG 14951 - KG 14962 recto', 'KG 14951a - KG 14974 verso recto', 'KG 14951a - KG 14974 recto', 'KG 14951a recto', 'KG 14951b verso recto', 'KG 14951b recto', 'KG 14951c verso recto', 'KG 14951c recto', 'KG 14951d verso recto', 'KG 14951d recto', 'KG 14951e verso recto', 'KG 14951e recto', 'KG 14951f verso recto', 'KG 14951f recto', 'KG 14951g verso recto', 'KG 14951g recto', 'KG 14951h verso recto', 'KG 14951h recto', 'KG 14951i verso recto', 'KG 14951i recto', 'KG 14951j verso recto', 'KG 14951j recto', 'KG 14963a verso recto', 'KG 14963a recto', 'KG 14963b verso recto', 'KG 14963b recto', 'KG 14963c verso recto', 'KG 14963c recto', 'KG 14963d verso recto', 'KG 14963d recto', 'KG 14964e verso recto', 'KG 14964e recto', 'KG 14965f verso recto', 'KG 14965f recto', 'KG 15207 recto', 'KG 15353b recto', 'KG 15463a recto', 'KG 15520 recto', 'KG 15540 recto', 'KG 15544a recto', 'KG 15547a recto', 'KG 15547b recto', 'KG 15549a recto', 'KG 15550a recto', 'KG 15564_1 recto', 'KG 1560 recto', 'KG 15663b recto', 'KG 15663c recto', 'KG 15663d recto', 'KG 15663e recto', 'KG 15666a recto', 'KG 15666b recto', 'KG 15678-01 recto', 'KG 15678-02 recto', 'KG 15678-03 recto', 'KG 15678-04 recto', 'KG 15678-05 recto', 'KG 15678-06 recto', 'KG 15678-07 recto', 'KG 15678-08 recto', 'KG 15678-09 recto', 'KG 15678-10 recto', 'KG 15678-11 recto', 'KG 15678-12 recto', 'KG 15678-13 recto', 'KG 15678-14 recto', 'KG 15678-15 recto', 'KG 15678-16 recto', 'KG 15678-17 recto', 'KG 15678-18 recto', 'KG 15678-19 recto', 'KG 15678-20 recto', 'KG 15678-21 recto', 'KG 15678-22 recto', 'KG 15678-23 recto', 'KG 15678-24 recto', 'KG 15678-25 recto', 'KG 15678-26 recto', 'KG 15678-27 recto', 'KG 15766-KG 15775 verso recto', 'KG 15766-KG 15775 recto', 'KG 15776-KG 15818 verso recto', 'KG 15776-KG 15818 recto', 'KG 15819-KG 15829 verso recto', 'KG 15819-KG 15829 recto', 'KG 15830-KG 15838 01 verso recto', 'KG 15830-KG 15838 01 recto', 'KG 15830-KG 15838 02 verso recto', 'KG 15830-KG 15838 02 recto', 'KG 15830-KG 15838 03 verso recto', 'KG 15830-KG 15838 03 recto', 'KG 15830-KG 15838 recto', 'KG 15839 verso recto', 'KG 15839 recto', 'KG 15839a recto', 'KG 15839b recto', 'KG 15839c verso recto', 'KG 15839c recto', 'KG 15839d verso recto', 'KG 15839d recto', 'KG 15839e verso recto', 'KG 15839e recto', 'KG 15839f verso recto', 'KG 15839f recto', 'KG 15839g recto', 'KG 15839h recto', 'KG 15839i verso recto', 'KG 15839i recto', 'KG 15862 verso recto', 'KG 15869 recto', 'KG 15870 recto', 'KG 15871 recto', 'KG 15872 recto', 'KG 15873 recto', 'KG 15874 recto', 'KG 15875 recto', 'KG 15876 recto', 'KG 15877 recto', 'KG 15878 recto', 'KG 15879 recto', 'KG 15880 recto', 'KG 15881 recto', 'KG 15882 recto', 'KG 15883 recto', 'KG 15884 recto', 'KG 15885 recto', 'KG 15886 recto', 'KG 15910-01 recto', 'KG 15910-02 recto', 'KG 15910-03 recto', 'KG 15910-04 recto', 'KG 15910-05 recto', 'KG 15910-06 recto', 'KG 15910_002 recto', 'KG 15910_003 recto', 'KG 15910_004 recto', 'KG 15910_005 recto', 'KG 15910_006 recto', 'KG 15910_007 recto', 'KG 15910_008 recto', 'KG 15910_009 recto', 'KG 15910_010 recto', 'KG 15910_011 recto', 'KG 15910_012 recto', 'KG 15910_013 recto', 'KG 15910_014 recto', 'KG 15910_015 recto', 'KG 15910_016 recto', 'KG 15910_017 recto', 'KG 15910_018 recto', 'KG 15910_019 recto', 'KG 15910_020 recto', 'KG 15910_021 recto', 'KG 15910_022 recto', 'KG 15910_023 recto', 'KG 15910_024 recto', 'KG 15910_025 recto', 'KG 15910_026 recto', 'KG 15910_027 recto', 'KG 15910_028 recto', 'KG 15910_029 recto', 'KG 15910_030 recto', 'KG 15910_031 recto', 'KG 15910_032 recto', 'KG 15910_033 recto', 'KG 15910_034 recto', 'KG 15910_035 recto', 'KG 15910_036 recto', 'KG 15910_037 recto', 'KG 15910_038 recto', 'KG 15910_039 recto', 'KG 15910_040 recto', 'KG 15910_041 recto', 'KG 15910_042 recto', 'KG 15910_043 recto', 'KG 15910_044 recto', 'KG 15910_045 recto', 'KG 15910_046 recto', 'KG 15910_047 recto', 'KG 15910_048 recto', 'KG 15910_049 recto', 'KG 15910_050 recto', 'KG 15910_051 recto', 'KG 15910_052 recto', 'KG 15910_053 recto', 'KG 15910_054 recto', 'KG 15910_055 recto', 'KG 15910_056 recto', 'KG 15910_057 recto', 'KG 15910_058 recto', 'KG 15910_059 recto', 'KG 15910_060 recto', 'KG 15910_061 recto', 'KG 15910_062 recto', 'KG 15910_063 recto', 'KG 15910_064 recto', 'KG 15910_065 recto', 'KG 15910_066 recto', 'KG 15910_067 recto', 'KG 15910_068 recto', 'KG 15910_069 recto', 'KG 15910_070 recto', 'KG 15910_071 recto', 'KG 15910_072 recto', 'KG 15910_073 recto', 'KG 15910_074 recto', 'KG 15910_075 recto', 'KG 15910_076 recto', 'KG 15910_077 recto', 'KG 15910_078 recto', 'KG 15910_079 recto', 'KG 15910_080 recto', 'KG 15910_081 recto', 'KG 15910_082 recto', 'KG 15910_083 recto', 'KG 15910_084 recto', 'KG 15910_085 recto', 'KG 15910_086 recto', 'KG 15910_087 recto', 'KG 15910_088 recto', 'KG 15910_089 recto', 'KG 15910_090 recto', 'KG 15910_091 recto', 'KG 15910_092 recto', 'KG 15910_093 recto', 'KG 15910_094 recto', 'KG 15910_095 recto', 'KG 15910_096 recto', 'KG 15910_097 recto', 'KG 15910_098 recto', 'KG 15910_099 recto', 'KG 15910_100 recto', 'KG 15910_101 recto', 'KG 15910_102 recto', 'KG 15981 1 recto', 'KG 16095 recto', 'KG 16135 recto', 'KG 16136 recto', 'KG 16137 recto', 'KG 16138 recto', 'KG 16139 recto', 'KG 16140 recto', 'KG 16141 recto', 'KG 16142 recto', 'KG 16143 recto', 'KG 16144 recto', 'KG 16145 recto', 'KG 16146 recto', 'KG 16147 recto', 'KG 16148 recto', 'KG 16149 recto', 'KG 16150 recto', 'KG 16151 recto', 'KG 16152 recto', 'KG 16153 recto', 'KG 16154 recto', 'KG 16155 recto', 'KG 16156 recto', 'KG 16157 recto', 'KG 16158 recto', 'KG 16159 recto', 'KG 16160 recto', 'KG 16161 recto', 'KG 16162 recto', 'KG 16163 recto', 'KG 16164 recto', 'KG 16165 recto', 'KG 16166 recto', 'KG 16167 recto', 'KG 16168 recto', 'KG 16169 recto', 'KG 16170 recto', 'KG 16171 recto', 'KG 16172 recto', 'KG 16173 recto', 'KG 16174 recto', 'KG 16175 recto', 'KG 16176 recto', 'KG 16177 recto', 'KG 16178 recto', 'KG 16179 recto', 'KG 16180 recto', 'KG 16181 recto', 'KG 16182 recto', 'KG 16183 recto', 'KG 16184 recto', 'KG 16185 recto', 'KG 16186 recto', 'KG 16187 recto', 'KG 16188 recto', 'KG 16189 recto', 'KG 16190 recto', 'KG 16191 recto', 'KG 16192 recto', 'KG 16193 recto', 'KG 16194 recto', 'KG 16195 recto', 'KG 16196 recto', 'KG 16197 recto', 'KG 16198 recto', 'KG 16199 recto', 'KG 16200 recto', 'KG 16201 recto', 'KG 16202 recto', 'KG 16203 recto', 'KG 16204 recto', 'KG 16205 recto', 'KG 16206 recto', 'KG 16207 recto', 'KG 16208 recto', 'KG 16209 recto', 'KG 16210 recto', 'KG 16211 recto', 'KG 16212 recto', 'KG 16213 recto', 'KG 16214 recto', 'KG 16215 recto', 'KG 16216 recto', 'KG 16217 recto', 'KG 16218 recto', 'KG 16219 recto', 'KG 16220 recto', 'KG 16221 recto', 'KG 16222 recto', 'KG 16223 recto', 'KG 16224 recto', 'KG 16225 recto', 'KG 16226 recto', 'KG 16227 recto', 'KG 16228 recto', 'KG 16229 recto', 'KG 16230 recto', 'KG 16231 recto', 'KG 16232 recto', 'KG 16233 recto', 'KG 16268a recto', 'KG 16269a recto', 'KG 16270a recto', 'KG 16271a recto', 'KG 16272a recto', 'KG 16273a recto', 'KG 16274a recto', 'KG 16275a recto', 'KG 16276a recto', 'KG 16277a recto', 'KG 16328-16348_001 recto', 'KG 16328-16348_002 recto', 'KG 16328-16348_003 recto', 'KG 16328-16348_004 recto', 'KG 16328-16348_005 recto', 'KG 16328-16348_006 recto', 'KG 16328-16348_007 recto', 'KG 16328-16348_008 recto', 'KG 16328-16348_009 recto', 'KG 16328-16348_010 recto', 'KG 16328-16348_011 recto', 'KG 16328-16348_012 recto', 'KG 16328-16348_013 recto', 'KG 16328-16348_014 recto', 'KG 16328-16348_015 recto', 'KG 16328-16348_016 recto', 'KG 16328-16348_017 recto', 'KG 16328-16348_018 recto', 'KG 16328-16348_019 recto', 'KG 16328-16348_020 recto', 'KG 16328-16348_021 recto', 'KG 16328-16348_022 recto', 'KG 16328-16348_023 recto', 'KG 16328-16348_024 recto', 'KG 16328-16348_025 recto', 'KG 16328-16348_026 recto', 'KG 16328-16348_027 recto', 'KG 16328-16348_028 recto', 'KG 16367b recto', 'KG 16534a recto', 'KG 16534b recto', 'KG 16536 001 recto', 'KG 16536 002 recto', 'KG 16536 003 recto', 'KG 16536 004 recto', 'KG 16536 005 recto', 'KG 16536 006 recto', 'KG 16536 007 recto', 'KG 16536 008 recto', 'KG 16536 009 recto', 'KG 16536 010 recto', 'KG 16536 011 recto', 'KG 16536 012 recto', 'KG 16536 013 recto', 'KG 16536 014 recto', 'KG 16536 015 recto', 'KG 16536 016 recto', 'KG 16536 017 recto', 'KG 16536 018 recto', 'KG 16536 019 recto', 'KG 16536 020 recto', 'KG 16536 021 recto', 'KG 16536 022 recto', 'KG 16536 023 recto', 'KG 16536 024 recto', 'KG 16536 025 recto', 'KG 16536 026 recto', 'KG 16536 027 recto', 'KG 16536 028 recto', 'KG 16536 029 recto', 'KG 16536 030 recto', 'KG 16536 031 recto', 'KG 16536 032 recto', 'KG 16536 033 recto', 'KG 16536 034 recto', 'KG 16536 035 recto', 'KG 16536 036 recto', 'KG 16536 037 recto', 'KG 16536 038 recto', 'KG 16536 039 recto', 'KG 16536 040 recto', 'KG 16536 041 recto', 'KG 16536 042 recto', 'KG 16536 043 recto', 'KG 16536 044 recto', 'KG 16536 045 recto', 'KG 16536 046 recto', 'KG 16536 047 recto', 'KG 16536 048 recto', 'KG 16536 049 recto', 'KG 16536 050 recto', 'KG 16536 051 recto', 'KG 16536 052 recto', 'KG 16536 053 recto', 'KG 16536 054 recto', 'KG 16536 055 recto', 'KG 16536 056 recto', 'KG 16536 057 recto', 'KG 16536 058 recto', 'KG 16536 059 recto', 'KG 16536 060 recto', 'KG 16536 061 recto', 'KG 16536 062 recto', 'KG 16536 063 recto', 'KG 16536 064 recto', 'KG 16536 065 recto', 'KG 16536 066 recto', 'KG 16536 067 recto', 'KG 16536 068 recto', 'KG 16536 069 recto', 'KG 16536 070 recto', 'KG 16536 071 recto', 'KG 16536 072 recto', 'KG 16536 073 recto', 'KG 16536 074 recto', 'KG 16536 075 recto', 'KG 16536 076 recto', 'KG 16536 077 recto', 'KG 16536 078 recto', 'KG 16536 079 recto', 'KG 16536 080 recto', 'KG 16536 081 recto', 'KG 16536 082 recto', 'KG 16536 083 recto', 'KG 16536 084 recto', 'KG 16536 085 recto', 'KG 16536 086 recto', 'KG 16536 087 recto', 'KG 16536 088 recto', 'KG 16536 089 recto', 'KG 16536 090 recto', 'KG 16536 091 recto', 'KG 16536 092 recto', 'KG 16536 093 recto', 'KG 16536 094 recto', 'KG 16536 095 recto', 'KG 16536 096 recto', 'KG 16536 097 recto', 'KG 16536 098 recto', 'KG 16597a verso recto', 'KG 16597a recto', 'KG 16613 A recto', 'KG 16645a recto', 'KG 16645b recto', 'KG 16655 recto', 'KG 16656 recto', 'KG 16657 recto', 'KG 16658 recto', 'KG 16659 recto', 'KG 16660 recto', 'KG 16661 recto', 'KG 16662 recto', 'KG 16663 recto', 'KG 16664 recto', 'KG 16665 recto', 'KG 16666 recto', 'KG 16667 recto', 'KG 16668 recto', 'KG 16669 recto', 'KG 16670 recto', 'KG 16671 recto', 'KG 16672 recto', 'KG 16673 recto', 'KG 16674 recto', 'KG 16675 recto', 'KG 16676 recto', 'KG 16677 recto', 'KG 16678 recto', 'KG 16679 recto', 'KG 16680 recto', 'KG 16681 recto', 'KG 16682 recto', 'KG 16683 recto', 'KG 16684 recto', 'KG 16685 recto', 'KG 16686 recto', 'KG 16687 recto', 'KG 16688 recto', 'KG 16689 recto', 'KG 16690 recto', 'KG 16691 recto', 'KG 16692 recto', 'KG 16693 recto', 'KG 16694 recto', 'KG 16695 recto', 'KG 16696 recto', 'KG 16697 recto', 'KG 16698 recto', 'KG 16699 recto', 'KG 16700 recto', 'KG 16701 recto', 'KG 16702 recto', 'KG 16703 recto', 'KG 16704 recto', 'KG 16705 recto', 'KG 16706 recto', 'KG 16707 recto', 'KG 16708 recto', 'KG 16709 recto', 'KG 16710 recto', 'KG 16711 recto', 'KG 16712 recto', 'KG 16713 recto', 'KG 16714 recto', 'KG 16715 recto', 'KG 16716 recto', 'KG 16717 recto', 'KG 16718 recto', 'KG 16719 recto', 'KG 16720 recto', 'KG 16721 recto', 'KG 16722 recto', 'KG 16723 recto', 'KG 16724 recto', 'KG 16725 recto', 'KG 16726 recto', 'KG 16727 recto', 'KG 16728 recto', 'KG 16729 recto', 'KG 16730 recto', 'KG 16731 recto', 'KG 16732 recto', 'KG 16733 recto', 'KG 16734 recto', 'KG 16735 recto', 'KG 16736 recto', 'KG 16737 recto', 'KG 16738 recto', 'KG 16739 recto', 'KG 16740 recto', 'KG 16741 recto', 'KG 16742 recto', 'KG 16743 recto', 'KG 16744 recto', 'KG 16745 recto', 'KG 16746 recto', 'KG 16747 recto', 'KG 16748 recto', 'KG 16749 recto', 'KG 16750 recto', 'KG 16751 recto', 'KG 16752 recto', 'KG 16753 recto', 'KG 16754 recto', 'KG 16755 recto', 'KG 16756 recto', 'KG 16757 recto', 'KG 16758 recto', 'KG 16759 recto', 'KG 16760 recto', 'KG 16761 recto', 'KG 16762 recto', 'KG 16763 recto', 'KG 16764 recto', 'KG 16765 recto', 'KG 16766 recto', 'KG 16767 recto', 'KG 16769 recto', 'KG 16770 recto', 'KG 16772 recto', 'KG 16773 recto', 'KG 16774 recto', 'KG 16775 recto', 'KG 16777-01 recto', 'KG 16777-02 recto', 'KG 16778 recto', 'KG 16779 recto', 'KG 16780 recto', 'KG 16781 recto', 'KG 16782 recto', 'KG 16783 recto', 'KG 16784 recto', 'KG 16785 recto', 'KG 16786 recto', 'KG 16787 recto', 'KG 16788 recto', 'KG 16789 recto', 'KG 16790 recto', 'KG 16791 recto', 'KG 16792 recto', 'KG 16793 recto', 'KG 16794 recto', 'KG 16795 recto', 'KG 16796 recto', 'KG 16797 recto', 'KG 16798 recto', 'KG 16799 recto', 'KG 16800 recto', 'KG 16801 recto', 'KG 16802 recto', 'KG 16803 recto', 'KG 16804 recto', 'KG 16805 recto', 'KG 16806 recto', 'KG 16807 recto', 'KG 16808 recto', 'KG 16809 recto', 'KG 16810 recto', 'KG 16811 recto', 'KG 16812 recto', 'KG 16813 recto', 'KG 16814 recto', 'KG 16815 recto', 'KG 16816 recto', 'KG 16817 recto', 'KG 16818 recto', 'KG 16819 recto', 'KG 16820 recto', 'KG 16821 recto', 'KG 16822 recto', 'KG 16823 recto', 'KG 16824 recto', 'KG 16825 recto', 'KG 16826 recto', 'KG 16827 recto', 'KG 16828 recto', 'KG 16829 recto', 'KG 16830 recto', 'KG 16831 recto', 'KG 16832 recto', 'KG 16833 recto', 'KG 16834 recto', 'KG 16835 recto', 'KG 16836 recto', 'KG 16837 recto', 'KG 16838 recto', 'KG 16839 recto', 'KG 16840 recto', 'KG 16841 recto', 'KG 16842 recto', 'KG 16843 recto', 'KG 16844 recto', 'KG 16845 recto', 'KG 16846 recto', 'KG 16847 recto', 'KG 16848 recto', 'KG 16849 recto', 'KG 16850 recto', 'KG 16851 recto', 'KG 16852 recto', 'KG 16853 recto', 'KG 16854 recto', 'KG 16855 recto', 'KG 16856 recto', 'KG 16857 recto', 'KG 16858 recto', 'KG 16859 recto', 'KG 16860 recto', 'KG 16861 recto', 'KG 16862 recto', 'KG 16867 recto', 'KG 16868 recto', 'KG 16869 recto', 'KG 16870 recto', 'KG 16871 recto', 'KG 16872 recto', 'KG 16873 recto', 'KG 16874 recto', 'KG 16875 recto', 'KG 16876 recto', 'KG 16877 recto', 'KG 16878 recto', 'KG 16879 recto', 'KG 16880 recto', 'KG 16881 recto', 'KG 16882 recto', 'KG 16883 recto', 'KG 16884 recto', 'KG 16885 recto', 'KG 16886 recto', 'KG 16887 recto', 'KG 16888 recto', 'KG 16895a recto', 'KG 16895b recto', 'KG 16950 recto', 'KG 16994 recto', 'KG 17024 recto', 'KG 17025 recto', 'KG 17055 recto', 'KG 17073-A recto', 'KG 17083 recto', 'KG 17130 recto', 'KG 17180 recto', 'KG 17194 recto', 'KG 17213 recto', 'KG 17217 recto', 'KG 17218 recto', 'KG 17219 recto', 'KG 17230 recto', 'KG 17231a recto', 'KG 17231b recto', 'KG 17235 recto', 'KG 17238a recto', 'KG 17238b recto', 'KG 17370 recto', 'KG 17371 recto', 'KG 17467 recto', 'KG 17475 recto', 'KG 17487 recto', 'KG 17508 recto', 'KG 17550 recto', 'KG 17559 recto', 'KG 17573 recto', 'KG 17598 verso recto', 'KG 17625 recto', 'KG 17642 verso recto', 'KG 17659 recto', 'KG 17662a recto', 'KG 17662b recto', 'KG 17664 recto', 'KG 17745a kopie recto', 'KG 17762 recto', 'KG 17813 recto', 'KG 17814 recto', 'KG 17831 recto', 'KG 17832 recto', 'KG 17835 recto', 'KG 17836 recto', 'KG 17859b recto', 'KG 17887 recto', 'KG 18177a recto', 'KG 18477 recto', 'KG 18480 recto', 'KG 18606 recto', 'KG 18614 verso recto', 'KG 18615 verso recto', 'KG 18616 verso recto', 'KG 18617 verso recto', 'KG 18620 verso recto', 'KG 18621 verso recto', 'KG 18623 recto', 'KG 18624 verso recto', 'KG 18627 verso recto', 'KG 18628 verso recto', 'KG 18659 recto', 'KG 1991 10 recto', 'KG 1993 001b recto 1 recto', 'KG 1993 001b recto recto', 'KG 1993 001b verso recto', 'KG 1996 055 recto', 'KG 1996 093 recto', 'KG 1997 001-2 recto', 'KG 1997 001-3 recto', 'KG 1997 005 recto', 'KG 1997 006 recto', 'KG 1997 042a recto', 'KG 1997 066 recto', 'KG 1997 50 recto', 'KG 1999 059 recto', 'KG 2000 033_1 recto', 'KG 2000 042 verso recto', 'KG 2000 085 recto', 'KG 2000 086 recto', 'KG 2000 087 recto', 'KG 2000 093 verso recto', 'KG 2000 153 recto', 'KG 2000 154 recto', 'KG 2000 155 recto', 'KG 2000 156 recto', 'KG 2000 157 recto', 'KG 2000 158 recto', 'KG 2000 159-01 recto', 'KG 2000 159-02 recto', 'KG 2000 159-03 recto', 'KG 2000 159-04 recto', 'KG 2000 159-05 recto', 'KG 2000 159-06 recto', 'KG 2000 159-07 recto', 'KG 2000 159-08 recto', 'KG 2000 159-09 recto', 'KG 2000 159-10 recto', 'KG 2000 159-11 recto', 'KG 2000 159-12 recto', 'KG 20009 verso recto', 'KG 2001 1 recto', 'KG 2001 10 recto', 'KG 2001 11 recto', 'KG 2001 12 recto', 'KG 2001 13 recto', 'KG 2001 14 recto', 'KG 2001 15 recto', 'KG 2001 2 recto', 'KG 2001 3 recto', 'KG 2001 4 recto', 'KG 2001 5 recto', 'KG 2001 6 recto', 'KG 2001 7 recto', 'KG 2001 8 recto', 'KG 2001 9 recto', 'KG 2005 015-a recto', 'KG 2005 015-b recto', 'KG 2005 015-c recto', 'KG 2005 015-d recto', 'KG 2005 015-e recto', 'KG 2005 015-f recto', 'KG 2005 015-g recto', 'KG 2005 015-h recto', 'KG 2005 015-i recto', 'KG 2005 015-j recto', 'KG 2005 015-k recto', 'KG 2005 015-l recto', 'KG 2006 001 recto', 'KG 2006 050 recto', 'KG 2006 Br 01 recto', 'KG 2006 Br 02 recto', 'KG 2006 Br 03 recto', 'KG 2006 Br 05 recto', 'KG 2007 018 recto', 'KG 2007 024a-l recto', 'KG 2007 2 recto', 'KG 2009 002-1 recto', 'KG 2009 002-2 recto', 'KG 2009 075 recto', 'KG 2010 014 recto recto', 'KG 2010 014 verso recto', 'KG 2010 014a recto', 'KG 2010 014b recto', 'KG 2010 014c recto', 'KG 2010 014d recto', 'KG 2010 017 recto', 'KG 2011 014 verso recto', 'KG 2011 014 recto', 'KG 2011 014a recto', 'KG 2011 014b recto', 'KG 2011 014c recto', 'KG 2011 014d recto', 'KG 2012 002-2 recto', 'KG 2012 003-2 recto', 'KG 2012 018 recto', 'KG 2012 019 recto', 'KG 2012 020 recto', 'KG 2012 021 recto', 'KG 2012 022 recto', 'KG 2012 023 recto', 'KG 2012 024 recto', 'KG 2012 025 recto', 'KG 2012 026 recto', 'KG 2012 033 recto', 'KG 2012 034 recto', 'KG 2012 035 recto', 'KG 2012 036 recto', 'KG 2048a recto', 'KG 21023 recto', 'KG 3985 41 cm recto', 'KG 57777-88 recto', 'KG 6320 recto', 'KG FENIERS verso recto', 'KG FENIERS recto', 'KG GEEN NUMMER recto', 'KG MAP 143 ZONDER NUMMER_01 recto', 'KG MAP 143 ZONDER NUMMER_02 recto', 'KG MAP 143 ZONDER NUMMER_03 recto', 'KG MAP 143 ZONDER NUMMER_04 recto', 'KG MAPJE verso recto', 'KG MAPJE recto', 'KG-62+++ 122 bis recto', 'KG-62+++ 122 recto', 'KG-62+++136 bis recto', 'Kleurenkaart recto', 'KMs 2000 001 recto', 'KMs 2000 002 recto', 'KMs 2000 003 recto', 'KMs 2000 004 recto', 'KMs 2000 005 recto', 'KMs 2000 006 recto', 'KMs 2000 007 recto', 'KMs 2000 007_007 recto', 'KMs 2000 008 recto', 'KMs 2000 009 recto', 'KMs 2000 010 recto', 'KMs 2000 011 recto', 'KMs 2000 012 recto', 'KMs 2000 013 recto', 'KMs 2000 014 recto', 'KMs 2000 015 recto', 'KMs 2000 016 recto', 'KMs 2000 017 recto', 'KMs 2000 018 recto', 'KMs 2000 019 recto', 'KMs 2000 020 recto', 'KMs 2000 021 recto', 'KMs 2000 022 recto', 'KMs 2000 023 recto', 'KMs 2000 024 recto', 'KMs 2000 025 recto', 'KMs 2000 026 recto', 'KMs 2000 027 recto', 'KMs 2000 028 recto', 'KMs 2000 029 recto', 'KMs 2000 030 recto', 'KMs 2000 031 recto', 'KMs 2000 032 recto', 'KMs 2000 033 recto', 'KMs 2000 034 recto', 'KMs 2000 035 recto', 'KMs 2000 036 recto', 'KMs 2000 037 recto', 'KMs 2000 038 recto', 'KMs 2000 039 recto', 'KMs 2000 040 recto', 'KMs 2000 041 recto', 'KMs 2000 042 recto', 'KMs 2000 043 recto', 'KMs 2000 044 recto', 'KMs 2000 045 recto', 'KMs 2000 046 recto', 'KMs 2000 047 recto', 'KMs 2000 048 recto', 'KMs 2000 049 recto', 'KMs 2000 050 recto', 'KMs 2000 051 recto', 'Kraanvogel recto', 'KS 001 verso recto', 'KS 001-16b recto', 'KS 003 verso recto', 'KS 004 verso recto', 'KS 006 verso recto', 'KS 007 verso recto', 'KS 008  verso recto', 'KS 008-16b recto', 'KS 008-2 recto', 'KS 009  verso recto', 'KS 011 verso recto', 'KS 013  verso recto', 'KS 014  verso recto', 'KS 014 100% recto', 'KS 015  verso recto', 'KS 015 100% recto', 'KS 016  verso recto', 'KS 016 100% recto', 'KS 017  verso recto', 'KS 019 verso recto', 'KS 020 verso recto', 'KS 021  verso recto', 'KS 022  verso recto', 'KS 023  verso recto', 'KS 028  verso recto', 'KS 029  verso recto', 'KS 030  verso recto', 'KS 032  verso recto', 'KS 034  verso recto', 'kS 035  verso recto', 'KS 037  verso recto', 'KS 038  verso recto', 'KS 038-16b recto', 'KS 039  verso recto', 'KS 039-16b recto', 'KS 041  verso recto', 'KS 044  verso recto', 'KS 044-16b recto', 'KS 045  verso recto', 'KS 045 100% recto', 'KS 046  verso recto', 'KS 047 100% recto', 'KS 047 verso recto', 'KS 048  verso recto', 'KS 048 100% recto', 'KS 049  verso recto', 'KS 049 100% recto', 'KS 051  verso recto', 'KS 052  verso recto', 'KS 062  verso recto', 'KS 064  verso recto', 'KS 065  verso recto', 'KS 066  verso recto', 'KS 067  verso recto', 'KS 067 100% recto', 'KS 067-schoon recto', 'KS 071  verso recto', 'KS 072  verso recto', 'KS 072-16b recto', 'KS 073  verso recto', 'KS 076  verso recto', 'KS 077  verso recto', 'KS 078  verso recto', 'KS 079  verso recto', 'KS 080  verso recto', 'KS 080 100% recto', 'KS 083  verso recto', 'KS 085-2 recto', 'KS 087  verso recto', 'KS 090  verso recto', 'KS 092  verso recto', 'KS 092-16b recto', 'KS 093  verso recto', 'KS 094  verso recto', 'KS 098  verso recto', 'KS 098-schoon recto', 'KS 105  verso recto', 'KS 106  verso recto', 'KS 106 100% recto', 'KS 109  verso recto', 'KS 111  verso recto', 'KS 112  verso recto', 'KS 113  verso recto', 'KS 114  verso recto', 'KS 115  verso recto', 'ks 116  verso recto', 'KS 117  verso recto', 'KS 118  verso recto', 'KS 121  verso recto', 'KS 124  verso recto', 'KS 126  verso recto', 'KS 126 100% recto', 'KS 128  verso recto', 'KS 129  verso recto', 'KS 130  verso recto', 'KS 131  verso recto', 'KS 132  verso recto', 'KS 133  veso recto', 'KS 135 lijst recto', 'KS 137  verso recto', 'KS 137_1 recto', 'KS 139  verso recto', 'KS 141  verso recto', 'KS 142  verso recto', 'KS 144  verso recto', 'KS 148 verso recto', 'KS 148-Scholten recto', 'KS 151  verso recto', 'KS 155  verso recto', 'KS 157  verso recto', 'KS 161  verso recto', 'KS 165  verso recto', 'KS 165-2 recto', 'KS 165-lijst recto', 'KS 169  verso recto', 'KS 174  verso recto', 'KS 180  verso recto', 'KS 194 verso recto', 'KS 195  verso recto', 'KS 1986 003  verso recto', 'KS 1987 002 verso recto', 'KS 1989 010_1 recto', 'KS 1989 014 recto', 'KS 1991 002  verso recto', 'KS 1991 002 100% recto', 'KS 1991 003 100% recto', 'Ks 1991 003 verso recto', 'KS 1992 001 100% recto', 'KS 1992 001 verso recto', 'KS 1994 001 verso recto', 'KS 1994 br 001 recto', 'KS 1994 br 004 verso recto', 'KS 1994 br 004 recto', 'KS 1996 001 verso recto', 'KS 1996 004 recto', 'KS 1997 01 recto', 'KS 1998 003v recto', 'KS 1999 004  verso recto', 'KS 1999 004 100% recto', 'KS 2000 007 verso recto', 'KS 2000 007-schoon recto', 'KS 2000 008 verso recto', 'KS 2001 001 recto', 'KS 2001 002 recto', 'KS 2001 003 recto', 'KS 2001 004 recto', 'KS 2001 005 recto', 'KS 2003 002 verso recto', 'KS 2004 001 verso recto', 'KS 2006 006 recto', 'KS 2006 br 001 recto', 'KS 2008 001-schoon recto', 'KS 2010 001  verso recto', 'KS 2010 002  verso recto', 'KS 2010 002 recto', 'KS 2011 001 verso recto', 'KS 2011 001_1 recto', 'KS 2012 001 lijst recto', 'KS 2012 001 recto', 'KS 2013 001 oud met lijst recto', 'KS 2013-001 met lijst recto', 'KS 2013-001 nieuw recto', 'KS 2014 001_02 recto', 'KS 2014 002_02 recto', 'KS 2014 004 recto', 'KS 2014 Br 01 lijst recto', 'KS 202  verso recto', 'KS 207  verso recto', 'KS 208  verso recto', 'KS 209 verso recto', 'KS 210 verso recto', 'KS 223  verso recto', 'KS 224  verso recto', 'KS 226  verso recto', 'KS 229  verso recto', 'KS 230 100% recto', 'KS 230 verso recto', 'KS 239  verso recto', 'KS 240  verso recto', 'KS 243-verso recto', 'KS 244  verso recto', 'KS 255 100% recto', 'KS 266 recto', 'KS 63 recto', 'KS geen nummer-02 recto', 'KS geen nummer recto', 'KS HesHuizen recto', 'KS Hulk recto', 'KS Springer recto', 'KSC 2006 Br recto', 'KT  2009 028-030 recto', 'KT 01423 recto', 'KT 01424 recto', 'KT 01436 recto', 'KT 01850 recto', 'KT 02217 recto', 'KT 02393 recto', 'KT 02522 recto', 'KT 02523 recto', 'KT 02524 recto', 'KT 02525 recto', 'KT 02526 recto', 'KT 02531 recto', 'KT 02533 recto', 'KT 02534 recto', 'KT 02535 recto', 'KT 02536 recto', 'KT 02537 recto', 'KT 02538 recto', 'KT 02543 recto', 'KT 02544 recto', 'KT 02545 recto', 'KT 02546 recto', 'KT 02547 recto', 'KT 02548 recto', 'KT 02549 recto', 'KT 02550 recto', 'KT 02551 recto', 'KT 02552 recto', 'KT 02553 recto', 'KT 02658 recto', 'KT 02659 recto', 'KT 02660 recto', 'KT 02819 recto', 'KT 02820 recto', 'KT 02821 recto', 'KT 02822 recto', 'KT 02823 recto', 'KT 02824 recto', 'KT 02825 recto', 'KT 02826 recto', 'KT 02827 recto', 'KT 02828 recto', 'KT 02829 recto', 'KT 02830 recto', 'KT 02831 recto', 'KT 02832 recto', 'KT 02833 recto', 'KT 02835 recto', 'KT 02836 recto', 'KT 02837 recto', 'KT 02838 recto', 'KT 02839 recto', 'KT 02840 recto', 'KT 02841 recto', 'KT 02842 recto', 'KT 02843 recto', 'KT 02844 recto', 'KT 02845 recto', 'KT 02846 recto', 'KT 02847 recto', 'KT 02848 recto', 'KT 02849 recto', 'KT 02850 recto', 'KT 02851 recto', 'KT 02852 recto', 'KT 02853 recto', 'KT 02854 recto', 'KT 02855 recto', 'KT 02856 recto', 'KT 02857 recto', 'KT 02858 recto', 'KT 02859 recto', 'KT 02860 recto', 'KT 02861 recto', 'KT 02862 recto', 'KT 02863 recto', 'KT 02864 recto', 'KT 02865 recto', 'KT 02866 recto', 'KT 02867 recto', 'KT 02868 recto', 'KT 02869 recto', 'KT 02870 recto', 'KT 02871 recto', 'KT 02872 recto', 'KT 02873 recto', 'KT 02874 recto', 'KT 02875 recto', 'KT 02876 recto', 'KT 02877 recto', 'KT 02878 recto', 'KT 02879 recto', 'KT 02880 recto', 'KT 02881 recto', 'KT 02882 recto', 'KT 02883 recto', 'KT 02884 recto', 'KT 02885 recto', 'KT 02886 recto', 'KT 02887 recto', 'KT 02888 recto', 'KT 02889 recto', 'KT 02890 recto', 'KT 02891 recto', 'KT 02892 recto', 'KT 02893 recto', 'KT 02894 recto', 'KT 02895 recto', 'KT 02896 recto', 'KT 02897 recto', 'KT 02898 recto', 'KT 02899 recto', 'KT 02900 recto', 'KT 02901 recto', 'KT 02902 recto', 'KT 02903 recto', 'KT 02904 recto', 'KT 02905 recto', 'KT 02906 recto', 'KT 02907 recto', 'KT 02908 recto', 'KT 02909 recto', 'KT 02910 recto', 'KT 02911 recto', 'KT 02912 recto', 'KT 02913 recto', 'KT 02914 recto', 'KT 02915 recto', 'KT 02916 recto', 'KT 02917 recto', 'KT 02918 recto', 'KT 02919 recto', 'KT 02920 recto', 'KT 02921 recto', 'KT 02922 recto', 'KT 02923 recto', 'KT 02924 recto', 'KT 02925 recto', 'KT 02926 recto', 'KT 02927 recto', 'KT 02928 recto', 'KT 02929 recto', 'KT 02930 recto', 'KT 02931 recto', 'KT 02932 recto', 'KT 02933 recto', 'KT 02934 recto', 'KT 02935 recto', 'KT 02936 recto', 'KT 02937 recto', 'KT 02938 recto', 'KT 02939 recto', 'KT 02940 recto', 'KT 02941 recto', 'KT 02942 recto', 'KT 02943 recto', 'KT 02944 recto', 'KT 02945 recto', 'KT 02946 recto', 'KT 02947 recto', 'KT 02948 recto', 'KT 02949 recto', 'KT 02950 recto', 'KT 02951 recto', 'KT 02952 019 recto', 'KT 02953 recto', 'KT 02954 recto', 'KT 02955 recto', 'KT 02956 recto', 'KT 02957 recto', 'KT 02958 recto', 'KT 02959 recto', 'KT 02960 recto', 'KT 02961 recto', 'KT 02962 recto', 'KT 02963 recto', 'KT 02964 recto', 'KT 02965 recto', 'KT 02966 recto', 'KT 02967 recto', 'KT 02968 recto', 'KT 02969 recto', 'KT 02970 recto', 'KT 02971 recto', 'KT 02972 recto', 'KT 02973 recto', 'KT 02974 recto', 'KT 02975 recto', 'KT 02976 recto', 'KT 02977 recto', 'KT 02978 recto', 'KT 02979 recto', 'KT 02980 recto', 'KT 02981 recto', 'KT 02982 recto', 'KT 02983 recto', 'KT 02984 recto', 'KT 02985 recto', 'KT 02986 recto', 'KT 02987 recto', 'KT 02988 recto', 'KT 02989 recto', 'KT 02990 recto', 'KT 02991 recto', 'KT 02992 recto', 'KT 02993 recto', 'KT 02994 recto', 'KT 02995 recto', 'KT 02996 recto', 'KT 02997 recto', 'KT 02998 recto', 'KT 02999 recto', 'KT 03000 recto', 'KT 03001 recto', 'KT 03002 recto', 'KT 03003 recto', 'KT 03004 recto', 'KT 03005 recto', 'KT 03006 recto', 'KT 03007 recto', 'KT 03008 recto', 'KT 03009 recto', 'KT 03010 recto', 'KT 03011 recto', 'KT 03012 recto', 'KT 03013 recto', 'KT 03014 recto', 'KT 03015 recto', 'KT 03016 recto', 'KT 03017 recto', 'KT 03018 recto', 'KT 03019 recto', 'KT 11465-2 recto', 'KT 1377a recto', 'KT 1386a verso recto', 'KT 1386a recto', 'KT 1405a recto', 'KT 1510-1511 recto', 'KT 1618 recto', 'KT 1853_1 recto', 'KT 1853_2 recto', 'KT 1877 recto', 'KT 1985 035 recto', 'KT 1985 125 recto', 'KT 1985 126 recto', 'KT 1986 037_03-04 recto', 'KT 1986 041_05 recto', 'KT 1986 041_06 recto', 'KT 1986 041_07 recto', 'KT 1986 041_08 recto', 'KT 1986 041_09 recto', 'KT 1986 C_SPRINGER_geen nummer_01 recto', 'KT 1986 C_SPRINGER_geen nummer_02 recto', 'KT 1986 C_SPRINGER_geen nummer_03 recto', 'KT 1986 C_SPRINGER_geen nummer_04 recto', 'KT 1986 C_SPRINGER_geen nummer_05 recto', 'KT 1986 C_SPRINGER_geen nummer_06 recto', 'KT 1986 C_SPRINGER_geen nummer_07 recto', 'KT 1986 C_SPRINGER_geen nummer_08 recto', 'KT 1986 C_SPRINGER_geen nummer_09 recto', 'KT 1986 C_SPRINGER_geen nummer_10 recto', 'KT 1986 C_SPRINGER_geen nummer_11 recto', 'KT 1986 C_SPRINGER_inhoud envelop recto', 'KT 1987 040 recto', 'KT 1988 008-01 recto', 'KT 1988 021 verso recto', 'KT 1989 045 recto', 'KT 1989 046 recto', 'KT 1989 047 recto', 'KT 1989 048 recto', 'KT 1989 061 recto', 'KT 1989 067 recto', 'KT 1989 077_001 recto', 'KT 1989 077_002 recto', 'KT 1989 077_003 recto', 'KT 1989 077_004 recto', 'KT 1989 077_005 recto', 'KT 1989 077_006 recto', 'KT 1989 077_007 recto', 'KT 1989 077_008 recto', 'KT 1989 077_009 recto', 'KT 1989 077_010 recto', 'KT 1989 077_011 recto', 'KT 1989 077_012 recto', 'KT 1989 077_013 recto', 'KT 1989 077_014 recto', 'KT 1989 077_015 recto', 'KT 1989 077_016 recto', 'KT 1989 077_017 recto', 'KT 1989 077_018 recto', 'KT 1989 077_019 recto', 'KT 1989 077_020 recto', 'KT 1989 077_021 recto', 'KT 1989 077_022 recto', 'KT 1989 077_023 recto', 'KT 1989 077_024 recto', 'KT 1989 083 verso recto', 'KT 1989 085-01 recto', 'KT 1989 085-02 recto', 'KT 1989 085-03 recto', 'KT 1989 086-01 recto', 'KT 1989 086-02 recto', 'KT 1989 088 verso recto', 'KT 1989 091-01 recto', 'KT 1989 091-02 recto', 'KT 1989 091-03 recto', 'KT 1989 091-04 recto', 'KT 1989 092-01 recto', 'KT 1989 092-02 recto', 'KT 1989 092-03 recto', 'KT 1989 096-01 recto', 'KT 1989 096-02 recto', 'KT 1989 096-03 recto', 'KT 1989 096-04 recto', 'KT 1989 112 recto', 'KT 1990 003 recto', 'KT 1990 004 recto', 'KT 1990 005 recto', 'KT 1990 006 recto', 'KT 1990 007 recto', 'KT 1990 008 recto', 'KT 1990 042a recto', 'KT 1990 042b recto', 'KT 1990 049 recto', 'KT 1990 050 recto', 'KT 1990 055 recto', 'KT 1990 056 recto', 'KT 1990 057 recto', 'KT 1990 058 recto', 'KT 1990 059 recto', 'KT 1990 060 recto', 'KT 1990 061 recto', 'KT 1990 062 recto', 'KT 1990 063 recto', 'KT 1990 064 recto', 'KT 1990 067 verso recto', 'KT 1990 105 recto', 'KT 1990 106 recto', 'KT 1990 135a recto', 'KT 1990 135v recto', 'KT 1990 139 recto', 'KT 1990 139_01 recto', 'KT 1990 139_02 recto', 'KT 1990 139_03 recto', 'KT 1990 139_04 recto', 'KT 1990 139_05 recto', 'KT 1990 139_06 recto', 'KT 1990 139_07 recto', 'KT 1990 139_08 recto', 'KT 1990 139_09 recto', 'KT 1990 139_10 recto', 'KT 1990 139_11 recto', 'KT 1990 139_12 recto', 'KT 1990 139_13 recto', 'KT 1990 140_01 recto', 'KT 1990 140_02 recto', 'KT 1990 140_03 recto', 'KT 1990 140_04 recto', 'KT 1990 140_05 recto', 'KT 1990 140_06 recto', 'KT 1990 140_07 recto', 'KT 1990 140_08 recto', 'KT 1990 140_09 recto', 'KT 1990 140_10 recto', 'KT 1990 140_11 recto', 'KT 1990 140_12 recto', 'KT 1990 140_13 recto', 'KT 1990 141_01 recto', 'KT 1990 141_02 recto', 'KT 1990 141_03 recto', 'KT 1990 141_04 recto', 'KT 1990 141_05 recto', 'KT 1990 141_06 recto', 'KT 1990 141_07 recto', 'KT 1990 141_08 recto', 'KT 1990 141_09 recto', 'KT 1990 141_10 recto', 'KT 1990 141_11 recto', 'KT 1990 141_12 recto', 'KT 1990 141_13 recto', 'KT 1990 141_14 recto', 'KT 1990 141_15 recto', 'KT 1990 141_16 recto', 'KT 1990 141_17 recto', 'KT 1990 141_18 recto', 'KT 1990 141_19 recto', 'KT 1990 141_20 recto', 'KT 1990 141_21 recto', 'KT 1990 141_22 recto', 'KT 1990 141_23 recto', 'KT 1990 141_24 recto', 'KT 1990 141_25 recto', 'KT 1990 141_26 recto', 'KT 1990 142_01 recto', 'KT 1990 142_02 recto', 'KT 1990 142_03 recto', 'KT 1990 142_04 recto', 'KT 1990 142_05 recto', 'KT 1990 142_06 recto', 'KT 1990 142_07 recto', 'KT 1990 142_08 recto', 'KT 1990 142_09 recto', 'KT 1990 143 verso recto', 'KT 1990 143 recto', 'KT 1990 144 verso recto', 'KT 1990 144 recto', 'KT 1990 145 verso recto', 'KT 1990 145 recto', 'KT 1990 146 verso recto', 'KT 1990 146 recto', 'KT 1990 147 verso recto', 'KT 1990 147 recto', 'KT 1990 148 verso recto', 'KT 1990 148 recto', 'KT 1990 149 verso recto', 'KT 1990 149 recto', 'KT 1990 150 verso recto', 'KT 1990 150 recto', 'KT 1990 151 verso recto', 'KT 1990 151 recto', 'KT 1990 152 verso recto', 'KT 1990 152 recto', 'KT 1990 153 verso recto', 'KT 1990 153 recto', 'KT 1990 154 verso recto', 'KT 1990 154 recto', 'KT 1990 155 verso recto', 'KT 1990 155 recto', 'KT 1990 156 verso recto', 'KT 1990 156 recto', 'KT 1990 157 verso recto', 'KT 1990 157 recto', 'KT 1990 158 recto', 'KT 1990 159 verso recto', 'KT 1990 159 recto', 'KT 1990 160 verso recto', 'KT 1990 160 recto', 'KT 1990 161 verso recto', 'KT 1990 161 recto', 'KT 1990 162 verso recto', 'KT 1990 162 recto', 'KT 1990 163 recto', 'KT 1990 164 verso recto', 'KT 1990 164 recto', 'KT 1990 165 verso recto', 'KT 1990 165 recto', 'KT 1990 166 verso recto', 'KT 1990 166 recto', 'KT 1990 167 verso recto', 'KT 1990 167 recto', 'KT 1990 168 verso recto', 'KT 1990 168 recto', 'KT 1990 169 verso recto', 'KT 1990 169 recto', 'KT 1990 170 verso recto', 'KT 1990 170 recto', 'KT 1990 171 verso recto', 'KT 1990 171 recto', 'KT 1990 172 verso recto', 'KT 1990 172 recto', 'KT 1990 173 verso recto', 'KT 1990 173 recto', 'KT 1990 174 verso recto', 'KT 1990 174 recto', 'KT 1990 175 verso recto', 'KT 1990 175 recto', 'KT 1990 176 verso recto', 'KT 1990 176 recto', 'KT 1990 177 verso recto', 'KT 1990 177 recto', 'KT 1990 178 verso recto', 'KT 1990 178 recto', 'KT 1990 179 verso recto', 'KT 1990 179 recto', 'KT 1990 180 verso recto', 'KT 1990 180 recto', 'KT 1990 181 verso recto', 'KT 1990 181 recto', 'KT 1990 182 verso recto', 'KT 1990 182 recto', 'KT 1990 183 verso recto', 'KT 1990 183 recto', 'KT 1990 184 verso recto', 'KT 1990 184 recto', 'KT 1990 185 verso recto', 'KT 1990 185 recto', 'KT 1990 186 verso recto', 'KT 1990 186 recto', 'KT 1990 187 verso recto', 'KT 1990 187 recto', 'KT 1990 188 verso recto', 'KT 1990 188 recto', 'KT 1990 189 recto', 'KT 1990 190 recto', 'KT 1990 191 recto', 'KT 1990 192 recto', 'KT 1990 193 recto', 'KT 1990 194 recto', 'KT 1990 195 recto', 'KT 1990 196 recto', 'KT 1990 197 recto', 'KT 1990 198 verso recto', 'KT 1990 198 recto', 'KT 1990 199 verso recto', 'KT 1990 199 recto', 'KT 1991  003 recto', 'KT 1991  004 recto', 'KT 1991  005 recto', 'KT 1991  006 recto', 'KT 1991  007 recto', 'KT 1991  008 recto', 'KT 1991  009 recto', 'KT 1991  010 recto', 'KT 1991  011 recto', 'KT 1991  012 recto', 'KT 1991  013 recto', 'KT 1991  014 recto', 'KT 1991  015 recto', 'KT 1991  016 recto', 'KT 1991  017 recto', 'KT 1991  018 recto', 'KT 1991  019 recto', 'KT 1991  020- recto', 'KT 1991  020 recto', 'KT 1991  022 recto', 'KT 1991  023 recto', 'KT 1991  024 recto', 'KT 1991  026 recto', 'KT 1991  027 recto', 'KT 1991  030 recto', 'KT 1991  031 recto', 'KT 1991  032 recto', 'KT 1991  033 recto', 'KT 1991  034 recto', 'KT 1991  035 recto', 'KT 1991  106 recto', 'KT 1991  129 recto', 'KT 1991  131 recto', 'KT 1991 133 recto', 'KT 1991 134 recto', 'KT 1991 135 recto', 'KT 1992 027 verso recto', 'KT 1992 031 recto', 'KT 1992 032 recto', 'KT 1992 033 recto', 'KT 1992 035 recto', 'KT 1992 036 recto', 'KT 1992 037 recto', 'KT 1992 038 recto', 'KT 1992 039 recto', 'KT 1992 040 recto', 'KT 1992 041 recto', 'KT 1992 042 recto', 'KT 1992 043 recto', 'KT 1992 044 recto', 'KT 1992 046 recto', 'KT 1992 047 recto', 'KT 1992 050 recto', 'KT 1992 051 recto', 'KT 1992 052 recto', 'KT 1992 054 recto', 'KT 1992 055 recto', 'KT 1992 057 recto', 'KT 1992 061 recto', 'KT 1992 062 recto', 'KT 1992 063 recto', 'KT 1992 064 recto', 'KT 1992 065 recto', 'KT 1992 066 recto', 'KT 1992 067 recto', 'KT 1992 068 recto', 'KT 1993 037 recto', 'KT 1993 039 recto', 'KT 1996 054-02 recto', 'KT 1996 078 recto', 'KT 1997  057 recto', 'KT 1997 013 recto', 'KT 1997 019 recto', 'KT 1997 021 recto', 'KT 1997 037-042 recto', 'KT 1997 058 recto', 'KT 1997 059 recto', 'KT 1997 060 recto', 'KT 1997 061 recto', 'KT 1997 062 recto', 'KT 1997 063 recto', 'KT 1997 064 recto', 'KT 1997 065 recto', 'KT 1997 066 recto', 'KT 1997 066_01 recto', 'KT 1997 067 recto', 'KT 1997 068 recto', 'KT 1997 068_01 recto', 'KT 1997 068_02 recto', 'KT 1997 069 recto', 'KT 1997 070 recto', 'KT 1997 071 recto', 'KT 1997 071_01 recto', 'KT 1997 071_02 recto', 'KT 1997 071_03 recto', 'KT 1997 071_04 recto', 'KT 1997 071_05 recto', 'KT 1998 024 recto', 'KT 1999 008a recto', 'KT 1999 034 recto', 'KT 1999 035 recto', 'KT 1999 036 recto', 'KT 1999 037 recto', 'KT 1999 038 recto', 'KT 1999 039 recto', 'KT 1999 041 recto', 'KT 1999 042 recto', 'KT 2000 034 recto', 'KT 2000 079 verso recto', 'KT 2000 097 recto', 'KT 2000 120 v recto', 'KT 2000 120 recto', 'KT 2000 121 v recto', 'KT 2000 121 recto', 'KT 2000 124 v recto', 'KT 2000 128 v recto', 'KT 2000 130 v recto', 'KT 2000 132 v recto', 'KT 2000 136 v recto', 'KT 2000 150 v recto', 'KT 2000 151 v recto', 'KT 2000 152_1 recto', 'KT 2000 153-2 recto', 'KT 2000 156 recto', 'KT 2000 br 002 recto', 'KT 2000 br 005 recto', 'KT 2000 br 006 recto', 'KT 2000 br 008 recto', 'KT 2000 br 009 recto', 'KT 2000 BR 010 recto', 'KT 2000 br 011 recto', 'KT 2000 br 012 recto', 'KT 2000 br 014 recto', 'KT 2000 br 016 recto', 'KT 2000 br 017 recto', 'KT 2000 br 018 recto', 'KT 2000 br 019 recto', 'KT 2000 br 021 recto', 'KT 2000 br 030 recto', 'KT 2000 br 040 recto', 'KT 2000 br 041 recto', 'KT 2000 br 042 recto', 'KT 2000 geen vervolgnummer recto', 'KT 2000 zn 002 recto', 'KT 2001 003 (11) recto', 'KT 2001 003 (20) recto', 'KT 2001 003 (7) recto', 'KT 2001 003 recto', 'KT 2001 003_01 recto', 'KT 2001 003_02 recto', 'KT 2001 003_03 recto', 'KT 2001 003_04 recto', 'KT 2001 003_05 recto', 'KT 2001 003_06 recto', 'KT 2001 003_08 recto', 'KT 2001 003_09 recto', 'KT 2001 003_10 recto', 'KT 2001 003_12 recto', 'KT 2001 003_13 recto', 'KT 2001 003_14 recto', 'KT 2001 003_15 recto', 'KT 2001 003_16 recto', 'KT 2001 003_17 recto', 'KT 2001 003_18 recto', 'KT 2001 003_19 recto', 'KT 2001 003_21 recto', 'KT 2001 003_22 recto', 'KT 2001 003_23 recto', 'KT 2001 003_24 recto', 'KT 2001 003_25 recto', 'KT 2001 003_26 recto', 'KT 2001 003_27 recto', 'KT 2001 003_28 recto', 'KT 2001 003_29 recto', 'KT 2001 003_30 recto', 'KT 2001 003_31 recto', 'KT 2001 003_32 recto', 'KT 2001 003_33 recto', 'KT 2001 003_34 recto', 'KT 2001 003_35 recto', 'KT 2001 003_36 recto', 'KT 2001 003_37 recto', 'KT 2001 003_38 recto', 'KT 2001 003_39 recto', 'KT 2001 003_40 recto', 'KT 2001 038 recto', 'KT 2001 100-01 recto', 'KT 2001 100-02 recto', 'KT 2001 100-03 recto', 'KT 2001 100-04 recto', 'KT 2001 100-05 recto', 'KT 2001 100-06 recto', 'KT 2001 100-07 recto', 'KT 2001 100-08 recto', 'KT 2001 100-09 recto', 'KT 2001 100-10 recto', 'KT 2001 100-11 recto', 'KT 2001 100-12 recto', 'KT 2001 100-13 recto', 'KT 2001 100-14 recto', 'KT 2001 100-15 recto', 'KT 2001 100-16 recto', 'KT 2001 100-17 recto', 'KT 2001 100-18 recto', 'KT 2001 100-19 recto', 'KT 2001 100-20 recto', 'KT 2001 100-21 recto', 'KT 2001 135 recto recto', 'KT 2001 135 verso recto', 'KT 2001 142-01 recto', 'KT 2001 142-02 recto', 'KT 2001 142-03 recto', 'KT 2001 142-04 recto', 'KT 2001 142-05 recto', 'KT 2001 142-06 recto', 'KT 2001 142-07 recto', 'KT 2001 142-08 recto', 'KT 2001 142-09 recto', 'KT 2001 142-10 recto', 'KT 2001 142-11 recto', 'KT 2001 142-12 recto', 'KT 2001 142-13 recto', 'KT 2001 142-14 recto', 'KT 2001 142-15 recto', 'KT 2001 144-01 recto', 'KT 2001 144-02 recto', 'KT 2001 144-03 recto', 'KT 2001 144-04 recto', 'KT 2001 144-05 recto', 'KT 2001 144-06 recto', 'KT 2001 144-07 recto', 'KT 2001 144-08 recto', 'KT 2001 144-09 recto', 'KT 2001 144-10 recto', 'KT 2001 144-11 recto', 'KT 2001 144-12 recto', 'KT 2001 144-13 recto', 'KT 2001 144-14 recto', 'KT 2001 144-15 recto', 'KT 2001 144-16 recto', 'KT 2001 144-17 recto', 'KT 2001 144-18 recto', 'KT 2001 144-19 recto', 'KT 2001 144-20 recto', 'KT 2001 144-21 recto', 'KT 2001 144-22 recto', 'KT 2001 144-23 recto', 'KT 2001 144-24 recto', 'KT 2001 144-25 recto', 'KT 2001 144-26 recto', 'KT 2001 144-27 recto', 'KT 2001 144-28 recto', 'KT 2001 144-29 recto', 'KT 2001 144-30 recto', 'KT 2001 144-31 recto', 'KT 2001 144-32 recto', 'KT 2001 144-33 recto', 'KT 2001 144-34 recto', 'KT 2001 144-35 recto', 'KT 2001 144-36 recto', 'KT 2001 144-37 recto', 'KT 2001 145-01 recto', 'KT 2001 145-02 recto', 'KT 2001 145-03 recto', 'KT 2001 145-04 recto', 'KT 2001 145-05 recto', 'KT 2001 145-06 recto', 'KT 2001 145-07 recto', 'KT 2001 145-08 recto', 'KT 2001 145-09 recto', 'KT 2001 145-10 recto', 'KT 2001 145-11 recto', 'KT 2001 145-12 recto', 'KT 2001 145-13 recto', 'KT 2001 145-14 recto', 'KT 2001 145-15 recto', 'KT 2001 145-16 recto', 'KT 2001 145-17 recto', 'KT 2001 145-18 recto', 'KT 2001 146 recto recto', 'KT 2001 146 verso recto', 'KT 2001 198a verso recto', 'KT 2001 198b verso recto', 'KT 2001 199a verso recto', 'KT 2001 266-01 recto', 'KT 2001 266-02 recto', 'KT 2001 266-03 recto', 'KT 2001 266-04 recto', 'KT 2001 266-05 recto', 'KT 2001 266-06 recto', 'KT 2001 266-07 recto', 'KT 2001 266-08 recto', 'KT 2001 266-09 recto', 'KT 2001 266-10 recto', 'KT 2001 266-11 recto', 'KT 2001 266-12 recto', 'KT 2001 br 004 recto', 'KT 2001-16-02-geen nummer-01 recto', 'KT 2001-16-02-geen nummer-02 recto', 'KT 2001-16-02-geen nummer-03 recto', 'KT 2001-16-02-geen nummer-04 recto', 'KT 2001-16-02-geen nummer-05 recto', 'KT 2001-16-02-geen nummer-06 recto recto', 'KT 2001-16-02-geen nummer-06 verso recto', 'KT 2001-16-02-geen nummer-07 recto', 'KT 2001-16-02-geen nummer-08 recto', 'KT 2001-16-02-geen nummer-09 recto', 'KT 2001-16-02-geen nummer-10 recto', 'KT 2001-16-02-geen nummer-11 recto', 'KT 2001-16-02-geen nummer-12 recto', 'KT 2003 013 recto', 'KT 2003 014 (1) recto', 'KT 2003 017 recto', 'KT 2003 077_01 recto', 'KT 2003_013-01_02 recto', 'KT 2003_013-03-04 recto', 'KT 2003_013-05-06 recto', 'KT 2003_013-07-08 recto', 'KT 2003_013-09-10 recto', 'KT 2003_013-11-12 recto', 'KT 2003_013-13-14 recto', 'KT 2003_013-15-16 recto', 'KT 2003_013-17-18 recto', 'KT 2003_013-19-20 recto', 'KT 2003_013-21-22 recto', 'KT 2003_013-23-24 recto', 'KT 2003_013-25-26 recto', 'KT 2003_013-27-28 recto', 'KT 2003_013-29-30 recto', 'KT 2003_013-31-32 recto', 'KT 2003_013-33-34 recto', 'KT 2003_013-35-36 recto', 'KT 2003_013-37-38 recto', 'KT 2003_013-39-40 recto', 'KT 2003_013-41-42 recto', 'KT 2004 059 verso recto', 'KT 2004 120 recto', 'KT 2004 121 recto', 'KT 2004 br 057 recto', 'KT 2005 010 verso recto', 'KT 2005 012 verso recto', 'KT 2005 014-01 recto', 'KT 2005 014-02 recto', 'KT 2005 014-03 recto', 'KT 2005 014-04 recto', 'KT 2005 014-05 recto', 'KT 2005 014-06 recto', 'KT 2005 014-07 recto', 'KT 2005 014-08 recto', 'KT 2005 014-09 recto', 'KT 2005 014-10 recto', 'KT 2005 014-11 recto', 'KT 2005 014-12 recto', 'KT 2005 014-13 recto', 'KT 2005 014-14 recto', 'KT 2005 014-15 recto', 'KT 2005 014-16 recto', 'KT 2005 014-17 recto', 'KT 2005 014-18 recto', 'KT 2005 014-19 recto', 'KT 2005 014-20 recto', 'KT 2005 014-21 recto', 'KT 2005 014-22 recto', 'KT 2005 014-23 recto', 'KT 2005 014-24 recto', 'KT 2005 014-25 recto', 'KT 2005 014-26 recto', 'KT 2005 014-27 recto', 'KT 2005 014-28 recto', 'KT 2005 014-29 recto', 'KT 2005 014-30 recto', 'KT 2005 014-31 recto', 'KT 2005 014-32 recto', 'KT 2005 014-33 recto', 'KT 2005 014-34 recto', 'KT 2005 014-35 recto', 'KT 2005 014-36 recto', 'KT 2005 014-37 recto', 'KT 2005 014-38 recto', 'KT 2005 014-39 recto', 'KT 2005 014-40 recto', 'KT 2005 014-41 recto', 'KT 2005 014-42 recto', 'KT 2005 014-43 recto', 'KT 2005 014-44 recto', 'KT 2005 023 recto', 'KT 2006 011 recto', 'KT 2006 021  verso recto', 'KT 2006 022  verso recto', 'KT 2006 023  verso recto', 'KT 2006 024  verso recto', 'KT 2006 025  verso recto', 'KT 2006 026  verso recto', 'KT 2006 028  verso recto', 'KT 2006 029  verso recto', 'KT 2006 033  verso recto', 'KT 2006 034  verso recto', 'KT 2006 034 recto', 'KT 2006 035  verso recto', 'KT 2006 037  verso recto', 'KT 2006 038  verso recto', 'KT 2006 039  verso recto', 'KT 2006 141  recto recto', 'KT 2006 160 verso recto', 'KT 2006 32 verso recto', 'KT 2007 028verso recto', 'KT 2007 034a recto', 'KT 2007 034b recto', 'KT 2007 049_02 recto', 'KT 2007 049_04 recto', 'KT 2007 049_05 recto', 'KT 2007 049_06 recto', 'KT 2007 049_07 recto', 'KT 2007 049_08 recto', 'KT 2007 049_09 recto', 'KT 2007 049_10 recto', 'KT 2007 049_11 recto', 'KT 2007 049_12 recto', 'KT 2007 049_13 recto', 'KT 2007 049_14 recto', 'KT 2007 049_15 recto', 'KT 2007 049_16 recto', 'KT 2007 054 recto', 'KT 2007 055 recto', 'KT 2007 056 recto', 'KT 2007 057 recto', 'KT 2007 058 recto', 'KT 2007 059 recto', 'KT 2007 060 recto', 'KT 2007 061 recto', 'KT 2007 076 recto', 'KT 2007 077 recto', 'KT 2007 078 recto', 'KT 2007_000 recto', 'KT 2008 020 verso recto', 'KT 2008 br002 recto', 'KT 2009 022 recto', 'KT 2009 028-04 recto', 'KT 2009 028-078-2 recto', 'KT 2009 028-143-1 recto', 'KT 2009 048 verso recto', 'KT 2009 049 verso recto', 'KT 2009 050 verso recto', 'KT 2009 051_002 recto', 'KT 2009 051_004 recto', 'KT 2009 051_005 recto', 'KT 2009 051_006 recto', 'KT 2009 051_007 recto', 'KT 2009 051_008 recto', 'KT 2009 051_009 recto', 'KT 2009 051_010 recto', 'KT 2009 051_011 recto', 'KT 2009 051_012 recto', 'KT 2009 056 recto', 'KT 2009 057 recto', 'KT 2009 058 recto', 'KT 2009 059 recto', 'KT 2009 060 recto', 'KT 2009 061 recto', 'KT 2009 062 recto', 'KT 2009 080_0000 recto', 'KT 2009 080_0001 recto', 'KT 2009 080_0002 recto', 'KT 2009 080_0003 recto', 'KT 2009 080_0004 recto', 'KT 2009 080_0005 recto', 'KT 2009 080_0006 recto', 'KT 2009 080_0007 recto', 'KT 2009 080_0008 recto', 'KT 2009 080_0009 recto', 'KT 2009 080_0010 recto', 'KT 2009 080_0011 recto', 'KT 2009 080_0012 recto', 'KT 2009 080_0013 recto', 'KT 2009 080_0014 recto', 'KT 2009 080_0015 recto', 'KT 2009 080_0016 recto', 'KT 2009 080_0017 recto', 'KT 2009 080_0018 recto', 'KT 2009 080_0019 recto', 'KT 2009 080_0020 recto', 'KT 2009 080_0021 recto', 'KT 2009 080_0022 recto', 'KT 2009 080_0023 recto', 'KT 2009 080_0024 recto', 'KT 2009 080_0025 recto', 'KT 2009 080_0026 recto', 'KT 2009 080_0027 recto', 'KT 2009 080_0028 recto', 'KT 2009 080_0029 recto', 'KT 2009 080_0030 recto', 'KT 2009 080_0031 recto', 'KT 2009 080_0032 recto', 'KT 2009 080_0033 recto', 'KT 2009 080_0034 recto', 'KT 2009 080_0035 recto', 'KT 2009 080_0036 recto', 'KT 2009 080_0037 recto', 'KT 2009 080_0038 recto', 'KT 2009 080_0039 recto', 'KT 2009 080_0040 recto', 'KT 2009 080_0041 recto', 'KT 2009_051_001 recto', 'KT 2009_051_003 recto', 'KT 2010 022 verso recto', 'KT 2010 061 recto', 'KT 2010 062 recto', 'KT 2010 265-01 recto', 'KT 2010 290 kopie recto', 'KT 2010 315-01 recto', 'KT 2011 001-02 recto', 'KT 2012 006 verso recto', 'KT 2012 037 recto', 'KT 2012 039 recto', 'KT 2013 001 recto', 'KT 2013 002 recto', 'KT 2013 003 recto', 'KT 2013 004 recto', 'KT 2013 064 recto', 'KT 2013 098 verso recto', 'KT 2014 030 recto', 'KT 2014 036 recto', 'KT 2014 037 recto', 'KT 2014 038 recto', 'KT 2097 recto', 'KT 2099 recto', 'KT 2100 recto', 'KT 2101 recto', 'KT 2102 recto', 'KT 2367 recto', 'KT 2369 recto', 'KT 2377 recto', 'KT 2378 recto', 'KT 2379 recto', 'KT 2386 recto', 'KT 2389 recto', 'KT 2405 recto', 'KT 2417 recto', 'KT 2418 recto', 'KT 2419 recto', 'KT 2420 recto', 'KT 2421 recto', 'KT 2422 recto', 'KT 2423 recto', 'KT 2424 recto', 'KT 2425 recto', 'KT 2426 recto', 'KT 2427 recto', 'KT 2428 recto', 'KT 2429 recto', 'KT 2430 recto', 'KT 2431 recto', 'KT 2432 recto', 'KT 2433 recto', 'KT 2434 recto', 'KT 2435 recto', 'KT 2436 recto', 'KT 2437 recto', 'KT 2438 recto', 'KT 2439 recto', 'KT 2440 recto', 'KT 2441 recto', 'KT 2563-2 recto', 'KT 2592_002 recto', 'KT 2613-2 recto', 'KT 2689 recto', 'KT 2690 recto', 'KT 2696_004 recto', 'KT 2704 recto', 'KT 2705 recto', 'KT 2706 recto', 'KT 2707 recto', 'KT 2708 recto', 'KT 2709 recto', 'KT 2710 recto', 'KT 2711 recto', 'KT 2712 recto', 'KT 2714 recto', 'KT 2715 recto', 'KT 2716 recto', 'KT 2717 recto', 'KT 2718 recto', 'KT 2719 recto', 'KT 2720 recto', 'KT 2729a recto', 'KT 2730a recto', 'KT 2731a recto', 'KT 2732a recto', 'KT 2733a recto', 'KT 2734a recto', 'KT 2735a recto', 'KT 2736a recto', 'KT 2739a recto', 'KT 2740a recto', 'KT 2741a recto', 'KT 2742a recto', 'KT 2743a recto', 'KT 2744a recto', 'KT 2745a recto', 'KT 2746a recto', 'KT 2747a recto', 'KT 2748a recto', 'KT 2749a recto', 'KT 2750a recto', 'KT 2751a recto', 'KT 2752a recto', 'KT 2753a recto', 'KT 2754a recto', 'KT 2755a recto', 'KT 2756a recto', 'KT 2757a recto', 'KT 2758a recto', 'KT 2759a recto', 'KT 2760a recto', 'KT 2761a recto', 'KT 2762a recto', 'KT 2763a recto', 'KT 2764a recto', 'KT 2765a recto', 'KT 2766a recto', 'KT 2767a recto', 'KT 2768a recto', 'KT 2769a recto', 'KT 2770a recto', 'KT 2771a recto', 'KT 2772a recto', 'KT 2773a recto', 'KT 2774a recto', 'KT 2775a recto', 'KT 2776a recto', 'KT 2777a recto', 'KT 2778a recto', 'KT 2779a recto', 'KT 2780a recto', 'KT 2781a recto', 'KT 2782a recto', 'KT 2783a recto', 'KT 2784a recto', 'KT 2785a recto', 'KT 2786a recto', 'KT 2787a recto', 'KT 2788a recto', 'KT 2789a recto', 'KT 2790a recto', 'KT 2791a recto', 'KT 2792a recto', 'KT 2793a recto', 'KT 2794a recto', 'KT 2795a recto', 'KT 2796a recto', 'KT 2797a recto', 'KT 3023-2 recto', 'KT ALLEEN KAFT recto', 'KT geen nummer_01 recto', 'KT geen nummer_02 recto', 'KT geen nummer_03 recto', 'KT geen nummer_04 recto', 'KT geen nummer_05 recto', 'KT geen nummer_06 recto', 'KT geen nummer_07 recto', 'KT geen nummer_08 recto', 'KT geen nummer_09 recto', 'KT zonder nummer recto', 'KT2009 19_02-0002 recto', 'KT2009 19_03-0003 recto', 'KT2009 19_04-0004 recto', 'KT2009 19_05-0005 recto', 'KT2009 19_06-0006 recto', 'KT2009 19_07-0007 recto', 'KT2009 19_08-0008 recto', 'KT2009 19_09-0009 recto', 'KT2009 19_10-0010 recto', 'KT2009 19_11-0011 recto', 'KT2009 19_12-0012 recto', 'KT2009 19_13-0013 recto', 'KT2009 19_14-0014 recto', 'KT2009 19_15-0015 recto', 'KT2009 19_16-0016 recto', 'KT2009 19_17-0017 recto', 'KT2009 19_18-0018 recto', 'KT2009 19_19-0019 recto', 'KT2009 19_20-0020 recto', 'KT2009 19_21-0021 recto', 'KT2009 19_22-0022 recto', 'KT2009 19_23-0023 recto', 'KT2009 19_24-0024 recto', 'KT2009 19_25-0025 recto', 'KT2009 19_26-0026 recto', 'KT2009 19_27-0027 recto', 'KT2009 19_28-0028 recto', 'KT2009 19_29-0029 recto', 'KT2009 19_30-0030 recto', 'KT2009 19_31-0031 recto', 'KT2009 19_32-0032 recto', 'KT2009 19_33-0033 recto', 'KT2009 19_34-0034 recto', 'KT2009 19_35-0035 recto', 'KT2009 19_36-0036 recto', 'KT2009 19_37-0037 recto', 'KT2009 19_38-0038 recto', 'KT2009 19_39-0039 recto', 'KT2009 19_40-0040 recto', 'KT2009 19_41-0041 recto', 'KT2009 19_42-0042 recto', 'KT2009 19_43-0043 recto', 'KT2009 19_44-0044 recto', 'KT2009 19_45-0045 recto', 'KT2009 19_46-0046 recto', 'KT2009 19_47-0047 recto', 'KT2009 19_48-0048 recto', 'KT2009 19_49-0049 recto', 'KT2009 19_50-0050 recto', 'KT2009 19_51-0051 recto', 'KV 1991 003 recto', 'L 001  verso recto', 'L 002  verso recto', 'L 003  verso recto', 'L 004  verso recto', 'L 005  verso recto', 'L 006  verso recto', 'L 008  verso recto', 'L 009  verso recto', 'L 010  verso recto', 'L 011  verso recto', 'L 012  verso recto', 'L 013  verso recto', 'L 014  verso recto', 'L 015  verso recto', 'L 016  verso recto', 'L 017  verso recto', 'L 018  verso recto', 'L 019  verso recto', 'L 020  verso recto', 'L 021  verso recto', 'L 022  verso recto', 'L 023  verso recto', 'L 024  verso recto', 'L 024a  verso recto', 'L 025  verso recto', 'L 026  verso recto', 'L 027  verso recto', 'L 028  verso recto', 'L 029  verso recto', 'L 030  verso recto', 'L 031  verso recto', 'L 032  verso recto', 'L 033  verso recto', 'L 034  verso recto', 'L 035  verso recto', 'L 036  verso recto', 'L 037  verso recto', 'L 038  verso recto', 'L 039  verso recto', 'L 040  verso recto', 'L 041  verso recto', 'L 042  verso recto', 'L 043  verso recto', 'L 044  verso recto', 'L 045  verso recto', 'L 046  verso recto', 'L 047  verso recto', 'L 048  verso recto', 'L 049  verso recto', 'L 050  verso recto', 'L 051  verso recto', 'L 052  verso recto', 'L 053  verso recto', 'L 053a  verso recto', 'L 054  verso recto', 'L 055  verso recto', 'L 056  verso recto', 'L 057  verso recto', 'L 057 recto', 'L 058  verso recto', 'L 059  verso recto', 'L 060  verso recto', 'L 061  verso recto', 'L 062  verso recto', 'L 063  verso recto', 'L 064  verso recto', 'L 065  verso recto', 'L 066  verso recto', 'L 067  verso recto', 'L 068  verso recto', 'L 069  verso recto', 'L 070  verso recto', 'L 071  verso recto', 'L 072  verso recto', 'L 073  verso recto', 'L 074  verso recto', 'L 075  verso recto', 'L 076  verso recto', 'L 077  verso recto', 'L 078  verso recto', 'L 078 verso recto', 'L 079  verso recto', 'L 080  verso recto', 'L 081  verso recto', 'L 082  verso recto', 'L 083  verso recto', 'L 083 recto', 'L 084  verso recto', 'L 085  verso recto', 'L 086  verso recto', 'L 087  verso recto', 'L 088  verso recto', 'L 089  verso recto', 'L 090  verso recto', 'L 091  verso recto', 'L 092  verso recto', 'L 093  verso recto', 'L 094  verso recto', 'L 095  verso recto', 'L 096  verso recto', 'L 100  verso recto', 'L 101  verso recto', 'L 102  verso recto', 'L 104 verso recto', 'Lade 106 Geen nummer 01 recto', 'Lade 106 Geen nummer 02 recto', 'Lade 106 Geen nummer 03 recto', 'Lade 106 Geen nummer 04 recto', 'Lade 106 Geen nummer 05 recto', 'Lade 106 Geen nummer 06 recto', 'Lade 106 Geen nummer 07 recto', 'Lade 106 Geen nummer 08 recto', 'Lade 106 Geen nummer 09 recto', 'Lade 106 Geen nummer 10 recto', 'Lade 106 Geen nummer 11 recto', 'Lade 106 Geen nummer 12 recto', 'Lade 106 Geen nummer 13 recto', 'Lade 106 Geen nummer 14 recto', 'Lade 106 Geen nummer 15 recto', 'Lade 106 Geen nummer 16 recto', 'Lade 106 Geen nummer 17 recto', 'Lade 106 Geen nummer 18 recto', 'Lade 106 Geen nummer 19 recto', 'Lade 106 Geen nummer 20 recto', 'Lade 107 Reproductie 01 recto', 'Lade 107 Reproductie 02 recto', 'M 004 recto', 'M 006a recto', 'M 015 verso recto', 'M 042a recto', 'MAP JONGKIND verso recto', 'MAP JONGKIND recto', 'MAP verso recto', 'MAP recto', 'MAP_01 verso recto', 'MAP_01 recto', 'MAPJE verso recto', 'MAPJE recto', 'Marinus Fuit ZN 11-2013 recto', 'N 008c recto', 'N 008d recto', 'N 051 HighRes recto', 'N 054_1 recto', 'N 054_10 recto', 'N 054_11 recto', 'N 054_12 recto', 'N 054_13 recto', 'N 054_14 recto', 'N 054_15 recto', 'N 054_16 recto', 'N 054_17 recto', 'N 054_18 recto', 'N 054_19 recto', 'N 054_2 recto', 'N 054_20 recto', 'N 054_21 recto', 'N 054_22 recto', 'N 054_23 recto', 'N 054_24 recto', 'N 054_3 recto', 'N 054_4 recto', 'N 054_5 recto', 'N 054_6 recto', 'N 054_7 recto', 'N 054_8 recto', 'N 054_9 recto', 'N 076 verso recto', 'N 080-02(groor) recto', 'N 084 verso recto', 'N 085 verso recto', 'N 086 verso recto', 'N 087 verso recto', 'N 092 verso recto', 'N 093 verso recto', 'NC 946 recto', 'NI recto', 'NN 000 recto', 'NN 0000 recto', 'NN 00000-0 recto', 'NN 010 recto', 'NN 011 recto', 'NN 012 recto', 'NN 05 recto', 'NN_01 recto', 'NN_02 recto', 'NN_03 recto', 'NN_04 recto', 'NN_05 recto', 'NN_08 recto', 'NOOD 086 recto', 'NOTA 001 recto', 'NOTA 002 recto', 'O 049 recto', 'O 052c recto', 'O 055 verso recto', 'O 072 recto', 'O 073 recto', 'O+ 008-2 recto', 'O+ 012 recto', 'O+ 013 recto', 'O+ 014 recto', 'O+ 048-max recto', 'O+ 052 recto', 'O+ 070 verso recto', 'OMSLAG verso recto', 'OMSLAG recto', 'P 003a recto', 'P 004a recto', 'P 08a recto', 'P+ 001 recto', 'P+ 053-2 recto', 'P+ 061 recto recto', 'P+ 061 verso recto', 'P+ 070 recto', 'PDF recto', 'PP  Zonder nummer verso 91 recto', 'PP 0005 recto', 'PP 00059 recto', 'PP 0008 recto', 'PP 0011 recto', 'PP 0014 recto', 'PP 0016 recto', 'PP 00173 recto', 'PP 00203 recto', 'PP 00207 recto', 'PP 0032 recto', 'PP 0045 recto', 'PP 0047 1 recto', 'PP 0047 recto', 'PP 00506 recto', 'PP 0052 recto', 'PP 00525 recto', 'PP 00642 recto', 'PP 00684 recto', 'PP 0068a 1 recto', 'PP 0072 recto', 'PP 0074 recto', 'PP 0082 verso recto', 'PP 0083bb recto', 'PP 0094 recto', 'PP 00943 recto', 'PP 0101a recto', 'PP 0104b recto', 'PP 0106 recto', 'PP 0107a recto', 'PP 0108 recto', 'PP 0109 recto', 'PP 0116 recto', 'PP 01255 recto', 'PP 0127a recto', 'PP 0127b recto', 'PP 0128 recto', 'PP 0128a recto', 'PP 0134 recto', 'PP 0145 recto', 'PP 0145a recto', 'PP 0145b recto', 'PP 0146 recto', 'PP 0189 recto', 'PP 0200a recto', 'PP 0200b recto', 'PP 0211b recto', 'PP 0244a recto', 'PP 0252 dubbel nummer___ recto', 'PP 0254a 01 recto', 'PP 0254a 02 recto', 'PP 0254a 03 recto', 'PP 0254a 04 recto', 'PP 0254a 05 recto', 'PP 0254a 06 recto', 'PP 0254a 07 recto', 'PP 0254a 08 recto', 'PP 0254a recto', 'PP 0254b recto', 'PP 0262 recto', 'PP 0263a 01 recto', 'PP 0263a recto', 'PP 0263b recto', 'PP 0263c recto', 'PP 0264a recto', 'PP 0264b recto', 'PP 0265 recto', 'PP 0266 recto', 'PP 0267 recto', 'PP 0269 recto', 'PP 0270 recto', 'PP 0271 recto', 'PP 0272 recto', 'PP 0273 recto', 'PP 0274a recto', 'PP 0274b recto', 'PP 0275 recto', 'PP 0276 recto', 'PP 0277 recto', 'PP 0278 recto', 'PP 0279 recto', 'PP 0280 recto', 'PP 0281 recto', 'PP 0282 recto', 'PP 0282a recto', 'PP 0282b recto', 'PP 0283 recto', 'PP 0284 recto', 'PP 0285a recto', 'PP 0286 recto', 'PP 0287a recto', 'PP 0288 recto', 'PP 0289a recto', 'PP 0289b recto', 'PP 0291 dubbel nummer___ recto', 'PP 0291 recto', 'PP 0292 recto', 'PP 0293 recto', 'PP 0294 recto', 'PP 0295 01 recto', 'PP 0295 02 recto', 'PP 0295 03 recto', 'PP 0295 04 recto', 'PP 0295 05 recto', 'PP 0295 recto', 'PP 0296 recto', 'PP 0297 recto', 'PP 0298 recto', 'PP 0299 recto', 'PP 0300 recto', 'PP 0301 recto', 'PP 0302 recto', 'PP 0303 recto', 'PP 0304 recto', 'PP 0305 recto', 'PP 0306a recto', 'PP 0306b recto', 'PP 0307 recto', 'PP 0308 recto', 'PP 0309 recto', 'PP 0310 recto', 'PP 0311 01 recto', 'PP 0311 02 recto', 'PP 0311 recto', 'PP 0312 recto', 'PP 0313a recto', 'PP 0313b recto', 'PP 0314 recto', 'PP 0315 recto', 'PP 0316 recto', 'PP 0317 recto', 'PP 0318 recto', 'PP 0319 recto', 'PP 0320a recto', 'PP 0320b recto', 'PP 0321 recto', 'PP 0322a recto', 'PP 0322b recto', 'PP 0323 recto', 'PP 0324 recto', 'PP 0325 recto', 'PP 0326 recto', 'PP 0327 recto', 'PP 0328 recto', 'PP 0329 recto', 'PP 0330 recto', 'PP 0331 recto', 'PP 0332 recto', 'PP 0333 recto', 'PP 0334 recto', 'PP 0335 recto', 'PP 0336 recto', 'PP 0337 recto', 'PP 0338 recto', 'PP 0339a recto', 'PP 0339b recto', 'PP 0339c recto', 'PP 0340 recto', 'PP 0341 recto', 'PP 0342 recto', 'PP 0343 recto', 'PP 0344 recto', 'PP 0344b recto', 'PP 0345 recto', 'PP 0347 recto', 'PP 0348 recto', 'PP 0349 recto', 'PP 0350 recto', 'PP 0351 recto', 'PP 0352 recto', 'PP 0353 recto', 'PP 0354 recto', 'PP 0355a recto', 'PP 0355b recto', 'PP 0355c recto', 'PP 0358 recto', 'PP 0359 recto', 'PP 0360a recto', 'PP 0360b recto', 'PP 0361a dubbel nummer recto', 'PP 0361a recto', 'PP 0361b dubbel nummer recto', 'PP 0361b recto', 'PP 0362 dubbel nummer recto', 'PP 0362 recto', 'PP 0363a recto', 'PP 0363b recto', 'PP 0364 recto', 'PP 0365 recto', 'PP 0366 recto', 'PP 0367a recto', 'PP 0367b recto', 'PP 0368a recto', 'PP 0368b recto', 'PP 0369 recto', 'PP 0370a recto', 'PP 0370b recto', 'PP 0371 recto', 'PP 0372 recto', 'PP 0373a recto', 'PP 0373b recto', 'PP 0374 recto', 'PP 0375 recto', 'PP 0376 recto', 'PP 0377 recto', 'PP 0378 recto', 'PP 0380 recto', 'PP 0381 recto', 'PP 0382 recto', 'PP 0383 recto', 'PP 0384 recto', 'PP 0385 recto', 'PP 0388 recto', 'PP 0390 recto', 'PP 0391 recto', 'PP 0392 recto', 'PP 0393 recto', 'PP 0394 recto', 'PP 0395 recto', 'PP 0396 recto', 'PP 0397 recto', 'PP 0398 recto', 'PP 0399 recto', 'PP 0400 recto', 'PP 0401 recto', 'PP 0402 recto', 'PP 0403 recto', 'PP 0404 recto', 'PP 0405 recto', 'PP 0407 recto', 'PP 0408 recto', 'PP 0409 dubbel nummer recto', 'PP 0409 recto', 'PP 0410 recto', 'PP 0411 dubbel nummer recto', 'PP 0411 recto', 'PP 0412 recto', 'PP 0413a recto', 'PP 0414 recto', 'PP 0414a recto', 'PP 0415 recto', 'PP 0416 recto', 'PP 0417 recto', 'PP 0418 recto', 'PP 0418a recto', 'PP 0418b recto', 'PP 0419 recto', 'PP 0420 recto', 'PP 0422 recto', 'PP 0423 recto', 'PP 0424 recto', 'PP 0426 recto', 'PP 0430 recto', 'PP 0431a recto', 'PP 0431b recto', 'PP 0431c recto', 'PP 0432 recto', 'PP 0433 recto', 'PP 0434 recto', 'PP 0435 recto', 'PP 0436a recto', 'PP 0436b recto', 'PP 0437 recto', 'PP 0438 recto', 'PP 0439 recto', 'PP 0440a recto', 'PP 0441 recto', 'PP 0442 recto', 'PP 0443 recto', 'PP 0444 recto', 'PP 0445 recto', 'PP 0446 recto', 'PP 0447 recto', 'PP 0448 recto', 'PP 0449 recto', 'PP 0450 recto', 'PP 0451 recto', 'PP 0453 recto', 'PP 0455 recto', 'PP 0456 recto', 'PP 0457a recto', 'PP 0458 recto', 'PP 0459 recto', 'PP 0460 recto', 'PP 0461 recto', 'PP 0462 recto', 'PP 0463 recto', 'PP 0464 recto', 'PP 0465 recto', 'PP 0466 recto', 'PP 0467a recto', 'PP 0467b recto', 'PP 0469a recto', 'PP 0469b recto', 'PP 0470a recto', 'PP 0470b recto', 'PP 0472 recto', 'PP 0473 recto', 'PP 0474 recto', 'PP 0474a recto', 'PP 0475a recto', 'PP 0475b recto', 'PP 0476 recto', 'PP 0477 recto', 'PP 0478 recto', 'PP 0479a-b recto', 'PP 0479a recto', 'PP 0480a recto', 'PP 0481 recto', 'PP 0482 recto', 'PP 0484a recto', 'PP 0484b recto', 'PP 0485 recto', 'PP 0487 recto', 'PP 0488 recto', 'PP 0489 recto', 'PP 0490 recto', 'PP 0491 recto', 'PP 0492 recto', 'PP 0493 recto', 'PP 0494 recto', 'PP 0495 recto', 'PP 0496 recto', 'PP 0497 recto', 'PP 0498 recto', 'PP 0500 dubbel nummer recto', 'PP 0500 recto', 'PP 0501a recto', 'PP 0501b recto', 'PP 0503a recto', 'PP 0503b recto', 'PP 0504 recto', 'PP 0505 recto', 'PP 0507 recto', 'PP 0508 recto', 'PP 0509 dubbel nummer recto', 'PP 0509 recto', 'PP 0510 recto', 'PP 0512 recto', 'PP 0514 recto', 'PP 0518 recto', 'PP 0519a recto', 'PP 0519b recto', 'PP 0520a recto', 'PP 0520b recto', 'PP 0521 recto', 'PP 0522 recto', 'PP 0523 recto', 'PP 0524 recto', 'PP 0526 recto', 'PP 0527 recto', 'PP 0528 recto', 'PP 0529 recto', 'PP 0530 recto', 'PP 0531a recto', 'PP 0531b recto', 'PP 0532 recto', 'PP 0533 recto', 'PP 0534a recto', 'PP 0534b recto', 'PP 0535 recto', 'PP 0537 recto', 'PP 0538 recto', 'PP 0539 recto', 'PP 0540 recto', 'PP 0541 recto', 'PP 0542 recto', 'PP 0543 recto', 'PP 0544 recto', 'PP 0545 recto', 'PP 0546 recto', 'PP 0547 recto', 'PP 0548 recto', 'PP 0549 recto', 'PP 0550 recto', 'PP 0551 recto', 'PP 0552 recto', 'PP 0553 recto', 'PP 0554 recto', 'PP 0555a recto', 'PP 0556a recto', 'PP 0556b recto', 'PP 0557 recto', 'PP 0558 recto', 'PP 0559 recto', 'PP 0560 recto', 'PP 0561 recto', 'PP 0564 recto', 'PP 0565 recto', 'PP 0566 recto', 'PP 0567 recto', 'PP 0568 recto', 'PP 0569 recto', 'PP 0570 recto', 'PP 0571 recto', 'PP 0572 recto', 'PP 0574 recto', 'PP 0575a recto', 'PP 0575b recto', 'PP 0576a recto', 'PP 0576b recto', 'PP 0578 recto', 'PP 0579 recto', 'PP 0582 recto', 'PP 0583 recto', 'PP 0584 recto', 'PP 0585 recto', 'PP 0587 recto', 'PP 0588 recto', 'PP 0589 recto', 'PP 0590 recto', 'PP 0591 recto', 'PP 0591a recto', 'PP 0591b recto', 'PP 0592 recto', 'PP 0593 recto', 'PP 0594 recto', 'PP 0595 recto', 'PP 0596 recto', 'PP 0597 recto', 'PP 0598 recto', 'PP 0599 recto', 'PP 0600 recto', 'PP 0601 recto', 'PP 0602 recto', 'PP 0603 recto', 'PP 0604 recto', 'PP 0606 recto', 'PP 0607 recto', 'PP 0608 recto', 'PP 0609 recto', 'PP 0610 recto', 'PP 0611 recto', 'PP 0612 recto', 'PP 0613 recto', 'PP 0616 recto', 'PP 0617 recto', 'PP 0618 recto', 'PP 0619a recto', 'PP 0619b recto', 'PP 0620 recto', 'PP 0621 recto', 'PP 0622 recto', 'PP 0624 recto', 'PP 0625a recto', 'PP 0625b recto', 'PP 0626 recto', 'PP 0627 recto', 'PP 0628 recto', 'PP 0629 recto', 'PP 0630 recto', 'PP 0631 recto', 'PP 0632 recto', 'PP 0633 recto', 'PP 0634 recto', 'PP 0635 recto', 'PP 0636 recto', 'PP 0637 recto', 'PP 0638 recto', 'PP 0640 recto', 'PP 0641 recto', 'PP 0643 recto', 'PP 0644 recto', 'PP 0646 recto', 'PP 0647 recto', 'PP 0648 recto', 'PP 0649a recto', 'PP 0650b recto', 'PP 0651 recto', 'PP 0652 recto', 'PP 0653 recto', 'PP 0655 recto', 'PP 0655b recto', 'PP 0656 recto', 'PP 0657 recto', 'PP 0658 recto', 'PP 0659 recto', 'PP 0660 recto', 'PP 0663 recto', 'PP 0664a recto', 'PP 0664b recto', 'PP 0665a recto', 'PP 0666 recto', 'PP 0667 recto', 'PP 0668 recto', 'PP 0669 recto', 'PP 0670 recto', 'PP 0671 recto', 'PP 0672 recto', 'PP 0673 recto', 'PP 0674 recto', 'PP 0675 recto', 'PP 0676 recto', 'PP 0677 recto', 'PP 0678 kopie recto', 'PP 0679 recto', 'PP 0680 recto', 'PP 0681a recto', 'PP 0681b recto', 'PP 0681c recto', 'PP 0682 recto', 'PP 0685 recto', 'PP 0686 recto', 'PP 0687 recto', 'PP 0688a recto', 'PP 0688b recto', 'PP 0689 recto', 'PP 0691 recto', 'PP 0692 recto', 'PP 0693 verso recto', 'PP 0693 recto', 'PP 0694a recto', 'PP 0694b recto', 'PP 0696 recto', 'PP 0697 recto', 'PP 0698 recto', 'PP 0699 recto', 'PP 0701b recto', 'PP 0703 recto', 'PP 0704 recto', 'PP 0707 recto', 'PP 0708a recto', 'PP 0708b recto', 'PP 0709 recto', 'PP 0710 recto', 'PP 0711 recto', 'PP 0712a recto', 'PP 0712b recto', 'PP 0714 recto', 'PP 0715 recto', 'PP 0716a recto', 'PP 0716b recto', 'PP 0717-01 recto', 'PP 0717-02 recto', 'PP 0717-03 recto', 'PP 0717-04 recto', 'PP 0717 recto', 'PP 0718 recto', 'PP 0719 recto', 'PP 0720 recto', 'PP 0721 recto', 'PP 0722 recto', 'PP 0724 recto', 'PP 0725 recto', 'PP 0726 recto', 'PP 0727 recto', 'PP 0728a recto', 'PP 0728b recto', 'PP 0729 recto', 'PP 0730 recto', 'PP 0730a recto', 'PP 0731 recto', 'PP 0732 recto', 'PP 0733 recto', 'PP 0734 recto', 'PP 0735 recto', 'PP 0736 recto', 'PP 0737 recto', 'PP 0738 recto', 'PP 0739 recto', 'PP 0741 recto', 'PP 0742 recto', 'PP 0743 recto', 'PP 0744a recto', 'PP 0744b recto', 'PP 0745 recto', 'PP 0746 recto', 'PP 0747a recto', 'PP 0747b recto', 'PP 0749 recto', 'PP 0750 recto', 'PP 0751 recto', 'PP 0752 recto', 'PP 0753 recto', 'PP 0754 recto', 'PP 0755 recto', 'PP 0756 recto', 'PP 0757 recto', 'PP 0758 recto', 'PP 0760a recto', 'PP 0760b recto', 'PP 0761 recto', 'PP 0762 recto', 'PP 0763 recto', 'PP 0764 recto', 'PP 0765a recto', 'PP 0765b recto', 'PP 0766 recto', 'PP 0768a recto', 'PP 0768b recto', 'PP 0770 recto', 'PP 0771 recto', 'PP 0772 recto', 'PP 0773 verso recto', 'PP 0773 recto', 'PP 0774 recto', 'PP 0775 recto', 'PP 0776 verso recto', 'PP 0776 recto', 'PP 0777 recto', 'PP 0778 recto', 'PP 0779 recto', 'PP 0781a recto', 'PP 0781b recto', 'PP 0782 recto', 'PP 0783 recto', 'PP 0785a recto', 'PP 0785b recto', 'PP 0785c recto', 'PP 0786 recto', 'PP 0787 recto', 'PP 0788 recto', 'PP 0789 recto', 'PP 0791a recto', 'PP 0791b recto', 'PP 0792 recto', 'PP 0793 recto', 'PP 0794 recto', 'PP 0795 recto', 'PP 0796 recto', 'PP 0797a recto', 'PP 0797b recto', 'PP 0798 recto', 'PP 0799a recto', 'PP 0799b recto', 'PP 0800 recto', 'PP 0801 recto', 'PP 0802 recto', 'PP 0804 recto', 'PP 0805 recto', 'PP 0806 recto', 'PP 0807a recto', 'PP 0807b recto', 'PP 0808 recto', 'PP 0808a recto', 'PP 0809 recto', 'PP 0810 recto', 'PP 0811 recto', 'PP 0812 recto', 'PP 0813 recto', 'PP 0814 recto', 'PP 0815 recto', 'PP 0816 recto', 'PP 0817 recto', 'PP 0818 recto', 'PP 0819 recto', 'PP 0820 recto', 'PP 0821 recto', 'PP 0822 recto', 'PP 0824 recto', 'PP 0825 recto', 'PP 0826 recto', 'PP 0827 recto', 'PP 0828 recto', 'PP 0829 recto', 'PP 0830 recto', 'PP 0831 recto', 'PP 0832 recto', 'PP 0833 recto', 'PP 0834 recto', 'PP 0835 recto', 'PP 0837 recto', 'PP 0838 recto', 'PP 0839a recto', 'PP 0839b recto', 'PP 0840a recto', 'PP 0840b recto', 'PP 0841 recto', 'PP 0842 recto', 'PP 0843 recto', 'PP 0844 recto', 'PP 0845+ recto', 'PP 0845a recto', 'PP 0845b recto', 'PP 0846 recto', 'PP 0847 recto', 'PP 0848 recto', 'PP 0849 recto', 'PP 0850 recto', 'PP 0851 recto', 'PP 0851a recto', 'PP 0852 recto', 'PP 0853 recto', 'PP 0854 recto', 'PP 0855 recto', 'PP 0856a recto', 'PP 0856b recto', 'PP 0857 recto', 'PP 0858 recto', 'PP 0859 recto', 'PP 0860 recto', 'PP 0861 recto', 'PP 0863 recto', 'PP 0864a recto', 'PP 0864b recto', 'PP 0865a recto', 'PP 0865b recto', 'PP 0866a recto', 'PP 0866b recto', 'PP 0867 recto', 'PP 0868 recto', 'PP 0869 recto', 'PP 0871a recto', 'PP 0871b recto', 'PP 0873 recto', 'PP 0875a recto', 'PP 0875b recto', 'PP 0876a recto', 'PP 0876b recto', 'PP 0877 recto', 'PP 0878 recto', 'PP 0879 recto', 'PP 0880 recto', 'PP 0881 recto', 'PP 0882 recto', 'PP 0883 recto', 'PP 0884 recto', 'PP 0885 recto', 'PP 0886 recto', 'PP 0887 recto', 'PP 0888 recto', 'PP 0889 recto', 'PP 0890 recto', 'PP 0891 recto', 'PP 0893 recto', 'PP 0894 recto', 'PP 0895 recto', 'PP 0896 recto', 'PP 0896a recto', 'PP 0896b recto', 'PP 0897 recto', 'PP 0900 recto', 'PP 0901 recto', 'PP 0902 recto', 'PP 0903a recto', 'PP 0903b recto', 'PP 0904 recto', 'PP 0905 recto', 'PP 0906 recto', 'PP 0907 recto', 'PP 0908 recto', 'PP 0909a recto', 'PP 0910a recto', 'PP 0910b recto', 'PP 0911 recto', 'PP 0911a recto', 'PP 0912 recto', 'PP 0913 recto', 'PP 0914a recto', 'PP 0914b recto', 'PP 0915a recto', 'PP 0916 recto', 'PP 0917 recto', 'PP 0918 recto', 'PP 0919 recto', 'PP 0920 recto', 'PP 0921a recto', 'PP 0921b recto', 'PP 0922 recto', 'PP 0923 recto', 'PP 0924 recto', 'PP 0924a recto', 'PP 0925a recto', 'PP 0925b recto', 'PP 0926 recto', 'PP 0927 recto', 'PP 0928 recto', 'PP 0929 recto', 'PP 0930 recto', 'PP 0931 recto', 'PP 0932 recto', 'PP 0933 recto', 'PP 0934 recto', 'PP 0936 recto', 'PP 0937 recto', 'PP 0939 recto', 'PP 0939a recto', 'PP 0939b recto', 'PP 0940 recto', 'PP 0945 recto', 'PP 0946 recto', 'PP 0948 recto', 'PP 0949 recto', 'PP 0950 recto', 'PP 0951 recto', 'PP 0952 recto', 'PP 0953 recto', 'PP 0954 recto', 'PP 0956 recto', 'PP 0957 recto', 'PP 0958 recto', 'PP 0959 recto', 'PP 0960 recto', 'PP 0960a recto', 'PP 0960b recto', 'PP 0960c recto', 'PP 0960d recto', 'PP 0961 recto', 'PP 0962 recto', 'PP 0963 recto', 'PP 0964 recto', 'PP 0965 recto', 'PP 0966 recto', 'PP 0967 recto', 'PP 0968 recto', 'PP 0969a recto', 'PP 0969b recto', 'PP 0970 recto', 'PP 0971 recto', 'PP 0972 recto', 'PP 0973 recto', 'PP 0974a recto', 'PP 0974b recto', 'PP 0975 recto', 'PP 0976a recto', 'PP 0976b recto', 'PP 0977 recto', 'PP 0978 recto', 'PP 0979 recto', 'PP 0980 recto', 'PP 0981 recto', 'PP 0982 recto', 'PP 0985 recto', 'PP 0986 recto', 'PP 0987a recto', 'PP 0987b recto', 'PP 0988 recto', 'PP 0989 recto', 'PP 0991a recto', 'PP 0991b recto', 'PP 0992 recto', 'PP 0993 recto', 'PP 0994 recto', 'PP 0995 recto', 'PP 0996 recto', 'PP 0996a recto', 'PP 0997 recto', 'PP 0998 recto', 'PP 0999 recto', 'PP 1000 recto', 'PP 1001 recto', 'PP 1002 recto', 'PP 1003 recto', 'PP 1004 recto', 'PP 1006 recto', 'PP 1009 recto', 'PP 1010 recto', 'PP 1011 recto', 'PP 1012 recto', 'PP 1013 recto', 'PP 1014a recto', 'PP 1014b recto', 'PP 1015a recto', 'PP 1015b recto', 'PP 1016 recto', 'PP 1017 recto', 'PP 1018 recto', 'PP 1019 recto', 'PP 1020 recto', 'PP 1021 recto', 'PP 1022 recto', 'PP 1023a recto', 'PP 1023b recto', 'PP 1024 recto', 'PP 1025 recto', 'PP 1026 verso recto', 'PP 1026 recto', 'PP 1027 recto', 'PP 1028 recto', 'PP 1029 recto', 'PP 1030 recto', 'PP 1031 recto', 'PP 1032a recto', 'PP 1032b recto', 'PP 1033 recto', 'PP 1034a recto', 'PP 1034b recto', 'PP 1037 recto', 'PP 1038a recto', 'PP 1038b recto', 'PP 1039 recto', 'PP 1041 recto', 'PP 1042 recto', 'PP 1045 recto', 'PP 1046 recto', 'PP 1047 recto', 'PP 1048 recto', 'PP 1050a recto', 'PP 1050b recto', 'PP 1051 recto', 'PP 1052 recto', 'PP 1053 recto', 'PP 1054 recto', 'PP 1055 recto', 'PP 1056 recto', 'PP 1057 recto', 'PP 1058 recto', 'PP 1059a recto', 'PP 1059b recto', 'PP 1060a recto', 'PP 1060b recto', 'PP 1060c recto', 'PP 1061 recto', 'PP 1062 recto', 'PP 1063a recto', 'PP 1063b recto', 'PP 1064 recto', 'PP 1065 recto', 'PP 1066 recto', 'PP 1068 recto', 'PP 1069 recto', 'PP 1070 recto', 'PP 1071 recto', 'PP 1072 recto', 'PP 1073 recto', 'PP 1075 recto', 'PP 1076 recto', 'PP 1078 recto', 'PP 1079 recto', 'PP 1080 recto', 'PP 1081 recto', 'PP 1082 recto', 'PP 1083a recto', 'PP 1083b recto', 'PP 1084 recto', 'PP 1085 recto', 'PP 1087 recto', 'PP 1088 recto', 'PP 1089a recto', 'PP 1089b recto', 'PP 1090 recto', 'PP 1092 recto', 'PP 1093 recto', 'PP 1094 recto', 'PP 1095 recto', 'PP 1095a recto', 'PP 1095b recto', 'PP 1096 recto', 'PP 1096a recto', 'PP 1097 recto', 'PP 1098 recto', 'PP 1099 recto', 'PP 1100 recto', 'PP 1101a recto', 'PP 1101b recto', 'PP 1102 recto', 'PP 1103 recto', 'PP 1104 recto', 'PP 1105 recto', 'PP 1106 recto', 'PP 1107 recto', 'PP 1108 recto', 'PP 1109 recto', 'PP 1110 recto', 'PP 1111 recto', 'PP 1112 recto', 'PP 1113a recto', 'PP 1113b recto', 'PP 1114 recto', 'PP 1115 recto', 'PP 1116 recto', 'PP 1117 recto', 'PP 1118 recto', 'PP 1119a recto', 'PP 1119b recto', 'PP 1120 recto', 'PP 1121 recto', 'PP 1122 recto', 'PP 1123 recto', 'PP 1124 recto', 'PP 1125 recto', 'PP 1126 recto', 'PP 1127 recto', 'PP 1128 recto', 'PP 1129 recto', 'PP 1130 recto', 'PP 1131 recto', 'PP 1132 recto', 'PP 1133 recto', 'PP 1134a recto', 'PP 1134b recto', 'PP 1135a recto', 'PP 1135b recto', 'PP 1136 recto', 'PP 1137 recto', 'PP 1138 recto', 'PP 1139 recto', 'PP 1140 recto', 'PP 1142 recto', 'PP 1143 recto', 'PP 1144 recto', 'PP 1145 recto', 'PP 1146 recto', 'PP 1148 recto', 'PP 1149 recto', 'PP 1150 recto', 'PP 1151 recto', 'PP 1151a recto', 'PP 1152 recto', 'PP 1153a recto', 'PP 1153b recto', 'PP 1154 recto', 'PP 1155 recto', 'PP 1157 recto', 'PP 1158a recto', 'PP 1159 recto', 'PP 1160 recto', 'PP 1161 recto', 'PP 1162a recto', 'PP 1162b recto', 'PP 1163a recto', 'PP 1163b recto', 'PP 1164 recto', 'PP 1165 recto', 'PP 1167 recto', 'PP 1168 recto', 'PP 1169 recto', 'PP 1170 recto', 'PP 1171 recto', 'PP 1172 recto', 'PP 1173 recto', 'PP 1174 recto', 'PP 1175 recto', 'PP 1176 recto', 'PP 1177 recto', 'PP 1178 recto', 'PP 1179 recto', 'PP 1180a recto', 'PP 1180b recto', 'PP 1181a recto', 'PP 1181b recto', 'PP 1182 recto', 'PP 1183 recto', 'PP 1184 recto', 'PP 1184a recto', 'PP 1185 recto', 'PP 1187 recto', 'PP 1189 recto', 'PP 1190a recto', 'PP 1190b recto', 'PP 1191 recto', 'PP 1192a recto', 'PP 1192b recto', 'PP 1193 recto', 'PP 1194 recto', 'PP 1195 recto', 'PP 1196 recto', 'PP 1197 recto', 'PP 1198 recto', 'PP 1199 recto', 'PP 1200 recto', 'PP 1201 recto', 'PP 1202 recto', 'PP 1203 recto', 'PP 1204 recto', 'PP 1205 recto', 'PP 1206 recto', 'PP 1207 recto', 'PP 1207a recto', 'PP 1208 recto', 'PP 1209 recto', 'PP 1210 recto', 'PP 1212 recto', 'PP 1214 recto', 'PP 1215 recto', 'PP 1216 recto', 'PP 1217 recto', 'PP 1218 recto', 'PP 1219 recto', 'PP 1220 recto', 'PP 1222 recto', 'PP 1223a recto', 'PP 1223b recto', 'PP 1224 recto', 'PP 1225 recto', 'PP 1226 recto', 'PP 1227 recto', 'PP 1228 recto', 'PP 1229 recto', 'PP 1230 recto', 'PP 1231 recto', 'PP 1232 recto', 'PP 1236a recto', 'PP 1236b recto', 'PP 1239 recto', 'PP 1241 recto', 'PP 1243a recto', 'PP 1243b recto', 'PP 1244 recto', 'PP 1245 recto', 'PP 1246a recto', 'PP 1246b recto', 'PP 1247 recto', 'PP 1248 recto', 'PP 1249 recto', 'PP 1250 recto', 'PP 1251 recto', 'PP 1252 recto', 'PP 1253a recto', 'PP 1253b recto', 'PP 1254 recto', 'PP 1256 recto', 'PP 1257a recto', 'PP 1257b recto', 'PP 1258 recto', 'PP 1260 recto', 'PP 1261 recto', 'PP 1263 recto', 'PP 1264 recto', 'PP 1265 recto', 'PP 1266 recto', 'PP 1267 recto', 'PP 1268a recto', 'PP 1268b recto', 'PP 1269 recto', 'PP 1269a recto', 'PP 1269b recto', 'PP 1269c recto', 'PP 1270a recto', 'PP 1270b recto', 'PP 1270c recto', 'PP 1270e recto', 'PP 1271 recto', 'PP 1272 recto', 'PP 1273 recto', 'PP 1275 recto', 'PP 1276 recto', 'PP 1277a recto', 'PP 1277b recto', 'PP 1279a recto', 'PP 1279b recto', 'PP 1280 recto', 'PP 1281 recto', 'PP 1282 recto', 'PP 1283a recto', 'PP 1283b recto', 'PP 1284 recto', 'PP 1285a recto', 'PP 1286 recto', 'PP 1287 recto', 'PP 1289a recto', 'PP 1289b recto', 'PP 1290 recto', 'PP 1291 recto', 'PP 1292 recto', 'PP 1293a recto', 'PP 1293b recto', 'PP 1294 recto', 'PP 1295 recto', 'PP 1296 recto', 'PP 1297 recto', 'PP 1298 recto', 'PP 1299 recto', 'PP 1300 recto', 'PP 1301 recto', 'PP 1302 recto', 'PP 1303 recto', 'PP 1304 recto', 'PP 1305 recto', 'PP 1307 recto', 'PP 1308a recto', 'PP 1308b recto', 'PP 1310 recto', 'PP 1311 recto', 'PP 1312a recto', 'PP 1312c recto', 'PP 1315 recto', 'PP 1316 recto', 'PP 1317 recto', 'PP 1318 recto', 'PP 1319 recto', 'PP 1320 recto', 'PP 1321 recto', 'PP 1322 recto', 'PP 1323 recto', 'PP 1324 recto', 'PP 1325 recto', 'PP 1327 recto', 'PP 1328a recto', 'PP 1328b recto', 'PP 1330a recto', 'PP 1330b recto', 'PP 1331 recto', 'PP 1332a recto', 'PP 1332b recto', 'PP 1333 recto', 'PP 1334 recto', 'PP 1335a recto', 'PP 1335b recto', 'PP 1336 recto', 'PP 1337 recto', 'PP 1338 recto', 'PP 1338b recto', 'PP 1339 recto', 'PP 1340 recto', 'PP 1341a recto', 'PP 1342 recto', 'PP 1343 recto', 'PP 1344 recto', 'PP 1345 recto', 'PP 1346 recto', 'PP 1347 recto', 'PP 1348 recto', 'PP 1349 recto', 'PP 1350 recto', 'PP 1351 recto', 'PP 1352 recto', 'PP 1353 recto', 'PP 1354 recto', 'PP 1355 recto', 'PP 1356 recto', 'PP 1357 recto', 'PP 1358 recto', 'PP 1359 recto', 'PP 1360a recto', 'PP 1360b recto', 'PP 1361 recto', 'PP 1362 recto', 'PP 1364 recto', 'PP 1364a recto', 'PP 1364b recto', 'PP 1365a recto', 'PP 1365b recto', 'PP 1366 recto', 'PP 1369 recto', 'PP 1370 recto', 'PP 1371 recto', 'PP 1373 recto', 'PP 1373a recto', 'PP 1373b recto', 'PP 1375 recto', 'PP 1376 recto', 'PP 1377 recto', 'PP 1378a recto', 'PP 1378b recto', 'PP 1379 recto', 'PP 1380 recto', 'PP 1382 recto', 'PP 1383 recto', 'PP 1384 recto', 'PP 1385 recto', 'PP 1386 recto', 'PP 1389 recto', 'PP 1390 recto', 'PP 1391 recto', 'PP 1392-2 recto', 'PP 1393 recto', 'PP 1394 recto', 'PP 1395 recto', 'PP 1396 recto', 'PP 1397 recto', 'PP 1616-1 recto', 'PP 1616-2 recto', 'PP 1616-3 recto', 'PP 1616-4 recto', 'PP 1616-5 recto', 'PP 1616 recto', 'PP 2081 recto', 'PP 2488 recto', 'PP 3252 recto', 'PP 379 recto', 'PP 4799 recto', 'PP 4867a kopie recto', 'PP 4867b recto', 'PP 5019a recto', 'PP 5019b recto', 'PP 6086 recto', 'PP dubbel 0921a recto', 'PP dubbel 0960b recto', 'PP dubbel 1248 recto', 'PP dubbel hoort bij 1374 recto', 'PP dubbel nummer 1018 recto', 'PP dubbel nummer 1112 recto', 'PP dubbel nummer 1382 recto', 'PP Geen nummer 035 recto', 'PP Geen nummer 036 recto', 'PP Grafschrift J recto', 'PP hoort bij -1 0661 recto', 'PP hoort bij -2 0661 recto', 'PP hoort bij -2 verso 0661 recto', 'PP Hoort bij 0014 recto', 'PP hoort bij 0397 recto', 'PP hoort bij 0655b recto', 'PP hoort bij 0704 recto', 'PP hoort bij 0717 recto', 'PP hoort bij 0727 recto', 'PP hoort bij 0773 recto', 'PP hoort bij 0785a recto', 'PP hoort bij 0797a recto', 'PP hoort bij 0801 kopie recto', 'PP hoort bij 0806 recto', 'PP hoort bij 0807a recto', 'PP hoort bij 0818 recto', 'PP hoort bij 0819 recto', 'PP hoort bij 0824 recto', 'PP hoort bij 0827 recto', 'PP hoort bij 0830 recto', 'PP hoort bij 0841 recto', 'PP hoort bij 0845+ recto', 'PP hoort bij 0854 recto', 'PP hoort bij 0865a recto', 'PP hoort bij 0865b recto', 'PP hoort bij 0924 recto', 'PP hoort bij 0951 recto', 'PP hoort bij 0958 recto', 'PP hoort bij 0960 recto', 'PP hoort bij 0961 recto', 'PP hoort bij 1006 recto', 'PP hoort bij 1032 recto', 'PP hoort bij 1037 recto', 'PP hoort bij 1048 recto', 'PP hoort bij 1062 recto', 'PP hoort bij 1095b recto', 'PP hoort bij 1108 recto', 'PP hoort bij 1117 recto', 'PP hoort bij 1128 recto', 'PP hoort bij 1153a recto', 'PP hoort bij 1153b recto', 'PP hoort bij 1158a recto', 'PP hoort bij 1167 recto', 'PP hoort bij 1172 recto', 'PP hoort bij 1183 recto', 'PP hoort bij 1189 recto', 'PP hoort bij 1196 recto', 'PP hoort bij 1208 recto', 'PP hoort bij 1216 recto', 'PP hoort bij 1231 recto', 'PP hoort bij 1239 recto', 'PP hoort bij 1243 recto', 'PP hoort bij 1247 recto', 'PP hoort bij 1257a recto', 'PP hoort bij 1265 recto', 'PP hoort bij 1267 recto', 'PP hoort bij 1269b recto', 'PP hoort bij 1303 recto', 'PP hoort bij 1348 recto', 'PP hoort bij 1362 recto', 'PP hoort bij 1374 recto', 'PP hoort bij 991b recto', 'PP hoort bij verso 0655b recto', 'PP hoort bij verso 0785a recto', 'PP hoort bij verso 0797a recto', 'PP hoort bij verso 0798 recto', 'PP hoort bij verso 0801 recto', 'PP hoort bij verso 0807a recto', 'PP hoort bij verso 0819 recto', 'PP hoort bij verso 0841 recto', 'PP hoort bij verso 0845+ recto', 'PP hoort bij verso 0854 recto', 'PP hoort bij verso 0865a recto', 'PP hoort bij verso 0924 recto', 'PP hoort bij verso 1196 recto', 'PP hoort bij verso 1239 recto', 'PP hoort bij verso 1243 recto', 'PP hoort bij verso 1247 recto', 'PP hoort bij verso 1267 recto', 'PP hoort bij verso 1375 recto', 'PP hoort bij Vondel recto', 'PP hoort bij zonder nummer 87 recto', 'PP hoort bij Zonder nummer 98 recto', 'PP hoort bij Zonder nummer verso 98 recto', 'PP hoort bij-01 0931 recto', 'PP hoort bij-02 0931 recto', 'PP hoort bij-03 0931 recto', 'PP hoort bij-1 0982 recto', 'PP hoort bij-1 1251 recto', 'PP hoort bij-1 1375 recto', 'PP hoort bij-2 0982 recto', 'PP hoort bij-2 1251 recto', 'PP hoort bij-2 verso 0982 recto', 'PP kopie 1121 recto', 'PP kopie1034a recto', 'PP kopie1163a recto', 'PP onder nummer 64 recto', 'PP Uitnodiging begrafenis Vondel recto', 'PP Zonder Nummer 01 recto', 'PP Zonder Nummer 02 recto', 'PP Zonder Nummer 03 recto', 'PP Zonder nummer 04 recto', 'PP Zonder nummer 05 verso recto', 'PP Zonder nummer 05 recto', 'PP Zonder nummer 06 recto', 'PP Zonder nummer 07 recto', 'PP Zonder nummer 08 recto', 'PP Zonder nummer 09 recto', 'PP Zonder nummer 10 recto', 'PP Zonder nummer 11 recto', 'PP Zonder nummer 12 recto', 'PP Zonder nummer 13 recto', 'PP Zonder nummer 14 recto', 'PP Zonder nummer 15 recto', 'PP Zonder nummer 16 recto', 'PP Zonder nummer 17 recto', 'PP Zonder nummer 18 recto', 'PP Zonder nummer 19 recto', 'PP Zonder nummer 20 recto', 'PP Zonder nummer 21 recto', 'PP Zonder nummer 22 recto', 'PP Zonder nummer 23 recto', 'PP Zonder nummer 24 recto', 'PP Zonder nummer 25 recto', 'PP Zonder nummer 26 recto', 'PP Zonder nummer 27 recto', 'PP Zonder nummer 28 recto', 'PP Zonder nummer 29 recto', 'PP Zonder nummer 30 recto', 'PP Zonder nummer 31 recto', 'PP Zonder nummer 32 recto', 'PP Zonder nummer 33 recto', 'PP Zonder nummer 34 recto', 'PP Zonder nummer 37 verso recto', 'PP Zonder nummer 37 recto', 'PP Zonder nummer 38 01 recto', 'PP Zonder nummer 38 02 recto', 'PP Zonder nummer 38 03 recto', 'PP Zonder nummer 38 04 recto', 'PP Zonder nummer 38 05 recto', 'PP Zonder nummer 39 verso recto', 'PP Zonder nummer 39 recto', 'PP Zonder nummer 40 verso recto', 'PP Zonder nummer 40 recto', 'PP Zonder nummer 41 verso recto', 'PP Zonder nummer 41 recto', 'PP Zonder nummer 42 recto', 'PP Zonder nummer 43 verso recto', 'PP Zonder nummer 43 recto', 'PP Zonder nummer 44 recto', 'PP Zonder nummer 45 recto', 'PP Zonder nummer 46 recto', 'PP Zonder nummer 47 recto', 'PP Zonder nummer 48 verso recto', 'PP Zonder nummer 48 recto', 'PP Zonder nummer 49 recto', 'PP Zonder nummer 50 recto', 'PP Zonder nummer 51 recto', 'PP Zonder nummer 52 recto', 'PP Zonder nummer 53 recto', 'PP Zonder nummer 56 recto', 'PP Zonder nummer 57 recto', 'PP Zonder nummer 58 recto', 'PP Zonder nummer 59 recto', 'PP Zonder nummer 61 recto', 'PP Zonder nummer 62 recto', 'PP Zonder nummer 63 recto', 'PP Zonder nummer 65 recto', 'PP Zonder nummer 66 recto', 'PP Zonder nummer 67 recto', 'PP Zonder nummer 68 recto', 'PP Zonder nummer 69 recto', 'PP Zonder nummer 70 recto', 'PP Zonder nummer 71 recto', 'PP Zonder nummer 72 recto', 'PP Zonder nummer 73 verso recto', 'PP Zonder nummer 73 recto', 'PP Zonder nummer 74 recto', 'PP Zonder nummer 75 recto', 'PP Zonder nummer 76 verso recto', 'PP Zonder nummer 76 recto', 'PP Zonder nummer 77 recto', 'PP Zonder nummer 78 verso recto', 'PP Zonder nummer 78 recto', 'PP Zonder nummer 79 verso recto', 'PP Zonder nummer 79 recto', 'PP Zonder nummer 80 recto', 'PP Zonder nummer 81 recto', 'PP Zonder nummer 82 recto', 'PP Zonder nummer 83 recto', 'PP Zonder nummer 84 recto', 'PP Zonder nummer 85 recto', 'PP Zonder nummer 86 recto', 'PP Zonder nummer 87 recto', 'PP Zonder nummer 88 recto', 'PP Zonder nummer 89 recto', 'PP Zonder nummer 90 recto', 'PP Zonder nummer 91 recto', 'PP Zonder nummer 92 recto', 'PP Zonder nummer 93 recto', 'PP Zonder nummer 94 recto', 'PP Zonder nummer 95 recto', 'PP Zonder nummer 96 recto', 'PP Zonder nummer 97 recto', 'PP Zonder nummer 98 recto', 'PP Zonder nummer verso 50 recto', 'PP Zonder nummer verso 51 recto', 'PP Zonder nummer verso 59 recto', 'PP Zonder nummer verso 85 recto', 'PP Zonder nummer verso 96 recto', 'PP Zonder nummer-1 55 recto', 'PP Zonder nummer-1 75 recto', 'PP Zonder nummer-2 55 recto', 'PP Zonder nummer-2 75 recto', 'PP Zonder nummer-3 55 recto', 'PP Zonder nummer-3 75 recto', 'Ptlood vraag recto', 'Q 041 recto', 'Q 042 recto', 'Q 052a recto', 'Q 076 recto', 'Q+ 002 recto', 'Q+ 003 recto', 'Q+ 003a recto', 'Q+ 019-2 recto', 'Q+ 036a verso recto', 'R+ 010 recto', 'R+ 054a 1 recto', 'R+ 094 recto', 'RdW G 001 recto', 'RdW G 002 recto', 'RdW G 003 recto', 'RdW G 004 recto', 'RdW G 005 recto', 'RdW G 006 recto', 'RdW G 007 recto', 'RdW G 008 recto', 'RdW G 009 recto', 'RdW G 010 recto', 'RdW G 011 recto', 'RdW G 012 recto', 'RdW G 013 recto', 'RdW G 014 recto', 'RdW G 015 recto', 'RdW G 016 recto', 'RdW G 017 recto', 'RdW G 018 recto', 'RdW G 026 recto', 'RdW G 027 recto', 'RdW G 029 recto', 'RdW G 030 recto', 'RdW G 031 recto', 'RdW G 032 recto', 'RdW G 033 recto', 'RdW G 034 recto', 'RdW G 035 recto', 'RdW G 036 recto', 'RdW G 037 recto', 'RdW G 038 recto', 'RdW G 049 recto', 'RdW G 050_01 recto', 'RdW G 050_02 recto', 'RdW G 051 recto', 'RdW G 052 recto', 'RdW G 054 recto', 'RdW G 055 recto', 'RdW G 056 recto', 'RdW G 057 recto', 'RdW G 058 recto', 'RdW G 059 recto', 'RdW G 060 recto', 'RdW G 061 recto', 'RdW G 072 recto', 'RdW G 073 recto', 'RdW G 074 recto', 'RdW G 179 recto', 'RdW G 179a recto', 'RdW G 180 recto', 'RdW G 181 recto', 'RdW G 182 recto', 'RdW G 183 recto', 'RdW G 206 recto', 'RdW G 224 recto', 'RdW G 225 recto', 'RdW G 226 recto', 'RdW G 227 recto', 'RdW G 228 recto', 'RdW G 229 recto', 'RdW G 230 recto', 'RdW G 231 recto', 'RdW G 232 recto', 'RdW G 233 recto', 'RdW T 001 recto', 'RdW T 002 recto', 'RdW T 003 recto', 'RdW T 004 recto', 'RdW T 005 recto', 'RdW T 006 recto', 'RdW T 007 recto', 'RdW T 008 recto', 'RdW T 009 recto', 'RdW T 010 recto', 'RdW T 011 recto', 'RdW T 012 recto', 'RdW T 013 recto', 'RdW T 021 recto', 'RdW T 022 recto', 'RdW T 023 recto', 'RdW T 024 recto', 'RdW T 025 recto', 'RdW T 026 recto', 'RdW T 027 recto', 'RdW T 028 recto', 'RdW T 031 recto', 'RdW T 032 recto', 'RdW T 034 recto', 'RdW T 036 recto', 'REPRODUCTIE recto', 'S 031a recto', 'S 059-01 recto', 'S 059-02 recto', 'S 059-03 recto', 'S 059-04 recto', 'S 059-05 recto', 'S 059-06 recto', 'S 059-07 recto', 'S 059-08 recto', 'S 059-09 recto', 'S 141 7 recto', 'S+ 001 recto', 'S+ 002 recto', 'S+ 003 recto', 'S+ 004 recto', 'S+ 005 recto', 'S+ 006 recto', 'S+ 007 recto', 'S+ 008 recto', 'S+ 009 recto', 'S+ 010 recto', 'S+ 011 recto', 'S+ 012 recto', 'S+ 013 recto', 'S+ 014 recto', 'S+ 014b recto', 'S+ 015 recto', 'S+ 016 recto', 'S+ 017 recto', 'S+ 018 recto', 'S+ 018a recto', 'S+ 019 recto', 'S+ 020 recto', 'S+ 021 recto', 'S+ 022 recto', 'S+ 023 recto', 'S+ 024 recto', 'S+ 025 recto', 'S+ 025a recto', 'S+ 026 recto', 'S+ 027 recto', 'S+ 028 recto', 'S+ 029 recto', 'S+ 030 recto', 'S+ 031 recto', 'S+ 032 recto', 'S+ 033 recto', 'S+ 034 recto', 'S+ 035 recto', 'S+ 036 recto', 'S+ 037 recto', 'S+ 038 recto', 'S+ 039 recto', 'S+ 040 recto', 'S+ 041 recto', 'S+ 042 recto', 'S+ 043 recto', 'S+ 044 recto', 'S+ 045 recto', 'S+ 047 recto', 'S+ 048 recto', 'S+ 049 recto', 'S+ 050 recto', 'S+ 051 recto', 'S+ 052 recto', 'S+ 053 recto', 'S+ 054 recto', 'S+ 054a recto', 'S+ 054b recto', 'S+ 055 recto', 'S+ 056 recto', 'S+ 057 recto', 'S+ 058 recto', 'S+ 059 recto', 'S+ 060 recto', 'S+ 061 recto', 'S+ 062 recto', 'S+ 063 recto', 'S+ 064 recto', 'S+ 065 recto', 'S+ 066 recto', 'S+ 067 recto', 'S+ 068 recto', 'S+ 069 recto', 'S+ 070 recto', 'S+ 071 recto', 'S+ 072 recto', 'S+ 073 recto', 'S+ 074 recto', 'S+ 075 recto', 'S+ 076 recto', 'S+ 077 recto', 'S+ 078 recto', 'S+ 079 recto', 'S+ 080 recto', 'S+ 081 recto', 'S+ 082 recto', 'S+ 083 recto', 'S+ 084 recto', 'S+ 085 recto', 'S+ 086 recto', 'S+ 087 recto', 'S+ 088 recto', 'S+ 089 recto', 'S+ 090 recto', 'S+ 091 recto', 'S+ 092 recto', 'S+ 093 recto', 'S+ 094 recto', 'S+ 095 recto', 'S+ 096 recto', 'S+ 097 recto', 'S+ 098 recto', 'S+ 099 recto', 'S+ 099a recto', 'S+ 134 recto', 'St G 079 recto', 'St G 081 recto', 'St G 118 recto', 'St G 216 recto', 'St G 253 recto', 'St G 293 recto', 'St G geen nummer-01 30-03-2012 recto', 'St G geen nummer-02 30-03-2012 recto', 'St G zonder nummer 01_05-04-2012 recto', 'St G zonder nummer 01_05-04-2012_1 recto', 'St G zonder nummer 02_05-04-2012 recto', 'StG 142 recto', 'T 085-2 recto', 'T 085_3 recto', 'TdM 0001 recto', 'TdM 0004 recto', 'TdM 0005 recto', 'TdM 0025 recto', 'TdM 0027 recto', 'TdM 0073 recto', 'TdM 0086 recto', 'TdM 0088 recto', 'TdM 0090 recto', 'TdM 0091 recto', 'TdM 0092 recto', 'TdM 0093 recto', 'TdM 0094 recto', 'TdM 0095 recto', 'TdM 0098 recto', 'TdM 0120 recto', 'TdM 0121 recto', 'TdM 0127 recto', 'TdM 0650 recto', 'TdM 0669 recto', 'TdM 0670 recto', 'TdM 0671 recto', 'TdM 0675 recto', 'TdM 0687 recto', 'TdM 0688 recto', 'TdM 0698 recto', 'TdM 0701a recto', 'TdM 0701b recto', 'TdM 0701c recto', 'TdM 0779b recto', 'TdM 0800 recto', 'TdM 0814 recto', 'TdM 0854 recto', 'TdM 088-2 recto', 'TdM 090 recto', 'TdM 091 recto', 'TdM 1647 recto', 'TdM 2132 recto', 'TdM 2208 recto', 'TdM C 0001 recto', 'TdM C 0005 recto', 'TdM C 0006 recto', 'TdM C 0013 recto', 'TdM C 0025 recto', 'TdM C 0026 recto', 'TdM C 0027 recto', 'TdM C 0029 recto', 'TdM C 0030 recto', 'TdM C 0038 recto', 'TdM C 0049 recto', 'TdM C 0050 recto', 'TdM C 0053 recto', 'TdM C 0055 recto', 'TdM C 0057 recto', 'TdM C 0062 recto', 'TdM C 0063 recto', 'TdM C 0074 recto', 'TdM C 0080 recto', 'TdM C 0089 recto', 'TdM C 0090 recto', 'TdM C 0098 recto', 'TdM C 0099 recto', 'TdM C 0106 recto', 'TdM C 0111 recto', 'TdM C 0117 recto', 'TdM C 013 recto', 'TdM C 0130a recto', 'TdM C 0130b recto', 'TdM C 0133 recto', 'TdM C 0136 recto', 'TdM C 0139 recto', 'TdM C 0153 recto', 'TdM C 0158 recto', 'TdM C 0160 recto', 'TdM C 0161 recto', 'TdM C 0162 recto', 'TdM C 0171 recto', 'TdM C 0176 recto', 'TdM C 0181 recto', 'TdM C 0213 recto', 'TdM C 0220 recto', 'TdM C 0222 recto', 'TdM C 0223 recto', 'TdM C 0224 recto', 'TdM C 0235 recto', 'TdM C 0244 recto', 'TdM C 0248 recto', 'TdM C 0252 recto', 'TdM C 0258 recto', 'TdM C 0363 recto', 'TdM C 0652 recto', 'TdM C 0653 recto', 'TdM C 0655 recto', 'TdM C 0660 recto', 'TdM C 0662 recto', 'TdM C 0684 recto', 'TdM C 0688 recto', 'TdM C 0694 recto', 'TdM C 0696 recto', 'TdM C 0698 recto', 'TdM C 0701b recto', 'TdM C 0725 recto', 'TdM C 0753 recto', 'TdM C 0782 recto', 'TdM C 0783 recto', 'TdM C 0784 recto', 'TdM C 0786 recto', 'TdM C 0792 recto', 'TdM C 0800 recto', 'TdM C 0802 recto', 'TdM C 0809 recto', 'TdM C 0810 recto', 'TdM C 0813 recto', 'TdM C 0822 recto', 'TdM C 0825 recto', 'TdM C 0826 recto', 'TdM C 0827 recto', 'TdM C 0828 recto', 'TdM C 0832 recto', 'TdM C 0833 recto', 'TdM C 0837 recto', 'TdM C 0838 recto', 'TdM C 0839 recto', 'TdM C 0840 recto', 'TdM C 0841 recto', 'TdM C 0842 recto', 'TdM C 0843 recto', 'TdM C 0847 recto', 'TdM C 0849 recto', 'TdM C 0851 recto', 'TdM C 0852 recto', 'TdM C 0854 recto', 'TdM C 0855 recto', 'TdM C 0857 recto', 'TdM C 0858 recto', 'TdM C 0859 recto', 'TdM C 0860 recto', 'TdM C 0865 recto', 'TdM C 0871 recto', 'TdM C 0872 recto', 'TdM C 0873 recto', 'TdM C 0875 recto', 'TdM C 0878 recto', 'TdM C 0882 recto', 'TdM C 0885 recto', 'TdM C 0889 recto', 'TdM C 0892 recto', 'TdM C 0893 recto', 'TdM C 0898 recto', 'TdM C 0900 recto', 'TdM C 0901 recto', 'TdM C 0904 recto', 'TdM C 0907 recto', 'TdM C 0912 recto', 'TdM C 0916 recto', 'TdM C 0917 recto', 'TdM C 0919 recto', 'TdM C 0922 recto', 'TdM C 0933 recto', 'TdM C 0938 recto', 'TdM C 0940 recto', 'TdM C 0941 recto', 'TdM C 0943 recto', 'TdM C 0944a recto', 'TdM C 0944b recto', 'TdM C 0950 recto', 'TdM C 0951a recto', 'TdM C 0953 recto', 'TdM C 0961 recto', 'TdM C 0964 recto', 'TdM C 0967 recto', 'TdM C 0973 recto', 'TdM C 0975 recto', 'TdM C 0978 recto', 'TdM C 0979 recto', 'TdM C 0980 recto', 'TdM C 0984 recto', 'TdM C 0989 recto', 'TdM C 0993 recto', 'TdM C 0998 recto', 'TdM C 0999 recto', 'TdM C 1004 recto', 'TdM C 1007 recto', 'TdM C 1010 recto', 'TdM C 1011 recto', 'TdM C 1012 recto', 'TdM C 1013 recto', 'TdM C 1014 recto', 'TdM C 1015 recto', 'TdM C 1017 recto', 'TdM C 1018 recto', 'TdM C 1019 recto', 'TdM C 1024 recto', 'TdM C 1028 recto', 'TdM C 1029 recto', 'TdM C 107 recto', 'TdM C 1076 recto', 'TdM C 1077 recto', 'TdM C 1114 recto', 'TdM C 1122 recto', 'TdM C 1134 recto', 'TdM C 1137 recto', 'TdM C 1149 recto', 'TdM C 1169 recto', 'TdM C 1172 recto', 'TdM C 1178 recto', 'TdM C 1182 recto', 'TdM C 1183 recto', 'TdM C 1194 recto', 'TdM C 1195 recto', 'TdM C 1203 recto', 'TdM C 1205 recto', 'TdM C 1208 recto', 'TdM C 1213 recto', 'TdM C 1216 recto', 'TdM C 1219 recto', 'TdM C 1221 recto', 'TdM C 1222 recto', 'TdM C 1235 recto', 'TdM C 1236 recto', 'TdM C 1237 recto', 'TdM C 1241 recto', 'TdM C 1252 recto', 'TdM C 1253 recto', 'TdM C 1257 recto', 'TdM C 1297 recto', 'TdM C 1298 recto', 'TdM C 1305 recto', 'TdM C 1307 recto', 'TdM C 1308 recto', 'TdM C 1317 recto', 'TdM C 1333 recto', 'TdM C 1338 recto', 'TdM C 1348 recto', 'TdM C 1378 recto', 'TdM C 1391 recto', 'TdM C 1393 recto', 'TdM C 1394 recto', 'TdM C 1399 recto', 'TdM C 1400 recto', 'TdM C 1403 recto', 'TdM C 1404 recto', 'TdM C 1418 recto', 'TdM C 1423 recto', 'TdM C 1424 recto', 'TdM C 1428 recto', 'TdM C 1429 recto', 'TdM C 1433 recto', 'TdM C 1457 recto', 'TdM C 1458 recto', 'TdM C 1462 recto', 'TdM C 1474 recto', 'TdM C 1477 recto', 'TdM C 1486_1 recto', 'TdM C 1488 recto', 'TdM C 1490 recto', 'TdM C 1496 recto', 'TdM C 1497 recto', 'TdM C 1498 recto', 'TdM C 1500 recto', 'TdM C 1501 recto', 'TdM C 1503 recto', 'TdM C 1507 recto', 'TdM C 1508 recto', 'TdM C 1515 recto', 'TdM C 1517 recto', 'TdM C 1526 recto', 'TdM C 1530 recto', 'TdM C 1558 recto', 'TdM C 1561 recto', 'TdM C 1563 recto', 'TdM C 1573 recto', 'TdM C 1574 recto', 'TdM C 1575 recto', 'TdM C 1577 recto', 'TdM C 1579 recto', 'TdM C 1580 recto', 'TdM C 1583 recto', 'TdM C 1587 recto', 'TdM C 1593 recto', 'TdM C 1595 recto', 'TdM C 1597 recto', 'TdM C 1599 recto', 'TdM C 1614 recto', 'TdM C 1620 recto', 'TdM C 1622 recto', 'TdM C 1623 recto', 'TdM C 1624 recto', 'TdM C 1627 recto', 'TdM C 1634 recto', 'TdM C 1636 recto', 'TdM C 1644 recto', 'TdM C 1647 recto', 'TdM C 1648 recto', 'TdM C 1665 recto', 'TdM C 1676 recto', 'TdM C 1677 recto', 'TdM C 1678 recto', 'TdM C 1679 recto', 'TdM C 1681 recto', 'TdM C 1682 recto', 'TdM C 1687 recto', 'TdM C 1688 recto', 'TdM C 1692 recto', 'TdM C 1698 recto', 'TdM C 1699 recto', 'TdM C 1717 recto', 'TdM C 1720 recto', 'TdM C 1721 recto', 'TdM C 1725 recto', 'TdM C 1727 recto', 'TdM C 1730 recto', 'TdM C 1733 recto', 'TdM C 1737 recto', 'TdM C 1743 recto', 'TdM C 1752 recto', 'TdM C 1762 recto', 'TdM C 1764 recto', 'TdM C 1768 recto', 'TdM C 1769 recto', 'TdM C 1771 recto', 'TdM C 1774 recto', 'TdM C 1777 recto', 'TdM C 1781 recto', 'TdM C 1782 recto', 'TdM C 1789 recto', 'TdM C 1796 recto', 'TdM C 1797 recto', 'TdM C 1798 recto', 'TdM C 1815 recto', 'TdM C 1818 recto', 'TdM C 1819 recto', 'TdM C 1827 recto', 'TdM C 1830 recto', 'TdM C 1833 recto', 'TdM C 1838 recto', 'TdM C 1843 recto', 'TdM C 1847 recto', 'TdM C 1851 recto', 'TdM C 1870 recto', 'TdM C 1872 recto', 'TdM C 1876 recto', 'TdM C 1880 recto', 'TdM C 1882 recto', 'TdM C 1899 recto', 'TdM C 1901 recto', 'TdM C 1929 recto', 'TdM C 1942 recto', 'TdM C 1949 recto', 'TdM C 1951 recto', 'TdM C 1952 recto', 'TdM C 1961 recto', 'TdM C 1962 recto', 'TdM C 1970 recto', 'TdM C 1983 recto', 'TdM C 1984 recto', 'TdM C 1991 recto', 'TdM C 1992 recto', 'TdM C 1993 recto', 'TdM C 1997 recto', 'TdM C 1999 recto', 'TdM C 2000 recto', 'TdM C 2001 recto', 'TdM C 2015 recto', 'TdM C 2027 recto', 'TdM C 2049 recto', 'TdM C 2058 recto', 'TdM C 2059 recto', 'TdM C 2063 recto', 'TdM C 2084 recto', 'TdM C 2093 recto', 'TdM C 2098 recto', 'TdM C 2103 recto', 'TdM C 2110 recto', 'TdM C 2111 recto', 'TdM C 2117 recto', 'TdM C 2120 recto', 'TdM C 2131 recto', 'TdM C 2132 recto', 'TdM C 2134 recto', 'TdM C 2137 recto', 'TdM C 2138 recto', 'TdM C 2140 recto', 'TdM C 2142 recto', 'TdM C 2145 recto', 'TdM C 2146 recto', 'TdM C 2152 recto', 'TdM C 2154 recto', 'TdM C 2155 recto', 'TdM C 2163 recto', 'TdM C 2166 recto', 'TdM C 2167 recto', 'TdM C 2170 recto', 'TdM C 2171 recto', 'TdM C 2174 recto', 'TdM C 2180 recto', 'TdM C 2182 recto', 'TdM C 2183 recto', 'TdM C 2184 recto', 'TdM C 2185 recto', 'TdM C 2190 recto', 'TdM C 2202 recto', 'TdM C 2206 recto', 'TdM C 2208 recto', 'TdM C 2223 recto', 'TdM C 2225 recto', 'TdM C 2230 recto', 'TdM C 2231 recto', 'TdM C 2235 recto', 'TdM C 2238 recto', 'TdM C 2240 recto', 'TdM C 2244 recto', 'TdM C 2246 recto', 'TdM C 2254 recto', 'TdM C 2264 recto', 'TdM C 2265 recto', 'TdM C 2270 recto', 'TdM C 2275 recto', 'TdM C 2276 recto', 'TdM C 2280 recto', 'TdM C 2290 recto', 'TdM C 2294 recto', 'TdM C 2295 recto', 'TdM C 2296 recto', 'TdM C 2303 recto', 'TdM C 2304 recto', 'TdM C 2305 recto', 'TdM C 2317 recto', 'TdM C 2319 recto', 'TdM C 2320 recto', 'TdM C 2321 recto', 'TdM C 2331 recto', 'TdM C 2340 recto', 'TdM C 2342 recto', 'TdM C 2343 recto', 'TdM C 2349 recto', 'TdM C 2350 recto', 'TdM C 2351 recto', 'TdM C 2353 recto', 'TdM C 2355 recto', 'TdM C 2361 recto', 'TdM C 2365 recto', 'TdM C 2370 recto', 'TdM C 2381 recto', 'TdM C 2391 recto', 'TdM C 2392 recto', 'TdM C 2394 recto', 'TdM C 3001 recto', 'TdM C 3014 recto', 'TdM C 3016 recto', 'TdM C 3017 recto', 'TdM C 3025 recto', 'TdM C 3027 recto', 'TdM C 3030 recto', 'TdM C 3031 recto', 'TdM C 3034 recto', 'TdM C 3054 recto', 'TdM C 3064 recto', 'TdM C 3068 recto', 'TdM C 3069 recto', 'TdM C 3072 recto', 'TdM C 3075 recto', 'TdM C 3076 recto', 'TdM C 3078 recto', 'TdM C 3080 recto', 'TdM C 3081 recto', 'TdM C 3084 recto', 'TdM C 3089 recto', 'TdM C 3090 recto', 'TdM C 3091 recto', 'TdM C 3092 recto', 'TdM C 3093 recto', 'TdM C 3097 recto', 'TdM C 3098 recto', 'TdM C 3099 recto', 'TdM C 3102 recto', 'TdM C 3115 recto', 'TdM C 3119 recto', 'TdM C 3125 recto', 'TdM C 3126 recto', 'TdM C 3128 recto', 'TdM C 3130 recto', 'TdM C 3131 recto', 'TdM C 3133 recto', 'TdM C 3155 recto', 'TdM C 3170 recto', 'TdM C 3174 recto', 'TdM C 3175 recto', 'TdM C 3181 recto', 'TdM C 3185 recto', 'TdM C 3193 recto', 'TdM C 3197 recto', 'TdM C 3202 recto', 'TdM C 3203 recto', 'TdM C 3204 recto', 'TdM C 3207 recto', 'TdM C 3210 recto', 'TdM C 3212 recto', 'TdM C 3214 recto', 'TdM C 3215 recto', 'TdM C 3224 recto', 'TdM C 3227 recto', 'TdM C 3228 recto', 'TdM C 3229 recto', 'TdM C 3230 recto', 'TdM C 3231 recto', 'TdM C 3232 recto', 'TdM C 3233 recto', 'TdM C 3234 recto', 'TdM C 3237 recto', 'TdM C 3239 recto', 'TdM C 3240 recto', 'TdM C 3242 recto', 'TdM C 3244 recto', 'TdM C 3245 recto', 'TdM C 3246 recto', 'TdM C 3247 recto', 'TdM C 3250 recto', 'TdM C 3251 recto', 'TdM C 3264 recto', 'TdM C 3269 recto', 'TdM C 3270 recto', 'TdM C 3271 recto', 'TdM C 3278 recto', 'TdM C 3282 recto', 'TdM C 3283 recto', 'TdM C 3285 recto', 'TdM C 3286 recto', 'TdM C 3287 recto', 'TdM C 3290 recto', 'TdM C 3293 recto', 'TdM C 3297 recto', 'TdM C 3304 recto', 'TdM C 3307 recto', 'TdM C 3308 recto', 'TdM C 3309 recto', 'TdM C 3310 recto', 'TdM C 3312 recto', 'TdM C 3313 recto', 'TdM C 3316 recto', 'TdM C 3317 recto', 'TdM C 3318 recto', 'TdM C 3319 recto', 'TdM C 3321 recto', 'TdM C 3322 recto', 'TdM C 3323 recto', 'TdM C 3324 recto', 'TdM C 3325 recto', 'TdM C 3326 recto', 'TdM C 3327 recto', 'TdM C 3328 recto', 'TdM C 3330 recto', 'TdM C 3332 recto', 'TdM C 3333 recto', 'TdM C 3334 recto', 'TdM C 3336 recto', 'TdM C 3337 recto', 'TdM C 3338 recto', 'TdM C 3340 recto', 'TdM C 3341 recto', 'TdM C 3342 recto', 'TdM C 3343 recto', 'TdM C 3344 recto', 'TdM C 3345 recto', 'TdM C 3346 recto', 'TdM C 3347 recto', 'TdM C 3348 recto', 'TdM C 3351 recto', 'TdM C 3352 recto', 'TdM C 3353 recto', 'TdM C 3354 recto', 'TdM C 3355 recto', 'TdM C 3356 recto', 'TdM C 3358 recto', 'TdM C 3360 recto', 'TdM C 3361 recto', 'TdM C 3362 recto', 'TdM C 3363 recto', 'TdM C 3364 recto', 'TdM C 3367 recto', 'TdM C 3368 recto', 'TdM C 3369 recto', 'TdM C 3370 recto', 'TdM C 3371 recto', 'TdM C 3373 recto', 'TdM C 3374 recto', 'TdM C 3375 recto', 'TdM C 3377 recto', 'TdM C 3378 recto', 'TdM C 3379 recto', 'TdM C 3380 recto', 'TdM C 3381 recto', 'TdM C 3382 recto', 'TdM C 3383 recto', 'TdM C 3384 recto', 'TdM C 3385 recto', 'TdM C 3386 recto', 'TdM C 3388 recto', 'TdM C 3389 recto', 'TdM C 3390 recto', 'TdM C 3391 recto', 'TdM C 3392 recto', 'TdM C 3393 recto', 'TdM C 3395 recto', 'TdM C 3396 recto', 'TdM C 3399 recto', 'TdM C 3400 recto', 'TdM C 3401 recto', 'TdM C 3402 recto', 'TdM C 3404 recto', 'TdM C 3405 recto', 'TdM C 3406 recto', 'TdM C 3408 recto', 'TdM C 3409 recto', 'TdM C 3411 recto', 'TdM C 3419 recto', 'TdM C 3423 recto', 'TdM C 3424 recto', 'TdM C 3425 recto', 'TdM C 3427 recto', 'TdM C 3430 recto', 'TdM C 3433 recto', 'TdM C 3436 recto', 'TdM C 3437 recto', 'TdM C 3439 recto', 'TdM C 3440 recto', 'TdM C zonder nummer-01 recto', 'TdM C zonder nummer-02 recto', 'TdM C zonder nummer-03 recto', 'TdM C zonder nummer-04 recto', 'TvB G 0058 recto', 'TvB G 0065 recto', 'TvB G 01-02-Geen nummer-01 recto', 'TvB G 010 recto', 'TvB G 0147 recto', 'TvB G 0148 recto', 'TvB G 0160 recto', 'TvB G 0161 recto', 'TvB G 0162 recto', 'TvB G 0163 recto', 'TvB G 0164 recto', 'TvB G 0165 recto', 'TvB G 0172 recto', 'TvB G 0173 recto', 'TvB G 0174 recto', 'TvB G 0175 recto', 'TvB G 0176 recto', 'TvB G 0177 recto', 'TvB G 0178 recto', 'TvB G 0182 recto', 'TvB G 0183 recto', 'TvB G 0209 recto', 'TvB G 0210 recto', 'TvB G 0211 recto', 'TvB G 0212 recto', 'TvB G 0213 recto', 'TvB G 0214 recto', 'TvB G 0215 recto', 'TvB G 0216 recto', 'TvB G 0217 recto', 'TvB G 0218 recto', 'TvB G 0219 recto', 'TvB G 0220 recto', 'TvB G 0221 recto', 'TvB G 0222 recto', 'TvB G 0223 recto', 'TvB G 030 recto', 'TvB G 031 recto', 'TvB G 032 recto', 'TvB G 033 recto', 'TvB G 034 recto', 'TvB G 035 recto', 'TvB G 036 recto', 'TvB G 037 recto', 'TvB G 038 recto', 'TvB G 0382 recto', 'TvB G 039 recto', 'TvB G 040 recto', 'TvB G 041 recto', 'TvB G 042 recto', 'TvB G 043 recto', 'TvB G 044 recto', 'TvB G 045 recto', 'TvB G 046 recto', 'TvB G 047 recto', 'TvB G 048 recto', 'TvB G 049 recto', 'TvB G 050 recto', 'TvB G 051 recto', 'TvB G 0510 recto', 'TvB G 0512 recto', 'TvB G 052 recto', 'TvB G 053 recto', 'TvB G 054 recto', 'TvB G 055 recto', 'TvB G 056 recto', 'TvB G 0566 verso recto', 'TvB G 057 recto', 'TvB G 058 recto', 'TvB G 059a recto', 'TvB G 060 recto', 'TvB G 061 recto', 'TvB G 062 recto', 'TvB G 0623 verso recto', 'TvB G 063 recto', 'TvB G 064 recto', 'TvB G 065 recto', 'TvB G 066 recto', 'TvB G 0676 verso recto', 'TvB G 0712 recto', 'TvB G 0716 recto', 'TvB G 0875tif recto', 'TvB G 0894 _ recto', 'TvB G 0903 _ recto', 'TvB G 0916 recto', 'TvB G 0918 recto', 'TvB G 0919 recto', 'TvB G 0920 recto', 'TvB G 0921 recto', 'TvB G 0922 recto', 'TvB G 0930 recto', 'TvB G 0931 recto', 'TvB G 0932 recto', 'TvB G 0933 recto', 'TvB G 0934 recto', 'TvB G 0935 recto', 'TvB G 0936 recto', 'TvB G 0937 recto', 'TvB G 0938 recto', 'TvB G 0939 recto', 'TvB G 0940 recto', 'TvB G 0941 recto', 'TvB G 0948 recto', 'TvB G 0955 recto', 'TvB G 10-02 zonder nummer-01 recto', 'TvB G 1083 recto', 'TvB G 1338 recto', 'TvB G 1492 recto', 'TvB G 1570e recto', 'TvB G 1821 recto', 'TvB G 1941 recto', 'TvB G 1978 recto', 'TvB G 2110 verso recto', 'TvB G 2110 recto', 'TvB G 2111a recto', 'TvB G 2111b recto', 'TvB G 2274 recto', 'TvB G 2290- recto', 'TvB G 2303- recto', 'TvB G 2337- recto', 'TvB G 2416-01 recto', 'TvB G 2416-02 recto', 'TvB G 2416-03 recto', 'TvB G 2416-04 recto', 'TvB G 2539 recto', 'TvB G 2540 recto', 'TvB G 2541 recto', 'TvB G 2542 recto', 'TvB G 2543 recto', 'TvB G 26724 recto', 'TvB G 26780 recto', 'TvB G 2808 recto', 'TvB G 2809 recto', 'TvB G 2810 recto', 'TvB G 2811 recto', 'TvB G 2813 recto', 'TvB G 2814 recto', 'TvB G 2815-2824 verso recto', 'TvB G 2815-2824 recto', 'TvB G 2875 recto', 'TvB G 2878 recto', 'TvB G 2879 recto', 'TvB G 2880 recto', 'TvB G 2881 recto', 'TvB G 2884 recto', 'TvB G 2885 recto', 'TvB G 2890 recto', 'TvB G 2891 recto', 'TvB G 2892 recto', 'TvB G 3085 recto', 'TvB G 3180 recto', 'TvB G 3181 recto', 'TvB G 3182 recto', 'TvB G 3183 recto', 'TvB G 3184 recto', 'TvB G 3185 recto', 'TvB G 3398 recto', 'TvB G 3545 01 recto', 'TvB G 3545 02 recto', 'TvB G 3545 03 recto', 'TvB G 3545 04 recto', 'TvB G 3545 05 recto', 'TvB G 3545 06 recto', 'TvB G 3545 07 recto', 'TvB G 3545 recto recto', 'TvB G 3545 verso recto', 'TvB G 3558 recto recto', 'TvB G 3558 verso recto', 'TvB G 3559 recto recto', 'TvB G 3559 verso recto', 'TvB G 3560 recto recto', 'TvB G 3560 verso recto', 'TvB G 3575 recto', 'TvB G 3585 recto', 'TvB G 4088 recto', 'TvB G 4425-01 recto', 'TvB G 4425-02 recto', 'TvB G 4425-03 recto', 'TvB G 4425-04 recto', 'TvB G 4425-05 recto', 'TvB G 4425-06 recto', 'TvB G 4425-07 recto', 'TvB G 4425-08 recto', 'TvB G 4425-09 recto', 'TvB G 4425-10 recto', 'TvB G 4425-11 recto', 'TvB G 4425-12 recto', 'TvB G 4447 recto', 'TvB G 5355- recto', 'TvB G 5501_01 recto', 'TvB G 5501_02 recto', 'TvB G 5501_03 recto', 'TvB G 5501_04 recto', 'TvB G 5501_05 recto', 'TvB G 5501_06 recto', 'TvB G 5501_07 recto', 'TvB G 5501_08 recto', 'TvB G 5501_09 recto', 'TvB G 5501_10 recto', 'TvB G 5501_11 recto', 'TvB G 5561 recto', 'TvB G 5941_01 recto', 'TvB G 5941_02 recto', 'TvB G 5941_03 recto', 'TvB G 5941_04 recto', 'TvB G 5941_05 recto', 'TvB G 5942_01 recto', 'TvB G 5942_02 recto', 'TvB G 5942_03 recto', 'TvB G 5942_04 recto', 'TvB G 5942_05 recto', 'TvB G 5942_06 recto', 'TvB G 5942_07 recto', 'TvB G 5942_08 recto', 'TvB G 5942_09 recto', 'TvB G 5943_01 recto', 'TvB G 5943_02 recto', 'TvB G 5943_03 recto', 'TvB G 5943_04 recto', 'TvB G 5943_05 recto', 'TvB G 5943_06 recto', 'TvB G 5943_07 recto', 'TvB G 5943_08 recto', 'TvB G 5943_09 recto', 'TvB G 5943_10 recto', 'TvB G 5943_11 recto', 'TvB G 5943_12 recto', 'TvB G 5944_01 recto', 'TvB G 5944_02 recto', 'TvB G 5944_03 recto', 'TvB G 5944_04 recto', 'TvB G 5944_05 recto', 'TvB G 5944_06 recto', 'TvB G 5945_01 recto', 'TvB G 5945_02 recto', 'TvB G 5945_03 recto', 'TvB G 5945_04 recto', 'TvB G 5945_05 recto', 'TvB G 5946_01 recto', 'TvB G 5946_02 recto', 'TvB G 5946_03 recto', 'TvB G 5946_04 recto', 'TvB G 5946_05 recto', 'TvB G 5946_06 recto', 'TvB G 5946_07 recto', 'TvB G 5946_08 recto', 'TvB G 5946_09 recto', 'TvB G 5946_10 recto', 'TvB G 5946_11 recto', 'TvB G 5947_01 recto', 'TvB G 5947_02 recto', 'TvB G 5947_03 recto', 'TvB G 5947_04 recto', 'TvB G 5947_05 recto', 'TvB G 5948_01 recto', 'TvB G 5948_02 recto', 'TvB G 5948_03 recto', 'TvB G 5948_04 recto', 'TvB G 5948_05 recto', 'TvB G 5948_06 recto', 'TvB G 6089 recto', 'TvB G 6161 recto recto', 'TvB G 6161 verso recto', 'TvB G 6242 recto', 'TvB G 6546 verso recto', 'TvB G 6577 recto', 'TvB G 6580 recto', 'TvB G 6595 1 recto', 'TvB G 6596 1 recto', 'TvB G B 13 recto', 'TvB G B 133 recto', 'TvB G B 136 recto', 'TvB G B 148 recto', 'TvB G B 16 recto', 'TvB G B 32 recto', 'TvB G B 34 recto', 'TvB G B 41 recto', 'TvB G B 86 recto', 'TvB G B 87 recto', 'TvB G B 88 recto', 'TvB G B 89 recto', 'TvB G B 90 recto', 'TvB G B 91 recto', 'TvB G B 92 recto', 'TvB G B 93 recto', 'TvB G B 94 recto', 'TvB G B 95 recto', 'TvB G B 96 recto', 'TvB G B 97 recto', 'TvB G B 98 recto', 'TvB G BLAUW NR 1732 recto', 'TvB G dubbel nummer 1545 recto', 'TvB G dubbel nummer 1572 recto', 'TvB G geen nummer Rembrandt recto', 'TvB G Geen nummer-01 recto', 'TvB G geen nummer recto', 'TvB G Gerard Dumbar geen nummer recto', 'TvB G Glafey geen nummer recto', 'TvB G hoort bij 0427 - 0432 recto', 'TvB G Lambert geen nummer recto', 'TvB G Le Grand geen nummer recto', 'TvB G Lundius geen nummer recto', 'TvB G naar Rubens recto', 'TvB G Zonder nummer-04 recto', 'TvB G zonder nummer recto', 'TvB G zondernr_03 recto', 'TvB G5643 recto', 'TvB T 0003 recto', 'TvB T 0004 recto', 'TvB T 0005 recto', 'TvB T 0006 recto', 'TvB T 0007 recto', 'TvB T 0008 recto', 'TvB T 0009 recto', 'TvB T 0010 recto', 'TvB T 0011 recto', 'TvB T 0012 recto', 'TvB T 0013 recto', 'TvB T 0014 recto', 'TvB T 0015 recto', 'TvB T 0016 recto', 'TvB T 0017 recto', 'TvB T 0018 recto', 'TvB T 0019 recto', 'TvB T 0020 recto', 'TvB T 0021 recto', 'TvB T 0022 recto', 'TvB T 0023 recto', 'TvB T 0024 recto', 'TvB T 0025 recto', 'TvB T 0026 recto', 'TvB T 0027 recto', 'TvB T 0028 recto', 'TvB T 0029 recto', 'TvB T 0030 recto', 'TvB T 0031 recto', 'TvB T 0032 recto', 'TvB T 0033 recto', 'TvB T 0034 recto', 'TvB T 0035 recto', 'TvB T 0036 recto', 'TvB T 0037 recto', 'TvB T 0038 recto', 'TvB T 0039 recto', 'TvB T 0040 recto', 'TvB T 0041 recto', 'TvB T 0042 recto', 'TvB T 0043 recto', 'TvB T 0044 recto', 'TvB T 0045 recto', 'TvB T 0046 recto', 'TvB T 0047 recto', 'TvB T 0048 recto', 'TvB T 0049 recto', 'TvB T 0050 recto', 'TvB T 0051 recto', 'TvB T 0052 recto', 'TvB T 0053 recto', 'TvB T 0054 recto', 'TvB T 0055 recto', 'TvB T 0056 recto', 'TvB T 0057 recto', 'TvB T 0058 recto', 'TvB T 0059 recto', 'TvB T 0060 recto', 'TvB T 0061 recto', 'TvB T 0062 recto', 'TvB T 0063 recto', 'TvB T 0064 recto', 'TvB T 0065 recto', 'TvB T 0066 recto', 'TvB T 0067 recto', 'TvB T 0068 recto', 'TvB T 0069 recto', 'TvB T 0070 recto', 'TvB T 0071 recto', 'TvB T 0072 recto', 'TvB T 0073 recto', 'TvB T 0075 recto', 'TvB T 0076 recto', 'TvB T 0077 recto', 'TvB T 0078 recto', 'TvB T 0079 recto', 'TvB T 0080 recto', 'TvB T 0081 recto', 'TvB T 0082 recto', 'TvB T 0083 recto', 'TvB T 0084 recto', 'TvB T 0085 recto', 'TvB T 0086 recto', 'TvB T 0087 recto', 'TvB T 0088 recto', 'TvB T 0089 recto', 'TvB T 0090 recto', 'TvB T 0091 recto', 'TvB T 0092 recto', 'TvB T 0093 recto', 'TvB T 0094 recto', 'TvB T 0095 recto', 'TvB T 0096 recto', 'TvB T 0097 recto', 'TvB T 0098 recto', 'TvB T 0099 recto', 'TvB T 0100 recto', 'TvB T 0101 recto', 'TvB T 0102 recto', 'TvB T 0103 recto', 'TvB T 0104 recto', 'TvB T 0105 recto', 'TvB T 0106 recto', 'TvB T 0107 recto', 'TvB T 0108 recto', 'TvB T 0109 recto', 'TvB T 0110 recto', 'TvB T 0111 recto', 'TvB T 0112 recto', 'TvB T 0113 recto', 'TvB T 0114 recto', 'TvB T 0115 recto', 'TvB T 0116 recto', 'TvB T 0117 recto', 'TvB T 0118 recto', 'TvB T 0119 recto', 'TvB T 0120 recto', 'TvB T 0121 recto', 'TvB T 0122 recto', 'TvB T 0123 recto', 'TvB T 0124 recto', 'TvB T 0126 recto', 'TvB T 0127 recto', 'TvB T 0128 recto', 'TvB T 0129 recto', 'TvB T 0130 recto', 'TvB T 0131 recto', 'TvB T 0132 recto', 'TvB T 0133 recto', 'TvB T 0134 recto', 'TvB T 0135 recto', 'TvB T 0136 recto', 'TvB T 0137 recto', 'TvB T 0138 recto', 'TvB T 0139 recto', 'TvB T 0140 recto', 'TvB T 0141 recto', 'TvB T 0142 recto', 'TvB T 0143 recto', 'TvB T 0144 recto', 'TvB T 0145 recto', 'TvB T 0146 recto', 'TvB T 0147 recto', 'TvB T 0148 recto', 'TvB T 0149 recto', 'TvB T 0150 recto', 'TvB T 0151 recto', 'TvB T 0152a recto', 'TvB T 0152b recto', 'TvB T 0153 recto', 'TvB T 0154 recto', 'TvB T 0155 recto', 'TvB T 0156 recto', 'TvB T 0157 recto', 'TvB T 0158 recto', 'TvB T 0159 recto', 'TvB T 0160 recto', 'TvB T 0161 recto', 'TvB T 0162 recto', 'TvB T 0163 recto', 'TvB T 0164 recto', 'TvB T 0165 recto', 'TvB T 0166 recto', 'TvB T 0167 recto', 'TvB T 0168 recto', 'TvB T 0169 recto', 'TvB T 0170 recto', 'TvB T 0171 recto', 'TvB T 0172 recto', 'TvB T 0173 recto', 'TvB T 0174 recto', 'TvB T 0175 recto', 'TvB T 0176 recto', 'TvB T 0177 recto', 'TvB T 0178 recto', 'TvB T 0179 recto', 'TvB T 0180 recto', 'TvB T 0181 recto', 'TvB T 0182 recto', 'TvB T 0183 recto', 'TvB T 0184 recto', 'TvB T 0185 recto', 'TvB T 0186 recto', 'TvB T 0187 recto', 'TvB T 0188 recto', 'TvB T 0189 recto', 'TvB T 0190 recto', 'TvB T 0191 recto', 'TvB T 0192 recto', 'TvB T 0193 recto', 'TvB T 0194 recto', 'TvB T 0195 recto', 'TvB T 0196 recto', 'TvB T 0197 recto', 'TvB T 0198 kopie recto', 'TvB T 0198 recto', 'TvB T 0199 recto', 'TvB T 0200 recto', 'TvB T 0201 recto', 'TvB T 0202 recto', 'TvB T 0203 recto', 'TvB T 0204 recto', 'TvB T 0205 recto', 'TvB T 0206 recto', 'TvB T 0207 recto', 'TvB T 0208 recto', 'TvB T 0209 recto', 'TvB T 0210 recto', 'TvB T 0211 recto', 'TvB T 0212 recto', 'TvB T 0213 recto', 'TvB T 0214 recto', 'TvB T 0215 recto', 'TvB T 0216 recto', 'TvB T 0217 recto', 'TvB T 0218 recto', 'TvB T 0219 recto', 'TvB T 0220 recto', 'TvB T 0221 recto', 'TvB T 0222 recto', 'TvB T 0223 recto', 'TvB T 0224 recto', 'TvB T 0225 recto', 'TvB T 0226 recto', 'TvB T 0227 recto', 'TvB T 0228 recto', 'TvB T 0229 recto', 'TvB T 0230 recto', 'TvB T 0231 recto', 'TvB T 0232 recto', 'TvB T 0233 recto', 'TvB T 0234 recto', 'TvB T 0235 recto', 'TvB T 0236 recto', 'TvB T 0237 recto', 'TvB T 0238 recto', 'TvB T 0239 recto', 'TvB T 0240 recto', 'TvB T 0241 recto', 'TvB T 0242 recto', 'TvB T 0243 recto', 'TvB T 0244 recto', 'TvB T 0245 recto', 'TvB T 0246 recto', 'TvB T 0247 recto', 'TvB T 0248 recto', 'TvB T 0249 recto', 'TvB T 0250 recto', 'TvB T 0251 recto', 'TvB T 0252 recto', 'TvB T 0253 recto', 'TvB T 0255 recto', 'TvB T 0256 recto', 'TvB T 0257 recto', 'TvB T 0258 recto', 'TvB T 0259 recto', 'TvB T 0260 recto', 'TvB T 0261 recto', 'TvB T 0262 recto', 'TvB T 0263 recto', 'TvB T 0264 recto', 'TvB T 0265 recto', 'TvB T 0266 recto', 'TvB T 0267 recto', 'TvB T 0268 recto', 'TvB T 0269 recto', 'TvB T 0270 recto', 'TvB T 0271 recto', 'TvB T 0272 recto', 'TvB T 0273 recto', 'TvB T 0274 recto', 'TvB T 0275 recto', 'TvB T 0276 recto', 'TvB T 0277 recto', 'TvB T 0278 recto', 'TvB T 0279 recto', 'TvB T 0280 recto', 'TvB T 0281 recto', 'TvB T 0282 recto', 'TvB T 0283 recto', 'TvB T 0284 recto', 'TvB T 0285 recto', 'TvB T 0286 recto', 'TvB T 0287 recto', 'TvB T 0288 recto', 'TvB T 0289 recto', 'TvB T 0290 recto', 'TvB T 0291 recto', 'TvB T 0292 recto', 'TvB T 0293 recto', 'TvB T 0295 recto', 'TvB T 0296 recto', 'TvB T 0297 recto', 'TvB T 0298 recto', 'TvB T 0299 recto', 'TvB T 0300 recto', 'TvB T 0301 recto', 'TvB T 0302 recto', 'TvB T 0303 recto', 'TvB T 0304 recto', 'TvB T 0305 recto', 'TvB T 0306 recto', 'TvB T 0307 recto', 'TvB T 0308 recto', 'TvB T 0309 recto', 'TvB T 0310 recto', 'TvB T 0311 recto', 'TvB T 0312 recto', 'TvB T 0313 recto', 'TvB T 0314 recto', 'TvB T 0315 recto', 'TvB T 0316 recto', 'TvB T 0317 recto', 'TvB T 0318 recto', 'TvB T 0319 recto', 'TvB T 0320 recto', 'TvB T 0321 recto', 'TvB T 0323 recto', 'TvB T 0324 recto', 'TvB T 0325 recto', 'TvB T 0326 recto', 'TvB T 0327 recto', 'TvB T 0328 recto', 'TvB T 0329 recto', 'TvB T 0330 recto', 'TvB T 0331 recto', 'TvB T 0332 recto', 'TvB T 0333 recto', 'TvB T 0334 recto', 'TvB T 0335 recto', 'TvB T 0336 recto', 'TvB T 0337 recto', 'TvB T 0338 recto', 'TvB T 0339 recto', 'TvB T 0340 recto', 'TvB T 0341 recto', 'TvB T 0342 recto', 'TvB T 0343 recto', 'TvB T 0344 recto', 'TvB T 0345 recto', 'TvB T 0346 recto', 'TvB T 0347 recto', 'TvB T 0348 recto', 'TvB T 0349 recto', 'TvB T 0350 recto', 'TvB T 0351 recto', 'TvB T 0352 recto', 'TvB T 0353 recto', 'TvB T 0354 recto', 'TvB T 0355 recto', 'TvB T 0356 recto', 'TvB T 0357 recto', 'TvB T 0358 recto', 'TvB T 0359 recto', 'TvB T 0360 recto', 'TvB T 0361 recto', 'TvB T 0362 recto', 'TvB T 0363 recto', 'TvB T 0364 recto', 'TvB T 0365 recto', 'TvB T 0366 recto', 'TvB T 0367 recto', 'TvB T 0368 recto', 'TvB T 0369 recto', 'TvB T 0370 recto', 'TvB T 0371 recto', 'TvB T 0372 recto', 'TvB T 0373 recto', 'TvB T 0374 recto', 'TvB T 0375 recto', 'TvB T 0376 recto', 'TvB T 0377 recto', 'TvB T 0378 recto', 'TvB T 0379 recto', 'TvB T 0380-2 recto', 'TvB T 0380 recto', 'TvB T 0381 recto', 'TvB T 0382 recto', 'TvB T 0383 recto', 'TvB T 0384 recto', 'TvB T 0385 recto', 'TvB T 0386 recto', 'TvB T 0387 recto', 'TvB T 0388 recto', 'TvB T 0390 recto', 'TvB T 0391 recto', 'TvB T 0392 recto', 'TvB T 0393 recto', 'TvB T 0394 recto', 'TvB T 0395 recto', 'TvB T 0396 recto', 'TvB T 0397 recto', 'TvB T 0398 recto', 'TvB T 0399 recto', 'TvB T 0400 recto', 'TvB T 0401 recto', 'TvB T 0402 recto', 'TvB T 0403 recto', 'TvB T 0404 recto', 'TvB T 0405 recto', 'TvB T 0406 recto', 'TvB T 0407 recto', 'TvB T 0408 recto', 'TvB T 0409 recto', 'TvB T 0410 recto', 'TvB T 0411 recto', 'TvB T 0412 recto', 'TvB T 0413 recto', 'TvB T 0414 recto', 'TvB T 0415 recto', 'TvB T 0416 recto', 'TvB T 0417 recto', 'TvB T 0418 recto', 'TvB T 0419 recto', 'TvB T 0421 recto', 'TvB T 0422 recto', 'TvB T 0423 recto', 'TvB T 0424 recto', 'TvB T 0425 recto', 'TvB T 0426 recto', 'TvB T 0427 recto', 'TvB T 0428 recto', 'TvB T 0429 recto', 'TvB T 0430 recto', 'TvB T 0431 recto', 'TvB T 0432 recto', 'TvB T 0433 recto', 'TvB T 0434 recto', 'TvB T 0435 recto', 'TvB T 0436 recto', 'TvB T 0437 recto', 'TvB T 0438 recto', 'TvB T 0439 recto', 'TvB T 0440 recto', 'TvB T 0441 recto', 'TvB T 0442 recto', 'TvB T 0443 recto', 'TvB T 0444 recto', 'TvB T 0445 recto', 'TvB T 0446 recto', 'TvB T 0447 recto', 'TvB T 0448 recto', 'TvB T 0449 recto', 'TvB T 0450 recto', 'TvB T 0451 recto', 'TvB T 0452 recto', 'TvB T 0453 recto', 'TvB T 0454 recto', 'TvB T 0455 recto', 'TvB T 0456 recto', 'TvB T 0457 recto', 'TvB T 0458 recto', 'TvB T 0459 recto', 'TvB T 0460 recto', 'TvB T 0461 recto', 'TvB T 0462 recto', 'TvB T 0463 recto', 'TvB T 0464 recto', 'TvB T 0465 recto', 'TvB T 0466 recto', 'TvB T 0467 recto', 'TvB T 0468 recto', 'TvB T 0469 recto', 'TvB T 0470 recto', 'TvB T 0471 recto', 'TvB T 0472 recto', 'TvB T 0473 recto', 'TvB T 0474 recto', 'TvB T 0475 recto', 'TvB T 0476 recto', 'TvB T 0477 recto', 'TvB T 0478 recto', 'TvB T 0479 recto', 'TvB T 0480 recto', 'TvB T 0481 recto', 'TvB T 0482 recto', 'TvB T 0483 recto', 'TvB T 0485 recto', 'TvB T 0486 recto', 'TvB T 0487 recto', 'TvB T 0488 recto', 'TvB T 0489 recto', 'TvB T 0490 recto', 'TvB T 0491 recto', 'TvB T 0492 recto', 'TvB T 0493 recto', 'TvB T 0494 recto', 'TvB T 0495 recto', 'TvB T 0496 recto', 'TvB T 0497 recto', 'TvB T 0498 recto', 'TvB T 0499 recto', 'TvB T 0500 recto', 'TvB T 0501 recto', 'TvB T 0502 recto', 'TvB T 0503 recto', 'TvB T 0504 recto', 'TvB T 0505 recto', 'TvB T 0506 recto', 'TvB T 0507 recto', 'TvB T 0508 recto', 'TvB T 0509 recto', 'TvB T 0510 recto', 'TvB T 0511 recto', 'TvB T 0512 recto', 'TvB T 0513 recto', 'TvB T 0514 recto', 'TvB T 0515 recto', 'TvB T 0516 recto', 'TvB T 0517 recto', 'TvB T 0518 recto', 'TvB T 0519 recto', 'TvB T 0520 recto', 'TvB T 0521 recto', 'TvB T 0522 recto', 'TvB T 0523 recto', 'TvB T 0524 recto', 'TvB T 0525 recto', 'TvB T 0526 recto', 'TvB T 0527 recto', 'TvB T 0528 recto', 'TvB T 0529 recto', 'TvB T 0530 recto', 'TvB T 0531 recto', 'TvB T 0532 recto', 'TvB T 0533 recto', 'TvB T 0534 recto', 'TvB T 0535 recto', 'TvB T 0536 recto', 'TvB T 0537 recto', 'TvB T 0538 recto', 'TvB T 0539 recto', 'TvB T 0540 recto', 'TvB T 0541 recto', 'TvB T 0542 recto', 'TvB T 0543 recto', 'TvB T 0544 recto', 'TvB T 0545 recto', 'TvB T 0546 recto', 'TvB T 0547 recto', 'TvB T 0548 recto', 'TvB T 0549 recto', 'TvB T 0550 recto', 'TvB T 0551 recto', 'TvB T 0552 recto', 'TvB T 0553 recto', 'TvB T 0554 recto', 'TvB T 0555 recto', 'TvB T 0556 recto', 'TvB T 0557 recto', 'TvB T 0558 recto', 'TvB T 0559 recto', 'TvB T 0560 recto', 'TvB T 0561 recto', 'TvB T 0562 recto', 'TvB T 0563 recto', 'TvB T 0564 recto', 'TvB T 0565 recto', 'TvB T 0566 recto', 'TvB T 0567 recto', 'TvB T 0568 recto', 'TvB T 0569 recto', 'TvB T 0570- recto', 'TvB T 0570 recto', 'TvB T 0571 recto', 'TvB T 0572 recto', 'TvB T 0573 recto', 'TvB T 0574 recto', 'TvB T 0575 recto', 'TVB T 0576 recto', 'TvB T 0577 recto', 'TvB T 0578 recto', 'TvB T 0579 recto', 'TvB T 0580 recto', 'TvB T 0581 recto', 'TvB T 0582 recto', 'TvB T 0583 recto', 'TvB T 0584 recto', 'TvB T 0585 recto', 'TvB T 0586 recto', 'TvB T 0587 recto', 'TvB T 0588 recto', 'TvB T 0589 recto', 'TvB T 0590 recto', 'TvB T 0591 recto', 'TvB T 0592 recto', 'TvB T 0593 recto', 'TvB T 0594 recto', 'TvB T 0595 recto', 'TvB T 0596 recto', 'TvB T 0597 recto', 'TvB T 0598 recto', 'TvB T 0599 recto', 'TvB T 0600 recto', 'TvB T 0601 recto', 'TvB T 0602 recto', 'TvB T 0603 recto', 'TvB T 0604 recto', 'TvB T 0605 recto', 'TvB T 0606 recto', 'TvB T 0607 recto', 'TvB T 0608 recto', 'TvB T 0609 recto', 'TvB T 0610 recto', 'TvB T 0611 recto', 'TvB T 0612 recto', 'TvB T 0613 recto', 'TvB T 0614 recto', 'TvB T 0615 recto', 'TvB T 0616 recto', 'TvB T 0617 recto', 'TvB T 0618 recto', 'TvB T 0619 recto', 'TvB T 0620 recto', 'TvB T 0621 recto', 'TvB T 0622 recto', 'TvB T 0623 recto', 'TvB T 0624 recto', 'TvB T 0625 recto', 'TvB T 0626 recto', 'TvB T 0627 recto', 'TvB T 0628 recto', 'TvB T 0629 recto', 'TvB T 0630 recto', 'TvB T 0631 recto', 'TvB T 0632 recto', 'TvB T 0633 recto', 'TvB T 0634 recto', 'TvB T 0635 recto', 'TvB T 0636 recto', 'TvB T 0637 recto', 'TvB T 0638 recto', 'TvB T 0639 recto', 'TvB T 0640 recto', 'TvB T 0641 recto', 'TvB T 0642 recto', 'TvB T 0643 recto', 'TvB T 0644 recto', 'TvB T 0645 recto', 'TvB T 0646 recto', 'TvB T 0647 recto', 'TvB T 0648 recto', 'TvB T 0649 recto', 'TvB T 0650 recto', 'TvB T 0651 recto', 'TvB T 0652 recto', 'TvB T 0653 recto', 'TvB T 0654 recto', 'TvB T 0655 recto', 'TvB T 0656 recto', 'TvB T 0657 recto', 'TvB T 0658 recto', 'TvB T 0659 recto', 'TvB T 0660 recto', 'TvB T 0661 recto', 'TvB T 0662 recto', 'TvB T 0663 recto', 'TvB T 0664 recto', 'TvB T 0665 recto', 'TvB T 0666 recto', 'TvB T 0667 recto', 'TvB T 0668 recto', 'TvB T 0669 recto', 'TvB T 0670 recto', 'TvB T 0671 recto', 'TvB T 0672 recto', 'TvB T 0673 recto', 'TvB T 0674 recto', 'TvB T 0675 recto', 'TvB T 0676 recto', 'TvB T 0677 recto', 'TvB T 0678-0691_000 recto', 'TvB T 0678 recto', 'TvB T 0679 recto', 'TvB T 0680 recto', 'TvB T 0681 recto', 'TvB T 0682 recto', 'TvB T 0683 recto', 'TvB T 0684 recto', 'TvB T 0685 recto', 'TvB T 0686 recto', 'TvB T 0687 recto', 'TvB T 0688 recto', 'TvB T 0689 recto', 'TvB T 0690 recto', 'TvB T 0691 recto', 'TvB T 0692 recto', 'TvB T 0693 recto', 'TvB T 0694 recto', 'TvB T 0695 recto', 'TvB T 0696 recto', 'TvB T 0697 recto', 'TvB T 0698 recto', 'TvB T 0699 recto', 'TvB T 0700 recto', 'TvB T 0701 recto', 'TvB T 0702 recto', 'TvB T 0703 recto', 'TvB T 0704-0715 recto', 'TvB T 0704-715 recto', 'TvB T 0704 recto', 'TvB T 0705 recto', 'TvB T 0706 recto', 'TvB T 0707 recto', 'TvB T 0708 recto', 'TvB T 0709 recto', 'TvB T 0710 recto', 'TvB T 0711 recto', 'TvB T 0712 recto', 'TvB T 0713 recto', 'TvB T 0714 recto', 'TvB T 0715 recto', 'TvB T 0716-0727 recto', 'TvB T 0716 recto', 'TvB T 0717 recto', 'TvB T 0718 recto', 'TvB T 0719 recto', 'TvB T 0720 recto', 'TvB T 0721 recto', 'TvB T 0722 recto', 'TvB T 0723 recto', 'TvB T 0724 recto', 'TvB T 0725 recto', 'TvB T 0726 recto', 'TvB T 0727 recto', 'TvB T 0728-0739 recto', 'TvB T 0728 recto', 'TvB T 0729 recto', 'TvB T 0730 recto', 'TvB T 0731 recto', 'TvB T 0732 recto', 'TvB T 0733 recto', 'TvB T 0734 recto', 'TvB T 0735 recto', 'TvB T 0736 recto', 'TvB T 0737 recto', 'TvB T 0738 recto', 'TvB T 0740 recto', 'TvB T 0741 recto', 'TvB T 0742 recto', 'TvB T 0743 recto', 'TvB T 0744 recto', 'TvB T 0745 recto', 'TvB T 0746 recto', 'TvB T 0747 recto', 'TvB T 0748 recto', 'TvB T 0749 recto', 'TvB T 0750 recto', 'TvB T 0753 recto', 'TvB T 0754 recto', 'TvB T 0755 recto', 'TvB T 0756 recto', 'TvB T 0757 recto', 'TvB T 0758 recto', 'TvB T 0759 recto', 'TvB T 0760 recto', 'TvB T 0761 recto', 'TvB T 0762 recto', 'TvB T 0763 recto', 'TvB T 0764 recto', 'TvB T 0765 recto', 'TvB T 0766 recto', 'TvB T 0769 recto', 'TvB T 0770 recto', 'TvB T 0771 recto', 'TvB T 0772 recto', 'TvB T 0773 recto', 'TvB T 0774 recto', 'TvB T 0775 recto', 'TvB T 0776 recto', 'TvB T 0777 recto', 'TvB T 0778 recto', 'TvB T 0779 recto', 'TvB T 0780 recto', 'TvB T 0781 recto', 'TvB T 0782 recto', 'TvB T 0784 recto', 'TvBT 0183 recto', 'TvBT 0184 recto', 'TvBT 0185 recto', 'U 012 recto', 'U 029 recto', 'U 055 1 recto', 'U+ 026e recto', 'U+ 053 recto', 'U+ 054 recto', 'U+ 055 recto', 'V 009c detail_001 recto', 'V 009c detail_002 recto', 'V 009c hoort bij recto', 'V 009c_02 recto', 'V 028f recto', 'V 032b recto', 'V 033 LIII recto', 'V 033a-Geen nummer recto', 'V 033a-Ia recto', 'V 033a-Ib recto', 'V 033a-Ic recto', 'V 033a-II recto', 'V 033a-III recto', 'V 033a-IV recto', 'V 033a-IX recto', 'V 033a-L recto', 'V 033a-LI recto', 'V 033a-LII recto', 'V 033a-LIII recto', 'V 033a-LIV recto', 'V 033a-LIX recto', 'V 033a-LVI recto', 'V 033a-LVIIa recto', 'V 033a-LVIIb recto', 'V 033a-LVIII recto', 'V 033a-LX recto', 'V 033a-LXI recto', 'V 033a-LXII recto', 'V 033a-LXIII recto', 'V 033a-LXIV recto', 'V 033a-LXIX recto', 'V 033a-LXV recto', 'V 033a-LXVI recto', 'V 033a-LXVII recto', 'V 033a-LXVIII recto', 'V 033a-LXX recto', 'V 033a-LXXI recto', 'V 033a-LXXII recto', 'V 033a-LXXIII recto', 'V 033a-LXXIV recto', 'V 033a-LXXIX recto', 'V 033a-LXXV recto', 'V 033a-LXXVI recto', 'V 033a-LXXVII recto', 'V 033a-LXXVIII recto', 'V 033a-LXXXIII recto', 'V 033a-V recto', 'V 033a-VI recto', 'V 033a-VII recto', 'V 033a-VIII recto', 'V 033a-X recto', 'V 033a-XI recto', 'V 033a-XII recto', 'V 033a-XIII recto', 'V 033a-XIV recto', 'V 033a-XIX recto', 'V 033a-XL recto', 'V 033a-XLI recto', 'V 033a-XLII recto', 'V 033a-XLIII recto', 'V 033a-XLIV recto', 'V 033a-XLIX recto', 'V 033a-XLV recto', 'V 033a-XLVI recto', 'V 033a-XLVII recto', 'V 033a-XLVIII recto', 'V 033a-XV recto', 'V 033a-XVI recto', 'V 033a-XVII recto', 'V 033a-XVIII recto', 'V 033a-XX recto', 'V 033a-XXI recto', 'V 033a-XXII recto', 'V 033a-XXIII recto', 'V 033a-XXIV recto', 'V 033a-XXIX recto', 'V 033a-XXV recto', 'V 033a-XXVI recto', 'V 033a-XXVII recto', 'V 033a-XXVIII recto', 'V 033a-XXX recto', 'V 033a-XXXI recto', 'V 033a-XXXIII recto', 'V 033a-XXXIV recto', 'V 033a-XXXIX recto', 'V 033a-XXXV recto', 'V 033a-XXXVI recto', 'V 033a-XXXVII recto', 'V 033a-XXXVIII recto', 'V 040 recto', 'V 041 recto', 'V 042 recto', 'V 043 recto', 'V 048-02 recto', 'V 050a recto', 'V 063c recto', 'Van Marum recto', 'Van Trigt_012 recto', 'Van Trigt_012_b recto', 'van Trigt_057_01 recto', 'van Trigt_072a recto', 'van Trigt_110 recto', 'van Trigt_111 recto', 'van Trigt_112 recto', 'van Trigt_113 2 recto', 'van Trigt_113 recto', 'van Trigt_114 recto', 'van Trigt_115 recto', 'van Trigt_116 recto', 'van Trigt_117-1 recto', 'van Trigt_117-2 recto', 'van Trigt_118-1 recto', 'van Trigt_118-2 recto', 'van Trigt_119-1 recto', 'van Trigt_119-2 recto', 'van Trigt_120-1 recto', 'van Trigt_120-2 recto', 'van Trigt_121 recto', 'van Trigt_122 recto', 'van Trigt_123 recto', 'van Trigt_124 recto', 'van Trigt_125 recto', 'van Trigt_126 recto', 'van Trigt_127 recto', 'van Trigt_128 recto', 'van Trigt_129 recto', 'van Trigt_130 recto', 'van Trigt_131 recto', 'van Trigt_132 recto', 'van Trigt_133 recto', 'van Trigt_134 recto', 'van Trigt_135 recto', 'van Trigt_136 recto', 'van Trigt_137 recto', 'van Trigt_138 recto', 'van Trigt_139 recto', 'van Trigt_140 recto', 'van Trigt_141 recto', 'van Trigt_142 recto', 'van Trigt_143 recto', 'van Trigt_144 recto', 'van Trigt_145 recto', 'van Trigt_146 recto', 'van Trigt_147 recto', 'van Trigt_148 recto', 'van Trigt_149-2 recto', 'van Trigt_149-3 recto', 'van Trigt_149 recto', 'van Trigt_149a recto', 'van Trigt_150 recto', 'van Trigt_151 recto', 'van Trigt_152 recto', 'van Trigt_153 recto', 'van Trigt_154 recto', 'van Trigt_155 recto', 'van Trigt_156 recto', 'van Trigt_157 recto', 'van Trigt_158 recto', 'van Trigt_159 recto', 'van Trigt_160 recto', 'van Trigt_161 recto', 'van Trigt_162 recto', 'van Trigt_163 recto', 'van Trigt_164 recto', 'van Trigt_165 recto', 'van Trigt_166 recto', 'van Trigt_167 recto', 'van Trigt_168 recto', 'van Trigt_169 recto', 'van Trigt_170 recto', 'van Trigt_171 recto', 'van Trigt_172 recto', 'van Trigt_173 recto', 'van Trigt_174 recto', 'van Trigt_175 recto', 'van Trigt_176 recto', 'van Trigt_177 recto', 'van Trigt_178 recto', 'van Trigt_179 recto', 'van Trigt_180 recto', 'van Trigt_181 recto', 'van Trigt_182 recto', 'van Trigt_183 recto', 'van Trigt_184 recto', 'van Trigt_185 recto', 'van Trigt_186 recto', 'van Trigt_187 recto', 'van Trigt_188 recto', 'van Trigt_189 recto', 'van Trigt_190 recto', 'van Trigt_191 recto', 'van Trigt_192 recto', 'van Trigt_193 recto', 'van Trigt_194 recto', 'van Trigt_195-1 recto', 'van Trigt_195-2 recto', 'van Trigt_196 recto', 'van Trigt_197 recto', 'van Trigt_198-1 recto', 'van Trigt_198-2 recto', 'van Trigt_199-1 recto', 'van Trigt_199-2 recto', 'van Trigt_20-1 recto', 'van Trigt_200-1 recto', 'van Trigt_200-2 recto', 'van Trigt_201-1 recto', 'van Trigt_201-2 recto', 'van Trigt_202-1 recto', 'van Trigt_202-2 recto', 'van Trigt_203 recto', 'van Trigt_204-2 recto', 'van Trigt_205-1 recto', 'van Trigt_205-2 recto', 'van Trigt_206-1 recto', 'van Trigt_206-2 recto', 'van Trigt_207 recto', 'van Trigt_208 recto', 'van Trigt_209 recto', 'van Trigt_210 recto', 'van Trigt_211 recto', 'van Trigt_212 recto', 'van Trigt_213 recto', 'van Trigt_214 recto', 'van Trigt_215 recto', 'van Trigt_216-2 recto', 'van Trigt_216 recto', 'van Trigt_217 recto', 'van Trigt_218 recto', 'van Trigt_219 recto', 'van Trigt_220 recto', 'van Trigt_221 recto', 'van Trigt_222 recto', 'van Trigt_223-1 recto', 'van Trigt_223-2 recto', 'van Trigt_224 recto', 'van Trigt_225 recto', 'van Trigt_226 recto', 'van Trigt_227 recto', 'van Trigt_228 recto', 'van Trigt_229 recto', 'van Trigt_230 recto', 'van Trigt_231-1 recto', 'van Trigt_231-2 recto', 'van Trigt_232 recto', 'van Trigt_233 recto', 'van Trigt_234 recto', 'van Trigt_235 recto', 'van Trigt_236 recto', 'van Trigt_237 recto', 'van Trigt_238 recto', 'van Trigt_239 recto', 'van Trigt_240 recto', 'van Trigt_241 recto', 'van Trigt_242 recto', 'van Trigt_243 recto', 'van Trigt_244 recto', 'van Trigt_245 recto', 'van Trigt_246 recto', 'van Trigt_247 recto', 'van Trigt_248 recto', 'van Trigt_249 recto', 'van Trigt_250 recto', 'van Trigt_251 recto', 'van Trigt_252 recto', 'van Trigt_253 recto', 'van Trigt_254 recto', 'van Trigt_255-1 recto', 'van Trigt_255-2 recto', 'van Trigt_256 recto', 'van Trigt_257 recto', 'van Trigt_258 recto', 'van Trigt_259 recto', 'van Trigt_260 recto', 'van Trigt_261 recto', 'van Trigt_262 recto', 'van Trigt_263 recto', 'van Trigt_264 recto', 'van Trigt_265 recto', 'van Trigt_266 recto', 'van Trigt_267 recto', 'van Trigt_268-01 recto', 'van Trigt_268-2 recto', 'van Trigt_268-3 recto', 'van Trigt_268-4 recto', 'van Trigt_268-5 recto', 'van Trigt_268-6 recto', 'van Trigt_268-7 recto', 'van Trigt_269-1 recto', 'van Trigt_269-2 recto', 'van Trigt_269-3 recto', 'van Trigt_269-4 recto', 'van Trigt_269-5 recto', 'van Trigt_269-6 recto', 'van Trigt_270-1 recto', 'van Trigt_270-10 recto', 'van Trigt_270-11 recto', 'van Trigt_270-2 recto', 'van Trigt_270-3 recto', 'van Trigt_270-4 recto', 'van Trigt_270-5 recto', 'van Trigt_270-6 recto', 'van Trigt_270-7 recto', 'van Trigt_270-8 recto', 'van Trigt_270-9 recto', 'van Trigt_271 recto', 'van Trigt_272-1 recto', 'van Trigt_272-2 recto', 'van Trigt_272-3 recto', 'van Trigt_272-4 recto', 'van Trigt_272-5 recto', 'van Trigt_272-6 recto', 'van Trigt_273-1 recto', 'van Trigt_273-2 recto', 'van Trigt_273-3 recto', 'van Trigt_273-4 recto', 'van Trigt_273-5 recto', 'van Trigt_274-1 recto', 'van Trigt_274-2 recto', 'van Trigt_274-3 recto', 'van Trigt_274-4 recto', 'van Trigt_274-5 recto', 'van Trigt_274-6 recto', 'van Trigt_274-7 recto', 'van Trigt_275-1 recto', 'van Trigt_275-2 recto', 'van Trigt_275-3 recto', 'van Trigt_275-4 recto', 'van Trigt_276-1 recto', 'van Trigt_276-2 recto', 'van Trigt_276-3 recto', 'van Trigt_276-4 recto', 'van Trigt_276-5 recto', 'van Trigt_276-6 recto', 'van Trigt_277-1 recto', 'van Trigt_277-2 recto', 'van Trigt_277-3 recto', 'van Trigt_277-4 recto', 'van Trigt_277-5 recto', 'van Trigt_277-6 recto', 'van Trigt_277-7 recto', 'van Trigt_277-8 recto', 'van Trigt_277-9 recto', 'van Trigt_278-1 recto', 'van Trigt_278-2 recto', 'van Trigt_278-3 recto', 'van Trigt_278-4 recto', 'van Trigt_278-5 recto', 'van Trigt_278-6 recto', 'van Trigt_279-1 recto', 'van Trigt_279-2 recto', 'van Trigt_279-3 recto', 'van Trigt_28-1 recto', 'van Trigt_280-1 recto', 'van Trigt_280-2 recto', 'van Trigt_280-3 recto', 'van Trigt_280-4 recto', 'van Trigt_280-5 recto', 'van Trigt_280-6 recto', 'van Trigt_280-7 recto', 'van Trigt_280-8 recto', 'van Trigt_281-1 recto', 'van Trigt_281-2 recto', 'van Trigt_281-3 recto', 'van Trigt_281-4 recto', 'van Trigt_281-5 recto', 'van Trigt_281-6 recto', 'van Trigt_281-7 recto', 'van Trigt_281-8 recto', 'van Trigt_281-9 recto', 'van Trigt_282-1 recto', 'van Trigt_282-2 recto', 'van Trigt_282-3 recto', 'van Trigt_282-4 recto', 'van Trigt_282-5 recto', 'van Trigt_282-6 recto', 'van Trigt_282-7 recto', 'van Trigt_282-8 recto', 'van Trigt_283-1 recto', 'van Trigt_283-2 recto']
        
        fixed_list = []
        not_fixed_list = []

        for drawing in list_of_drawings:
            object_number = ""
            fixed = False

            if " verso" in drawing:
                object_number = drawing.replace(" verso", "")

            elif drawing[-1] == "p" or drawing[-1] == "a" or drawing[-1] == "c" or drawing[-1] == "d":
                object_number = drawing[:-1]

            elif drawing[-2:] == "_1":
                object_number = drawing[:-2]

            elif drawing[-3:] == "-max":
                object_number = drawing[:-3]

            elif len(drawing.split("_")) == 2:
                if len(drawing.split(" ")[:-1]) <= 4:
                    object_number = drawing.split('_')[0]

            elif len(drawing.split(" ")) == 3:
                if len(drawing.split(" ")[:-1]) <= 4:
                    object_number = " ".join(drawing.split(" ")[:-1])

            elif len(drawing.split("-")) == 2:
                if len(drawing.split("-")[1]) <= 4:
                    object_number = drawing.split("-")[0]

            elif "dubbel genummerd " in drawing or "Dubbel genummerd " in drawing:
                if len(drawing.split('-')) > 0:
                    object_number = drawing.split('-')[0].lower().replace("dubbel genummerd ", "")
                else:
                    object_number = drawing.lower().replace("dubbel genummerd ", "")

            elif drawing[:-5] == "verso":
                object_number = drawing[:-5]
                object_number += " verso"

            priref = self.convert_object_number_priref(object_number)

            if priref != "":
                fixed = True

            if fixed:
                # Outcome of the real object number
                result = self.has_object_number(fixed_list, object_number)
                if len(result) > 0:
                    draw_image = "%s%s" % (drawing, ".jpg")
                    result[0]['images'].append(draw_image)
                else:
                    draw_image = "%s%s" % (drawing, ".jpg")
                    new_object = {"number": object_number, "images":[draw_image]}
                    fixed_list.append(new_object)
            else:
                not_fixed_list.append(drawing)

        print "List of fixed drawings:"
        print fixed_list
        print "TOTAL: %s" % (str(len(fixed_list)))

        print "List of failed to fix drawings: "
        print not_fixed_list
        print "TOTAL: %s" % (str(len(not_fixed_list)))

        return


    def transform_coins(self):

        list_of_coins = ['GeenColl 0452', 'TMNK 00304a', 'TMNK 00667a', 'TMNK 00714a', 'TMNK 00754a', 'TMNK 00757a', 'TMNK 00772a', 'TMNK 00789a', 'TMNK 00823a', 'TMNK 00995a', 'TMNK 01063a', 'TMNK 01781a', 'TMNK 02087', 'TMNK 02247', 'TMNK 02606a', 'TMNK 02803', 'TMNK 02837', 'TMNK 02991b', 'TMNK 03065', 'TMNK 03068', 'TMNK 03134', 'TMNK 03141', 'TMNK 03144a', 'TMNK 03144b', 'TMNK 03201', 'TMNK 03202a', 'TMNK 03377a', 'TMNK 03408b', 'TMNK 03408c', 'TMNK 03647', 'TMNK 03719', 'TMNK 03828a', 'TMNK 03857b', 'TMNK 04328', 'TMNK 04423aa', 'TMNK 04423ab', 'TMNK 04465a', 'TMNK 04465b', 'TMNK 04583b', 'TMNK 04589b', 'TMNK 04627', 'TMNK 04642', 'TMNK 04676b', 'TMNK 04897', 'TMNK 04929b', 'TMNK 05045', 'TMNK 0527', 'TMNK 05372', 'TMNK 05796a', 'TMNK 05915a', 'TMNK 05915b', 'TMNK 05915c', 'TMNK 05915d', 'TMNK 06264a', 'TMNK 06809', 'TMNK 09645c', 'TMNK 10232a_', 'TMNK 10232b_', 'TMNK 10877a', 'TMNK 10993', 'TMNK 10994', 'TMNK 10995', 'TMNK 10997', 'TMNK 11001', 'TMNK 11002', 'TMNK 11020', 'TMNK 11021', 'TMNK 11031', 'TMNK 11051', 'TMNK 11052', 'TMNK 11058', 'TMNK 11067', 'TMNK 11072', 'TMNK 11077', 'TMNK 11079', 'TMNK 11084', 'TMNK 11090', 'TMNK 11093', 'TMNK 11096', 'TMNK 11097', 'TMNK 11106', 'TMNK 11109', 'TMNK 11110', 'TMNK 11111', 'TMNK 11112', 'TMNK 11130', 'TMNK 11132', 'TMNK 11137', 'TMNK 11138', 'TMNK 11139', 'TMNK 11140', 'TMNK 11150', 'TMNK 11159', 'TMNK 11209', 'TMNK 11234', 'TMNK 11253', 'TMNK 11259', 'TMNK 11275', 'TMNK 11279', 'TMNK 11300', 'TMNK 11403', 'TMNK 11404', 'TMNK 11405', 'TMNK 11406', 'TMNK 11408', 'TMNK 11412', 'TMNK 11414', 'TMNK 11418', 'TMNK 11432', 'TMNK 11458', 'TMNK 11459', 'TMNK 11467', 'TMNK 11473', 'TMNK 11474', 'TMNK 11479', 'TMNK 11481', 'TMNK 11490', 'TMNK 11491', 'TMNK 11499', 'TMNK 11748', 'TMNK 11782', 'TMNK 11783', 'TMNK 11784', 'TMNK 11785', 'TMNK 11808', 'TMNK 11851', 'TMNK 11856', 'TMNK 11895', 'TMNK 11910', 'TMNK 11912', 'TMNK 11913', 'TMNK 11916', 'TMNK 11917', 'TMNK 11919', 'TMNK 11922', 'TMNK 11925', 'TMNK 11926', 'TMNK 11927', 'TMNK 11928', 'TMNK 11929', 'TMNK 11930', 'TMNK 11931', 'TMNK 11932', 'TMNK 11933', 'TMNK 11935', 'TMNK 11938', 'TMNK 11939', 'TMNK 11940', 'TMNK 11941', 'TMNK 11943', 'TMNK 11944', 'TMNK 11945', 'TMNK 11946', 'TMNK 11949', 'TMNK 11950', 'TMNK 11951', 'TMNK 11952', 'TMNK 11953', 'TMNK 11954', 'TMNK 11956', 'TMNK 11957', 'TMNK 11958', 'TMNK 11959', 'TMNK 11961', 'TMNK 11962', 'TMNK 11963', 'TMNK 11964', 'TMNK 11966', 'TMNK 11968', 'TMNK 11969', 'TMNK 11970', 'TMNK 11971', 'TMNK 11972', 'TMNK 11973', 'TMNK 11974', 'TMNK 11975', 'TMNK 11976', 'TMNK 11977', 'TMNK 11978', 'TMNK 11979', 'TMNK 11981', 'TMNK 11982', 'TMNK 11983', 'TMNK 11987', 'TMNK 11988', 'TMNK 11989', 'TMNK 11990', 'TMNK 11991', 'TMNK 11992', 'TMNK 11995', 'TMNK 11996', 'TMNK 11997', 'TMNK 11998', 'TMNK 12033', 'TMNK 12034', 'TMNK 12038', 'TMNK 12039', 'TMNK 12040', 'TMNK 12046', 'TMNK 12047', 'TMNK 12049', 'TMNK 12050', 'TMNK 12051', 'TMNK 12052', 'TMNK 12053', 'TMNK 12054', 'TMNK 12056', 'TMNK 12057', 'TMNK 12058', 'TMNK 12059', 'TMNK 12060', 'TMNK 12061', 'TMNK 12063', 'TMNK 12064', 'TMNK 12065', 'TMNK 12066', 'TMNK 12070', 'TMNK 12071', 'TMNK 12072', 'TMNK 12073', 'TMNK 12075', 'TMNK 12076', 'TMNK 12077', 'TMNK 12078', 'TMNK 12079', 'TMNK 12080', 'TMNK 12081', 'TMNK 12082', 'TMNK 12083', 'TMNK 12084', 'TMNK 12085', 'TMNK 12088', 'TMNK 12090', 'TMNK 12091', 'TMNK 12092', 'TMNK 12093', 'TMNK 12094', 'TMNK 12096', 'TMNK 12097', 'TMNK 12098', 'TMNK 12099', 'TMNK 12100', 'TMNK 12101', 'TMNK 12102', 'TMNK 12103', 'TMNK 12104', 'TMNK 12105', 'TMNK 12106', 'TMNK 12107', 'TMNK 12108', 'TMNK 12109', 'TMNK 12110', 'TMNK 12111', 'TMNK 12112', 'TMNK 12113', 'TMNK 12114', 'TMNK 12115', 'TMNK 12116', 'TMNK 12117', 'TMNK 12118', 'TMNK 12119', 'TMNK 12120', 'TMNK 12121', 'TMNK 12122', 'TMNK 12123', 'TMNK 12124', 'TMNK 12125', 'TMNK 12126', 'TMNK 12127', 'TMNK 12128', 'TMNK 12129', 'TMNK 12130', 'TMNK 12131', 'TMNK 12132', 'TMNK 12133', 'TMNK 12134', 'TMNK 12135', 'TMNK 12136', 'TMNK 12137', 'TMNK 12138', 'TMNK 12139', 'TMNK 12140', 'TMNK 12141', 'TMNK 12142', 'TMNK 12143', 'TMNK 12144', 'TMNK 12145', 'TMNK 12146', 'TMNK 12147', 'TMNK 12148', 'TMNK 12149', 'TMNK 12152', 'TMNK 12153', 'TMNK 12154', 'TMNK 12155', 'TMNK 12156', 'TMNK 12157', 'TMNK 12158', 'TMNK 12159', 'TMNK 12169', 'TMNK 12188', 'TMNK 12225', 'TMNK 12235', 'TMNK 12237', 'TMNK 12241', 'TMNK 12244', 'TMNK 12258', 'TMNK 12262', 'TMNK 12301', 'TMNK 12303', 'TMNK 12304', 'TMNK 12305', 'TMNK 12306', 'TMNK 12307', 'TMNK 12308', 'TMNK 12309', 'TMNK 12310', 'TMNK 12311', 'TMNK 12312', 'TMNK 12313', 'TMNK 12314', 'TMNK 12315', 'TMNK 12316', 'TMNK 12317', 'TMNK 12318', 'TMNK 12319', 'TMNK 12320', 'TMNK 12321', 'TMNK 12322', 'TMNK 12323', 'TMNK 12324', 'TMNK 12325', 'TMNK 12326', 'TMNK 12331', 'TMNK 12332', 'TMNK 12333', 'TMNK 12334', 'TMNK 12335', 'TMNK 12336', 'TMNK 12337', 'TMNK 12338', 'TMNK 12339', 'TMNK 12340', 'TMNK 12341', 'TMNK 12342', 'TMNK 12343', 'TMNK 12344', 'TMNK 12345', 'TMNK 12346', 'TMNK 12347', 'TMNK 12348', 'TMNK 12349', 'TMNK 12350', 'TMNK 12352', 'TMNK 12386', 'TMNK 12387', 'TMNK 12388', 'TMNK 12389', 'TMNK 12390', 'TMNK 12391', 'TMNK 12392', 'TMNK 12393', 'TMNK 12394', 'TMNK 12395', 'TMNK 12396', 'TMNK 12397', 'TMNK 12398', 'TMNK 12399', 'TMNK 12400', 'TMNK 12401', 'TMNK 12402', 'TMNK 12403', 'TMNK 12404', 'TMNK 12405', 'TMNK 12406', 'TMNK 12407', 'TMNK 12408', 'TMNK 12409', 'TMNK 12410', 'TMNK 12411', 'TMNK 12412', 'TMNK 12413', 'TMNK 12414', 'TMNK 12415', 'TMNK 12416', 'TMNK 12417', 'TMNK 12418', 'TMNK 12419', 'TMNK 12420', 'TMNK 12421', 'TMNK 12422', 'TMNK 12423', 'TMNK 12424', 'TMNK 12425', 'TMNK 12426', 'TMNK 12427', 'TMNK 12428', 'TMNK 12429', 'TMNK 12430', 'TMNK 12431', 'TMNK 12432', 'TMNK 12433', 'TMNK 12434', 'TMNK 12435', 'TMNK 12436', 'TMNK 12437', 'TMNK 12438', 'TMNK 12439', 'TMNK 12440', 'TMNK 12441', 'TMNK 12442', 'TMNK 12443', 'TMNK 12444', 'TMNK 12445', 'TMNK 12446', 'TMNK 12449', 'TMNK 12451', 'TMNK 12452', 'TMNK 12453', 'TMNK 12454', 'TMNK 12455', 'TMNK 12456', 'TMNK 12457', 'TMNK 12459', 'TMNK 12460', 'TMNK 12461', 'TMNK 12462', 'TMNK 12465', 'TMNK 12466', 'TMNK 12467', 'TMNK 12468', 'TMNK 12469', 'TMNK 12470', 'TMNK 12471', 'TMNK 12472', 'TMNK 12472a', 'TMNK 12472b', 'TMNK 12473', 'TMNK 12474', 'TMNK 12475', 'TMNK 12476', 'TMNK 12477', 'TMNK 12478', 'TMNK 12479', 'TMNK 12480', 'TMNK 12481', 'TMNK 12482', 'TMNK 12483', 'TMNK 12484', 'TMNK 12486', 'TMNK 12488', 'TMNK 12489', 'TMNK 12490', 'TMNK 12493', 'TMNK 12494', 'TMNK 12497', 'TMNK 12498', 'TMNK 12499', 'TMNK 12500', 'TMNK 12502', 'TMNK 12504', 'TMNK 12505', 'TMNK 12507', 'TMNK 12508', 'TMNK 12509', 'TMNK 12513', 'TMNK 12515', 'TMNK 12516', 'TMNK 12518', 'TMNK 12519', 'TMNK 12520', 'TMNK 12521', 'TMNK 12522', 'TMNK 12523', 'TMNK 12524', 'TMNK 12525', 'TMNK 12526', 'TMNK 12527', 'TMNK 12528', 'TMNK 12529', 'TMNK 12530', 'TMNK 12531', 'TMNK 12532', 'TMNK 12533', 'TMNK 12534', 'TMNK 12535', 'TMNK 12536', 'TMNK 12537', 'TMNK 12538', 'TMNK 12539', 'TMNK 12540', 'TMNK 12541', 'TMNK 12542', 'TMNK 12543', 'TMNK 12544', 'TMNK 12545', 'TMNK 12546', 'TMNK 12547', 'TMNK 12549', 'TMNK 12550', 'TMNK 12551', 'TMNK 12552', 'TMNK 12553', 'TMNK 12554', 'TMNK 12555', 'TMNK 12556', 'TMNK 12557', 'TMNK 12558', 'TMNK 12559', 'TMNK 12560', 'TMNK 12561', 'TMNK 12562', 'TMNK 12563', 'TMNK 12565', 'TMNK 12566', 'TMNK 12567', 'TMNK 12568', 'TMNK 12569', 'TMNK 12570', 'TMNK 12571', 'TMNK 12572', 'TMNK 12573', 'TMNK 12574', 'TMNK 12575', 'TMNK 12576', 'TMNK 12577', 'TMNK 12578', 'TMNK 12579', 'TMNK 12580', 'TMNK 12581', 'TMNK 12582', 'TMNK 12583', 'TMNK 12584', 'TMNK 12585', 'TMNK 12586', 'TMNK 12587', 'TMNK 12588', 'TMNK 12760', 'TMNK 12764', 'TMNK 12766', 'TMNK 12791', 'TMNK 12792', 'TMNK 12796', 'TMNK 12798', 'TMNK 12799', 'TMNK 12800', 'TMNK 12801', 'TMNK 12802', 'TMNK 12804', 'TMNK 12805', 'TMNK 12806', 'TMNK 12807', 'TMNK 12808', 'TMNK 12809', 'TMNK 12810', 'TMNK 12811', 'TMNK 12812', 'TMNK 12813', 'TMNK 12814', 'TMNK 12815', 'TMNK 12816', 'TMNK 12817', 'TMNK 12818', 'TMNK 12819', 'TMNK 12820', 'TMNK 12821', 'TMNK 12822', 'TMNK 12823', 'TMNK 12824', 'TMNK 12825', 'TMNK 12826', 'TMNK 12827', 'TMNK 12828', 'TMNK 12829', 'TMNK 12830', 'TMNK 12831', 'TMNK 12832', 'TMNK 12833', 'TMNK 12834', 'TMNK 12835', 'TMNK 12836', 'TMNK 12837', 'TMNK 12838', 'TMNK 12839', 'TMNK 12840', 'TMNK 12841', 'TMNK 12842', 'TMNK 12849', 'TMNK 12850', 'TMNK 12851', 'TMNK 12852', 'TMNK 12853', 'TMNK 12854', 'TMNK 12855', 'TMNK 12856', 'TMNK 12857', 'TMNK 12858', 'TMNK 12859', 'TMNK 12860', 'TMNK 12861', 'TMNK 12862', 'TMNK 12863', 'TMNK 12864', 'TMNK 12865', 'TMNK 12866', 'TMNK 12867', 'TMNK 12868', 'TMNK 12869', 'TMNK 12870', 'TMNK 12871', 'TMNK 12872', 'TMNK 12873', 'TMNK 12874', 'TMNK 12875', 'TMNK 12876', 'TMNK 12877', 'TMNK 12878', 'TMNK 12879', 'TMNK 12880', 'TMNK 12881', 'TMNK 12882', 'TMNK 12883', 'TMNK 12884', 'TMNK 12885', 'TMNK 12886', 'TMNK 12887', 'TMNK 12888', 'TMNK 12889', 'TMNK 12890', 'TMNK 12891', 'TMNK 12892', 'TMNK 12893', 'TMNK 12894', 'TMNK 12895', 'TMNK 12896', 'TMNK 12897', 'TMNK 12898', 'TMNK 12899', 'TMNK 12900', 'TMNK 12901', 'TMNK 12902', 'TMNK 12903', 'TMNK 12904', 'TMNK 12905', 'TMNK 12906', 'TMNK 12907', 'TMNK 12908', 'TMNK 12909', 'TMNK 12910', 'TMNK 12911', 'TMNK 12912', 'TMNK 12913', 'TMNK 12914', 'TMNK 12915', 'TMNK 12916', 'TMNK 12917', 'TMNK 12918', 'TMNK 12919', 'TMNK 12920', 'TMNK 12921', 'TMNK 12922', 'TMNK 12923', 'TMNK 12924', 'TMNK 12925', 'TMNK 12926', 'TMNK 12927', 'TMNK 12928', 'TMNK 12929', 'TMNK 12930', 'TMNK 12931', 'TMNK 12932', 'TMNK 12933', 'TMNK 12934', 'TMNK 12935', 'TMNK 12936', 'TMNK 12937', 'TMNK 12938', 'TMNK 12939', 'TMNK 12940', 'TMNK 12941', 'TMNK 12942', 'TMNK 12943', 'TMNK 12944', 'TMNK 12945', 'TMNK 12946', 'TMNK 12947', 'TMNK 12948', 'TMNK 12949', 'TMNK 12950', 'TMNK 12951', 'TMNK 12952', 'TMNK 12953', 'TMNK 12954', 'TMNK 12955', 'TMNK 12956', 'TMNK 12957', 'TMNK 12958', 'TMNK 12959', 'TMNK 12960', 'TMNK 12961', 'TMNK 12962', 'TMNK 12963', 'TMNK 12964', 'TMNK 12965', 'TMNK 12966', 'TMNK 12967', 'TMNK 12968', 'TMNK 12969', 'TMNK 12970', 'TMNK 12971', 'TMNK 12972', 'TMNK 12973', 'TMNK 12974', 'TMNK 12975', 'TMNK 12976', 'TMNK 12977', 'TMNK 12978', 'TMNK 12979', 'TMNK 12980', 'TMNK 12981', 'TMNK 12982', 'TMNK 12983', 'TMNK 12984', 'TMNK 12985', 'TMNK 12986', 'TMNK 12987', 'TMNK 12988', 'TMNK 12989', 'TMNK 12990', 'TMNK 12991', 'TMNK 12992', 'TMNK 12993', 'TMNK 12994', 'TMNK 12995', 'TMNK 12996', 'TMNK 12997', 'TMNK 12998', 'TMNK 12999', 'TMNK 13000', 'TMNK 13001', 'TMNK 13002', 'TMNK 13003', 'TMNK 13004', 'TMNK 13005', 'TMNK 13006', 'TMNK 13007', 'TMNK 13008', 'TMNK 13009', 'TMNK 13010', 'TMNK 13011', 'TMNK 13012', 'TMNK 13013', 'TMNK 13014', 'TMNK 13015', 'TMNK 13016', 'TMNK 13017', 'TMNK 13018', 'TMNK 13019', 'TMNK 13020', 'TMNK 13021', 'TMNK 13022', 'TMNK 13023', 'TMNK 13024', 'TMNK 13025', 'TMNK 13026', 'TMNK 13027', 'TMNK 13028', 'TMNK 13029', 'TMNK 13030', 'TMNK 13031', 'TMNK 13034', 'TMNK 13035', 'TMNK 13036', 'TMNK 13037', 'TMNK 13038', 'TMNK 13039', 'TMNK 13040', 'TMNK 13041', 'TMNK 13042', 'TMNK 13043', 'TMNK 13044', 'TMNK 13045', 'TMNK 13046', 'TMNK 13047', 'TMNK 13049', 'TMNK 13050', 'TMNK 13051', 'TMNK 13052', 'TMNK 13053', 'TMNK 13054', 'TMNK 13055', 'TMNK 13056', 'TMNK 13057', 'TMNK 13058', 'TMNK 13059', 'TMNK 13060', 'TMNK 13061', 'TMNK 13062', 'TMNK 13063', 'TMNK 13064', 'TMNK 13065', 'TMNK 13066', 'TMNK 13067', 'TMNK 13068', 'TMNK 13069', 'TMNK 13070', 'TMNK 13071', 'TMNK 13072', 'TMNK 13073', 'TMNK 13074', 'TMNK 13075', 'TMNK 13076', 'TMNK 13077', 'TMNK 13078', 'TMNK 13079', 'TMNK 13080', 'TMNK 13081', 'TMNK 13082', 'TMNK 13083', 'TMNK 13084', 'TMNK 13085', 'TMNK 13086', 'TMNK 13087', 'TMNK 13088', 'TMNK 13089', 'TMNK 13090', 'TMNK 13091', 'TMNK 13092', 'TMNK 13093', 'TMNK 13094', 'TMNK 13095', 'TMNK 13096', 'TMNK 13097', 'TMNK 13098', 'TMNK 13099', 'TMNK 13100', 'TMNK 13101', 'TMNK 13102', 'TMNK 13103', 'TMNK 13104', 'TMNK 13105', 'TMNK 13106', 'TMNK 13107', 'TMNK 13108', 'TMNK 13109', 'TMNK 13110', 'TMNK 13111', 'TMNK 13112', 'TMNK 13113', 'TMNK 13114', 'TMNK 13115', 'TMNK 13116', 'TMNK 13117', 'TMNK 13118', 'TMNK 13119', 'TMNK 13120', 'TMNK 13121', 'TMNK 13122', 'TMNK 13123', 'TMNK 13124', 'TMNK 13125', 'TMNK 13126', 'TMNK 13127', 'TMNK 13128', 'TMNK 13129', 'TMNK 13130', 'TMNK 13131', 'TMNK 13132', 'TMNK 13133', 'TMNK 13134', 'TMNK 13135', 'TMNK 13136', 'TMNK 13137', 'TMNK 13138', 'TMNK 13139', 'TMNK 13140', 'TMNK 13141', 'TMNK 13142', 'TMNK 13143', 'TMNK 13144', 'TMNK 13145', 'TMNK 13146', 'TMNK 13147', 'TMNK 13148', 'TMNK 13149', 'TMNK 13150', 'TMNK 13151', 'TMNK 13152', 'TMNK 13153', 'TMNK 13154', 'TMNK 13155', 'TMNK 13156', 'TMNK 13157', 'TMNK 13158', 'TMNK 13159', 'TMNK 13160', 'TMNK 13161', 'TMNK 13162', 'TMNK 13163', 'TMNK 13165', 'TMNK 13166', 'TMNK 13167', 'TMNK 13168', 'TMNK 13169', 'TMNK 13170', 'TMNK 13171', 'TMNK 13172', 'TMNK 13173', 'TMNK 13174', 'TMNK 13175', 'TMNK 13176', 'TMNK 13177', 'TMNK 13178', 'TMNK 13179', 'TMNK 13180', 'TMNK 13181', 'TMNK 13182', 'TMNK 13183', 'TMNK 13184', 'TMNK 13185', 'TMNK 13186', 'TMNK 13187', 'TMNK 13188', 'TMNK 13189', 'TMNK 13190', 'TMNK 13191', 'TMNK 13192', 'TMNK 13193', 'TMNK 13194', 'TMNK 13195', 'TMNK 13196', 'TMNK 13197', 'TMNK 13198', 'TMNK 13199', 'TMNK 13200', 'TMNK 13201', 'TMNK 13202', 'TMNK 13203', 'TMNK 13204', 'TMNK 13205', 'TMNK 13206', 'TMNK 13208', 'TMNK 13209', 'TMNK 13210', 'TMNK 13211', 'TMNK 13212', 'TMNK 13213', 'TMNK 13214', 'TMNK 13215', 'TMNK 13216', 'TMNK 13217', 'TMNK 13218', 'TMNK 13219', 'TMNK 13220', 'TMNK 13221', 'TMNK 13222', 'TMNK 13223', 'TMNK 13224', 'TMNK 13225', 'TMNK 13226', 'TMNK 13228', 'TMNK 13229', 'TMNK 13230', 'TMNK 13231', 'TMNK 13232', 'TMNK 13233', 'TMNK 13234', 'TMNK 13235', 'TMNK 13236', 'TMNK 13237', 'TMNK 13238', 'TMNK 13239', 'TMNK 13240', 'TMNK 13241', 'TMNK 13242', 'TMNK 13243', 'TMNK 13244', 'TMNK 13245', 'TMNK 13246', 'TMNK 13247', 'TMNK 13248', 'TMNK 13249', 'TMNK 13250', 'TMNK 13251', 'TMNK 13252', 'TMNK 13253', 'TMNK 13254', 'TMNK 13255', 'TMNK 13256', 'TMNK 13257', 'TMNK 13258', 'TMNK 13259', 'TMNK 13260', 'TMNK 13261', 'TMNK 13262', 'TMNK 13263', 'TMNK 13264', 'TMNK 13265', 'TMNK 13266', 'TMNK 13267', 'TMNK 13268', 'TMNK 13269', 'TMNK 13270', 'TMNK 13271', 'TMNK 13272', 'TMNK 13273', 'TMNK 13274', 'TMNK 13275', 'TMNK 13276', 'TMNK 13277', 'TMNK 13278', 'TMNK 13279', 'TMNK 13280', 'TMNK 13281', 'TMNK 13282', 'TMNK 13283', 'TMNK 13284', 'TMNK 13285', 'TMNK 13286', 'TMNK 13287', 'TMNK 13288', 'TMNK 13289', 'TMNK 13290', 'TMNK 13291', 'TMNK 13292', 'TMNK 13293', 'TMNK 13294', 'TMNK 13295', 'TMNK 13296', 'TMNK 13297', 'TMNK 13298', 'TMNK 13299', 'TMNK 13300', 'TMNK 13301', 'TMNK 13302', 'TMNK 13303', 'TMNK 13304', 'TMNK 13305', 'TMNK 13306', 'TMNK 13307', 'TMNK 13308', 'TMNK 13309', 'TMNK 13310', 'TMNK 13311', 'TMNK 13312', 'TMNK 13313', 'TMNK 13314', 'TMNK 13315', 'TMNK 13316', 'TMNK 13317', 'TMNK 13318', 'TMNK 13319', 'TMNK 13320', 'TMNK 13321', 'TMNK 13322', 'TMNK 13323', 'TMNK 13324', 'TMNK 13325', 'TMNK 13326', 'TMNK 13327', 'TMNK 13328', 'TMNK 13329', 'TMNK 13330', 'TMNK 13331', 'TMNK 13332', 'TMNK 13333', 'TMNK 13334', 'TMNK 13335', 'TMNK 13336', 'TMNK 13337', 'TMNK 13338', 'TMNK 13339', 'TMNK 13340', 'TMNK 13341', 'TMNK 13342', 'TMNK 13343', 'TMNK 13344', 'TMNK 13345', 'TMNK 13346', 'TMNK 13347', 'TMNK 13348', 'TMNK 13349', 'TMNK 13350', 'TMNK 13351', 'TMNK 13352', 'TMNK 13353', 'TMNK 13357', 'TMNK 13358', 'TMNK 13359', 'TMNK 13360', 'TMNK 13361', 'TMNK 13362', 'TMNK 13363', 'TMNK 13364', 'TMNK 13365', 'TMNK 13366', 'TMNK 13367', 'TMNK 13368', 'TMNK 13369', 'TMNK 13370', 'TMNK 13371', 'TMNK 13372', 'TMNK 13373', 'TMNK 13375', 'TMNK 13376', 'TMNK 13377', 'TMNK 13378', 'TMNK 13379', 'TMNK 13380', 'TMNK 13382', 'TMNK 13386', 'TMNK 13387', 'TMNK 13388', 'TMNK 13574', 'TMNK 13575', 'TMNK 13576', 'TMNK 13577', 'TMNK 13578', 'TMNK 13579', 'TMNK 13580', 'TMNK 13581', 'TMNK 13582', 'TMNK 13583', 'TMNK 13584', 'TMNK 13585', 'TMNK 13586', 'TMNK 13587', 'TMNK 13588', 'TMNK 13589', 'TMNK 13590', 'TMNK 13591', 'TMNK 13592', 'TMNK 13593', 'TMNK 13594', 'TMNK 13595', 'TMNK 13596', 'TMNK 13597', 'TMNK 13598', 'TMNK 13599', 'TMNK 13600', 'TMNK 13601', 'TMNK 13602', 'TMNK 13603', 'TMNK 13604', 'TMNK 13605', 'TMNK 13606', 'TMNK 13607', 'TMNK 13608', 'TMNK 13609', 'TMNK 13610', 'TMNK 13611', 'TMNK 13612', 'TMNK 13613', 'TMNK 13614', 'TMNK 13615', 'TMNK 1992-0234', 'TMNK 1992-224', 'TMNK 1993-334', 'TMNK 1993-335', 'TMNK 1993-336', 'TMNK 1996-06', 'TMNK 1997-24', 'TMNK 1997-275', 'TMNK 1997-276', 'TMNK 1997-277', 'TMNK 1998-36', 'TMNK 1999-077', 'TMNK 1999-09', 'TMNK 1999-120', 'TMNK 1999-12', 'TMNK 1999-391', 'TMNK 2001-02', 'TMNK 2002-013', 'TMNK 2002-267-v', 'TMNK 61288']

        
        current = 0
        total = len(list_of_coins)
        new_ids = []

        for obj in list_of_coins:
            try:
                current += 1
                # FIRST TEST
                priref = self.convert_object_number_priref(obj)

                print "Test %s / %s" % (str(current), str(total))
                print "Testing: %s" % (obj)

                if priref == "":
                    if obj[-1] == "a":
                        
                        # TEST Without a
                        obj_without_a = obj[:-1] 
                        priref = self.convert_object_number_priref(obj_without_a)
                        
                        if priref != "":
                            new_ids.append({"original":obj, "fixed": obj_without_a})
                        else:
                            # TEST With a
                            obj_with_a = "%s%s" % (obj, "a")
                            priref = self.convert_object_number_priref(obj_with_a)
                            if priref != "":
                                new_ids.append({"original":obj, "fixed": obj_with_a})
                            else:
                                # TEST With b
                                obj_with_b = "%s%s" % (obj, "b")
                                priref = self.convert_object_number_priref(obj_with_b)
                                if priref != "":
                                    new_ids.append({"original":obj, "fixed": obj_with_b})
                                else:
                                    self.skipped_ids.append(obj)

                    elif obj[-1] == "b":
                        # TEST Without b
                        obj_without_b = obj[:-1] 
                        priref = self.convert_object_number_priref(obj_without_b)
                        
                        if priref != "":
                            new_ids.append({"original":obj, "fixed": obj_without_b})
                        else:
                            # TEST With b
                            obj_with_b = "%s%s" % (obj, "b")
                            priref = self.convert_object_number_priref(obj_with_b)
                            if priref != "":
                                new_ids.append({"original":obj, "fixed": obj_with_b})
                            else:
                                # TEST With a
                                obj_with_a = "%s%s" % (obj, "a")
                                priref = self.convert_object_number_priref(obj_with_a)
                                if priref != "":
                                    new_ids.append({"original":obj, "fixed": obj_with_a})
                                else:
                                    self.skipped_ids.append(obj)
                    
                    # No B or A in the end
                    else:
                        obj_with_a = "%s%s" % (obj, "a")
                        priref = self.convert_object_number_priref(obj_with_a)
                        if priref != "":
                            new_ids.append({"original":obj, "fixed": obj_with_a})
                        else:
                            # TEST With b
                            obj_with_b = "%s%s" % (obj, "b")
                            priref = self.convert_object_number_priref(obj_with_b)
                            if priref != "":
                                new_ids.append({"original":obj, "fixed": obj_with_b})
                            else:
                                self.skipped_ids.append(obj)
            except Exception as e:
                print "Errno: %s" %(e.errno)
                print "STRERROR: %s" %(e.strerror)
                self.skipped_ids.append(obj)
                pass

        print "New ID's found:"
        print new_ids
        print "TOTAL FIXED: %s" % (str(len(new_ids)))
        
        return

    def add_new_objects(self):
        print "Add new objects!"
        number = 0
        for obj in self.art_list:
            try:
                # Convert object number to priref
                priref = self.convert_object_number_priref(obj['number'])
                
                if priref != "":
                    self.fetch_object_api(priref, True)
                else:
                    if 'drawings' in self.image_folder:
                        obj['number'] = obj['number'] + " recto"
                        priref = self.convert_object_number_priref(obj['number'])
                        
                        if priref != "":
                            self.fetch_object_api(priref, True)
                        else:
                            self.skipped += 1
                            print "Skipped item: " + obj['number']
                            self.skipped_ids.append(obj['number'])
                    else:
                        self.skipped += 1
                        print "Skipped item: " + obj['number']
                        self.skipped_ids.append(obj['number'])
            except:
                print "== Skipped %s ==" %(obj['number'])
                self.skipped_ids.append(obj['number'])

            number += 1
            if number >= self.set_limit:
                self.success = True
                return

    def add_crops(self):
        print "Add crops!"
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_images = catalog(portal_type='Image', Language="all")

        total = len(all_images)
        current = 1
        
        print "Total of images: "+str(total)
        
        for res in all_images:
            transaction.begin()
            try:
                image = res.getObject()
                current += 1
                print "Cropping image %s / %s" %(str(current), str(total))
                imageObjectCreated(image, False)
            except:
                transaction.abort()
                self.skipped_ids.append(res.getObject().getId())
                pass
            transaction.commit()
    
        print "Finished cropping images"
        
        return

    def remove_duplicates(self):
        container = self.get_container()

        list_ids = []

        total = 0

        for obj in container:
            try:
                transaction.begin()
                item = container[obj]
                if item.portal_type == 'Object':
                    if item.identification_identification_objectNumber in list_ids:
                        total += 1
                        #container.manage_delObjects([obj])
                        #timestamp = datetime.datetime.today().isoformat()
                        #print "%s - Remove duplicate object %s" %(timestamp, obj)
                    else:
                        list_ids.append(item.identification_identification_objectNumber)

                transaction.commit()
            except:
                transaction.abort()
                raise

        print "Total of repeated items:"
        print total
        return



    def fix_all_tags(self):
        print "Fix all tags!"
        
        do_not_delete = ["top", "haagse school", "penningen 30 topstukken", "medals top 30", "frontpage", "font-page", "nederlandse romantiek"]
        
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        
        all_objects = catalog(portal_type='Object', Language="all")

        total = len(all_objects)
        current = 0

        print "Total of objects: "+str(total)

        for obj in all_objects:
            try:
                current += 1
                print "Fix object %s / %s" %(str(current), str(total))

                transaction.begin()

                # Get object
                item = obj.getObject()
        
                # Get object tags           
                object_tags = list(item.Subject())

                # Check current tags and save them
                if len(object_tags) > 0:
                    backup_tags = ";".join(object_tags)
                    item.object_tags = backup_tags

                # Delete tags that are not in the do_not_delete list
                new_tags_obj = []

                for tag in object_tags:
                    if tag in do_not_delete:
                        new_tags_obj.append(tag)

                # Set new tags
                print new_tags_obj
                item.setSubject(new_tags_obj)
                
                # reindex object Subject index
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Reindex object %s" %(timestamp, item.identification_identification_objectNumber)

                item.reindexObject(idxs=['Subject'])
                transaction.commit()
            except:
                transaction.abort();
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Skipped object %s" %(timestamp, item.identification_identification_objectNumber)
                self.skipped_ids.append(item.identification_identification_objectNumber)
                raise
        
        self.success = True
        print "Total of objects: "+str(total)
        
        return

    def unpublish_drawings(self):

        xmlFilePath = "/var/www/data/xml/unpublish2.xml"
        xmlDoc = etree.parse(xmlFilePath)

        root = xmlDoc.getroot()
        recordList = root.find("recordList")
        print "Found recordList"

        records = recordList.getchildren()
        print "Found "+str(len(records))+" records"

        container = self.get_container()
        workflowTool = getToolByName(container, 'portal_workflow')

        
        for record in records:
            try:
                if record.find('object_number') != None:
                    object_number = record.find('object_number').text

                    item = self.get_object_from_instance(object_number)

                    if item != None:
                        transaction.begin()
                        timestamp = datetime.datetime.today().isoformat()
                        print "%s - Unpublishing %s" % (timestamp, object_number)
                        workflowTool.doActionFor(item, 'reject')
                        transaction.commit()
            except:
                transaction.abort()
                pass

        return

    def unpublish_coins(self):

        xmlFilePath = "/var/www/teylers/migration/unpublish_coins.xml"
        xmlDoc = etree.parse(xmlFilePath)

        root = xmlDoc.getroot()

        records = root.findall('{http://www.filemaker.com/fmpdsoresult}ROW')

        container = self.get_container()
        workflowTool = getToolByName(container, 'portal_workflow')

        for record in records:
            try:
                if record.find('{http://www.filemaker.com/fmpdsoresult}F_2003_inventarisnummer') != None:
                    object_number = record.find('{http://www.filemaker.com/fmpdsoresult}F_2003_inventarisnummer').text
                    print "Try to unpublish: %s" %(object_number)
                    item = self.get_object_from_instance(object_number)

                    if item != None:
                        transaction.begin()
                        timestamp = datetime.datetime.today().isoformat()
                        print "%s - Unpublishing %s" % (timestamp, object_number)
                        workflowTool.doActionFor(item, 'reject')
                        transaction.commit()
            except:
                transaction.abort()
                pass

        return

    def add_view_to_coins(self):
        transaction.begin()
        print "Add view to coins"
        container = self.get_container()

        total = len(container)
        curr = 1

        for obj in container[:100]:
            print "%s / %s" %(str(curr), str(total))
            item = container[obj]
            if item.portal_type == "Object":
                current_view = item.getLayout()
                print current_view
                if current_view != "double_view":
                    item.setLayout("double_view")
            curr += 1
        transaction.commit()
        return  

    def add_view_to_instruments(self):
        container = self.get_container()
        transaction.begin()
        total = len(container)
        curr = 1

        for obj in container:
            print "%s / %s" %(str(curr), str(total))
            item = container[obj]
            if item.portal_type == "Object":
                current_view = item.getLayout()
                if current_view != "instruments_view":
                    item.setLayout("instruments_view")
            curr += 1
        transaction.commit()
        return

    def add_view_to_books(self):
        container = self.get_container()
        transaction.begin()
        total = len(container)
        curr = 1

        for obj in container:
            print "%s / %s" %(str(curr), str(total))
            item = container[obj]
            if item.portal_type == "Object":
                current_view = item.getLayout()
                if current_view != "book_view":
                    item.setLayout("book_view")
            curr += 1
        transaction.commit()
        return

    def add_view_to_drawings(self):
        container = self.get_container()
        
        total = len(container)
        curr = 1

        for obj in container:
            transaction.begin()
            print "%s / %s" %(str(curr), str(total))
            item = container[obj]
            if item.portal_type == "Object":
                current_view = item.getLayout()
                if current_view != "drawing_view":
                    item.setLayout("drawing_view")
            curr += 1
            transaction.commit()
        
        self.success = True
        return

    def delete_paintings(self):
        list_objn = ['KS 001', 'KS 002', 'KS 003', 'KS 004', 'KS 005', 'KS 006', 'KS 007', 'KS 008', 'KS 009', 'KS 010', 'KS 011', 'KS 013', 'KS 014', 'KS 016', 'KS 017', 'KS 019', 'KS 020', 'KS 021', 'KS 022', 'KS 023', 'KS 024', 'KS 025', 'KS 027', 'KS 028', 'KS 029', 'KS 030', 'KS 031', 'KS 032', 'KS 033', 'KS 034', 'KS 035', 'KS 036', 'KS 037', 'KS 038', 'KS 039', 'KS 041', 'KS 043', 'KS 044', 'KS 045', 'KS 046', 'KS 047', 'KS 048', 'KS 049', 'KS 051', 'KS 052', 'KS 056', 'KS 062', 'KS 064', 'KS 065', 'KS 066', 'KS 067', 'KS 068', 'KS 069', 'KS 071', 'KS 072', 'KS 073', 'KS 076', 'KS 077', 'KS 078', 'KS 079', 'KS 080', 'KS 081', 'KS 082', 'KS 083', 'KS 087', 'KS 088', 'KS 089', 'KS 090', 'KS 091', 'KS 092', 'KS 093', 'KS 094', 'KS 097', 'KS 098', 'KS 099', 'KS 100', 'KS 101', 'KS 103', 'KS 104', 'KS 105', 'KS 106', 'KS 108', 'KS 109', 'KS 110', 'KS 111', 'KS 112', 'KS 113', 'KS 114', 'KS 115', 'KS 116', 'KS 117', 'KS 118', 'KS 119', 'KS 121', 'KS 124', 'KS 125', 'KS 126', 'KS 127', 'KS 128', 'KS 129', 'KS 130', 'KS 131', 'KS 132', 'KS 133', 'KS 135', 'KS 136', 'KS 137', 'KS 138a', 'KS 139', 'KS 141', 'KS 142', 'KS 144', 'KS 145', 'KS 146', 'KS 148', 'KS 151', 'KS 156', 'KS 157', 'KS 160', 'KS 161', 'KS 165', 'KS 166', 'KS 167', 'KS 168', 'KS 169', 'KS 171', 'KS 174', 'KS 175', 'KS 176', 'KS 178', 'KS 180', 'KS 180a', 'KS 183', 'KS 186', 'KS 187', 'KS 190', 'KS 194', 'KS 195', 'KS 196', 'KS 1984 001', 'KS 1985 001', 'KS 1985 002', 'KS 1986 002', 'KS 1986 003', 'KS 1987 002', 'KS 1988 001', 'KS 1989 004', 'KS 1989 005', 'KS 1989 006', 'KS 1989 007', 'KS 1989 008', 'KS 1989 009', 'KS 1989 010', 'KS 1989 011', 'KS 1989 012', 'KS 1989 013', 'KS 1990 001', 'KS 1990 003', 'KS 1990 003a', 'KS 1990 004', 'KS 1990 005', 'KS 1990 007', 'KS 1990 008', 'KS 1990 009', 'KS 1990 010', 'KS 1990 012', 'KS 1990 013', 'KS 1990 014', 'KS 1990 015', 'KS 1990 016', 'KS 1990 023', 'KS 1990 025', 'KS 1991 002', 'KS 1991 003', 'KS 1992 001', 'KS 1992 002', 'KS 1994 001', 'KS 1995 004', 'KS 1996 002', 'KS 1996 003', 'KS 1998 001', 'KS 1998 002', 'KS 1998 003', 'KS 1999 002', 'KS 1999 003', 'KS 1999 004', 'KS 1999 005', 'KS 1999 006', 'KS 1999 007', 'KS 1999 008', 'KS 2000 001', 'KS 2000 002', 'KS 2000 003', 'KS 2000 004', 'KS 2000 005', 'KS 2000 007', 'KS 2000 008', 'KS 2003 002', 'KS 2004 001', 'KS 2005 001', 'KS 2008 001', 'KS 2009 001', 'KS 2010 001', 'KS 2011 001', 'KS 2014 003', 'KS 202', 'KS 206', 'KS 207', 'KS 208', 'KS 209', 'KS 210', 'KS 213', 'KS 216', 'KS 221', 'KS 222', 'KS 223', 'KS 224', 'KS 225', 'KS 225a', 'KS 226', 'KS 227', 'KS 228', 'KS 229', 'KS 230', 'KS 237', 'KS 239', 'KS 240', 'KS 241', 'KS 243', 'KS 244', 'KS 245', 'KS 246', 'KS 247', 'KS 248', 'KS 249', 'KS 250', 'KS 252', 'KS 255', 'KS 256', 'KS 258', 'KS 276', 'KS 281', 'KS 282', 'KS 283', 'KS 284', 'KS 285', '3014-000']
        container = self.get_container()
        total = 0
        for obj in container:
            item = container[obj]
            if item.portal_type == "Object":
                if item.identification_identification_objectNumber in list_objn:
                    container.manage_delObjects([obj])
                    total+=1
                    print total
        print total



    def update_all_objects(self):
        print "Update all object metadata"
        
        container = self.get_container()

        curr = 0
        total_c = len(container)
        for item in container:
            try:
                transaction.begin()
                obj = container[item]
                if obj.portal_type == "Object":

                    object_number = obj.identification_identification_objectNumber

                    if object_number != None:
                        if object_number not in ['FK 0487', 'FK 0278 1-6', 'FK 0508']:
                            print "Pass"
                            transaction.commit()
                            continue

                        if not self.is_book:
                            priref = self.convert_object_number_priref(object_number)
                        else:
                            priref = self.convert_shelf_priref(object_number)

                        if priref != "":
                            if not self.is_book:
                                object_data = self.fetch_object_api(priref, False)
                            else:
                                object_data = self.fetch_book_api(priref, False)

                            new_text = object_data['text'].replace('\n', '<br>')

                            text = RichTextValue(new_text, 'text/html', 'text/html')
                            
                            if self.is_book:
                                if self.is_en and object_data["translated_title"] != "":
                                    #obj.title = object_data['title']
                                    #obj.description = object_data['translated_title']
                                    print ""
                                else:
                                    print ""
                                    #obj.description = object_data['title']
                            else:
                                if self.is_en and object_data["translated_title"] != "":
                                    obj.title = object_data['translated_title']
                                else:
                                    obj.title = object_data['title']

                                obj.description = object_data['description']

                            obj.identification_identification_objectNumber = object_data['object_number']
                            obj.object_type = object_data['object_type']
                            obj.dating = object_data['dating']
                            obj.artist = object_data['artist']
                            obj.material = object_data['material']
                            obj.technique = object_data['technique']
                            obj.dimension = object_data['dimension']
                            obj.credit_line = object_data['credit_line']
                            obj.object_description = ""
                            obj.scientific_name = object_data['scientific_name']
                            obj.translated_title = object_data['translated_title']
                            obj.production_period = object_data['production_period']
                            obj.object_category = object_data['object_category']
                            obj.location = object_data['location']
                            obj.publisher = object_data['publisher']
                            #obj.inscription = object_data['inscription']
                            obj.fossil_dating = object_data['fossil_dating']
                            obj.digital_reference = object_data['digital_reference']
                            obj.illustrator = object_data["illustrator"]
                            obj.author = object_data["author"]
                            obj.production_notes = object_data['production_notes']
                            obj.text = text

                            if self.is_book:
                                obj.book_title = object_data['book_title']

                            timestamp = datetime.datetime.today().isoformat()
                            print "%s - Updated %s" % (timestamp, object_number)
                            curr += 1
                            print "Progress %s / %s" % (str(curr), str(total_c))
                            #if self.is_en:
                            
                            #obj.reindexObject()
                        else:
                            timestamp = datetime.datetime.today().isoformat()
                            print "%s - Not in API %s" % (timestamp, object_number)
                            self.skipped_ids.append(object_number)
                    else:
                        timestamp = datetime.datetime.today().isoformat()
                        print "%s - Not in API %s" % (timestamp, object_number)
                        self.skipped_ids.append(object_number)
                else:
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Item not Object %s - Skipping." % (timestamp, object_number)
                
                transaction.commit()
            except:
                transaction.abort()
                raise

        

        print "Finishing update of all objects metadata"
        return True


    def fetch_book_api(self, priref, create):
        print "Fetch Book %s from API." %(str(priref))

        API_REQ = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=priref=%s&xmltype=grouped" % (priref)
        xml_file = self.parse_api_doc(API_REQ)
        root = xml_file.getroot()

        recordList = root.find('recordList')
        records = recordList.getchildren()

        first_record = records[0]

        object_data = {
            "title": "",
            "dirty_id": "",
            "description": "",
            "artist": "",
            "text": "",
            "object_number": "",
            "object_type": "",
            "dating": "",
            "term": "",
            "material": "",
            "technique": "",
            "dimension": "",
            "credit_line": "",
            "object_description": "",
            "inscription": "",
            "scientific_name": "",
            "translated_title": "",
            "production_period": "",
            "object_category": "",
            "location": "",
            "publisher": "",
            "illustrator": "",
            "author": "",
            "fossil_dating": "",
            "digital_reference": "",
            "book_title": "",
            "production_notes": "",
            "tags": []
        }


        object_temp_data = {
            "production_date_end": "",
            "production_date_start": "",
            "dimensions": []
        }

        inscription_temp_data = []

        if first_record.find('shelf_mark') != None:
            object_data['object_number'] = self.trim_white_spaces(first_record.find('shelf_mark').text)

        if first_record.find('Object_name') != None:
            if first_record.find('Object_name').find('object_name') != None:
                object_data['object_type'] = self.trim_white_spaces(first_record.find('Object_name').find('object_name').text)
        
        if first_record.find('Title') != None:
            if first_record.find('Title').find('title').find('value') != None:
                object_data['title'] = self.trim_white_spaces(first_record.find('Title').find('title').find('value').text)

        if first_record.find('Technique') != None:
            if first_record.find('Technique').find('technique') != None:
                object_data['technique'] = self.trim_white_spaces(first_record.find('Technique').find('technique').text)
        

        #
        # Digital reference
        #

        if len(first_record.findall('Digital_reference')) > 0: 
            for reference in first_record.findall('Digital_reference'):
                ref_link = ""
                ref_title = ""
                if reference.find('digital_reference') != None:
                    ref_link = reference.find('digital_reference').text
                    if reference.find('digital_reference.description') != None:
                        if reference.find('digital_reference.description').find('value') != None:
                            ref_title = reference.find('digital_reference.description').find('value').text

                    object_data['digital_reference'] += "<a href='%s'>%s</a><p>" %(ref_link, ref_title)

        #
        # Update material
        #
        if first_record.findall('Material') != None:
            index = 0
            if len(first_record.findall('Material')) > 1:
                # Multiple material
                for material in first_record.findall('Material'):
                    index += 1
                    if material.find('material') != None:
                        if index != len(first_record.findall('Material')):
                            object_data['material'] += "%s, " %(self.trim_white_spaces(material.find('material').text))
                        else:
                            object_data['material'] += "%s" %(self.trim_white_spaces(material.find('material').text))
            # Single material
            elif len(first_record.findall('Material')) > 0:
                if first_record.findall('Material')[0].find('material') != None:
                    object_data['material'] = self.trim_white_spaces(first_record.findall('Material')[0].find('material').text)
        
        # priref
        if first_record.find('priref') != None:
            object_data['priref'] = self.trim_white_spaces(first_record.find('priref').text)

        # Creator

        creator_details = {
            "temp_name": "",
            "name": "",
            "date_of_birth": "",
            "date_of_death": "",
            "role": ""
        }

        list_of_autors = []
        
        if len(first_record.findall('Author')) > 0:
            for author in first_record.findall('Author'):
                if author.find("author.name") != None:
                    list_of_autors.append(self.transform_creator_name(author.find("author.name").text))

        creator_details["name"] = ", ".join(list_of_autors)

        ## ILLUSTRATOR
        if first_record.find('Illustrator') != None:
            if first_record.find('Illustrator').find('illustrator.name') != None:
                object_data['illustrator'] = self.transform_creator_name(first_record.find('Illustrator').find('illustrator.name').text)


        if first_record.find('year_of_publication') != None:
            object_temp_data["production_date_start"] = first_record.find('year_of_publication').text

        if first_record.find('material_type') != None:
            object_data["material"] = first_record.find('material_type').text

        if first_record.find('place_of_publication') != None:
            if first_record.find('place_of_publication').find('value') != None:
                object_data["location"] = first_record.find('place_of_publication').find('value').text

        if first_record.find('publisher') != None:
            object_data["publisher"] = self.transform_creator_name(first_record.find('publisher').text)

        lead_word = ""
        if first_record.find('Title') != None:
            if first_record.find('Title').find('lead_word') != None:
                if first_record.find('Title').find('lead_word').find('value') != None:
                    lead_word = first_record.find('Title').find('lead_word').find('value').text

        old_title = object_data["title"]
        if lead_word != "":
            new_title = "%s %s" %(lead_word, old_title)
            object_data["book_title"] = new_title
        else:
            object_data["book_title"] = old_title

        object_data["title"] = ""

        if first_record.find('Production') != None:
            if first_record.find('Production').find('creator') != None:
                creator_details["temp_name"] = self.trim_white_spaces(first_record.find('Production').find('creator').text)
            if first_record.find('Production').find('creator.date_of_birth') != None:
                creator_details["date_of_birth"] = self.trim_white_spaces(first_record.find('Production').find('creator.date_of_birth').text)
            if first_record.find('Production').find('creator.date_of_death') != None:
                creator_details["date_of_death"] = self.trim_white_spaces(first_record.find('Production').find('creator.date_of_death').text)
            if first_record.find('Production').find('creator.role') != None:
                creator_details["role"] = self.trim_white_spaces(first_record.find('Production').find('creator.role').text)

        if first_record.find('Production_date') != None:
            if first_record.find('Production_date').find('production.date.start') != None:
                object_temp_data['production_date_start'] = self.trim_white_spaces(first_record.find('Production_date').find('production.date.start').text) 
            if first_record.find('Production_date').find('production.date.end') != None:
                object_temp_data['production_date_end'] = self.trim_white_spaces(first_record.find('Production_date').find('production.date.end').text)
        if object_temp_data['production_date_start'] == "" and object_temp_data['production_date_end'] == "" and first_record.find('Production_date') != None:
            if first_record.find('Production_date').find('production.date.start.prec') != None:
                object_temp_data['production_date_start'] = first_record.find('Production_date').find('production.date.start.prec').text

        use_label = False

        if self.is_en:
            label_text = ""
            if len(first_record.findall('Label')) > 0:
                for label in first_record.findall('Label'):
                    if label.find('label.type') != None:
                        if len(label.find('label.type').findall('value')) > 0:
                            for value in label.find('label.type').findall('value'):
                                if (value.text == "WEBTEXT ENG") or (value.text == "website text ENG") or (value.text == "website-tekst ENG"):
                                    use_label = True
                                    if label.find('label.text') != None:
                                        label_text = label.find('label.text').text
                                        object_data["text"] = self.trim_white_spaces(label_text)
                                    break

            if use_label and label_text == "":
                if first_record.find('Label').find('label.text') != None:
                        object_data["text"] = self.trim_white_spaces(first_record.find('Label').find('label.text').text)
        else:
            if first_record.find('Label') != None:
                if first_record.find('Label').find('label.text') != None:
                    object_data["text"] = self.trim_white_spaces(first_record.find('Label').find('label.text').text)

        if self.is_en:
            if first_record.find('title.translation') != None:
                object_data["translated_title"] = first_record.find('title.translation').text

        if first_record.findall('Dimension') != None:
            for d in first_record.findall('Dimension'):
                if d.find('dimension.part') != None:
                    new_dimension = {
                        "part": "",
                        "value": "",
                        "type": "",
                        "unit": ""
                    }

                    new_dimension['part'] = self.trim_white_spaces(d.find('dimension.part').text)

                    if d.find('dimension.value') != None:
                        new_dimension['value'] = self.trim_white_spaces(d.find('dimension.value').text)
                    if d.find('dimension.type') != None:
                        new_dimension['type'] = self.trim_white_spaces(d.find('dimension.type').text)
                    if d.find('dimension.unit') != None:
                        new_dimension['unit'] = self.trim_white_spaces(d.find('dimension.unit').text)
                    
                    object_temp_data['dimensions'].append(new_dimension)
                else:
                    new_dimension = {
                        "part": "",
                        "value": "",
                        "type": "",
                        "unit": ""
                    }

                    if d.find('dimension.value') != None:
                        new_dimension['value'] = self.trim_white_spaces(d.find('dimension.value').text)
                    if d.find('dimension.type') != None:
                        new_dimension['type'] = self.trim_white_spaces(d.find('dimension.type').text)
                    if d.find('dimension.unit') != None:
                        new_dimension['unit'] = self.trim_white_spaces(d.find('dimension.unit').text)
                    
                    object_temp_data['dimensions'].append(new_dimension)
            

        if len(first_record.findall('Content_subject')) > 0:
            for tag in first_record.findall('Content_subject'):
                if tag.find('content.subject') != None:
                    object_data['tags'].append(self.trim_white_spaces(tag.find('content.subject').text))

        # Credit line
        if first_record.find('credit_line') != None:
            object_data['credit_line'] = self.trim_white_spaces(first_record.find('credit_line').text)


        # Descriptions
        if len(first_record.findall('Description')) != None:
            for desc in first_record.findall('Description'):
                if desc.find('description') != None:
                    object_data['object_description'] += self.trim_white_spaces(desc.find('description').text)
                    object_data['object_description'] += "\n"

        if len(first_record.findall('Inscription')) != None:
            for inscription in first_record.findall('Inscription'):
                if inscription.find('inscription.content') != None:
                    if inscription.find('inscription.content').text != "":
                        if inscription.find('inscription.type') != None:
                            inscription_temp_data.append({
                                "content": self.trim_white_spaces(inscription.find('inscription.content').text),
                                "type": self.trim_white_spaces(inscription.find('inscription.type').text)
                            })

        # Scientific name
        if first_record.find('Taxonomy') != None:
            if first_record.find('Taxonomy').find('taxonomy.scientific_name') != None:
                object_data['scientific_name'] = self.trim_white_spaces(first_record.find('Taxonomy').find('taxonomy.scientific_name').text)

        object_data['inscription'] = self.create_inscription_field(inscription_temp_data)

        if ("books" in self.image_folder) or ("boeken" in self.folder_path):
            creator_details["name"] = creator_details["name"]
            object_data["author"] = creator_details["name"]
        else:   
            creator_details["name"] = self.transform_creator_name(creator_details['temp_name'])
            object_data['artist'] = self.create_creator_field(creator_details)

        object_data['dimension'] = self.create_dimension_field(object_temp_data)
        object_data['dating'] = self.create_object_production(object_temp_data['production_date_start'], object_temp_data['production_date_end'])

        if first_record.find('object_category') != None:
            object_data['object_category'] = first_record.find('object_category').text

        object_data['dirty_id'] = self.create_object_dirty_id(object_data['object_number'], object_data['title'], object_data['artist'])

        if create:
            self.create_new_object(object_data)
        else:
            return object_data

    def add_books(self):
        API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(shelf_mark='%s')&xmltype=structured"
        API_REQUEST_ALL_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(%s)&xmltype=structured"

        number = 0

        for obj in self.art_list:
            priref = self.convert_shelf_priref(obj['number'])
            if priref != "":    
                self.fetch_book_api(priref, True)

            number += 1
            if number >= self.set_limit:
                break

        self.success = True
        return True

    def add_all_books(self):
        API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(shelf_mark='%s')&xmltype=structured"
        API_REQUEST_ALL_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(%s)&xmltype=structured"

        """books_path = "/var/www/teylers/migration/books/"
        directory_walk = os.walk(books_path)
        all_directories = [x[0] for x in directory_walk]

        image_folders = [f for f in all_directories if ' jpgs' in f]

        list_of_failed_from_api = []
        list_of_books = []
        
        for folder in image_folders:
            object_number_with_jpg = folder.split('/')[-1]
            object_number = object_number_with_jpg.replace(" jpgs", "")
            folder_name = folder.decode('utf8')
            images = os.listdir(folder_name)
            sorted_images = sorted(images)
            list_of_books.append({"number":object_number, "path": folder_name, "images": sorted_images})
        """

        number = 0
        
        """self.art_list = [{
            "number":"75f 213 / lade IXb 213", 
            "path":"/var/www/teylers/migration/books/20  Java, deszelfs gedaante, bekleeding en inwendige structuur/Lade 9b 213 jpg",
            "images": os.listdir("/var/www/teylers/migration/books/20  Java, deszelfs gedaante, bekleeding en inwendige structuur/Lade 9b 213 jpg")
            }]
        """

        ## MODEL
        """{
            "number":"139e 52", 
            "path":"/var/www/teylers/migration/books/26  The birds of Australia.", 
            "folders": [
                {"name": "", "images":os.listdir(""), "images_path": ""},
            ],
            "pdfs": [
                
            ]
        }"""

        self.set_limit = 1000

        if self.is_multiple_book:
            for obj in self.art_list:
                for folder in obj["folders"]:
                    folder["images"].sort()
        
        for obj in self.art_list:
            if not self.is_multiple_book:
                obj["images"].sort()

            try:
                priref = self.convert_shelf_priref(obj['number'])
                if priref != "":
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Got from API %s" % (timestamp, obj["number"])
                    self.fetch_book_api(priref, True)
                else:
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Not in API %s" % (timestamp, obj["number"])
                    list_of_failed_from_api.append(obj['number'])
                    self.skipped_ids.append(obj['number'])

                number += 1
                if number >= self.set_limit:
                    break
            except:
                print "%s - Unexpected error on %s" % (timestamp, obj["number"])
                self.skipped_ids.append(obj['number'])
                raise

        self.success = True
        return True

    def get_all_ids(self):
        print "Get all ids"
        objs_numbers = []
        container = self.get_container()

        for obj in container:
            item = container[obj]
            if item.portal_type == "Object":
                objs_numbers.append(item.identification_identification_objectNumber)

        print "ids:"
        print objs_numbers
        return True

    def get_all_sketch_books(self):
        print "Get all sketch books"
        
        sketch_books = []

        container = self.get_container()

        for obj in container:
            item = container[obj]
            if item.portal_type == "Object":
                if hasattr(item, 'slideshow'):
                    slideshow = item['slideshow']
                    total = len(slideshow.objectIds())
                    if total > 5:
                        sketch_books.append(item.absolute_url())


        print sketch_books
        print "TOTAL sketch books:"
        print len(sketch_books)

        self.success = True
        return

    def get_drawings_list(self):
        API_REQUEST_URL_DRAWINGS = "http://teylers.adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&limit=20000&search=(object_name=tekening)&xmltype=grouped"
        xml_doc = self.parse_api_doc(API_REQUEST_URL_DRAWINGS)
        
        root = xml_doc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        return records

    def get_coins_list(self):
        API_REQUEST_URL_DRAWINGS = "http://teylers.adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&limit=20000&search=(object_name=%27munt%27%20or%20object_name=%27penning%27)&xmltype=grouped"
        xml_doc = self.parse_api_doc(API_REQUEST_URL_DRAWINGS)
        
        root = xml_doc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        return records

    def find_all_blank_objects(self):
        container = self.get_container()

        total = 0
        not_deleted = []

        for brain in container:
            item = container[brain]
            if item.portal_type == 'Object':
                if hasattr(item, 'slideshow'):
                    slideshow = item['slideshow']
                    if len(slideshow.objectIds()) == 0:
                        try:
                            container.manage_delObjects([brain])
                            timestamp = datetime.datetime.today().isoformat()
                            print "[%s] Object deleted %s." %(timestamp, item.identification_identification_objectNumber)
                            total += 1
                        except:
                            timestamp = datetime.datetime.today().isoformat()
                            print "[%s] ERROR. Object not deleted %s." %(timestamp, item.identification_identification_objectNumber)
                            not_deleted.append(item.identification_identification_objectNumber)
                            pass

        print "Total of blank drawings"
        print total
        print "Failed to delete list:"
        print not_deleted

        self.success = True
        return True

    def remove_all_unpublished(self):
        container = self.get_container()

        pw = getToolByName(container, 'portal_workflow')

        total = 0
        total_unpublished = 0
        try:
            for obj in container:
                transaction.begin()

                item = container[obj]
                if item.portal_type == "Object":
                    total += 1
                    review_state = pw.getInfoFor(item, 'review_state')
                    if review_state != "published":
                        if item.identification_identification_objectNumber == None:
                            container.manage_delObjects([obj])
                            timestamp = datetime.datetime.today().isoformat()
                            print "[%s] Object deleted [%s] - %s." %(timestamp, item.identification_identification_objectNumber, obj)
                            total_unpublished += 1
                            print "Progress: %s / %s" %(str(total), str(len(container)))

                transaction.commit()
        except:
            transaction.abort()
            raise

        print "Total unpublished state:"
        print total
        self.success = True
        return




    ####
    #### ZM Migration
    ####

    def get_identification_fieldset(self, object_data, first_record):
        # Institution_name
        if first_record.find('institution.name') != None:
            if first_record.find('institution.name').find('name') != None:
                object_data['identification_identification_institutionName'] = self.trim_white_spaces(first_record.find('institution.name').find('name').text)

        # Administrative_name
        if first_record.find('administration_name') != None:
            object_data['identification_identification_administrativeName'] = self.trim_white_spaces(first_record.find('administration_name').text)

        # Collection
        """ class ICategory(Interface):
            term = schema.TextLine(title=_(u'Collection'), required=False)"""

        collection = []
        if len(first_record.findall('collection')) > 0:
            for col in first_record.findall('collection'):
                if col.find('term') != None:
                    collection.append({
                        "term": col.find('term').text
                    })

        object_data["identification_identification_collection"] = collection

        # Object number
        if first_record.find('object_number') != None:
            object_data['identification_identification_objectNumber'] = self.trim_white_spaces(first_record.find('object_number').text)

        # Title
        if first_record.find('title') != None:
            object_data['title'] = self.trim_white_spaces(first_record.find('title').text)

        # Description
        if first_record.find('description') != None:
            object_data['description'] = self.trim_white_spaces(first_record.find('description').text)

        # Part
        if first_record.find('part') != None:
            object_data['identification_identification_part'] = self.trim_white_spaces(first_record.find('part').text)

        # Tot number
        if first_record.find('number_of_parts') != None:
            object_data['identification_identification_totNumber'] = self.trim_white_spaces(first_record.find('number_of_parts').text)

        # Copy number
        if first_record.find('copy_number') != None:
            object_data['identification_identification_copyNumber'] = self.trim_white_spaces(first_record.find('copy_number').text)

        # Edition
        if first_record.find('edition') != None:
            object_data['identification_identification_edition'] = self.trim_white_spaces(first_record.find('edition').text)

        # Distinguish_features
        if first_record.find('distinguishing_features') != None:
            object_data['identification_identification_distinguishFeatures'] = self.trim_white_spaces(first_record.find('distinguishing_features').text)

        # Object category
        """ class ICategory(Interface):
            term = schema.TextLine(title=_(u'Collection'), required=False)"""

        object_category = []

        if len(first_record.findall('object_category')) > 0:
            for cat in first_record.findall('object_category'):
                if cat.find('term') != None:
                    object_category.append({
                        "term": cat.find('term').text
                        })

        object_data["identification_objectName_objectCategory"] = object_category
    
        # Object name
        object_name = []
        """class IObjectName(Interface):
            name = schema.TextLine(title=_(u'Object name'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        if len(first_record.findall('object_name')) > 0:
            for name in first_record.findall('object_name'):
                if name.find('term') != None:
                    object_name.append({
                        "name":self.trim_white_spaces(name.find('term').text),
                        "type":"",
                        "notes":""
                        })

        if len(object_name) > 0:
            # Object name type
            if len(first_record.findall('object_name.type')) > 0:
                for slot, object_name_type in enumerate(first_record.findall('object_name.type')):
                    if object_name_type.find('term') != None:
                        object_name[slot]["type"] = object_name_type.find('term').text

            # Object name notes
            if len(first_record.findall('object_name.notes')) > 0:
                for slot, object_name_notes in enumerate(first_record.findall('object_name.notes')):
                    object_name[slot]["notes"] = object_name_notes.text      
        
        object_data['identification_objectName_objectName'] = object_name

        # Other name
        other_names = []
        """class IOtherName(Interface):
            name = schema.TextLine(title=_(u'Other name'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)"""

        if len(first_record.findall('other_name')) > 0:
            for other_name in first_record.findall('other_name'):
                other_names.append({
                    "name":self.trim_white_spaces(other_name.text),
                    "type":""                        
                })

        if len(other_names) > 0:
            # Other name type
            if len(first_record.findall('other_name.type')) > 0:
                for slot, other_name_type in enumerate(first_record.findall('other_name.type')):
                    other_names[slot]["type"] = other_name_type.text      
        
        object_data['identification_objectName_otherName'] = other_names

        # identification_title_notes
        if first_record.find('title.notes') != None:
            object_data['identification_titleDescription_notes'] = self.trim_white_spaces(first_record.find('title.notes').text)

        # identification_translated_title
        if first_record.find('title.translation') != None:
            object_data['identification_titleDescription_translatedTitle'] = self.trim_white_spaces(first_record.find('title.translation').text)

        # identification_title_language
        if first_record.find('title.language') != None:
            object_data['identification_titleDescription_language'] = self.trim_white_spaces(first_record.find('title.language').text)

        # identification_describer
        if first_record.find('description.name') != None:
            object_data['identification_titleDescription_describer'] = self.trim_white_spaces(first_record.find('description.name').text)

        # identification_describer_date
        if first_record.find('description.date') != None:
            object_data['identification_titleDescription_date'] = self.trim_white_spaces(first_record.find('description.date').text)

        # identification_taxonomy
        """class ITaxonomy(Interface):
            rank = schema.TextLine(title=_(u'Taxonomy rank'), required=False)
            scientific_name = schema.TextLine(title=_(u'Scient. name'), required=False)
            common_name = schema.TextLine(title=_(u'Common name'), required=False)"""

        taxonomy = []
        if len(first_record.findall('Taxonomy')) > 0:
            for tax in first_record.findall('Taxonomy'):
                new_taxonomy = {
                    "rank": "",
                    "scientific_name": "",
                    "common_name": ""
                }

                if tax.find('taxonomy.rank') != None:
                    if tax.find('taxonomy.rank').find('text') != None:
                        new_taxonomy['rank'] = tax.find('taxonomy.rank').find('text').text

                if tax.find('taxonomy.scientific_name') != None:
                    if tax.find('taxonomy.scientific_name').find('scientific_name') != None:
                        new_taxonomy['scientific_name'] = tax.find('taxonomy.scientific_name').find('scientific_name').text

                    if tax.find('taxonomy.scientific_name').find('common_name') != None:
                        new_taxonomy['common_name'] = tax.find('taxonomy.scientific_name').find('common_name').text

                taxonomy.append(new_taxonomy)

        object_data['identification_taxonomy'] = taxonomy
        
        # identification_taxonomy_determiner

        """
        class IDeterminer(Interface):
            name = schema.TextLine(title=_(u'Determiner'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)"""
        
        determiner = []

        if len(first_record.findall('Determination')) > 0:
            for det in first_record.findall('Determination'):
                new_determiner = {
                    "name": "",
                    "date": ""
                }

                if det.find('determination.name') != None:
                    if det.find('determination.name').find('name') != None:
                        new_determiner['name'] = det.find('determination.name').find('name').text

                if det.find('determination.date') != None:
                    new_determiner['date'] = det.find('determination.date').text

                determiner.append(new_determiner)

        object_data['identification_taxonomy_determiner'] = determiner

        # identification_taxonomy_object_status
        object_status = []

        if first_record.find('object_status') != None:
            if len(first_record.find('object_status').findall('text')) > 0:
                for status in first_record.find('object_status').findall('text'):
                    object_status.append(status.text)

        object_data['identification_taxonomy_object_status'] = ', '.join(object_status)

        # identification_taxonomy_notes
        """class INotes(Interface):
            notes = schema.Text(title=_(u'Notes'), required=False)"""

        taxonomy_notes = []

        if len(first_record.findall('determination.notes')) > 0:
            for note in first_record.findall('determination.notes'):
                taxonomy_notes.append({
                    "notes": note.text
                })

        object_data["identification_taxonomy_notes"] = taxonomy_notes


    def get_physical_characteristics_fieldset(self, object_data, first_record):
        
        # physical_description
        if first_record.find('physical_description') != None:
            object_data['physicalCharacteristics_physicalDescription_description'] = self.trim_white_spaces(first_record.find('physical_description').text)

        # keywords
        """class IKeyword(Interface):
            part = schema.TextLine(title=_(u'Part'), required=False)
            aspect = schema.TextLine(title=_(u'Aspect'), required=False)
            keyword = schema.TextLine(title=_(u'Keyword'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""
        keywords = []

        if len(first_record.findall('phys_characteristic.keyword')) > 0:
            for phys_keyword in first_record.findall('phys_characteristic.keyword'):
                if phys_keyword.find('term') != None:
                    keywords.append({
                        "part": "",
                        "aspect": "",
                        "keyword": phys_keyword.find('term').text,
                        "notes": ""
                    })

            if len(first_record.findall('phys_characteristic.part')) > 0:
                for slot, key_part in enumerate(first_record.findall('phys_characteristic.part')):
                    keywords[slot]["part"] = key_part.text

            if len(first_record.findall('phys_characteristic.aspect.lref')) > 0:
                for slot, key_aspect in enumerate(first_record.findall('phys_characteristic.aspect.lref')):
                    keywords[slot]["aspect"] = key_aspect.text

            if len(first_record.findall('phys_characteristic.notes')) > 0:
                for slot, key_note in enumerate(first_record.findall('phys_characteristic.notes')):
                    keywords[slot]["notes"] = key_note.text

        object_data["physicalCharacteristics_keywords"] = keywords


        # techniques
        techniques = []
        """class ITechnique(Interface):
            part = schema.TextLine(title=_(u'Part'), required=False)
            technique = schema.TextLine(title=_(u'Technique'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""
        
        if len(first_record.findall('technique')) > 0:
            for technique in first_record.findall('technique'):
                if technique.find('term') != None:
                    techniques.append({
                        "part": "",
                        "technique": technique.find('term').text,
                        "notes": ""
                    })

            if len(first_record.findall('technique.part')) > 0:
                for slot, technique_part in enumerate(first_record.findall('technique.part')):
                    techniques[slot]["part"] = technique_part.text

            if len(first_record.findall('technique.notes')) > 0:
                for slot, technique_note in enumerate(first_record.findall('technique.notes')):
                    techniques[slot]["notes"] = technique_note.text

        object_data["physicalCharacteristics_techniques"] = techniques

        
        # materials 
        materials = []
        """class IMaterial(Interface):
            part = schema.TextLine(title=_(u'Part'), required=False)
            material = schema.TextLine(title=_(u'Material'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        if len(first_record.findall('material')) > 0:
            for material in first_record.findall('material'):
                if material.find('term') != None:
                    materials.append({
                        "part": "",
                        "material": material.find('term').text,
                        "notes": ""
                    })

            if len(first_record.findall('material.part')) > 0:
                for slot, material_part in enumerate(first_record.findall('material.part')):
                    materials[slot]["part"] = material_part.text

            if len(first_record.findall('material.notes')) > 0:
                for slot, material_note in enumerate(first_record.findall('material.notes')):
                    materials[slot]["notes"] = material_note.text

        object_data["physicalCharacteristics_materials"] = materials
        
        # dimensions
        """class IDimension(Interface):
            part = schema.TextLine(title=_(u'Part'), required=False)
            dimension = schema.TextLine(title=_(u'Dimension'), required=False)
            value = schema.TextLine(title=_(u'Value'), required=False)
            unit = schema.TextLine(title=_(u'Unit'), required=False)
            precision = schema.TextLine(title=_(u'Precision'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        dimensions = []

        if len(first_record.findall('dimension.type')) > 0:
            for dimension in first_record.findall('dimension.type'):
                if dimension.find('term') != None:
                    dimensions.append({
                        "part": "",
                        "dimension": dimension.find('term').text,
                        "value": "",
                        "unit": "",
                        "precision": "",
                        "notes": ""
                    })

            if len(first_record.findall('dimension.part')) > 0:
                for slot, dimension_part in enumerate(first_record.findall('dimension.part')):
                    dimensions[slot]["part"] = dimension_part.text

            if len(first_record.findall('dimension.value')) > 0:
                for slot, dimension_value in enumerate(first_record.findall('dimension.value')):
                    dimensions[slot]["value"] = dimension_value.text

            if len(first_record.findall('dimension.unit')) > 0:
                for slot, dimension_unit in enumerate(first_record.findall('dimension.unit')):
                    if dimension_unit.find('term') != None:
                        dimensions[slot]["unit"] = dimension_unit.find('term').text

            if len(first_record.findall('dimension.precision')) > 0:
                for slot, dimension_precision in enumerate(first_record.findall('dimension.precision')):
                    dimensions[slot]["precision"] = dimension_precision.text

            if len(first_record.findall('dimension.notes')) > 0:
                for slot, dimension_notes in enumerate(first_record.findall('dimension.notes')):
                    dimensions[slot]["notes"] = dimension_notes.text       


        object_data['physicalCharacteristics_dimensions'] = dimensions

        # dimensions_free_text

        # frame
        """ class IFrame(Interface):
            frame = schema.TextLine(title=_(u'Frame'), required=False)
            detail = schema.TextLine(title=_(u'Detail'), required=False) """
        frames = []
        if len(first_record.findall('frame')) > 0:
            for frame in first_record.findall('frame'):
                frames.append({
                    "frame": frame.text,
                    "detail": ""
                })
            
        if len(frames) > 0:
            # frame_detail
            if len(first_record.findall('frame.notes')) > 0:
                for slot, frame_notes in enumerate(first_record.findall('frame.notes')):
                    frames[slot]["detail"] = frame_notes.text      
                
        object_data['physicalCharacteristics_frame'] = frames

    def get_production_dating_fieldset(self, object_data, first_record):
        
        # productionDating_production
        """ class IProduction(Interface):
            maker = schema.TextLine(title=_(u'Maker'), required=False)
            qualifier = schema.TextLine(title=_(u'Qualifier'), required=False)
            role = schema.TextLine(title=_(u'Role'), required=False)
            place = schema.TextLine(title=_(u'Place'), required=False)
            production_notes = schema.TextLine(title=_(u'Production notes'), required=False)"""

        production = []

        if len(first_record.findall('creator')) > 0:
            for prod in first_record.findall('creator'):
                if prod.find('name') != None:
                    production.append({
                        "maker": prod.find('name').text,
                        "qualifier": "",
                        "role": "",
                        "place": "",
                        "production_notes": ""
                    })



        if len(production) > 0:
            # production_qualifier
            if len(first_record.findall('creator.qualifier')) > 0:
                for slot, production_qualifier in enumerate(first_record.findall('creator.qualifier')):
                    production[slot]["qualifier"] = production_qualifier.text
            
            # production_role
            if len(first_record.findall('creator.role')) > 0:
                for slot, production_role in enumerate(first_record.findall('creator.role')):
                    if production_role.find('term') != None: 
                        production[slot]["role"] = production_role.find('term').text

            # production_place
            if len(first_record.findall('production.place')) > 0:
                for slot, production_place in enumerate(first_record.findall('production.place')):
                    if production_place.find('term') != None:
                        production[slot]["place"] = production_place.find('term').text

            # production_notes
            if len(first_record.findall('production.notes')) > 0:
                for slot, production_notes in enumerate(first_record.findall('production.notes')):
                    production[slot]["production_notes"] = production_notes.text
        
        object_data['productionDating_production'] = production
        
        # production_reason
        if first_record.find('production.reason') != None:
            object_data['productionDating_production_productionReason'] = first_record.find('production.reason').text

        # production_school
        """ class ISchool(Interface):
            term = schema.TextLine(title=_(u'School / style'), required=False)"""

        school_style = []

        if len(first_record.findall('school_style')) > 0:
            for school in first_record.findall('school_style'):
                if school.find('term') != None:
                    school_style.append({
                        "term": school.find('term').text
                    })

        object_data['productionDating_production_schoolStyle'] = school_style

        # production_period
        """class IPeriod(Interface):
            period = schema.TextLine(title=_(u'Period'), required=False)
            date_early = schema.TextLine(title=_(u'Date (early)'), required=False)
            date_early_precision = schema.TextLine(title=_(u'Precision'), required=False)
            date_late = schema.TextLine(title=_(u'Date (late)'), required=False)
            date_late_precision = schema.TextLine(title=_(u'Precision'), required=False)"""

        periods = []

        if len(first_record.findall('production.period')) > 0:
            for period in first_record.findall('production.period'):
                if period.find('term') != None:
                    periods.append({
                        "period": period.find('term').text,
                        "date_early": "",
                        "date_early_precision": "",
                        "date_late": "",
                        "date_late_precision": "",
                    })

        if len(periods) > 0:
            if len(first_record.findall('production.date.start')) > 0:
                for slot, period_date_early in enumerate(first_record.findall('production.date.start')):
                    periods[slot]["date_early"] = period_date_early.text

            if len(first_record.findall('production_date.start.prec')) > 0:
                for slot, period_date_early_precision in enumerate(first_record.findall('production_date.start.prec')):
                    periods[slot]["date_early_precision"] = period_date_early_precision.text

            if len(first_record.findall('production.date.end')) > 0:
                for slot, period_date_late in enumerate(first_record.findall('production.date.end')):
                    periods[slot]["date_late"] = period_date_late.text

            if len(first_record.findall('production.date.end.prec')) > 0:
                for slot, period_date_late_precision in enumerate(first_record.findall('production.date.end.prec')):
                    periods[slot]["date_late_precision"] = period_date_late_precision.text

        object_data["productionDating_dating_period"] = periods

        
        # production_dating_notes

        production_dating_notes = []

        if len(first_record.findall('production.date.notes')) > 0:
            for note in first_record.findall('production.date.notes'):
                production_dating_notes.append({
                    "notes": note.text
                })

        object_data["productionDating_dating_notes"] = production_dating_notes



    def get_condition_and_conservation_fieldset(self, object_data, first_record):
        
        # conservation_priority

        # conservation_next_condition_check

        # conservation_date
        if first_record.find('condition.date') != None:
            object_data['conditionConservation_date'] = first_record.find('condition.date').text

        # completeness
        """class ICompleteness(Interface):
            completeness = schema.TextLine(title=_(u'Completeness'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)
            checked_by = schema.TextLine(title=_(u'Checked by'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)"""

        completeness = []
        if len(first_record.findall('completeness')) > 0:
            for complete in first_record.findall('completeness'):
                completeness.append({
                    "completeness": complete.text,
                    "notes": "",
                    "checked_by": "",
                    "date": ""
                })

        if len(completeness) > 0:
            if len(first_record.findall('completeness.notes')) > 0:
                for slot, complete_notes in enumerate(first_record.findall('completeness.notes')):
                    completeness[slot]["notes"] = complete_notes.text

            if len(first_record.findall('completeness.date')) > 0:
                for slot, complete_date in enumerate(first_record.findall('completeness.date')):
                    completeness[slot]["date"] = complete_date.text

            if len(first_record.findall('completeness.check.name')) > 0:
                for slot, complete_checked_by in enumerate(first_record.findall('completeness.check.name')):
                    completeness[slot]["checked_by"] = complete_checked_by.text

        object_data["conditionConservation_completeness"] = completeness

        # condition
        """class ICondition(Interface):
            part = schema.TextLine(title=_(u'Part'), required=False)
            condition = schema.TextLine(title=_(u'Condition'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)
            checked_by = schema.TextLine(title=_(u'Checked by'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)"""

        condition = []
        if len(first_record.findall('condition')) > 0:
            for cond in first_record.findall('condition'):
                if cond.find('term') != None:
                    condition.append({
                        "part":"",
                        "condition": cond.find('term').text,
                        "notes": "",
                        "checked_by": "",
                        "date": ""
                    })

        if len(condition) > 0:
            if len(first_record.findall('condition.part')) > 0:
                for slot, condition_part in enumerate(first_record.findall('condition.part')):
                    condition[slot]["part"] = condition_part.text

            if len(first_record.findall('condition.notes')) > 0:
                for slot, condition_notes in enumerate(first_record.findall('condition.notes')):
                    condition[slot]["notes"] = condition_notes.text

            if len(first_record.findall('condition.check.name')) > 0:
                for slot, condition_checked_by in enumerate(first_record.findall('condition.check.name')):
                    condition[slot]["checked_by"] = condition_checked_by.text

            if len(first_record.findall('condition.date')) > 0:
                for slot, condition_date in enumerate(first_record.findall('condition.date')):
                    condition[slot]["date"] = condition_date.text


        object_data['conditionConservation_condition'] = condition

        # enviromental_condition
        """class IEnvCondition(Interface):
            preservation_form = schema.TextLine(title=_(u'Preservation form'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)"""

        enviromental_condition = []
        if len(first_record.findall('preservation_form')) > 0:
            for cond in first_record.findall('preservation_form'):
                if cond.find('term') != None:
                    enviromental_condition.append({
                        "preservation_form":cond.find('term').text,
                        "notes": "",
                        "date": ""
                    })

        if len(enviromental_condition) > 0:
            if len(first_record.findall('preservation_form.notes')) > 0:
                for slot, env_condition_notes in enumerate(first_record.findall('preservation_form.notes')):
                    enviromental_condition[slot]["notes"] = env_condition_notes.text

            if len(first_record.findall('preservation_form.date')) > 0:
                for slot, env_condition_date in enumerate(first_record.findall('preservation_form.date')):
                    enviromental_condition[slot]["date"] = env_condition_date.text

        object_data['conditionConservation_enviromental_condition'] = enviromental_condition

        # conservation_request
        """class IConsRequest(Interface):
            treatment = schema.TextLine(title=_(u'Treatment'), required=False)
            requester = schema.TextLine(title=_(u'Requester'), required=False)
            reason = schema.TextLine(title=_(u'Reason'), required=False)
            status = schema.TextLine(title=_(u'Status'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)"""

        conservation_request = []
        if len(first_record.findall('old.conservation_request.treatme')) > 0:
            for cons in first_record.findall('old.conservation_request.treatme'):
                conservation_request.append({
                    "treatment": cons.text,
                    "requester": "",
                    "reason": "",
                    "status": "",
                    "date": ""
                })

        if len(conservation_request) > 0:
            if len(first_record.findall('old.conservation_request.name')) > 0:
                for slot, cons_requester in enumerate(first_record.findall('old.conservation_request.name')):
                    conservation_request[slot]["requester"] = cons_requester.text

            if len(first_record.findall('old.conservation_request.reason')) > 0:
                for slot, cons_reason in enumerate(first_record.findall('old.conservation_request.reason')):
                    conservation_request[slot]["reason"] = cons_reason.text

            if len(first_record.findall('old.conservation_request.status')) > 0:
                for slot, cons_status in enumerate(first_record.findall('old.conservation_request.status')):
                    conservation_request[slot]["status"] = cons_status.text

            if len(first_record.findall('old.conservation_request.date')) > 0:
                for slot, cons_date in enumerate(first_record.findall('old.conservation_request.date')):
                    conservation_request[slot]["date"] = cons_date.text

        object_data['conditionConservation_conservation_request'] = conservation_request


    def get_inscriptions_and_markings_fieldset(self, object_data, first_record):
        """ class IInscription(Interface):
            type = schema.TextLine(title=_(u'Type'), required=False)
            position = schema.TextLine(title=_(u'Position'),required=False)
            method = schema.TextLine(title=_(u'Method'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            creator = schema.TextLine(title=_(u'Creator'), required=False)
            creator_role = schema.TextLine(title=_(u'Role'), required=False)
            content = schema.TextLine(title=_(u'Content'), required=False)
            description = schema.TextLine(title=_(u'Description'), required=False)
            interpretation = schema.TextLine(title=_(u'Interpretation'), required=False)
            language = schema.TextLine(title=_(u'Language'), required=False)
            script = schema.TextLine(title=_(u'Script'), required=False)
            transliteration = schema.TextLine(title=_(u'Transliteration'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        inscriptions = []

        # inscription_type 
        if len(first_record.findall('inscription.type')) > 0:
            for inscription in first_record.findall('inscription.type'):
                if inscription.find('term') != None:
                    inscriptions.append({
                        "type":inscription.find('term').text,
                        "position":"",
                        "method": "",
                        "date": "",
                        "creator": "",
                        "role":"",
                        "content":"",
                        "description":"",
                        "interpretation": "",
                        "language":"",
                        "transliteration": "",
                        "script": "",
                        "notes": ""
                    })

        if len(inscriptions) > 0:
            # inscription_position
            if len(first_record.findall('inscription.position')) > 0:
                for slot, inscription_position in enumerate(first_record.findall('inscription.position')):
                    inscriptions[slot]["position"] = inscription_position.text

            # inscription_method
            if len(first_record.findall('inscription.method')) > 0:
                for slot, inscription_method in enumerate(first_record.findall('inscription.method')):
                    inscriptions[slot]["method"] = inscription_method.text

            # inscription_date
            if len(first_record.findall('inscription.date')) > 0:
                for slot, inscription_method in enumerate(first_record.findall('inscription.date')):
                    inscriptions[slot]["date"] = inscription_method.text

            # inscription_creator
            if len(first_record.findall('inscription.maker')) > 0:
                for slot, inscription_maker in enumerate(first_record.findall('inscription.maker')):
                    if inscription_maker.find('name') != None:
                        inscriptions[slot]["creator"] = inscription_maker.find('name').text

            # inscription_creator_role
            if len(first_record.findall('inscription.maker.role')) > 0:
                for slot, inscription_maker_role in enumerate(first_record.findall('inscription.maker.role')):
                    if inscription_maker_role.find('term') != None:
                        inscriptions[slot]["role"] = inscription_maker_role.find('term').text

            # inscription_content
            if len(first_record.findall('inscription.content')) > 0:
                for slot, inscription_content in enumerate(first_record.findall('inscription.content')):
                    inscriptions[slot]["content"] = inscription_content.text

            # inscription_description
            if len(first_record.findall('inscription.description')) > 0:
                for slot, inscription_description in enumerate(first_record.findall('inscription.description')):
                    inscriptions[slot]["description"] = inscription_description.text

            # inscription_interpretation
            if len(first_record.findall('inscription.interpretation')) > 0:
                for slot, inscription_interpretation in enumerate(first_record.findall('inscription.interpretation')):
                    inscriptions[slot]["interpretation"] = inscription_interpretation.text

            # inscription_language
            if len(first_record.findall('inscription.language')) > 0:
                for slot, inscription_language in enumerate(first_record.findall('inscription.language')):
                    inscriptions[slot]["language"] = inscription_language.text

            # inscription_script
            if len(first_record.findall('inscription.script')) > 0:
                for slot, inscription_script in enumerate(first_record.findall('inscription.script')):
                    if inscription_script.find('term') != None:
                        inscriptions[slot]["script"] = inscription_script.find('term').text

            # transliteration
            if len(first_record.findall('inscription.transliteration')) > 0:
                for slot, inscription_trans in enumerate(first_record.findall('inscription.transliteration')):
                    inscriptions[slot]["transliteration"] = inscription_trans.text

            # inscription_notes
            if len(first_record.findall('inscription.notes')) > 0:
                for slot, inscription_notes in enumerate(first_record.findall('inscription.notes')):
                    inscriptions[slot]["notes"] = inscription_notes.text


        object_data['inscriptionsMarkings_inscriptionsMarkings'] = inscriptions

    def get_value_insurance_fieldset(self, object_data, first_record):
        #
        # Validation
        #
        valuation = []
        """class IValuation(Interface):
            value = schema.TextLine(title=_(u'Value'), required=False)
            curr = schema.TextLine(title=_(u'Curr.'), required=False)
            valuer = schema.TextLine(title=_(u'Valuer'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            reference = schema.TextLine(title=_(u'Reference'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""


        if len(first_record.findall('valuation.value')) > 0:
            for v in first_record.findall('valuation.value'):
                valuation.append({
                    "value":v.text,
                    "curr":"",
                    "valuer": "",
                    "date": "",
                    "reference": "",
                    "notes":""
                })

        if len(valuation) > 0:

            # Valuation - curr
            if len(first_record.findall('valuation.value.currency')) > 0:
                for slot, val_curr in enumerate(first_record.findall('valuation.value.currency')):
                    valuation[slot]["curr"] = val_curr.text

            # Valuation - valuer
            if len(first_record.findall('valuation.name')) > 0:
                for slot, val_name in enumerate(first_record.findall('valuation.name')):
                    valuation[slot]["valuer"] = val_name.text

            # Valuation - date
            if len(first_record.findall('valuation.date')) > 0:
                for slot, val_date in enumerate(first_record.findall('valuation.date')):
                    valuation[slot]["date"] = val_date.text

            # Valuation - reference
            if len(first_record.findall('valuation.reference')) > 0:
                for slot, val_reference in enumerate(first_record.findall('valuation.reference')):
                    valuation[slot]["reference"] = val_reference.text

            # Valuation - notes
            if len(first_record.findall('valuation.notes')) > 0:
                for slot, val_notes in enumerate(first_record.findall('valuation.notes')):
                    valuation[slot]["notes"] = val_notes.text

            object_data['valueInsurance_valuation'] = valuation

        #
        # Insurance
        #
        insurance = []
        """
        class IInsurance(Interface):
            type = schema.Choice(
                vocabulary=insurance_type_vocabulary,
                title=_(u'Type'),
                required=False
            )
            value = schema.TextLine(title=_(u'Value'), required=False)
            curr = schema.TextLine(title=_(u'Curr.'), required=False)
            valuer = schema.TextLine(title=_(u'Valuer'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            policy_number = schema.TextLine(title=_(u'Policy number'), required=False)
            insurance_company = schema.TextLine(title=_(u'Insurance company'), required=False)
            confirmation_date = schema.TextLine(title=_(u'Confirmation date'), required=False)
            renewal_date = schema.TextLine(title=_(u'Renewal date'), required=False)
            reference = schema.TextLine(title=_(u'Reference'), required=False)
            conditions = schema.TextLine(title=_(u'Conditions'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        if len(first_record.findall('insurance.value')) > 0:
            for ins in first_record.findall('insurance.value'):
                insurance.append({
                    "type": "commercial",
                    "value":ins.text,
                    "curr":"",
                    "valuer": "",
                    "date": "",
                    "policy_number": "",
                    "insurance_company": "",
                    "confirmation_date":"",
                    "renewal_date": "",
                    "reference": "",
                    "conditions": "",
                    "notes":""
                })

        if len(insurance) > 0:
            # Insurance - curr
            if len(first_record.findall('insurance.value.currency')) > 0:
                for slot, insurance_curr in enumerate(first_record.findall('insurance.value.currency')):
                    insurance[slot]["curr"] = insurance_curr.text

            # Insurance - valuer
            if len(first_record.findall('insurance.valuer')) > 0:
                for slot, insurance_name in enumerate(first_record.findall('insurance.valuer')):
                    insurance[slot]["valuer"] = insurance_name.text

            # Insurance - date
            if len(first_record.findall('insurance.date')) > 0:
                for slot, insurance_date in enumerate(first_record.findall('insurance.date')):
                    insurance[slot]["date"] = insurance_date.text

            # Insurance - policy_number
            if len(first_record.findall('insurance.policy_number')) > 0:
                for slot, insurance_policy_number in enumerate(first_record.findall('insurance.policy_number')):
                    insurance[slot]["policy_number"] = insurance_policy_number.text

            # Insurance - insurance_company
            if len(first_record.findall('insurance.company')) > 0:
                for slot, insurance_company in enumerate(first_record.findall('insurance.company')):
                    insurance[slot]["insurance_company"] = insurance_company.text

            # Insurance - confirmation_date

            # Insurance - renewal_date

            # Insurance - reference
            if len(first_record.findall('insurance.reference')) > 0:
                for slot, insurance_reference in enumerate(first_record.findall('insurance.reference')):
                    insurance[slot]["reference"] = insurance_reference.text

            # Insurance - conditions
            if len(first_record.findall('insurance.conditions')) > 0:
                for slot, insurance_conditions in enumerate(first_record.findall('insurance.conditions')):
                    insurance[slot]["conditions"] = insurance_conditions.text

            # Insurance - notes
            if len(first_record.findall('insurance.notes')) > 0:
                for slot, insurance_notes in enumerate(first_record.findall('insurance.notes')):
                    insurance[slot]["notes"] = insurance_notes.text

            
            object_data["valueInsurance_insurance"] = insurance

    def get_acquisition_fieldset(self, object_data, first_record):

        # accession_date
        if first_record.find('accession_date') != None:
            object_data['aquisition_accession_date'] = first_record.find('accession_date').text


        # acquisition_number
        if first_record.find('acquisition.number') != None:
            object_data['acquisition_number'] = first_record.find('acquisition.number').text


        # acquisition_date
        if first_record.find('acquisition.date') != None:
            object_data['acquisition_date'] = first_record.find('acquisition.date').text

        # acquisition_precision
        if first_record.find('acquisition.date.precision') != None:
            object_data['acquisition_precision'] = first_record.find('acquisition.date.precision').text

        # acquisition_method
        if first_record.find('acquisition.method') != None:
            if first_record.find('acquisition.method').find('term') != None:
                object_data['acquisition_method'] = first_record.find('acquisition.method').find('term').text

        # acquisition_rec_no

        # acquisition_lot_no
        if first_record.find('acquisition.auction.lot_number') != None:
            object_data['acquisition_lot_no'] = first_record.find('acquisition.auction.lot_number').text

        # acquisition_from

        # acquisition_auction
        if first_record.find('acquisition.auction') != None:
            if first_record.find('acquisition.auction').find('auction') != None:
                object_data['acquisition_auction'] = first_record.find('acquisition.auction').find('auction').text

        # acquisition_place
        if first_record.find('acquisition.place') != None:
            if first_record.find('acquisition.place').find('term') != None:
                object_data['acquisition_place'] = first_record.find('acquisition.place').find('term').text

        # acquisition_reason
        if first_record.find('acquisition.reason') != None:
            object_data['acquisition_reason'] = first_record.find('acquisition.reason').text

        # acquisition_conditions
        if first_record.find('acquisition.conditions') != None:
            object_data['acquisition_conditions'] = first_record.find('acquisition.conditions').text

        # authorization_authorizer
        if first_record.find('acquisition.authorisation.name') != None:
            object_data['aquisition_authorization_authorizer'] = first_record.find('acquisition.authorisation.name').text

        # authorization_date
        if first_record.find('acquisition.authorisation.date') != None:
            object_data['aquisition_authorization_date'] = first_record.find('acquisition.authorisation.date').text

        # costs_offer_price
        if first_record.find('acquisition.offer_price.value') != None:
            object_data['aquisition_costs_offer_price'] = first_record.find('acquisition.offer_price.value').text

        # costs_offer_price_curr
        if first_record.find('acquisition.offer_price.currency') != None:
            object_data['aquisition_costs_offer_price_curr'] = first_record.find('acquisition.offer_price.currency').text

        # costs_purchase_price
        if first_record.find('acquisition.price.value') != None:
            object_data['aquisition_costs_purchase_price'] = first_record.find('acquisition.price.value').text

        # costs_purchase_price_curr
        if first_record.find('acquisition.price.currency') != None:
            object_data['aquisition_costs_purchase_price_curr'] = first_record.find('acquisition.price.currency').text

        # costs_notes
        if first_record.find('acquisition.price.notes') != None:
            object_data['aquisision_costs_notes'] = first_record.find('acquisition.price.notes').text

        # funding
        """ class IFunding(Interface):
            amount = schema.TextLine(title=_(u'Amount'), required=False)
            curr = schema.TextLine(title=_(u'Curr.'), required=False)
            source = schema.TextLine(title=_(u'Source'), required=False)
            provisos = schema.TextLine(title=_(u'Provisos'), required=False)
        """

        funding = []
        if len(first_record.findall('acquisition.funding.value')) > 0:
            for fund in first_record.findall('acquisition.funding.value'):
                funding.append({
                    "amount": fund.text,
                    "curr":"",
                    "source":"",
                    "provisos": ""
                })

        if len(funding) > 0:
            # curr
            if len(first_record.findall('acquisition.funding.currency')) > 0:
                for slot, funding_curr in enumerate(first_record.findall('acquisition.funding.currency')):
                    funding[slot]["curr"] = funding_curr.text

            # source
            if len(first_record.findall('acquisition.funding.source')) > 0:
                for slot, funding_source in enumerate(first_record.findall('acquisition.funding.source')):
                    funding[slot]["source"] = funding_source.text

            # provisos
            if len(first_record.findall('acquisition.funding.proviso')) > 0:
                for slot, funding_proviso in enumerate(first_record.findall('acquisition.funding.proviso')):
                    funding[slot]["provisos"] = funding_proviso.text

        object_data['aquisition_funding'] = funding

        # Documentation
        """ class IDocumentation(Interface):
            description = schema.TextLine(title=_(u'Description'), required=False)
            reference = schema.TextLine(title=_(u'Reference'), required=False)
        """

        documentation = []
        if len(first_record.findall('acquisition.document.description')) > 0:
            for doc in first_record.findall('acquisition.document.description'):
                documentation.append({
                    "description": doc.text,
                    "reference":""
                })

        if len(documentation) > 0:
            # reference
            if len(first_record.findall('acquisition.document.reference')) > 0:
                for slot, doc_ref in enumerate(first_record.findall('acquisition.document.reference')):
                    documentation[slot]["reference"] = doc_ref.text

        object_data["aquisition_documentation"] = documentation

        # acquisition_copyright
        if first_record.find('copyright') != None:
            object_data['acquisition_copyright'] = first_record.find('copyright').text

        # acquisition_notes
        if first_record.find('acquisition.notes') != None:
            object_data['acquisition_notes'] = first_record.find('acquisition.notes').text


    def get_disposal_fieldset(self, object_data, first_record):
        # disposal_deaccession
        if first_record.find('deaccession.date') != None:
            object_data['disposal_deaccession'] = first_record.find('deaccession.date').text

        # disposal_new_object_number
        if first_record.find('new_object_number') != None:
            object_data['disposal_new_object_number'] = first_record.find('new_object_number').text

        # disposal_number
        if first_record.find('disposal.number') != None:
            object_data['disposal_number'] = first_record.find('disposal.number').text

        # disposal_date
        if first_record.find('disposal.date') != None:
            object_data['disposal_date'] = first_record.find('disposal.date').text

        # disposal_method
        if first_record.find('disposal.method') != None:
            object_data['disposal_method'] = first_record.find('disposal.method').text

        # disposal_proposed_recipient
        if first_record.find('disposal.prop_recipient') != None:
            if first_record.find('disposal.prop_recipient').find('name') != None:
                object_data['disposal_proposed_recipient'] = first_record.find('disposal.prop_recipient').find('name').text

        # disposal_recipient
        if first_record.find('disposal.recipient') != None:
            if first_record.find('disposal.recipient').find('name') != None:
                object_data['disposal_recipient'] = first_record.find('disposal.recipient').find('name').text

        # disposal_reason
        if first_record.find('disposal.reason') != None:
            object_data['disposal_reason'] = first_record.find('disposal.reason').text

        # disposal_provisos
        if first_record.find('disposal.provisos') != None:
            object_data['disposal_provisos'] = first_record.find('disposal.provisos').text

        # finance_disposal_price
        if first_record.find('disposal.price.value') != None:
            object_data['disposal_finance_disposal_price'] = first_record.find('disposal.price.value').text

        # finance_curr
        if first_record.find('disposal.price.currency') != None:
            object_data['disposal_finance_currency'] = [first_record.find('disposal.price.currency').text]

        # disposal_documentation
        """ class IDocumentation(Interface):
            description = schema.TextLine(title=_(u'Description'), required=False)
            reference = schema.TextLine(title=_(u'Reference'), required=False)
        """

        disposal_documentation = []
        if len(first_record.findall('disposal.document.description')) > 0:
            for doc in first_record.findall('disposal.document.description'):
                disposal_documentation.append({
                    "description": doc.text,
                    "reference":""
                })

        if len(disposal_documentation) > 0:
            # reference
            if len(first_record.findall('disposal.document.reference')) > 0:
                for slot, doc_ref in enumerate(first_record.findall('disposal.document.reference')):
                    disposal_documentation[slot]["reference"] = doc_ref.text

        object_data["disposal_documentation"] = disposal_documentation

        # disposal_notes
        if first_record.find('disposal.notes') != None:
            object_data['disposal_notes'] = first_record.find('disposal.notes').text


    def get_ownership_history_fieldset(self, object_data, first_record):

        # ownership_current_owner
        if first_record.find('current_owner') != None:
            if first_record.find('current_owner').find('name') != None:
                object_data['ownershipHistory_current_owner'] = first_record.find('current_owner').find('name').text

        # ownership_history_owner
        if first_record.find('owner_hist.owner') != None:
            if first_record.find('owner_hist.owner').find('name') != None:
                object_data['ownershipHistory_owner'] = first_record.find('owner_hist.owner').find('name').text

        # ownership_history_from
        if first_record.find('owner_hist.date.start') != None:
            object_data['ownershipHistory_from'] = first_record.find('owner_hist.date.start').text

        # ownership_history_until
        if first_record.find('owner_hist.date.end') != None:
            object_data['ownershipHistory_until'] = first_record.find('owner_hist.date.end').text

        # ownership_exchange_method
        if first_record.find('owner_hist.acquisition.method') != None:
            if first_record.find('owner_hist.acquisition.method').find('term') != None:
                object_data['ownershipHistory_exchange_method'] = first_record.find('owner_hist.acquisition.method').find('term').text

        # ownership_acquired_from
        if first_record.find('owner_hist.acquired_from') != None:
            if first_record.find('owner_hist.acquired_from').find('name') != None:
                object_data['ownershipHistory_acquired_from'] = first_record.find('owner_hist.acquired_from').find('name').text

        # ownership_auction
        if first_record.find('owner_hist.auction') != None:
            if first_record.find('owner_hist.auction').find('auction') != None:
                object_data['ownershipHistory_auction'] = first_record.find('owner_hist.auction').find('auction').text

        # ownership_rec_no
        
        # ownership_lot_no
        if first_record.find('owner_hist.auction.lot_number') != None:
            object_data['ownershipHistory_lot_no'] = first_record.find('owner_hist.auction.lot_number').text

        # ownership_place
        if first_record.find('owner_hist.place') != None:
            if first_record.find('owner_hist.place').find('term') != None:
                object_data['ownershipHistory_place'] = first_record.find('owner_hist.place').find('term').text

        # ownership_price
        if first_record.find('owner_hist.price') != None:
            object_data['ownershipHistory_price'] = first_record.find('owner_hist.price').text

        # ownership_category
        if first_record.find('owner_hist.ownership_category') != None:
            object_data['ownershipHistory_category'] = first_record.find('owner_hist.ownership_category').text

        # ownership_access
        if first_record.find('owner_hist.access') != None:
            object_data['ownershipHistory_access'] = first_record.find('owner_hist.access').text

        # ownership_notes
        if first_record.find('owner_hist.notes') != None:
            object_data['ownershipHistory_notes'] = first_record.find('owner_hist.notes').text


    def get_location_fieldset(self, object_data, first_record):

        # location_normal_location
        if first_record.find('location.default') != None:
            if first_record.find('location.default').find('term') != None:
                object_data['location_normal_location'] = first_record.find('location.default').find('term').text

        #
        # location_current_location
        #
        """ class ICurrentLocation(Interface):
            start_date = schema.TextLine(title=_(u'Start date'), required=False)
            end_date = schema.TextLine(title=_(u'End date'), required=False)
            location_type = schema.TextLine(title=_(u'Location type'), required=False)
            location = schema.TextLine(title=_(u'Location'), required=False)
            fitness = schema.TextLine(title=_(u'Fitness'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False) """

        location_current_location = []
        if len(first_record.findall('location')) > 0:
            for loc in first_record.findall('location'):
                if loc.find('term') != None:
                    location_current_location.append({
                        "start_date": "",
                        "end_date": "",
                        "location_type": "",
                        "location": loc.find('term').text,
                        "fitness": "",
                        "notes": ""
                    })

        if len(location_current_location) > 0:
            # start_date
            if len(first_record.findall('location.date.begin')) > 0:
                for slot, loc_start_date in enumerate(first_record.findall('location.date.begin')):
                    location_current_location[slot]["start_date"] = loc_start_date.text
            # end_date
            if len(first_record.findall('location.date.end')) > 0:
                for slot, loc_end_date in enumerate(first_record.findall('location.date.end')):
                    location_current_location[slot]["end_date"] = loc_end_date.text

            # location_type
            if len(first_record.findall('location_type')) > 0:
                for slot, loc_type in enumerate(first_record.findall('location_type')):
                    location_current_location[slot]["location_type"] = loc_type.text

            # fitness
            if len(first_record.findall('location.fitness')) > 0:
                for slot, loc_fitness in enumerate(first_record.findall('location.fitness')):
                    location_current_location[slot]["fitness"] = loc_fitness.text

            # notes
            if len(first_record.findall('location.notes')) > 0:
                for slot, loc_notes in enumerate(first_record.findall('location.notes')):
                    location_current_location[slot]["notes"] = loc_notes.text

        object_data["location_current_location"] = location_current_location

        #
        # location_checks
        #
        """ class ILocationChecks(Interface):
            date = schema.TextLine(title=_(u'Date'), required=False)
            checked_by = schema.TextLine(title=_(u'Checked by'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False) """

        location_checks = []
        if len(first_record.findall('location_check.name')) > 0:
            for loc_check in first_record.findall('location_check.name'):
                location_checks.append({
                    "date": "",
                    "checked_by": loc_check.text,
                    "notes": "",
                })

        if len(location_checks) > 0:
            # date
            if len(first_record.findall('location_check.date')) > 0:
                for slot, loc_check_date in enumerate(first_record.findall('location_check.date')):
                    location_checks[slot]["date"] = loc_check_date.text

            # notes
            if len(first_record.findall('location_check.notes')) > 0:
                for slot, loc_check_notes in enumerate(first_record.findall('location_check.notes')):
                    location_checks[slot]["notes"] = loc_check_notes.text

        object_data["location_checks"] = location_checks


    def get_notes_fieldset(self, object_data, first_record):
        # notes
        """class INotes(Interface):
            notes = schema.Text(title=_(u'Notes'), required=False)"""

        notes = []

        if len(first_record.findall('notes')) > 0:
            for note in first_record.findall('notes'):
                notes.append({
                    "notes": note.text
                })

        object_data["notes"] = notes

        # notes_free_fields
        """class IFreeFields(Interface):
            date = schema.TextLine(title=_(u'Date'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)
            confidential = schema.TextLine(title=_(u'Confidential'), required=False)
            content = schema.TextLine(title=_(u'Content'), required=False)"""

        notes_free_fields = []

        if len(first_record.findall('free_field.type')) > 0:
            for free_field in first_record.findall('free_field.type'):
                notes_free_fields.append({
                    "date": "",
                    "type": free_field.text,
                    "confidential": "",
                    "content": "",
                })

        if len(notes_free_fields) > 0:
            # date
            if len(first_record.findall('free_field.date')) > 0:
                for slot, free_field_date in enumerate(first_record.findall('free_field.date')):
                    notes_free_fields[slot]["date"] = free_field_date.text

            # confidential
            if len(first_record.findall('free_field.confidential')) > 0:
                for slot, free_field_confidential in enumerate(first_record.findall('free_field.confidential')):
                    notes_free_fields[slot]["confidential"] = free_field_confidential.text

            # content
            if len(first_record.findall('free_field.content')) > 0:
                for slot, free_field_content in enumerate(first_record.findall('free_field.content')):
                    notes_free_fields[slot]["content"] = free_field_content.text


        object_data['notes_free_fields'] = notes_free_fields


    def get_label_fieldset(self, object_data, first_record):
        # labels
        """ class ILabel(Interface):
            date = schema.TextLine(title=_(u'Date'), required=False)
            text = schema.Text(title=_(u'Text'), required=False)"""

        labels = []
        if len(first_record.findall('label')) > 0:
            for label in first_record.findall('label'):
                
                new_label = {
                    "date": "",
                    "text": ""
                }

                if label.find('label.text') != None:
                    new_label['text'] = label.find('label.text').text
                
                if label.find('label.date') != None:
                    new_label['date'] = label.find('label.date').text

                labels.append(new_label)

        object_data['labels'] = labels

    def get_iconography_fieldset(self, object_data, first_record):

        # iconography_generalSearchCriteria_generalTheme
        """class IIconographyGeneralTheme(Interface):
            term = schema.TextLine(title=_(u'General theme'), required=False)"""

        general_themes = []

        if len(first_record.findall('content.motif.general')) > 0:
            for general_theme in first_record.findall('content.motif.general'):
                if general_theme.find('term') != None:
                    general_themes.append({
                        "term": general_theme.find('term').text
                    })

        object_data['iconography_generalSearchCriteria_generalTheme'] = general_themes

        # iconography_generalSearchCriteria_specificTheme
        """ class IIconographySpecificTheme(Interface):
            term = schema.TextLine(title=_(u'Specific theme'), required=False)"""

        specific_themes = []

        if len(first_record.findall('content.motif.specific')) > 0:
            for specific_theme in first_record.findall('content.motif.specific'):
                if specific_theme.find('term') != None:
                    specific_themes.append({
                        "term": specific_theme.find('term').text
                    })

        object_data['iconography_generalSearchCriteria_specificTheme'] = specific_themes

        # iconography_generalSearchCriteria_classificationTheme
        """ class IIconographyClassificationTheme(Interface):
            term = schema.TextLine(title=_(u'Classification theme'), required=False) """

        classification_themes = []

        if len(first_record.findall('content.classification.scheme')) > 0:
            for classification_theme in first_record.findall('content.classification.scheme'):
                classification_themes.append({
                    "term": classification_theme.text,
                    "code": ""
                })

        if len(classification_themes) > 0:
            if len(first_record.findall('content.classification.code')) > 0:
                for slot, classification_code in enumerate(first_record.findall('content.classification.code')):
                    classification_themes[slot]["code"] = classification_code.text

        object_data['iconography_generalSearchCriteria_classificationTheme'] = classification_themes


        # iconography_contentDescription
        """class IIconographyContentDescription(Interface):
            part = schema.TextLine(title=_(u'Part'), required=False)
            description = schema.TextLine(title=_(u'Description'), required=False)"""

        content_description = []

        if len(first_record.findall('content.description')) > 0:
            for desc in first_record.findall('content.description'):
                content_description.append({
                    "part": "",
                    "description": desc.text
                })


        if len(content_description) > 0:
            if len(first_record.findall('content.description.part')) > 0:
                for slot, classification_part in enumerate(first_record.findall('content.description.part')):
                    content_description[slot]["part"] = classification_part.text

        object_data['iconography_contentDescription'] = content_description

        # iconography_contentPersonInstitution
        """ class IIconographyContentPersonInstitution(Interface):
            position = schema.TextLine(title=_(u'Position'), required=False)
            nameType = schema.TextLine(title=_(u'Name type'), required=False)
            name = schema.TextLine(title=_(u'Name'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        person_institution = []

        if len(first_record.findall('content.person.position')) > 0:
            for person in first_record.findall('content.person.position'):
                person_institution.append({
                    "position": person.text,
                    "nameType": "",
                    "name": "",
                    "notes": ""
                })

        if len(person_institution) > 0:
            # nameType
            if len(first_record.findall('content.person.name.type')) > 0:
                for slot, person_name_type in enumerate(first_record.findall('content.person.name.type')):
                    if person_name_type.find('text') != None:
                        person_institution[slot]["nameType"] = person_name_type.find('text').text

            # name
            if len(first_record.findall('content.person.name')) > 0:
                for slot, person_name in enumerate(first_record.findall('content.person.name')):
                    if person_name.find('name') != None:
                        person_institution[slot]["name"] = person_name.find('name').text

            # notes
            if len(first_record.findall('content.person.note')) > 0:
                for slot, person_notes in enumerate(first_record.findall('content.person.note')):
                    person_institution[slot]["notes"] = person_notes.text


        object_data['iconography_contentPersonInstitution'] = person_institution

        # iconography_contentSubject
        """ class IIconographyContentSubject(Interface):
            position = schema.TextLine(title=_(u'Position'), required=False)
            subjectType = schema.TextLine(title=_(u'Subject type'), required=False)
            subject = schema.TextLine(title=_(u'Subject'), required=False)
            taxonomicRank = schema.TextLine(title=_(u'Taxonomic rank'), required=False)
            scientificName = schema.TextLine(title=_(u'Scientific name'), required=False)
            properName = schema.TextLine(title=_(u'Proper name'), required=False)
            identifier = schema.TextLine(title=_(u'Identifier'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        content_subject = []

        if len(first_record.findall('content.subject')) > 0:
            for content_sub in first_record.findall('content.subject'):
                if content_sub.find('term') != None:
                    content_subject.append({
                        "position": "",
                        "subjectType": "",
                        "subject": content_sub.find('term').text,
                        "taxonomicRank": "",
                        "scientificName": "",
                        "properName": "",
                        "identifier": "",
                        "notes": ""
                    })

        if len(content_subject) > 0:
            # position
            if len(first_record.findall('content.subject.position')) > 0:
                for slot, subject_position in enumerate(first_record.findall('content.subject.position')):
                    content_subject[slot]["position"] = subject_position.text

            # subjectType
            if len(first_record.findall('content.subject.type')) > 0:
                for slot, subject_type in enumerate(first_record.findall('content.subject.type')):
                    if subject_type.find('text') != None:
                        content_subject[slot]["subjectType"] = subject_type.find('text').text

            # taxonomicRank
            if len(first_record.findall('content.subject.tax.rank')) > 0:
                for slot, subject_tax_rank in enumerate(first_record.findall('content.subject.tax.rank')):
                    if subject_tax_rank.find('text') != None:
                        content_subject[slot]["taxonomicRank"] = subject_tax_rank.find('text').text

            # scientificName
            if len(first_record.findall('content.subject.tax')) > 0:
                for slot, subject_tax in enumerate(first_record.findall('content.subject.tax')):
                    if subject_tax.find('scientific_name') != None:
                        content_subject[slot]["scientificName"] = subject_tax.find('scientific_name').text

            # properName
            if len(first_record.findall('content.subject.name')) > 0:
                for slot, subject_name in enumerate(first_record.findall('content.subject.name')):
                    if subject_name.find('term') != None:
                        content_subject[slot]["properName"] = subject_name.find('term').text


            # identifier
            if len(first_record.findall('content.subject.identifier')) > 0:
                for slot, subject_identifier in enumerate(first_record.findall('content.subject.identifier')):
                    content_subject[slot]["identifier"] = subject_identifier.text

            # notes
            if len(first_record.findall('content.subject.note')) > 0:
                for slot, subject_notes in enumerate(first_record.findall('content.subject.note')):
                    content_subject[slot]["notes"] = subject_notes.text


        object_data['iconography_contentSubject'] = content_subject

        # iconography_contentPeriodDate
        """class IIconographyContentPeriodDate(Interface):
            position = schema.TextLine(title=_(u'Position'), required=False)
            period = schema.TextLine(title=_(u'Period'), required=False)
            startDate = schema.TextLine(title=_(u'Start date'), required=False)
            endDate = schema.TextLine(title=_(u'End date'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        content_period_date = []

        if len(first_record.findall('content.date.period')) > 0:
            for content_period in first_record.findall('content.date.period'):
                if content_period.find('term') != None:
                    content_period_date.append({
                        "position": "",
                        "period": content_period.find('term').text,
                        "startDate": "",
                        "endDate": "",
                        "notes": ""
                    })

        if len(content_period_date) > 0:
            # position
            if len(first_record.findall('content.date.position')) > 0:
                for slot, date_position in enumerate(first_record.findall('content.date.position')):
                    content_period_date[slot]["position"] = date_position.text

            # startDate
            if len(first_record.findall('content.date.start')) > 0:
                for slot, date_start in enumerate(first_record.findall('content.date.start')):
                    content_period_date[slot]["startDate"] = date_start.text

            # endDate
            if len(first_record.findall('content.date.end')) > 0:
                for slot, date_end in enumerate(first_record.findall('content.date.end')):
                    content_period_date[slot]["endDate"] = date_end.text

            # notes
            if len(first_record.findall('content.date.note')) > 0:
                for slot, date_note in enumerate(first_record.findall('content.date.note')):
                    content_period_date[slot]["notes"] = date_note.text

        object_data['iconography_contentPeriodDate'] = content_period_date


        # iconography_iconographySource_sourceGeneral

        # iconography_iconographySource_sourceSpecific

        # iconography_iconographySource_sourceObjectNumber

    def get_associations_tab(self, object_data, first_record):

        # associations_associatedPersonInstitution
        """class IAssociatedPersonInstitution(Interface):
            association = schema.TextLine(title=_(u'Association'), required=False)
            nameType = schema.TextLine(title=_(u'Name Type'), required=False)
            name = schema.TextLine(title=_(u'Name'), required=False)
            startDate = schema.TextLine(title=_(u'Start date'), required=False)
            endDate = schema.TextLine(title=_(u'End date'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        person_institution = []

        if len(first_record.findall('association.person')) > 0:
            for person in first_record.findall('association.person'):
                if person.find('name') != None:
                    person_institution.append({
                        "association":"",
                        "nameType":"",
                        "name": person.find('name').text,
                        "startDate": "",
                        "endDate": "",
                        "notes": ""
                    })

        if len(person_institution) > 0:
            # association
            if len(first_record.findall('association.person.association')) > 0:
                for slot, person_association in enumerate(first_record.findall('association.person.association')):
                    if person_association.find('term') != None:
                        person_institution[slot]["association"] = person_association.find('term').text

            # nameType
            if len(first_record.findall('association.person.type')) > 0:
                for slot, person_type in enumerate(first_record.findall('association.person.type')):
                    if person_type.find('text') != None:
                        person_institution[slot]["nameType"] = person_type.find('text').text

            # startDate
            if len(first_record.findall('association.person.date.start')) > 0:
                for slot, person_startDate in enumerate(first_record.findall('association.person.date.start')):
                    person_institution[slot]["startDate"] = person_startDate.text

            # endDate
            if len(first_record.findall('association.person.date.end')) > 0:
                for slot, person_endDate in enumerate(first_record.findall('association.person.date.end')):
                    person_institution[slot]["endDate"] = person_endDate.text

            # notes
            if len(first_record.findall('association.person.note')) > 0:
                for slot, person_endDate in enumerate(first_record.findall('association.person.note')):
                    person_institution[slot]["notes"] = person_endDate.text


        object_data['associations_associatedPersonInstitution'] = person_institution

        # associations_associatedSubject
        """ class IAssociatedSubject(Interface):
            association = schema.TextLine(title=_(u'Association'), required=False)
            subjectType = schema.TextLine(title=_(u'Subject type'), required=False)
            subject = schema.TextLine(title=_(u'Subject'), required=False)
            taxonomicRank = schema.TextLine(title=_(u'Taxonomic rank'), required=False)
            scientificName = schema.TextLine(title=_(u'Scientific name'), required=False)
            properName = schema.TextLine(title=_(u'Proper name'), required=False)
            startDate = schema.TextLine(title=_(u'Start date'), required=False)
            endDate = schema.TextLine(title=_(u'End date'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False) """

        associated_subject = []

        if len(first_record.findall('association.subject')) > 0:
            for subject in first_record.findall('association.subject'):
                if subject.find('term') != None:
                    associated_subject.append({
                        "association": "",
                        "subjectType": "",
                        "subject": subject.find('term').text,
                        "taxonomicRank": "",
                        "scientificName": "",
                        "properName": "",
                        "startDate": "",
                        "endDate": "",
                        "notes": ""
                    })

        if len(associated_subject) > 0:
            # association
            if len(first_record.findall('association.subject.association')) > 0:
                for slot, subject_association in enumerate(first_record.findall('association.subject.association')):
                    if subject_association.find('term') != None:
                        associated_subject[slot]["association"] = subject_association.find('term').text
            
            # subjectType
            if len(first_record.findall('association.subject.type')) > 0:
                for slot, subject_type in enumerate(first_record.findall('association.subject.type')):
                    if subject_type.find('text') != None:
                        associated_subject[slot]["subjectType"] = subject_type.find('text').text

            # taxonomicRank
            if len(first_record.findall('association.subject.tax.rank')) > 0:
                for slot, subject_tax_rank in enumerate(first_record.findall('association.subject.tax.rank')):
                    if subject_tax_rank.find('text') != None:
                        associated_subject[slot]["taxonomicRank"] = subject_tax_rank.find('text').text


            # scientificName  
            if len(first_record.findall('association.subject.tax')) > 0:
                for slot, subject_tax in enumerate(first_record.findall('association.subject.tax')):
                    if subject_tax.find('scientific_name') != None:
                        associated_subject[slot]["scientificName"] = subject_tax.find('scientific_name').text


            # properName
            if len(first_record.findall('association.subject.name')) > 0:
                for slot, subject_name in enumerate(first_record.findall('association.subject.name')):
                    if subject_name.find('term') != None:
                        associated_subject[slot]["properName"] = subject_name.find('term').text

            # startDate
            if len(first_record.findall('association.subject.date.start')) > 0:
                for slot, subject_startDate in enumerate(first_record.findall('association.subject.date.start')):
                    associated_subject[slot]["startDate"] = subject_startDate.text

            # endDate
            if len(first_record.findall('association.subject.date.end')) > 0:
                for slot, subject_endDate in enumerate(first_record.findall('association.subject.date.end')):
                    associated_subject[slot]["endDate"] = subject_endDate.text

            # notes
            if len(first_record.findall('association.subject.note')) > 0:
                for slot, subject_notes in enumerate(first_record.findall('association.subject.note')):
                    associated_subject[slot]["notes"] = subject_notes.text

        object_data["associations_associatedSubject"] = associated_subject

        # associations_associatedPeriod
        """ class IAssociatedPeriod(Interface):
            association = schema.TextLine(title=_(u'Association'), required=False)
            period = schema.TextLine(title=_(u'Period'), required=False)
            startDate = schema.TextLine(title=_(u'Start date'), required=False)
            endDate = schema.TextLine(title=_(u'End date'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        associated_period = []

        if len(first_record.findall('association.period')) > 0:
            for period in first_record.findall('association.period'):
                if period.find('term') != None:
                    associated_period.append({
                        "association": "",
                        "period": period.find('term').text,
                        "startDate": "",
                        "endDate": "",
                        "notes": ""
                    })

        if len(associated_period) > 0:
            # association
            if len(first_record.findall('association.period.assoc')) > 0:
                for slot, period_association in enumerate(first_record.findall('association.period.assoc')):
                    if period_association.find('term') != None:
                        associated_period[slot]["association"] = period_association.find('term').text

            # startDate
            if len(first_record.findall('association.period.date.start')) > 0:
                for slot, period_startDate in enumerate(first_record.findall('association.period.date.start')):
                    associated_period[slot]["startDate"] = period_startDate.text

            # endDate
            if len(first_record.findall('association.period.date.end')) > 0:
                for slot, period_endDate in enumerate(first_record.findall('association.period.date.end')):
                    associated_period[slot]["endDate"] = period_endDate.text

            # notes
            if len(first_record.findall('association.period.note')) > 0:
                for slot, period_notes in enumerate(first_record.findall('association.period.note')):
                    associated_period[slot]["notes"] = period_notes.text


        object_data['associations_associatedPeriod'] = associated_period


    def get_numbers_relationships_fieldset(self, object_data, first_record):

        # numbersRelationships_numbers 
        """ class INumbers(Interface):
            type = schema.TextLine(title=_(u'Type'), required=False)
            number = schema.TextLine(title=_(u'Number'), required=False)
            institution = schema.TextLine(title=_(u'Institution'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)"""

        numbers = []

        if len(first_record.findall('Alternative_number')) > 0:
            for number in first_record.findall('Alternative_number'):
                new_number = {
                    "type": "",
                    "number": "",
                    "institution": "",
                    "date": ""
                }

                if number.find('alternative_number.type') != None:
                    new_number['type'] = number.find('alternative_number.type').text

                if number.find('alternative_number') != None:
                    new_number['number'] = number.find('alternative_number').text

                if number.find('alternative_number.institution') != None:
                    new_number['institution'] = number.find('alternative_number.institution').text

                if number.find('alternative_number.date') != None:
                    new_number['date'] = number.find('alternative_number.date').text

                numbers.append(new_number)

        object_data['numbersRelationships_numbers'] = numbers

        # numbersRelationships_relationshipsWithOtherObjects_partOf
        if first_record.find('part_of_reference') != None:
            object_data['numbersRelationships_relationshipsWithOtherObjects_partOf'] = first_record.find('part_of_reference').text

        # numbersRelationships_relationshipsWithOtherObjects_notes
        if first_record.find('part_of.notes') != None:
            object_data['numbersRelationships_relationshipsWithOtherObjects_notes'] = first_record.find('part_of.notes').text


        # numbersRelationships_relationshipsWithOtherObjects_parts
        """class IParts(Interface):
            parts = schema.TextLine(title=_(u'Parts'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        parts = []
        if len(first_record.findall('parts_reference')) > 0:
            for part in first_record.findall('parts_reference'):
                parts.append({
                    "parts": part.text,
                    "notes": ""
                })

        if len(parts) > 0:
            if len(first_record.findall('parts.notes')) > 0:
                for slot, part_notes in enumerate(first_record.findall('parts.notes')):
                    parts[slot]["notes"] = part_notes.text

        object_data['numbersRelationships_relationshipsWithOtherObjects_parts'] = parts

        # numbersRelationships_relationshipsWithOtherObjects_relatedObject
        """ class IRelatedObject(Interface):
            relatedObject = schema.TextLine(title=_(u'Related object'), required=False)
            association = schema.TextLine(title=_(u'Association'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        related_objects = []
        if len(first_record.findall("related_object.reference")) > 0:
            for related_object in first_record.findall("related_object.reference"):
                related_objects.append({
                    "relatedObject": related_object.text,
                    "association": "",
                    "notes": ""
                })

        if len(related_objects) > 0:
            # association
            if len(first_record.findall('related_object.association')) > 0:
                for slot, obj_association in enumerate(first_record.findall('related_object.association')):
                    if obj_association.find('term') != None:
                        related_objects[slot]["association"] = obj_association.find('term').text

            # notes
            if len(first_record.findall('related_object.notes')) > 0:
                for slot, obj_notes in enumerate(first_record.findall('related_object.notes')):
                    related_objects[slot]["notes"] = obj_notes.text

        object_data['numbersRelationships_relationshipsWithOtherObjects_relatedObject'] = related_objects

        # numbersRelationships_digitalReferences
        """class IDigitalReferences(Interface):
            type = schema.TextLine(title=_(u'Type'), required=False)
            reference = schema.TextLine(title=_(u'Reference'), required=False)"""

        digital_references = []

        if len(first_record.findall('digital_reference')) > 0:
            for reference in first_record.findall('digital_reference'):
                digital_references.append({
                    "type": "",
                    "reference": reference.text
                })

        if len(digital_references) > 0:
            # type
            if len(first_record.findall('digital_reference.type')) > 0:
                for slot, digital_type in enumerate(first_record.findall('digital_reference.type')):
                    digital_references[slot]["type"] = digital_type.text

        object_data['numbersRelationships_digitalReferences'] = digital_references


    def get_documentation_fieldset(self, object_data, first_record):
        # documentation_documentation
        """ class IDocumentationDocumentation(Interface):
            article = schema.TextLine(title=_(u'Article'), required=False)
            title = schema.TextLine(title=_(u'Title'), required=False)
            author = schema.TextLine(title=_(u'Author'), required=False)
            pageMark = schema.TextLine(title=_(u'Page mark'), required=False)
            shelfMark = schema.TextLine(title=_(u'Shelf mark'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        documentation = []

        if len(first_record.findall('documentation')) > 0:
            for doc in first_record.findall('documentation'):
                new_doc = {
                    "article": "",
                    "title": "",
                    "author": "",
                    "pageMark": "",
                    "shelfMark": "",
                    "notes": ""
                }

                if doc.find('documentation.title.article') != None:
                    new_doc['article'] = doc.find('documentation.title.article').text

                if doc.find('documentation.title') != None:
                    if doc.find('documentation.title').find('title') != None:
                        new_doc['title'] = doc.find('documentation.title').find('title').text

                if doc.find('documentation.author') != None:
                    new_doc['author'] = doc.find('documentation.author').text

                if doc.find('documentation.page_reference') != None:
                    new_doc['pageMark'] = doc.find('documentation.page_reference').text

                if doc.find('documentation.shelfmark') != None:
                    new_doc['shelfMark'] = doc.find('documentation.shelfmark').text

                if doc.find('documentation.notes') != None:
                    new_doc['notes'] = doc.find('documentation.notes').text

                documentation.append(new_doc)


        object_data['documentation_documentation'] = documentation

    def get_documentation_free_archive_fieldset(self, object_data, first_record):

        # documentationFreeArchive_documentationFreeText
        """ class IDocumentationFreeText(Interface):
            title = schema.TextLine(title=_(u'Title'), required=False)"""

        documentation_free_text = []

        if len(first_record.findall('documentation.free_text')) > 0:
            for doc in first_record.findall('documentation.free_text'):
                documentation_free_text.append({
                    "title": doc.text
                })

        object_data['documentationFreeArchive_documentationFreeText'] = documentation_free_text

        # documentationFreeArchive_archive
        """class IArchive(Interface):
            archiveNumber = schema.TextLine(title=_(u'Archive number'), required=False)"""

        archive = []

        if len(first_record.findall("archive.number")) > 0:
            for arch in first_record.findall("archive.number"):
                if arch.find('number') != None:
                    archive.append({
                        "archiveNumber": arch.find('number').text
                    })

        object_data['documentationFreeArchive_archive'] = archive

        
    def get_object_reproductions_fieldset(self, object_data, first_record):
        # reproductions_reproduction
        """ class IReproduction(Interface):
            reference = schema.TextLine(title=_(u'Reference'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)
            format = schema.TextLine(title=_(u'Format'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            identifierURL = schema.TextLine(title=_(u'Identifier (URL)'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        reproductions = [] 

        if len(first_record.findall('reproduction.reference')) > 0:
            for reproduction in first_record.findall('reproduction.reference'):
                
                new_rep = {
                    "reference": "",
                    "type": "",
                    "format": "",
                    "date": "",
                    "identifierURL": "",
                    "notes": ""
                }

                # reference
                if reproduction.find('reference_number') != None:
                    new_rep['reference'] = self.trim_white_spaces(reproduction.find('reference_number').text)

                # type
                if reproduction.find('reproduction_type') != None:
                    new_rep['type'] = self.trim_white_spaces(reproduction.find('reproduction_type').text)

                # format
                if reproduction.find('format') != None:
                    new_rep['format'] = self.trim_white_spaces(reproduction.find('format').text)

                # date
                if reproduction.find('production_date') != None:
                    new_rep['date'] = self.trim_white_spaces(reproduction.find('production_date').text)

                # identifierURL
                if reproduction.find('image_reference') != None:
                    new_rep['identifierURL'] = self.trim_white_spaces(reproduction.find('image_reference').text)

                # notes
                if reproduction.find('notes') != None:
                    new_rep['notes'] = self.trim_white_spaces(reproduction.find('notes').text)

                reproductions.append(new_rep)

        object_data["reproductions_reproduction"] = reproductions

    def get_reproductions_fieldset(self, object_data, first_record):

        # reproductions_reproduction
        """ class IReproduction(Interface):
            reference = schema.TextLine(title=_(u'Reference'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)
            format = schema.TextLine(title=_(u'Format'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            identifierURL = schema.TextLine(title=_(u'Identifier (URL)'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        reproductions = [] 

        if len(first_record.findall('parts_reference')) > 0:
            for reproduction in first_record.findall('parts_reference'):
                
                new_rep = {
                    "reference": "",
                    "type": "",
                    "format": "",
                    "date": "",
                    "identifierURL": "",
                    "notes": ""
                }

                # reference
                if reproduction.find('reproduction.reference') != None:
                    if reproduction.find('reproduction.reference').find('reference_number') != None:
                        new_rep['reference'] = self.trim_white_spaces(reproduction.find('reproduction.reference').find('reference_number').text)

                # type
                if reproduction.find('reproduction.type') != None:
                    new_rep['type'] = self.trim_white_spaces(reproduction.find('reproduction.type').text)

                # format
                if reproduction.find('reproduction.format') != None:
                    new_rep['format'] = self.trim_white_spaces(reproduction.find('reproduction.format').text)

                # date
                if reproduction.find('reproduction.date') != None:
                    new_rep['date'] = self.trim_white_spaces(reproduction.find('reproduction.date').text)

                # identifierURL
                if reproduction.find('reproduction.identifier_URL') != None:
                    new_rep['identifierURL'] = self.trim_white_spaces(reproduction.find('reproduction.identifier_URL').text)

                # notes
                if reproduction.find('reproduction.notes') != None:
                    new_rep['notes'] = self.trim_white_spaces(reproduction.find('reproduction.notes').text)

                reproductions.append(new_rep)

        object_data["reproductions_reproduction"] = reproductions

    def get_field_collection_fieldset(self, object_data, first_record):
        # fieldCollection_fieldCollection_fieldCollNumber
        """class IFieldCollNumber(Interface):
            number = schema.TextLine(title=_(u'Field coll. number'), required=False)"""        
        field_coll_numbers = []

        if len(first_record.findall('field_coll.number')) > 0:
            for number in first_record.findall('field_coll.number'):
                field_coll_numbers.append({
                    "number": number.text
                })

        object_data['fieldCollection_fieldCollection_fieldCollNumber'] = field_coll_numbers
        
        # fieldCollection_fieldCollection_collector
        """class ICollector(Interface):
            name = schema.TextLine(title=_(u'Collector'), required=False)
            role = schema.TextLine(title=_(u'Role'), required=False)"""
        collectors = []

        if len(first_record.findall('field_coll.name')) > 0:
            for collector in first_record.findall('field_coll.name'):
                if collector.find('name') != None:
                    collectors.append({
                        "name": collector.find('name').text,
                        "role": ""
                        })


        if len(collectors) > 0:
            if len(first_record.findall('field_coll.name.role')) > 0:
                for slot, collector_role in enumerate(first_record.findall('field_coll.name.role')):
                    if collector_role.find('term') != None:
                        collectors[slot]["role"] = collector_role.find('term').text

        object_data['fieldCollection_fieldCollection_collector'] = collectors

        # fieldCollection_fieldCollection_event
        """class IEvent(Interface):
            term = schema.TextLine(title=_(u'Event'), required=False)"""
        events = []

        if len(first_record.findall('field_coll.event')) > 0:
            for event in first_record.findall('field_coll.event'):
                if event.find('term') != None:
                    events.append({
                        "term": event.find('term').text
                    })


        object_data['fieldCollection_fieldCollection_event'] = events

        # fieldCollection_fieldCollection_dateEarly
        if first_record.find('field_coll.date.start') != None:
            object_data["fieldCollection_fieldCollection_dateEarly"] = first_record.find('field_coll.date.start').text

        # fieldCollection_fieldCollection_dateEarlyPrecision
        if first_record.find('field_coll.date.start.precision') != None:
            object_data["fieldCollection_fieldCollection_dateEarlyPrecision"] = first_record.find('field_coll.date.start.precision').text

        # fieldCollection_fieldCollection_dateLate
        if first_record.find('field_coll.date.end') != None:
            object_data["fieldCollection_fieldCollection_dateLate"] = first_record.find('field_coll.date.end').text

        # fieldCollection_fieldCollection_dateLatePrecision
        if first_record.find('field_coll.date.end.precision') != None:
            object_data["fieldCollection_fieldCollection_dateLatePrecision"] = first_record.find('field_coll.date.end.precision').text


        # fieldCollection_fieldCollection_method
        """class IMethod(Interface):
            term = schema.TextLine(title=_(u'Method'), required=False) """
        methods = []

        if len(first_record.findall('field_coll.method')) > 0:
            for method in first_record.findall('field_coll.method'):
                if method.find('term') != None:
                    methods.append({
                        "term": method.find('term').text
                    })

        object_data['fieldCollection_fieldCollection_method'] = methods

        # fieldCollection_fieldCollection_place
        """class IPlace(Interface):
            term = schema.TextLine(title=_(u'Place'), required=False)"""
        places = []

        if len(first_record.findall('field_coll.place')) > 0:
            for place in first_record.findall('field_coll.place'):
                if place.find('term') != None:
                    places.append({
                        "term": place.find('term').text
                    })

        object_data['fieldCollection_fieldCollection_place'] = places

        # fieldCollection_fieldCollection_placeCode
        """class IPlaceCode(Interface):
            code = schema.TextLine(title=_(u'Place code'), required=False)
            codeType = schema.TextLine(title=_(u'Code type'), required=False)"""
        place_codes = []

        # fieldCollection_fieldCollection_placeFeature
        object_data['fieldCollection_fieldCollection_placeCode'] = place_codes
        """class IPlaceFeature(Interface):
            term = schema.TextLine(title=_(u'Place feature'), required=False)"""
        

        place_features = []

        if len(first_record.findall('field_coll.place.feature')) > 0:
            for place_feature in first_record.findall('field_coll.place.feature'):
                if place_feature.find('term') != None:
                    place_features.append({
                        "term": place_feature.find('term').text
                    })

        object_data['fieldCollection_fieldCollection_placeFeature'] = place_features

        # fieldCollection_coordinatesFieldCollectionPlace

        collection_places = []
        """class IFieldCollectionPlace(Interface):
            gridType = schema.TextLine(title=_(u'Grid type'), required=False)
            xCoordinate = schema.TextLine(title=_(u'X co-ordinate'), required=False)
            xAddition = schema.TextLine(title=_(u'Addition'), required=False)
            yCoordinate = schema.TextLine(title=_(u'Y co-ordinate'), required=False)
            yAddition = schema.TextLine(title=_(u'Addition'), required=False)
            precision = schema.TextLine(title=_(u'Precision'), required=False)"""
        object_data['fieldCollection_coordinatesFieldCollectionPlace'] = collection_places

        # fieldCollection_habitatStratigraphy_habitat
        habitats = []
        """class IHabitat(Interface):
            term = schema.TextLine(title=_(u'Habitat'), required=False)"""
        object_data['fieldCollection_habitatStratigraphy_habitat'] = habitats

        # fieldCollection_habitatStratigraphy_stratigraphy
        """class IStratigraphy(Interface):
            unit = schema.TextLine(title=_(u'Stratigraphy'), required=False)
            type = schema.TextLine(title=_(u'Strat. type'), required=False)"""
        stratigraphys = []

        if len(first_record.findall('Stratigraphy')) > 0:
            for strati in first_record.findall('Stratigraphy'):
                new_strati = {
                    "unit": "",
                    "type": ""
                }

                if strati.find('stratigraphy.unit') != None:
                    if strati.find('stratigraphy.unit').find('term') != None:
                        new_strati["unit"] = strati.find('stratigraphy.unit').find('term').text

                if strati.find('stratigraphy.type') != None:
                    new_strati["type"] = strati.find('stratigraphy.type').text

        object_data['fieldCollection_habitatStratigraphy_stratigraphy'] = stratigraphys

        # fieldCollection_notes
        notes = []

        if len(first_record.findall('field_coll.notes')) > 0:
            for note in first_record.findall('field_coll.notes'):
                notes.append({
                    "notes": note.text
                })
        object_data['fieldCollection_notes'] = notes

    def get_exhibitions_fieldset(self, object_data, first_record):
        # exhibitions_exhibition
        """class IExhibition(Interface):
            name = schema.TextLine(title=_(u'Exhibition name'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            to = schema.TextLine(title=_(u'to'), required=False)
            organiser = schema.TextLine(title=_(u'Organiser'), required=False)
            venue = schema.TextLine(title=_(u'Venue'), required=False)
            place = schema.TextLine(title=_(u'Place'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)
            catObject = schema.TextLine(title=_(u'Cat. no. object'), required=False)"""
        
        exhibitions = []

        if len(first_record.findall('parts_reference')) > 0:
            for parts_ref in first_record.findall('parts_reference'):
                
                exhibition = parts_ref.find('exhibition')

                if exhibition != None:

                    new_exhibition = {
                        "name": "",
                        "date": "",
                        "to": "",
                        "organiser": "",
                        "venue": "",
                        "place": "",
                        "notes": "",
                        "catObject": ""
                    }

                    if exhibition.find('exhibition') != None:
                        if exhibition.find('exhibition').find('title') != None:
                            new_exhibition['name'] = exhibition.find('exhibition').find('title').text

                    if exhibition.find('exhibition.date.start') != None:
                        new_exhibition['date'] = exhibition.find('exhibition.date.start').text

                    if exhibition.find('exhibition.date.end') != None:
                        new_exhibition['to'] = exhibition.find('exhibition.date.end').text

                    if exhibition.find('exhibition.organiser') != None:
                        new_exhibition['organiser'] = exhibition.find('exhibition.organiser').text

                    if exhibition.find('exhibition.venue') != None:
                        new_exhibition['venue'] = exhibition.find('exhibition.venue').text

                    if exhibition.find('exhibition.venue.place') != None:
                        new_exhibition['place'] = exhibition.find('exhibition.venue.place').text

                    if exhibition.find('exhibition.notes') != None:
                        new_exhibition['notes'] = exhibition.find('exhibition.notes').text

                    if exhibition.find('exhibition.catalogue_number') != None:
                        new_exhibition['catObject'] = exhibition.find('exhibition.catalogue_number').text

                    exhibitions.append(new_exhibition)

        object_data['exhibitions_exhibition'] = exhibitions



    def get_recommendations_requirements(self, object_data, first_record):
        #'recommendationsRequirements_creditLine_creditLine':""
        if first_record.find('credit_line') != None:
            object_data['recommendationsRequirements_creditLine_creditLine'] = self.trim_white_spaces(first_record.find('credit_line').text)

        #'recommendationsRequirements_legalLicenceRequirements_requirements':"",
        if first_record.find('requirem.legal') != None:
            object_data['recommendationsRequirements_legalLicenceRequirements_requirements'] = self.trim_white_spaces(first_record.find('requirem.legal').text)

        #'recommendationsRequirements_legalLicenceRequirements_requirementsHeld':[],
        """class IRequirements(Interface):
            requirementsHeld = schema.TextLine(title=_(u'Requirements held'), required=False)
            number = schema.TextLine(title=_(u'Number'), required=False)
            currentFrom = schema.TextLine(title=_(u'Current From'), required=False)
            until = schema.TextLine(title=_(u'Until'), required=False)
            renewalDate = schema.TextLine(title=_(u'Renewal date'), required=False)"""
        requirements = []

        for requirement in first_record.findall('requirem.legal.held'):
            requirements.append({
                "requirementsHeld": self.trim_white_spaces(requirement.text),
                "number": "",
                "currentFrom": "",
                "until": "",
                "renewalDate": ""
                })

        if len(requirements) > 0:
            for slot, number in first_record.findall('requirem.legal.held.number'):
                requirements[slot]['number'] = self.trim_white_spaces(number.text)

            for slot, currentFrom in first_record.findall('requirem.legal.held.date.start'):
                requirements[slot]['currentFrom'] = self.trim_white_spaces(currentFrom.text)

            for slot, until in first_record.findall('requirem.legal.held.date.end'):
                requirements[slot]['until'] = self.trim_white_spaces(until.text)

            for slot, renewalDate in first_record.findall('requirem.legal.held.renewal'):
                requirements[slot]['renewalDate'] = self.trim_white_spaces(renewalDate.text)

        object_data['recommendationsRequirements_legalLicenceRequirements_requirementsHeld'] = requirements


    def get_loans_fieldset(self, object_data, first_record):
        """class IIncomingLoan(Interface):
        loanNumber = schema.TextLine(title=_(u'Loan number'), required=False)
        status = schema.TextLine(title=_(u'Status'), required=False)
        lender = schema.TextLine(title=_(u'Lender'), required=False)
        contact = schema.TextLine(title=_(u'Contact'), required=False)
        requestReason = schema.TextLine(title=_(u'Request reason'), required=False)
        requestPeriod = schema.TextLine(title=_(u'Request period'), required=False)
        requestPeriodTo = schema.TextLine(title=_(u'to'), required=False)
        contractPeriod = schema.TextLine(title=_(u'Contract period'), required=False)
        contractPeriodTo = schema.TextLine(title=_(u'to'), required=False)"""


        """class IOutgoingLoan(Interface):
        loanNumber = schema.TextLine(title=_(u'Loan number'), required=False)
        status = schema.TextLine(title=_(u'Status'), required=False)
        requester = schema.TextLine(title=_(u'Requester'), required=False)
        contact = schema.TextLine(title=_(u'Contact'), required=False)
        requestReason = schema.TextLine(title=_(u'Request reason'), required=False)
        requestPeriod = schema.TextLine(title=_(u'Request period'), required=False)
        requestPeriodTo = schema.TextLine(title=_(u'to'), required=False)
        contractPeriod = schema.TextLine(title=_(u'Contract period'), required=False)
        contractPeriodTo = schema.TextLine(title=_(u'to'), required=False)"""

        pass


    def get_zm_object(self, priref, record, create):

        first_record = record

        object_data = {
            # ZM FIELDS #

            # Identification
            "identification_identification_institutionName": "",
            "identification_identification_administrativeName": "",
            "identification_identification_collection": "",
            "identification_identification_objectNumber": "",
            "identification_identification_part": "",
            "identification_identification_totNumber": "",
            "identification_identification_copyNumber": "",
            "identification_identification_edition": "",
            "identification_identification_distinguishFeatures": "",
            "identification_objectName_objectCategory": [],
            "identification_objectName_objectName": [],
            "identification_objectName_otherName": [],
            "identification_titleDescription_notes": "",
            "identification_titleDescription_translatedTitle": "",
            "identification_titleDescription_language": "",
            "identification_titleDescription_describer": "",
            "identification_titleDescription_date": "",
            "identification_taxonomy": [],
            "identification_taxonomy_determiner": [],
            "identification_taxonomy_object_status": "",
            "identification_taxonomy_notes": [],


            # ZM physical characteristics
            "physicalCharacteristics_physicalDescription_description":"",
            "physicalCharacteristics_keywords":[],
            "physicalCharacteristics_techniques":[],
            "physicalCharacteristics_materials" :[],
            "physicalCharacteristics_dimensions":[],
            "physicalCharacteristics_dimensions_free_text":"",
            "physicalCharacteristics_frame":"",
            "physicalCharacteristics_frame_detail":"",

            # ZM Production dating
            "productionDating_production": [],
            "productionDating_production_productionReason": "",
            "productionDating_production_schoolStyle": [],
            "productionDating_dating_period": [],
            "productionDating_dating_notes": [],

            # Iconography
            "iconography_generalSearchCriteria_generalTheme": [],
            "iconography_generalSearchCriteria_specificTheme": [],
            "iconography_generalSearchCriteria_classificationTheme": [],
            "iconography_contentDescription": [],
            "iconography_contentPersonInstitution": [],
            "iconography_contentSubject": [],
            "iconography_contentPeriodDate": [],
            "iconography_iconographySource_sourceGeneral": "",
            "iconography_iconographySource_sourceSpecific": "",
            "iconography_iconographySource_sourceObjectNumber": "",

            # Condition & Conservation
            "conditionConservation_priority": "low",
            "conditionConservation_next_condition_check": "",
            "conditionConservation_date": "",
            "conditionConservation_completeness": [],
            "conditionConservation_condition": [],
            "conditionConservation_enviromental_condition": [],
            "conditionConservation_conservation_request": [],
            'conditionConservation_recommendations_display':"",
            'conditionConservation_recommendations_environment':"",
            'conditionConservation_recommendations_handling':"",
            'conditionConservation_recommendations_packing':"",
            'conditionConservation_recommendations_security':"",
            'conditionConservation_recommendations_storage':"",

            # Recommendations/requirements
            'recommendationsRequirements_creditLine_creditLine':"",
            'recommendationsRequirements_legalLicenceRequirements_requirements':"",
            'recommendationsRequirements_legalLicenceRequirements_requirementsHeld':[],

            # Inscriptions and Markings
            "inscriptionsMarkings_inscriptionsMarkings": [],

            # Numbers / relationships
            "numbersRelationships_numbers": [],
            "numbersRelationships_relationshipsWithOtherObjects_partOf": "",
            "numbersRelationships_relationshipsWithOtherObjects_notes": "",
            "numbersRelationships_relationshipsWithOtherObjects_parts": [],
            "numbersRelationships_relationshipsWithOtherObjects_relatedObject": [],
            "numbersRelationships_digitalReferences": [],

            # Documentation 
            "documentation_documentation": [],

            # Documentation (free) / archive
            "documentationFreeArchive_documentationFreeText": [],
            "documentationFreeArchive_archive": [],

            # Reproductions
            "reproductions_reproduction": [],

            # Associations
            "associations_associatedPersonInstitution": [],
            "associations_associatedSubject": [],
            "associations_associatedPeriod": [],

            # Value & Insurance
            "valueInsurance_valuation": [],
            "valueInsurance_insurance": [],

            # Acquisition
            "acquisition_accession_date": "",
            "acquisition_number": "",
            "acquisition_date": "",
            "acquisition_precision": "",
            "acquisition_method": "",
            "acquisition_rec_no": "",
            "acquisition_lot_no": "",
            "acquisition_from": "",
            "acquisition_auction": "",
            "acquisition_place": "",
            "acquisition_reason": "",
            "acquisition_conditions": "",
            "acquisition_authorization_authorizer": "",
            "acquisition_authorization_date": "",
            "acquisition_costs_offer_price":"",
            "acquisition_costs_offer_price_curr": "",
            "acquisition_costs_purchase_price": "",
            "acquisition_costs_purchase_price_curr": "",
            "acquisition_costs_notes": "",
            "acquisition_funding": [],
            "acquisition_documentation": [],
            "acquisition_copyright": "",
            "acquisition_notes": "",

            # Disposal
            "disposal_deaccession":"",
            "disposal_new_object_number":"",
            "disposal_number":"",
            "disposal_date":"",
            "disposal_method":"",
            "disposal_proposed_recipient":"",
            "disposal_recipient":"",
            "disposal_reason":"",
            "disposal_provisos":"",
            "disposal_finance_disposal_price":"",
            "disposal_finance_currency":[],
            "disposal_documentation":"",
            "disposal_notes":"",

            # Ownership history
            "ownershipHistory_current_owner":"",
            "ownershipHistory_owner":"",
            "ownershipHistory_from":"",
            "ownershipHistory_until":"",
            "ownershipHistory_exchange_method":"",
            "ownershipHistory_acquired_from":"",
            "ownershipHistory_auction":"",
            "ownershipHistory_rec_no":"",
            "ownershipHistory_lot_no":"",
            "ownershipHistory_place":"",
            "ownershipHistory_price":"",
            "ownershipHistory_category":"",
            "ownershipHistory_access":"",
            "ownershipHistory_notes":"",

            # Location
            "location_normal_location": "",
            "location_current_location": [],
            "location_checks": [],

            # Notes
            "notes": [],
            "notes_free_fields": [],

            # Labels
            "labels": [],

            # Field Collection
            'fieldCollection_fieldCollection_fieldCollNumber':[],
            'fieldCollection_fieldCollection_collector':[],

            'fieldCollection_fieldCollection_event':[],
            'fieldCollection_fieldCollection_dateEarly': "",

            'fieldCollection_fieldCollection_dateEarlyPrecision': "",
            'fieldCollection_fieldCollection_dateLate': "",

            'fieldCollection_fieldCollection_dateLatePrecision': "",
            'fieldCollection_fieldCollection_method':[],

            'fieldCollection_fieldCollection_place':[],
            'fieldCollection_fieldCollection_placeCode':[],

            'fieldCollection_fieldCollection_placeFeature':[],
            'fieldCollection_coordinatesFieldCollectionPlace':[],

            'fieldCollection_habitatStratigraphy_habitat':[],
            'fieldCollection_habitatStratigraphy_stratigraphy':[],

            'fieldCollection_notes':[],

            # TM fields #
            "title": "",
            "dirty_id": "",
            "description": "",
            "artist": "",
            "text": "",
            "object_type": "",
            "dating": "",
            "term": "",
            "material": "",
            "technique": "",
            "dimension": "",
            "credit_line": "",
            "object_description": "",
            "inscription": "",
            "scientific_name": "",
            "translated_title": "",
            "production_period": "",
            "location": "",
            "publisher": "",
            "fossil_dating": "",
            "illustrator": "",
            "author": "",
            "digital_reference": "",
            "production_notes": "",
            "tags": [],

            # Exhibitions
            "exhibitions_exhibition": [],

            # Loans
            "loans_incomingLoans": [],
            "loans_outgoingLoans": []
        }

        object_temp_data = {
            "production_date_end": "",
            "production_date_start": "",
            "production_date_prec": "",
            "dimensions": []
        }

        inscription_temp_data = []
        
        try:
            ####
            #### Identification
            #### 
            self.get_identification_fieldset(object_data, first_record)
        except:
            pass

        try:
            ####
            #### Physical Characteristics
            ####
            self.get_physical_characteristics_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Production / Dating
            ###
            self.get_production_dating_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Iconography
            ###
            self.get_iconography_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Condition & Conservation
            ###
            self.get_condition_and_conservation_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Inscriptions and Markings
            ###
            self.get_inscriptions_and_markings_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Numbers / relationships
            ###
            self.get_numbers_relationships_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Documentation
            ###
            self.get_documentation_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Documentation (free) / archive
            ###
            self.get_documentation_free_archive_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Reproductions
            ###
            self.get_object_reproductions_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Associations
            ###
            self.get_associations_tab(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Value & Insurance
            ###
            self.get_value_insurance_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Acquisition
            ###
            self.get_acquisition_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Recommendations/requirements
            ###
            self.get_recommendations_requirements_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Disposal
            ###
            self.get_disposal_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Ownership history
            ###
            self.get_ownership_history_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Location
            ###
            self.get_location_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Notes
            ###
            self.get_notes_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Labels
            ###
            self.get_label_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Field Collection
            ###
            self.get_field_collection_fieldset(object_data, first_record)
        except:
            pass
        
        try:
            ###
            ### Exhibitions
            ###
            self.get_exhibitions_fieldset(object_data, first_record)
        except:
            pass


        try:
            ###
            ### Loans
            ###
            self.get_loans_fieldset(object_data, first_record)
        except:
            pass
    
        ###
        ### Create dirty object ID
        ###    
        object_data['dirty_id'] = self.create_object_dirty_id(object_data['identification_identification_objectNumber'], object_data['title'], object_data['artist'])

        if create:
            result = self.create_zm_object(object_data)
            return result
        else:
            return object_data

    ###
    ### Creates object in Plone folder
    ###
    def create_zm_object(self, obj):
        
        transaction.begin()
        
        container = self.get_container()
        dirty_id = obj['dirty_id']
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Object already exists normalized_id %s" % (timestamp, obj["identification_identification_objectNumber"])
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_object_from_instance(obj["identification_identification_objectNumber"])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(obj['text'], 'text/html', 'text/html')

                    if (obj['title'] == "") or (obj['title'] == None):
                        obj['title'] = obj['identification_identification_objectNumber']

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Object",
                        id=normalized_id,
                        title=obj['title'],
                        description=obj['description'],
                        text=text,

                        ## Identification
                        identification_identification_institutionName=obj["identification_identification_institutionName"],
                        identification_identification_administrativeName=obj["identification_identification_administrativeName"],
                        identification_identification_collection=obj["identification_identification_collection"],
                        identification_identification_objectNumber=obj["identification_identification_objectNumber"],
                        identification_identification_part=obj["identification_identification_part"],
                        identification_identification_totNumber=obj["identification_identification_totNumber"],
                        identification_identification_copyNumber=obj["identification_identification_copyNumber"],
                        identification_identification_edition=obj["identification_identification_edition"],
                        identification_identification_distinguishFeatures=obj["identification_identification_distinguishFeatures"],
                        identification_objectName_objectCategory=obj["identification_objectName_objectCategory"],
                        identification_objectName_objectName=obj["identification_objectName_objectName"],
                        identification_objectName_otherName=obj["identification_objectName_otherName"],
                        identification_titleDescription_notes=obj["identification_titleDescription_notes"],
                        identification_titleDescription_translatedTitle=obj["identification_titleDescription_translatedTitle"],
                        identification_titleDescription_language=obj["identification_titleDescription_language"],
                        identification_titleDescription_describer=obj["identification_titleDescription_describer"],
                        identification_titleDescription_date=obj["identification_titleDescription_date"],
                        identification_taxonomy=obj["identification_taxonomy"],
                        identification_taxonomy_determiner=obj["identification_taxonomy_determiner"],
                        identification_taxonomy_object_status=obj["identification_taxonomy_object_status"],
                        identification_taxonomy_notes=obj["identification_taxonomy_notes"],

                        # Physical Char.
                        physicalCharacteristics_physicalDescription_description=obj['physicalCharacteristics_physicalDescription_description'],
                        physicalCharacteristics_keywords=obj['physicalCharacteristics_keywords'],
                        physicalCharacteristics_techniques=obj['physicalCharacteristics_techniques'],
                        physicalCharacteristics_dimensions=obj["physicalCharacteristics_dimensions"],
                        physicalCharacteristics_materials=obj['physicalCharacteristics_materials'],
                        physicalCharacteristics_frame=obj['physicalCharacteristics_frame'],

                        # Iconography
                        iconography_generalSearchCriteria_generalTheme=obj["iconography_generalSearchCriteria_generalTheme"],
                        iconography_generalSearchCriteria_specificTheme=obj["iconography_generalSearchCriteria_specificTheme"],
                        iconography_generalSearchCriteria_classificationTheme=obj["iconography_generalSearchCriteria_classificationTheme"],
                        iconography_contentDescription=obj["iconography_contentDescription"],
                        iconography_contentPersonInstitution=obj["iconography_contentPersonInstitution"],
                        iconography_contentSubject=obj["iconography_contentSubject"],
                        iconography_contentPeriodDate=obj["iconography_contentPeriodDate"],
                        iconography_iconographySource_sourceGeneral=obj["iconography_iconographySource_sourceGeneral"],
                        iconography_iconographySource_sourceSpecific=obj["iconography_iconographySource_sourceSpecific"],
                        iconography_iconographySource_sourceObjectNumber=obj["iconography_iconographySource_sourceObjectNumber"],

                        # Prod. Dating
                        productionDating_production=obj['productionDating_production'],
                        productionDating_production_productionReason=obj['productionDating_production_productionReason'],
                        productionDating_production_schoolStyle=obj['productionDating_production_schoolStyle'],
                        productionDating_dating_period=obj['productionDating_dating_period'],
                        productionDating_dating_notes=obj['productionDating_dating_notes'],

                        # Condition & Conservation
                        conditionConservation_priority=obj['conditionConservation_priority'],
                        conditionConservation_next_condition_check=obj['conditionConservation_next_condition_check'],
                        conditionConservation_date=obj['conditionConservation_date'],
                        conditionConservation_completeness=obj['conditionConservation_completeness'],
                        conditionConservation_condition=obj['conditionConservation_condition'],
                        conditionConservation_enviromental_condition=obj['conditionConservation_enviromental_condition'],
                        conditionConservation_conservation_request=obj['conditionConservation_conservation_request'],
                        conditionConservation_recommendations_display=obj['conditionConservation_recommendations_display'],
                        conditionConservation_recommendations_environment=obj['conditionConservation_recommendations_environment'],
                        conditionConservation_recommendations_handling=obj['conditionConservation_recommendations_handling'],
                        conditionConservation_recommendations_packing=obj['conditionConservation_recommendations_packing'],
                        conditionConservation_recommendations_security=obj['conditionConservation_recommendations_security'],
                        conditionConservation_recommendations_storage=obj['conditionConservation_recommendations_storage'],

                        # Inscriptions and markings
                        inscriptionsMarkings_inscriptionsMarkings=obj['inscriptionsMarkings_inscriptionsMarkings'],

                        # Numbers / relationships
                        numbersRelationships_numbers=obj["numbersRelationships_numbers"],
                        numbersRelationships_relationshipsWithOtherObjects_partOf=obj["numbersRelationships_relationshipsWithOtherObjects_partOf"],
                        numbersRelationships_relationshipsWithOtherObjects_notes=obj["numbersRelationships_relationshipsWithOtherObjects_notes"],
                        numbersRelationships_relationshipsWithOtherObjects_parts=obj["numbersRelationships_relationshipsWithOtherObjects_parts"],
                        numbersRelationships_relationshipsWithOtherObjects_relatedObject=obj["numbersRelationships_relationshipsWithOtherObjects_relatedObject"],
                        numbersRelationships_digitalReferences=obj["numbersRelationships_digitalReferences"],

                        # Documentation
                        documentation_documentation=obj['documentation_documentation'],

                        # Documentation (free) / archive 
                        documentationFreeArchive_documentationFreeText=obj["documentationFreeArchive_documentationFreeText"],
                        documentationFreeArchive_archive=obj["documentationFreeArchive_archive"],

                        # Reproductions
                        reproductions_reproduction=obj["reproductions_reproduction"],

                        # Associations
                        associations_associatedPersonInstitution=obj["associations_associatedPersonInstitution"],
                        associations_associatedSubject=obj["associations_associatedSubject"],
                        associations_associatedPeriod=obj["associations_associatedPeriod"],

                        # Value & Insurance
                        valueInsurance_valuation=obj['valueInsurance_valuation'],
                        valueInsurance_insurance=obj['valueInsurance_insurance'],

                        # Acquisition
                        acquisition_accession_date=obj["acquisition_accession_date"],
                        acquisition_number=obj["acquisition_number"],
                        acquisition_date=obj["acquisition_date"],
                        acquisition_precision=obj["acquisition_precision"],
                        acquisition_method=obj["acquisition_method"],
                        acquisition_rec_no=obj["acquisition_rec_no"],
                        acquisition_lot_no=obj["acquisition_lot_no"],
                        acquisition_from=obj["acquisition_from"],
                        acquisition_auction=obj["acquisition_auction"],
                        acquisition_place=obj["acquisition_place"],
                        acquisition_reason=obj["acquisition_reason"],
                        acquisition_conditions=obj["acquisition_conditions"],
                        acquisition_authorization_authorizer=obj["acquisition_authorization_authorizer"],
                        acquisition_authorization_date=obj["acquisition_authorization_date"],
                        acquisition_costs_offer_price=obj["acquisition_costs_offer_price"],
                        acquisition_costs_offer_price_curr=obj["acquisition_costs_offer_price_curr"],
                        acquisition_costs_purchase_price=obj["acquisition_costs_purchase_price"],
                        acquisition_costs_purchase_price_curr=obj["acquisition_costs_purchase_price_curr"],
                        acquisition_costs_notes=obj["acquisition_costs_notes"],
                        acquisition_funding=obj["acquisition_funding"],
                        acquisition_documentation=obj["acquisition_documentation"],
                        acquisition_copyright=obj["acquisition_copyright"],
                        acquisition_notes=obj["acquisition_notes"],

                        # Disposal
                        disposal_deaccession=obj["disposal_deaccession"],
                        disposal_new_object_number=obj["disposal_new_object_number"],
                        disposal_number=obj["disposal_number"],
                        disposal_date=obj["disposal_date"],
                        disposal_method=obj["disposal_method"],
                        disposal_proposed_recipient=obj["disposal_proposed_recipient"],
                        disposal_recipient=obj["disposal_recipient"],
                        disposal_reason=obj["disposal_reason"],
                        disposal_provisos=obj["disposal_provisos"],
                        disposal_finance_disposal_price=obj["disposal_finance_disposal_price"],
                        #disposal_finance_currency=obj["disposal_finance_curr"],
                        disposal_documentation=obj["disposal_documentation"],
                        disposal_notes=obj["disposal_notes"],

                        # Ownership history
                        ownershipHistory_current_owner=obj["ownershipHistory_current_owner"],
                        ownershipHistory_owner=obj["ownershipHistory_owner"],
                        ownershipHistory_from=obj["ownershipHistory_from"],
                        ownershipHistory_until=obj["ownershipHistory_until"],
                        ownershipHistory_exchange_method=obj["ownershipHistory_exchange_method"],
                        ownershipHistory_acquired_from=obj["ownershipHistory_acquired_from"],
                        ownershipHistory_auction=obj["ownershipHistory_auction"],
                        ownershipHistory_rec_no=obj["ownershipHistory_rec_no"],
                        ownershipHistory_lot_no=obj["ownershipHistory_lot_no"],
                        ownershipHistory_place=obj["ownershipHistory_place"],
                        ownershipHistory_price=obj["ownershipHistory_price"],
                        ownershipHistory_category=obj["ownershipHistory_category"],
                        ownershipHistory_access=obj["ownershipHistory_access"],
                        ownershipHistory_notes=obj["ownershipHistory_notes"],

                        # Location
                        location_normal_location=obj["location_normal_location"],
                        location_current_location=obj["location_current_location"],
                        location_checks=obj["location_checks"],

                        # Notes
                        notes=obj['notes'],
                        notes_free_fields=obj['notes_free_fields'],

                        # Labels
                        labels=obj['labels'],

                        # Field Collection
                        fieldCollection_fieldCollection_fieldCollNumber=obj["fieldCollection_fieldCollection_fieldCollNumber"],
                        fieldCollection_fieldCollection_collector=obj["fieldCollection_fieldCollection_collector"],
                        fieldCollection_fieldCollection_event=obj["fieldCollection_fieldCollection_event"],
                        fieldCollection_fieldCollection_dateEarly=obj["fieldCollection_fieldCollection_dateEarly"],
                        fieldCollection_fieldCollection_dateEarlyPrecision=obj["fieldCollection_fieldCollection_dateEarlyPrecision"],
                        fieldCollection_fieldCollection_dateLate=obj["fieldCollection_fieldCollection_dateLate"],
                        fieldCollection_fieldCollection_dateLatePrecision=obj["fieldCollection_fieldCollection_dateLatePrecision"],
                        fieldCollection_fieldCollection_method=obj["fieldCollection_fieldCollection_method"],
                        fieldCollection_fieldCollection_place=obj["fieldCollection_fieldCollection_place"],
                        fieldCollection_fieldCollection_placeCode=obj["fieldCollection_fieldCollection_placeCode"],
                        fieldCollection_fieldCollection_placeFeature=obj["fieldCollection_fieldCollection_placeFeature"],
                        fieldCollection_coordinatesFieldCollectionPlace=obj["fieldCollection_coordinatesFieldCollectionPlace"],
                        fieldCollection_habitatStratigraphy_habitat=obj["fieldCollection_habitatStratigraphy_habitat"],
                        fieldCollection_habitatStratigraphy_stratigraphy=obj["fieldCollection_habitatStratigraphy_stratigraphy"],
                        fieldCollection_notes=obj["fieldCollection_notes"],

                        # Exhibitions
                        exhibitions_exhibition=obj["exhibitions_exhibition"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    

                    #### Commmit to the database
                    transaction.commit()

                    #### Log object added
                    timestamp = datetime.datetime.today().isoformat()
                    #print "%s - Added object %s" % (timestamp, obj["identification_identification_objectNumber"])

                    self.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Object already exists container %s" % (timestamp, obj["identification_identification_objectNumber"])
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.errors += 1
            self.success = False
            print "Unexpected error on create_object (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            #print "%s - Skipped object: %s" %(timestamp, obj["object_number"])

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def get_zm_collection(self, path):
        xmlFilePath = path
        xmlDoc = etree.parse(xmlFilePath)

        root = xmlDoc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()

        return records, xmlDoc

    def image_in_list_images(self, name, images_list):
        #
        # Check if image is in server
        #
        for img in images_list:
            if img['name'].lower() == name.lower():
                return img["path"]

        return None

    def get_obj_from_xml(self, objects, object_number):
        for obj in objects:
            if obj.find('object_number') != None:
                if obj.find('object_number').text == object_number:
                    print "Found obj in XML"
                    return obj

        return None

    def update_zm_collection(self):
        collection_path = "/Users/AG/Projects/collectie-zm/grouped2.xml"
        server_path = "/var/dev/collectie-zm-v0/xml/grouped2.xml"
        prod_server_path = "/var/www/zm-collectie/xml/grouped2.xml"

        objects = self.get_zm_collection(prod_server_path)
        print "Got collection!"

        collection = self.get_container()

        total = len(collection)
        curr = 0

        for item in list(collection):
            try:
                transaction.begin()
                curr += 1
                ob = collection[item]
                if ob.portal_type == 'Object':
                    if hasattr(ob, 'identification_identification_objectNumber'):

                        # Update title
                        if hasattr(ob, 'title'):
                            object_number = ob.identification_identification_objectNumber
                            record = self.get_obj_from_xml(objects, object_number)
                            if record != None:

                                new_title = ""
                                if record.find('title') != None:
                                    new_title = record.find('title').text

                                if new_title != "" and new_title != None:
                                    ob.title = new_title

                                else:
                                    ob.title = str(ob.identification_identification_objectNumber)

                                ob.reindexObject()

                                print "Updated Object %s / %s" %(str(curr), str(total))

                        # Update administrative name
                        """if hasattr(ob, 'identification_identification_administrativeName'):
                            object_number = ob.identification_identification_objectNumber

                            record = self.get_obj_from_xml(objects, object_number)
                            if record != None:
                                data = {
                                    "identification_identification_administrativeName": "",
                                }
                                
                                if record.find('administration_name') != None:
                                    data['identification_identification_administrativeName'] = self.trim_white_spaces(record.find('administration_name').text)

                                ob.identification_identification_administrativeName = data['identification_identification_administrativeName']
                                #ob.reindexObject()

                                print "Updated Object %s / %s" %(str(curr), str(total))"""
                transaction.commit()

            except:
                transaction.abort()
                raise

        self.success = True
        return True



    def update_field_usage(self, data, field_usage):
        if data['institution_name'] != "":
            field_usage["institution_name"] += 1

        if data['administrative_name'] != "":
            field_usage["administrative_name"] += 1

        if data['collection'] != "":
            field_usage["collection"] += 1

        if data['object_number'] != "":
            field_usage["object_number"] += 1

        if data['part'] != "":
            field_usage["part"] += 1

        if data['tot_number'] != "":
            field_usage["tot_number"] += 1

        if data['copy_number'] != "":
            field_usage["copy_number"] += 1

        if data['edition'] != "":
            field_usage["edition"] += 1

        if data['distinguish_features'] != "":
            field_usage["distinguish_features"] += 1

        if data['object_category'] != "":
            field_usage["object_category"] += 1

        if data['object_name'] != "":
            field_usage["object_name"] += 1

        if data["object_name_type"] != "":
            field_usage["object_name_type"] += 1

        if data["object_name_notes"] != "":
            field_usage["object_name_notes"] += 1

        if data['other_name'] != "":
            field_usage["other_name"] += 1

        if data['other_name_type'] != "":
            field_usage["other_name_type"] += 1


    def check_themes(self):

        total_values = {
            # geschiedenis
            'archeologie':0,
            'beeld en geluid - overig':0,
            'bouwfragmenten':0,
            'boeken':0,
            'documenten':0,
            'etnografica - boeken':0,
            'etnografica - documenten':0,
            'etnografica - gebruiksvoorwerpen':0,
            'etnografica - modellen':0,
            'etnografica - wapens':0,
            'gebruiksvoorwerpen':0,
            'historische voorwerpen en memorabilia':0,
            'modellen - volkskunst':0,
            'munten en penningen':0,
            'plat textiel - gebruiksgoed':0,
            'wapens en munitie': 0,

            # kunst
            'beeldhouwwerken':0,
            'etnografica - beelden':0,
            'moderne en hedendaagse kunst':0,
            'prenten en tekeningen':0,
            'schilderkunst':0,

            # kunstnijverheid
            'aardewerk en tegels':0,
            'etnografica - kunstnijverheid':0,
            'kunstnijverheid':0,
            'meubilair':0,
            'modellen - kunstnijverheid':0,
            'plat textiel - kunstnijverheid':0,
            'porselein':0,
            'zilver en goud':0,

            # mode_en_streekdracht

            'beeld en geluid - streekdracht':0,
            'etnografica - kleding en accessoires':0,
            'etnografica - sieraden':0,
            'sieraden (geen streeksieraden)':0,
            'streekdrachten en mode':0,
            'streeksieraden':0,

            # natuurhistorie
            'etnografica - natuurhistorie':0,
            'natuurhistorie':0,

            # _16eEeuwseZeeuwsewandtapijten
            '16e eeuwse zeeuwse wandtapijten': 0

        }

        geschiedenis = ['Archeologie', 'Beeld en geluid - overig', 'Bouwfragmenten', 'Boeken',
                        'Documenten', 'Etnografica - boeken', 'Etnografica - documenten',
                        'Etnografica - gebruiksvoorwerpen', 'Etnografica - modellen',
                        'Etnografica - wapens', 'Gebruiksvoorwerpen', 'Historische voorwerpen en memorabilia',
                        'Modellen - volkskunst', 'Munten en penningen', 'Plat textiel - gebruiksgoed',
                        'Wapens en munitie']

        _geschiedenis = [item.lower() for item in geschiedenis]

        kunst = ['Beeldhouwwerken', 'Etnografica - beelden', 'Moderne en hedendaagse kunst',
                'Prenten en tekeningen', 'Schilderkunst']

        _kunst = [item.lower() for item in kunst]

        kunstnijverheid = ['Aardewerk en tegels', 'Etnografica - kunstnijverheid', 'Kunstnijverheid',
                            'Meubilair', 'Modellen - kunstnijverheid', 'Plat textiel - kunstnijverheid',
                            'Porselein', 'Zilver en goud']

        _kunstnijverheid = [item.lower() for item in kunstnijverheid]

        mode_en_streekdracht = ['Beeld en geluid - streekdracht', 'Etnografica - kleding en accessoires',
                                'Etnografica - sieraden', 'Sieraden (geen streeksieraden)',
                                'Streekdrachten en mode', 'Streeksieraden']

        _mode_en_streekdracht = [item.lower() for item in mode_en_streekdracht]

        natuurhistorie = ['etnografica - natuurhistorie', 'natuurhistorie']
        _natuurhistorie = [item.lower() for item in natuurhistorie]

        _16eEeuwseZeeuwsewandtapijten = ['16e Eeuwse Zeeuwse wandtapijten']
        __16eEeuwseZeeuwsewandtapijten = [item.lower() for item in _16eEeuwseZeeuwsewandtapijten]

        collection_path = "/var/www/zm-collectie-v2/xml/objectsall.xml"
        objects = self.get_zm_collection(collection_path)
        print "Got collection XML!"

        total_without_admin_name = 0
        total_with_admin_name_empty = 0
        total_not_in_list = 0

        for obj in list(objects):
            if obj.find('administration_name') != None:
                if obj.find('administration_name').text != "":
                    admin_name = obj.find('administration_name').text
                    admin_name = admin_name.lower()
                    if (admin_name in _geschiedenis) or (admin_name in _kunst) or (admin_name in _kunstnijverheid) or (admin_name in _mode_en_streekdracht) or (admin_name in _natuurhistorie) or (admin_name in __16eEeuwseZeeuwsewandtapijten):
                        total_values[admin_name] += 1
                    else:
                        total_not_in_list += 1
                else:
                    total_with_admin_name_empty += 1
            else:
                total_without_admin_name += 1

        print "Total without admin name field %s" %(str(total_without_admin_name))
        print "Total with admin name empty %s" %(str(total_with_admin_name_empty))
        print "Total not in list: %s" %(str(total_not_in_list))
        print "\n"
        print "Total values"
        print total_values




    def check_zm_collection(self):
        total_objects_in_xml = 0
        total_images = 0
        total_images_w_text = 0
        total_objects_with_images = 0
        total_objects_without_images = 0
        total_images_not_found = 0
        total_images_found = 0
        total_distinct_images = []

        images_not_found = []

        collection_path = "/var/www/zm-collectie-v2/xml/objectsall.xml"
        objects = self.get_zm_collection(collection_path)
        print "Got collection XML!"

        list_images = []
        for root, dirnames, filenames in os.walk('/var/www/zm-data/zm-collection'):
            for filename in fnmatch.filter(filenames, '*.jpg'):
                list_images.append({"path": os.path.join(root, filename), "name": filename})

        for root, dirnames, filenames in os.walk('/var/www/zm-data/zm-collection'):
            for filename in fnmatch.filter(filenames, '*.JPG'):
                list_images.append({"path": os.path.join(root, filename), "name": filename})


        print "Number of images in HD: %s" %(str(len(list_images)))


        total_objects_in_xml = len(list(objects))
        curr = 0
        for obj in list(objects):
            curr += 1
            print "Testing: %s / %s" %(str(curr), str(total_objects_in_xml))

            if len(obj.findall('reproduction.identifier_URL')) > 0:
                total_objects_with_images += 1
                
                total_images += len(obj.findall('reproduction.identifier_URL'))

                for rep in obj.findall('reproduction.identifier_URL'):
                    if rep.text != None and rep.text != "":
                        
                        total_images_w_text += 1
                        
                        image_path = rep.text
                        image_path_split = image_path.split("\\")
                        image = image_path_split[-1]
                        image_real_path = self.image_in_list_images(image, list_images)

                        if image not in total_distinct_images:
                            total_distinct_images.append(image)

                        if image_real_path != None:
                            total_images_found += 1
                        else:
                            total_images_not_found += 1
                            if image not in images_not_found:
                                images_not_found.append(image)
            else:
                total_objects_without_images += 1

        total_objects_with_images_plone = 0

        print "##### Migration data #####"
        print "--------"
        print "OBJECTS"
        print "--------\n"
        print "Total objects in XML: %s" %(str(total_objects_in_xml))
        print "Total objects with images: %s" %(str(total_objects_with_images))
        print "Total objects without images: %s" %(str(total_objects_without_images))
        print "Total objects with images in Plone: %s\n" %(str(total_objects_with_images_plone))
        print "--------"
        print "IMAGES"
        print "--------\n"
        print "Total images referenced in XML: %s" %(str(total_images))
        print "Total images with text in XML: %s" %(str(total_images_w_text))
        print "Total distinct images referenced in XML: %s" %(str(len(total_distinct_images)))
        print "Total images in HD: %s" %(str(len(list_images)))
        print "Total images found: %s" %(str(total_images_found))
        print "Total images not found: %s" %(str(total_images_not_found))
        print "--------"
        print "Images not found list:"
        print images_not_found
        print len(images_not_found)


    def check_duplicated_objects(self):
        object_numbers = []
        duplicates = []
        without_object_number = 0

        collection_third_party = "/var/www/zm-collectie-v2/xml/objectsall.xml"
        objects = self.get_zm_collection(collection_third_party)
        print "Got collection XML!"

        curr = 0
        total = len(list(objects))
        for obj in list(objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))

            if obj.find("object_number") != None:
                object_number = obj.find("object_number").text
                if object_number not in object_numbers:
                    object_numbers.append(object_number)
                else:
                    duplicates.append(object_number)
            else:
                without_object_number += 1


        print "Nr. distinct object numbers = %s" %(str(len(object_numbers)))
        print "Nr. of duplicates = %s" %(str(len(duplicates)))
        print "Nr. Records without object_number = %s" %(str(without_object_number))
        print "Duplicates: "
        print duplicates



    def check_zm_migration_plone(self):
        container = self.get_container()
        #catalog = getToolByName(container, 'portal_catalog')
        #all_objects = catalog(portal_type='Object', Language="all")

        """total_objects_with_images_plone = 0
        for item in all_objects:
            obj = item.getObject()
            if hasattr(obj, 'slideshow'):
                slideshow = obj['slideshow']
                images = len(slideshow.objectIds())
                if images > 0:
                    total_objects_with_images_plone += 1

        print "--------"
        print "Total objects with images in Plone: %s\n" %(str(total_objects_with_images_plone))
        print "--------"""""
        
        """total_w_id = 0
        total_without_id = 0
        list_ids = []
        list_ids_duplicated = []

        for item in all_objects:
            obj = item.getObject()
            if hasattr(obj, 'identification_identification_objectNumber'):
                if obj.identification_identification_objectNumber != "":
                    total_w_id += 1
                else:
                    total_without_id += 1

                if obj.identification_identification_objectNumber in list_ids:
                    if obj.identification_identification_objectNumber not in list_ids_duplicated:
                        list_ids_duplicated.append(obj.identification_identification_objectNumber)
                else:
                    list_ids.append(obj.identification_identification_objectNumber)

        print "Total objects with id: %s" %(str(total_w_id))
        print "Total objects without id: %s" %(str(total_without_id))
        print "Total ids duplicated: %s" %(str(len(list_ids_duplicated)))
        print "List ids duplicated:"
        print list_ids_duplicated"""


        path = "nl/collectie/geschiedenis-en-archeologie"
        folder = self.get_folder(path)
        print "Geschiedenis en archeologie = %s" %(str(len(folder)))
        print folder.UID()

        path = "nl/collectie/kunst"
        folder = self.get_folder(path)
        print "Kunst = %s" %(str(len(folder)))
        print folder.UID()

        path = "nl/collectie/kunstnijverheid"
        folder = self.get_folder(path)
        print "Kunstnijverheid = %s" %(str(len(folder)))
        print folder.UID()

        path = "nl/collectie/mode-en-streekdracht"
        folder = self.get_folder(path)
        print "Mode en streekdracht = %s" %(str(len(folder)))
        print folder.UID()

        path = "nl/collectie/natuurhistorie"
        folder = self.get_folder(path)
        print "Natuurhistorie = %s" %(str(len(folder)))
        print folder.UID()

        path = "nl/collectie/16e-eeuwse-zeeuwse-wandtapijten"
        folder = self.get_folder(path)
        print "16e Eeuwse Zeeuwse wandtapijten = %s" %(str(len(folder)))
        print folder.UID()


    def import_zm_collection(self):
        self.folder_path = "nl/collectie/objecten-in-beheer-van-derden".split("/")

        collection_path = "/var/www/zm-collectie-v2/xml/objectsall.xml"
        collection_third_party = "/var/www/zm-collectie-v2/xml/thirdparty.xml"
        objects = self.get_zm_collection(collection_third_party)

        list_images = []
        for root, dirnames, filenames in os.walk('/var/www/zm-data/zm-collection'):
            for filename in fnmatch.filter(filenames, '*.jpg'):
                list_images.append({"path": os.path.join(root, filename), "name": filename})

        for root, dirnames, filenames in os.walk('/var/www/zm-data/zm-collection'):
            for filename in fnmatch.filter(filenames, '*.JPG'):
                list_images.append({"path": os.path.join(root, filename), "name": filename})

        print "Number of images in HD: %s" %(str(len(list_images)))

        image_log = open('/var/www/zm-collectie-v2/migration/image-log_new.csv', 'w')
        img_fieldnames = ['object_number', 'number_of_images_imported', 'total_images']
        img_writer = csv.DictWriter(image_log, fieldnames=img_fieldnames)
        img_writer.writeheader()

        obj_log = open('/var/www/zm-collectie-v2/migration/object-log_new.csv', 'w')
        obj_fieldnames = ['object_number', 'failed']
        obj_writer = csv.DictWriter(obj_log, fieldnames=obj_fieldnames)
        obj_writer.writeheader()


        images_not_found = []
        total_with_images = 0
        total_images = 0

        _total_objs = len(list(objects))
        curr = 0

        total_without_priref = 0
        tried_to_create = 0

        for obj in list(objects):
            curr += 1
            print "%s / %s" %(str(curr), str(_total_objs))

            try:
                if obj.find('object_number') != None:
                    object_number = obj.find('object_number').text
                    if len(obj.findall('reproduction.identifier_URL')) > 0:
                        total_with_images += 1
                        total_images += len(obj.findall('reproduction.identifier_URL'))

                        ### Data for logs
                        imported_image = 0
                        failed = 0
                        
                        priref = obj.find('priref').text
                        object_number = obj.find('object_number').text
                        result = self.get_zm_object(priref, obj, True)

                        for rep in obj.findall('reproduction.identifier_URL'):
                            if rep.text != None:
                                image_path = rep.text
                                if image_path != None:
                                    image_path_split = image_path.split("\\")
                                    image = image_path_split[-1]

                                    image_real_path = self.image_in_list_images(image, list_images)
                                    #image_real_path = None
                                    
                                    if image_real_path != None:
                                        timestamp = datetime.datetime.today().isoformat()
                                        print "[%s] Found image %s in HD" %(timestamp, image)
                                        
                                        priref = obj.find('priref').text
                                        object_number = obj.find('object_number').text

                                        if priref == None:
                                            total_without_priref += 1

                                        if priref != None and object_number != None:
                                            timestamp = datetime.datetime.today().isoformat()
                                            print "[%s] Adding Object %s to Plone." %(timestamp, object_number)
                                            result = self.get_zm_object(priref, obj, True)
                                            failed = 1

                                            if result != None and result != False and result != True:
                                                if result.portal_type == "Object":
                                                    timestamp = datetime.datetime.today().isoformat()
                                                    print "[%s] Object created/exists %s. Try to add image found." %(timestamp, object_number)
                                                    object_item = result
                                                    path = image_real_path
                                                    imported_image += 1
                                                    self.add_image(image, path, object_item)
                                    else:
                                        timestamp = datetime.datetime.today().isoformat()
                                        print "[%s] Image %s not found in HD" %(timestamp, image)
                                        images_not_found.append(image)

                    
                        total_images = len(obj.findall('reproduction.identifier_URL'))

                        ### 
                        ### Add line to image log
                        ### Object number, number of images imported, total images
                        img_writer.writerow({'object_number': object_number, 'number_of_images_imported': imported_image, 'total_images':total_images})

                        ###
                        ### Add line to object log
                        ### Object number, failed[true, false]
                        obj_writer.writerow({'object_number': object_number, 'failed': failed})

                    else:
                        print "Adding object without images! %s" %(str(curr))
                        total_images += len(obj.findall('reproduction.identifier_URL'))

                        ### Data for logs
                        imported_image = 0
                        priref = obj.find('priref').text
                        object_number = obj.find('object_number').text
                        result = self.get_zm_object(priref, obj, True)
                        failed = 1

                        ### 
                        ### Add line to image log
                        ### Object number, number of images imported, total images
                        img_writer.writerow({'object_number': object_number, 'number_of_images_imported': imported_image, 'total_images':total_images})

                        ###
                        ### Add line to object log
                        ### Object number, failed[true, false]
                        obj_writer.writerow({'object_number': object_number, 'failed': failed})

            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        print "Not found images:"
        print images_not_found

        print "Total in API"
        print len(objects)

        print "total with images"
        print total_with_images

        print "total images"
        print total_images
        #print field_usage

        #for key, value in field_usage.iteritems():
        #    print "%s, %s" % (key, str(value))

        print "Total without priref:"
        print total_without_priref

        self.success = True
        return


 
    def import_zm_collection_test(self):
        collection_path = "/Users/AG/Projects/collectie-zm/single-object-v21.xml"
        collection_prod_test = "/var/www/zm-collectie-v1/xml/single-object-v21.xml"

        self.folder_path = "nl/revised-test-folder".split('/')

        objects = self.get_zm_collection(collection_path)

        for obj in list(objects):
            try:
                if len(obj.findall('reproduction.identifier_URL')) >= 0:
                    
                    priref = obj.find('priref').text
                    object_number = obj.find('object_number').text

                    result = self.get_zm_object(priref, obj, True)
            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return


    ####
    #### EXHIBITIONS
    ####



    ###
    ### Creates Exhibition in Plone folder
    ###

    def get_exhibition_from_instance(self, object_number):
        container = self.get_container()

        for obj in container:
            if hasattr(container[obj], 'priref'):
                if container[obj].priref == object_number:
                    print "== Found object! =="
                    return container[obj]
        return None

    def create_zm_exhibition(self, obj):
        
        transaction.begin()
        
        container = self.get_container()

        try:
            dirty_id = obj['dirty_id']
            if dirty_id == "" or dirty_id == " ":
                dirty_id = obj['priref']
        except:
            dirty_id = obj['priref']
            pass


        #print "DIRTY ID: %s" %(dirty_id)

        try:
            dirty_id = "%s %s" %(str(obj['priref']), str(dirty_id))
        except:
            dirty_id = str(obj['priref'])
            pass
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Object already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_exhibition_from_instance(obj['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(obj['text'], 'text/html', 'text/html')

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Exhibition",
                        id=normalized_id,
                        title=obj['exhibitionsDetails_exhibition_title'],
                        text=text,
                        start_date=obj["exhibitionsDetails_exhibition_startDate"],
                        end_date=obj["exhibitionsDetails_exhibition_endDate"],
                        priref=obj["priref"],

                        # Exhibition details
                        #exhibitionsDetails_exhibition_title=obj["exhibitionsDetails_exhibition_title"],
                        exhibitionsDetails_exhibition_startDate="",
                        exhibitionsDetails_exhibition_endDate="",
                        exhibitionsDetails_exhibition_altTitle=obj["exhibitionsDetails_exhibition_altTitle"],
                        exhibitionsDetails_exhibition_notes=obj["exhibitionsDetails_exhibition_notes"],
                        exhibitionsDetails_organizingInstitutions=obj["exhibitionsDetails_organizingInstitutions"],
                        exhibitionsDetails_itinerary=obj["exhibitionsDetails_itinerary"],

                        # Documentation
                        documentation_documentation=obj['documentation_documentation'],

                        # Linked Objects
                        linkedObjects_linkedObjects=obj['linkedObjects_linkedObjects']
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    

                    #### Commmit to the database
                    transaction.commit()

                    #### Log object added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added object %s" % (timestamp, normalized_id)

                    self.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Object already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.errors += 1
            self.success = False
            print "Unexpected error on create_object (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            print "%s - Skipped object: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def get_exhibition_details_fieldset(self, object_data, first_record):
        # exhibitionsDetails_exhibition_title
        if first_record.find('title') != None:
            object_data["exhibitionsDetails_exhibition_title"] = self.trim_white_spaces(first_record.find('title').text)

        # exhibitionsDetails_exhibition_altTitle
        alt_titles = []

        if len(first_record.findall('alternativetitle')) > 0:
            for alt_title in first_record.findall('alternativetitle'):
                if alt_title.find('title.alternative') != None:
                    alt_titles.append({
                        "title": self.trim_white_spaces(alt_title.find('title.alternative').text)
                    })

        object_data["exhibitionsDetails_exhibition_altTitle"] = alt_titles

        # exhibitionsDetails_exhibition_startDate
        if first_record.find('date.start') != None:
            start_date = datetime.datetime.strptime(first_record.find('date.start').text, "%Y-%m-%d")
            object_data["exhibitionsDetails_exhibition_startDate"] = start_date

        # exhibitionsDetails_exhibition_endDate
        if first_record.find('date.end') != None:
            end_date = datetime.datetime.strptime(first_record.find('date.end').text, "%Y-%m-%d")
            object_data["exhibitionsDetails_exhibition_endDate"] = end_date

        # exhibitionsDetails_exhibition_notes
        if first_record.find('notes') != None:
            object_data["exhibitionsDetails_exhibition_notes"] = self.trim_white_spaces(first_record.find('notes').text)

        # exhibitionsDetails_organizingInstitutions
        """class IOrganizingInstitutions(Interface):
            name = schema.TextLine(title=_(u'Name'), required=False)
            address = schema.TextLine(title=_(u'Address'), required=False)
            postalCode = schema.TextLine(title=_(u'Postal code'), required=False)
            place = schema.TextLine(title=_(u'Place'), required=False)
            country = schema.TextLine(title=_(u'Country'), required=False)
            telephone = schema.TextLine(title=_(u'Telephone'), required=False)
            fax = schema.TextLine(title=_(u'Fax'), required=False)"""

        organizing_institutions = []

        if len(first_record.findall('organiser')) > 0:
            for organiser in first_record.findall('organiser'):
                new_organiser = {
                    "name": "",
                    "address": "",
                    "postalCode": "",
                    "place": "",
                    "country": "",
                    "telephone": "",
                    "fax": "",
                    "linkref": ""
                }

                if organiser.find('organiser') != None:
                    linkref = organiser.find('organiser').get('linkref')
                    if linkref != None:
                        new_organiser['linkref'] = linkref

                    if organiser.find('organiser').find('name') != None:
                        new_organiser['name'] = self.trim_white_spaces(organiser.find('organiser').find('name').text)

                if organiser.find('organiser.address') != None:
                    new_organiser['address'] = self.trim_white_spaces(organiser.find('organiser.address').text)

                if organiser.find('organiser.postal_code') != None:
                    new_organiser['postalCode'] = self.trim_white_spaces(organiser.find('organiser.postal_code').text)

                if organiser.find('organiser.place') != None:
                    new_organiser['place'] = self.trim_white_spaces(organiser.find('organiser.place').text)

                if organiser.find('organiser.country') != None:
                    new_organiser['country'] = self.trim_white_spaces(organiser.find('organiser.country').text)

                if organiser.find('organiser.telephone') != None:
                    new_organiser['telephone'] = self.trim_white_spaces(organiser.find('organiser.telephone').text)

                if organiser.find('organiser.fax') != None:
                    new_organiser['fax'] = self.trim_white_spaces(organiser.find('organiser.fax').text)

                organizing_institutions.append(new_organiser)


        object_data["exhibitionsDetails_organizingInstitutions"] = organizing_institutions

        # exhibitionsDetails_itinerary
        """class IItinerary(Interface):
            startDate = schema.TextLine(title=_(u'Start date'), required=False)
            endDate = schema.TextLine(title=_(u'End date'), required=False)
            venue = schema.TextLine(title=_(u'Venue'), required=False)
            place = schema.TextLine(title=_(u'Place'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        itinerary = []

        if len(first_record.findall('venue')) > 0:
            for venue in first_record.findall('venue'):
                new_venue = {
                    "startDate": "",
                    "endDate": "",
                    "venue": "",
                    "place": "",
                    "notes": ""
                }

                if venue.find('venue.date.start') != None:
                    new_venue["startDate"] = self.trim_white_spaces(venue.find('venue.date.start').text)

                if venue.find('venue.date.end') != None:
                    new_venue["endDate"] = self.trim_white_spaces(venue.find('venue.date.end').text)

                if venue.find('venue') != None:
                    if venue.find('venue').find('name') != None:
                        new_venue["venue"] = self.trim_white_spaces(venue.find('venue').find('name').text)

                if venue.find('venue.place') != None:
                    new_venue["place"] = self.trim_white_spaces(venue.find('venue.place').text)

                if venue.find('venue.notes') != None:
                    new_venue["notes"] = self.trim_white_spaces(venue.find('venue.notes').text)

                itinerary.append(new_venue)

        object_data["exhibitionsDetails_itinerary"] = itinerary

    def get_linked_objects_fieldset(self, object_data, first_record):
        # Linked Objects
        # linkedObjects_linkedObjects

        """class ILinkedObjects(Interface):
            objectNumber = schema.TextLine(title=_(u'Object number'), required=False)
            creator = schema.TextLine(title=_(u'Creator'), required=False)
            objectName = schema.TextLine(title=_(u'Object name'), required=False)
            title = schema.TextLine(title=_(u'Title'), required=False)"""

        linked_objects = []

        if len(first_record.findall('object.object_number')):
            for obj in first_record.findall('object.object_number'):
                new_object = {
                    "objectNumber": "",
                    "creator": "",
                    "objectName": "",
                    "title": ""
                }

                if obj.find('object_number') != None:
                    new_object["objectNumber"] = obj.find('object_number').text

                if obj.find('creator') != None:
                    new_object["creator"] = obj.find('creator').text

                if obj.find('object_name') != None:
                    new_object["objectName"] = obj.find('object_name').text

                if obj.find('title') != None:
                    new_object["title"] = obj.find('title').text

                linked_objects.append(new_object)


        object_data["linkedObjects_linkedObjects"] = linked_objects

    def get_linked_objects_fieldset_archive(self, object_data, first_record):
        # Linked Objects
        # linkedObjects_linkedObjects

        """class ILinkedObjects(Interface):
            objectNumber = schema.TextLine(title=_(u'Object number'), required=False)
            creator = schema.TextLine(title=_(u'Creator'), required=False)
            objectName = schema.TextLine(title=_(u'Object name'), required=False)
            title = schema.TextLine(title=_(u'Title'), required=False)"""

        linked_objects = []

        if len(first_record.findall('object')):
            for obj in first_record.findall('object'):
                new_object = {
                    "objectNumber": "",
                    "creator": "",
                    "objectName": "",
                    "title": ""
                }

                if obj.find('object.object_number') != None:
                    if obj.find('object.object_number').find('object_number') != None:
                        new_object["objectNumber"] = obj.find('object.object_number').find('object_number').text

                if obj.find('object.creator') != None:
                    new_object["creator"] = obj.find('object.creator').text

                if obj.find('object.object_name') != None:
                    new_object["objectName"] = obj.find('object.object_name').text

                if obj.find('object.title>') != None:
                    new_object["title"] = obj.find('object.title>').text

                linked_objects.append(new_object)


        object_data["linkedObjects_linkedObjects"] = linked_objects


    def get_zm_exhibition(self, priref, record, create):

        first_record = record

        object_data = {
            # Standard fields
            "text": "",
            "priref": "",

            # Exhibitions details  
            "exhibitionsDetails_exhibition_title": "",
            "exhibitionsDetails_exhibition_altTitle": [],
            "exhibitionsDetails_exhibition_startDate": "",
            "exhibitionsDetails_exhibition_endDate": "",
            "exhibitionsDetails_exhibition_notes": "",
            "exhibitionsDetails_organizingInstitutions": [],
            "exhibitionsDetails_itinerary": [],

            # Documentation 
            "documentation_documentation": [],

            # Linked Objects
            "linkedObjects_linkedObjects": []
        }


            
        try:
            ###
            ### Exhibitions details
            ###
            object_data['priref'] = priref
            self.get_exhibition_details_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Documentation
            ###
            self.get_documentation_fieldset(object_data, first_record)
        except:
            raise

        try:
            ###
            ### Linked Objects
            ###
            self.get_linked_objects_fieldset(object_data, first_record)
        except:
            raise

        ###
        ### Create dirty object ID
        ###    
        object_data['dirty_id'] = self.create_object_dirty_id("", object_data['exhibitionsDetails_exhibition_title'], "")

        if create:
            result = self.create_zm_exhibition(object_data)
            return result
        else:
            return object_data

    def find_exhibition(self, title):
        container = self.get_container()

        for brain in container:
            item = container[brain]
            if hasattr(item, 'title'):
                if item.title == title:
                    return item

        return None

    def update_exhibitions(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/single-exhibition-v01.xml"

        collection_path = "/home/andre/collectie-zm-v1/xml/Tentoonstellingen.xml"
        prod_collection_path = "/var/www/zm-collectie/xml/grouped2.xml"
        exhibitions = "/var/www/zm-collectie/xml/grouped2.xml"
        
        objects = self.get_zm_collection(collection_path)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            curr += 1
            
            print "Updating: %s / %s" %(str(curr), str(total))
            
            try:
                if len(obj.findall('reproduction.identifier_URL')) >= 0:
                    
                    priref = obj.find('priref').text

                    data = self.get_zm_exhibition(priref, obj, False)

                    title = data['exhibitionsDetails_exhibition_title']
                    exhibition = self.find_exhibition(title)

                    if exhibition != None:
                        exhibition.exhibitionsDetails_organizingInstitutions = data['exhibitionsDetails_organizingInstitutions']
                        #exhibition.priref = data['priref']
                        print data['exhibitionsDetails_organizingInstitutions']
                        #exhibition.reindexObject()
                        print "Exhibition updated."
                    else:
                        print "Cannot find Exhibition."

            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return

    def update_ex_dates(self):

        container = self.get_container()

        total = len(list(container))
        curr = 0
        
        for brain in container:
            curr += 1
            item = container[brain]
            changed = False

            if hasattr(item, 'start_date'):
                if item.start_date == "":
                    item.start_date = None
                    changed = True

            if hasattr(item, 'end_date'):
                if item.end_date == "":
                    item.end_date = None
                    changed = True

            if changed:
                item.reindexObject()
                print "Updated %s / %s" %(str(curr), str(total))

        return True

    def import_zm_exhibition_test(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/single-exhibition-v01.xml"

        collection_path = "/home/andre/collectie-zm-v1/xml/Tentoonstellingen.xml"
        prod_collection_path = "/var/www/zm-collectie-v2/xml/Tentoonstellingen.xml"
        exhibitions = "/var/www/zm-collectie/xml/grouped2.xml"
        objects = self.get_zm_collection(prod_collection_path)

        total = len(list(objects))
        curr = 0

        #list_of_missing = ['18', '87', '147', '192', '204', '223', '228', '242', '251', '258', '276', '289', '294', '295', '296', '297', '298', '299', '300', '301', '383']

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                if len(obj.findall('reproduction.identifier_URL')) >= 0:
                    priref = obj.find('priref').text
                    #if priref in list_of_missing:
                    result = self.get_zm_exhibition(priref, obj, True)
                    
                    #result = self.get_zm_exhibition(priref, obj, True)
            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return


    ###
    ### Treatment
    ###

    def get_treatment_from_instance(self, object_number):
        container = self.get_container()

        for obj in container:
            if hasattr(container[obj], 'treatmentDetails_identification_treatmentNumber'):
                if container[obj].treatmentDetails_identification_treatmentNumber == object_number:
                    print "== Found object! =="
                    return container[obj]
        return None

    def create_zm_treatment(self, obj):
        
        transaction.begin()

        self.folder_path = "nl/conserverings-behandelingen/conserverings-behandelingen".split('/')
        
        container = self.get_container()
        dirty_id = obj['dirty_id']
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

        result = False

        created_object = None

        treatment_title = obj['treatmentDetails_identification_treatmentNumber']
        if treatment_title == "":
            treatment_title = str(obj['priref'])

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Treatment already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_treatment_from_instance(obj['treatmentDetails_identification_treatmentNumber'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(obj['text'], 'text/html', 'text/html')

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="treatment",
                        id=normalized_id,
                        title=treatment_title,
                        text=text,
                        priref=obj['priref'],

                        # Treatment details
                        treatmentDetails_identification_treatmentNumber=obj["treatmentDetails_identification_treatmentNumber"],
                        treatmentDetails_identification_treatmentType=obj["treatmentDetails_identification_treatmentType"],
                        treatmentDetails_identification_reversible=obj["treatmentDetails_identification_reversible"],
                        treatmentDetails_identification_treatmentMethod=obj["treatmentDetails_identification_treatmentMethod"],
                        treatmentDetails_identification_conservator=obj["treatmentDetails_identification_conservator"],
                        treatmentDetails_identification_material=obj["treatmentDetails_identification_material"],
                        treatmentDetails_progress_startDate=obj["treatmentDetails_progress_startDate"],
                        treatmentDetails_progress_status=obj["treatmentDetails_progress_status"],
                        treatmentDetails_progress_recallDate=obj["treatmentDetails_progress_recallDate"],
                        treatmentDetails_progress_endDate=obj["treatmentDetails_progress_endDate"],
                        treatmentDetails_treatment_conditionDescription=obj["treatmentDetails_treatment_conditionDescription"],
                        treatmentDetails_treatment_treatmentPlan=obj["treatmentDetails_treatment_treatmentPlan"],
                        treatmentDetails_treatment_treatmentSummary=obj["treatmentDetails_treatment_treatmentSummary"],
                        treatmentDetails_digitalReferences=obj["treatmentDetails_digitalReferences"],
                        treatmentDetails_notes=obj["treatmentDetails_notes"],

                        # Reproductions
                        reproductions_reproduction=obj["reproductions_reproduction"],

                        # Linked Objects
                        linkedObjects_linkedObjects=obj['linkedObjects_linkedObjects']
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    

                    #### Commmit to the database
                    transaction.commit()

                    #### Log object added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Treatment %s" % (timestamp, normalized_id)

                    self.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Treatment already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.errors += 1
            self.success = False
            print "Unexpected error on Treatment (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            print "%s - Skipped Treatment: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def get_treatment_details_fieldset(self, object_data, first_record):

        # treatmentDetails_identification_treatmentNumber
        if first_record.find('treatment_number') != None:
            object_data['treatmentDetails_identification_treatmentNumber'] = first_record.find('treatment_number').text

        # treatmentDetails_identification_treatmentType
        if first_record.find('treatment_type') != None:
            if first_record.find('treatment_type').find('text') != None:
                object_data['treatmentDetails_identification_treatmentType'] = first_record.find('treatment_type').find('text').text

        # treatmentDetails_identification_reversible
        if first_record.find('reversible') != None:
            if first_record.find('reversible').text == "x":
                object_data['treatmentDetails_identification_reversible'] = True
            else:
                object_data['treatmentDetails_identification_reversible'] = False

        # treatmentDetails_identification_treatmentMethod
        """class ITreatmentMethod(Interface):
            term = schema.TextLine(title=_(u'Treatment method'), required=False)"""

        treatment_methods = []

        if len(first_record.findall('Treatmentmethod')) > 0:
            for method in first_record.findall('Treatmentmethod'):
                new_method = {
                    "term":""
                }

                if method.find('treatment_method') != None:
                    if method.find('treatment_method').find('term') != None:
                        new_method["term"] = method.find('treatment_method').find('term').text

                treatment_methods.append(new_method)

        object_data['treatmentDetails_identification_treatmentMethod'] = treatment_methods

        # treatmentDetails_identification_conservator
        """class IConversator(Interface):
            name = schema.TextLine(title=_(u'Conversator'), required=False)"""

        conservators = []

        if len(first_record.findall('Conservator')) > 0:
            for conservator in first_record.findall('Conservator'):
                new_conservator = {
                    "name":""
                }

                if conservator.find('conservator') != None:
                    if conservator.find('conservator').find('name') != None:
                        new_conservator["name"] = conservator.find('conservator').find('name').text

                conservators.append(new_conservator)

        object_data['treatmentDetails_identification_conservator'] = conservators

        # treatmentDetails_identification_material
        """class IMaterial(Interface):
            term = schema.TextLine(title=_(u'Material'), required=False)"""

        materials = []

        if len(first_record.findall('Material')) > 0:
            for material in first_record.findall('Material'):
                new_material = {
                    "term":""
                }

                if material.find('material') != None:
                    if material.find('material').find('term') != None:
                        new_material["term"] = material.find('material').find('term').text

                materials.append(new_material)

        object_data['treatmentDetails_identification_material'] = materials

        # treatmentDetails_progress_startDate
        if first_record.find('date.start') != None:
            if first_record.find('date.start').text != "" and first_record.find('date.start').text != None:
                #start_date = datetime.datetime.strptime(first_record.find('date.start').text, "%Y-%m-%d")
                object_data["treatmentDetails_progress_startDate"] = first_record.find('date.start').text

        # treatmentDetails_progress_status
        if first_record.find('status') != None:
            object_data["treatmentDetails_progress_status"] = first_record.find('status').text

        # treatmentDetails_progress_recallDate
        if first_record.find('recall_date') != None:
            if first_record.find('recall_date').text != "" and first_record.find('recall_date').text != None:
                #recall_date = datetime.datetime.strptime(first_record.find('recall_date').text, "%Y-%m-%d")
                object_data["treatmentDetails_progress_recallDate"] = first_record.find('recall_date').text

        # treatmentDetails_progress_endDate
        if first_record.find('date.end') != None:
            if first_record.find('date.end').text != "" and first_record.find('date.end').text != None:
                #end_date = datetime.datetime.strptime(first_record.find('date.end').text, "%Y-%m-%d")
                object_data["treatmentDetails_progress_endDate"] = first_record.find('date.end').text

    
        # treatmentDetails_treatment_conditionDescription
        """class IConditionDescription(Interface):
            description = schema.TextLine(title=_(u'Condition description'), required=False)"""

        condition_descriptions = []
        if len(first_record.findall('condition_description')) > 0:
            for condition in first_record.findall('condition_description'):
                condition_descriptions.append({
                    "description": condition.text
                })

        object_data["treatmentDetails_treatment_conditionDescription"] = condition_descriptions

        # treatmentDetails_treatment_treatmentPlan
        """class ITreatmentPlan(Interface):
            plan = schema.TextLine(title=_(u'Treatment plan'), required=False)"""

        treatment_plans = []

        if len(first_record.findall('treatment_plan')) > 0:
            for treatment in first_record.findall('treatment_plan'):
                treatment_plans.append({
                    "plan": treatment.text
                })

        object_data["treatmentDetails_treatment_treatmentPlan"] = treatment_plans

        # treatmentDetails_treatment_treatmentSummary
        """class ITreatmentSummary(Interface):
            summary = schema.TextLine(title=_(u'Treatment summary'), required=False)"""

        treatment_summarys = []

        if len(first_record.findall('treatment_summary')) > 0:
            for treatment in first_record.findall('treatment_summary'):
                treatment_summarys.append({
                    "summary": treatment.text
                })

        object_data['treatmentDetails_treatment_treatmentSummary'] = treatment_summarys

        # treatmentDetails_digitalReferences
        """class IDigitalReferences(Interface):
            type = schema.TextLine(title=_(u'Type'), required=False)
            reference = schema.TextLine(title=_(u'Reference'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        digital_references = []

        if len(first_record.findall('Digreference')) > 0:
            for digital_reference in first_record.findall('Digreference'):
                new_ref = {
                  "type": "",
                  "reference": "",
                  "notes": ""  
                }

                if digital_reference.find('digital_reference.type') != None:
                    new_ref['type'] = self.trim_white_spaces(digital_reference.find('digital_reference.type').text)

                if digital_reference.find('digital_reference') != None:
                    new_ref['reference'] = self.trim_white_spaces(digital_reference.find('digital_reference').text)

                if digital_reference.find('digital_reference.notes') != None:
                    new_ref['notes'] = self.trim_white_spaces(digital_reference.find('digital_reference.notes').text)

                digital_references.append(new_ref)

        object_data['treatmentDetails_digitalReferences'] = digital_references

        # treatmentDetails_notes
        notes = []

        if len(first_record.findall('notes')) > 0:
            for note in first_record.findall('notes'):
                notes.append({
                    "notes": note.text
                })

        object_data["treatmentDetails_notes"] = notes

    def get_zm_treatment(self, priref, record, create):

        first_record = record

        object_data = {
            # Standard fields
            "text": "",

            # Treatment details  
            "treatmentDetails_identification_treatmentNumber": "",
            "treatmentDetails_identification_treatmentType": "",
            "treatmentDetails_identification_reversible": "",
            "treatmentDetails_identification_treatmentMethod": [],
            "treatmentDetails_identification_conservator": [],
            "treatmentDetails_identification_material": [],
            "treatmentDetails_progress_startDate": "",
            "treatmentDetails_progress_status": "",
            "treatmentDetails_progress_recallDate": "",
            "treatmentDetails_progress_endDate": "",
            "treatmentDetails_treatment_conditionDescription": [],
            "treatmentDetails_treatment_treatmentPlan": [],
            "treatmentDetails_treatment_treatmentSummary": [],
            "treatmentDetails_digitalReferences": [],
            "treatmentDetails_notes": [],

            # Reproduction
            "reproductions_reproduction": [],

            # Linked Objects
            "linkedObjects_linkedObjects": []
        }

        object_data['priref'] = priref
            
        try:
            ###
            ### Treatment details
            ###
            self.get_treatment_details_fieldset(object_data, first_record)
        except:
            raise

        try:
            ###
            ### Reproduction
            ###
            self.get_reproductions_fieldset(object_data, first_record)
        except:
            pass

        try:
            ###
            ### Linked Objects
            ###
            self.get_linked_objects_fieldset(object_data, first_record)
        except:
            pass

        ###
        ### Create dirty object ID
        ###    
        object_data['dirty_id'] = self.create_object_dirty_id("", object_data['treatmentDetails_identification_treatmentNumber'], "")
        if priref != "":
            object_data['dirty_id'] = "%s %s" %(str(priref), str(object_data['dirty_id']))

        if create:
            result = self.create_zm_treatment(object_data)
            return result
        else:
            return object_data

    def import_zm_treatment_test(self):
        collection_path = "/Users/AG/Projects/collectie-zm/Treatment-details-v01.xml"
        objects = self.get_zm_collection(collection_path)

        for obj in list(objects):
            try:
                if len(obj.findall('reproduction.identifier_URL')) >= 0:
                    priref = obj.find('priref').text
                    result = self.get_zm_treatment(priref, obj, True)
            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return

    def import_zm_treatments(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/Treatment-details-v01.xml"
        collection_path = "/home/andre/collectie-zm-v1/xml/Treatments.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Treatments.xml"
        objects = self.get_zm_collection(collection_path_prod)


        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            curr += 1
            
            print "Importing: %s / %s" %(str(curr), str(total))
            
            try:
                if len(obj.findall('reproduction.identifier_URL')) >= 0:
                    priref = obj.find('priref').text
                    result = self.get_zm_treatment(priref, obj, True)
            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return

    def update_treatment(self, data, obj):
        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(obj, key):
                    setattr(obj, key, value)

        print "Treatment updated!"

        return True

    def update_treatments(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/Treatment-details-v01.xml"
        collection_path = "/home/andre/collectie-zm-v1/xml/Treatments.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Treatments.xml"
        objects, root = self.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            curr += 1
            
            print "Updating: %s / %s" %(str(curr), str(total))
            
            try:
                priref = obj.find('priref').text
                data = self.get_zm_treatment(priref, obj, False)

                treatment_number = data['treatmentDetails_identification_treatmentNumber']
                if treatment_number:
                    continue
                    treatment = self.find_treatment_by_treatmentnumber(treatment_number)
                    if treatment:
                        self.update_treatment(data, treatment)
                    else:
                        print "Treatment does not exist: Create new Treatment object"
                        result = self.get_zm_treatment(priref, obj, True)
                else:
                    print "Treatment %s does not have a treatment number. CREATING" %(str(priref))
                    result = self.get_zm_treatment(priref, obj, True)
            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return


    ###
    ### Person or Institution
    ###


    def get_name_information_fieldset(self, object_data, first_record):

        # nameInformation_name_name
        if first_record.find('name') !=  None:
            object_data["nameInformation_name_name"] = self.trim_white_spaces(first_record.find('name').text)

        # nameInformation_name_institutionNumber
        if first_record.find('institution_code') != None:
            object_data["nameInformation_name_institutionNumber"] = self.trim_white_spaces(first_record.find('name').text)

        # nameInformation_name_nameType
        name_types = []

        if len(first_record.findall('name.type')) > 0:
            for name in first_record.findall('name.type'):
                if name.find('text') != None:
                    name_types.append({
                        "type": self.trim_white_spaces(name.find('text').text)
                    })

        object_data["nameInformation_name_nameType"] = name_types

        # nameInformation_name_nameNotes
        if first_record.find('name.note') != None:
            object_data["nameInformation_name_nameNotes"] = self.trim_white_spaces(first_record.find('name.note').text)


        # nameInformation_relationWithOtherNames_use
        uses = []

        ##TODO

        object_data["nameInformation_relationWithOtherNames_use"] = uses


        # nameInformation_relationWithOtherNames_usedFor
        ##TODO

        # nameInformation_relationWithOtherNames_equivalent
        equivalents = []

        if len(first_record.findall('equivalent_name')) > 0:
            for equivalent in first_record.findall('equivalent_name'):
                equivalents.append({
                    "name":self.trim_white_spaces(equivalent.text)
                })

        object_data["nameInformation_relationWithOtherNames_equivalent"] = equivalents

        # nameInformation_addressDetails
        """class IAddressDetails(Interface):
            addressType = schema.TextLine(title=_(u'Address type'), required=False)
            address = schema.TextLine(title=_(u'Address'), required=False)
            postalCode = schema.TextLine(title=_(u'Postal code'), required=False)
            place = schema.TextLine(title=_(u'Place'), required=False)
            country = schema.TextLine(title=_(u'Country'), required=False)"""
        addressDetails = []

        if len(first_record.findall('address')) > 0:
            for address in first_record.findall('address'):
                addressDetails.append({
                    "addressType": "",
                    "address": self.trim_white_spaces(address.text),
                    "postalCode": "",
                    "place": "",
                    "country": ""
                })

        if len(addressDetails) > 0:

            # addressType
            if len(first_record.findall('address.type')) > 0:
                for slot, address_type in enumerate(first_record.findall('address.type')):
                    addressDetails[slot]["addressType"] = self.trim_white_spaces(address_type.text)

            # postalCode
            if len(first_record.findall('address.postal_code')) > 0:
                for slot, address_postal in enumerate(first_record.findall('address.postal_code')):
                    addressDetails[slot]["postalCode"] = self.trim_white_spaces(address_postal.text)

            # place
            if len(first_record.findall('address.place')) > 0:
                for slot, address_place in enumerate(first_record.findall('address.place')):
                    if address_place.find('term') != None:
                        addressDetails[slot]["place"] = self.trim_white_spaces(address_place.find('term').text)

            # country
            if len(first_record.findall('address.country')) > 0:
                for slot, address_country in enumerate(first_record.findall('address.country')):
                    if address_country.find('term') != None:
                        addressDetails[slot]["country"] = self.trim_white_spaces(address_country.find('term').text)



        object_data["nameInformation_addressDetails"] = addressDetails

        # nameInformation_telephoneFaxEmail_telephone
        phones = []
        if len(first_record.find('phone')) > 0:
            for phone in first_record.find('phone'):
                phones.append({
                    "phone": self.trim_white_spaces(phone.text),
                })

        object_data["nameInformation_telephoneFaxEmail_telephone"] = phones

        # nameInformation_telephoneFaxEmail_fax
        faxs = []
        if len(first_record.find('fax')) > 0:
            for fax in first_record.find('fax'):
                faxs.append({
                    "fax": self.trim_white_spaces(fax.text),
                })

        object_data["nameInformation_telephoneFaxEmail_fax"] = faxs

        # nameInformation_telephoneFaxEmail_email
        emails = []
        if len(first_record.find('email')) > 0:
            for fax in first_record.find('email'):
                emails.append({
                    "email": self.trim_white_spaces(email.text),
                })

        object_data["nameInformation_telephoneFaxEmail_fax"] = emails


        # nameInformation_telephoneFaxEmail_website
        websites = []
        if len(first_record.find('url')) > 0:
            for url in first_record.find('url'):
                websites.append({
                    "url": self.trim_white_spaces(url.text),
                })

        object_data["nameInformation_telephoneFaxEmail_website"] = websites

        # nameInformation_contacts
        """class IContacts(Interface):
            name = schema.TextLine(title=_(u'Name'), required=False)
            jobTitle = schema.TextLine(title=_(u'Job title'), required=False)
            phone = schema.TextLine(title=_(u'Phone'), required=False)"""

        contacts = []

        if len(first_record.findall('contact.name')) > 0:
            for contact in first_record.findall('contact.name'):
                if contact.find('name') != None:
                    contacts.append({
                        "name": self.trim_white_spaces(contact.find('name').text),
                        "jobTitle": "",
                        "phone": ""
                    })

        object_data["nameInformation_contacts"] = contacts

        # nameInformation_miscellaneous_group
        groups = []
        if len(first_record.findall('group')) > 0:
            for group in first_record.findall('group'):
                if group.find('term') != None:
                    groups.append({
                        "term": self.trim_white_spaces(group.find('term').text)
                    })

        object_data["nameInformation_miscellaneous_group"] = groups

        # nameInformation_miscellaneous_notes
        notes = []

        if len(first_record.findall("notes")) > 0:
            for note in first_record.findall("notes"):
                notes.append({
                    "note": self.trim_white_spaces(note.text)
                })


        object_data["nameInformation_miscellaneous_notes"] = notes

    def get_person_details_fieldset(self, object_data, first_record):

        if first_record.find('priref') != None:
            object_data['priref'] = self.trim_white_spaces(first_record.find('priref').text)

        # personDetails_birthDetails_dateStart
        if first_record.find('birth.date.start') != None:
            object_data['personDetails_birthDetails_dateStart'] = self.trim_white_spaces(first_record.find('birth.date.start').text)

        # personDetails_birthDetails_dateEnd
        if first_record.find('birth.date.end') != None:
            object_data['personDetails_birthDetails_dateEnd'] = self.trim_white_spaces(first_record.find('birth.date.end').text)

        # personDetails_birthDetails_precision
        if first_record.find('birth.date.precision') != None:
            object_data['personDetails_birthDetails_precision'] = self.trim_white_spaces(first_record.find('birth.date.precision').text)

        # personDetails_birthDetails_place
        if first_record.find('birth.place') != None:
            if first_record.find('birth.place').find('term') != None:
                object_data['personDetails_birthDetails_place'] = self.trim_white_spaces(first_record.find('birth.place').find('term').text)

        # personDetails_birthDetails_notes
        if first_record.find('birth.notes') != None:
            object_data['personDetails_birthDetails_notes'] = [{"note":self.trim_white_spaces(first_record.find('birth.notes').text)}]

        # personDetails_deathDetails_dateStart
        if first_record.find('death.date.start') != None:
            object_data['personDetails_deathDetails_dateStart'] = self.trim_white_spaces(first_record.find('death.date.start').text)

        # personDetails_deathDetails_dateEnd
        if first_record.find('death.date.end') != None:
            object_data['personDetails_deathDetails_dateEnd'] = self.trim_white_spaces(first_record.find('death.date.end').text)

        # personDetails_deathDetails_precision
        if first_record.find('death.date.precision') != None:
            object_data['personDetails_deathDetails_precision'] = self.trim_white_spaces(first_record.find('death.date.precision').text)

        # personDetails_deathDetails_place
        if first_record.find('death.place') != None:
            if first_record.find('death.place').find('term') != None:
                object_data['personDetails_deathDetails_place'] = self.trim_white_spaces(first_record.find('death.place').find('term').text)

        # personDetails_deathDetails_notes
        if first_record.find('death.notes') != None:
            object_data['personDetails_deathDetails_notes'] = [{"note":self.trim_white_spaces(first_record.find('death.notes').text)}]

        # personDetails_nationality_nationality
        nationalities = []

        if len(first_record.findall('nationality')) > 0:
            for nationality in first_record.findall('nationality'):
                nationalities.append({
                    "nationality": self.trim_white_spaces(nationality.text)
                })

        object_data["personDetails_nationality_nationality"] = nationalities

        # personDetails_nationality_language
        languages = []

        if len(first_record.findall('language')) > 0:
            for language in first_record.findall('language'):
                if language.find('term') != None:
                    languages.append({
                        "term": self.trim_white_spaces(language.find('term').text)
                    })

        object_data["personDetails_nationality_language"] = languages

        # personDetails_ocupation_ocupation
        occupations = []

        if len(first_record.findall('occupation')) > 0:
            for occupation in first_record.findall('occupation'):
                if occupation.find('term') != None:
                    occupations.append({
                        "term": self.trim_white_spaces(occupation.find('term').text)
                    })

        object_data["personDetails_ocupation_ocupation"] = occupations

        # personDetails_ocupation_schoolStyle
        schools = []

        if len(first_record.findall('school_style')) > 0:
            for school_style in first_record.findall('school_style'):
                if school_style.find('term') != None:
                    schools.append({
                        "term": self.trim_white_spaces(school_style.find('term').text)
                    })

        object_data["personDetails_ocupation_schoolStyle"] = schools

        # personDetails_placeOfActivity
        """ class IPlaceOfActivity(Interface):
            place = schema.TextLine(title=_(u'Place'), required=False)
            dateStart = schema.TextLine(title=_(u'Date (start)'), required=False)
            dateEnd = schema.TextLine(title=_(u'Date (end)'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        places = []

        if len(first_record.findall('place_activity')) > 0:
            for place in first_record.findall('place_activity'):
                if place.find('term') != None:
                    places.append({
                        "place": self.trim_white_spaces(place.find('term').text),
                        "dateStart": "",
                        "dateEnd": "",
                        "notes":""
                    })

        if len(places) > 0:
            # dateStart
            if len(first_record.findall('place_activity.date.start')) > 0:
                for slot, date_start in enumerate(first_record.findall('place_activity.date.start')):
                    places[slot]["dateStart"] = self.trim_white_spaces(date_start.text)

            # dateEnd
            if len(first_record.findall('place_activity.date.end')) > 0:
                for slot, date_end in enumerate(first_record.findall('place_activity.date.end')):
                    places[slot]["dateEnd"] = self.trim_white_spaces(date_end.text)

            # notes
            if len(first_record.findall('place_activity.notes')) > 0:
                for slot, place_notes in enumerate(first_record.findall('place_activity.notes')):
                    places[slot]["notes"] = self.trim_white_spaces(place_notes.text)


        object_data["personDetails_placeOfActivity"] = places
        
        # personDetails_biography
        if first_record.find('biography') != None:
            object_data['personDetails_biography'] = self.trim_white_spaces(first_record.find('biography').text)


    #
    # Outgoing loans
    #

    def create_zm_outgoing_loan(self, obj):
        
        transaction.begin()
        
        container = self.get_container()
        dirty_id = obj['dirty_id']
        if dirty_id == "":
            dirty_id = "%s" %(str(obj['priref']))

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                #print "%s - Object already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_outgoingloan_from_instance(obj['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(obj['text'], 'text/html', 'text/html')

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="OutgoingLoan",
                        id=normalized_id,
                        title=obj['loanRequest_general_loanNumber'],
                        text=text,
                        priref=obj["priref"],

                        # Loan request
                        loanRequest_general_loanNumber=obj["loanRequest_general_loanNumber"],
                        loanRequest_general_requester=obj["loanRequest_general_requester"],
                        loanRequest_general_contact=obj["loanRequest_general_contact"],
                        loanRequest_internalCoordination_coordinator=obj["loanRequest_internalCoordination_coordinator"],
                        loanRequest_internalCoordination_administrConcerned=obj["loanRequest_internalCoordination_administrConcerned"],
                        loanRequest_requestDetails_periodFrom=obj["loanRequest_requestDetails_periodFrom"],
                        loanRequest_requestDetails_to=obj["loanRequest_requestDetails_to"],
                        loanRequest_requestDetails_reason=obj["loanRequest_requestDetails_reason"],
                        loanRequest_requestDetails_exhibition=obj["loanRequest_requestDetails_exhibition"],
                        loanRequest_requestLetter_date=obj["loanRequest_requestLetter_date"],
                        loanRequest_requestLetter_digRef=obj["loanRequest_requestLetter_digRef"],
                        loanRequest_requestConfirmation_template=obj["loanRequest_requestConfirmation_template"],
                        loanRequest_requestConfirmation_date=obj["loanRequest_requestConfirmation_date"],
                        loanRequest_requestConfirmation_digRef=obj["loanRequest_requestConfirmation_digRef"],

                        # Objects
                        objects_object=obj['objects_object'],

                        # Contract
                        contract_contractDetails_requestPeriodFrom=obj["contract_contractDetails_requestPeriodFrom"],
                        contract_contractDetails_to=obj["contract_contractDetails_to"],
                        contract_contractDetails_conditions=obj["contract_contractDetails_conditions"],
                        contract_contractDetails_notes=obj["contract_contractDetails_notes"],
                        contract_contractLetter_template=obj["contract_contractLetter_template"],
                        contract_contractLetter_date=obj["contract_contractLetter_date"],
                        contract_contractLetter_digRef=obj["contract_contractLetter_digRef"],
                        contract_contractLetter_signedReturned=obj["contract_contractLetter_signedReturned"],
                        contract_contractLetter_signedReturnedDigRef=obj["contract_contractLetter_signedReturnedDigRef"],
                        contract_conditionReport_template=obj["contract_conditionReport_template"],
                        contract_conditionReport_date=obj["contract_conditionReport_date"],
                        contract_conditionReport_digRef=obj["contract_conditionReport_digRef"],
                        contract_extension=obj["contract_extension"],

                        # Correspondence
                        correspondence_otherCorrespondence=obj["correspondence_otherCorrespondence"],

                        # Transport
                        transport_despatchDetails=obj["correspondence_otherCorrespondence"],
                        transport_entryDetails=obj['transport_entryDetails']
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    

                    #### Commmit to the database
                    transaction.commit()

                    #### Log object added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added object %s" % (timestamp, normalized_id)

                    self.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Object already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.errors += 1
            self.success = False
            print "Unexpected error on create_object (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            print "%s - Skipped object: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object


    def get_zm_outgoingloan(self, priref, record, create):

        first_record = record

        object_data = {
            # Standard fields
            "text": "",
            "priref": "",

            # Loan request
            'loanRequest_general_loanNumber':"",
            'loanRequest_general_requester':"",
            'loanRequest_general_contact':"",
            'loanRequest_internalCoordination_coordinator':"",
            'loanRequest_internalCoordination_administrConcerned':[],
            'loanRequest_requestDetails_periodFrom':"",
            'loanRequest_requestDetails_to':"",
            'loanRequest_requestDetails_reason':"",
            'loanRequest_requestDetails_exhibition':"",
            'loanRequest_requestLetter_date':"",
            'loanRequest_requestLetter_digRef':"",
            'loanRequest_requestConfirmation_template':"",
            'loanRequest_requestConfirmation_date':"",
            'loanRequest_requestConfirmation_digRef':"",

            # Objects
            'objects_object': [],

            # Contract 
            'contract_contractDetails_requestPeriodFrom': "",
            'contract_contractDetails_to': "",
            'contract_contractDetails_conditions': "",
            'contract_contractDetails_notes': [],
            'contract_contractLetter_template': "",
            'contract_contractLetter_date': "",
            'contract_contractLetter_digRef': "",
            'contract_contractLetter_signedReturned': "",
            'contract_contractLetter_signedReturnedDigRef': "",
            'contract_conditionReport_template': "",
            'contract_conditionReport_date': "",
            'contract_conditionReport_digRef': "",
            'contract_extension': [],

            # Correspondence
            'correspondence_otherCorrespondence': [],

            # Transport
            'transport_despatchDetails': [],
            'transport_entryDetails': []
        }

        object_data['priref'] = priref
            
        try:
            ###
            ### Loan request
            ###
            self.get_loan_request_fieldset(object_data, first_record)
        except:
            raise

        try:
            ###
            ### Objects
            ###
            self.get_outgoingloan_objects_fieldset(object_data, first_record)
        except:
            raise

        try:
            ###
            ### Contract
            ###
            self.get_contract_fieldset(object_data, first_record)
        except:
            raise

        try:
            ###
            ### Correspondence
            ###
            self.get_correspondence_fieldset(object_data, first_record)
        except:
            raise

        ###
        ### Create dirty object ID
        ###    
        object_data['dirty_id'] = self.create_object_dirty_id("", object_data['loanRequest_general_loanNumber'], "")

        if create:
            result = self.create_zm_outgoing_loan(object_data)
            return result
        else:
            return object_data

    def get_correspondence_fieldset(self, object_data, first_record):

        # correspondence_otherCorrespondence
        """class ICorrespondence(Interface):
            digitalReference = schema.TextLine(title=_(u'(Digital) Reference'), required=False)
            date = schema.TextLine(title=_(u'label_date'), required=False)
            sender = schema.TextLine(title=_(u'Sender'), required=False)
            destination = schema.TextLine(title=_(u'Destination'), required=False)
            subject = schema.TextLine(title=_(u'Subject'), required=False)"""

        correspondences = []

        object_data['correspondence_otherCorrespondence'] = correspondences


    def get_outgoingloan_transport_fieldset(self, object_data, first_record):

        # transport_despatchDetails
        """class IDespatchDetails(Interface):
            despatchNumber = schema.TextLine(title=_(u'Despatch number'), required=False)"""

        # transport_entryDetails
        """class IEntryDetails(Interface):
            entryNumber = schema.TextLine(title=_(u'Entry number'), required=False)"""


        pass


    def import_zm_outgoingloan_test(self):
        collection_path = "/Users/AG/Projects/collectie-zm/xml/Outgoingloans.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Outgoingloans.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/outgoingloans.xml"
        objects = self.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))
            try:
                if len(obj.findall('reproduction.identifier_URL')) >= 0:
                    priref = obj.find('priref').text
                    result = self.get_zm_outgoingloan(priref, obj, True)
            except:
                print "Outgoing loan failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                raise

        self.success = True
        return

    def get_loan_request_fieldset(self, object_data, first_record):
        
        # loanRequest_general_loanNumber
        if first_record.find('loan_number') != None:
            object_data["loanRequest_general_loanNumber"] = first_record.find('loan_number').text

        # loanRequest_general_requester
        if first_record.find('requester') != None:
            if first_record.find('requester').find('name') != None:
                object_data["loanRequest_general_requester"] = first_record.find('requester').find('name').text

        # loanRequest_general_contact
        if first_record.find('requester.contact') != None:
            if first_record.find('requester.contact').find('name') != None:
                object_data["loanRequest_general_contact"] = first_record.find('requester.contact').find('name').text

        # loanRequest_internalCoordination_coordinator
        if first_record.find('co-ordinator') != None:
            if first_record.find('co-ordinator').find('name') !=  None:
                object_data["loanRequest_internalCoordination_coordinator"] = first_record.find('co-ordinator').find('name').text

        # loanRequest_internalCoordination_administrConcerned
        admins = []
        if len(first_record.findall('administration_concerned')) > 0:
            for admin in first_record.findall('administration_concerned'):
                admins.append({
                    "name": admin.text
                })
        
        object_data["loanRequest_internalCoordination_administrConcerned"] = admins

        # loanRequest_requestDetails_periodFrom
        if first_record.find('request.period.start') != None:
            object_data["loanRequest_requestDetails_periodFrom"] = first_record.find('request.period.start').text

        # loanRequest_requestDetails_to
        if first_record.find('request.period.end') != None:
            object_data["loanRequest_requestDetails_to"] = first_record.find('request.period.end').text

        # loanRequest_requestDetails_reason
        if first_record.find('request.reason') != None:
            if first_record.find('request.reason').find('text') != None:
                object_data["loanRequest_requestDetails_reason"] = first_record.find('request.reason').find('text').text

        # loanRequest_requestDetails_exhibition
        if first_record.find('exhibition') != None:
            if first_record.find('exhibition').find('title') != None:
                object_data["loanRequest_requestDetails_exhibition"] = first_record.find('exhibition').find('title').text

        # loanRequest_requestLetter_date
        if first_record.find('request.date') != None:
            object_data["loanRequest_requestLetter_date"] = first_record.find('request.date').text

        # loanRequest_requestLetter_digRef
        if first_record.find('request-in.reference') != None:
            object_data["loanRequest_requestLetter_digRef"] = first_record.find('request-in.reference').text

        # loanRequest_requestConfirmation_template
        if first_record.find('request-in.confirmation.template') != None:
            if first_record.find('request-in.confirmation.template').find('text') != None:
                object_data["loanRequest_requestConfirmation_template"] = first_record.find('request-in.confirmation.template').find('text').text

        # loanRequest_requestConfirmation_date
        if first_record.find('request-in.confirmation.date') != None:
            object_data["loanRequest_requestConfirmation_date"] = first_record.find('request-in.confirmation.date').text

        # loanRequest_requestConfirmation_digRef
        if first_record.find('request-in.confirmation.referenc') != None:
            object_data["loanRequest_requestConfirmation_digRef"] = first_record.find('request-in.confirmation.referenc').text

    def get_outgoingloan_objects_fieldset(self, object_data, first_record):

        # objects_object
        """class IObjects(Interface):
            objectNumber = schema.TextLine(title=_(u'Object number'), required=False)
            loanTitle = schema.TextLine(title=_(u'Loan title'), required=False)
            status = schema.Choice(
                vocabulary=status_vocabulary,
                title=_(u'Status'),
                required=False
            )

            date = schema.TextLine(title=_(u'Date'), required=False)
            authoriserInternal = schema.TextLine(title=_(u'Authoriser (internal)'), required=False)
            authorisationDate = schema.TextLine(title=_(u'Authorisation date'), required=False)

            # Review request
            reviewRequest_template = schema.Choice(
                vocabulary=template_vocabulary,
                title=_(u'Template'),
                required=False
            )

            reviewRequest_date = schema.TextLine(title=_(u'Date'), required=False)
            reviewRequest_digRef = schema.TextLine(title=_(u'Dig. ref.'), required=False)

            # Permission owner 
            permissionOwner_requestTemplate = schema.Choice(
                vocabulary=template_vocabulary,
                title=_(u'Request template'),
                required=False
            )

            permissionOwner_date = schema.TextLine(title=_(u'Date'), required=False)
            permissionOwner_digRef = schema.TextLine(title=_(u'Dig. ref.'), required=False)
            permissionOwner_permissionResult = schema.Choice(
                vocabulary=permission_result_vocabulary,
                title=_(u'Permission result'),
                required=False
            )
            permissionOwner_permissionDigRef = schema.TextLine(title=_(u'Dig. ref.'), required=False)

            # Miscellaneous
            miscellaneous_insuranceValue = schema.TextLine(title=_(u'Insurance Value'), required=False)
            miscellaneous_currency = schema.TextLine(title=_(u'Currency'), required=False)
            miscellaneous_conditions = schema.TextLine(title=_(u'Conditions'), required=False)
            miscellaneous_notes = schema.TextLine(title=_(u'Notes'), required=False)"""
        
        objects = []

        if len(first_record.findall('object-out')) > 0:
            for obj in first_record.findall('object-out'):
                new_obj = {
                    "objectNumber":"",
                    "loanTitle": "",
                    "status": "",
                    "date": "",
                    "authoriserInternal": "",
                    "authorisationDate": "",
                    "reviewRequest_template": "",
                    "reviewRequest_date": "",
                    "reviewRequest_digRef": "",
                    "permissionOwner_requestTemplate": "",
                    "permissionOwner_date": "",
                    "permissionOwner_digRef": "",
                    "permissionOwner_permissionResult": "",
                    "permissionOwner_permissionDigRef": "",
                    "miscellaneous_insuranceValue": "",
                    "miscellaneous_currency": "",
                    "miscellaneous_conditions": "",
                    "miscellaneous_notes": ""
                }

                # objectNumber
                if obj.find('object-out.object_number') != None:
                    if obj.find('object-out.object_number').find('object_number') != None:
                        new_obj['objectNumber'] = obj.find('object-out.object_number').find('object_number').text

                # loanTitle
                if obj.find('object-out.title.loan') != None:
                    new_obj['loanTitle'] = obj.find('object-out.title.loan').text

                # status
                if obj.find('object-out.status') != None:
                    if obj.find('object-out.status').find('text') != None:
                        new_obj['status'] = obj.find('object-out.status').find('text').text

                # date
                if obj.find('object-out.status.date') != None:
                    new_obj['date'] = obj.find('object-out.status.date').text

                # authoriserInternal
                if obj.find('object-out.authoriser') != None:
                    if obj.find('object-out.authoriser').find('name') != None:
                        new_obj['authoriserInternal'] = obj.find('object-out.authoriser').find('name').text

                # authorisationDate
                if obj.find('object-out.authorisation_date') != None:
                    new_obj['authorisationDate'] = obj.find('object-out.authorisation_date').text

                # reviewRequest_template
                if obj.find('object-out.review_request.templa') != None:
                    if obj.find('object-out.review_request.templa').find('text') != None:
                        new_obj['reviewRequest_template'] = obj.find('object-out.review_request.templa').find('text').text

                # reviewRequest_date
                if obj.find('object-out.review_request.date') != None:
                    new_obj['reviewRequest_date'] = obj.find('object-out.review_request.date').text

                # reviewRequest_digRef
                if obj.find('object-out.review_request.refere') != None:
                    new_obj['reviewRequest_digRef'] = obj.find('object-out.review_request.refere').text

                # permissionOwner_requestTemplate
                if obj.find('object-out.perm_owner.req.templa') != None:
                    if obj.find('object-out.perm_owner.req.templa').find('text') != None:
                        new_obj['permissionOwner_requestTemplate'] = obj.find('object-out.perm_owner.req.templa').find('text').text

                # permissionOwner_date
                if obj.find('object-out.perm_owner.req.date') != None:
                    new_obj['permissionOwner_date'] = obj.find('object-out.perm_owner.req.date').text

                # permissionOwner_digRef
                if obj.find('object-out.perm_owner.req.ref') != None:
                    new_obj['permissionOwner_digRef'] = obj.find('object-out.perm_owner.req.ref').text

                # permissionOwner_permissionResult
                if obj.find('object-out.perm_owner.result') != None:
                    if obj.find('object-out.perm_owner.result').find('text') != None:
                        new_obj['permissionOwner_permissionResult'] = obj.find('object-out.perm_owner.result').find('text').text

                # permissionOwner_permissionDigRef
                if obj.find('object-out.perm_owner.result.ref') != None:
                    new_obj['permissionOwner_permissionDigRef'] = obj.find('object-out.perm_owner.result.ref').text

                # miscellaneous_insuranceValue
                if obj.find('object-out.insurance_value') != None:
                    new_obj['miscellaneous_insuranceValue'] = obj.find('object-out.insurance_value').text

                # miscellaneous_currency
                if obj.find('object-out.insurance_value.curr') != None:
                    new_obj['miscellaneous_currency'] = obj.find('object-out.insurance_value.curr').text

                # miscellaneous_conditions
                if obj.find('object-out.loan_conditions') != None:
                    new_obj['miscellaneous_conditions'] = obj.find('object-out.loan_conditions').text

                # miscellaneous_notes
                if obj.find('object-out.notes') != None:
                    new_obj['miscellaneous_notes'] = obj.find('object-out.notes').text


                objects.append(new_obj)


        object_data['objects_object'] = objects

    def get_contract_fieldset(self, object_data, first_record):

        # contract_contractDetails_requestPeriodFrom


        # contract_contractDetails_to

        # contract_contractDetails_conditions

        # contract_contractDetails_notes

        # contract_contractLetter_template

        # contract_contractLetter_date

        # contract_contractLetter_digRef

        # contract_contractLetter_signedReturned

        # contract_contractLetter_signedReturnedDigRef

        # contract_conditionReport_template

        # contract_conditionReport_date

        # contract_conditionReport_digRef

        # contract_extension

        pass

    def find_item_by_type(self, object_number, portal_type):
        result = None
        if portal_type == "Object":
            result = self.find_object(self.all_objects, object_number, False)
        elif portal_type == "Book":
            result = self.find_object(self.all_objects, object_number, True)
        elif portal_type == "PersonOrInstitution":
            result = self.find_person_by_priref(self.all_persons, object_number)
        elif portal_type == "Exhibition":
            result = self.find_exhibition_by_priref(object_number)
        elif portal_type == "IncomingLoan":
            result = self.find_incomingloan_by_nummer(object_number)
        elif portal_type == "OutgoingLoan":
            result = self.find_outgoingloan_by_priref(object_number)
        elif portal_type == "treatment":
            result = self.find_treatment_by_priref(object_number)
        elif portal_type == "ObjectEntry":
            result = self.find_objectentry_by_priref(object_number)
        elif portal_type == "Resource":
            result = self.find_resource_by_priref(object_number)
        elif portal_type == "Taxonomie":
            result = self.find_taxonomie_by_priref(object_number)
        else:
            print "[ ERROR ] Portal type '%s' not supported." %(portal_type)

        return result
 
    def find_object(self, all_objects, object_number, is_book=False):
        if object_number:
            if is_book:
                results = self.portal_catalog(portal_type="Book")
                if results:
                    for res in results:
                        obj = res.getObject()
                        if object_number == obj.priref:
                            return obj
            else:
                results = self.portal_catalog(identification_identification_objectNumber=object_number, portal_type="Object")
                if results:
                    item = results[0]
                    obj = item.getObject()
                    return obj
                else:
                    lower_number = object_number.lower()
                    results = self.portal_catalog(identification_identification_objectNumber=lower_number, portal_type="Object")
                    if results:
                        item = results[0]
                        obj = item.getObject()
                        return obj
        return None

    def rel_exists(self, rel_obj, related_objects):
        # Try to check if related item already exists

        if hasattr(rel_obj, 'identification_identification_objectNumber'):
            object_number = rel_obj.identification_identification_objectNumber
            for obj in related_objects:
                rel = obj.to_object
                if hasattr(rel, 'identification_identification_objectNumber'):
                    if rel.identification_identification_objectNumber == object_number:
                        print "Rel already exists."
                        return True
            return False
        else:
            return False

    def add_related_object(self, rel_obj, obj):
        # Tries to add linked object to related items

        intids = component.getUtility(IIntIds)
        if hasattr(obj, 'linkedObjects_relatedObjects'):
            curr_related_objects = obj.linkedObjects_relatedObjects

            # Try to check if related item already exists
            
            if not self.rel_exists(rel_obj, curr_related_objects):
                # Add related object if rel doesn't exist
                if len(obj.linkedObjects_relatedObjects) == 0:
                    obj.linkedObjects_relatedObjects = []

                rel_obj_id = intids.getId(rel_obj)
                rel_obj_value = RelationValue(rel_obj_id)
                obj.linkedObjects_relatedObjects.append(rel_obj_value)
                print "Added relation."

        return None

    def transform_linkedObjects_relatedObjects(self):

        # get items
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")

        total = len(container)
        curr = 0

        for item in container:
            obj = container[item]

            curr += 1
            print "%s / %s" %(str(curr), str(total))

            if hasattr(obj, 'linkedObjects_linkedObjects'):
                linked_objects = obj.linkedObjects_linkedObjects
                # Original linked objects
                print "Object n. related: %s" %(len(linked_objects))
                for linked in linked_objects:
                    rel_object_number = linked['objectNumber']

                    # Find if linked object exists
                    rel_object = self.find_object(all_objects, rel_object_number)
                    if rel_object != None:
                        # Tries to add linked object to related items
                        self.add_related_object(rel_object, obj)
                    else:
                        print "Object not found."

        return True


    def rel_person_exists(self, rel_obj, related_objects):
        # Try to check if related item already exists

        if hasattr(rel_person, 'nameInformation_name_name'):
            name = rel_obj.nameInformation_name_name
            for obj in related_objects:
                rel = obj.to_object
                if hasattr(rel, 'nameInformation_name_name'):
                    if rel.nameInformation_name_name == name:
                        print "Rel already exists."
                        return True
            return False
        else:
            return False

    def add_related_person(self, rel_obj, obj, target_field, target_term, index):
        # Tries to add linked object to related items

        intids = component.getUtility(IIntIds)
        if hasattr(obj, target_field):
            curr_related_objects = getattr(obj, target_field, [])
            if curr_related_objects:
                current_rel = curr_related_objects[index][target_term]

            # Try to check if related item already exists
            
            if not self.rel_person_exists(rel_obj, current_rel):
                # Add related object if rel doesn't exist
                if len(current_rel) == 0:
                    curr_related_objects[index][target_term] = []

                rel_obj_id = intids.getId(rel_obj)
                rel_obj_value = RelationValue(rel_obj_id)

                current_rel.append(rel_obj_value)
                curr_related_objects[index][target_term] = current_rel

                setattr(obj, target_field, curr_related_objects)
                print "Added person relation."

        return None

    def find_person(self, all_persons, name):
        if name:
            for brain in all_persons:
                obj = brain.getObject()
                if hasattr(obj, 'nameInformation_name_name'):
                    if obj.nameInformation_name_name == name:
                        return obj
        return None

    def find_person_by_priref(self, all_persons, priref, updater=None):
        """if priref:
            for brain in all_persons:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        """
        if priref:
            results = self.portal_catalog(person_priref=priref, portal_type="PersonOrInstitution")
            if results:
                item = results[0]
                obj = item.getObject()
                return obj

        return None

    def find_person_by_name(self, name):
        relations = []
        if name:
            for brain in self.all_persons:
                obj = brain.getObject()
                if hasattr(obj, 'nameInformation_name_name'):
                    if obj.nameInformation_name_name == name:
                        relations.append(obj)

        return relations

    def find_bibliotheek_by_priref(self, priref):
        if priref:
            results = self.portal_catalog(path={"query":"/zm/nl/bibliotheek", "depth": 2})
            if results:
                for res in results:
                    item = res.getObject()
                    if hasattr(item, 'priref'):
                        if item.priref == priref:
                            return item
        return None

    def find_article_by_priref(self, priref):
        if priref:
            for brain in self.all_articles:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        return None

    def find_objectentry_by_priref(self, priref):
        if priref:
            for brain in self.all_objectentries:
                try:
                    obj = brain.getObject()
                    if hasattr(obj, 'priref'):
                        if obj.priref == priref:
                            return obj
                except:
                    continue

        return None

    def find_incomingloan_by_priref(self, priref):
        if priref:
            for brain in self.all_incoming:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        return None

    def find_incomingloan_by_nummer(self, nummer):

        if nummer:
            for brain in self.all_incoming:
                obj = brain.getObject()
                if hasattr(obj, 'loanRequest_general_loanNumber'):
                    if obj.loanRequest_general_loanNumber == nummer:
                        return obj

        return None

    def find_outgoingloan_by_nummer(self, nummer):

        if nummer:
            for brain in self.all_outgoing:
                obj = brain.getObject()
                if hasattr(obj, 'loanRequest_general_loanNumber'):
                    if obj.loanRequest_general_loanNumber == nummer:
                        return obj

        return None
    
    def find_outgoingloan_by_priref(self, priref):
        if priref:
            for brain in self.all_outgoing:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        return None 

    def find_resource_by_priref(self, priref):
        if priref:
            for brain in self.all_resources:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        return None

    def find_taxonomie_by_priref(self, priref):
        if priref:
            for brain in self.all_taxonomies:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        return None

    def find_taxonomie_by_name(self, name):
        relations = []
        if name:
            for brain in self.all_taxonomies:
                obj = brain.getObject()
                if hasattr(obj, 'taxonomicTermDetails_term_scientificName'):
                    if obj.taxonomicTermDetails_term_scientificName == name:
                        relations.append(obj)

        return relations

    def find_exhibition_by_priref(self, priref):
        if priref:
            for brain in self.all_exhibitions:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj

        return None

    def find_archive_by_priref(self, priref):
        """if priref:
            for brain in self.all_archives:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj"""

        if priref:
            results = self.portal_catalog(archive_priref=priref, portal_type="Archive")
            if results:
                item = results[0]
                obj = item.getObject()
                return obj

        return None

    def find_treatment_by_priref(self, priref):
        """if priref:
            results = self.portal_catalog(treatment_priref=priref, portal_type="treatment")
            if results:
                item = results[0]
                obj = item.getObject()
                return obj"""
        if priref:
            for brain in self.all_treatments:
                obj = brain.getObject()
                if hasattr(obj, 'priref'):
                    if obj.priref == priref:
                        return obj
        return None

    def find_treatment_by_treatmentnumber(self, priref):
        if priref:
            for brain in self.all_treatments:
                obj = brain.getObject()
                if hasattr(obj, 'treatmentDetails_identification_treatmentNumber'):
                    if obj.treatmentDetails_identification_treatmentNumber == priref:
                        return obj
        return None

    def transform_relation_institutions(self):

        # get items
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")
        all_persons = catalog(portal_type='PersonOrInstitution', Language="all")

        total = len(container)
        curr = 0

        original_field = "productionDating_production"
        target_field = 'productionDating_productionDating'
        term = "maker"
        target_term = "makers"

        for item in all_objects:
            obj = item.getObject()

            curr += 1
            print "%s / %s" %(str(curr), str(total))

            if hasattr(obj, orginal_field):
                linked_objects = getattr(obj, original_field, [])
                # Original linked objects
                print "Object n. related: %s" %(len(linked_objects))
                for index, linked in enumerate(linked_objects):
                    maker = linked[term]

                    # Find if linked object exists
                    rel_person = self.find_person(all_persons, maker)
                    if rel_person != None:
                        # Tries to add linked object to related items
                        self.add_related_person(rel_object, obj, target_field, target_term, index)
                    else:
                        print "Object not found."

        return True

    def transform_exhibition_example_linkedObjects(self):
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")

        for item in container:
            obj = container[item]
            if obj.title == "Zwartvoet Indianen":
                if hasattr(obj, 'linkedObjects_linkedObjects'):
                    linked_objects = obj.linkedObjects_linkedObjects
                    
                    # Original linked objects
                    total = len(linked_objects)
                    curr = 0
                    for linked in linked_objects:
                        transaction.begin()
                        curr += 1
                        print "Get linkedObject %s / %s" %(curr, total) 
                        
                        rel_object_number = linked['objectNumber']

                        # Find if linked object exists
                        rel_object = self.find_object(all_objects, rel_object_number)
                        if rel_object != None:
                            # Tries to add linked object to related items
                            self.add_related_object(rel_object, obj)
                        else:
                            print "Object does not exist %s" %(rel_object_number)

                        transaction.commit()

                print "Final reindexObject"
                obj.reindexObject()
                print "END!"
                return True

        print "END!"
        return True


    def transform_content_linkedObjects(self):
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")

        for item in container:
            obj = container[item]
            if hasattr(obj, 'linkedObjects_linkedObjects'):
                linked_objects = obj.linkedObjects_linkedObjects
                
                # Original linked objects
                total = len(linked_objects)
                curr = 0
                for linked in linked_objects:
                    transaction.begin()
                    curr += 1
                    print "Get linkedObject %s / %s" %(curr, total) 
                    
                    rel_object_number = linked['objectNumber']

                    # Find if linked object exists
                    rel_object = self.find_object(all_objects, rel_object_number)
                    if rel_object != None:
                        # Tries to add linked object to related items
                        self.add_related_object(rel_object, obj)
                    else:
                        print "Object does not exist %s" %(rel_object_number)

                    transaction.commit()

            print "Final reindexObject"
            obj.reindexObject()
            print "END!"
            return True

        print "END!"
        return True

    ##
    ## Related items for Persons or Institutions
    ##

    def rel_institution_exists(self, rel_obj, related_objects):
        # Try to check if related item already exists

        if hasattr(rel_obj, 'priref'):
            ref = rel_obj.priref
            for obj in related_objects:
                rel = obj.to_object
                if hasattr(rel, 'priref'):
                    if rel.priref == ref:
                        print "Rel already exists."
                        return True
            return False
        else:
            return False

    def add_related_institution(self, rel_obj, obj):
        # Tries to add linked object to related items

        intids = component.getUtility(IIntIds)
        if hasattr(obj, 'exhibitionsDetails_organizingInstitution'):
            curr_related_objects = obj.exhibitionsDetails_organizingInstitution

            # Try to check if related item already exists
            if not self.rel_institution_exists(rel_obj, curr_related_objects):
                # Add related object if rel doesn't exist
                if len(obj.exhibitionsDetails_organizingInstitution) == 0:
                    obj.exhibitionsDetails_organizingInstitution = []
                    
                rel_obj_id = intids.getId(rel_obj)
                rel_obj_value = RelationValue(rel_obj_id)
                obj.exhibitionsDetails_organizingInstitution.append(rel_obj_value)
                obj.reindexObject()
                print "Added relation."

        return None

    #def find_person(self, all_objects, ref):
    #    for brain in all_objects:
    #        obj = brain.getObject()
    #        if hasattr(obj, 'priref'):
    #            if obj.priref == ref:
    #                return obj
    #    return None

    def transform_exhibition_example_institutions(self):
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='PersonOrInstitution', Language="all")

        total_ob = len(container)
        curr_ob = 0
        for item in list(container):
            curr_ob += 1
            print "%s / %s" %(str(curr_ob), str(total_ob))

            obj = container[item]
            if hasattr(obj, 'exhibitionsDetails_organizingInstitutions'):
                transaction.begin()
                institutions = obj.exhibitionsDetails_organizingInstitutions
                
                # Original Organising institutions
                total = len(institutions)
                curr = 0
                for linked in institutions:
                    
                    curr += 1
                    print "Get Relation %s / %s" %(str(curr), str(total)) 
                    
                    rel_ref = linked['linkref']

                    # Find if linked object exists
                    rel_object = self.find_person(all_objects, rel_ref)

                    if rel_object != None:
                        # Tries to add linked object to related items
                        self.add_related_institution(rel_object, obj)
                    else:
                        print "Person does not exist %s" %(rel_ref)

                    

                print "reindexObject"
                obj.reindexObject()
                print "END!"
                transaction.commit()

        print "END!"
        return True

    def get_folder(self, path):
        container = self.portal

        folder_path = path.split("/")

        for folder in folder_path:
            if hasattr(container, folder):
                container = container[folder]
            else:
                print ("== Chosen folder " + folder + " does not exist. ==")
                self.success = False
                return None

        return container

    def move_obj_folder(self, source, target):
        api.content.move(source=source, target=target)

    def divide_collection_by_folder(self):
        container = self.get_container()

        geschiedenis = ['Archeologie', 'Beeld en geluid - overig', 'Bouwfragmenten', 'Boeken',
                        'Documenten', 'Etnografica - boeken', 'Etnografica - documenten',
                        'Etnografica - gebruiksvoorwerpen', 'Etnografica - modellen',
                        'Etnografica - wapens', 'Gebruiksvoorwerpen', 'Historische voorwerpen en memorabilia',
                        'Modellen - volkskunst', 'Munten en penningen', 'Plat textiel - gebruiksgoed',
                        'Wapens en munitie']

        _geschiedenis = [item.lower() for item in geschiedenis]

        kunst = ['Beeldhouwwerken', 'Etnografica - beelden', 'Moderne en hedendaagse kunst',
                'Prenten en tekeningen', 'Schilderkunst']

        _kunst = [item.lower() for item in kunst]

        kunstnijverheid = ['Aardewerk en tegels', 'Etnografica - kunstnijverheid', 'Kunstnijverheid',
                            'Meubilair', 'Modellen - kunstnijverheid', 'Plat textiel - kunstnijverheid',
                            'Porselein', 'Zilver en goud']

        _kunstnijverheid = [item.lower() for item in kunstnijverheid]

        mode_en_streekdracht = ['Beeld en geluid - streekdracht', 'Etnografica - kleding en accessoires',
                                'Etnografica - sieraden', 'Sieraden (geen streeksieraden)',
                                'Streekdrachten en mode', 'Streeksieraden']

        _mode_en_streekdracht = [item.lower() for item in mode_en_streekdracht]

        natuurhistorie = ['Etnografica - natuurhistorie', 'Natuurhistorie']
        _natuurhistorie = [item.lower() for item in natuurhistorie]

        _16eEeuwseZeeuwsewandtapijten = ['16e Eeuwse Zeeuwse wandtapijten']
        __16eEeuwseZeeuwsewandtapijten = [item.lower() for item in _16eEeuwseZeeuwsewandtapijten]

        _total = len(container)
        curr = 0

        admin_names_not_in_list = []

        for brain in list(container):
            transaction.begin()
            curr += 1
            obj = container[brain]
            
            print "Moving object %s / %s" %(str(curr), str(_total))

            if hasattr(obj, 'identification_identification_administrativeName'):
                admin_name = obj.identification_identification_administrativeName
                admin_name = admin_name.lower()

                if admin_name in _geschiedenis:
                    path = "nl/collectie/geschiedenis-en-archeologie"
                    folder = self.get_folder(path)
                elif admin_name in _kunst:
                    path = "nl/collectie/kunst"
                    folder = self.get_folder(path)
                elif admin_name in _kunstnijverheid:
                    path = "nl/collectie/kunstnijverheid"
                    folder = self.get_folder(path)
                elif admin_name in _mode_en_streekdracht:
                    path = "nl/collectie/mode-en-streekdracht"
                    folder = self.get_folder(path)
                elif admin_name in _natuurhistorie:
                    path = "nl/collectie/natuurhistorie"
                    folder = self.get_folder(path)
                elif admin_name in __16eEeuwseZeeuwsewandtapijten:
                    path = "nl/collectie/16e-eeuwse-zeeuwse-wandtapijten"
                    folder = self.get_folder(path)
                else:
                    path = "nl/collectie/prive"
                    folder = self.get_folder(path)
                    #if admin_name not in admin_names_not_in_list:
                    #    admin_names_not_in_list.append(admin_name)
                    #continue

                print "Moving object to: %s" %(str(folder))

                try:
                    last_folder = path.split("/")[-1]
                    if last_folder not in self.folder_path:
                        self.move_obj_folder(obj, folder)
                    else:
                        print "Same folder. Skipping."
                except:
                    pass

                transaction.commit()

        print "Admin names not in list:"
        print admin_names_not_in_list
        
        return True


    def test_move_folder(self):
        container = self.get_container()

        for item in container:
            obj = container[item]
            if obj.title == "Zwartvoet Indianen":
                path = "nl/geschiedenis-en-archeologie"
                folder = self.get_folder(path)
                print folder
                self.move_obj_folder(obj, folder)
                print "Moved"

        return True

    def import_zm_exhibitions(self):
        pass

    def delete_all_objects_container(self):
        container = self.get_container()

        total = len(container)
        curr = 0

        for obj in container:
            transaction.begin()
            curr += 1
            item = container[obj]
            if item.portal_type == "Object":
                print "Delete object %s / %s" %(str(curr), str(total))
                container.manage_delObjects([obj])
            transaction.commit()

        print "Deleted objects!"
        return True


    def find_contained_object_number(self, objects, curr_number):
        contain = []
        for obj in objects:
            if obj.find('object_number') != None:
                object_number = obj.find('object_number').text
                if object_number != curr_number:
                    if curr_number in object_number:
                        contain.append(object_number)

        return contain


    def verify_object_numbers(self):
        collection_path = "/Users/AG/Projects/collectie-zm/grouped2.xml"
        objects = self.get_zm_collection(collection_path)

        total = len(objects)
        curr = 0

        for obj in objects:
            curr += 1
            #print "Find %s / %s" %(str(curr), str(total))
            if obj.find('object_number') != None:
                object_number = obj.find('object_number').text
                contained = self.find_contained_object_number(objects, object_number)
                if len(contained) > 0:
                    print "Object number %s contained in %s" %(str(object_number), str(contained))

        return True


    def find_image_by_ref(self, ref, all_images):
        image_path_split = ref.lower().split("\\")
        img = image_path_split[-1]
        
        image_id = idnormalizer.normalize(img, max_length=len(img))

        for image in all_images:
            if image.id == image_id:
                return True

        return None

    def get_image_data(self, record):
        object_data = {
            'priref': '',
            'reproductionData_identification_reproductionReference':"",
            'reproductionData_identification_format':"",
            'reproductionData_identification_reproductionType':"",
            'reproductionData_identification_copies':"",
            'reproductionData_identification_technique':"",
            'reproductionData_identification_location':"",
            'reproductionData_identification_date':"",
            'reproductionData_identification_identifierURL':"",
            'reproductionData_descriptiveElements_title':"",
            'reproductionData_descriptiveElements_creator':"",
            'reproductionData_descriptiveElements_subject':"",
            'reproductionData_descriptiveElements_description':"",
            'reproductionData_descriptiveElements_publisher':"",
            'reproductionData_descriptiveElements_contributor':"",
            'reproductionData_descriptiveElements_source':"",
            'reproductionData_descriptiveElements_coverage':"",
            'reproductionData_descriptiveElements_rights':"",
            'reproductionData_descriptiveElements_notes':"",

            'documentation_documentation':[],

            'linkedObjects_linkedObjects':[],
        }


        # reference number 

        if record != None:
            try:
                if record.find('reference_number') != None:
                    object_data['reproductionData_identification_reproductionReference'] = self.trim_white_spaces(record.find('reference_number').text)
            except:
                pass

            if record.find('priref') != None:
                object_data['priref'] = self.trim_white_spaces(record.find('priref').text)
                
            if record.find('format') != None:
                object_data['reproductionData_identification_format'] = self.trim_white_spaces(record.find('format').text)

            if record.find('reproduction_type') != None:
                if record.find('reproduction_type').find('term') != None:
                    object_data['reproductionData_identification_reproductionType'] = self.trim_white_spaces(record.find('reproduction_type').find('term').text)

            if record.find('copies') != None:
                object_data['reproductionData_identification_copies'] = self.trim_white_spaces(record.find('copies').text)

            if record.find('technique') != None:
                if record.find('technique').find('term') != None:
                    object_data['reproductionData_identification_technique'] = self.trim_white_spaces(record.find('technique').find('term').text)

            if record.find('location') != None:
                if record.find('location').find('term') != None:
                    object_data['reproductionData_identification_location'] = self.trim_white_spaces(record.find('location').find('term').text)

            if record.find('production_date') != None:
                object_data['reproductionData_identification_date'] = self.trim_white_spaces(record.find('production_date').text)


            if record.find('image_reference') != None:
                object_data['reproductionData_identification_identifierURL'] = self.trim_white_spaces(record.find('image_reference').text)


            # descriptive

            if record.find('title') != None:
                object_data['reproductionData_descriptiveElements_title'] = self.trim_white_spaces(record.find('title').text)

            if record.find('creator') != None:
                if record.find('creator').find('name') != None:
                    object_data['reproductionData_descriptiveElements_creator'] = self.trim_white_spaces(record.find('creator').find('name').text)


            if record.find('subject') != None:
                if record.find('subject').find('term') != None:
                    object_data['reproductionData_descriptiveElements_subject'] = self.trim_white_spaces(record.find('subject').find('term').text)

            if record.find('description') != None:
                object_data['reproductionData_descriptiveElements_description'] = self.trim_white_spaces(record.find('description').text)

            if record.find('publisher') != None:
                if record.find('publisher').find('name') != None:
                    object_data['reproductionData_descriptiveElements_publisher'] = self.trim_white_spaces(record.find('publisher').find('name').text)

            if record.find('contributor') != None:
                if record.find('contributor').find('name') != None:
                    object_data['reproductionData_descriptiveElements_contributor'] = self.trim_white_spaces(record.find('contributor').find('name').text)

            if record.find('source') != None:
                object_data['reproductionData_descriptiveElements_source'] = self.trim_white_spaces(record.find('source').text)

            if record.find('coverage') != None:
                if record.find('coverage').find('term') != None:
                    object_data['reproductionData_descriptiveElements_coverage'] = self.trim_white_spaces(record.find('coverage').find('term').text)

            if record.find('rights') != None:
                object_data['reproductionData_descriptiveElements_rights'] = self.trim_white_spaces(record.find('rights').text)

            if record.find('notes') != None:
                object_data['reproductionData_descriptiveElements_notes'] = self.trim_white_spaces(record.find('notes').text)


        # Documentation

        # documentation_documentation
        """ class IDocumentationDocumentation(Interface):
            article = schema.TextLine(title=_(u'Article'), required=False)
            title = schema.TextLine(title=_(u'Title'), required=False)
            author = schema.TextLine(title=_(u'Author'), required=False)
            pageMark = schema.TextLine(title=_(u'Page mark'), required=False)
            shelfMark = schema.TextLine(title=_(u'Shelf mark'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        documentation = []

        if len(record.findall('documentation')) > 0:
            for doc in record.findall('documentation'):
                new_doc = {
                    "article": "",
                    "title": "",
                    "author": "",
                    "pageMark": "",
                    "shelfMark": "",
                    "notes": ""
                }

                if doc.find('documentation.title') != None:
                    if doc.find('documentation.title').find('lead_word') != None:
                        new_doc['article'] = self.trim_white_spaces(doc.find('documentation.title').find('lead_word').text)

                if doc.find('documentation.title') != None:
                    if doc.find('documentation.title').find('title') != None:
                        new_doc['title'] = self.trim_white_spaces(doc.find('documentation.title').find('title').text)

                if doc.find('documentation.author') != None:
                    new_doc['author'] = self.trim_white_spaces(doc.find('documentation.author').text)

                if doc.find('documentation.page_reference') != None:
                    new_doc['pageMark'] = self.trim_white_spaces(doc.find('documentation.page_reference').text)

                if doc.find('documentation.shelfmark') != None:
                    new_doc['shelfMark'] = self.trim_white_spaces(doc.find('documentation.shelfmark').text)

                if doc.find('documentation.notes') != None:
                    new_doc['notes'] = self.trim_white_spaces(doc.find('documentation.notes').text)

                documentation.append(new_doc)


        object_data['documentation_documentation'] = documentation

        # Linked Objects
        # linkedObjects_linkedObjects

        """class ILinkedObjects(Interface):
            objectNumber = schema.TextLine(title=_(u'Object number'), required=False)
            creator = schema.TextLine(title=_(u'Creator'), required=False)
            objectName = schema.TextLine(title=_(u'Object name'), required=False)
            title = schema.TextLine(title=_(u'Title'), required=False)"""

        linked_objects = []

        if len(record.findall('object.object_number')):
            for obj in record.findall('object.object_number'):
                new_object = {
                    "objectNumber": "",
                    "creator": "",
                    "objectName": "",
                    "title": ""
                }

                if obj.find('object_number') != None:
                    new_object["objectNumber"] = self.trim_white_spaces(obj.find('object_number').text)

                if obj.find('creator') != None:
                    new_object["creator"] = self.trim_white_spaces(obj.find('creator').text)

                if obj.find('object_name') != None:
                    new_object["objectName"] = self.trim_white_spaces(obj.find('object_name').text)

                if obj.find('title') != None:
                    new_object["title"] = self.trim_white_spaces(obj.find('title').text)

                linked_objects.append(new_object)


        object_data["linkedObjects_linkedObjects"] = linked_objects


        return object_data

    def update_image_obj_data(self, image, data):
        for key, value in data.iteritems():
            if key not in ['priref']:
                setattr(image, key, value)

        return True

    def update_image_data(self, image, data):
        image_obj = image.getObject()
        for key, value in data.iteritems():
            if key not in ['priref']:
                setattr(image_obj, key, value)

        return True

    def find_object_refs(self, data):
        pass


    def update_visual_metadata(self):
        live_collection_path = "/var/www/zm-collectie-v2/xml/Beelddocumentatie.xml"
        collection_path = "/home/andre/collectie-zm-v1/migration/imagesreference.xml"
        dev_path = "/Users/AG/Projects/collectie-zm/Beelddocumentatie.xml"
        single_object = "/Users/AG/Projects/collectie-zm/visual-documentation-v1.xml"
        objects = self.get_zm_collection(live_collection_path)

        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")
        all_images = catalog(portal_type='Image', Language="all")

        total = len(objects)
        curr = 0

        total_images_updated = 0
        images_updated = []
        images_not_found = []

        for obj in objects:
            curr += 1
            transaction.begin()
            print "%s / %s" %(str(curr), str(total))
            
            if len(obj.findall('image_reference')) > 0:
                for img_reference in obj.findall('image_reference'):
                    ref = img_reference.text
                    image_found = self.find_image_by_ref(ref, all_images)
                    
                    if image_found != True:
                        print "Cannot find image %s in website" %(str(ref))
                        data = self.get_image_data(obj)
                        images_not_found.append(ref)
                        related_objects = data['linkedObjects_linkedObjects']

                        for related_object in related_objects:
                            object_number = related_object['objectNumber']
                            item = self.find_object(all_objects, object_number)

                            if item != None:
                                try:
                                    self.create_visual_data(item, data)
                                    print "Add empty image in %s" %(item.absolute_url())
                                    total_images_updated += 1
                                except:
                                    print "Failed to create empty image"
                                    raise
                            else:
                                print "Object number ref not found %s" %(object_number)
                    else:
                        print "Image was found."

            else:
                print "Object has no image references."

            transaction.commit()

        #print images_updated
        print "Detailed list of images not found: "
        print images_not_found

        print "Total images updated: %s" %(str(total_images_updated))
        print "Total images not found: %s" %(str(len(images_not_found)))
        
        return True

    def update_images_metadata(self):
        live_collection_path = "/var/www/zm-collectie-v2/xml/Beelddocumentatie.xml"
        collection_path = "/home/andre/collectie-zm-v1/migration/imagesreference.xml"
        dev_path = "/Users/AG/Projects/collectie-zm/Beelddocumentatie.xml"
        single_object = "/Users/AG/Projects/collectie-zm/visual-documentation-v1.xml"
        objects = self.get_zm_collection(live_collection_path)

        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_images = catalog(portal_type='Image', Language="all")
        all_objects = catalog(portal_type='Object', Language="all")

        total = len(objects)
        curr = 0

        total_images_updated = 0
        images_updated = []
        images_not_found = []

        for obj in objects:
            curr += 1
            
            print "%s / %s" %(str(curr), str(total))

            if len(obj.findall('image_reference')) > 0:
                for img_reference in obj.findall('image_reference'):
                    image = self.find_image_by_ref(img_reference.text, all_images)
                    
                    if image != None:
                        continue
                        # Get data
                        data = self.get_image_data(obj)
                        
                        # Update data
                        try:
                            self.update_image_data(image, data)
                            print "Image updated!"
                            total_images_updated += 1
                            images_updated.append(image.getObject().absolute_url())
                        except:
                            print "Failed to update image"
                            pass
                        
                    else:
                        print "Cannot find image %s in website" %(str(ref))
                        data = self.get_image_data(obj)
                        images_not_found.append(ref)
                        related_objects = data['linkedObjects_linkedObjects']

                        for rel in related_objects:
                            object_number = rel['objectNumber']
                            item = self.find_object(all_objects, object_number)
                            if item != None:
                                try:
                                    self.create_visual_data(item, data)
                                    print "Add empty image in %s" %(item.absolute_url())
                                    total_images_updated += 1
                                except:
                                    print "Failed to create empty image"
                                    raise
                            else:
                                print "Object number ref not found %s" %(object_number)

            else:
                print "Object has no image references."

        #print images_updated
        
        print "Detailed list of images not found: "
        print images_not_found

        print "Total images updated: %s" %(str(total_images_updated))
        print "Total images not found: %s" %(str(len(images_not_found)))
        
        return

    def create_visual_data(self, item, data):
        if data['reproductionData_identification_reproductionReference'] != "":
            dirty_id = data['reproductionData_identification_reproductionReference']
        else:
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id)

        transaction.begin()
        
        # get price of item
        if 'prive' in item:
            prive = item['prive']
            if prive != None:
                if not hasattr(prive, normalized_id):
                    prive.invokeFactory(type_name="Image", id=normalized_id, title=normalized_id)
                    new_image = prive[normalized_id]

                    # Create fields
                    self.update_image_obj_data(new_image, data)

        # get slideshow of item
        elif hasattr(item, 'slideshow'):
            slideshow = item['slideshow']
            if not hasattr(slideshow, normalized_id):
                slideshow.invokeFactory(type_name="Image", id=normalized_id, title=normalized_id)
                new_image = slideshow[normalized_id]

                # Create fields
                self.update_image_obj_data(new_image, data)
        else:
            print "Slideshow/Prive folder not found."

        transaction.commit()

        return True

    def create_visual_no_ref(self, data):

        transaction.begin()

        if data['reproductionData_identification_reproductionReference'] != "":
            dirty_id = data['reproductionData_identification_reproductionReference']
        else:
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id)

        folder = "nl/collectie/beelddocumentatie"
        container = self.get_folder(folder)

        if normalized_id not in container:
            container.invokeFactory(type_name="Image", id=normalized_id, title=normalized_id)
            new_image = container[normalized_id]

            self.update_image_obj_data(new_image, data)

        transaction.commit()

        print "Created image without obj ref"

        return True

    def create_visual_documentation(self):
        collection_path = "/home/andre/collectie-zm-v1/migration/imagesreference.xml"
        dev_path = "/Users/AG/Projects/collectie-zm/Beelddocumentatie.xml"
        live_path = "/var/www/zm-collectie-v2/xml/Beelddocumentatie.xml"
        single_object = "/Users/AG/Projects/collectie-zm/visual-documentation-v1.xml"
        objects = self.get_zm_collection(dev_path)

        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type="Object", Language='nl')

        total = len(objects)
        curr = 0

        images_without_image_ref = 0
        total_images_updated = 0
        images_updated = []

        n_without_obj_ref = 0

        if len(list(all_objects)) > 0:
            for obj in objects:
                try:
                    curr += 1
                    
                    print "%s / %s" %(str(curr), str(total))
                    
                    if len(obj.findall('image_reference')) > 0:
                        data = self.get_image_data(obj)

                        item = None
                        
                        if len(obj.findall('object.object_number')) > 0:
                            has_ref = False
                            for obj_ref in obj.findall('object.object_number'):
                                if obj_ref.find('object_number') != None:
                                    if obj_ref.find('object_number').text == "" or obj_ref.find('object_number').text == None:
                                        has_ref = False
                                    else:
                                        has_ref = True
                                        object_number = obj.find('object.object_number').find('object_number').text
                                        item = self.find_object(all_objects, object_number)
                                        
                                        if item != None:
                                            try:
                                                self.create_visual_data(item, data)
                                                print "Image created in %s" %(item.absolute_url())
                                                total_images_updated += 1
                                            except:
                                                print "Failed to create image"
                                                raise
                                        else:
                                            print "Object number ref not found %s" %(object_number)
                                
                            if not has_ref:
                                n_without_obj_ref += 1
                                self.create_visual_no_ref(data)
                                    
                        else:
                            n_without_obj_ref += 1
                            self.create_visual_no_ref(data)

                    else:
                        images_without_image_ref += 1
                        self.create_visual_no_ref(data)

                except:
                    raise

        print images_without_image_ref
        print total_images_updated
        print n_without_obj_ref
            
        return

    def find_id_in_visualdoc(self, brain_id, doc):
        for obj in list(doc):
            try:
                for image_ref in obj.findall('image_reference'):
                    if image_ref.text != "" and image_ref.text != None:
                        reference = image_ref.text
                        reference_no_case = reference.lower().split("\\")
                        img_id = reference_no_case[-1]
                        image_id = idnormalizer.normalize(img_id, max_length=len(img_id))

                        if brain_id == image_id:
                            return True
            except:
                raise

        return False

    def check_images_in_plone(self):
        live_path = "/var/www/zm-collectie-v2/xml/Beelddocumentatie.xml"

        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_images = catalog(portal_type="Image", Language='nl')

        objects = self.get_zm_collection(live_path)

        found = 0
        not_found = 0

        total = len(list(all_images))
        curr = 0

        for image in all_images:
            curr += 1
            print "%s / %s" %(str(curr), str(total))
            image_object = image.getObject()
            brain_id = image_object.id
            is_found = self.find_id_in_visualdoc(brain_id, objects)

            if is_found:
                found += 1
            else:
                not_found += 1



        print "Found in Visual documentation: %s" %(str(found))
        print "Not found in Visual documentation: %s" %(str(not_found))

        return True

    def check_visual_documentation(self):
        collection_path = "/home/andre/collectie-zm-v1/migration/imagesreference.xml"
        dev_path = "/Users/AG/Projects/collectie-zm/Beelddocumentatie.xml"
        single_object = "/Users/AG/Projects/collectie-zm/visual-documentation-v1.xml"
        live_path = "/var/www/zm-collectie-v2/xml/Beelddocumentatie.xml"

        objects = self.get_zm_collection(dev_path)

        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type="Object", Language='nl')

        total = len(objects)
        curr = 0

        references = []
        duplicates = []

        obj_references = []
        obj_duplicates = []
        no_image_but_ref = []

        list_of_no_image_no_ref = []
        image_no_obj = []

        n_without_references = 0
        n_without_obj_ref = 0
        n_records_no_image_but_ref = 0
        n_records_image_but_no_ref = 0

        n_records_without_imageref_without_objectref = 0
        ref_to_image_and_obj = 0

        for obj in list(objects):
            try:
                data = self.get_image_data(obj)
                curr += 1
                no_image = False
                print "%s / %s" %(str(curr), str(total))

                if len(obj.findall('image_reference')) == 0:
                    no_image = True
                    n_without_references += 1
                    #self.data(obj)

                elif len(obj.findall('image_reference')) > 0:
                    for image_ref in obj.findall('image_reference'):
                        if image_ref.text not in references:
                            references.append(image_ref.text)
                        else:
                            if image_ref.text not in duplicates:
                                duplicates.append(image_ref.text)

                if len(obj.findall('object.object_number')) > 0:
                    has_ref = False
                    total_refs = 0
                    for obj_ref in obj.findall('object.object_number'):
                        if obj_ref.find('object_number') != None:
                            if obj_ref.find('object_number').text == "" or obj_ref.find('object_number').text == None:
                                if not has_ref:
                                    has_ref = False
                            else:
                                import_obj = False
                                if not has_ref:
                                    import_obj = True

                                has_ref = True
                                total_refs += 1
                                obj_references.append(obj_ref.find('object_number').text)

                                #if no_image and import_obj: # no image but obj ref [needs to create empty image]
                                    #item = self.find_object(all_objects, obj_ref.find('object_number').text)
                                    #if item != None:
                                    #    self.create_visual_data(item, data)
                                    #    print "Image without image file created in %s" %(item.absolute_url())
                                    #else:
                                    #    print "Object %s not found." %(obj_ref.find('object_number').text)


                                if obj_ref.find('object_number').text not in obj_duplicates:
                                    obj_duplicates.append(obj_ref.find('object_number').text)
                        else:
                            has_ref = False

                    if not has_ref: # does not have reference to object
                        n_without_obj_ref += 1 
                        #self.create_visual_no_ref(data)
                        if not no_image: # does not have reference to object, has reference to image
                            n_records_image_but_no_ref += 1
                            image_no_obj.append(obj.find('reference_number').text)
                            ## TODO
                        else:
                            n_records_without_imageref_without_objectref += 1
                            list_of_no_image_no_ref.append(obj.find('reference_number').text)
                            #self.create_visual_no_ref(data)

                    else: # has reference to object
                        if no_image: # has reference to object but not reference to image
                            n_records_no_image_but_ref += 1
                            no_image_but_ref.append(obj.find('reference_number').text)
                        else: # has reference to object and ref to image
                            ref_to_image_and_obj += 1

                else: # no ref to object
                    #self.create_visual_no_ref(data)
                    n_without_obj_ref += 1
                    if not no_image: # no ref to image
                        n_records_without_imageref_without_objectref += 1
                        list_of_no_image_no_ref.append(obj.find('reference_number').text)
                        #self.create_visual_no_ref(data)
                    else:
                        # no ref to object
                        # ref to image
                        n_records_image_but_no_ref += 1
                        image_no_obj.append(obj.find('reference_number').text)

                        ## TODO
            except:
                raise

        print "Number of references to images: %s" %(str(len(references)))
        print "Number of duplicate image references: %s" %(str(len(duplicates))) 
        print "Number of objects references: %s" %(str(len(obj_references)))
        print "Number of objects referenced more than once: %s" %(str(len(obj_duplicates)))
        print "\nNumber of records that do not have image ref but are associated with an object: %s" %(str(n_records_no_image_but_ref))
        print "\nNumber of records without ref to image and without ref to object: %s" %(str(n_records_without_imageref_without_objectref))
        print "\nNumber of records with ref to image and ref to obj: %s" %(str(ref_to_image_and_obj))
        print "\nNumber of records that have image ref but are not associated with an object: %s\n" %(str(n_records_image_but_no_ref))
        print "Visual documentation without reference to an image: %s" %(str(n_without_references))
        print "Visual documentation without reference to an object: %s" %(str(n_without_obj_ref))

        #print list_of_no_image_no_ref
        #print image_no_obj
        print no_image_but_ref

        print "Total of records in XML: %s" %(str(total))

        return

    def create_persons_institutions(self, obj):
        
        transaction.begin()
        
        self.folder_path = "personen-en-instellingen".split('/')

        container = self.get_container()
        dirty_id = str(obj["priref"] + " " + obj['nameInformation_name_institutionNumber'].encode('ascii', 'ignore').decode('ascii') + " " + obj['nameInformation_name_name'].encode('ascii', 'ignore').decode('ascii'))

        if (obj['nameInformation_name_institutionNumber'] == "") and (obj['nameInformation_name_name'] == ""):
            dirty_id = obj['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

        result = False
        obj['text'] = ""

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Person already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = None

                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(obj['text'], 'text/html', 'text/html')

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="PersonOrInstitution",
                        id=normalized_id,
                        title=obj['nameInformation_name_name'],
                        text=text
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    for key, value in obj.iteritems():
                        if key not in ['text']:
                            setattr(created_object, key, value)

                    # Publish object
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])
                    

                    #### Commmit to the database
                    transaction.commit()

                    #### Log object added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Person %s" % (timestamp, normalized_id)

                    self.created += 1
                    result = True
                else:
                    ##
                    ## Person with object_number already exists in database
                    ##
                    self.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Person already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.errors += 1
            self.success = False
            print "Unexpected error on create_persons (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.skipped += 1
            print "%s - Skipped person: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def get_persons_institutions(self, priref, first_record, create):
        object_data = {
            'priref': "",
            'nameInformation_name_name': "", 
            'nameInformation_name_institutionNumber': "",
            'nameInformation_name_nameType': [], 
            'nameInformation_name_nameNotes': "",
            'nameInformation_relationWithOtherNames_use': [], 
            'nameInformation_relationWithOtherNames_usedFor': [],
            'nameInformation_relationWithOtherNames_equivalent': [], 
            'nameInformation_addressDetails': [],
            'nameInformation_telephoneFaxEmail_telephone': [], 
            'nameInformation_telephoneFaxEmail_fax': [],
            'nameInformation_telephoneFaxEmail_email': [], 
            'nameInformation_telephoneFaxEmail_website': [],
            'nameInformation_contacts': [], 
            'nameInformation_miscellaneous_group': [], 
            'nameInformation_miscellaneous_notes': [],
            'personDetails_birthDetails_dateStart' : "", 
            'personDetails_birthDetails_dateEnd': "",
            'personDetails_birthDetails_precision': "", 
            'personDetails_birthDetails_place': "", 
            'personDetails_birthDetails_notes': [], 
            'personDetails_deathDetails_dateStart': "",
            'personDetails_deathDetails_dateEnd': "", 
            'personDetails_deathDetails_precision': "",
            'personDetails_deathDetails_place': "", 
            'personDetails_deathDetails_notes': [],
            'personDetails_nationality_nationality': [], 
            'personDetails_nationality_language': [],
            'personDetails_ocupation_ocupation': [], 
            'personDetails_ocupation_schoolStyle': [],
            'personDetails_placeOfActivity': [], 
            'personDetails_biography': ""
        }

        try:
            self.get_person_details_fieldset(object_data, first_record)
        except:
            pass

        try:
            self.get_name_information_fieldset(object_data, first_record)
        except:
            pass

        return object_data

    def import_persons_institutions(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/persons2.xml"

        collection_path = "/home/andre/collectie-zm-v1/xml/persons.xml"
        prod_collection_path = "/var/www/zm-collectie-v2/xml/persons.xml"
        persons = "/var/www/zm-collectie-v1/xml/persons.xml"
        
        objects = self.get_zm_collection(prod_collection_path)

        total = len(list(objects))
        curr = 0

        for obj in list(objects)[:100]:
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text
                data = self.get_persons_institutions(priref, obj, True)
                self.create_persons_institutions(data)
            except:
                print "Object failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Object failed unexpected" %(timestamp)
                pass

        self.success = True
        return

    def test_books_integration(self, text):
        print "Books integration"
        print text

        return True

    def find_missing_exhibition(self, priref):
        folder = self.get_folder('nl/bezoek-het-museum/tentoonstellingen')

        for item in folder:
            exhibition = folder[item]
            if hasattr(exhibition, 'priref'):
                if exhibition.priref == priref:
                    return True

        return False

    def find_missing_exhibitions(self):
        collection_path = "/var/www/zm-collectie-v1/xml/Tentoonstellingen.xml"
        collection_path_test = "/Users/AG/Projects/collectie-zm/Tentoonstellingen.xml"
        objects = self.get_zm_collection(collection_path)

        total = len(list(objects))
        curr = 0

        missing_exhibitions = []

        for obj in list(objects):
            try:
                curr += 1
                print "Checking Exhibition %s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text
                if not self.find_missing_exhibition(priref):
                    missing_exhibitions.append(priref)
            except:
                raise

        print "Exhibitions missing:"
        print missing_exhibitions

        return True

    def move_image(self, name, src, dst):
        print "Moving image. [%s]\nsrc: %s\ndst: %s" %(name, src.absolute_url(), dst.absolute_url())
        try:
            api.content.move(source=src, target=dst)
        except:
            print "Error moving image. [%s]" %(name)
            raise
        return True

    def move_images_from_slideshow(self, slideshow, prive, LIMIT):
        list_images_to_move = list(slideshow)[LIMIT:]
        
        for img in list_images_to_move:
            self.move_image(img, slideshow[img], prive)

        return True

    def move_images(self):
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")

        LIMIT = 1
        total = len(all_objects)
        curr = 0

        #MAX = 10
        imported = 0

        objects_with_multiple_images = []

        for brain in list(all_objects):
            transaction.begin()
            curr += 1
            print "Moving %s / %s" %(str(curr), str(total))

            item = brain.getObject()
            if 'slideshow' in item:
                slideshow = item['slideshow']
                length = len(slideshow.contentItems())
                if length > LIMIT:
                    imported += 1
                    #print "%s / %s" %(str(imported), str(MAX))
                    objects_with_multiple_images.append(str(item.identification_identification_objectNumber))
                    folder = self.new_prive_folder(item)
                    if folder != False:
                        self.move_images_from_slideshow(slideshow, folder, LIMIT)
            transaction.commit()

            #if imported >= MAX:
            #    break

        print "\n\n#######\nReport\n#######\n"
        print "Imported: %s" %(str(imported))
        print "Number of objects with multiple images: %s\n" %(str(len(objects_with_multiple_images)))
        print "Detailed list of objects with multiple images: "
        print objects_with_multiple_images

        return True


    def new_prive_folder(self, item):

        if 'prive' in item:
            print "Item already contains prive folder."
            return item['prive']
        try:
            print "Create new prive folder"

            dirty_id = "prive"
            normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
            title = "Privé"
            type_name = "Folder"

            item.invokeFactory(
                type_name=type_name,
                id=normalized_id,
                title=title,
            )

            item.reindexObject()
            folder = item[str(normalized_id)]
            folder.reindexObject()

            return folder

        except:
            transaction.abort()
            print "Failed to create new prive folder."
            raise

        return False

    def create_prive_folder(self):
        print "Run script for [ Creating prive folders ]"

        self.folder_path = 'nl/test-prive-folder'.split('/')
        container = self.get_container()

        objects_with_multiple_images = []

        LIMIT = 1
        total = len(container)
        curr = 0

        for _id in container:
            curr += 1
            print "Check Object %s / %s" %(str(curr), str(total))

            item = container[_id]
            if item.portal_type == "Object":
                if 'slideshow' in item:
                    slideshow = item['slideshow']
                    length = len(slideshow.contentItems())
                    if length > LIMIT:
                        objects_with_multiple_images.append(str(item.identification_identification_objectNumber))
                        self.new_prive_folder(item)

        print "\n\n#######\nReport\n#######\n"
        print "Number of objects with multiple images: %s\n" %(str(len(objects_with_multiple_images)))
        print "Detailed list of objects with multiple images: "
        print objects_with_multiple_images
        return True

    def get_all_without_slideshow(self):
        container = self.get_container()
        catalog = getToolByName(container, 'portal_catalog')
        
        all_objects = catalog(portal_type='Object', Language="all")
        no_slideshow = []

        total = len(list(all_objects))
        curr = 0

        for obj in list(all_objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))
            item = obj.getObject()
            if hasattr(item, 'identification_identification_objectNumber'):
                if 'slideshow' not in item:
                    no_slideshow.append(str(item.identification_identification_objectNumber))
                    
                    lang = "nl"
                    item.invokeFactory(
                        type_name="Folder",
                        id=u'slideshow',
                        title='slideshow',
                    )   

                    folder = item['slideshow']
                    ILanguage(folder).set_language(lang)

                    print "Added slideshow %s" %(item.identification_identification_objectNumber)

                    try:
                        folder.portal_workflow.doActionFor(folder, "publish", comment="Slideshow content automatically published")
                        item.reindexObject()
                    except:
                        print "Cannot publish slideshow"
                        pass
               

        print no_slideshow
        print len(no_slideshow)

        return True

    def transform_objectname(self):
        #self.folder_path = "nl/test-prive-folder".split('/')

        #container = self.get_container()

        #imit = 100
        total = len(list(self.all_objects))
        curr = 0

        for obj in list(self.all_objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))

            transaction.begin()
            item = obj.getObject()
            if item.portal_type == "Object":
                
                if hasattr(item, 'identification_objectName_objectName'):
                    
                    old_categories = item.identification_objectName_objectName
                    new_cats = []

                    if old_categories != None:
                        for cat in old_categories:
                            term = cat['name']
                            notes = cat['notes']
                            if term != None:
                                new_cats.append({
                                    "name":[term.encode('ascii', 'ignore')],
                                    "notes":notes}
                                    )
                        if hasattr(item, 'identification_objectName_objectname'):
                            item.identification_objectName_objectname = new_cats

                    item.reindexObject()
                    item.reindexObject(idxs=['identification_objectName_objectname'])
                    print "Item updated: %s" %(item.absolute_url())

                    #if curr >= limit:
                    #    return True

            transaction.commit()

        return True

    def transform_dimensions_field(self):
        #self.folder_path = "nl/test-prive-folder".split('/')

        #container = self.get_container()

        #imit = 100
        total = len(list(self.all_objects))
        curr = 0

        for obj in list(self.all_objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))

            transaction.begin()
            item = obj.getObject()
            if item.portal_type == "Object":
                
                if hasattr(item, 'physicalCharacteristics_dimensions'):
                    
                    old_dimensions = item.physicalCharacteristics_dimensions
                    new_dimensions = []

                    if old_dimensions != None:
                        for cat in old_dimensions:
                            unit = cat['unit']
                            notes = cat['notes']
                            part = cat['part']
                            value = cat['value']
                            dimension = cat['dimension']
                            precision = cat['precision']

                            new_dimensions.append({
                                "dimension":[dimension.encode('ascii', 'ignore')],
                                "unit":[unit.encode('ascii', 'ignore')],
                                "notes":notes,
                                "part":part,
                                "value":value,
                                "precision": precision
                                }
                            )
                        if hasattr(item, 'physicalCharacteristics_dimensions'):
                            item.physicalCharacteristics_dimensions = new_dimensions

                    item.reindexObject()
                    item.reindexObject(idxs=['physicalCharacteristics_dimension'])
                    item.reindexObject(idxs=['physicalCharacteristics_dimensions_unit'])
                    print "Item updated: %s" %(item.absolute_url())

                    #if curr >= limit:
                    #    return True

            transaction.commit()

        return True

    def transform_objects_all(self):

        total = len(list(self.all_objects))
        curr = 0

        converter = Converter(self)

        for obj in list(self.all_objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))

            transaction.begin()
            item = obj.getObject()
          
            transaction.commit()

        return True

    def transform_productionRole(self):
        #self.folder_path = "nl/test-prive-folder".split('/')

        #container = self.get_container()

        #imit = 100
        total = len(list(self.all_objects))
        curr = 0

        for obj in list(self.all_objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))

            transaction.begin()
            item = obj.getObject()
            if item.portal_type == "Object":
                
                if hasattr(item, 'identification_objectName_objectName'):
                    
                    old_categories = item.identification_objectName_objectName
                    new_cats = []

                    if old_categories != None:
                        for cat in old_categories:
                            term = cat['name']
                            notes = cat['notes']
                            if term != None:
                                new_cats.append({
                                    "name":[term.encode('ascii', 'ignore')],
                                    "notes":notes}
                                    )
                        if hasattr(item, 'identification_objectName_objectname'):
                            item.identification_objectName_objectname = new_cats

                    item.reindexObject()
                    item.reindexObject(idxs=['identification_objectName_objectname'])
                    print "Item updated: %s" %(item.absolute_url())

                    #if curr >= limit:
                    #    return True

            transaction.commit()

        return True


    def transform_category(self):
        #self.folder_path = "nl/test-prive-folder".split('/')

        #container = self.get_container()


        #imit = 100
        total = len(list(self.all_objects))
        curr = 0

        for obj in list(self.all_objects):
            curr += 1
            print "%s / %s" %(str(curr), str(total))

            transaction.begin()
            item = obj.getObject()
            if item.portal_type == "Object":
                
                if hasattr(item, 'identification_objectName_objectCategory'):
                    
                    old_categories = item.identification_objectName_objectCategory
                    new_cats = []

                    if old_categories != None:
                        for cat in old_categories:
                            term = cat['term']
                            if term != None:
                                new_cats.append(term.encode('ascii', 'ignore'))
                        if hasattr(item, 'identification_objectName_category'):
                            item.identification_objectName_category = new_cats

                    item.reindexObject()
                    item.reindexObject(idxs=['identification_objectName_category'])
                    print "Item updated: %s" %(item.absolute_url())

                    #if curr >= limit:
                    #    return True

            transaction.commit()

        return True

    def find_record_by_object_number(self, xml, object_number):
        # Search in all records
        for record in xml:
            if record.find('object_number') != None:
                record_nr = record.find('object_number').text
                if record_nr.lower() == object_number.lower():
                    return record

        return None

    def create_alphabetic_folders(self):
        print "Create alphabetic folders"
        
        import string
        base_folder = "personen-en-instellingen"
        self.folder_path = base_folder.split('/')
        container = self.get_container()

        alphabet = list(string.ascii_uppercase)
        for letter in alphabet:
            transaction.begin()
            container.invokeFactory(type_name="Folder", id=letter, title=letter)
            created_folder = container[letter]
            created_folder.portal_workflow.doActionFor(created_folder, "publish", comment="Folder published")
            transaction.commit()

        return True


    def move_all_folders_content(self):
        total = 13041 + 2600 + 270
        curr = 0
        transaction.begin()
        origin = 'nl/intern/conserverings-behandelingen/conserverings-behandelingen'
        target = 'nl/intern/conserverings-behandelingen'
        self.move_folders(origin, target, total, curr)
        transaction.commit()

        curr = 2600
        transaction.begin()
        origin = 'nl/intern/archiefstukken/archiefstukken'
        target = 'nl/intern/archiefstukken'
        self.move_folders(origin, target, total, curr)
        transaction.commit()

        curr = 2870
        transaction.begin()
        origin = 'nl/intern/personen-en-instellingen/personen-en-instellingen'
        target = 'nl/intern/personen-en-instellingen'
        self.move_folders(origin, target, total, curr)
        transaction.commit()

        self.success = True
        return True

    def move_folders(self, origin, target, total, curr):

        origin = origin
        target = target

        origin_folder = self.get_folder(origin)
        target_folder = self.get_folder(target)

        total = total
        curr = curr
        for _id in origin_folder:
            #transaction.begin()
            curr += 1
            print "Moving %s / %s" %(str(curr), str(total))
            obj = origin_folder[_id]
            self.move_obj_folder(obj, target_folder)
            #transaction.commit()



        return True

    def move_persons_folder(self):
        import string
        base_folder = "personen-en-instellingen"

        self.folder_path = base_folder.split('/')
        container = self.get_container()

        alphabet = list(string.ascii_uppercase)
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
            
        total = len(container)
        curr = 0
        for _id in container:
            curr += 1
            print "Moving %s / %s" %(str(curr), str(total))
            transaction.begin()
            obj = container[_id]
            if obj.portal_type == "PersonOrInstitution":
                if obj.title:
                    title = obj.title
                    first_letter = title[0]
                    if first_letter.upper() in alphabet:
                        source = obj
                        target = self.get_folder('%s/%s' %(base_folder, first_letter.upper()))
                        self.move_obj_folder(source, target)
                    elif first_letter.upper() in numbers:
                        source = obj
                        target = self.get_folder('%s/0-9' %(base_folder))
                        self.move_obj_folder(source, target)
                    else:
                        source = obj
                        target = self.get_folder('%s/meer' %(base_folder))
                        self.move_obj_folder(source, target)
                        print "Unknown type - id: %s - letter: %s" %(str(_id), first_letter)
                else:
                    print "No title - %s" %(str(_id))

            transaction.commit()

        return True


    def start_migration(self):
        if self.portal is not None:
            self.is_en = False
            self.is_book = False
            self.use_books = True

            self.type_migrator = "updater"

            if self.type_migrator == "books":
                book_migrator = BookMigrator(self)
                book_migrator.start()

            elif self.type_migrator == "updater":
                updater = Updater(self)
                updater.start()

            elif self.type_migrator == "update_treatments":
                self.update_treatments()

            elif self.type_migrator == "converter":
                converter = Converter(self)
                converter.start()

            elif self.type_migrator == "relations":
                relations = Relations(self)
                relations.start()   

            elif self.type_migrator == "incomming_loans":
                print "#### incoming loans"
                self.folder_path = "nl/binnenkomende-bruiklenen/binnenkomende-bruiklenen".split('/')
                inloan_migrator = IncomingLoanMigrator(self)
                inloan_migrator.start()

            elif self.type_migrator == "objectentry":
                objectentry_migrator = ObjectEntryMigrator(self)
                objectentry_migrator.start()

            elif self.type_migrator == "archive":
                self.folder_path = "nl/archiefstukken/archiefstukken".split('/')
                archive_migrator = ArchiveMigrator(self)
                archive_migrator.start()
            else:
                #self.import_zm_collection_test()
                #converter = Converter(self)
                #converter.start()
                #print "Import persons!"
                #self.import_persons_institutions()
                self.move_all_folders_content()
                #self.create_alphabetic_folders()
                #self.move_persons_folder()


            ###
            ### EXTRAS
            ###


            #self.transform_linkedObjects_relatedObjects()
            #self.import_zm_outgoingloan_test()
            #print "#### archiefstukken"
            #self.folder_path = "nl/archiefstukken/archiefstukken".split('/')
            #archive_migrator = ArchiveMigrator(self)
            #archive_migrator.start()
            #self.transform_linkedObjects_relatedObjects()
            #print "No type of migrator selected"
            #self.folder_path = 'nl/uitgaande-bruiklenen/uitgaande-bruiklenen'.split('/')
            #self.import_zm_outgoingloan_test()
            #self.find_missing_exhibitions()
            #self.folder_path = 'nl/collectie/objecten-in-beheer-van-derden'.split('/')
            #self.transform_exhibition_example_institutions()
            #self.update_ex_dates()
            #self.transform_exhibition_example_institutions()
            #self.folder_path = "nl/test-folder".split("/")
            #self.import_zm_collection_test()
            ##self.import_persons_institutions()
            #self.import_zm_treatments()
            #self.update_images_metadata()
            #self.folder_path = 'nl/collectie'.split('/')
            #self.check_themes()
            #self.move_images()
            #self.check_visual_documentation()
            #self.check_images_in_plone()
            #self.transform_dimensions_field()
            #self.update_visual_metadata()
            #self.check_visual_documentation()
            #self.get_all_without_slideshow()
            #self.update_images_metadata()
            #self.folder_path = "nl/bezoek-het-museum/tentoonstellingen".split('/')
            #self.import_zm_exhibition_test()
            #self.import_zm_collection()
            #self.folder_path = "nl/conserverings-behandelingen/conserverings-behandelingen".split('/')
            #self.import_persons_institutions()
            #self.import_zm_treatments()

            #self.update_exhibitions()
            
            #self.import_zm_exhibition_test()
            
            #container = self.get_container()
            ###catalog = getToolByName(container, 'portal_catalog')
            #all_images = catalog(portal_type='Image', Language="all")

            #self.find_image_by_ref(all_images)

            #self.check_visual_documentation()
            #self.create_visual_documentation()
            #self.update_images_metadata()
            #self.transform_exhibition_example_linkedObjects()

            #self.verify_object_numbers()
            #self.check_zm_migration_plone()
            #self.check_themes()
            #self.check_zm_collection()
            #self.folder_path = 'nl/collectie/kunstnijverheid'.split('/')
            #self.update_zm_collection()

            #self.folder_path = 'nl/collectie/mode-en-streekdracht'.split('/')
            #self.update_zm_collection()

             
            #self.folder_path = 'nl/collectie/kunstnijverheid'.split('/')
            #self.divide_collection_by_folder()
            #self.import_zm_collection()
            #self.transform_exhibition_example_linkedObjects()
            #self.check_duplicated_objects()
            #self.delete_all_objects_container()
            #self.test_move_folder()
        else:
            if self.type_to_create == "api_test":
                self.migrate_test_api()
            elif self.type_to_create == "create_test":
                self.test_create_object()
            elif self.type_to_create == "create_test_add_images":
                self.test_create_object()
                self.test_add_image()
            elif self.type_to_create == "add_objects":
                #self.add_objects()
                self.add_new_objects()
                self.add_images()
            elif self.type_to_create == "add_objects_and_images":
                #self.add_objects()
                #self.add_images()
                pass
            elif self.type_to_create == "add_translations":
                self.add_translations()
            elif self.type_to_create == "add_objecten":
                self.add_new_objects()
                self.add_images()
            elif self.type_to_create == "update_objects":
                self.update_objects()
            elif self.type_to_create == "all":
                #self.add_objects()
                #self.add_images()
                #self.add_translations()
                pass
            elif self.type_to_create == 'add_test_objects':
                self.add_test_objects()
                self.add_images()
            elif self.type_to_create == 'add_crops':
                self.add_crops()
            elif self.type_to_create == 'transform_coins':
                self.transform_coins()
            elif self.type_to_create == 'fix_drawings':
                self.fix_drawings_from_api()
            elif self.type_to_create == 'add_view_to_coins':
                self.add_view_to_coins()
            elif self.type_to_create == "add_crops_and_views":
                self.add_crops()
                self.add_view_to_instruments()
            elif self.type_to_create == "add_view_to_instruments":
                self.add_view_to_instruments()



        
