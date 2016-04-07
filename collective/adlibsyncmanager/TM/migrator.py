#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""

import re, AccessControl, transaction, time, sys, datetime, os, csv, unicodedata, csv, pytz, string, fnmatch, urllib2, urllib  
from Acquisition import aq_parent, aq_inner
from z3c.relationfield.interfaces import IRelationList, IRelationValue
from plone import api 
from zope.intid.interfaces import IIntIds
from z3c.relationfield.schema import RelationList
from zope import component
from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice, ITextLine, IList, IText, IBool, IDatetime
from plone.app.textfield.interfaces import IRichText
from zc.relation.interfaces import ICatalog
from lxml import etree
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime
from plone.i18n.normalizer import idnormalizer
from Testing.makerequest import makerequest
from plone.dexterity.utils import createContentInContainer
from collective.leadmedia.utils import addCropToTranslation
from collective.leadmedia.utils import imageObjectCreated
from plone.app.textfield.value import RichTextValue
from plone.event.interfaces import IEventAccessor
from z3c.relationfield import RelationValue
import glob
from plone.multilingual.interfaces import ITranslationManager

from collective.leadmedia.utils import autoCropImage

from .teylers_contenttypes_path import CONTENT_TYPES_PATH
from .teylers_contenttypes_path import IMAGES_HD_PATH

from .teylers_core import CORE
from .teylers_utils import subfields_types, relation_types
from .log_files_path import LOG_FILES_PATH


NOT_ALLOWED = ['', ' ', None]
ALLOWED_SOURCES = [None, 'Instrumentenwebsite']

FOSSILS_FIX = ["F 00545", "F 01524", "F 07424", "F 09102", "F 15776", "F 16269", "F 16390", "F 17003", "F 50001", "F 50003", "F 01324", "F 06928", "F 08432", "F 13280", "F 16266", "F 16277", "F 16724", "F 17046d", "F 50002", "M 01518"]
KUNST_FIX = ['KT 1990 061', 'KT 2009 034', 'KT 1990 105', 'KT 2689', 'KT 2666', 'KT 1997 069', 'KT 2644', 'KT 2012 016', 'KT 2000 102', 'KT 1985 126', 'KT 1997 059', 'KT 2697', 'KT 2611', 'KT 2571', 'KT 2684', 'KT 1990 057', 'KT 2602', 'KT 1993 037', 'KT 2581', 'KT 1985 125', 'KT 1986 032', 'KT 2606', 'KT 1990 059', 'KT 2599', 'KT 2568', 'KT 2593', 'KT 2620', 'KT 2004 121', 'KT 2565', 'KT 1990 007', 'KT 2588', 'KT 2617', 'KT 2615', 'KT 2641', 'KT 2007 007', 'KT 2007 078', 'KT 2600', 'KT 2009 019', 'KT 2673', 'KT 2682', 'KT 2579', 'KT 2584', 'KT 2597', 'KT 2577', 'KT 2665', 'KT 2634', 'KT 2570', 'KT 1999 048', 'KT 2738', 'KT 2679', 'KT 2621', 'KT 2004 120', 'KT 2653', 'KT 2662', 'KT 1991 134', 'KT 2010 061', 'KT 2604', 'KT 2586', 'KT 2616', 'KT 1999 041', 'KT 2669', 'KT 1986 036', 'KT 1990 064', 'KT 1998_042', 'KT 2683', 'KT 1986 030', 'KT 2594', 'KT 2818', 'KT 1997 064', 'KT 2622', 'KT 2812', 'KT 2714', 'KT 2007_005', 'KT 1986 022', 'KT 2817', 'KT 2009 059', 'KT 1999 035', 'KT 1989 048', 'KT 2009 056', 'KT 2626', 'KT 2567', 'KT 2614', 'KT 1991 133', 'KT 2612', 'KT 2815', 'KT 2811', 'KT 2671', 'KT 1989 112', 'KT 2007 058', 'KT 1986 038', 'KT 2656', 'KT 2582', 'KT 1986 041', 'KT 2628', 'KT 2585', 'KT 2003 013', 'KT 2623', 'KT 2595', 'KT 2000 100', 'KT 1986 035', 'KT 1986 033', 'KT 2000 106', 'KT 2685', 'KT 2007 077', 'KT 2636', 'KT 2000 105', 'KT 2007 059', 'KT 1997 066', 'KT 2722', 'KT 2596', 'KT 2000 103', 'KT 2012 015', 'KT 1997 060', 'KT 2580', 'KT 1991 135', 'KT 2013 103', 'KT 2007 060', 'KT 1998 024', 'KT 2591', 'KT 2709', 'KT 2704', 'KT 2677', 'KT 1997 062', 'KT 2608', 'KT 1997 070', 'KT 2635', 'KT 1997 067', 'KT 1997 039', 'KT 2293', 'KT 2655', 'KT 2631', 'KT 2651', 'KT 2603', 'KT 1987 040', 'KT 2720', 'KT 2672', 'KT 2647', 'KT 2613', 'KT 1990 055', 'KT 2578', 'KT 2607', 'KT 2718', 'KT 2676', 'KT 1985 027', 'KT 2717', 'KT 1999 042', 'KT 2716', 'KT 2007 055', 'KT 2592', 'KT 2688', 'KT 1997 068', 'KT 2572', 'KT 2007 057', 'KT 2561', 'KT 2663', 'KT 1999 038', 'KT 2009 057', 'KT 2692', 'KT 1997 071', 'KT 2618', 'KT 2694', '._Boeken', 'KT 2664', 'KT 1993 039', 'KT 1990 004', 'KT 1990 049', 'KT 2630', 'KT 2695', 'KT 1997 061', 'KT 2566', 'KT 2693', 'KT 2652', 'KT 2005 023', 'KG 1990 062', 'KT 1990 003', 'KT 2699', 'KT 1999 047', 'KT 2007 061', 'KT 2009 058', 'KT 2576', 'KT 1985 024', 'KT 2000 134', 'KG 1985 025', 'KT 1989 045', 'KT 1996 078', 'KT 2013 002', 'KT 2678', 'KT 2650', 'KT 2707', 'KT 1990 050', 'KT 1997 065', 'KT 2633', 'KT 2691', 'KT 2813', 'KT 1986 040', 'KT 2681', 'KT 2006 011', 'KT 2569', 'KT 2674', 'KT 2000 156', 'KT 2668', 'KT 1999 037', 'KT 1999 043', 'KT 1989 047', 'KT 1985 026', 'KT 2007 056', 'KT 2007 076', 'KT 2637', 'KT 2703', 'KT 1986 037', 'KT 2696', 'KT 2711', 'KT 1990 005', 'KT 2690', 'KT 1989 046', 'KT 2680', 'KT 2575', 'KT 1986 021', 'KT 1986 039', 'KT 2000 101', 'KT 2013 001', 'KT 2649', 'KT 1997 058', 'KT 2698', 'KT 2661', 'KT 2564', 'KT 2657', 'KT 2675', 'KT 2712', 'KT 2705', 'KT 2000 107', 'KT 2719', 'KT 2625', 'KT 2708', 'KT 2563', 'KT 1997 063', 'KT 2632', 'KT 2700', 'KT 2574', 'KT 2598', 'KT 2605', 'KT 2816', 'KT 2654', 'KT 2009 062', 'KT 2645', 'KT 1986 034', 'KT 2687', 'KT 2012 014', 'KT 2589', 'KT 1996 082', 'KT 1999 039', 'KT 2646', 'KT 1990 106', 'KT 1986 023', 'KT 2583', 'KT 2005 015', 'KT 2713', 'KT 2686', 'KT 2643', 'KT 2639', 'KT 2009 061', 'KT 2638', 'KT 1990 083', 'KT 2003 017', 'KT 1989 001', 'KT 2629', 'KT 1990 083a', 'KT 2715', 'KT 2627', 'KT 1986 031', 'KT 2670', 'KT 1990 008', 'KT 2640', 'KT 2610', 'KT 1999 034', 'KT 1990 006', 'KT 2010 062', 'KT 2009 022', 'KT 2562', 'KT 1999 036', 'KT 2573', 'KT 2642', 'KT 2701', 'KT 1986 024', 'KT 2619', 'KT 2590', 'KT 2601', 'KT 2667', 'KT 1990 063', 'KT 2814', 'KT 2648', 'KT 2710', 'KT 2587', 'KT 2706', 'KT 2000 104', 'KT 1990 056', 'KT 2624']
PAINTINGS_FIX = ['KS 001', 'KS 002', 'KS 003', 'KS 004', 'KS 005', 'KS 006', 'KS 007', 'KS 008', 'KS 009', 'KS 010', 'KS 011', 'KS 013', 'KS 014', 'KS 016', 'KS 017', 'KS 019', 'KS 020', 'KS 021', 'KS 022', 'KS 023', 'KS 024', 'KS 025', 'KS 027', 'KS 028', 'KS 029', 'KS 030', 'KS 031', 'KS 032', 'KS 033', 'KS 034', 'KS 035', 'KS 036', 'KS 037', 'KS 038', 'KS 039', 'KS 041', 'KS 043', 'KS 044', 'KS 045', 'KS 046', 'KS 047', 'KS 048', 'KS 049', 'KS 050', 'KS 051', 'KS 052', 'KS 056', 'KS 062', 'KS 063', 'KS 064', 'KS 065', 'KS 066', 'KS 067', 'KS 068', 'KS 069', 'KS 071', 'KS 072', 'KS 073', 'KS 076', 'KS 077', 'KS 078', 'KS 079', 'KS 080', 'KS 081', 'KS 082', 'KS 083', 'KS 085-2', 'KS 087', 'KS 088', 'KS 089', 'KS 090', 'KS 091', 'KS 092', 'KS 093', 'KS 094', 'KS 097', 'KS 098', 'KS 099', 'KS 100', 'KS 101', 'KS 103', 'KS 104', 'KS 105', 'KS 106', 'KS 108', 'KS 109', 'KS 110', 'KS 111', 'KS 112', 'KS 113', 'KS 114', 'KS 115', 'ks-116', 'KS 117', 'KS 118', 'KS 119', 'KS 121', 'KS 124', 'KS 125', 'KS 126', 'KS 127', 'KS 128', 'KS 129', 'KS 130', 'KS 131', 'KS 132', 'KS 133', 'KS 135', 'KS 136', 'KS 137', 'KS 138a', 'KS 139', 'KS 141', 'KS 142', 'KS 144', 'KS 145', 'KS 146', 'KS 148', 'KS 151', 'KS 156', 'KS 157', 'KS 160', 'KS 161', 'KS 165', 'KS 166', 'KS 167', 'KS 168', 'KS 169', 'KS 171', 'KS 174', 'KS 175', 'KS 176', 'KS 178', 'KS 180', 'KS 180a', 'KS 183', 'KS 186', 'KS 187', 'KS 190', 'KS 192', 'KS 194', 'KS 195', 'KS 196', 'KS 1984-001', 'KS 1985-001', 'KS 1985-002', 'KS 1986-002', 'KS 1986-003', 'KS 1987-002', 'KS 1988-001', 'KS 1988-002', 'KS 1989-004', 'KS 1989-005', 'KS 1989-006', 'KS 1989-007', 'KS 1989-008', 'KS 1989-009', 'KS 1989-010', 'KS 1989-010_1', 'KS 1989-011', 'KS 1989-012', 'KS 1989-013', 'KS 1989-014', 'KS 1990-001', 'KS 1990-003', 'KS 1990-003a', 'KS 1990-004', 'KS 1990-005', 'KS 1990-006', 'KS 1990-007', 'KS 1990-008', 'KS 1990-009', 'KS 1990-010', 'KS 1990-011', 'KS 1990-012', 'KS 1990-013', 'KS 1990-014', 'KS 1990-015', 'KS 1990-016', 'KS 1990-023', 'KS 1990-025', 'KS 1991-002', 'KS 1991-003', 'KS 1992-001', 'KS 1992-002', 'KS 1994-001', 'KS 1994-br-001', 'KS 1994-br-004', 'KS 1995-001', 'KS 1995-003-', 'KS 1995-004', 'KS 1996-001', 'KS 1996-002', 'KS 1996-003', 'KS 1996-004', 'KS 1997-01', 'KS 1998-001', 'KS 1998-002', 'KS 1998-003', 'KS 1999-002', 'KS 1999-003', 'KS 1999-004', 'ks-1999-005', 'KS 1999-006', 'KS 1999-007', 'KS 1999-008', 'KS 2000-001', 'KS 2000-002', 'KS 2000-003', 'KS 2000-004', 'KS 2000-005', 'KS 2000-007', 'KS 2000-008', 'KS 2001-001', 'KS 2001-002', 'KS 2001-003', 'KS 2001-004', 'KS 2001-005', 'KS 2003-002', 'KS 2004-001', 'KS 2005-001', 'KS 2006-006', 'KS 2006-br-001', 'KS 2008-001', 'KS 2009-001', 'KS 2010-001', 'KS 2010-002', 'KS 2011-001', 'KS 2012-001', 'KS 2014-003', 'KS 202', 'KS 206', 'KS 207', 'KS 208', 'KS 209', 'KS 210', 'KS 213', 'KS 216', 'KS 221', 'KS 222', 'KS 223', 'KS 224', 'KS 225', 'KS 225a', 'KS 226', 'KS 227', 'KS 228', 'KS 229', 'KS 230', 'KS 237', 'KS 239', 'KS 240', 'KS 241', 'KS 243', 'KS 244', 'KS 245', 'KS 246', 'KS 247', 'KS 248', 'KS 249', 'KS 250', 'KS 252', 'KS 254', 'KS 255', 'KS 256', 'KS 258', 'KS 266', 'KS 276', 'KS 281', 'KS 282', 'KS 283', 'KS 284', 'KS 285', 'KS geen-nummer-02', 'KS geen-nummer', 'KS HesHuizen', 'KS Hulk', 'KS Springer']


CREATE_NEW = False
TIME_LIMIT = False
UPLOAD_IMAGES = False
UPDATE_TRANSLATIONS = False

#if books change shelf_mark in CORE dict
#if Kunst do not include content.person.name
PORTAL_TYPE = "Object"
OBJECT_TYPE = "books"
IMPORT_TYPE = "import"
TYPE_IMPORT_FILE = "total"


#
# Utils - Options - Validations
#
SUPPORTED_ENV = ['dev', 'prod', 'sync']
WEBSITE_TEXT = ['WEBTEXT', 'website text Dutch', 'website-tekst', 'texte site web', 'Website-Text']

FOLDER_PATHS = {
    "coins": "nl/collectie/munten-en-penningen",
    "fossils": "nl/collectie/fossielen-en-mineralen",
    "kunst": "nl/collectie/kunst",
    "instruments": "nl/collectie/instrumenten",
    "books": "nl/collectie/boeken"
}

IMAGE_FIX = ['8011975', '8011976', '8011977', '8011978', '8011979', '8011980', '8011981', '8011982', '8011983', '8011984', '8011985', '8011986', '8011987', '8011988', '8011989', '8011990', '8011991', '8011992', '8011993', '8011994', '8011995', '8011996', '8011997', '8011998', '8011999', '8012000', '8012001', '8012002', '8012003', '8012004', '8012005', '8012006', '8012007', '8012008', '8012009', '8012010', '8012011', '8012012', '8012013', '8012014', '8012015', '8012016', '8012017', '8012018', '8012019', '8012020', '8012021', '8012022', '8012023', '8012024', '8012025', '8012026', '8012028', '8012029', '8012030', '8012032', '8012033', '8012034', '8012035', '8012036', '8012037', '8012038', '8012039', '8012040', '8012041', '8012042', '8012043', '8012044', '8012045', '8012046', '8012047', '8012048', '8012050', '8012051', '8012052', '8012053', '8012054', '8012055', '8012057', '8012058', '8012059', '8012060', '8012061', '8012062', '8012063', '8012064', '8012066', '8012067', '8012068', '8012069', '8012070', '8012071', '8012072', '8012073', '8012074', '8012075', '8012077', '8012078', '8012080', '8012081', '8012082', '8012083', '8012084', '8012085', '8012086', '8012087', '8012089', '8012090', '8012095', '8012096', '8012097', '8012099', '8012100', '8012101', '8012102', '8012104', '8012105', '8012106', '8012113', '8012115', '8012116', '8012117', '8012118', '8012119', '8012122', '8012123', '8012124', '8012125', '8012126', '8012127', '8012128', '8012129', '8012130', '8012132', '8012133', '8012134', '8012135', '8012136', '8012137', '8012139', '8012140', '8012141', '8012142', '8012143', '8012144', '8012145', '8012146', '8012147', '8012148', '8012149', '8012150', '8012151', '8012152', '8012153', '8012154', '8012155', '8012156', '8012157', '8012159', '8012160', '8012161', '8012163', '8012164', '8012165', '8012166', '8012167', '8012168', '8012169', '8012170', '8012171', '8012172', '8012173', '8012174', '8012175', '8012176', '8012177', '8012178', '8012179', '8012180', '8012181', '8012182', '8012183', '8012184', '8012185', '8012186', '8012187', '8012188', '8012189', '8012190', '8012193', '8012194', '8012195', '8012196', '8012197', '8012198', '8012199', '8012200', '8012202', '8012203', '8012204', '8012205', '8012206', '8012207', '8012208', '8012209', '8012210', '8012212', '8012213', '8012214', '8012215', '8012216', '8012217', '8012218', '8012219', '8012220', '8012221', '8012222', '8012223', '8012224', '8012226', '8012227', '8012228', '8012229', '8012230', '8012231', '8012232', '8012233', '8012234', '8012235', '8012236', '8012237', '8012238', '8012239', '8012240', '8012241', '8012242', '8012243', '8012244', '8012245', '8012246', '8012247', '8012248', '8012249', '8012250', '8012252', '8012253', '8012254', '8012255', '8012257', '8012258', '8012259', '8012260', '8012261', '8012262', '8012263', '8012264', '8012265', '8012267', '8012268', '8012269', '8012270', '8012271', '8012272', '8012273', '8012274', '8012275', '8012276', '8012277', '8012278', '8012279', '8012280', '8012281', '8012282', '8012283', '8012284', '8012285', '8012286', '8012287', '8012288', '8012289', '8012290', '8012291', '8012292', '8012293', '8012294', '8012295', '8012296', '8012297', '8012298', '8012299', '8012300', '8012301', '8012302', '8012303', '8012304', '8012305', '8012306', '8012307', '8012308', '8012309', '8012310', '8012311', '8012312', '8012313', '8012314', '8012315', '8012316', '8012317', '8012318', '8012319', '8012320', '8012322', '8012323', '8012324', '8012325', '8012326', '8012327', '8012328', '8012329', '8012330', '8012331', '8012332', '8012333', '8012334', '8012335', '8012336', '8012338', '8012339', '8012340', '8012341', '8012342', '8012343', '8012344', '8012345', '8012346', '8012348', '8012349', '8012350', '8012351', '8012352', '8012353', '8012354', '8012355', '8012356', '8012357', '8012358', '8012359', '8012360', '8012361', '8012362', '8012363', '8012364', '8012365', '8012366', '8012367', '8012368', '8012369', '8012370', '8012371', '8012372', '8012373', '8012374', '8012376', '8012377', '8012378', '8012379', '8012380', '8012381', '8012382', '8012383', '8012384', '8012385', '8012386', '8012387', '8012388', '8012389', '8012390', '8012391', '8012392', '8012393', '8012394', '8012395', '8012396', '8012397', '8012398', '8012399', '8012400', '8012401', '8012402', '8012403', '8012404', '8012405', '8012406', '8012407', '8012408', '8012409', '8012410', '8012411', '8012412', '8012413', '8012414', '8012415', '8012416', '8012417', '8012418', '8012419', '8012420', '8012421', '8012422', '8012423', '8012424', '8012425', '8012426', '8012427', '8012428', '8012429', '8012430', '8012431', '8012432', '8012433', '8012434', '8012435', '8012436', '8012437', '8012438', '8012439', '8012440', '8012441', '8012443', '8012444', '8012445', '8012446', '8012447', '8012448', '8012449', '8012450', '8012451', '8012452', '8012453', '8012454', '8012455', '8012456', '8012457', '8012458', '8012460', '8012461', '8012462', '8012463', '8012464', '8012465', '8012466', '8012467', '8012468', '8012469', '8012470', '8012471', '8012472', '8012473', '8012474', '8012475', '8012476', '8012477', '8012478', '8012479', '8012480', '8012481', '8012482', '8012483', '8012484', '8012485', '8012486', '8012487', '8012488', '8012489', '8012490', '8012491', '8012492', '8012493', '8012494', '8012495', '8012496', '8012497', '8012498', '8012499', '8012500', '8012501', '8012502', '8012503', '8012504', '8012506', '8012507', '8012508', '8012509', '8012510', '8012512', '8012513', '8012515', '8012516', '8012518', '8012519', '8012520', '8012521', '8012522', '8012524', '8012525', '8012526', '8012527', '8012528', '8012529', '8012530', '8012531', '8012532', '8012533', '8012534', '8012535', '8012536', '8012537', '8012538', '8012539', '8012540', '8012541', '8012542', '8012543', '8012544', '8012545', '8012546', '8012547', '8012548', '8012549', '8012550', '8012551', '8012552', '8012553', '8012554', '8012555', '8012556', '8012557', '8012559', '8012560', '8012561', '8012562', '8012563', '8012564', '8012565', '8012566', '8012567', '8012568', '8012569', '8012570', '8012571', '8012572', '8012573', '8012574', '8012575', '8012576', '8012577', '8012578', '8012579', '8012580', '8012581', '8012582', '8012583', '8012584', '8012585', '8012586', '8012587', '8012588', '8012589', '8012590', '8012591', '8012592', '8012593', '8012594', '8012595', '8012596', '8012597', '8012598', '8012599', '8012600', '8012601', '8012602', '8012603', '8012604', '8012605', '8012606', '8012607', '8012608', '8012609', '8012610', '8012611', '8012612', '8012613', '8012614', '8012615', '8012616', '8012617', '8012618', '8012619', '8012620', '8012621', '8012622', '8012623', '8012624', '8012625', '8012626', '8012627', '8012628', '8012629', '8012630', '8012631', '8012632', '8012633', '8012634', '8012635', '8012636', '8012637', '8012638', '8012639', '8012640', '8012641', '8012643', '8012644', '8012645', '8012646', '8012647', '8012648', '8012649', '8012650', '8012651', '8012652', '8012653', '8012654', '8012655', '8012656', '8012657', '8012658', '8012659', '8012660', '8012661', '8012662', '8012663', '8012664', '8012665', '8012666', '8012667', '8012668', '8012669', '8012670', '8012671', '8012672', '8012673', '8012674', '8012675', '8012676', '8012677', '8012678', '8012679', '8012680', '8012681', '8012682', '8012683', '8012684', '8012685', '8012686', '8012687', '8012688', '8012689', '8012690', '8012691', '8012692', '8012693', '8012694', '8012695', '8012696', '8012697', '8012698', '8012699', '8012700', '8012701', '8012702', '8012703', '8012704', '8012705', '8012706', '8012707', '8012708', '8012709', '8012710', '8012711', '8012712', '8012713', '8012714', '8012715', '8012716', '8012717', '8012718', '8012719', '8012720', '8012721', '8012722', '8012723', '8012724', '8012725', '8012726', '8012727', '8012728', '8012729', '8012730', '8012731', '8012732', '8012733', '8012734', '8012735', '8012736', '8012737', '8012738', '8012739', '8012740', '8012741', '8012742', '8012743', '8012744', '8012745', '8012746', '8012747', '8012748', '8012749', '8012750', '8012751', '8012752', '8012753', '8012754', '8012755', '8012756', '8012757', '8012758', '8012759', '8012760', '8012761', '8012762', '8012763', '8012764', '8012765', '8012766', '8012767', '8012768', '8012769', '8012770', '8012771', '8012772', '8012773', '8012774', '8012775', '8012776', '8012777', '8012778', '8012779', '8012780', '8012781', '8012782', '8012783', '8012784', '8012785', '8012786', '8012787', '8012788', '8012789', '8012790', '8012791', '8012792', '8012793', '8012794', '8012796', '8012797', '8012799', '8012801', '8012802', '8012803', '8012804', '8012806', '8012807', '8012809', '8012810', '8012812', '8012814', '8012815', '8012816', '8012818', '8012819', '8012820', '8012822', '8012823', '8012824', '8012826', '8012827', '8012828', '8012829', '8012830', '8012831', '8012832', '8012833', '8012834', '8012835', '8012836', '8012837', '8012838', '8012839', '8012840', '8012841', '8012842', '8012843', '8012844', '8012845', '8012846', '8012847', '8012848', '8012849', '8012850', '8012851', '8012852', '8012853', '8012854', '8012855', '8012856', '8012857', '8012858', '8012859', '8012860', '8012861', '8012862', '8012863', '8012864', '8012865', '8012866', '8012867', '8012868', '8012869', '8012870', '8012871', '8012873', '8012874', '8012875', '8012877', '8012878', '8012879', '8012881', '8012884', '8012886', '8012887', '8012889', '8012890', '8012891', '8012892', '8012893', '8012894', '8012895', '8012896', '8012897', '8012898', '8012899', '8012900', '8012901', '8012902', '8012903', '8012904', '8012905', '8012907', '8012908', '8012909', '8012910', '8012911', '8012912', '8012913', '8012914', '8012915', '8012916', '8012917', '8012918', '8012919', '8012920', '8012921', '8012922', '8012923', '8012924', '8012925', '8012926', '8012927', '8012929', '8012930', '8012931', '8012933', '8012934', '8012935', '8012936', '8012937', '8012938', '8012939', '8012940', '8012941', '8012942', '8012943', '8012944', '8012946', '8012947', '8012948', '8012949', '8012950', '8012951', '8012954', '8012955', '8012956', '8012957', '8012958', '8012959', '8012960', '8012961', '8012962', '8012963', '8012964', '8012965', '8012966', '8012967', '8012968', '8012969', '8012970', '8012971', '8012972', '8012973', '8012974', '8012975', '8012976', '8012977', '8012978', '8012979', '8012980', '8012981', '8012982', '8012983', '8012984', '8012985', '8012986', '8012987', '8012988', '8012989', '8012990', '8012991', '8012994', '8012995', '8012996', '8012997', '8012998', '8012999', '8013000', '8013001', '8013002', '8013003', '8013004', '8013006', '8013007', '8013008', '8013009', '8013010', '8013011', '8013013', '8013014', '8013015', '8013016', '8013017', '8013018', '8013020', '8013021', '8013022', '8013023', '8013024', '8013025', '8013026', '8013027', '8013028', '8013029', '8013030', '8013032', '8013033', '8013034', '8013035', '8013036', '8013037', '8013038', '8013039', '8013040', '8013041', '8013042', '8013045', '8013046', '8013047', '8013048', '8013049', '8013050', '8013051', '8013052', '8013053', '8013054', '8013055', '8013057', '8013058', '8013060', '8013061', '8013062', '8013063', '8013064', '8013065', '8013066', '8013067', '8013068', '8013069', '8013070', '8013071', '8013072', '8013073', '8013074', '8013075', '8013076', '8013077', '8013078', '8013079', '8013080', '8013081', '8013082', '8013083', '8013084', '8013085', '8013086', '8013087', '8013088', '8013089', '8013090', '8013091', '8013092', '8013093', '8013094', '8013095', '8013096', '8013097', '8013098', '8013099', '8013100', '8013101', '8013102', '8013103', '8013104', '8013105', '8013106', '8013107', '8013108', '8013109', '8013110', '8013111', '8013112', '8013113', '8013114', '8013115', '8013116', '8013117', '8013118', '8013119', '8013120', '8013121', '8013123', '8013124', '8013125', '8013128', '8013129', '8013131', '8013132', '8013133', '8013134', '8013135', '8013136', '8013137', '8013138', '8013139', '8013140', '8013141', '8013142', '8013143', '8013145', '8013146', '8013147', '8013148', '8013149', '8013150', '8013151', '8013152', '8013153', '8013154', '8013155', '8013156', '8013157', '8013158', '8013159', '8013160', '8013161', '8013162', '8013163', '8013164', '8013165', '8013166', '8013167', '8013168', '8013169', '8013170', '8013171', '8013172', '8013173', '8013174', '8013175', '8013176', '8013177', '8013178', '8013179', '8013180', '8013181', '8013182', '8013183', '8013184', '8013185', '8013186', '8013187', '8013188', '8013189', '8013190', '8013191', '8013192', '8013193', '8013194', '8013195', '8013196', '8013197', '8013199', '8013200', '8013201', '8013202', '8013203', '8013204', '8013205', '8013206', '8013208', '8013209', '8013210', '8013211', '8013212', '8013213', '8013215', '8013216', '8013217', '8013218', '8013219', '8013220', '8013221', '8013222', '8013223', '8013224', '8013225', '8013226', '8013227', '8013228', '8013229', '8013230', '8013231', '8013232', '8013233', '8013234', '8013235', '8013236', '8013237', '8013238', '8013239', '8013240', '8013241', '8013242', '8013243', '8013244', '8013245', '8013246', '8013247', '8013248', '8013249', '8013250', '8013251', '8013252', '8013253', '8013254', '8013255', '8013256', '8013257', '8013258', '8013259', '8013260', '8013261', '8013262', '8013263', '8013264', '8013265', '8013266', '8013267', '8013268', '8013269', '8013270', '8013271', '8013272', '8013273', '8013274', '8013275', '8013276', '8013277', '8013278', '8013279', '8013280', '8013281', '8013282', '8013283', '8013284', '8013285', '8013286', '8013287', '8013288', '8013289', '8013290', '8013291', '8013292', '8013293', '8013294', '8013296', '8013298', '8013299', '8013300', '8013301', '8013302', '8013303', '8013304', '8013306', '8013307', '8013308', '8013309', '8013310', '8013311', '8013312', '8013313', '8013314', '8013315', '8013316', '8013317', '8013318', '8013319', '8013320', '8013321', '8013322', '8013323', '8013324', '8013325', '8013326', '8013327', '8013328', '8013329', '8013330', '8013331', '8013332', '8013333', '8013334', '8013335', '8013336', '8013337', '8013338', '8013339', '8013340', '8013341', '8013342', '8013343', '8013344', '8013345', '8013346', '8013347', '8013348', '8013349', '8013350', '8013351', '8013352', '8013353', '8013354', '8013355', '8013356', '8013357', '8013358', '8013359', '8013360', '8013361', '8013362', '8013363', '8013364', '8013365', '8013366', '8013367', '8013368', '8013369', '8013370', '8013371', '8013372', '8013373', '8013374', '8013375', '8013376', '8013377', '8013378', '8013379', '8013380', '8013381', '8013382', '8013383', '8013447', '8013461', '8013508']

TEST_EXAMPLES = {
    "coins": ['8015607', '8006953', '8000670'],
    "fossils": ['7008516'],
    "kunst": ['336', '37213', '16434'],
    "instruments": ['4000808', '4000678', '4000217', '4000180', '4000383', '4000136'],
    "books": ['12908']
}

RESTRICTIONS = {
    "coins": [],
    "fossils": ['object_type', 'object_production_period', 'object_dating', 'object_dimension'],
    "kunst": ['acquisition_source', 'object_inscription', 'object_descriptions'],
    "instruments":['object_descriptions'],
    "books": []
}

FIELDS_ALLOW_SINGLE_ONLY = ['scientific_name']

VIEW_TYPES = {
    "coins": "double_view",
    "fossils": "view",
    "kunst": "view",
    "instruments":"instruments_view",
    "books":"view"
}

#
# Environment
#
ENV = "prod"
DEBUG = False
RUNNING = True

class Migrator:
    
    def __init__(self, Updater):
        self.updater = Updater
        self.portal_type = PORTAL_TYPE
        self.updater.portal_type = PORTAL_TYPE
        self.object_type = OBJECT_TYPE
        self.updater.RUNNING = RUNNING
        self.updater.DEBUG = DEBUG
        self.updater.CORE = CORE
        self.updater.subfields_types = subfields_types
        self.updater.relation_types = relation_types
        self.log_files_path = LOG_FILES_PATH
        self.images_hd_path = IMAGES_HD_PATH
        self.list_images_in_hd = []
        self.ENV = ENV
        self.UPLOAD_IMAGES = UPLOAD_IMAGES
        self.CREATE_NEW = CREATE_NEW
        self.DEBUG = DEBUG
        self.RUNNING = RUNNING
        self.FOLDER_PATHS = FOLDER_PATHS
        self.CORE = CORE
        self.IMPORT_TYPE = IMPORT_TYPE
        self.subfields_types = subfields_types
        self.relation_types = relation_types
        self.TYPE_IMPORT_FILE = TYPE_IMPORT_FILE
        self.TIME_LIMIT = TIME_LIMIT
        self.VIEW_TYPES = VIEW_TYPES
        self.UPDATE_TRANSLATIONS = UPDATE_TRANSLATIONS

        # Init schema
        self.schema = getUtility(IDexterityFTI, name=self.portal_type).lookupSchema()
        self.fields = getFieldsInOrder(self.schema)

        self.updater.schema = self.schema
        self.updater.fields = self.fields
        self.updater.field_types = {}
        self.updater.datagrids = {}
        self.updater.xml_path = ""
        self.updater.is_tm = True

        self.syncing = False

    ## LOGS
    def log(self, text=""):
        self.updater.log(text)

    def log_images(self, text="", use_timestamp=True):
        if text:
            timestamp = datetime.datetime.today().isoformat()
            text = text.encode('ascii', 'ignore')
            if not use_timestamp:
                final_log = "%s" %(str(text))
            else:
                final_log = "[%s]__%s" %(str(timestamp), str(text))
            
            list_log = final_log.split('__')
            print final_log.replace('__', ' ')
            self.images_wr.writerow(list_log)
        else:
            return True

    def log_status(self, text="", use_timestamp=True):
        self.updater.log_status(text, use_timestamp)

    def error(self, text=""):
        self.updater.error(text)

    def warning(self, text=""):
        self.updater.warning(text)

    def set_core(self, core):
        self.CORE = core
        self.updater.CORE = core
        return True

    def log_created(self, text, use_timestamp=True):
        if self.IMPORT_TYPE == "sync":
            if text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')
                if not use_timestamp:
                    final_log = "%s" %(str(text))
                else:
                    final_log = "[%s]__%s" %(str(timestamp), str(text))
                
                list_log = final_log.split('__')
                self.created_wr.writerow(list_log)
            else:
                return True

    def log_deleted(self, text, use_timestamp=True):
        if self.IMPORT_TYPE == "sync":
            if text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')
                if not use_timestamp:
                    final_log = "%s" %(str(text))
                else:
                    final_log = "[%s]__%s" %(str(timestamp), str(text))
                
                list_log = final_log.split('__')
                self.deleted_wr.writerow(list_log)
            else:
                return True

    def init_log_files(self):

        self.list_images_in_hd = glob.glob(IMAGES_HD_PATH[self.object_type][self.ENV]['path'])        
        self.error_path = self.get_log_path('error', self.ENV)
        self.warning_path = self.get_log_path('warning', self.ENV)
        self.status_path = self.get_log_path('status', self.ENV)
        self.log_images_path = self.get_log_path('images', self.ENV)

        read_mode = "w+"
        if self.IMPORT_TYPE == 'sync':
            read_mode = "a"

        self.error_log_file = open(self.error_path, read_mode)
        self.warning_log_file = open(self.warning_path, read_mode)
        self.status_log_file = open(self.status_path, read_mode)
        self.images_log_file = open(self.log_images_path, read_mode)

        self.error_wr = csv.writer(self.error_log_file, quoting=csv.QUOTE_ALL)
        self.warning_wr = csv.writer(self.warning_log_file, quoting=csv.QUOTE_ALL)
        self.status_wr = csv.writer(self.status_log_file, quoting=csv.QUOTE_ALL)
        self.images_wr = csv.writer(self.images_log_file, quoting=csv.QUOTE_ALL)

        self.updater.error_log_file = self.error_log_file
        self.updater.warning_log_file = self.warning_log_file
        self.updater.status_log_file = self.status_log_file

        self.updater.error_wr = self.error_wr
        self.updater.warning_wr = self.warning_wr
        self.updater.status_wr = self.status_wr

        if self.IMPORT_TYPE == "sync":
            self.log_created_path = self.get_log_path('created', self.ENV)
            self.created_log_file = open(self.log_created_path, read_mode)
            self.created_wr = csv.writer(self.created_log_file, quoting=csv.QUOTE_ALL)
            
            self.log_deleted_path = self.get_log_path('deleted', self.ENV)
            self.deleted_log_file = open(self.log_deleted_path, read_mode)
            self.deleted_wr = csv.writer(self.deleted_log_file, quoting=csv.QUOTE_ALL)


    ## GETS
    def get_priref(self, xml_record):
        if xml_record.find('priref') != None:
            return xml_record.find('priref').text
        else:
            return ""

    def get_log_path(self, log_type='error', env="dev"):
        path = ""

        if self.ENV in SUPPORTED_ENV:
            timestamp = datetime.datetime.today().isoformat()
            if self.IMPORT_TYPE != 'sync':
                path = self.log_files_path[self.IMPORT_TYPE][log_type][self.ENV] % (self.portal_type, timestamp, self.object_type)
            else:
                path = self.log_files_path[self.IMPORT_TYPE][log_type][self.ENV]

        else:
            print "#### Environment '%s' for log file is unsupported. ####" %(str(server))

        return path

    def get_collection(self):
        collection_xml = CONTENT_TYPES_PATH[self.portal_type][self.object_type][self.ENV][self.TYPE_IMPORT_FILE]
        self.collection, self.xml_root = self.updater.api.get_tm_collection(collection_xml)

        self.updater.collection = self.collection
        self.updater.xml_root = self.xml_root

    ## FINDS
    def find_object_by_priref(self, priref):
        #return api.content.get(path='/nl/collectie/instrumenten-new/fk-0014-projectile-trolley')
        
        if priref:
            brains = self.updater.api.portal_catalog(object_priref=priref, portal_type="Object") 
            for brain in brains:
                if brain:
                    obj = brain.getObject()
                    if getattr(obj, 'priref', None) == priref:
                        if self.FOLDER_PATHS[self.object_type] in obj.absolute_url():
                            return obj
                        else:
                            pass
                    else:
                        return None
            return None
        else:
            return None

    def valid_field(self, name):
        if RESTRICTIONS[self.object_type]:
            if name in RESTRICTIONS[self.object_type]:
                return False
            else:
                return True
        else:
            return True
    
    ## CORE
    def write(self, xml_path, xml_element, plone_object, priref):

        plone_fieldname = self.updater.check_dictionary(xml_path)
        
        if plone_fieldname:
            plone_fieldroot = plone_fieldname.split('-')[0]
            has_field = hasattr(plone_object, plone_fieldroot)
           
            if has_field:
                current_value = getattr(plone_object, plone_fieldroot)
                field_type = self.updater.get_type_of_field(plone_fieldroot)

                if self.valid_field(plone_fieldroot):
                    value = self.transform_all_types(xml_element, field_type, current_value, xml_path, plone_fieldname)
                else:
                    value = current_value

                self.updater.setattribute(plone_object, plone_fieldroot, field_type, value)
            else:
                self.error("Field not available in Plone object: %s" %(plone_fieldroot))

        ## Ignored tags
        elif plone_fieldname == "":
            self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))

        else:
            if ".lref" in xml_path:
                self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))
            else:
                if xml_path == "":
                    xml_path = xml_element.tag
                    if (xml_path == "record") or ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(priref, xml_path, xml_element.text))
                else:
                    if ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(priref, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(priref, xml_path, xml_element.text))

        return True

    def update(self, xml_record, plone_object, priref):
        for element in xml_record.iter():
            xml_path = self.updater.get_xml_path(element)
            self.xml_path = xml_path
            self.write(xml_path, element, plone_object, priref)
        return True

    # Handle datagridfield 
    def handle_datagridfield(self, current_value, xml_path, xml_element, plone_fieldname):
        subfield = self.updater.get_subfield(plone_fieldname)
        plone_fieldroot = plone_fieldname.split('-')[0]
        subfield_type = self.updater.get_type_of_subfield(xml_path)

        if not self.updater.datagrids[plone_fieldroot]:
            current_value = []
            self.updater.datagrids[plone_fieldroot] = True
        else:
            self.updater.datagrids[plone_fieldroot] = True

        if current_value == None:
            current_value = []

        length = len(current_value)
        field_value = None

        if subfield:
            if length:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.updater.update_dictionary_new(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
            else:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.updater.create_dictionary(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
        else:
            self.error("Badly formed CORE dictionary for repeatable field: %s" %(plone_fieldname))

        return field_value

    def transform_all_types(self, xml_element, field_type, current_value, xml_path, plone_fieldname):
        if plone_fieldname in FIELDS_ALLOW_SINGLE_ONLY:
            if current_value not in NOT_ALLOWED:
                return current_value

        # Text
        if field_type == "text":
            return self.updater.api.trim_white_spaces(xml_element.text)

        elif field_type == "rich-text":
            try:
                current_val = current_value.raw
            except:
                current_val = ""

            parent = xml_element.getparent()
            if parent is not None:

            	if parent.find('label.source') != None:
            		source = parent.find('label.source').text
            		if source not in ALLOWED_SOURCES:
            			return current_value

                if parent.find('label.type') != None:
                    if parent.find('label.type').get('option') in WEBSITE_TEXT:
                        text = xml_element.text
                        text = current_val + "<br>" + text
                        text = text.replace('\n','<br />')
                        value = RichTextValue(text, 'text/html', 'text/html')
                        return value
                    elif parent.find('label.type').find('value') != None:
                        if parent.find('label.type').find('value').text in WEBSITE_TEXT:
                            text = xml_element.text
                            text = current_val + "<br>" + text
                            text = text.replace('\n','<br />')
                            value = RichTextValue(text, 'text/html', 'text/html')
                            return value
                    elif parent.find('label.type').find('text') != None:
                        if parent.find('label.type').find('text').text in WEBSITE_TEXT:
                            text = xml_element.text
                            text = current_val + "<br>" + text
                            text = text.replace('\n','<br />')
                            value = RichTextValue(text, 'text/html', 'text/html')
                            return value
                    else:
                        text = current_val.replace('\n','<br />')
                        value = RichTextValue(text, 'text/html', 'text/html')
                else:
                    text = current_val.replace('\n','<br />')
                    value = RichTextValue(current_val, 'text/html', 'text/html')

                text = current_val.replace('\n','<br />')
                return RichTextValue(text, 'text/html', 'text/html')
            else:
                text = current_val.replace('\n','<br />')
                return RichTextValue(text, 'text/html', 'text/html')

        elif field_type == "datagridfield":
            value = self.handle_datagridfield(current_value, xml_path, xml_element, plone_fieldname)
        # Unknown
        else:
            value = None
            self.error("Unkown type of field for fieldname %s" %(plone_fieldname))

        return value

    def create_object(self, priref, xml_record, folder_path='nl/'):
        created_object = None

        folder_path = folder_path
        container = self.updater.api.get_folder(folder_path)

        title = self.updater.get_title_by_type(xml_record)
        object_number = self.updater.get_required_field_by_type(xml_record, self.object_type)
        if not title and object_number:
            #fallback object number
            title = object_number
        elif not title and not object_number:
            #fallback priref
            title = priref
        elif not title:
            title = ""
        else:
            title = title


        dirty_id = "%s %s"%(str(object_number.encode('ascii', 'ignore')), str(title.encode('ascii', 'ignore')))
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
        if normalized_id not in container:
            container.invokeFactory(
                type_name=self.portal_type,
                id=normalized_id,
                title=title
            )

            created_object = container[str(normalized_id)]
            setattr(created_object, 'priref', priref)
        else:
            created_object = container[normalized_id]

        return created_object

    def convert_image_name(self, image_name):
        #
        # TMNK_06362-v.jpg -> TMNK 06362a.jpg
        # TMNK_06362-k.jpg -> TMNK 06362b.jpg 
        #

        if self.object_type != 'coins':
            return image_name

        if "TMNK_" in image_name:
            new_image_name = image_name.replace('TMNK_', 'TMNK ')
            return new_image_name

        # verify if convertible
        if ("-v.jpg" in image_name) or ("-k.jpg" in image_name):
            pass
        else:
            return image_name

        new_image_name = ""

        # Convert to A
        if "-v.jpg" in image_name:
            new_image_name = image_name.replace("-v.jpg", "a.jpg")
            copy_image_name = new_image_name
            if "aa.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('aa.jpg', 'a.jpg')
            elif "ba.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('ba.jpg', 'a.jpg')


            if 'TMNK_' in new_image_name:
                final_image_name = copy_image_name.replace('TMNK_', 'TMNK ')
                return final_image_name
            else:
                return image_name

        # Convert to B
        elif ("-k.jpg" in image_name):
            new_image_name = image_name.replace("-k.jpg", "b.jpg")
            copy_image_name = new_image_name

            if "ab.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('ab.jpg', 'b.jpg')
            elif "bb.jpg" in new_image_name:
                copy_image_name = new_image_name.replace('bb.jpg', 'b.jpg')

            if 'TMNK_' in new_image_name:
                final_image_name = copy_image_name.replace('TMNK_', 'TMNK ')
                return final_image_name
            else:
                return image_name
        else:
            return image_name

        if new_image_name:
            return new_image_name
        else:
            return image_name

    def find_image_in_hd(self, image_name):
        for image in self.list_images_in_hd:
            if image_name.lower() in image.lower():
                return image
        return None

    def find_images_in_hd(self, image_name):
        images = []
        for image in self.list_images_in_hd:
            if image_name.lower() in image.lower():
                images.append(image)
        return images

    def add_image(self, image_name, path, priref, plone_object, crop=False, replace=False):
        if path:
            if 'slideshow' in plone_object:
                container = plone_object['slideshow']
                dirty_id = image_name
                normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

                if normalized_id not in container:
                    try:
                        image_file = open(path, "r")
                        image_data = image_file.read()
                        try:
                            img = NamedBlobImage(
                                data=image_data
                            )
                            image_file.close()
                            container.invokeFactory(type_name="Image", id=normalized_id, title=image_name, image=img)

                            if crop:
                                img_obj = container[normalized_id]
                                autoCropImage(img_obj)

                            self.log_status("! STATUS !__Created image [%s] for priref: %s" %(image_name, priref))
                        except:
                            self.log_images("%s__%s__%s"%(priref, image_name, "Error while creating Image content type."))
                            pass
                    except:
                        self.log_images("%s__%s__%s"%(priref, path, "Cannot open image file from HD."))
                        pass
                else:
                    if replace:
                        image_file = open(path, "r")
                        image_data = image_file.read()

                        obj_image = container[normalized_id]
                        img = NamedBlobImage(
                            data=image_data
                        )
                        image_file.close()
                        setattr(obj_image, 'image', img)

                        if crop:
                            autoCropImage(obj_image)

                        self.log_status("! STATUS !__Image [%s] got replaced for priref: %s" %(image_name, priref))
                    else:
                        self.log_images("%s__%s__%s"%(priref, path, "Image already exists in website."))

            else:
                self.log_images("%s__%s__%s"%(priref, image_name, "Cannot create image in Object. Slideshow folder is not found."))
        else:
            self.log_images("%s__%s__%s"%(priref, image_name, "Cannot find image in HD."))

    def upload_images(self, priref, plone_object, xml_record):

        if self.object_type == "instruments":
            self.upload_multiple_images(priref, plone_object, xml_record)
            return True
        
        if xml_record.findall('Reproduction') != None:
            for reproduction in xml_record.findall('Reproduction'):
                if reproduction.find('reproduction.reference') != None:
                    if reproduction.find('reproduction.reference').find('reference_number') != None:
                        reference_number = reproduction.find('reproduction.reference').find('reference_number').text
                        if reference_number:
                            reference_split = reference_number.split("\\")
                            if reference_split:
                                image_name = reference_split[-1]
                                new_image_name = self.convert_image_name(image_name)
                                path = self.find_image_in_hd(new_image_name)
                                self.add_image(new_image_name, path, priref, plone_object)
                            else:
                                path = self.find_image_in_hd(reference_number)
                                self.add_image(reference_number, path, priref, plone_object)
                        else:
                            self.log_images("%s__%s__%s"%(priref, '', "Cannot find image reference in XML."))
                    else:
                        self.log_images("%s__%s__%s"%(priref, '', "Cannot find image reference in XML."))

        return True


    def upload_multiple_images(self, priref, plone_object, xml_record):

        object_number = getattr(plone_object, 'object_number', None)

        path = "%s%s/*.jpg" % (self.images_hd_path[self.object_type][self.ENV]['path'], object_number)

        list_images = glob.glob(path)

        if list_images:
            for index, img in enumerate(list_images):
                crop = False
                if index == 0:
                    crop = True
                img_split = img.split("/")
                image_name = img_split[-1]
                self.add_image(image_name, img, priref, plone_object, crop)
        else:
            self.log_images("%s__%s__%s"%(priref, path.replace('*.jpg', ''), "Cannot find folder in HD."))

        #for img in list_images:
        #    print img

        return True

    def create_description_field(self, plone_object):
        description = ""
        authors = getattr(plone_object,'creator', None)
        periods = getattr(plone_object,'object_dating', None)
        
        if authors:
            field = authors[0]
            author = self.updater.utils.create_production_field(field)
        else:
            author = ""

        if periods:
            field = periods[0]
            period = self.updater.utils.create_prod_dating_field(field)
        else:
            period = ""

        if author and period:
            description = "%s, %s" %(author, period)
        elif author:
            description = "%s" %(author)
        elif period:
            description = "%s" %(period)
        
        return description

    def generate_special_fields(self, plone_object, xml_record):
        object_title = getattr(plone_object, 'title', '')
        

        if self.object_type == 'books':
            if xml_record.find('Title') != None:
                if xml_record.find('Title').find('lead_word') != None:
                    lead_word = ""
                    if self.IMPORT_TYPE == "sync":
                        if xml_record.find('Title').find('lead_word').find('value') != None:
                            lead_word = xml_record.find('Title').find('lead_word').find('value').text
                    else:
                        lead_word = xml_record.find('Title').find('lead_word').text

                    if lead_word:
                        new_title = "%s %s" %(lead_word, object_title)
                        setattr(plone_object, 'title', new_title)

        elif self.object_type == "fossils":
            title = self.updater.get_title_by_type(xml_record)
            object_number = self.updater.get_required_field_by_type(xml_record, self.object_type)
            if not title and object_number:
                #fallback object number
                title = object_number
            elif not title and not object_number:
                #fallback priref
                title = priref
            elif not title:
                title = ""
            else:
                title = title

            setattr(plone_object, 'title', title)

        object_title = getattr(plone_object, 'title', '')
        setattr(plone_object, 'object_title', object_title)
        description = self.create_description_field(plone_object)
        setattr(plone_object, 'description', description)

        return True

    def import_record(self, priref, plone_object, xml_record, create_if_not_found=True):
            if plone_object:
                self.updater.generate_field_types()
                self.updater.empty_fields(plone_object, True)
                self.update(xml_record, plone_object, priref)
                self.updater.fix_all_choices(plone_object)
                self.generate_special_fields(plone_object, xml_record)

                plone_object.reindexObject() 
                is_new = False
                if not create_if_not_found:
                    is_new = True
                return True, is_new
            else:
                if self.CREATE_NEW:
                    if create_if_not_found:
                        object_created = self.create_object(priref, xml_record, self.FOLDER_PATHS[self.object_type])

                        obj_layout = self.VIEW_TYPES[self.object_type]
                        layout = object_created.getLayout()
                        if layout != obj_layout:
                            object_created.setLayout(obj_layout)

                        imported, is_new = self.import_record(priref, object_created, xml_record, False)
                        return object_created, True
                    else:
                        self.error("%s__ __Object is not found on Plone with priref."%(str(priref))) 
                        return False, False
                else:
                    return False, False

    def update_existing(self, priref, plone_object, xml_record):
        self.updater.generate_field_types()
        self.updater.empty_fields(plone_object, True)
        self.update(xml_record, plone_object, priref)
        self.updater.fix_all_choices(plone_object)
        self.generate_special_fields(plone_object, xml_record)

        plone_object.reindexObject()

        return plone_object

    def update_object_translation(self, priref, plone_object, xml_record):
        # get translation
        if ITranslationManager(plone_object).has_translation('en'):
            object_translated = ITranslationManager(plone_object).get_translation('en')
            self.update_existing(priref, object_translated, xml_record)
            self.log_status("! STATUS !__Updated translation")
            self.log_status("! STATUS !__URL: %s" %(object_translated.absolute_url()))
        else:
            pass

        return True


    def create_new_object(self, priref, plone_object, xml_record):
        if self.CREATE_NEW:
            object_created = self.create_object(priref, xml_record, self.FOLDER_PATHS[self.object_type])
            obj_layout = self.VIEW_TYPES[self.object_type]
            layout = object_created.getLayout()
            if layout != obj_layout:
                object_created.setLayout(obj_layout)

            self.update_existing(priref, object_created, xml_record)
            return object_created
        else:
            return None

    def time_limit_check(self):
        if self.TIME_LIMIT:
            now = datetime.datetime.now()
            if now.time() > datetime.time(6):
                return False
        else:
            return True

    def time_limit_stop(self, curr, total, priref):
        # LOG
        msg = "! STATUS ! Script stopped after time limit. [%s] %s / %s" %(str(priref), str(curr), str(total))

        self.log_status("! STATUS !__Script stopped after time limit. [%s] %s / %s" %(str(priref), str(curr), str(total)))

        # Send email
        api.portal.send_email(
            recipient='andre@itsnotthatkind.org',
            sender='andre@intk.com',
            subject="TM - Import status",
            body=msg
        )

        self.error_log_file.close()
        self.warning_log_file.close()
        self.status_log_file.close()

        transaction.commit()
        return True

    def valid_priref(self, priref):
        if self.ENV in ['dev']:
            if priref in TEST_EXAMPLES[self.object_type] and self.TYPE_IMPORT_FILE == 'single':
                return True
            elif self.TYPE_IMPORT_FILE == 'total':
                return True
            else:
                return False
        elif self.ENV in ['prod']:
            if priref not in TEST_EXAMPLES[self.object_type] or self.TYPE_IMPORT_FILE == 'total':
                return True
            elif self.TYPE_IMPORT_FILE == 'single':
                return True
            else:
                return False
        else:
            return True

        return False

    def generate_special_translated_fields(self, obj, xml_record):

        # Check body text - label.text
        for label in xml_record.findall('Label'):
            if label.find('label.text') != None:
                field = label.find('label.text')
                parent = label
                if parent.find('label.type') != None:
                    if parent.find('label.type').find('text') != None:
                        if parent.find('label.type').find('text').text in ['website text ENG', 'website-tekst ENG']:
                            text = field.text
                            text = text.replace('\n','<br />')
                            value = RichTextValue(text, 'text/html', 'text/html')
                            setattr(obj, 'text', value)
                    elif parent.find('label.type').find('value') != None:
                        if parent.find('label.type').find('value').text in ['website text ENG', 'website-tekst ENG']:
                            text = field.text
                            text = text.replace('\n','<br />')
                            value = RichTextValue(text, 'text/html', 'text/html')
                            setattr(obj, 'text', value)

        # Check title.translation
        if xml_record.find('title.translation') != None:
            translation = xml_record.find('title.translation').text
            if translation:
                setattr(obj, 'title', translation)
                setattr(obj, 'object_title', translation)

                obj.reindexObject(idxs=['Title'])

        return True

    def add_images_translation(self, container):
        curr = 0
        for _id in container:
            curr += 1
            obj = container[_id]
            if obj.portal_type == 'Image':
                if not ITranslationManager(obj).has_translation('en'):
                    ITranslationManager(obj).add_translation('en')
                    img_translated = ITranslationManager(obj).get_translation('en')
                    setattr(img_translated, 'image', getattr(obj, 'image', None))
                    setattr(img_translated, 'title', getattr(obj, 'title', ''))
                    
                    if self.object_type == "instruments":
                        img_translated.reindexObject()
                    if curr == 1:
                        addCropToTranslation(obj, img_translated)
                else:
                    # has translation - do not translate
                    pass
            else:
                if not ITranslationManager(obj).has_translation('en'):
                    ITranslationManager(obj).add_translation('en')
                    obj_translated = ITranslationManager(obj).get_translation('en')
                    setattr(obj_translated, 'title', getattr(obj, 'title', None))
                else:
                    # has translation - do not translate
                    pass

        return True

    def generate_contents_translation(self, obj):

        # get slideshow
        if 'slideshow' in obj:
            slideshow = obj['slideshow']

            if not ITranslationManager(slideshow).has_translation('en'):
                ITranslationManager(slideshow).add_translation('en')
                slideshow_trans = ITranslationManager(slideshow).get_translation('en')
                setattr(slideshow_trans, 'title', getattr(slideshow, 'title', ''))
                slideshow_trans.portal_workflow.doActionFor(slideshow_trans, "publish", comment="Slideshow published")
                self.add_images_translation(slideshow)

            else:
                self.add_images_translation(slideshow)
                
        else:
            # Do not translate contents
            pass

        return True

    def copy_original_to_translated(self, plone_object, translated_object):
        original_fields = {}
        original_fields['title'] = getattr(plone_object, 'title', '')
        original_fields['description'] = getattr(plone_object, 'description', '')

        for name, field in self.fields:
            original_f = getattr(plone_object, name, '')
            if original_f:
                original_fields[name] = original_f

        for key, value in original_fields.iteritems():
            setattr(translated_object, key, value)

        layout = plone_object.getLayout()
        translated_object.setLayout(layout)

        return True

    def create_translations(self):
        self.init_log_files()
        self.get_collection()

        curr, limit = 0, 0
        total = len(list(self.collection))
        
        for xml_record in list(self.collection):
            try:
                transaction.begin()
                curr += 1
                priref = self.get_priref(xml_record)
                if priref:
                    # Create translation
                    plone_object = self.find_object_by_priref(priref)
                    if plone_object:
                        # Check translation
                        if not ITranslationManager(plone_object).has_translation('en'):
                            try:
                                ITranslationManager(plone_object).add_translation('en')
                                translated_object = ITranslationManager(plone_object).get_translation('en')

                                # Copy fields from original object
                                self.copy_original_to_translated(plone_object, translated_object)
                                self.generate_contents_translation(plone_object)
                                self.generate_special_translated_fields(translated_object, xml_record)
                                translated_object.reindexObject()

                                self.log_status("! STATUS !__Translation created [%s] %s / %s" %(str(priref), str(curr), str(total)))
                                self.log_status("! STATUS !__URL: %s" %(str(translated_object.absolute_url())))
                            except Exception, e:
                                self.error("%s__ __Translation for object failed - %s"%(str(priref), str(e))) 
                                raise
                        else:
                            self.log_status("! STATUS !__Translation for object already created. %s"%(str(priref))) 
                    else:
                        self.error("%s__ __Object is not found on Plone with priref."%(str(priref))) 
                else:
                    self.error("%s__ __Cannot find priref in XML record"%(str(curr)))
                transaction.commit()
            except Exception, e:
                transaction.abort()
                self.error(" __ __An unknown exception ocurred. %s" %(str(e)))
                self.error_log_file.close()
                self.warning_log_file.close()
                self.status_log_file.close()
                self.images_log_file.close()
                raise

        return True

    ## UTILS

    def move_kunst(self, target, condition, collection):
        container = self.updater.api.get_folder('nl/collectie/kunst-new')
        col_total = len(list(collection))
        total = 0
        curr = 0
        #target = 'nl/collectie/tekening-new'

        target_folder = self.updater.api.get_folder(target)

        
        for _id in container:
            obj = container[_id]

            obj_name = getattr(obj, 'object_type', None)
            if obj_name == condition:
                total += 1
                self.updater.api.move_obj_folder(obj, target_folder)           
                self.log_status("! STATUS !__Moved object %s" %(obj.absolute_url()))

                if total >= 100:
                    return True

        """for xml_record in list(collection):
                                    transaction.begin()
                                    curr += 1
                                    for obj_name in xml_record.findall('Object_name'):
                                        if obj_name.find('object_name') != None:
                                            if obj_name.find('object_name').find('term') != None:
                                                term = obj_name.find('object_name').find('term').text
                                                if term == condition:
                                                    
                                                    priref = xml_record.find('priref').text
                                                    plone_object = self.find_object_by_priref(priref)
                                                    if plone_object:
                                                        self.updater.api.move_obj_folder(plone_object, target_folder)
                                                        self.log_status("! STATUS !__Moved object [%s] %s / %s" %(priref, curr, col_total))
                                                        total += 1
                                                    else:
                                                        self.log_status("! STATUS !__Cannot find object with priref [%s] %s / %s" %(priref, curr, col_total))
                        
                                                    if total >= 100:
                                                        transaction.commit()
                                                        return True
                                                    break
                                    transaction.commit()"""

        print "Total '%s':" %(condition)
        print total

        return True

    def fix_fossils_images(self):
        path = 'nl/collectie/fossielen-en-mineralen-new'

        folder = self.updater.api.get_folder(path)

        for _id in folder:
            obj = folder[_id]
            object_number = getattr(obj, 'object_number', None)
            if object_number:
                alternative = object_number
                if "F " in object_number:
                    alternative = alternative.replace("F ", "")

                for number in FOSSILS_FIX:
                    if object_number.lower() in number.lower():
                #if (object_number.lower() in [number.lower() for number in FOSSILS_FIX]) or (alternative.lower() in [number.lower() for number in FOSSILS_FIX]):
                        image_name = "%s.jpg" %(object_number.lower())
                        image_path = self.find_image_in_hd(image_name)
                        self.add_image(image_name, image_path, getattr(obj, 'priref', ''), obj, True)
                        break

        return True 

    def fix_kunst_images(self):
        path = 'nl/collectie/kunst-new'

        folder = self.updater.api.get_folder(path)

        for _id in folder:
            obj = folder[_id]
            object_number = getattr(obj, 'object_number', None)
            if object_number:
                for number in KUNST_FIX:
                    if object_number.lower() in number.lower():
                        image_name = "%s.jpg" %(object_number.lower())
                        image_path = self.find_image_in_hd(image_name)
                        self.add_image(image_name, image_path, getattr(obj, 'priref', ''), obj, True)
                        break

        return True 

    def fix_paintings_images(self):
        found_paintings = []

        path = 'nl/collectie/kunst-new'

        folder = self.updater.api.get_folder(path)

        for _id in folder:
            obj = folder[_id]
            object_number = getattr(obj, 'object_number', None)
            if object_number:
                for number in PAINTINGS_FIX:
                    if object_number.lower() in number.lower():
                        found_paintings.append(object_number)
                        image_name = "%s.jpg" %(object_number.lower())
                        new_image_name = image_name.replace("ks ", "ks-")
                        image_path = self.find_image_in_hd(new_image_name)
                        self.add_image(new_image_name, image_path, getattr(obj, 'priref', ''), obj, True, True)
                        break

        print "Found paintings: [%s]" %(str(len(found_paintings)))
        print found_paintings

        return True 

    def reindex_directory(self, path):
        folder = self.updater.api.get_folder(path)
        total = len(folder)
        curr = 0

        for _id in folder:
            curr += 1
            obj = folder[_id]
            obj.reindexObject()
            self.log_status("! STATUS !__Reindexed %s / %s" %(str(curr), str(total)))

        return True

    def fix_fossil_name(self, obj):

        common_name = getattr(obj, 'common_name', '')

        if common_name:
            setattr(obj, 'title', common_name)
            obj.reindexObject(idxs=['Title'])

        return True

    def rename_all_fossils(self):

        folder = self.updater.api.get_folder("nl/collectie/fossielen-en-mineralen-new")
        total = len(folder)
        curr = 0

        for _id in folder:
            try:
                transaction.begin()
                print "Renaming %s / %s" %(str(curr), str(total))
                curr += 1
                obj = folder[_id]

                new_id = ""
                object_number = getattr(obj, 'object_number', '')
                if object_number not in NOT_ALLOWED:
                    new_id = "%s" %(object_number)

                scientific_name = getattr(obj, 'scientific_name', '')
                if scientific_name not in NOT_ALLOWED:
                    new_id = "%s %s" %(scientific_name, new_id)

                common_name = getattr(obj, 'common_name', '')
                if common_name not in NOT_ALLOWED:
                    new_id = "%s %s" %(common_name, new_id)

                if common_name:
                    setattr(obj, 'title', common_name)
                    obj.reindexObject(idxs=['Title'])

                dirty_id = new_id.strip()
                normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

                api.content.rename(obj=obj, new_id=normalized_id, safe_id=True)
                print "Renamed [ %s ]" %(obj.absolute_url()) 
                transaction.commit()
            except:
                transaction.abort()
                pass

        return True

    def fix_all_images(self):

        folder = self.updater.api.get_folder("nl/collectie/kunst-new")
        total = len(folder)
        curr = 0

        for _id in folder:
            try:
                transaction.begin()
                curr += 1
                obj = folder[_id]
                priref = getattr(obj, 'priref', '')
                object_number = getattr(obj, 'object_number', '')

                print "------ [ %s ] ------ %s / %s" %(object_number, curr, total)

                slideshow = obj['slideshow']

                # Get object reproduction
                reproduction_reference = getattr(obj, 'object_reproduction_reference', '')

                if reproduction_reference:
                    for reference in reproduction_reference:
                        reference_image_name = reference['reference']
                        image_name = reference_image_name.split("\\")[-1]
                        images_found = self.find_images_in_hd(image_name)
                        if len(images_found):
                            print "Several images found."
                            # Several images found
                            # replace image with exact same name
                            # check image with exact same name
                            path_to_replace = None
                            ref_to_replace = None
                            for ref in images_found:
                                ref_name = ref.split("/")[-1]
                                if ref_name.lower() == image_name.lower():
                                    # Found image
                                    path_to_replace = ref
                                    ref_to_replace = ref_name
                                    break
                            
                            if not path_to_replace:
                                print "Image with exact same name was not found - delete current created image"
                                # delete current created image
                                current_img_name = image_name
                                dirty_id = current_img_name
                                normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

                                if normalized_id in slideshow:
                                    img = slideshow[normalized_id]
                                    # delete image
                                    print "Delete current created image - Will delete image %s" %(normalized_id)
                                else:
                                    print "Original imported image is not found in the slideshow. Delete it's contents."
                                    # delete wtv is in the slideshow
                                    if len(slideshow) == 1:
                                        img = slideshow[0]
                                        # delete image
                                        print "There's one item in the slideshow. Delete %s" %(img.id)
                                    else:
                                        print "There's several images in the slideshow. We don't know what to do in this case."
                                        # there's no image in the slideshow
                                        # or we don't know what's in the slideshow 
                                        pass

                            else:
                                original_found = images_found[0]
                                original_name = original_found.split('/')[-1]
                                # Replace current image
                                if original_name.lower() != ref_to_replace.lower():
                                    print "Image to replace was found. Replacing [ %s ] with [ %s ]" %(original_name, ref_to_replace)
                                    self.add_image(image_name, path_to_replace, priref, obj, True, True)
                                else:
                                    print "Image is correct. Do not replace"
                                    pass

                        else:
                            print "No images found. Do nothing."
                            # No images found - do nothing
                            pass
                else:
                    print "No reproduction references found. Do nothing."
                    # there's no reproduction references - do nothing
                    pass
                transaction.commit()
            except:
                transaction.abort()
                pass


    def unpublish_items(self, xml_path):
        collection_xml = xml_path
        collection, xml_root = self.updater.api.get_tm_collection(collection_xml)

        total = len(list(collection))
        curr = 0
        for xml_record in list(collection):
            transaction.begin()
            curr += 1
            print "Unpublishing %s / %s" %(str(curr), str(total))

            if xml_record.find('priref') != None:
                priref = xml_record.find('priref').text

                obj = self.find_object_by_priref(priref)
                if obj:
                    try:
                        api.content.transition(obj=obj, transition='reject', comment='Do not include Kunst object in website.')
                        print "Unpublished %s" %(obj.absolute_url())
                    except:
                        pass
                else:
                    print "Object not found - priref: %s" %(priref)
            else:
                print "Record %s has invalid priref [None]" %(curr)

            transaction.commit()

        return True

    def fix_drawings_view(self):
    
        collection_xml = "/var/www/tm-data/xml/priref_drawings.xml"
        collection, xml_root = self.updater.api.get_tm_collection(collection_xml)

        total = len(list(collection))
        curr = 0
        for xml_record in list(collection):
            transaction.begin()
            curr += 1
            print "Change view %s / %s" %(str(curr), str(total))

            if xml_record.find('priref') != None:
                priref = xml_record.find('priref').text

                obj = self.find_object_by_priref(priref)
                if obj:
                    try:
                        obj.setLayout('drawing_view')
                        print "Changed view of %s" %(obj.absolute_url())
                    except:
                        pass
                else:
                    print "Object not found - priref: %s" %(priref)
            else:
                print "Record %s has invalid priref [None]" %(curr)

            transaction.commit()

        return True

    def fix_books_folder(self, folder, books):
        images = glob.glob(folder)

        curr = 0
        total = len(images)

        print "Name of the image, Object number extracted"

        list_to_fix = ["139e-f 52","25c-e 8","75f 213 # lade IXb 213","143f 84","lade 11e f 126","30d 26 # 141e 26 # 140e 26-1 # 140e 26-2 # 140f 26-4 # 140f 26-5","167a-g 26","155c-f 5","lade 13c-e 3","lade 22 a, b, 30 (2)","143b-c 51","135b 125 1-2","135b 125 1%2","134d-e 113","lade 9c 31 # 28c 31","25f 9-1","24b 6-1 140b-c 6","W2b 20 W"]

        for image in images:
            transaction.begin()
            if 'Icon' not in image:
                curr += 1
                #print "Add image %s / %s" %(curr, total)

                image_name = image.split('/')[-1]
                image_name_no_extension = image_name.split('.')[0]

                if image_name_no_extension in list_to_fix:

                    object_number = image_name_no_extension.replace('#', '/').replace("%", "-")

                    obj = self.get_book_by_shelfmark(object_number, books)
                    if obj:
                        dirty_id = image_name
                        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                        priref = getattr(obj, 'priref', '')
                        self.add_image(normalized_id, image, priref, obj, True)
                    else:
                        print "%s, %s" %(image_name, object_number)
                else:
                    pass
            else:
                pass

            transaction.commit()

        return True

    def fix_books_images(self):

        top = []
        reisboeken = []
        toonboeken = []
        paddenstoekenboeken = []

        books = self.updater.api.get_folder('nl/collectie/boeken-new')

        print "Name of the image, Object number extracted"

        self.fix_books_folder('/var/www/tm-data/Books/books-images-20160215/01.Top/*', books)
        self.fix_books_folder('/var/www/tm-data/Books/books-images-20160215/02.Reisboeken/*', books)
        self.fix_books_folder('/var/www/tm-data/Books/books-images-20160215/03.Toonboeken/*', books)
        self.fix_books_folder('/var/www/tm-data/Books/books-images-20160215/04.Paddenstoelenboeken/*', books)
        
        return True

    def fix_books_categories(self):

        books = self.updater.api.get_folder('nl/collectie/boeken-new')

        print "Name of the image, Object number extracted"

        #self.add_categories('/var/www/tm-data/Books/books-images-20160215/01.Top/*' books, 'topboeken')
        #self.add_categories('/var/www/tm-data/Books/books-images-20160215/02.Reisboeken/*', books, 'reisboeken')
        #self.add_categories('/var/www/tm-data/Books/books-images-20160215/03.Toonboeken/*', books, 'toonboeken')
        #self.add_categories('/var/www/tm-data/Books/books-images-20160215/04.Paddenstoelenboeken/*', books, 'paddenstoelenboeken')

        self.add_categories('/Users/AG/Desktop/books-images-20160215/01.Top/*', books, 'topboeken')
        self.add_categories('/Users/AG/Desktop/books-images-20160215/02.Reisboeken/*', books, 'reisboeken')
        self.add_categories('/Users/AG/Desktop/books-images-20160215/03.Toonboeken/*', books, 'toonboeken')
        self.add_categories('/Users/AG/Desktop/books-images-20160215/04.Paddenstoelenboeken/*', books, 'paddenstoelenboeken')


        return True

    def add_categories(self, folder, books, category):
        images = glob.glob(folder)

        for image in images:
            transaction.begin()
            if 'Icon' not in image:
                image_name = image.split('/')[-1]
                image_name_fixed = image_name.replace('-', ' ').replace('_', ' ')

                object_number = image_name_fixed.split('.')[0]
                obj = self.get_book_by_shelfmark(object_number, books)

                if obj:
                    subjects = list(obj.Subject())
                    subjects.append(category)
                    obj.setSubject(subjects)
                    obj.reindexObject(idxs=['Subject'])
                    print "Fixed %s" %(obj.absolute_url())
                else:
                    print "%s, %s" %(image_name, object_number)
            else:
                pass
            transaction.commit()

        return True

    def get_book_by_shelfmark(self, shelf_mark, folder):

        for _id in folder:
            obj = folder[_id]
            if getattr(obj, 'object_number', '').lower() == shelf_mark.lower():
                return obj

        return None

    def fix_book_title(self, obj):
        title = getattr(obj, 'title', '')
        setattr(obj, 'book_title', title)

        authors = getattr(obj, 'object_author', '')
        if authors:
            author = authors[0]
            name = author['creator']
            if name not in NOT_ALLOWED:
                setattr(obj, 'title', name)
                setattr(obj, 'description', title)

                obj.reindexObject(idxs=['Title'])
                obj.reindexObject(idxs=['Description'])
        
        return True

    def fix_books_titles(self):

        folder = self.updater.api.get_folder('nl/collectie/boeken')

        total = len(folder)
        curr = 0

        for _id in folder:
            curr += 1
            transaction.begin()
            try:

                print "Fixing %s / %s" %(str(curr), str(total))

                obj = folder(_id)

                title = getattr(obj, 'title', '')
                setattr(obj, 'book_title', title)

                authors = getattr(obj, 'object_author', '')
                if authors:
                    author = authors[0]
                    name = author['creator']
                    if name not in NOT_ALLOWED:
                        setattr(obj, 'title', name)
                        setattr(obj, 'description', title)

                        obj.reindexObject(idxs=['Title'])
                        obj.reindexObject(idxs=['Description'])

                transaction.commit()
            except:
                transaction.abort()
                pass

        return True

    ## START
    def start(self):
        # Create translation
        #self.create_translations()
        #return True
        self.init_log_files()
        #self.get_collection()

        self.fix_books_titles()
        return True
        #self.unpublish_items("/var/www/tm-data/xml/unpublish_books1.xml")
        #self.unpublish_items("/var/www/tm-data/xml/unpublish_books2.xml")

        # Fix fossils
        #self.fix_paintings_images()
        #return True
        #self.fix_all_images()
        #return True
        #self.fix_drawings_view()

        #self.unpublish_kunst()
        #return True

        curr, limit = 0, 0
        total = len(list(self.collection))
        
        #self.move_kunst('nl/collectie/tekening-new', 'tekening', self.collection)
        #return True

        for xml_record in list(self.collection):
            try:
                transaction.begin()
                curr += 1

                priref = self.get_priref(xml_record)
                time_limit_continue = self.time_limit_check()

                if not time_limit_continue:
                    self.time_limit_stop(curr, total, priref)
                    return True

                self.updater.object_number = priref

                if self.valid_priref(priref):
                    plone_object = self.find_object_by_priref(priref)
                    if plone_object:
                        self.update_existing(priref, plone_object, xml_record)
                        self.log_status("! STATUS !__Updated [%s] %s / %s" %(str(priref), str(curr), str(total)))
                        self.log_status("! STATUS !__URL: %s" %(str(plone_object.absolute_url())))
                        if self.UPDATE_TRANSLATIONS:
                            self.update_object_translation(priref, plone_object, xml_record)
                    else:
                        if self.CREATE_NEW:
                            created_object = self.create_new_object(priref, plone_object, xml_record)
                            if created_object:
                                self.log_status("! STATUS !__Created [%s] %s / %s" %(str(priref), str(curr), str(total)))
                                self.log_status("! STATUS !__URL: %s" %(str(created_object.absolute_url())))
                                if self.UPLOAD_IMAGES:
                                    self.upload_images(priref, created_object, xml_record)
                            else:
                                self.error("%s__ __Created object is None. Something went wrong."%(str(priref)))
                        else:
                            self.log_status("! STATUS !__Create new objects is disabled. Object not created. [%s] %s / %s" %(str(priref), str(curr), str(total)))
                #if curr % 100 == 0:
                transaction.commit()

            except Exception, e:
                transaction.abort()
                self.error(" __ __An unknown exception ocurred. %s" %(str(e)))
                self.error_log_file.close()
                self.warning_log_file.close()
                self.status_log_file.close()
                self.images_log_file.close()
                raise

        return True







