#!/usr/bin/env python
# -*- coding: utf-8 -*-

PERSON_CORE = {
	# Name information tab
    'priref':'priref',
	'name':'nameInformation_name_name', 
	'institution_code':'nameInformation_name_institutionNumber',
    'name.type':'',
    'name.type-text':'nameInformation_name_nameType-type', 
    'name.note':'nameInformation_name_nameNotes',

    'use':'nameInformation_relationWithOtherNames_use-use', 
    'used_for':'nameInformation_relationWithOtherNames_usedFor-usedFor',
    'equivalent_name':'nameInformation_relationWithOtherNames_equivalent-name', 

    'address.place':'',
    'address.place-term':'nameInformation_addressDetails-place',
    'address.country':'',
    'address.country-term':'nameInformation_addressDetails-country',
    'address.type':'nameInformation_addressDetails-addressType',
    'address':'nameInformation_addressDetails-address',
    'address.postal_code':'nameInformation_addressDetails-postalCode',

    'phone':'nameInformation_telephoneFaxEmail_telephone-phone', 
    'fax':'nameInformation_telephoneFaxEmail_fax-fax',
    'email':'nameInformation_telephoneFaxEmail_email-email', 
    'url':'nameInformation_telephoneFaxEmail_website-url',

    'contact.name':'nameInformation_contacts-name', 
    'contact.name-name':'',
    'contact.job_title':'nameInformation_contacts-jobTitle',
    'contact.phone':'nameInformation_contacts-phone',

    'group': '',
    'group-term':'nameInformation_miscellaneous_group', 
    'notes':'nameInformation_miscellaneous_notes-note',

    # Biography tab
    'birth.date.start':'personDetails_birthDetails_dateStart',
    'birth.date.end':'personDetails_birthDetails_dateEnd',
    'birth.date.precision':'personDetails_birthDetails_precision',
    'birth.place':'',
    'birth.place-term':'personDetails_birthDetails_place', 
    'birth.notes':'personDetails_birthDetails_notes-note', 

    'death.date.start':'personDetails_deathDetails_dateStart',
    'death.date.end':'personDetails_deathDetails_dateEnd', 
    'death.date.precision':'personDetails_deathDetails_precision',
    'death.place':'',
    'death.place-term':'personDetails_deathDetails_place', 
    'death.notes':'personDetails_deathDetails_notes-note',
    
    'nationality':'personDetails_nationality_nationality-nationality', 
    'language':'',
    'language-term':'personDetails_nationality_language',
    
    'occupation':'',
    'occupation-term':'personDetails_ocupation_ocupation', 
    'school_style':'',
    'school_style-term':'personDetails_ocupation_schoolStyle',


    'place_activity-term':'personDetails_placeOfActivity-place', 
    'place_activity.date.start':'personDetails_placeOfActivity-dateStart',
    'place_activity.date.end':'personDetails_placeOfActivity-dateEnd',
    'place_activity.notes':'personDetails_placeOfActivity-notes',

    'biography':'personDetails_biographies-biography',

    # Suplier - ignore this field
    'supplier.language':'',
    'supplier.currency':'',
    'supplier.letter.ser.order':'',
    'supplier.letter.ser.cancel':'',
    'supplier.letter.ser.claim':'',
    'supplier.letter.ser.order':'',
    'supplier.letter.ser.cancel':'',
    'supplier.letter.ser.renew':'',
    'supplier.letter.ser.order.claim':'',

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