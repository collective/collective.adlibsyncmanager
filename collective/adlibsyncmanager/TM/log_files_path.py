#!/usr/bin/env python
# -*- coding: utf-8 -*-

LOG_FILES_PATH = {
	"import": {
		"error": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/error/error_%s_%s_%s.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/error/error_%s_%s_%s.csv"
		},
		
		"status": {
			"dev":'/Users/AG/Projects/NewTeylersMuseum/logs/status/status_%s_%s_%s.csv',
			"prod":"/var/www/centraalmuseum-dev/cm-logs/status/status_%s_%s_%s.csv"
		},

		"warning": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/warning/warning_%s_%s_%s.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/warning/warning_%s_%s_%s.csv"
		},

		"images": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/images/images_%s_%s_%s.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/images/images_%s_%s_%s.csv"
		}
	},
	"sync": {
		"error": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/sync/sync_errors.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/sync/sync_errors.csv"
		},

		"error_import": {
			"dev":'/Users/AG/Projects/NewTeylersMuseum/logs/sync/sync_error.csv',
			"prod":"/var/www/centraalmuseum-dev/cm-logs/sync/import/sync_error_%s_%s.csv"
		},
		
		"status": {
			"dev":'/Users/AG/Projects/NewTeylersMuseum/logs/sync/sync_status.csv',
			"prod":"/var/www/centraalmuseum-dev/cm-logs/sync/sync_status.csv"
		},

		"warning": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/sync/sync_warning.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/sync/sync_warning.csv"
		},

		"images": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/sync/sync_images.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/images/sync_images.csv"
		},

		"created": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/sync/created_objects.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/sync/created_objects.csv"
		},
		
		"deleted": {
			"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/sync/deleted_objects.csv",
			"prod":"/var/www/centraalmuseum-dev/cm-logs/sync/deleted_objects.csv"
		}
	}
	
}
