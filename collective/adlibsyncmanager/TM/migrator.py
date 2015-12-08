#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""

import re, AccessControl, transaction, time, sys, datetime, os, csv, unicodedata, csv, pytz, string, fnmatch, urllib2, urllib  
from Acquisition import aq_parent, aq_inner
from z3c.relationfield.interfaces import IRelationList, IRelationValue
from plone import api 
from zope.intid.interfaces import IIntIds
from z3c.relationfield.schema import RelationList
from zope import component
from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice, ITextLine, IList, IText, IBool, IDatetime
from plone.app.textfield.interfaces import IRichText
from zc.relation.interfaces import ICatalog
from lxml import etree
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime
from plone.i18n.normalizer import idnormalizer
from Testing.makerequest import makerequest
from plone.dexterity.utils import createContentInContainer
from collective.leadmedia.utils import addCropToTranslation
from collective.leadmedia.utils import imageObjectCreated
from plone.app.textfield.value import RichTextValue
from plone.event.interfaces import IEventAccessor
from z3c.relationfield import RelationValue
import glob

from .teylers_contenttypes_path import CONTENT_TYPES_PATH
from .teylers_contenttypes_path import IMAGES_HD_PATH

from .teylers_core import CORE
from .teylers_utils import subfields_types, relation_types
from .log_files_path import LOG_FILES_PATH

RESTRICTIONS = []
SUPPORTED_ENV = ['dev', 'prod']
UPLOAD_IMAGES = True
FOLDER_PATH = "nl/collectie/munten"

ENV = "prod"
DEBUG = False
RUNNING = True

class Migrator:
    
    def __init__(self, Updater):
        self.updater = Updater
        self.portal_type = "Object"
        self.updater.portal_type = "Object"
        self.object_type = "coins"
        self.updater.RUNNING = RUNNING
        self.updater.DEBUG = DEBUG
        self.updater.CORE = CORE
        self.updater.subfields_types = subfields_types
        self.updater.relation_types = relation_types
        self.log_files_path = LOG_FILES_PATH
        self.images_hd_path = IMAGES_HD_PATH
        self.list_images_in_hd = []

        self.schema = getUtility(IDexterityFTI, name=self.portal_type).lookupSchema()
        self.fields = getFieldsInOrder(self.schema)


        self.updater.schema = self.schema
        self.updater.fields = self.fields
        self.updater.field_types = {}
        self.updater.datagrids = {}
        self.updater.xml_path = ""
        self.updater.is_tm = True

    ## LOGS
    def log(self, text=""):
        self.updater.log(text)

    def log_images(self, text="", use_timestamp=True):
        if text:
            timestamp = datetime.datetime.today().isoformat()
            text = text.encode('ascii', 'ignore')
            if not use_timestamp:
                final_log = "%s" %(str(text))
            else:
                final_log = "[%s]__%s" %(str(timestamp), str(text))
            
            list_log = final_log.split('__')
            print final_log.replace('__', ' ')
            self.images_wr.writerow(list_log)
        else:
            return True

    def log_status(self, text="", use_timestamp=True):
        self.updater.log_status(text, use_timestamp)

    def error(self, text=""):
        self.updater.error(text)

    def warning(self, text=""):
        self.updater.warning(text)

    def init_log_files(self):

        self.list_images_in_hd = glob.glob(IMAGES_HD_PATH[ENV]['path'])        
        self.error_path = self.get_log_path('error', ENV)
        self.warning_path = self.get_log_path('warning', ENV)
        self.status_path = self.get_log_path('status', ENV)
        self.log_images_path = self.get_log_path('images', ENV)

        self.error_log_file = open(self.error_path, "w+")
        self.warning_log_file = open(self.warning_path, "w+")
        self.status_log_file = open(self.status_path, "w+")
        self.images_log_file = open(self.log_images_path, "w+")

        self.error_wr = csv.writer(self.error_log_file, quoting=csv.QUOTE_ALL)
        self.warning_wr = csv.writer(self.warning_log_file, quoting=csv.QUOTE_ALL)
        self.status_wr = csv.writer(self.status_log_file, quoting=csv.QUOTE_ALL)
        self.images_wr = csv.writer(self.images_log_file, quoting=csv.QUOTE_ALL)

        self.updater.error_log_file = self.error_log_file
        self.updater.warning_log_file = self.warning_log_file
        self.updater.status_log_file = self.status_log_file

        self.updater.error_wr = self.error_wr
        self.updater.warning_wr = self.warning_wr
        self.updater.status_wr = self.status_wr

    ## GETS
    def get_priref(self, xml_record):
        if xml_record.find('priref') != None:
            return xml_record.find('priref').text
        else:
            return ""

    def get_log_path(self, log_type='error', env="dev"):
        path = ""

        if ENV in SUPPORTED_ENV:
            timestamp = datetime.datetime.today().isoformat()
            path = self.log_files_path[log_type][ENV] % (self.portal_type, timestamp)
        else:
            print "#### Environment '%s' for log file is unsupported. ####" %(str(server))

        return path

    def get_collection(self):
        collection_xml = CONTENT_TYPES_PATH[self.portal_type][self.object_type][ENV]['total']
        self.collection, self.xml_root = self.updater.api.get_tm_collection(collection_xml)

        self.updater.collection = self.collection
        self.updater.xml_root = self.xml_root

    ## FINDS
    def find_object_by_priref(self, priref):
        if priref:
            brains = self.updater.api.portal_catalog(object_priref=priref, portal_type="Object")
            if brains:
                brain = brains[0]
                obj = brain.getObject()
                if getattr(obj, 'priref', None) == priref:
                    return obj
                else:
                    return None
            else:
                return None
        else:
            return None
    
    ## CORE
    def write(self, xml_path, xml_element, plone_object, priref):

        plone_fieldname = self.updater.check_dictionary(xml_path)
        
        if plone_fieldname:
            plone_fieldroot = plone_fieldname.split('-')[0]
            has_field = hasattr(plone_object, plone_fieldroot)
           
            if has_field:
                current_value = getattr(plone_object, plone_fieldroot)
                field_type = self.updater.get_type_of_field(plone_fieldroot)
                value = self.transform_all_types(xml_element, field_type, current_value, xml_path, plone_fieldname)
                self.updater.setattribute(plone_object, plone_fieldroot, field_type, value)
            else:
                self.error("Field not available in Plone object: %s" %(plone_fieldroot))

        ## Ignored tags
        elif plone_fieldname == "":
            self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))

        else:
            if ".lref" in xml_path:
                self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))
            else:
                if xml_path == "":
                    xml_path = xml_element.tag
                    if (xml_path == "record") or ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(priref, xml_path, xml_element.text))
                else:
                    if ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(priref, xml_path, xml_element.text))

        return True

    def update(self, xml_record, plone_object, priref):
        for element in xml_record.iter():
            xml_path = self.updater.get_xml_path(element)
            self.xml_path = xml_path
            self.write(xml_path, element, plone_object, priref)
        return True

    # Handle datagridfield 
    def handle_datagridfield(self, current_value, xml_path, xml_element, plone_fieldname):
        subfield = self.updater.get_subfield(plone_fieldname)
        plone_fieldroot = plone_fieldname.split('-')[0]
        subfield_type = self.updater.get_type_of_subfield(xml_path)

        if not self.updater.datagrids[plone_fieldroot]:
            current_value = []
            self.updater.datagrids[plone_fieldroot] = True
        else:
            self.updater.datagrids[plone_fieldroot] = True

        if current_value == None:
            current_value = []

        length = len(current_value)
        field_value = None

        if subfield:
            if length:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.updater.update_dictionary_new(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
            else:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.updater.create_dictionary(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
        else:
            self.error("Badly formed CORE dictionary for repeatable field: %s" %(plone_fieldname))

        return field_value

    def transform_all_types(self, xml_element, field_type, current_value, xml_path, plone_fieldname):

        # Text
        if field_type == "text":
            return self.updater.api.trim_white_spaces(xml_element.text)

        elif field_type == "rich-text":
            parent = xml_element.getparent()
            if parent:
                if parent.find('label.type') != None:
                    if parent.find('label.type').get('option') == "WEBTEXT":
                        text = xml_element.text
                        value = RichTextValue(text, 'text/html', 'text/html')
                        return value
                    else:
                        value = RichTextValue('', 'text/html', 'text/html')
                else:
                    value = RichTextValue('', 'text/html', 'text/html')
                return RichTextValue('', 'text/html', 'text/html')
            else:
                return RichTextValue('', 'text/html', 'text/html')

        elif field_type == "datagridfield":
            value = self.handle_datagridfield(current_value, xml_path, xml_element, plone_fieldname)
        # Unknown
        else:
            value = None
            self.error("Unkown type of field for fieldname %s" %(plone_fieldname))

        return value

    def create_object(self, priref, xml_record, folder_path='nl/'):
        created_object = None

        folder_path = folder_path
        container = self.updater.api.get_folder(folder_path)

        title = self.updater.get_title_by_type(xml_record)
        object_number = self.updater.get_required_field_by_type(xml_record)
        if not title and object_number:
            #fallback object number
            title = object_number
        elif not title and not object_number:
            #fallback priref
            title = priref
        elif not title:
            title = ""
        else:
            title = title


        dirty_id = "%s %s"%(str(object_number), str(title.encode('ascii', 'ignore')))
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        container.invokeFactory(
            type_name=self.portal_type,
            id=normalized_id,
            title=title
        )

        created_object = container[str(normalized_id)]
        setattr(created_object, 'priref', priref)

        return created_object

    def convert_image_name(self, image_name):
        #
        # TMNK_06362-v.jpg -> TMNK 06362a.jpg
        # TMNK_06362-k.jpg -> TMNK 06362b.jpg 
        #

        # verify if convertible
        if ("-v.jpg" in image_name) or ("-k.jpg" in image_name):
            pass
        else:
            return image_name

        new_image_name = ""

        # Convert to A
        if "-v.jpg" in image_name:
            new_image_name = image_name.replace("-v.jpg", "a.jpg")
            copy_image_name = new_image_name
            if "aa.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('aa.jpg', 'a.jpg')
            elif "ba.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('ba.jpg', 'a.jpg')


            if 'TMNK_' in new_image_name:
                final_image_name = copy_image_name.replace('TMNK_', 'TMNK ')
                return final_image_name
            else:
                return image_name

        # Convert to B
        elif ("-k.jpg" in image_name):
            new_image_name = image_name.replace("-k.jpg", "b.jpg")
            copy_image_name = new_image_name

            if "ab.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('ab.jpg', 'b.jpg')
            elif "bb.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('bb.jpg', 'b.jpg')

            if 'TMNK_' in new_image_name:
                final_image_name = copy_image_name.replace('TMNK_', 'TMNK ')
                return final_image_name
            else:
                return image_name
        else:
            return image_name

        if new_image_name:
            return new_image_name
        else:
            return image_name

    def find_image_in_hd(self, image_name):
        for image in self.list_images_in_hd:
            if image_name.lower() in image.lower():
                return image
        return None

    def add_image(self, image_name, path, priref, plone_object):
        if path:
            if 'slideshow' in plone_object:
                container = plone_object['slideshow']
                dirty_id = image_name
                normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                try:
                    image_file = open(path, "r")
                    image_data = image_file.read()
                    try:
                        img = NamedBlobImage(
                            data=image_data
                        )
                        image_file.close()
                        container.invokeFactory(type_name="Image", id=normalized_id, title=image_name, image=img)
                        self.log_status("! STATUS !__Created image [%s] for priref: %s" %(image_name, priref))
                    except:
                        self.log_images("%s__%s__%s"%(priref, image_name, "Error while creating Image content type."))
                        pass
                except:
                    self.log_images("%s__%s__%s"%(priref, path, "Cannot open image file from HD."))
                    pass
            else:
                self.log_images("%s__%s__%s"%(priref, image_name, "Cannot upload image to HD. Slideshow folder is not found."))
        else:
            self.log_images("%s__%s__%s"%(priref, image_name, "Cannot find image in HD."))

    def upload_images(self, priref, plone_object, xml_record):
        
        if xml_record.findall('Reproduction') != None:
            for reproduction in xml_record.findall('Reproduction'):
                if reproduction.find('reproduction.reference') != None:
                    if reproduction.find('reproduction.reference').find('reference_number') != None:
                        reference_number = reproduction.find('reproduction.reference').find('reference_number').text
                        reference_split = reference_number.split("\\")
                        if reference_split:
                            image_name = reference_split[-1]
                            new_image_name = self.convert_image_name(image_name)
                            path = self.find_image_in_hd(new_image_name)
                            self.add_image(new_image_name, path, priref, plone_object)
                        else:
                            path = self.find_image_in_hd(reference_number)
                            self.add_image(reference_number, path, priref, plone_object)
                    else:
                        self.log_images("%s__%s__%s"%(priref, '', "Cannot find image reference in XML."))

        return True

    def create_description_field(self, plone_object):
        description = ""
        authors = getattr(plone_object,'creator', None)
        periods = getattr(plone_object,'object_dating', None)
        
        if authors:
            field = authors[0]
            author = self.updater.utils.create_production_field(field)
        else:
            author = ""

        if periods:
            field = periods[0]
            period = self.updater.utils.create_prod_dating_field(field)
        else:
            period = ""

        if author and period:
            description = "%s, %s" %(author, period)
        elif author:
            description = "%s" %(author)
        elif period:
            description = "%s" %(period)
        
        return description

    def generate_special_fields(self, plone_object):
        object_title = getattr(plone_object, 'title', '')
        setattr(plone_object, 'object_title', object_title)
        description = self.create_description_field(plone_object)
        setattr(plone_object, 'description', description)
        return True

    def import_record(self, priref, plone_object, xml_record, create_if_not_found=True):
            if plone_object:
                self.updater.generate_field_types()
                self.updater.empty_fields(plone_object, True)
                self.update(xml_record, plone_object, priref)
                self.updater.fix_all_choices(plone_object)
                self.generate_special_fields(plone_object)

                plone_object.reindexObject() 
                is_new = False
                if not create_if_not_found:
                    is_new = True
                return True, is_new
            else:
                if create_if_not_found:
                    object_created = self.create_object(priref, xml_record, FOLDER_PATH)
                    layout = object_created.getLayout()
                    if layout != "double_view":
                        object_created.setLayout("double_view")

                    imported, is_new = self.import_record(priref, object_created, xml_record, False)
                    return object_created, True
                else:
                    self.error("%s__ __Object is not found on Plone with priref."%(str(priref))) 
                    return False, False

    ## START
    def start(self):
        self.init_log_files()
        self.get_collection()

        curr, limit = 0, 0
        total = len(list(self.collection))

        for xml_record in list(self.collection):
            try:
                curr += 1
                transaction.begin()

                priref = self.get_priref(xml_record)
                self.updater.object_number = priref
                if priref in ['8000069', '8006953', '8000670']:
                    if priref:

                        plone_object = self.find_object_by_priref(priref)
                        imported, is_new = self.import_record(priref, plone_object, xml_record)
                        if imported:
                            # Log status
                            if is_new:
                                self.log_status("! STATUS !__Created [%s] %s / %s" %(str(priref), str(curr), str(total)))
                                self.log_status("! STATUS !__URL: %s" %(str(imported.absolute_url())))
                                if UPLOAD_IMAGES:
                                    self.upload_images(priref, imported, xml_record)
                            else:
                                self.log_status("! STATUS !__Updated [%s] %s / %s" %(str(priref), str(curr), str(total)))
                                self.log_status("! STATUS !__URL: %s" %(str(plone_object.absolute_url())))
                        else:
                            pass
                    else:
                        self.error("%s__ __Cannot find priref in XML record"%(str(curr)))

                transaction.commit()

            except Exception, e:
                transaction.abort()
                self.error(" __ __An unknown exception ocurred. %s" %(str(e)))
                raise

        return True







