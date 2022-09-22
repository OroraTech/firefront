/*

Copyright (C) 2021 ForeFire Team, SPE, Universit� de Corse.

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

// model from :
// Balbi et. al. IJWF 2020 A convective–radiative propagation model for wildland fires 10.1071/WF19103

*/

#include "Balbi2020.h"
#include <algorithm> 

namespace libforefire {

/* name of the model */
const string Balbi2020::name = "Balbi2020";

/* instantiation */
PropagationModel* getBalbi2020Model(const int & mindex, DataBroker* db) {
	return new Balbi2020(mindex, db);
}

/* registration */
int Balbi2020::isInitialized =
        FireDomain::registerPropagationModelInstantiator(name, getBalbi2020Model );

/* constructor */
Balbi2020::Balbi2020(const int & mindex, DataBroker* db)
: PropagationModel(mindex, db) {

	/* defining the properties needed for the model */
	slope = registerProperty("slope");
	normalWind = registerProperty("normalWind");
	moisture = registerProperty("moisture");
	temperature = registerProperty("temperature");
	Rhod = registerProperty("fuel.Rhod");
	Rhol = registerProperty("fuel.Rhol");
	Md = registerProperty("fuel.Md");
	Ml = registerProperty("fuel.Ml");
	sd = registerProperty("fuel.sd");
	sl = registerProperty("fuel.sl");
	e = registerProperty("fuel.e");
	Sigmad = registerProperty("fuel.Sigmad");
	Sigmal = registerProperty("fuel.Sigmal");
	stoch = registerProperty("fuel.stoch");
	RhoA = registerProperty("fuel.RhoA");
	Ta = registerProperty("fuel.Ta");
	Tau0 = registerProperty("fuel.Tau0");
	Deltah = registerProperty("fuel.Deltah");
	DeltaH = registerProperty("fuel.DeltaH");
	Cp = registerProperty("fuel.Cp");
	Ti = registerProperty("fuel.Ti");
	X0 = registerProperty("fuel.X0");
	r00 = registerProperty("fuel.r00");
	Blai = registerProperty("fuel.Blai");

	/* allocating the vector for the values of these properties */
	if ( numProperties > 0 ) properties =  new double[numProperties];

	/* registering the model in the data broker */
	dataBroker->registerPropagationModel(this);

	/* Definition of the coefficients */
	cooling = 0.;
	if ( params->isValued("Balbi2020.cooling") )
		cooling = params->getDouble("Balbi2020.cooling");
	Cpa = 1004.;
	if ( params->isValued("Balbi2020.Cpa") )
		Cpa = params->getDouble("Balbi2020.Cpa");
}

/* destructor (shoudn't be modified) */
Balbi2020::~Balbi2020() {
}

/* accessor to the name of the model */
string Balbi2020::getName(){
	return name;
}

/* *********************************************** */
/* Model for the propagation velovity of the front */
/* *********************************************** */




double Balbi2020::getSpeed(double* valueOf){

   
    // Fuel Specific 
	double lh   = valueOf[e];
	if( lh <= 0 ) return 0;
	double lrhov = valueOf[Rhod];
	double lm  = valueOf[Md];
	double ls  = valueOf[sd];
	double lsigma = valueOf[Sigmad];
	double lrhoa  = valueOf[RhoA];

	double lCp = valueOf[Cp];
    // Env Specific
	double lTa  = valueOf[Ta];
	double lTi  = valueOf[Ti];
	double lDeltah   = valueOf[Deltah];
	double lDeltaH = valueOf[DeltaH];
	double lr00  = valueOf[r00];	
	
	double ltau0  = valueOf[Tau0];
	double lU = 0.;
	double RU = valueOf[normalWind];
	if(RU > 0){
	  lU = RU;
	}

	double lChi0  = valueOf[X0];
	double lalpha = atan(valueOf[slope]);
	double lg = 9.81;
	double B = 5.6e-8; // nomenclature

	double Cpa = 1150 ;// nomenclature
	double Tvap = 373; // nomenclature
	double K1 = 130 ;// nomenclature new parameter
	double st = 17 ;// nomenclature new parameter



    int step = 1;
    bool flag = 1;
    bool stopcondition = true;
    double error = 0;
    // Numerical Coefficients
    double maxEps = 0.01;
    int N=40;

 


    double R = 0.01;
	double Rnew = 0;


    while (stopcondition){

        // Packing ratio
        double Beta = lsigma/(lh*lrhov) ;  // between eq. B8 and eq. B9
        //print("Packing ratio ", Beta)

        //Leaf Area ratio
        double S = ls*Beta*lh ;// just before eq. 13
        //print("Leaf Area Index ", S/2) // just before eq. 13 S is the total fuel surface area per horizontal area unit of fuel bed and denotes the double of the leaf area index (LAI),

        //Ignition energy (J/kg)
        double q =  lCp*(lTi-lTa) + lm*(lDeltah+lCp*(Tvap-lTa)) ;// eq. 9
        //print("Ignition energy ", q)

        // scaling factor
        double ar = min(S/(2*PI),1.) ;// eq. 17

        // Radiative factor
        double A = ar*( (lChi0*lDeltaH)/(4*q)   ) ;// eq. 16
        //print("Radiant Factor A ", A)

        // coefficient p required for T
        double p = (2/lr00)/ltau0 ;  // derived from expression between C7 and C8 

        // Radiant fractor
        double Chi = lChi0 /(1+p*((R*ltau0*cos(lalpha))/2*ls)) ;  // eq. C7 
        //print("Radiant Fraction ", Chi)

        // Mean Flame Temperature
        double T = lTa+lDeltaH*((1-Chi)/(Cpa*(st+1))) ;// eq. B11
        //print("Flame Temperature ", T)

        // reference vertical velocity
        double u0 = 2* (st + 1)/ltau0 * T/lTa *  lrhov/lrhoa * min(S,2*PI) ; // eq. B9
        //print("Vertical Velocity ref (u0) ", u0)

        // flame angle
        double gamma = atan(tan(lalpha)+ (lU/u0)) ;  // eq. 2
        //print("Flame angle in degrees ", math.degrees(gamma))

        // flame height 
        double H = (u0*u0)/(lg*(T/lTa - 1.))  ; // eq. 23
        //print("Flame Height ", H)

        double Rb = min((S/PI),1.)*((B*pow(T,4))/(Beta*lrhov*q))  ;// eq. 13
        //print("Ros base (Rb) ", Rb)

        double Rc1 = ls * (lDeltaH/(q*ltau0)) * min(lh, (2*PI)/(ls*Beta));
        double Rc2 = (lh/(2*lh+H))  *  tan(lalpha)  + ( (lU*exp(-K1*pow(Beta,0.5)*R)) / u0);
        double Rc = Rc1*Rc2  ;   // eq. 27
        //print("Ros conv Total (Rc) ", Rc)

        double Rr = A*R*((1+sin(gamma)-cos(gamma))/( 1+ ( (R*cos(gamma)) / (ls*lr00) )) ) ;// eq. 15
        //print("Rosradiant (Rr) ", Rr)

        Rnew = Rb+Rc+Rr;
        
        error = R-Rnew;
        //print('-------------Iteration-%d, R = %0.6f  Diff = %0.6f ' % (step, x1, error))

        R = Rnew; 
        if (step++ > N){
            flag=0;
            break;
			}
        stopcondition = (abs(error) > maxEps);
	}
    if (flag==1){
        return Rnew;
	}
	
	//cout << "R "<< R << " not convergent " << error <<  endl;
    return R+error/2;
}

} /* namespace libforefire */
