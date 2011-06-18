import math, random

from panda3d.core import Vec3, Quat, GeomVertexFormat

from panda3d.core import *

from terrain.bakery.bakery import Tile, parseFile, loadTex

import meshManager


class GroundFactory(meshManager.MeshFactory):
    
    def __init__(self,path,heightScale,shader=None):
        self.shader=shader
        meshManager.MeshFactory.__init__(self)
    
        self.dataIndex={}
        
        
        
        self.heightScale=heightScale
        
        d=parseFile(path+'/texList.txt')
        
        self.mapTexStages={}
        self.specialMaps={}
        for m in d['Special']:
            s=m.split('\t')
            self.specialMaps[s[1]]=s[0]
        
        
        # List of non map texture stages, and their sizes
        # (TexStage,Size)
        self.texList=[]
        
        if "Tex2D" in d:
            sort=0;
            for m in d["Tex2D"]:
                sort+=1
                s=m.split()
                name=s[0]
                texStage=TextureStage(name+'stage'+str(sort))
                texStage.setSort(sort)
                source=s[1]
                
#                 def setTexModes(modeText):
#                     combineMode=[]
#                     for t in modeText:
#                         if t[:1]=='M':
#                             texStage.setMode(getRenderMapType(t))
#                         elif t[:1]=='C':
#                             combineMode.append(getCombineMode(t))
#                         elif t=='Save':
#                             texStage.setSavedResult(True)
#                         else:
#                             print "Illegal mode info for "+name
#                     if len(combineMode)>0:
#                         texStage.setCombineRgb(*combineMode)
#                     if len(modeText)==0:
#                         texStage.setMode(TextureStage.MModulate)
                
                if source=='file':
                    
#                     setTexModes(s[3:])
                    tex=loadTex(path+"/textures/"+name)
#                     self.terrainNode.setTexture(texStage,tex)
#                     self.terrainNode.setShaderInput('tex2D_'+name,tex)
                    self.texList.append((texStage,float(s[2]),tex,name))
                    
                elif source=='map':
#                     setTexModes(s[2:])
                    self.mapTexStages[s[0]]=texStage
# 
#                 else:
#                     print 'Invalid source for '+name+' int Tex2D'
        
        
        
        
        
    def regesterGeomRequirements(self,LOD,collection):
        # for now, going to use our own node, so we don't have any special requirements
        requirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3t2()
                )
        
        self.dataIndex[LOD]=collection.add(requirements)
        
    def draw(self,LOD,x0,y0,x1,y1,drawResourcesFactory,tileCenter):
        tile=drawResourcesFactory.getTile()
        resources=drawResourcesFactory.getDrawResources(self.dataIndex[LOD])
        
        # Set up the GeoMipTerrain
        terrain = GeoMipTerrain("TerrainTile")
        heightTex=tile.bakedTile.renderMaps[self.specialMaps["height"]].tex
        heightTexSize=heightTex.getXSize()
        pnmImage=PNMImage()
        # heightTex.makeRamImage () # Makes it run without having ran image in advance, but it all ends up flat.
        heightTex.store(pnmImage)
        terrain.setHeightfield(pnmImage)
        
        
        # Set terrain properties
        terrain.setBruteforce(True)
        # Store the root NodePath for convenience
        root = terrain.getRoot()
        root.setPos(tile.bakedTile.x-tileCenter.getX(),tile.bakedTile.y-tileCenter.getY(),0)
        
        for t in self.texList:
            texScale=1.0/(t[1])
            root.setTexture(t[0],t[2])
            root.setShaderInput('tex2D_'+t[3],t[2])
            root.setTexScale(t[0],texScale*tile.tileScale)
            root.setTexOffset(t[0],(tile.getX() % t[1])*texScale,(tile.getY() % t[1])*texScale)
        
        for t in self.mapTexStages:
            tex=tile.bakedTile.renderMaps[t].tex
            
            
            root.setTexture(self.mapTexStages[t],tex)
            
            # Here we apply a transform to the textures so centers of the edge pixels fall on the edges of the tile
            # Normally the edges of the edge pixels would fall on the edges of the tiles.
            # The benifits of this should be visible, though they have not been varified sucessfully yet.
            # In fact, these transforms appear to not do anything.
            # This is troubling, but the problem they are supposed to fix is currently invisible as well.
            #size=tex.getXSize()
            #margin=bakery.texMargin(size)
            #tile.setTexOffset(t,-margin,-margin)
            #tile.setTexScale(t,float(size+margin*2)/size)
            
        root.setShaderInput("offset",tile.bakedTile.x,tile.bakedTile.y,0.0,0.0)
        root.setShaderInput("scale",tile.bakedTile.scale)
        
        xyScale=float(tile.tileScale)/(heightTexSize-1)
        root.setScale(xyScale,xyScale,self.heightScale)
        if self.shader: root.setShader(self.shader)
        # Generate it.
        terrain.generate()
        
        resources.attachNode(root)
        
        tile.terrain=terrain
        
        def height(x,y):
            t=self
            xDif=x-tile.bakedTile.x
            if xDif>=0 and xDif<=tile.tileScale:
                yDif=y-tile.bakedTile.y
                if yDif>=0 and yDif<=tile.tileScale:
        
                    # found correct tile
                    h=terrain.heightfield()
                    mapSize=h.getXSize()
                    s=(mapSize-1)/tile.tileScale
                    xLoc=min(mapSize,max(0,xDif*s))
                    yLoc=min(mapSize,max(0,yDif*s))
                    
                    return terrain.getElevation(xLoc,yLoc)*self.heightScale

            print "Find height Failed"
            return 0.0

        
        tile.height=height