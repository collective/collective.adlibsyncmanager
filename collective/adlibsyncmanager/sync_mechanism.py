

#
# Adlib sync mechanism by Andre Goncalves
#

import transaction
from datetime import datetime, timedelta
import urllib2, urllib
from lxml import etree
from plone.app.textfield.value import RichTextValue
from Products.CMFCore.utils import getToolByName
import re

# SET ORGANIZATION
ORGANIZATION = "teylers"

VALID_TYPES = ['test', 'sync_date']
API_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=%s"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured"

class SyncMechanism:
    def __init__(self, portal, date, _type, folder, log_path):
        self.METHODS = {
            'test': self.test_api,
            'sync_date': self.sync_date,
        }

        self.log_file = open(log_path, 'a')

        self.portal = portal
        self.folder_path = folder.split('/')

        self.api_request = ""
        self.xmldoc = ""
        self.date = date
        self.type = _type

        self.records_modified = 0
        self.skipped = 0
        self.updated = 0
        self.errors = 0
        self.success = False
        self.error_message = ""

    ##### Utils #####

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
                    if text[:-1] == " ":
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
                            dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                        else:
                            dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                    else:
                        if d["part"] != "":
                            dimensions += "%s: %s %s (%s)" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                        else:
                            dimensions += "%s: %s %s" % (self.transform_d(d['type']), d['value'], d['unit'])
                dimension = dimensions
            else:
                dimensions = ""
                number = 0
                for d in all_dimensions:
                    number += 1
                    if number != len(all_dimensions):
                        if self.transform_d(d['type']) != "":
                            if d["part"] != "":
                                dimensions += "%s: %s %s (%s)<p>" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s: %s %s<p>" % (self.transform_d(d['type']), d['value'], d['unit'])
                        else:
                            dimensions += "%s %s<p>" % (d['value'], d['unit'])
                    else:
                        if self.transform_d(d['type']) != "":
                            if d["part"] != "":
                                dimensions += "%s: %s %s (%s)" % (self.transform_d(d['type']), d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s: %s %s" % (self.transform_d(d['type']), d['value'], d['unit'])
                        else:
                            if d['part'] != "":
                                dimensions += "%s %s (%s)" % (d['value'], d['unit'], d['part'])
                            else:
                                dimensions += "%s %s" % (d['value'], d['unit'])

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
        
        if first_record.find('Technique') != None:
            if first_record.find('Technique').find('technique') != None:
                object_data['technique'] = self.trim_white_spaces(first_record.find('Technique').find('technique').text)
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
                if "fossielen-en-mineralen" in self.folder_path or "fossils-and-minerals" in self.folder_path:
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

        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path)) and object_data["title"] != "":
            object_data["description"] = object_data["title"]

        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path)) and object_data["title"] != "" and object_data['scientific_name'] != "":
            object_data["description"] = object_data["scientific_name"]

        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path)) and object_data["title"] == "":
            object_data["title"] = object_data["scientific_name"]

        object_data['inscription'] = self.create_inscription_field(inscription_temp_data)
        


        ## CREATOR
        self.transform_creators_name(creators)
        object_data['artist'] = self.create_creators_field(creators)


        object_data['dimension'] = self.create_dimension_field(object_temp_data)
        
        if (("fossielen-en-mineralen" in self.folder_path) or ("fossils-and-minerals" in self.folder_path)):
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

    def build_request(self, request_quote):
        search = "modification greater '%s'"
        search = search % (request_quote)

        quoted_query = urllib.quote(search)
        
        print "Build request for: %s" % (quoted_query)
        self.api_request = API_REQUEST % (quoted_query)

        print self.api_request

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

    def test_api(self):
        timestamp = datetime.today().isoformat()
        self.write_log_details("=== Test for last day ===", timestamp)
        self.date = '2015-03-18'
        self.xmldoc = self.build_request(self.date)
        records = self.get_records(self.xmldoc)

        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records modified since %s" % (str(len(records)), self.date))
        self.write_log_details("=== Result ===", timestamp)

        timestamp = datetime.today().isoformat()
        self.write_log_details("=== Test for last hour ===", timestamp)
        last_hour_time = datetime.today() - timedelta(hours = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        self.xmldoc = self.build_request(last_hour_datetime)
        records = self.get_records(self.xmldoc)
        
        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records modified since %s" % (str(len(records)), last_hour_datetime))
        self.write_log_details("=== Result ===", timestamp)

        timestamp = datetime.today().isoformat()
        self.write_log_details("=== Test for one minute ago ===", timestamp)
        last_hour_time = datetime.today() - timedelta(minutes = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        self.xmldoc = self.build_request(last_hour_datetime)
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)

        self.write_log_details("=== Result ===", timestamp)
        self.write_log_details("%s records modified since %s" % (str(self.records_modified), last_hour_datetime), timestamp)
        self.write_log_details("=== Result ===", timestamp)
        
        return

    ########
    #
    # SYNC 
    #
    ########

    def write_log_details(self, log, timestamp=datetime.today().isoformat()):
        final_log = "[ %s ] - %s \n" %(timestamp, log)
        print final_log
        self.log_file.write(final_log)

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

    def sync_date(self):
        date = self.date

        self.xmldoc = self.build_request(date)
        records = self.get_records(self.xmldoc)

        self.write_log_details("=== Sync Results ===")
        self.write_log_details("%s records modified since %s" % (str(len(records)), date))
        
        for record in records:
            if record.find('object_number') != None:
                object_number = record.find('object_number').text
                _object = self.get_object_from_instance(object_number)
                if _object != None:
                    transaction.begin()
                    try:
                        # Request details of object
                        priref = self.convert_object_number_priref(object_number)
                        
                        self.write_log_details("== Found updated object %s. Fetch details from API ==" % (object_number))
                        object_new_data = self.fetch_object_api(priref, False)

                        self.write_log_details("== Update object ==")
                        self.update_object_metadata(_object, object_new_data)           

                        transaction.commit()
                    
                    except:
                        transaction.abort()
                        self.write_log_details("== Unexpected expection. Aborting. ")
                        self.errors += 1
                        self.success = False
                        return

                    self.write_log_details("== Object updated ==")
                    self.updated += 1
                else:
                    self.skipped += 1

        self.success = True
                
    def start_sync(self):
        if self.type in VALID_TYPES:
            self.METHODS[self.type]()
        else:
            self.success = False
            self.error_message = "Not a valid type of request."



