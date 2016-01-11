#!/usr/bin/env python
# -*- coding: utf-8 -*-

objectentry_subfields_types = {
	"Shipper-shipper": "relation",
	"Template_production-template.creator":"relation",
	"Template_production-template.production_place":"gridlist",
	"Object-in-object-in.object_number":"relation",
	"Object-in-object-in.condition_check":"bool",
	"Object-in-object-in.insurance.currency":"gridlist"
}

objectentry_relation_types = {
	"Shipper-shipper":"PersonOrInstitution",
	"Template_production-template.creator": "PersonOrInstitution",
	"Object-in-object-in.object_number":"Object"
}

