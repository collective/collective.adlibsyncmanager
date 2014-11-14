#
# Adlib API migration
#

def migrate(self):
    from collective.adlibsyncmanager.api_migrator import APIMigrator
    
 
    folder = "nl/collectie/schilderijen"
    art_list = []

    #
    # Define image folder
    #
    IMAGE_FOLDER = ""

    type_to_create = "add_translations"
    set_limit = len(art_list);
    
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
