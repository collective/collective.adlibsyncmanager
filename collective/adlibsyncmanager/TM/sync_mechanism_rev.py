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

from .teylers_sync_core import CORE

# SET ORGANIZATION
ORGANIZATION = "teylers"

VALID_TYPES = ['test', 'sync_date']
API_COLLECTION_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=%s&search=%s&limit=0"
API_DELETED_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=%s&command=getdeletedrecords&datefrom=%s"

API_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=%s&limit=0"
API_REQUEST_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=%s"
API_REQUEST_URL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicecollect&search=(object_number='%s')&xmltype=structured&limit=0"
API_REQUEST_URL_BOOKS = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacx/wwwopac.ashx?database=choicebooks&search=(shelf_mark='%s')&xmltype=structured"


COLLECTION_OBJ_TYPE = {
    'ChoiceMunten': "coins",
    'ChoiceGeologie': "fossils",
    'ChoiceKunst':"kunst",
    'ChoiceInstrumenten':"instruments",
    'ChoiceBooks':"books"
}

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
            'sync_date': self.run_sync,
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
        self.migrator.CREATE_NEW = False
        self.migrator.CORE = CORE
        self.migrator.updater.CORE = CORE
        self.migrator.UPLOAD_IMAGES = False
        self.collection_type = ""
        

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

        """self.write_log_details("%s__## Test for long period"%(collection), timestamp)
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
        self.write_log_details("%s__%s records modified since %s" % (collection, str(len(records)), last_hour_datetime))"""

        timestamp = datetime.today().isoformat()
        self.write_log_details("%s__## Test for one minute ago"%(collection), timestamp)
        last_hour_time = datetime.today() - timedelta(minutes = 120)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')
        self.xmldoc = self.build_api_request(last_hour_datetime, search_query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)
        self.write_log_details("%s__%s records modified since %s" % (collection, str(self.records_modified), last_hour_datetime), timestamp)

        self.write_log_details("%s__TEST MODIFIED RECORDS FINISHED ##" %(collection))

        return records

    

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

    def get_record_by_priref(self, priref, collection):
        query = "priref='%s'"

        self.xmldoc = self.build_api_request(priref, query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)

        if len(records):
            return records[0]
        else:
            return None

    def test_deleted_records(self, collection, date):

        last_hour_time = datetime.today() - timedelta(minutes = 360)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')

        quoted_query = urllib.quote(last_hour_datetime)

        api_request = API_DELETED_REQUEST %(collection, quoted_query)
        req = urllib2.Request(api_request)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)

        records = self.get_records(doc)

        for record in records:
            priref = record.find('priref').text

            obj = self.migration.find_object_by_priref(priref)

            print obj

        return True


    def test_api(self):
        print "test api"
        self.object_type = ""
        # Run tests
        #
        self.is_test = True

        self.test_query('ChoiceMunten', "modification greater '%s'")
        self.test_query('ChoiceGeologie', "modification greater '%s'")
        self.test_query('ChoiceKunst', "creation greater '%s'")
        self.test_query('ChoiceInstrumenten', "modification greater '%s'")
        self.test_query('ChoiceBooks', "modification greater '%s'")
        #self.test_deleted_records('ChoiceCollect', self.date)

        self.creation_success = True
        self.success = True
        return

    def update_sync_records(self, records, collection):
        curr = 0
        total = len(records)
        for record in records:

            curr += 1
            priref = self.migrator.get_priref(record)
            xml_record = self.get_record_by_priref(priref, self.collection_type)

            if xml_record is not None:
                if self.migrator.valid_priref(priref):
                    if priref:
                        plone_object = self.migrator.find_object_by_priref(priref)
                        if plone_object:
                            self.migrator.update_existing(priref, plone_object, xml_record)
                            self.write_log_details("%s__Updated [%s] - %s" %(str(collection), str(priref), plone_object.absolute_url()))
                        else:
                           pass
                    else:
                        self.migrator.error("%s__ __Cannot find priref in XML record"%(str(curr)))
            else:
                #TODO log error
                pass


        return True

    def sync_query_records(self, collection, query):

        self.write_log_details("%s__SYNC RECORDS" %(collection))
        search_query = query

        self.xmldoc = self.build_api_request(self.date, search_query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)
        records_modified = len(records)

        if self.migrator.CREATE_NEW:
            self.write_log_details("%s__%s records created since %s" % (collection, str(records_modified), self.date))
        else:
            self.write_log_details("%s__%s records modified since %s" % (collection, str(records_modified), self.date))

        return records


    def run_sync(self):

        #
        # Run sync
        #
        
        collections = ['ChoiceMunten', 'ChoiceGeologie', 'ChoiceKunst', 'ChoiceInstrumenten', 'ChoiceBooks']

        #last_hour_time = datetime.today() - timedelta(minutes = 240)
        #last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')
        #self.date = last_hour_datetime

        # Created
        self.migrator.CREATE_NEW = True
        #for collection in collections:
        #    self.collection_type = collection
        #    records = self.sync_query_records(self.collection_type, "creation greater '%s'")
        #    self.migrator.object_type = COLLECTION_OBJ_TYPE[self.collection_type]
        #    self.update_sync_records(records)

        # Modified
        self.migrator.CREATE_NEW = False
        for collection in collections:
            transaction.begin()
            # Exception for books
            if collection == "ChoiceBooks":
                CORE["object_number"] = ""
                CORE["shelf_mark"] = "object_number"
                self.migrator.CORE = CORE
                self.migrator.updater.CORE = CORE

            self.collection_type = collection
            records = self.sync_query_records(self.collection_type, "modification greater '%s'")
            self.migrator.object_type = COLLECTION_OBJ_TYPE[self.collection_type]
            self.update_sync_records(records, collection)
            transaction.commit()
        
        self.creation_success = True
        self.success = True
        return True

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
                log_to_write = final_log.replace('__', '')
                self.log_file.write(log_to_write+"\n")
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
        self.type = "sync_date"
        if self.type in VALID_TYPES:
            self.METHODS[self.type]()
        else:
            self.success = False
            self.error_message = "Not a valid type of request."



