#!/usr/bin/env python
# -*- coding: utf-8 -*-


exhibition_subfields_types = {
	"venue-venue": "relation",
	"venue-venue.place-term": "gridlist",
	"organiser-organiser": "relation",
	"documentation-documentation.title": "relation",
	"object.object_number": "relation"
}

exhibition_relation_types = {
	"venue-venue": "PersonOrInstitution",
	"organiser-organiser": "PersonOrInstitution",
	"documentation-documentation.title": "Bibliotheek",
	"object.object_number": "Object"
}
