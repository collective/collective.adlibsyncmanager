

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
ORGANIZATION = ""

VALID_TYPES = ['test', 'sync_date']
API_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=%s"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured"

class SyncMechanism:
	def __init__(self, portal, date, _type, folder):
		self.METHODS = {
			'test': self.test_api,
			'sync_date': self.sync_date,
		}

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
		print "=== Test for last day ==="
		self.date = '2014-11-11'
		self.xmldoc = self.build_request(self.date)
		records = self.get_records(self.xmldoc)

		print "=== Result ==="
		print "%s records modified since %s" % (str(len(records)), self.date)
		print "=== Result ==="

		print "=== Test for last hour ==="
		last_hour_time = datetime.today() - timedelta(hours = 1)
		last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

		self.xmldoc = self.build_request(last_hour_datetime)
		records = self.get_records(self.xmldoc)
		
		print "=== Result ==="
		print "%s records modified since %s" % (str(len(records)), last_hour_datetime)
		print "=== Result ==="

		print "=== Test for one minute ago ==="
		last_hour_time = datetime.today() - timedelta(minutes = 1)
		last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

		self.xmldoc = self.build_request(last_hour_datetime)
		records = self.get_records(self.xmldoc)
		self.records_modified = len(records)

		print "=== Result ==="
		print "%s records modified since %s" % (str(self.records_modified), last_hour_datetime)
		print "=== Result ==="
		
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
				print ("== Chosen folder " + folder + " does not exist. ==")
				self.success = False
				return None

		return container

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

		return object_data

	def get_object_from_instance(self, object_number):
		container = self.get_container()
		catalog = getToolByName(container, 'portal_catalog')
		results = catalog.searchResults({'portal_type': 'Object'})

		for result in results:
			if result.getObject().object_number == object_number:
				print "== Found object! =="
				return result.getObject()

		return None


	def sync_date(self):
		date = self.date

		self.xmldoc = self.build_request(date)
		records = self.get_records(self.xmldoc)

		print "=== Result ==="
		print "%s records modified since %s" % (str(len(records)), date)
		
		list_of_objects = []
		for record in records:
			if record.find('object_number') != None:
				object_number = record.find('object_number').text
				_object = self.get_object_from_instance(object_number)
				if _object != None:
					transaction.begin()
					try:
						# Request details of object
						priref = self.convert_object_number_priref(object_number)
						
						print "== Found updated object %s. Fetch details from API ==" % (object_number)
						object_new_data = self.fetch_object_api(priref)

						print "== Update object =="
						_object.title = object_new_data['title']
						_object.description = object_new_data['description']
						_object.object_number = object_new_data['object_number']
						_object.object_type = object_new_data['object_type']
						_object.dating = object_new_data['dating']
						_object.artist = object_new_data['artist']
						_object.material = object_new_data['material']
						_object.technique = object_new_data['technique']
						_object.dimension = object_new_data['dimension']

						# Text update with rich text value
						text = RichTextValue(object_new_data['text'], 'text/plain', 'text/html')
						_object.text = text

						transaction.commit()
					
					except:
						transaction.abort()
						print "== Unexpected expection. Aborting. "
						self.errors += 1
						self.success = False
						return

					
					
					print "== Object updated =="
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



