#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""
from Acquisition import aq_parent, aq_inner
from z3c.relationfield.interfaces import IRelationList
from plone import api
import csv

from z3c.relationfield.schema import RelationList
from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice, ITextLine, IList, IText, IBool, IDatetime
from collective.z3cform.datagridfield.interfaces import IDataGridField
from plone.app.textfield.interfaces import IRichText
from collective.object.utils.interfaces import IListField

from plone.app.event.dx.behaviors import IEventBasic

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
from plone.event.interfaces import IEventAccessor
from collective.object.utils.interfaces import INotes

from z3c.relationfield import RelationValue
from zope import component

PORTAL_TYPE = "Book"

from .contenttypes_path import CONTENT_TYPES_PATH

if PORTAL_TYPE == "Object":
    from .core import CORE
    from .utils import *

elif PORTAL_TYPE == "Book":
    # Books
    from .book_utils import book_subfields_types as subfields_types
    from .book_utils import book_relation_types as relation_types
    from .book_core import BOOK_CORE as CORE

elif PORTAL_TYPE == "PersonOrInstitution":
    # Persons
    from .persons_utils import persons_subfields_types as subfields_types
    from .persons_utils import persons_relation_types as relation_types
    from .persons_core import PERSON_CORE as CORE

elif PORTAL_TYPE == "Exhibition":
    # Exhibitions
    from .exhibition_utils import exhibition_subfields_types as subfields_types
    from .exhibition_utils import exhibition_relation_types as relation_types
    from .exhibition_core import EXHIBITION_CORE as CORE

elif PORTAL_TYPE == "IncomingLoan":
    # Incoming loan
    from .loans_utils import loans_subfields_types as subfields_types
    from .loans_utils import loans_relation_types as relation_types
    from .loans_core import INCOMMING_CORE as CORE

elif PORTAL_TYPE == "OutgoingLoan":
    # Outgoing loan
    from .loans_utils import loans_subfields_types as subfields_types
    from .loans_utils import loans_relation_types as relation_types
    from .loans_core import OUTGOING_CORE as CORE

elif PORTAL_TYPE == "treatment":
    from .treatment_utils import treatment_subfields_types as subfields_types
    from .treatment_utils import treatment_relation_types as relation_types
    from .treatment_core import TREATMENT_CORE as CORE

elif PORTAL_TYPE == "ObjectEntry":
    from .objectentry_utils import objectentry_subfields_types as subfields_types
    from .objectentry_utils import objectentry_relation_types as relation_types
    from .objectentry_core import OBJECTENTRY_CORE as CORE

elif PORTAL_TYPE == "Resource":
    from .resource_utils import resource_subfields_types as subfields_types
    from .resource_utils import resource_relation_types as relation_types
    from .resource_core import RESOURCE_CORE as CORE

elif PORTAL_TYPE == "Taxonomie":
    from .taxonomy_utils import taxonomy_subfields_types as subfields_types
    from .taxonomy_utils import taxonomy_relation_types as relation_types
    from .taxonomy_core import TAXONOMY_CORE as CORE

elif PORTAL_TYPE == "Serial":
    from .serial_utils import serial_subfields_types as subfields_types
    from .serial_utils import serial_relation_types as relation_types
    from .serial_core import SERIAL_CORE as CORE

elif PORTAL_TYPE == "Article":
    from .article_utils import article_subfields_types as subfields_types
    from .article_utils import article_relation_types as relation_types
    from .article_core import ARTICLE_CORE as CORE

elif PORTAL_TYPE == "Audiovisual":
    from  .audiovisual_utils import audiovisual_subfields_types as subfields_types
    from  .audiovisual_utils import audiovisual_relation_types as relation_types
    from  .audiovisual_core import AUDIOVISUAL_CORE as CORE


DEBUG = False
RUNNING = True

class Updater:
    
    def __init__(self, APIMigrator):
        self.api = APIMigrator
        self.collection = []
        self.xml_root = []
        self.portal_type = PORTAL_TYPE

        self.schema = getUtility(IDexterityFTI, name=self.portal_type).lookupSchema()
        self.fields = getFieldsInOrder(self.schema)
        if self.portal_type == "Exhibition":
            self.exhibition_fields = getFieldsInOrder(IEventBasic)
            self.fields.extend(self.exhibition_fields)

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

                final_log = "[%s]__%s" %(str(timestamp), str(text).replace('\n', ''))
                list_log = final_log.split('__')

                if ".lref" not in text and "Warning" not in text and "STATUS" not in text:
                    
                    self.error_wr.writerow(list_log)

                if "Warning" in text or ".lref" in text or "STATUS" in text:
                    wr = csv.writer(self.warning_log_file, quoting=csv.QUOTE_ALL)
                    self.warning_wr.writerow(list_log)

            else:
                pass

    def get_field(self, fieldname):
        for name, field in self.fields:
            if name == fieldname:
                return field
        return None

    def fix_all_choices(self, obj):
        for name, field in self.fields:
            field_type = self.get_fieldtype_by_schema(field)
            if field_type == "datagridfield":
                obj_field = getattr(obj, name, None)
                if obj_field:
                    for line in obj_field:
                        for key in line:
                            if line[key] == "_No value":
                                line[key] = "No value"
                            elif line[key] == ['no value']:
                                line[key] = []
                            elif line[key] == 'False':
                                line[key] = False
                    setattr(obj, name, obj_field)
        return True


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

        self.error("%s__%s__Cannot find type of relation" %(self.object_number, self.xml_path))
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
        elif IBool.providedBy(field):
            type_field = 'bool'
        else:
            type_field = "unknown"

        return type_field

    def get_default_value_by_schema(self, field):
        type_field = " "
        if IRelationList.providedBy(field):
            type_field = ['no value']
        elif "ListField" in str(field):
            type_field = ['no value']
            self.datagrids[field.__name__] = False
        elif IChoice.providedBy(field):
            type_field = "_No value"
        elif ITextLine.providedBy(field):
            type_field = " "
        elif IList.providedBy(field):
            type_field = ['no value']
        elif IText.providedBy(field):
            type_field = " "
        elif IRichText.providedBy(field):
            type_field = " "
        elif IBool.providedBy(field):
            type_field = 'False'
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

        #current_value = []

        if objecttype_relatedto == "Taxonomie":
            if by_name:
                taxonomies = self.api.find_taxonomie_by_name(priref)
                if len(taxonomies) > 1:
                    taxonomy = taxonomies[0]
                    other_taxonomies = [str(p.priref) for p in taxonomies[1:]]
                    self.error("%s__%s__Relation with more than one result. First result: %s Other results: %s" %(str(self.object_number), str(self.xml_path), person.priref, str(other_taxonomies)))
                else:
                    if taxonomies:
                        taxonomy = taxonomies[0]
                    else:
                        taxonomy = None
                        self.error("%s__%s__Cannot create relation with content type Taxonomie with name '%s'" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))
                        return current_value
            else:
                taxonomy = self.api.find_taxonomie_by_priref(priref)
            
            if taxonomy:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(taxonomy)
                    relation_value = RelationValue(person_id)
                    for relation in current_value:
                        if relation.to_object.id == taxonomy.id:
                            self.warning("%s__%s__Taxonomie Relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(taxonomy)
            else:
                try:
                    self.error("%s__%s__Cannot create relation with content type Taxonomie with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                except:
                    self.error("%s__%s__Cannot create relation with content type Taxonomie with priref %s" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))

        
        elif objecttype_relatedto == "PersonOrInstitution":
            if by_name:
                persons = self.api.find_person_by_name(priref)
                if len(persons) > 1:
                    person = persons[0]
                    other_persons = [str(p.priref) for p in persons[1:]]
                    self.error("%s__%s__Relation with more than one result. First result: %s Other results: %s" %(str(self.object_number), str(self.xml_path), person.priref, str(other_persons)))
                else:
                    if persons:
                        person = persons[0]
                    else:
                        person = None
                        self.error("%s__%s__Cannot create relation with content type PersonOrInstitution with name '%s'" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))
                        return current_value
            else:
                person = self.api.find_person_by_priref(self.api.all_persons, priref)
            
            if person:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(person)
                    relation_value = RelationValue(person_id)
                    for relation in current_value:
                        if relation.to_object.id == person.id:
                            self.warning("%s__%s__PersonOrInstitution Relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(person)
            else:
                try:
                    self.error("%s__%s__Cannot create relation with content type PersonOrInstitution with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                except:
                    self.error("%s__%s__Cannot create relation with content type PersonOrInstitution with priref %s" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))

        elif objecttype_relatedto == "Object":
            obj = self.api.find_object(self.api.all_objects, priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    
                    if len(current_value) == 0:
                        current_value = []

                    for relation in current_value:
                        if relation.to_object.identification_identification_objectNumber == priref:
                            self.warning("%s__%s__Object relation already created with object number %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type Object with object number %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Exhibition":
            obj = self.api.find_exhibition_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Exhibition relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type Exhibition with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Archive":
            obj = self.api.find_archive_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Archive relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type Archive priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Serial":
            obj = self.api.find_serial_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Serial relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type Serial priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "treatment":
            obj = self.api.find_treatment_by_treatmentnumber(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Treatment relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type Treatment with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "OutgoingLoan":
            obj = self.api.find_outgoingloan_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Outgoing loan relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type OutgoingLoan with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "IncomingLoan":
            obj = self.api.find_incomingloan_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__IncomingLoan relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type IncomingLoan with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Article":
            obj = self.api.find_article_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Article relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type Article priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Bibliotheek":
            obj = self.api.find_bibliotheek_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Bibliotheek relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with an item from the Bibliotheek with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "ObjectEntry":
            obj = self.api.find_objectentry_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__ObjectEntry relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    current_value.append(obj)
            else:
                self.error("%s__%s__Cannot create relation with content type ObjectEntry with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                
        else:
            self.error("%s__%s__Relation type not available %s" %(str(self.object_number), str(self.xml_path), str(objecttype_relatedto)))


        return current_value

    def log_status(self, text):
        if text:
            timestamp = datetime.datetime.today().isoformat()
            text = text.encode('ascii', 'ignore')
            final_log = "[%s]__%s" %(str(timestamp), str(text))
            list_log = final_log.split('__')
            print final_log.replace('__', ' ')
            self.status_wr.writerow(list_log)
        else:
            return True

    def error(self, text="", object_number="", xml_path="", value=""):
        if text:
            self.log("%s%s" %("[ ERROR ]__", text))
        else:
            if not object_number:
                object_numnber = "None"
            if not xml_path:
                xml_path = "No path"
            if not value:
                value = "No value"
            value.encode('ascii', 'ignore')

            self.log("%s%s__%s__%s" %("[ ERROR ]__", object_number, xml_path, value))

        return True

    def warning(self, text="", object_number="", xml_path="", value=""):
        try:
            if text:
                self.log("%s%s" %("[ Warning ]__", text))
            else:
                if not object_number:
                    object_numnber = "None"
                if not xml_path:
                    xml_path = "No path"
                if not value:
                    value = "No value"
                value.encode('ascii', 'ignore')

                self.log("%s%s__%s__%s" %("[ Warning ]__", object_number, xml_path, value))

            return True
        except:
            return True


    def get_object_number(self, xml_record, portal_type=""):
        if portal_type != "Object":
            if portal_type == "IncomingLoan":
                return xml_record.find('loan_number').text
            else:
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

    def escape_empty_string(self, old_value):
        value = old_value
        for val in value:
            for k in val:
                if val[k] == " ":
                    val[k] = ""

        return value


    def update_dictionary_new(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        updated = False
        found = False

        # Check if first choice
        if subfield_type == "choice":
            if "taxonomy.rank" in self.xml_path:
                value = value
            elif type(value) == list:
                return current_value
            elif xml_element.get('option') != "" and xml_element.get('option') != None:
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    value = ""
            elif xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
                return current_value

        for line in current_value:
            if subfield in line:
                found = True

                if subfield_type == "choice":
                    if line[subfield] == '_No value' and value == "":
                        line[subfield] = 'No value'
                        updated = True
                        break
                    elif line[subfield] == '_No value' and value != "":
                        line[subfield] = value
                        updated = True
                        break
                    else:
                        # there's a value - try next line
                        pass
                elif subfield_type == "gridlist" or subfield_type == "relation":
                    if line[subfield] == ['no value'] and value == []:
                        line[subfield] = []
                        updated = True
                        break
                    elif line[subfield] == ['no value'] and value != []:
                        line[subfield] = value
                        updated = True
                        break
                    else:
                        # there's a value - try next line
                        pass
                elif subfield_type == "bool":
                    if line[subfield] == 'False':
                        line[subfield] = value
                        updated = True
                        break
                    else: 
                        # there's a value - try next line
                        pass
                else:
                    if line[subfield] == ' ':
                        line[subfield] = value
                        updated = True
                        break
                    else:
                        # there's a value - try next line
                        pass

        # Not found
        if not found:
            return current_value

        # Found
        if not updated:
            # create new row
            val = self.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value

    def update_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        default_test = " "
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
                        line[subfield] = '_No value'
                    else:
                        if subfield_type == "choice":
                            if type(value) != list:
                                line[subfield] = value
                            else:
                                line[subfield] = '_No value'
                        else:
                            if (subfield_type == "gridlist" and value == []) or (subfield_type == "gridlist" and value == ""):
                                line[subfield] = ['no value']
                            else:
                                line[subfield] = value
                    
                    updated = True
                    break

        if not found:
            return current_value

        if not updated:
            if subfield_type == "choice" and type(value) == list:
                value = "_No value"
            if (subfield_type == "gridlist" and value == []) or (subfield_type == "gridlist" and value == ['no value']):
                value = ['no value']
            val = self.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value

    def create_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        if subfield_type == "choice":
            if value == "":
                value = "No value"

            if "taxonomy.rank" in self.xml_path:
                value = value
            elif xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
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
                field_value = self.update_dictionary_new(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
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
                        value_split = field_val.split('-')
                        if len(value_split) == 2:
                            new_date = "%s-%s" %(field_val, "01")
                            datetime_value = datetime.datetime.strptime(new_date, "%Y-%m-%d")
                            value = datetime_value
                        else:
                            year = field_val
                            new_date = "%s-%s-%s" %(year, "01", "01")
                            datetime_value = datetime.datetime.strptime(new_date, "%Y-%m-%d")
                            value = datetime_value
                except:
                    self.error("%s__%s__Unable to create datetime value. %s"%(str(self.object_number), str(xml_path), str(field_val)))
                    return ""
            else:
                return ""

        elif field_type == "choice":
            if "taxonomy.rank" in self.xml_path:
                value = xml_element.get("value")
                if value:
                    return value.lower()
                else:
                    return ""

            if xml_element.get('language') == "0" and xml_element.get('language') != "" and xml_element.get('language') != None: # first entry
                value = self.api.trim_white_spaces(xml_element.text)
                if value == "":
                    return ""
                else:
                    return value

            elif xml_element.get("option") != "" and xml_element.get("option") != None: # empty entry
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    return ""
            elif xml_element.tag == "term":
                return xml_element.text
            else: # rest of the languages_keep the same value
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
                    self.error("%s__%s__Not possible to add value to the vocabulary %s"%(str(self.object_number), str(self.xml_path), str(new_value.encode('ascii','ignore'))))
                else:
                    try:
                        self.warning("%s__%s__Value already in vocabulary %s"%(str(self.object_number), str(self.xml_path), str(new_value.encode('ascii','ignore'))))
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
            elif objecttype_relatedto == "Taxonomie":
                linkref = xml_element.get('linkref')
                if not linkref:
                    linkdata = xml_element.get('linkdata')
                    if linkdata:
                        linkref = linkdata
                        by_name = True
                    else:
                        linkref = ""

            elif objecttype_relatedto == "Serial":
                linkref = xml_element.get('linkref')
                if not linkref:
                    linkdata = xml_element.get('linkdata')
                    linkref = linkdata
                            
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

            if "object.object_number" in self.xml_path:
                print "Number of values: "+str(len(value))
                if len(value) > 100:
                    value = value[:100]
                #print len(value)1
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
            self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))

        else:
            if ".lref" in xml_path:
                self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))
            else:
                if xml_path == "":
                    xml_path = xml_element.tag
                    if (xml_path == "record") or ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(object_number, xml_path, xml_element.text))
                else:
                    if ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(object_number, xml_path, xml_element.text))

        return True

    def update(self, xml_record, plone_object, object_number):
        
        # Iterate the whole tree
        for element in xml_record.iter():
            xml_path = self.get_xml_path(element)
            self.xml_path = xml_path
            self.write(xml_path, element, plone_object, object_number)

        return True

    def update_indexes(self, targets=[]):
        
        self.log("Updating indexes")

        for target in targets:
            if target == "Object":
                for obj in self.api.all_objects:
                    item = obj.getObject()
                    item.reindexObject(idxs=["identification_identification_objectNumber"])

                self.log("Objects updated!")

            elif target == "PersonOrInstitution":
                for obj in self.api.all_persons:
                    item = obj.getObject()
                    item.reindexObject(idxs=["person_priref"])

                self.log("PersonOrInstitution objects updated!")

            elif target == "Archive":
                for obj in self.api.all_archives:
                    item = obj.getObject()
                    item.reindexObject(idxs=["archive_priref"])

                self.log("Archive objects updated!")
            else:    
                self.log("Type %s does not have a method to be reindexed!" %(target))

        return True

    def get_required_field_by_type(self, xml_record):
        title = ""
        if self.portal_type == "Taxonomie":
            if xml_record.find("scientific_name") != None:
                title = xml_record.find("scientific_name").text

        elif self.portal_type == "Object":
            if xml_record.find("object_number") != None:
                title = xml_record.find("object_number").text
        else:
            self.error("Content type not supported to be created.")
        return title

    def get_title_by_type(self, xml_record):
        title = ""
        if self.portal_type == "Taxonomie":
            if xml_record.find("scientific_name") != None:
                title = xml_record.find("scientific_name").text

        elif self.portal_type == "Object":
            if xml_record.find("title") != None:
                title = xml_record.find("title").text
        else:
            self.error("Content type not supported to be created.")
        return title

    def create_object(self, xml_record):

        REQUIRED_FIELDS = {
            "Taxonomie": "taxonomicTermDetails_term_scientificName",
            "Object": "object_number"
        }
        required_field = REQUIRED_FIELDS[self.portal_type]

        container = self.api.get_folder('nl/collectie/collectie')
        title = self.get_title_by_type(xml_record)
        required_field_value = self.get_required_field_by_type(xml_record)

        dirty_id = "%s %s"%(str(self.object_number), str(title.encode('ascii', 'ignore')))
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

        container.invokeFactory(
            type_name=self.portal_type,
            id=normalized_id,
            title=title
        )

        created_object = container[str(normalized_id)]
        created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")
        setattr(created_object, required_field, required_field_value)

        return created_object

    def reindex_all_taxonomies(self):
        index = "taxonomicTermDetails_term_rank"

        curr = 0
        for tax in self.api.all_taxonomies[:400]:
            curr += 1 
            print curr
            obj = tax.getObject()
            obj.reindexObject(idxs=["taxonomicTermDetails_term_rank"])

        return True


    def reindex_all_persons(self):
        index = "nameInformation_name_nameType_type"

        curr = 0
        transaction.begin()
        for person in self.api.all_persons:
            curr += 1 
            print curr
            obj = person.getObject()
            obj.reindexObject(idxs=[index])
        transaction.commit()

        return True


    def create_large_pages(self):
        total = 100000
        curr = 0
        for i in range(100):
            curr += 1
            print "%s / %s" %(str(curr), str(total))
            transaction.begin()
            
            container = self.api.get_folder('nl/test-large')
            dirty_id = "page %s" %(str(i+1))
            normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

            container.invokeFactory(
                type_name='Document',
                id=normalized_id,
                title=dirty_id
            )
            transaction.commit()

        return True


    def init_log_files(self):
        timestamp = datetime.datetime.today().isoformat()

        self.error_path = "/var/www/zm-collectie-v3/logs/error_%s_%s.csv" %(self.portal_type, str(timestamp))
        self.error_path_dev = "/Users/AG/Projects/collectie-zm/logs/error_%s_%s.csv" %(self.portal_type, str(timestamp))
        
        self.warning_path = "/var/www/zm-collectie-v3/logs/warning_%s_%s.csv" %(self.portal_type, str(timestamp))
        self.warning_path_dev = "/Users/AG/Projects/collectie-zm/logs/warning_%s_%s.csv" %(self.portal_type, str(timestamp))
        
        self.status_path_dev = "/Users/AG/Projects/collectie-zm/logs/status_%s_%s.csv" %(self.portal_type, str(timestamp))
        self.status_path = "/var/www/zm-collectie-v3/logs/status_%s_%s.csv" %(self.portal_type, str(timestamp))

        if self.dev:
            self.error_log_file = open(self.error_path_dev, "w+")
            self.warning_log_file = open(self.warning_path_dev, "w+")
            self.status_log_file = open(self.status_path_dev, "w+")
        else:
            self.error_log_file = open(self.error_path, "w+")
            self.warning_log_file = open(self.warning_path, "w+")
            self.status_log_file = open(self.status_path, "w+")

        self.error_wr = csv.writer(self.error_log_file, quoting=csv.QUOTE_ALL)
        self.warning_wr = csv.writer(self.warning_log_file, quoting=csv.QUOTE_ALL)
        self.status_wr = csv.writer(self.status_log_file, quoting=csv.QUOTE_ALL)

        
    def start(self):
        self.dev = False

        #self.create_large_pages()
        #self.api.divide_collection_by_folder()
        #return True

        self.init_log_files()
    
        #
        # Choose collection XML
        #
        collection_xml = CONTENT_TYPES_PATH[self.portal_type]['prod']['total']
        self.collection, self.xml_root = self.api.get_zm_collection(collection_xml)

        #
        # Generate field types
        #
        self.generate_field_types()

        total = len(list(self.collection))
        curr = 0
        limit = 0
        create_new = False

        for xml_record in list(self.collection):
            try:
                curr += 1
                transaction.begin()
                self.object_number = ""
                object_number = self.get_object_number(xml_record, self.portal_type)
                if object_number:
                    self.object_number = object_number

                    if self.object_number == "11210":
                        plone_object = self.api.find_item_by_type(object_number, self.portal_type)
                        if plone_object:
                            if self.portal_type == "Exhibition":
                                plone_object.start = ""
                                plone_object.end = ""
                                plone_object.whole_day = True

                            self.object_number = str(object_number)
                            self.generate_field_types()
                            self.log_status("! STATUS !__Updating [%s] %s / %s" %(str(object_number), str(curr), str(total)))
                            self.update(xml_record, plone_object, object_number)
                            self.log_status("! STATUS !__Updated [%s] %s / %s" %(str(object_number), str(curr), str(total)))
                            self.log_status("! STATUS !__URL: %s" %(str(plone_object.absolute_url())))
                            self.fix_all_choices(plone_object)

                            if self.portal_type == "Exhibition":
                                if plone_object.start:
                                    IEventBasic(plone_object).start = plone_object.start
                                if plone_object.end:
                                    IEventBasic(plone_object).end = plone_object.end
                            
                            plone_object.reindexObject() 
                            transaction.commit()
                            break
                        else:
                            if create_new:
                                created_object = self.create_object(xml_record)
                                self.update(xml_record, created_object, object_number)
                                self.fix_all_choices(created_object)
                                created_object.reindexObject()
                                self.log_status("%s__ __New object created with type %s."%(str(object_number), str(self.portal_type)))
                                self.log_status("! STATUS !__URL: %s" %(str(created_object.absolute_url())))
                            else:
                                self.error("%s__ __Object is not found on Plone with priref/object_number."%(str(object_number)))

                        

                        
                else:
                    self.error("%s__ __Cannot find object number/priref in XML record"%(str(curr)))

                transaction.commit()
            except Exception, e:
                self.error(" __ __An unknown exception ocurred. %s" %(str(e)))
                raise

        self.api.success = True
        return True


