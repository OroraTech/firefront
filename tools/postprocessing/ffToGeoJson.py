import os
import sys
from pyproj import Proj, transform
import numpy as np
import json
from shapely.geometry import Polygon
from osgeo import gdal, ogr
from datetime import timedelta,datetime
#srcDS = gdal.OpenEx('input.kml')
#ds = gdal.VectorTranslate('output.json', srcDS, format='GeoJSON')
from geo2kml import to_timed_kml

class ffData:
    def isPoint(element):
        if len(element) == 2:
            if isinstance(element[0],float) and isinstance(element[1],float) :
                return True
        return False
    
    def __init__(self, finenamein=None,mode="batchWeb",destProj='epsg:4326',baseDate=datetime(2020, 1, 1, 0, 0, 0, 0),wsen=None):
        
        self.fname = finenamein
 
        self.inXYpolygon = []
        self.inLLpolygon = []
        
        if mode == "batchWeb" :
            simpleFname = finenamein.split("/")[-1]
            self.frontCount=int(simpleFname.split("-")[0])
            frontProj=int(simpleFname[simpleFname.find("Z")+2:simpleFname.find(".ff")].split("-")[1])
            epsgstring=('epsg:%d')%frontProj
            self.mode = "batchWeb"
            self.projSRC=Proj(epsgstring)
            self.projDest=Proj(destProj) 
            self.area=0
            laDate=simpleFname[simpleFname.find("-")+1:simpleFname.find("Z")].split("T")
             
            self.frontDate = "%s %s UTC"%(laDate[0],laDate[1].replace('-', ':'))
     
        if mode == "mnhPGD" :
            
            self.frontCount=1
            self.projSRC=None
            self.projDest=None
            self.wsen = wsen
            self.lbrt = None
            self.area=0
            localDate = baseDate + timedelta(seconds=int(finenamein.split(".")[-1]))
            self.mode="mnhPGD"
            self.frontDate = localDate.isoformat()
            

            
          

            
        self.parse()
            

    def lalo2xy(self,lalo):
        if self.projSRC is None or self.projDest is None:
            wsen = self.wsen
            lbrt = self.lbrt
            if wsen is None or lbrt is None:
                return lalo
            x = lbrt[0]+((lalo[1] - wsen[0])/(wsen[2] - wsen[0]))*(lbrt[2]-lbrt[0])
            y = lbrt[1]+((lalo[0] - wsen[1])/(wsen[3] - wsen[1]))*(lbrt[3]-lbrt[1])
            return (x,y)
        return transform(self.projDest,self.projSRC,point[0],point[1])
    
    def xy2lalo(self,xy):
        if self.projSRC is None or self.projDest is None:
            wsen = self.wsen
            lbrt = self.lbrt
            if wsen is None or lbrt is None:
                return xy
            lo = wsen[0]+(float(xy[0] - lbrt[0])/float(lbrt[2] - lbrt[0]))*(wsen[2]-wsen[0])
            la = wsen[1]+(float(xy[1] - lbrt[1])/float(lbrt[3] - lbrt[1]))*(wsen[3]-wsen[1])
            
            return (la,lo)       
        return transform(self.projSRC,self.projDest,point[0],point[1])
           
    
    def getLLPolygon(self, ):
        if len(self.inXYpolygon) > len(self.inLLpolygon):
            for front in self.inXYpolygon:
                fa = []
                for element in front:
                    if ffData.isPoint(element):
                        fa.append(self.xy2lalo(element))
                    else:
                        fb = [] 
                        for el2 in element:
                            if ffData.isPoint(el2):
                                fb.append(self.xy2lalo(el2))
                            else:
                                print("WARNING SUB-SUB-SUB front not parsed")
                        fa.append(fb)
                self.inLLpolygon.append(fa)
                    
        return self.inLLpolygon
    
    def getCartesianPolygon(self, ):
        
        return self.inXYpolygon
    
    def toKML(self, ):
        return to_kml(self.toGeoJson())
 
    
    def toVTK(self, ):
        return 0
    
    def toGeoJson(self, ):
        llPoly = self.getLLPolygon()
        
        geoJSonStyleData = []
        
        for front in llPoly:
            mainfront = []
            otherfronts = []
            for element in front:
                if ffData.isPoint(element): 
                    mainfront.append((element[1],element[0]))
                else:
                    otherfronts.append(element)
 
            geoJSonStyleData.append(mainfront[::-1])
            
            for nfront in otherfronts:
                holesFronts  = []
                for element in nfront:
                    if ffData.isPoint(element): 
                        holesFronts.append((element[1],element[0]))
                    else:
                        print("Error Json Parsing fronts, too many holes in holes") 
                geoJSonStyleData.append(holesFronts[::-1])
                
   
   
        geometryInfo={}   
        geometryInfo["numberOfPolygons"]=  len(geoJSonStyleData)
 
 
            
        self.area = self.metadata["totalArea"]
        data = {
        "type": "FeatureCollection",
        "date": self.frontDate, 
        "details":self.metadata ,
        "features": [
        { "type": "Feature", "properties": { "numberOfPolygons": len(geoJSonStyleData) }, 

        "geometry": { "type": "MultiPolygon", "coordinates": [geoJSonStyleData]
        } 
        }
        ]
        }
        return data
        return 0
    
    def toFFPrint(self, ):
        return 0        
       
    def parse(self, ):            

        
        def getLocationFromLine(line,pattern="loc=("):
          
            llv = line.split(pattern)
            if len(llv) < 2: 
                return None
            llr = llv[1].split(",");
            if len(llr) < 3: 
                return None
            return (float(llr[0]),float(llr[1]))
        
        def getMarkPropFromLine(line):
      
            Mpos = getLocationFromLine(line,pattern="loc=(")
           # Mvel = (1,1)#getLocationFromLine(line,pattern="vel=(")
         #   print("here ", Mvel)
            return Mpos#, Mvel #+ Mvel
    
        def printToPolygons(linePrinted, level=1):
            if level > 8:
                 return 

            fronts = linePrinted.split("\n%sFireFront"%('\t'*level))

            pointsMap = []
            if len(fronts)>0:
                nodes = fronts[0].split("FireNode")
                if len(nodes) > 1:
                    for node in nodes[1:]:
                        #ptl, sptl = getMarkPropFromLine(node)
                        pointsMap.append(getMarkPropFromLine(node))
                    #ptl, sptl =  
                    pointsMap.append(getMarkPropFromLine(nodes[1]))

                for subline in fronts[1:]:
                    pointsMap.append(printToPolygons(subline,level+1))

            return pointsMap
        
        self.inXYpolygon = []
        f = open(self.fname, 'r')
        rawdata = f.read()
        firstLine = rawdata.partition('\n')[0]
        print(firstLine)
        llv = firstLine.split("sw=(")
        llr = llv[1].split("ne=(");
        self.lbrt = [  float( llr[0].split(",")[0]), float(llr[0].split(",")[1]), float(llr[1].split(",")[0]), float(llr[1].split(",")[1]) ]
        
        self.inXYpolygon = printToPolygons(rawdata)
        
        f.close()
        
        metaHelper = []
        for front in self.inXYpolygon :
            mainfront = []
            otherfronts = []
            for element in front:
                if ffData.isPoint(element): 
                    mainfront.append(element)
                else:
                    otherfronts.append(element)
 
            metaHelper.append(mainfront[::-1])
            for element in otherfronts:
                metaHelper.append(element[::-1])
                            
        self.metadata = {}   
        self.metadata["numberOfPolygons"]=  len(metaHelper)
        totalArea = 0
        totalLength = 0
        
        for na,a in enumerate(metaHelper):
            pgon = Polygon(a)
            self.metadata["P%d"%na]={"area":pgon.area,"perimeter":pgon.length, "directWinding":pgon.exterior.is_ccw}
            totalLength = totalLength+pgon.length
            totalArea = totalArea+pgon.area
        
        self.metadata["totalLength"]=  totalLength
        self.metadata["totalArea"]=  totalArea

         
 
def areaBurnt():    
    contours1  = glob.glob('/Users/filippi_j/data/2022/pedrogao/OutputsFullCoupled/output.0.*')
    contours2  = glob.glob('/Users/filippi_j/data/2022/pedrogao/OutputsNoCoupled/output.0.*')
    

        
    for contour in contours1:
        ffGSon= ffToGeoJson(contour,mode = "mnhPGD", baseDate=baseDate)
        d = ffGSon.parse()
        area = d["details"]["P0"]["area"] 
        date = datetime.fromisoformat(d["date"])
        v = [date , area]
        lCnt.append( v )
    
        
    
    dfc = pd.DataFrame(lCnt, columns=['date','HaCoupled'])
    dfc["HaCoupled"] = dfc["HaCoupled"]/10000
    
    dfc = dfc.set_index("date")
    dfc.sort_values(by=['date'], inplace=True)
    
    lCnt = []
    for contour in contours2:
        ffGSon= ffToGeoJson(contour,mode = "mnhPGD",baseDate=baseDate)
        d = ffGSon.parse()
        area = d["area"] 
        date = datetime.fromisoformat(d["date"])
        v = [date , area]
        lCnt.append( v )
            
    
    dnc = pd.DataFrame(lCnt, columns=['date','HaNoCoupled'])
    dnc["HaNoCoupled"] = dnc["HaNoCoupled"]/10000
    
    dnc = dnc.set_index("date")
    dnc.sort_values(by=['date'], inplace=True)
    
     
    
     
    totalBurnArea = np.count_nonzero(dBmap.arrival_time_of_front > 000000)
    mSize = (dBmap.domain.Lx/dBmap.arrival_time_of_front.shape[0]) * (dBmap.domain.Ly/dBmap.arrival_time_of_front.shape[1])
    lCnt = []
    for lDate in dnc.index:
        yetBurnt =( totalBurnArea - np.count_nonzero(dBmap.arrival_time_of_front > (lDate-baseDate).seconds))*mSize
        lCnt.append( [lDate, yetBurnt ])
     
    
    doc = pd.DataFrame(lCnt, columns=['date','HaObserved'])
    doc["HaObserved"] = doc["HaObserved"]/10000
    
    doc = doc.set_index("date")
    doc.sort_values(by=['date'], inplace=True)
    
    dac = pd.concat([dfc,dnc,doc], join='inner', axis=1)
    dac.plot()       
        
    
import glob
import pandas as pd
import xarray as xr

import geojson
from fastkml import kml, styles
from shapely.geometry import shape
from datetime import datetime

def geojson_to_placemark(geojson_obj, timestamp):
    # Convertir la géométrie GeoJSON en géométrie Shapely
    geom = shape(geojson_obj['geometry'])

    # Créer un Placemark KML
    pm = kml.Placemark()
    pm.geometry = geom
    pm.timestamp = timestamp

    # Créer et définir le style (contour orange de 2 points, pas de remplissage)
    style = styles.Style()
    style.linestyle.color = styles.Color.rgb(255, 165, 0)  # Orange
    style.linestyle.width = 2  # 2 points de large
    style.polystyle.fill = 0  # Pas de remplissage
    pm.style = style

    return pm

def geojsons_to_kml(geojson_objs):
    # Créer un KML
    k = kml.KML()

    # Créer un document pour contenir les Placemarks
    doc = kml.Document()
    k.append(doc)

    # Convertir chaque objet GeoJSON en Placemark et l'ajouter au document
    for gj in geojson_objs:
        timestamp_str = gj['properties']['timestamp']  # Assumer une propriété 'timestamp'
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))  # Convertir la chaîne en datetime
        pm = geojson_to_placemark(gj, timestamp)
        doc.append(pm)

    return k.to_string(prettyprint=True)

def otherJsonToKml():
    # Utilisation :
    geojson_objs = [
        # Vos objets GeoJSON vont ici
    ]
    kml_str = geojsons_to_kml(geojson_objs)
    with open('output.kml', 'w') as f:
        f.write(kml_str)



def bmap2kml(ds, wsen ,fnameKMLOUT='my_kml.kml',fnameKMLPNGOUT='imagePIL.png', method="pil",maxSpeed=0.1):
  
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    import simplekml
    print("computed BMap")
    lon_min,  lat_min, lon_max, lat_max = wsen
    # Créez une figure
   
    minRealVal = float(ds['arrival_time_of_front'].where(ds['arrival_time_of_front'] > 0).min())
    max_val = float(ds['arrival_time_of_front'].max())
    norm_data = (ds['arrival_time_of_front'] -minRealVal)/  (max_val - minRealVal)
    norm_data = norm_data.values
    norm_data[norm_data < 0] =  np.nan
    gradient_y, gradient_x = np.gradient(norm_data, 10)
    speed = np.sqrt(gradient_x**2 + gradient_y**2) 
    
    minOverallSpeed = np.nanmin(speed)
    maxOverallSpeed = np.nanmax(speed) 
    norm_speed = (speed -minOverallSpeed)/  (maxOverallSpeed - minOverallSpeed)
    
    print("max speed ",np.nanmax(speed))
    # Créez une colormap
    cmap = plt.get_cmap('jet') 
    
    # Créez une nouvelle colormap avec des valeurs transparentes en dessous du seuil
    # 'viridis' a des valeurs entre 0 et 1, donc nous mettons le seuil relativement à ça
    
    cmaplist = [cmap(i) for i in range(cmap.N)]

        
    for i in range(200):
        cmaplist[i] = (*cmaplist[i][:3], i/200.0)  # change l'opacité à 0   
    cmap = colors.LinearSegmentedColormap.from_list('Custom cmap', cmaplist, cmap.N)
 
    from PIL import Image, ImageOps
    print("using PIL")
    
    # Mappez les données normalisées à la colormap pour obtenir une image RGB
    rgba_image = cmap(1-norm_speed)
    plt.imshow(rgba_image, cmap='jet',origin='lower'); plt.colorbar(); plt.show()
    
    # Convertir en une image PIL pour un contrôle plus précis
    pil_image = Image.fromarray((rgba_image * 255).astype(np.uint8))
    
    # Pour assurer la transparence, nous devons convertir l'image en mode "RGBA"
    pil_image = pil_image.convert("RGBA")
    pil_image = ImageOps.flip(pil_image)
    
    # Sauvegardez l'image en PNG
    pil_image.save(fnameKMLPNGOUT)

        
        
       
 
    # Supposons que 'lon_min', 'lat_min', 'lon_max', et 'lat_max' sont les coordonnées des coins de votre DataSet

    
 
    kml = simplekml.Kml()

    ground = kml.newgroundoverlay(name='GroundOverlay') 
    ground.icon.href = fnameKMLPNGOUT  # Utilisez le fichier PNG enregistré
    ground.latlonbox.north = lat_max
    ground.latlonbox.south = lat_min
    ground.latlonbox.east = lon_max
    ground.latlonbox.west = lon_min
 
    
    # Sauvegardez le kml
    kml.save(fnameKMLOUT)





#pedrogao 
BMAPFILE = "/Users/filippi_j/data/2022/pedrogao/REF_REPORT_BMAP.nc"
PGDFILE = "/Users/filippi_j/data/2022/pedrogao/PGD_D80mA.nested.nc"
FFINPUTPATTERN='/Users/filippi_j/data/2022/pedrogao/OutputsNoCoupled/output.0.*'

#prunelli
BMAPFILE = "//Users/filippi_j/Volumes/fcouto/KTEST_PEDROGAO/nested3FirePattern/006_runff/ForeFire/Outputs_coupled_brise_couvent/ForeFire.0.nc"
PGDFILE = "/Users/filippi_j/Volumes/fcouto/KTEST_PEDROGAO/nested3FirePattern/006_runff/PGD_D80mA.nested.nc"
FFINPUTPATTERN='/Users/filippi_j/Volumes/fcouto/KTEST_PEDROGAO/nested3FirePattern/006_runff/ForeFire/Outputs_coupled_brise_couvent//output.0.*'

#prunelli local
BMAPFILE = "/Users/filippi_j/data/2023/prunelli/frontData/coupled.nc"
PGDFILE = "/Users/filippi_j/data/2023/prunelli/PGD_D80mA.nc"
FFINPUTPATTERN= "/Users/filippi_j/data/2023/prunelli/frontData/cpl/output.0.*"

#Pigna
BMAPFILE = "//Users/filippi_j/Volumes/orsu/firecaster/2023/nest150Ref/006_runff/ForeFire/Outputs/ForeFire.0.nc"
PGDFILE = "/Users/filippi_j/Volumes/orsu/firecaster/2023/nest150Ref/001_pgd/PGD_D80mA.nested.nc"
FFINPUTPATTERN='/Users/filippi_j/Volumes/orsu/firecaster/2023/nest150Ref/006_runff/ForeFire/Outputs/output.0.*'



    
dBmap = xr.open_dataset(BMAPFILE)
baseDate= datetime(int(dBmap.domain.refYear), 1, 1, 0, 0, 0, 0)
baseDate= baseDate+timedelta(days=int(dBmap.domain.refDay))

pgd = xr.open_dataset(PGDFILE)

lon0 = float(pgd["longitude"][0,0])
lon1 = float(pgd["longitude"][0,1])
lonM1 = float(pgd["longitude"][0,-1])
lonM2 = float(pgd["longitude"][0,-2])


wsen = [
    float(lon0+(lon1-lon0)/2),
    float(pgd.latitude.min()),
    float(lonM1+(lonM2-lonM1)/2),
    float(pgd.latitude.max())
             ]



 

contours1  = glob.glob(FFINPUTPATTERN)

lCnt=[]
import os
selectionSorted =  sorted(contours1)#[::6]

for contour in selectionSorted[::30]:#[50:261]:
    
#    strcp="cp %s %s"%(contour,"/Users/filippi_j/data/2023/prunelli/frontData/cpl")
#    print(strcp)
#    os.system(strcp)
   # print(contour)
    f = ffData(contour,mode = "mnhPGD", baseDate=baseDate,wsen=wsen)
    lCnt.append((f.toGeoJson(),f.frontDate))


with open("/Users/filippi_j/data/2023/corbara20230727/OutputsNonCoupled.kml", "w") as text_file:
    text_file.write(to_timed_kml(lCnt))

fnameKMLOUT="/Users/filippi_j/data/2023/corbara20230727/speedNC.kml"
fnameKMLPNGOUT="/Users/filippi_j/data/2023/corbara20230727/speedNC.png"
bmap2kml(dBmap,wsen,fnameKMLOUT=fnameKMLOUT,fnameKMLPNGOUT=fnameKMLPNGOUT)


#print(json.dumps(ffGSon.parse()))
