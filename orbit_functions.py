from sgp4.api import SGP4_ERRORS

from astropy.coordinates import TEME, CartesianRepresentation  # CartesianDifferential
from astropy import units as u
from astropy.coordinates import ITRS
from astropy.time import Time

import pymap3d as pm

import os
import glob

class PropagInit:
    def __init__(self, satellite, lc, sample_time=1):
        self.satellite = satellite
        self.lc = lc
        self.sample_time = sample_time

        self.tempo = []
        self.traj = []
        self.dist = []
        self.hdmin = []
        self.dmin = []
        self.hrmin = []

    def orbitpropag(self, t_inic, n):
        tvar = t_inic

        enu_dv = []
        tv = []
        enu_pv = []

        tsample = self.sample_time

        hr = 0

        flagmin = True
        hdmin = 0
        dmin = 0
        hrmin = 0

        for i in range(0, n):
            error_code, teme_p, teme_v = self.satellite.sgp4(tvar.jd1, tvar.jd2)
            if error_code != 0:
                # raise RuntimeError(SGP4_ERRORS[error_code])
                print(" SGP4_ERRORS: {}\n".format(SGP4_ERRORS[error_code]))
                break
            teme_p = CartesianRepresentation(teme_p * u.km)
            teme = TEME(teme_p, obstime=tvar)  # ver diferença entre UT1 e UTC
            itrsp = teme.transform_to(ITRS(obstime=tvar))
            location = itrsp.earth_location
            # location.geodetic
            enu_p = pm.ecef2enu(1000 * location.x.value, 1000 * location.y.value, 1000 * location.z.value, self.lc.lat,
                                self.lc.lon, self.lc.height)
            enu_d = (enu_p[0] ** 2 + enu_p[1] ** 2 + enu_p[2] ** 2) ** 0.5
            enu_dv.append(enu_d)
            enu_pv.append(enu_p)
            tv.append(tvar)

            if (enu_dv[len(enu_dv) - 2] < enu_dv[len(enu_dv) - 1]) and flagmin:
                print('NORAD: {} dmin= {:.3f}'.format(self.satellite.satnum, enu_dv[len(enu_dv) - 2]))
                dmin = enu_dv[len(enu_dv) - 2]
                hdmin = tvar - tsample / (60 * 60 * 24)
                hrmin = hr - 1
                flagmin = False

            hr += 1
            tvar += tsample / (60 * 60 * 24)
            if hr == n:
                self.tempo.append(tv)
                self.traj.append(enu_pv)
                self.dist.append(enu_dv)
                self.hdmin.append(hdmin)
                self.dmin.append(dmin)
                self.hrmin.append(hrmin)
        return self

    def searchh0(self, t_inic, t_final, distmin, distmin2,  n):

        enu_dv = []
        tv = []
        enu_pv = []
        flagmin = True
        ntraj = 0

        tvar = t_inic

        hr = 0
        hrmin = 0

        for i in range(0, n):
            error_code, teme_p, teme_v = self.satellite.sgp4(tvar.jd1, tvar.jd2)
            if error_code != 0:
                # raise RuntimeError(SGP4_ERRORS[error_code])
                print(" SGP4_ERRORS: {}\n".format(SGP4_ERRORS[error_code]))
                break
            teme_p = CartesianRepresentation(teme_p * u.km)
            teme = TEME(teme_p, obstime=tvar)  # ver diferença entre UT1 e UTC
            itrsp = teme.transform_to(ITRS(obstime=tvar))
            location = itrsp.earth_location
            # location.geodetic
            enu_p = pm.ecef2enu(1000 * location.x.value, 1000 * location.y.value, 1000 * location.z.value, self.lc.lat,
                                self.lc.lon, self.lc.height)
            enu_d = (enu_p[0]**2 + enu_p[1]**2 + enu_p[2]**2)**0.5

            if enu_d > distmin:
                tsample = round(abs(enu_d - distmin)/10000+1)
                # print("sample = {}".format(tsample))
                if not flagmin:
                    flagmin = True
                    self.tempo.append(tv)
                    self.traj.append(enu_pv)
                    self.dist.append(enu_dv)
                    self.hdmin.append(hdmin)
                    self.dmin.append(dmin)
                    self.hrmin.append(hrmin)
                    tv = []
                    enu_pv = []
                    enu_dv = []
                hr = 0
                hrmin = 0
            else:
                tsample = self.sample_time
                tv.append(tvar)
                enu_dv.append(enu_d)
                enu_pv.append(enu_p)
                # print('{} {:.3f}'.format(tvar.value, enu_d))
                if (enu_dv[len(enu_dv)-2] < enu_dv[len(enu_dv)-1]) and flagmin:
                    dmin = enu_dv[len(enu_dv) - 2]
                    if dmin < distmin2:
                        hdmin = tvar - tsample / (60 * 60 * 24)
                        hrmin = hr - 1
                        flagmin = False
                        ntraj += 1
                        print('NORAD: {}, H0: {}, dmin= {:.3f}'.format(self.satellite.satnum, tv[0].value, dmin))
                    else:
                        tsample = 60*5

            hr += 1
            tvar += tsample / (60 * 60 * 24)

            if tvar > t_final: # Time.strptime('2021-8-25 19:00:00', '%Y-%m-%d %H:%M:%S'):
                print("fim loop")
                break
        return self


