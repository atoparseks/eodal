'''
Module defining geographic features for mapping.

Copyright (C) 2022 Lukas Valentin Graf

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import geopandas as gpd
import pandas as pd

from shapely.geometry import MultiPoint, MultiPolygon, Point, Polygon
from typing import Any, Dict, Optional

allowed_geom_types = [MultiPoint, MultiPolygon, Point, Polygon]

class Feature:
    """
    Generic class for a geographic feature

    :attrib name:
        name of the feature (used for identification)
    :attrib geometry:
        `shapely` geometry of the feature in a spatial reference system
    :attrib epgs:
        spatial coordinate reference system of the feature as EPSG code
    :attrib attributes:
        optional attributes of the feature
    """
    def __init__(
            self,
            name: str,
            geometry: MultiPoint | MultiPolygon | Point | Polygon,
            epsg: int,
            attributes: Optional[Dict[str, Any] | pd.Series] = {}
        ):
        """
        Class constructor

        :param name:
            name of the feature (used for identification)
        :param geometry:
            `shapely` geometry of the feature in a spatial reference system
        :param epgs:
            spatial coordinate reference system of the feature as EPSG code
        :param attributes:
            optional attributes of the feature
        """
        # check inputs
        if name == '':
            raise ValueError(f'Empty feature names are not allowed')
        if type(geometry) not in allowed_geom_types:
            raise ValueError(f'geometry must of type {",".join(allowed_geom_types)}')
        if type(epsg) != int or epsg <= 0:
            raise ValueError('EPSG code must be a positive integer value')
        if not isinstance(attributes, pd.Series) and not isinstance(attributes, dict):
            raise ValueError('Attributes must pd.Series or dictionary')

        self._name = name
        self._geometry = geometry
        self._epsg = epsg
        self._attributes = attributes

    def __repr__(self) -> str:
        return f'Name\t\t{self.name}\nGeometry\t' + \
            f'{self.geometry}\nEPSG Code\t{self.epsg}' + \
            f'\nAttributes\t{self.attributes}'

    @property
    def attributes(self) -> Dict:
        """feature attributes"""
        if isinstance(self._attributes, pd.Series):
            return self._attributes.to_dict()
        else:
            return self._attributes

    @property
    def epsg(self) -> int:
        """the feature coordinate reference system as EPSG code"""
        return self._epsg

    @property
    def geometry(self) -> MultiPoint | MultiPolygon | Point | Polygon:
        """the feature geometry"""
        return self._geometry

    @property
    def name(self) -> str:
        """the feature name"""
        return self._name

    @classmethod
    def from_geoseries(cls, gds: gpd.GeoSeries):
        """
        Feature object from `GeoSeries`

        :param gds:
            `GeoSeries` to cast to Feature
        :returns:
            Feature instance created from input `GeoSeries`
        """
        return cls(
            name=gds.name,
            geometry=gds.geometry.values[0],
            epsg=gds.crs.to_epsg(),
            attributes=gds.attrs
        )

    def to_epsg(self, epsg: int):
        """
        Projects the feature into a different spatial reference system
        identified by an EPSG code. Returns a copy of the Feature with
        transformed coordinates.

        :param epsg:
            EPSG code of the reference system the feature is project to
        :returns:
            new Feature instance in the target spatial reference system
        """
        gds = self.to_geoseries()
        gds_projected = gds.to_crs(epsg=epsg)
        return Feature.from_geoseries(gds_projected)

    def to_geoseries(self) -> gpd.GeoSeries:
        """
        Casts the feature to a GeoSeries object

        :returns:
            Feature object casted as `GeoSeries`
        """
        gds = gpd.GeoSeries([self.geometry], crs=f'EPSG:{self.epsg}')
        # add attributes from Feature
        gds.attrs = self.attributes
        # set name of Feature to GeoSeries
        gds.name = self.name
        return gds

    def to_dict(self) -> Dict[str, Any]:
        """
        Casts feature to a pure Python dictionary

        :returns:
            Feature object as pure Python dictionary
        """
        feature_dict = {}
        feature_dict['name'] = self.name
        feature_dict['epsg'] = self.epsg
        feature_dict['geometry'] = self.geometry.wkt
        feature_dict['attributes'] = self.attributes
        return feature_dict

if __name__ == '__main__':

    # working constructor calls
    geom = Point([49,11])
    epsg = 4326
    name = 'Test Point'
    feature = Feature(name, geom, epsg)

    assert feature.geometry == geom, 'geometry differs'
    assert feature.epsg == epsg, 'EPSG code differs'
    assert feature.name == name, 'name differs'
    assert feature.attributes == {}, 'attributes must be empty'

    attributes = {'key': 'value'}
    feature = Feature(name, geom, epsg, attributes)
    assert feature.attributes == attributes, 'attributes differ'

    attributes = pd.Series({'key1': 'value1', 'key2': 'value2'})
    feature = Feature(name, geom, epsg, attributes)
    assert feature.attributes == attributes.to_dict(), 'attributes differ'

    gds = feature.to_geoseries()
    assert gds.name == feature.name, 'name differs'
    assert gds.crs.to_epsg() == feature.epsg, 'EPSG differs'
    assert gds.attrs == feature.attributes, 'attributes differ'

    # from_geoseries class method
    gds.attrs = {}
    feature = Feature.from_geoseries(gds)
    assert gds.name == feature.name, 'name differs'
    assert gds.crs.to_epsg() == feature.epsg, 'EPSG differs'
    assert gds.attrs == feature.attributes, 'attributes differ'

    # project into another spatial reference system
    feature_utm = feature.to_epsg(epsg=32632)
    assert feature_utm.epsg == 32632, 'projection had no effect'
    assert feature_utm.name == feature.name, 'name got lost'
    assert feature_utm.attributes == feature.attributes, 'attributes got lost'
