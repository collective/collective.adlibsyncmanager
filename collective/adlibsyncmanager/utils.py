
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

subfields_types = {
	"Taxonomy-taxonomy.scientific_name": "relation",
	"Determination-determination.name": "relation",
	"object_name-term": "gridlist",
	"Taxonomy-taxonomy.rank-text": "choice",
	"dimension.type-term": "choice",
	"creator": "relation",
	"creator.role-term": "gridlist",
	"production.place-term": "gridlist",
	"documentation-documentation.title":"relation",

	"technique-term": "gridlist",
	"material-term": "gridlist",
	"dimension.type-term": "gridlist",
	"association.person.type-text": "choice",
	"phys_characteristic.keyword-term":"gridlist",
	"phys_characteristic.aspect-term": "gridlist",
	"content.motif.general-term":"gridlist",
	'content.motif.specific-term':"gridlist",
	"association.subject.name-term": "gridlist",
	"content.person.name":"relation",
	"content.person.name.type-text":"choice",

	"content.subject.type-text":"choice",
	"content.subject.type": "choice",
	
	"content.subject.tax.rank-text": "choice",
	"content.subject.name-term": "gridlist",
	"content.subject-term": "gridlist",
	"object_name.type-term":"gridlist",

	"inscription.type-term": "gridlist",
	"inscription.maker": "relation",
	"inscription.maker.role-term": "gridlist",
	"inscription.script-term":"gridlist",
	"parts_reference": "relation",
	"related_object.reference": "relation",
	"related_object.association-term": "gridlist",

	"condition-term":"gridlist",
	"preservation_form-term":"gridlist",
	"conservation-conservation.number-treatment_number":"relation",
	"valuation.value.currency": "gridlist",
	"owner_hist.owner":"relation",
	"owner_hist.acquisition.method-term":"gridlist",
	"owner_hist.acquired_from":"relation",
	"location-term":"gridlist",
	"Collector-field_coll.name":"relation",
	"Collector-field_coll.name.role-term":"gridlist",
	"Stratigraphy-stratigraphy.unit-term":"gridlist",
	"exhibition-exhibition":"relation",
	"association.person.type-text":"choice",
	"association.person": "relation",
	"association.subject.tax.rank-text":"choice",
	"association.subject-term":"gridlist",
	"association.subject.association-term":"gridlist",
	"association.subject.type-text":"choice",
	"association.period.assoc-term":"gridlist",
	"association.period-term":"gridlist",
	"acquisition.funding.currency":"gridlist",
	"entry.number":"relation",
	"Loan_out-loan.out.number":"relation",
	"Loan-in-loan.in.number":"relation",
	"archive.number":"relation",
	"association.person.association-term":"gridlist",
	"content.date.period-term":"gridlist",
	"acquisition.source": "relation",
	"owner_hist.place-term":"gridlist",
	"owner_hist.acquisition.method-term":"gridlist",
	"owner_hist.acquired_from":"relation",
	"owner_hist.owner":"relation",
	"free_field.confidential":"bool",
	"dimension.unit-term":"choice"
	#"owner_hist.auction": "relation"
}

relation_types = {
	"Taxonomy-taxonomy.scientific_name":"Taxonomie",
	"creator": "PersonOrInstitution",
	"inscription.maker": "PersonOrInstitution",
	"content.person.name": "PersonOrInstitution",
	"Determination-determination.name": "PersonOrInstitution",
	"parts_reference": "Object",
	"related_object.reference": "Object",
	"conservation-conservation.number-treatment_number":"treatment",
	"owner_hist.owner":"PersonOrInstitution",
	"owner_hist.acquired_from":"PersonOrInstitution",
	"Collector-field_coll.name":"PersonOrInstitution",
	"exhibition-exhibition": "Exhibition",
	"association.person":"PersonOrInstitution",
	"documentation-documentation.title": "Bibliotheek",
	"entry.number": "ObjectEntry",
	"Loan_out-loan.out.number":"OutgoingLoan",
	"Loan-in-loan.in.number": "IncomingLoan",
	"archive.number": "Archive",
	"acquisition.source": "PersonOrInstitution",
	"owner_hist.acquired_from":"PersonOrInstitution",
	"owner_hist.owner":"PersonOrInstitution"
	#"owner_hist.auction": "Auction"
}