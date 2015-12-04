#!/usr/bin/env python
# -*- coding: utf-8 -*-

LOG_FILES_PATH = {
	"error": {
		"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/error/error_%s_%s.csv",
		"prod":"/var/www/tm-logs/error/error_%s_%s.csv"
	},

	"status": {
		"dev":'/Users/AG/Projects/NewTeylersMuseum/logs/status/status_%s_%s.csv',
		"prod":"/var/www/tm-logs/status/status_%s_%s.csv"
	},

	"warning": {
		"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/warning/warning_%s_%s.csv",
		"prod":"/var/www/tm-logs/warning/warning_%s_%s.csv"
	},
	"images": {
		"dev":"/Users/AG/Projects/NewTeylersMuseum/logs/images/images_%s_%s.csv",
		"prod":"/var/www/tm-logs/images/images_%s_%s.csv"
	}
}
