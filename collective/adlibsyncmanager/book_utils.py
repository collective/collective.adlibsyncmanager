
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

book_subfields_types = {
	"author.name":"relation",
	"Illustrator-illustrator.name": "relation",
	"Illustrator-illustrator.role-term": "gridlist",
	"author.role-term":"gridlist",
	"publisher": "relation",
	"keyword.type-text":"choice",
	"keyword.contents-term": "gridlist",
	"keyword.proper_name-term":"gridlist",
	"person.keyword.type-text": "choice",
	"person.keyword.name-name": "gridlist",
	"person.keyword.role-term":"gridlist",
	"exhibition-exhibition": "relation",
	"object.object_number":"relation",
	"free_field.confidential":"bool",
	"copy.number": "relation",
	"copy.number-loan_category":"gridlist",
	"site":"gridlist",
	"print.name": "relation",
	"loan_category-term":"gridlist",
	"site-term": "gridlist",
	"corporate_author":"relation",
	"person.keyword.name":"relation",
	"accompanying_material": "gridlist"
}

book_relation_types = {
	"author.name": "PersonOrInstitution",
	"Illustrator-illustrator.name": "PersonOrInstitution",
	"publisher": "PersonOrInstitution",
	"exhibition-exhibition": "Exhibition",
	"object.object_number":"Object",
	"copy.number": "Bibliotheek",
	"print.name": "PersonOrInstitution",
	"corporate_author": "PersonOrInstitution",
	"person.keyword.name": "PersonOrInstitution"
}