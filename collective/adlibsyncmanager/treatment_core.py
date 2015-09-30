#!/usr/bin/env python
# -*- coding: utf-8 -*-

TREATMENT_CORE = {
	
	# Treatment details
	'priref': "priref",

	'treatment_number':'treatmentDetails_identification_treatmentNumber',
    'treatment_type-text':'treatmentDetails_identification_treatmentType',
    'reversible':'treatmentDetails_identification_reversible',
    'Treatmentmethod-treatment_method-term':'treatmentDetails_identification_treatmentMethod',
    'Conservator-conservator':'treatmentDetails_identification_conservator-name', # repeatable
    "Conservator-conservator-name": "",
    'Material-material-term':'treatmentDetails_identification_material',
    'date.start':'treatmentDetails_progress_startDate',
    'status':'treatmentDetails_progress_status',
    'recall_date':'treatmentDetails_progress_recallDate',
    'date.end':'treatmentDetails_progress_endDate',
    
    'condition_description':'treatmentDetails_treatment_conditionDescription-description', # repeatable
    'treatment_plan':'treatmentDetails_treatment_treatmentPlan-plan', # repeatable
    'treatment_summary':'treatmentDetails_treatment_treatmentSummary-summary', # repeatable
    
    'Digreference-digital_reference.type':'treatmentDetails_digitalReferences-type', # repeatable
    'Digreference-digital_reference':'treatmentDetails_digitalReferences-reference', # repeatable
    'Digreference-digital_reference.notes':'treatmentDetails_digitalReferences-notes', # repeatable
    'notes':'treatmentDetails_notes-notes', # repeatable

	# Reproductions
	'reproduction-reproduction.reference-reference_number': 'reproductions_reproduction-reference',
    'reproduction-reproduction.reference-image_reference': 'reproductions_reproduction-identifierURL',
    'reproduction-reproduction.notes': 'reproductions_reproduction-notes',
	
	# Linked objects
	'object.object_number':"linkedObjects_linkedObjects-objectNumber" #repeatable

}
