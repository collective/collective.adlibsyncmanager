#!/usr/bin/env python
# -*- coding: utf-8 -*-

persons_subfields_types = {
	"name.type-text":"choice",
	"equivalent_name": "relation",
	"address.place-term": "gridlist",
	"address.country-term": "gridlist",
	"contact.name": "relation",
	"place_activity-term":"gridlist"
}

persons_relation_types = {
	"equivalent_name": "PersonOrInstitution",
	"contact.name": "PersonOrInstitution"
}

