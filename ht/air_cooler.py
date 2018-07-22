# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2016, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

from __future__ import division
from math import atan, sin, log10
from scipy.constants import hp, minute, inch
from fluids.geometry import AirCooledExchanger
from fluids import Prandtl, Reynolds
from ht.core import LMTD, fin_efficiency_Kern_Kraus

__all__ = ['Ft_aircooler', 'air_cooler_noise_GPSA', 
           'air_cooler_noise_Mukherjee', 'h_Briggs_Young',
           'h_ESDU_highfin_staggered']

fin_densities_inch = [7, 8, 9, 10, 11] # fins/inch
fin_densities = [round(i/0.0254, 1) for i in fin_densities_inch]
ODs = [1, 1.25, 1.5, 2] # Actually though, just use TEMA. API 661 says 1 inch min.
fin_heights = [0.010, 0.012, 0.016] # m


tube_orientations = ['vertical (inlet at bottom)', 'vertical (inlet at top)', 'horizontal', 'inclined']

_fan_diameters = [0.71, 0.8, 0.9, 1.0, 1.2, 1.24, 1.385, 1.585, 1.78, 1.98, 2.22, 2.475, 2.775, 3.12, 3.515, 4.455, 4.95, 5.545, 6.24, 7.03, 7.92, 8.91, 9.9, 10.4, 11.1, 12.4, 13.85, 15.85]

fan_ring_types = ['straight', 'flanged',  'bell', '15 degree cone', '30 degree cone']

fin_constructions = ['extruded', 'embedded', 'L-footed', 'overlapped L-footed', 'externally bonded', 'knurled footed']

headers = ['plug', 'removable cover', 'removable bonnet', 'welded bonnet']
configurations = ['forced draft', 'natural draft', 'induced-draft (top drive)', 'induced-draft (bottom drive)']




# Coefs are from: Roetzel and Nicole - 1975 - Mean Temperature Difference for Heat Exchanger Design A General Approximate Explicit Equation
# Checked twice.

_crossflow_1_row_1_pass = [[-4.62E-1, -3.13E-2, -1.74E-1, -4.2E-2],
                           [5.08E0, 5.29E-1, 1.32E0, 3.47E-1],
                           [-1.57E1, -2.37E0, -2.93E0, -8.53E-1],
                           [1.72E1, 3.18E0, 1.99E0, 6.49E-1]]

_crossflow_2_rows_1_pass = [[-3.34E-1, -1.54E-1, -8.65E-2, 5.53E-2],
                            [3.3E0, 1.28E0, 5.46E-1, -4.05E-1],
                            [-8.7E0, -3.35E0, -9.29E-1, 9.53E-1],
                            [8.7E0, 2.83E0, 4.71E-1, -7.17E-1]]

_crossflow_3_rows_1_pass = [[-8.74E-2, -3.18E-2, -1.83E-2, 7.1E-3],
                            [1.05E0, 2.74E-1, 1.23E-1, -4.99E-2],
                            [-2.45E0, -7.46E-1, -1.56E-1, 1.09E-1],
                            [3.21E0, 6.68E-1, 6.17E-2, -7.46E-2]]

_crossflow_4_rows_1_pass = [[-4.14E-2, -1.39E-2, -7.23E-3, 6.1E-3],
                            [6.15E-1, 1.23E-1, 5.66E-2, -4.68E-2],
                            [-1.2E0, -3.45E-1, -4.37E-2, 1.07E-1],
                            [2.06E0, 3.18E-1, 1.11E-2, -7.57E-2]]

_crossflow_2_rows_2_pass = [[-2.35E-1, -7.73E-2, -5.98E-2, 5.25E-3],
                            [2.28E0, 6.32E-1, 3.64E-1, -1.27E-2],
                            [-6.44E0, -1.63E0, -6.13E-1, -1.14E-2],
                            [6.24E0, 1.35E0, 2.76E-1, 2.72E-2]]

_crossflow_3_rows_3_pass = [[-8.43E-1, 3.02E-2, 4.8E-1, 8.12E-2],
                            [5.85E0, -9.64E-3, -3.28E0, -8.34E-1],
                            [-1.28E1, -2.28E-1, 7.11E0, 2.19E0],
                            [9.24E0, 2.66E-1, -4.9E0, -1.69E0]]

_crossflow_4_rows_4_pass = [[-3.39E-1, 2.77E-2, 1.79E-1, -1.99E-2],
                            [2.38E0, -9.99E-2, -1.21E0, 4E-2],
                            [-5.26E0, 9.04E-2, 2.62E0, 4.94E-2],
                            [3.9E0, -8.45E-4, -1.81E0, -9.81E-2]]

_crossflow_4_rows_2_pass = [[-6.05E-1, 2.31E-2, 2.94E-1, 1.98E-2],
                            [4.34E0, 5.9E-3, -1.99E0, -3.05E-1],
                            [-9.72E0, -2.48E-1, 4.32, 8.97E-1],
                            [7.54E0, 2.87E-1, -3E0, -7.31E-1]]




def Ft_aircooler(Thi, Tho, Tci, Tco, Ntp=1, rows=1):
    r'''Calculates log-mean temperature difference correction factor for
    a crossflow heat exchanger, as in an Air Cooler. Method presented in [1]_,
    fit to other's nonexplicit work. Error is < 0.1%. Requires number of rows
    and tube passes as well as stream temperatures.

    .. math::
        F_T = 1 - \sum_{i=1}^m \sum_{k=1}^n a_{i,k}(1-r_{1,m})^k\sin(2i\arctan R)

        R = \frac{T_{hi} - T_{ho}}{T_{co}-T_{ci}}

        r_{1,m} = \frac{\Delta T_{lm}}{T_{hi} - T_{ci}}

    Parameters
    ----------
    Thi : float
        Temperature of hot fluid in [K]
    Tho : float
        Temperature of hot fluid out [K]
    Tci : float
        Temperature of cold fluid in [K]
    Tco : float
        Temperature of cold fluid out [K]
    Ntp : int
        Number of passes the tubeside fluid will flow through [-]
    rows : int
        Number of rows of tubes [-]

    Returns
    -------
    Ft : float
        Log-mean temperature difference correction factor [-]

    Notes
    -----
    This equation assumes that the hot fluid is tubeside, as in the case of air
    coolers. The model is not symmetric, so ensure to switch around the inputs
    if using this function for other purposes.

    This equation appears in [1]_. It has been verified.
    For some cases, approximations are made to match coefficients with the
    number of tube passes and rows provided.
    16 coefficients are used for each case; 8 cases are considered:

    * 1 row 1 pass
    * 2 rows 1 pass
    * 2 rows 2 passes
    * 3 rows 1 pass
    * 3 rows 3 passes
    * 4 rows 1 pass
    * 4 rows 2 passes
    * 4 rows 4 passes

    Examples
    --------
    >>> Ft_aircooler(Thi=125., Tho=45., Tci=25., Tco=95., Ntp=1, rows=4)
    0.5505093604092708

    References
    ----------
    .. [1] Roetzel, W., and F. J. L. Nicole. "Mean Temperature Difference for
       Heat Exchanger Design-A General Approximate Explicit Equation." Journal
       of Heat Transfer 97, no. 1 (February 1, 1975): 5-8.
       doi:10.1115/1.3450288
    '''
    dTlm = LMTD(Thi=Thi, Tho=Tho, Tci=Tci, Tco=Tco)
    rlm = dTlm/(Thi-Tci)
    R = (Thi-Tho)/(Tco-Tci)
#    P = (Tco-Tci)/(Thi-Tci)

    if Ntp == 1 and rows == 1:
        coefs = _crossflow_1_row_1_pass
    elif Ntp == 1 and rows == 2:
        coefs = _crossflow_2_rows_1_pass
    elif Ntp == 1 and rows == 3:
        coefs = _crossflow_3_rows_1_pass
    elif Ntp == 1 and rows == 4:
        coefs = _crossflow_4_rows_1_pass
    elif Ntp == 1 and rows > 4:
        # A reasonable assumption
        coefs = _crossflow_4_rows_1_pass
    elif Ntp == 2 and rows == 2:
        coefs = _crossflow_2_rows_2_pass
    elif Ntp == 3 and rows == 3:
        coefs = _crossflow_3_rows_3_pass
    elif Ntp == 4 and rows == 4:
        coefs = _crossflow_4_rows_4_pass
    elif Ntp > 4 and rows > 4 and Ntp == rows:
        # A reasonable assumption
        coefs = _crossflow_4_rows_4_pass
    elif Ntp  == 2 and rows == 4:
        coefs = _crossflow_4_rows_2_pass
    else:
        # A bad assumption, but hey, gotta pick something.
        coefs = _crossflow_4_rows_2_pass
    tot = 0
    atanR = atan(R)
    cmps = range(len(coefs))
    for k in cmps:
        x0 = (1. - rlm)**(k + 1.)
        for i in cmps:
            tot += coefs[k][i]*x0*sin(2.*(i + 1.)*atanR)
    return 1. - tot


def air_cooler_noise_GPSA(tip_speed, power):
    r'''Calculates the noise generated by an air cooler bay with one fan 
    according to the GPSA handbook [1]_.    

    .. math::
        \text{PWL[dB(A)]} = 56 + 30\log_{10}\left( \frac{\text{tip speed}
        [m/min]}{304.8 [m/min]}\right) + 10\log_{10}( \text{power}[hp])
    
    Parameters
    ----------
    tip_speed : float
        Tip speed of the air cooler fan blades, [m/s]
    power : float
        Shaft power of single fan motor, [W]
        
    Returns
    -------
    noise : float
        Sound pressure level at 1 m from source, [dB(A)]

    Notes
    -----
    Internal units are in m/minute, and hp. 

    Examples
    --------
    Example problem from GPSA [1]_.
    
    >>> air_cooler_noise_GPSA(tip_speed=3177/minute, power=25.1*hp)
    100.53680477959792

    References
    ----------
    .. [1] GPSA. "Engineering Data Book, SI." 13th edition. Gas Processors 
       Suppliers Association (2012).
    '''
    tip_speed = tip_speed*minute # convert tip speed to m/minute
    power = power/hp # convert power from W to hp 
    return 56.0 + 30.0*log10(tip_speed/304.8) + 10.0*log10(power)


def air_cooler_noise_Mukherjee(tip_speed, power, fan_diameter, induced=False):
    r'''Calculates the noise generated by an air cooler bay with one fan 
    according to [1]_.    

    .. math::
        \text{SPL[dB(A)]} = 46 + 30\log_{10}\text{(tip speed)}[m/s] 
        + 10\log_{10}( \text{power}[hp]) - 20 \log10(D_{fan})
    
    Parameters
    ----------
    tip_speed : float
        Tip speed of the air cooler fan blades, [m/s]
    power : float
        Shaft power of single fan motor, [W]
    fan_diameter : float
        Diameter of air cooler fan, [m]
    induced : bool
        Whether the air cooler is forced air (False) or induced air (True), [-]

    Returns
    -------
    noise : float
        Sound pressure level at 1 m from source (p0=2E-5 Pa), [dB(A)]

    Notes
    -----
    Internal units are in m/minute, hp, and m.
    
    If the air cooler is induced, the sound pressure level is reduced by 3 dB.

    Examples
    --------    
    >>> air_cooler_noise_Mukherjee(tip_speed=3177/minute, power=25.1*hp, fan_diameter=4.267)
    99.11026329092925

    References
    ----------
    .. [1] Mukherjee, R., and Geoffrey Hewitt. Practical Thermal Design of
       Air-Cooled Heat Exchangers. New York: Begell House Publishers Inc.,U.S.,
       2007.
    '''
    noise = 46.0 + 30.0*log10(tip_speed) + 10.0*log10(power/hp) - 20.0*log10(fan_diameter)
    if induced:
        noise -= 3.0
    return noise


def h_Briggs_Young(m, A, A_min, A_increase, A_fin, A_tube_showing, 
                   tube_diameter, fin_diameter, fin_thickness, bare_length, 
                   rho, Cp, mu, k, k_fin):
    r'''Calculates the air side heat transfer coefficient for an air cooler
    or other finned tube bundle with the formulas of Briggs and Young [1], [2]_
    [3]_.
    
    .. math::
        Nu = 0.134Re^{0.681} Pr^{0.33}\left(\frac{S}{h}\right)^{0.2}
        \left(\frac{S}{b}\right)^{0.1134}
        
    Parameters
    ----------
    m : float
        Mass flow rate of air across the tube bank, [kg/s]
    A : float
        Surface area of combined finned and non-finned area exposed for heat
        transfer, [m^2]
    A_min : float
        Minimum air flow area, [m^2]
    A_increase : float
        Ratio of actual surface area to bare tube surface area
        :math:`A_{increase} = \frac{A_{tube}}{A_{bare, total/tube}}`, [-]
    A_fin : float
        Surface area of all fins in the bundle, [m^2]
    A_tube_showing : float
        Area of the bare tube which is exposed in the bundle, [m^2]
    tube_diameter : float
        Diameter of the bare tube, [m]
    fin_diameter : float
        Outer diameter of each tube after including the fin on both sides,
        [m]
    fin_thickness : float
        Thickness of the fins, [m]
    bare_length : float
        Length of bare tube between two fins 
        :math:`\text{bare length} = \text{fin interval} - t_{fin}`, [m]
    rho : float
        Average density of air across the tube bank, [kg/m^3]
    Cp : float
        Average heat capacity of air across the tube bank, [J/kg/K]
    mu : float
        Average viscosity of air across the tube bank, [Pa*s]
    k : float
        Average thermal conductivity of air across the tube bank, [W/m/K]
    k_fin : float
        Thermal conductivity of the fin, [W/m/K]
        
    Returns
    -------
    h_bare_tube_basis : float
        Air side heat transfer coefficient on a bare-tube surface area as if 
        there were no fins present basis, [W/K/m^2]

    Notes
    -----
    The limits on this equation are :math:`1000 < Re < `8000`, 
    11.13 mm :math:`< D_o < ` 40.89 mm, 1.42 mm < fin height < 16.57 mm,
    0.33 mm < fin thickness < 2.02 mm, 1.30 mm < fin pitch < 4.06 mm, and 
    24.49 mm < normal pitch < 111 mm.
    
    Examples
    --------
    >>> AC = AirCooledExchanger(tube_rows=4, tube_passes=4, tubes_per_row=20, tube_length=3, 
    ... tube_diameter=1*inch, fin_thickness=0.000406, fin_density=1/0.002309,
    ... pitch_normal=.06033, pitch_parallel=.05207,
    ... fin_height=0.0159, tube_thickness=(.0254-.0186)/2,
    ... bundles_per_bay=1, parallel_bays=1, corbels=True)
    
    >>> h_Briggs_Young(m=21.56, A=AC.A, A_min=AC.A_min, A_increase=AC.A_increase, A_fin=AC.A_fin,
    ... A_tube_showing=AC.A_tube_showing, tube_diameter=AC.tube_diameter,
    ... fin_diameter=AC.fin_diameter, bare_length=AC.bare_length,
    ... fin_thickness=AC.fin_thickness,
    ... rho=1.161, Cp=1007., mu=1.85E-5, k=0.0263, k_fin=205)
    1422.8722403237716

    References
    ----------
    .. [1] Briggs, D.E., and Young, E.H., 1963, "Convection Heat Transfer and
       Pressure Drop of Air Flowing across Triangular Banks of Finned Tubes",
       Chemical Engineering Progress Symp., Series 41, No. 59. Chem. Eng. Prog.
       Symp. Series No. 41, "Heat Transfer - Houston".
    .. [2] Mukherjee, R., and Geoffrey Hewitt. Practical Thermal Design of 
       Air-Cooled Heat Exchangers. New York: Begell House Publishers Inc.,U.S.,
       2007.
    .. [3] Kroger, Detlev. Air-Cooled Heat Exchangers and Cooling Towers: 
       Thermal-Flow Performance Evaluation and Design, Vol. 1. Tulsa, Okl:
       PennWell Corp., 2004.
    '''
    fin_height = 0.5*(fin_diameter - tube_diameter)
    
    V_max = m/(A_min*rho)
    
    Re = Reynolds(V=V_max, D=tube_diameter, rho=rho, mu=mu)
    Pr = Prandtl(Cp=Cp, mu=mu, k=k)

    Nu = 0.134*Re**0.681*Pr**(1/3.)*(bare_length/fin_height)**0.2*(bare_length/fin_thickness)**0.1134

    h = k/tube_diameter*Nu
    efficiency = fin_efficiency_Kern_Kraus(Do=tube_diameter, D_fin=fin_diameter,
                                           t_fin=fin_thickness, k_fin=k_fin, h=h)
    h_total_area_basis = (efficiency*A_fin + A_tube_showing)/A*h
    h_bare_tube_basis = h_total_area_basis*A_increase
        
    return h_bare_tube_basis


def h_ESDU_highfin_staggered(m, A, A_min, A_increase, A_fin,
                             A_tube_showing, tube_diameter,
                             fin_diameter, fin_thickness, bare_length,
                             pitch_parallel, pitch_normal, 
                             rho, Cp, mu, k, k_fin):
    r'''Calculates the air side heat transfer coefficient for an air cooler
    or other finned tube bundle with the formulas of [2]_ as presented in [1]_.
        
    Parameters
    ----------
    m : float
        Mass flow rate of air across the tube bank, [kg/s]
    A : float
        Surface area of combined finned and non-finned area exposed for heat
        transfer, [m^2]
    A_min : float
        Minimum air flow area, [m^2]
    A_increase : float
        Ratio of actual surface area to bare tube surface area
        :math:`A_{increase} = \frac{A_{tube}}{A_{bare, total/tube}}`, [-]
    A_fin : float
        Surface area of all fins in the bundle, [m^2]
    A_tube_showing : float
        Area of the bare tube which is exposed in the bundle, [m^2]
    tube_diameter : float
        Diameter of the bare tube, [m]
    fin_diameter : float
        Outer diameter of each tube after including the fin on both sides,
        [m]
    fin_thickness : float
        Thickness of the fins, [m]
    bare_length : float
        Length of bare tube between two fins 
        :math:`\text{bare length} = \text{fin interval} - t_{fin}`, [m]
    pitch_parallel : float
        Distance between tube center along a line parallel to the flow;
        has been called `longitudinal` pitch, `pp`, `s2`, `SL`, and `p2`, [m]
    pitch_normal : float
        Distance between tube centers in a line 90° to the line of flow;
        has been called the `transverse` pitch, `pn`, `s1`, `ST`, and `p1`, [m]
    rho : float
        Average density of air across the tube bank, [kg/m^3]
    Cp : float
        Average heat capacity of air across the tube bank, [J/kg/K]
    mu : float
        Average viscosity of air across the tube bank, [Pa*s]
    k : float
        Average thermal conductivity of air across the tube bank, [W/m/K]
    k_fin : float
        Thermal conductivity of the fin, [W/m/K]
        
    Returns
    -------
    h_bare_tube_basis : float
        Air side heat transfer coefficient on a bare-tube surface area as if 
        there were no fins present basis, [W/K/m^2]

    Notes
    -----
    Two factors `F1` and `F2` should be included as well.
    
    Examples
    --------
    >>> AC = AirCooledExchanger(tube_rows=4, tube_passes=4, tubes_per_row=20, tube_length=3, 
    ... tube_diameter=1*inch, fin_thickness=0.000406, fin_density=1/0.002309,
    ... pitch_normal=.06033, pitch_parallel=.05207,
    ... fin_height=0.0159, tube_thickness=(.0254-.0186)/2,
    ... bundles_per_bay=1, parallel_bays=1, corbels=True)
    
    >>> h_ESDU_highfin_staggered(m=21.56, A=AC.A, A_min=AC.A_min, A_increase=AC.A_increase, A_fin=AC.A_fin,
    ... A_tube_showing=AC.A_tube_showing, tube_diameter=AC.tube_diameter,
    ... fin_diameter=AC.fin_diameter, bare_length=AC.bare_length,
    ... fin_thickness=AC.fin_thickness,
    ... pitch_normal=AC.pitch_normal, pitch_parallel=AC.pitch_parallel, 
    ... rho=1.161, Cp=1007., mu=1.85E-5, k=0.0263, k_fin=205)
    1390.888918049757

    References
    ----------
    .. [1] Hewitt, G. L. Shires, T. Reg Bott G. F., George L. Shires, and T.
       R. Bott. Process Heat Transfer. 1st edition. Boca Raton: CRC Press, 
       1994.
    .. [2] "High-Fin Staggered Tube Banks: Heat Transfer and Pressure Drop for
       Turbulent Single Phase Gas Flow." ESDU 86022 (October 1, 1986). 
    '''
    fin_height = 0.5*(fin_diameter - tube_diameter)

    V_max = m/(A_min*rho)
    Re = Reynolds(V=V_max, D=tube_diameter, rho=rho, mu=mu)
    Pr = Prandtl(Cp=Cp, mu=mu, k=k)
    Nu = 0.242*Re**0.658*(bare_length/fin_height)**0.297*(pitch_normal/pitch_parallel)**-0.091*Pr**(1/3.)
    h = k/tube_diameter*Nu

    efficiency = fin_efficiency_Kern_Kraus(Do=tube_diameter, D_fin=fin_diameter, t_fin=fin_thickness, k_fin=k_fin, h=h)
    h_total_area_basis = (efficiency*A_fin + A_tube_showing)/A*h
    h_bare_tube_basis =  h_total_area_basis*A_increase
    return h_bare_tube_basis


