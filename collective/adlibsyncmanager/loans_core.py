#!/usr/bin/env python
# -*- coding: utf-8 -*-

INCOMMING_CORE = {
	# Loan request
	'priref':'priref',
	'record':'',
	'loan_number':'loanRequest_general_loanNumber',
	'lender':'loanRequest_general_lender',
    'lender.contact':'loanRequest_general_contact',
    'co-ordinator':'loanRequest_internalCoordination_coordinator',

    'administration_concerned':'loanRequest_internalCoordination_administrConcerned-name', # grid

    'request.period.start':'loanRequest_requestDetails_periodFrom',
    'request.period.end':'loanRequest_requestDetails_to',

    'request.reason':'',
    'request.reason-text':'loanRequest_requestDetails_reason',

    'exhibition':'loanRequest_requestDetails_exhibition',
    'request.date':'loanRequest_requestLetter_date',
    'request-out.reference':'loanRequest_requestLetter_digRef',
    'request-out.template':'loanRequest_requestLetter_template',
    'request-out.confirm.date':'loanRequest_requestConfirmation_date',
    'request-out.confirm.reference':'loanRequest_requestConfirmation_digRef',

    # Objects

    'object-in-object-in.object_number':'objects_object-objectNumber', # relation
    'object-in-object-in.status':'objects_object-status',
    'object-in-object-in.status-text':'objects_object-status', # choice
    'object-in-object-in.status.date':'objects_object-date',
    'object-in-object-in.authoriser_lender':'objects_object-authoriserInternal', # relation
    'object-in-object-in.authorisation_date':'objects_object-authorisationDate',
    'object-in-object-in.loan_conditions':'objects_object-miscellaneous_conditions',
    'object-in-object-in.insurance_value':'objects_object-miscellaneous_insurancevalue',
    'object-in-object-in.insurance.value.curren':'objects_object-miscellaneous_currency', #gridfield
    'object-in-object-in.notes':'objects_object-miscellaneous_notes',

    # Contract
    'contract.period.start':'contract_contractDetails_requestPeriodFrom',
    'contract.period.end':'contract_contractDetails_to',
    'conditions':'contract_contractDetails_conditions',
    'notes':'contract_contractDetails_notes-note', # grid
    'contract.date':'contract_contractLetter_date',
    'contract.reference':'contract_contractLetter_digRef',
    'contract.returned.date':'contract_contractLetter_signedReturned',
    'contract.returned.reference':'contract_contractLetter_signedReturnedDigRef',
    
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
    'Correspondence-correspondence.reference':'correspondence_otherCorrespondence-digitalReference',
    'Correspondence-correspondence.date':'correspondence_otherCorrespondence-date',
    'Correspondence-correspondence.sender':'correspondence_otherCorrespondence-sender',
    'Correspondence-correspondence.destination':'correspondence_otherCorrespondence-destination',
    'Correspondence-correspondence.subject':'correspondence_otherCorrespondence-subject',

    # Related loans
	'Relatedloan-related_loan':'relatedLoans_relatedLoans-loanNumber',
	'Relatedloan-related_loan.relation_type':'relatedLoans_relatedLoans-relationType'

}


