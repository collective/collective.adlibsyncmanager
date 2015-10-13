
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

serial_subfields_types = {
	"author.name":"relation",
	"corporate_author":"relation",
	"publisher":"relation",
	"print.name":"relation",
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
}

serial_relation_types = {
	"author.name":"PersonOrInstitution",
	"corporate_author":"PersonOrInstitution",
	"publisher":"PersonOrInstitution",
	"print.name":"PersonOrInstitution",
	"serial.continued.from.recordno":"Serial",
	"serial.continued.as.recordno":"Serial",
	"person.keyword.name": "PersonOrInstitution",
	"object.object_number":"Object",
	"exhibition-exhibition": "Exhibition",
}