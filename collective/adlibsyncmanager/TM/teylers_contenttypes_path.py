#!/usr/bin/env python
# -*- coding: utf-8 -*-

CONTENT_TYPES_PATH = {
	"Object": {
		"coins": {
		    "dev":{
		        "single":"/Users/AG/Projects/NewTeylersMuseum/xml/single-coin-v02.xml",
		        "total":"/Users/AG/Projects/NewTeylersMuseum/xml/coins-export10-v02.xml"
		    },
		    "prod": {
		        "single":"",
		        "total":"/var/www/tm-data/xml/coins.xml"
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
	}
}

