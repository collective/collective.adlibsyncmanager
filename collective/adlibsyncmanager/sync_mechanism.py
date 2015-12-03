#!/usr/bin/python
# -*- coding: utf-8 -*-


#
# Adlib sync mechanism by Andre Goncalves
#

import transaction
from datetime import datetime, timedelta
import urllib2, urllib
from plone.i18n.normalizer import idnormalizer
from lxml import etree
from plone.app.textfield.value import RichTextValue
from Products.CMFCore.utils import getToolByName
import re
import sys
import smtplib

# SET ORGANIZATION
ORGANIZATION = "teylers"

VALID_TYPES = ['test', 'sync_date']
API_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=%s"
API_REQUEST_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=%s"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured"
API_REQUEST_URL_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(shelf_mark='%s')&xmltype=structured"

class SyncMechanism:
    def __init__(self, portal, date, creation_date, _type, folder, log_path):
        self.METHODS = {
            'test': self.test_api,
            'sync_date': self.sync_date,
        }

        self.log_file = open(log_path, 'a')

        self.portal = portal
        self.folder_path = folder.split('/')
        self.image_folder = folder.split('/')

        self.api_request = ""
        self.xmldoc = ""
        self.creation_xmldoc = ""
        self.date = date
        self.creation_date = creation_date
        self.type = _type

        self.records_modified = 0
        self.skipped = 0
        self.updated = 0
        self.created = 0
        self.errors = 0
        self.success = False
        self.creation_success = False
        self.error_message = ""
        self.is_en = False
        

    ##### Utils #####

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

    def get_object_from_folder(self, object_number, folder):
        container = folder

        for obj in container:
            if hasattr(container[obj], 'object_number'):
                if container[obj].object_number == object_number:
                    return container[obj]
        
        return None

    def get_object_from_instance(self, object_number):
        container = self.get_container()

        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="nl")

        for brain in all_objects:
            item = brain.getObject()
            if hasattr(item, 'object_number'):
                if item.object_number == object_number:
                    return item

        return None


    def transform_creators_name(self, creators):
        date_birth = ""
        for creator in creators:
            if "instrumenten" in self.folder_path or "instruments" in self.folder_path:
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

            print date_birth

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
        dirty_id = "%s %s %s" % (object_number, title, creator)
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
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
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
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
                                    pass
                                else:
                                    dimensions += "%s %s (%s)<p>" % (d['value'], d['unit'], d['part'])
                        else:
                            if self.transform_d(d['type']) != "":
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                            else:
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
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
                                else:
                                    dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                        else:
                            if d['part'] != "":
                                if d["part"] in ['papier', 'opzet', 'lijst'] and (('drawings' in self.image_folder) or ('tekening' in self.folder_path)):
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

    def convert_shelf_priref(self, object_number):
        quoted_query = urllib.quote(object_number)
        api_request = API_REQUEST_URL_BOOKS % (quoted_query)
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

    def fetch_book_api(self, priref, create):
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


        # BUG BUG
        if self.is_book:
            creator_details["name"] = creator_details["name"]
            object_data["author"] = creator_details["name"]
        else:   
            creator_details["name"] = self.transform_creator_name(creator_details['temp_name'])
            object_data['artist'] = self.create_creator_field(creator_details)

        object_data['dimension'] = self.create_dimension_field(object_temp_data)
        if object_data['dimension'] == "":
            dms = []
            if len(first_record.findall('dimensions')) > 0:
                for dimens in first_record.findall('dimensions'):
                    dms.append(self.trim_white_spaces(dimens.text))

                new_dms = '<p>'.join(dms)
                object_data['dimension'] = new_dms

        object_data['dating'] = self.create_object_production(object_temp_data['production_date_start'], object_temp_data['production_date_end'])

        if first_record.find('object_category') != None:
            object_data['object_category'] = first_record.find('object_category').text

        object_data['dirty_id'] = self.create_object_dirty_id(object_data['object_number'], object_data['book_title'], object_data['artist'])

        if create:
            return []
        else:
            return object_data

    def fetch_object_api(self, priref, create):
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
                if "fossielen-en-mineralen" in self.folder_path or "fossils-and-minerals" in self.folder_path or self.is_test or object_data['object_number'] == "3014-000":
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

        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path) or self.object_type == "fossil") and object_data["title"] != "":
            object_data["description"] = object_data["title"]

        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path) or self.object_type == "fossil") and object_data["title"] != "" and object_data['scientific_name'] != "":
            object_data["description"] = object_data["scientific_name"]

        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path) or self.object_type == "fossil") and object_data["title"] == "":
            object_data["title"] = object_data["scientific_name"]

        object_data['inscription'] = self.create_inscription_field(inscription_temp_data)
        

        ## CREATOR
        self.transform_creators_name(creators)
        object_data['artist'] = self.create_creators_field(creators)


        object_data['dimension'] = self.create_dimension_field(object_temp_data)
        
        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path) or self.is_test or object_data['object_number'] == "3014-000"):
            #object_data['dating'] = ""
            object_data['fossil_dating'] = self.create_object_productions(object_temp_data['production_date_prec'], object_temp_data['production_date_start'], object_temp_data['production_date_end'])
        
        object_data['dating'] = self.create_object_productions(object_temp_data['production_date_prec'], object_temp_data['production_date_start'], object_temp_data['production_date_end'])
        
        if not "Fossils" in self.image_folder:
            if len(creators) > 0:
                object_data['description'] = self.create_object_description(creators[0]["name"], object_temp_data['production_date_end'])
            else:
                object_data['description'] = self.create_object_description("", object_temp_data['production_date_end'])
        
        if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path):
            if first_record.find('title.translation') != None:
                object_data["translated_title"] = first_record.find('title.translation').text

        if first_record.find('title.translation') != None:
            object_data["translated_title"] = first_record.find('title.translation').text

        if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path) or self.is_test or object_data['object_number'] == "3014-000":
            if first_record.find('production.period') != None:
                object_data["production_period"] = first_record.find('production.period').text

        # FOSSIL SPECIFIC
        """if ("Fossils" in self.image_folder) or ("fossielen-en-mineralen" in self.folder_path) or self.is_test:
            if object_data['object_type'] != "":
                #object_data["description"] += object_data["object_type"]
                #if object_data["production_period"] != "":
                #    object_data["description"] += ", %s" %(object_data["production_period"])
                pass
            else:
                if object_data["production_period"] != "":
                    object_data["description"] += "%s" %(object_data["production_period"])"""

        if self.is_en:
            if first_record.find('title.translation') != None:
                object_data["translated_title"] = first_record.find('title.translation').text


        if first_record.find('object_category') != None:
            object_data['object_category'] = first_record.find('object_category').text

        object_data['dirty_id'] = self.create_object_dirty_id(object_data['object_number'], object_data['title'], object_data['artist'])

        if create:
            #result = self.create_new_object(object_data)
            return []
        else:
            return object_data


    #################

    def parse_api_doc(self, url):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        return doc

    def update_object(self, data):
        return None

    def build_request(self, request_quote, is_book=False):
        search = "modification greater '%s'"
        search = search % (request_quote)

        quoted_query = urllib.quote(search)

        REQUEST = API_REQUEST
        if is_book:
            REQUEST = API_REQUEST_BOOKS
        
        #print "Build request for: %s" % (quoted_query)
        self.api_request = REQUEST % (quoted_query)

        #print self.api_request

        req = urllib2.Request(self.api_request)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        return doc

    def build_creation_request(self, request_quote, database=None):
        REQUEST = API_REQUEST

        search = "creation greater '%s'"
        search = search % (request_quote)

        quoted_query = urllib.quote(search)

        if database != None:
            REQUEST = "http://teylers.adlibhosting.com/wwwopacx/wwwopac.ashx?database=%s&search=%s" % (database, quoted_query)
            self.api_request = REQUEST
        else:
            self.api_request = REQUEST % (quoted_query)

        req = urllib2.Request(self.api_request)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        return doc

    def get_records(self, xmldoc):
        root = xmldoc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()
        return records

    def test_modified(self):
        timestamp = datetime.today().isoformat()

        self.write_log_details("\n\n##\n## TEST MODIFIED RECORDS\n##")

        self.write_log_details("## Test for long period", timestamp)
        self.date = '2015-03-18'
        self.xmldoc = self.build_request(self.date)
        records = self.get_records(self.xmldoc)

        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records modified since %s" % (str(len(records)), self.date))
        self.write_log_details("=== Result ===", timestamp)

        timestamp = datetime.today().isoformat()
        self.write_log_details("## Test for last hour", timestamp)
        last_hour_time = datetime.today() - timedelta(hours = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        self.xmldoc = self.build_request(last_hour_datetime)
        records = self.get_records(self.xmldoc)
        
        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records modified since %s" % (str(len(records)), last_hour_datetime))
        self.write_log_details("=== Result ===", timestamp)

        timestamp = datetime.today().isoformat()
        self.write_log_details("## Test for one minute ago", timestamp)
        last_hour_time = datetime.today() - timedelta(minutes = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        self.xmldoc = self.build_request(last_hour_datetime)
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)

        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records modified since %s" % (str(self.records_modified), last_hour_datetime), timestamp)
        self.write_log_details("=== Result ===", timestamp)

    def test_created(self):
        timestamp = datetime.today().isoformat()

        self.write_log_details("\n\n##\n## TEST CREATED RECORDS\n##")

        self.write_log_details("## Test for long period", timestamp)
        self.creation_date = '2015-03-18'
        self.xmldoc = self.build_creation_request(self.creation_date)
        records = self.get_records(self.xmldoc)

        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records created since %s" % (str(len(records)), self.creation_date))
        self.write_log_details("=== Result ===", timestamp)

        timestamp = datetime.today().isoformat()
        self.write_log_details("## Test for last hour", timestamp)
        last_hour_time = datetime.today() - timedelta(hours = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        self.xmldoc = self.build_creation_request(last_hour_datetime)
        records = self.get_records(self.xmldoc)
        
        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records created since %s" % (str(len(records)), last_hour_datetime))
        self.write_log_details("=== Result ===", timestamp)

        timestamp = datetime.today().isoformat()
        self.write_log_details("## Test for one minute ago", timestamp)
        last_hour_time = datetime.today() - timedelta(minutes = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        self.xmldoc = self.build_creation_request(last_hour_datetime)
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)

        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records created since %s" % (str(self.records_modified), last_hour_datetime), timestamp)
        self.write_log_details("=== Result ===", timestamp)

    def test_api(self):

        # Run tests
        #
        self.is_test = True

        self.creation_date = '2015-06-04'
        creation_date = self.creation_date
        self.get_new_created_objects(creation_date)


        date = '2015-06-03'
        self.xmldoc = self.build_request(date)
        records = self.get_records(self.xmldoc)
        self.is_book = False
        self.write_log_details("=== MODIFICATION Sync Results ===")
        self.write_log_details("%s records modified since %s" % (str(len(records)), date))
        
        # Update modified objects
        self.update_modified_objects(records)

        date = '2015-06-03'
        self.xmldoc = self.build_request(date, True)
        records = self.get_records(self.xmldoc)
        self.is_book = True
        self.write_log_details("=== MODIFICATION Sync Results ===")
        self.write_log_details("%s records modified since %s" % (str(len(records)), date))
        
        # Update modified objects
        self.update_modified_objects(records)

        self.creation_success = True
        self.success = True

        return

    def get_folder(self, path):
        container = self.portal

        folder_path = path.split("/")

        for folder in folder_path:
            if hasattr(container, folder):
                container = container[folder]
            else:
                print ("== Chosen folder " + folder + " does not exist. ==")
                return None

        return container

    def get_created_items(self, date, database):
        records = []
        
        xmlDoc = self.build_creation_request(date, database)
        records = self.get_records(xmlDoc)

        return records

    def create_object(self, object_data, folder, is_kunst=False):

        plone_folder = folder

        if is_kunst:
            if object_data["object_type"] in ['schilderij', 'schild']:
                plone_folder = folder
            else:
                plone_folder = self.get_folder('nl/collectie/tekening')

        plone_folder = folder

        dirty_id = object_data['dirty_id']
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        
        result = False
        exists = False
        created_object = None

        try:
            transaction.begin()
            if hasattr(plone_folder, normalized_id) and normalized_id != "":
                self.skipped += 1
                self.write_log_details("Object already exists %s" % (object_data["object_number"]))
                transaction.commit()
                exists = True
                return exists, plone_folder[normalized_id]

            if not hasattr(plone_folder, normalized_id):
                
                item = self.get_object_from_folder(object_data["object_number"], folder)
                if item == None:

                    if object_data['book_title'] != "":
                        object_data['title'] = object_data['book_title']

                    plone_folder.invokeFactory(
                        type_name="Object",
                        id=normalized_id,
                        title=object_data['title'],
                        description=object_data['description'],
                        object_number=object_data['object_number'])

                    # Get object
                    created_object = plone_folder[str(normalized_id)]
                    self.update_object_metadata(created_object, object_data)

                    # Publish created object
                    created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")
                    created_object.reindexObject()
                    transaction.commit()

                    self.write_log_details("Added object %s" % (object_data["object_number"]))
                    self.created += 1
                    result = True

                else:
                    self.skipped += 1
                    self.write_log_details("Object already exists %s" % (object_data["object_number"]))
                    transaction.commit()
                    exists = True
                    return exists, item

        except:
            self.errors += 1
            self.write_log_details("Unexpected error on create_object (%s): %s" % (dirty_id, sys.exc_info()[1]))
            result = False
            transaction.abort()
            return exists, result

        if not result:
            self.skipped += 1
            self.write_log_details("Skipped object: %s" %(object_data["object_number"]))

        return exists, created_object

    def create_items(self, records, path, is_kunst=False):

        folder = self.get_folder(path)

        for record in list(records):
            if record.find('object_number') != None or (self.is_book):
                #object_number = record.find('object_number').text
                priref = record.find('priref').text

                if priref != None:
                    if not self.is_book:
                        object_data = self.fetch_object_api(priref, False)
                    else:
                        object_data = self.fetch_book_api(priref, False)

                    exists, result = self.create_object(object_data, folder, is_kunst)

                    if result != None:
                        if result != False:
                            if exists:
                                self.write_log_details("Item already exists %s." %(priref))
                            else:
                                self.write_log_details("Create items run successfully for %s." %(priref))
                        else:
                            self.write_log_details("Exception occurr for %s." %(priref))
                            return False
        return True

    def get_new_created_objects(self, date):

        # ChoiceMunten
        records = self.get_created_items(date, 'ChoiceMunten')
        self.write_log_details("ChoiceMunten - %s records created since %s" % (str(len(records)), date))
        self.create_items(records, 'nl/collectie/munten-en-penningen')

        # ChoiceGeologie
        records = self.get_created_items(date, 'ChoiceGeologie')
        self.write_log_details("ChoiceGeologie - %s records created since %s" % (str(len(records)), date))
        self.folder_path = 'nl/collectie/fossielen-en-mineralen'.split('/')
        self.create_items(records, 'nl/collectie/fossielen-en-mineralen')
        
        # ChoiceKunst
        records = self.get_created_items(date, 'ChoiceKunst')
        self.write_log_details("ChoiceKunst - %s records created since %s" % (str(len(records)), date))
        self.create_items(records, 'nl/collectie/schilderijen', True)
        
        # ChoiceInstrumenten
        records = self.get_created_items(date, 'ChoiceInstrumenten')
        self.write_log_details("ChoiceInstrumenten - %s records created since %s" % (str(len(records)), date))
        self.create_items(records, 'nl/collectie/instrumenten')
        

        # ChoiceBooks
        records = self.get_created_items(date, 'ChoiceBooks')
        self.is_book = True
        self.write_log_details("ChoiceBooks - %s records created since %s" % (str(len(records)), date))
        self.create_items(records, 'nl/collectie/boeken')
        
        return True

    def update_modified_objects(self, records):
        for record in records:
            if record.find('object_number') != None or self.is_book:

                if self.is_book:
                    object_number = record.find('shelf_mark').text
                else:
                    object_number = record.find('object_number').text

                if self.is_book:
                    if object_number != "3014h 000":
                        continue
                else:
                    if object_number != "3014-000":
                        continue
                
                self.write_log_details("== Try to find object %s in website ==" % (object_number))

                _object = self.get_object_from_instance(object_number)
                if _object != None:
                    transaction.begin()
                    try:
                        # Request details of object
                        if self.is_book:
                            priref = self.convert_shelf_priref(object_number)
                        else:
                            priref = self.convert_object_number_priref(object_number)
                        
                        self.write_log_details("== Found updated object %s. Fetch details from API ==" % (object_number))
                        if self.is_book:
                            object_new_data = self.fetch_book_api(priref, False)
                        else:
                            object_new_data = self.fetch_object_api(priref, False)

                        self.write_log_details("== Update object ==")

                        self.update_object_metadata(_object, object_new_data)           

                        transaction.commit()
                    
                    except Exception, e:
                        transaction.abort()
                        self.write_log_details("== Unexpected exception. Aborting. ")
                        self.errors += 1
                        self.success = False
                        
                        exception_text = str(e)
                        raise
                        #self.send_fail_email(exception_text, )

                    self.write_log_details("== Object updated ==")
                    self.updated += 1
                else:
                    self.write_log_details("== Object %s not found." %(object_number))
                    self.skipped += 1


    ########
    #
    # SYNC 
    #
    ########

    def write_log_details(self, log, timestamp=datetime.today().isoformat()):
        final_log = "[ %s ] - %s \n" %(timestamp, log)
        print final_log
        try:
            self.log_file.write(final_log)
        except:
            pass

    def update_object_metadata(self, _object, object_new_data):
        if object_new_data['object_type'] != 'boeken':
            _object.title = object_new_data['title']
            _object.description = object_new_data['description']

        _object.object_number = object_new_data['object_number']
        _object.object_type = object_new_data['object_type']
        _object.dating = object_new_data['dating']
        _object.artist = object_new_data['artist']
        _object.material = object_new_data['material']
        _object.technique = object_new_data['technique']
        _object.dimension = object_new_data['dimension']
        _object.credit_line = object_new_data['credit_line']
        _object.object_description = object_new_data['object_description']
        _object.inscription = object_new_data['inscription']
        _object.scientific_name = object_new_data['scientific_name']
        _object.translated_title = object_new_data['translated_title']
        _object.production_period = object_new_data['production_period']
        _object.object_category = object_new_data['object_category']
        _object.location = object_new_data['location']
        _object.publisher = object_new_data['publisher']
        _object.fossil_dating = object_new_data['fossil_dating']
        _object.illustrator = object_new_data['illustrator']
        _object.author = object_new_data['author']
        _object.digital_reference = object_new_data['digital_reference']
        _object.production_notes = object_new_data['production_notes']

        text = RichTextValue(object_new_data['text'], 'text/plain', 'text/html')
        # Text update with rich text value
        _object.text = text
        _object.reindexObject()



    def send_fail_email(self, error_text, object_number):
        """
        Send email if sync fails
        """
        
        sender = "andre@intk.com"
        receivers = ['andre@goncalves.me', 'andre@itsnotthatkind.org']

        subject = "Sync mechanism - FAIL"        
        msg = "Subject: %s\n\nObject number: %s failed to sync with Adlib.\nError details: %s" %(subject, object_number, error_text)

        try:
            smtpObj = smtplib.SMTP('localhost')
            smtpObj.sendmail(sender, receivers, msg)
        except:
            self.write_log_details("=== ! Send email failed ===\nEmail msg: %s" %(msg))

    def sync_date(self):
        date = self.date
        creation_date = self.creation_date
        
        self.is_book = False
        self.is_test = False
        self.creation_success = False

        # # # # # # # # # # # #
        # Sync for Created    #
        # # # # # # # # # # # #

        self.write_log_details("=== CREATION Sync Results ===")
        creation_result = self.get_new_created_objects(creation_date)
        self.creation_success = creation_result

        # # # # # # # # # # # #
        # Sync for modified   #
        # # # # # # # # # # # #

        self.xmldoc = self.build_request(date)
        records = self.get_records(self.xmldoc)
        self.is_book = False
        self.write_log_details("=== MODIFICATION Sync Results ===")
        self.write_log_details("%s records modified since %s" % (str(len(records)), date))
        
        # Update modified objects
        self.update_modified_objects(records)

        self.xmldoc = self.build_request(date, True)
        records = self.get_records(self.xmldoc)
        self.is_book = True
        self.write_log_details("=== MODIFICATION Sync Results ===")
        self.write_log_details("%s records modified since %s" % (str(len(records)), date))

        # Update modified objects
        self.update_modified_objects(records)


        self.success = True
        self.creation_success = True
        return
                
    def start_sync(self):
        if self.type in VALID_TYPES:
            self.METHODS[self.type]()
        else:
            self.success = False
            self.error_message = "Not a valid type of request."



