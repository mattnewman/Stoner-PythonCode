"""Library of functions that nlfit can use to fit to. Functions should accept an array of x values
and a list of parmeters, they should then return an array of y values the same size as the x array.
Please do keep documentation up to date, see other functions for documentation examples"""

import numpy
import scipy

def quadratic(x, p):
    return p[0]*x*x

def Simmons(V, params):
    """
    Simmons model tunnelling
    V=bias voltage, params=[A, phi, d]
    A in m^2, phi barrier height in eV, d barrier width in angstrom
    
    Simmons model as in
    Simmons J. App. Phys. 34 6 1963
    """
    [A, phi, d] = params
    I=6.2e6*A/d**2*((phi-V/2)*numpy.exp(-1.025*d*numpy.sqrt(phi-V/2))-(phi+V/2)*exp(-1.025*d*numpy.sqrt(phi+V/2)))
    return I

def BDR(V, params):
    """BDR model tunnelling
    V=bias voltage, params=[A, phi, dphi, d, mass]
    A: in m^2, phi: average barrier height in eV, dphi: change in barrier height in eV,
    d: barrier width in angstrom, mass: effective electron mass as a fraction of electron rest mass
    
    See Brinkman et. al. J. Appl. Phys. 41 1915 (1970)
    or Tuan Comm. in Phys. 16, 1, (2006)"""
    [A, phi, dphi, d, mass] = params
    I=3.16e10*A**2*numpy.sqrt(phi)/d*numpy.exp(-1.028*numpy.sqrt(phi)*d)*(V-0.0214*numpy.sqrt(mass)*d*dphi/phi**1.5*V**2+0.0110*mass*d**2/phi*V**3)
    return I

def FowlerNordheim(V, params):
    """
    Simmons model tunnelling at V>phi
    V=bias voltage, params=[A, phi, d]
    A in m^2, phi barrier height in eV, d barrier width in angstrom
    
    Simmons model as in
    Simmons J. App. Phys. 34 6 1963
    """
    [A, phi, d] = params
    I=V/abs(V)*3.38e6*A*V**2/(d**2*phi)*numpy.exp(-0.689*phi**1.5*d/abs(V)) 
    return I
    
def TersoffHammann(V, params):
    """TersoffHamman model for tunnelling through STM tip
    V=bias voltage, params=[A]
    """
    [A] = params
    I=A*V
    return V
    
def WLfit(B, params):
    """
    Weak localisation
    VRH(B, params):
    B = mag. field, params=list of parameter values, s0, B1, B2
    
    2D WL model as per
    Wu PRL 98, 136801 (2007)
    Porter PRB 86, 064423 (2012)
    """
#   Parameters
    s0 = params[0]    #zero field conductance
    DS = params[1]    #scaling parameter
    B1 = params[2]    #elastic characteristic field (B1)
    B2 = params[3]    #inelastic characteristic field (B2)

    e = 1.6e-19 #C
    h = 6.62e-34 #Js
    #Sets up conductivity fit array
    cond=scipy.zeros(len(B));
    if B2 == B1:
        B2 = B1*1.00001 #prevent dividing by zero

        #performs calculation for all parts    
    for tt in range(len(B)):
        if B[tt] != 0: #prevent dividing by zero
            WLpt1 = scipy.special.digamma( 0.5 + B2 / numpy.abs(B[tt]))
            WLpt2 = scipy.special.digamma( 0.5 + B1 / numpy.abs(B[tt]))
        else:
            WLpt1 = ( scipy.special.digamma( 0.5 + B2 / numpy.abs(B[tt - 1])) + scipy.special.digamma( 0.5 + B2 / numpy.abs(B[tt + 1])) ) / 2
            WLpt2 = ( scipy.special.digamma( 0.5 + B1 / numpy.abs(B[tt - 1])) + scipy.special.digamma( 0.5 + B1 / numpy.abs(B[tt + 1])) ) / 2

        WLpt3 = numpy.log(B2 / B1)

    #Calculates fermi level smearing
        cond[tt] = ( e**2 / (h*numpy.pi) )*( WLpt1 - WLpt2 - WLpt3 )
    #cond = s0*cond / min(cond)
    cond = s0 + DS*cond
    return cond

def strijkers(V, params):
    """
    strijkers(V, params):
    V = bias voltages, params=list of parameter values, imega, delta,P and Z
    PCAR fitting
    Strijkers modified BTK model
        BTK PRB 25 4515 1982, Strijkers PRB 63, 104510 2000

    Only using 1 delta, not modified for proximity
    """
    #   Parameters
    print '.',
    omega=params[0]     #Broadening
    delta=params[1]    #SC energy Gap
    P=params[2]         #Interface parameter 
    Z=params[3]         #Current spin polarization through contact
    
    E = scipy.arange(-50, 50, 0.05) # Energy range in meV
    
    #Reflection prob arrays
    Au=scipy.zeros(len(E))
    Bu=scipy.zeros(len(E))
    Bp=scipy.zeros(len(E))
    
    #Conductance calculation
    """    
    % For ease of calculation, epsilon = E/(sqrt(E^2 - delta^2))
    %Calculates reflection probabilities when E < or > delta
    %A denotes Andreev Reflection probability
    %B denotes normal reflection probability
    %subscript p for polarised, u for unpolarised
    %Ap is always zero as the polarised current has 0 prob for an Andreev
    %event
    """
    
    for ss in range(len(E)):
        if abs(E[ss])<=delta:
            Au[ss]=(delta**2)/((E[ss]**2)+(((delta**2)-(E[ss]**2))*(1+2*(Z**2))**2));
            Bu[ss] = 1-Au[ss];
            Bp[ss] = 1;
        else:
            Au[ss] = (((abs(E[ss])/(scipy.sqrt((E[ss]**2)-(delta**2))))**2)-1)/(((abs(E[ss])/(scipy.sqrt((E[ss]**2)-(delta**2)))) + (1+2*(Z**2)))**2);
            Bu[ss] = (4*(Z**2)*(1+(Z**2)))/(((abs(E[ss])/(scipy.sqrt((E[ss]**2)-(delta**2)))) + (1+2*(Z**2)))**2);
            Bp[ss] = Bu[ss]/(1-Au[ss]);
        
    #  Calculates reflection 'probs' for pol and unpol currents
    Guprob = 1+Au-Bu;
    Gpprob = 1-Bp;

    #Calculates pol and unpol conductance and normalises
    Gu = (1-P)*(1+(Z**2))*Guprob;
    Gp = 1*(P)*(1+(Z**2))*Gpprob;
    
    G = Gu + Gp;
    
    
    #Sets up gaus
    gaus=scipy.zeros(len(V));
    cond=scipy.zeros(len(V));
    
    #computes gaussian and integrates over all E(more or less)
    for tt in range(len(V)):
    #Calculates fermi level smearing
        gaus=(1/(2*omega*scipy.sqrt(scipy.pi)))*scipy.exp(-(((E-V[tt])/(2*omega))**2))
        cond[tt]=numpy.trapz(gaus*G,E);
    return cond
