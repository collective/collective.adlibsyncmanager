#!/usr/bin/env python
# -*- coding: utf-8 -*-

audiovisual_subfields_types = {
	"author.name":"relation",
	"Illustrator-illustrator.name": "relation",
	"Illustrator-illustrator.role-term": "gridlist",
	"author.role-term":"gridlist",
	"publisher": "relation",
	"corporate_author":"relation",
	"keyword.type-text":"choice",
	"keyword.contents-term": "gridlist",
	"keyword.proper_name-term":"gridlist",
	"person.keyword.type-text": "choice",
	"person.keyword.name": "relation",
	"person.keyword.role-term":"gridlist",
	"free_field.confidential":"bool",
	"exhibition-exhibition": "relation",
	"object.object_number":"relation",
	"free_field.confidential":"bool",
	"copy.number-loan_category":"gridlist",
	"site":"gridlist",
	"loan_category-term":"gridlist",
	"site-term": "gridlist",
	"used_for":"relation",
	"use":"relation",
	"source.title":"relation",
	"print.name":"relation",
	"broadcasting_company":"relation",
	"production_company":"relation"
}

audiovisual_relation_types = {
	"serial.continued.from.recordno":"Serial",
	"serial.continued.as.recordno":"Serial",
	"person.keyword.name": "PersonOrInstitution",
	"object.object_number":"Object",
	"exhibition-exhibition": "Exhibition",
	"used_for":"Bibliotheek",
	"use":"Bibliotheek",
	"Illustrator-illustrator.name":"PersonOrInstitution",
	"source.title":"Bibliotheek",
	"corporate_author":"PersonOrInstitution",
	"author.name":"PersonOrInstitution",
	"Illustrator-illustrator.name":"PersonOrInstitution",
	"publisher":"PersonOrInstitution",
	"print.name":"PersonOrInstitution",
	"broadcasting_company":"PersonOrInstitution",
	"production_company":"PersonOrInstitution"
}

