#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 11:34:06 2023

Sample tools usages for pre and post processing of coupled MesoNH-ForeFire

@author: Jean-Baptiste Filippi
@todo : timed kml with wind from preal -
@todo : pMNH2vtk - with pgd file, not with domains
@todo : pMNH2vtk : include bmaptovtk with the atimebmap in standard and ZS from PDG
@todo : mode output diagnowtics
@todo : 2Dmore frequent outputs
@todo : include the Mars request
@todo : a documentation that is also a presentation for MesoNH days
@todo : BMap reconstructions from contours... first anything to FireFront format, then make simulations, then compile results
@todo : intelligent analysis of reconstructed bmaps : find where there is the most coherent data and speed (filter by ROS, gradient like wind/slope...)
    
"""
from datetime import datetime, timedelta

Pigna20230725 = {
    "case_path": "",
    "template_path": "",
    "PGDFILES": [
        "/chemin/vers/le/fichier1",
        "/chemin/vers/le/fichier2",
        "/chemin/vers/le/fichier3"
    ],
    "info_position": {
        "date": "2023-09-11",
        "latitude": 48.8566,
        "longitude": 2.3522
    }
    
}
Monze20190814 = {
    "case_path": "/Users/filippi_j/Volumes/orsu/firecaster/2023/nest150Ref/",
    "template_path": "/Users/filippi_j/Volumes/orsu/firecaster/2023/nest150Ref/",
    "PGDFILES": [
        "/001_pgd/PGD_D2000mA.nc",
        "/001_pgd/PGD_D400mA.nc",
        "/001_pgd/PGD_D80mA.nc"
    ],
    "run_info": {
        "start_time": "2019-08-14T10:00:00",
        "end_time": "2019-08-15T00:00:10",
        "latitude_center": 43.1476,
        "longitude_center": 2.48590,
        "XOR1TO2": 46,
        "YOR1TO2": 46,
        "XOR2TO3": 60,
        "YOR2TO3": 60
    },
    "ignitions": [
        {"when": "2019-08-14T14:10:00", "latitude": 43.155, "longitude": 2.42222}
        ],
    "OUTKMLDOMAINFILE": "RESULTS/domains.kml"
    
}
orig = "/scratch/filippi_j/"
orig = "/Users/filippi_j/Volumes/orsu/"
orig = "/Users/filippi_j/data/2023/toulouse/"

toulouse20190814 = {
    "case_path": "%s/"%orig,
    "template_path": "%s/firecaster/2023/nest150Ref"%orig,
    "PGDFILES": [
        "/006_runff/PGD_D2000mA.nested.nc",
        "/006_runff/PGD_D400mA.nested.nc",
        "/006_runff/PGD_D80mA.nested.nc"
    ],
    "run_info": {
        "start_time": "2019-08-14T10:00:00",
        "end_time": "2019-08-15T03:00:10",
        "latitude_center": 44.43,
        "longitude_center": 0.48590,
        "XOR1TO2": 46,
        "YOR1TO2": 46,
        "XOR2TO3": 60,
        "YOR2TO3": 60
    },
    "ignitions": [
        {"when": "2019-08-14T14:10:00", "latitude": 44.43, "longitude": 0.48222},
        {"when": "2019-08-14T14:20:00", "latitude": 44.43, "longitude": 0.48322}
        ],
    "CoupledLandscape_path": "/006_runff/ForeFire/landcoupled.nc",
    "UnCoupledLandscape_path": "/006_runff/ForeFire/land.nc",
    "initff_path": "/006_runff/ForeFire/Init.ff",
    "BMAPFILE": "/006_runff/ForeFire/Outputs/ForeFire.0.nc",
    "FFINPUTPATTERN": "/006_runff/ForeFire/Outputs/output.0.*",
    "MODELOUTPATTERN": ["/006_runff/MODEL1/output","/006_runff/MODEL2/output","/006_runff/MODEL3/output"],
    
    "FFOUTVTKPATH": ["/RESULTS/vtkout1/","/RESULTS/vtkout2/","/RESULTS/vtkout3/"],
    "OUTKMLDOMAINFILE": "/RESULTS/domains.kml",
    "frontsKMLOUT": "/RESULTS/fronts.kml",
    "BMAPKMLOUT": "/RESULTS/ros.kml",
    "fuel_TIF_path": "/RESULTS/fuel.tif",
    "fuel_png_path": "/RESULTS/fuel.png",
    "fuel_kml_path": "/RESULTS/fuel.kml"
 
}

# Process type : 
# Make a first guess : a nofire with wind etc... make first quick outputs - that will be a 00 in pattern - make outputs from that in KML, fronts and intensity
# 


CAST = toulouse20190814

gen_empty_FFMNH_case = True
gen_domain_kml = False
gen_fuel_map  = False
gen_FAF_case = False
gen_AF_case = False
gen_2D_VTK_OUT = False
gen_3D_VTK_OUT = False
gen_KML_OUT = True
gen_TESTFUEL_case = False

OUTKMLDOMAINFILE = CAST["case_path"]+CAST["OUTKMLDOMAINFILE"]
PGDFILES = [CAST['case_path'] + file for file in CAST['PGDFILES']]
FFOUTVTKPATH = [CAST['case_path'] + file for file in CAST['FFOUTVTKPATH']]
MODELOUTPATTERN = [CAST['case_path'] + file for file in CAST['MODELOUTPATTERN']]

fuel_TIF_path= CAST['case_path'] + CAST['fuel_TIF_path']
fuel_png_path= CAST['case_path'] + CAST['fuel_png_path']
fuel_kml_path= CAST['case_path'] + CAST['fuel_kml_path']
CoupledLandscape_path= CAST['case_path'] + CAST['CoupledLandscape_path']
UnCoupledLandscape_path= CAST['case_path'] + CAST['UnCoupledLandscape_path']
initff_path= CAST['case_path'] + CAST['initff_path']
BMAPFILE = CAST['case_path'] + CAST['BMAPFILE'] 
FFINPUTPATTERN= CAST['case_path'] + CAST['FFINPUTPATTERN']
BMAPKMLOUT= CAST['case_path'] + CAST['BMAPKMLOUT']
frontsKMLOUT= CAST['case_path'] + CAST['frontsKMLOUT']


# with date and location, define domains > generate template and copy files also from weather archive
if gen_empty_FFMNH_case:
    # Convertir les chaînes en objets datetime
    start_date = datetime.fromisoformat(CAST['run_info']['start_time'])
    end_date = datetime.fromisoformat(CAST['run_info']['end_time'])
    
    # Extraire la date de début au format YYYYMMDD
    start_date_str = start_date.strftime("%Y%m%d")
    
    # Calculer la différence en secondes entre la fin et le début
    delta_seconds = (end_date - start_date).total_seconds()
    
    # Trouver la valeur heure de départ en multiple de 3
    start_hour = start_date.hour
    start_hour = (start_hour // 3) * 3
    
    # Calculer la valeur heure de fin en multiple de 3
    delta_hours = delta_seconds // 3600  # Convertir la différence en heures
    end_hour = ((delta_hours + 2) // 3) * 3  # Arrondir à l'entier multiple de 3 supérieur
    end_hour += start_hour  # Ajouter la valeur heure de départ
    
    start_hour_str = "%02d"%start_hour
    end_hour_str = "%02d"%end_hour
      
    # Trouver l'ignition la plus tôt
    earliest_ignition_time = min(datetime.fromisoformat(ignition["when"]) for ignition in CAST["ignitions"])
   
    # Trouver l'heure arrondie au multiple de 3 immédiatement inférieure à cette différence, mais supérieure à l'heure de début
    MODEL_1_ALONE_max_hour =((earliest_ignition_time.hour // 3)+1) * 3
    MODEL_2_3_hour = earliest_ignition_time.hour - 1
    MNHFILE_2_3_hour = MODEL_2_3_hour - start_hour 
    
    M123_PREAL_START = ((earliest_ignition_time.hour // 3)) * 3
    M123_PREAL_END = int(end_hour)
    
    # Exécution de la fonction
    
    print(f"# Fire at date {start_date_str}, ignition at time {earliest_ignition_time}" )    
    print(f"# Run from {CAST['run_info']['start_time']} to {CAST['run_info']['end_time']}" )
    print(f"# First domain running alone from {start_hour_str} to {MODEL_1_ALONE_max_hour} " )
    print(f"# Domain 2 and 3 starting at time {MODEL_2_3_hour} that is hourly step {MNHFILE_2_3_hour} of run1 that started at {start_hour_str} " )
    print(f"# Domain 1-2-3 starting at time {MODEL_2_3_hour} (file init {MNHFILE_2_3_hour}) using PREAL BC from {M123_PREAL_START} to {M123_PREAL_END} inited at {start_hour_str} " )
    
    print(f"# Configuration files generation script :")
    print(f"cp -r {CAST['template_path']} {CAST['case_path']}")
    print(f"cd {CAST['case_path']}")
    print(f"cd 001_pgd/ ; bash MAKE_PGD {CAST['run_info']['latitude_center']} {CAST['run_info']['longitude_center']} {CAST['run_info']['XOR1TO2']} {CAST['run_info']['YOR1TO2']} {CAST['run_info']['XOR2TO3']} {CAST['run_info']['YOR2TO3']}") 
    print(f"cd ../002_real/ ; bash MAKE_PREAL {start_hour_str} {end_hour_str} {start_date_str} ") 
    print(f"cd ../003_run/ ; bash MAKE_RUN1 {start_hour} {MODEL_1_ALONE_max_hour} {start_date_str} ") 
    print(f"cd ../004_SpawnReal/ ; bash MAKE_SPAWNREAL {MNHFILE_2_3_hour} {start_date_str} {MODEL_2_3_hour}") 
    print(f"cd ../005_SpawnReal/ ; bash MAKE_SPAWNREAL23 {start_date_str} {MODEL_2_3_hour}")

    print(f"cd ../006_runff/ ; bash MAKE_RUNFF {start_date_str} {M123_PREAL_START} {M123_PREAL_END} {MNHFILE_2_3_hour} {MODEL_2_3_hour}")     
    
# now run PGD, and see if domains OK in google earth/ re-run and adjust if needed
if gen_domain_kml:
    from preprocessing.kmlDomain import pgds_to_KML
    pgds_to_KML(PGDFILES,OUTKMLDOMAINFILE)

# Now we can try to make a fuel distribution file using PNG's and databases.. approach here is from 
if gen_fuel_map:
    from preprocessing.learnFuelTifPng import makeFuelMapFromPgd
    print(PGDFILES[-1])
    makeFuelMapFromPgd(PGDFILES[-1],fuel_TIF_path,fuel_png_path,fuel_kml_path)   
    
# IF OK, make all required files to ForeFire, also need tima and start
# FA : Fire-To-Atm one is AF : Atm-To-Fire last is FAF: Fire-To-Atm-To-Fire

if gen_FAF_case:
    from preprocessing.prealCF2Case import PGD2Case
    from preprocessing.ffToGeoJson import ffFromPgd
    domTime = datetime.fromisoformat(CAST['run_info']['start_time'])
    PGD2Case(PGDFILES[-1],fuel_png_path,UnCoupledLandscape_path, domTime)
    with open(initff_path, 'w') as file:
        file.write(ffFromPgd(PGDFILES[-1],domainDate=domTime,ignitions = CAST['ignitions']))
 

# for the atmosphere to fire only, Trying to use the PREAL files from Domain Nmax (smallest)
if gen_AF_case:
    PGD2Case(FIREDOMPGDFILE,IGNITIONS,OUTFFLANDSCAPE, OUTFFINIT)    

# now we assume everythng has run we can do the post-processing first the 2D VTKOUT
if gen_2D_VTK_OUT:
    print_vtkout_slurm_command_2D()
    
# now wa assume everythng has run we can do the post-processing the 3D VTKOUT
if gen_3D_VTK_OUT:
    from postprocessing.pMNHFF2VTK import ffmnhFileToVtk, ffFrontsToVtk
    #ffFrontsToVtk(inFFpattern = FFINPUTPATTERN,outPath = FFOUTVTKPATH[-1])
    ffmnhFileToVtk(inpattern = MODELOUTPATTERN[1],pgdFile = PGDFILES[1],outPath = FFOUTVTKPATH[1])
    
    #print_vtkout_slurm_command_3D()

if gen_TESTFUEL_case:
    from preprocessing.prealCF2Case import PGD2Case
    from preprocessing.ffToGeoJson import ffFromPgd
    domTime = datetime.fromisoformat(CAST['run_info']['start_time'])
    PGD2Case(PGDFILES[-1],fuel_png_path,UnCoupledLandscape_path, domTime, FuelTest=7)
    
    with open(initff_path, 'w') as file:
        file.write(ffFromPgd(PGDFILES[-1],domainDate=domTime,FuelTest = 7))
 
# now we assume everythng has run we try to do all output KMLs
if gen_KML_OUT:
    from preprocessing.ffToGeoJson import genKMLFiles
    genKMLFiles(PGDFILES[-1], BMAPFILE, FFINPUTPATTERN, BMAPKMLOUT,frontsKMLOUT, everyNFronts=6, change_color_every=30)



# define when to start
# define the domain
# 