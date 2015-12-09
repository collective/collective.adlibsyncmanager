#!/usr/bin/env python
# -*- coding: utf-8 -*-

CONTENT_TYPES_PATH = {
	"Object": {
		"coins": {
		    "dev":{
		        "single":"/Users/AG/Projects/NewTeylersMuseum/xml/single-coin-8006953-v01.xml",
		        "total":"/Users/AG/Projects/NewTeylersMuseum/xml/all-coins-v03.xml"
		    },
		    "prod": {
		        "single":"/var/www/tm-data/xml/single-coin.xml",
		        "total":"/var/www/tm-data/xml/coins-v03.xml"
		    }
		}
	}
}

IMAGES_HD_PATH = {
	'dev': {
		'path':'/Volumes/Website Numis/Numis voorwebsite/*.jpg'
	},
	'prod': {
		'path':'/var/www/tm-data/Coins/Numis voorwebsite/*.jpg'
	},
	'sync': {
		'path':'/var/www/tm-data/Coins/Numis voorwebsite/*.jpg'
	}
}

