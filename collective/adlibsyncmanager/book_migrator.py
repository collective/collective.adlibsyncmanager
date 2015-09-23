#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""
from Acquisition import aq_parent, aq_inner

from plone import api

from z3c.relationfield.schema import RelationList

import fnmatch
from lxml import etree
import urllib2, urllib
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
from plone.multilingual.interfaces import ITranslationManager
import datetime
import os
import csv
import unicodedata
import sys

from Products.CMFCore.utils import getToolByName
from zope.intid.interfaces import IIntIds
import re
import AccessControl
import transaction
import time
import sys
from DateTime import DateTime
from plone.i18n.normalizer import idnormalizer
from Testing.makerequest import makerequest
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from plone.dexterity.utils import createContentInContainer
from collective.leadmedia.utils import addCropToTranslation
from collective.leadmedia.utils import imageObjectCreated
from plone.app.textfield.value import RichTextValue

from z3c.relationfield import RelationValue
from zope import component

XML_PATH = ""
TEST_OBJECT = 0

class BookMigrator:
    
    def __init__(self, APIMigrator):
        self.api_migrator = APIMigrator

    def get_book_from_instance(self, priref):
        book_folder = self.api_migrator.get_folder('nl/bibliotheek/boeken')

        for brain in book_folder:
            item = book_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    def get_audiovisual_from_instance(self, priref):
        book_folder = self.api_migrator.get_folder('nl/bibliotheek/audio-visuele-materialen')

        for brain in book_folder:
            item = book_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    def get_article_from_instance(self, priref):
        book_folder = self.api_migrator.get_folder('nl/bibliotheek/artikelen')

        for brain in book_folder:
            item = book_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    def get_serial_from_instance(self, priref):
        book_folder = self.api_migrator.get_folder('nl/bibliotheek/tijdschriften')

        for brain in book_folder:
            item = book_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    def get_resource_from_instance(self, priref):
        book_folder = self.api_migrator.get_folder('nl/bibliotheek/digitale-bronnen')

        for brain in book_folder:
            item = book_folder[brain]
            if hasattr(item, 'priref'):
                if item.priref == priref:
                    return item

        return None

    # fieldsets

    def get_serial_title_author_fieldset(self, data, record):

        # Article
        if record.find('lead_word') != None:
            data['titleAuthorImprintCollation_titleAuthor_leadWord'] = self.api_migrator.trim_white_spaces(record.find('lead_word').text)

        # Title
        titles = []
        if len(record.findall('title')) > 0:
            for title in record.findall('title'):
                titles.append({
                    "title": self.api_migrator.trim_white_spaces(title.text)
                    })

        data['titleAuthorImprintCollation_titleAuthor_title'] = titles

        # titleAuthorImprintCollation_titleAuthor_statementOfRespsib
        if record.find('statement_of_responsibility') != None:
            data['titleAuthorImprintCollation_titleAuthor_statementOfRespsib'] = self.api_migrator.trim_white_spaces(record.find('statement_of_responsibility').text)

        # titleAuthorImprintCollation_titleAuthor_author
        authors = []
        if len(record.findall('author.name')) > 0:
            for author in record.findall('author.name'):
                if author.find('name') != None:
                    authors.append({
                        "author": self.api_migrator.trim_white_spaces(author.find('name').text),
                        "role": ""
                        })


        if len(authors) > 0:
            if len(record.findall('author.role')) > 0:
                for slot, role in enumerate(record.findall('author.role')):
                    if role.find('term') != None:
                        authors[slot]['role'] = self.api_migrator.trim_white_spaces(role.find('term').text)

        data['titleAuthorImprintCollation_titleAuthor_author'] = authors

        # titleAuthorImprintCollation_titleAuthor_corpAuthor
        if record.find('corporate_author') != None:
            if record.find('corporate_author').find('name') != None:
                data['titleAuthorImprintCollation_titleAuthor_corpAuthor'] = self.api_migrator.trim_white_spaces(record.find('corporate_author').find('name').text)

        # titleAuthorImprintCollation_edition_edition
        if record.find('edition') != None:
            data['titleAuthorImprintCollation_edition_edition'] = self.api_migrator.trim_white_spaces(record.find('edition').text)

        # titleAuthorImprintCollation_edition_edition
        if record.find('issues') != None:
            data['titleAuthorImprintCollation_issues_issues'] = self.api_migrator.trim_white_spaces(record.find('issues').text)

        # titleAuthorImprintCollation_imprint_place
        places = []
        if len(record.findall('place_of_publication')) > 0:
            for place in record.findall('place_of_publication'):
                places.append({
                    "term": self.api_migrator.trim_white_spaces(place.text)
                    })

        data['titleAuthorImprintCollation_imprint_place'] = places

        # titleAuthorImprintCollation_imprint_publisher
        publishers = []
        if len(record.findall('publisher')) > 0:
            for publisher in record.findall('publisher'):
                if publisher.find('name') != None:
                    publishers.append({
                        "term": self.api_migrator.trim_white_spaces(publisher.find('name').text)
                        })

        data['titleAuthorImprintCollation_imprint_publisher'] = publishers

        # titleAuthorImprintCollation_imprint_year
        if record.find('year_of_publication') != None:
            data['titleAuthorImprintCollation_imprint_year'] = self.api_migrator.trim_white_spaces(record.find('year_of_publication').text)

        # titleAuthorImprintCollation_imprint_placePrinted
        placesprinted = []

        if len(record.findall('print.place')) > 0:
            for placep in record.findall('print.place'):
                if placep.find('term') != None:
                    placesprinted.append({
                        "term": self.api_migrator.trim_white_spaces(placep.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_placePrinted'] = placesprinted

        # titleAuthorImprintCollation_imprint_printer
        printers = []
        if len(record.findall('print.name')) > 0:
            for printer in record.findall('print.name'):
                if printer.find('term') != None:
                    printers.append({
                        "term": self.api_migrator.trim_white_spaces(printer.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_printer'] = printers

        # titleAuthorImprintCollation_sortYear_sortYear
        if record.find('sort_year') != None:
            data['titleAuthorImprintCollation_sortYear_sortYear'] = self.api_migrator.trim_white_spaces(record.find('sort_year').text)

        # titleAuthorImprintCollation_collation_illustrations
        if record.find('illustrations') != None:
            data['titleAuthorImprintCollation_collation_illustrations'] = self.api_migrator.trim_white_spaces(record.find('illustrations').text)

        # titleAuthorImprintCollation_collation_dimensions
        if record.find('dimensions') != None:
            data['titleAuthorImprintCollation_collation_dimensions'] = self.api_migrator.trim_white_spaces(record.find('dimensions').text)

        # titleAuthorImprintCollation_collation_accompanyingMaterial
        materials = []
        if len(record.findall('accompanying_material')) > 0:
            for material in record.findall('accompanying_material'):
                materials.append({
                    "term": self.api_migrator.trim_white_spaces(material.text)
                    })

        data['titleAuthorImprintCollation_collation_accompanyingMaterial'] = materials

        return True

    def get_article_title_author_fieldset(self, data, record):
        # Article
        if record.find('lead_word') != None:
            data['titleAuthorSource_titleAuthor_leadWord'] = self.api_migrator.trim_white_spaces(record.find('lead_word').text)

        # Title
        titles = []
        if len(record.findall('title')) > 0:
            for title in record.findall('title'):
                titles.append({
                    "title": self.api_migrator.trim_white_spaces(title.text)
                    })

        data['titleAuthorSource_titleAuthor_title'] = titles

        # titleAuthorImprintCollation_titleAuthor_statementOfRespsib
        if record.find('statement_of_responsibility') != None:
            data['titleAuthorSource_titleAuthor_statementOfRespsib'] = self.api_migrator.trim_white_spaces(record.find('statement_of_responsibility').text)

        # titleAuthorImprintCollation_titleAuthor_author
        authors = []
        if len(record.findall('author.name')) > 0:
            for author in record.findall('author.name'):
                if author.find('name') != None:
                    authors.append({
                        "author": self.api_migrator.trim_white_spaces(author.find('name').text),
                        "role": ""
                        })


        if len(authors) > 0:
            if len(record.findall('author.role')) > 0:
                for slot, role in enumerate(record.findall('author.role')):
                    if role.find('term') != None:
                        authors[slot]['role'] = self.api_migrator.trim_white_spaces(role.find('term').text)

        data['titleAuthorSource_titleAuthor_author'] = authors

        # titleAuthorImprintCollation_titleAuthor_illustrator
        illustrators = []

        if len(record.findall('Illustrator')) > 0:
            for illustrator in record.findall('Illustrator'):
                new_illustrator = {
                    "illustrator": "",
                    "role": ""
                }

                if illustrator.find('illustrator.name') != None:
                    if illustrator.find('illustrator.name').find('name') != None:
                        new_illustrator['illustrator'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.name').find('name').text)

                if illustrator.find('illustrator.role') != None:
                    if illustrator.find('illustrator.role').find('term') != None:
                        new_illustrator['role'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.role').find('term').text)

                illustrators.append(new_illustrator)

        data['titleAuthorSource_titleAuthor_illustrator'] = illustrators

        # titleAuthorImprintCollation_titleAuthor_corpAuthor
        if record.find('corporate_author') != None:
            if record.find('corporate_author').find('name') != None:
                data['titleAuthorSource_titleAuthor_corpAuthor'] = self.api_migrator.trim_white_spaces(record.find('corporate_author').find('name').text)

        # titleAuthorImprintCollation_edition_edition
        if record.find('edition') != None:
            data['titleAuthorSource_edition_edition'] = self.api_migrator.trim_white_spaces(record.find('edition').text)


        # titleAuthorImprintCollation_source_source
        sources = []

        for source in record.findall('source.title'):
            if source.find('title') != None:
                sources.append({
                    "sourceTitleArticle":"",
                    "materialType":"",
                    "sourceTitle":self.api_migrator.trim_white_spaces(source.find('title').text),
                    "volume": "",
                    "issue":"",
                    "day":"",
                    "month":"",
                    "year":"",
                    "pagination":"",
                    "notes":""
                    })

        if len(sources) > 0:

            for slot, article in enumerate(record.findall('source.title.article')):
                sources[slot]['sourceTitleArticle'] = self.api_migrator.trim_white_spaces(article.text)

            for slot, material in enumerate(record.findall('source.material_type')):
                sources[slot]['materialType'] = self.api_migrator.trim_white_spaces(material.text)

            for slot, volume in enumerate(record.findall('source.volume')):
                sources[slot]['volume'] = self.api_migrator.trim_white_spaces(volume.text)

            for slot, issue in enumerate(record.findall('source.issue')):
                sources[slot]['issue'] = self.api_migrator.trim_white_spaces(issue.text)

            for slot, day in enumerate(record.findall('source.day')):
                sources[slot]['day'] = self.api_migrator.trim_white_spaces(day.text)

            for slot, month in enumerate(record.findall('source.month')):
                sources[slot]['month'] = self.api_migrator.trim_white_spaces(month.text)
            
            for slot, year in enumerate(record.findall('source.publication_years')):
                sources[slot]['year'] = self.api_migrator.trim_white_spaces(year.text)

            for slot, pagination in enumerate(record.findall('source.pagination')):
                sources[slot]['pagination'] = self.api_migrator.trim_white_spaces(pagination.text)

            for slot, notes in enumerate(record.findall('source.notes')):
                sources[slot]['notes'] = self.api_migrator.trim_white_spaces(notes.text)


        data['titleAuthorSource_source_source'] = sources


        # titleAuthorImprintCollation_illustrations_illustrations 
        illustrations = []

        for illustration in record.findall('illustrations'):
            illustrations.append({
                "term": self.api_migrator.trim_white_spaces(illustration.text)
                })

        data['titleAuthorSource_illustrations_illustrations'] = illustrations


        # titleAuthorImprintCollation_sortYear_sortYear
        if record.find('sort_year') != None:
            data['titleAuthorSource_sortYear_sortYear'] = self.api_migrator.trim_white_spaces(record.find('sort_year').text)


        #titleAuthorImprintCollation_notes_bibliographicalNotes
        notes = []
        if len(record.findall('notes')) > 0:
            for note in record.findall('notes'):
                notes.append({
                    "term": self.api_migrator.trim_white_spaces(note.text)
                    })


        data['titleAuthorSource_notes_bibliographicalNotes'] = notes

        return True

    def get_title_author_fieldset(self, data, record):
        # Article
        if record.find('lead_word') != None:
            data['titleAuthorImprintCollation_titleAuthor_article'] = self.api_migrator.trim_white_spaces(record.find('lead_word').text)

        # Title
        titles = []
        if len(record.findall('title')) > 0:
            for title in record.findall('title'):
                titles.append({
                    "title": self.api_migrator.trim_white_spaces(title.text)
                    })

        data['titleAuthorImprintCollation_titleAuthor_title'] = titles

        # titleAuthorImprintCollation_titleAuthor_statementOfRespsib
        if record.find('statement_of_responsibility') != None:
            data['titleAuthorImprintCollation_titleAuthor_statementOfRespsib'] = self.api_migrator.trim_white_spaces(record.find('statement_of_responsibility').text)

        # titleAuthorImprintCollation_titleAuthor_author
        authors = []
        if len(record.findall('author.name')) > 0:
            for author in record.findall('author.name'):
                if author.find('name') != None:
                    authors.append({
                        "author": self.api_migrator.trim_white_spaces(author.find('name').text),
                        "role": ""
                        })


        if len(authors) > 0:
            if len(record.findall('author.role')) > 0:
                for slot, role in enumerate(record.findall('author.role')):
                    if role.find('term') != None:
                        authors[slot]['role'] = self.api_migrator.trim_white_spaces(role.find('term').text)

        data['titleAuthorImprintCollation_titleAuthor_author'] = authors

        # titleAuthorImprintCollation_titleAuthor_illustrator
        illustrators = []

        if len(record.findall('Illustrator')) > 0:
            for illustrator in record.findall('Illustrator'):
                new_illustrator = {
                    "illustrator": "",
                    "role": ""
                }

                if illustrator.find('illustrator.name') != None:
                    if illustrator.find('illustrator.name').find('name') != None:
                        new_illustrator['illustrator'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.name').find('name').text)

                if illustrator.find('illustrator.role') != None:
                    if illustrator.find('illustrator.role').find('term') != None:
                        new_illustrator['role'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.role').find('term').text)

                illustrators.append(new_illustrator)

        data['titleAuthorImprintCollation_titleAuthor_illustrator'] = illustrators

        # titleAuthorImprintCollation_titleAuthor_corpAuthor
        if record.find('corporate_author') != None:
            if record.find('corporate_author').find('name') != None:
                data['titleAuthorImprintCollation_titleAuthor_corpAuthor'] = self.api_migrator.trim_white_spaces(record.find('corporate_author').find('name').text)

        # titleAuthorImprintCollation_edition_edition
        if record.find('edition') != None:
            data['titleAuthorImprintCollation_edition_edition'] = self.api_migrator.trim_white_spaces(record.find('edition').text)

        # titleAuthorImprintCollation_imprint_place
        places = []
        if len(record.findall('place_of_publication')) > 0:
            for place in record.findall('place_of_publication'):
                places.append({
                    "term": self.api_migrator.trim_white_spaces(place.text)
                    })

        data['titleAuthorImprintCollation_imprint_place'] = places

        # titleAuthorImprintCollation_imprint_publisher
        publishers = []
        if len(record.findall('publisher')) > 0:
            for publisher in record.findall('publisher'):
                if publisher.find('name') != None:
                    publishers.append({
                        "term": self.api_migrator.trim_white_spaces(publisher.find('name').text)
                        })

        data['titleAuthorImprintCollation_imprint_publisher'] = publishers


        # titleAuthorImprintCollation_imprint_year
        if record.find('year_of_publication') != None:
            data['titleAuthorImprintCollation_imprint_year'] = self.api_migrator.trim_white_spaces(record.find('year_of_publication').text)

        # titleAuthorImprintCollation_imprint_placePrinted
        placesprinted = []

        if len(record.findall('print.place')) > 0:
            for placep in record.findall('print.place'):
                if placep.find('term') != None:
                    placesprinted.append({
                        "term": self.api_migrator.trim_white_spaces(placep.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_placePrinted'] = placesprinted

        # titleAuthorImprintCollation_imprint_printer
        printers = []
        if len(record.findall('print.name')) > 0:
            for printer in record.findall('print.name'):
                if printer.find('term') != None:
                    printers.append({
                        "term": self.api_migrator.trim_white_spaces(printer.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_printer'] = printers

        # titleAuthorImprintCollation_sortYear_sortYear
        if record.find('sort_year') != None:
            data['titleAuthorImprintCollation_sortYear_sortYear'] = self.api_migrator.trim_white_spaces(record.find('sort_year').text)

        # titleAuthorImprintCollation_collation_pagination
        if record.find('pagination') != None:
            data['titleAuthorImprintCollation_collation_pagination'] = self.api_migrator.trim_white_spaces(record.find('pagination').text)

        # titleAuthorImprintCollation_collation_illustrations
        if record.find('illustrations') != None:
            data['titleAuthorImprintCollation_collation_illustrations'] = self.api_migrator.trim_white_spaces(record.find('illustrations').text)

        # titleAuthorImprintCollation_collation_dimensions
        if record.find('dimensions') != None:
            data['titleAuthorImprintCollation_collation_dimensions'] = self.api_migrator.trim_white_spaces(record.find('dimensions').text)

        # titleAuthorImprintCollation_collation_accompanyingMaterial
        materials = []
        if len(record.findall('accompanying_material')) > 0:
            for material in record.findall('accompanying_material'):
                materials.append({
                    "term": self.api_migrator.trim_white_spaces(material.text)
                    })

        data['titleAuthorImprintCollation_collation_accompanyingMaterial'] = materials

        return True

    def get_audiovisual_title_author_fieldset(self, data, record):
        # Article
        if record.find('lead_word') != None:
            data['titleAuthorImprintCollation_titleAuthor_leadWord'] = self.api_migrator.trim_white_spaces(record.find('lead_word').text)

        # Title
        titles = []
        if len(record.findall('title')) > 0:
            for title in record.findall('title'):
                titles.append({
                    "title": self.api_migrator.trim_white_spaces(title.text)
                    })

        data['titleAuthorImprintCollation_titleAuthor_title'] = titles

        # titleAuthorImprintCollation_titleAuthor_statementOfRespsib
        if record.find('statement_of_responsibility') != None:
            data['titleAuthorImprintCollation_titleAuthor_statementOfRespsib'] = self.api_migrator.trim_white_spaces(record.find('statement_of_responsibility').text)

        # titleAuthorImprintCollation_titleAuthor_author
        authors = []
        if len(record.findall('author.name')) > 0:
            for author in record.findall('author.name'):
                if author.find('name') != None:
                    authors.append({
                        "author": self.api_migrator.trim_white_spaces(author.find('name').text),
                        "role": ""
                        })


        if len(authors) > 0:
            if len(record.findall('author.role')) > 0:
                for slot, role in enumerate(record.findall('author.role')):
                    if role.find('term') != None:
                        authors[slot]['role'] = self.api_migrator.trim_white_spaces(role.find('term').text)

        data['titleAuthorImprintCollation_titleAuthor_author'] = authors

        # titleAuthorImprintCollation_titleAuthor_illustrator
        illustrators = []

        if len(record.findall('Illustrator')) > 0:
            for illustrator in record.findall('Illustrator'):
                new_illustrator = {
                    "illustrator": "",
                    "role": ""
                }

                if illustrator.find('illustrator.name') != None:
                    if illustrator.find('illustrator.name').find('name') != None:
                        new_illustrator['illustrator'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.name').find('name').text)

                if illustrator.find('illustrator.role') != None:
                    if illustrator.find('illustrator.role').find('term') != None:
                        new_illustrator['role'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.role').find('term').text)

                illustrators.append(new_illustrator)

        data['titleAuthorImprintCollation_titleAuthor_illustrator'] = illustrators

        # titleAuthorImprintCollation_titleAuthor_corpAuthor
        if record.find('corporate_author') != None:
            if record.find('corporate_author').find('name') != None:
                data['titleAuthorImprintCollation_titleAuthor_corpAuthor'] = self.api_migrator.trim_white_spaces(record.find('corporate_author').find('name').text)

        # titleAuthorImprintCollation_edition_edition
        if record.find('edition') != None:
            data['titleAuthorImprintCollation_edition_edition'] = self.api_migrator.trim_white_spaces(record.find('edition').text)

        # titleAuthorImprintCollation_imprint_place
        places = []
        if len(record.findall('place_of_publication')) > 0:
            for place in record.findall('place_of_publication'):
                places.append({
                    "term": self.api_migrator.trim_white_spaces(place.text)
                    })

        data['titleAuthorImprintCollation_imprint_place'] = places

        # titleAuthorImprintCollation_imprint_publisher
        publishers = []
        if len(record.findall('publisher')) > 0:
            for publisher in record.findall('publisher'):
                if publisher.find('name') != None:
                    publishers.append({
                        "term": self.api_migrator.trim_white_spaces(publisher.find('name').text)
                        })

        data['titleAuthorImprintCollation_imprint_publisher'] = publishers


        # titleAuthorImprintCollation_imprint_year
        if record.find('year_of_publication') != None:
            data['titleAuthorImprintCollation_imprint_year'] = self.api_migrator.trim_white_spaces(record.find('year_of_publication').text)

        # titleAuthorImprintCollation_imprint_placePrinted
        placesprinted = []

        if len(record.findall('print.place')) > 0:
            for placep in record.findall('print.place'):
                if placep.find('term') != None:
                    placesprinted.append({
                        "term": self.api_migrator.trim_white_spaces(placep.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_placePrinted'] = placesprinted

        # titleAuthorImprintCollation_imprint_printer
        printers = []
        if len(record.findall('print.name')) > 0:
            for printer in record.findall('print.name'):
                if printer.find('term') != None:
                    printers.append({
                        "term": self.api_migrator.trim_white_spaces(printer.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_printer'] = printers

        # titleAuthorImprintCollation_sortYear_sortYear
        if record.find('sort_year') != None:
            data['titleAuthorImprintCollation_sortYear_sortYear'] = self.api_migrator.trim_white_spaces(record.find('sort_year').text)

        # titleAuthorImprintCollation_collation_pagination
        if record.find('quantity') != None:
            data['titleAuthorImprintCollation_collation_quantity'] = self.api_migrator.trim_white_spaces(record.find('quantity').text)

        # titleAuthorImprintCollation_collation_illustrations
        if record.find('pagination') != None:
            data['titleAuthorImprintCollation_collation_contents'] = self.api_migrator.trim_white_spaces(record.find('pagination').text)

        # titleAuthorImprintCollation_collation_physicalDetails
        physicaldetails = []

        for attr in record.findall('attributes'):
            physicaldetails.append({
                "term": self.api_migrator.trim_white_spaces(attr.text)
                })

        data['titleAuthorImprintCollation_collation_physicalDetails'] = physicaldetails

        # titleAuthorImprintCollation_collation_dimensions
        if record.find('dimensions') != None:
            data['titleAuthorImprintCollation_collation_dimensions'] = self.api_migrator.trim_white_spaces(record.find('dimensions').text)

        # titleAuthorImprintCollation_collation_accompanyingMaterial
        materials = []
        if len(record.findall('accompanying_material')) > 0:
            for material in record.findall('accompanying_material'):
                materials.append({
                    "term": self.api_migrator.trim_white_spaces(material.text)
                    })

        data['titleAuthorImprintCollation_collation_accompanyingMaterial'] = materials

        return True

    def get_title_author_fieldset(self, data, record):
        # Article
        if record.find('lead_word') != None:
            data['titleAuthorImprintCollation_titleAuthor_article'] = self.api_migrator.trim_white_spaces(record.find('lead_word').text)

        # Title
        titles = []
        if len(record.findall('title')) > 0:
            for title in record.findall('title'):
                titles.append({
                    "title": self.api_migrator.trim_white_spaces(title.text)
                    })

        data['titleAuthorImprintCollation_titleAuthor_title'] = titles

        # titleAuthorImprintCollation_titleAuthor_statementOfRespsib
        if record.find('statement_of_responsibility') != None:
            data['titleAuthorImprintCollation_titleAuthor_statementOfRespsib'] = self.api_migrator.trim_white_spaces(record.find('statement_of_responsibility').text)

        # titleAuthorImprintCollation_titleAuthor_author
        authors = []
        if len(record.findall('author.name')) > 0:
            for author in record.findall('author.name'):
                if author.find('name') != None:
                    authors.append({
                        "author": self.api_migrator.trim_white_spaces(author.find('name').text),
                        "role": ""
                        })


        if len(authors) > 0:
            if len(record.findall('author.role')) > 0:
                for slot, role in enumerate(record.findall('author.role')):
                    if role.find('term') != None:
                        authors[slot]['role'] = self.api_migrator.trim_white_spaces(role.find('term').text)

        data['titleAuthorImprintCollation_titleAuthor_author'] = authors

        # titleAuthorImprintCollation_titleAuthor_illustrator
        illustrators = []

        if len(record.findall('Illustrator')) > 0:
            for illustrator in record.findall('Illustrator'):
                new_illustrator = {
                    "illustrator": "",
                    "role": ""
                }

                if illustrator.find('illustrator.name') != None:
                    if illustrator.find('illustrator.name').find('name') != None:
                        new_illustrator['illustrator'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.name').find('name').text)

                if illustrator.find('illustrator.role') != None:
                    if illustrator.find('illustrator.role').find('term') != None:
                        new_illustrator['role'] = self.api_migrator.trim_white_spaces(illustrator.find('illustrator.role').find('term').text)

                illustrators.append(new_illustrator)

        data['titleAuthorImprintCollation_titleAuthor_illustrator'] = illustrators

        # titleAuthorImprintCollation_titleAuthor_corpAuthor
        if record.find('corporate_author') != None:
            if record.find('corporate_author').find('name') != None:
                data['titleAuthorImprintCollation_titleAuthor_corpAuthor'] = self.api_migrator.trim_white_spaces(record.find('corporate_author').find('name').text)

        # titleAuthorImprintCollation_edition_edition
        if record.find('edition') != None:
            data['titleAuthorImprintCollation_edition_edition'] = self.api_migrator.trim_white_spaces(record.find('edition').text)

        # titleAuthorImprintCollation_imprint_place
        places = []
        if len(record.findall('place_of_publication')) > 0:
            for place in record.findall('place_of_publication'):
                places.append({
                    "term": self.api_migrator.trim_white_spaces(place.text)
                    })

        data['titleAuthorImprintCollation_imprint_place'] = places

        # titleAuthorImprintCollation_imprint_publisher
        publishers = []
        if len(record.findall('publisher')) > 0:
            for publisher in record.findall('publisher'):
                if publisher.find('name') != None:
                    publishers.append({
                        "term": self.api_migrator.trim_white_spaces(publisher.find('name').text)
                        })

        data['titleAuthorImprintCollation_imprint_publisher'] = publishers


        # titleAuthorImprintCollation_imprint_year
        if record.find('year_of_publication') != None:
            data['titleAuthorImprintCollation_imprint_year'] = self.api_migrator.trim_white_spaces(record.find('year_of_publication').text)

        # titleAuthorImprintCollation_imprint_placePrinted
        placesprinted = []

        if len(record.findall('print.place')) > 0:
            for placep in record.findall('print.place'):
                if placep.find('term') != None:
                    placesprinted.append({
                        "term": self.api_migrator.trim_white_spaces(placep.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_placePrinted'] = placesprinted

        # titleAuthorImprintCollation_imprint_printer
        printers = []
        if len(record.findall('print.name')) > 0:
            for printer in record.findall('print.name'):
                if printer.find('term') != None:
                    printers.append({
                        "term": self.api_migrator.trim_white_spaces(printer.find('term').text)
                        })

        data['titleAuthorImprintCollation_imprint_printer'] = printers

        # titleAuthorImprintCollation_sortYear_sortYear
        if record.find('sort_year') != None:
            data['titleAuthorImprintCollation_sortYear_sortYear'] = self.api_migrator.trim_white_spaces(record.find('sort_year').text)

        # titleAuthorImprintCollation_collation_pagination
        if record.find('pagination') != None:
            data['titleAuthorImprintCollation_collation_pagination'] = self.api_migrator.trim_white_spaces(record.find('pagination').text)

        # titleAuthorImprintCollation_collation_illustrations
        if record.find('illustrations') != None:
            data['titleAuthorImprintCollation_collation_illustrations'] = self.api_migrator.trim_white_spaces(record.find('illustrations').text)

        # titleAuthorImprintCollation_collation_dimensions
        if record.find('dimensions') != None:
            data['titleAuthorImprintCollation_collation_dimensions'] = self.api_migrator.trim_white_spaces(record.find('dimensions').text)

        # titleAuthorImprintCollation_collation_accompanyingMaterial
        materials = []
        if len(record.findall('accompanying_material')) > 0:
            for material in record.findall('accompanying_material'):
                materials.append({
                    "term": self.api_migrator.trim_white_spaces(material.text)
                    })

        data['titleAuthorImprintCollation_collation_accompanyingMaterial'] = materials

        return True

    def get_audiovisual_series_fieldset(self, data, record):
        # seriesNotesISBN_series_series
        series = []

        if len(record.findall('series.title')) > 0:
            for serie in record.findall('series.title'):
                new_serie = {
                    "seriesArticle":"",
                    "series":"",
                    "seriesNo":"",
                    "ISSNSeries":""
                }

                if serie.find('lead_word') != None:
                    new_serie['seriesArticle'] = self.api_migrator.trim_white_spaces(serie.find('lead_word').text)

                if serie.find('series') != None:
                    new_serie['series'] = self.api_migrator.trim_white_spaces(serie.find('series').text)

                if serie.find('issn') != None:
                    new_serie['ISSNSeries'] = self.api_migrator.trim_white_spaces(serie.find('issn').text)

                series.append(new_serie)


        if len(series) > 0:
            if len(record.findall('series.number')) > 0:
                for slot, number in enumerate(record.findall('series.number')):
                    series[slot]['seriesNo'] = self.api_migrator.trim_white_spaces(number.text)

        data['seriesNotesISBN_series_series'] = series

        # seriesNotesISBN_notes_bibliographicalNotes
        notes = []
        if len(record.findall('notes')) > 0:
            for note in record.findall('notes'):
                notes.append({
                    "term": self.api_migrator.trim_white_spaces(note.text)
                    })


        data['seriesNotesISBN_notes_bibliographicalNotes'] = notes

        # seriesNotesISBN_notes_production
        productions = []
        for prod in record.findall('production'):
            productions.append({
                "term":self.api_migrator.trim_white_spaces(prod.text)
                })
        data['seriesNotesISBN_notes_production'] = productions

        # seriesNotesISBN_notes_broadcast
        broadcasts = []

        for broadcast in record.findall('broadcast'):
            broadcasts.append({
                "term": self.api_migrator.trim_white_spaces(broadcast.text)
                }) 

        data['seriesNotesISBN_notes_broadcast'] = broadcasts

        # seriesNotesISBN_notes_broadcastingCompany
        broad_companies = []

        for comp in record.findall('broadcasting_company'):
            if comp.find('term') != None:
                broad_companies.append({
                    "term": self.api_migrator.trim_white_spaces(comp.find('term').text)
                    })

        data['seriesNotesISBN_notes_broadcastingCompany'] = broad_companies

        # seriesNotesISBN_notes_productionCompany
        production_companies = []

        for prodc in record.findall('production_company'):
            if prodc.find('term') != None:
                production_companies.append({
                    "term": self.api_migrator.trim_white_spaces(prodc.find('term').text)
                    })

        data['seriesNotesISBN_notes_broadcastingCompany'] = production_companies
        
        # seriesNotesISBN_ISBN_ISBN
        isbns = []

        if len(record.findall('isbn')) > 0:
            for isbn_number in record.findall('isbn'):
                isbns.append({
                    "ISBN": self.api_migrator.trim_white_spaces(isbn_number.text),
                    "price": "",
                    "bindingMethod": ""
                    })

        if len(isbns) > 0:
            for slot, price in enumerate(record.findall('price')):
                isbns[slot]['price'] = self.api_migrator.trim_white_spaces(price.text)


            for slot, method in enumerate(record.findall('binding_method')):
                isbns[slot]['bindingMethod'] = self.api_migrator.trim_white_spaces(method.text)

        data['seriesNotesISBN_ISBN_ISBN'] = isbns

        # seriesNotesISBN_conference_conference

        return True

    def get_serials_series_fieldset(self, data, record):
        # seriesNotesISSNShelfmark_series_series
        series = []

        if len(record.findall('series.title')) > 0:
            for serie in record.findall('series.title'):
                new_serie = {
                    "seriesArticle":"",
                    "series":"",
                    "seriesNo":"",
                    "ISSNSeries":""
                }

                if serie.find('lead_word') != None:
                    new_serie['seriesArticle'] = self.api_migrator.trim_white_spaces(serie.find('lead_word').text)

                if serie.find('series') != None:
                    new_serie['series'] = self.api_migrator.trim_white_spaces(serie.find('series').text)

                if serie.find('issn') != None:
                    new_serie['ISSNSeries'] = self.api_migrator.trim_white_spaces(serie.find('issn').text)

                series.append(new_serie)


        if len(series) > 0:
            if len(record.findall('series.number')) > 0:
                for slot, number in enumerate(record.findall('series.number')):
                    series[slot]['seriesNo'] = self.api_migrator.trim_white_spaces(number.text)

        data['seriesNotesISSNShelfmark_series_series'] = series

        # seriesNotesISSNShelfmark_notes_holding
        holdings = []

        for holding in record.findall('holding'):
            holdings.append({
                "term": self.api_migrator.trim_white_spaces(holding.text)
                })

        data['seriesNotesISSNShelfmark_notes_holding'] = holdings

        # seriesNotesISSNShelfmark_notes_bibliographicalNotes
        notes = []
        if len(record.findall('notes')) > 0:
            for note in record.findall('notes'):
                notes.append({
                    "term": self.api_migrator.trim_white_spaces(note.text)
                    })


        data['seriesNotesISSNShelfmark_notes_bibliographicalNotes'] = notes

        
        # seriesNotesISSNShelfmark_ISSN_ISSN
        issns = []

        if len(record.findall('ISSN')) > 0:
            for issn_number in record.findall('ISSN'):
                issns.append({
                    "ISSN": self.api_migrator.trim_white_spaces(issn_number.text),
                    })

        data['seriesNotesISSNShelfmark_ISSN_ISSN'] = issns

        # seriesNotesISSNShelfmark_continuation_continuedFrom
        continuedfrom = []

        for continued in record.findall('serial.continued.from.recordno'):
            if continued.get('linkdata') != None:
                continuedfrom.append({
                    "term": self.api_migrator.trim_white_spaces(continued.get('linkdata'))
                    })

        data['seriesNotesISSNShelfmark_continuation_continuedFrom'] = continuedfrom


        # seriesNotesISSNShelfmark_continuation_continuedAs
        continuedAs = []

        for continuedas in record.findall('serial.continued.from.recordno'):
            if continuedas.get('linkdata') != None:
                continuedAs.append({
                    "term": self.api_migrator.trim_white_spaces(continuedas.get('linkdata'))
                    })

        data['seriesNotesISSNShelfmark_continuation_continuedAs'] = continuedAs

        # seriesNotesISBN_conference_conference

        return True

    def get_series_fieldset(self, data, record):

        # seriesNotesISBN_series_series
        series = []

        if len(record.findall('series.title')) > 0:
            for serie in record.findall('series.title'):
                new_serie = {
                    "seriesArticle":"",
                    "series":"",
                    "seriesNo":"",
                    "ISSNSeries":""
                }

                if serie.find('lead_word') != None:
                    new_serie['seriesArticle'] = self.api_migrator.trim_white_spaces(serie.find('lead_word').text)

                if serie.find('series') != None:
                    new_serie['series'] = self.api_migrator.trim_white_spaces(serie.find('series').text)

                if serie.find('issn') != None:
                    new_serie['ISSNSeries'] = self.api_migrator.trim_white_spaces(serie.find('issn').text)

                series.append(new_serie)


        if len(series) > 0:
            if len(record.findall('series.number')) > 0:
                for slot, number in enumerate(record.findall('series.number')):
                    series[slot]['seriesNo'] = self.api_migrator.trim_white_spaces(number.text)

        data['seriesNotesISBN_series_series'] = series

        # seriesNotesISBN_series_subseries
        subseries = []

        if len(record.findall('subseries.title')) > 0:
            for subserie in record.findall('subseries.title'):
                new_serie = {
                    "subseriesArticle":"",
                    "subseries":"",
                    "subseriesNo":"",
                    "ISSNSubseries":""
                }

                if subserie.find('lead_word') != None:
                    new_serie['subseriesArticle'] = self.api_migrator.trim_white_spaces(subserie.find('lead_word').text)

                if subserie.find('series') != None:
                    new_serie['subseries'] = self.api_migrator.trim_white_spaces(subserie.find('series').text)

                if subserie.find('issn') != None:
                    new_serie['ISSNSubseries'] = self.api_migrator.trim_white_spaces(subserie.find('issn').text)


                subseries.append(new_serie)


        if len(subseries) > 0:
            if len(record.findall('subseries.number')) > 0:
                for slot, number in enumerate(record.findall('subseries.number')):
                    subseries[slot]['subseriesNo'] = self.api_migrator.trim_white_spaces(number.text)

        data['seriesNotesISBN_series_subseries'] = subseries

        # seriesNotesISBN_notes_bibliographicalNotes
        notes = []
        if len(record.findall('notes')) > 0:
            for note in record.findall('notes'):
                notes.append({
                    "term": self.api_migrator.trim_white_spaces(note.text)
                    })


        data['seriesNotesISBN_notes_bibliographicalNotes'] = notes
        
        # seriesNotesISBN_ISBN_ISBN
        isbns = []

        if len(record.findall('isbn')) > 0:
            for isbn_number in record.findall('isbn'):
                isbns.append({
                    "ISBN": self.api_migrator.trim_white_spaces(isbn_number.text),
                    "price": "",
                    "bindingMethod": ""
                    })

        if len(isbns) > 0:
            for slot, price in enumerate(record.findall('price')):
                isbns[slot]['price'] = self.api_migrator.trim_white_spaces(price.text)


            for slot, method in enumerate(record.findall('binding_method')):
                isbns[slot]['bindingMethod'] = self.api_migrator.trim_white_spaces(method.text)

        data['seriesNotesISBN_ISBN_ISBN'] = isbns

        # seriesNotesISBN_ISBN_ISSN
        issns = []

        for issn in record.findall('ISSN'):
            issns.append({
                "ISSN": self.api_migrator.trim_white_spaces(issn.text)
                })

        data['seriesNotesISBN_ISBN_ISSN'] = issns

        # seriesNotesISBN_conference_conference

        return True

    def get_abstract_and_subject_terms_fieldset(self, data, record):

        #'abstractAndSubjectTerms_materialType 
        materials = []

        for material in record.findall('material_type'):
            if material.find('term') != None:
                materials.append({
                    "term": self.api_migrator.trim_white_spaces(material.find('term').text)
                    })

        data['abstractAndSubjectTerms_materialType'] = materials


        #'abstractAndSubjectTerms_biblForm
        bibls = []
        data['abstractAndSubjectTerms_biblForm'] = bibls
        
        #'abstractAndSubjectTerms_language 
        languages = []

        for language in record.findall('language_code'):
            if language.find('term') != None:
                languages.append({
                    "term": self.api_migrator.trim_white_spaces(language.find('term').text)
                    })

        data['abstractAndSubjectTerms_language'] = languages
        
        #'abstractAndSubjectTerms_level
        if record.find('level') != None:
            data['abstractAndSubjectTerms_level'] = self.api_migrator.trim_white_spaces(record.find('level').text)
        
        #'abstractAndSubjectTerms_notes 
        notes = []

        for comment in record.findall('comments'):
            notes.append({
                "note": self.api_migrator.trim_white_spaces(comment.text)
                })

        data['abstractAndSubjectTerms_notes'] = notes
        
        #'abstractAndSubjectTerms_classNumber

        classnumbers = []

        for classnumber in record.findall('class_number'):
            if classnumber.find('term') != None:
                classnumbers.append({
                    "term": self.api_migrator.trim_white_spaces(classnumber.find('term').text)
                    })

        data['abstractAndSubjectTerms_classNumber'] = classnumbers
        
        #'abstractAndSubjectTerms_subjectTerm 
        subjectterms = []

        for keyword_type in record.findall('keyword.type'):
            if keyword_type.find('text') != None:
                subjectterms.append({
                    "subjectTermType": self.api_migrator.trim_white_spaces(keyword_type.find('text')),
                    "subjectType": "",
                    "properName": ""
                    })

        for slot, proper_name in enumerate(record.findall('keyword.proper_name')):
            if proper_name.find('term') != None:
                subjectterms[slot]['properName'] = self.api_migrator.trim_white_spaces(proper_name.find('term').text)

        for slot, contents in enumerate(record.findall('keyword.contents')):
            if contents.find('term') != None:
                subjectterms[slot]['subjectType'] = self.api_migrator.trim_white_spaces(contents.find('term').text)

        data['abstractAndSubjectTerms_subjectTerm'] = subjectterms
        
        #'abstractAndSubjectTerms_personKeywordType
        persons = []

        for person_keyword in record.findall('person.keyword.type'):
            if person_keyword.find('text') != None:
                persons.append({
                    "personKeywordType": self.api_migrator.trim_white_spaces(person_keyword.find('text').text),
                    "name": "",
                    "role": ""
                    })

        if len(persons) > 0:
            for slot, role in enumerate(record.findall('person.keyword.role')):
                if role.find('term') != None:
                    persons[slot]['role'] = self.api_migrator.trim_white_spaces(role.find('term').text)

            for slot, name in enumerate(record.findall('person.keyword.name')):
                if name.find('term') != None:
                    persons[slot]['name'] = self.api_migrator.trim_white_spaces(name.find('term').text)

        data['abstractAndSubjectTerms_personKeywordType'] = persons
        
        #'abstractAndSubjectTerms_geographicalKeyword 
        geographicalkeywords = []

        for geo in record.findall('geographical_keyword'):
            if geo.find('term') != None:
                geographicalkeywords.append({
                    "term": self.api_migrator.trim_white_spaces(geo.find('term').text)
                    })

        data['abstractAndSubjectTerms_geographicalKeyword'] = geographicalkeywords

        #'abstractAndSubjectTerms_period
        periods = []

        for period in record.findall('timeperiod'):
            if period.find('term') != None:
                periods.append({
                    "term": self.api_migrator.trim_white_spaces(period.find('term').text)
                    })

        data['abstractAndSubjectTerms_period'] = periods


        #'abstractAndSubjectTerms_startDate 
        if record.find('start_date') != None:
            data['abstractAndSubjectTerms_startDate'] = self.api_migrator.trim_white_spaces(record.find('start_date').text)

        #'abstractAndSubjectTerms_endDate
        if record.find('end_date') != None:
            data['abstractAndSubjectTerms_endDate'] = self.api_migrator.trim_white_spaces(record.find('end_date').text)
        
        #'abstractAndSubjectTerms_digitalReferences_reference 
        digital_references = []
        for ref in record.findall('digital_reference'):
            digital_references.append({
                "reference": self.api_migrator.trim_white_spaces(ref.text)
                })

        data['abstractAndSubjectTerms_digitalReferences_reference'] = digital_references
        
        #'abstractAndSubjectTerms_abstract_abstract
        abstracts = []

        for abstract in record.findall('abstract'):
            abstracts.append({
                "term": self.api_migrator.trim_white_spaces(abstract.text)
                })

        data['abstractAndSubjectTerms_abstract_abstract'] = abstracts

        return True

    ##
    ## Get exhibitions fieldset
    ##
    def get_exhibitions_fieldset(self, data, record):

        #'exhibitionsAuctionsCollections_exhibition':[], 
        exhibitions = []

        for exhibition in record.findall('exhibition'):
            new_exhibition = {
            "exhibitionName": "",
            "date": "",
            "to": "",
            "organiser": "",
            "venue": "",
            "place": "",
            "notes": "",
            "priref": ""
            }

            if exhibition.find('exhibition') != None:
                ## Title 
                if exhibition.find('exhibition').find('title') != None:
                    new_exhibition['exhibitionName'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition').find('title').text)

                ### Priref
                if exhibition.find('exhibition').get('linkref') != None:
                    new_exhibition['priref'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition').get('linkref'))

            # Date start
            if exhibition.find('exhibition.date.start') != None:
                new_exhibition['date'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition.date.start').text)

            # Date end
            if exhibition.find('exhibition.date.end') != None:
                new_exhibition['to'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition.date.end').text)

            # Organiser
            if exhibition.find('exhibition.organiser') != None:
                new_exhibition['organiser'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition.organiser').text)

            # Venue
            if exhibition.find('exhibition.venue') != None:
                new_exhibition['venue'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition.venue').text)

            # Place
            if exhibition.find('exhibition.place') != None:
                new_exhibition['place'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition.place').text)

            # Notes
            if exhibition.find('exhibition.notes') != None:
                new_exhibition['notes'] = self.api_migrator.trim_white_spaces(exhibition.find('exhibition.notes').text)

            # Add to exhibitions
            exhibitions.append(new_exhibition)

        data['exhibitionsAuctionsCollections_exhibition'] = exhibitions

        #'exhibitionsAuctionsCollections_auction':[],
        auctions = []

        for auction in record.findall('auction.name'):
            new_auction = {
            "auctionName": "",
            "auctioneer": "",
            "date": "",
            "to": "",
            "place":"",
            "location": "",
            "collector": "",
            "commissairPriseur": "",
            "auctionNumber": "",
            "notes": ""
            }

            if auction.find('auction') != None:
                new_auction['auctionName'] = self.api_migrator.trim_white_spaces(auction.find('auction').text)

            if auction.find('auctioneer') != None:
                new_auction['auctioneer'] = self.api_migrator.trim_white_spaces(auction.find('auctioneer').text)

            if auction.find('date_early') != None:
                new_auction['date'] = self.api_migrator.trim_white_spaces(auction.find('date_early').text)

            if auction.find('date_late') != None:
                new_auction['to'] = self.api_migrator.trim_white_spaces(auction.find('date_late').text)

            if auction.find('place') != None:
                new_auction['place'] = self.api_migrator.trim_white_spaces(auction.find('place').text)

            if auction.find('location') != None:
                new_auction['location'] = self.api_migrator.trim_white_spaces(auction.find('location').text)

            if auction.find('collector') != None:
                new_auction['collector'] = self.api_migrator.trim_white_spaces(auction.find('collector').text)

            if auction.find('commissair-priseur') != None:
                new_auction['commissairPriseur'] = self.api_migrator.trim_white_spaces(auction.find('commissair-priseur').text)

            if auction.find('auction_number') != None:
                new_auction['auctionNumber'] = self.api_migrator.trim_white_spaces(auction.find('auction_number').text)

            if auction.find('auction') != None:
                new_auction['notes'] = self.api_migrator.trim_white_spaces(auction.find('auction').text)

            auctions.append(new_auction)

        if len(auctions) > 0:
            for slot, auction_note in enumerate(record.findall('auction.notes')):
                auctions[slot]['notes'] = self.api_migrator.trim_white_spaces(auction_note.text)
        
        data['exhibitionsAuctionsCollections_auction'] = auctions

        #'exhibitionsAuctionsCollections_collection':[]
        collections = []

        for collection in record.findall('collection.notes'):
            collections.append({
                "collectionName":"",
                "collector":"",
                "organisation": "",
                "date": "",
                "place": "",
                "notes": self.api_migrator.trim_white_spaces(collection.text)
                })

        data['exhibitionsAuctionsCollections_collection'] = collections

        return True

    def get_reproductions_fieldset(self, object_data, first_record):
        # reproductions_reproduction
        """ class IReproduction(Interface):
            reference = schema.TextLine(title=_(u'Reference'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)
            format = schema.TextLine(title=_(u'Format'), required=False)
            date = schema.TextLine(title=_(u'Date'), required=False)
            identifierURL = schema.TextLine(title=_(u'Identifier (URL)'), required=False)
            notes = schema.TextLine(title=_(u'Notes'), required=False)"""

        reproductions = [] 

        if len(first_record.findall('reproduction')) > 0:
            for reproduction in first_record.findall('reproduction'):
                if reproduction.find('reproduction.reference') != None:
                
                    new_rep = {
                        "reference": "",
                        "type": "",
                        "format": "",
                        "date": "",
                        "identifierURL": "",
                        "notes": ""
                    }

                    # reference
                    if reproduction.find('reproduction.reference').find('reference_number') != None:
                        new_rep['reference'] = self.api_migrator.trim_white_spaces(reproduction.find('reproduction.reference').find('reference_number').text)

                    # type
                    if reproduction.find('reproduction.reference').find('reproduction_type') != None:
                        new_rep['type'] = self.api_migrator.trim_white_spaces(reproduction.find('reproduction.reference').find('reproduction_type').text)

                    # format
                    if reproduction.find('reproduction.reference').find('format') != None:
                        new_rep['format'] = self.api_migrator.trim_white_spaces(reproduction.find('reproduction.reference').find('format').text)

                    # date
                    if reproduction.find('reproduction.reference').find('production_date') != None:
                        new_rep['date'] = self.api_migrator.trim_white_spaces(reproduction.find('reproduction.reference').find('production_date').text)

                    # identifierURL
                    if reproduction.find('reproduction.notes') != None:
                        new_rep['notes'] = self.api_migrator.trim_white_spaces(reproduction.find('reproduction.notes').text)

                    # notes
                    if reproduction.find('reproduction.identifier_URL') != None:
                        new_rep['identifierURL'] = self.api_migrator.trim_white_spaces(reproduction.find('reproduction.identifier_URL').text)

                    reproductions.append(new_rep)

        object_data["reproductions_reproduction"] = reproductions

    def get_relations_fieldset(self, data, record):

        #'relations_volume':"", 

        if record.find('volume') != None:
            data['relations_volume'] = self.api_migrator.trim_white_spaces(record.find('volume').text)

        #'relations_analyticalCataloguing_recordNo':"",

        #'relations_analyticalCataloguing_volume':"", 

        #'relations_analyticalCataloguing_title':"", 

        #'relations_analyticalCataloguing_partOf':[],

        #'relations_analyticalCataloguing_consistsOf':[], 

        #'relations_museumObjects':[]

        objects = []
        for obj in record.findall('object.object_number'):
            new_obj = {
            "objectNo": "",
            "objectName":"",
            "title":"",
            "maker":""
            }

            if obj.find('object_number') != None:
                new_obj['objectNo'] = self.api_migrator.trim_white_spaces(obj.find('object_number').text)

            if obj.find('object_name') != None:
                new_obj['objectName'] = self.api_migrator.trim_white_spaces(obj.find('object_name').text)

            if obj.find('title') != None:
                new_obj['title'] = self.api_migrator.trim_white_spaces(obj.find('title').text)

            if obj.find('creator') != None:
                new_obj['maker'] = self.api_migrator.trim_white_spaces(obj.find('creator').text)

            objects.append(new_obj)

        data['relations_museumObjects'] = objects

        return True


    def get_free_fields_fieldset(self, data, record):

        # free_fields
        """class IFreeFields(Interface):
            date = schema.TextLine(title=_(u'Date'), required=False)
            type = schema.TextLine(title=_(u'Type'), required=False)
            confidential = schema.TextLine(title=_(u'Confidential'), required=False)
            content = schema.TextLine(title=_(u'Content'), required=False)"""

        free_fields = []

        if len(record.findall('free_field.type')) > 0:
            for free_field in record.findall('free_field.type'):
                free_fields.append({
                    "date": "",
                    "type": self.api_migrator.trim_white_spaces(free_field.text),
                    "confidential": "",
                    "contents": "",
                })

        if len(free_fields) > 0:
            # date
            if len(record.findall('free_field.date')) > 0:
                for slot, free_field_date in enumerate(record.findall('free_field.date')):
                    free_fields[slot]["date"] = self.api_migrator.trim_white_spaces(free_field_date.text)

            # confidential
            if len(record.findall('free_field.confidential')) > 0:
                for slot, free_field_confidential in enumerate(record.findall('free_field.confidential')):
                    free_fields[slot]["confidential"] = self.api_migrator.trim_white_spaces(free_field_confidential.text)

            # content
            if len(record.findall('free_field.content')) > 0:
                for slot, free_field_content in enumerate(record.findall('free_field.content')):
                    free_fields[slot]["contents"] = self.api_migrator.trim_white_spaces(free_field_content.text)


        data['freeFieldsAndNumbers_freeFields'] = free_fields

        #'freeFieldsAndNumbers_otherNumber':[],
        othernumbers = []

        for other_type in record.findall('old_number_type'):
            othernumbers.append({
                "type": self.api_migrator.trim_white_spaces(other_type.text),
                "contents": ""
                })

        if len(othernumbers) > 0:
            for slot, content in enumerate(record.findall('old_number_contents')):
                othernumbers[slot]['contents'] = self.api_migrator.trim_white_spaces(content.text)

        data['freeFieldsAndNumbers_otherNumber'] = othernumbers

        #'freeFieldsAndNumbers_PPN':"",
        if record.find('PPN') != None:
            data['freeFieldsAndNumbers_PPN'] = self.api_migrator.trim_white_spaces(record.find('PPN').text)

        return True

    def get_copies_fieldset(self, data, record):

        # 'copiesAndShelfMarks_defaultShelfMark':"", 
        if record.find('shelf_mark') != None:
            data['copiesAndShelfMarks_defaultShelfMark'] = self.api_migrator.trim_white_spaces(record.find('shelf_mark').text)

        # 'copiesAndShelfMarks_copyDetails':[]
        copies = []

        for copy in record.findall('copy.number'):
            new_copy = {
                "copyNumber":"",
                "shelfMark": "",
                "availability":"",
                "loanCategory":"",
                "site":"",
                "locationNotes":""
            }

            if copy.find('copy_number') != None:
                new_copy['copyNumber'] = self.api_migrator.trim_white_spaces(copy.find('copy_number').text)

            if copy.find('shelfmark') != None:
                new_copy['shelfMark'] = self.api_migrator.trim_white_spaces(copy.find('shelfmark').text)

            if copy.find('loan_status') != None:
                if copy.find('loan_status').find('text') != None:
                    new_copy['availability'] = self.api_migrator.trim_white_spaces(copy.find('loan_status').find('text').text)

            if copy.find('location.note') != None:
                new_copy['locationNotes'] = self.api_migrator.trim_white_spaces(copy.find('location.note'))

            copies.append(new_copy)

        if len(copies) > 0:
            for slot, loan_cat in enumerate(record.findall('loan_category')):
                if loan_cat.find('term') != None:
                    copies[slot]['loanCategory'] = self.api_migrator.trim_white_spaces(loan_cat.find('term').text)

            for slot, site in enumerate(record.findall('site')):
                if site.find('term') != None:
                    copies[slot]['site'] = self.api_migrator.trim_white_spaces(site.find('term').text)

        data['copiesAndShelfMarks_copyDetails'] = copies

        return True

    def create_article_dirty_id(self, data):
        if data["priref"] != "":
            dirty_id = "%s" %(data['priref'])

        title = ""
        if len(data['titleAuthorSource_titleAuthor_title']) > 0:
            title = data['titleAuthorSource_titleAuthor_title'][0]['title']

        if title != "":
            dirty_id = "%s %s" %(dirty_id, title)

        data['dirty_id'] = dirty_id
        return dirty_id

    def create_resource_dirty_id(self, data):
        if data["priref"] != "":
            dirty_id = "%s" %(data['priref'])

        title = ""
        if len(data['resourceDublinCore_title']) > 0:
            title = data['resourceDublinCore_title'][0]['title']

        if title != "":
            dirty_id = "%s %s" %(dirty_id, title)

        data['dirty_id'] = dirty_id
        return dirty_id

    def create_dirty_id(self, data):
        if data["priref"] != "":
            dirty_id = "%s" %(data['priref'])

        title = ""
        if len(data['titleAuthorImprintCollation_titleAuthor_title']) > 0:
            title = data['titleAuthorImprintCollation_titleAuthor_title'][0]['title']

        if title != "":
            dirty_id = "%s %s" %(dirty_id, title)

        data['dirty_id'] = dirty_id
        return dirty_id

    def get_audiovisual(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",
            'titleAuthorImprintCollation_titleAuthor_leadWord':'',
            'titleAuthorImprintCollation_titleAuthor_title':[],
            'titleAuthorImprintCollation_titleAuthor_statementOfRespsib':'',
            'titleAuthorImprintCollation_titleAuthor_author':[],
            'titleAuthorImprintCollation_titleAuthor_illustrator':[],
            'titleAuthorImprintCollation_titleAuthor_corpAuthor':'',
            'titleAuthorImprintCollation_edition_edition':'',
            'titleAuthorImprintCollation_imprint_place':[], 
            'titleAuthorImprintCollation_imprint_publisher':[],
            'titleAuthorImprintCollation_imprint_year':"", 
            'titleAuthorImprintCollation_imprint_placePrinted':[],
            'titleAuthorImprintCollation_imprint_printer':[], 
            'titleAuthorImprintCollation_sortYear_sortYear':'',
            'titleAuthorImprintCollation_collation_quantity':'', 
            'titleAuthorImprintCollation_collation_contents':'',
            'titleAuthorImprintCollation_collation_physicalDetails':[],
            'titleAuthorImprintCollation_collation_dimensions':'', 
            'titleAuthorImprintCollation_collation_accompanyingMaterial':[],
            
            # Series
            'seriesNotesISBN_series_series':"", 
            'seriesNotesISBN_notes_bibliographicalNotes':"",
            'seriesNotesISBN_notes_production':[],
            'seriesNotesISBN_notes_broadcast':[],
            'seriesNotesISBN_notes_broadcastingCompany':[],
            'seriesNotesISBN_notes_productionCompany':[],
            'seriesNotesISBN_ISBN_ISBN':"",
            'seriesNotesISBN_conference_conference':"",

            # Abstract and subject terms
            'abstractAndSubjectTerms_materialType':[], 
            'abstractAndSubjectTerms_biblForm':[],
            'abstractAndSubjectTerms_language':[], 
            'abstractAndSubjectTerms_level':"",
            'abstractAndSubjectTerms_notes':[], 
            'abstractAndSubjectTerms_classNumber':[],
            'abstractAndSubjectTerms_subjectTerm':[], 
            'abstractAndSubjectTerms_personKeywordType':[],
            'abstractAndSubjectTerms_geographicalKeyword':[], 
            'abstractAndSubjectTerms_period':[],
            'abstractAndSubjectTerms_startDate':"", 
            'abstractAndSubjectTerms_endDate':"",
            'abstractAndSubjectTerms_digitalReferences_reference':[], 
            'abstractAndSubjectTerms_abstract_abstract':[],

            # Reproductions
            "reproductions_reproduction": [],

            # Exhibitions, auctions, collections
            'exhibitionsAuctionsCollections_exhibition':[], 
            'exhibitionsAuctionsCollections_auction':[],
            'exhibitionsAuctionsCollections_collection':[],

            # Relations
            'relations_volume':"", 
            'relations_analyticalCataloguing_recordNo':"",
            'relations_analyticalCataloguing_volume':"", 
            'relations_analyticalCataloguing_title':"", 
            'relations_analyticalCataloguing_partOf':[],
            'relations_analyticalCataloguing_consistsOf':[], 
            'relations_museumObjects':[],

            # Free fields
            'freeFieldsAndNumbers_freeFields':[], 
            'freeFieldsAndNumbers_otherNumber':[],
            'freeFieldsAndNumbers_PPN':"",

            # Copies
            'copiesAndShelfMarks_defaultShelfMark':"", 
            'copiesAndShelfMarks_copyDetails':[]
        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_audiovisual_title_author_fieldset(data, record)
        except:
            pass

        # Series
        try:
            self.get_audiovisual_series_fieldset(data, record)
        except:
            pass

        # Abstract
        try:
            self.get_abstract_and_subject_terms_fieldset(data, record)
        except:
            pass

        # reproductions
        try:
            self.get_reproductions_fieldset(data, record)
        except:
            pass

        # Exhibitions
        try:
            self.get_exhibitions_fieldset(data, record)
        except:
            pass

        # Relations
        try:
            self.get_relations_fieldset(data, record)
        except:
            pass

        try:
            self.get_free_fields_fieldset(data, record)
        except:
            pass

        try:
            self.get_copies_fieldset(data, record)
        except:
            pass

        # Create dirty plone id
        dirty_id = self.create_dirty_id(data)
            
        return data


    def get_article(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",
            'titleAuthorSource_titleAuthor_leadWord':'',
            'titleAuthorSource_titleAuthor_title':[],
            'titleAuthorSource_titleAuthor_statementOfRespsib':'',
            'titleAuthorSource_titleAuthor_author':[],
            'titleAuthorSource_titleAuthor_illustrator':[],
            'titleAuthorSource_titleAuthor_corpAuthor':'',
            'titleAuthorSource_source_source': [],
            'titleAuthorSource_sortYear_sortYear':'',
            'titleAuthorSource_illustrations_illustrations': [],
            'titleAuthorSource_notes_bibliographicalNotes':[],
            'titleAuthorSource_conference_conference':[],

            # Abstract and subject terms
            'abstractAndSubjectTerms_materialType':[], 
            'abstractAndSubjectTerms_biblForm':[],
            'abstractAndSubjectTerms_language':[], 
            'abstractAndSubjectTerms_level':"",
            'abstractAndSubjectTerms_notes':[], 
            'abstractAndSubjectTerms_classNumber':[],
            'abstractAndSubjectTerms_subjectTerm':[], 
            'abstractAndSubjectTerms_personKeywordType':[],
            'abstractAndSubjectTerms_geographicalKeyword':[], 
            'abstractAndSubjectTerms_period':[],
            'abstractAndSubjectTerms_startDate':"", 
            'abstractAndSubjectTerms_endDate':"",
            'abstractAndSubjectTerms_digitalReferences_reference':[], 
            'abstractAndSubjectTerms_abstract_abstract':[],

            # Reproductions
            "reproductions_reproduction": [],

            # Exhibitions, auctions, collections
            'exhibitionsAuctionsCollections_exhibition':[], 
            'exhibitionsAuctionsCollections_auction':[],
            'exhibitionsAuctionsCollections_collection':[],

            # Relations
            'relations_volume':"", 
            'relations_analyticalCataloguing_recordNo':"",
            'relations_analyticalCataloguing_volume':"", 
            'relations_analyticalCataloguing_title':"", 
            'relations_analyticalCataloguing_partOf':[],
            'relations_analyticalCataloguing_consistsOf':[], 
            'relations_museumObjects':[],

            # Free fields
            'freeFieldsAndNumbers_freeFields':[], 
            'freeFieldsAndNumbers_otherNumber':[],
            'freeFieldsAndNumbers_PPN':"",

            # Copies
            'copiesAndShelfMarks_defaultShelfMark':"", 
            'copiesAndShelfMarks_copyDetails':[]
        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_article_title_author_fieldset(data, record)
        except:
            pass

        # Abstract
        try:
            self.get_abstract_and_subject_terms_fieldset(data, record)
        except:
            pass

        # reproductions
        try:
            self.get_reproductions_fieldset(data, record)
        except:
            pass

        # Exhibitions
        try:
            self.get_exhibitions_fieldset(data, record)
        except:
            pass

        # Relations
        try:
            self.get_relations_fieldset(data, record)
        except:
            pass

        try:
            self.get_free_fields_fieldset(data, record)
        except:
            pass

        try:
            self.get_copies_fieldset(data, record)
        except:
            pass

        # Create dirty plone id
        dirty_id = self.create_article_dirty_id(data)
            
        return data

    def get_serial(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",
            'titleAuthorImprintCollation_titleAuthor_leadWord':'',
            'titleAuthorImprintCollation_titleAuthor_title':[],
            'titleAuthorImprintCollation_titleAuthor_statementOfRespsib':'',
            'titleAuthorImprintCollation_titleAuthor_author':[],
            'titleAuthorImprintCollation_titleAuthor_corpAuthor':'',
            'titleAuthorImprintCollation_edition_edition':'',
            'titleAuthorImprintCollation_issues_issues':'',
            'titleAuthorImprintCollation_imprint_place':[], 
            'titleAuthorImprintCollation_imprint_publisher':[],
            'titleAuthorImprintCollation_imprint_year':"", 
            'titleAuthorImprintCollation_imprint_placePrinted':[],
            'titleAuthorImprintCollation_imprint_printer':[], 
            'titleAuthorImprintCollation_sortYear_sortYear':'',
            'titleAuthorImprintCollation_collation_illustrations':'',
            'titleAuthorImprintCollation_collation_dimensions':'', 
            'titleAuthorImprintCollation_collation_accompanyingMaterial':[],
            
            # Series
            'seriesNotesISSNShelfmark_series_series':"", 
            'seriesNotesISSNShelfmark_notes_holding':"",
            'seriesNotesISSNShelfmark_notes_bibliographicalNotes':"",
            'seriesNotesISSNShelfmark_ISSN_ISSN':"",
            'seriesNotesISSNShelfmark_continuation_continuedFrom': [],
            'seriesNotesISSNShelfmark_continuation_continuedAs': [],
            'seriesNotesISSNShelfmark_conference_conference':"",

            # Abstract and subject terms
            'abstractAndSubjectTerms_materialType':[], 
            'abstractAndSubjectTerms_biblForm':[],
            'abstractAndSubjectTerms_language':[], 
            'abstractAndSubjectTerms_level':"",
            'abstractAndSubjectTerms_notes':[], 
            'abstractAndSubjectTerms_classNumber':[],
            'abstractAndSubjectTerms_subjectTerm':[], 
            'abstractAndSubjectTerms_personKeywordType':[],
            'abstractAndSubjectTerms_geographicalKeyword':[], 
            'abstractAndSubjectTerms_period':[],
            'abstractAndSubjectTerms_startDate':"", 
            'abstractAndSubjectTerms_endDate':"",
            'abstractAndSubjectTerms_digitalReferences_reference':[], 
            'abstractAndSubjectTerms_abstract_abstract':[],

            # Reproductions
            "reproductions_reproduction": [],

            # Exhibitions, auctions, collections
            'exhibitionsAuctionsCollections_exhibition':[], 
            'exhibitionsAuctionsCollections_auction':[],
            'exhibitionsAuctionsCollections_collection':[],

            # Relations
            'relations_volume':"", 
            'relations_analyticalCataloguing_recordNo':"",
            'relations_analyticalCataloguing_volume':"", 
            'relations_analyticalCataloguing_title':"", 
            'relations_analyticalCataloguing_partOf':[],
            'relations_analyticalCataloguing_consistsOf':[], 
            'relations_museumObjects':[],

            # Free fields
            'freeFieldsAndNumbers_freeFields':[], 
            'freeFieldsAndNumbers_otherNumber':[],
            'freeFieldsAndNumbers_PPN':"",

            # Copies
            'copiesAndShelfMarks_defaultShelfMark':"", 
            'copiesAndShelfMarks_copyDetails':[]
        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_serial_title_author_fieldset(data, record)
        except:
            raise

        # Series
        try:
            self.get_serials_series_fieldset(data, record)
        except:
            raise

        # Abstract
        try:
            self.get_abstract_and_subject_terms_fieldset(data, record)
        except:
            raise

        # reproductions
        try:
            self.get_reproductions_fieldset(data, record)
        except:
            raise

        # Exhibitions
        try:
            self.get_exhibitions_fieldset(data, record)
        except:
            raise

        # Relations

        try:
            self.get_relations_fieldset(data, record)
        except:
            raise

        try:
            self.get_free_fields_fieldset(data, record)
        except:
            raise

        try:
            self.get_copies_fieldset(data, record)
        except:
            raise

        # Create dirty plone id
        dirty_id = self.create_dirty_id(data)
            
        return data

    def get_book(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",
            'titleAuthorImprintCollation_titleAuthor_article':'',
            'titleAuthorImprintCollation_titleAuthor_title':[],
            'titleAuthorImprintCollation_titleAuthor_statementOfRespsib':'',
            'titleAuthorImprintCollation_titleAuthor_author':[],
            'titleAuthorImprintCollation_titleAuthor_illustrator':[],
            'titleAuthorImprintCollation_titleAuthor_corpAuthor':'',
            'titleAuthorImprintCollation_edition_edition':'',
            'titleAuthorImprintCollation_imprint_place':[], 
            'titleAuthorImprintCollation_imprint_publisher':[],
            'titleAuthorImprintCollation_imprint_year':"", 
            'titleAuthorImprintCollation_imprint_placePrinted':[],
            'titleAuthorImprintCollation_imprint_printer':[], 
            'titleAuthorImprintCollation_sortYear_sortYear':'',
            'titleAuthorImprintCollation_collation_pagination':'', 
            'titleAuthorImprintCollation_collation_illustrations':'',
            'titleAuthorImprintCollation_collation_dimensions':'', 
            'titleAuthorImprintCollation_collation_accompanyingMaterial':[],
            
            # Series
            'seriesNotesISBN_series_series':"", 
            'seriesNotesISBN_series_subseries':"",
            'seriesNotesISBN_notes_bibliographicalNotes':"",
            'seriesNotesISBN_ISBN_ISBN':"",
            'seriesNotesISBN_ISBN_ISSN':"",
            'seriesNotesISBN_conference_conference':"",

            # Abstract and subject terms
            'abstractAndSubjectTerms_materialType':[], 
            'abstractAndSubjectTerms_biblForm':[],
            'abstractAndSubjectTerms_language':[], 
            'abstractAndSubjectTerms_level':"",
            'abstractAndSubjectTerms_notes':[], 
            'abstractAndSubjectTerms_classNumber':[],
            'abstractAndSubjectTerms_subjectTerm':[], 
            'abstractAndSubjectTerms_personKeywordType':[],
            'abstractAndSubjectTerms_geographicalKeyword':[], 
            'abstractAndSubjectTerms_period':[],
            'abstractAndSubjectTerms_startDate':"", 
            'abstractAndSubjectTerms_endDate':"",
            'abstractAndSubjectTerms_digitalReferences_reference':[], 
            'abstractAndSubjectTerms_abstract_abstract':[],

            # Reproductions
            "reproductions_reproduction": [],

            # Exhibitions, auctions, collections
            'exhibitionsAuctionsCollections_exhibition':[], 
            'exhibitionsAuctionsCollections_auction':[],
            'exhibitionsAuctionsCollections_collection':[],

            # Relations
            'relations_volume':"", 
            'relations_analyticalCataloguing_recordNo':"",
            'relations_analyticalCataloguing_volume':"", 
            'relations_analyticalCataloguing_title':"", 
            'relations_analyticalCataloguing_partOf':[],
            'relations_analyticalCataloguing_consistsOf':[], 
            'relations_museumObjects':[],

            # Free fields
            'freeFieldsAndNumbers_freeFields':[], 
            'freeFieldsAndNumbers_otherNumber':[],
            'freeFieldsAndNumbers_PPN':"",

            # Copies
            'copiesAndShelfMarks_defaultShelfMark':"", 
            'copiesAndShelfMarks_copyDetails':[]
        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_title_author_fieldset(data, record)
        except:
            pass

        # Series
        try:
            self.get_series_fieldset(data, record)
        except:
            pass

        # Abstract
        try:
            self.get_abstract_and_subject_terms_fieldset(data, record)
        except:
            pass

        # reproductions
        try:
            self.get_reproductions_fieldset(data, record)
        except:
            raise

        # Exhibitions
        try:
            self.get_exhibitions_fieldset(data, record)
        except:
            pass

        # Relations
        try:
            self.get_relations_fieldset(data, record)
        except:
            pass

        try:
            self.get_free_fields_fieldset(data, record)
        except:
            pass

        try:
            self.get_copies_fieldset(data, record)
        except:
            pass

        # Create dirty plone id
        dirty_id = self.create_dirty_id(data)
            
        return data

    # Get resource dublincore
    def get_resource_dublincore_fieldset(self, data, record):
        
        #resourceDublinCore_title
        titles = []
        if len(record.findall('title')) > 0:
            for title in record.findall('title'):
                titles.append({
                    "title": self.api_migrator.trim_white_spaces(title.text)
                    })

        data['resourceDublinCore_title'] = titles

        #'resourceDublinCore_creator':[],
        creators = []

        for creator in record.findall('author.name'):
            if creator.find('name') != None:
                creators.append({
                    "name": self.api_migrator.trim_white_spaces(creator.find('name').text)
                    })

        data['resourceDublinCore_creator'] = creators

        #'resourceDublinCore_subject':[], 
        subjects = []

        for subject in record.findall('keyword.contents'):
            if subject.find('term') != None:
                subjects.append({
                    "term": self.api_migrator.trim_white_spaces(subject.find('term').text)
                    })

        data['resourceDublinCore_subject'] = subjects

        #'resourceDublinCore_description':[],
        descriptions = []

        for description in record.findall('abstract'):
            descriptions.append({
                "term": self.api_migrator.trim_white_spaces(description.text)
                })

        data['resourceDublinCore_description'] = descriptions

        #'resourceDublinCore_publisher':[], 
        publishers = []

        for publisher in record.findall('publisher'):
            if publisher.find('name') != None:
                publishers.append({
                    "name": self.api_migrator.trim_white_spaces(publisher.find('name').text)
                    })

        data['resourceDublinCore_publisher'] = publishers

        #'resourceDublinCore_contributor':[],
        contributors = []

        for contributor in record.findall('contributor'):
            if contributor.find('name') != None:
                contributors.append({
                    "term": self.api_migrator.trim_white_spaces(contributor.find('name').text)
                    })

        data['resourceDublinCore_contributor'] = contributors

        #'resourceDublinCore_date':"", 
        
        if record.find('year_of_publication') != None:
            data['resourceDublinCore_date'] = self.api_migrator.trim_white_spaces(record.find('year_of_publication').text)

        #'resourceDublinCore_resourceType':[],
        resources = []

        for resource in record.findall('material_type'):
            if resource.find('term') != None:
                resources.append({
                    "term": self.api_migrator.trim_white_spaces(resource.find('term').text)
                })

        data['resourceDublinCore_resourceType'] = resources

        #'resourceDublinCore_format':[], 
        formats = []       

        for f in record.findall('dimensions'):
            formats.append({
                "term": self.api_migrator.trim_white_spaces(f.text)
                })

        data['resourceDublinCore_format'] = formats     

        #'resourceDublinCore_identifier':[],
        identifiers = []

        for identifier in record.findall('digital_reference'):
            identifiers.append({
                "term": self.api_migrator.trim_white_spaces(identifier.text)
                })

        data['resourceDublinCore_identifier'] = identifiers

        #'resourceDublinCore_sortYear_sortYear':[], 
        if record.find('sort_year') != None:
            data['resourceDublinCore_sortYear_sortYear'] = self.api_migrator.trim_white_spaces(record.find('sort_year').text)

        #'resourceDublinCore_source':[],
        sources = []

        for source in record.findall('source'):
            sources.append({
                "term": self.api_migrator.trim_white_spaces(source.text)
                })

        data['resourceDublinCore_source'] = sources

        #'resourceDublinCore_language':[], 
        languages = []

        for language in record.findall('language_code'):
            if language.find('term') != None:
                languages.append({
                    "term": self.api_migrator.trim_white_spaces(language.find('term').text)
                    })

        data['resourceDublinCore_language'] = languages

        #'resourceDublinCore_relation':[],
        relations = []

        for rel in record.findall('relation'):
            relations.append({
                "term": self.api_migrator.trim_white_spaces(rel.text)
                })

        data['resourceDublinCore_relation'] = relations

        #'resourceDublinCore_coverage':[], 
        coverages = []

        for coverage in record.findall('coverage'):
            coverages.append({
                "term": self.api_migrator.trim_white_spaces(coverage.text)
                })

        data['resourceDublinCore_coverage'] = coverages

        #'resourceDublinCore_rights':[],
        rights = []

        for right in record.findall('rights'):
            rights.append({
                "term": self.api_migrator.trim_white_spaces(right.text)
                })

        data['resourceDublinCore_rights'] = rights

        return True

    def get_resource(self, priref, record, create):

        data = {
            'text':"",
            'priref':"",
            'resourceDublinCore_title':[], 
            'resourceDublinCore_creator':[],
            'resourceDublinCore_subject':[], 
            'resourceDublinCore_description':[],
            'resourceDublinCore_publisher':[], 
            'resourceDublinCore_contributor':[],
            'resourceDublinCore_date':"", 
            'resourceDublinCore_resourceType':[],
            'resourceDublinCore_format':[], 
            'resourceDublinCore_identifier':[],
            'resourceDublinCore_sortYear_sortYear':"", 
            'resourceDublinCore_source':[],
            'resourceDublinCore_language':[], 
            'resourceDublinCore_relation':[],
            'resourceDublinCore_coverage':[], 
            'resourceDublinCore_rights':[],

            # Reproductions
            "reproductions_reproduction": [],

            # Exhibitions, auctions, collections
            'exhibitionsAuctionsCollections_exhibition':[], 
            'exhibitionsAuctionsCollections_auction':[],
            'exhibitionsAuctionsCollections_collection':[],

            # Relations
            'linkedObjects_linkedObjects':[],

            # Copies
            'copiesAndShelfMarks_defaultShelfMark':"", 
            'copiesAndShelfMarks_copyDetails':[]
        }   

        # Title and Author]
        data['priref'] = priref

        try:
            self.get_resource_dublincore_fieldset(data, record)
        except:
            pass

        # reproductions
        try:
            self.get_reproductions_fieldset(data, record)
        except:
            pass

        # Exhibitions
        try:
            self.get_exhibitions_fieldset(data, record)
        except:
            pass

        # Linked objects
        try:
            self.api_migrator.get_linked_objects_fieldset(data, record)
        except:
            pass

        try:
            self.get_copies_fieldset(data, record)
        except:
            pass

        # Create dirty plone id
        dirty_id = self.create_resource_dirty_id(data)
            
        return data

    def create_book(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/bibliotheek/boeken')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Book already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_book_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if len(data['titleAuthorImprintCollation_titleAuthor_title']) > 0:
                        title = data['titleAuthorImprintCollation_titleAuthor_title'][0]['title']

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Book",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_book(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Book %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Book already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_book (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped object: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def create_audiovisual(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/bibliotheek/audio-visuele-materialen')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Audio visual already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_audiovisual_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if len(data['titleAuthorImprintCollation_titleAuthor_title']) > 0:
                        title = data['titleAuthorImprintCollation_titleAuthor_title'][0]['title']

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Audiovisual",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_audiovisual(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Audiovisual %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Audiovisual already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_audiovisual (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped Audiovisual: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def create_article(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/bibliotheek/artikelen')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Article already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_article_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if len(data['titleAuthorSource_titleAuthor_title']) > 0:
                        title = data['titleAuthorSource_titleAuthor_title'][0]['title']

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Article",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_article(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Article %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Article already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_article (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped Article: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def create_resource(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/bibliotheek/digitale-bronnen')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Resource already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_resource_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if len(data['resourceDublinCore_title']) > 0:
                        title = data['resourceDublinCore_title'][0]['title']

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Resource",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_resource(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Resource %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Resource already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_Resource (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped Resource: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object

    def create_serial(self, data):
        transaction.begin()
        
        container = self.api_migrator.get_folder('nl/bibliotheek/tijdschriften')
        
        dirty_id = data['dirty_id']
        if dirty_id == "":
            dirty_id = data['priref']

        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        result = False

        created_object = None

        try:
            ## Verify if id already exists in container
            if hasattr(container, normalized_id) and normalized_id != "":
                self.api_migrator.skipped += 1
                timestamp = datetime.datetime.today().isoformat()
                print "%s - Serial already exists %s" % (timestamp, normalized_id)
                transaction.commit()
                return container[normalized_id]

            ## ID not in container
            if not hasattr(container, normalized_id):
                ##
                ## Check if object exists in database
                ##
                object_item = self.get_serial_from_instance(data['priref'])
                
                if object_item == None:
                    ##
                    ## Creates object
                    ##
                    text = RichTextValue(data['text'], 'text/html', 'text/html')

                    title = ""
                    if len(data['titleAuthorImprintCollation_titleAuthor_title']) > 0:
                        title = data['titleAuthorImprintCollation_titleAuthor_title'][0]['title']

                    # Create Object inside of the container
                    container.invokeFactory(
                        ## Standard
                        type_name="Serial",
                        id=normalized_id,
                        title=title,
                        text=text,
                        priref=data["priref"]
                    )

                    # Get object and add tags
                    created_object = container[str(normalized_id)]

                    # Publish object
                    #created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

                    # Renindex portal catalog
                    self.update_serial(created_object, data)

                    created_object.reindexObject()
                    created_object.reindexObject(idxs=["hasMedia"])
                    created_object.reindexObject(idxs=["leadMedia"])

                    #### Commmit to the database
                    transaction.commit()

                    #### Log Book added
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Added Serial object %s" % (timestamp, normalized_id)

                    self.api_migrator.created += 1
                    result = True
                else:
                    ##
                    ## Object with object_number already exists in database
                    ##
                    self.api_migrator.skipped += 1
                    timestamp = datetime.datetime.today().isoformat()
                    print "%s - Serial already exists %s" % (timestamp, normalized_id)
                    transaction.commit()
                    return object_item
        except:
            ##
            ## Exception handling
            ##
            self.api_migrator.errors += 1
            self.api_migrator.success = False
            print "Unexpected error on create_serial (" +dirty_id+ "):", sys.exc_info()[1]
            raise
            result = False
            transaction.abort()
            return result

        ##
        ## Skipped object
        ##
        if not result:
            timestamp = datetime.datetime.today().isoformat()
            self.api_migrator.skipped += 1
            print "%s - Skipped Serial: %s" %(timestamp, normalized_id)

        ###
        ### Returns created object item
        ### Returns None if nothing was created
        ###
        return created_object


    def update_book(self, book, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(book, key):
                    setattr(book, key, value)

        print "Book updated!"
        return True

    def update_audiovisual(self, book, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(book, key):
                    setattr(book, key, value)

        print "Audiovisual updated!"
        return True

    def update_article(self, book, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(book, key):
                    setattr(book, key, value)

        print "Article updated!"
        return True

    def update_serial(self, book, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(book, key):
                    setattr(book, key, value)

        print "Serial updated!"
        return True

    def update_resource(self, book, data):

        for key, value in data.iteritems():
            if key not in ['text', 'dirty_id']:
                if hasattr(book, key):
                    setattr(book, key, value)

        print "Resource updated!"
        return True

    def import_books(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/single-book-v02.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Books-v02.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Boeken.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_book(priref, obj, True)
                    # Create books
                    self.create_book(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Book failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Book failed unexpected" %(timestamp)
                pass

        self.success = True
        return True

    def import_resources(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/single-resource-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Resources-v01.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Digitalebronnen.xml"


        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_resource(priref, obj, True)
                    self.create_resource(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Resource failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Resource failed unexpected" %(timestamp)
                raise

        self.success = True
        return True

    def update_books(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/single-book-v02.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Books-v02.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Boeken.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "Updating %s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    current_object = self.get_book_from_instance(priref)
                    if current_object != None:
                        data = self.get_book(priref, obj, False)
                        self.update_book(current_object, data)
                        current_object.reindexObject()
                else:
                    print "Error, priref does not exist."

            except:
                print "Book failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Book failed unexpected" %(timestamp)
                raise

        self.success = True
        return True


    def import_audiovisual(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/single-audio-visual-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Audio-visual-materials-v01.xml"
        colletion_path_prod = "/var/www/zm-collectie-v2/xml/Audiovisuelematerialen.xml"

        objects = self.api_migrator.get_zm_collection(colletion_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_audiovisual(priref, obj, True)
                    self.create_audiovisual(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Audiovisual failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Audiovisual failed unexpected" %(timestamp)
                pass

        self.success = True
        return True

    def import_articles(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/single-article-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Articles-v01.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Artikelen.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_article(priref, obj, True)
                    self.create_article(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Article failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Article failed unexpected" %(timestamp)
                raise

        self.success = True
        return True

    def import_serials(self):

        collection_path_test = "/Users/AG/Projects/collectie-zm/single-serial-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Serials-v01.xml"
        collection_path_prod = "/var/www/zm-collectie-v2/xml/Tijdschriften.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_prod)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    data = self.get_serial(priref, obj, True)
                    self.create_serial(data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Serial failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Serial failed unexpected" %(timestamp)
                raise

        self.success = True
        return True

    def update_audiovisuals(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/single-audio-visual-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Audio-visual-materials-v01.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_test)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    current_object = self.get_audiovisual_from_instance(priref)
                    if current_object != None:
                        data = self.get_audiovisual(priref, obj, False)
                        self.update_audiovisual(current_object, data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Audiovisual failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Audiovisual failed unexpected" %(timestamp)
                raise

        self.success = True
        return True

    def update_articles(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/single-article-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Articles-v01.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_test)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    current_object = self.get_article_from_instance(priref)
                    if current_object != None:
                        data = self.get_article(priref, obj, False)
                        self.update_article(current_object, data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Article failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Article failed unexpected" %(timestamp)
                raise

        self.success = True
        return True

    def update_serials(self):
        collection_path_test = "/Users/AG/Projects/collectie-zm/single-serial-v01.xml"
        collection_path_stage = "/home/andre/collectie-zm-v1/xml/Serials-v01.xml"

        objects = self.api_migrator.get_zm_collection(collection_path_test)

        total = len(list(objects))
        curr = 0

        for obj in list(objects):
            try:
                curr += 1
                print "%s / %s" %(str(curr), str(total))
                priref = obj.find('priref').text

                if priref != "" and priref != None:
                    current_object = self.get_serial_from_instance(priref)
                    if current_object != None:
                        data = self.get_serial(priref, obj, False)
                        self.update_serial(current_object, data)
                else:
                    print "Error, priref does not exist."

            except:
                print "Serial failed"
                timestamp = datetime.datetime.today().isoformat()
                print "[%s] Serial failed unexpected" %(timestamp)
                raise

        self.success = True
        return True

    def find_object(self, all_objects, object_number):
        for brain in all_objects:
            obj = brain.getObject()
            if hasattr(obj, 'identification_identification_objectNumber'):
                if obj.identification_identification_objectNumber == object_number:
                    return obj

        return None

    def rel_exists(self, rel_obj, related_objects):
        # Try to check if related item already exists

        if hasattr(rel_obj, 'identification_identification_objectNumber'):
            object_number = rel_obj.identification_identification_objectNumber
            for obj in related_objects:
                rel = obj.to_object
                if hasattr(rel, 'identification_identification_objectNumber'):
                    if rel.identification_identification_objectNumber == object_number:
                        print "Rel already exists."
                        return True
            return False
        else:
            return False

    def add_related_object(self, rel_obj, obj):
        # Tries to add linked object to related items

        intids = component.getUtility(IIntIds)
        if hasattr(obj, 'relations_relatedMuseumObjects'):
            curr_related_objects = obj.relations_relatedMuseumObjects

            # Try to check if related item already exists
            
            if not self.rel_exists(rel_obj, curr_related_objects):
                # Add related object if rel doesn't exist
                rel_obj_id = intids.getId(rel_obj)
                rel_obj_value = RelationValue(rel_obj_id)
                if len(obj.relations_relatedMuseumObjects) == 0:
                    obj.relations_relatedMuseumObjects = []
                obj.relations_relatedMuseumObjects.append(rel_obj_value)
                print "Added relation."

        return None

    def transform_related_objects(self):

        # get items
        container = self.api_migrator.get_folder('nl/bibliotheek/boeken')

        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Object', Language="all")

        total = len(list(container))
        curr = 0

        for item in container:
            curr += 1
            transaction.begin()

            print "Adding %s / %s" %(str(curr), str(total))

            obj = container[item]

            if hasattr(obj, 'relations_museumObjects'):
                linked_objects = obj.relations_museumObjects
                if linked_objects != None:
                    # Original linked objects
                    for linked in linked_objects:
                        rel_object_number = linked['objectNo']

                        # Find if linked object exists
                        rel_object = self.find_object(all_objects, rel_object_number)
                        if rel_object != None:
                            # Tries to add linked object to related items
                            self.add_related_object(rel_object, obj)
                        else:
                            print "Object not found."

            transaction.commit()

        return True

    def find_exhibition(self, all_objects, object_number):
        for brain in all_objects:
            obj = brain.getObject()
            if hasattr(obj, 'title'):
                if obj.title == object_number:
                    return obj

        return None

    def rel_exhibition_exists(self, rel_obj, related_objects):
        # Try to check if related item already exists

        if hasattr(rel_obj, 'priref'):
            object_number = rel_obj.priref
            for obj in related_objects:
                rel = obj.to_object
                if hasattr(rel, 'priref'):
                    if rel.priref == object_number:
                        print "Rel exhibition already exists."
                        return True
            return False
        else:
            return False

    def add_related_exhibition(self, rel_obj, obj):
        # Tries to add linked object to related items

        intids = component.getUtility(IIntIds)
        if hasattr(obj, 'exhibitionsAuctionsCollections_relatedExhibitions'):
            curr_related_objects = obj.exhibitionsAuctionsCollections_relatedExhibitions

            # Try to check if related item already exists
            
            if not self.rel_exhibition_exists(rel_obj, curr_related_objects):
                # Add related object if rel doesn't exist
                rel_obj_id = intids.getId(rel_obj)
                rel_obj_value = RelationValue(rel_obj_id)
                if len(obj.exhibitionsAuctionsCollections_relatedExhibitions) == 0:
                    obj.exhibitionsAuctionsCollections_relatedExhibitions = []
                obj.exhibitionsAuctionsCollections_relatedExhibitions.append(rel_obj_value)
                print "Added exhibition relation."

        return None

    def transform_related_exhibitions(self):

        # get items
        container = self.api_migrator.get_folder('nl/bibliotheek/boeken')

        catalog = getToolByName(container, 'portal_catalog')
        all_objects = catalog(portal_type='Exhibition', Language="all")

        total = len(list(container))
        curr = 0

        for item in container:
            curr += 1

            print "Adding relation to exhibition %s / %s" %(str(curr), str(total))

            obj = container[item]

            if hasattr(obj, 'exhibitionsAuctionsCollections_exhibition'):
                linked_objects = obj.exhibitionsAuctionsCollections_exhibition
                if linked_objects != None:
                    # Original linked objects
                    for linked in linked_objects:
                        rel_object_number = linked['exhibitionName']

                        # Find if linked object exists
                        rel_object = self.find_exhibition(all_objects, rel_object_number)
                        if rel_object != None:
                            # Tries to add linked object to related items
                            self.add_related_exhibition(rel_object, obj)
                        else:
                            print "Object not found."

        self.success = True
        return True

    def start(self):

        self.run_type = "update_books"

        print "\n[ Run for type: %s ]\n" %(self.run_type)

        if self.run_type == "import_books":
            #self.import_books()
            self.import_audiovisual()
            self.import_articles()
            self.import_serials()
            self.import_resources()

        elif self.run_type == "update_books":
            self.update_books()

        elif self.run_type == "import_audiovisual":
            self.import_audiovisual()

        elif self.run_type == "import_articles":
            self.import_articles()

        elif self.run_type == "import_serials":
            self.import_serials()

        elif self.run_type == "import_resources":
            self.import_resources()

        elif self.run_type == "transform_related_objects":
            self.transform_related_objects()

        elif self.run_type == "transform_related_exhibitions":
            self.transform_related_exhibitions()
        else:
            print "Run type not available. Exiting."
            return True


        return True
