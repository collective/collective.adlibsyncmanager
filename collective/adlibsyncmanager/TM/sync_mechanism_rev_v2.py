#!/usr/bin/python
# -*- coding: utf-8 -*-


#
# Adlib sync mechanism by Andre Goncalves
#

import transaction
from datetime import datetime, timedelta
import urllib2, urllib
import requests
from plone.i18n.normalizer import idnormalizer
from lxml import etree
from plone.app.textfield.value import RichTextValue
from Products.CMFCore.utils import getToolByName
import re
import sys
import smtplib
import plone.api

from .teylers_sync_core import CORE


# SET ORGANIZATION
ORGANIZATION = "cmu"

VALID_TYPES = ['test', 'sync_date']
API_ALL = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacximages/wwwopac.ashx?database=%s&search=%s&limit=0"
API_COLLECTION_REQUEST_COLLECT = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacximages/wwwopac.ashx?database=collect&search=%s&limit=1000"
API_COLLECTION_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacximages/wwwopac.ashx?%s&limit=0"
API_COLLECTION_REQUEST_PRIREF = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacximages/wwwopac.ashx?database=%s&search=%s&limit=0"

API_DELETED_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacximages/wwwopac.ashx?database=%s&command=getdeletedrecords&datefrom=%s"
API_IMAGES_REQUEST = "http://"+ORGANIZATION+".adlibhosting.com/wwwopacximages/wwwopac.ashx?database=collect&command=getcontent&server=images&value=%s&imageformat=jpg"


COLLECTION_OBJ_TYPE = {
    'beeldende kunst 1850 - heden': "database=collect&search=collection='"+urllib.quote('beeldende kunst 1850 - heden')+"'",
    'collect': "collect",
    #'stadsgeschiedenis': "database=collect&search=collection='"+urllib.quote('stadsgeschiedenis')+"'",
    #'kostuums':"database=collect&search=collection='"+urllib.quote('kostuums')+"'",
    #'intk':"database=collect&search=all",
    #'beeldende kunst':"database=collect&search=collection='"+urllib.quote('beeldende kunst')+"'",
    #"prenten en tekeningen": "database=collect&search=collection='"+urllib.quote("prenten en tekeningen")+"'-'"+urllib.quote("beeldende kunst 1850 - heden")+"'",
    #'onedele metalen':"database=collect&search=collection='"+urllib.quote('onedele metalen')+"'",
    #'edele metalen': "database=collect&search=collection='"+urllib.quote('edele metalen')+"'",
    #'beeldhouwkunst tot 1850': "database=collect&search=collection='"+urllib.quote('beeldhouwkunst tot 1850')+"'",
    #'schilderkunst tot 1850': "database=collect&search=collection='"+urllib.quote('schilderkunst tot 1850')+"'",
    #'meubelen tot 1900': "database=collect&search=collection='"+urllib.quote('meubelen tot 1900')+"'",
    #'van baaren': "database=collect&search=acquisition.source='"+urllib.quote('Stichting van Baaren Museum')+"'",
    #'kunstnijverheid': "database=collect&search=collection='"+urllib.quote('kunstnijverheid')+"'",
    #'bruna': "database=bruna&search=all",
    #'rsa': "database=rsa&search=all",
}

TOTAL_TIMES = 0

class SyncMechanism:
    def __init__(self, portal, options):
        self.sync_request_details = options['sync_request_details']
        self.request_type = options['request_type']
        self.collections = options['collections']
        self.collection_type = ""
        self.sync_images = False
        self.translate_objects = True

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
            timestamp = datetime.today().isoformat()
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

        self.xmldoc = self.build_api_request(priref, query, collection, True)
        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)

        if len(records):
            return records[0]
        else:
            return None

    def build_api_request_prod(self, date):
        search = date
        quoted_query = urllib.quote(search)

        self.api_request = API_COLLECTION_REQUEST_COLLECT % (quoted_query)
        req = urllib2.Request(self.api_request)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)
        return doc

    def get_all_records(self, collection, priref="collection='"+urllib.quote('beeldende kunst 1850 - heden')+"'&fields=reproduction.reference"):
        self.api_request = API_ALL % (collection, priref)
        req = urllib2.Request(self.api_request)
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib2.urlopen(req)
        doc = etree.parse(response)
        return doc

    def build_api_request(self, request_date, search_query, collection, getpriref=False):
        # collection = database=etc
        # query = all, modification
        # date = test_collection
        search = search_query

        if not getpriref:
            request_date = request_date

        if request_date != "test_collection" or (getpriref == True):
            search = search % (request_date)
        quoted_query = urllib.quote(search)

        if request_date == "test_collection" or (getpriref == True):
            collection = COLLECTION_OBJ_TYPE[collection]
        
        if not getpriref:
            self.api_request = API_COLLECTION_REQUEST % (collection)
        else:
            if collection in ['database=bruna&search=all']:
                self.api_request = API_COLLECTION_REQUEST_PRIREF % ('bruna', quoted_query)
            elif collection in ['database=rsa&search=all']:
                self.api_request = API_COLLECTION_REQUEST_PRIREF % ('rsa', quoted_query)
            else:
                self.api_request = API_COLLECTION_REQUEST_PRIREF % ('collect', quoted_query)
        
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

    def get_query_records(self, collection, query, date, prod=False):

        # collection = database=etc
        # query = all
        # date = test_collection

        self.write_log_details("%s__SYNC RECORDS" %(collection))
        search_query = query

        if not prod:
            self.xmldoc = self.build_api_request(date, search_query, collection)
        else:
            search_date = "modification greater '%s'" %(date)
            self.xmldoc = self.build_api_request_prod(search_date)

        self.migrator.updater.xml_root = self.xmldoc
        records = self.get_records(self.xmldoc)
        records_modified = len(records)

        if date == "test_collection":
            self.write_log_details("%s__ %s records to be tested for the collection" % (collection, str(records_modified)))
        elif prod:
            self.write_log_details("%s__ %s records modified since '%s'" % (collection, str(records_modified), date))
        else:
            if self.migrator.CREATE_NEW:
                self.write_log_details("%s__ %s records created since %s" % (collection, str(records_modified), date))
            else:
                self.write_log_details("%s__ %s records modified since %s" % (collection, str(records_modified), date))

        return records

    def sync_records(self, collection, query, run_type):
        if run_type in ["test_collection", "test_collection_prod"]:
            if run_type == "test_collection_prod":
                today_datetime = datetime.today()
                today_datetime_one_minute_ago = today_datetime - timedelta(minutes=1)
                today_one_minute_ago_date = today_datetime_one_minute_ago.strftime('%Y-%m-%d %H:%M:%S')
                records = self.get_query_records(collection, query, today_one_minute_ago_date, True)
            else:
                records = self.get_query_records(collection, query, "test_collection")
            self.update_sync_records(records, collection)
            return True
        else: 
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

    def get_object_images(self, plone_object):

        images = []
        slideshow = None

        if 'slideshow' in plone_object:
            slideshow = plone_object.get('slideshow', None)
            if slideshow:
                for sitem in slideshow:
                    item = slideshow[sitem]
                    if item.portal_type == 'Image':
                        images.append(item)
            else:
                return images

        return images, slideshow
    
    def get_reproduction_references_all(self, xml_record):

        references = []

        if xml_record.findall('Reproduction') != None:
            for reference in xml_record.findall('Reproduction'):
                if reference.find('reproduction.reference') != None:
                    reference_path = reference.find('reproduction.reference').text

                    if reference_path:
                        reference_split = reference_path.split('\\')
                        if reference_split:
                            image_name = reference_split[-1]
                        else:
                            image_name = reference_path

                        new_reference = {"path": reference_path, "name": image_name}
                        references.append(new_reference)

        return references

    def get_reproduction_references(self, xml_record):

        references = []

        if xml_record.findall('Reproduction') != None:
            for reference in xml_record.findall('Reproduction'):
                if reference.find('reproduction.reference') != None:
                    if reference.find('reproduction.reference').find('reference_number') != None:
                        reference_path = reference.find('reproduction.reference').find('reference_number').text

                        if reference_path:
                            reference_split = reference_path.split('\\')
                            if reference_split:
                                image_name = reference_split[-1]
                            else:
                                image_name = reference_path

                            image_title = ""
                            image_description = ""

                            if reference.find('reproduction.reference').find('title') != None:
                                if reference.find('reproduction.reference').find('title').find('value') != None:
                                    image_title = reference.find('reproduction.reference').find('title').find('value').text
                            if reference.find('reproduction.reference').find('description') != None:
                                image_description = reference.find('reproduction.reference').find('description').text

                            if image_name:
                                normalized_id = idnormalizer.normalize(image_name, max_length=len(image_name))

                            new_reference = {"path": reference_path, "name": image_name, "title":image_title, "description": image_description, "_id": normalized_id}
                            references.append(new_reference)

        return references

    def download_image(self, url, priref, image_name):
        img_date = None
        try:
            img_request = requests.get(url)
            if img_request:
                img_data = img_request.content
                return img_data
            else:
                self.migrator.log_images("%s__%s__%s"%(priref, image_name, "Download image from API request invalid"))
                return None
        except:
            self.migrator.log_images("%s__%s__%s"%(priref, image_name, "Error while downloading image from API URL"))
            return None

        return img_data

    def sync_record_images(self, priref, plone_object, xml_record):

        # get reproduction images
        adlib_references = self.get_reproduction_references(xml_record)
        adlib_references_names = [ref['_id'] for ref in adlib_references]
        adlib_references_names_reversed = adlib_references_names[::-1]

        # get list of images in objects slideshow
        object_images, slideshow = self.get_object_images(plone_object)

        slideshow_content = {}
        for img in object_images:
            img_title = getattr(img, 'id', None)
            if img_title:
                slideshow_content[img_title] = img
            else:
                self.migrator.log_images("%s__%s__%s"%(priref, getattr(img, 'title', 'None'), "Error while getting Image content type title."))
                pass

        # Download image if not in objects slideshpw
        images_to_create = []
        images_to_update = []
        for ref in adlib_references:
            name = ref['_id']
            if name not in slideshow_content.keys():
                images_to_create.append(ref)
            else:
                images_to_update.append(ref)

        # Create/update new image
        for create_image in images_to_create:
            try:
                path = create_image['path']
                image_name = create_image['name']
                image_download_url = API_IMAGES_REQUEST %(path)
                image_file = self.download_image(image_download_url, priref, image_name)
                image_description = create_image['description']
                image_title = create_image['title']

                img_obj_created = self.migrator.add_image(image_name, image_file, priref, plone_object, True, False, True)

                if image_title:
                    setattr(img_obj_created, 'title', image_title)
                if image_description:
                    setattr(img_obj_created, 'description', image_description)

                slideshow_content[getattr(img_obj_created, 'id', '')] = img_obj_created
                self.migrator.log_images("%s__%s__%s"%(priref, image_name, "Image content type created."))
               
            except:
                self.migrator.log_images("%s__%s__%s"%(priref, create_image.get('name', 'None'), "Error while creating Image content type."))
                pass

        for update_image in images_to_update:
            try:
                _id = update_image['_id']
                slideshow_img = slideshow_content.get(_id, None)

                if slideshow_img:
                    image_description = update_image['description']
                    if image_description:
                        setattr(slideshow_img, 'description', image_description)
                    
                    image_title = update_image['title']
                    if image_title:
                        setattr(slideshow_img, 'title', image_description)

            except:
                self.migrator.log_images("%s__%s__%s"%(priref, update_image.get('name', 'None'), "Error while updating Image content type."))
                pass

        # Delete images
        to_delete = []
        for simg in slideshow_content:
            try:
                if simg not in adlib_references_names:
                    img_obj = slideshow_content[simg]
                    plone.api.content.delete(obj=img_obj)
                    self.migrator.log_images("%s__%s__%s"%(priref, simg, "Image content type deleted."))
                    to_delete.append(simg)
            except:
                self.migrator.log_images("%s__%s__%s"%(priref, simg, "Error while deleting Image content type."))
                pass

        for item_to_delete in to_delete:
            del slideshow_content[item_to_delete]

        # Fix order
        for ref_image in adlib_references_names_reversed:
            try:
                ref_img_obj = slideshow_content.get(ref_image, None)
                if ref_img_obj:
                    slideshow.moveObjectsToTop([getattr(ref_img_obj, 'id', None)])
                else:
                    self.migrator.log_images("%s__%s__%s"%(priref, ref_image, "Error while fixing the order of the images. Image not in slideshow."))
            except:
                self.migrator.log_images("%s__%s__%s"%(priref, ref_image, "Error while fixing the order of the images"))
                pass

        return True

    def generate_special_fields(self, priref, plone_object, xml_record):
        #title
        #lead_word
        #author
        #statement_of_responsibility
        #place_of_publication
        #year_of_publication

        documentation = []

        for doc in xml_record.findall('Documentation'):
            title = ""
            lead_word = ""
            statement_of_responsibility = ""
            place_of_publication = ""
            year_of_publication = ""
            authors = []

            if doc.find('documentation.title') != None:

                docxml = doc.find('documentation.title')
                if docxml.find('title') != None:
                    title = docxml.find('title').text

                if docxml.find('lead_word') != None:
                    if docxml.find('lead_word').find('value') != None:
                        lead_word = docxml.find('lead_word').find('value').text

                if docxml.find('year_of_publication') != None:
                    year_of_publication = docxml.find('year_of_publication').text

                if docxml.find('place_of_publication') != None:
                    if docxml.find('place_of_publication').find('value') != None:
                        place_of_publication = docxml.find('place_of_publication').find('value').text

                if docxml.find('statement_of_responsibility') != None:
                    if docxml.find('statement_of_responsibility').find('value') != None:
                        statement_of_responsibility = docxml.find('statement_of_responsibility').find('value').text

                for author in docxml.findall('author.name'):
                    if author.find('value') != None:
                        authors.append(author.find('value').text)

                new_author = {
                    "title":title,
                    "lead_word":lead_word,
                    "statement_of_responsibility":statement_of_responsibility,
                    "place_of_publication":place_of_publication,
                    "year_of_publication":year_of_publication,
                    "author":authors
                }

                documentation.append(new_author)

        setattr(plone_object, "documentation", documentation)
        return True

    def update_sync_records(self, records, collection, test=False):
        curr = 0
        total = len(records)

        for record in list(records):
    
            curr += 1
            priref = self.migrator.get_priref(record)

            failed_to_get = False

            try:
                if not test:
                    xml_record = self.get_record_by_priref(priref, self.collection_type)
                else:
                    xml_record = record
            except:
                failed_to_get = True
                pass

            if failed_to_get:
                try:
                    if not test:
                        xml_record = self.get_record_by_priref(priref, self.collection_type)
                    else:
                        xml_record = record
                except:
                    failed_to_get = True
                    self.migrator.error("%s__ __ Failed to get object from API after 2 requests."%(str(priref)))
                    pass

            if xml_record is not None:
                if self.migrator.valid_priref(priref):
                    try:
                        if priref:
                            plone_object = self.migrator.find_object_by_priref(priref)
                            if plone_object:
                                self.migrator.update_existing(priref, plone_object, xml_record)

                                if self.sync_images:
                                    self.sync_record_images(priref, plone_object, xml_record)

                                self.write_log_details("%s__ Updated %s / %s - [%s] - %s" %(str(collection), str(curr), str(total), str(priref), plone_object.absolute_url()))
                                
                                if self.translate_objects:
                                    obj_translated, is_translation_new = self.migrator.update_object_translation(priref, plone_object, xml_record, False)
                                    if not is_translation_new and self.sync_images and obj_translated:
                                        self.sync_record_images(priref, obj_translated, xml_record)

                                self.generate_special_fields(priref, plone_object, xml_record)
                                self.generate_special_fields(priref, obj_translated, xml_record)
                            else:
                                if self.migrator.CREATE_NEW:
                                    created_object = self.migrator.create_new_object(priref, plone_object, xml_record)
                                    if created_object:
                                        if self.sync_images:
                                            self.sync_record_images(priref, created_object, xml_record)

                                        self.write_log_details("%s__ Created %s / %s - [%s] - %s" %(str(collection), str(curr), str(total), str(priref), created_object.absolute_url()))

                                        if self.translate_objects:
                                            obj_translated, is_translation_new = self.migrator.update_object_translation(priref, created_object, xml_record)
                                            if not is_translation_new and self.sync_images and obj_translated:
                                                self.sync_record_images(priref, obj_translated, xml_record)

                                        self.generate_special_fields(priref, created_object, xml_record)
                                        self.generate_special_fields(priref, obj_translated, xml_record)
                                    else:
                                        self.migrator.error("%s__ __ Created object is None. Something went wrong."%(str(priref)))
                                else:
                                    pass
                        else:
                            self.migrator.error("%s__ __ Cannot find priref in XML record"%(str(curr)))
                    except Exception, e:
                        exception_text = str(e)
                        self.send_fail_email(exception_text, self.collection_type, "priref: %s" %(priref))
                        pass
            else:
                self.migrator.error("%s__ __ XML record is None"%(str(curr)))
                pass
            
            #transaction.get().commit()

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

                self.migrator.object_type = self.collection_type
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

                self.migrator.object_type = self.collection_type
                self.sync_records(collection, query, 'modification')
            except Exception, e:
                exception_text = "\nUnexpected failure.\n" + str(e)
                self.migrator.error("%s__ __Sync unexpected failure on date: %s. Exception: %s" %(self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), exception_text))
                self.send_fail_email(exception_text, self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                self.sync_request_details[collection]['modification']['last_request_success'] = False

        return True

    def sync_test_collection(self):
        
        print "\n#### TEST RUN COLLECTION ####"
    
        self.migrator.CREATE_NEW = True
        self.sync_images = True
        self.translate_objects = True

        for collection in self.collections:
            try:
                CORE["object_number"] = "object_number"
                self.migrator.CORE = CORE
                self.migrator.updater.CORE = CORE
                self.collection_type = collection

                self.migrator.object_type = self.collection_type
                
                query = ""
                self.sync_records(collection, query, 'test_collection')

            except Exception, e:
                exception_text = "\nUnexpected failure.\n" + str(e)
                self.migrator.error("%s__ __Sync unexpected failure on date: %s. Exception: %s" %(self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), exception_text))
                #self.send_fail_email(exception_text, self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                #self.sync_request_details[collection]['modification']['last_request_success'] = False
                raise

        return True

    def sync_test_prod(self):
        
        print "\n#### TEST PROD COLLECTION ####"
    
        self.migrator.CREATE_NEW = False
        self.sync_images = True
        self.translate_objects = True

        for collection in self.collections:
            try:
                CORE["object_number"] = "object_number"
                self.migrator.CORE = CORE
                self.migrator.updater.CORE = CORE
                self.collection_type = collection

                self.migrator.object_type = self.collection_type
                
                query = ""
                self.sync_records(collection, query, 'test_collection_prod')

            except Exception, e:
                exception_text = "\nUnexpected failure.\n" + str(e)
                self.migrator.error("%s__ __Sync unexpected failure on date: %s. Exception: %s" %(self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), exception_text))
                self.send_fail_email(exception_text, self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                #self.sync_request_details[collection]['modification']['last_request_success'] = False
                pass

        return True


    def find_reproductions(self):

        print "Find multiple reproductions"

        records_collect = self.get_records(self.get_all_records("collect"))
        records_rsa = self.get_records(self.get_all_records("rsa"))
        records_bruna = self.get_records(self.get_all_records("bruna"))
        print "Got records from all collections"

        reproductions = {}

        collections = {"collect": records_collect, "rsa": records_rsa, "bruna": records_bruna}
        total_records = 0

        for collection in collections.keys():
            total = len(collections[collection])
            curr = 0
            for record in collections[collection]:
                curr += 1
                total_records += 1
                
                priref = self.migrator.get_priref(record)

                try:
                    print "[%s][%s] Testing %s / %s reproductions. [idx: %s]" %(collection, priref, curr, total, total_records)

                    """xml_records = self.get_records(self.get_all_records(collection, "priref='%s'&fields=reproduction.reference"%(priref)))
                    if len(xml_records):
                        xml_record = xml_records[0]
                    else:
                        xml_record = None
                        print "[%s][%s] priref not found" %(collection, priref) """

                    images = self.get_reproduction_references_all(record)

                    for image in images:
                        if image['path'] not in reproductions.keys():
                            reproductions[image['path']] = {"total": 1, "records": [priref]}
                        else:
                            rep_total = reproductions[image['path']]["total"]
                            rep_total += 1
                            reproductions[image['path']]["total"] = rep_total
                            rep_records = reproductions[image['path']]["records"]
                            rep_records.append(priref)
                            reproductions[image['path']]["records"] = rep_records
                except:
                    print "[ERROR][%s][%s] Error while getting reproductions" %(collection, priref)
                    pass

        # Analyse
        repeated_images = [{key: reproductions[key]} for key in reproductions.keys() if reproductions[key]['total'] > 1]

        #print "\nReproductions:"
        #print reproductions

        print "\nRepeated images:"
        print repeated_images
        print "\nTotal repeated: %s" %(len(repeated_images))
        
        return True


    def find_reproductions_collect(self):

        print "Find multiple reproductions"

        records_collect = self.get_records(self.get_all_records("collect"))
        print "Got records from all collections"

        reproductions = {}

        collections = {"collect": records_collect}
        total_records = 0

        without_images = []
        more_than_one = []
        
        for collection in collections.keys():
            total = len(collections[collection])
            curr = 0
            for record in collections[collection]:
                curr += 1
                total_records += 1

                priref = self.migrator.get_priref(record)

                try:
                    print "[%s][%s] Testing %s / %s reproductions. [idx: %s]" %(collection, priref, curr, total, total_records)

                    """xml_records = self.get_records(self.get_all_records(collection, "priref='%s'&fields=reproduction.reference"%(priref)))
                    if len(xml_records):
                        xml_record = xml_records[0]
                    else:
                        xml_record = None
                        print "[%s][%s] priref not found" %(collection, priref) """

                    images = self.get_reproduction_references_all(record)

                    if not images:
                        without_images.append(priref)

                    if images and len(images) > 1:
                        more_than_one.append(priref)

                    for image in images:
                        if image['path'] not in reproductions.keys():
                            reproductions[image['path']] = {"total": 1, "records": [priref]}
                        else:
                            rep_total = reproductions[image['path']]["total"]
                            rep_total += 1
                            reproductions[image['path']]["total"] = rep_total
                            rep_records = reproductions[image['path']]["records"]
                            rep_records.append(priref)
                            reproductions[image['path']]["records"] = rep_records
                except:
                    print "[ERROR][%s][%s] Error while getting reproductions" %(collection, priref)
                    pass

        # Analyse
        #repeated_images = [{key: reproductions[key]} for key in reproductions.keys() if reproductions[key]['total'] > 1]

        print "Total reproductions: %s" %(len(reproductions))
        print "Total records without images: %s" %(len(without_images))
        print "Total records with more than one image: %s" %(len(more_than_one))
        print more_than_one[:10]
        # ['1608', '1610', '1943', '2643', '3308', '3902', '4070', '4075', '4248', '4737']
        #print "\nReproductions:"
        #print reproductions

        #print "\nRepeated images:"
        #print repeated_images
        #print "\nTotal repeated: %s" %(len(repeated_images))
        
        return True

    def sync_test_record(self):
        
        print "\n#### TEST RUN ####"
    
        self.migrator.CREATE_NEW = True
        self.sync_images = False

        for collection in self.collections:
            try:
                CORE["object_number"] = "object_number"
                self.migrator.CORE = CORE
                self.migrator.updater.CORE = CORE
                self.collection_type = collection

                self.migrator.object_type = "beeldende kunst 1850 - heden"
                
                TEST_PRIREF_MEISJE = "24409"
                TEST_PRIREF = "40923"

                #test records = 24409, 4687, 13303
                record = self.get_record_by_priref("24409", collection)
                self.update_sync_records([record], collection, True)

                record = self.get_record_by_priref("4687", collection)
                self.update_sync_records([record], collection, True)

                record = self.get_record_by_priref("13303", collection)
                self.update_sync_records([record], collection, True)

                record = self.get_record_by_priref("40923", collection)
                self.update_sync_records([record], collection, True)

                """record = self.get_record_by_priref("40923", collection)
                self.update_sync_records([record], collection, True)"""

            except Exception, e:
                #exception_text = "\nUnexpected failure.\n" + str(e)
                #self.migrator.error("%s__ __Sync unexpected failure on date: %s. Exception: %s" %(self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), exception_text))
                #self.send_fail_email(exception_text, self.collection_type, datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                #self.sync_request_details[collection]['modification']['last_request_success'] = False
                raise
                
        return True


    ###### INIT ######
    def test_run_prod(self):
        self.migrator.init_log_files()
        if self.request_type == "test":
            self.sync_test_prod()
        else:
            self.sync_test_prod()
        return True

    def test_run_collection(self):
        self.migrator.init_log_files()
        if self.request_type == "test":
            self.sync_test_collection()
        else:
            self.sync_test_collection()
        return True

    def test_run(self):
        self.migrator.init_log_files()
        if self.request_type == "test":
            self.sync_test_record()
        else:
            self.sync_test_record()
        return True

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



