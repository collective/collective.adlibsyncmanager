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

DEBUG = False
RUNNING = True

IDENTIFIERS = ['m:\\images\\M79-028.jpg', 'M:\\images\\M79-032.JPG', 'm:\\images\\M66-14-02-06.jpg', 'm:\\images\\G1929.jpg', 'm:\\images\\G2732q.jpg', 'm:\\images\\M66-14-02-07.jpg', 'm:\\images\\G2707-01a.jpg', 'm:\\images\\pkcz00274-02.jpg', 'm:\\images\\M79-004.jpg', 'm:\\images\\G1875a.jpg', 'm:\\images\\G1222q.jpg', 'm:\\images\\AB0955-01k1.jpg', 'm:\\images\\AB1035qk1.jpg', 'm:\\images\\AB1017qk1.jpg', 'm:\\images\\AB1033qk1.jpg', 'm:\\images\\AB1767-06.jpg', 'm:\\images\\G1184q.jpg', 'm:\\images\\Br72-005-01 Veere 1.jpg', 'm:\\images\\G2619-01.jpg', 'm:\\images\\M62-010 & m62-012.jpg', 'm:\\images\\M86-035a1.jpg', 'm:\\images\\G2900-01a.jpg', 'm:\\images\\M93-018-01a.jpg', 'm:\\images\\M66-14-02-01.jpg', 'm:\\images\\M66-14-02-02.jpg', 'm:\\images\\G1446-01a.jpg', 'M:\\images\\M96-047-01-04a.jpg', 'm:\\images\\M66-14-02-05.jpg', 'm:\\images\\M91-014qa.jpg', 'm:\\images\\wonderkamer31mei2006-1.jpg', 'm:\\images\\AB1771-01a.jpg', 'm:\\images\\AB1175k1.jpg', 'm:\\images\\ab1431k2.jpg', 'm:\\images\\AB1207q.jpg', 'm:\\images\\AB1137q.jpg', 'm:\\images\\ab1136.jpg', 'm:\\images\\AB1668q.jpg', 'm:\\images\\AB1470-01k1.jpg', 'm:\\images\\AB1470-02k1.jpg', 'm:\\images\\AB1470-03k1.jpg', 'm:\\images\\AB1470-04k1.jpg', 'm:\\images\\AB1470-05k1.jpg', 'm:\\images\\AB1559q.jpg', 'm:\\images\\AB0955-03k1.jpg', 'm:\\images\\AB1476-03k2.jpg', 'm:\\images\\AB1476-03k3.jpg', 'm:\\images\\AB1476-03k4.jpg', 'm:\\images\\AB1469-02-k2.jpg', 'm:\\images\\AB1469-02-k3.jpg', 'm:\\images\\AB1469-02-k4.jpg', 'm:\\images\\AB1473q.jpg', 'm:\\images\\AB1599q1.jpg', 'm:\\images\\AB1599q2.jpg', 'm:\\images\\ab1422-02.jpg', 'm:\\images\\AB1614qk1.jpg', 'm:\\images\\AB1614qk2.jpg', 'm:\\images\\AB1754-02a.jpg', 'm:\\images\\AB1524q.jpg', 'm:\\images\\G1198a.jpg', 'm:\\images\\wonderkamer-15juni2005.jpg', 'm:\\images\\ZM-15juni2005-31.jpg', 'm:\\images\\BR00-001-02h1.jpg', 'm:\\images\\G2492-02.jpg', 'm:\\images\\G2492-03.jpg', 'm:\\images\\G2492-04.jpg', 'm:\\images\\G2492-05.jpg', 'm:\\images\\G2492-06.jpg', 'm:\\images\\G2492-08.jpg', 'm:\\images\\G2520h3.jpg', 'm:\\images\\G2520h4.jpg', 'm:\\images\\G2520h2.jpg', 'm:\\images\\G2520h5.jpg', 'm:\\images\\G2520h6.jpg', '', 'm:\\images\\PKCZ00-07.jpg', 'm:\\images\\pkcz00-07-a.jpg', 'm:\\images\\pkcz00-07-5.jpg', 'm:\\images\\pkcz00-07-8.jpg', 'm:\\images\\pkcz00-07-7.jpg', 'm:\\images\\PKCZ00450-a.jpg', 'm:\\images\\HW055-056q.jpg', 'm:\\images\\HW067-068q.jpg', 'm:\\images\\HW086-087q2.jpg', 'm:\\images\\HW086-087q3.jpg', 'm:\\images\\HW086-087q4.jpg', 'm:\\images\\HW086-087q5.jpg', 'm:\\images\\pkcz00516-4.jpg', 'm:\\images\\M69-020h4.jpg', 'm:\\images\\G1177+M98-086b.jpg', 'm:\\images\\wonderkamer-1juni2005.jpg', 'm:\\images\\G2478-02a.jpg', 'm:\\images\\G2478-03a.jpg', 'm:\\images\\G2478-04a.jpg', 'm:\\images\\G2478-05a.jpg', 'm:\\images\\G2478-06a.jpg', 'm:\\images\\G2478-07a.jpg', 'm:\\images\\G2478-08a.jpg', 'm:\\images\\G2478-09a.jpg', 'm:\\images\\G2478-10a.jpg', 'm:\\images\\G2478-11a.jpg', 'm:\\images\\G2478-12a.jpg', 'm:\\images\\G2478-13a.jpg', 'm:\\images\\G2478-14a.jpg', 'm:\\images\\G2478-15a.jpg', 'm:\\images\\G2478-16a.jpg', 'm:\\images\\G2478-17a.jpg', 'm:\\images\\G2478-18a.jpg', 'm:\\images\\G2478-19a.jpg', 'm:\\images\\G2478-20a.jpg', 'm:\\images\\G2478-21a.jpg', 'm:\\images\\G2478-22a.jpg', 'm:\\images\\G2478-23a.jpg', 'm:\\images\\G2478-24a.jpg', 'm:\\images\\G2478-25a.jpg', 'm:\\images\\G2478-26a.jpg', 'm:\\images\\G2478-27a.jpg', 'm:\\images\\G2478-33a.jpg', 'm:\\images\\g2478-34a.jpg', 'm:\\images\\G2478-07b.jpg', 'm:\\images\\G2478b.jpg', 'm:\\images\\G2478c.jpg', 'm:\\images\\G2478d.jpg', 'm:\\images\\G2891a1.jpg', 'm:\\images\\G2702-019.jpg', 'm:\\images\\ZM-4mei2005-3.jpg', 'm:\\images\\ZM-4mei2005-pano.jpg', 'm:\\images\\3600-Z-8064qk1.jpg', 'M:\\Images\\ROUWKOSTUUM-V1.JPG', 'M:\\images\\G1846-01Q.JPG', 'm:\\images\\3600-Z-3166-01.jpg', 'M:\\images\\G2518-12.JPG', 'M:\\images\\M75-068-01.JPG', 'm:\\images\\M81-026qa.jpg', 'm:\\images\\M81-027qa.jpg', 'm:\\images\\M81-031qa.jpg', 'm:\\images\\G2355-02.jpg', 'm:\\images\\G2355-03.jpg', 'm:\\images\\G2355-04.jpg', 'm:\\images\\G2520h1.jpg', 'm:\\images\\G2891a.jpg', 'm:\\images\\M10-114.JPG', 'm:\\images\\M10-115.JPG', 'm:\\images\\M10-116.JPG', 'm:\\images\\HW041-042q1.jpg', 'm:\\images\\PKCZ00154-2ecta.jpg', 'm:\\images\\PKCZ00154-3ecta.jpg', 'm:\\images\\PKCZ00154-4ecta.jpg', 'm:\\images\\PKCZ00154-5ecta.jpg', 'm:\\images\\PKCZ00154-6ecta.jpg', 'm:\\images\\PKCZ00154-8ecta.jpg', 'm:\\images\\PKCZ00154-9ecta.jpg', 'm:\\images\\PKCZ00154-10ecta.jpg', 'm:\\images\\PKCZ00154-11ecta.jpg', 'm:\\images\\PKCZ00154-12ecta.jpg', 'm:\\images\\PKCZ00154-13ecta.jpg', 'm:\\images\\PKCZ00154-14ecta.jpg', 'm:\\images\\PKCZ00154-15ecta.jpg', 'm:\\images\\PKCZ00154-17ecta.jpg', 'm:\\images\\M89-056foto.jpg', 'm:\\images\\M90-012foto.jpg', 'm:\\images\\PKCZ00443foto.jpg', 'm:\\images\\PKCZ94-05.jpg', 'm:\\images\\PKCZ96-19.jpg', 'm:\\images\\PKCZ99-10.jpg', 'm:\\images\\PKCZ00468.jpg', 'm:\\images\\PKCZ92-12b.jpg', 'm:\\images\\PKCZ96-20-a.jpg', 'm:\\images\\PKCZ01-14-07.jpg', 'm:\\images\\BR98-056-BR98-057.jpg', 'm:\\images\\M64-104.jpg', 'm:\\images\\br86-24a.jpg', 'm:\\images\\PKCZ00-02-01.jpg', 'm:\\images\\PKCZ93-04.jpg', 'm:\\images\\PKCZ98-73.jpg', 'm:\\images\\ZG959.jpg', 'm:\\images\\PKCZ00-01.jpg', 'm:\\images\\PKCZ00-15.jpg', 'm:\\images\\ab1103a.jpg', 'm:\\images\\wonderkamer-24mei2006-02.jpg', 'm:\\images\\1327-21.jpg', 'm:\\images\\G1177+M98-086a.jpg', 'm:\\images\\pkcz00130.jpg', 'm:\\images\\G2352-01h.jpg', 'm:\\images\\G2352-01k1.jpg', 'm:\\images\\G2243-BC01.jpg', 'm:\\images\\AB1767-07.jpg', 'm:\\images\\AB1476-03k1.jpg', 'm:\\images\\AB1767-08.jpg', 'm:\\images\\AB1469-02-k1.jpg', 'm:\\images\\AB1473-06k1.jpg', 'm:\\images\\AB1767-03.jpg', 'm:\\images\\AB1030qk1.jpg', 'm:\\images\\AB1767-04.jpg', 'm:\\images\\AB1767-01a.jpg', 'm:\\images\\G2698-01.jpg', 'm:\\images\\M66-014-04-1.jpg', 'm:\\images\\AB1593qk1.jpg', 'm:\\images\\AB1593qk2.jpg', 'm:\\images\\AB1593qk3.jpg', 'm:\\images\\AB1593qk4.jpg', 'm:\\images\\AB1203q.jpg', 'm:\\images\\AB1474q.jpg', 'm:\\images\\PKCZ00167-4.jpg', 'm:\\images\\PKCZ00167-5.jpg', 'm:\\images\\PKCZ00167-6.jpg', 'm:\\images\\PKCZ00167-7.jpg', 'm:\\images\\PKCZ00167-8.jpg', 'm:\\images\\PKCZ00167-9.jpg', 'm:\\images\\PKCZ00167-10.jpg', 'm:\\images\\PKCZ00167-11.jpg', 'm:\\images\\PKCZ00167-12.jpg', 'm:\\images\\PKCZ00167-2.jpg', 'm:\\images\\PKCZ96-02-01.jpg', 'm:\\images\\PKCZ96-02-02.jpg', 'm:\\images\\PKCZ96-02-03.jpg', 'm:\\images\\PKCZ96-02-04.jpg', 'm:\\images\\PKCZ96-02-05.jpg', 'm:\\images\\PKCZ00518ecta.jpg', 'm:\\images\\pkcz00409-2.jpg', 'm:\\images\\PKCZ00-14.jpg', 'm:\\images\\PKCZ00-02-02.jpg', 'm:\\images\\PKCZ00-02-03.jpg', 'm:\\images\\PKCZ00-02-04.jpg', 'm:\\images\\PKCZ00-02-05.jpg', 'm:\\images\\PKCZ00233-a.jpg', 'm:\\images\\pkcz00083.jpg', 'm:\\images\\PKCZ00475.jpg', 'm:\\images\\PKCZ94-22-a.jpg', 'm:\\images\\PKCZ94-22-b.jpg', 'm:\\images\\PKCZ94-22-c.jpg', 'm:\\images\\PKCZ94-22-d.jpg', 'm:\\images\\PKCZ94-22-e.jpg', 'm:\\images\\PKCZ94-22-f.jpg', 'm:\\images\\PKCZ94-22-g.jpg', 'm:\\images\\PKCZ94-22-h.jpg', 'm:\\images\\PKCZ94-22-i.jpg', 'm:\\images\\PKCZ94-22-j.jpg', 'm:\\images\\PKCZ94-22-k.jpg', 'm:\\images\\PKCZ94-22-l.jpg', 'm:\\images\\PKCZ94-22-m.jpg', 'm:\\images\\PKCZ94-22-n.jpg', 'm:\\images\\PKCZ94-22-o.jpg', 'm:\\images\\PKCZ94-22-p.jpg', 'm:\\images\\PKCZ94-22-q.jpg', 'm:\\images\\PKCZ94-22-r.jpg', 'm:\\images\\PKCZ94-22-s.jpg', 'm:\\images\\PKCZ94-22-t.jpg', 'm:\\images\\PKCZ94-22-u.jpg', 'm:\\images\\PKCZ94-22-v.jpg', 'm:\\images\\PKCZ94-22-w.jpg', 'm:\\images\\PKCZ94-22-x.jpg', 'm:\\images\\G1707-G1708sb.jpg', 'm:\\images\\M91-015-021h.jpg', 'm:\\images\\G0299sb.jpg', 'm:\\images\\PKCZ92-02-01.jpg', 'm:\\images\\PKCZ92-02-02.jpg', 'm:\\images\\PKCZ92-02-03.jpg', 'm:\\images\\PKCZ92-02-04.jpg', 'm:\\images\\PKCZ92-02-05.jpg', 'm:\\images\\PKCZ92-02-06.jpg', 'm:\\images\\pkcz00545.jpg', 'm:\\images\\pkcz00154-05.jpg', 'm:\\images\\AB1590-4.jpg', 'm:\\images\\AB1591.jpg', 'm:\\images\\AB1525.jpg', 'm:\\images\\AB1604.jpg', 'm:\\images\\AB1581.jpg', 'm:\\images\\AB1083.jpg', 'm:\\images\\AB1133-2.jpg', 'm:\\images\\AB1143-5.jpg', 'm:\\images\\ab1440.jpg', 'm:\\images\\AB1601.jpg', 'm:\\images\\AB1530.jpg', 'm:\\images\\AB1563.jpg', 'm:\\images\\AB1576a.jpg', 'm:\\images\\AB1433.jpg', 'm:\\images\\AB1551.jpg', 'm:\\images\\AB1129.jpg', 'm:\\images\\AB1129b.jpg', 'm:\\images\\AB1579.jpg', 'm:\\images\\AB1515.jpg', 'm:\\images\\G1198sb.jpg', 'm:\\images\\G3360-06.jpg', 'm:\\images\\G3360-07.jpg', 'm:\\images\\G2165.jpg', 'm:\\images\\725-24_25.jpg', 'm:\\images\\3600-ZG-380.jpg', 'm:\\images\\AB1629q.jpg', 'm:\\images\\AB0977.jpg', 'm:\\images\\AB1144.jpg', 'm:\\images\\AB1017qk2.jpg', 'm:\\images\\AB1017qk3.jpg', 'm:\\images\\AB1017qk4.jpg', 'm:\\images\\AB1017e.jpg', 'm:\\images\\G1431-G1412.jpg', 'm:\\images\\G2875-12.jpg', 'm:\\images\\G2700-06.jpg', 'm:\\images\\G2700-08a.jpg', 'm:\\images\\G2708-01.jpg', 'm:\\images\\G2708-05b.jpg', 'm:\\images\\G2708-11.jpg', 'm:\\images\\G2708-24k1.jpg', 'm:\\images\\G2459-05k1.jpg', 'm:\\images\\G2492-01.jpg', 'm:\\images\\M66-14-02-08.jpg', 'm:\\images\\M66-14-02-09.jpg', 'm:\\images\\M66-14-02-10.jpg', 'm:\\images\\BR78-008-051.jpg', 'm:\\images\\M62-128-13-02a.jpg', 'm:\\images\\G1707-G1708.jpg', 'm:\\images\\G2714-02.jpg', 'M:\\images\\G1467ENM09-576.JPG', 'm:\\images\\HW086-087q1.jpg', 'M:\\images\\GM2023B.JPG', 'm:\\images\\AB1771-02a.jpg', 'm:\\images\\AB1771-03a.jpg', 'm:\\images\\AB1114q.jpg', 'm:\\images\\AB1766-02.jpg', 'm:\\images\\AB1766-03.jpg', 'm:\\images\\AB1766-04.jpg', 'm:\\images\\AB1766-05.jpg', 'm:\\images\\AB1766-06.jpg', 'm:\\images\\AB1766h.jpg', 'm:\\images\\AB1166q.jpg', 'm:\\images\\AB1584f.jpg', 'm:\\images\\AB1584.jpg', 'm:\\images\\AB1036k2.jpg', 'm:\\images\\AB1036k3.jpg', 'm:\\images\\AB1036k4.jpg', 'm:\\images\\AB1025qk2.jpg', 'm:\\images\\AB1025qk3.jpg', 'm:\\images\\AB1025qk4.jpg', 'm:\\images\\AB1485q.jpg', 'm:\\images\\M86-004q.jpg', 'm:\\images\\BR00-003a.jpg', 'M:\\images\\G2518-7.JPG', 'm:\\images\\B191-32+34-1.jpg', 'm:\\images\\B191-32+34-2.jpg', 'm:\\images\\B191-005-01A.JPG', 'm:\\images\\B191-005-01B.JPG', 'm:\\images\\B191-005-02A.JPG', 'm:\\images\\B191-005-02B.JPG', 'm:\\images\\AB1099q.jpg', 'm:\\images\\AB1522q.jpg', 'm:\\images\\AB1514.jpg', 'm:\\images\\AB1514q.jpg', 'm:\\images\\AB1383a.jpg', 'm:\\images\\AB1520q.jpg', 'm:\\images\\ab1428-02c.jpg', 'm:\\images\\pkcz00022.jpg', 'm:\\images\\PKCZ94-24foto.jpg', 'm:\\images\\pkcz00084-01a.jpg', 'm:\\images\\pkcz00199-2.jpg', 'm:\\images\\pkcz00199-3.jpg', 'm:\\images\\pkcz00199-4.jpg', 'm:\\images\\pkcz00089-2.jpg', 'm:\\images\\PKCZ92-03.jpg', 'm:\\images\\PKCZ94-25-a-k.jpg', 'm:\\images\\PKCZ96-08.jpg', 'm:\\images\\pkcz92-04-2.jpg', 'm:\\images\\PKCZ00272-Becta.jpg', 'm:\\images\\PKCZ92-12.jpg', 'm:\\images\\pkcz93-08-9.jpg', 'm:\\images\\pkcz00455.jpg', 'm:\\images\\pkcz00455 a.jpg', 'm:\\images\\pkcz00456.jpg', 'm:\\images\\pkcz00457.jpg', 'm:\\images\\pkcz00458.jpg', 'm:\\images\\pkcz00459.jpg', 'm:\\images\\pkcz00460.jpg', 'm:\\images\\pkcz00461.jpg', 'm:\\images\\pkcz00462.jpg', 'm:\\images\\pkcz00463.jpg', 'm:\\images\\pkcz00464.jpg', 'm:\\images\\pkcz00465.jpg', 'm:\\images\\pkcz00466.jpg', 'm:\\images\\pkcz00469.jpg', 'm:\\images\\pkcz00470.jpg', 'm:\\images\\pkcz00471.jpg', 'm:\\images\\G1184a.jpg', 'm:\\images\\G2478-01a.jpg', 'm:\\images\\M66-014-05-2.jpg', 'm:\\images\\G2352-01k2.jpg', 'm:\\images\\G2495-001a.jpg', 'm:\\images\\G2485-01a.jpg', 'm:\\images\\M96-013-01a.jpg', 'm:\\images\\G1184-02a.jpg', 'm:\\images\\M66-14-02-11.jpg', 'm:\\images\\M81-029q.jpg', 'm:\\images\\AB1604a.jpg', 'm:\\images\\Br91-012q.jpg', 'm:\\images\\Br99-005j.jpg', 'm:\\images\\G3655g.jpg', 'm:\\images\\G3689a.jpg', 'm:\\images\\G2484-01a.jpg', 'm:\\images\\G2484-02a.jpg', 'm:\\images\\G2484-03a.jpg', 'm:\\images\\G2484-04a.jpg', 'm:\\images\\br03-001a.jpg', 'm:\\images\\br03-001b.jpg', 'm:\\images\\M73-041a.jpg', 'm:\\images\\AB1584a.jpg', 'm:\\images\\HANS WARREN 103A.jpg', 'm:\\images\\HANS WARREN 154.jpg', 'm:\\images\\HANS WARREN 164.jpg', 'm:\\images\\HANS WARREN 173.jpg', 'm:\\images\\PKCZ00084 01.jpg', 'm:\\images\\PKCZ00075-1.jpg', 'm:\\images\\PKCZ00075-2.jpg', 'm:\\images\\M04-005.jpg', 'M:\\images\\G03-050.JPG', 'm:\\images\\G0533a.jpg', 'm:\\images\\AB1766-01.jpg', 'm:\\images\\AB1036k1.jpg', 'm:\\images\\ab1421.jpg', 'm:\\images\\AB1025qk1.jpg', 'M:\\images\\M64-66.JPG', 'M:\\images\\M75-068-02.JPG', 'm:\\images\\3600-3189QB.JPG', 'm:\\images\\3600-4795A.JPG', 'm:\\images\\3600-7596-01Q1.JPG', 'm:\\images\\3600-Z-9004a.jpg', 'm:\\images\\AB1354-02.jpg', 'm:\\images\\B191-036A.JPG', 'm:\\images\\B191-8q.jpg', 'm:\\images\\B191-8ma.jpg', 'm:\\images\\pkcz00-07-2b.jpg', 'm:\\images\\pkcz00-09.jpg', 'm:\\images\\pkcz00305scan.jpg', 'm:\\images\\pkcz00128-129.jpg', 'm:\\images\\pkcz00488.jpg', 'm:\\images\\pkcz 92-05.jpg', 'm:\\images\\pkcz00552-1.jpg', 'm:\\images\\pkcz98-79 -3.jpg', 'm:\\images\\pkcz00552.jpg', 'm:\\images\\pkcz01-02-6.jpg', 'm:\\images\\pkcz01-02-5.jpg', 'm:\\images\\pkcz01-02-4.jpg', 'm:\\images\\pkcz01-02-3.jpg', 'm:\\images\\pkcz01-02-2.jpg', 'm:\\images\\pkcz01-02-1.jpg', 'm:\\images\\pkcz00175-01.jpg', 'm:\\images\\pkcz00089-3.jpg', 'm:\\images\\PKCZ00167-1.jpg', 'm:\\images\\pkcz00199-1.jpg', 'm:\\images\\M10-139.jpg', 'm:\\images\\PKCZ00095-01.jpg', 'm:\\images\\PKCZ00095-02.jpg', 'm:\\images\\pkcz00410-1.jpg', 'm:\\images\\pkcz00410-2.jpg', 'm:\\images\\pkcz00410-3.jpg', 'm:\\images\\pkcz00410-4.jpg', 'm:\\images\\pkcz00410-5.jpg', 'm:\\images\\pkcz00294-1.jpg', 'm:\\images\\pkcz00294-2.jpg', 'm:\\images\\pkcz00294-3.jpg', 'm:\\images\\pkcz00488-01.jpg', 'm:\\images\\pkcz00409-1.jpg', 'm:\\images\\pkcz00516.jpg', 'm:\\images\\AB1102a.jpg', 'm:\\images\\AB1476-05k1.jpg', 'm:\\images\\AB0953-01k1.jpg', 'm:\\images\\AB1758-01.jpg', 'm:\\images\\AB1104q.jpg', 'm:\\images\\AB1770-01a.jpg', 'm:\\images\\ab1431k1.jpg', 'm:\\images\\PKCZ00073-01.jpg', 'm:\\images\\ZNA046.jpg', 'm:\\images\\M04-057.jpg', 'm:\\images\\PKCZ04-022.jpg', 'm:\\images\\pkcz00-008-02.jpg', 'm:\\images\\AB1577k1.jpg', 'm:\\images\\AB1698-01Q.JPG', 'm:\\images\\3600-ZG-380a.jpg', 'M:\\images\\M01-044+M01-045.JPG', 'm:\\images\\M64-129.jpg', 'm:\\images\\G1198.jpg', 'm:\\images\\M64-171-15a.jpg', 'm:\\images\\pkcz00282 1.jpg', 'm:\\images\\pkcz00107.jpg', 'm:\\images\\pkcz00174b.jpg', 'm:\\images\\pkcz00174a.jpg', 'm:\\images\\pkcz00330-1.jpg', 'm:\\images\\pkcz00309 a.jpg', 'm:\\images\\pkcz00024-2.jpg', 'm:\\images\\pkcz00024-4.jpg', 'm:\\images\\pkcz00024-3.jpg', 'm:\\images\\pkcz00024-1.jpg', 'm:\\images\\pkcz00194-2.jpg', 'm:\\images\\pkcz00194-3.jpg', 'm:\\images\\pkcz00194-4.jpg', 'm:\\images\\pkcz00074-1.jpg', 'm:\\images\\pkcz00074-3.jpg', 'm:\\images\\pkcz00074-5.jpg', 'm:\\images\\pkcz00242-01.jpg', 'm:\\images\\pkcz00242-02.jpg', 'm:\\images\\pkcz00242-03.jpg', 'm:\\images\\pkcz00242-04.jpg', 'm:\\images\\pkcz00301.jpg', 'm:\\images\\pkcz00301a.jpg', 'm:\\images\\pkcz00201-2.jpg', 'm:\\images\\pkcz00201-3.jpg', 'm:\\images\\pkcz00201-4.jpg', 'm:\\images\\pkcz00201-5.jpg', 'm:\\images\\pkcz00201-1.jpg', 'M:\\images\\AE.1956.0006.0003.JPG', 'M:\\images\\Christoffelmedaille - voorbeeldfoto.jpg', 'M:\\images\\VOORBEELD HOOFDBOEK2.JPG', 'm:\\images\\BR93-002.jpg', 'm:\\images\\br99-005.jpg', 'm:\\images\\G3465c.jpg', 'm:\\images\\AB1571.jpg', 'm:\\images\\AB1023qk1.jpg', 'm:\\images\\AB1585a.jpg', 'm:\\images\\AB1024qk1.jpg', 'm:\\images\\M01-006-02.jpg', 'm:\\images\\M95-005&006qa.jpg', 'm:\\images\\M91-015-021.jpg', 'm:\\images\\M93-018-11a.jpg', 'm:\\images\\m62-102.jpg', 'm:\\images\\M78-013.jpg', 'm:\\images\\G2654a.jpg', 'm:\\images\\G1402.jpg', 'm:\\images\\M79-018.jpg', 'm:\\images\\G3620a.jpg', 'm:\\images\\G3620b.jpg', 'm:\\images\\3600-BEV-Z-100m.jpg', 'm:\\images\\3600-BEV-Z-100a1.jpg', 'm:\\images\\3600-BEV-Z-100a2.jpg', 'm:\\images\\3600-BEV-Z-100bw.jpg', 'm:\\images\\AB0972-02a-2.jpg', 'm:\\images\\AB1516-01e.jpg', 'm:\\images\\M68-35-01.jpg', 'm:\\images\\G2480-036g.jpg', 'm:\\images\\G1650a.jpg', 'm:\\images\\m11-011a1.jpg', 'm:\\images\\m11-011a2.jpg', 'm:\\images\\m11-011a3.jpg', 'm:\\images\\G0299.jpg', 'm:\\images\\M06-018.jpg', 'm:\\images\\M70-056a.jpg', 'm:\\images\\M67-238.jpg', 'm:\\images\\ab1402.jpg', 'm:\\images\\AB1038qk1.jpg', 'm:\\images\\pkcz00406-01.jpg', 'm:\\images\\pkcz00406-03.jpg', 'm:\\images\\pkcz00406-02.jpg', 'm:\\images\\M10-005.JPG', 'm:\\images\\M10-006-01.JPG', 'm:\\images\\BP025f1.jpg', 'm:\\images\\BP025f3.jpg', 'm:\\images\\BP028f3.jpg', 'm:\\images\\BP029f1.jpg', 'm:\\images\\BP029f3.jpg', 'm:\\images\\BP031L1.jpg', 'm:\\images\\BP031L2.jpg', 'm:\\images\\BP033f1.jpg', 'm:\\images\\BP033f2.jpg', 'm:\\images\\BP038f1.jpg', 'm:\\images\\BP059m2.jpg', 'm:\\images\\M66-014-05-1a.jpg', 'm:\\images\\G0697 tm G0704.jpg', 'm:\\images\\3600-Z-7587.jpg', 'm:\\images\\3600-Z-7588.jpg', 'm:\\images\\3600-Z-7589.jpg', 'm:\\images\\3600-Z-3165a.jpg', 'M:\\images\\3600-Z-8064-02&-03Q1.JPG', 'M:\\images\\3600-Z-8064-02&-03Q2.JPG', 'm:\\images\\M91-014qb.jpg', 'm:\\images\\G2352-01k3.jpg', 'm:\\images\\G2352-01k4.jpg', 'm:\\images\\G2352-01-02.jpg', 'm:\\images\\G2352-02-02.jpg', 'm:\\images\\G2352-02k1.jpg', 'm:\\images\\G2352-02k2.jpg', 'm:\\images\\G2352-02k3.jpg', 'm:\\images\\G2352-02k4.jpg', 'm:\\images\\G2495-001b.jpg', 'm:\\images\\G2495-002b.jpg', 'm:\\images\\G2495-003b.jpg', 'm:\\images\\G2495-004b.jpg', 'm:\\images\\G2495-005b.jpg', 'm:\\images\\G2495-006b.jpg', 'm:\\images\\G2495-007b.jpg', 'm:\\images\\G2495-008b.jpg', 'm:\\images\\M96-013-01b.jpg', 'm:\\images\\M96-013h.jpg', 'm:\\images\\M87-088foto.jpg', 'm:\\images\\wonderkamer-24mei2006-01a.jpg', 'm:\\images\\wonderkamer-24mei2006-03.jpg', 'm:\\images\\wonderkamer-24mei2006-04.jpg', 'm:\\images\\wonderkamer-24mei2006-05.jpg', 'm:\\images\\wonderkamer-24mei2006-06.jpg', 'm:\\images\\wonderkamer-24mei2006-07.jpg', 'm:\\images\\wonderkamer-24mei2006-08.jpg', 'm:\\images\\ZM-26april2006-10.jpg', 'm:\\images\\ZM-26april2006-10-2.jpg', 'm:\\images\\M81-029-01h1.jpg', 'm:\\images\\M81-029-01h2.jpg', 'm:\\images\\M81-029-02-h1.jpg', 'm:\\images\\M81-029-04h1.jpg', 'm:\\images\\M81-029-04h2.jpg', 'm:\\images\\M81-029-05h1.jpg', 'm:\\images\\M81-029-05h2.jpg', 'm:\\images\\M81-030h1.jpg', 'm:\\images\\M81-031-01h1.jpg', 'M:\\images\\M96-047-07+08.JPG', 'm:\\images\\AB1026qk1.jpg', 'm:\\images\\ab1420.jpg', 'm:\\images\\AB1083j.jpg', 'm:\\images\\AB1754-01a.jpg', 'm:\\images\\AB1354-01.jpg', 'm:\\images\\AB0940a.jpg', 'm:\\images\\AB1119q.jpg', 'm:\\images\\AB1082q.jpg', 'm:\\images\\AB1022qk1.jpg', 'm:\\images\\1420-1_zn0024.jpg', 'm:\\images\\1420q.jpg', 'm:\\images\\598-22.jpg', 'm:\\images\\C1591-01a1.jpg', 'm:\\images\\2405.jpg', 'm:\\images\\HANS WARREN 076.jpg', 'm:\\images\\HANS WARREN 004.jpg', 'm:\\images\\HANS WARREN 047.jpg', 'm:\\images\\HANS WARREN 122.jpg', 'm:\\images\\HANS WARREN 126.jpg', 'm:\\images\\HANS WARREN 201.jpg', 'm:\\images\\HANS WARREN 138B.jpg', 'm:\\images\\HANS WARREN 066.jpg', 'm:\\images\\GRAF 76-01.JPG', 'm:\\images\\GRAF 104.JPG', 'm:\\images\\AB1592qk1.jpg', 'm:\\images\\AB1592qk2.jpg', 'm:\\images\\AB1592qk3.jpg', 'm:\\images\\AB1592qk4.jpg', 'm:\\images\\AB1562k1.jpg', 'm:\\images\\AB1562k2.jpg', 'm:\\images\\AB1562k3.jpg', 'm:\\images\\wonderkamer-8juni2005.jpg', 'm:\\images\\wonderkamer-8juni2005-2.jpg', 'm:\\images\\wonderkamer-8juni2005-3.jpg', 'M:\\images\\AB1135q1.jpg', 'm:\\images\\wonderkamer-18mei2005.jpg', 'm:\\images\\wonderkamer-18mei2005-2.jpg', 'm:\\images\\G2243-01-02-03.jpg', 'm:\\images\\G2243-04-05-09.jpg', 'm:\\images\\G2243-06-07-08.jpg', 'm:\\images\\G2243-BC02.jpg', 'm:\\images\\G2243-BC03.jpg', 'm:\\images\\G2243-BC04.jpg', 'm:\\images\\G2243-BC05.jpg', 'm:\\images\\G3266b.jpg', 'm:\\images\\wonderkamer-overzicht.jpg', 'm:\\images\\wonderkamer-30nov2005-vitrine.jpg', 'm:\\images\\wonderkamer-30nov2005-03.jpg', 'm:\\images\\wonderkamer-30nov2005-02.jpg', 'm:\\images\\wonderkamer-30nov2005-04.jpg', 'm:\\images\\wonderkamer-30nov2005-05.jpg', 'm:\\images\\Br78-008-006-01q.jpg', 'm:\\images\\ZE445l.jpg', 'm:\\images\\G3657q.jpg', 'm:\\images\\G3654q.jpg', 'm:\\images\\G3689m.jpg', 'm:\\images\\G3689q.jpg', 'm:\\images\\pkcz94-19-ac.jpg', 'm:\\images\\PKCZ94-19.jpg', 'm:\\images\\PKCZ95-03.jpg', 'm:\\images\\PKCZ92-07.jpg', 'm:\\images\\G2480-056b.jpg', 'm:\\images\\PKC00521foto.jpg', 'm:\\images\\PKCZ00522.jpg', 'm:\\images\\G2480-037k2.jpg', 'm:\\images\\G2480-037k3.jpg', 'm:\\images\\G2480-037k4.jpg', 'm:\\images\\GA0119_0121.jpg', 'm:\\images\\ZM-3mei2006-06.jpg', 'm:\\images\\ZM-3mei2006-10.jpg', 'm:\\images\\G0533b.jpg', 'm:\\images\\G0533c.jpg', 'm:\\images\\G0533d.jpg', 'm:\\images\\pkcz00-07-1.jpg', 'm:\\images\\PKCZ00-07-2.jpg', 'm:\\images\\pkcz00-07-3.jpg', 'm:\\images\\pkcz00-07-4.jpg', 'm:\\images\\PKCZ00154-7ecta.jpg', 'm:\\images\\PKCZ00-10foto.jpg', 'm:\\images\\pkcz00-11.jpg', 'm:\\images\\PKCZ96-20-b.jpg', 'm:\\images\\PKCZ96-20-c.jpg', 'm:\\images\\PKCZ96-20-d.jpg', 'm:\\images\\PKCZ96-20-e.jpg', 'm:\\images\\PKCZ96-20-f.jpg', 'm:\\images\\PKCZ97-01.jpg', 'm:\\images\\pkcz00272.jpg', 'm:\\images\\ab1422-01.jpg', 'm:\\images\\AB1563q1.jpg', 'm:\\images\\AB1551j.jpg', 'm:\\images\\G2517-02.jpg', 'm:\\images\\G2517-04.jpg', 'm:\\images\\G2517-05.jpg', 'm:\\images\\G1463.jpg', 'm:\\images\\M91-005foto.jpg', 'm:\\images\\pkcz00395scan.jpg', 'm:\\images\\PKCZ00113foto.jpg', 'm:\\images\\PKCZ00544foto.jpg', 'm:\\images\\G0531-002.jpg', 'm:\\images\\PKCZ00431-2foto.jpg', 'm:\\images\\G3451.jpg', 'm:\\images\\G2480-01.jpg', 'm:\\images\\AB1592.jpg', 'm:\\images\\pkcz00092.jpg', 'm:\\images\\pkcz00193a.jpg', 'm:\\images\\pkcz00445.jpg', 'm:\\images\\M90-038-17.jpg', 'm:\\images\\G2714.jpg', 'm:\\images\\ab1542.jpg', 'm:\\images\\ab1542b.jpg', 'm:\\images\\ZE445.jpg', 'm:\\images\\PKCZ04-023.jpg', 'm:\\images\\3600-Z-8064qk2.jpg', 'm:\\images\\G3702q.jpg', 'm:\\images\\M81-026qb.jpg', 'm:\\images\\M81-027qb.jpg', 'm:\\images\\M81-031qb.jpg', 'm:\\images\\BP032.jpg', 'm:\\images\\BP031.jpg', 'm:\\images\\BP032f.jpg', 'm:\\images\\BP033.jpg', 'm:\\images\\BP034.jpg', 'm:\\images\\BP035.jpg', 'm:\\images\\BP036.jpg', 'm:\\images\\BP037f.jpg', 'm:\\images\\BP038f2.jpg', 'm:\\images\\BP039f1.jpg', 'm:\\images\\BP039f2.jpg', 'm:\\images\\BP040f1.jpg', 'm:\\images\\BP041f.jpg', 'm:\\images\\BP042f.jpg', 'm:\\images\\BP043.jpg', 'm:\\images\\BP044.jpg', 'm:\\images\\BP045f1.jpg', 'm:\\images\\BP045f2.jpg', 'm:\\images\\BP046.jpg', 'm:\\images\\BP047f1.jpg', 'm:\\images\\BP047f2.jpg', 'm:\\images\\BP048a.jpg', 'm:\\images\\BP048d.jpg', 'm:\\images\\BP048m1.jpg', 'm:\\images\\BP048m2.jpg', 'm:\\images\\BP048m3.jpg', 'm:\\images\\BP048m4.jpg', 'm:\\images\\BP048m5.jpg', 'm:\\images\\BP048m6.jpg', 'm:\\images\\BP048m7.jpg', 'm:\\images\\BP049.jpg', 'm:\\images\\BP050.jpg', 'm:\\images\\BP051-01.jpg', 'm:\\images\\BP051-02f1.jpg', 'm:\\images\\BP051-02f2.jpg', 'm:\\images\\BP052.jpg', 'm:\\images\\BP053.jpg', 'm:\\images\\BP054.jpg', 'm:\\images\\BP055.jpg', 'm:\\images\\BP056.jpg', 'm:\\images\\BP057.jpg', 'm:\\images\\BP059a.jpg', 'm:\\images\\BP059m1.jpg', 'm:\\images\\BP062.jpg', 'm:\\images\\BP062h.jpg', 'm:\\images\\BP064.jpg', 'm:\\images\\BP066.jpg', 'm:\\images\\BP068.jpg', 'm:\\images\\G2357-01.jpg', 'm:\\images\\G2357-02.jpg', 'm:\\images\\G2558-01f1.jpg', 'm:\\images\\G2558-01f2.jpg', 'm:\\images\\G2558-02.jpg', 'm:\\images\\M63-135.jpg', 'm:\\images\\M63-135m1.jpg', 'm:\\images\\M63-135m2.jpg', 'm:\\images\\G2357-07.jpg', 'm:\\images\\BP013.jpg', 'm:\\images\\BP014.jpg', 'm:\\images\\BP015.jpg', 'm:\\images\\BP016.jpg', 'm:\\images\\BP017.jpg', 'm:\\images\\BP018.jpg', 'm:\\images\\BP019.jpg', 'm:\\images\\BP020.jpg', 'm:\\images\\BP021.jpg', 'm:\\images\\BP022.jpg', 'm:\\images\\BP024.jpg', 'm:\\images\\BP023.jpg', 'm:\\images\\BP025.jpg', 'm:\\images\\BP025f2.jpg', 'm:\\images\\BP026.jpg', 'm:\\images\\BP026f.jpg', 'm:\\images\\BP027.jpg', 'm:\\images\\BP027f.jpg', 'm:\\images\\BP028.jpg', 'm:\\images\\BP028f1.jpg', 'm:\\images\\BP028f2.jpg', 'm:\\images\\BP029.jpg', 'm:\\images\\BP029f2.jpg', 'm:\\images\\BP030.jpg', 'm:\\images\\BP030f1.jpg', 'm:\\images\\BP030f2.jpg', 'm:\\images\\G3711q.jpg', 'm:\\images\\HW041-042q2.jpg', 'm:\\images\\HW041-042q3.jpg', 'm:\\images\\HW041-042q4.jpg', 'm:\\images\\M90-014ecta.jpg', 'm:\\images\\AB1496.jpg', 'm:\\images\\AB1578.jpg', 'm:\\images\\AB1589.jpg', 'm:\\images\\AB1589qk1.jpg', 'm:\\images\\AB1589qk2.jpg', 'm:\\images\\AB1589qk4.jpg', 'm:\\images\\AB1589qk3.jpg', 'm:\\images\\AB1572q.jpg', 'm:\\images\\AB1113q.jpg', 'm:\\images\\AB1577k2.jpg', 'm:\\images\\AB1408J.jpg', 'm:\\images\\ab1085.jpg', 'm:\\images\\AB1085q.jpg', 'm:\\images\\AB1084qk1.jpg', 'm:\\images\\AB1084qk2.jpg', 'm:\\images\\AB1084qk3.jpg', 'm:\\images\\AB1084qk4.jpg', 'm:\\images\\AB1097q.jpg', 'm:\\images\\AB1097qe.jpg', 'm:\\images\\AB1615qk1.jpg', 'm:\\images\\AB1615qk2.jpg', 'm:\\images\\AB1611qk1.jpg', 'm:\\images\\AB1611qk2.jpg', 'm:\\images\\AB1617q.jpg', 'm:\\images\\AB1580.jpg', 'm:\\images\\AB1580qk1.jpg', 'm:\\images\\AB1580qk2.jpg', 'm:\\images\\AB1610q.jpg', 'm:\\images\\AB1595q.jpg', 'm:\\images\\AB1608q.jpg', 'm:\\images\\AB1607qk1.jpg', 'm:\\images\\AB1607qk2.jpg', 'm:\\images\\AB1607qk3.jpg', 'm:\\images\\AB1123q.jpg', 'm:\\images\\AB1631q.jpg', 'm:\\images\\ab1410.jpg', 'm:\\images\\AB1475q1.jpg', 'm:\\images\\ab1679q.jpg', 'm:\\images\\G2700-08b.jpg', 'm:\\images\\G2700-08q.jpg', 'm:\\images\\G2708-06.jpg', 'm:\\images\\G2459-05k2.jpg', 'm:\\images\\G2459-05k3.jpg', 'm:\\images\\G2459-05k4.jpg', 'm:\\images\\G2459-06.jpg', 'm:\\images\\G2459q.jpg', 'm:\\images\\BR78-008-050c.jpg', 'm:\\images\\wonderkamer-17mei2006-01.jpg', 'm:\\images\\wonderkamer-17mei2006-02.jpg', 'm:\\images\\wonderkamer-17mei2006-03.jpg', 'm:\\images\\3600-BEV-Z-67q.jpg', 'm:\\images\\3600-BEV-Z-67qm.jpg', 'm:\\images\\M64-102-01-02-03.jpg', 'm:\\images\\M86-035a2.jpg', 'm:\\images\\M86-035b.jpg', 'm:\\images\\G2714-01.jpg', 'm:\\images\\G2714-04.jpg', 'm:\\images\\M04-057-01h.jpg', 'm:\\images\\M04-057-02h.jpg', 'm:\\images\\M04-057-03h.jpg', 'm:\\images\\M04-057b.jpg', 'm:\\images\\M05-014Q.jpg', 'm:\\images\\PKCZ00-08-01a.jpg', 'm:\\images\\G3465.jpg', 'M:\\images\\GA0019-G0020.JPG', 'm:\\images\\AB1571a.jpg', 'm:\\images\\AB1585.jpg', 'm:\\images\\AB1612a.jpg']


class SyncUtils:
    
    def __init__(self, APIUpdater):
        self.api = APIUpdater.api
        self.api_updater = APIUpdater
        self.dev = False

    def reindex_all_taxonomies(self):
        index = "taxonomicTermDetails_term_rank"

        curr = 0
        for tax in self.api.all_taxonomies[:400]:
            curr += 1 
            print curr
            obj = tax.getObject()
            obj.reindexObject(idxs=["taxonomicTermDetails_term_rank"])

        return True

    def reindex_books(self):

        total = len(self.api.all_books)
        curr = 0

        for brain in self.api.all_books:
            obj = brain.getObject()
            obj.reindexObject()
            curr += 1

            print "Reindexing %s / %s" %(str(curr), str(total))

        return True

    def move_person(self, obj):
        
        _id = obj.priref

        base_folder = "nl/intern/personen-en-instellingen"
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        alphabet = list(string.ascii_uppercase)
        
        if obj.title:
            title = obj.title
            first_letter = title[0]
            if first_letter.upper() in alphabet:
                source = obj
                target = self.api.get_folder('%s/%s' %(base_folder, first_letter.upper()))
                self.api.move_obj_folder(source, target)
            elif first_letter.upper() in numbers:
                source = obj
                target = self.api.get_folder('%s/0-9' %(base_folder))
                self.api.move_obj_folder(source, target)
            else:
                source = obj
                target = self.api.get_folder('%s/meer' %(base_folder))
                self.api.move_obj_folder(source, target)
                self.error("Unknown type - id: %s - letter: %s" %(str(_id), first_letter))
        else:
            self.error("No title - %s"%(str(_id)))

    def fix_institutions(self):
        all_institutions = self.api.portal_catalog(nameInformation_name_nameType_type="institution")

        total = len(all_institutions)
        curr = 0

        for institution in all_institutions:
            transaction.begin()
            person = institution.getObject()

            curr += 1
            print "Fixing %s / %s" %(str(curr), str(total))

            priref = getattr(person, 'priref', "")
            name = getattr(person, 'nameInformation_name_name', "")

            dirty_id = "%s %s" %(str(priref), str(name.encode('ascii', 'ignore')))
            normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

            person.title = name

            api.content.rename(obj=person, new_id=normalized_id, safe_id=True)
            self.move_person(person)
            transaction.commit()

        return True

    def fix_person_name(self, person):
        priref = getattr(person, 'priref', "")
        title = getattr(person, 'title', "")

        if title:
            title_separated = [x.strip() for x in title.split(",")]
            length = len(title_separated)
            if length == 0:
                self.warning('%s__%s__Number of commas is 0. No modifications are done.' %(str(priref), str(title.encode('ascii', 'ignore'))))
            elif length > 2:
                self.error("%s__%s__Number of commas is >= 2" %(str(priref), str(title.encode('ascii', 'ignore'))))
            elif length == 2:
                brackets = re.findall('\(.*?\)', title)
                
                if len(brackets) <= 1:
                    if len(brackets) == 1:
                        last_part = brackets[0]
                        title = title.replace(last_part, '')
                        title = title.strip()
                        title_separated = [x.strip() for x in title.split(",")]
                    else:
                        last_part = ""

                    if len(title_separated) == 2:
                        first_name = title_separated[1]
                        last_name = title_separated[0]
                        new_title = [first_name, last_name]
                        new_title_string = " ".join(new_title)
                        new_title_string = new_title_string.strip()

                        if last_part:
                            new_title_string = "%s %s" %(new_title_string, last_part)

                        # Set title
                        person.title = new_title_string
                        #person.nameInformation_name_name = new_title_string

                        self.log_status("! STATUS !__%s__Name updated from '%s' to '%s'." %(str(priref), str(title.encode('ascii', 'ignore')), str(new_title_string.encode('ascii', 'ignore'))))

                        # Change ID
                        dirty_id = "%s %s" %(str(priref), new_title_string)
                        normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))
                        person.reindexObject(idxs=['Title'])

                        #api.content.rename(obj=person, new_id=normalized_id, safe_id=True)
                        #self.move_person(person)
                    else:
                        self.warning('%s__%s__Number of commas is 0. No modifications are done.' %(str(priref), str(title.encode('ascii', 'ignore'))))

                elif len(brackets) > 1:
                    self.error("%s__%s__Number of text between parenthesis is >= 2" %(str(priref), str(title.encode('ascii', 'ignore'))))

            else:
                self.error("%s__%s__Number of commas is 0. No modifications are done." %(str(priref), str(title.encode('ascii', 'ignore'))))
        else:
            self.error("%s__%s__Current title is empty." %(str(priref), str("")))

    def fix_persons_names(self):
        total = len(self.api.all_persons)
        curr = 0

        for brain in list(self.api.all_persons):
            try:
                curr += 1
                transaction.begin()
                self.log_status("! STATUS !__ __Reindexing %s / %s" %(str(curr), str(total)))
                person = brain.getObject()
                person.reindexObject()
                #self.fix_person_name(person)
                transaction.commit()
            except:
                transaction.abort()
                pass

        return True

    def check_number_of_commas(self):
        count = 0
        curr = 0
        total = len(list(self.api.all_persons))
        for brain in list(self.api.all_persons):
            curr += 1
            
            self.log_status("! STATUS !__ Checking %s / %s" %(str(curr), str(total)))
            person = brain.getObject()
            title = getattr(person, 'title', "")

            title_separated = [x.strip() for x in title.split(",")]
            length = len(title_separated)

            if length == 2:
                print title.encode('ascii', 'ignore')

        print "Total of Persons / Institutions with 1 comma: %s" %(str(count))
        return True


    def find_relations(self):
        from zope.intid.interfaces import IIntIds
        from Acquisition import aq_inner

        total = 0

        intids = getUtility(IIntIds)
        cat = getUtility(ICatalog)
        for brain in list(self.api.all_persons):
            person = brain.getObject()
            _id = intids.getId(aq_inner(person))
            from_relations = list(cat.findRelations(dict(from_id=_id)))
            to_relations = list(cat.findRelations(dict(to_id=_id)))

            len_from = len(from_relations)
            len_to = len(to_relations)

            if person.id == "test-title":
                for relation in to_relations:
                    print relation.from_attribute

        return True

    def reindex_all_objects(self):
        self.api_updater.portal_type = "Object"
        self.api_updater.init_fields()
        
        for name, field in self.api_updater.fields:
            if name not in ['productionDating_productionDating']:
                searchable(IObject, name)

        total = len(list(self.api.all_objects))
        curr = 0

        for brain in list(self.api.all_objects):
            transaction.begin()
            curr += 1
            print "Reindexing %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            obj.reindexObject()
            transaction.commit()

        return True

    def reindex_all_books(self):
        """total = len(list(self.api.all_books))
        curr = 0

        for brain in self.api.all_books:
            curr += 1
            print "Reindexing book %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass

        print "== AUDIOVISUALS =="
        total = len(list(self.api.all_audiovisuals))
        curr = 0

        for brain in self.api.all_audiovisuals:
            curr += 1
            print "Reindexing audiovisual %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass"""


        print "== ARTICLES =="
        total = len(list(self.api.all_articles))
        curr = 0

        for brain in self.api.all_articles:
            curr += 1
            print "Reindexing article %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass

        """print "== SERIALS =="
        total = len(list(self.api.all_serials))
        curr = 0

        for brain in self.api.all_serials:
            curr += 1
            print "Reindexing serial %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass

        print "== RESOURCES =="
        total = len(list(self.api.all_resources))
        curr = 0

        for brain in self.api.all_resources:
            curr += 1
            print "Reindexing resource %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            try:
                obj.reindexObject()
            except:
                pass"""

        return True

    def reindex_all_exhibitions(self):
        total = len(list(self.api.all_exhibitions))
        curr = 0

        for brain in self.api.all_exhibitions:
            curr += 1
            print "Reindexing %s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            obj.reindexObject()

        return True

    def reindex_all_images(self):
        total = len(list(self.api.all_images))
        curr = 0

        for brain in self.api.all_images:
            curr += 1
            print "Reindexing %s / %s" %(str(curr), str(total))

            obj = brain.getObject()
            obj.reindexObject(idxs=['reproductionData_identification_identifierURL'])

        return True

    def find_image_by_id(self, _id):
        if _id:
            image_path_split = _id.lower().split("\\")
            img = image_path_split[-1]
        
            image_id = idnormalizer.normalize(img, max_length=len(img))
            
            #if image_id in self.images_dict:
            #    img_brain = self.images_dict[image_id]
            #    img_obj = img_brain.getObject()
            #    return img_obj
        
            if _id in self.images_ref_dict:
                img_brain = self.images_ref_dict[_id]
                return img_brain

            else:
                return None

        return None

    def create_page_relations(self):
        page = self.api.get_folder('test-folder/test-page-with-200-related-items')

        person_container = self.api.get_folder('personen-en-instellingen')

        limit = 200
        curr = 0

        transaction.begin()
        for brain in person_container:
            person = person_container[brain]

            intids = component.getUtility(IIntIds)
            person_id = intids.getId(person)
            relation_value = RelationValue(person_id)

            page.relatedItems.append(relation_value)
            
            curr += 1
            if curr >= limit:
                transaction.commit()
                return True


    def reindex_all_persons(self):
        index = "nameInformation_name_nameType_type"

        curr = 0
        transaction.begin()
        for person in self.api.all_persons:
            curr += 1 
            print curr
            obj = person.getObject()
            obj.reindexObject(idxs=[index])
        transaction.commit()

        return True


    def create_large_pages(self):
        total = 100000
        curr = 0
        for i in range(100):
            curr += 1
            print "%s / %s" %(str(curr), str(total))
            transaction.begin()
            
            container = self.api.get_folder('nl/test-large')
            dirty_id = "page %s" %(str(i+1))
            normalized_id = idnormalizer.normalize(dirty_id, max_length=len(dirty_id))

            container.invokeFactory(
                type_name='Document',
                id=normalized_id,
                title=dirty_id
            )
            transaction.commit()

        return True

    def update_indexes(self, targets=[]):
        
        self.log("Updating indexes")

        for target in targets:
            if target == "Object":
                for obj in self.api.all_objects:
                    item = obj.getObject()
                    item.reindexObject(idxs=["identification_identification_objectNumber"])

                self.log("Objects updated!")

            elif target == "PersonOrInstitution":
                for obj in self.api.all_persons:
                    item = obj.getObject()
                    item.reindexObject(idxs=["person_priref"])

                self.log("PersonOrInstitution objects updated!")

            elif target == "Archive":
                for obj in self.api.all_archives:
                    item = obj.getObject()
                    item.reindexObject(idxs=["archive_priref"])

                self.log("Archive objects updated!")
            else:    
                self.log("Type %s does not have a method to be reindexed!" %(target))

        return True

    def import_portaltypes_utils(self, PORTAL_TYPE):
        pass

    def create_dating_field(self, field):
        start_date = field['date_early']
        start_date_precision = field['date_early_precision']
        end_date = field['date_late']
        end_date_precision = field['date_late_precision']

        result = ""

        if start_date != "" and start_date != " ":
            if result:
                if start_date_precision != "" and start_date_precision != " ":
                    result = "%s, %s %s" %(result, start_date_precision, start_date)
                else:
                    result = "%s, %s" %(result, start_date)
            else:
                if start_date_precision != "" and start_date_precision != " ":
                    result = "%s %s" %(start_date_precision, start_date)
                else:
                    result = "%s" %(start_date)
    

        if end_date != "" and end_date != " ":
            if result:
                if end_date_precision != "" and end_date_precision != " ":
                    result = "%s - %s %s" %(result, end_date_precision, start_date)
                else:
                    result = "%s - %s" %(result, end_date)
            else:
                if end_date_precision != "" and end_date_precision != " ":
                    result = "%s %s" %(end_date_precision, start_date)
                else:
                    result = "%s" %(end_date)
        return result


    def update_object_standardfields(self, obj):
        final_title = []

        # Title
        curr_title = getattr(obj, 'title', '')
        final_title.append(curr_title)

        production = getattr(obj, 'productionDating_productionDating', None)
        makers = []
        
        if production:
            for maker in production:
                if 'makers' in maker:
                    makers_field = maker['makers']
                    if makers_field:
                        for relation in makers_field:
                            if IRelationValue.providedBy(relation):
                                rel_obj = relation.to_object
                                title = getattr(rel_obj, 'title', None)
                                if title:
                                    final_title.append(title)
                            elif getattr(relation, 'portal_type', "") == "PersonOrInstitution":
                                title = getattr(relation, 'title', None)
                                if title:
                                    final_title.append(title)
                    else:
                        continue
                else:
                    continue


        
        # Get Year
        dating = getattr(obj, 'productionDating_dating_period', None)
        if dating:
            line = dating[0]
            dates = self.create_dating_field(line)
            if dates:
                final_title.append(dates)

        final_title_string = ", ".join(final_title)

        setattr(obj, 'title', final_title_string)
        
        # Description - clear value
        setattr(obj, 'description', '')

        # Body
        labels = getattr(obj, 'labels', "")
        if labels:
            label = labels[0]
            text = label['text']
            if text:
                final_text = RichTextValue(text, 'text/html', 'text/html')
                setattr(obj, 'text', final_text)

        print final_title_string
        print obj.absolute_url()
        print "----"

        obj.reindexObject(idxs=["Title"])
        return True

    def find_ref_in_brains(self, ref_id, brains):
        found = False

        for brain in brains:
            if brain.id == ref_id:
                return True

        return found


    def find_digitalreferences(self, obj):
        object_number = getattr(obj, 'identification_identification_objectNumber', None)
        slideshow = None
        prive = None

        field_to_search = "disposal_documentation"

        if 'slideshow' in obj:
            slideshow = obj['slideshow']
        if 'prive' in obj:
            prive = obj['prive']

        objs = self.api.portal_catalog(path={"query":"/".join(obj.getPhysicalPath()), "depth": 2})

        references = getattr(obj, field_to_search, None)
        if references:
            if len(references) > 0:
                for line in references:
                    reference = line['reference']
                    if reference != "" and reference != " " and reference != None:
                        reference_path_split = reference.lower().split("\\")
                        ref = reference_path_split[-1]
                        ref_id = idnormalizer.normalize(ref, max_length=len(ref))

                        found = self.find_ref_in_brains(ref_id, objs)
                        if not found:
                            log_text = "%s__%s" %(object_number, reference)
                            self.log_status(log_text, False)
            else:
                self.warning("%s__%s" %(object_number, "Object doesn't contain digital references"))

        return True

    def find_img_record(self, identifier_url):
        for record in list(self.api_updater.collection):
            if record.find('image_reference') != None:
                ref = record.find('image_reference').text
                if ref == identifier_url:
                    return record
        return None

    def find_multiplefields(self, obj):

        reprod_type = getattr(obj, 'reproductionData_identification_reproductionType', '')

        if reprod_type:
            if type(reprod_type) != list:
                length = len(reprod_type)
                if length > 1:
                    priref = getattr(obj, 'priref', '')
                    reproduction_ref = getattr(obj, 'reproductionData_identification_reproductionReference', '')
                    identifier_url = getattr(obj, 'reproductionData_identification_identifierURL', '')

                    #url = obj.absolute_url()
                    #self.api_updater.log_status("%s__%s__%s__%s__%s"%(str(reprod_type), priref, reproduction_ref, identifier_url, url))

                    if identifier_url:
                        if identifier_url in IDENTIFIERS:
                            record = self.find_img_record(identifier_url)
                            if record:
                                object_number = identifier_url
                                self.api_updater.object_number = str(object_number)
                                self.api_updater.generate_field_types()
                                self.api_updater.log_status("! STATUS !__Updating [%s] %s / %s" %(str(object_number), str(curr), str(total)))
                                self.api_updater.empty_fields(obj)
                                self.api_updater.update(record, obj, object_number)
                                self.api_updater.log_status("! STATUS !__Updated [%s] %s / %s" %(str(object_number), str(curr), str(total)))
                                self.api_updater.log_status("! STATUS !__URL: %s" %(str(obj.absolute_url())))
                                self.api_updater.fix_all_choices(obj)
                            else:
                                self.api_updater.log_status("! STATUS !__Cannot find identifier url in XML %s, %s" %(identifier_url, priref))

        return True

    def update_images_with_xml(self):
        total = len(list(self.api.all_images))
        curr = 0

        for brain in list(self.api.all_images):
            transaction.begin()
            curr += 1
            print "%s / %s" %(str(curr), str(total))
            obj = brain.getObject()
            obj_img = IImageReference(obj)
            self.find_multiplefields(obj_img)
            transaction.commit()

        return True

    def check_special_fields(self, obj):

        fields = getattr(obj, 'fieldCollection_habitatStratigraphy_habitat', None)
        if fields:
            for line in fields:
                field = line['term']
                if field:
                    if field.strip() != "":
                        print obj.absolute_url()

        return True

    def find_images_without_ref(self):
        curr = 0
        total = len(list(self.api.all_images))
        rep_reference = []

        for brain in list(self.api.all_images):
            obj = brain.getObject()
            reference = getattr(obj, 'reproductionData_identification_identifierURL', '')
            rep_ref = getattr(obj, 'reproductionData_identification_reproductionReference', '')
            if reference in [None, '', ' ']:
                self.log_status("%s__%s" %(obj.id, obj.absolute_url()), False)
                if rep_ref not in rep_reference:
                    rep_reference.append(rep_ref)


        print "REFERENCES:"
        print rep_reference

        return True

    def update_dictionary(self, subfield, current_value, value, xml_element, subfield_type, plone_fieldroot):
        default_test = " "
        if subfield_type == "choice":
            if xml_element.get('option') != "" and xml_element.get('option') != None:
                if len(xml_element.findall('text')) > 0:
                    return current_value
                else:
                    value = ""
            elif xml_element.get('language') != "0" and xml_element.get('language') != "" and xml_element.get('language') != None:
                return current_value

        updated = False
        found = False

        for line in current_value:
            if subfield in line:
                found = True
                if line[subfield] == default_test or line[subfield] == [] or line[subfield] == 'No value' or line[subfield] == False:
                    if line[subfield] == 'No value' and value == "":
                        line[subfield] = '_No value'
                    else:
                        if subfield_type == "choice":
                            if type(value) != list:
                                line[subfield] = value
                            else:
                                line[subfield] = '_No value'
                        else:
                            if (subfield_type == "gridlist" and value == []) or (subfield_type == "gridlist" and value == ""):
                                line[subfield] = ['no value']
                            else:
                                line[subfield] = value
                    
                    updated = True
                    break

        if not found:
            return current_value

        if not updated:
            if subfield_type == "choice" and type(value) == list:
                value = "_No value"
            if (subfield_type == "gridlist" and value == []) or (subfield_type == "gridlist" and value == ['no value']):
                value = ['no value']
            val = self.api.create_dictionary(subfield, current_value, value, xml_element, subfield_type, plone_fieldroot)
            return val
        else:
            return current_value


    def create_indexes(self, idxs):
        indexes = self.api.portal_catalog.indexes()
    
        print "Adding new indexes"
        
        # Specify the indexes you want, with ('index_name', 'index_type')
        wanted = idxs
        
        indexables = []
        for name, meta_type in wanted:
            if name not in indexes:
                self.api.portal_catalog.addIndex(name, meta_type)
                indexables.append(name)
                print "Added %s for field %s." %(meta_type, name)

        return True





