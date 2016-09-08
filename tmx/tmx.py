# coding:utf-8

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
from itertools import chain, product
from collections import defaultdict, namedtuple
from xml.etree.ElementTree import *
from six.moves import zip, map
from operator import attrgetter

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
    "version": None,
    "orientation": None,
    "renderorder": None,
    "width": None,
    "height": None,
    "tilewidth": None,
    "tileheight": None,
    "hexsidelength": None,
    "staggeraxis": None,
    "staggerindex": None,
    "backgroundcolor": None,
    "nextobjectid": None,
    "firstgid": None,
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
    "draworder": "topdown",
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
        return tuple(tuple(map(float, i.split(','))) for i in text.split())
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

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        print name
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

    def read_xml(self, node):
        """read the xml attributes to self

        :param node: etree element
        :rtype : BaseObject instance
        """
        classname = self.__class__.__name__
        classnodename = get_class_node_name(classname)
        if classnodename != node.tag:
            logger.error("classnodename != node.tag. classnodename:%s, node.tag:%s", classnodename, node.tag)
            raise Exception
        for key, value in node.items():
                casted_value = types[key](value)
                setattr(self, key, casted_value)
        return self

    def write_xml(self):
        """write the attributes to xml

        :rtype : Element instance
        """
        classname = self.__class__.__name__
        element = Element(get_class_node_name(classname))
        for key, value in vars(self).items():
           if key.startswith('_'):
                continue
           if typesdefaultvalue.has_key(key):
               if typesdefaultvalue[key] == value:
                   continue
           element.set(key, ("%s" % value))
        return element

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

class TiledMap(BaseObject):
    """TileMap Data. Contains the layers, objects, images, and others
    <map>
    This class is meant to handle most of the work you need to do to use a map.

    Can contain: properties, tileset, layer, objectgroup, imagelayer
    """

    def __init__(self, filepath):
        self.version = "1.0"
        self.orientation= "orthogonal"
        self.renderorder = ""
        self.width = 0
        self.height = 0
        self.tilewidth = 0
        self.tileheight = 0
        self.hexsidelength = 0
        self.staggeraxis = ""
        self.staggerindex = ""
        self.backgroundcolor = ""
        self.nextobjectid = 0
        super(TiledMap, self).__init__(self, None)

        self.__filepath = filepath
        self.__properties = None
        self.__tilesets = None
        self.__layers = list()

        if filepath:
            elementTree = parse(filepath).getroot()
            self.read_xml(elementTree)

    def read_xml(self, node):
        super(TiledMap, self).read_xml(node)
        
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__tilesets = self._child_list_attr_read_xml(node, TiledTileset, self)
        
        for child in node:
            if child.tag == get_class_node_name(TiledLayer.__name__):
                tiledlayer = TiledLayer(self, self).read_xml(child)
                if tiledlayer is not None:
                   self.__layers.append(tiledlayer)
            if child.tag == get_class_node_name(TiledImagelayer.__name__):
                tiledImagelayer = TiledImagelayer(self, self).read_xml(child)
                if tiledImagelayer is not None:
                    self.__layers.append(tiledImagelayer)
            if child.tag == get_class_node_name(TiledObjectgroup.__name__):
                tiledObjectgroup = TiledObjectgroup(self, self).read_xml(child)
                if tiledObjectgroup is not None:
                    self.__layers.append(tiledObjectgroup)

        return self

    def write_xml(self):
        element = super(TiledMap, self).write_xml()

        element = self._child_attr_write_xml(element, self.__properties)
        element = self._child_list_attr_write_xml(element, self.__tilesets)
        if self.__layers and len(self.__layers):
            for child in self.__layers:
                element = self._child_attr_write_xml(element, child)
        indent(element)
        return element

    def filepath(self):
        """ TileMap file path
        """
        return self.__filepath

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

    def tilesets(self):
        """ all tileset info
        <tileset>
        rtype : list  child is TiledTiledet instance
        """
        return self.__tilesets

    def layers(self):
        """ layers info
        <properties>
        rtype : list  child is 
                            TiledLayer instance
                            or TiledImageLayer
                            or TiledObjectgroup
        """
        return self.__layers

    def get_tiledtile_by_gid(self, gid):
        """ get TiledTile by gid
        rtype : TiledTile instance
        """
        firstgid = endgid = 0
        length = len(self.__tilesets)
        for i in range(length):
            tileset = self.__tilesets[i]
            firstgid = tileset.firstgid
            if i >= length - 1 :
                return tileset.get_tiledtile_by_id(gid - firstgid)
            else:
                endgid = self.__tilesets[i + 1].firstgid
                if firstgid <= gid and endgid > gid:
                    return tileset.get_tiledtile_by_id(gid - firstgid)
        return None

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
    def write_tmx_xml(tiledmap, filepath):
        """Read .tmx file

        :param filepath: string file's path
        :rtype TiledMap instance
        """
        ElementTree(tiledmap.write_xml()).write(filepath, encoding="utf-8", xml_declaration="utf-8", method="xml")
        return True


class TiledTileset(BaseObject):
    """ Represents a Tiledset 
    <tileset>
    External tilesets are supported.  GID/ID's from Tiled are not guaranteed to
    be the same after loaded.

    Can contain: tileoffset (since 0.8), 
                 properties (since 0.8), 
                 terraintypes (since 0.9),
                 tile
                 (Notice: 
                    image is in tile, not appear In other places.
                    so only this kind of situation.)
                 image, 
    """
    def __init__(self, tiledmap, parent):
        self.firstgid = None
        self.source = None
        self.name = None
        self.tilewidth = None
        self.tileheight = None
        self.spacing = None
        self.margin = None
        self.tilecount = None
        self.columns = None
        super(TiledTileset, self).__init__(tiledmap, parent)

        self.__tileoffset = None
        self.__properties = None
        self.__terraintypes = None
        self.__tiles = None

    def read_xml(self, node):
        super(TiledTileset, self).read_xml(node)
        if self.source is not None and self.source[-4:].lower() == ".tsx":
            dirname = os.path.dirname(self._tiledmap.filepath())
            path = os.path.abspath(os.path.join(dirname, self.source))
            path = unicode(path, 'utf-8')
            node = parse(path).getroot()
            super(TiledTileset, self).read_xml(node)

        self.__tileoffset = self._child_attr_read_xml(node, TiledTileoffset, self)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__terraintypes = self._child_attr_read_xml(node, TiledTerraintypes, self)
        self.__tiles = self._child_list_attr_read_xml(node, TiledTile, self)
        return self

    def write_xml(self):
        element = super(TiledTileset, self).write_xml()
        if self.source is not None and self.source[-4:].lower() == ".tsx":
            element.attrib.clear()
            element.set('firstgid', ("%s" % self.firstgid))
            element.set('source', ("%s" % self.source))
        else:
            element = self._child_attr_write_xml(element, self.__tileoffset)
            element = self._child_attr_write_xml(element, self.__properties)
            element = self._child_attr_write_xml(element, self.__terraintypes)
            element = self._child_list_attr_write_xml(element, self.__tiles)
        return element

    def tileoffset(self):
        """ all Property info
        <tileoffset>
        rtype : list   child is TiledTileoffset instance
        """
        return self.__tileoffset

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

    def terraintypes(self):
        """ terraintypes info
        <terraintypes>
        rtype : TiledTerraintypes instance
        """
        return self.__terraintypes

    def tiles(self):
        """ list tile info
        <tile>
        rtype : list  child is TiledTerraintypes instance
        """
        return self.__tiles

    def get_tiledtile_by_id(self, id):
        """ get tiledtile by id

        rtype : TiledTile instance
        """
        if self.__tiles is not None:
            for tile in self.__tiles:
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
        self.x = 0.0
        self.y = 0.0
        super(TiledTileoffset, self).__init__(tiledmap, parent)

class TiledProperties(BaseObject):
    """ Properties
    <properties>

    Can contain: property
    """
    
    def __init__(self, tiledmap, parent):
        super(TiledProperties, self).__init__(tiledmap, parent)
        self.__properties = None

    def read_xml(self, node):
        super(TiledProperties, self).read_xml(node)
        self.__properties = self._child_list_attr_read_xml(node, TiledProperty, self)
        return self

    def write_xml(self):
        element = super(TiledProperties, self).write_xml()
        element = self._child_list_attr_write_xml(element, self.__properties)
        return element

    def properties(self):
        """ all Property info
        <property>
        rtype : list   child is TiledProperty instance
        """
        return self.__properties

class TiledProperty(BaseObject):
    """ Property
    <Property>
    """
    
    def __init__(self, tiledmap, parent):
        self.name = ""
        self.type = ""
        self.value = ""
        super(TiledProperty, self).__init__(tiledmap, parent)

class TiledTerraintypes(BaseObject):
    """ Represents a Terraintypes
    <terraintypes>

    Can contain: terrain
    """
    def __init__(self, tiledmap, parent):
        super(TiledTerraintypes, self).__init__(tiledmap, parent)
        self.__terraintypes = None

    def read_xml(self, node):
        super(TiledTerraintypes, self).read_xml(node)
        self.__terraintypes = self._child_list_attr_read_xml(node, TiledTerrain, self)
        return self

    def write_xml(self):
        element = super(TiledTerraintypes, self).write_xml()
        element = self._child_list_attr_write_xml(element, self.__terraintypes)
        return element

class TiledTerrain(BaseObject):
    """ Represents a Terrain
    <terrain>

    Can contain: properties
    """
    def __init__(self, tiledmap, parent):
        self.name = None
        self.tile = 0
        super(TiledTerrain, self).__init__(tiledmap, parent)
        self.__properties = None

    def read_xml(self, node):
        super(TiledTerrain, self).read_xml(node)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        return self

    def write_xml(self):
        element = super(TiledTerrain, self).write_xml()
        element = self._child_attr_write_xml(element, self.__properties)
        return element

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

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
        self.__properties = None
        self.__image = None
        self.__animation = None

    def read_xml(self, node):
        super(TiledTile, self).read_xml(node)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__image = self._child_attr_read_xml(node, TiledImage, self)
        self.__animation = self._child_attr_read_xml(node, TiledAnimation, self)
        return self

    def write_xml(self):
        element = super(TiledTile, self).write_xml()
        element = self._child_attr_write_xml(element, self.__properties)
        element = self._child_attr_write_xml(element, self.__image)
        element = self._child_attr_write_xml(element, self.__animation)
        return element

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

    def image(self):
        """ image info
        <image>
        rtype : TiledImage instance
        """
        return self.__image

    def animation(self):
        """ animation info
        <animation>
        rtype : TiledAnimation instance
        """
        return self.__animation


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

class TiledAnimation(BaseObject):
    """ Represents a Animation 
    <animation>

    Contains a list of animation frames.

    Can contain: frame
    """
    def __init__(self, tiledmap, parent):
        super(TiledAnimation, self).__init__(tiledmap, parent)
        self.__frames = None

    def read_xml(self, node):
        super(TiledAnimation, self).read_xml(node)
        self.__frames = self._child_list_attr_read_xml(node, TiledFrame, self)
        return self

    def write_xml(self):
        element = super(TiledAnimation, self).write_xml()
        element = self._child_list_attr_write_xml(element, self.__frames)
        return element

    def frames(self):
        """ all frame info
        <frame>
        rtype : list   child is TiledFrame instance
        """
        return self.__frames

class TiledFrame(BaseObject):
    """ Represents a Frame 
    <frame>
    """
    def __init__(self, tiledmap, parent):
        tileid = None
        duration = None
        super(TiledFrame, self).__init__(tiledmap, parent)




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
        self.__properties = None
        self.__data = None

    def read_xml(self, node):
        super(TiledLayer, self).read_xml(node)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__data = self._child_attr_read_xml(node, TiledData, self)
        return self

    def write_xml(self):
        element = super(TiledLayer, self).write_xml()
        element = self._child_attr_write_xml(element, self.__properties)
        element = self._child_attr_write_xml(element, self.__data)
        return element

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

    def data(self):
        """ data info
        <data>
        rtype : TiledData instance
        """
        return self.__data

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
        self.__data = None

    def read_xml(self, node):
        super(TiledData, self).read_xml(node)

        self.__datasrc = node.text
        self.__data = None
        tempdata = None
        next_gid = None
        
        if self.encoding == 'base64':
            from base64 import b64decode
            tempdata = b64decode(self.__datasrc.strip())
        elif self.encoding == 'csv':
            next_gid = map(int, "".join(
                line.strip() for line in self.__datasrc.strip()
            ).split(","))
        elif encodeing:
            msg = 'TMX encoding type: {0} is not supported.'
            logger.error(msg.format(encoding))
            raise Exception

        if self.compression == 'gzip':
            import gzip

            with gzip.GzipFile(fileobj=six.BytesIO(tempdata)) as fh:
                tempdata = fh.read()
        elif self.compression == 'zlib':
            import zlib

            tempdata = zlib.decompress(tempdata)
        elif self.compression:
            msg = 'TMX compression type: {0} is not supported.'
            logger.error(msg.format(compression))
            raise Exception
        
        import struct
        import array

        # if data is None, then it was not decoded or decompressed, so
        # we assume here that it is going to be a bunch of tile elements
        # TODO: this will/should raise an exception if there are no tiles
        if self.encoding == next_gid is None:
            def get_children(parent):
                for child in parent.findall('tile'):
                    yield int(child.get('gid'))

            next_gid = get_children(node)

        elif tempdata:
            if type(tempdata) == bytes:
                fmt = struct.Struct('<L')
                iterator = (tempdata[i:i + 4] for i in range(0, len(tempdata), 4))
                next_gid = (fmt.unpack(i)[0] for i in iterator)
            else:
                msg = 'layer data not in expected format ({})'
                logger.error(msg.format(type(tempdata)))
                raise Exception

        init = lambda: [0] * self._parent.width
        reg = self._tiledmap.get_tiledtile_by_gid
        
        # H (16-bit) may be a limitation for very detailed maps
        self.__data = tuple(array.array('H', init()) for i in range(self._parent.height))
        for (y, x) in product(range(self._parent.height), range(self._parent.width)):
            gid = int("%s" % next(next_gid))
            self.__data[y][x] = gid
        return self

    def write_xml(self):
        element = super(TiledData, self).write_xml()
        element.text = self.__datasrc
        return element

    def datasrc(self):
        """ The original data

        Read data from the XML
        It may be encrypted
        """
        return self.__datasrc

    def data(self):
        """ data

        format datasrc to data
        May be datasrc = data; or encrypted datasrc to data
        """
        return self.__data

    def get_tiledtile_position(self, x, y):
        """ get tiledtile position
        rtype : TiledTile instance
        """
        gid = self.__data[y, x]
        return self._tiledmap.get_tiledtile_by_gid(gid)


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

        self.__properties = None
        self.__image = None

    def read_xml(self, node):
        super(TiledImagelayer, self).read_xml(node)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__image = self._child_attr_read_xml(node, TiledImage, self)
        return self

    def write_xml(self):
        element = super(TiledImagelayer, self).write_xml()
        element = self._child_attr_write_xml(element, self.__properties)
        element = self._child_attr_write_xml(element, self.__image)
        return element

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

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

        self.__objects = None

    def read_xml(self, node):
        super(TiledObjectgroup, self).read_xml(node)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__objects = self._child_list_attr_read_xml(node, TiledObject, self)
        return self

    def write_xml(self):
        element = super(TiledObjectgroup, self).write_xml()
        element = self._child_attr_write_xml(element, self.__properties)
        element = self._child_list_attr_write_xml(element, self.__objects)
        return element

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

    def objects(self):
        """ objects info
        <object>
        rtype : list()  child is TiledObject instance
        """
        return self.__objects

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
        
        self.__ellipse = None
        self.__polygon = None
        self.__polyline = None
        self.__tile = None
        self.__objecttype = TiledObjectType.NONE

    def read_xml(self, node):
        super(TiledObject, self).read_xml(node)
        self.__properties = self._child_attr_read_xml(node, TiledProperties, self)
        self.__ellipse = self._child_attr_read_xml(node, TiledEllipse, self)
        self.__polygon = self._child_attr_read_xml(node, TiledPolygon, self)
        self.__polyline = self._child_attr_read_xml(node, TiledPolyline, self)
        if self.__ellipse is not None:
            self.__objecttype = TiledObjectType.ELLIPSE
        elif self.__polygon is not None:
            self.__objecttype = TiledObjectType.POLYGON
        elif self.__polyline is not None:
            self.__objecttype = TiledObjectType.POLYLINE
        elif self.gid is not None:
            tiledtile = self._tiledmap.get_tiledtile_by_gid(self.gid)
            if tiledtile is not None:
                self.__tile = tiledtile
                self.__objecttype = TiledObjectType.TILE
        else:
            self.__objecttype = TiledObjectType.RECTANGLE
        return self

    def write_xml(self):
        element = super(TiledObject, self).write_xml()
        element = self._child_attr_write_xml(element, self.__properties)
        element = self._child_attr_write_xml(element, self.__ellipse)
        element = self._child_attr_write_xml(element, self.__polygon)
        element = self._child_attr_write_xml(element, self.__polyline)
        return element

    def properties(self):
        """ properties info
        <properties>
        rtype : TiledProperties instance
        """
        return self.__properties

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

    def ellipse(self):
        """ Ellipse info
        <ellipse>
        rtype : None or TiledEllipse instance
        """
        return self.__ellipse

    def polygon(self):
        """ Polygon info
        <polygon>
        rtype : None or TiledPolygon instance
        """
        return self.__polygon

    def polyline(self):
        """ Polyline info
        <polyline>
        rtype : None or TiledPolyline instance
        """
        return self.__polyline

class TiledEllipse(BaseObject):
    """ Represents a Ellipse Object
    <ellipse>

    Used to mark an object as an ellipse. 
    The existing x, y, width and height attributes 
    are used to determine the size of the ellipse.
    """

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
        
        self.__positions = None
        self.__width = 0.0
        self.__height = 0.0

    def read_xml(self, node):
        super(TiledPolygon, self).read_xml(node)
        self.__positions = read_positions(self.points)
        self.__recalculate()
        return self

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
    definition as a polygon object.
    """
    def __init__(self, tiledmap, parent):
        self.points = None
        super(TiledPolyline, self).__init__(tiledmap, parent)
        
        self.__positions = None
        self.__width = 0.0
        self.__height = 0.0

    def read_xml(self, node):
        super(TiledPolyline, self).read_xml(node)
        self.__positions = read_positions(self.points)
        self.__recalculate()
        return self

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
