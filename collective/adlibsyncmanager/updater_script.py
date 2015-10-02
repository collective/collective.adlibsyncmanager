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
from zope.schema.interfaces import IChoice, ITextLine, IList, IText, IBool, IDatetime
from collective.z3cform.datagridfield.interfaces import IDataGridField
from plone.app.textfield.interfaces import IRichText
from collective.object.utils.interfaces import IListField

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

from collective.object.utils.interfaces import INotes

from z3c.relationfield import RelationValue
from zope import component

PORTAL_TYPE = "PersonOrInstitution"

# Objects

if PORTAL_TYPE == "Object":
    from .core import CORE
    from .utils import *

elif PORTAL_TYPE == "Book":
    # Books
    from .book_utils import book_subfields_types as subfields_types
    from .book_utils import book_relation_types as relation_types
    from .book_core import BOOK_CORE as CORE

# Persons
elif PORTAL_TYPE == "PersonOrInstitution":
    from .persons_utils import persons_subfields_types as subfields_types
    from .persons_utils import persons_relation_types as relation_types
    from .persons_core import PERSON_CORE as CORE

elif PORTAL_TYPE == "Exhibition":
    # Exhibitions
    from .exhibition_utils import exhibition_subfields_types as subfields_types
    from .exhibition_utils import exhibition_relation_types as relation_types
    from .exhibition_core import EXHIBITION_CORE as CORE


DEBUG = False
RUNNING = True

class Updater:
    
    def __init__(self, APIMigrator):
        self.api = APIMigrator
        self.collection = []
        self.xml_root = []
        self.portal_type = "PersonOrInstitution"

        self.schema = getUtility(IDexterityFTI, name=self.portal_type).lookupSchema()
        self.fields = getFieldsInOrder(self.schema)

        self.field_types = {}
        self.datagrids = {}
        self.object_number = ""
        self.xml_path = ""
        self.dev = False

    def log(self, text=""):

        if DEBUG:
            if text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')
                final_log = "[%s] %s" %(str(timestamp), str(text))
            else:
                pass
        elif RUNNING:
            if "STATUS" in text or "ERROR" in text or "Warning" in text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')

                final_log = "[%s] %s" %(str(timestamp), str(text))
                print final_log

                if ".lref" not in text and "Warning" not in text and "STATUS" not in text:
                    self.error_log_file.write(final_log+"\n")

                if "Warning" in text or ".lref" in text or "STATUS" in text:
                    self.warning_log_file.write(final_log+"\n")

            else: # do not log
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
        elif IDatetime.providedBy(field):
            type_field = "date"
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
            type_field = "No value"
        elif ITextLine.providedBy(field):
            type_field = " "
        elif IList.providedBy(field):
            type_field = []
        elif IText.providedBy(field):
            type_field = " "
        elif IRichText.providedBy(field):
            type_field = " "
        elif IBool.providedBy(field):
            type_field = False
        elif IDatetime.providedBy(field):
            type_field = None
        else:
            type_field = " "

        return type_field

    def generate_field_types(self):
        for name, field in self.fields:
            type_field = self.get_fieldtype_by_schema(field)
            self.field_types[name] = type_field

        self.field_types['title'] = "text"
        self.field_types['description'] = 'text'

    def create_relation(self, current_value, objecttype_relatedto, priref, grid=False, by_name=False):
        if grid:
            current_value = []
        
        if objecttype_relatedto == "PersonOrInstitution":
            if by_name:
                persons = self.api.find_person_by_name(priref)
                if len(persons) > 1:
                    person = persons[0]
                    other_persons = [str(p.priref) for p in persons[1:]]
                    self.error("%s - %s - Relation with more than one result - First result: %s - Other results: %s" %(str(self.object_number), str(self.xml_path), person.priref, str(other_persons)))
                else:
                    if persons:
                        person = persons[0]
                    else:
                        person = None
            else:
                person = self.api.find_person_by_priref(self.api.all_persons, priref)
            
            if person:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(person)
                    relation_value = RelationValue(person_id)
                    for relation in current_value:
                        if relation.to_object.id == person.id:
                            self.warning("%s - %s - PersonOrInstitution Relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(person)
            else:
                try:
                    self.error("%s - %s - Cannot find PersonOrInstitution %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))
                except:
                    self.error("%s - %s - Cannot find PersonOrInstitution %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))

        elif objecttype_relatedto == "Object":
            obj = self.api.find_object(self.api.all_objects, priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.identification_identification_objectNumber == priref:
                            self.warning("%s - %s - Object relation already created with object number %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s - %s - Cannot find Object %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Exhibition":
            obj = self.api.find_exhibition_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s - %s - Exhibition relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s - %s - Cannot find Exhibition %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Archive":
            obj = self.api.find_archive_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s - %s - Archive relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s - %s - Cannot find Archive %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

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
                self.error("%s - %s - Cannot find Treatment %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "OutgoingLoan":
            obj = self.api.find_outgoingloan_by_priref(priref)
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
                self.error("%s - %s - Cannot find Outgoing Loan %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "IncomingLoan":
            obj = self.api.find_incomingloan_by_priref(priref)
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
                self.error("%s - %s - Cannot find Incoming Loan %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Article":
            obj = self.api.find_article_by_priref(priref)
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
                self.error("%s - %s - Cannot find Article %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Bibliotheek":
            obj = self.api.find_bibliotheek_by_priref(priref)
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
                self.error("%s - %s - Cannot find Bibliotheek object %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "ObjectEntry":
            obj = self.api.find_objectentry_by_priref(priref)
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
                self.error("%s - %s - Cannot find ObjectEntry %s in Plone" %(str(self.object_number), str(self.xml_path), str(priref)))
                

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

    def warning(self, text="", object_number="", xml_path="", value=""):
        if text:
            self.log("%s%s" %("[ Warning ] ", text))
        else:
            if not object_number:
                object_numnber = "None"
            if not xml_path:
                xml_path = "No path"
            if not value:
                value = "No value"
            value.encode('ascii', 'ignore')

            self.log("%s%s - %s - %s" %("[ Warning ] ", object_number, xml_path, value))

        return True


    def get_object_number(self, xml_record, portal_type=""):
        if portal_type != "Object":
            if xml_record.find('priref') != None:
                return xml_record.find('priref').text
        else:
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
        default_test = ""
        if subfield_type == "choice":
            if xml_element.get('option') != "" and xml_element.get('option') != None:
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    value = ""
            elif xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
                return current_value

        updated = False
        found = False

        for line in current_value:
            if subfield in line:
                found = True
                if line[subfield] == default_test or line[subfield] == [] or line[subfield] == 'No value' or line[subfield] == False:
                    if line[subfield] == 'No value' and value == "":
                        line[subfield] = 'No value'
                    else:
                        if subfield_type == "choice":
                            if type(value) != list:
                                line[subfield] = value
                            else:
                                line[subfield] = 'No value'
                        else:
                            line[subfield] = value
                    
                    updated = True
                    break

        if not found:
            return current_value

        if not updated:
            if subfield_type == "choice" and type(value) == list:
                value = "No value"
            val = self.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value

    def create_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        if subfield_type == "choice":
            if xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
                return current_value

        new_value = self.get_schema_gridfield(plone_fieldroot)

        if subfield not in new_value:
            return current_value
            
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

    def transform_all_types(self, xml_element, field_type, current_value, xml_path, plone_fieldname, grid=False):

        # Text
        if field_type == "text":
            return self.api.trim_white_spaces(xml_element.text)

        elif field_type == "date":
            field_val = self.api.trim_white_spaces(xml_element.text)
            if field_val:
                try:
                    try: 
                        datetime_value = datetime.datetime.strptime(field_val, "%Y-%m-%d")
                        value = datetime_value
                    except:
                        year = field_val
                        new_date = "%s-%s-%s" %(year, "01", "01")
                        datetime_value = datetime.datetime.strptime(new_date, "%Y-%m-%d")
                        value = datetime_value
                except:
                    self.error("Unable to create datetime value.", str(self.object_number), str(xml_path), str(field_val))
                    return ""
            else:
                return ""

        elif field_type == "choice":
            if xml_element.get('language') == "0" and xml_element.get('language') != "" and xml_element.get('language') != None: # first entry
                value = self.api.trim_white_spaces(xml_element.text)
                if value == "":
                    return "No value"
                else:
                    return value

            elif xml_element.get("option") != "" and xml_element.get("option") != None: # empty entry
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    return "No value"

            else: # rest of the languages
                return current_value
        
        # Vocabulary
        elif field_type == "list":
            if current_value != None:
                new_value = self.api.trim_white_spaces(xml_element.text)
                try:
                    if new_value not in current_value:
                        if new_value:
                            current_value.append(self.api.trim_white_spaces(xml_element.text))
                except:
                    self.error("%s - %s - Not possible to add value to the vocabulary - %s"%(str(self.object_number), str(self.xml_path), str(new_value.encode('ascii','ignore'))))
                else:
                    try:
                        self.warning("%s - %s - Value already in vocabulary - %s"%(str(self.object_number), str(self.xml_path), str(new_value.encode('ascii','ignore'))))
                    except:
                        pass
                value = current_value
            else:
                value = [self.api.trim_white_spaces(xml_element.text)]

        elif field_type == "gridlist":
            new_value = self.api.trim_white_spaces(xml_element.text)
            if new_value != None and new_value != "":
                value = [new_value]
            else:
                value = []

        # Create relation type
        elif field_type == "relation":
            value = []
            by_name = False
            objecttype_relatedto, grid = self.get_objecttype_relation(plone_fieldname)
            if objecttype_relatedto == "Object":
                linkref = xml_element.get('linkdata')
                if not linkref:
                    linkref = xml_element.get('linkterm')
                    if not linkref:
                        if xml_element.find('object_number') != None:
                            linkref = xml_element.find('object_number').text
                        else:
                            linkref = ""

            elif objecttype_relatedto == "PersonOrInstitution":
                linkref = xml_element.get('linkref')
                if not linkref:
                    linkdata = xml_element.get('linkdata')
                    if linkdata:
                        linkref = linkdata
                        by_name = True
                    else:
                        linkref = ""
                            
            elif objecttype_relatedto == "treatment":
                linkref = xml_element.text
            else:
                linkref = xml_element.get('linkref')

            value = self.create_relation(current_value, objecttype_relatedto, linkref, grid, by_name)

        elif field_type == "bool":
            if xml_element.text == "x":
                return True
            else:
                return False

        elif field_type == "datagridfield":
            value = self.handle_datagridfield(current_value, xml_path, xml_element, plone_fieldname)
        
        # Unknown
        else:
            value = None
            self.error("Unkown type of field for fieldname %s" %(plone_fieldname))

        return value

    def setattribute(self, plone_object, plone_fieldname, field_type, value):
        if value != None:
            if field_type == "choice" and (value == "" or value == " "):
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

        elif plone_fieldname == "":
            self.warning("%s - %s - Tag was ignored. %s" %(object_number, xml_path, xml_element.text))

        else:
            self.error("%s - %s - Tag not found in dictionary. %s" %(object_number, xml_path, xml_element.text))

        return True

    def update(self, xml_record, plone_object, object_number):
        
        # Iterate the whole tree
        for element in xml_record.iter():
            xml_path = self.get_xml_path(element)
            self.xml_path = xml_path
            self.write(xml_path, element, plone_object, object_number)

        return True

    def start(self):

        self.dev = False

        person_single = "/Users/AG/Projects/collectie-zm/single-persons-v2.xml"
        collection_path = "/Users/AG/Projects/collectie-zm/single-exhibition-v01.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/single-book-v02.xml"
        test = "/Users/AG/Projects/collectie-zm/objectsall2.xml"
        collection_total = "/var/www/zm-collectie-v2/xml/objectsall.xml"
        book_total = "/var/www/zm-collectie-v2/xml/booksall.xml"
        persons_total = "/var/www/zm-collectie-v2/xml/persons.xml"
        exhibitions_total = "/var/www/zm-collectie-v2/xml/Tentoonstellingen.xml"

        timestamp = datetime.datetime.today().isoformat()
        self.error_path = "/var/www/zm-collectie-v2/logs/error_%s_%s.log" %(self.portal_type, str(timestamp))
        self.error_path_dev = "/Users/AG/Projects/collectie-zm/logs/error_%s_%s.log" %(self.portal_type, str(timestamp))
        self.warning_path = "/var/www/zm-collectie-v2/logs/warning_%s_%s.log" %(self.portal_type, str(timestamp))
        self.warning_path_dev = "/Users/AG/Projects/collectie-zm/logs/warning_%s_%s.log" %(self.portal_type, str(timestamp))
        
        
        collection_xml = persons_total
        if self.dev:
            collection_xml = persons_total
            self.error_log_file = open(self.error_path_dev, "w+")
            self.warning_log_file = open(self.warning_path_dev, "w+")
        else:
            collection_xml = persons_total
            self.error_log_file = open(self.error_path, "w+")
            self.warning_log_file = open(self.warning_path, "w+")
        

        self.collection, self.xml_root = self.api.get_zm_collection(collection_xml)
        self.generate_field_types()

        total = len(list(self.collection))
        curr = 0
        limit = 0

        for xml_record in list(self.collection):
            try:
                curr += 1
                transaction.begin()
                object_number = self.get_object_number(xml_record, self.portal_type)
                if object_number:
                    plone_object = self.api.find_item_by_type(object_number, self.portal_type)
                    if plone_object:
                        self.object_number = str(object_number)
                        self.generate_field_types()
                        self.log("! STATUS ! Updating [%s] - %s / %s" %(str(object_number), str(curr), str(total)))
                        self.update(xml_record, plone_object, object_number)
                        self.log("! STATUS ! Updated [%s] - %s / %s" %(str(object_number), str(curr), str(total)))
                        self.log("URL: %s" %(str(plone_object.absolute_url())))
                        plone_object.reindexObject()
                        print str(plone_object.absolute_url())
                    else:
                        self.error("Object is not found on Plone.")
                else:
                    self.error("Cannot find object number/priref in XML record")

                transaction.commit()
            except Exception, e:
                self.error("An unknown exception ocurred. %s" %(str(e)))
                raise

        self.api.success = True
        return True


