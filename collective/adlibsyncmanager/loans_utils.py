#!/usr/bin/env python
# -*- coding: utf-8 -*-

loans_subfields_types = {
	"loan_status":"choice",
	"loan_status-text":"choice",
	"object-in-object-in.authoriser_lender":"relation",
	"object-in-object-in.insurance.value.curren":"gridlist",
	"object-in-object-in.object_number":"relation",
	
	'Entry-entry.number':'relation',
	'Relatedloan-related_loan':'relation',

	'object-in-object-in.status': "choice",
	'object-in-object-in.status-text': "choice",

	'object-out-object-out.object_number': 'relation',
	'object-out-object-out.authoriser':'relation',
	'object-out-object-out.insurance.value.curr':"gridlist",
	'object-out-object-out.review_request.templa-text':"choice",
	'object-out-object-out.perm_owner.req.templa-text':'choice',
	
	"object-out.perm_owner.result-text":"choice",
	'object-out-object-out.status-text':"choice",
	'object-out-object-out.perm_owner.result-text':"choice",
	
	'extension.contract.template-text':"choice",
	'extension.request.template':'choice',
	'extension.request.template-text':'choice',
	'extension.review.status':'choice',
	'extension.review.status-text':'choice',
	'extension.review.authoriser':'relation',
	'object-out-object-out.insurance_value.curr':"gridlist"
}

loans_relation_types = {
	"object-in-object-in.object_number":"Object",
	"object-in-object-in.authoriser_lender": "PersonOrInstitution",
	"Entry-entry.number":"ObjectEntry",
	"Relatedloan-related_loan":"OutgoingLoan",
	"object-out-object-out.object_number": "Object",
	"object-out-object-out.authoriser": "PersonOrInstitution",
	'extension.review.authoriser': "PersonOrInstitution"
}

