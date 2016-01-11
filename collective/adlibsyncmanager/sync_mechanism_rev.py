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
API_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=%s&limit=0"
API_REQUEST_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=%s"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured&limit=0"
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

    #################

    def parse_api_doc(self, url):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        return doc

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
        self.object_type = ""
        # Run tests
        #
        self.is_test = True

        self.creation_date = '2015-06-04'
        creation_date = self.creation_date
        #self.get_new_created_objects(creation_date)


        date = self.date
        self.xmldoc = self.build_request(date)
        records = self.get_records(self.xmldoc)
        self.is_book = False
        self.write_log_details("=== MODIFICATION Sync Results ===")
        self.write_log_details("%s records modified since %s" % (str(len(records)), date))
        
        # Update modified objects
        self.update_modified_objects(records)

        date = self.date
        self.xmldoc = self.build_request(date, True)
        records = self.get_records(self.xmldoc)
        self.is_book = True
        self.write_log_details("=== MODIFICATION Books Sync Results ===")
        self.write_log_details("%s books records modified since %s" % (str(len(records)), date))
        
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
        self.write_log_details("ChoiceBooks - %s records created since %s" % (str(len(records)), date))
        self.create_items(records, 'nl/collectie/boeken')
        
        return True

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



