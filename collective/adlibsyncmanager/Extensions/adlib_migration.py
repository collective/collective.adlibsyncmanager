#
# Adlib API migration
#

def migrate(self):
    from collective.adlibsyncmanager.migrator import APIMigrator
    
 
    folder = "nl/collectie"
    art_list = []

    #
    # Define image folder
    #
    IMAGE_FOLDER = ""

    type_to_create = ""
    set_limit = 100000
    
    #Create the migrator
    migrator = APIMigrator(self, folder, IMAGE_FOLDER, type_to_create, set_limit, art_list)
    
    #Finally migrate
    print("=== Starting Migration. ===")
    migrator.start_migration()
    
    print "Skipped list:"
    print migrator.skipped_ids

    if migrator.success:
        return "=== Migration sucessfull for running type '%s'. Created %d items (%d errors and %d skipped) ==="%(type_to_create, migrator.created, migrator.errors, migrator.skipped)
    else:
        return "!=== Migration unsucessfull for running type '%s' ==="%(type_to_create)
