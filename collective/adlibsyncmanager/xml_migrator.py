"""XML migration script by David Jonas
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""

from lxml import etree
import re
import urllib2
import AccessControl
import transaction
import time
import sys
from DateTime import DateTime
from plone.i18n.normalizer import idnormalizer
from Testing.makerequest import makerequest
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
    
# Folder where the images are (Do not forget to add a trailing slash)
IMAGE_FOLDER = ""

class ObjectItem:
    """Class to store an WorkObject from the xml file"""
    def __init__(self):
        self.title = ""
        self.name_of_artist = ""
        self.date_of_production = ""
        self.object_number = ""

class XMLMigrator:
    """ Gets an XML file, parses it and creates the content in the chosen plone instance """
 
    def __init__(self, portal, xmlFilePath, typeToCreate, folder):
        """Constructor that gets access to both the parsed file and the chosen portal"""
        print("INITIALIZING CONTENT MIGRATOR")
        #check if portal exists
        self.portal = portal
        
        #Parse the XML file
        self.xmlDoc = etree.parse(xmlFilePath)
        
        #Set the migration mode
        self.typeToCreate = typeToCreate
        
        #Save the path to the folder to migrate to
        self.folderPath = folder.split("/")
        
        #Initialize the counters for the log
        self.errors = 0 #Number of errors - failed to create an item
        self.created = 0 #Number of sucessfully created items
        self.skipped = 0 #Number of items skipped because another item with the same id already exists on that folder.
    
        #DEBUG
        self.fields = []
    
    
    def cleanUp(self):
        #self.xmlDoc.freeDoc()
        return
    
    def getContainer(self):
        #if there is no folder info, fail.
        if len(self.folderPath) == 0:
            print("Folder check failed")
            return None
        
        #Set the container to the root object of the portal
        container = self.portal
        
        #Navigate the folders creating them if necessary
        for folder in self.folderPath:
            if hasattr(container, folder):
                container = container[folder]
            else:
                print ("== Chosen folder " + folder + " does not exist. Creating new folder ==")
                container.invokeFactory(type_name="Folder", id=folder, title="migration of type: " + self.typeToCreate)
                container = container[folder]
            
        return container

    def getOrCreateFolder(self, container, folderId, publish):
        #Get a folder if it exists or create it if it doesn't
        if folderId != "":
            try:
                if hasattr(container, folderId):
                        container = container[folderId]
                else:
                    print ("== Creating new folder ==")
                    container.invokeFactory(type_name="Folder", id=folderId, title=folderId)
                    container = container[folderId]
                    
                    #publish the folder if needed
                    if publish:
                        container.portal_workflow.doActionFor(container, "publish", comment="content automatically published by migrationScript")
                    
                return container
            except:
                print("Folder %s could not be created: %s"%(folderId, sys.exc_info()[1]))
                return None
        else:
            return None

    def addTranslationToObject(self, _object, language):
        try:
            container = self.getContainer()
            dirty_object_id = idnormalizer.normalize(_object, max_length=len(_object))

            if hasattr(container, dirty_object_id):
                item_object = container[str(dirty_object_id)]
                item_object.addTranslation(language)
                item_translated = item_object.getTranslation(language)
                
                item_translated.title = item_object.title
                item_translated.description = item_object.description
                item_translated.reindexObject()
                item_translated.portal_workflow.doActionFor(item_translated, "publish", comment="content automatically published")
                item_translated.reindexObject()
                print "== Translation created =="
            else:
                print "Translation not created"
                return False

        except:
            print "Unexpected error on addTranslationToObject: ", sys.exc_info()[1]
            return False
            
    def addImageToSlideshow(self, image, object_id):
        try:
            container = self.getContainer()
            
            #dirtyWorkId = image.upper()
            #dirty_work_id = idnormalizer.normalize(unicode(dirtyWorkId, "utf-8"))

            filename = image.replace(' ', '-').upper()
            filename = filename + ".jpg"

            dirtyId = filename
            result = False

            transaction.begin()

            _id = idnormalizer.normalize(dirtyId)

            if hasattr(container, object_id):
                work_item = container[str(object_id)]
                if hasattr(work_item, 'slideshow'):
                    slideshow = work_item['slideshow']
                    if not hasattr(slideshow, _id):
                        print "Adding image to slideshow %s"%_id
                        slideshow.invokeFactory(type_name="Image", id=_id, title=filename)
                    else:
                        print "Image %s already exists, skipping"%filename
                        return True

                    image_item = slideshow[str(_id)]

                    imageFile = open(IMAGE_FOLDER + filename, "r")
                    imageData = imageFile.read()
                    image_item.edit(file=imageData)
                    imageFile.close()

                    image_item.processForm()
                    transaction.commit()

                    result = True
                    return work_item
                else:
                    print "Slideshow not created, skipping"
                    return False

        except:
            transaction.abort()
            print "Unexpected error on createImage: ", sys.exc_info()[1]
            return False


    def addImage(self, container, image):
        try:
            filename = image.split("\\")[2]
            dirtyId = filename
            result = False
            transaction.begin()
        
        
            id = idnormalizer.normalize(unicode(dirtyId, "utf-8"))
            
            #if not hasattr(container, str(id)):                                             #The processForm changes the id to the fileneame in lower case
            if not hasattr(container, filename.lower()): 
                #import pdb; pdb.set_trace()
                print "Adding a new image: %s"%filename
                container.invokeFactory(type_name="Image", id=id, title=filename)
            else:
                print "Image %s already exists, skipping"%filename
                return True
            
            item = container[str(id)]
            
            imageFile = open(IMAGE_FOLDER + filename.lower(), "r")
            imageData = imageFile.read()
            item.edit(file=imageData)
            imageFile.close()
            
            #import pdb; pdb.set_trace()
            item.processForm()
             
            transaction.commit()
            result = True
            return result
        except:
            transaction.abort()
            print "Unexpected error on createImage: ", sys.exc_info()[1]
            return False

    def addLeadImage(self, item, image):
        #set the lead image if necessary and if lead image product is installed
        if LEADIMAGE_EXISTS and image != "":
            #download and create the image
            try:
                imageFile = urllib2.urlopen(image)
                imageData = imageFile.read()
                urlSplit = image.split("/")
                filename = urlSplit[len(urlSplit)-1]
                
                #add the image as leadImage
                if ILeadImageable.providedBy(item):
                    field = aq_inner(item).getField(IMAGE_FIELD_NAME)
                    field.set(item, imageData, filename=filename)
                else:
                    print("Item type does not accept leadImage")
                
                #release the image file
                imageFile.close()
                return
            except:
                print "LeadImage URL not available. LeadImage not created because: (" + image + ")", sys.exc_info()[1]
                return
            
    def addLeadImageCaption(self, item, caption):
        #set the caption if necessary and if lead image product is installed
        if LEADIMAGE_EXISTS and caption != "":
            #add the caption
            try:
                if ILeadImageable.providedBy(item):
                    field = aq_inner(item).getField(IMAGE_CAPTION_FIELD_NAME) 
                    field.set(item, caption)
                else:
                    print("Item type does not accept leadImage therefore captions will be ignored")
            except:
                print "Error adding leadImage caption: ", sys.exc_info()[1]
        return


    def createWorkObject(self, obj):

        transaction.begin()
        container = self.getContainer()
        dirtyId = obj.object_number

        image_name = obj.object_number.lower()

        result = False

        try:
            new_name_of_artist = self.transformArtistName(obj.name_of_artist)
            obj.name_of_artist = new_name_of_artist

            _improved_id = dirtyId+" "+obj.title+" "+new_name_of_artist

            _id = idnormalizer.normalize(_improved_id, max_length=len(_improved_id))

            if hasattr(container, _id) and _id != "":
                self.skipped = self.skipped + 1
                print "Item already exists, reviewing fields"
                transaction.commit()
                return True

            if not hasattr(container, _id):
                print "NEW OBJECT FOUND. ADDING: %s"%_id

                obj_description = obj.name_of_artist
                if obj.date_of_production != "":
                    obj_description += ", "+obj.date_of_production
                
                container.invokeFactory(
                    type_name="Object",
                    id=_id,
                    title=obj.title,
                    description=obj_description
                    )

                item = container[_id]
                item.setText(obj_description)

                item.processForm()
                transaction.commit()
                
                result = True
                self.created = self.created + 1

                item.portal_workflow.doActionFor(item, "publish", comment="content automatically published")
                item.reindexObject()
                print("== Object published ==")
                
                object_item = self.addImageToSlideshow(image_name, _id)
                print("== Images added to slideshow ==")
                
                #self.addTranslationToObject(_improved_id, 'en')
                print("== Object translated ==")
                print("== Object created ==")
        except:
            self.errors = self.errors + 1
            print "Unexpected error on createObject (" +dirtyId+ "):", sys.exc_info()[1]
            transaction.abort()
            raise
            return result

        if not result:
            self.skipped = self.skipped + 1
            print("Skipped item: " + dirtyId)
        return result


    def transformArtistName(self, name):
        if name != "":
            name_without_year = re.sub(r'\([^)]*\)', '', name)
            name_separated = name_without_year.split(',')
            if len(name_separated) > 1:
                real_name = name_separated[1] + name_separated[0]
                return real_name
            else:
                return name_separated[0]
        else:
            return name

    def migrateTranslation(self, limit, language):

        art_list = ['ks 001', 'ks 002', 'ks 003', 'ks 004', 'ks 005', 'ks 006', 'ks 007', 'ks 008', 'ks 009', 'ks 010', 'ks 011', 'ks 013', 'ks 014', 'ks 016', 'ks 017', 'ks 019', 'ks 020', 'ks 021', 'ks 022', 'ks 023', 'ks 024', 'ks 025', 'ks 027', 'ks 028', 'ks 029', 'ks 030', 'ks 031', 'ks 032', 'ks 033', 'ks 034', 'ks 035', 'ks 036', 'ks 037', 'ks 038', 'ks 039', 'ks 041', 'ks 043', 'ks 044', 'ks 045', 'ks 046', 'ks 048', 'ks 049', 'ks 051', 'ks 052', 'ks 056', 'ks 062', 'ks 064', 'ks 065', 'ks 066', 'ks 067', 'ks 068', 'ks 069', 'ks 071', 'ks 072', 'ks 073', 'ks 076', 'ks 077', 'ks 078', 'ks 079', 'ks 080', 'ks 081', 'ks 082', 'ks 083', 'ks 085 2', 'ks 087', 'ks 088', 'ks 089', 'ks 090', 'ks 091', 'ks 092', 'ks 093', 'ks 094', 'ks 097', 'ks 098', 'ks 099', 'ks 100', 'ks 101', 'ks 103', 'ks 104', 'ks 105', 'ks 106', 'ks 108', 'ks 109', 'ks 110', 'ks 111', 'ks 112', 'ks 113', 'ks 114', 'ks 115', 'ks 116', 'ks 117', 'ks 118', 'ks 119', 'ks 121', 'ks 124', 'ks 125', 'ks 126', 'ks 127', 'ks 128', 'ks 129', 'ks 130', 'ks 131', 'ks 132', 'ks 133', 'ks 135', 'ks 136', 'ks 137', 'ks 138a', 'ks 139', 'ks 141', 'ks 142', 'ks 144', 'ks 145', 'ks 146', 'ks 148', 'ks 151', 'ks 156', 'ks 157', 'ks 160', 'ks 161', 'ks 165', 'ks 166', 'ks 167', 'ks 168', 'ks 169', 'ks 171', 'ks 174', 'ks 175', 'ks 176', 'ks 178', 'ks 180', 'ks 180a', 'ks 183', 'ks 186', 'ks 187', 'ks 190', 'ks 194', 'ks 195', 'ks 196', 'ks 1984 001', 'ks 1985 001', 'ks 1985 002', 'ks 1986 002', 'ks 1986 003', 'ks 1987 002', 'ks 1988 001', 'ks 1989 004', 'ks 1989 005', 'ks 1989 006', 'ks 1989 007', 'ks 1989 008', 'ks 1989 009', 'ks 1989 010', 'ks 1989 010_1', 'ks 1989 011', 'ks 1989 012', 'ks 1989 013', 'ks 1989 014', 'ks 1990 001', 'ks 1990 003', 'ks 1990 003a', 'ks 1990 004', 'ks 1990 005', 'ks 1990 007', 'ks 1990 008', 'ks 1990 009', 'ks 1990 010', 'ks 1990 012', 'ks 1990 013', 'ks 1990 014', 'ks 1990 015', 'ks 1990 016', 'ks 1990 023', 'ks 1991 002', 'ks 1991 003', 'ks 1992 001', 'ks 1992 002', 'ks 1994 001', 'ks 1994 br 001', 'ks 1994 br 004', 'ks 1995 004', 'ks 1996 002', 'ks 1996 003', 'ks 1996 004', 'ks 1997 01', 'ks 1998 001', 'ks 1998 002', 'ks 1998 003', 'ks 1999 002', 'ks 1999 003', 'ks 1999 004', 'ks 1999 005', 'ks 1999 006', 'ks 1999 007', 'ks 1999 008', 'ks 2000 001', 'ks 2000 002', 'ks 2000 003', 'ks 2000 004', 'ks 2000 005', 'ks 2000 007', 'ks 2000 008', 'ks 2001 001', 'ks 2001 002', 'ks 2001 003', 'ks 2001 004', 'ks 2001 005', 'ks 2003 002', 'ks 2004 001', 'ks 2005 001', 'ks 2006 006', 'ks 2008 001', 'ks 2009 001', 'ks 2010 001', 'ks 2010 002', 'ks 2011 001', 'ks 2012 001', 'ks 2014 003', 'ks 202', 'ks 206', 'ks 207', 'ks 208', 'ks 209', 'ks 210', 'ks 213', 'ks 216', 'ks 221', 'ks 222', 'ks 223', 'ks 224', 'ks 225', 'ks 225a', 'ks 226', 'ks 228', 'ks 229', 'ks 230', 'ks 237', 'ks 239', 'ks 241', 'ks 243', 'ks 244', 'ks 245', 'ks 246', 'ks 247', 'ks 248', 'ks 249', 'ks 250', 'ks 252', 'ks 255', 'ks 256', 'ks 258', 'ks 266', 'ks 276', 'ks 281', 'ks 282', 'ks 283', 'ks 284', 'ks 285', 'ks geen nummer 02', 'ks geen nummer', 'ks heshuizen', 'ks hulk', 'ks springer']

        root = self.xmlDoc.getroot()
        recordList = root.find("recordList")
        print "Found recordList"
        records = recordList.getchildren()
        print "Found "+str(len(records))+" records"
        
        limit = limit
        number = 0
        for record in records:
            if record.find('object_number') != None:
                object_number = record.find('object_number').text
                if object_number.lower() in art_list:
                    number += 1
                    if record.find('title') != None:
                        title = record.find('title').text
                    else:
                        title = ""

                    if record.find('creator') != None:
                        name_of_artist = record.find('creator').text
                    else:
                        name_of_artist = ""

                    new_name_of_artist = self.transformArtistName(name_of_artist)
                    name_of_artist = new_name_of_artist

                    _improved_id = object_number.lower()+" "+title+" "+name_of_artist

                    self.addTranslationToObject(_improved_id, language)
                    
                    if number >= limit:
                        return
                else:
                    #print "Skip art-work for now. No image available."
                    self.skipped += 1
            else:
                object_number = "Unknown"
        return

    def migrateImages(self):

        art_list = ['ks 001', 'ks 002', 'ks 003', 'ks 004', 'ks 005', 'ks 006', 'ks 007', 'ks 008', 'ks 009', 'ks 010', 'ks 011', 'ks 013', 'ks 014', 'ks 016', 'ks 017', 'ks 019', 'ks 020', 'ks 021', 'ks 022', 'ks 023', 'ks 024', 'ks 025', 'ks 027', 'ks 028', 'ks 029', 'ks 030', 'ks 031', 'ks 032', 'ks 033', 'ks 034', 'ks 035', 'ks 036', 'ks 037', 'ks 038', 'ks 039', 'ks 041', 'ks 043', 'ks 044', 'ks 045', 'ks 046', 'ks 048', 'ks 049', 'ks 051', 'ks 052', 'ks 056', 'ks 062', 'ks 064', 'ks 065', 'ks 066', 'ks 067', 'ks 068', 'ks 069', 'ks 071', 'ks 072', 'ks 073', 'ks 076', 'ks 077', 'ks 078', 'ks 079', 'ks 080', 'ks 081', 'ks 082', 'ks 083', 'ks 085 2', 'ks 087', 'ks 088', 'ks 089', 'ks 090', 'ks 091', 'ks 092', 'ks 093', 'ks 094', 'ks 097', 'ks 098', 'ks 099', 'ks 100', 'ks 101', 'ks 103', 'ks 104', 'ks 105', 'ks 106', 'ks 108', 'ks 109', 'ks 110', 'ks 111', 'ks 112', 'ks 113', 'ks 114', 'ks 115', 'ks 116', 'ks 117', 'ks 118', 'ks 119', 'ks 121', 'ks 124', 'ks 125', 'ks 126', 'ks 127', 'ks 128', 'ks 129', 'ks 130', 'ks 131', 'ks 132', 'ks 133', 'ks 135', 'ks 136', 'ks 137', 'ks 138a', 'ks 139', 'ks 141', 'ks 142', 'ks 144', 'ks 145', 'ks 146', 'ks 148', 'ks 151', 'ks 156', 'ks 157', 'ks 160', 'ks 161', 'ks 165', 'ks 166', 'ks 167', 'ks 168', 'ks 169', 'ks 171', 'ks 174', 'ks 175', 'ks 176', 'ks 178', 'ks 180', 'ks 180a', 'ks 183', 'ks 186', 'ks 187', 'ks 190', 'ks 194', 'ks 195', 'ks 196', 'ks 1984 001', 'ks 1985 001', 'ks 1985 002', 'ks 1986 002', 'ks 1986 003', 'ks 1987 002', 'ks 1988 001', 'ks 1989 004', 'ks 1989 005', 'ks 1989 006', 'ks 1989 007', 'ks 1989 008', 'ks 1989 009', 'ks 1989 010', 'ks 1989 010_1', 'ks 1989 011', 'ks 1989 012', 'ks 1989 013', 'ks 1989 014', 'ks 1990 001', 'ks 1990 003', 'ks 1990 003a', 'ks 1990 004', 'ks 1990 005', 'ks 1990 007', 'ks 1990 008', 'ks 1990 009', 'ks 1990 010', 'ks 1990 012', 'ks 1990 013', 'ks 1990 014', 'ks 1990 015', 'ks 1990 016', 'ks 1990 023', 'ks 1991 002', 'ks 1991 003', 'ks 1992 001', 'ks 1992 002', 'ks 1994 001', 'ks 1994 br 001', 'ks 1994 br 004', 'ks 1995 004', 'ks 1996 002', 'ks 1996 003', 'ks 1996 004', 'ks 1997 01', 'ks 1998 001', 'ks 1998 002', 'ks 1998 003', 'ks 1999 002', 'ks 1999 003', 'ks 1999 004', 'ks 1999 005', 'ks 1999 006', 'ks 1999 007', 'ks 1999 008', 'ks 2000 001', 'ks 2000 002', 'ks 2000 003', 'ks 2000 004', 'ks 2000 005', 'ks 2000 007', 'ks 2000 008', 'ks 2001 001', 'ks 2001 002', 'ks 2001 003', 'ks 2001 004', 'ks 2001 005', 'ks 2003 002', 'ks 2004 001', 'ks 2005 001', 'ks 2006 006', 'ks 2008 001', 'ks 2009 001', 'ks 2010 001', 'ks 2010 002', 'ks 2011 001', 'ks 2012 001', 'ks 2014 003', 'ks 202', 'ks 206', 'ks 207', 'ks 208', 'ks 209', 'ks 210', 'ks 213', 'ks 216', 'ks 221', 'ks 222', 'ks 223', 'ks 224', 'ks 225', 'ks 225a', 'ks 226', 'ks 228', 'ks 229', 'ks 230', 'ks 237', 'ks 239', 'ks 241', 'ks 243', 'ks 244', 'ks 245', 'ks 246', 'ks 247', 'ks 248', 'ks 249', 'ks 250', 'ks 252', 'ks 255', 'ks 256', 'ks 258', 'ks 266', 'ks 276', 'ks 281', 'ks 282', 'ks 283', 'ks 284', 'ks 285', 'ks geen nummer 02', 'ks geen nummer', 'ks heshuizen', 'ks hulk', 'ks springer']

        root = self.xmlDoc.getroot()
        recordList = root.find("recordList")
        print "Found recordList"
        records = recordList.getchildren()
        print "Found "+str(len(records))+" records"
        
        for record in records:
            if record.find('object_number') != None:
                object_number = record.find('object_number').text
                if object_number.lower() in art_list:
                    self.addImageToSlideshow(object_number.lower())
                else:
                    print "Skip art-work for now. No image available."
                    self.skipped += 1
            else:
                object_number = "Unknown"
        return

    def migratePublish(self):
        container = self.getContainer()
        for obj in container:
            obj = container[obj]
            obj.portal_workflow.doActionFor(obj, "publish", comment="content automatically published by migrationScript")
        return "=== Publication sucessfull. ==="


    def migrateLimit(self, limit):
        art_list = ['ks 001', 'ks 002', 'ks 003', 'ks 004', 'ks 005', 'ks 006', 'ks 007', 'ks 008', 'ks 009', 'ks 010', 'ks 011', 'ks 013', 'ks 014', 'ks 016', 'ks 017', 'ks 019', 'ks 020', 'ks 021', 'ks 022', 'ks 023', 'ks 024', 'ks 025', 'ks 027', 'ks 028', 'ks 029', 'ks 030', 'ks 031', 'ks 032', 'ks 033', 'ks 034', 'ks 035', 'ks 036', 'ks 037', 'ks 038', 'ks 039', 'ks 041', 'ks 043', 'ks 044', 'ks 045', 'ks 046', 'ks 048', 'ks 049', 'ks 051', 'ks 052', 'ks 056', 'ks 062', 'ks 064', 'ks 065', 'ks 066', 'ks 067', 'ks 068', 'ks 069', 'ks 071', 'ks 072', 'ks 073', 'ks 076', 'ks 077', 'ks 078', 'ks 079', 'ks 080', 'ks 081', 'ks 082', 'ks 083', 'ks 085 2', 'ks 087', 'ks 088', 'ks 089', 'ks 090', 'ks 091', 'ks 092', 'ks 093', 'ks 094', 'ks 097', 'ks 098', 'ks 099', 'ks 100', 'ks 101', 'ks 103', 'ks 104', 'ks 105', 'ks 106', 'ks 108', 'ks 109', 'ks 110', 'ks 111', 'ks 112', 'ks 113', 'ks 114', 'ks 115', 'ks 116', 'ks 117', 'ks 118', 'ks 119', 'ks 121', 'ks 124', 'ks 125', 'ks 126', 'ks 127', 'ks 128', 'ks 129', 'ks 130', 'ks 131', 'ks 132', 'ks 133', 'ks 135', 'ks 136', 'ks 137', 'ks 138a', 'ks 139', 'ks 141', 'ks 142', 'ks 144', 'ks 145', 'ks 146', 'ks 148', 'ks 151', 'ks 156', 'ks 157', 'ks 160', 'ks 161', 'ks 165', 'ks 166', 'ks 167', 'ks 168', 'ks 169', 'ks 171', 'ks 174', 'ks 175', 'ks 176', 'ks 178', 'ks 180', 'ks 180a', 'ks 183', 'ks 186', 'ks 187', 'ks 190', 'ks 194', 'ks 195', 'ks 196', 'ks 1984 001', 'ks 1985 001', 'ks 1985 002', 'ks 1986 002', 'ks 1986 003', 'ks 1987 002', 'ks 1988 001', 'ks 1989 004', 'ks 1989 005', 'ks 1989 006', 'ks 1989 007', 'ks 1989 008', 'ks 1989 009', 'ks 1989 010', 'ks 1989 010_1', 'ks 1989 011', 'ks 1989 012', 'ks 1989 013', 'ks 1989 014', 'ks 1990 001', 'ks 1990 003', 'ks 1990 003a', 'ks 1990 004', 'ks 1990 005', 'ks 1990 007', 'ks 1990 008', 'ks 1990 009', 'ks 1990 010', 'ks 1990 012', 'ks 1990 013', 'ks 1990 014', 'ks 1990 015', 'ks 1990 016', 'ks 1990 023', 'ks 1991 002', 'ks 1991 003', 'ks 1992 001', 'ks 1992 002', 'ks 1994 001', 'ks 1994 br 001', 'ks 1994 br 004', 'ks 1995 004', 'ks 1996 002', 'ks 1996 003', 'ks 1996 004', 'ks 1997 01', 'ks 1998 001', 'ks 1998 002', 'ks 1998 003', 'ks 1999 002', 'ks 1999 003', 'ks 1999 004', 'ks 1999 005', 'ks 1999 006', 'ks 1999 007', 'ks 1999 008', 'ks 2000 001', 'ks 2000 002', 'ks 2000 003', 'ks 2000 004', 'ks 2000 005', 'ks 2000 007', 'ks 2000 008', 'ks 2001 001', 'ks 2001 002', 'ks 2001 003', 'ks 2001 004', 'ks 2001 005', 'ks 2003 002', 'ks 2004 001', 'ks 2005 001', 'ks 2006 006', 'ks 2008 001', 'ks 2009 001', 'ks 2010 001', 'ks 2010 002', 'ks 2011 001', 'ks 2012 001', 'ks 2014 003', 'ks 202', 'ks 206', 'ks 207', 'ks 208', 'ks 209', 'ks 210', 'ks 213', 'ks 216', 'ks 221', 'ks 222', 'ks 223', 'ks 224', 'ks 225', 'ks 225a', 'ks 226', 'ks 228', 'ks 229', 'ks 230', 'ks 237', 'ks 239', 'ks 241', 'ks 243', 'ks 244', 'ks 245', 'ks 246', 'ks 247', 'ks 248', 'ks 249', 'ks 250', 'ks 252', 'ks 255', 'ks 256', 'ks 258', 'ks 266', 'ks 276', 'ks 281', 'ks 282', 'ks 283', 'ks 284', 'ks 285', 'ks geen nummer 02', 'ks geen nummer', 'ks heshuizen', 'ks hulk', 'ks springer']

        root = self.xmlDoc.getroot()
        recordList = root.find("recordList")
        print "Migration with limit: "+str(limit)
        print "Found recordList"
        records = recordList.getchildren()
        print "Found "+str(len(records))+" records"
        
        number = 0
        for record in records:
            if record.find('object_number') != None:
                object_number = record.find('object_number').text
                if object_number.lower() in art_list:
                    number += 1
                    currentObject = ObjectItem()

                    if record.find('title') != None:
                        title = record.find('title').text
                    else:
                        title = ""

                    if record.find('creator') != None:
                        name_of_artist = record.find('creator').text
                    else:
                        name_of_artist = ""

                    if record.find('production.date.end') != None:
                        date_of_production = record.find('production.date.end').text
                    else:
                        date_of_production = ""

                    priref = record.find('priref').text

                    if title != None:
                        currentObject.title = title
                    else:
                        currentObject.title = ""

                    if name_of_artist != None: 
                        currentObject.name_of_artist = name_of_artist
                    else:
                        currentObject.name_of_artist = ""
                    
                    if date_of_production != None:
                        currentObject.date_of_production = date_of_production
                    else:
                        currentObject.date_of_production = ""

                    if object_number != None:
                        currentObject.object_number = object_number
                    else:
                        currentObject.object_number = priref

                    self.createWorkObject(currentObject)
                    if number >= limit:
                        return
                else:
                    print "Skip art-work for now. No image available."
                    self.skipped += 1

            else:
                object_number = "Unknown"
        return

    def migrateXMLTest(self):
        root = self.xmlDoc.getroot()
        recordList = root.find("recordList")
        print "Found recordList"
        records = recordList.getchildren()
        print "Found "+str(len(records))+" records"
        for record in records:
            title = record.find('title').text
            name_of_artist = record.find('creator').text
            date_of_production = record.find('production.date.end').text
            self.fields.append(title + ", "+name_of_artist+", "+date_of_production)
            break

        return

    def startMigration(self):
        if self.portal is not None:
            if self.typeToCreate == "Test":
                self.migrateXMLTest()
                for f in self.fields:
                    print f
            elif self.typeToCreate == "Object":
                self.migrateToObject()
            elif self.typeToCreate == "Limit":
                self.migrateLimit(10)
            elif self.typeToCreate == "Images":
                self.migrateImages()
            elif self.typeToCreate == "Publish":
                self.migratePublish()
            elif self.typeToCreate == "Translation":
                self.migrateTranslation('en')
            elif self.typeToCreate == "All":
                self.migrateLimit(300)
                self.migratePublish()
                self.migrateTranslation(300, 'en')
            else:
                print("TYPE NOT RECOGNIZED!! ==>> " + self.typeToCreate)
            
            #self.cleanUp()
        else:
            print ("Portal is NONE!!!")
            #self.cleanUp()
        return