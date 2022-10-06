/*

Copyright (C) 2012 ForeFire Team, SPE, Université de Corse.

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

#include "ScalarFluxNominalModel.h"

namespace libforefire {

/* name of the model */
const string ScalarFluxNominalModel::name = "SFMod";

/* instantiation */
FluxModel* getScalarFluxNominalModel(const int& index, DataBroker* db) {
	return new ScalarFluxNominalModel(index, db);
}

/* registration */
int ScalarFluxNominalModel::isInitialized =
        FireDomain::registerFluxModelInstantiator(name, getScalarFluxNominalModel );

/* constructor */
ScalarFluxNominalModel::ScalarFluxNominalModel(
		const int & mindex, DataBroker* db) : FluxModel(mindex, db) {

	/* defining the properties needed for the model */
	tau0 = registerProperty("fuel.Tau0");
	sd = registerProperty("fuel.sd");

	/* allocating the vector for the values of these properties */
	if ( numProperties > 0 ) properties =  new double[numProperties];

	/* registering the model in the data broker */
	dataBroker->registerFluxModel(this);

	/* Definition of the coefficients */
	nominalScalarFlux = 1.;
	if ( params->isValued("nominalScalarFlux") )
		nominalScalarFlux = params->getDouble("nominalScalarFlux");
}

/* destructor (shoudn't be modified) */
ScalarFluxNominalModel::~ScalarFluxNominalModel() {
	if ( properties != 0 ) delete properties;
}

/* accessor to the name of the model */
string ScalarFluxNominalModel::getName(){
	return name;
}

/* ****************** */
/* Model for the flux */
/* ****************** */

double ScalarFluxNominalModel::getValue(double* valueOf
		, const double& bt, const double& et, const double& at){
	/* Mean vapor flux released between the time interval [bt, et] */
	/* The vapor flux is supposed to be constant from the arrival time (at)
	 * and for a period of time of given by fuel properties tau0/sd */

	double burningDuration = valueOf[tau0]/valueOf[sd];

	/* Instantaneous flux */
	/* ------------------ */
	if ( bt == et ){
		if ( bt < at ) return 0;
		if ( bt < at + burningDuration ) return nominalScalarFlux;
		return 0;
	}

	/* Averaged flux */
	/* ------------- */

	/* looking outside burning interval */
	if ( et < at or bt > at + burningDuration ) return 0;
	/* begin time outside interval, end time inside */
	if ( bt < at and et <= at + burningDuration ) return nominalScalarFlux*(et-at)/(et-bt);
	/* begin time outside interval, end time outside */
	if ( bt < at and et > at + burningDuration ) return nominalScalarFlux*burningDuration/(et-bt);
	/* begin time inside interval, end time inside */
	if ( bt >= at and et <= at + burningDuration ) return nominalScalarFlux;
	/* begin time inside interval, end time outside */
	return nominalScalarFlux*(at+burningDuration-bt)/(et-bt);

}

} /* namespace libforefire */
