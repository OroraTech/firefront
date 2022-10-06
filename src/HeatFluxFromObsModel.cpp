/*

Copyright (C) 2012 ForeFire Team, SPE, Universite de Corse.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 US

*/

#include "HeatFluxFromObsModel.h"

namespace libforefire {

/* name of the model */
const string HeatFluxFromObsModel::name = "heatFluxFromObs";

/* registration */
int HeatFluxFromObsModel::isInitialized =
        FireDomain::registerFluxModelInstantiator(name, getHeatFluxFromObsModel );

/* instantiation */
FluxModel* getHeatFluxFromObsModel(const int& index, DataBroker* db) {
	return new HeatFluxFromObsModel(index, db);
}

/* constructor */
HeatFluxFromObsModel::HeatFluxFromObsModel(
		const int & mindex, DataBroker* db) : FluxModel(mindex, db) {

	/* defining the properties needed for the model */
	evaporationTime_data = registerProperty("FromObs_evaporationTime");
    residenceTime_data = registerProperty("FromObs_residenceTime");
	burningTime_data = registerProperty("FromObs_burningTime");
	nominalHeatFlux_f_data = registerProperty("FromObs_NominalHeatFlux_flaming");
	nominalHeatFlux_s_data = registerProperty("FromObs_NominalHeatFlux_smoldering");

    /* allocating the vector for the values of these properties */
	if ( numProperties > 0 ) properties =  new double[numProperties];

	/* registering the model in the data broker */
	dataBroker->registerFluxModel(this);

	/* Definition of the coefficients */
	/*nominalHeatFlux = 150000.;
	if ( params->isValued("nominalHeatFlux") )
		nominalHeatFlux = params->getDouble("nominalHeatFlux");*/

}

/* destructor (shoudn't be modified) */
HeatFluxFromObsModel::~HeatFluxFromObsModel() {
	if ( properties != 0 ) delete properties;
}

/* accessor to the name of the model */
string HeatFluxFromObsModel::getName(){
	return name;
}

/* ****************** */
/* Model for the flux */
/* ****************** */

SensibleheatFlux  computeHeatFLuxFromBmap(const double& burningTime, const double& residenceTime, const double&  nominalHeatFlux_f, const double&  nominalHeatFlux_s, 
		 const double& bt, const double& et, const double& at){
	
    /* Mean heat flux released between the time interval [bt, et] */
	/* The heat flux is supposed to be constant from the arrival time (at)
	 * and for a period of time of 'burningDuration', constant of the model */

	/* Instantaneous flux */
	/* ------------------ */

	if ( bt == et ){
		if ( bt < at ) return SensibleheatFlux(0.,0.);
		if ( bt < at + residenceTime ) return SensibleheatFlux(nominalHeatFlux_f, 0.);
		if ( bt < at + burningTime )   return SensibleheatFlux(0., nominalHeatFlux_s);
		return SensibleheatFlux(0.,0.);
	}

	/* Averaged flux */
	/* ------------- */

	/* looking outside burning interval */
	if ( et < at or bt > at + burningTime ) return SensibleheatFlux( 0.,0.);
	

    
    /* begin time outside interval, end time inside flaming time*/
	if ( bt < at and et <= at + residenceTime ) return SensibleheatFlux(nominalHeatFlux_f*(et-at)/(et-bt), 0.);
    
    /* begin time outside interval, end time inside smoldering time*/
	if ( bt < at and et <= at + burningTime ) return SensibleheatFlux(nominalHeatFlux_f*residenceTime/ (et-bt),  nominalHeatFlux_s*(et-(at+residenceTime)) / (et-bt) );
	
    /* begin time outside interval, end time outside */
	if ( bt < at and et > at + burningTime ) return  SensibleheatFlux(nominalHeatFlux_f*residenceTime / (et-bt),  nominalHeatFlux_s*(burningTime-residenceTime) / (et-bt) );
	


    /* begin time inside flaming, end time inside flaming */
	if ( bt >= at and bt <= at + residenceTime and et <= at + residenceTime ) return SensibleheatFlux(nominalHeatFlux_f, 0. );
    
    /* begin time inside flaming, end time inside smoldering*/
	if ( bt >= at and bt <= at + residenceTime and et <= at + burningTime   ) return SensibleheatFlux(nominalHeatFlux_f*(at+residenceTime-bt) / (et-bt) , nominalHeatFlux_s*(et-(at+residenceTime)) / (et-bt) );
	
    /* begin time insObsModel.cpp:129: warning: coide flaming, end time outside*/
	if ( bt >= at and bt <= at + residenceTime and et > at + burningTime   ) return SensibleheatFlux(nominalHeatFlux_f*(at+residenceTime-bt) / (et-bt) , nominalHeatFlux_s*(burningTime-residenceTime) / (et-bt));



    /* begin time inside smoldering, end time inside smoldering */
	if ( bt >= at+residenceTime and bt <= at+burningTime and et <= at+burningTime ) return SensibleheatFlux(0., nominalHeatFlux_s);
    
    /* begin time inside smoldering, end time outside*/
	if ( bt >= at+residenceTime and bt <= at+burningTime and et >  at+burningTime   ) return SensibleheatFlux(0., nominalHeatFlux_s*((burningTime+at)-bt) / (et-bt)) ;

    return  SensibleheatFlux( -999.,-999.);

    //cout << "merde" << endl;

}


double HeatFluxFromObsModel::getValue(double* valueOf
		, const double& bt, const double& et, const double& at){
	
    /* Mean heat flux released between the time interval [bt, et] */
	/* The heat flux is supposed to be constant from the arrival time (at)
	 * and for a period of time of 'burningDuration', constant of the model */


    double burningTime       = valueOf[burningTime_data];
    double residenceTime     = valueOf[residenceTime_data];
    double evaporationTime     = valueOf[evaporationTime_data];
    double nominalHeatFlux_f = valueOf[nominalHeatFlux_f_data];
    double nominalHeatFlux_s = valueOf[nominalHeatFlux_s_data];
	
    SensibleheatFlux sensibleheatFlux = computeHeatFLuxFromBmap(burningTime,residenceTime,nominalHeatFlux_f,nominalHeatFlux_s,bt,et,at+evaporationTime);
    //cout << nominalHeatFlux_f << endl;	
	//if (burningTime>=0)
	//	cout << "formObs " << et << ' ' << bt << ' ' << at << ' ' << burningTime << ' ' << nominalHeatFlux << ' ' << mm << '\n';
	
	return sensibleheatFlux.flaming + sensibleheatFlux.smoldering ;

}

} /* namespace libforefire */
