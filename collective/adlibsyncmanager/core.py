#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Adlib - Plone object

CORE = {
    #
    # Identification tab
    #
    "priref": "priref",
    "title": "identification_titleDescription_title-title",
    "description": "identification_titleDescription_description",

    "institution.name":"identification_identification_institutionNames",
    "institution.name-name":"",# value is in the relation - parent
    "institution.place":"",#repeated
    "institution.name-address.place":"identification_identification_institutionPlace",
    "institution.code":"",#repeated
    "institution.name-institution_code":"",
    "object_number":"identification_identification_objectNumber",
    "administration_name": "identification_identification_administrativeName",
    "collection": "",#parent
    "collection-term": "identification_identification_collections",
    
    "part":"identification_identification_part",
    "number_of_parts": "identification_identification_totNumber",
    "copy_number": "identification_identification_copyNumber",
    "edition": "identification_identification_edition",
    "distinguishing_features": "identification_identification_distinguishFeatures",
    
    "object_category": "",#parent
    "object_category-term": "identification_objectName_category",
    
    "object_name":"",#parent
    "object_name-term": "identification_objectName_objectname-name",
    "object_name.notes": "identification_objectName_objectname-notes",
    'object_name.type':'',
    "object_name.type-term":"identification_objectName_objectname-types",

    "title.type":"identification_titleDescription_title-type",
    "description.date": "identification_titleDescription_titleDate",
    "title.notes": "identification_titleDescription_title-notes",
    "title.language": "identification_titleDescription_language",
    "title.translation": "identification_titleDescription_translatedTitle-title",
    "description.name": "identification_titleDescription_describer",

    "other_name":"identification_objectName_otherName-name",
    "other_name.type":"identification_objectName_otherName-type",
    
    "Taxonomy": "",#parent
    "Taxonomy-taxonomy.scientific_name": "identification_taxonomy-scientific_name",#parent
    "Taxonomy-taxonomy.scientific_name-scientific_name": "",
    "Taxonomy-taxonomy.scientific_name-common_name": "identification_taxonomy-common_name",
    "Taxonomy-taxonomy.rank": "identification_taxonomy-rank",#parent
    "Taxonomy-taxonomy.rank-text": "",

    #"Taxonomy-taxonomy.scientific_name.lref":"",
    #"Taxonomy-taxonomy.scientific_name.lref":"",

    "Determination": "",#parent
    "Determination-determination.name": "identification_taxonomy_determiners-name",
    "Determination-determination.name-name": "",#value is in the relation - parent
    "Determination-determination.date": "identification_taxonomy_determiners-date",
    "object_status":"",
    "object_status-text": "identification_taxonomy_objectstatus",
    "determination.notes": "identification_taxonomy_notes-notes",

    #"Determination-determination.name-name":"",
    #"Determination-determination.name.lref":"",
    #"Determination-determination.name-name":"",
    #"Determination-determination.name.lref":"",
        
    #
    # Production tab
    #
    "creator": "productionDating_productionDating-makers",
    "creator-name": "",# value is in the relation - parenet
    "creator.role": "",#parent
    "creator.role-term": "productionDating_productionDating-role",
    "creator.qualifier": "productionDating_productionDating-qualifier",
    "creator.date_of_birth":"", #repeated
    "creator-birth.date.start":"productionDating_productionDating-dateBirth",
    "creator.date_of_death":"", #repeated
    "creator-death.date.start":"productionDating_productionDating-dateDeath",

    "production": "",#parent
    "production.place":"",
    "production.place-term": "productionDating_productionDating-place",
    "production.notes": "productionDating_productionDating-production_notes",
 
    "production.reason": "productionDating_production_productionReason",
    "school_style": "",#parent
    "school_style-term": "productionDating_production_schoolStyles",
    
    "production.date.start":"productionDating_dating_period-date_early",
    "production_date.start.prec":"productionDating_dating_period-date_early_precision",
    "production.date.end":"productionDating_dating_period-date_late",
    "production.date.end.prec":"productionDating_dating_period-date_late_precision",

    "production.period": "",#parent
    "production.period-term": "productionDating_production_periods",
    "production.date.notes": "productionDating_dating_notes-notes",

    #
    # Physical characteristics
    #
    "phys_characteristic.aspect":"",
    "phys_characteristic.aspect-term":"physicalCharacteristics_keyword-aspect",
    "phys_characteristic.keyword":"",
    "phys_characteristic.keyword-term":"physicalCharacteristics_keyword-keyword",
    "phys_characteristic.notes":"physicalCharacteristics_keyword-notes",
    "phys_characteristic.part":"physicalCharacteristics_keyword-part",

    "physical_description": "physicalCharacteristics_physicalDescription_description",
    "technique.part":"physicalCharacteristics_technique-part",
    "technique": "",#parent
    "technique-term": "physicalCharacteristics_technique-technique",
    "technique.notes": "physicalCharacteristics_technique-notes",

    "material.part":"physicalCharacteristics_material-part",
    "material": "",#parent
    "material-term":"physicalCharacteristics_material-material",
    "material.notes":"physicalCharacteristics_material-notes",

    "dimension.part": "physicalCharacteristics_dimension-part",
    "dimension.type": "",#parent
    "dimension.type-term":"physicalCharacteristics_dimension-dimension",
    "dimension.value":"physicalCharacteristics_dimension-value",
    "dimension.unit": "",#parent
    "dimension.unit-term": "physicalCharacteristics_dimension-units",
    "dimension.precision": "physicalCharacteristics_dimension-precision",
    "dimension.notes": "physicalCharacteristics_dimension-notes",

    "frame":"physicalCharacteristics_frame-frame",#parent
    "frame.notes":"physicalCharacteristics_frame-detail",

    #
    # Iconography
    #
    "content.motif.general": "",#parent
    "content.motif.general-term": "iconography_generalSearchCriteria_generalthemes",
    "content.motif.specific":"",#parent
    "content.motif.specific-term":"iconography_generalSearchCriteria_specificthemes",
    
    "content.classification.scheme":"iconography_generalSearchCriteria_classificationTheme-term",
    "content.classification.code":"iconography_generalSearchCriteria_classificationTheme-code",
    
    "content.description.part":"iconography_contentDescription-part",
    "content.description":"iconography_contentDescription-description",
    
    "content.person.position":"iconography_contentPersonInstitution-position",
    "content.person.name":"iconography_contentPersonInstitution-names",
    "content.person.name-name":"",#value is in the relation - parent
    "content.person.name.type":"",#parent
    "content.person.name.type-text": "iconography_contentPersonInstitution-nameType",
    "content.person.note":"iconography_contentPersonInstitution-notes",

    "content.subject.position":"iconography_contentSubjects-position",
    
    "content.subject.type": "iconography_contentSubjects-subjectType",#parent
    "content.subject.type-text":"iconography_contentSubjects-subjectType",
    
    "content.subject.name": "",#parent
    "content.subject.name-term": "iconography_contentSubjects-properName",
    "content.subject.tax.rank": "",#parent
    "content.subject.tax.rank-text":"iconography_contentSubjects-taxonomicRank",
    "content.subject.tax":"iconography_contentSubjects-scientificName",#parent
    "content.subject.tax-scientific_name": "",
    "content.subject.note": "iconography_contentSubjects-notes",

    "content.subject":"",
    "content.subject-term":"iconography_contentSubjects-subject",
    "content.subject.identifier":"iconography_contentSubjects-identifier",

    "content.date.position": "iconography_contentPeriodDates-position",
    "content.date.period":"",# parent
    "content.date.period-term":"iconography_contentPeriodDates-period",
    "content.date.start":"iconography_contentPeriodDates-startDate",
    "content.date.end":"iconography_contentPeriodDates-endDate",
    "content.date.note":"iconography_contentPeriodDates-notes",

    # Iconografisch bron
    "content.source.general":"iconography_iconographySource_sourceGeneral",
    "content.source.object_number":"iconography_iconographySource_sourceObjectNumber",
    "content.source.specific":"iconography_iconographySource_sourceSpecific",

    #
    # Inscriptions and markings
    # 
    "inscription.type":"",#parent
    "inscription.type-term":"inscriptionsMarkings_inscriptionsAndMarkings-type",
    "inscription.position":"inscriptionsMarkings_inscriptionsAndMarkings-position",
    "inscription.method":"inscriptionsMarkings_inscriptionsAndMarkings-method",
    "inscription.date":"inscriptionsMarkings_inscriptionsAndMarkings-date",
    "inscription.maker":"inscriptionsMarkings_inscriptionsAndMarkings-creators",
    "inscription.maker-name":"",# name is in the parent
    "inscription.maker.role":"",# parent
    "inscription.maker.role-term":"inscriptionsMarkings_inscriptionsAndMarkings-role",
    "inscription.content":"inscriptionsMarkings_inscriptionsAndMarkings-content",
    "inscription.description":"inscriptionsMarkings_inscriptionsAndMarkings-description",
    "inscription.interpretation":"inscriptionsMarkings_inscriptionsAndMarkings-interpretation",
    "inscription.language":"inscriptionsMarkings_inscriptionsAndMarkings-language",
    "inscription.translation":"inscriptionsMarkings_inscriptionsAndMarkings-translation",
    "inscription.script":"",#parent
    "inscription.script-term":"inscriptionsMarkings_inscriptionsAndMarkings-script",
    "inscription.transliteration":"inscriptionsMarkings_inscriptionsAndMarkings-transliteration",
    "inscription.notes":"inscriptionsMarkings_inscriptionsAndMarkings-notes",

    #
    # Nummers / relaties
    #

    "Alternative_number":"",#parent
    "Alternative_number-alternative_number.type": "numbersRelationships_numbers-type",
    "Alternative_number-alternative_number": "numbersRelationships_numbers-number",
    "Alternative_number-alternative_number.institution": "numbersRelationships_numbers-institution",
    "Alternative_number-alternative_number.date": "numbersRelationships_numbers-date",

    "part_of_reference":"numbersRelationships_relationshipsWithOtherObjects_partOf",
    "part_of.notes": "numbersRelationships_relationshipsWithOtherObjects_notes",
    "parts_reference": "numbersRelationships_relationshipsWithOtherObjects_parts-parts",
    "parts.notes": "numbersRelationships_relationshipsWithOtherObjects_parts-notes",

    "related_object.reference": "numbersRelationships_relationshipsWithOtherObjects_relatedObjects-relatedObject",
    "related_object.association": "",#parent
    "related_object.association-term": "numbersRelationships_relationshipsWithOtherObjects_relatedObjects-associations",
    "related_object.notes":"numbersRelationships_relationshipsWithOtherObjects_relatedObjects-notes",

    "digital_reference.type":"numbersRelationships_digitalReferences-type",
    "digital_reference":"numbersRelationships_digitalReferences-reference",

    #
    # Documentatie
    #

    "documentation":"",#parent
    "documentation-documentation.title":"documentation_documentation-titles",#relation
    "documentation-documentation.title-lead_word":"documentation_documentation-article",
    "documentation-documentation.title-title":"",
    "documentation-documentation.title-author.name":"documentation_documentation-author",
    "documentation-documentation.page_reference":"documentation_documentation-pageMark",
    "documentation-documentation.notes":"documentation_documentation-notes",
    "documentation-documentation.shelfmark": "documentation_documentation-shelfMark",

    # repeated
    "documentation-documentation.author":"",
    "documentation-documentation.title-shelf_mark":"",
    "documentation-documentation.title.article":"",

    # Documentation (free text)
    "documentation.free_text": "documentationFreeArchive_documentationFreeText-title",
    "archive.number": "",#relation
    "archive.number-number":"documentationFreeArchive_archiveNumber-archiveNumber",
    "archive.number-content": "",
    
    # repeated
    "archive.content":"",

    # Toestand & Conservering
    "condition.part":"conditionConservation_conditions-part",
    "condition":"",#parent
    "condition-term":"conditionConservation_conditions-condition",
    "condition.notes":"conditionConservation_conditions-notes",
    "condition.check.name":"conditionConservation_conditions-checked_by",
    "condition.date":"conditionConservation_conditions-date",


    "completeness":"conditionConservation_completeness-completeness",
    "completeness.notes":"conditionConservation_completeness-notes",
    "completeness.check.name":"conditionConservation_completeness-checked_by",
    "completeness.date":"conditionConservation_completeness-date",

    "old.conservation_request.treatme":"conditionConservation_conservation_request-treatment",
    "old.conservation_request.name":"conditionConservation_conservation_request-requester",
    "old.conservation_request.reason":"conditionConservation_conservation_request-reason",
    "old.conservation_request.date":"conditionConservation_conservation_request-date",
    "old.conservation_request.status":"conditionConservation_conservation_request-status",

    "conservation":"",#parent
    "conservation-conservation.number":"",#parent
    "conservation-conservation.number-treatment_number":"conditionConservation_conservationTreatments-treatmentNumber",
    "conservation-conservation.number-treatment_method":"conditionConservation_conservationTreatments-treatmentMethod",
    "conservation-conservation.number-date.start":"conditionConservation_conservationTreatments-startDate",
    "conservation-conservation.number-date.end":"conditionConservation_conservationTreatments-endDate",

    # repeated
    "conservation-conservation.method":"",
    "conservation-conservation.date.start":"",
    "conservation-conservation.date.end":"",
    "conservation-conservation.lref":"",

    "preservation_form":"",# parent
    "preservation_form-term":"conditionConservation_preservationForm-preservation_form",
    "preservation_form.notes":"conditionConservation_preservationForm-notes",

    "recommendation.display":"conditionConservation_recommendations_display",
    "recommendation.environment":"conditionConservation_recommendations_environment",
    "recommendation.handling":"conditionConservation_recommendations_handling",
    "recommendation.packing":"conditionConservation_recommendations_packing",
    "recommendation.security":"conditionConservation_recommendations_security",
    "recommendation.storage":"conditionConservation_recommendations_storage",
    "requirem.special":"conditionConservation_recommendations_specialRequirements",

    # Aanbevelingen / vereistein
    "credit_line": "recommendationsRequirements_creditLine_creditLine",
    "requirem.legal":"recommendationsRequirements_legalLicenceRequirements_requirements",
    "requirem.legal.held":"recommendationsRequirements_legalLicenceRequirements_requirementsHeld-requirementsHeld",
    "requirem.legal.held.number":"recommendationsRequirements_legalLicenceRequirements_requirementsHeld-number",
    "requirem.legal.held.date.start":"recommendationsRequirements_legalLicenceRequirements_requirementsHeld-currentFrom",
    "requirem.legal.held.date.end":"recommendationsRequirements_legalLicenceRequirements_requirementsHeld-until",
    "requirem.legal.held.renewal":"recommendationsRequirements_legalLicenceRequirements_requirementsHeld-renewalDate",

    #
    # Reproducties
    #
    
    # Reproductie
    "reproduction.reference":"",#parent
    "reproduction.reference-image_reference":"reproductions_reproduction-identifierURL",
    "reproduction.reference-reproduction_type":"reproductions_reproduction-type",
    "reproduction.reference-format":"reproductions_reproduction-format",
    "reproduction.reference-reference_number":"reproductions_reproduction-reference",
    "reproduction.creator": "",
    "reproduction.reference-creator":"reproductions_reproduction-creator",
    "reproduction.reference-production_date":"reproductions_reproduction-date",
    "reproduction.notes":"reproductions_reproduction-notes",
    
    # repeated
    "reproduction.identifier_URL":"",
    "reproduction.format":"",
    "reproduction.type":"",
    "reproduction.date":"",

    # 
    # Waarde
    #

    # Waardebepaling
    "valuation.value":"valueInsurance_valuations-value",
    "valuation.value.currency":"valueInsurance_valuations-curr",
    "valuation.name":"valueInsurance_valuations-valuer",
    "valuation.date":"valueInsurance_valuations-date",
    "valuation.notes":"valueInsurance_valuations-notes",

    # Verzekering
    "insurance.value":"valueInsurance_insurance-value",
    "insurance.value.currency":"valueInsurance_insurance-curr",
    "insurance.valuer":"valueInsurance_insurance-valuer",
    "insurance.date":"valueInsurance_insurance-date",
    "insurance.policy_number":"valueInsurance_insurance-policy_number",
    "insurance.company":"valueInsurance_insurance-insurance_company",
    "insurance.expiry_date":"valueInsurance_insurance-renewal_date",
    "insurance.reference":"valueInsurance_insurance-reference",
    "insurance.conditions":"valueInsurance_insurance-conditions",
    "insurance.notes":"valueInsurance_insurance-notes",

    # 
    # Acquisition
    #
    "accession_date":"acquisition_accession_date",
    "acquisition.number":"acquisition_number",
    "acquisition.reason":"acquisition_reason",
    "acquisition.date":"acquisition_date",
    "acquisition.method":"",
    "acquisition.method-term":"acquisition_methods",
    "acquisition.conditions":"acquisition_conditions",
    "acquisition.source":"acquisition_acquisition_acquisitionfrom",
    "acquisition.source-name":"",# name is in the relation
    "acquisition.place":"",
    "acquisition.place-term":"acquisition_places",
    "acquisition.notes":"acquisition_notes",
    "acquisition.date.precision":"acquisition_precision",

    "acquisition.authorisation.name":"acquisition_authorization_authorizer",
    "acquisition.authorisation.date":"acquisition_authorization_date",

    "acquisition.offer_price.value":"acquisition_costs_offer_price",
    "acquisition.offer_price.currency":"acquisition_costs_offer_price_currency",
    
    "acquisition.auction.lot_number":"acquisition_lot_no",
    "acquisition.auction-auction":"acquisition_auction",
    
    "acquisition.price.value":"acquisition_costs_purchase_price",
    "acquisition.price.notes":"acquisition_costs_notes",
    "acquisition.price.currency":"acquisition_costs_purchase_price_currency",
    
    "acquisition.funding.source":"acquisition_fundings-source",
    "acquisition.funding.proviso":"acquisition_fundings-provisos",
    "acquisition.funding.currency":"acquisition_fundings-curr",
    "acquisition.funding.value":"acquisition_fundings-amount",

    "acquisition.document.description":"acquisition_documentation-description",
    "acquisition.document.reference":"acquisition_documentation-reference",

    "copyright":"acquisition_copyright",

    # DOUBLE CHECK:
    "acquisition.subject":"",
    "acquisition.subject.type":"",


    #
    # Afstoting
    #

    # Uitschrijving
    "deaccession.date":"disposal_deaccession",
    "new_object_number":"disposal_new_object_number",
    
    # Afstoning
    "disposal.number":"disposal_number",
    "disposal.date":"disposal_date",
    "disposal.method": "disposal_method",
    "disposal.prop_recipient":"disposal_disposal_proposedRecipient",
    "disposal.prop_recipient-name":"",#name is in the relation - parent
    "disposal.recipient":"disposal_disposal_recipient",
    "disposal.recipient-name":"",# name is in the relation - parent
    "disposal.reason":"disposal_reason",
    "disposal.provisos":"disposal_provisos",

    # Financie
    "disposal.price.value":"disposal_finance_disposal_price",
    "disposal.price.currency":"disposal_finance_currency",

    # Documentatie
    "disposal.document.description":"disposal_documentation-description",
    "disposal.document.reference":"disposal_documentation-reference",
    "disposal.notes":"disposal_notes",
    "despatch.number":"",
    "acquisition.auction":"",
    #
    # Associations
    #
    "association.person":"associations_associatedPersonInstitutions-names",
    "association.person.type":"",
    "association.person.type-text":"associations_associatedPersonInstitutions-nameType",
    "association.person-name":"",#name is in the relation
    "association.person.association":"",
    "association.person.association-term":"associations_associatedPersonInstitutions-associations",
    "association.person.date.start":"associations_associatedPersonInstitutions-startDate",# removed based on feedback
    "association.person.date.end":"associations_associatedPersonInstitutions-endDate",# removed based on feedback
    "association.person.note":"associations_associatedPersonInstitutions-notes",
    "association.subject.tax.rank":"",
    "association.subject.tax.rank-text": "associations_associatedSubjects-taxonomicRank",
    "association.subject.tax":"associations_associatedSubjects-scientificName",
    "association.subject.tax-scientific_name": "",
    "association.subject.name":"",
    "association.subject.name-term":"associations_associatedSubjects-properName",
    "association.subject":"",
    "association.subject.type":"",
    "association.subject.type-text":"associations_associatedSubjects-subjectType",
    "association.subject-term":"associations_associatedSubjects-subject",
    "association.subject.association":"",
    "association.subject.association-term":"associations_associatedSubjects-associations",
        
    # In the future this two fields are likely to be removed
    "association.subject.date.start":"associations_associatedSubjects-startDate",
    "association.subject.date.end":"associations_associatedSubjects-endDate",
    
    "association.subject.note":"associations_associatedSubjects-notes",
    "association.period.date.start":"associations_associatedPeriods-startDate",
    "association.period.date.end":"associations_associatedPeriods-endDate",
    "association.period.assoc":"",
    "association.period.assoc-term":"associations_associatedPeriods-associations",
    "association.period":"",
    "association.period-term":"associations_associatedPeriods-period",
    "association.period.note":"associations_associatedPeriods-notes",
    
    
    #
    #  Eigendomsgeschiedenis
    #

    "current_owner": "ownershipHistory_ownership_currentOwner",
    "current_owner-name":"",#value its in the relation (parent)

    "owner_hist.owner":"ownershipHistory_historyOwner-owner",
    "owner_hist.owner-name":"",#parent
    "owner_hist.date.start":"ownershipHistory_historyOwner-startDate",
    "owner_hist.date.end":"ownershipHistory_historyOwner-endDate",
    "owner_hist.acquisition.method":"",
    "owner_hist.acquisition.method-term":"ownershipHistory_historyOwner-method",
    "owner_hist.acquired_from":"ownershipHistory_historyOwner-acquiredFrom",
    "owner_hist.acquired_from-name":"",#value is in the relation - parent
    "owner_hist.auction":"",#parent
    "owner_hist.auction-auction":"ownershipHistory_historyOwner-auction",#relation in the parent (future)
    "owner_hist.auction.lot_number":"ownershipHistory_historyOwner-lotnr",
    "owner_hist.place":"",#parent
    "owner_hist.place-term":"ownershipHistory_historyOwner-place",

    "owner_hist.notes":"ownershipHistory_historyOwner-notes",
    "owner_hist.price":"ownershipHistory_historyOwner-price",
    "owner_hist.ownership_category":"ownershipHistory_historyOwner-category",
    "owner_hist.access":"ownershipHistory_historyOwner-access",


    #
    # Location
    #

    "location.default":"",#parent
    "location.default-term":"location_normalLocation_normalLocation",

    "location.date.begin":"location_currentLocation-start_date",
    "location.date.end":"location_currentLocation-end_date",
    "location":"",#parent
    "location-term":"location_currentLocation-location",
    "location.fitness":"location_currentLocation-fitness",
    "location_type":"location_currentLocation-location_type",
    "location.notes":"location_currentLocation-notes",

    "location_check.name":"location_checks-checked_by",
    "location_check.date":"location_checks-date",
    "location_check.notes":"location_checks-notes",



    #
    # Vondstomstandigheden
    #

    "field_coll.number":"fieldCollection_fieldCollection_fieldCollNumber-number",
    "Collector":"",#parent
    "Collector-field_coll.name":"fieldCollection_fieldCollection_collectors-name",
    "Collector-field_coll.name-name":"",#its in the relation
    "Collector-field_coll.name.role":"",# parent
    "Collector-field_coll.name.role-term":"fieldCollection_fieldCollection_collectors-role",

    #"Collector-field_coll.name.lref":"",
    #"Collector-field_coll.name.role.lref":"",
 
    "field_coll.event":"",#parent
    "field_coll.event-term":"fieldCollection_fieldCollection_events",
    "field_coll.date.start":"fieldCollection_fieldCollection_dateEarly",
    "field_coll.date.start.precision":"fieldCollection_fieldCollection_dateEarlyPrecision",
    "field_coll.date.end":"fieldCollection_fieldCollection_dateLate",
    "field_coll.date.end.precision":"fieldCollection_fieldCollection_dateLatePrecision",
    "field_coll.method":"",#parent
    "field_coll.method-term":"fieldCollection_fieldCollection_methods",
    "field_coll.place":"",#parent
    "field_coll.place-term":"fieldCollection_fieldCollection_places",

    #"field_coll.method.lref":"",

    "Fieldcollplacecode":"",#parent
    "Fieldcollplacecode-field_coll.place.code":"",#parent
    "Fieldcollplacecode-field_coll.place.code-term":"fieldCollection_fieldCollection_placeCodes-code",
    "Fieldcollplacecode-field_coll.place.code.type":"",#parent
    "Fieldcollplacecode-field_coll.place.code.type-term":"fieldCollection_fieldCollection_placeCodes-codeType",
    
    #"Fieldcollplacecode-field_coll.code.type.lref":"",
    #"Fieldcollplacecode-field_coll.place.code.lref":"",

    "field_coll.place.feature":"",#parent
    "field_coll.place.feature-term":"fieldCollection_fieldCollection_placeFeatures",
    
    #"field_coll.event.lref":"",
    #"field_coll.place.lref":"",
    #"field_coll.place.feature.lref":"",

    "Grid":"",
     #"Grid-grid.type.lref":"",
    "Grid-grid.type":"",#parent
    "Grid-grid.type-term":"fieldCollection_coordinatesFieldCollectionPlace-gridType",
    "Grid-grid.X_reference":"fieldCollection_coordinatesFieldCollectionPlace-xCoordinate",
    "Grid-grid.X_reference.addition":"fieldCollection_coordinatesFieldCollectionPlace-xAddition",
    "Grid-grid.Y_reference":"fieldCollection_coordinatesFieldCollectionPlace-yCoordinate",
    "Grid-grid.Y_reference.addition":"fieldCollection_coordinatesFieldCollectionPlace-yAddition",
    "Grid-grid.precision":"fieldCollection_coordinatesFieldCollectionPlace-precision",

    "Stratigraphy":"",#parent
    "Stratigraphy-stratigraphy.unit":"",#parent
    "Stratigraphy-stratigraphy.unit-term":"fieldCollection_habitatStratigraphy_stratigrafie-unit",
    "Stratigraphy-stratigraphy.type":"",#parent
    "Stratigraphy-stratigraphy.type-term":"fieldCollection_habitatStratigraphy_stratigrafie-type",
    "habitat":"",#parent
    "habitat-term":"fieldCollection_habitatStratigraphy_habitats",

    "field_coll.notes":"fieldCollection_notes-notes",

    #
    # Tentoonstelling
    #
    "exhibition":"",#parent
    "exhibition-exhibition.catalogue_number":"exhibitions_exhibition-catObject",
    "exhibition-exhibition":"exhibitions_exhibition-exhibitionName",
    "exhibition-title":"exhibitions_exhibition-name",
    "exhibition-old.exhibition.date.start":"",
    "exhibition-exhibition.notes":"exhibitions_exhibition-notes",
    "exhibition-exhibition-venue":"exhibitions_exhibition-venue",
    "exhibition-exhibition-date.start":"exhibitions_exhibition-date",
    "exhibition-exhibition-date.end":"exhibitions_exhibition-to",
    "exhibition-exhibition-organiser":"exhibitions_exhibition-organiser",
    "exhibition-exhibition-venue.place":"exhibitions_exhibition-place",
    
    #"exhibition-exhibition.lref":"",
    
    # repeated fields
    "exhibition-exhibition.venue":"",
    "exhibition.date.start":"",
    "exhibition.date.end":"",
    "exhibition.organiser":"",
    "exhibition.venue.place":"",
    "exhibition-old.exhibition.date.end":"",
    "exhibition-exhibition-title":"",
    "exhibition-exhibition.date.start":"",
    "exhibition-exhibition.date.end":"",
    "exhibition-exhibition.organiser":"",
    "exhibition-exhibition.venue.place":"",

    #
    # Bruikelen
    #
    "Loan_out":"",#parent
    "Loan_out-loan.out.requester":"",#parent
    "Loan_out-loan.out.request.reason":"",#parent
    "Loan_out-loan.out.number-request.reason":"loans_outgoingLoans-requestReason",

    "Loan_out-loan.out.contract.period.start":"",
    "Loan_out-loan.out.contract.period.end":"",
    "Loan_out-loan.out.number":"loans_outgoingLoans-loannumber",#relation
    "Loan_out-loan.out.number-contract.period.start":"loans_outgoingLoans-contractPeriod",
    "Loan_out-loan.out.number-contract.period.end":"loans_outgoingLoans-contractPeriod-to",
    
    
    "Loan_out-loan.out.number-loan_status":"loans_outgoingLoans-status",
    "Loan_out-loan.out.status":"",#repeated

    "Loan_out-loan.out.requester":"",#repeated
    "Loan_out-loan.out.number-requester":"loans_outgoingLoans-requester",

    "Loan_out-loan.out.requester.contact":"",#repeated
    "Loan_out-loan.out.number-requester.contact":"loans_outgoingLoans-contact",
    "Loan_out-loan.out.number-loan_number":"loans_outgoingLoans-loanNumber",
    
    #"Loan_out-loan.out.number.lref":"",
    "Loan_out-loan.out.request.period.start":"",#repeated
    "Loan_out-loan.out.number-request.period.start":"loans_outgoingLoans-requestPeriod",
    "Loan_out-loan.out.request.period.end":"",#repeated
    "Loan_out-loan.out.number-request.period.end":"loans_outgoingLoans-requestPeriodTo",
    
    #"Loan_out-loan.out.number.lref":"",
    
    "Loan_in":"",
    "Loan_in-loan.in.requester":"",#repeated
    "Loan-in-loan.in.number":"loans_incomingLoans-loannumber",#relation
    "Loan_in-loan.in.request.reason":"",
    "Loan_in-loan.in.number-request.reason":"loans_incomingLoans-requestReason",
    
    "Loan_in-loan.in.number":'',
    "Loan_in-loan.in.contract.period.start":"",
    "Loan_in-loan.in.number-contract.period.start":"loans_incomingLoans-contractPeriod",
    "Loan_in-loan.in.contract.period.end":"",
    "Loan_in-loan.in.number-contract.period.end":"loans_incomingLoans-contractPeriod-to",
    
    "Loan_in-loan.in.status":"",#repeated
    "Loan_in-loan.in.number-loan_status":"loans_incomingLoans-status",

    "Loan_in-loan.in.lender":"",#repeated
    "Loan_in-loan.in.number-lender":"loans_incomingLoans-lender",

    "Loan_in-loan.in.requester.contact":"",#repeated
    "Loan_in-loan.in.number-lender.contact":"loans_incomingLoans-contact",
    "Loan_in-loan.in.number-loan_number":"loans_incomingLoans-loanNumber",
    
    #"Loan_in-loan.in.number.lref":"",
    "Loan_in-loan.in.request.period.start":"",#repeated
    "Loan_in-loan.in.number-request.period.start":"loans_incomingLoans-requestPeriod",
    "Loan_in-loan.in.request.period.end":"",#repeated
    "Loan_in-loan.in.number-request.period.end":"loans_incomingLoans-requestPeriodTo",

    #
    # Etiketten
    #

    "label":"",
    "label-label.date":"labels-date",
    "label-label.text":"labels-text",

    #
    # Notes
    #

    "notes":"notes-notes",
    "free_field.content":"notes_free_fields-content",
    "free_field.date":"notes_free_fields-date",
    "free_field.confidential":"notes_free_fields-notesConfidential",
    "free_field.type":"notes_free_fields-type",

    #
    # Extras - Edit
    #

    # Edit
    "Edit":"",
    "input.date":"managementDetails_input-date",
    "input.time":"managementDetails_input-time",
    "input.source":"managementDetails_input-source",
    "input.name":"managementDetails_input-name",
    "Edit-edit.date":"managementDetails_edit-editDate",
    "Edit-edit.notes":"managementDetails_edit-editNotes",
    "Edit-edit.name":"managementDetails_edit-editName",
    "Edit-edit.time":"managementDetails_edit-editTime",
    "Edit-edit.source":"managementDetails_edit-editSource",

    # Transport tab
    "despatch.date":"transport_despatch-date",
    "despatch.arrival_date":"transport_despatch-arrival_date",
    "despatch.destination":"transport_despatch-destination",
    "despatch.number-despatch_date":"transport_despatchNumber-despatch_date",
    "despatch.number-delivery_date":"transport_despatchNumber-delivery_date",
    "despatch.number-destination":"transport_despatchNumber-destination",
    "despatch.number-transport_number":"transport_despatchNumber-transport_number",
    
    "entry.depositor":"",#repeated
    "entry.number-depositor":"transport_entry_number-depositor",
    "entry.reason":"",#repeated
    "entry.number-entry_reason":"transport_entry_number-entry_reason",
    "entry.number-transport_number":"",#value in the relation
    "entry.entry_date":"",#repeated
    "entry.number-entry_date":"transport_entry_number-entry_date",
    "entry.return_date":"",#repeated
    "entry.number-return_date":"transport_entry_number-return_date",
    "entry.owner":"",#repeated
    "entry.number-owner":"transport_entry_number-owner",
    "entry.number":"transport_entry_number-transport_number",

    "datasets.document-text":"",
    "datasets.document":"",

    "object_name.authority-term":"",
    "object_name.authority":"",

} 


