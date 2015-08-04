#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""
from Acquisition import aq_parent, aq_inner
from z3c.relationfield.interfaces import IRelationList
from plone import api

from z3c.relationfield.schema import RelationList
from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice, ITextLine, IList, IText
from collective.z3cform.datagridfield.interfaces import IDataGridField
from plone.app.textfield.interfaces import IRichText
from collective.object.utils.interfaces import IListField

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

from collective.object.utils.interfaces import INotes

from z3c.relationfield import RelationValue
from zope import component
from .core import CORE
from .utils import *


DEBUG = False
RUNNING = True

class Updater:
    
    def __init__(self, APIMigrator):
        self.api = APIMigrator
        self.collection = []
        self.xml_root = []
        self.schema = getUtility(IDexterityFTI, name='Object').lookupSchema()
        self.fields = getFieldsInOrder(self.schema)
        self.field_types = {}
        self.datagrids = {}

    def log(self, text=""):
        if DEBUG:
            if text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')
                print "[%s] %s" %(str(timestamp), str(text))
            else:
                pass
        elif RUNNING:
            if "STATUS" in text or "ERROR" in text or "warning" in text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')
                print "[%s] %s" %(str(timestamp), str(text))
            else:
                pass

    def get_field(self, fieldname):
        for name, field in self.fields:
            if name == fieldname:
                return field
        return None

    def get_subfield(self, plone_fieldname):
        split_name = plone_fieldname.split('-')
        if len(split_name) > 1:
            return split_name[1]
        else:
            return None

    def get_schema_gridfield(self, fieldname):
        field = self.get_field(fieldname)
        gridfield_schema = {}
        schema = field.value_type.schema
        for name, field in getFieldsInOrder(schema):
            gridfield_schema[name] = self.get_default_value_by_schema(field)

        return gridfield_schema


    def get_objecttype_relation(self, plone_fieldname):

        relation_type = ""
        for name, field in self.fields:
            if name == plone_fieldname:
                try:
                    portal_type = field.value_type.source.selectable_filter.criteria['portal_type'][0]
                    return portal_type, False
                except:
                    if plone_fieldname in relation_types:
                        return relation_type[plone_fieldname], True
                    else:
                        self.error("Cannot get portal_type of relation.")
        
        if not relation_type:
            if plone_fieldname in relation_types:
                return relation_types[plone_fieldname], True

        self.error("Cannot find type of relation")
        return None, None

    def get_type_of_subfield(self, plone_fieldname):
        if plone_fieldname in subfields_types:
            return subfields_types[plone_fieldname]
        else:
            return "text"

    def get_type_of_field(self, plone_fieldname):
        if plone_fieldname in self.field_types:
            return self.field_types[plone_fieldname]
        else:
            return None

    def get_fieldtype_by_schema(self, field):
        type_field = ""
        if IRelationList.providedBy(field):
            type_field = "relation"
        elif "ListField" in str(field):
            type_field = "datagridfield"
            self.datagrids[field.__name__] = False
        elif IChoice.providedBy(field):
            type_field = "choice"
        elif ITextLine.providedBy(field):
            type_field = "text"
        elif IList.providedBy(field):
            type_field = "list"
        elif IText.providedBy(field):
            type_field = "text"
        elif IRichText.providedBy(field):
            type_field = "text"
        else:
            type_field = "unknown"

        return type_field

    def get_default_value_by_schema(self, field):
        type_field = " "
        if IRelationList.providedBy(field):
            type_field = []
        elif "ListField" in str(field):
            type_field = []
            self.datagrids[field.__name__] = False
        elif IChoice.providedBy(field):
            type_field = " "
        elif ITextLine.providedBy(field):
            type_field = " "
        elif IList.providedBy(field):
            type_field = []
        elif IText.providedBy(field):
            type_field = " "
        elif IRichText.providedBy(field):
            type_field = " "
        else:
            type_field = " "

        return type_field

    def generate_field_types(self):
        for name, field in self.fields:
            type_field = self.get_fieldtype_by_schema(field)
            self.field_types[name] = type_field

        self.field_types['title'] = "text"
        self.field_types['description'] = 'text'

    def create_relation(self, current_value, objecttype_relatedto, priref, grid=False):
        if grid:
            current_value = []
        current_value = []
        
        if objecttype_relatedto == "PersonOrInstitution":
            person = self.api.find_person_by_priref(self.api.all_persons, priref)
            if person:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(person)
                    relation_value = RelationValue(person_id)
                    for relation in current_value:
                        if relation.to_object.priref == priref:
                            self.error("Relation already created.")
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(person)
            else:
                self.error("Cannot find person %s in Plone" %(str(priref)))
        elif objecttype_relatedto == "Object":
            obj = self.api.find_object(self.api.all_objects, priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.identification_identification_objectNumber == priref:
                            self.error("Relation already created.")
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)

        elif objecttype_relatedto == "Exhibition":
            obj = self.api.find_exhibition_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.priref == priref:
                            self.error("Relation already created.")
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("Cannot find Exhibition %s in Plone" %(str(priref)))

        elif objecttype_relatedto == "Archive":
            obj = self.api.find_archive_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.priref == priref:
                            self.error("Relation already created.")
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("Cannot find Archive %s in Plone" %(str(priref)))

        elif objecttype_relatedto == "treatment":
            obj = self.api.find_treatment_by_treatmentnumber(priref)
            if obj:
                if not grid:
                    current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("Cannot find Treatment %s in Plone" %(str(priref)))
        else:
            self.error("Relation type not available %s" %(str(objecttype_relatedto)))


        return current_value

    def error(self, text="", object_number="", xml_path="", value=""):
        
        if text:
            self.log("%s%s" %("[ ERROR ] ", text))
        else:
            if not object_number:
                object_numnber = "None"
            if not xml_path:
                xml_path = "No path"
            if not value:
                value = "No value"
            value.encode('ascii', 'ignore')

            self.log("%s%s - %s - %s" %("[ ERROR ] ", object_number, xml_path, value))

        return True

    def get_object_number(self, xml_record):
        if xml_record.find('object_number') != None:
            return xml_record.find('object_number').text
        return None
    
    def get_xml_path(self, xml_element):
        xml_path = re.sub("\[[^]]*\]", '', self.xml_root.getpath(xml_element).replace("/adlibXML/recordList/record", "").replace("/", "-"))
        if len(xml_path) > 0:
            if xml_path[0] == "-":
                if len(xml_path) > 1:
                    xml_path = xml_path[1:]

        return xml_path

    def check_dictionary(self, xml_path):
        if xml_path in CORE.keys():
            return CORE[xml_path]
        return False

    def update_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        if subfield_type == "choice":
            if xml_element.get('language') != "0":
                return current_value

        updated = False
        for line in current_value:
            if subfield in line:
                if line[subfield] == " " or line[subfield] == []:
                    line[subfield] = value
                    updated = True
                    break

        if not updated:
            val = self.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value

    def create_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        if subfield_type == "choice":
            if xml_element.get('language') != "0":
                return current_value

        new_value = self.get_schema_gridfield(plone_fieldroot)
        new_value[subfield] = value
        current_value.append(new_value)

        return current_value

    # Handle datagridfield 
    def handle_datagridfield(self, current_value, xml_path, xml_element, plone_fieldname):
        subfield = self.get_subfield(plone_fieldname)
        plone_fieldroot = plone_fieldname.split('-')[0]
        subfield_type = self.get_type_of_subfield(xml_path)

        if not self.datagrids[plone_fieldroot]:
            current_value = []
            self.datagrids[plone_fieldroot] = True
        else:
            self.datagrids[plone_fieldroot] = True

        if current_value == None:
            current_value = []

        length = len(current_value)
        field_value = None

        if subfield:
            if length:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.update_dictionary(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
            else:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.create_dictionary(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
        else:
            self.error("Badly formed CORE dictionary for repeatable field: %s" %(plone_fieldname))

        return field_value

    def transform_all_types(self, xml_element, field_type, current_value, xml_path, plone_fieldname):
        
        # Text
        if field_type == "text":
            return self.api.trim_white_spaces(xml_element.text)

        elif field_type == "choice":
            if xml_element.get('language') == "0":
                return self.api.trim_white_spaces(xml_element.text)
            else:
                return current_value
        
        # Vocabulary
        elif field_type == "list":
            if current_value != None:
                new_value = self.api.trim_white_spaces(xml_element.text)
                if new_value not in current_value:
                    current_value.append(self.api.trim_white_spaces(xml_element.text))
                else:
                    self.error("Value already in vocabulary.")
                value = current_value
            else:
                value = [self.api.trim_white_spaces(xml_element.text)]

        elif field_type == "gridlist":
            new_value = self.api.trim_white_spaces(xml_element.text)
            if new_value != None:
                value = [new_value]
            else:
                value = []

        # Create relation type
        elif field_type == "relation":
            value = []
            objecttype_relatedto, grid = self.get_objecttype_relation(plone_fieldname)
            if objecttype_relatedto == "Object":
                linkref = xml_element.get('linkdata')
                if not linkref:
                    linkref = xml_element.get('linkterm')
            elif objecttype_relatedto == "treatment":
                linkref = xml_element.text
            else:
                linkref = xml_element.get('linkref')

            value = self.create_relation(current_value, objecttype_relatedto, linkref, grid)


        elif field_type == "datagridfield":
            value = self.handle_datagridfield(current_value, xml_path, xml_element, plone_fieldname)

        # Unknown
        else:
            value = None
            self.error("Unkown type of field for fieldname %s" %(plone_fieldname))
        return value

    def setattribute(self, plone_object, plone_fieldname, field_type, value):
        if value != None:
            if field_type == "choice" and value == "":
                value = "No value"
            setattr(plone_object, plone_fieldname, value)
        else:
            self.error("Value to be set is None. field: %s" %(plone_fieldname))

    def write(self, xml_path, xml_element, plone_object, object_number):

        plone_fieldname = self.check_dictionary(xml_path)
        
        if plone_fieldname:
            plone_fieldroot = plone_fieldname.split('-')[0]
            has_field = hasattr(plone_object, plone_fieldroot)
            if has_field:
                current_value = getattr(plone_object, plone_fieldroot)
                field_type = self.get_type_of_field(plone_fieldroot)

                value = self.transform_all_types(xml_element, field_type, current_value, xml_path, plone_fieldname)

                self.setattribute(plone_object, plone_fieldroot, field_type, value)
            else:
                self.error("Field not available in Plone object: %s" %(plone_fieldroot))

        elif len(xml_element.getchildren()):
            pass

        else:
            object_number = object_number
            value = getattr(xml_element, 'text', 'No value')
            if plone_fieldname != "":
                self.error("", object_number, xml_path, value)

        return True

    def update(self, xml_record, plone_object, object_number):
        
        # Iterate the whole tree
        for element in xml_record.iter():
            xml_path = self.get_xml_path(element)
            self.write(xml_path, element, plone_object, object_number)

        return True

    def update_indexes(self):
        self.log("Updating indexes")
        #for obj in self.api.all_objects:
        #    item = obj.getObject()
        #    item.reindexObject(idxs=["identification_identification_objectNumber"])

        for obj in self.api.all_persons:
            item = obj.getObject()
            item.reindexObject(idxs=["person_priref"])

        self.log("Persons updated!")

        for obj in self.api.all_archives:
            item = obj.getObject()
            item.reindexObject(idxs=["archive_priref"])

        self.log("Updated!")

    def start(self):
        collection_path = "/Users/AG/Projects/collectie-zm/single-object-v33.xml"
        collecion_path_prod = "/var/www/zm-collectie-v2/xml/single-object-v33.xml"
        test = "/Users/AG/Projects/collectie-zm/objectsall2.xml"
        collection_total = "/var/www/zm-collectie-v2/xml/objectsall.xml"

        self.collection, self.xml_root = self.api.get_zm_collection(collecion_path_prod)
        self.generate_field_types()

        total = len(list(self.collection))
        curr = 0

        limit = 0

        for xml_record in list(self.collection):
            curr += 1
           
            transaction.begin()
            
            object_number = self.get_object_number(xml_record)
            if object_number:
                plone_object = self.api.find_object(self.api.all_objects, object_number)
                if plone_object:
                    self.generate_field_types()
                    self.log("! STATUS ! Updating [%s] - %s / %s" %(str(object_number), str(curr), str(total)))
                    self.update(xml_record, plone_object, object_number)
                    self.log("! STATUS ! Updated [%s] - %s / %s" %(str(object_number), str(curr), str(total)))
                else:
                    self.error("Object is corrupt.")
            else:
                self.error("Cannot find object number in XML record")

            transaction.commit()

        self.api.success = True

        return True


