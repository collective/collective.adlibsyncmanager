#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""
from Acquisition import aq_parent, aq_inner

from plone import api

from z3c.relationfield.schema import RelationList

import fnmatch
from lxml import etree
import urllib2, urllib
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
from plone.multilingual.interfaces import ITranslationManager
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

from z3c.relationfield import RelationValue
from zope import component

XML_PATH = ""
TEST_OBJECT = 0

class IncomingLoanMigrator:
    
    def __init__(self, APIMigrator):
        self.api_migrator = APIMigrator

        self.collection_path_test = "/Users/AG/Projects/collectie-zm/single-incomingloan-entry-v01.xml"
        self.collection_path_stage = "/home/andre/collectie-zm-v1/xml/IncomingLoan-v01.xml"
        self.collection_path_prod = "/var/www/zm-collectie-v2/xml/incomingloans.xml"

    def get_object_from_instance(self, priref):
        # TODO
        object_folder = self.api_migrator.get_folder('nl/binnenkomende-bruiklenen/binnenkomende-bruiklenen')

        for brain in object_folder:
            item = object_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    def create_dirty_id(self, data):
        if data["priref"] != "":
            dirty_id = "%s" %(data['priref'])

        title = ""
        if data['loanRequest_general_loanNumber'] != "":
            title = data['loanRequest_general_loanNumber']

        if title != "":
            dirty_id = "%s %s" %(dirty_id, title)

        data['dirty_id'] = dirty_id
        return dirty_id

    def get_objects_fieldset(self, object_data, first_record):
        # objects_object
        """class IObjects(Interface):
            objectNumber = schema.TextLine(title=_(u'Object number'), required=False)
            title = schema.TextLine(title=_(u'Title'), required=False)
            status = schema.Choice(
                vocabulary=status_vocabulary,
                title=_(u'Status'),
                required=False
            )

            date = schema.TextLine(title=_(u'Date'), required=False)
            authoriser = schema.TextLine(title=_(u'Authoriser'), required=False)
            authorisationDate = schema.TextLine(title=_(u'Authorisation date'), required=False)
            conditions = schema.TextLine(title=_(u'Conditions'), required=False)
            insuranceValue = schema.TextLine(title=_(u'Insurance value'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""
        
        objects = []

        if len(first_record.findall('object-in')) > 0:
            for obj in first_record.findall('object-in'):
                new_obj = {
                    "objectNumber":"",
                    "title": "",
                    "status": "",
                    "date": "",
                    "authoriser": "",
                    "authorisationDate": "",
                    "conditions": "",
                    "insuranceValue": "",
                    "notes": ""
                }

                # objectNumber
                if obj.find('object-in.object_number') != None:
                    if obj.find('object-in.object_number').find('object_number') != None:
                        new_obj['objectNumber'] = obj.find('object-in.object_number').find('object_number').text

                # loanTitle
                if obj.find('object-in.title') != None:
                    new_obj['title'] = obj.find('object-in.title').text

                # status
                if obj.find('object-in.status') != None:
                    if obj.find('object-in.status').find('text') != None:
                        new_obj['status'] = obj.find('object-in.status').find('text').text

                # date
                if obj.find('object-in.status.date') != None:
                    new_obj['date'] = obj.find('object-in.status.date').text

                # authorise
                if obj.find('object-in.authoriser') != None:
                    if obj.find('object-in.authoriser_lender').find('name') != None:
                        new_obj['authoriser'] = obj.find('object-in.authoriser_lender').find('name').text

                # authorisationDate
                if obj.find('object-in.authorisation_date') != None:
                    new_obj['authorisationDate'] = obj.find('object-in.authorisation_date').text

                # conditions
                if obj.find('object-in.loan_conditions') != None:
                    new_obj['conditions'] = obj.find('object-in.loan_conditions').text

                # insuranceValue
                if obj.find('object-in.insurance_value') != None:
                    new_obj['miscellaneous_insuranceValue'] = obj.find('object-in.insurance_value').text

                # notes
                if obj.find('object-in.notes') != None:
                    new_obj['insuranceValue'] = obj.find('object-in.notes').text

                objects.append(new_obj)


        object_data['objects_object'] = objects


    def get_loan_request_fieldset(self, object_data, first_record):
        
        # loanRequest_general_loanNumber
        if first_record.find('loan_number') != None:
            object_data["loanRequest_general_loanNumber"] = first_record.find('loan_number').text

        # loanRequest_general_requester
        if first_record.find('lender') != None:
            if first_record.find('lender').find('name') != None:
                object_data["loanRequest_general_lender"] = first_record.find('lender').find('name').text

        # loanRequest_general_contact
        if first_record.find('requester.contact') != None:
            if first_record.find('requester.contact').find('name') != None:
                object_data["loanRequest_general_contact"] = first_record.find('requester.contact').find('name').text

        # loanRequest_internalCoordination_coordinator
        if first_record.find('co-ordinator') != None:
            if first_record.find('co-ordinator').find('name') !=  None:
                object_data["loanRequest_internalCoordination_coordinator"] = first_record.find('co-ordinator').find('name').text

        # loanRequest_internalCoordination_administrConcerned
        admins = []
        if len(first_record.findall('administration_concerned')) > 0:
            for admin in first_record.findall('administration_concerned'):
                admins.append({
                    "name": admin.text
                })
        
        object_data["loanRequest_internalCoordination_administrConcerned"] = admins

        # loanRequest_requestDetails_periodFrom
        if first_record.find('request.period.start') != None:
            object_data["loanRequest_requestDetails_periodFrom"] = first_record.find('request.period.start').text

        # loanRequest_requestDetails_to
        if first_record.find('request.period.end') != None:
            object_data["loanRequest_requestDetails_to"] = first_record.find('request.period.end').text

        # loanRequest_requestDetails_reason
        if first_record.find('request.reason') != None:
            if first_record.find('request.reason').find('text') != None:
                object_data["loanRequest_requestDetails_reason"] = first_record.find('request.reason').find('text').text

        # loanRequest_requestDetails_exhibition
        if first_record.find('exhibition') != None:
            if first_record.find('exhibition').find('title') != None:
                object_data["loanRequest_requestDetails_exhibition"] = first_record.find('exhibition').find('title').text

        # loanRequest_requestLetter_date
        if first_record.find('request.date') != None:
            object_data["loanRequest_requestLetter_date"] = first_record.find('request.date').text

        # loanRequest_requestLetter_digRef
        if first_record.find('request-in.reference') != None:
            object_data["loanRequest_requestLetter_digRef"] = first_record.find('request-in.reference').text

        # loanRequest_requestConfirmation_template
        if first_record.find('request-in.confirmation.template') != None:
            if first_record.find('request-in.confirmation.template').find('text') != None:
                object_data["loanRequest_requestConfirmation_template"] = first_record.find('request-in.confirmation.template').find('text').text

        # loanRequest_requestConfirmation_date
        if first_record.find('request-in.confirmation.date') != None:
            object_data["loanRequest_requestConfirmation_date"] = first_record.find('request-in.confirmation.date').text

        # loanRequest_requestConfirmation_digRef
        if first_record.find('request-in.confirmation.referenc') != None:
            object_data["loanRequest_requestConfirmation_digRef"] = first_record.find('request-in.confirmation.referenc').text


    def get_object(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",

            # Loan request
            'loanRequest_general_loanNumber':"",
            'loanRequest_general_lender':"",
            'loanRequest_general_contact':"",
            'loanRequest_internalCoordination_coordinator':"",
            'loanRequest_internalCoordination_administrConcerned':[],
            'loanRequest_requestDetails_periodFrom':"",
            'loanRequest_requestDetails_to':"",
            'loanRequest_requestDetails_reason':"",
            'loanRequest_requestDetails_exhibition':"",
            'loanRequest_requestLetter_date':"",
            'loanRequest_requestLetter_digRef':"",
            'loanRequest_requestConfirmation_template':"",
            'loanRequest_requestConfirmation_date':"",
            'loanRequest_requestConfirmation_digRef':"",

            # Objects
            'objects_object': [],

            # Contract 
            'contract_contractDetails_requestPeriodFrom': "",
            'contract_contractDetails_to': "",
            'contract_contractDetails_conditions': "",
            'contract_contractDetails_notes': [],
            'contract_contractLetter_template': "",
            'contract_contractLetter_date': "",
            'contract_contractLetter_digRef': "",
            'contract_contractLetter_signedReturned': "",
            'contract_contractLetter_signedReturnedDigRef': "",
            'contract_conditionReport_template': "",
            'contract_conditionReport_date': "",
            'contract_conditionReport_digRef': "",
            'contract_extension': [],

            # Correspondence
            'correspondence_otherCorrespondence': [],

            # Transport
            'transport_despatchDetails': [],
            'transport_entryDetails': []

        }   

        # Title and Author]
        data['priref'] = priref

        try:
            ###
            ### Loan request
            ###
            self.get_loan_request_fieldset(data, record)
        except:
            raise

        try:
            ###
            ### Objects
            ###
            self.get_objects_fieldset(data, record)
        except:
            raise

        try:
            ###
            ### Contract
            ###
            self.api_migrator.get_contract_fieldset(data, record)
        except:
            raise

        try:
            ###
            ### Correspondence
            ###
            self.api_migrator.get_correspondence_fieldset(data, record)
        except:
            raise

        self.create_dirty_id(data)
            
        return data

    def create_object(self, data):
        transaction.begin()
        
        ## TODO
        container = self.api_migrator.get_folder('nl/binnenkomende-bruiklenen/binnenkomende-bruiklenen')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Incoming loan already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_object_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if data['loanRequest_general_loanNumber'] != "":
                        title = data['loanRequest_general_loanNumber']
                    else:
                        title = dirty_id

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="IncomingLoan",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_object(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Incoming loan %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Incoming loan already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_object (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped incoming loan: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def update_object(self, obj, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(obj, key):
                    setattr(obj, key, value)

        print "Incoming loan fields updated!"
        return True

    def import_objects(self):

        collection_path_test = self.collection_path_test
        collection_path_stage = self.collection_path_stage
        collection_path_prod = self.collection_path_prod

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_object(priref, obj, True)
                    # Create object
                    self.create_object(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Incoming loan failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Incoming loan failed unexpected" %(timestamp)
                raise

        self.success = True
        return True


    def update_objects(self):
        collection_path_test = self.collection_path_test
        collection_path_stage = self.collection_path_stage
        collection_path_prod = self.collection_path_prod

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "Updating %s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    current_object = self.get_object_from_instance(priref)
                    if current_object != None:
                        data = self.get_object(priref, obj, False)
                        self.update_object(current_object, data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Incoming loan failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Incoming loan failed unexpected" %(timestamp)
                raise

        self.success = True
        return True


    def start(self):

        self.run_type = "import_objects"

        print "\n[ Run for type: %s ]\n" %(self.run_type)

        if self.run_type == "import_objects":
            self.import_objects()

        elif self.run_type == "update_objects":
            self.update_objects()


        return True
