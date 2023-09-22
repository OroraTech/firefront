#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 17:45:24 2023

@author: filippi_j
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import xarray as xr
import matplotlib.image as mpimg
import os.path
import struct
import laspy 
import geopandas as gpd
from fiona.crs import from_epsg
from shapely.geometry import box
from rasterio import Affine
from pyproj import Transformer
import rasterio
 
from rasterio.warp import reproject, Resampling
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import vtk
from PIL import Image
# Convertir le point SW
import contextily as cx
import json
from rasterio.mask import mask
import pycrs







def filter_las_files_with_attributes(file_paths, left, bottom, right, top):
    all_filtered_points = {'coords': np.array([]).reshape(0, 3), 'intensity': [], 'color': np.array([]).reshape(0, 3)}

    for file_path in file_paths:
        inFile = laspy.read(file_path)

        points = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()
        tr = np.max(points[:,0])
        tl = np.min(points[:,0])
        tt = np.max(points[:,1])
        tb = np.min(points[:,1]) 

        intensity = inFile.intensity
  

        mask = (points[:, 0] >= left) & (points[:, 0] <= right) & (points[:, 1] >= bottom) & (points[:, 1] <= top)
        print("Got ", np.sum(mask)," from file ",file_path )
        filtered_points = points[mask]
        filtered_intensity = intensity[mask]
        

        all_filtered_points['coords'] = np.vstack((all_filtered_points['coords'], filtered_points))
        
        all_filtered_points['intensity'].extend(filtered_intensity)


    all_filtered_points['intensity'] = np.array(all_filtered_points['intensity'])
 
    print("filtered box ", left, bottom, right, top," from files ", file_paths)
    return all_filtered_points

def save_filtered_las(all_filtered_points, output_file_path):
    outFile = laspy.create()
    outFile.x = all_filtered_points['coords'][:, 0]
    outFile.y = all_filtered_points['coords'][:, 1]
    outFile.z = all_filtered_points['coords'][:, 2]
    outFile.intensity = all_filtered_points['intensity']
    outFile.red = all_filtered_points['color'][:, 0]
    outFile.green = all_filtered_points['color'][:, 1]
    outFile.blue = all_filtered_points['color'][:, 2]
    outFile.write(output_file_path)
    print("saved LAS as ", output_file_path)
    
def convert_LASCRS_to_latlon(filtered_points, lidarCRS = 2154):
    # Initialiser le transformateur pour convertir de Lambert-93 (EPSG:2154) à WGS84 (EPSG:4326)
    transformer = Transformer.from_crs(lidarCRS, 4326)
    
    # Extraire les coordonnées x, y, et z
    x_lambert = filtered_points['coords'][:, 0]
    y_lambert = filtered_points['coords'][:, 1]
    z_lambert = filtered_points['coords'][:, 2]
    
    # Effectuer la transformation
    lat, lon = transformer.transform(x_lambert, y_lambert)
    
    # Recréer le dictionnaire des points avec les nouvelles coordonnées
    filtered_points_latlon = {
        'coords': np.vstack((lat, lon, z_lambert)).T,
        'intensity': filtered_points['intensity'],
        'color': filtered_points['color']
    }
    print("Projected points to latlon from CRS ", lidarCRS)
    return filtered_points_latlon    
    

def toImage(red,green,blue, outF):
 
    
    # Convert the normalized bands to 8-bit (0-255)
    red_8bit = (red * 255).astype('uint8')
    green_8bit = (green * 255).astype('uint8')
    blue_8bit = (blue * 255).astype('uint8')
    
    # Create an RGB image
    rgb_array = np.stack((red_8bit, green_8bit, blue_8bit), axis=2)
    rgb_image = Image.fromarray(rgb_array, 'RGB')
    
    # Save the image
    print("saved RVB bands to ", outF)
    rgb_image.save(outF)

def assign_colors_from_tif(filtered_points, tif_path, bands=[1,2,3],scale=[255.0,255.0,255.0]):
    # Lire l'image TIF avec rasterio
    with rasterio.open(tif_path) as src:
 
        transform = src.transform

        inv_transform = ~transform
        
        red  = src.read(bands[0]).astype('float64')/scale[0]
        green  = src.read(bands[1]).astype('float64')/scale[0]
        blue  = src.read(bands[2]).astype('float64')/scale[0]
        
        # Normalisation des valeurs de pixel
    
        toImage(red,green,blue, tif_path+"testIMG.jpg")
        
        # Pour chaque point, trouver la valeur de pixel correspondante dans l'image TIF
        new_colors = []
        for point in filtered_points['coords']:
            # Convertir les coordonnées du point en coordonnées de pixel
            lamx, lamby = point[0], point[1]
            px, py = inv_transform * (lamx, lamby)
            col,row = int(px), int(py)
    
            # Récupérer et normaliser la valeur de pixel
            try:
                # Utiliser les bandes NIR (3), R (0) et V (1) pour créer un point RVB
                vr = (red[row, col]*255.0).astype(np.uint8)
                vv = (green[row, col]*255.0).astype(np.uint8)
                vb = (blue[row, col]*255.0).astype(np.uint8)
                
                new_colors.append([vr,vv,vb])
            except IndexError:
                # Si le point est en dehors des limites de l'image, attribuer une couleur par défaut (par exemple, noir)
                print("error assigning tif color")
                new_colors.append([0, 0, 0])
    
        # Mettre à jour l'attribut de couleur des points
        filtered_points['color'] = np.array(new_colors)
        print("Assigned colors to points using ", tif_path)
        return filtered_points
        


# Ouvrir le fichier TIF source
def reprojectTif(inTif, outTif, destCRS=2154):
    with rasterio.open(inTif) as src:
        transform = src.transform
        crs = src.crs
        array = src.read()
    
        # Définir les métadonnées pour le fichier de destination
        dst_crs = destCRS  # WGS 84
        dst_transform, dst_width, dst_height = rasterio.warp.calculate_default_transform(
            crs, dst_crs, src.width, src.height, *src.bounds
        )
        dst_kwargs = src.meta.copy()
        dst_kwargs.update({
            'crs': dst_crs,
            'transform': dst_transform,
            'width': dst_width,
            'height': dst_height
        })
    
        # Créer le fichier TIF de destination
        with rasterio.open(outTif, 'w', **dst_kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=transform,
                    src_crs=crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )
        print(inTif, " converted to crs ", destCRS, " saved to ", outTif)


def getLeftRightBottomTop(inTif):
    with rasterio.open(inTif) as src:
        
        wsen = src.bounds.left,  src.bounds.right, src.bounds.bottom, src.bounds.top
        print("got bounds of ", inTif, " as ", wsen)
        return wsen

def plot_colored_points_3d(points, dpi=300, filename="3D_colored_points.png", z_scale=1):
    coords = points['coords']
    colors = points['color'] / 255.0  # Assurez-vous que les couleurs sont normalisées entre 0 et 1
    
    fig = plt.figure(dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    
    # Appliquer un facteur d'échelle à l'axe Z pour le rendre moins grand
    ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2] * z_scale, c=colors, s=0.05)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    # Sauvegarder la figure en PNG avec une résolution spécifique (dpi)
    plt.savefig(filename, dpi=dpi)
    print("Plotted points in ", filename)

def save_points_to_vtk(points, filename='points.vtk'):
    # Créer un objet vtkPoints pour stocker les coordonnées
    vtk_points = vtk.vtkPoints()
    tb = np.min(points['coords'][:,1])
    tl = np.min(points['coords'][:,0])
    
    for coord in points['coords']:
        ncoord = coord - [tl,tb,0]
        vtk_points.InsertNextPoint(ncoord)
    
    # Créer un objet vtkCellArray pour stocker la connectivité des points
    vertices = vtk.vtkCellArray()
    vertices.InsertNextCell(len(points['coords']))
    
    for i in range(len(points['coords'])):
        vertices.InsertCellPoint(i)
    
    # Créer un objet vtkPolyData pour stocker les points et leur connectivité
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetVerts(vertices)
    
    # Créer un objet vtkUnsignedCharArray pour stocker les couleurs
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("Colors")
    
    for color in points['color']:
        colors.InsertNextTuple3(*color)
    
    # Ajouter les couleurs au polydata
    polydata.GetPointData().SetScalars(colors)
    
    # Écrire les données dans un fichier VTK
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(polydata)
    writer.Write()
    print("Saved vtk file points in ", filename)

 

def webMapsToTif(west, south, east, north, outF, providerSRC=cx.providers.GeoportailFrance.orthos, zoomLevel=19):
    tempOUT = outF+"_temp.tif"
 
 
    
    cx.bounds2raster(west, south, east, north ,
                         ll=True,
                         path=tempOUT,
                                         zoom=zoomLevel,
                                         source=cx.providers.GeoportailFrance.orthos
     
                        )
    
    
    data = rasterio.open(tempOUT) 
    
    bbox = box(west, south, east, north)
    
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
    geo = geo.to_crs(crs=data.crs.data)

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]
      
    out_img, out_transform = mask(data, shapes=coords, crop=True)
    epsg_code = int(data.crs.data['init'][5:])
    out_meta = data.meta.copy()
    print(out_meta)
    
    
    out_meta.update({"driver": "GTiff",
                        "height": out_img.shape[1],
                        "width": out_img.shape[2],
                         "transform": out_transform,
                        "crs": pycrs.parse.from_epsg_code(epsg_code).to_proj4()}
                               )
    
    with rasterio.open(outF, "w", **out_meta) as dest:
        dest.write(out_img)
    
    print("Extracted image from contextily bounds:",west, south, east, north," zoom ", zoomLevel, " out files ",outF," and temporary ",tempOUT)

las1 = "/Users/filippi_j/data/2023/prunelli/LIDARHD_1-0_LAZ_VT-1224_6123-2021/Semis_2021_1224_6122_LA93_IGN78.laz"
las2 = "/Users/filippi_j/data/2023/prunelli/LIDARHD_1-0_LAZ_VT-1224_6123-2021/Semis_2021_1224_6123_LA93_IGN78.laz"
las3 = "/Users/filippi_j/data/2023/prunelli/LIDARHD_1-0_LAZ_VT-1224_6123-2021/Semis_2021_1225_6122_LA93_IGN78.laz"
las4 = "/Users/filippi_j/data/2023/prunelli/LIDARHD_1-0_LAZ_VT-1224_6123-2021/Semis_2021_1225_6123_LA93_IGN78.laz"
las5 = "/Users/filippi_j/data/2023/prunelli/LIDARHD_1-0_LAZ_VT-1226_6123-2021/Semis_2021_1226_6122_LA93_IGN78.laz"
las6 = "/Users/filippi_j/data/2023/prunelli/LIDARHD_1-0_LAZ_VT-1226_6123-2021/Semis_2021_1226_6123_LA93_IGN78.laz"

subsetFDS = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/subsetFDS.TIF"
subsetFDSLamb = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/subsetFDSLAMBERT.TIF"
lidplot = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/slidarColor.png"
outLAS = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/slidarArea.las"
lidarVTKout = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/slidarArea.vtk"
orthoTIF = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/ortho.tif"
orthoTIFLamb = "/Users/filippi_j/data/2023/prunelli/6731213101-2/sub/orthoLambert.tif"

#bbox de Yolanda
lat_sw, lon_sw = 42.0063067 , 9.3263082
lat_ne, lon_ne = 42.0104249 ,  9.3327945

#bbox réduite
#lat_sw, lon_sw = 42.007884 , 9.327366
#lat_ne, lon_ne = 42.008428 ,  9.328064

west, south, east, north = lon_sw,lat_sw, lon_ne,lat_ne

webMapsToTif(west, south, east, north, orthoTIF, zoomLevel=18)

lidarCRS=2154

reprojectTif(subsetFDS,subsetFDSLamb,lidarCRS)
reprojectTif(orthoTIF,orthoTIFLamb,lidarCRS)

left,right,bottom,top = getLeftRightBottomTop(orthoTIFLamb)  
all_filtered_points = filter_las_files_with_attributes(     (las1,las2,las3,las4), left, bottom, right, top )

all_filtered_points_colored = assign_colors_from_tif(all_filtered_points, orthoTIFLamb)

save_filtered_las(all_filtered_points_colored, outLAS)

save_points_to_vtk(all_filtered_points_colored, filename=lidarVTKout)

#plot_colored_points_3d(all_filtered_points_colored, filename=lidplot)
#print("plotted")
all_filtered_points_latlon = convert_LASCRS_to_latlon(all_filtered_points_colored)
save_filtered_las(all_filtered_points_latlon, outLAS+"latlon.las")


