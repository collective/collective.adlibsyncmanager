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

COLLECTION_OBJ_TYPE = {
    'ChoiceMunten': "coins",
    'ChoiceGeologie': "fossils",
    'ChoiceKunst':"kunst",
    'ChoiceInstrumenten':"instruments",
    'ChoiceBooks':"books"
}


class SyncMechanism:
    def __init__(self, portal, options):
        self.sync_request_details = options['sync_request_details']
        self.request_type = options['request_type']
        self.collections = options['collections']
        self.collection_type = ""

        self.migrator = options['teylers_migrator']
        self.migrator.IMPORT_TYPE = "sync"
        self.migrator.updater.IMPORT_TYPE = "sync"

        self.log_file = open(options['log_path'], 'a')

        self.portal = portal
        self.folder_path = options['folder'].split('/')
        self.image_folder = options['folder'].split('/')

        self.api_request = ""
        self.xmldoc = ""
        

    ###### UTILS ######
    def write_log_details(self, log, timestamp=datetime.today().isoformat()):
        if log:
            self.migrator.log_status(log)

            if 'TEST MODIFIED' in log:
                final_log = "%s" %(log)
            else:
                final_log = "[ %s ] - %s" %(timestamp, log)

            try:

                log_to_write = final_log.replace('__', '')
                #print log_to_write
                self.log_file.write(log_to_write+"\n")
            except:
                pass

    def send_fail_email(self, error_text, collection, date):
        """
        Send email if sync fails
        """
        
        sender = "andre@intk.com"
        receivers = ['andre@goncalves.me', 'andre@itsnotthatkind.org']

        subject = "Sync mechanism - FAIL"        
        msg = "Subject: %s\n\nCollection: %s failed to sync with Adlib.\nSync date: %s\nError details: %s" %(subject, collection, date, error_text)

        try:
            smtpObj = smtplib.SMTP('localhost')
            smtpObj.sendmail(sender, receivers, msg)
        except:
            self.write_log_details("=== ! Send email failed ===\nEmail msg: %s" %(msg))

    def get_record_by_priref(self, priref, collection):
        query = "priref='%s'"

        self.xmldoc = self.build_api_request(priref, query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)

        if len(records):
            return records[0]
        else:
            return None


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


    def test_query(self, collection, query, custom_date=""):
        timestamp = datetime.today().isoformat()

        search_query = query

        ###
        self.write_log_details("%s__ TEST MODIFIED RECORDS" %(collection))
        ###

        timestamp = datetime.today().isoformat()
        self.write_log_details("%s__## Test for one minute ago"%(collection), timestamp)
        last_hour_time = datetime.today() - timedelta(minutes = 1)
        last_hour_datetime = last_hour_time.strftime('%Y-%m-%d %H:%M:%S')
        self.xmldoc = self.build_api_request(last_hour_datetime, search_query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)
        self.write_log_details("%s__## %s records modified since %s" % (collection, str(self.records_modified), last_hour_datetime), timestamp)

        self.write_log_details("%s__## Test for one hour ago"%(collection), timestamp)
        _hour_time = datetime.today() - timedelta(minutes = 60)
        _hour_datetime = _hour_time.strftime('%Y-%m-%d %H:%M:%S')
        self.xmldoc = self.build_api_request(_hour_datetime, search_query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)
        self.records_modified = len(records)
        self.write_log_details("%s__## %s records modified since %s" % (collection, str(self.records_modified), _hour_datetime), timestamp)
        
        if custom_date:
            self.write_log_details("%s__## Test for custom date [%s]"%(collection, custom_date.strftime('%Y-%m-%d %H:%M:%S')), timestamp)
            _hour_datetime = custom_date.strftime('%Y-%m-%d %H:%M:%S')
            self.xmldoc = self.build_api_request(_hour_datetime, search_query, collection)
            self.migrator.updater.xml_root = self.xmldoc
            records = self.get_records(self.xmldoc)
            self.records_modified = len(records)
            self.write_log_details("%s__## %s records modified since %s" % (collection, str(self.records_modified), _hour_datetime), timestamp)
        
        ####
        self.write_log_details("%s__ TEST MODIFIED RECORDS FINISHED ##\n" %(collection))
        ###

        return records

    ###### TEST ######
    def test_modified(self):
        for collection in self.collections:
            
            print "\nTEST COLLECTION [%s]\n" %(collection)

            details = self.sync_request_details[collection]['modification']
            last_request_success = details['last_request_success']
            last_successful_date = details['last_successful_date']
            last_successful_date_datetime = datetime.strptime(last_successful_date, "%Y-%m-%d %H:%M:%S")
            today_datetime = datetime.today()
            today_datetime_one_minute_ago = today_datetime - timedelta(minutes=1)

            if last_request_success:
                if today_datetime > (last_successful_date_datetime + timedelta(minutes=120)):
                    # sync date + 1min + now-1min
                    last_successful_date_datetime_one_minute_after = last_successful_date_datetime + timedelta(minutes=1)
                    self.test_query(collection, "modification greater '%s'", last_successful_date_datetime_one_minute_after)
                    self.test_query(collection, "modification greater '%s'", today_datetime_one_minute_ago)
                else:
                    # sync now - 1min
                    self.test_query(collection, "modification greater '%s'", today_datetime_one_minute_ago)

                # sync()
                self.test_query(collection, "modification greater '%s'")
                success = True
            else:
                # sync same date
                self.test_query(collection, "modification greater '%s'", last_successful_date_datetime)
                success = True
                
            # Update sync details
            if success:
                self.sync_request_details[collection]['modification']['last_request_success'] = True
                self.sync_request_details[collection]['modification']['last_successful_date'] = today_datetime_one_minute_ago.strftime('%Y-%m-%d %H:%M:%S')
            else:
                self.sync_request_details[collection]['modification']['last_request_success'] = False
                self.sync_request_details[collection]['modification']['last_successful_date'] = last_successful_date 

        return True

    def test_created(self):
        pass

    ###### SYNC ######

    def get_query_records(self, collection, query, date):

        self.write_log_details("%s__SYNC RECORDS" %(collection))
        search_query = query

        self.xmldoc = self.build_api_request(date, search_query, collection)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)
        records_modified = len(records)

        if self.migrator.CREATE_NEW:
            self.write_log_details("%s__%s records created since %s" % (collection, str(records_modified), date))
        else:
            self.write_log_details("%s__%s records modified since %s" % (collection, str(records_modified), date))

        return records

    def sync_records(self, collection, query, run_type):
        details = self.sync_request_details[collection][run_type]
        last_request_success = details['last_request_success']
        last_successful_date = details['last_successful_date']
        last_successful_date_datetime = datetime.strptime(last_successful_date, "%Y-%m-%d %H:%M:%S")
        today_datetime = datetime.today()
        today_datetime_one_minute_ago = today_datetime - timedelta(minutes=1)
        today_one_minute_ago_date = today_datetime_one_minute_ago.strftime('%Y-%m-%d %H:%M:%S')

        success = False
        try:
            if last_request_success:
                if today_datetime > (last_successful_date_datetime + timedelta(minutes=2)):
                    # if last request took more than 2 min but succeeded
                    # SYNC: 
                    #   last sync date + 1min until now 
                    #   since now-1min
                    last_successful_date_datetime_one_minute_after = last_successful_date_datetime + timedelta(minutes=1)
                    records = self.get_query_records(collection, query, last_successful_date_datetime_one_minute_after.strftime('%Y-%m-%d %H:%M:%S'))
                    self.update_sync_records(records, collection)
                    records = self.get_query_records(collection, query, today_one_minute_ago_date)
                    self.update_sync_records(records, collection)
                else:
                    # SYNC: since now-1min
                    records = self.get_query_records(collection, query, today_one_minute_ago_date)
                    self.update_sync_records(records, collection)
            else:
                if today_datetime > (last_successful_date_datetime + timedelta(minutes=120)):
                    # if is stuck in the same date without succeeding for more than 1h30min
                    # SYNC: 
                    #   last sync date + 1min until now
                    #   since now-1min
                    last_successful_date_datetime_one_minute_after = last_successful_date_datetime + timedelta(minutes=1)
                    records = self.get_query_records(collection, query, last_successful_date_datetime_one_minute_after.strftime('%Y-%m-%d %H:%M:%S'))
                    self.update_sync_records(records, collection)
                    records = self.get_query_records(collection, query, today_one_minute_ago_date)
                    self.update_sync_records(records, collection)
                else:
                    # Sync failed. Try again:
                    # SYNC: 
                    #   since same date as the previous request
                    records = self.get_query_records(collection, query, last_successful_date)
                    self.update_sync_records(records, collection)

            success = True
        except Exception, e:
            exception_text = str(e)
            self.migrator.error("%s__ __Sync unexcepted exception on date: %s. Exception: %s" %(self.collection_type, today_one_minute_ago_date, exception_text))
            self.send_fail_email(exception_text, self.collection_type, today_one_minute_ago_date)
            success = False

        # Update sync details
        if success:
            self.sync_request_details[collection][run_type]['last_request_success'] = True
            self.sync_request_details[collection][run_type]['last_successful_date'] = today_one_minute_ago_date
        else:
            self.sync_request_details[collection][run_type]['last_request_success'] = False
            self.sync_request_details[collection][run_type]['last_successful_date'] = last_successful_date 

        return True

    def update_sync_records(self, records, collection):
        curr = 0
        total = len(records)
        for record in list(records):
            transaction.begin()

            curr += 1
            priref = self.migrator.get_priref(record)
            xml_record = self.get_record_by_priref(priref, self.collection_type)

            if xml_record is not None:
                if self.migrator.valid_priref(priref):
                    if priref:
                        plone_object = self.migrator.find_object_by_priref(priref)
                        if plone_object:
                            self.migrator.update_existing(priref, plone_object, xml_record)
                            
                            # Books special case
                            if collection == 'ChoiceBooks':
                                self.migrator.fix_book_title(plone_object)

                            # Fossils special case
                            elif collection == "ChoiceGeologie":
                                self.migrator.fix_fossil_name(plone_object)

                            obj_translated = self.migrator.update_object_translation(priref, plone_object, xml_record)
                            if obj_translated:
                                self.migrator.generate_special_translated_fields(obj_translated, xml_record)

                            self.write_log_details("%s__Updated %s / %s - [%s] - %s" %(str(collection), str(curr), str(total), str(priref), plone_object.absolute_url()))
                        else:
                            if self.migrator.CREATE_NEW:
                                created_object = self.migrator.create_new_object(priref, plone_object, xml_record)
                                if created_object:
                                    self.write_log_details("%s__Created %s / %s - [%s] - %s" %(str(collection), str(curr), str(total), str(priref), created_object.absolute_url()))
                                else:
                                    self.migrator.error("%s__ __Created object is None. Something went wrong."%(str(priref)))
                            else:
                                pass

                    else:
                        self.migrator.error("%s__ __Cannot find priref in XML record"%(str(curr)))
            else:
                #TODO log error
                pass

            transaction.commit()
        return True


    def run_created(self):
        """
            print "\n#### RUN CREATED ####"
        """
        self.migrator.CREATE_NEW = True

        for collection in self.collections:
            try:
                if collection == "ChoiceBooks":
                    CORE["object_number"] = ""
                    CORE["shelf_mark"] = "object_number"
                    self.migrator.CORE = CORE
                    self.migrator.updater.CORE = CORE
                else:
                    CORE["object_number"] = "object_number"
                    self.migrator.CORE = CORE
                    self.migrator.updater.CORE = CORE

                self.collection_type = collection
                
                query = "creation greater '%s'"

                self.migrator.object_type = COLLECTION_OBJ_TYPE[self.collection_type]
                self.sync_records(collection, query, 'creation')
            except Exception, e:
                exception_text = "\nUnexpected failure.\n" + str(e)
                self.migrator.error("%s__ __Sync unexpected failure on date: %s. Exception: %s" %(self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), exception_text))
                self.send_fail_email(exception_text, self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                self.sync_request_details[collection]['creation']['last_request_success'] = False

        return True

    def run_modified(self):
        """
        print "\n#### RUN MODIFIED ####"
        """
        self.migrator.CREATE_NEW = False

        for collection in self.collections:
            try:
                if collection == "ChoiceBooks":
                    CORE["object_number"] = ""
                    CORE["shelf_mark"] = "object_number"
                    self.migrator.CORE = CORE
                    self.migrator.updater.CORE = CORE
                else:
                    CORE["object_number"] = "object_number"
                    self.migrator.CORE = CORE
                    self.migrator.updater.CORE = CORE

                self.collection_type = collection
                
                query = "modification greater '%s'"

                self.migrator.object_type = COLLECTION_OBJ_TYPE[self.collection_type]
                self.sync_records(collection, query, 'modification')
            except Exception, e:
                exception_text = "\nUnexpected failure.\n" + str(e)
                self.migrator.error("%s__ __Sync unexpected failure on date: %s. Exception: %s" %(self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), exception_text))
                self.send_fail_email(exception_text, self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                self.sync_request_details[collection]['modification']['last_request_success'] = False

        return True


    ###### INIT ######

    def sync_created(self):
        self.migrator.init_log_files()
        if self.request_type == "test":
            self.test_created()
        else:
            self.run_created()

    def sync_modified(self):
        self.migrator.init_log_files()
        if self.request_type == "test":
            self.test_modified()
        else:
            self.run_modified()



