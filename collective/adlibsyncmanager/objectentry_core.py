#!/usr/bin/env python
# -*- coding: utf-8 -*-

OBJECTENTRY_CORE = {

	# General
	'priref':'priref',
	'record':'',
	'transport_number':'general_entry_transportNumber',
    'entry_date.expected':'general_entry_dateExpected', 
    'entry_date':'general_entry_entryDate',
    'return_date':'general_entry_returnDate',
    #'':'general_entry_transportMethod',  NEEDS FIX

    'entry_reason':'',
    'entry_reason-text':'general_entry_reason',
    'owner-name':'',
    'owner':'general_entry_currentOwner', 
    'depositor':'general_entry_depositor',
    'depositor-name':'',
    'depositor.contact':'general_entry_depositorContact',
    'depositor.contact-name':'',
    'destination':'general_entry_destination', 
    'destination-name':'',
    'destination.contact':'general_entry_destinationContact',
    'destination.contact-name':'',
    
    'Shipper-shipper':'general_transport_shipper-shipper',#relation
    'Shipper-shipper.contact':'general_transport_shipper-contact',
    
    'courier':'general_transport_courier', 
    'number_of_objects.stated':'general_numberOfObjects_numberInFreightLetter',
    'number_of_objects.sent':'general_numberOfObjects_numberDelivered', 
    'general_freightLetter_template':'',
    'freight_letter_in.template-text':'general_freightLetter_template',
    'freight_letter_in.reference':'general_freightLetter_digRef', 
    'insurance.value':'general_totalInsuranceValue_insuranceValue',
    'insurance.currency':'general_totalInsuranceValue_currency', 
    
    'requirements':'general_requirements_requirements-term',
    
    'packing_notes':'general_requirements_packingNotes-term', 
    
    'Digitalreference':'',
    'Digitalreference-digital_reference.type':'general_requirements_digitalReferences-type',
    'Digitalreference-digital_reference':'general_requirements_digitalReferences-reference',
    
    'notes':'general_notes_notes-notes',

    # Template for object data
    'template.object_name':'templateForObjectData_objectName', 

    'template.title':'templateForObjectData_title-title',

    'template.description':'templateForObjectData_description', 
    	
    'Template_date':'',
    'Template_date-template.date.start':'templateForObjectData_date-dateEarly',
    'Template_date-template.date.end':'templateForObjectData_date-dateLate',
    
    'Template_production':'',
    'Template_production-template.creator':'templateForObjectData_creator-creator', #relation
    'Template_production-template.production_place':'templateForObjectData_creator-productionPlace', 
    
    'template.material':'templateForObjectData_material',
    'template.technique':'templateForObjectData_technique', 
    'template.current_location':'templateForObjectData_location',
    'template.current_owner':'templateForObjectData_currentOwner', 
    
    'template.notes':'templateForObjectData_notes-notes',
    
    #'':'templateForObjectData_createLinkedObjectRecords' needs fix

    # List with linked objects
    'miscellaneous_transport_content':'listWithLinkedObjects_transportContentNote', 

    'Object-in':'',
    'Object-in-object-in.object_number':'listWithLinkedObjects_linkedObjects-objectNumber',#relation
    'Object-in-object-in.status':'listWithLinkedObjects_linkedObjects-status',
    'Object-in-object-in.condition_check':'listWithLinkedObjects_linkedObjects-conditionChecked',#bool
    'Object-in-object-in.reason':'listWithLinkedObjects_linkedObjects-transportReason',
    'Object-in-object-in.packing':'listWithLinkedObjects_linkedObjects-packing',
    'Object-in-object-in.insurance.value':'listWithLinkedObjects_linkedObjects-insuranceValue',
    'Object-in-object-in.insurance.currency':'listWithLinkedObjects_linkedObjects-curr',#gridlist
    'Object-in-object-in.insurance.date':'listWithLinkedObjects_linkedObjects-date',
    'Object-in-object-in.notes':'listWithLinkedObjects_linkedObjects-notes',

    'Edit':'',
    'Edit-edit.name':'',
    'Edit-edit.time':'',
    'Edit-edit.date':'',
    'Edit-edit.source':'',
    'Edit-edit.notes':'',
    'input.source':'',
    'input.date':'',
    'input.name':'',
    'input.time': '',
}



