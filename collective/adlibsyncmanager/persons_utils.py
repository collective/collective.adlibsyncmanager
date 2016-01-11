#!/usr/bin/env python
# -*- coding: utf-8 -*-

persons_subfields_types = {
	"name.type-text":"choice",
	"equivalent_name": "relation",
	"address.place-term": "gridlist",
	"address.country-term": "gridlist",
	"contact.name": "relation",
	"place_activity-term":"gridlist",
	"use": "relation",
	"used_for": "relation"
}

persons_relation_types = {
	"equivalent_name": "PersonOrInstitution",
	"contact.name": "PersonOrInstitution",
	"use": "PersonOrInstitution",
	"used_for": "PersonOrInstitution"
}

