#!/usr/bin/python
# -*- coding: utf-8 -*-

# Adlib API migration
# Extension

from datetime import datetime, timedelta
from plone.registry.record import Record
from plone.registry import field
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
import transaction
import smtplib


COLLECTIONS = [
    'ChoiceMunten',
    'ChoiceGeologie',
    'ChoiceKunst',
    'ChoiceInstrumenten',
    'ChoiceBooks'
]

def send_fail_email():
    """
    Send email if sync fails
    """
    
    sender = "andre@intk.com"
    receivers = ['andre@goncalves.me', 'andre@itsnotthatkind.org']

    subject = "Sync mechanism - Database FAIL"        
    msg = "Failed to commit that sync is complete.\nDate: %s" %(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, msg)
    except:
        self.write_log_details("=== ! Send email failed ===\nEmail msg: %s" %(msg))

def sync(self):

    FOLDER = "nl"
    REQUEST_TYPE = "run"
    LOG_PATH = "/var/www/teylers/sync-log/adlib_sync.log"

    from collective.adlibsyncmanager.TM.sync_mechanism_rev_v2 import SyncMechanism
    from collective.adlibsyncmanager.migrator import APIMigrator
    from collective.adlibsyncmanager.updater import Updater
    from collective.adlibsyncmanager.TM.migrator import Migrator

    #
    # Create the migrator
    #
    migrator = APIMigrator(self, FOLDER, "", REQUEST_TYPE)
    updater = Updater(migrator)
    teylers_migrator = Migrator(updater)


    #
    # Get registry entries
    #    
    registry = getUtility(IRegistry)

    try:
        sync_request_details = registry.records['sync_request_details'].value
    except:
        # Records do not exist in the registry
        print "Create new records in the registry."

        sync_request_details = {}
        sync_request_details['sync_complete'] = True

        ten_days_ago = datetime.today() - timedelta(days = 1)
        last_date = ten_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        unicode_date = u"%s" % (last_date)

        for collection in COLLECTIONS:

            sync_request_details[collection] = {
                "creation": {
                    "last_request_success": False,
                    "last_successful_date": unicode_date
                },
                "modification": {
                    "last_request_success": False,
                    "last_successful_date": unicode_date
                }
            }

        registry.records['sync_request_details'] = Record(field.Dict(title=u"sync_request_details"), sync_request_details)


    options = {
        "teylers_migrator": teylers_migrator, 
        "sync_request_details": sync_request_details,
        "request_type": REQUEST_TYPE,
        "collections": COLLECTIONS,
        "log_path": LOG_PATH,
        "folder": FOLDER
    }

    if sync_request_details["sync_complete"]:
        sync_request_details['sync_complete'] = False
        registry.records['sync_request_details'] = Record(field.Dict(title=u"sync_request_details"), sync_request_details)
        transaction.get().commit()

        sync = SyncMechanism(self, options)

        # # # # # # # # #

        sync.sync_created()
        sync.sync_modified()

        # # # # # # # # #

        """print sync.sync_request_details"""
        sync.sync_request_details['sync_complete'] = True
        registry.records['sync_request_details'] = Record(field.Dict(title=u"sync_request_details"), sync.sync_request_details)
        try:
            transaction.get().commit()
        except:
            transaction.abort()
            sync.sync_request_details['sync_complete'] = True
            registry.records['sync_request_details'] = Record(field.Dict(title=u"sync_request_details"), sync.sync_request_details)
            send_fail_email()

    else:
        """
        print "\n\nPREVIOUS SYNC IS NOT COMPLETE - SKIP\n\n"
        """
        pass

    #
    # Check results
    #

    return True

        