# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2016, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.'''

from __future__ import division
from math import log, exp, sqrt
from ht import *
import numpy as np
from numpy.testing import assert_allclose
import pytest
from random import uniform, randint


### TODO hx requires testing, but perhaps first improvement
def test_Ntubes_Perrys():
    Nt_perry = [[Ntubes_Perrys(DBundle=1.184, Ntp=i, do=.028, angle=j) for i in [1,2,4,6]] for j in [30, 45, 60, 90]]
    Nt_values = [[1001, 973, 914, 886], [819, 803, 784, 769], [1001, 973, 914, 886], [819, 803, 784, 769]]
    assert_allclose(Nt_perry, Nt_values)
#    angle = 30 or 60 and ntubes = 1.5 raise exception

    with pytest.raises(Exception):
        Ntubes_Perrys(DBundle=1.184, Ntp=5, do=.028, angle=30)
    with pytest.raises(Exception):
        Ntubes_Perrys(DBundle=1.184, Ntp=5, do=.028, angle=45)


def test_Ntubes_VDI():
    VDI_t = [[Ntubes_VDI(DBundle=1.184, Ntp=i, do=.028, pitch=.036, angle=j) for i in [1,2,4,6,8]] for j in [30, 45, 60, 90]]
    VDI_values = [[983, 966, 929, 914, 903], [832, 818, 790, 778, 769], [983, 966, 929, 914, 903], [832, 818, 790, 778, 769]]
    assert_allclose(VDI_t, VDI_values)
    with pytest.raises(Exception):
        Ntubes_VDI(DBundle=1.184, Ntp=5, do=.028, pitch=.036, angle=30)
    with pytest.raises(Exception):
        Ntubes_VDI(DBundle=1.184, Ntp=2, do=.028, pitch=.036, angle=40)

    # TODO: Phadke

def test_Ntubes_HEDH():
    Ntubes_HEDH_c = [Ntubes_HEDH(DBundle=1.200-.008*2, do=.028, pitch=.036, angle=i) for i in [30, 45, 60, 90]]
    assert_allclose(Ntubes_HEDH_c, [928, 804, 928, 804])
    with pytest.raises(Exception):
        Ntubes_HEDH(DBundle=1.200-.008*2, do=.028, pitch=.036, angle=20)

def test_Ntubes():
    methods = Ntubes(DBundle=1.2, do=0.025, AvailableMethods=True)
    Ntubes_calc = [Ntubes(DBundle=1.2, do=0.025, Method=i) for i in methods]
    assert Ntubes_calc == [1285, 1272, 1340, 1297, None]

    assert_allclose(Ntubes(DBundle=1.2, do=0.025), 1285)

    with pytest.raises(Exception):
        Ntubes(DBundle=1.2, do=0.025, Method='failure')


def test_D_for_Ntubes_VDI():
    D_VDI =  [[D_for_Ntubes_VDI(Nt=970, Ntp=i, do=0.00735, pitch=0.015, angle=j) for i in [1, 2, 4, 6, 8]] for j in [30, 60, 45, 90]]
    D_VDI_values = [[0.489981989464919, 0.5003600119829544, 0.522287673753684, 0.5311570964003711, 0.5377131635291736], [0.489981989464919, 0.5003600119829544, 0.522287673753684, 0.5311570964003711, 0.5377131635291736], [0.5326653264480428, 0.5422270203444146, 0.5625250342473964, 0.5707695340997739, 0.5768755899087357], [0.5326653264480428, 0.5422270203444146, 0.5625250342473964, 0.5707695340997739, 0.5768755899087357]]
    assert_allclose(D_VDI, D_VDI_values)

    with pytest.raises(Exception):
        D_for_Ntubes_VDI(Nt=970, Ntp=5., do=0.00735, pitch=0.015, angle=30.)
    with pytest.raises(Exception):
        D_for_Ntubes_VDI(Nt=970, Ntp=2., do=0.00735, pitch=0.015, angle=40.)


def test_effectiveness_NTU():
    # Counterflow
    for i in range(20):
        eff = uniform(0, 1)
        Cr = uniform(0, 1)
        units = NTU_from_effectiveness(effectiveness=eff, Cr=Cr, subtype='counterflow')
        eff_calc = effectiveness_from_NTU(NTU=units, Cr=Cr, subtype='counterflow')
        assert_allclose(eff, eff_calc)
    # Case with Cr = 1
    NTU = NTU_from_effectiveness(effectiveness=.9, Cr=1, subtype='counterflow')
    assert_allclose(NTU, 9)
    e = effectiveness_from_NTU(NTU=9, Cr=1, subtype='counterflow')
    assert_allclose(e, 0.9)
        
        
    # Parallel
    for i in range(20):
        Cr = uniform(0, 1)
        eff = uniform(0, 1./(Cr + 1.)*(1-1E-7))
        units = NTU_from_effectiveness(effectiveness=eff, Cr=Cr, subtype='parallel')
        eff_calc = effectiveness_from_NTU(NTU=units, Cr=Cr, subtype='parallel')
        assert_allclose(eff, eff_calc)
        
    with pytest.raises(Exception):
        Cr = 0.6
        NTU_from_effectiveness(effectiveness=0.62500001, Cr=Cr, subtype='parallel')
        
        
    # Crossflow, Cmin mixed, Cmax unmixed
    
    for i in range(20):
        Cr = uniform(0, 1)
        eff = uniform(0, (1 - exp(-1/Cr))*(1-1E-7))
        N = NTU_from_effectiveness(eff, Cr=Cr, subtype='crossflow, mixed Cmin')
        eff_calc = effectiveness_from_NTU(N, Cr=Cr, subtype='crossflow, mixed Cmin')
        assert_allclose(eff, eff_calc)
        
    with pytest.raises(Exception):
        Cr = 0.7
        NTU_from_effectiveness(0.760348963559, Cr=Cr, subtype='crossflow, mixed Cmin')
        
            
    # Crossflow, Cmax mixed, Cmin unmixed
    for i in range(20):
        Cr = uniform(0, 1)
        eff = uniform(0, (exp(Cr) - 1)*exp(-Cr)/Cr-1E-5)
        N = NTU_from_effectiveness(eff, Cr=Cr, subtype='crossflow, mixed Cmax')
        eff_calc = effectiveness_from_NTU(N, Cr=Cr, subtype='crossflow, mixed Cmax')
        assert_allclose(eff, eff_calc)

    with pytest.raises(Exception):
        Cr = 0.7
        eff = 0.7201638517265581
        NTU_from_effectiveness(eff, Cr=Cr, subtype='crossflow, mixed Cmax')
        
        
    # Crossflow, this one needed a closed-form solver
    for i in range(100):
        Cr = uniform(0, 1)
        eff = uniform(0, 1)
        N = NTU_from_effectiveness(eff, Cr=Cr, subtype='crossflow')
        eff_calc = effectiveness_from_NTU(N, Cr=Cr, subtype='crossflow')
        assert_allclose(eff, eff_calc)

    # Shell and tube - this one doesn't have a nice effectiveness limit,
    # and it depends on the number of shells
    
    for i in range(20):
        Cr = uniform(0, 1)
        shells = randint(1, 10)
        eff_max = (-((-Cr + sqrt(Cr**2 + 1) + 1)/(Cr + sqrt(Cr**2 + 1) - 1))**shells + 1)/(Cr - ((-Cr + sqrt(Cr**2 + 1) + 1)/(Cr + sqrt(Cr**2 + 1) - 1))**shells)
        eff = uniform(0, eff_max-1E-5)
        N = NTU_from_effectiveness(eff, Cr=Cr, subtype=str(shells)+'S&T')
        eff_calc = effectiveness_from_NTU(N, Cr=Cr, subtype=str(shells)+'S&T')
        assert_allclose(eff, eff_calc)
        
    with pytest.raises(Exception):
        NTU_from_effectiveness(.99, Cr=.7, subtype='5S&T')
        
    # Easy tests
    effectiveness = effectiveness_from_NTU(NTU=5, Cr=0.7, subtype='crossflow, mixed Cmin')
    assert_allclose(effectiveness, 0.7497843941508544)
    NTU = NTU_from_effectiveness(effectiveness=effectiveness, Cr=0.7, subtype='crossflow, mixed Cmin')
    assert_allclose(NTU, 5)
    
    eff = effectiveness_from_NTU(NTU=5, Cr=0.7, subtype='crossflow, mixed Cmax')
    assert_allclose(eff, 0.7158099831204696)
    NTU = NTU_from_effectiveness(eff, Cr=0.7, subtype='crossflow, mixed Cmax')
    assert_allclose(5, NTU)
    
    eff = effectiveness_from_NTU(NTU=5, Cr=0, subtype='boiler')
    assert_allclose(eff, 0.9932620530009145)
    NTU = NTU_from_effectiveness(eff, Cr=0, subtype='boiler')
    assert_allclose(NTU, 5)
    
    with pytest.raises(Exception):
        effectiveness_from_NTU(NTU=5, Cr=1.01, subtype='crossflow, mixed Cmin')

    with pytest.raises(Exception):
        NTU_from_effectiveness(effectiveness=.2, Cr=1.01, subtype='crossflow, mixed Cmin')
    
    
def test_effectiveness_NTU_method():
    ans_known = {'Q': 192850.0, 'Thi': 130, 'Cmax': 9672.0, 'Tho': 110.06100082712986, 'Cmin': 2755.0, 'NTU': 1.1040839095588, 'Tco': 85, 'Tci': 15, 'Cr': 0.2848428453267163, 'effectiveness': 0.6086956521739131, 'UA': 3041.751170834494}
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tci=15, Tco=85, Tho=110.06100082712986)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tci=15, Tco=85, Thi=130)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]

    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Thi=130, Tho=110.06100082712986, Tci=15)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Thi=130, Tho=110.06100082712986, Tco=85)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]

    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tco=85, Tho=110.06100082712986, UA=3041.751170834494)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tci=15, Thi=130, UA=3041.751170834494)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tci=15, Tho=110.06100082712986, UA=3041.751170834494)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tco=85, Thi=130, UA=3041.751170834494)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tci=15, Tco=85, Tho=110.06100082712986, UA=3041.751170834494)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]
    ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tco=85, Thi=130, Tho=110.06100082712986, UA=3041.751170834494)
    [assert_allclose(ans_known[i], ans[i]) for i in ans_known.keys()]

    with pytest.raises(Exception):
        # Test raising an error with only on set of stream information 
        effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Thi=130, Tho=110.06100082712986, UA=3041.751170834494)
        
    with pytest.raises(Exception):
        # Inconsistent hot and cold temperatures and heat capacity ratios
        effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Thi=130, Tho=110.06100082712986, Tco=85, Tci=5)

    with pytest.raises(Exception):
        # Calculate UA, but no code side temperature information given
        effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Thi=130, Tho=110.06100082712986)
        
    with pytest.raises(Exception):
        # Calculate UA, but no hot side temperature information given
        effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype='crossflow, mixed Cmax', Tci=15, Tco=85)
        
        
def test_F_LMTD_Fakheri():
    '''Number of tube passes must be a multiple of 2N for correlation to work.
    N can be 1.

    Example from http://excelcalculations.blogspot.ca/2011/06/lmtd-correction-factor.html 
    spreadsheet file which Bowman et al (1940).
    This matches for 3, 6, and 11 shell passes perfectly.

    This also matches that from the sheet: 
    http://www.mhprofessional.com/getpage.php?c=0071624082_download.php&cat=113
    '''    
    F_calc = F_LMTD_Fakheri(Tci=15, Tco=85, Thi=130, Tho=110, shells=1)
    assert_allclose(F_calc, 0.9438358829645933)
    
    # R = 1 check
    F_calc = F_LMTD_Fakheri(Tci=15, Tco=35, Thi=130, Tho=110, shells=1)
    assert_allclose(F_calc, 0.9925689447100824)
    
    for i in range(1, 10):
        ans = effectiveness_NTU_method(mh=5.2, mc=1.45, Cph=1860., Cpc=1900, subtype=str(i)+'S&T', Tci=15, Tco=85, Thi=130)
        dTlm = LMTD(Thi=130, Tho=110.06100082712986,  Tci=15, Tco=85)
        F_expect = ans['Q']/ans['UA']/dTlm
        
        F_calc = F_LMTD_Fakheri(Tci=15, Tco=85, Thi=130, Tho=110.06100082712986, shells=i)
        assert_allclose(F_expect, F_calc)
        F_calc = F_LMTD_Fakheri(Thi=15, Tho=85, Tci=130, Tco=110.06100082712986, shells=i)
        assert_allclose(F_expect, F_calc)
