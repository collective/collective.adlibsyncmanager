#!/usr/bin/env python
# -*- coding: utf-8 -*-

PERSON_CORE = {
	# Name information tab

	'':'nameInformation_name_name', 
	'':'nameInformation_name_institutionNumber',
    'name.type-text':'nameInformation_name_nameType-type', 
    '':'nameInformation_name_nameNotes',
    '':'nameInformation_relationWithOtherNames_use', 
    '':'nameInformation_relationWithOtherNames_usedFor',
    'equivalent_name':'nameInformation_relationWithOtherNames_equivalent-name', 

    'address.place':'',
    'address.place-term':'nameInformation_addressDetails-place',
    'address.country':'',
    'address.country-term':'nameInformation_addressDetails-country',
    'address.place':'nameInformation_addressDetails',
    'address.place':'nameInformation_addressDetails',
    'address.place':'nameInformation_addressDetails',

    '':'nameInformation_telephoneFaxEmail_telephone', 
    '':'nameInformation_telephoneFaxEmail_fax',
    '':'nameInformation_telephoneFaxEmail_email', 
    '':'nameInformation_telephoneFaxEmail_website',

    'contact.name':'nameInformation_contacts-name', 
    'contact.name-name':'',
    'contact.name':'nameInformation_contacts',
    'contact.name':'nameInformation_contacts',

    'group': '',
    'group-term':'nameInformation_miscellaneous_group', 
    '':'nameInformation_miscellaneous_notes',

    # Biography tab
    '':'personDetails_birthDetails_dateStart' ,
    '':'personDetails_birthDetails_dateEnd',
    '':'personDetails_birthDetails_precision',
    'birth.place':'',
    'birth.place-term':'personDetails_birthDetails_place', 
    '':'personDetails_birthDetails_notes', 
    '':'personDetails_deathDetails_dateStart',
    '':'personDetails_deathDetails_dateEnd', 
    '':'personDetails_deathDetails_precision',
    'death.place':'',
    'death.place-term':'personDetails_deathDetails_place', 
    '':'personDetails_deathDetails_notes',
    '':'personDetails_nationality_nationality', 
    '':'personDetails_nationality_language',
    '':'personDetails_ocupation_ocupation', 
    '':'personDetails_ocupation_schoolStyle',
    'place_activity-term':'personDetails_placeOfActivity-place', 
    '':'personDetails_biography'

}