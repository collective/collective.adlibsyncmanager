#!/usr/bin/env python
# -*- coding: utf-8 -*-

INCOMMING_CORE = {
	# Loan request
	'priref':'priref',
	'record':'',
	'loan_number':'loanRequest_general_loanNumber',
	'lender':'loanRequest_general_lender',
	'lender-name':'',
    'lender.contact':'loanRequest_general_contact',
    'lender.contact-name':'',
    'co-ordinator':'loanRequest_internalCoordination_coordinator',
    'co-ordinator-name':'',

    'administration_concerned':'loanRequest_internalCoordination_administrConcerned-name', # grid

    'request.period.start':'loanRequest_requestDetails_periodFrom',
    'request.period.end':'loanRequest_requestDetails_to',

    'request.reason':'',
    'request.reason-text':'loanRequest_requestDetails_reason',

    'exhibition':'loanRequest_requestDetails_exhibition',
    'request.date':'loanRequest_requestLetter_date',
    'request-out.reference':'loanRequest_requestLetter_digRef',
    'request-out.template':'',
    'request-out.template-text':'loanRequest_requestLetter_template',
    'request-out.confirm.date':'loanRequest_requestConfirmation_date',
    'request-out.confirm.reference':'loanRequest_requestConfirmation_digRef',
    'request-out.confirm.confirmed': 'loanRequest_requestConfirmation_dateCheck'

    # Objects
    'object-in':'',
    'object-in-object-in.object_number':'objects_object-objectNumber', # relation
    'object-in-object-in.status':'',
    'object-in-object-in.status-text':'objects_object-status', # choice
    'object-in-object-in.status.date':'objects_object-date',
    'object-in-object-in.authoriser_lender':'objects_object-authoriserInternal', # relation
    'object-in-object-in.authorisation_date':'objects_object-authorisationDate',
    'object-in-object-in.loan_conditions':'objects_object-miscellaneous_conditions',
    'object-in-object-in.insurance_value':'objects_object-miscellaneous_insurancevalue',
    'object-in-object-in.insurance.value.curren':'objects_object-miscellaneous_currency', #gridfield
    'object-in-object-in.notes':'objects_object-miscellaneous_notes',
    'loan_status':'',
    'loan_status-text':'',

    # Contract
    'contract.period.start':'contract_contractDetails_requestPeriodFrom',
    'contract.period.end':'contract_contractDetails_to',
    'conditions':'contract_contractDetails_conditions',
    'notes':'contract_contractDetails_notes-note', # grid
    'contract.date':'contract_contractLetter_date',
    'contract.reference':'contract_contractLetter_digRef',
    'contract.returned.date':'contract_contractLetter_signedReturned',
    'contract.returned.reference':'contract_contractLetter_signedReturnedDigRef',
    'contract.returned': 'contract_contractLetter_returned'
    
    'extension.request.end_date':'contract_extension-request_newEndDate', 
    'extension.request.template': 'contract_extension-request_template',
    'extension.request.template-text':'contract_extension-request_template', # choice
    'extension.request.date':'contract_extension-request_date', 
    'extension.request.reference':'contract_extension-request_digRef', 
    'extension.review.status':'contract_extension-review_status',
    'extension.review.status-text':'contract_extension-review_status', # choice
    'extension.review.end_date':'contract_extension-review_newEndDate', 
    'extension.contract.date':'contract_extension-review_date', 
    'extension.contract.reference':'contract_extension-review_digRef', 
    'extension.review.notes':'contract_extension-review_notes', 

    # Transport
    'Despatch-despatch.number-transport_number':'transport_despatchDetails-despatchNumber', # grid
    'Entry-entry.number':'transport_entryDetails-entryNumber', # grid

    # Correspondence
    'Correspondence':'',
    'Correspondence-correspondence.reference':'correspondence_otherCorrespondence-digitalReference',
    'Correspondence-correspondence.date':'correspondence_otherCorrespondence-date',
    'Correspondence-correspondence.sender':'correspondence_otherCorrespondence-sender',
    'Correspondence-correspondence.destination':'correspondence_otherCorrespondence-destination',
    'Correspondence-correspondence.subject':'correspondence_otherCorrespondence-subject',

    # Related loans
	'Relatedloan-related_loan':'relatedLoans_relatedLoans-loanNumber',
	'Relatedloan-related_loan.relation_type':'relatedLoans_relatedLoans-relationType',

	# Ignored fields
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

    'datasets.collect':'',
    'datasets.collect-text':'',

    'object-in-object-in.authoriser_lender-name':'',
    'object-in-object-in.object_number-object_number':'',
    'object-in-object-in.object_number-object_name':'',
    'object-in-object-in.object_number-title':'',
    'object-in-object-in.object_number-creator':'',
    'object-in-object-in.object_name':'',
    'object-in-object-in.title':'',
    'object-in-object-in.creator':'',

    'exhibition':'',
    'exhibition-title':'',
    'exhibition-date.start':'',
    'exhibition-date.end':'',
    'exhibition.date.start':'',
	'exhibition.date.end':'',
	'exhibition.duration':'',


    'Relatedloan':'',

    'Entry':'',
    'Entry-entry.number':'',
    'Entry-entry.number-transport_number':'',
    'Entry-entry.number-transport_method':'',
    'Entry-entry.number-number_of_objects.stated':'',
    'Entry-entry.number-number_of_objects.sent':'',
    'Entry-entry.number-entry_date.expected':'',
    'Entry-entry.number-entry_date':'',
    'Entry-entry.number-shipper':'',
    'Entry-entry.number-courier':'',
    'Entry-entry.number_stated':'',
    'Entry-entry.number_sent':'',
    'Entry-entry.date_expected':'',
    'Entry-entry.date':'',
    'Entry-entry.method':'',
    'Entry-entry.shipper':'',
    'Entry-entry.courier':'',

    'Despatch':'',
    'Despatch-despatch.number':'',
    'Despatch-despatch.number-number_of_objects.sent':'',
    'Despatch-despatch.number-despatch_date':'',
    'Despatch-despatch.number-delivery_date':'',
    'Despatch-despatch.number-delivered':'',
    'Despatch-despatch.number-delivered.date':'',
    'Despatch-despatch.number-transport_method':'',
    'Despatch-despatch.number-shipper':'',
    'Despatch-despatch.number-courier':'',
    'Despatch-despatch.number-despatch_date.expected':'',
    'Despatch-despatch.number_of_objects':'',
    'Despatch-despatch.date':'',
    'Despatch-despatch.delivered':'',
    'Despatch-despatch.delivered.date':'',
    'Despatch-despatch.delivery_date':'',
    'Despatch-despatch.method':'',
    'Despatch-despatch.shipper':'',
    'Despatch-despatch.courier':'',
    'Despatch-despatch.date_expected':'',
}


