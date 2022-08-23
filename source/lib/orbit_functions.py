from sgp4.api import SGP4_ERRORS

from astropy.coordinates import TEME, CartesianRepresentation  # CartesianDifferential
from astropy import units as u
from astropy.coordinates import ITRS

import pymap3d as pm

from sgp4 import omm
from sgp4.api import Satrec
from astropy.time import Time
from astropy.time import TimeDelta
import numpy as np

class PropagInit:
    def __init__(self, orbital_elem, lc, sample_time=1):
        self.lc = lc
        self.sample_time = sample_time
        self.sample_fast = 30
        self.time_array = []
        self.enu = []
        self.az_el_r = []
        self.itrs = []
        self.geodetic = []
        satellite = Satrec()
        omm.initialize(satellite, orbital_elem)
        self.satellite = satellite

    def orbit_propag(self, h0, n, sample_time_v):
        time_array = np.linspace(h0,h0 + TimeDelta(sample_time_v*(n -1)* u.s),n)
        error_code, teme_p, teme_v = self.satellite.sgp4_array(time_array.jd1, time_array.jd2)
        teme_p = CartesianRepresentation(teme_p[:,0]*u.km, teme_p[:,1]*u.km, teme_p[:,2]*u.km)
        teme = TEME(teme_p, obstime=time_array)  
        itrsp = teme.transform_to(ITRS(obstime=time_array))
        location = itrsp.earth_location
        enu_p = pm.ecef2enu(u.km.to(u.m,location.x).value,
                    u.km.to(u.m,location.y).value,
                    u.km.to(u.m,location.z).value,
                    self.lc['lat'], self.lc['lon'], self.lc['height'])
        az_el_r = np.transpose(pm.enu2aer(enu_p[0],enu_p[1],enu_p[2]))
        enu_p = np.transpose(enu_p)
        #pm.ecef2geodetic(x, y, z)
        geodetic = np.transpose(location.geodetic)
        geocentric = np.transpose([location.x.value,location.y.value,location.z.value])   

        return time_array, enu_p, az_el_r, geodetic, geocentric

    def traj_calc(self, h0, n):
        time_array, enu_p, az_el_r, geodetic, geocentric = self.orbit_propag(h0, n, self.sample_time)        
  
        self.time_array.append(time_array)
        self.enu.append(enu_p)
        self.az_el_r.append(az_el_r)
        self.geodetic.append(geodetic)
        self.itrs.append(geocentric)
        return self

    def search2h0(self, t_inic, t_final, dist_max, dist_min):
        time_array_fast, enu_p, az_el_r, geodetic, geocentric = self.orbit_propag(t_inic,
                                                    1 + int((t_final-t_inic)/TimeDelta(self.sample_fast * u.s)),
                                                    self.sample_fast)                                                    
        enu_d = az_el_r[:,2]
        dist_dif = enu_d - dist_max
        idx1 = np.where(dist_dif[:-1] * dist_dif[1:] < 0 )[0] + 1      

        i = 0
        while i < len(idx1)-1:
            if dist_dif[idx1[i]]<0:
                #print( 'H0: {}, HF: {} \n'.format(time_array[idx1[i]], time_array[idx1[i+1]]))
                t_in = time_array_fast[idx1[i]] - TimeDelta(self.sample_fast * u.s)
                t_o = time_array_fast[idx1[i+1]]
                #print( 'H0: {}, HF: {} \n'.format(t_in, t_o))        
                time_array, enu_p, az_el_r, geodetic, geocentric = self.orbit_propag(t_in,
                                                            1 + int((t_o-t_in)/TimeDelta(self.sample_time * u.s)),
                                                            self.sample_time)

                #print( 'H0: {}, HF: {}, dmin: {}, d0: {}, df: {} \n'.format(time_array[0], time_array[-1], np.min(enu_d),enu_d[0],enu_d[-1] ))
                enu_d = az_el_r[:,2]
                idx = np.where(enu_d < dist_max)[0]
                time_array = time_array[idx]
                enu_p = enu_p[idx]
                az_el_r = az_el_r[idx]
                geodetic = geodetic[idx]
                geocentric = geocentric[idx]               
                
                d_min = np.min(enu_d)
                

                if d_min < dist_min:
                    self.time_array.append(time_array)
                    self.enu.append(enu_p)
                    self.az_el_r.append(az_el_r)
                    self.geodetic.append(geodetic)
                    self.itrs.append(geocentric)              
                i+=2
            else: 
                i+=1        

        return self

    # def orbitpropag(self, t_inic, n):
    # # Slowly, obsolete
    #     tvar = t_inic

    #     enu_dv = []
    #     tv = []
    #     enu_pv = []

    #     tsample = self.sample_time

    #     hr = 0

    #     flagmin = True
    #     hdmin = 0
    #     dmin = 0
    #     hrmin = 0

    #     for i in range(0, n):
    #         error_code, teme_p, teme_v = self.satellite.sgp4(tvar.jd1, tvar.jd2)
    #         if error_code != 0:
    #             # raise RuntimeError(SGP4_ERRORS[error_code])
    #             print(" SGP4_ERRORS: {}\n".format(SGP4_ERRORS[error_code]))
    #             break
    #         teme_p = CartesianRepresentation(teme_p * u.km)
    #         teme = TEME(teme_p, obstime=tvar)  # ver diferença entre UT1 e UTC
    #         itrsp = teme.transform_to(ITRS(obstime=tvar))
    #         location = itrsp.earth_location
    #         # location.geodetic
    #         enu_p = pm.ecef2enu(1000 * location.x.value, 1000 * location.y.value, 1000 * location.z.value, self.lc['lat'],
    #                             self.lc['lon'], self.lc['height'])
    #         enu_d = (enu_p[0] ** 2 + enu_p[1] ** 2 + enu_p[2] ** 2) ** 0.5
    #         enu_dv.append(enu_d)
    #         enu_pv.append(enu_p)
    #         tv.append(tvar)

    #         if (enu_dv[len(enu_dv) - 2] < enu_dv[len(enu_dv) - 1]) and flagmin:
    #             print('NORAD: {} dmin= {:.3f}'.format(self.satellite.satnum, enu_dv[len(enu_dv) - 2]))
    #             dmin = enu_dv[len(enu_dv) - 2]
    #             hdmin = tvar - tsample / (60 * 60 * 24)
    #             hrmin = hr - 1
    #             flagmin = False

    #         hr += 1
    #         tvar += tsample / (60 * 60 * 24)
    #         if hr == n:
    #             self.time_array.append(tv)
    #             self.enu.append(enu_pv)
    #             self.dist.append(enu_dv)
    #             self.hdmin.append(hdmin)
    #             self.dmin.append(dmin)
    #             self.hrmin.append(hrmin)
    #     return self

    # def searchh0(self, t_inic, t_final, distmin, distmin2,  n):
    # # Slowly, obsolete in process update
    #     enu_dv = []
    #     tv = []
    #     enu_pv = []
    #     flagmin = True
    #     ntraj = 0

    #     tvar = t_inic

    #     hr = 0
    #     hrmin = 0

    #     for i in range(0, n):
    #         error_code, teme_p, teme_v = self.satellite.sgp4(tvar.jd1, tvar.jd2)
    #         if error_code != 0:
    #             # raise RuntimeError(SGP4_ERRORS[error_code])
    #             print(" SGP4_ERRORS: {}\n".format(SGP4_ERRORS[error_code]))
    #             break
    #         teme_p = CartesianRepresentation(teme_p * u.km)
    #         teme = TEME(teme_p, obstime=tvar)  # ver diferença entre UT1 e UTC
    #         itrsp = teme.transform_to(ITRS(obstime=tvar))
    #         location = itrsp.earth_location
    #         # location.geodetic
    #         enu_p = pm.ecef2enu(1000 * location.x.value, 1000 * location.y.value, 1000 * location.z.value, self.lc['lat'],
    #                             self.lc['lon'], self.lc['height'])
    #         enu_d = (enu_p[0]**2 + enu_p[1]**2 + enu_p[2]**2)**0.5

    #         if enu_d > distmin:
    #             tsample = round(abs(enu_d - distmin)/10000+1)
    #             # print("sample = {}".format(tsample))
    #             if not flagmin:
    #                 flagmin = True
    #                 self.time_array.append(tv)
    #                 self.enu.append(enu_pv)
    #                 self.dist.append(enu_dv)
    #                 self.hdmin.append(hdmin)
    #                 self.dmin.append(dmin)
    #                 self.hrmin.append(hrmin)
    #                 tv = []
    #                 enu_pv = []
    #                 enu_dv = []
    #             hr = 0
    #             hrmin = 0
    #         else:
    #             tsample = self.sample_time
    #             tv.append(tvar)
    #             enu_dv.append(enu_d)
    #             enu_pv.append(enu_p)
    #             # print('{} {:.3f}'.format(tvar.value, enu_d))
    #             if (enu_dv[len(enu_dv)-2] < enu_dv[len(enu_dv)-1]) and flagmin:
    #                 dmin = enu_dv[len(enu_dv) - 2]
    #                 if dmin < distmin2:
    #                     hdmin = tvar - tsample / (60 * 60 * 24)
    #                     hrmin = hr - 1
    #                     flagmin = False
    #                     ntraj += 1
    #                     print('NORAD: {}, H0: {}, dmin= {:.3f}'.format(self.satellite.satnum, tv[0].value, dmin))
    #                 else:
    #                     tsample = 60*5

    #         hr += 1
    #         tvar += tsample / (60 * 60 * 24)

    #         if tvar > t_final: # Time.strptime('2021-8-25 19:00:00', '%Y-%m-%d %H:%M:%S'):
    #             print("fim loop")
    #             break
    #     return self


