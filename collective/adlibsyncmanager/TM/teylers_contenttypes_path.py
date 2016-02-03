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
		        "total":"/var/www/tm-data/xml/coins-v04.xml"
		    }
		},
		"fossils": {
			"dev":{
		        "single":"/Users/AG/Projects/NewTeylersMuseum/xml/single-fossil-v01.xml",
		        "total":"/Users/AG/Projects/NewTeylersMuseum/xml/all-fossils-v01.xml"
		    },
		    "prod": {
		        "single":"/var/www/tm-data/xml/single-fossil.xml",
		        "total":"/var/www/tm-data/xml/fossils.xml"
		    }
		},
		"kunst": {
			"dev":{
		        "single":"/Users/AG/Projects/NewTeylersMuseum/xml/single-kunst-KG12857.xml",
		        "total":"/Users/AG/Projects/NewTeylersMuseum/xml/all-kunst-v01.xml"
		    },
		    "prod": {
		        "single":"/var/www/tm-data/xml/single-kunst-1.xml",
		        "total":"/var/www/tm-data/xml/kunst.xml"
		    }
		},
		"instruments": {
			"dev":{
		        "single":"/Users/AG/Projects/NewTeylersMuseum/xml/single-instrument-FK0014.xml",
		        "total":"/Users/AG/Projects/NewTeylersMuseum/xml/all-instruments-v01.xml"
		    },
		    "prod": {
		        "single":"/var/www/tm-data/xml/single-instrument.xml",
		        "total":"/var/www/tm-data/xml/instruments.xml"
		    }
		},
		"books": {
			"dev":{
		        "single":"/Users/AG/Projects/NewTeylersMuseum/xml/single-book-v01.xml",
		        "total":"/Users/AG/Projects/NewTeylersMuseum/xml/all-books-v04.xml"
		    },
		    "prod": {
		        "single":"/var/www/tm-data/xml/single-book.xml",
		        "total":"/var/www/tm-data/xml/books-v04.xml"
		    }
		}
	}
}

IMAGES_HD_PATH = {
	'coins': {
		'dev': { 
			'path':'/Volumes/Website Numis/Numis voorwebsite/*.jpg'
		},
		'prod': {
			'path':'/var/www/tm-data/Coins/Numis voorwebsite/*.jpg'
		},
		'sync': {
			'path':'/var/www/tm-data/Coins/Numis voorwebsite/*.jpg'
		}
	},
	'kunst': {
		'dev': { 
			#'path':'/Volumes/INTK Kunst/Kunst web dec 2015/JPEG/*.jpg'
			'path':'/Users/AG/Projects/NewTeylersMuseum/Art/*.jpg'
		},
		'prod': {
			'path':'/var/www/tm-data/Kunst/JPEG/*.jpg'
			#'path':'/var/www/tm-data/Kunst-fix/*.jpg'
		},
		'sync': {
			'path':'/var/www/tm-data/Coins/Numis voorwebsite/*.jpg'
		}
	},
	'instruments': {
		'dev': { 
			'path':'/Volumes/INSTRUM-WEB/Instruments-web corrections/'
		},
		'prod': {
			'path':'/var/www/tm-data/Instruments/INSTRUM-WEB/Instruments-web corrections/'
		},
		'sync': {
			'path':''
		}
	},
	'books': {
		'dev': { 
			'path':''
		},
		'prod': {
			'path':'/var/www/tm-data/Fossils/Boeken/*.jpg'
		},
		'sync': {
			'path':''
		}
	},
	'fossils': {
		'dev': { 
			'path':'/Users/AG/Projects/NewTeylersMuseum/Fossils/*.jpg'
		},
		'prod': {
			'path':'/var/www/tm-data/Fossils/*.jpg'
		},
		'sync': {
			'path':''
		}
	},
}

