#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""

import string
from Acquisition import aq_parent, aq_inner
from z3c.relationfield.interfaces import IRelationList, IRelationValue
from plone import api
import csv
import pytz
from zope.intid.interfaces import IIntIds

from z3c.relationfield.schema import RelationList
from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice, ITextLine, IList, IText, IBool, IDatetime
from collective.z3cform.datagridfield.interfaces import IDataGridField
from plone.app.textfield.interfaces import IRichText
from collective.object.utils.interfaces import IListField
from zc.relation.interfaces import ICatalog
from zope.component import getUtility

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
from collective.imageReference.imageReference import IImageReference

from z3c.relationfield import RelationValue
from zope import component
from collective.object.object import IObject
from collective.dexteritytextindexer.utils import searchable

DEBUG = False
RUNNING = True

class SyncUtils:
    
    def __init__(self, APIUpdater):
        self.api = APIUpdater.api
        self.api_updater = APIUpdater
        self.dev = False

    def reindex_all_taxonomies(self):
        index = "taxonomicTermDetails_term_rank"

        curr = 0
        for tax in self.api.all_taxonomies[:400]:
            curr += 1 
            print curr
            obj = tax.getObject()
            obj.reindexObject(idxs=["taxonomicTermDetails_term_rank"])

        return True

    def reindex_books(self):

        total = len(self.api.all_books)
        curr = 0

        for brain in self.api.all_books:
            obj = brain.getObject()
            obj.reindexObject()
            curr += 1

            print "Reindexing %s / %s" %(str(curr), str(total))

        return True

    def move_person(self, obj):
        
        _id = obj.priref

        base_folder = "nl/intern/personen-en-instellingen"
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        alphabet = list(string.ascii_uppercase)
        
        if obj.title:
            title = obj.title
            first_letter = title[0]
            if first_letter.upper() in alphabet:
                source = obj
                target = self.api.get_folder('%s/%s' %(base_folder, first_letter.upper()))
                self.api.move_obj_folder(source, target)
            elif first_letter.upper() in numbers:
                source = obj
                target = self.api.get_folder('%s/0-9' %(base_folder))
                self.api.move_obj_folder(source, target)
            else:
                source = obj
                target = self.api.get_folder('%s/meer' %(base_folder))
                self.api.move_obj_folder(source, target)
                self.error("Unknown type - id: %s - letter: %s" %(str(_id), first_letter))
        else:
            self.error("No title - %s"%(str(_id)))

    def fix_institutions(self):
        all_institutions = self.api.portal_catalog(nameInformation_name_nameType_type="institution")

        total = len(all_institutions)
        curr = 0

        for institution in all_institutions:
            transaction.begin()
            person = institution.getObject()

            curr += 1
            print "Fixing %s / %s" %(str(curr), str(total))

            priref = getattr(person, 'priref', "")
            name = getattr(person, 'nameInformation_name_name', "")

            dirty_id = "%s %s" %(str(priref), str(name.encode('ascii', 'ignore')))
            normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

            person.title = name

            api.content.rename(obj=person, new_id=normalized_id, safe_id=True)
            self.move_person(person)
            transaction.commit()

        return True

    def fix_person_name(self, person):
        priref = getattr(person, 'priref', "")
        title = getattr(person, 'title', "")

        if title:
            title_separated = [x.strip() for x in title.split(",")]
            length = len(title_separated)
            if length == 0:
                self.warning('%s__%s__Number of commas is 0. No modifications are done.' %(str(priref), str(title.encode('ascii', 'ignore'))))
            elif length > 2:
                self.error("%s__%s__Number of commas is >= 2" %(str(priref), str(title.encode('ascii', 'ignore'))))
            elif length == 2:
                brackets = re.findall('\(.*?\)', title)
                
                if len(brackets) <= 1:
                    if len(brackets) == 1:
                        last_part = brackets[0]
                        title = title.replace(last_part, '')
                        title = title.strip()
                        title_separated = [x.strip() for x in title.split(",")]
                    else:
                        last_part = ""

                    if len(title_separated) == 2:
                        first_name = title_separated[1]
                        last_name = title_separated[0]
                        new_title = [first_name, last_name]
                        new_title_string = " ".join(new_title)
                        new_title_string = new_title_string.strip()

                        if last_part:
                            new_title_string = "%s %s" %(new_title_string, last_part)

                        # Set title
                        person.title = new_title_string
                        #person.nameInformation_name_name = new_title_string

                        self.log_status("! STATUS !__%s__Name updated from '%s' to '%s'." %(str(priref), str(title.encode('ascii', 'ignore')), str(new_title_string.encode('ascii', 'ignore'))))

                        # Change ID
                        dirty_id = "%s %s" %(str(priref), new_title_string)
                        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                        person.reindexObject(idxs=['Title'])

                        #api.content.rename(obj=person, new_id=normalized_id, safe_id=True)
                        #self.move_person(person)
                    else:
                        self.warning('%s__%s__Number of commas is 0. No modifications are done.' %(str(priref), str(title.encode('ascii', 'ignore'))))

                elif len(brackets) > 1:
                    self.error("%s__%s__Number of text between parenthesis is >= 2" %(str(priref), str(title.encode('ascii', 'ignore'))))

            else:
                self.error("%s__%s__Number of commas is 0. No modifications are done." %(str(priref), str(title.encode('ascii', 'ignore'))))
        else:
            self.error("%s__%s__Current title is empty." %(str(priref), str("")))

    def fix_persons_names(self):
        total = len(self.api.all_persons)
        curr = 0

        for brain in list(self.api.all_persons):
            try:
                curr += 1
                transaction.begin()
                self.log_status("! STATUS !__ __Reindexing %s / %s" %(str(curr), str(total)))
                person = brain.getObject()
                person.reindexObject()
                #self.fix_person_name(person)
                transaction.commit()
            except:
                transaction.abort()
                pass

        return True

    def check_number_of_commas(self):
        count = 0
        curr = 0
        total = len(list(self.api.all_persons))
        for brain in list(self.api.all_persons):
            curr += 1
            
            self.log_status("! STATUS !__ Checking %s / %s" %(str(curr), str(total)))
            person = brain.getObject()
            title = getattr(person, 'title', "")

            title_separated = [x.strip() for x in title.split(",")]
            length = len(title_separated)

            if length == 2:
                print title.encode('ascii', 'ignore')

        print "Total of Persons / Institutions with 1 comma: %s" %(str(count))
        return True


    def find_relations(self):
        from zope.intid.interfaces import IIntIds
        from Acquisition import aq_inner

        total = 0

        intids = getUtility(IIntIds)
        cat = getUtility(ICatalog)
        for brain in list(self.api.all_persons):
            person = brain.getObject()
            _id = intids.getId(aq_inner(person))
            from_relations = list(cat.findRelations(dict(from_id=_id)))
            to_relations = list(cat.findRelations(dict(to_id=_id)))

            len_from = len(from_relations)
            len_to = len(to_relations)

            if person.id == "test-title":
                for relation in to_relations:
                    print relation.from_attribute

        return True

    def reindex_all_objects(self):
        self.api_updater.portal_type = "Object"
        self.api_updater.init_fields()
        
        for name, field in self.fields:
            if name not in ['productionDating_productionDating']:
                searchable(IObject, name)

        total = len(list(self.api.all_objects))
        curr = 0

        for brain in list(self.api.all_objects):
            transaction.begin()
            curr += 1
            print "Reindexing %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            obj.reindexObject()
            transaction.commit()

        return True

    def reindex_all_books(self):
        """total = len(list(self.api.all_books))
        curr = 0

        for brain in self.api.all_books:
            curr += 1
            print "Reindexing book %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass

        print "== AUDIOVISUALS =="
        total = len(list(self.api.all_audiovisuals))
        curr = 0

        for brain in self.api.all_audiovisuals:
            curr += 1
            print "Reindexing audiovisual %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass"""


        print "== ARTICLES =="
        total = len(list(self.api.all_articles))
        curr = 0

        for brain in self.api.all_articles:
            curr += 1
            print "Reindexing article %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass

        """print "== SERIALS =="
        total = len(list(self.api.all_serials))
        curr = 0

        for brain in self.api.all_serials:
            curr += 1
            print "Reindexing serial %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass

        print "== RESOURCES =="
        total = len(list(self.api.all_resources))
        curr = 0

        for brain in self.api.all_resources:
            curr += 1
            print "Reindexing resource %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass"""

        return True

    def reindex_all_exhibitions(self):
        total = len(list(self.api.all_exhibitions))
        curr = 0

        for brain in self.api.all_exhibitions:
            curr += 1
            print "Reindexing %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            obj.reindexObject()

        return True

    def reindex_all_images(self):
        total = len(list(self.api.all_images))
        curr = 0

        for brain in self.api.all_images:
            curr += 1
            print "Reindexing %s / %s" %(str(curr), str(total))

            obj = brain.getObject()
            obj.reindexObject(idxs=['reproductionData_identification_identifierURL'])

        return True

    def find_image_by_id(self, _id):
        if _id:
            image_path_split = _id.lower().split("\\")
            img = image_path_split[-1]
        
            image_id = idnormalizer.normalize(img, max_length=len(img))
            
            #if image_id in self.images_dict:
            #    img_brain = self.images_dict[image_id]
            #    img_obj = img_brain.getObject()
            #    return img_obj
        
            if _id in self.images_ref_dict:
                img_brain = self.images_ref_dict[_id]
                return img_brain

            else:
                return None

        return None

    def create_page_relations(self):
        page = self.api.get_folder('test-folder/test-page-with-200-related-items')

        person_container = self.api.get_folder('personen-en-instellingen')

        limit = 200
        curr = 0

        transaction.begin()
        for brain in person_container:
            person = person_container[brain]

            intids = component.getUtility(IIntIds)
            person_id = intids.getId(person)
            relation_value = RelationValue(person_id)

            page.relatedItems.append(relation_value)
            
            curr += 1
            if curr >= limit:
                transaction.commit()
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

    def import_portaltypes_utils(self, PORTAL_TYPE):
        pass

    def create_dating_field(self, field):
        start_date = field['date_early']
        start_date_precision = field['date_early_precision']
        end_date = field['date_late']
        end_date_precision = field['date_late_precision']

        result = ""

        if start_date != "" and start_date != " ":
            if result:
                if start_date_precision != "" and start_date_precision != " ":
                    result = "%s, %s %s" %(result, start_date_precision, start_date)
                else:
                    result = "%s, %s" %(result, start_date)
            else:
                if start_date_precision != "" and start_date_precision != " ":
                    result = "%s %s" %(start_date_precision, start_date)
                else:
                    result = "%s" %(start_date)
    

        if end_date != "" and end_date != " ":
            if result:
                if end_date_precision != "" and end_date_precision != " ":
                    result = "%s - %s %s" %(result, end_date_precision, start_date)
                else:
                    result = "%s - %s" %(result, end_date)
            else:
                if end_date_precision != "" and end_date_precision != " ":
                    result = "%s %s" %(end_date_precision, start_date)
                else:
                    result = "%s" %(end_date)
        return result


    def update_object_standardfields(self, obj):
        final_title = []

        # Title
        curr_title = getattr(obj, 'title', '')
        final_title.append(curr_title)

        production = getattr(obj, 'productionDating_productionDating', None)
        makers = []
        
        if production:
            for maker in production:
                if 'makers' in maker:
                    makers_field = maker['makers']
                    if makers_field:
                        for relation in makers_field:
                            if IRelationValue.providedBy(relation):
                                rel_obj = relation.to_object
                                title = getattr(rel_obj, 'title', None)
                                if title:
                                    final_title.append(title)
                            elif getattr(relation, 'portal_type', "") == "PersonOrInstitution":
                                title = getattr(relation, 'title', None)
                                if title:
                                    final_title.append(title)
                    else:
                        continue
                else:
                    continue


        
        # Get Year
        dating = getattr(obj, 'productionDating_dating_period', None)
        if dating:
            line = dating[0]
            dates = self.create_dating_field(line)
            if dates:
                final_title.append(dates)

        final_title_string = ", ".join(final_title)

        setattr(obj, 'title', final_title_string)
        
        # Description - clear value
        setattr(obj, 'description', '')

        # Body
        labels = getattr(obj, 'labels', "")
        if labels:
            label = labels[0]
            text = label['text']
            if text:
                final_text = RichTextValue(text, 'text/html', 'text/html')
                setattr(obj, 'text', final_text)

        print final_title_string
        print obj.absolute_url()
        print "----"

        obj.reindexObject(idxs=["Title"])
        return True

    def find_ref_in_brains(self, ref_id, brains):
        found = False

        for brain in brains:
            if brain.id == ref_id:
                return True

        return found


    def find_digitalreferences(self, obj):
        object_number = getattr(obj, 'identification_identification_objectNumber', None)
        slideshow = None
        prive = None

        field_to_search = "disposal_documentation"

        if 'slideshow' in obj:
            slideshow = obj['slideshow']
        if 'prive' in obj:
            prive = obj['prive']

        objs = self.api.portal_catalog(path={"query":"/".join(obj.getPhysicalPath()), "depth": 2})

        references = getattr(obj, field_to_search, None)
        if references:
            if len(references) > 0:
                for line in references:
                    reference = line['reference']
                    if reference != "" and reference != " " and reference != None:
                        reference_path_split = reference.lower().split("\\")
                        ref = reference_path_split[-1]
                        ref_id = idnormalizer.normalize(ref, max_length=len(ref))

                        found = self.find_ref_in_brains(ref_id, objs)
                        if not found:
                            log_text = "%s__%s" %(object_number, reference)
                            self.log_status(log_text, False)
            else:
                self.warning("%s__%s" %(object_number, "Object doesn't contain digital references"))

        return True

    def find_multiplefields(self, obj, identifiers):

        reprod_type = getattr(obj, 'reproductionData_identification_reproductionType', '')

        if reprod_type:
            if type(reprod_type) != list:
                length = len(reprod_type)
                if length > 1:
                    priref = getattr(obj, 'priref', '')
                    reproduction_ref = getattr(obj, 'reproductionData_identification_reproductionReference', '')
                    identifier_url = getattr(obj, 'reproductionData_identification_identifierURL', '')
                    if identifier_url not in identifiers:
                        identifiers.append(identifier_url)

                    url = obj.absolute_url()
                    self.log_status("%s__%s__%s__%s__%s"%(str(reprod_type), priref, reproduction_ref, identifier_url, url), False)
        return True



    def check_special_fields(self, obj):

        fields = getattr(obj, 'fieldCollection_habitatStratigraphy_habitat', None)
        if fields:
            for line in fields:
                field = line['term']
                if field:
                    if field.strip() != "":
                        print obj.absolute_url()

        return True

    def find_images_without_ref(self):
        curr = 0
        total = len(list(self.api.all_images))
        rep_reference = []

        for brain in list(self.api.all_images):
            obj = brain.getObject()
            reference = getattr(obj, 'reproductionData_identification_identifierURL', '')
            rep_ref = getattr(obj, 'reproductionData_identification_reproductionReference', '')
            if reference in [None, '', ' ']:
                self.log_status("%s__%s" %(obj.id, obj.absolute_url()), False)
                if rep_ref not in rep_reference:
                    rep_reference.append(rep_ref)


        print "REFERENCES:"
        print rep_reference

        return True

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
            val = self.api.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value


    def create_indexes(self, idxs):
        indexes = self.api.portal_catalog.indexes()
    
        print "Adding new indexes"
        
        # Specify the indexes you want, with ('index_name', 'index_type')
        wanted = idxs
        
        indexables = []
        for name, meta_type in wanted:
            if name not in indexes:
                self.api.portal_catalog.addIndex(name, meta_type)
                indexables.append(name)
                print "Added %s for field %s." %(meta_type, name)

        return True





