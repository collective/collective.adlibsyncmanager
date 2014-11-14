"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""

from lxml import etree
import urllib2, urllib
from plone.namedfile.file import NamedBlobImage
from plone.multilingual.interfaces import ITranslationManager

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

#from collective.leadmedia.utils import addCropToTranslation
from plone.app.textfield.value import RichTextValue

ORGANIZATION = ""
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured"
API_REQUEST_ALL_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(%s)&xmltype=structured"

XML_PATH = ""

TEST_OBJECT = 0

# Folder where the images are (Do not forget to add a trailing slash)
class ObjectItem:
    def __init__(self):
        self.title = ""
        self.description = ""
        self.object_number = ""
        self.production = ""
        self.creator = ""
        self.dirty_id = ""
        self.tags = []

class APIMigrator:
    
    def __init__(self, portal, folder, image_folder, type_to_create="art_list", set_limit=0, art_list=[]):
        self.portal = portal
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
                print "Item '%s' already exists" % (dirty_id)
                transaction.commit()
                return True

            if not hasattr(container, normalized_id):
                print "New object found. Adding: %s" % (dirty_id)

                container.invokeFactory(
                    type_name="object",
                    id=normalized_id,
                    title=obj.title,
                    description=obj.description,
                    object_number=obj.object_number,
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
            self.skipped += 1
            print "Skipped item: " + dirty_id

        self.success = result
        return result

    def add_image(self, image_name, path, object_id):
        
        container = self.get_container()
        dirty_id = image_name

        normalized_id = idnormalizer.normalize(dirty_id)

        try:
            if hasattr(container, object_id):
                object_item = container[str(object_id)]
                if hasattr(object_item, 'slideshow'):
                    slideshow = object_item['slideshow']
                    if not hasattr(slideshow, normalized_id):
                        print "Adding image to slideshow %s" % (normalized_id)
                        image_file = open(path, "r")
                        image_data = image_file.read()
                        img = NamedBlobImage(
                            data=image_data
                        )
                        image_file.close()
                        slideshow.invokeFactory(type_name="Image", id=normalized_id, title=image_name, image=img)
                    else:
                        print "Image %s already exists, skipping"%dirty_id
                        return True

                    transaction.commit()
                    
                    object_item.reindexObject()
                    object_item.reindexObject(idxs=["hasMedia"])
                    object_item.reindexObject(idxs=["leadMedia"])

                    result = True
                    return result
                else:
                    print "Unexpected error adding image to slideshow folder.", sys.exc_info()[1]
                    transaction.abort()
                    raise
                    return False
        except:
            transaction.abort()
            print "Unexpected error adding image to slideshow folder.", sys.exc_info()[1]
            raise
            return False

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
                current_object.object_number = object_number

                self.create_object(current_object)

        return

    def transform_creator_name(self, name):
        if name != "":
            name_without_year = re.sub(r'\([^)]*\)', '', name)
            name_separated = name_without_year.split(',')
            if len(name_separated) > 1:
                real_name = name_separated[1] + name_separated[0]
                return real_name
            else:
                return name_separated[0]
        else:
            return name

    def create_object_dirty_id(self, object_number, title, creator):
        dirty_id = "%s %s %s" % (object_number, title, creator)
        return dirty_id

    def create_object_description(self, creator, production):
        
        if production != "":
            description = "%s, %s" % (creator, production)
        else:
            description = "%s" % (creator)

        return description

    def create_object_production(self, production_date_start, production_date_end):
        if production_date_end == production_date_start:
            production = production_date_end
        elif production_date_end == None:
            production = "%s" % (production_date_start)
        elif production_date_start == None:
            production = "%s" % (production_date_end)
        else:
            production = "%s - %s" % (production_date_start, production_date_end)

        return production

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
        current_object.object_number = object_number
        current_object.production = production
        current_object.creator = creator
        current_object.dirty_id = self.create_object_dirty_id(object_number, title, creator)
        current_object.description = self.create_object_description(creator, production_date_end)
        current_object.text = current_object.description
        current_object.tags = tags

        return current_object
      
    def add_images(self):
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
                    object_number = record.find('object_number').text

                    current_object = self.create_object_data(record)
                    dirty_id = current_object.dirty_id

                    imagefilename = object_number.upper().replace(' ', "-")
                    imagefilename = imagefilename + ".jpg"
                    path = self.image_folder + imagefilename 

                    object_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                    self.add_image(imagefilename, path, object_id)
                    
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

        try:
            if hasattr(container, normalized_id) and normalized_id != "":
                self.skipped += 1
                print "Item '%s' already exists" % (dirty_id)
                transaction.commit()
                return True

            if not hasattr(container, normalized_id):
                print "New object found. Adding: %s" % (dirty_id)

                text = RichTextValue(obj['text'], 'text/plain', 'text/html')

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
                    text=text
                    )

                # Get object and add tags
                created_object = container[str(normalized_id)]
                
                if len(obj['tags']) > 0:
                    created_object.setSubject(obj['tags'])

                created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                created_object.reindexObject()
                created_object.reindexObject(idxs=["hasMedia"])
                created_object.reindexObject(idxs=["leadMedia"])
                
                transaction.commit()

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
            self.skipped += 1
            print "Skipped item: " + dirty_id

        self.success = result
        return result

    def transform_d(self, dimension_type):
        if dimension_type == "hoogte":
            return "h"
        elif dimension_type == "breedte":
            return "w"
        elif dimension_type == "gewicht":
            return "kg"

    def create_dimension_field(self, dimension_data):
        if len(dimension_data['dimensions']) > 0:

            all_dimensions = dimension_data['dimensions']
            part = all_dimensions[0]['part']
            
            dimensions = ""
            number = 0
            for d in all_dimensions:
                number += 1
                if number != len(all_dimensions):
                    dimensions += " %s %s %s x" % (self.transform_d(d['type']), d['value'], d['unit'])
                else:
                    dimensions += " %s %s %s" % (self.transform_d(d['type']), d['value'], d['unit'])

            dimension = "%s:%s" % (part, dimensions)
            return dimension
        else:
            return ""


    def fetch_object_api(self, priref):
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
            "tags": []
        }

        object_temp_data = {
            "production_date_end": "",
            "production_date_start": "",
            "dimensions": []
        }

        if first_record.find('object_number') != None:
            object_data['object_number'] = first_record.find('object_number').text

        if first_record.find('Object_name') != None:
            if first_record.find('Object_name').find('object_name') != None:
                object_data['object_type'] = first_record.find('Object_name').find('object_name').text
        
        if first_record.find('Title') != None:
            if first_record.find('Title').find('title').find('value') != None:
                object_data['title'] = first_record.find('Title').find('title').find('value').text
        
        if first_record.find('Technique') != None:
            if first_record.find('Technique').find('technique') != None:
                object_data['technique'] = first_record.find('Technique').find('technique').text

        if first_record.find('Material') != None:
            if first_record.find('Material').find('material') != None:
                object_data['material'] = first_record.find('Material').find('material').text
        
        if first_record.find('priref') != None:
            object_data['priref'] = first_record.find('priref').text

        if first_record.find('Production') != None:
            if first_record.find('Production').find('creator') != None:
                object_data['artist'] = first_record.find('Production').find('creator').text
        
        if first_record.find('Production_date') != None:
            if first_record.find('Production_date').find('production.date.start') != None:
                object_temp_data['production_date_start'] = first_record.find('Production_date').find('production.date.start').text  
            if first_record.find('Production_date').find('production.date.end') != None:
                object_temp_data['production_date_end'] = first_record.find('Production_date').find('production.date.end').text
        
        if first_record.find('Label') != None:
            if first_record.find('Label').find('label.text') != None:
                object_data["text"] = first_record.find('Label').find('label.text').text

        if first_record.findall('Dimension') != None:
            for d in first_record.findall('Dimension'):
                if d.find('dimension.part') != None:
                    new_dimension = {
                        "part": "",
                        "value": "",
                        "type": "",
                        "unit": ""
                    }

                    new_dimension['part'] = d.find('dimension.part').text

                    if d.find('dimension.value') != None:
                        new_dimension['value'] = d.find('dimension.value').text
                    if d.find('dimension.type') != None:
                        new_dimension['type'] = d.find('dimension.type').text
                    if d.find('dimension.unit') != None:
                        new_dimension['unit'] = d.find('dimension.unit').text
                    
                    object_temp_data['dimensions'].append(new_dimension)
            

        if len(first_record.findall('Content_subject')) > 0:
            for tag in first_record.findall('Content_subject'):
                if tag.find('content.subject') != None:
                    object_data['tags'].append(tag.find('content.subject').text)

        object_data['artist'] = self.transform_creator_name(object_data['artist'])
        object_data['dimension'] = self.create_dimension_field(object_temp_data)
        object_data['dating'] = self.create_object_production(object_temp_data['production_date_start'], object_temp_data['production_date_end'])
        object_data['description'] = self.create_object_description(object_data["artist"], object_temp_data['production_date_end'])
        object_data['dirty_id'] = self.create_object_dirty_id(object_data['object_number'], object_data['title'], object_data['artist'])

        self.create_new_object(object_data)
        return

    def add_translations(self):
        number = 0
        container = self.get_container()

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
                    object_number = record.find('object_number').text
                    
                    current_object = self.create_object_data(record)
                    dirty_id = current_object.dirty_id
                    normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                    
                    if hasattr(container, normalized_id):
                        transaction.begin()
                        
                        item = container[str(normalized_id)]
                        ITranslationManager(item).add_translation('en')

                        item_trans = ITranslationManager(item).get_translation('en')
                        item_trans.title = item.title
                        item_trans.text = item.text
                        item_trans.description = item.description
                        item_trans.object_number = item.object_number
                        item_trans.object_type = item.object_type
                        item_trans.artist = item.artist
                        item_trans.dating = item.dating
                        item_trans.dimension = item.dimension
                        item_trans.material = item.material
                        item_trans.technique = item.technique
                        item_trans.setSubject(current_object.tags)
                        item_trans.portal_workflow.doActionFor(item_trans, "publish", comment="Item published")

                        if hasattr(item, 'slideshow'):
                            
                            slideshow = item['slideshow']
                            ITranslationManager(slideshow).add_translation('en')
                            slideshow_trans = ITranslationManager(slideshow).get_translation('en')
                            slideshow_trans.title = slideshow.title
                            slideshow_trans.portal_workflow.doActionFor(slideshow_trans, "publish", comment="Slideshow published")

                            for sitem in slideshow:
                                if slideshow[sitem].portal_type == "Image":
                                    ITranslationManager(slideshow[sitem]).add_translation('en')
                                    trans = ITranslationManager(slideshow[sitem]).get_translation('en')
                                    trans.image = slideshow[sitem].image

                                    #addCropToTranslation(slideshow[sitem], trans)

                        item_trans.reindexObject()
                        item_trans.reindexObject(idxs=["hasMedia"])
                        item_trans.reindexObject(idxs=["leadMedia"])
                        transaction.commit()

                        print "Added translation for %s" % (normalized_id)
                    
                    number += 1
                    if number >= self.set_limit:
                        self.success = True
                        return


        self.success = True
        return

    def convert_object_number_priref(self, object_number):
        quoted_query = urllib.quote(object_number)
        api_request = API_REQUEST_URL % (quoted_query)
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

    def add_new_objects(self):
        number = 0
        for obj in self.art_list:
            # Convert object number to priref
            priref = self.convert_object_number_priref(obj)
            
            if priref != "":
                self.fetch_object_api(priref)
            else:
                self.skipped += 1
                print "Skipped item: " + obj

            number += 1
            if number >= self.set_limit:
                self.success = True
                return

    def start_migration(self):
        if self.portal is not None:
            if self.type_to_create == "api_test":
                self.migrate_test_api()
            elif self.type_to_create == "create_test":
                self.test_create_object()
            elif self.type_to_create == "create_test_add_images":
                self.test_create_object()
                self.test_add_image()
            elif self.type_to_create == "add_objects":
                self.add_objects()
            elif self.type_to_create == "add_objects_and_images":
                self.add_objects()
                self.add_images()
            elif self.type_to_create == "add_translations":
                self.add_translations()
            elif self.type_to_create == "new_test":
                self.add_new_objects()
                self.add_images()
            elif self.type_to_create == "all":
                self.add_objects()
                self.add_images()
                self.add_translations()
        else:
            print "Portal is NONE!"



        