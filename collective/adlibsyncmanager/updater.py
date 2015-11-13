#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Adlib API migration script by Andre Goncalves
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
"""

import string
from Acquisition import aq_parent, aq_inner
from z3c.relationfield.interfaces import IRelationList, IRelationValue
from plone import api
import csv
import pytz
from zope.intid.interfaces import IIntIds

from z3c.relationfield.schema import RelationList
from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice, ITextLine, IList, IText, IBool, IDatetime
from collective.z3cform.datagridfield.interfaces import IDataGridField
from plone.app.textfield.interfaces import IRichText
from collective.object.utils.interfaces import IListField
from zc.relation.interfaces import ICatalog
from zope.component import getUtility

from plone.app.event.dx.behaviors import IEventBasic

import fnmatch
from lxml import etree
import urllib2, urllib
from plone.namedfile.file import NamedBlobImage, NamedBlobFile
#from plone.multilingual.interfaces import ITranslationManager
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
from plone.event.interfaces import IEventAccessor
from collective.object.utils.interfaces import INotes
from collective.imageReference.imageReference import IImageReference

from z3c.relationfield import RelationValue
from zope import component
from collective.object.object import IObject
from collective.dexteritytextindexer.utils import searchable

from .sync_utils import SyncUtils

PORTAL_TYPE = "Taxonomie"

from .contenttypes_path import CONTENT_TYPES_PATH

if PORTAL_TYPE == "Object":
    from .core import CORE
    from .utils import subfields_types, relation_types

elif PORTAL_TYPE == "Resource":
    from .resource_utils import resource_subfields_types as subfields_types
    from .resource_utils import resource_relation_types as relation_types
    from .resource_core import RESOURCE_CORE as CORE

elif PORTAL_TYPE == "Serial":
    from .serial_utils import serial_subfields_types as subfields_types
    from .serial_utils import serial_relation_types as relation_types
    from .serial_core import SERIAL_CORE as CORE

elif PORTAL_TYPE == "Article":
    from .article_utils import article_subfields_types as subfields_types
    from .article_utils import article_relation_types as relation_types
    from .article_core import ARTICLE_CORE as CORE

elif PORTAL_TYPE == "Audiovisual":
    from  .audiovisual_utils import audiovisual_subfields_types as subfields_types
    from  .audiovisual_utils import audiovisual_relation_types as relation_types
    from  .audiovisual_core import AUDIOVISUAL_CORE as CORE

elif PORTAL_TYPE == "PersonOrInstitution":
    # Persons
    from .persons_utils import persons_subfields_types as subfields_types
    from .persons_utils import persons_relation_types as relation_types
    from .persons_core import PERSON_CORE as CORE

elif PORTAL_TYPE == "Exhibition":
    # Persons
    from .exhibition_utils import exhibition_subfields_types as subfields_types
    from .exhibition_utils import exhibition_relation_types as relation_types
    from .exhibition_core import EXHIBITION_CORE as CORE

elif PORTAL_TYPE == "Image":
    # Persons
    from .image_utils import image_subfields_types as subfields_types
    from .image_utils import image_relation_types as relation_types
    from .image_core import IMAGE_CORE as CORE

elif PORTAL_TYPE == "Taxonomie":
    # Taxonomie
    from .taxonomy_utils import taxonomy_subfields_types as subfields_types
    from .taxonomy_utils import taxonomy_relation_types as relation_types
    from .taxonomy_core import TAXONOMY_CORE as CORE


REP_REFERENCES = ['PKCZ00-06 foto', 'PKCZ00450-A/P foto 3', 'PKCZ00450-A/P foto 4', 'M91-029 foto kl', 'M90-001 foto z', 'M90-001 dia', 'M84-004-3 foto z', 'M79-049 foto z', 'M79-049 dia', 'PKCZ00-14', 'PKCZ97-05', 'PKCZ00-12', 'PKCZ00-13', 'PKCZ00518 foto-02', 'PKCZ00518 foto-03', 'PKCZ00518 foto- 04', 'PKCZ00518 foto -01', 'PKCZ95-04 foto', 'PKCZ94-05 foto', 'PKCZ00375 foto 02', 'PKCZ94-01 foto', 'PKCZ00308 foto 02', 'PKCZ00308 ecta 02', 'PKCZ92-11 foto 1', 'PKCZ93-06', 'PKCZ95-11 foto 02', 'PKCZ95-11 foto 03', 'PKCZ95-11 foto 04', 'PKCZ00083-A/F foto 02', 'PKCZ00374 ecta', 'PKCZ94-20 foto 2', 'PKCZ99-05 foto 2', 'PKCZ00475 foto-01', 'PKCZ00475 foto-02', 'PKCZ00475 foto- 03', 'PKCZ94-12foto', 'M67-113 foto z', 'G1784 dia', 'G 1784 foto 01', 'G1875-04 foto z', 'G1875 foto z', 'G 1857 foto 01', 'M88-36-14 foto z', 'G2582 foto kl', 'M90-010 foto 01', 'G 1854 foto 01', 'G 1854 foto 02', 'G 1854 foto 03', 'G2043 foto kl', 'G2899', 'G2085 foto kl', 'G0323 foto kl', 'G3238 kleur', 'G2124 foto kl', 'M89-016 dia', 'M89-016 foto 01', 'M89-016 foto 02', 'M89-016 foto 03', 'M89-016 foto 04', 'G 1851 foto 02', 'M96-031 dia', '81-049 foto z', 'M81-049 dia', 'M81-050 foto z', 'M81-050 dia', 'M67-075 foto kl', 'M67-075 foto z', 'M67-075 dia 01', 'M67-075 dia 02', 'M67-133 foto z', 'M67-077 foto kl', 'M67-077 foto z', 'M67-077 dia 01', 'M67-077 dia 02', 'M67-078 foro kl', 'M67-078 foto z', 'M67-078 dia 02', 'M67-078 dia 01', 'M83-031 foto kl', 'M83-031 foto z', 'M83-031 dia', 'M80-039 foto z', 'M80-039 dia 01', 'M80-039 dia 02', 'M72-039 foto kl', 'M72-039 foto z', 'M72-039 dia 02', 'M72-039 dia 01', 'M 67-076 foto z', 'M67-076 dia', 'M85-017 foto kl', 'M85-017 foto z', 'M85-017 dia 01', 'M85-017 dia 02', 'G1617 foto z', 'M68-033 foto z', 'M68-033 dia', 'M67-137   foto z', 'G1565 foto z', 'M80-056 foto z', 'M98-001 foto z', 'G1582 foto z', 'M62-105  foto z', 'G1581 foto z', 'G1534 foto z', 'M67-124 dia', 'G1697 dia', 'G1640 foto z', 'BR65-004 dia', 'M67-067 foto z', 'M67-067 dia', 'M67-130 foto z', 'M80-055 foto z', 'M67-028 foto z', 'M80-058 foto z', 'PKCZ00517 foto 01', 'PKCZ00517 ecta 02', 'PKCZ00517 foto 02', 'PKCZ00517 foto 03', 'PKCZ00517 foto 04', 'PKCZ00545-A/F foto', 'AB1222 dia', 'G1533a', 'G2207 foto kl', 'G2254 A', 'M81-006 foto kl', 'M81-006 foto z', 'M81-006 dia 01', 'M81-006 dia 02', 'G0848 dia', 'M82-006 foto kl', 'M82-006 foto z', 'M82-006 dia', 'G2121 foto kl', 'BR91-012-A/F foto 01', 'BR91-012-A/F foto 02', 'BR91-012-A/F foto 03', 'M95-006 foto 01', 'M95-007 foto 01', 'G2130 foto kl', 'G2117 foto kl', 'M67-142 foto z', 'M81-037 foto z', 'M81-037 dia', 'g2203 foto kl', 'G1362 foto kl', 'AB1212 dia', 'AB1260 dia', 'BR95-050 foto', 'G1626 dia', 'G1634 fotoz', 'G1671 foto z', 'G1671 dia', 'G1668 foto z', 'G1668 foto kl', 'M64-059 dia', 'M99-015 foto kl', 'M67-144 foto z', 'G1614 dia', 'G1198 dia', 'M67-088 foto z', 'M67-118 foto z', 'G2249 dia', 'M90-025 foto z', 'G1530 foto 1', 'G1530 foto 2', 'G2577 foto kl', 'M89-047 foto z', 'M89-050 foto z', 'M67-086 foto z', 'M67-112  foto z', 'M67-110 foto z', 'M67-109 foto z', 'M67-117 foto z', 'M67-114 foto z', 'M67-116 dia 01', 'M67-116 dia 02', 'M67-117 dia 01', 'M67-117 dia 02', 'M67-119 foto z', 'M67-119 dia 01', 'M67-119 dia 02', 'M67-120 foto z', 'M67-120 dia 01', 'M67-120 dia 02', 'M67-136 foto z', 'M68-071 foto z', 'M68-071 dia', 'G 1667 foto z', 'G1667 dia', 'M79-044 foto z', 'M79-045 foto z', 'G2231 foto z', 'G2231 foto kl', 'G 2309 foto z', 'G2256 foto kl', 'M79-047 foto z', 'G2202 foto z', 'M93-028 foto 2', 'M67-068 foto z', 'AB1287-A dia', 'AB1259 dia', 'AB1347 dia', 'G1800 dia', 'M79-043 foto z', 'M62-104 foto kl', 'G1813 foto kl', 'G1844 foto kl', 'G2292 foto kl', 'HG1591 foto z', 'M62-050 foto kl', 'M62-050 dia', 'G1672 foto z', 'G1672 dia 01', 'G1672 dia 02', 'M66-091 foto z', 'G2198 foto kl', 'G2126 foto kl', 'G2141 foto z', 'G2181 foto kl', 'G2197 foto kl', 'G1196b', 'G1183', 'G1183a', 'G1183b', 'M91-009 foto z', 'G2132 foto kl', 'G2132 foto z', 'G2161 foto`s kl', 'G1566 dia', 'G2619 foto`s kl', 'M79-046 foto z', 'M89-048 foto z', 'G1212', 'G1212a', 'BR98-055', 'BR98-058', 'Br98-012', 'BR98-051', 'G1408', 'G1408a', 'G1429 kleurenecta 01', 'M63-107 foto z', 'M63-107 dia', 'G0858 dia', 'AB0982 dia', 'M94-008 ecta', 'M94-008 foto kl', 'M94-008 foto z', 'M94-008 dia 01', 'M94-008 dia 02', 'M94-008 dia 03', 'G2301 foto kl', 'M93-027 foto kl', 'M93-027 foto z', 'M93-027 dia', 'G0819 foto kl', 'G2264 foto kl', 'G2273 foto kl', 'BR94-012 dia', 'M79-038 foto z', 'G1995 foto kl', 'G1`842 foto z', 'G2044 foto kl', 'G2103 foto kl', 'M79-055 dia 01', 'M79-055 dia 02', 'G2116 foto kl', 'M93-029 foto 2', 'M92-002 foto z', 'M92-002 dia 01', 'M92-002 dia 02', 'G2440 foto kl', 'G2042 foto kl', 'M67-087 foto z', 'BR96-006 dia', 'M65-088 foto z', 'M65-088 dia', 'M67-044 foto z', 'G 2344 foto kl', 'M67-034 foto z', 'G1680  foto z', 'G 1680 dia', 'G2665 foto kl', 'M82-005 foto z', 'M82-005 dia', 'G2307 foto kl', 'G2258 foto kl', 'G2061 foto kl', 'AB1261 dia', 'PKCZ00022-A/C foto 02', 'PKCZ94-24-A/F foto 03', 'PKCZ93-10 foto', 'PKCZ92-03 foto 2', 'PKCZ95-05 foto', 'PKCZ96-02 foto 2', 'PKCZ98-66 dia', 'PKCZ98-066 foto', 'PKCZ95-07 foto', 'PKCZ94-03 foto', 'PKCZ94-25-A/K ecta', 'PKCZ94-25-A/K tekening', 'PKCZ94-06 foto', 'PKCZ96-04 foto', 'PKCZ96-05 foto', 'PKCZ94-22a', 'PKCZ94-22a foto', 'PKCZ93-04 foto 02', 'PKCZ00443-A/C foto 02', 'PKCZ98-73 foto 2', 'PKCZ98-73 foto 3', 'pkcz96-21 foto 2', 'PKCZ96-12 foto', 'PKCZ92-12-A/C dia 02', 'PKCZ94-14 ecta', 'PKCZ94-14 foto', 'PKCZ93-07 foto 2', 'M97-014 foto kl', 'M92-001 fot kl', 'M86-058 foto z', 'M87-051 foto z', 'M87-104 foto z', 'M88-36-13 foto z', 'M89-026 dia', 'M89-026 foto z', 'M89-030 foto z', 'M90-040 foto z', 'M89-055 foto z', 'M90-020 foto z', 'M90-021 foto z', 'M89-053 A/G foto kl', 'M89-054 foto z', 'M93-015 foto z', 'M93-006 foto z', 'M93-032 foto kl', 'M95-002 foto z', 'M98-072 foto kl', 'M98-080 foto kl', 'M98-082 foto kl', 'M99-036 foro kl', 'M99-037 foto kl', 'G 3239 foto z', 'G0834 foto kl', 'G1172 foto kl', 'G1421 foto kl', 'G1424 foto kl', 'G1426 foto kl', 'G1474 foto kl', 'G1562 foto z', 'G1618 foto z', 'G1644 foto z', 'G`766 foto kl', 'G1767 foto kl', 'G1859 foto kl', 'G1878 foto z', '1889 foto kl', 'G1904 foto kl', 'G1933 foto kl', 'G2001 foto kl', 'G2009 foto kl', 'G2021 foto kl', 'G2026 foto kl', 'G2037 foto kl', 'G2054 foto kl', 'G2102 foto kl', 'G2104 foto kl', 'G2072 foto kl', 'G2064 foto kl', 'G2107 foto kl', 'G2109 foto kl', 'G2112 foto kl', 'G2123 foto kl', 'G2129 foto kl', 'G2142 foto z', 'G2147 foto kl', 'G2150 foto kl', 'G1652 foto kl', 'G2159 foto kl', 'G2158-A/B foto kl', 'G2166 foto kl', 'G2188 foto kl', 'G2185  foto kl', 'G2208 foto kl', 'G2259 foto kl', 'G2217 foto kl', 'G2218 foto kl', 'G2220 foto kl', 'G2221 foto kl', 'G2223 foto z', 'G2225 foto z', 'foto`s kleur', 'G2229-A foto kl', 'G2229-B foto kl', 'G2233 foto kl', 'G2243 foto z', 'G2246 foto kl', 'G2255 foto kl', 'G2282 foto kl', 'G2288 foto kl', 'G2299 foto z', 'G2302 foto kl', 'G 2310 foto z', 'G 2316 foto kl', 'G2331 foto kl', 'G 2337 foto kl', 'G2351 foto kl', 'foto kl', 'G2480 foto kl', 'G2526 foto kl', 'G2528 foto kl', 'G2532 foto kl', 'G2540 foto kl', 'G2543 foto kl', 'G2595 foto kl', 'G2600 foto kl', 'G2651 foto kl', 'G2661 foto kl', 'G2662 foto kl', 'G2682 foto kl', 'G 2685 foto kl', 'G2716 foto kl', 'G2736 foto z', 'G2865 foto kl', 'G2870 foto kl', 'G2879 foto kl', 'G 2884 foto kl', 'G2907 foto kl', 'G2908 foto z', 'G2945 foto kl', 'G3355-01 repr. kl', 'G99-028 foto z', 'G01-001foto kl', 'G02-002 foto kl', 'G02-003 foto kl', 'NHG98-050 foto z', 'NHG98-049 foto z', 'NHG98-136 foto z', 'M92-001 dia 01', 'M92-001 dia 02', 'M92-001 dia 03', 'M92-001 dia 04', 'M94-015 dia', 'M98-072 dia 01', 'M98-072 dia 02', 'M02-001 dia', 'G1196a', 'G1387', 'G1388', 'G1395', 'G1420', 'G1578', 'G1666', 'G3389-kleur', 'G3377-kleur', 'M79-050 dia', 'M81-046 dia', 'M87-088 dia', 'M89-026 dia 01', 'M62-100 dia', 'AB1724 dia 01', 'BR91-024 dia', 'BR93-003 dia 01', 'BR95-055 dia', 'BR96-007 dia', 'BR93-003 dia 02', 'G1838 dia 01', 'G1838 dia 02', 'G1838 dia 03', 'G1838 dia 04', 'G2240 dia 01', 'G2240 dia 02', 'G3414_G3415 dia', 'AB1724 dia 02', 'M84-080 dia 01', 'M84-080 dia 02', 'M84-080-01_05 dia 01', 'M84-080-01_05 dia 02', 'AB1724 dia 03', 'G 1344 foto 01', 'G 1344 foto 02', 'G 1783 foto 01', 'G 1783 foto 02', 'G 1851 foto 01', 'G 1892 foto 01', 'G 1892 foto 02', 'G 1970 foto 01', 'G 1970 foto 02', 'M63-011 fotocopie 01', 'M64-061 foto 01', 'M65-106 foto 01', 'M68-072 foto 01', 'M68-072 foto 02', 'M81-026-A/E foto 01', 'M81-029-A/E foto 01', 'M81-029-A/E foto 02', 'M90-034 foto 01', 'M90-034 foto 02', 'M91-014-1 foto 01', 'AB1724 foto 01', u'HW1600-10', 'G2212 foto kl', 'G2212 dia', 'G2648 foto z', 'G2648 dia', 'M67-061 foto z', 'M67-091 foto z', 'M67-091 dia', 'M67-176 foto z', 'M88-042 foto z', 'M98-077 foto kl', 'M98-078 foto kl', 'AB0990 dia', 'BR87-127-A foto 01', 'BR87-127-B foto 01', 'BR87-127-C foto 01', 'BR87-127-D', 'BR87-127-E foto 01', 'BR87-127-F', 'BR87-127-G foto 01', 'BR87-127-H foto 01', 'BR87-130 foto 01', 'BR 87-133 foto 01', 'BR91-008 foto 01', 'BR91-008 foto 02', 'BR91-008 foto 03', 'Br91-009 foto 01', 'BR91-009 foto 02', 'BR91-013-A foto 01', 'BR91-013-B foto 01', 'BR91-013-C foto 01', 'BR91-014-A foto 01', 'BR91-014A dia 01', 'BR91-019 foto 03', 'BR91-019 foto 02', 'BR91-019 foto 01', 'BR91-021 foto 01', 'BR91-025 foto 01', 'BR91-027 foto 01', 'BR91-027 foto 02', 'BR91-029 dia', 'BR98-042', 'G99-078', 'PKCZ00091 foto 2', 'PKCZ00309', 'PKCZ00420 foto 1', 'PKCZ00420 foto 2', 'G1651 foto z', 'AB0031 dia', 'BR91-018 foto 01', 'BR91-018 foto 02', 'PKCZ97-06', 'PKCZ94-21', 'PKCZ93-12', 'PKCZ93-13', 'PKCZ00283-foto', 'PKCZ92-08', 'PKCZ92-09', 'PKCZ92-10foto', 'PKCZ98-80', 'PKCZ99-11', 'PKCZ 99-13', 'PKCZ99-14', 'PKCZ00369', 'PKCZ00373 dia', 'PKCZ00204', 'PKCZ94-19-A/C', 'PKCZ00320-E', 'PKCZ93-07 foto 1', 'PKCZ98-69', 'PKCZ98-70', 'PKCZ98-71', 'PKCZ00081', 'PKCZ93-09', 'PKCZ93-08', 'PKCZ95-01ecta 1', 'M87-089', 'PKCZ94-10', 'PKCZ92-02-a', 'PKCZ92-02-b', 'PKCZ92-02-c', 'PKCZ92-02-d', 'PKCZ92-02-e', 'PKCZ92-02-f', 'PKCZ96-07', 'PKCZ96-21 foto 1', 'M92-031 foto', 'PKCZ93-10 ecta', 'PKCZ93-11', 'PKCZ99-07', 'PKCZ99-08', 'PKCZ00488A/B', 'PKCZ93-03', 'PKCZ00-03-01', 'PKCZ00-03-02', 'PKCZ00-03-03', 'PKCZ00-03-04', 'PKCZ00-03-05', 'PKCZ00-03-06', 'PKCZ00-03-07', 'PKCZ00-03-08', 'PKCZ00144', 'PKCZ00146', 'PKCZ00490', 'PKCZ00489', 'PKCZ96-01', 'PKCZ96-03', 'PKCZ97-01 foto 1', 'PKCZ98-73 foto 1', 'PKCZ94-03 ecta', 'PKCZ95-04 ecta', 'PKCZ94-06 ecta', 'PKCZ94-05 ecta', 'PKCZ96-13', 'PKCZ94-08foto', 'PKCZ94-07', 'PKCZ00297', 'PKCZ99-06', 'PKCZ00265', 'PKCZ00019', 'PKCZ00299', 'M77-004', 'M91-005', 'PKCZ00446 foto 2', 'PKCZ95-09', 'PKCZ99-05 foto 1', 'PKCZ94-22a/x', 'PKCZ94-22x', 'PKCZ92-04a/b', 'PKCZ99-04', 'PKCZ99-03', 'PKCZ92-13', 'PKCZ95-05 dia', 'PKCZ94-02 foto', 'PKCZ94-01 ecta', 'PKCZ95-07 ecta', 'PKCZ95-08 ecta', 'PKCZ95-06 ecta', 'PKCZ98-66 ecta', 'PKCZ99-09', 'PKCZ00523', 'PKCZ00524', 'PKCZ00525', 'PKCZ00526', 'PKCZ92-11 foto 2', 'PKCZ94-20 foto 1', 'PKCZ96-08', 'PKCZ00-15', 'PKCZ93-02', 'PKCZ96-04 ecta', 'PKCZ96-05 ecta', 'PKCZ99-02 ecta', 'PKCZ94-24-A/F foto 02', 'PKCZ00-10 foto 02', 'PKCZ00-11 foto 01', 'PKCZ00022-A/C foto 01', 'PKCZ00154-A/O dia', 'PKCZ00545-A/F dia', 'PKZC00272-A/0 ecta', 'PKCZ00374 foto', 'PKCZ00443-A/C foto 01', 'PKCZ93-04 foto 01', 'PKCZ00375 foto 01', 'PKCZ92-07 A/E foto 01', 'PKCZ98-78', 'PKCZ00-01-01', 'PKCZ00-01-02', 'PKCZ00-01-03', 'PKCZ00-01-04', 'PKCZ00-01-05', 'PKCZ00-01-06', 'PKCZ00-01-07', 'PKCZ00-02-01', 'PKCZ00-02-02', 'PKCZ00-02-03', 'PKCZ00-02-04', 'PKCZ00-02-05', 'PKCZ96-20-A/F', 'PKCZ00083-A/F foto 01', 'PKCZ00308 ecta 01', 'PKCZ95-11 foto 01', 'PCKZ00307', 'PCKZ00408', 'PKCZ92-03 foto 1', 'PKCZ95-03 foto 1', 'PKCZ96 09 ecta', 'PKCZ96-10 ecta', 'PKCZ96-11 ecta', 'PKCZ96-12 ecta', 'PKCZ00494ecta', 'PKCZ95-02 foto 1', 'PKCZ97-08', 'PKCZ99-01', 'M93-028 foto 1', 'PKCZ94-17 dia', 'PKCZ94-18  dia', 'PKCZ00-04 dia', 'PKCZ00477', 'PKCZ00522 ecta-01', 'PKCZ00521 foto 2', 'PKCZ92-01 foto 1', 'PKCZ96-02-A/E', 'PKCZ94-15 foto', 'PKCZ00450-A/P foto 2', 'PKCZ00512', 'PKCZ00-08-01', 'M90-014 ecta-02', 'PKCZ00513', 'PKCZ92-15', 'PKCZ92-16', 'PKCZ92-17', 'PKCZ94-16-02', 'PKCZ00-06 dia 02', 'PKCZ01-11 dia', 'PKCZ94-25-A/K foto', 'PKCZ92-12-A/C dia 01', 'PKCZ96-06', 'PKCZ00475 dia-01', 'PKCZ00518 dia-02', 'PKCZ00517 ecta  01', 'PKCZ 92-12 foto', 'M79-061', 'PKCZ97-07', 'Br98-004', 'Br-98-005', 'Br98-013', 'Br98-014', 'Br98-015', 'Br98-016', 'Br98-017', 'Br98-018', 'Br98-019', 'M01-032', 'M01-033', 'BR98-020', 'BR98-023', 'M99-014', 'BR98-022', 'BR98-027', 'BR98-028', 'BR98-032', 'BR98-033', 'BR98-034', 'BR98-035', 'BR98-041', 'BR98-046', 'BR98-047', 'BR98-048', 'BR98-049', 'BR98-050', 'BR98-052', 'BR98-056', 'BR98-062', 'PKCZ00-19', 'PKCZ96-18', 'M62-062 foto z', 'M62-099 foto kl', 'M62-051 foto z', 'M62-112 foto z', 'M62-113 foto kl', 'M62-114 foto kl', 'M63-007 foto z', 'M63-148 foto z', 'M64-086 foto z', 'M64-087 foto z', 'M65-076 foto z', 'M65-077', 'M66-007 foto kl', 'M66-106 foto kl', 'M67-021 foto z', 'M67-022 foto z', 'M64-061 foto z', 'M67-027 foto z', 'M67-025 foto z', 'M67-032 foto z', 'M67-033 foto z', 'M67=076 foto kl', 'M67-042 foto z', 'M67-051-foto z', 'M67-055 foto z', 'M67-057 foto z', 'M67-064 foto z', 'M67-073 foto z', 'M67-083 foto z', 'M67-084 foto z', 'M67-089 foto z', 'M67-090 foto z', 'M67-093 foto z', 'M67-111 foto z', 'M67--116 foto z', 'M67-126 foto kl', 'M67-122 foto kl', 'M67-132', 'M69-010 foto z', 'M78-056 foto kl', 'M79-040 foto z', 'M79-041 foto z', 'M79-050 foto z', 'M79-054 foto z', 'M79-055 foto z', 'M80-008 foto z', 'M80-009 foto kl', 'M80-039 foto kl', 'M80-059 foto z', 'M80-061 foto kl', 'M80-060 foto z', 'M81-046 foto z', 'M82-030 foto z', 'M82-031 foto z', 'PKZC00022', 'G 1643 A foto z', 'M89-047 foto z/w', 'AB1518-A/B dia', 'M79-036 foto z', 'G1592 foto z', 'G1861 foto z', 'M82-022 foto z', 'M84-078 foto z', 'M84-078 foto kl', 'M84-078 dia 01', 'M84-078 dia 02', 'M78-018 foto kl', 'M87-102 foto z', 'M87-102 dia', 'M81-038 foto z', 'M62-143 foto z', 'M62-143 dia', 'M68-067 foto 01', 'G2163 foto kl', 'G2114 foto kl', 'M87-099 foto z', 'M87-099 dia', 'G2106 foto kl', 'M68-073 foto kl', 'G2157 foto kl', 'G2128 foto kl', 'G2081 foto kl', 'G1575 dia', 'M 93-006 dia 01', 'G 1783 A foto 01', 'M79-039 foto z', 'G2918 foto kl', 'G2125 foto kl', 'G2354 oto kl', 'G2041 foto kl', 'G2235 foto kl', 'M79-061 foto z', 'M79-061 dia 01', 'M79-061 dia 02', 'M61-024-44 foto z', 'M61-024-48 foto z', 'M61-024-42 foto z', 'M61-024-47 foto z', 'M61-024-49 foto z', 'M61-024-53 foto z', 'M61-024-68 foto z', 'M61-024-78  foto z', 'M61-024-79 foto z', 'M61-024-90foto z', 'M61-024-89 foto z', 'M95-001 foto z', 'M95-001 dia', 'G2062 foto kl', 'G1647 foto z', 'G2552 foto kl', 'M63-008 foto z', 'M63-008 dia', 'M91-019 foto z', 'NHG98-002 foto z', 'g1643fotoz', 'G1670 foto z', 'G2281 foto kl', 'G1674 foto kl', 'G1674 dia 01', 'G1674 dia 02', 'BR94-015 dia 01', 'BR94-015 dia 02', 'M80-060 dia', 'M80-061 foto z', 'M80-061 dia', 'M95-002 dia 01', 'M95-002 dia 02', 'M83-019 foto z', 'M62-126 foto kl', 'G2557 foto kl', 'G2118 foto kl', 'M88-010 foto z', 'M88-010 dia', 'G2599 foto kl', 'M63-009 foto z', 'M63-009 dia', 'G1645 dia', 'G1797 foto z', 'G1797 dia', 'PKCZ95-03 foto 2', 'PKCZ95-03 foto 3', 'PKCZ92-07 A/E foto 02', 'PKCZ00521 foto 3', 'PKCZ00521 foto 4', 'PKCZ00522 ecta-02', 'PKCZ00522 ecta -03', 'M79-063 foto z', 'M79-063 dia', 'M67-145 foto z', 'PKCZ94-22b', 'PKCZ94-22b foto', 'PKCZ96-10 foto', 'PKCZ94-22g', 'PKCZ94-22g foto', 'PKCZ94-22h', 'PKCZ94-22h foto', 'PKCZ94-22i', 'PKCZ94-22i foto', 'PKCZ94-22j', 'PKCZ94-22j foto', 'PKCZ94-22k', 'PKCZ94-22k foto', 'PKCZ94-22l', 'PKCZ94-22l foto', 'PKCZ94-22m', 'PKCZ94-22m foto', 'PKCZ94-22n', 'PKCZ94-22n foto', 'PKCZ94-22o', 'PKCZ94-22o foto', 'PKCZ94-22t', 'PKCZ94-22t foto', 'PKCZ94-22u', 'PKCZ94-22u foto', 'PKCZ94-22v', 'PKCZ94-22v foto', 'PKCZ94-22w', 'PKCZ94-22w foto', 'PKCZ94-22s', 'PKCZ94-22s foto', 'PKCZ94-22r', 'PKCZ94-22r foto', 'PKCZ94-22q', 'PKCZ94-22q foto', 'PKCZ94-22p', 'PKCZ94-22p foto', 'PKCZ94-22c', 'PKCZ94-22c foto', 'PKCZ94-22d', 'PKCZ94-22d  foto', 'PKCZ94-22f', 'PKCZ94-22f foto', 'PKCZ94-22e', 'PKCZ94-22e foto', 'PKCZ00154-A/Q ecta', 'PKCZ96-09 foto', 'PKCZ00-10 foto 03', 'PKZC00-11 foto 02', 'PKCZ94-17 foto', 'PKCZ98-67', 'PKCZ95-01ecta 2', 'PKCZ97-01 foto 2', 'PKCZ94-02 ecta', 'PKCZ99-02 foto', 'PKCZ00272-A/O dia', 'PKCZ00446 foto 3', 'PKCZ01-12', 'M90-014 ecta-03', 'M90-014 foto-01', 'M90-014 foto-02', 'M61-024-01 foto z', 'M67-090 dia', 'M67-127 foto z', 'M91-005 foto', 'G1712 foto kl', 'G2222 foto kl', 'M79-037', 'G2188 foto z', 'M97-018 foto kl', 'M90-020 dia', 'G1691 foto z', 'G1691 dia', 'G1764 foto kl', 'G2260 foto kl', 'PKCZ00-08-02', 'PKCZ00-08 foto-1-3', 'PKCZ00-08-03', 'G02-014 digitaal', 'G02-014 foto kl', 'G 2305 foto kl', 'G2304 foto kl', 'G2303 foto kl', 'M61-949 foto z', 'M61-049 dia', 'M67-031 foto z', 'M92-032 foto 2', 'M92-032 foto 3', 'M00-002 foto z', 'G2542 foto kl', 'G2234 foto z', 'G2204 foto kl', 'M61-024-22 foto z', 'M61-024-23 foto z', 'G2140 foto z', 'M61-020 foto z', 'PKCZ92-01 foto 2', 'PKCZ99-04 foto', 'PKCZ00373 foto', 'PKCZ96-11 foto', 'PKCZ95-08 foto', 'PKCZ94-18 foto', 'PKCZ95-06 foto', 'M99-013', 'G1717 foto z', 'G2734 foto kl', 'M79-060 foto z', 'M79-060 dia', 'M79-042 foto z', 'G 2893 foto kl', 'G2115 foto kl', 'G0583 dia', 'G2289 foto kl', 'G3381-kleur', 'M91-012 foto 01', 'M91-012 foto 02', 'M63-015-A foto 01', 'M63-015-B foto 01', 'G 1781 foto 01', 'G1833 dia 01', 'G1833 dia 02', 'G1833 dia 03', 'G 1833 foto 03', 'G 1833 foto 01', 'G 1833 foto 02', 'G1462', 'G1628 foto z', 'G1628 dia', 'M67-048 foto z', 'M67-048 dia', 'M93-015 dia', 'M67-024 foto z', 'G1388a', 'G2016 foto z', 'NHG98-168 foto z', 'M95-005 foto 01', 'M95-005 foto 02', 'M63-148 dia 01', 'M63-148 dia 02', 'G2127 foto kl', 'G2210 foto kl', 'G 1932 foto kl', 'G2139 foto kl', 'M01-012 foto kl', 'G2113 foto kl', 'G2254 B', 'G2239 dia 01', 'G2239 dia 02', 'NHG98-211 foto z', 'NHG98-216 foto z', 'M67-036 foto z', 'M00-190 foto kl', 'M88-051 foto z', 'M88-051 dia', 'M98-081 foto kl', 'M67-147 foto z', 'M93-018 foto 01', 'M93-018 foto 02', 'M78-016 foto kl', 'M90-029 foto z', 'G1860 foto z', 'G2053 foto kl', 'M77-088 foto kl', 'M66-133 foto z', 'M78-017 foto kl', 'G1631 foto z', 'G1631 dia', 'M79-064 foto z', 'M79-064 dia', 'M67-058 foto z', 'G1353 dia', 'G2159 foto`s kl', 'M81-036 foto z', 'M81-036 dia', 'G 1852 foto 01', 'G1905 foto kl', 'G2063 foto kl', 'G1352 foto kl', 'G2168 foto`s kl', 'BR64-038 dia', 'M93-016 foto z', 'M93-016 dia', 'BR94-014 dia', 'G2291 foto kl', 'G1417', 'G1238', 'G1863 Foto kl', 'M00-186 foto kl', 'M00-187 foto kl', 'M00-188 foto kl', 'M00-189 foto kl', 'G99-062', 'M79-048 foto z', 'G 1850 foto 01', 'G 1850 foto 02', 'G1879', 'G1942 foto z', 'M95-039 dia', 'M95-039 foto 01', 'M95-039 foto 02', 'M95-039 foto 03', 'M95-039 foto 04', 'M83-033 foto 01', 'M83-033 foto 02', 'M67-023 foto z', 'G2296 foto kl', 'G2616 foto kl', 'G2537 foto kl', 'g1705 foto z', 'G1705 dia 01', 'G1705 dia 02', 'M79-062 foto z', 'M79-062 dia 01', 'M79-062 dia 02', 'M78-033 dia', 'm74-006 Foto kl', 'M74-006 dia', 'M67-072 foto z', 'M67-065 foto z', 'M87-087 foto z', 'M87-087 dia']
RESTRICTIONS = []
IDENTIFIERS = ['m:\\images\\M79-028.jpg', 'M:\\images\\M79-032.JPG', 'm:\\images\\M66-14-02-06.jpg', 'm:\\images\\G1929.jpg', 'm:\\images\\G2732q.jpg', 'm:\\images\\M66-14-02-07.jpg', 'm:\\images\\G2707-01a.jpg', 'm:\\images\\pkcz00274-02.jpg', 'm:\\images\\M79-004.jpg', 'm:\\images\\G1875a.jpg', 'm:\\images\\G1222q.jpg', 'm:\\images\\AB0955-01k1.jpg', 'm:\\images\\AB1035qk1.jpg', 'm:\\images\\AB1017qk1.jpg', 'm:\\images\\AB1033qk1.jpg', 'm:\\images\\AB1767-06.jpg', 'm:\\images\\G1184q.jpg', 'm:\\images\\Br72-005-01 Veere 1.jpg', 'm:\\images\\G2619-01.jpg', 'm:\\images\\M62-010 & m62-012.jpg', 'm:\\images\\M86-035a1.jpg', 'm:\\images\\G2900-01a.jpg', 'm:\\images\\M93-018-01a.jpg', 'm:\\images\\M66-14-02-01.jpg', 'm:\\images\\M66-14-02-02.jpg', 'm:\\images\\G1446-01a.jpg', 'M:\\images\\M96-047-01-04a.jpg', 'm:\\images\\M66-14-02-05.jpg', 'm:\\images\\M91-014qa.jpg', 'm:\\images\\wonderkamer31mei2006-1.jpg', 'm:\\images\\AB1771-01a.jpg', 'm:\\images\\AB1175k1.jpg', 'm:\\images\\ab1431k2.jpg', 'm:\\images\\AB1207q.jpg', 'm:\\images\\AB1137q.jpg', 'm:\\images\\ab1136.jpg', 'm:\\images\\AB1668q.jpg', 'm:\\images\\AB1470-01k1.jpg', 'm:\\images\\AB1470-02k1.jpg', 'm:\\images\\AB1470-03k1.jpg', 'm:\\images\\AB1470-04k1.jpg', 'm:\\images\\AB1470-05k1.jpg', 'm:\\images\\AB1559q.jpg', 'm:\\images\\AB0955-03k1.jpg', 'm:\\images\\AB1476-03k2.jpg', 'm:\\images\\AB1476-03k3.jpg', 'm:\\images\\AB1476-03k4.jpg', 'm:\\images\\AB1469-02-k2.jpg', 'm:\\images\\AB1469-02-k3.jpg', 'm:\\images\\AB1469-02-k4.jpg', 'm:\\images\\AB1473q.jpg', 'm:\\images\\AB1599q1.jpg', 'm:\\images\\AB1599q2.jpg', 'm:\\images\\ab1422-02.jpg', 'm:\\images\\AB1614qk1.jpg', 'm:\\images\\AB1614qk2.jpg', 'm:\\images\\AB1754-02a.jpg', 'm:\\images\\AB1524q.jpg', 'm:\\images\\G1198a.jpg', 'm:\\images\\wonderkamer-15juni2005.jpg', 'm:\\images\\ZM-15juni2005-31.jpg', 'm:\\images\\BR00-001-02h1.jpg', 'm:\\images\\G2492-02.jpg', 'm:\\images\\G2492-03.jpg', 'm:\\images\\G2492-04.jpg', 'm:\\images\\G2492-05.jpg', 'm:\\images\\G2492-06.jpg', 'm:\\images\\G2492-08.jpg', 'm:\\images\\G2520h3.jpg', 'm:\\images\\G2520h4.jpg', 'm:\\images\\G2520h2.jpg', 'm:\\images\\G2520h5.jpg', 'm:\\images\\G2520h6.jpg', '', 'm:\\images\\PKCZ00-07.jpg', 'm:\\images\\pkcz00-07-a.jpg', 'm:\\images\\pkcz00-07-5.jpg', 'm:\\images\\pkcz00-07-8.jpg', 'm:\\images\\pkcz00-07-7.jpg', 'm:\\images\\PKCZ00450-a.jpg', 'm:\\images\\HW055-056q.jpg', 'm:\\images\\HW067-068q.jpg', 'm:\\images\\HW086-087q2.jpg', 'm:\\images\\HW086-087q3.jpg', 'm:\\images\\HW086-087q4.jpg', 'm:\\images\\HW086-087q5.jpg', 'm:\\images\\pkcz00516-4.jpg', 'm:\\images\\M69-020h4.jpg', 'm:\\images\\G1177+M98-086b.jpg', 'm:\\images\\wonderkamer-1juni2005.jpg', 'm:\\images\\G2478-02a.jpg', 'm:\\images\\G2478-03a.jpg', 'm:\\images\\G2478-04a.jpg', 'm:\\images\\G2478-05a.jpg', 'm:\\images\\G2478-06a.jpg', 'm:\\images\\G2478-07a.jpg', 'm:\\images\\G2478-08a.jpg', 'm:\\images\\G2478-09a.jpg', 'm:\\images\\G2478-10a.jpg', 'm:\\images\\G2478-11a.jpg', 'm:\\images\\G2478-12a.jpg', 'm:\\images\\G2478-13a.jpg', 'm:\\images\\G2478-14a.jpg', 'm:\\images\\G2478-15a.jpg', 'm:\\images\\G2478-16a.jpg', 'm:\\images\\G2478-17a.jpg', 'm:\\images\\G2478-18a.jpg', 'm:\\images\\G2478-19a.jpg', 'm:\\images\\G2478-20a.jpg', 'm:\\images\\G2478-21a.jpg', 'm:\\images\\G2478-22a.jpg', 'm:\\images\\G2478-23a.jpg', 'm:\\images\\G2478-24a.jpg', 'm:\\images\\G2478-25a.jpg', 'm:\\images\\G2478-26a.jpg', 'm:\\images\\G2478-27a.jpg', 'm:\\images\\G2478-33a.jpg', 'm:\\images\\g2478-34a.jpg', 'm:\\images\\G2478-07b.jpg', 'm:\\images\\G2478b.jpg', 'm:\\images\\G2478c.jpg', 'm:\\images\\G2478d.jpg', 'm:\\images\\G2891a1.jpg', 'm:\\images\\G2702-019.jpg', 'm:\\images\\ZM-4mei2005-3.jpg', 'm:\\images\\ZM-4mei2005-pano.jpg', 'm:\\images\\3600-Z-8064qk1.jpg', 'M:\\Images\\ROUWKOSTUUM-V1.JPG', 'M:\\images\\G1846-01Q.JPG', 'm:\\images\\3600-Z-3166-01.jpg', 'M:\\images\\G2518-12.JPG', 'M:\\images\\M75-068-01.JPG', 'm:\\images\\M81-026qa.jpg', 'm:\\images\\M81-027qa.jpg', 'm:\\images\\M81-031qa.jpg', 'm:\\images\\G2355-02.jpg', 'm:\\images\\G2355-03.jpg', 'm:\\images\\G2355-04.jpg', 'm:\\images\\G2520h1.jpg', 'm:\\images\\G2891a.jpg', 'm:\\images\\M10-114.JPG', 'm:\\images\\M10-115.JPG', 'm:\\images\\M10-116.JPG', 'm:\\images\\HW041-042q1.jpg', 'm:\\images\\PKCZ00154-2ecta.jpg', 'm:\\images\\PKCZ00154-3ecta.jpg', 'm:\\images\\PKCZ00154-4ecta.jpg', 'm:\\images\\PKCZ00154-5ecta.jpg', 'm:\\images\\PKCZ00154-6ecta.jpg', 'm:\\images\\PKCZ00154-8ecta.jpg', 'm:\\images\\PKCZ00154-9ecta.jpg', 'm:\\images\\PKCZ00154-10ecta.jpg', 'm:\\images\\PKCZ00154-11ecta.jpg', 'm:\\images\\PKCZ00154-12ecta.jpg', 'm:\\images\\PKCZ00154-13ecta.jpg', 'm:\\images\\PKCZ00154-14ecta.jpg', 'm:\\images\\PKCZ00154-15ecta.jpg', 'm:\\images\\PKCZ00154-17ecta.jpg', 'm:\\images\\M89-056foto.jpg', 'm:\\images\\M90-012foto.jpg', 'm:\\images\\PKCZ00443foto.jpg', 'm:\\images\\PKCZ94-05.jpg', 'm:\\images\\PKCZ96-19.jpg', 'm:\\images\\PKCZ99-10.jpg', 'm:\\images\\PKCZ00468.jpg', 'm:\\images\\PKCZ92-12b.jpg', 'm:\\images\\PKCZ96-20-a.jpg', 'm:\\images\\PKCZ01-14-07.jpg', 'm:\\images\\BR98-056-BR98-057.jpg', 'm:\\images\\M64-104.jpg', 'm:\\images\\br86-24a.jpg', 'm:\\images\\PKCZ00-02-01.jpg', 'm:\\images\\PKCZ93-04.jpg', 'm:\\images\\PKCZ98-73.jpg', 'm:\\images\\ZG959.jpg', 'm:\\images\\PKCZ00-01.jpg', 'm:\\images\\PKCZ00-15.jpg', 'm:\\images\\ab1103a.jpg', 'm:\\images\\wonderkamer-24mei2006-02.jpg', 'm:\\images\\1327-21.jpg', 'm:\\images\\G1177+M98-086a.jpg', 'm:\\images\\pkcz00130.jpg', 'm:\\images\\G2352-01h.jpg', 'm:\\images\\G2352-01k1.jpg', 'm:\\images\\G2243-BC01.jpg', 'm:\\images\\AB1767-07.jpg', 'm:\\images\\AB1476-03k1.jpg', 'm:\\images\\AB1767-08.jpg', 'm:\\images\\AB1469-02-k1.jpg', 'm:\\images\\AB1473-06k1.jpg', 'm:\\images\\AB1767-03.jpg', 'm:\\images\\AB1030qk1.jpg', 'm:\\images\\AB1767-04.jpg', 'm:\\images\\AB1767-01a.jpg', 'm:\\images\\G2698-01.jpg', 'm:\\images\\M66-014-04-1.jpg', 'm:\\images\\AB1593qk1.jpg', 'm:\\images\\AB1593qk2.jpg', 'm:\\images\\AB1593qk3.jpg', 'm:\\images\\AB1593qk4.jpg', 'm:\\images\\AB1203q.jpg', 'm:\\images\\AB1474q.jpg', 'm:\\images\\PKCZ00167-4.jpg', 'm:\\images\\PKCZ00167-5.jpg', 'm:\\images\\PKCZ00167-6.jpg', 'm:\\images\\PKCZ00167-7.jpg', 'm:\\images\\PKCZ00167-8.jpg', 'm:\\images\\PKCZ00167-9.jpg', 'm:\\images\\PKCZ00167-10.jpg', 'm:\\images\\PKCZ00167-11.jpg', 'm:\\images\\PKCZ00167-12.jpg', 'm:\\images\\PKCZ00167-2.jpg', 'm:\\images\\PKCZ96-02-01.jpg', 'm:\\images\\PKCZ96-02-02.jpg', 'm:\\images\\PKCZ96-02-03.jpg', 'm:\\images\\PKCZ96-02-04.jpg', 'm:\\images\\PKCZ96-02-05.jpg', 'm:\\images\\PKCZ00518ecta.jpg', 'm:\\images\\pkcz00409-2.jpg', 'm:\\images\\PKCZ00-14.jpg', 'm:\\images\\PKCZ00-02-02.jpg', 'm:\\images\\PKCZ00-02-03.jpg', 'm:\\images\\PKCZ00-02-04.jpg', 'm:\\images\\PKCZ00-02-05.jpg', 'm:\\images\\PKCZ00233-a.jpg', 'm:\\images\\pkcz00083.jpg', 'm:\\images\\PKCZ00475.jpg', 'm:\\images\\PKCZ94-22-a.jpg', 'm:\\images\\PKCZ94-22-b.jpg', 'm:\\images\\PKCZ94-22-c.jpg', 'm:\\images\\PKCZ94-22-d.jpg', 'm:\\images\\PKCZ94-22-e.jpg', 'm:\\images\\PKCZ94-22-f.jpg', 'm:\\images\\PKCZ94-22-g.jpg', 'm:\\images\\PKCZ94-22-h.jpg', 'm:\\images\\PKCZ94-22-i.jpg', 'm:\\images\\PKCZ94-22-j.jpg', 'm:\\images\\PKCZ94-22-k.jpg', 'm:\\images\\PKCZ94-22-l.jpg', 'm:\\images\\PKCZ94-22-m.jpg', 'm:\\images\\PKCZ94-22-n.jpg', 'm:\\images\\PKCZ94-22-o.jpg', 'm:\\images\\PKCZ94-22-p.jpg', 'm:\\images\\PKCZ94-22-q.jpg', 'm:\\images\\PKCZ94-22-r.jpg', 'm:\\images\\PKCZ94-22-s.jpg', 'm:\\images\\PKCZ94-22-t.jpg', 'm:\\images\\PKCZ94-22-u.jpg', 'm:\\images\\PKCZ94-22-v.jpg', 'm:\\images\\PKCZ94-22-w.jpg', 'm:\\images\\PKCZ94-22-x.jpg', 'm:\\images\\G1707-G1708sb.jpg', 'm:\\images\\M91-015-021h.jpg', 'm:\\images\\G0299sb.jpg', 'm:\\images\\PKCZ92-02-01.jpg', 'm:\\images\\PKCZ92-02-02.jpg', 'm:\\images\\PKCZ92-02-03.jpg', 'm:\\images\\PKCZ92-02-04.jpg', 'm:\\images\\PKCZ92-02-05.jpg', 'm:\\images\\PKCZ92-02-06.jpg', 'm:\\images\\pkcz00545.jpg', 'm:\\images\\pkcz00154-05.jpg', 'm:\\images\\AB1590-4.jpg', 'm:\\images\\AB1591.jpg', 'm:\\images\\AB1525.jpg', 'm:\\images\\AB1604.jpg', 'm:\\images\\AB1581.jpg', 'm:\\images\\AB1083.jpg', 'm:\\images\\AB1133-2.jpg', 'm:\\images\\AB1143-5.jpg', 'm:\\images\\ab1440.jpg', 'm:\\images\\AB1601.jpg', 'm:\\images\\AB1530.jpg', 'm:\\images\\AB1563.jpg', 'm:\\images\\AB1576a.jpg', 'm:\\images\\AB1433.jpg', 'm:\\images\\AB1551.jpg', 'm:\\images\\AB1129.jpg', 'm:\\images\\AB1129b.jpg', 'm:\\images\\AB1579.jpg', 'm:\\images\\AB1515.jpg', 'm:\\images\\G1198sb.jpg', 'm:\\images\\G3360-06.jpg', 'm:\\images\\G3360-07.jpg', 'm:\\images\\G2165.jpg', 'm:\\images\\725-24_25.jpg', 'm:\\images\\3600-ZG-380.jpg', 'm:\\images\\AB1629q.jpg', 'm:\\images\\AB0977.jpg', 'm:\\images\\AB1144.jpg', 'm:\\images\\AB1017qk2.jpg', 'm:\\images\\AB1017qk3.jpg', 'm:\\images\\AB1017qk4.jpg', 'm:\\images\\AB1017e.jpg', 'm:\\images\\G1431-G1412.jpg', 'm:\\images\\G2875-12.jpg', 'm:\\images\\G2700-06.jpg', 'm:\\images\\G2700-08a.jpg', 'm:\\images\\G2708-01.jpg', 'm:\\images\\G2708-05b.jpg', 'm:\\images\\G2708-11.jpg', 'm:\\images\\G2708-24k1.jpg', 'm:\\images\\G2459-05k1.jpg', 'm:\\images\\G2492-01.jpg', 'm:\\images\\M66-14-02-08.jpg', 'm:\\images\\M66-14-02-09.jpg', 'm:\\images\\M66-14-02-10.jpg', 'm:\\images\\BR78-008-051.jpg', 'm:\\images\\M62-128-13-02a.jpg', 'm:\\images\\G1707-G1708.jpg', 'm:\\images\\G2714-02.jpg', 'M:\\images\\G1467ENM09-576.JPG', 'm:\\images\\HW086-087q1.jpg', 'M:\\images\\GM2023B.JPG', 'm:\\images\\AB1771-02a.jpg', 'm:\\images\\AB1771-03a.jpg', 'm:\\images\\AB1114q.jpg', 'm:\\images\\AB1766-02.jpg', 'm:\\images\\AB1766-03.jpg', 'm:\\images\\AB1766-04.jpg', 'm:\\images\\AB1766-05.jpg', 'm:\\images\\AB1766-06.jpg', 'm:\\images\\AB1766h.jpg', 'm:\\images\\AB1166q.jpg', 'm:\\images\\AB1584f.jpg', 'm:\\images\\AB1584.jpg', 'm:\\images\\AB1036k2.jpg', 'm:\\images\\AB1036k3.jpg', 'm:\\images\\AB1036k4.jpg', 'm:\\images\\AB1025qk2.jpg', 'm:\\images\\AB1025qk3.jpg', 'm:\\images\\AB1025qk4.jpg', 'm:\\images\\AB1485q.jpg', 'm:\\images\\M86-004q.jpg', 'm:\\images\\BR00-003a.jpg', 'M:\\images\\G2518-7.JPG', 'm:\\images\\B191-32+34-1.jpg', 'm:\\images\\B191-32+34-2.jpg', 'm:\\images\\B191-005-01A.JPG', 'm:\\images\\B191-005-01B.JPG', 'm:\\images\\B191-005-02A.JPG', 'm:\\images\\B191-005-02B.JPG', 'm:\\images\\AB1099q.jpg', 'm:\\images\\AB1522q.jpg', 'm:\\images\\AB1514.jpg', 'm:\\images\\AB1514q.jpg', 'm:\\images\\AB1383a.jpg', 'm:\\images\\AB1520q.jpg', 'm:\\images\\ab1428-02c.jpg', 'm:\\images\\pkcz00022.jpg', 'm:\\images\\PKCZ94-24foto.jpg', 'm:\\images\\pkcz00084-01a.jpg', 'm:\\images\\pkcz00199-2.jpg', 'm:\\images\\pkcz00199-3.jpg', 'm:\\images\\pkcz00199-4.jpg', 'm:\\images\\pkcz00089-2.jpg', 'm:\\images\\PKCZ92-03.jpg', 'm:\\images\\PKCZ94-25-a-k.jpg', 'm:\\images\\PKCZ96-08.jpg', 'm:\\images\\pkcz92-04-2.jpg', 'm:\\images\\PKCZ00272-Becta.jpg', 'm:\\images\\PKCZ92-12.jpg', 'm:\\images\\pkcz93-08-9.jpg', 'm:\\images\\pkcz00455.jpg', 'm:\\images\\pkcz00455 a.jpg', 'm:\\images\\pkcz00456.jpg', 'm:\\images\\pkcz00457.jpg', 'm:\\images\\pkcz00458.jpg', 'm:\\images\\pkcz00459.jpg', 'm:\\images\\pkcz00460.jpg', 'm:\\images\\pkcz00461.jpg', 'm:\\images\\pkcz00462.jpg', 'm:\\images\\pkcz00463.jpg', 'm:\\images\\pkcz00464.jpg', 'm:\\images\\pkcz00465.jpg', 'm:\\images\\pkcz00466.jpg', 'm:\\images\\pkcz00469.jpg', 'm:\\images\\pkcz00470.jpg', 'm:\\images\\pkcz00471.jpg', 'm:\\images\\G1184a.jpg', 'm:\\images\\G2478-01a.jpg', 'm:\\images\\M66-014-05-2.jpg', 'm:\\images\\G2352-01k2.jpg', 'm:\\images\\G2495-001a.jpg', 'm:\\images\\G2485-01a.jpg', 'm:\\images\\M96-013-01a.jpg', 'm:\\images\\G1184-02a.jpg', 'm:\\images\\M66-14-02-11.jpg', 'm:\\images\\M81-029q.jpg', 'm:\\images\\AB1604a.jpg', 'm:\\images\\Br91-012q.jpg', 'm:\\images\\Br99-005j.jpg', 'm:\\images\\G3655g.jpg', 'm:\\images\\G3689a.jpg', 'm:\\images\\G2484-01a.jpg', 'm:\\images\\G2484-02a.jpg', 'm:\\images\\G2484-03a.jpg', 'm:\\images\\G2484-04a.jpg', 'm:\\images\\br03-001a.jpg', 'm:\\images\\br03-001b.jpg', 'm:\\images\\M73-041a.jpg', 'm:\\images\\AB1584a.jpg', 'm:\\images\\HANS WARREN 103A.jpg', 'm:\\images\\HANS WARREN 154.jpg', 'm:\\images\\HANS WARREN 164.jpg', 'm:\\images\\HANS WARREN 173.jpg', 'm:\\images\\PKCZ00084 01.jpg', 'm:\\images\\PKCZ00075-1.jpg', 'm:\\images\\PKCZ00075-2.jpg', 'm:\\images\\M04-005.jpg', 'M:\\images\\G03-050.JPG', 'm:\\images\\G0533a.jpg', 'm:\\images\\AB1766-01.jpg', 'm:\\images\\AB1036k1.jpg', 'm:\\images\\ab1421.jpg', 'm:\\images\\AB1025qk1.jpg', 'M:\\images\\M64-66.JPG', 'M:\\images\\M75-068-02.JPG', 'm:\\images\\3600-3189QB.JPG', 'm:\\images\\3600-4795A.JPG', 'm:\\images\\3600-7596-01Q1.JPG', 'm:\\images\\3600-Z-9004a.jpg', 'm:\\images\\AB1354-02.jpg', 'm:\\images\\B191-036A.JPG', 'm:\\images\\B191-8q.jpg', 'm:\\images\\B191-8ma.jpg', 'm:\\images\\pkcz00-07-2b.jpg', 'm:\\images\\pkcz00-09.jpg', 'm:\\images\\pkcz00305scan.jpg', 'm:\\images\\pkcz00128-129.jpg', 'm:\\images\\pkcz00488.jpg', 'm:\\images\\pkcz 92-05.jpg', 'm:\\images\\pkcz00552-1.jpg', 'm:\\images\\pkcz98-79 -3.jpg', 'm:\\images\\pkcz00552.jpg', 'm:\\images\\pkcz01-02-6.jpg', 'm:\\images\\pkcz01-02-5.jpg', 'm:\\images\\pkcz01-02-4.jpg', 'm:\\images\\pkcz01-02-3.jpg', 'm:\\images\\pkcz01-02-2.jpg', 'm:\\images\\pkcz01-02-1.jpg', 'm:\\images\\pkcz00175-01.jpg', 'm:\\images\\pkcz00089-3.jpg', 'm:\\images\\PKCZ00167-1.jpg', 'm:\\images\\pkcz00199-1.jpg', 'm:\\images\\M10-139.jpg', 'm:\\images\\PKCZ00095-01.jpg', 'm:\\images\\PKCZ00095-02.jpg', 'm:\\images\\pkcz00410-1.jpg', 'm:\\images\\pkcz00410-2.jpg', 'm:\\images\\pkcz00410-3.jpg', 'm:\\images\\pkcz00410-4.jpg', 'm:\\images\\pkcz00410-5.jpg', 'm:\\images\\pkcz00294-1.jpg', 'm:\\images\\pkcz00294-2.jpg', 'm:\\images\\pkcz00294-3.jpg', 'm:\\images\\pkcz00488-01.jpg', 'm:\\images\\pkcz00409-1.jpg', 'm:\\images\\pkcz00516.jpg', 'm:\\images\\AB1102a.jpg', 'm:\\images\\AB1476-05k1.jpg', 'm:\\images\\AB0953-01k1.jpg', 'm:\\images\\AB1758-01.jpg', 'm:\\images\\AB1104q.jpg', 'm:\\images\\AB1770-01a.jpg', 'm:\\images\\ab1431k1.jpg', 'm:\\images\\PKCZ00073-01.jpg', 'm:\\images\\ZNA046.jpg', 'm:\\images\\M04-057.jpg', 'm:\\images\\PKCZ04-022.jpg', 'm:\\images\\pkcz00-008-02.jpg', 'm:\\images\\AB1577k1.jpg', 'm:\\images\\AB1698-01Q.JPG', 'm:\\images\\3600-ZG-380a.jpg', 'M:\\images\\M01-044+M01-045.JPG', 'm:\\images\\M64-129.jpg', 'm:\\images\\G1198.jpg', 'm:\\images\\M64-171-15a.jpg', 'm:\\images\\pkcz00282 1.jpg', 'm:\\images\\pkcz00107.jpg', 'm:\\images\\pkcz00174b.jpg', 'm:\\images\\pkcz00174a.jpg', 'm:\\images\\pkcz00330-1.jpg', 'm:\\images\\pkcz00309 a.jpg', 'm:\\images\\pkcz00024-2.jpg', 'm:\\images\\pkcz00024-4.jpg', 'm:\\images\\pkcz00024-3.jpg', 'm:\\images\\pkcz00024-1.jpg', 'm:\\images\\pkcz00194-2.jpg', 'm:\\images\\pkcz00194-3.jpg', 'm:\\images\\pkcz00194-4.jpg', 'm:\\images\\pkcz00074-1.jpg', 'm:\\images\\pkcz00074-3.jpg', 'm:\\images\\pkcz00074-5.jpg', 'm:\\images\\pkcz00242-01.jpg', 'm:\\images\\pkcz00242-02.jpg', 'm:\\images\\pkcz00242-03.jpg', 'm:\\images\\pkcz00242-04.jpg', 'm:\\images\\pkcz00301.jpg', 'm:\\images\\pkcz00301a.jpg', 'm:\\images\\pkcz00201-2.jpg', 'm:\\images\\pkcz00201-3.jpg', 'm:\\images\\pkcz00201-4.jpg', 'm:\\images\\pkcz00201-5.jpg', 'm:\\images\\pkcz00201-1.jpg', 'M:\\images\\AE.1956.0006.0003.JPG', 'M:\\images\\Christoffelmedaille - voorbeeldfoto.jpg', 'M:\\images\\VOORBEELD HOOFDBOEK2.JPG', 'm:\\images\\BR93-002.jpg', 'm:\\images\\br99-005.jpg', 'm:\\images\\G3465c.jpg', 'm:\\images\\AB1571.jpg', 'm:\\images\\AB1023qk1.jpg', 'm:\\images\\AB1585a.jpg', 'm:\\images\\AB1024qk1.jpg', 'm:\\images\\M01-006-02.jpg', 'm:\\images\\M95-005&006qa.jpg', 'm:\\images\\M91-015-021.jpg', 'm:\\images\\M93-018-11a.jpg', 'm:\\images\\m62-102.jpg', 'm:\\images\\M78-013.jpg', 'm:\\images\\G2654a.jpg', 'm:\\images\\G1402.jpg', 'm:\\images\\M79-018.jpg', 'm:\\images\\G3620a.jpg', 'm:\\images\\G3620b.jpg', 'm:\\images\\3600-BEV-Z-100m.jpg', 'm:\\images\\3600-BEV-Z-100a1.jpg', 'm:\\images\\3600-BEV-Z-100a2.jpg', 'm:\\images\\3600-BEV-Z-100bw.jpg', 'm:\\images\\AB0972-02a-2.jpg', 'm:\\images\\AB1516-01e.jpg', 'm:\\images\\M68-35-01.jpg', 'm:\\images\\G2480-036g.jpg', 'm:\\images\\G1650a.jpg', 'm:\\images\\m11-011a1.jpg', 'm:\\images\\m11-011a2.jpg', 'm:\\images\\m11-011a3.jpg', 'm:\\images\\G0299.jpg', 'm:\\images\\M06-018.jpg', 'm:\\images\\M70-056a.jpg', 'm:\\images\\M67-238.jpg', 'm:\\images\\ab1402.jpg', 'm:\\images\\AB1038qk1.jpg', 'm:\\images\\pkcz00406-01.jpg', 'm:\\images\\pkcz00406-03.jpg', 'm:\\images\\pkcz00406-02.jpg', 'm:\\images\\M10-005.JPG', 'm:\\images\\M10-006-01.JPG', 'm:\\images\\BP025f1.jpg', 'm:\\images\\BP025f3.jpg', 'm:\\images\\BP028f3.jpg', 'm:\\images\\BP029f1.jpg', 'm:\\images\\BP029f3.jpg', 'm:\\images\\BP031L1.jpg', 'm:\\images\\BP031L2.jpg', 'm:\\images\\BP033f1.jpg', 'm:\\images\\BP033f2.jpg', 'm:\\images\\BP038f1.jpg', 'm:\\images\\BP059m2.jpg', 'm:\\images\\M66-014-05-1a.jpg', 'm:\\images\\G0697 tm G0704.jpg', 'm:\\images\\3600-Z-7587.jpg', 'm:\\images\\3600-Z-7588.jpg', 'm:\\images\\3600-Z-7589.jpg', 'm:\\images\\3600-Z-3165a.jpg', 'M:\\images\\3600-Z-8064-02&-03Q1.JPG', 'M:\\images\\3600-Z-8064-02&-03Q2.JPG', 'm:\\images\\M91-014qb.jpg', 'm:\\images\\G2352-01k3.jpg', 'm:\\images\\G2352-01k4.jpg', 'm:\\images\\G2352-01-02.jpg', 'm:\\images\\G2352-02-02.jpg', 'm:\\images\\G2352-02k1.jpg', 'm:\\images\\G2352-02k2.jpg', 'm:\\images\\G2352-02k3.jpg', 'm:\\images\\G2352-02k4.jpg', 'm:\\images\\G2495-001b.jpg', 'm:\\images\\G2495-002b.jpg', 'm:\\images\\G2495-003b.jpg', 'm:\\images\\G2495-004b.jpg', 'm:\\images\\G2495-005b.jpg', 'm:\\images\\G2495-006b.jpg', 'm:\\images\\G2495-007b.jpg', 'm:\\images\\G2495-008b.jpg', 'm:\\images\\M96-013-01b.jpg', 'm:\\images\\M96-013h.jpg', 'm:\\images\\M87-088foto.jpg', 'm:\\images\\wonderkamer-24mei2006-01a.jpg', 'm:\\images\\wonderkamer-24mei2006-03.jpg', 'm:\\images\\wonderkamer-24mei2006-04.jpg', 'm:\\images\\wonderkamer-24mei2006-05.jpg', 'm:\\images\\wonderkamer-24mei2006-06.jpg', 'm:\\images\\wonderkamer-24mei2006-07.jpg', 'm:\\images\\wonderkamer-24mei2006-08.jpg', 'm:\\images\\ZM-26april2006-10.jpg', 'm:\\images\\ZM-26april2006-10-2.jpg', 'm:\\images\\M81-029-01h1.jpg', 'm:\\images\\M81-029-01h2.jpg', 'm:\\images\\M81-029-02-h1.jpg', 'm:\\images\\M81-029-04h1.jpg', 'm:\\images\\M81-029-04h2.jpg', 'm:\\images\\M81-029-05h1.jpg', 'm:\\images\\M81-029-05h2.jpg', 'm:\\images\\M81-030h1.jpg', 'm:\\images\\M81-031-01h1.jpg', 'M:\\images\\M96-047-07+08.JPG', 'm:\\images\\AB1026qk1.jpg', 'm:\\images\\ab1420.jpg', 'm:\\images\\AB1083j.jpg', 'm:\\images\\AB1754-01a.jpg', 'm:\\images\\AB1354-01.jpg', 'm:\\images\\AB0940a.jpg', 'm:\\images\\AB1119q.jpg', 'm:\\images\\AB1082q.jpg', 'm:\\images\\AB1022qk1.jpg', 'm:\\images\\1420-1_zn0024.jpg', 'm:\\images\\1420q.jpg', 'm:\\images\\598-22.jpg', 'm:\\images\\C1591-01a1.jpg', 'm:\\images\\2405.jpg', 'm:\\images\\HANS WARREN 076.jpg', 'm:\\images\\HANS WARREN 004.jpg', 'm:\\images\\HANS WARREN 047.jpg', 'm:\\images\\HANS WARREN 122.jpg', 'm:\\images\\HANS WARREN 126.jpg', 'm:\\images\\HANS WARREN 201.jpg', 'm:\\images\\HANS WARREN 138B.jpg', 'm:\\images\\HANS WARREN 066.jpg', 'm:\\images\\GRAF 76-01.JPG', 'm:\\images\\GRAF 104.JPG', 'm:\\images\\AB1592qk1.jpg', 'm:\\images\\AB1592qk2.jpg', 'm:\\images\\AB1592qk3.jpg', 'm:\\images\\AB1592qk4.jpg', 'm:\\images\\AB1562k1.jpg', 'm:\\images\\AB1562k2.jpg', 'm:\\images\\AB1562k3.jpg', 'm:\\images\\wonderkamer-8juni2005.jpg', 'm:\\images\\wonderkamer-8juni2005-2.jpg', 'm:\\images\\wonderkamer-8juni2005-3.jpg', 'M:\\images\\AB1135q1.jpg', 'm:\\images\\wonderkamer-18mei2005.jpg', 'm:\\images\\wonderkamer-18mei2005-2.jpg', 'm:\\images\\G2243-01-02-03.jpg', 'm:\\images\\G2243-04-05-09.jpg', 'm:\\images\\G2243-06-07-08.jpg', 'm:\\images\\G2243-BC02.jpg', 'm:\\images\\G2243-BC03.jpg', 'm:\\images\\G2243-BC04.jpg', 'm:\\images\\G2243-BC05.jpg', 'm:\\images\\G3266b.jpg', 'm:\\images\\wonderkamer-overzicht.jpg', 'm:\\images\\wonderkamer-30nov2005-vitrine.jpg', 'm:\\images\\wonderkamer-30nov2005-03.jpg', 'm:\\images\\wonderkamer-30nov2005-02.jpg', 'm:\\images\\wonderkamer-30nov2005-04.jpg', 'm:\\images\\wonderkamer-30nov2005-05.jpg', 'm:\\images\\Br78-008-006-01q.jpg', 'm:\\images\\ZE445l.jpg', 'm:\\images\\G3657q.jpg', 'm:\\images\\G3654q.jpg', 'm:\\images\\G3689m.jpg', 'm:\\images\\G3689q.jpg', 'm:\\images\\pkcz94-19-ac.jpg', 'm:\\images\\PKCZ94-19.jpg', 'm:\\images\\PKCZ95-03.jpg', 'm:\\images\\PKCZ92-07.jpg', 'm:\\images\\G2480-056b.jpg', 'm:\\images\\PKC00521foto.jpg', 'm:\\images\\PKCZ00522.jpg', 'm:\\images\\G2480-037k2.jpg', 'm:\\images\\G2480-037k3.jpg', 'm:\\images\\G2480-037k4.jpg', 'm:\\images\\GA0119_0121.jpg', 'm:\\images\\ZM-3mei2006-06.jpg', 'm:\\images\\ZM-3mei2006-10.jpg', 'm:\\images\\G0533b.jpg', 'm:\\images\\G0533c.jpg', 'm:\\images\\G0533d.jpg', 'm:\\images\\pkcz00-07-1.jpg', 'm:\\images\\PKCZ00-07-2.jpg', 'm:\\images\\pkcz00-07-3.jpg', 'm:\\images\\pkcz00-07-4.jpg', 'm:\\images\\PKCZ00154-7ecta.jpg', 'm:\\images\\PKCZ00-10foto.jpg', 'm:\\images\\pkcz00-11.jpg', 'm:\\images\\PKCZ96-20-b.jpg', 'm:\\images\\PKCZ96-20-c.jpg', 'm:\\images\\PKCZ96-20-d.jpg', 'm:\\images\\PKCZ96-20-e.jpg', 'm:\\images\\PKCZ96-20-f.jpg', 'm:\\images\\PKCZ97-01.jpg', 'm:\\images\\pkcz00272.jpg', 'm:\\images\\ab1422-01.jpg', 'm:\\images\\AB1563q1.jpg', 'm:\\images\\AB1551j.jpg', 'm:\\images\\G2517-02.jpg', 'm:\\images\\G2517-04.jpg', 'm:\\images\\G2517-05.jpg', 'm:\\images\\G1463.jpg', 'm:\\images\\M91-005foto.jpg', 'm:\\images\\pkcz00395scan.jpg', 'm:\\images\\PKCZ00113foto.jpg', 'm:\\images\\PKCZ00544foto.jpg', 'm:\\images\\G0531-002.jpg', 'm:\\images\\PKCZ00431-2foto.jpg', 'm:\\images\\G3451.jpg', 'm:\\images\\G2480-01.jpg', 'm:\\images\\AB1592.jpg', 'm:\\images\\pkcz00092.jpg', 'm:\\images\\pkcz00193a.jpg', 'm:\\images\\pkcz00445.jpg', 'm:\\images\\M90-038-17.jpg', 'm:\\images\\G2714.jpg', 'm:\\images\\ab1542.jpg', 'm:\\images\\ab1542b.jpg', 'm:\\images\\ZE445.jpg', 'm:\\images\\PKCZ04-023.jpg', 'm:\\images\\3600-Z-8064qk2.jpg', 'm:\\images\\G3702q.jpg', 'm:\\images\\M81-026qb.jpg', 'm:\\images\\M81-027qb.jpg', 'm:\\images\\M81-031qb.jpg', 'm:\\images\\BP032.jpg', 'm:\\images\\BP031.jpg', 'm:\\images\\BP032f.jpg', 'm:\\images\\BP033.jpg', 'm:\\images\\BP034.jpg', 'm:\\images\\BP035.jpg', 'm:\\images\\BP036.jpg', 'm:\\images\\BP037f.jpg', 'm:\\images\\BP038f2.jpg', 'm:\\images\\BP039f1.jpg', 'm:\\images\\BP039f2.jpg', 'm:\\images\\BP040f1.jpg', 'm:\\images\\BP041f.jpg', 'm:\\images\\BP042f.jpg', 'm:\\images\\BP043.jpg', 'm:\\images\\BP044.jpg', 'm:\\images\\BP045f1.jpg', 'm:\\images\\BP045f2.jpg', 'm:\\images\\BP046.jpg', 'm:\\images\\BP047f1.jpg', 'm:\\images\\BP047f2.jpg', 'm:\\images\\BP048a.jpg', 'm:\\images\\BP048d.jpg', 'm:\\images\\BP048m1.jpg', 'm:\\images\\BP048m2.jpg', 'm:\\images\\BP048m3.jpg', 'm:\\images\\BP048m4.jpg', 'm:\\images\\BP048m5.jpg', 'm:\\images\\BP048m6.jpg', 'm:\\images\\BP048m7.jpg', 'm:\\images\\BP049.jpg', 'm:\\images\\BP050.jpg', 'm:\\images\\BP051-01.jpg', 'm:\\images\\BP051-02f1.jpg', 'm:\\images\\BP051-02f2.jpg', 'm:\\images\\BP052.jpg', 'm:\\images\\BP053.jpg', 'm:\\images\\BP054.jpg', 'm:\\images\\BP055.jpg', 'm:\\images\\BP056.jpg', 'm:\\images\\BP057.jpg', 'm:\\images\\BP059a.jpg', 'm:\\images\\BP059m1.jpg', 'm:\\images\\BP062.jpg', 'm:\\images\\BP062h.jpg', 'm:\\images\\BP064.jpg', 'm:\\images\\BP066.jpg', 'm:\\images\\BP068.jpg', 'm:\\images\\G2357-01.jpg', 'm:\\images\\G2357-02.jpg', 'm:\\images\\G2558-01f1.jpg', 'm:\\images\\G2558-01f2.jpg', 'm:\\images\\G2558-02.jpg', 'm:\\images\\M63-135.jpg', 'm:\\images\\M63-135m1.jpg', 'm:\\images\\M63-135m2.jpg', 'm:\\images\\G2357-07.jpg', 'm:\\images\\BP013.jpg', 'm:\\images\\BP014.jpg', 'm:\\images\\BP015.jpg', 'm:\\images\\BP016.jpg', 'm:\\images\\BP017.jpg', 'm:\\images\\BP018.jpg', 'm:\\images\\BP019.jpg', 'm:\\images\\BP020.jpg', 'm:\\images\\BP021.jpg', 'm:\\images\\BP022.jpg', 'm:\\images\\BP024.jpg', 'm:\\images\\BP023.jpg', 'm:\\images\\BP025.jpg', 'm:\\images\\BP025f2.jpg', 'm:\\images\\BP026.jpg', 'm:\\images\\BP026f.jpg', 'm:\\images\\BP027.jpg', 'm:\\images\\BP027f.jpg', 'm:\\images\\BP028.jpg', 'm:\\images\\BP028f1.jpg', 'm:\\images\\BP028f2.jpg', 'm:\\images\\BP029.jpg', 'm:\\images\\BP029f2.jpg', 'm:\\images\\BP030.jpg', 'm:\\images\\BP030f1.jpg', 'm:\\images\\BP030f2.jpg', 'm:\\images\\G3711q.jpg', 'm:\\images\\HW041-042q2.jpg', 'm:\\images\\HW041-042q3.jpg', 'm:\\images\\HW041-042q4.jpg', 'm:\\images\\M90-014ecta.jpg', 'm:\\images\\AB1496.jpg', 'm:\\images\\AB1578.jpg', 'm:\\images\\AB1589.jpg', 'm:\\images\\AB1589qk1.jpg', 'm:\\images\\AB1589qk2.jpg', 'm:\\images\\AB1589qk4.jpg', 'm:\\images\\AB1589qk3.jpg', 'm:\\images\\AB1572q.jpg', 'm:\\images\\AB1113q.jpg', 'm:\\images\\AB1577k2.jpg', 'm:\\images\\AB1408J.jpg', 'm:\\images\\ab1085.jpg', 'm:\\images\\AB1085q.jpg', 'm:\\images\\AB1084qk1.jpg', 'm:\\images\\AB1084qk2.jpg', 'm:\\images\\AB1084qk3.jpg', 'm:\\images\\AB1084qk4.jpg', 'm:\\images\\AB1097q.jpg', 'm:\\images\\AB1097qe.jpg', 'm:\\images\\AB1615qk1.jpg', 'm:\\images\\AB1615qk2.jpg', 'm:\\images\\AB1611qk1.jpg', 'm:\\images\\AB1611qk2.jpg', 'm:\\images\\AB1617q.jpg', 'm:\\images\\AB1580.jpg', 'm:\\images\\AB1580qk1.jpg', 'm:\\images\\AB1580qk2.jpg', 'm:\\images\\AB1610q.jpg', 'm:\\images\\AB1595q.jpg', 'm:\\images\\AB1608q.jpg', 'm:\\images\\AB1607qk1.jpg', 'm:\\images\\AB1607qk2.jpg', 'm:\\images\\AB1607qk3.jpg', 'm:\\images\\AB1123q.jpg', 'm:\\images\\AB1631q.jpg', 'm:\\images\\ab1410.jpg', 'm:\\images\\AB1475q1.jpg', 'm:\\images\\ab1679q.jpg', 'm:\\images\\G2700-08b.jpg', 'm:\\images\\G2700-08q.jpg', 'm:\\images\\G2708-06.jpg', 'm:\\images\\G2459-05k2.jpg', 'm:\\images\\G2459-05k3.jpg', 'm:\\images\\G2459-05k4.jpg', 'm:\\images\\G2459-06.jpg', 'm:\\images\\G2459q.jpg', 'm:\\images\\BR78-008-050c.jpg', 'm:\\images\\wonderkamer-17mei2006-01.jpg', 'm:\\images\\wonderkamer-17mei2006-02.jpg', 'm:\\images\\wonderkamer-17mei2006-03.jpg', 'm:\\images\\3600-BEV-Z-67q.jpg', 'm:\\images\\3600-BEV-Z-67qm.jpg', 'm:\\images\\M64-102-01-02-03.jpg', 'm:\\images\\M86-035a2.jpg', 'm:\\images\\M86-035b.jpg', 'm:\\images\\G2714-01.jpg', 'm:\\images\\G2714-04.jpg', 'm:\\images\\M04-057-01h.jpg', 'm:\\images\\M04-057-02h.jpg', 'm:\\images\\M04-057-03h.jpg', 'm:\\images\\M04-057b.jpg', 'm:\\images\\M05-014Q.jpg', 'm:\\images\\PKCZ00-08-01a.jpg', 'm:\\images\\G3465.jpg', 'M:\\images\\GA0019-G0020.JPG', 'm:\\images\\AB1571a.jpg', 'm:\\images\\AB1585.jpg', 'm:\\images\\AB1612a.jpg']

DEBUG = False
RUNNING = True

class Updater:
    
    def __init__(self, APIMigrator):
        self.api = APIMigrator
        self.dev = False
        sync_utils = SyncUtils(self)
        self.utils = sync_utils

    def log(self, text=""):
        if DEBUG:
            if text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')
                final_log = "[%s] %s" %(str(timestamp), str(text))
            else:
                pass
        elif RUNNING:
            if "STATUS" in text or "ERROR" in text or "Warning" in text:
                timestamp = datetime.datetime.today().isoformat()
                text = text.encode('ascii', 'ignore')

                final_log = "[%s]__%s" %(str(timestamp), str(text).replace('\n', ''))
                list_log = final_log.split('__')

                if ".lref" not in text and "Warning" not in text and "STATUS" not in text:
                    
                    self.error_wr.writerow(list_log)

                if "Warning" in text or ".lref" in text or "STATUS" in text:
                    wr = csv.writer(self.warning_log_file, quoting=csv.QUOTE_ALL)
                    self.warning_wr.writerow(list_log)

            else:
                pass

    def get_field(self, fieldname):
        for name, field in self.fields:
            if name == fieldname:
                return field
        return None

    def empty_fields(self, obj):
        for name, field in self.fields:
            field_type = self.get_fieldtype_by_schema(field)
            if field_type == "list":
                setattr(obj, name, [])
            elif field_type == "relation":
                setattr(obj, name, [])

        return True

    def fix_all_choices(self, obj):
        for name, field in self.fields:
            field_type = self.get_fieldtype_by_schema(field)
            if field_type == "datagridfield":
                obj_field = getattr(obj, name, None)
                if obj_field:
                    for line in obj_field:
                        for key in line:
                            if line[key] == "_No value":
                                line[key] = "No value"
                            elif line[key] == ['no value']:
                                line[key] = []
                            elif line[key] == 'False':
                                line[key] = False
                    setattr(obj, name, obj_field)
        return True


    def get_subfield(self, plone_fieldname):
        split_name = plone_fieldname.split('-')
        if len(split_name) > 1:
            return split_name[1]
        else:
            return None

    def get_schema_gridfield(self, fieldname):
        field = self.get_field(fieldname)
        gridfield_schema = {}
        schema = field.value_type.schema
        for name, field in getFieldsInOrder(schema):
            gridfield_schema[name] = self.get_default_value_by_schema(field)

        return gridfield_schema


    def get_objecttype_relation(self, plone_fieldname):

        relation_type = ""
        for name, field in self.fields:
            if name == plone_fieldname:
                try:
                    portal_type = field.value_type.source.selectable_filter.criteria['portal_type'][0]
                    return portal_type, False
                except:
                    if plone_fieldname in relation_types:
                        return relation_type[plone_fieldname], True
                    else:
                        self.error("Cannot get portal_type of relation.")
        
        if not relation_type:
            if plone_fieldname in relation_types:
                return relation_types[plone_fieldname], True

        self.error("%s__%s__Cannot find type of relation" %(self.object_number, self.xml_path))
        return None, None

    def get_type_of_subfield(self, plone_fieldname):
        if plone_fieldname in subfields_types:
            return subfields_types[plone_fieldname]
        else:
            return "text"

    def get_type_of_field(self, plone_fieldname):
        if plone_fieldname in self.field_types:
            return self.field_types[plone_fieldname]
        else:
            return None

    def get_fieldtype_by_schema(self, field):
        type_field = ""
        if IRelationList.providedBy(field):
            type_field = "relation"
        elif IDatetime.providedBy(field):
            type_field = "date"
        elif "ListField" in str(field) or "ListRelatedField" in str(field):
            type_field = "datagridfield"
            self.datagrids[field.__name__] = False
        elif IChoice.providedBy(field):
            type_field = "choice"
        elif ITextLine.providedBy(field):
            type_field = "text"
        elif IList.providedBy(field):
            type_field = "list"
        elif IText.providedBy(field):
            type_field = "text"
        elif IRichText.providedBy(field):
            type_field = "text"
        elif IBool.providedBy(field):
            type_field = 'bool'
        else:
            type_field = "unknown"

        return type_field

    def get_default_value_by_schema(self, field):
        type_field = " "
        if IRelationList.providedBy(field):
            type_field = ['no value']
        elif "ListField" in str(field) or "ListRelatedField" in str(field):
            type_field = ['no value']
            self.datagrids[field.__name__] = False
        elif IChoice.providedBy(field):
            type_field = "_No value"
        elif ITextLine.providedBy(field):
            type_field = " "
        elif IList.providedBy(field):
            type_field = ['no value']
        elif IText.providedBy(field):
            type_field = " "
        elif IRichText.providedBy(field):
            type_field = " "
        elif IBool.providedBy(field):
            type_field = 'False'
        elif IDatetime.providedBy(field):
            type_field = None
        else:
            type_field = " "

        return type_field

    def generate_field_types(self):
        for name, field in self.fields:
            type_field = self.get_fieldtype_by_schema(field)
            self.field_types[name] = type_field

        self.field_types['title'] = "text"
        self.field_types['description'] = 'text'


    def create_relation(self, current_value, objecttype_relatedto, priref, grid=False, by_name=False):
        intids = component.getUtility(IIntIds)

        if grid:
            current_value = []

        #current_value = []
        if objecttype_relatedto == "Taxonomie":
            if by_name:
                taxonomies = self.api.find_taxonomie_by_name(priref)
                if len(taxonomies) > 1:
                    taxonomy = taxonomies[0]
                    other_taxonomies = [str(p.priref) for p in taxonomies[1:]]
                    self.error("%s__%s__Relation with more than one result. First result: %s Other results: %s" %(str(self.object_number), str(self.xml_path), person.priref, str(other_taxonomies)))
                else:
                    if taxonomies:
                        taxonomy = taxonomies[0]
                    else:
                        taxonomy = None
                        self.error("%s__%s__Cannot create relation with content type Taxonomie with name '%s'" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))
                        return current_value
            else:
                taxonomy = self.api.find_taxonomie_by_priref(priref)
            
            if taxonomy:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(taxonomy)
                    relation_value = RelationValue(person_id)
                    for relation in current_value:
                        if relation.to_object.id == taxonomy.id:
                            self.warning("%s__%s__Taxonomie Relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(taxonomy)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                try:
                    self.error("%s__%s__Cannot create relation with content type Taxonomie with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                except:
                    self.error("%s__%s__Cannot create relation with content type Taxonomie with priref %s" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))

        
        elif objecttype_relatedto == "PersonOrInstitution":
            if by_name:
                persons = self.api.find_person_by_name(priref)
                if len(persons) > 1:
                    person = persons[0]
                    other_persons = [str(p.priref) for p in persons[1:]]
                    self.error("%s__%s__Relation with more than one result. First result: %s Other results: %s" %(str(self.object_number), str(self.xml_path), person.priref, str(other_persons)))
                else:
                    if persons:
                        person = persons[0]
                    else:
                        person = None
                        self.error("%s__%s__Cannot create relation with content type PersonOrInstitution with name '%s'" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))
                        return current_value
            else:
                person = self.api.find_person_by_priref(self.api.all_persons, priref)

            if person:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(person)
                    relation_value = RelationValue(person_id)
                    for relation in current_value:
                        if relation.to_object.id == person.id:
                            self.warning("%s__%s__PersonOrInstitution Relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    intids = component.getUtility(IIntIds)
                    person_id = intids.getId(person)
                    relation_value = RelationValue(person_id)
                    current_value.append(relation_value)
            else:
                try:
                    self.error("%s__%s__Cannot create relation with content type PersonOrInstitution with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                except:
                    self.error("%s__%s__Cannot create relation with content type PersonOrInstitution with priref %s" %(str(self.object_number), str(self.xml_path), str(priref.encode('ascii', 'ignore'))))

        elif objecttype_relatedto == "Object":
            obj = self.api.find_object(self.api.all_objects, priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    
                    if len(current_value) == 0:
                        current_value = []

                    for relation in current_value:
                        if relation.to_object.identification_identification_objectNumber == priref:
                            self.warning("%s__%s__Object relation already created with object number %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type Object with object number %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Exhibition":
            obj = self.api.find_exhibition_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Exhibition relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type Exhibition with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Archive":
            obj = self.api.find_archive_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Archive relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type Archive priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Serial":
            obj = self.api.find_serial_by_priref(priref)
            if obj:
                if not grid:
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Serial relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type Serial priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "treatment":
            obj = self.api.find_treatment_by_treatmentnumber(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Treatment relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type Treatment with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "OutgoingLoan":
            obj = self.api.find_outgoingloan_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Outgoing loan relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type OutgoingLoan with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "IncomingLoan":
            obj = self.api.find_incomingloan_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__IncomingLoan relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type IncomingLoan with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Article":
            obj = self.api.find_article_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Article relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type Article priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "Bibliotheek":
            obj = self.api.find_bibliotheek_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__Bibliotheek relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value
                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with an item from the Bibliotheek with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))

        elif objecttype_relatedto == "ObjectEntry":
            obj = self.api.find_objectentry_by_priref(priref)
            if obj:
                if not grid:
                    #current_value = []
                    intids = component.getUtility(IIntIds)
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    for relation in current_value:
                        if relation.to_object.id == obj.id:
                            self.warning("%s__%s__ObjectEntry relation already created with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                            return current_value

                    current_value.append(relation_value)
                else:
                    current_value = []
                    obj_id = intids.getId(obj)
                    relation_value = RelationValue(obj_id)
                    current_value.append(relation_value)
            else:
                self.error("%s__%s__Cannot create relation with content type ObjectEntry with priref %s" %(str(self.object_number), str(self.xml_path), str(priref)))
                
        else:
            self.error("%s__%s__Relation type not available %s" %(str(self.object_number), str(self.xml_path), str(objecttype_relatedto)))


        return current_value

    def log_status(self, text, use_timestamp=True):
        if text:
            timestamp = datetime.datetime.today().isoformat()
            text = text.encode('ascii', 'ignore')
            if not use_timestamp:
                final_log = "%s" %(str(text))
            else:
                final_log = "[%s]__%s" %(str(timestamp), str(text))
            
            list_log = final_log.split('__')
            print final_log.replace('__', ' ')
            self.status_wr.writerow(list_log)
        else:
            return True

    def error(self, text="", object_number="", xml_path="", value=""):
        if text:
            self.log("%s%s" %("[ ERROR ]__", text))
        else:
            if not object_number:
                object_numnber = "None"
            if not xml_path:
                xml_path = "No path"
            if not value:
                value = "No value"
            value.encode('ascii', 'ignore')

            self.log("%s%s__%s__%s" %("[ ERROR ]__", object_number, xml_path, value))

        return True

    def warning(self, text="", object_number="", xml_path="", value=""):
        try:
            if text:
                self.log("%s%s" %("[ Warning ]__", text))
            else:
                if not object_number:
                    object_numnber = "None"
                if not xml_path:
                    xml_path = "No path"
                if not value:
                    value = "No value"
                value.encode('ascii', 'ignore')

                self.log("%s%s__%s__%s" %("[ Warning ]__", object_number, xml_path, value))

            return True
        except:
            return True


    def get_object_number(self, xml_record, portal_type=""):
        if portal_type != "Object":
            if portal_type == "IncomingLoan":
                return xml_record.find('loan_number').text

            if portal_type == "Image":
                if xml_record.find('image_reference') != None:
                    return xml_record.find('image_reference').text

            else:
                if xml_record.find('priref') != None:
                    return xml_record.find('priref').text
        else:
            if xml_record.find('object_number') != None:
                return xml_record.find('object_number').text

        return None
    
    def get_xml_path(self, xml_element):
        xml_path = re.sub("\[[^]]*\]", '', self.xml_root.getpath(xml_element).replace("/adlibXML/recordList/record", "").replace("/", "-"))
        if len(xml_path) > 0:
            if xml_path[0] == "-":
                if len(xml_path) > 1:
                    xml_path = xml_path[1:]

        return xml_path

    def check_dictionary(self, xml_path):
        if xml_path in CORE.keys():
            return CORE[xml_path]

        return False

    def escape_empty_string(self, old_value):
        value = old_value
        for val in value:
            for k in val:
                if val[k] == " ":
                    val[k] = ""

        return value


    def update_dictionary_new(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        updated = False
        found = False

        # Check if first choice
        if subfield_type == "choice":
            if "taxonomy.rank" in self.xml_path:
                value = value
            elif type(value) == list:
                return current_value
            elif xml_element.get('option') != "" and xml_element.get('option') != None:
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    value = ""
            elif xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
                return current_value

        for line in current_value:
            if subfield in line:
                found = True

                if subfield_type == "choice":
                    if line[subfield] == '_No value' and value == "":
                        line[subfield] = 'No value'
                        updated = True
                        break
                    elif line[subfield] == '_No value' and value != "":
                        line[subfield] = value
                        updated = True
                        break
                    else:
                        # there's a value - try next line
                        pass
                elif subfield_type == "gridlist" or subfield_type == "relation":
                    if line[subfield] == ['no value'] and value == []:
                        line[subfield] = []
                        updated = True
                        break
                    elif line[subfield] == ['no value'] and value != []:
                        line[subfield] = value
                        updated = True
                        break
                    else:
                        # there's a value - try next line
                        pass
                elif subfield_type == "bool":
                    if line[subfield] == 'False':
                        line[subfield] = value
                        updated = True
                        break
                    else: 
                        # there's a value - try next line
                        pass
                else:
                    if line[subfield] == ' ':
                        line[subfield] = value
                        updated = True
                        break
                    else:
                        # there's a value - try next line
                        pass

        # Not found
        if not found:
            return current_value

        # Found
        if not updated:
            # create new row
            val = self.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value

    def create_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        if subfield_type == "choice":
            if value == "":
                value = "No value"

            if "taxonomy.rank" in self.xml_path:
                value = value
            elif xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
                return current_value

        new_value = self.get_schema_gridfield(plone_fieldroot)

        if subfield not in new_value:
            return current_value
            
        new_value[subfield] = value
        current_value.append(new_value)

        return current_value

    # Handle datagridfield 
    def handle_datagridfield(self, current_value, xml_path, xml_element, plone_fieldname):
        subfield = self.get_subfield(plone_fieldname)
        plone_fieldroot = plone_fieldname.split('-')[0]
        subfield_type = self.get_type_of_subfield(xml_path)

        if not self.datagrids[plone_fieldroot]:
            current_value = []
            self.datagrids[plone_fieldroot] = True
        else:
            self.datagrids[plone_fieldroot] = True

        if current_value == None:
            current_value = []

        length = len(current_value)
        field_value = None

        if subfield:
            if length:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.update_dictionary_new(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
            else:
                new_value = self.transform_all_types(xml_element, subfield_type, current_value, xml_path, xml_path)
                field_value = self.create_dictionary(subfield, current_value, new_value, xml_element, subfield_type, plone_fieldroot)
        else:
            self.error("Badly formed CORE dictionary for repeatable field: %s" %(plone_fieldname))

        return field_value

    def transform_all_types(self, xml_element, field_type, current_value, xml_path, plone_fieldname, grid=False):

        # Text
        if field_type == "text":
            return self.api.trim_white_spaces(xml_element.text)

        elif field_type == "date":
            field_val = self.api.trim_white_spaces(xml_element.text)
            if field_val:
                try:
                    try: 
                        datetime_value = datetime.datetime.strptime(field_val, "%Y-%m-%d")
                        value = pytz.utc.localize(datetime_value)
                    except:
                        value_split = field_val.split('-')
                        if len(value_split) == 2:
                            new_date = "%s-%s" %(field_val, "01")
                            datetime_value = datetime.datetime.strptime(new_date, "%Y-%m-%d")
                            value = pytz.utc.localize(datetime_value)
                        else:
                            year = field_val
                            new_date = "%s-%s-%s" %(year, "01", "01")
                            datetime_value = datetime.datetime.strptime(new_date, "%Y-%m-%d")
                            value = pytz.utc.localize(datetime_value)
                except:
                    self.error("%s__%s__Unable to create datetime value. %s"%(str(self.object_number), str(xml_path), str(field_val)))
                    return ""
            else:
                return ""

        elif field_type == "choice":
            if "taxonomy.rank" in self.xml_path:
                value = xml_element.get("value")
                if value:
                    if len(xml_element.findall('text')) > 0:
                        value = xml_element.find('text').text
                        if value:
                            return value
                        else:
                            return ""
                    else:
                        return ""
                else:
                    return ""

            if xml_element.get('language') == "0" and xml_element.get('language') != "" and xml_element.get('language') != None: # first entry
                value = self.api.trim_white_spaces(xml_element.text)
                if value == "":
                    return ""
                else:
                    return value

            elif xml_element.get("option") != "" and xml_element.get("option") != None: # empty entry
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    return ""
            elif xml_element.tag == "term":
                return xml_element.text
            else: # rest of the languages_keep the same value
                return current_value
        
        # Vocabulary
        elif field_type == "list":
            if current_value != None:
                new_value = self.api.trim_white_spaces(xml_element.text)
                try:
                    if new_value not in current_value:
                        if new_value:
                            current_value.append(self.api.trim_white_spaces(xml_element.text))
                    else:
                        try:
                            self.warning("%s__%s__Value already in vocabulary %s"%(str(self.object_number), str(self.xml_path), str(new_value.encode('ascii','ignore'))))
                        except:
                            pass
                except:
                    self.error("%s__%s__Not possible to add value to the vocabulary %s"%(str(self.object_number), str(self.xml_path), str(new_value.encode('ascii','ignore'))))
                
                value = current_value
            else:
                value = [self.api.trim_white_spaces(xml_element.text)]

        elif field_type == "gridlist":
            new_value = self.api.trim_white_spaces(xml_element.text)
            if new_value != None and new_value != "":
                value = [new_value]
            else:
                value = []

        # Create relation type
        elif field_type == "relation":
            value = []
            by_name = False
            objecttype_relatedto, grid = self.get_objecttype_relation(plone_fieldname)
            if objecttype_relatedto == "Object":
                linkref = xml_element.get('linkdata')
                if not linkref:
                    linkref = xml_element.get('linkterm')
                    if not linkref:
                        if xml_element.find('object_number') != None:
                            linkref = xml_element.find('object_number').text
                        else:
                            linkref = ""

            elif objecttype_relatedto == "PersonOrInstitution":
                linkref = xml_element.get('linkref')
                if not linkref:
                    linkdata = xml_element.get('linkdata')
                    if linkdata:
                        linkref = linkdata
                        by_name = True
                    else:
                        linkref = ""

            elif objecttype_relatedto == "Taxonomie":
                linkref = xml_element.get('linkref')
                if not linkref:
                    linkref = xml_element.get('priref')
                    if not linkref:
                        linkdata = xml_element.get('linkdata')
                        if linkdata:
                            linkref = linkdata
                            by_name = True
                        else:
                            linkref = ""

            elif objecttype_relatedto == "Serial":
                linkref = xml_element.get('linkref')
                if not linkref:
                    linkdata = xml_element.get('linkdata')
                    linkref = linkdata
                            
            elif objecttype_relatedto == "treatment":
                linkref = xml_element.text
            else:
                linkref = xml_element.get('linkref')

            value = self.create_relation(current_value, objecttype_relatedto, linkref, grid, by_name)

        elif field_type == "bool":
            if xml_element.text == "x":
                return True
            else:
                return False

        elif field_type == "datagridfield":
            value = self.handle_datagridfield(current_value, xml_path, xml_element, plone_fieldname)
        
        # Unknown
        else:
            value = None
            self.error("Unkown type of field for fieldname %s" %(plone_fieldname))

        return value

    def setattribute(self, plone_object, plone_fieldname, field_type, value):
        if value != None:
            if field_type == "choice" and (value == "" or value == " "):
                value = "No value"
            setattr(plone_object, plone_fieldname, value)
        else:
            self.error("Value to be set is None. field: %s" %(plone_fieldname))

    def write(self, xml_path, xml_element, plone_object, object_number):

        plone_fieldname = self.check_dictionary(xml_path)
        
        if plone_fieldname:
            plone_fieldroot = plone_fieldname.split('-')[0]
            has_field = hasattr(plone_object, plone_fieldroot)
            

            if has_field:
                current_value = getattr(plone_object, plone_fieldroot)
                field_type = self.get_type_of_field(plone_fieldroot)
                value = self.transform_all_types(xml_element, field_type, current_value, xml_path, plone_fieldname)
                self.setattribute(plone_object, plone_fieldroot, field_type, value)
            else:
                self.error("Field not available in Plone object: %s" %(plone_fieldroot))

        elif plone_fieldname == "":
            self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))

        else:
            if ".lref" in xml_path:
                self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))
            else:
                if xml_path == "":
                    xml_path = xml_element.tag
                    if (xml_path == "record") or ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(object_number, xml_path, xml_element.text))
                else:
                    if ("parts_reference" in xml_path) or ("Child" in xml_path) or ("Synonym" in xml_path):
                        self.warning("%s__%s__Tag was ignored. %s" %(object_number, xml_path, xml_element.text))
                    else:
                        self.error("%s__%s__Tag not found in dictionary. %s" %(object_number, xml_path, xml_element.text))

        return True

    def update(self, xml_record, plone_object, object_number):
        
        # Iterate the whole tree
        for element in xml_record.iter():
            xml_path = self.get_xml_path(element)
            self.xml_path = xml_path
            self.write(xml_path, element, plone_object, object_number)

        return True

    def get_required_field_by_type(self, xml_record):
        title = ""
        if self.portal_type == "Taxonomie":
            if xml_record.find("scientific_name") != None:
                title = xml_record.find("scientific_name").text

        elif self.portal_type == "Object":
            if xml_record.find("object_number") != None:
                title = xml_record.find("object_number").text

        elif self.portal_type == "treatment":
            if xml_record.find("treatment_number") != None:
                title = xml_record.find("treatment_number").text

        elif self.portal_type == "IncomingLoan":
            if xml_record.find("loan_number") != None:
                title = xml_record.find("loan_number").text

        elif self.portal_type == "ObjectEntry":
            if xml_record.find("transport_number") != None:
                title = xml_record.find("transport_number").text

        elif self.portal_type == "OutgoingLoan":
            if xml_record.find("loan_number") != None:
                title = xml_record.find("loan_number").text

        elif self.portal_type == "Exhibition":
            if xml_record.find("title") != None:
                title = xml_record.find("title").text

        elif self.portal_type == "Book":
            if xml_record.find("title") != None:
                title = xml_record.find("title").text

        else:
            self.error("Content type not supported to be created.")
        return title

    def get_title_by_type(self, xml_record):
        title = ""
        if self.portal_type == "Taxonomie":
            if xml_record.find("scientific_name") != None:
                title = xml_record.find("scientific_name").text

        elif self.portal_type == "Object":
            if xml_record.find("title") != None:
                title = xml_record.find("title").text
        elif self.portal_type == "treatment":
            if xml_record.find("treatment_number") != None:
                title = xml_record.find("treatment_number").text
        
        elif self.portal_type == "IncomingLoan":
            if xml_record.find("loan_number") != None:
                title = xml_record.find("loan_number").text

        elif self.portal_type == "OutgoingLoan":
            if xml_record.find("loan_number") != None:
                title = xml_record.find("loan_number").text

        elif self.portal_type == "ObjectEntry":
            if xml_record.find("transport_number") != None:
                title = xml_record.find("transport_number").text

        elif self.portal_type == "Exhibition":
            if xml_record.find("title") != None:
                title = xml_record.find("title").text

        elif self.portal_type == "Book":
            if xml_record.find("title") != None:
                title = xml_record.find("title").text

        else:
            self.error("Content type not supported to be created.")
        return title

    def create_object(self, xml_record):

        REQUIRED_FIELDS = {
            "Taxonomie": "title",
            "Object": "object_number",
            "treatment":"title",
            "IncomingLoan":"title",
            "ObjectEntry": "title",
            "OutgoingLoan": "title",
            "Exhibition": "title",
            "Book":"title",
        }
        required_field = REQUIRED_FIELDS[self.portal_type]

        container = self.api.get_folder('nl/intern/bruiklenen/uitgaande-bruiklenen')
        title = self.get_title_by_type(xml_record)
        required_field_value = self.get_required_field_by_type(xml_record)

        dirty_id = "%s %s"%(str(self.object_number), str(title.encode('ascii', 'ignore')))
        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

        container.invokeFactory(
            type_name=self.portal_type,
            id=normalized_id,
            title=title
        )

        created_object = container[str(normalized_id)]
        created_object.portal_workflow.doActionFor(created_object, "publish", comment="Item published")

        setattr(created_object, required_field, required_field_value)

        return created_object

    def init_log_files(self):
        timestamp = datetime.datetime.today().isoformat()

        self.error_path = "/var/www/zm-collectie-v3/logs/error_%s_%s.csv" %(self.portal_type, str(timestamp))
        self.error_path_dev = "/Users/AG/Projects/collectie-zm/logs/error_%s_%s.csv" %(self.portal_type, str(timestamp))
        
        self.warning_path = "/var/www/zm-collectie-v3/logs/warning_%s_%s.csv" %(self.portal_type, str(timestamp))
        self.warning_path_dev = "/Users/AG/Projects/collectie-zm/logs/warning_%s_%s.csv" %(self.portal_type, str(timestamp))
        
        self.status_path_dev = "/Users/AG/Projects/collectie-zm/logs/status_%s_%s.csv" %(self.portal_type, str(timestamp))
        self.status_path = "/var/www/zm-collectie-v3/logs/status_%s_%s.csv" %(self.portal_type, str(timestamp))

        if self.dev:
            self.error_log_file = open(self.error_path_dev, "w+")
            self.warning_log_file = open(self.warning_path_dev, "w+")
            self.status_log_file = open(self.status_path_dev, "w+")
        else:
            self.error_log_file = open(self.error_path, "w+")
            self.warning_log_file = open(self.warning_path, "w+")
            self.status_log_file = open(self.status_path, "w+")

        self.error_wr = csv.writer(self.error_log_file, quoting=csv.QUOTE_ALL)
        self.warning_wr = csv.writer(self.warning_log_file, quoting=csv.QUOTE_ALL)
        self.status_wr = csv.writer(self.status_log_file, quoting=csv.QUOTE_ALL)

    def close_files(self):
        self.error_log_file.close()
        self.warning_log_file.close()
        self.status_log_file.close()

    def init_fields(self):
        
        self.collection = []
        self.xml_root = []
        self.schema = getUtility(IDexterityFTI, name=self.portal_type).lookupSchema()
        self.fields = getFieldsInOrder(self.schema)

        if self.portal_type == "Exhibition":
            self.exhibition_fields = getFieldsInOrder(IEventBasic)
            self.fields.extend(self.exhibition_fields)

        elif self.portal_type == "Image":
            self.images_dict = {}
            self.images_ref_dict = {}
            for img in list(self.api.all_images)[:10000]:
                img_obj = img.getObject()
                ref = img_obj.reproductionData_identification_identifierURL
                #_id = img.id
                #self.images_dict[_id] = img
                if ref:
                    if ref in self.images_ref_dict:
                        self.images_ref_dict[ref].append(img)
                    else:
                        self.images_ref_dict[ref] = list()
                        self.images_ref_dict[ref].append(img)

            self.image_reference_fields = getFieldsInOrder(IImageReference)
            self.fields.extend(self.image_reference_fields)

        self.field_types = {}
        self.datagrids = {}
        self.object_number = ""
        self.xml_path = ""

    def start(self):

        indexes = (
                    ('associations_associatedSubjects_subject','KeywordIndex'),
                    ('associations_associatedSubjects_period','KeywordIndex'),
                    ('associations_associatedSubjects_association','KeywordIndex'),
                    ('conditionConservation_conditions_condition','KeywordIndex'),
                    ('conditionConservation_preservationForms','KeywordIndex'),
                    ('fieldCollection_fieldCollection_collector_role','KeywordIndex'),
                    ('fieldCollection_fieldCollection_method','KeywordIndex'),
                    ('fieldCollection_fieldCollection_place','KeywordIndex'),
                    ('fieldCollection_fieldCollection_placeFeature','KeywordIndex'),
                    ('fieldCollection_habitatAndStratigraphy_stratigraphy','KeywordIndex'),
                    ('fieldCollection_fieldCollection_event','KeywordIndex'),
                    ('fieldCollection_fieldCollection_placeCode','KeywordIndex'),
                    ('fieldCollection_fieldCollection_placeCodeType','KeywordIndex'),
                    ('iconography_generalSearchCriteria_generalThemes','KeywordIndex'),
                    ('iconography_generalSearchCriteria_specificThemes','KeywordIndex'),
                    ('iconography_contentsubjects','KeywordIndex'),
                    ('identification_objectName_objectname_type','KeywordIndex'),
                    ('identification_identification_collection','KeywordIndex'),
                    ('inscriptionsMarkings_inscriptionsAndMarkings_type','KeywordIndex'),
                    ('inscriptionsMarkings_inscriptionsAndMarkings_role','KeywordIndex'),
                    ('inscriptionsMarkings_inscriptionsAndMarkings_script','KeywordIndex'),
                    ('location_normalLocation_normallocation','KeywordIndex'),
                    ('location_currentlocation','KeywordIndex'),
                    ('ownershipHistory_history_exchangeMethods','KeywordIndex'),
                    ('ownershipHistory_history_places','KeywordIndex'),
                    ('physicalCharacteristics_techniques','KeywordIndex'),
                    ('physicalCharacteristics_materials','KeywordIndex'),
                    ('physicalCharacteristics_dimensions','KeywordIndex'),
                    ('physicalCharacteristics_keyword_aspect','KeywordIndex'),
                    ('physicalCharacteristics_keyword_keyword','KeywordIndex'),
                    ('productionDating_production_productionRole','KeywordIndex'),
                    ('productionDating_production_productionPlace','KeywordIndex'),
                    ('productionDating_production_schoolStyle','KeywordIndex'),
                    ('productionDating_production_period','KeywordIndex'),
                    ('acquisition_method','KeywordIndex'),
                    ('acquisition_place','KeywordIndex'),
                    ('valueInsurance_valuations_currency','KeywordIndex'),
                    ('numbersRelationships_relationshipsWithOtherObjects_relatedObjects_association','KeywordIndex')
                )

        self.utils.create_indexes(indexes)

        self.api.success = True
        return True

    def import_entire_collection(self, content_types):
        self.dev = False

        for content_type in content_types:
            self.portal_type = content_type
            self.import_portaltypes_utils(self.portal_type)
            self.init_fields()
            self.init_log_files()

            collection_xml = CONTENT_TYPES_PATH[self.portal_type]['prod']['total']
            self.collection, self.xml_root = self.api.get_zm_collection(collection_xml)

            self.generate_field_types()
            self.import_contenttype(content_type)
            self.close_files()
        return True

    def import_contenttype(self, contenttype):
        total = len(list(self.collection))
        curr, limit = 0, 0
        create_new = False

        for xml_record in list(self.collection):
            try:
                curr += 1
                transaction.begin()
                
                self.object_number = ""

                object_number = self.get_object_number(xml_record, self.portal_type)

                if object_number:
                    if object_number in RESTRICTIONS or len(RESTRICTIONS) == 0:
                        self.object_number = object_number
                        #plone_object = ""
                        if self.portal_type == "Image":
                            plone_object = self.find_image_by_id(object_number)
                        else:
                            plone_object = self.api.find_item_by_type(object_number, self.portal_type)

                        if plone_object:
                            if self.portal_type == "Image":
                                plone_object = IImageReference(plone_object)

                            if self.portal_type == "Exhibition":
                                plone_object.start = ""
                                plone_object.end = ""
                                plone_object.whole_day = True

                            self.object_number = str(object_number)
                            self.generate_field_types()
                            self.log_status("! STATUS !__Updating [%s] %s / %s" %(str(object_number), str(curr), str(total)))
                            self.empty_fields(plone_object)
                            self.update(xml_record, plone_object, object_number)
                            self.log_status("! STATUS !__Updated [%s] %s / %s" %(str(object_number), str(curr), str(total)))
                            self.log_status("! STATUS !__URL: %s" %(str(plone_object.absolute_url())))
                            self.fix_all_choices(plone_object)

                            if self.portal_type == "Exhibition":
                                if plone_object.start:
                                    IEventBasic(plone_object).start = plone_object.start
                                if plone_object.end:
                                    IEventBasic(plone_object).end = plone_object.end
                            
                            plone_object.reindexObject() 
                        else:
                            if create_new:
                                created_object = self.create_object(xml_record)
                                self.update(xml_record, created_object, object_number)
                                self.fix_all_choices(created_object)
                                created_object.reindexObject()
                                self.log_status("%s__ __New object created with type %s."%(str(object_number), str(self.portal_type)))
                                self.log_status("! STATUS !__URL: %s" %(str(created_object.absolute_url())))
                            else:
                                self.error("%s__ __Object is not found on Plone with priref/object_number."%(str(object_number))) 
                    else:
                        continue

                else:
                    self.error("%s__ __Cannot find object number/priref in XML record"%(str(curr)))
                    #continue

                transaction.commit()
            except Exception, e:
                self.error(" __ __An unknown exception ocurred. %s" %(str(e)))
                raise

    


