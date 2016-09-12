# coding:utf-8

# TMX library
# Copyright (c) 2016 wboy <mrtop@126.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""=========================================
TMX Map Format (TiledMapEditor 0.17.0)
    http://doc.mapeditor.org/reference/tmx-map-format/#tmx-map-format
========================================="""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


import logging
import six
import os
import json
import base64
import gzip
import zlib
import array
from itertools import chain, product
from collections import defaultdict, namedtuple, OrderedDict
#from xml.etree.ElementTree import *
from ElementTree import *
from six.moves import map


logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
logger.addHandler(streamHandler)
logger.setLevel(logging.INFO)


__all__ = ['TiledObjectType',
           'TiledProperty',
           'TiledProperties',
           'TiledMap',
           'TiledTileset',
           'TiledTileoffset',
           'TiledProperties',
           'TiledProperty',
           'TiledTerraintypes',
           'TiledTerrain',
           'TiledTile',
           'TiledImage',
           'TiledAnimation',
           'TiledFrame',
           'TiledLayer',
           'TiledData',
           'TiledImagelayer',
           'TiledObjectgroup',
           'TiledObject',
           'TiledEllipse',
           'TiledPolygon',
           'TiledPolyline']

types = defaultdict(lambda: str)
types.update({
    "version": str,
    "orientation": str,
    "renderorder": str,
    "width": int,
    "height": int,
    "tilewidth": int,
    "tileheight": int,
    "hexsidelength": int,
    "staggeraxis": str,
    "staggerindex": str,
    "backgroundcolor": str,
    "nextobjectid": int,
    "firstgid": int,
    "source": str,
    "name": str,
    "spacing": int,
    "margin": int,
    "tilecount": int,
    "columns": int,
    "x": int,
    "y": int,
    "format": str,
    "trans": str,
    "tile": int,
    "id": int,
    "terrain" : str,
    "probability": float,
    "tileid": int,
    "duration": int,
    "opacity": float,
    "visible": int,
    "offsetx": float,
    "offsety": float,
    "encoding": str,
    "compression": str,
    "gid": int,
    "color": str,
    "draworder": str,
    "type": str,
    "rotation": float,
    "points": str,
    "value": str,
})

typesdefaultvalue = defaultdict(lambda: str)
typesdefaultvalue.update({
    "version": "1.0",
    "orientation": "orthogonal",
    "renderorder": "right-down",
    "width": 10,
    "height": 10,
    "tilewidth": 32,
    "tileheight": 32,
    "hexsidelength": 0,
    "staggeraxis": "y",
    "staggerindex": "odd",
    "backgroundcolor": None,
    "nextobjectid": 0,
    "firstgid": 1,
    "source": None,
    "name": None,
    "spacing": None,
    "margin": None,
    "tilecount": None,
    "columns": None,
    "x": None,
    "y": None,
    "format": None,
    "trans": None,
    "tile": None,
    "id": None,
    "terrain" : None,
    "probability": None,
    "tileid": None,
    "duration": None,
    "opacity": None,
    "visible": None,
    "offsetx": None,
    "offsety": None,
    "encoding": None,
    "compression": None,
    "gid": None,
    "color": None,
    "draworder": None,
    "type": None,
    "rotation": None,
    "points": None,
    "value": None,
})

classtypesnodename = defaultdict(lambda: str)
classtypesnodename.update({
    "TiledMap"                  : "map",
    "TiledProperty"             : "property",
    "TiledProperties"           : "properties",
    "TiledTileset"              : "tileset",
    "TiledTileoffset"           : "tileoffset",
    "TiledTerraintypes"         : "terraintypes",
    "TiledTerrain"              : "terrain",
    "TiledTile"                 : "tile",
    "TiledImage"                : "image",
    "TiledAnimation"            : "animation",
    "TiledFrame"                : "frame",
    "TiledLayer"                : "layer",
    "TiledData"                 : "data",
    "TiledData_Tile"            : "tile",
    "TiledImagelayer"           : "imagelayer",
    "TiledObjectgroup"          : "objectgroup",
    "TiledObject"               : "object",
    "TiledEllipse"              : "ellipse",
    "TiledPolygon"              : "polygon",
    "TiledPolyline"             : "polyline",
})

def get_class_node_name(classname):
    if not classtypesnodename.has_key(classname):
            logger.error("classname : %s not is standard tmx data format", classname)
            raise Exception
    return classtypesnodename[classname]

def indent( elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i
    return elem

def read_positions(text):
    """parse a text string of float tuples and return [(x,...),...]
    """
    if text is not None:
        return tuple(tuple(map(format_value, i.split(','))) for i in text.split())
    return None

def write_positions(positions):
    """parse float tuples of a text string

    return string
    """
    result = ""
    if positions is not None:
        for x,y in positions:
            result = "%s %s,%s" % (result, x, y)
    return result

def format_value(value, typestr = None):
    if typestr is not None:
        if typestr == "bool":
            if value == str(True).lower(): return True
            else: return False
        elif typestr == "float":
            f = float(value)
            if f == int(f):
                return int(f)
            else:
                return f
        elif typestr == "int":
            return int(value)
        return value
    else:
        if str(value).lower() == str(True).lower(): 
            return True
        elif str(value).lower() == str(False).lower():
            return True
        else:
            try:
                f = float(value)
                if f == int(f):
                    return int(f)
                else:
                    return f
            except:
                return value
    
def convert_to_bool(text):
    """ Convert a few common variations of "true" and "false" to boolean

    :param text: string to test
    :return: boolean
    :raises: ValueError
    """
    try:
        return bool(int(text))
    except:
        pass

    text = str(text).lower()
    if text == "true":
        return True
    if text == "yes":
        return True
    if text == "false":
        return False
    if text == "no":
        return False
    if text == 0:
        return False
    if text == 1:
        return True
    
    raise ValueError

def float_to_int(value):
    if type(value) is not float:
        return value
    else:
        try:
            f = float(value)
            if f == int(f):
                return int(f)
            else:
                return f
        except:
            return value

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
 
TiledObjectType = Enum(["NONE", "TILE", "RECTANGLE", "ELLIPSE", "POLYGON", "POLYLINE"])


class BaseObject(object):
    def __init__(self, tiledmap = None, parent=None):
        """ Initialize default value
        """
        items = vars(self).items()
        if items is not None:
            for key, value in vars(self).items():
                if key.startswith('_'):
                    continue
                if typesdefaultvalue.has_key(key):
                    setattr(self, key, typesdefaultvalue[key])

        self._tiledmap = tiledmap
        self._parent = parent

    def __str__(self):
        try:
            return tostring(self.write_xml())
        except:
            raise ValueError

    def read_xml(self, node, clearlevel = 1):
        """read the xml attributes to self

        :param node: etree element
        :param clearlevel: clear attribute level
                           0, Don't Clear
                           1, Clear public
                           2, Clear public and protect
                           3, All Clear (public and protect and private)
        :rtype : BaseObject instance
        """
        # all attr set None before read xml
        items = vars(self).items()
        if items is not None:
            for key, value in vars(self).items():
                if clearlevel == 0:
                    return
                elif clearlevel == 1:
                    if key.startswith('_'): continue
                elif clearlevel == 2:
                    if key.startswith('__'): continue
                setattr(self, key, None)

        classname = self.__class__.__name__
        classnodename = get_class_node_name(classname)
        if classnodename != node.tag:
            logger.error("classnodename != node.tag. classnodename:%s, node.tag:%s", classnodename, node.tag)
            raise Exception
        for key, value in node.items():
                casted_value = types[key](value)
                setattr(self, key, casted_value)
        return self

    def write_xml(self, outattrorder = None):
        """write the attributes to xml

        :param outattrorder: list()  out attr in order
                        None(default) is all attr is out
        :rtype : Element instance
        """
        classname = self.__class__.__name__
        element = Element(get_class_node_name(classname))

        dictattr = self.__dict__;
        orderdictattr = OrderedDict()
        if dictattr:
            if outattrorder is None or not outattrorder:
                keys = dictattr.keys()
            else:
                keys = outattrorder

            for key in keys:
                if key.startswith('_') or not dictattr.has_key(key):
                    continue
                value = dictattr[key]
                if value is None : continue
                if type(value) is list:
                   element = self._child_list_attr_write_xml(element, value)
                elif classtypesnodename.has_key(type(value).__name__):
                    element = self._child_attr_write_xml(element, value)
                else:
                    orderdictattr[key] = ("%s" % float_to_int(value))
        if orderdictattr:
            element.attrib = orderdictattr
        return element

    def write_json(self):
        """write the attributes to json

        :rtype : string
        """
        dictattr = self.__dict__;
        if dictattr is None:
            return None

        dic = {}
        for key, value in dictattr.items():
            if key.startswith('_'):
                continue
            if value is None : continue
            if type(value) is list:
                dic.update(self._child_list_attr_write_json(key, value))
            elif classtypesnodename.has_key(type(value).__name__):
                dic = self._child_attr_write_json(dic, value)
            else:
                dic[key] = format_value(value)
        if dic:
            return dic
        else:
            return None

    def _child_attr_read_xml(self, parentelement, type, parent):
        childattrelement = parentelement.find(get_class_node_name(type.__name__))
        if childattrelement is not None:
            return type(self._tiledmap, parent).read_xml(childattrelement)
        return None

    def _child_list_attr_read_xml(self, parentelement, type, parent):
        childlistattrelement = parentelement.findall(get_class_node_name(type.__name__))
        if childlistattrelement is not None:
            ls = list()
            for childelement in childlistattrelement:
                if childelement is not None:
                    child = type(self._tiledmap, parent).read_xml(childelement)
                    ls.append(child)
            if ls:
                return ls
        return None

    def _child_attr_write_xml(self, parentelement, childattr):
        if childattr:
            childattrelement = childattr.write_xml()
            if childattrelement is not None:
                parentelement.append(childattrelement)
        return parentelement

    def _child_list_attr_write_xml(self, parentelement, childattr):
        if childattr:
            for attr in childattr:
                parentelement = self._child_attr_write_xml(parentelement, attr)
        return parentelement

    def _child_attr_write_json(self, parentdict, childattr):
        if childattr:
            childattrdict = childattr.write_json()
            if childattrdict is not None:
                parentdict.update(childattrdict)
        return parentdict

    def _child_list_attr_write_json(self, parentname, childattr):
        ls = list()
        if childattr:
            for attr in childattr:
                ls.append(attr.write_json())
        return {parentname : ls}
            
            

class TiledMap(BaseObject):
    """TileMap Data. Contains the layers, objects, images, and others
    <map>
    This class is meant to handle most of the work you need to do to use a map.

    Can contain: properties, tileset, layer, objectgroup, imagelayer
    """
    def __init__(self, filepath = None):
        self.version = "1.0"
        self.orientation= "orthogonal"
        self.renderorder = "right-down"
        self.width = 10
        self.height = 10
        self.tilewidth = 32
        self.tileheight = 32
        self.hexsidelength = 0
        self.staggeraxis = "y"
        self.staggerindex = "odd"
        self.backgroundcolor = None
        self.nextobjectid = 0
        self.properties = None
        self.tilesets = None
        self.layers = None
        super(TiledMap, self).__init__(self, None)

        self.__encoding = None
        self.__compression = None
        self.__unfoldtsx = False

        self.__filepath = filepath
        if filepath:
            elementTree = parse(filepath).getroot()
            self.read_xml(elementTree)


    def read_xml(self, node):
        super(TiledMap, self).read_xml(node)
        
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.tilesets = self._child_list_attr_read_xml(node, TiledTileset, self)
        ls = []
        for child in node:
            if child.tag == get_class_node_name(TiledLayer.__name__):
                tiledlayer = TiledLayer(self, self).read_xml(child)
                if tiledlayer is not None:
                   ls.append(tiledlayer)
            if child.tag == get_class_node_name(TiledImagelayer.__name__):
                tiledImagelayer = TiledImagelayer(self, self).read_xml(child)
                if tiledImagelayer is not None:
                    ls.append(tiledImagelayer)
            if child.tag == get_class_node_name(TiledObjectgroup.__name__):
                tiledObjectgroup = TiledObjectgroup(self, self).read_xml(child)
                if tiledObjectgroup is not None:
                    ls.append(tiledObjectgroup)
        if ls: self.layers = ls
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["version", "orientation", "renderorder", "width",
                            "height", "tilewidth", "tileheight", "hexsidelength",
                            "staggeraxis", "staggerindex", "backgroundcolor",
                            "nextobjectid", "properties", "tilesets", "layers"]
        return super(TiledMap, self).write_xml(outattrorder)

    def get_tiledtile_by_gid(self, gid):
        """ get TiledTile by gid
        rtype : TiledTile instance
        """
        firstgid = endgid = 0
        length = len(self.tilesets)
        for i in range(length):
            tileset = self.tilesets[i]
            firstgid = tileset.firstgid
            if i >= length - 1 :
                return tileset.get_tiledtile_by_id(gid - firstgid)
            else:
                endgid = self.tilesets[i + 1].firstgid
                if firstgid <= gid and endgid > gid:
                    return tileset.get_tiledtile_by_id(gid - firstgid)
        return None

    @property
    def filepath(self):
        """ TileMap file path
        """
        return self.__filepath

    @property
    def encoding(self):
        """encoding: 
        The encoding used to encode the tile layer data.
        When used, it can be "base64" and "csv" at the moment.
        """
        return self.__encoding

    @encoding.setter
    def encoding(self, value):
        self.__encoding = value

    @property
    def compression(self):
        """compression: 
        The compression used to compress the tile layer data. 
        Tiled Qt supports "gzip" and "zlib".
        None : Keep the initial state
        """
        return self.__compression

    @compression.setter
    def compression(self, value):
        self.__compression = value

    @property
    def unfoldtsx(self):
        """The unfoldtsx used to read .tsx file data.
        """
        return self.__unfoldtsx

    @unfoldtsx.setter
    def unfoldtsx(self, value):
        self.__unfoldtsx = value


    @staticmethod
    def read_tmx_xml(filepath):
        """Read .tmx file

        :param filepath: string file's path
        :rtype TiledMap instance
        """

        if not filepath:
            logger.error('file path is not null')
            raise Exception
        if not os.path.exists(filepath):
            logger.error('file is not exit : %s', filepath)
            raise Exception
        if os.path.splitext(filepath)[1].lower() != ".tmx":
            Logger.error('file is not .tmx file : %s', filepath)
            raise Exception
        return TiledMap(filepath)

    @staticmethod
    def write_tmx_xml(tiledmap, filepath, 
                      encoding = None, compression = None,
                      unfoldtsx = True):
        """Read .tmx file

        :param filepath: string file's path
        :param encoding: 
                        The encoding used to encode the tile layer data.
                        When used, it can be "xml" and "base64" and "csv" at the moment.
                        None : Keep the initial state
        :param compression: 
                        The compression used to compress the tile layer data. 
                        Tiled Qt supports "gzip" and "zlib".
                        None : Keep the initial state
        :param unfoldtsx:
                        The unfoldtsx used to read .tsx file data.
                        True : When tileset source is .tsx file. read .tsx file data,
                               and combine to out data
                        False : Keep the initial state
        :rtype True or False
        """
        try:
            tiledmap.encoding = encoding
            tiledmap.compression = compression
            tiledmap.unfoldtsx = unfoldtsx
            element = tiledmap.write_xml()
            indent(element)
            ElementTree(element).write(filepath, encoding="utf-8", xml_declaration="utf-8", method="xml")
        except Exception,e:
            logger.exception(e) 
            return False
        return True

    @staticmethod
    def write_tmx_json(tiledmap, filepath, 
                       encoding = None, compression = None,
                       unfoldtsx = True):
        """Read .tmx file

        :param filepath: string file's path
        :param encoding: 
                        The encoding used to encode the tile layer data.
                        When used, it can be "base64" and "csv" at the moment.
                        None : Keep the initial state
        :param compression: 
                        The compression used to compress the tile layer data. 
                        Tiled Qt supports "gzip" and "zlib".
                        None : Keep the initial state
        :param unfoldtsx:
                        The unfoldtsx used to read .tsx file data.
                        True : When tileset source is .tsx file. read .tsx file data,
                               and combine to out data
                        False : Keep the initial state
        :rtype True or False
        """
        try:
            tiledmap.encoding = encoding
            tiledmap.compression = compression
            tiledmap.unfoldtsx = unfoldtsx
            dic = tiledmap.write_json()
            file = open(filepath, "wb")
            file.write(json.dumps(dic, indent = 4, sort_keys = True))
            file.flush()
            file.close()
        except Exception,e:
            logger.exception(e) 
            return False
        return True


class TiledTileset(BaseObject):
    """ Represents a Tiledset 
    <tileset>
    External tilesets are supported.  GID/ID's from Tiled are not guaranteed to
    be the same after loaded.

    Can contain: tileoffset (since 0.8), 
                 properties (since 0.8), 
                 image, 
                 terraintypes (since 0.9),
                 tile
    """
    def __init__(self, tiledmap, parent):
        self.firstgid = 1
        self.source = None
        self.name = None
        self.tilewidth = None
        self.tileheight = None
        self.spacing = 0
        self.margin = 0
        self.tilecount = None
        self.columns = None
        super(TiledTileset, self).__init__(tiledmap, parent)

        self.tileoffset = None
        self.properties = None
        self.terraintypes = None
        self.tiles = None
        self.image = None

    def read_xml(self, node):
        super(TiledTileset, self).read_xml(node)
        if self.source is not None and self.source[-4:].lower() == ".tsx":
            dirname = os.path.dirname(self._tiledmap.filepath)
            path = os.path.abspath(os.path.join(dirname, self.source))
            path = unicode(path, 'utf-8')
            node = parse(path).getroot()
            super(TiledTileset, self).read_xml(node, False)
        self.tileoffset = self._child_attr_read_xml(node, TiledTileoffset, self)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.terraintypes = self._child_attr_read_xml(node, TiledTerraintypes, self)
        self.tiles = self._child_list_attr_read_xml(node, TiledTile, self)
        self.image = self._child_attr_read_xml(node, TiledImage, self)
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            if self.source is not None and self.source[-4:].lower() == ".tsx":
                outattrorder = ["firstgid", "source"]
            else:
                outattrorder = ["firstgid", "source", "name", "tilewidth",
                                "tileheight", "spacing", "margin", "tilecount",
                                "columns", "tileoffset", "properties", "image",
                                "terraintypes", "tiles"]
        element = super(TiledTileset, self).write_xml(outattrorder)
        return element

    def write_json(self):
        if self.source is not None:
            return {"firstgid" : self.firstgid, "source" : self.source}
        dic = super(TiledTileset, self).write_json()
        if not dic.has_key("margin"): dic["margin"] = 0
        if not dic.has_key("spacing"): dic["spacing"] = 0
        del dic["tiles"]
        if self.tiles is not None:
            tilepropvalue = {}
            tileproptype = {}
            tilemap = {}
            for tile in self.tiles:
                tilemap.update(tile.write_json())
                if tile.properties is not None:
                   tempmap = tile.properties.write_json()
                   tilepropvalue.update({("%s" % tile.id) : tempmap["properties"]})
                   tileproptype.update({("%s" % tile.id) : tempmap["propertytypes"]})
            if tilemap:
                dic.update({"tiles" : tilemap})
            if tilepropvalue:
                dic.update({"tileproperties" : tilepropvalue})
            if tileproptype:
                dic.update({"tilepropertytypes" : tileproptype})
        if self.image is not None:
            dic["imageheight"] = self.image.height
            dic["imagewidth"] = self.image.width

        return dic

    def get_tiledtile_by_id(self, id):
        """ get tiledtile by id

        rtype : TiledTile instance
        """
        if self.tiles is not None:
            for tile in self.tiles:
                if tile.id == id:
                    return tile
        return None


class TiledTileoffset(BaseObject):
    """ Represents a Tileoffset 
    <tileoffset>
    This element is used to specify an offset in pixels, 
    to be applied when drawing a tile from the related tileset.
    When not present, no offset is applied.
    """
    def __init__(self, tiledmap, parent):
        self.x = None
        self.y = None
        super(TiledTileoffset, self).__init__(tiledmap, parent)

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["x", "y"]
        return super(TiledTileoffset, self).write_xml(outattrorder)

    def write_json(self):
        return {"tileoffset" : super(TiledTileoffset, self).write_json()}

class TiledProperties(BaseObject):
    """ Properties
    <properties>

    Can contain: property
    """
    
    def __init__(self, tiledmap, parent):
        super(TiledProperties, self).__init__(tiledmap, parent)
        self.properties = None

    def read_xml(self, node):
        super(TiledProperties, self).read_xml(node)
        self.properties = self._child_list_attr_read_xml(node, TiledProperty, self)
        return self

    def write_json(self):
        result = None
        propertiesjson = {}
        propertytypesjson = {}
        if self.properties is not None:
            for item in self.properties:
                propertiesjson[item.name] = format_value(item.value, item.type)
                if item.type is None:
                    propertytypesjson[item.name] = "string"
                else:
                    propertytypesjson[item.name] = item.type
        if propertiesjson and propertytypesjson:
            return {"properties":propertiesjson, "propertytypes" : propertytypesjson,}
        return None

class TiledProperty(BaseObject):
    """ Property
    <Property>
    """
    
    def __init__(self, tiledmap, parent):
        self.name = None
        self.type = None
        self.value = None
        super(TiledProperty, self).__init__(tiledmap, parent)
    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["name", "type", "value"]
        return super(TiledProperty, self).write_xml(outattrorder)

class TiledTerraintypes(BaseObject):
    """ Represents a Terraintypes
    <terraintypes>

    Can contain: terrain
    """
    def __init__(self, tiledmap, parent):
        super(TiledTerraintypes, self).__init__(tiledmap, parent)
        self.terrains = None

    def read_xml(self, node):
        super(TiledTerraintypes, self).read_xml(node)
        self.terrains = self._child_list_attr_read_xml(node, TiledTerrain, self)
        return self

class TiledTerrain(BaseObject):
    """ Represents a Terrain
    <terrain>

    Can contain: properties
    """
    def __init__(self, tiledmap, parent):
        self.name = None
        self.tile = 0
        super(TiledTerrain, self).__init__(tiledmap, parent)
        self.properties = None

    def read_xml(self, node):
        super(TiledTerrain, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        return self
    
    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["name", "tile", "properties"]
        return super(TiledTerrain, self).write_xml(outattrorder)

class TiledTile(BaseObject):
    """ Represents a Tile
    <tile>

    Can contain: properties, 
                 image (since 0.9), 
                 (Notice: 
                    objectgroup is in layer, not appear In other places.
                    so only this kind of situation.)
                 objectgroup (since 0.10),
                 animation (since 0.10)
    """
    def __init__(self, tiledmap, parent):
        self.id = None
        self.terrain = None
        self.probability = None
        super(TiledTile, self).__init__(tiledmap, parent)
        self.properties = None
        self.image = None
        self.animation = None

    def read_xml(self, node):
        super(TiledTile, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.image = self._child_attr_read_xml(node, TiledImage, self)
        self.animation = self._child_attr_read_xml(node, TiledAnimation, self)
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["id", "terrain", "probability", "properties",
                                "image", "animation"]
        return super(TiledTile, self).write_xml(outattrorder)

    def write_json(self):
        dic = {}
        if self.probability is not None:
            dic.update({"probability" : self.probability})
        if self.terrain is not None:
            ls = self.terrain.split(',')
            for i in range(len(ls)):
                if ls[i]:
                    ls[i] = format_value(ls[i])
                else:
                    ls[i] = -1
            dic.update({"terrain" : ls})
        #json 中提取属性 在父级实现统计然后json化
        #if self.__properties is not None:
        #    dic.update(self.__properties.write_json())
        if self.image is not None:
            dic.update(self.image.write_json())
        if self.animation is not None:
            dic.update(self.animation.write_json())
        return {("%s" % self.id) : dic}


class TiledImage(BaseObject):
    """ Represents a Image 
    <image>

    Can contain: data (since 0.9)
    Notice: I don't kown Where to use "data", so not read "data"
    """
    def __init__(self, tiledmap, parent):
        self.format = None
        self.source = None
        self.trans = None
        self.width = None
        self.height = None
        super(TiledImage, self).__init__(tiledmap, parent)

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["format", "trans", "width", "height",
                            "source"]
        return super(TiledImage, self).write_xml(outattrorder)

    def write_json(self):
        dic = { "image" : self.source }
        if self.trans is not None:
            dic["transparentcolor"] = self.trans
        return dic

class TiledAnimation(BaseObject):
    """ Represents a Animation 
    <animation>

    Contains a list of animation frames.

    Can contain: frame
    """
    def __init__(self, tiledmap, parent):
        super(TiledAnimation, self).__init__(tiledmap, parent)
        self.frames = None

    def read_xml(self, node):
        super(TiledAnimation, self).read_xml(node)
        self.frames = self._child_list_attr_read_xml(node, TiledFrame, self)
        return self

    def write_json(self):
        dic = {}
        if self.frames is not None:
            dic.update(self._child_list_attr_write_json("animation", self.frames))
        return dic

class TiledFrame(BaseObject):
    """ Represents a Frame 
    <frame>
    """
    def __init__(self, tiledmap, parent):
        tileid = None
        duration = None
        super(TiledFrame, self).__init__(tiledmap, parent)

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["tileid", "duration"]
        return super(TiledFrame, self).write_xml(outattrorder)


class TiledLayer(BaseObject):
    """ Represents a layer 
    <layer>

    All <tileset> tags shall occur before the first <layer> tag
    so that parsers may rely on having the tilesets 
    before needing to resolve tiles.

    Can contain: properties, data
    """
    def __init__(self, tiledmap, parent):
        self.name = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.opacity = None
        self.visible = None
        self.offsetx = None
        self.offsety = None
        super(TiledLayer, self).__init__(tiledmap, parent)
        self.properties = None
        self.data = None

    def read_xml(self, node):
        super(TiledLayer, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.data = self._child_attr_read_xml(node, TiledData, self)
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["name", "x", "y", "width",
                            "height", "opacity", "visible", "offsetx",
                            "offsety", "properties", "data"]
        return super(TiledLayer, self).write_xml(outattrorder)

    def write_json(self):
        dic = super(TiledLayer, self).write_json()
        dic["type"] = "tilelayer"
        if self.visible is None:
            dic["visible"] = True
        else:
            dic["visible"] = convert_to_bool(self.visible)
        if self.name is None: dic["name"] = ""
        if self.x is None: dic["x"] = 0
        if self.y is None: dic["y"] = 0
        if self.width is None: dic["width"] = 0
        if self.height is None: dic["height"] = 0
        if self.opacity is None: dic["opacity"] = 1
        return dic

class TiledData(BaseObject):
    """ Represents a data 
    <data>

    encoding: 
            The encoding used to encode the tile layer data.
            When used, it can be "base64" and "csv" at the moment.
    compression: 
            The compression used to compress the tile layer data. 
            Tiled Qt supports "gzip" and "zlib".

    Can contain: tile
    """
    def __init__(self, tiledmap, parent):
        self.encoding = None
        self.compression = None
        super(TiledData, self).__init__(tiledmap, parent)
        self.__datasrc = None
        self.__one_d_data = None
        self.__two_d_data = None
        self.__tiles = None

    def read_xml(self, node):
        super(TiledData, self).read_xml(node)
        self.__datasrc = node.text
        if self.__datasrc is not None and self.__datasrc.strip():
            self.__one_d_data = self.__data_decode(self.__datasrc, self.encoding, self.compression)
        self.__tiles = self._child_list_attr_read_xml(node, TiledData_Tile, self) 
        if self.__tiles is not None:
            self.__one_d_data = self.__data_decode(self.__tiles, "xml", self.compression)
        self.__two_d_data = self.__one_d_change_two_d(self.__one_d_data)
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["encoding", "compression"]
        element = super(TiledData, self).write_xml(outattrorder)

        if (self._tiledmap.encoding is None and self._tiledmap.compression is None):
            element.text = self.__datasrc
            element = self._child_list_attr_write_xml(element, self.__tiles)
        elif (self._tiledmap.encoding == self.encoding and self._tiledmap.compression == self.compression):
            element.text = self.__datasrc
            element = self._child_list_attr_write_xml(element, self.__tiles)
        else:
            encoding = self._tiledmap.encoding
            if encoding is None:
                encoding = self.encoding
            else:
                element.set("encoding", encoding)
            compression = self._tiledmap.compression
            if compression is None:
                compression = self.compression
            else:
                element.set("compression", compression)
            element = self.__data_encode_xml(self.__one_d_data, element, encoding, compression)
        return element

    def write_json(self):
        if (self._tiledmap.encoding is None and self._tiledmap.compression is None) or (self._tiledmap.encoding == self.encoding and self._tiledmap.compression == self.compression):
            dic = {}
            if self.__datasrc is not None and self.__datasrc.strip():
                if self.encoding is None:
                    dic["data"] = self.__one_d_data
                elif self.encoding == "csv":
                    del dic["encoding"]
                    dic["data"] = self.__one_d_data
                else:
                    dic = super(TiledData, self).write_json();
                    dic["data"] = self.__datasrc.strip()
            if self.__tiles is not None:
                dic["data"] = self.__one_d_data
            return dic
        else:
            encoding = self._tiledmap.encoding
            if encoding is None:
                encoding = self.encoding
            compression = self._tiledmap.compression
            if compression is None:
                compression = self.compression
            return self.__data_encode_json(self.__one_d_data, encoding, compression)

    def datasrc(self):
        """ The original data

        Read data from the XML
        It may be encrypted
        """
        return self.__datasrc

    def one_d_data(self):
        """ data

        format datasrc to one d data
        May be datasrc = data; or encrypted datasrc to one d data
        """
        return self.__one_d_data

    def two_d_data(self):
        """ data

        format datasrc to two d data
        May be datasrc = data; or encrypted datasrc to two d data
        """
        return self.__two_d_data

    def get_tiledtile_position(self, x, y):
        """ get tiledtile position
        rtype : TiledTile instance
        """
        gid = self.__two_d_data[y, x]
        return self._tiledmap.get_tiledtile_by_gid(gid)

    def __one_d_change_two_d(self, data):
        init = lambda: [0] * self._parent.width
        result = tuple(array.array('H', init()) for i in range(self._parent.height))
        for (y, x) in product(range(self._parent.height), range(self._parent.width)):
            result[y][x] = data[y * self._parent.width + x]
        return result

    def __data_decode(self, data, encoding = None, compression = None):
        """ data decode

        param data : Tile instance list or string
        param encoding : None or "xml" or "csv" or "base64"
        param compression : None or "gzip" or "zlib"

        rtype : one_d list
        """
        if encoding is None or encoding == "xml":
            data = [int(i.gid) for i in data]
        elif encoding == "csv":
            data = [int(i) for i in self.__datasrc.strip().split(",")]
        elif encoding == "base64":
            data = base64.b64decode(data.strip().encode("latin1"))
            if compression == "gzip":
                # data = gzip.decompress(data)
                with gzip.GzipFile(fileobj=six.BytesIO(data)) as f:
                    data = f.read()
            elif compression == "zlib":
                data = zlib.decompress(data)
            elif compression:
                e = 'Compression type "{}" not supported.'.format(compression)
                raise ValueError(e)

            if six.PY2:
                ndata = [ord(c) for c in data]
            else:
                ndata = [i for i in data]

            data = []
            for i in six.moves.range(0, len(ndata), 4):
                n = (ndata[i]  + ndata[i + 1] * (2 ** 8) +
                 ndata[i + 2] * (2 ** 16) + ndata[i + 3] * (2 ** 24))
                data.append(n)
        else:
            e = 'Encoding type "{}" not supported.'.format(encoding)
            raise ValueError(e)
        return data

    def __data_encode_xml(self, data, element, encoding = None, compression = None):
        """ data encode

        param data : 1d_data
        param encoding : "xml" or "csv" or "base64"
        param compression : None or "gzip" or "zlib"
        rtype: Element instance
        """
        if encoding is None or encoding == "xml":
            element.attrib.clear()
            for item in data:
                childelement = Element("tile")
                childelement.set("gid", ("%s" % item))
                element.append(childelement)
        elif encoding == "csv":
            element.attrib.clear()
            element.set("encoding", encoding)
            context = "\n".join([",".join([
                                            str(data[y * self._parent.width + x]) for x in range(self._parent.width)
                                          ])
                                 for y in range(self._parent.height)
                               ])
            element.text = "\n" + context + "\n"
        elif encoding == "base64":
            ndata = []
            for i in data:
                n = [i % (2 ** 8), i // (2 ** 8), i // (2 ** 16), i // ( 2 ** 24)]
                ndata.extend(n)

            if six.PY2:
                data = b''.join([chr(i) for i in ndata])
            else:
                data = b''.join([bytes((i,)) for i in ndata])

            if compression == "gzip":
                bytes_io = six.BytesIO()
                with gzip.GzipFile(fileobj=bytes_io, mode = 'wb') as f:
                    f.write(data)
                    f.close()
                data = bytes_io.getvalue()
            elif compression == "zlib":
                data = zlib.compress(data)
            elif compression:
                e = 'Compression type "{}" not supported.'.format(compression)
                raise ValueError(e)
            element.text = "\n      " + base64.b64encode(data).decode("latin1") + "\n    "
        else:
            e = 'Encoding type "{}" not supported.'.format(encoding)
            raise ValueError(e)
        return element

    def __data_encode_json(self, data, encoding = None, compression = None):
        """ data encode

        param data : 1d_data
        param encoding : "xml" or "csv" or "base64"
        param compression : None or "gzip" or "zlib"
        rtype : dict
        """
        dict = {}
        if encoding is None or encoding == "xml":
            dict["data"] = data
        elif encoding == "csv":
            dict["data"] = data
        elif encoding == "base64":
            dict["encoding"] = "base64"
            if compression is not None:
                dict["compression"] = compression
            ndata = []
            for i in data:
                n = [i % (2 ** 8), i // (2 ** 8), i // (2 ** 16), i // ( 2 ** 24)]
                ndata.extend(n)

            if six.PY2:
                data = b''.join([chr(i) for i in ndata])
            else:
                data = b''.join([bytes((i,)) for i in ndata])

            if compression == "gzip":
                bytes_io = six.BytesIO()
                with gzip.GzipFile(fileobj=bytes_io, mode = 'wb') as f:
                    f.write(data)
                    f.close()
                data = bytes_io.getvalue()
            elif compression == "zlib":
                data = zlib.compress(data)
            elif compression:
                e = 'Compression type "{}" not supported.'.format(compression)
                raise ValueError(e)
            dict["data"] = base64.b64encode(data).decode("latin1")
        else:
            e = 'Encoding type "{}" not supported.'.format(encoding)
            raise ValueError(e)
        return dict

class TiledData_Tile(BaseObject):
    """ Represents a Tile 
    <data><tile gid="0" /> ... </data>
    """
    def __init__(self, tiledmap = None, parent = None):
        self.gid = None
        super(TiledData_Tile, self).__init__(tiledmap, parent)

class TiledImagelayer(BaseObject):
    """ Represents a Imagelayer 
    <imagelayer>

    A layer consisting of a single image.

    Can contain: properties, image
    """
    
    def __init__(self, tiledmap, parent):
        self.name = None
        self.offsetx = None
        self.offsety = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.opacity = None
        self.visible = None
        super(TiledImagelayer, self).__init__(tiledmap, parent)

        self.properties = None
        self.image = None

    def read_xml(self, node):
        super(TiledImagelayer, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.image = self._child_attr_read_xml(node, TiledImage, self)
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["name", "visible", "offsetx", "offsety",
                            "x", "y", "width", "height",
                            "opacity", "image", "properties"]
        return super(TiledImagelayer, self).write_xml(outattrorder)

    def write_json(self):
        dic = super(TiledImagelayer, self).write_json()
        dic["type"] = "imagelayer"
        if self.visible is None:
            dic["visible"] = True
        else:
            dic["visible"] = convert_to_bool(self.visible)
        if self.name is None: dic["name"] = ""
        if self.x is None: dic["x"] = 0
        if self.y is None: dic["y"] = 0
        if self.width is None: dic["width"] = 0
        if self.height is None: dic["height"] = 0
        if self.opacity is None: dic["opacity"] = 1
        return dic

    def image(self):
        """ image info
        <image>
        rtype : TiledImage instance
        """
        return self.__image


class TiledObjectgroup(BaseObject):
    """ Represents a Objectgroup 
    <objectgroup>

    The object group is in fact a map layer,
    and is hence called "object layer" in Tiled Qt.

    Can contain: properties, object
    """
    def __init__(self, tiledmap, parent):
        self.name = None
        self.color = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.opacity = None
        self.visible = None
        self.offsetx = None
        self.offsety = None
        self.draworder = None
        super(TiledObjectgroup, self).__init__(tiledmap, parent)
        self.properties = None
        self.objects = None

    def read_xml(self, node):
        super(TiledObjectgroup, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.objects = self._child_list_attr_read_xml(node, TiledObject, self)
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["name", "color", "x", "y",
                            "width", "height", "opacity", "visible",
                            "offsetx", "offsety", "draworder", "properties",
                            "objects"]
        return super(TiledObjectgroup, self).write_xml(outattrorder)

    def write_json(self):
        dic = super(TiledObjectgroup, self).write_json()
        dic["type"] = "objectgroup"
        if self.visible is None:
            dic["visible"] = True
        else:
            dic["visible"] = convert_to_bool(self.visible)
        if self.name is None: dic["name"] = ""
        if self.x is None: dic["x"] = 0
        if self.y is None: dic["y"] = 0
        if self.width is None: dic["width"] = 0
        if self.height is None: dic["height"] = 0
        if self.opacity is None: dic["opacity"] = 1
        if self.draworder is None: dic["draworder"] = "topdown"
        return dic

class TiledObject(BaseObject):
    """ Represents a Object
    <object>

    When the object has a gid set, 
    then it is represented by the image of the tile with that global ID. 
    The image alignment currently depends on the map orientation. 
    In orthogonal orientation it's aligned to the bottom-left while
    in isometric it's aligned to the bottom-center.

    Can contain: properties,
                 ellipse (since 0.9), 
                 polygon, 
                 polyline, 
                 (Notice: 
                    image is in tile, not appear In other places.
                    so only this kind of situation.)
                 image
    """
    def __init__(self, tiledmap, parent):
        self.id = None
        self.name = None
        self.type = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.rotation = None
        self.gid = None
        self.visible = None
        super(TiledObject, self).__init__(tiledmap, parent)
        
        self.properties = None
        self.ellipse = None
        self.polygon = None
        self.polyline = None
        self.__tile = None
        self.__objecttype = TiledObjectType.NONE

    def read_xml(self, node):
        super(TiledObject, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.ellipse = self._child_attr_read_xml(node, TiledEllipse, self)
        self.polygon = self._child_attr_read_xml(node, TiledPolygon, self)
        self.polyline = self._child_attr_read_xml(node, TiledPolyline, self)
        if self.ellipse is not None:
            self.__objecttype = TiledObjectType.ELLIPSE
        elif self.polygon is not None:
            self.__objecttype = TiledObjectType.POLYGON
        elif self.polyline is not None:
            self.__objecttype = TiledObjectType.POLYLINE
        elif self.gid is not None:
            tiledtile = self._tiledmap.get_tiledtile_by_gid(self.gid)
            if tiledtile is not None:
                self.__tile = tiledtile
                self.__objecttype = TiledObjectType.TILE
        else:
            self.__objecttype = TiledObjectType.RECTANGLE
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["id", "gid", "name", "type",
                            "x","y", "width", "height",
                            "rotation", "visible", "properties",
                            "ellipse", "polygon", "polyline"]
        return super(TiledObject, self).write_xml(outattrorder)

    def write_json(self):
        dic = super(TiledObject, self).write_json()
        if self.visible is None:
            dic["visible"] = True
        else:
            dic["visible"] = convert_to_bool(self.visible)
        if self.name is None: dic["name"] = ""
        if self.type is None: dic["type"] = ""
        if self.x is None: dic["x"] = 0
        if self.y is None: dic["y"] = 0
        if self.width is None: dic["width"] = 0
        if self.height is None: dic["height"] = 0
        if self.rotation is None: dic["rotation"] = 0
        return dic

    def objecttype(self):
        """ object type

        rtype : TiledObjectType
        """
        return self.__objecttype

    def tile(self):
        """ tile info
        rtype : None or TiledTile instance
        """
        return self.__tile

class TiledEllipse(BaseObject):
    """ Represents a Ellipse Object
    <ellipse>

    Used to mark an object as an ellipse. 
    The existing x, y, width and height attributes 
    are used to determine the size of the ellipse.
    """
    def __init__(self, tiledmap = None, parent = None):
        self.properties = None

    def read_xml(self, node):
        super(TiledEllipse, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        return self

    def write_json(self):
        dic = {"ellipse" : True}
        superdic = super(TiledEllipse, self).write_json()
        if superdic:
            dic.update(superdic)
        return dic

class TiledPolygon(BaseObject):
    """ Represents a Polygon Object
    <polygon>

    Each polygon object is made up of a space-delimited
    list of x,y coordinates. The origin for these 
    coordinates is the location of the parent object. 
    By default, the first point is created as 0,0 denoting
    that the point will originate exactly where the object
    is placed.
    """
    def __init__(self, tiledmap, parent):
        self.points = None
        super(TiledPolygon, self).__init__(tiledmap, parent)
        self.properties = None

        self.__positions = None
        self.__width = 0.0
        self.__height = 0.0

    def read_xml(self, node):
        super(TiledPolygon, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__positions = read_positions(self.points)
        self.__recalculate()
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["properties", "points"]
        return super(TiledPolygon, self).write_xml(outattrorder)

    def write_json(self):
        dic = {}
        ls = []
        for position in self.__positions:
            ls.append({"x":position[0], "y":position[1]})
        if ls:
            dic["polygon"] = ls
        superdic = super(TiledPolygon, self).write_json()
        if superdic:
            del superdic["points"]
            dic.update(superdic)
        return dic

    @property
    def positions(self):
        return self.__positions

    @positions.setter
    def positions(self, value):
        self.__positions = value
        self.points = write_positions(self.__positions)
        self.__recalculate()

    def width(self):
        return self.__width

    def height(self):
        return self.__height

    def __recalculate(self):
        if self.__positions is not None:
            x1 = x2 = y1 = y2 = 0
            for x, y in self.__positions:
                if x < x1 : x1 = x
                if x > x2 : x2 = x
                if y < y1 : y1 = y
                if y > y2 : y2 = y
            self.__width = abs(x1 - x2)
            self.__height = abs(y1 - y2)

class TiledPolyline(BaseObject):
    """ Represents a Polyline Object
    <polyline>

    A polyline follows the same placement
    definition as a polyline object.
    """
    def __init__(self, tiledmap, parent):
        self.points = None
        super(TiledPolyline, self).__init__(tiledmap, parent)
        self.properties = None
        self.__positions = None
        self.__width = 0.0
        self.__height = 0.0

    def read_xml(self, node):
        super(TiledPolyline, self).read_xml(node)
        self.properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__positions = read_positions(self.points)
        self.__recalculate()
        return self

    def write_xml(self, outattrorder = None):
        if outattrorder is None:
            outattrorder = ["properties", "points"]
        return super(TiledPolyline, self).write_xml(outattrorder)

    def write_json(self):
        dic = {}
        ls = []
        for position in self.__positions:
            ls.append({"x":position[0], "y":position[1]})
        if ls:
            dic["polyline"] = ls
        superdic = super(TiledPolyline, self).write_json()
        if superdic:
            del superdic["points"]
            dic.update(superdic)
        return dic

    @property
    def positions(self):
        return self.__positions

    @positions.setter
    def positions(self, value):
        self.__positions = value
        self.points = write_positions(self.__positions)
        self.__recalculate()

    def width(self):
        return self.__width

    def height(self):
        return self.__height

    def __recalculate(self):
        if self.__positions is not None:
            x1 = x2 = y1 = y2 = 0
            for x, y in self.__positions:
                if x < x1 : x1 = x
                if x > x2 : x2 = x
                if y < y1 : y1 = y
                if y > y2 : y2 = y
            self.__width = abs(x1 - x2)
            self.__height = abs(y1 - y2)
