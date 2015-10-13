#!/usr/bin/env python
# -*- coding: utf-8 -*-

article_subfields_types = {
	"author.name":"relation",
	"Illustrator-illustrator.name": "relation",
	"Illustrator-illustrator.role-term": "gridlist",
	"corporate_author":"relation",
	"serial.continued.from.recordno":"relation",
	"serial.continued.as.recordno":"relation",
	"author.role-term":"gridlist",
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
	"source.title":"relation"
}

article_relation_types = {
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
	"Illustrator-illustrator.name":"PersonOrInstitution"
}

