#
# Adlib API migration
# Extension

from datetime import datetime, timedelta
from plone.registry.record import Record
from plone.registry import field
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

def migrate(self):
    from collective.adlibsyncmanager.sync_mechanism import SyncMechanism
    folder = "nl"

    #
    # Create or GET registry record
    #
    registry = getUtility(IRegistry)
    try:
        last_request_successful = registry.records['last_request_successful'].value
        last_creation_request_successful = registry.records['last_creation_request_successful'].value
        
        last_successful_date = registry.records['last_successful_date'].value
        last_successful_creation_date = registry.records['last_successful_creation_date'].value
        
        request_period = registry.records['request_period'].value
        print "Last request successful %s" % (last_request_successful)
        print "Last creation request successful %s" % (last_creation_request_successful)
        
        print "\nLast successfull date %s" % (last_successful_date)
        print "Last creation successful date %s\n" %(last_successful_creation_date)
        
        print "Request period %smin" % (str(request_period))
    except:
        print "Create new records!"
        ten_days_ago = datetime.today() - timedelta(days = 1)
        last_date = ten_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        unicode_date = u"%s" % (last_date)

        registry.records['last_request_successful'] = Record(field.Bool(title=u"last_request_successful"), False)
        registry.records['last_creation_request_successful'] = Record(field.Bool(title=u"last_creation_request_successful"), False)
        
        registry.records['last_successful_date'] = Record(field.Text(title=u"last_successful_date"), unicode_date)
        registry.records['last_successful_creation_date'] = Record(field.Text(title=u"last_successful_creation_date"), unicode_date)

        registry.records['request_period'] = Record(field.Int(title=u"request_period"), 1)
        last_request_successful = False
        last_successful_date = unicode_date
        request_period = 1
    
    #
    #Define date based on last request
    #
    if last_request_successful:
        one_minute_ago = datetime.today() - timedelta(minutes = request_period)
        date = one_minute_ago.strftime('%Y-%m-%d %H:%M:%S')
    else:
        date = last_successful_date

    if last_creation_request_successful:
        one_minute_ago = datetime.today() - timedelta(minutes = request_period)
        creation_date = one_minute_ago.strftime('%Y-%m-%d %H:%M:%S')
    else:
        creation_date = last_successful_creation_date
    
    #
    # Define request type
    #
    request_type = "test"


    #
    # Define log path
    #
    
    log_path = "/Users/AG/Projects/NewTeylersMuseum/adlib_sync.log"
    log_stage_path = "/var/www/teylers-stage/adlib_sync/adlib_sync.log"

    #Create the migrator
    migrator = APIMigrator(self, portal, folder, image_folder, type_to_create="art_list", set_limit=0, art_list=[])
    updater = Updater(migrator)
    sync = SyncMechanism(self, date, creation_date, request_type, folder, log_stage_path)
    
    print("=== Starting Sync. ===")

    # # # # # # # # #

    sync.start_sync()
    
    # # # # # # # # #


    if sync.creation_success and sync.success:
        # Update last_successful_request
        sync_date_unicode = u"%s" % (sync.date)
        sync_creation_date_unicode = u"%s" % (sync.creation_date)
        registry.records['last_request_successful'] = Record(field.Bool(title=u"last_request_successful"), True)
        registry.records['last_successful_date'] = Record(field.Text(title=u"last_successful_date"), sync_date_unicode)

        registry.records['last_creation_request_successful'] = Record(field.Bool(title=u"last_creation_request_successful"), True)
        registry.records['last_successful_creation_date'] = Record(field.Text(title=u"last_successful_creation_date"), sync_creation_date_unicode)

        registry.records['request_period'] = Record(field.Int(title=u"request_period"), request_period)


        #
        # Store last successful request
        #
        return "=== Sync Successfull ===\nObjects updated: %s\nObjects created: %s\nObjects skipped: %s\nErrors: %s" % (sync.updated, sync.created, sync.skipped, sync.errors)
    
    elif sync.creation_success:
        # Update last_creation_request_successful
        sync_creation_date_unicode = u"%s" % (sync.creation_date)
        registry.records['last_creation_request_successful'] = Record(field.Bool(title=u"last_creation_request_successful"), True)
        registry.records['last_successful_creation_date'] = Record(field.Text(title=u"last_successful_date"), sync_creation_date_unicode)
        registry.records['request_period'] = Record(field.Int(title=u"request_period"), request_period)

        #
        # Store last successful request
        #
        return "!=== Sync for Creation successfull ===\nObjects updated: %s\nObjects created: %s\nObjects skipped: %s\nErrors: %s" % (sync.updated, sync.created, sync.skipped, sync.errors)

    elif sync.success:
        # Update last_request_successful
        sync_date_unicode = u"%s" % (sync.date)
        registry.records['last_request_successful'] = Record(field.Bool(title=u"last_request_successful"), True)
        registry.records['last_successful_date'] = Record(field.Text(title=u"last_successful_date"), sync_date_unicode)
        registry.records['request_period'] = Record(field.Int(title=u"request_period"), request_period)

        #
        # Store last successful request
        #
        return "!=== Sync for Modification successfull ===\nObjects updated: %s\nObjects created: %s\nObjects skipped: %s\nErrors: %s" % (sync.updated, sync.created, sync.skipped, sync.errors)

    else:
        sync_date_unicode = u"%s" % (sync.date)
        sync_creation_date_unicode = u"%s" % (sync.creation_date)

        registry.records['last_request_successful'] = Record(field.Bool(title=u"last_request_successful"), False)
        registry.records['last_creation_request_successful'] = Record(field.Bool(title=u"last_creation_request_successful"), False)

        registry.records['last_successful_date'] = Record(field.Text(title=u"last_successful_date"), sync_date_unicode)
        registry.records['last_successful_creation_date'] = Record(field.Text(title=u"last_successful_creation_date"), sync_creation_date_unicode)

        registry.records['request_period'] = Record(field.Int(title=u"request_period"), request_period)

        return "=== Sync Unsuccessfull ===\nObjects updated: %s\nObjects created: %s\nObjects skipped: %s\nErrors: %s" % (sync.updated, sync.created, sync.skipped, sync.errors)
    return True





        
