#!/usr/bin/env python
# -*- coding: utf-8 -*-

resource_subfields_types = {
	"publisher":"relation",
	"author.name":"relation",
	"contributor":"relation",
	"exhibition-exhibition":"relation",
	"object.object_number":"relation",
	"site-term":"gridlist",
	"loan_category-term":"gridlist"
}

resource_relation_types = {
	"publisher":"PersonOrInstitution",
	"author.name": "PersonOrInstitution",
	"contributor": "PersonOrInstitution",
	"exhibition-exhibition":"Exhibition",
	"object.object_number":"Object"
}

