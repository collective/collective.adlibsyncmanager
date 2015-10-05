#!/usr/bin/env python
# -*- coding: utf-8 -*-

incomming_subfields_types = {
	"loan_status":"choice",
	"loan_status-text":"choice",
	"object-in-object-in.authoriser_lender":"relation",
	"object-in-object-in.insurance.value.curren":"gridlist",
	"object-in-object-in.object_number":"relation",
	'object-in-object-in.status': "choice",
	'object-in-object-in.status-text': "choice",
	'extension.request.template':'choice',
	'extension.request.template-text':'choice',
	'extension.review.status':'choice',
	'extension.review.status-text':'choice',
	'Entry-entry.number':'relation',
	'Relatedloan-related_loan':'relation'
}

incomming_relation_types = {
	"object-in-object-in.object_number":"Object",
	"object-in-object-in.authoriser_lender": "PersonOrInstitution",
	"Entry-entry.number":"ObjectEntry",
	"Relatedloan-related_loan":"OutgoingLoan"
}

