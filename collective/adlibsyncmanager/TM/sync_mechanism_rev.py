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
API_COLLECTION_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=%s&search=%s&limit=0"
API_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=%s&limit=0"
API_REQUEST_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=%s"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured&limit=0"
API_REQUEST_URL_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(shelf_mark='%s')&xmltype=structured"


COLLECTION_PATH = {
    'ChoiceMunten':{
        'dev':"",
        'prod':""
    },
    'ChoiceGeologie':{
        'dev':"",
        'prod':""
    },
    'ChoiceKunst':{
        'dev':"",
        'prod':""
    },
    'ChoiceInstrumenten':{
        'dev':"",
        'prod':""
    },
    'ChoiceBooks':{
        'dev':"",
        'prod':""
    }
}

class SyncMechanism:
    def __init__(self, portal, teylers_migrator, date, creation_date, _type, folder, log_path):
        self.METHODS = {
            'test': self.test_api,
            'sync_date': self.sync_date,
        }

        self.migrator = teylers_migrator
        self.migrator.IMPORT_TYPE = "sync"
        self.migrator.updater.IMPORT_TYPE = "sync"

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

        self.updated = 0
        self.created = 0
        self.skipped = 0
        self.errors = 0
        

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

    def get_records(self, xmldoc):
        root = xmldoc.getroot()
        recordList = root.find("recordList")
        records = recordList.getchildren()
        return records

    def test_query(self, collection, query):
        timestamp = datetime.today().isoformat()

        search_query = query

        self.write_log_details("%s__TEST MODIFIED RECORDS" %(collection))

        self.write_log_details("%s__## Test for long period"%(collection), timestamp)
        self.date = '2015-12-09'
        self.xmldoc = self.build_api_request(self.date, search_query, collection)
        records = self.get_records(self.xmldoc)
        self.write_log_details("%s__%s records modified since %s" % (collection, str(len(records)), self.date))

        timestamp = datetime.today().isoformat()
        self.write_log_details("%s__## Test for last hour"%(collection), timestamp)
        last_hour_time = datetime.today() - timedelta(hours = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')
        self.xmldoc = self.build_api_request(last_hour_datetime, search_query, collection)
        records = self.get_records(self.xmldoc)
        self.write_log_details("%s__%s records modified since %s" % (collection, str(len(records)), last_hour_datetime))

        timestamp = datetime.today().isoformat()
        self.write_log_details("%s__## Test for one minute ago"%(collection), timestamp)
        last_hour_time = datetime.today() - timedelta(minutes = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')
        self.xmldoc = self.build_api_request(last_hour_datetime, search_query, collection)
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)
        self.write_log_details("%s__%s records modified since %s" % (collection, str(self.records_modified), last_hour_datetime), timestamp)

        self.write_log_details("%s__TEST MODIFIED RECORDS FINISHED ##" %(collection))

    def build_api_request(self, request_date, search_query, collection):
        search = search_query
        search = search % (request_date)

        quoted_query = urllib.quote(search)
        
        #print "Build request for: %s" % (quoted_query)
        self.api_request = API_COLLECTION_REQUEST % (collection, quoted_query)

        req = urllib2.Request(self.api_request)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        return doc

    def get_records_to_sync(self, search_query, collection):

        date = self.date
        self.xmldoc = self.build_api_request(date, search_query, collection)
        records = self.get_records(self.xmldoc)

        return records

    def test_api(self):
        self.object_type = ""
        # Run tests
        #
        self.is_test = True
        self.test_query('ChoiceMunten', "modification greater '%s'")
        self.test_query('ChoiceGeologie', "modification greater '%s'")
        self.test_query('ChoiceKunst', "modification greater '%s'")
        self.test_query('ChoiceInstrumenten', "modification greater '%s'")
        self.test_query('ChoiceBooks', "modification greater '%s'")


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

    ########
    #
    # SYNC 
    #
    ########

    def write_log_details(self, log, timestamp=datetime.today().isoformat()):
        if log:
            self.migrator.log_status(log)

            if 'TEST MODIFIED' in log:
                final_log = "%s" %(log)
            else:
                final_log = "[ %s ] - %s" %(timestamp, log)

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
        # Sync for modified   #
        # # # # # # # # # # # #
        


        self.success = True
        self.creation_success = True
        return
                
    def start_sync(self):
        self.migrator.init_log_files()
        if self.type in VALID_TYPES:
            self.METHODS[self.type]()
        else:
            self.success = False
            self.error_message = "Not a valid type of request."



