#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# $Id$
#
# Project:  GDAL/OGR Test Suite
# Purpose:  Test basic OGR functionality against test shapefiles.
# Author:   Frank Warmerdam <warmerdam@pobox.com>
#
###############################################################################
# Copyright (c) 2003, Frank Warmerdam <warmerdam@pobox.com>
# Copyright (c) 2008-2014, Even Rouault <even dot rouault at mines-paris dot org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
###############################################################################

import os
import sys

sys.path.append('../pymod')

import gdaltest
import ogrtest
from osgeo import gdal
from osgeo import ogr

###############################################################################


def ogr_basic_1():

    gdaltest.ds = ogr.Open('data/poly.shp')

    if gdaltest.ds is None:
        gdaltest.post_reason('fail')
        return 'fail'

    return 'success'

###############################################################################
# Test Feature counting.


def ogr_basic_2():

    gdaltest.lyr = gdaltest.ds.GetLayerByName('poly')

    if gdaltest.lyr.GetName() != 'poly':
        return 'fail'
    if gdaltest.lyr.GetGeomType() != ogr.wkbPolygon:
        return 'fail'

    if gdaltest.lyr.GetLayerDefn().GetName() != 'poly':
        return 'fail'
    if gdaltest.lyr.GetLayerDefn().GetGeomType() != ogr.wkbPolygon:
        return 'fail'

    count = gdaltest.lyr.GetFeatureCount()
    if count != 10:
        gdaltest.post_reason('Got wrong count with GetFeatureCount() - %d, expecting 10' % count)
        return 'fail'

    # Now actually iterate through counting the features and ensure they agree.
    gdaltest.lyr.ResetReading()

    count2 = 0
    feat = gdaltest.lyr.GetNextFeature()
    while feat is not None:
        count2 = count2 + 1
        feat = gdaltest.lyr.GetNextFeature()

    if count2 != 10:
        gdaltest.post_reason('Got wrong count with GetNextFeature() - %d, expecting 10' % count2)
        return 'fail'

    return 'success'

###############################################################################
# Test Spatial Query.


def ogr_basic_3():

    minx = 479405
    miny = 4762826
    maxx = 480732
    maxy = 4763590

    ###########################################################################
    # Create query geometry.

    ring = ogr.Geometry(type=ogr.wkbLinearRing)
    ring.AddPoint(minx, miny)
    ring.AddPoint(maxx, miny)
    ring.AddPoint(maxx, maxy)
    ring.AddPoint(minx, maxy)
    ring.AddPoint(minx, miny)

    poly = ogr.Geometry(type=ogr.wkbPolygon)
    poly.AddGeometryDirectly(ring)

    gdaltest.lyr.SetSpatialFilter(poly)
    gdaltest.lyr.SetSpatialFilter(gdaltest.lyr.GetSpatialFilter())
    gdaltest.lyr.ResetReading()

    count = gdaltest.lyr.GetFeatureCount()
    if count != 1:
        gdaltest.post_reason('Got wrong feature count with spatial filter, expected 1, got %d' % count)
        return 'fail'

    feat1 = gdaltest.lyr.GetNextFeature()
    feat2 = gdaltest.lyr.GetNextFeature()

    if feat1 is None or feat2 is not None:
        gdaltest.post_reason('Got too few or too many features with spatial filter.')
        return 'fail'

    gdaltest.lyr.SetSpatialFilter(None)
    count = gdaltest.lyr.GetFeatureCount()
    if count != 10:
        gdaltest.post_reason('Clearing spatial query may not have worked properly, getting\n%d features instead of expected 10 features.' % count)
        return 'fail'

    return 'success'

###############################################################################
# Test GetDriver().


def ogr_basic_4():
    driver = gdaltest.ds.GetDriver()
    if driver is None:
        gdaltest.post_reason('GetDriver() returns None')
        return 'fail'

    if driver.GetName() != 'ESRI Shapefile':
        gdaltest.post_reason('Got wrong driver name: ' + driver.GetName())
        return 'fail'

    return 'success'

###############################################################################
# Test attribute query on special field fid - per bug 1468.


def ogr_basic_5():

    gdaltest.lyr.SetAttributeFilter('FID = 3')
    gdaltest.lyr.ResetReading()

    feat1 = gdaltest.lyr.GetNextFeature()
    feat2 = gdaltest.lyr.GetNextFeature()

    gdaltest.lyr.SetAttributeFilter(None)

    if feat1 is None or feat2 is not None:
        gdaltest.post_reason('unexpected result count.')
        return 'fail'

    if feat1.GetFID() != 3:
        gdaltest.post_reason('got wrong feature.')
        return 'fail'

    return 'success'


###############################################################################
# Test opening a dataset with an empty string and a non existing dataset
def ogr_basic_6():

    # Put inside try/except for OG python bindings
    if ogr.Open('') is not None:
        return 'fail'

    if ogr.Open('non_existing') is not None:
        return 'fail'

    return 'success'

###############################################################################
# Test ogr.Feature.Equal()


def ogr_basic_7():

    feat_defn = ogr.FeatureDefn()
    feat = ogr.Feature(feat_defn)
    if not feat.Equal(feat):
        return 'fail'

    try:
        feat.SetFieldIntegerList
    except AttributeError:
        return 'skip'

    feat_clone = feat.Clone()
    if not feat.Equal(feat_clone):
        return 'fail'

    # We MUST delete now as we are changing the feature defn afterwards!
    # Crash guaranteed otherwise
    feat = None
    feat_clone = None

    field_defn = ogr.FieldDefn('field1', ogr.OFTInteger)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field2', ogr.OFTReal)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field3', ogr.OFTString)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field4', ogr.OFTIntegerList)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field5', ogr.OFTRealList)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field6', ogr.OFTStringList)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field7', ogr.OFTDate)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field8', ogr.OFTTime)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field9', ogr.OFTDateTime)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field10', ogr.OFTBinary)
    feat_defn.AddFieldDefn(field_defn)
    field_defn = ogr.FieldDefn('field11', ogr.OFTInteger64)
    feat_defn.AddFieldDefn(field_defn)

    feat = ogr.Feature(feat_defn)
    feat.SetFID(100)
    feat.SetField(0, 1)
    feat.SetField(1, 1.2)
    feat.SetField(2, "A")
    feat.SetFieldIntegerList(3, [1, 2])
    feat.SetFieldDoubleList(4, [1.2, 3.4])
    feat.SetFieldStringList(5, ["A", "B"])
    feat.SetField(6, 2010, 1, 8, 22, 48, 15, 4)
    feat.SetField(7, 2010, 1, 8, 22, 48, 15, 4)
    feat.SetField(8, 2010, 1, 8, 22, 48, 15, 4)
    feat.SetFieldBinaryFromHexString(9, '012345678ABCDEF')
    feat.SetField(10, 1234567890123)

    feat_clone = feat.Clone()
    if not feat.Equal(feat_clone):
        feat.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    geom = ogr.CreateGeometryFromWkt('POINT(0 1)')
    feat_almost_clone.SetGeometry(geom)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    geom = ogr.CreateGeometryFromWkt('POINT(0 1)')
    feat.SetGeometry(geom)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_clone = feat.Clone()
    if not feat.Equal(feat_clone):
        feat.DumpReadable()
        feat_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFID(99)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetField(0, 2)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetField(1, 2.2)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetField(2, "B")
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldIntegerList(3, [1, 2, 3])
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldIntegerList(3, [1, 3])
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldDoubleList(4, [1.2, 3.4, 5.6])
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldDoubleList(4, [1.2, 3.5])
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldStringList(5, ["A", "B", "C"])
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldStringList(5, ["A", "D"])
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    for num_field in [6, 7, 8]:
        for i in range(7):
            feat_almost_clone = feat.Clone()
            feat_almost_clone.SetField(num_field, 2010 + (i == 0), 1 + (i == 1),
                                       8 + (i == 2), 22 + (i == 3), 48 + (i == 4),
                                       15 + (i == 5), 4 + (i == 6))
            if feat.Equal(feat_almost_clone):
                feat.DumpReadable()
                feat_almost_clone.DumpReadable()
                return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetFieldBinaryFromHexString(9, '00')
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetField(10, 2)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    feat_almost_clone = feat.Clone()
    feat_almost_clone.SetField(10, 2)
    if feat.Equal(feat_almost_clone):
        feat.DumpReadable()
        feat_almost_clone.DumpReadable()
        return 'fail'

    return 'success'

###############################################################################
# Issue several RegisterAll() to check that OGR drivers are good citizens


def ogr_basic_8():

    ogr.RegisterAll()
    ogr.RegisterAll()
    ogr.RegisterAll()

    return 'success'

###############################################################################
# Test ogr.GeometryTypeToName (#4871)


def ogr_basic_9():

    geom_type_tuples = [[ogr.wkbUnknown, "Unknown (any)"],
                        [ogr.wkbPoint, "Point"],
                        [ogr.wkbLineString, "Line String"],
                        [ogr.wkbPolygon, "Polygon"],
                        [ogr.wkbMultiPoint, "Multi Point"],
                        [ogr.wkbMultiLineString, "Multi Line String"],
                        [ogr.wkbMultiPolygon, "Multi Polygon"],
                        [ogr.wkbGeometryCollection, "Geometry Collection"],
                        [ogr.wkbNone, "None"],
                        [ogr.wkbUnknown | ogr.wkb25DBit, "3D Unknown (any)"],
                        [ogr.wkbPoint25D, "3D Point"],
                        [ogr.wkbLineString25D, "3D Line String"],
                        [ogr.wkbPolygon25D, "3D Polygon"],
                        [ogr.wkbMultiPoint25D, "3D Multi Point"],
                        [ogr.wkbMultiLineString25D, "3D Multi Line String"],
                        [ogr.wkbMultiPolygon25D, "3D Multi Polygon"],
                        [ogr.wkbGeometryCollection25D, "3D Geometry Collection"],
                        [123456, "Unrecognized: 123456"]
                       ]

    for geom_type_tuple in geom_type_tuples:
        if ogr.GeometryTypeToName(geom_type_tuple[0]) != geom_type_tuple[1]:
            gdaltest.post_reason('fail')
            print('Got %s, expected %s' % (ogr.GeometryTypeToName(geom_type_tuple[0]), geom_type_tuple[1]))
            return 'fail'

    return 'success'

###############################################################################
# Run test_ogrsf -all_drivers


def ogr_basic_10():

    import test_cli_utilities
    if test_cli_utilities.get_test_ogrsf_path() is None:
        return 'skip'

    ret = gdaltest.runexternal(test_cli_utilities.get_test_ogrsf_path() + ' -all_drivers')

    if ret.find('INFO') == -1 or ret.find('ERROR') != -1:
        print(ret)
        return 'fail'

    return 'success'

###############################################################################
# Test double call to UseExceptions() (#5704)


def ogr_basic_11():

    if not ogrtest.have_geos():
        return 'skip'

    used_exceptions_before = ogr.GetUseExceptions()
    for _ in range(2):
        ogr.UseExceptions()
        geom = ogr.CreateGeometryFromWkt('POLYGON ((-65 0, -30 -30, -30 0, -65 -30, -65 0))')
        with gdaltest.error_handler():
            geom.IsValid()
    if used_exceptions_before == 0:
        ogr.DontUseExceptions()

    return 'success'

###############################################################################
# Test OFSTBoolean, OFSTInt16 and OFSTFloat32


def ogr_basic_12():

    # boolean integer
    feat_def = ogr.FeatureDefn()
    if ogr.GetFieldSubTypeName(ogr.OFSTBoolean) != 'Boolean':
        gdaltest.post_reason('fail')
        return 'fail'
    field_def = ogr.FieldDefn('fld', ogr.OFTInteger)
    field_def.SetSubType(ogr.OFSTBoolean)
    if field_def.GetSubType() != ogr.OFSTBoolean:
        gdaltest.post_reason('fail')
        return 'fail'
    feat_def.AddFieldDefn(field_def)

    f = ogr.Feature(feat_def)
    f.SetField('fld', 0)
    f.SetField('fld', 1)
    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    f.SetField('fld', 2)
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if f.GetField('fld') != 1:
        gdaltest.post_reason('fail')
        return 'fail'

    f.SetField('fld', '0')
    f.SetField('fld', '1')
    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    f.SetField('fld', '2')
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if f.GetField('fld') != 1:
        gdaltest.post_reason('fail')
        return 'fail'

    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    field_def = ogr.FieldDefn('fld', ogr.OFTString)
    field_def.SetSubType(ogr.OFSTBoolean)
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if field_def.GetSubType() != ogr.OFSTNone:
        gdaltest.post_reason('fail')
        return 'fail'

    # boolean list
    feat_def = ogr.FeatureDefn()
    field_def = ogr.FieldDefn('fld', ogr.OFTIntegerList)
    field_def.SetSubType(ogr.OFSTBoolean)
    if field_def.GetSubType() != ogr.OFSTBoolean:
        gdaltest.post_reason('fail')
        return 'fail'
    feat_def.AddFieldDefn(field_def)

    f = ogr.Feature(feat_def)
    f.SetFieldIntegerList(0, [0, 1])
    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    f.SetFieldIntegerList(0, [0, 1, 2, 1])
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if f.GetField('fld') != [0, 1, 1, 1]:
        print(f.GetField('fld'))
        gdaltest.post_reason('fail')
        return 'fail'

    # int16 integer
    feat_def = ogr.FeatureDefn()
    if ogr.GetFieldSubTypeName(ogr.OFSTInt16) != 'Int16':
        gdaltest.post_reason('fail')
        return 'fail'
    field_def = ogr.FieldDefn('fld', ogr.OFTInteger)
    field_def.SetSubType(ogr.OFSTInt16)
    if field_def.GetSubType() != ogr.OFSTInt16:
        gdaltest.post_reason('fail')
        return 'fail'
    feat_def.AddFieldDefn(field_def)

    f = ogr.Feature(feat_def)
    f.SetField('fld', -32768)
    f.SetField('fld', 32767)
    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    f.SetField('fld', -32769)
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if f.GetField('fld') != -32768:
        gdaltest.post_reason('fail')
        return 'fail'
    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    f.SetField('fld', 32768)
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if f.GetField('fld') != 32767:
        gdaltest.post_reason('fail')
        return 'fail'

    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    field_def = ogr.FieldDefn('fld', ogr.OFTString)
    field_def.SetSubType(ogr.OFSTInt16)
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if field_def.GetSubType() != ogr.OFSTNone:
        gdaltest.post_reason('fail')
        return 'fail'

    # float32
    feat_def = ogr.FeatureDefn()
    if ogr.GetFieldSubTypeName(ogr.OFSTFloat32) != 'Float32':
        gdaltest.post_reason('fail')
        return 'fail'
    field_def = ogr.FieldDefn('fld', ogr.OFTReal)
    field_def.SetSubType(ogr.OFSTFloat32)
    if field_def.GetSubType() != ogr.OFSTFloat32:
        gdaltest.post_reason('fail')
        return 'fail'
    feat_def.AddFieldDefn(field_def)

    if False:
        f = ogr.Feature(feat_def)
        gdal.ErrorReset()
        f.SetField('fld', '1.23')
        if gdal.GetLastErrorMsg() != '':
            gdaltest.post_reason('fail')
            return 'fail'
        gdal.ErrorReset()
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        f.SetField('fld', 1.230000000001)
        gdal.PopErrorHandler()
        if gdal.GetLastErrorMsg() == '':
            gdaltest.post_reason('fail')
            return 'fail'
        if abs(f.GetField('fld') - 1.23) < 1e-8:
            gdaltest.post_reason('fail')
            f.DumpReadable()
            return 'fail'

    gdal.ErrorReset()
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    field_def = ogr.FieldDefn('fld', ogr.OFSTFloat32)
    field_def.SetSubType(ogr.OFSTInt16)
    gdal.PopErrorHandler()
    if gdal.GetLastErrorMsg() == '':
        gdaltest.post_reason('fail')
        return 'fail'
    if field_def.GetSubType() != ogr.OFSTNone:
        gdaltest.post_reason('fail')
        return 'fail'

    return 'success'

###############################################################################
# Test OGRParseDate (#6452)


def ogr_basic_13():
    feat_defn = ogr.FeatureDefn('test')
    field_defn = ogr.FieldDefn('date', ogr.OFTDateTime)
    feat_defn.AddFieldDefn(field_defn)

    tests = [('2016/1/1', '2016/01/01 00:00:00'),
             ('2016/1/1 12:34', '2016/01/01 12:34:00'),
             ('2016/1/1 12:34:56', '2016/01/01 12:34:56'),
             ('2016/1/1 12:34:56.789', '2016/01/01 12:34:56.789'),
             ('2016/12/31', '2016/12/31 00:00:00'),
             ('-2016/12/31', '-2016/12/31 00:00:00'),
             ('2016-12-31', '2016/12/31 00:00:00'),
             ('0080/1/1', '0080/01/01 00:00:00'),
             ('80/1/1', '1980/01/01 00:00:00'),
             ('0010/1/1', '0010/01/01 00:00:00'),
             ('9/1/1', '2009/01/01 00:00:00'),
             ('10/1/1', '2010/01/01 00:00:00'),
             ('2016-13-31', None),
             ('2016-0-31', None),
             ('2016-1-32', None),
             ('2016-1-0', None),
             ('0/1/1', '2000/01/01 00:00:00'),
             ('00/1/1', '2000/01/01 00:00:00'),
             ('00/00/00', None),
             ('000/00/00', None),
             ('0000/00/00', None),
             ('//foo', None)]

    for (val, expected_ret) in tests:
        f = ogr.Feature(feat_defn)
        f.SetField('date', val)
        if f.GetField('date') != expected_ret:
            gdaltest.post_reason('fail')
            print(val)
            print(f.GetField('date'))
            return 'fail'

    return 'success'

###############################################################################
# Test ogr.Open(.) in an empty directory


def ogr_basic_14():

    os.mkdir('tmp/ogr_basic_14')
    os.chdir('tmp/ogr_basic_14')
    ds = ogr.Open('.')
    os.chdir('../..')

    if ds is not None:
        return 'fail'

    os.rmdir('tmp/ogr_basic_14')

    return 'success'

###############################################################################
# Test exceptions with OGRErr return code


def ogr_basic_15():

    ds = ogr.Open('data/poly.shp')
    lyr = ds.GetLayer(0)

    used_exceptions_before = ogr.GetUseExceptions()
    ogr.UseExceptions()
    try:
        lyr.CreateFeature(ogr.Feature(lyr.GetLayerDefn()))
    except RuntimeError as e:
        ok = str(e).find('CreateFeature : unsupported operation on a read-only datasource') >= 0
        if not ok:
            print('Got: %s' + str(e))
            return 'fail'
        return 'success'
    finally:
        if used_exceptions_before == 0:
            ogr.DontUseExceptions()

    print('Expected exception')
    return 'fail'


###############################################################################
# Test issue with Python 3.5 and older SWIG (#6749)

def ogr_basic_16_make_geom():
    geom = ogr.Geometry(ogr.wkbPoint)
    geom.AddPoint_2D(0, 0)
    return geom


def ogr_basic_16_gen_list(N):
    for i in range(N):
        ogr_basic_16_make_geom()
        yield i


def ogr_basic_16():

    if list(ogr_basic_16_gen_list(2)) != [0, 1]:
        return 'fail'

    return 'success'


def ogr_basic_invalid_unicode():

    if sys.version_info >= (3, 0, 0):
        val = '\udcfc'
    else:
        exec("val = u'\\udcfc'")

    try:
        ogr.Open(val)
    except:
        pass

    data_source = ogr.GetDriverByName('Memory').CreateDataSource('')
    layer = data_source.CreateLayer("test")
    layer.CreateField(ogr.FieldDefn('attr', ogr.OFTString))
    feature = ogr.Feature(layer.GetLayerDefn())
    try:
        feature.SetField('attr', val)
    except:
        pass

    return 'success'


def ogr_basic_dataset_slice():

    ds = ogr.GetDriverByName('Memory').CreateDataSource('')
    ds.CreateLayer('lyr1')
    ds.CreateLayer('lyr2')
    ds.CreateLayer('lyr3')

    lyrs = [lyr.GetName() for lyr in ds[1:3]]
    if lyrs != ['lyr2', 'lyr3']:
        gdaltest.post_reason('fail')
        print(lyrs)
        return 'fail'

    lyrs = [lyr.GetName() for lyr in ds[0:4]]
    if lyrs != ['lyr1', 'lyr2', 'lyr3']:
        gdaltest.post_reason('fail')
        print(lyrs)
        return 'fail'

    lyrs = [lyr.GetName() for lyr in ds[0:3:2]]
    if lyrs != ['lyr1', 'lyr3']:
        gdaltest.post_reason('fail')
        print(lyrs)
        return 'fail'

    return 'success'


###############################################################################
# cleanup


def ogr_basic_cleanup():
    gdaltest.lyr = None
    gdaltest.ds = None

    return 'success'


gdaltest_list = [
    ogr_basic_1,
    ogr_basic_2,
    ogr_basic_3,
    ogr_basic_4,
    ogr_basic_5,
    ogr_basic_6,
    ogr_basic_7,
    ogr_basic_8,
    ogr_basic_9,
    ogr_basic_10,
    ogr_basic_11,
    ogr_basic_12,
    ogr_basic_13,
    ogr_basic_14,
    ogr_basic_15,
    ogr_basic_16,
    ogr_basic_invalid_unicode,
    ogr_basic_dataset_slice,
    ogr_basic_cleanup]

# gdaltest_list = [ ogr_basic_13 ]

if __name__ == '__main__':

    gdaltest.setup_run('ogr_basic_test')

    gdaltest.run_tests(gdaltest_list)

    gdaltest.summarize()
