from astropy.time import Time

import os
import glob

import csv


class LocalFrame:
    def __init__(self, lat, lon, height):
        self.lat = lat
        self.lon = lon
        self.height = height


class ConfRead:
    def __init__(self, file):
        with open(file) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',',
                                        fieldnames=['Satnum', 'H0', 'nPontos'])
            csv_reader.__next__()
            satnum = []
            h0 = []
            hrf = []
            for row in csv_reader:
                satnum.append(int(row["Satnum"]))
                h0.append(Time( row["H0"] , format='isot'))
                hrf.append(int(row["nPontos"]))
        self.satnum = satnum
        self.h0 = h0
        self.hrf = hrf


class RcsRead:
    def __init__(self, file):
        with open(file) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',',
                                        fieldnames=['NORAD_CAT_ID', 'RCS'])
            csv_reader.__next__()
            satnum = []
            rcs = []

            for row in csv_reader:
                satnum.append(int(row["NORAD_CAT_ID"]))
                rcs.append(float(row["RCS"]))

        self.satnum = satnum
        self.rcs = rcs


def writecsvconf(fname, nor, h0, npoint):
    try:
        with open(fname, 'w', newline='') as csvfile:
            fieldnames = ['Satnum', 'H0', 'nPontos']
            writer = csv.DictWriter(
                csvfile, delimiter=',', fieldnames=fieldnames)

            writer.writeheader()
            for i in range(0, len(nor)):
                writer.writerow(
                    {'Satnum': nor[i], 'H0': h0[i], 'nPontos': npoint[i]})

        csvfile.close()
    except IOError:
        print('error writing the file {}'.format(fname))
        return 1
    return 0


def writecsvdata(fname, satnum, sel_name, tle_epc, h0, dist_h0, h_min, point_min, dist_min,
                 hf, npoints, dist_hf, sel_rcs):
    try:
        with open(fname, 'w', newline='') as csvfile:
            fieldnames = ['NORAD_CAT_ID', 'OBJECT_NAME', 'RCS', 'TLEday', 'H0date', 'H0hour', 'D(H0)',
                          'H(dmin)', 'point(dmin)', 'dmin', 'HF', 'nPoints', 'd(HF)']
            writer = csv.DictWriter(
                csvfile, delimiter=',', fieldnames=fieldnames)

            writer.writeheader()

            for i in range(0, len(satnum)):
                writer.writerow({'NORAD_CAT_ID': satnum[i],
                                 'OBJECT_NAME': sel_name[i],                                
                                 'RCS': sel_rcs[i],
                                 'TLEday': tle_epc[i],
                                 'H0date': h0[i][0:10],
                                 'H0hour': h0[i][11:],
                                 'D(H0)': dist_h0[i],
                                 'H(dmin)': h_min[i],
                                 'point(dmin)': point_min[i],
                                 'dmin': dist_min[i],
                                 'HF': hf[i],
                                 'nPoints': npoints[i],
                                 'd(HF)': dist_hf[i]})

        csvfile.close()
    except IOError:
        print('error writing the file {}'.format(fname))
        return 1
    return 0


def write2csvdata(fname, satnum, sel_name, tle_epc, h0, dist_h0, h_min, point_min, dist_min,
                 hf, npoints, dist_hf, json_data, sel_rcs):
    try:
        with open(fname, 'w', newline='') as csvfile:
            fieldnames = ['NORAD_CAT_ID', 'OBJECT_NAME', 'OBJECT_TYPE', 'EPOCH', 'INCLINATION',
                          'PERIOD', 'APOAPSIS', 'PERIAPSIS', 'RCS', 'TLEday', 'H0date', 'H0hour', 'D(H0)',
                          'H(dmin)', 'point(dmin)', 'dmin', 'HF', 'nPoints', 'd(HF)']
            writer = csv.DictWriter(
                csvfile, delimiter=',', fieldnames=fieldnames)

            writer.writeheader()
            #colunag_id = list(map(int, [row["NORAD_CAT_ID"] for row in json_data]))
            for i in range(0, len(satnum)):
                #idx_g = colunag_id.index(satnum[i])
                writer.writerow({'NORAD_CAT_ID': satnum[i],
                                 'OBJECT_NAME': sel_name[i],
                                 'OBJECT_TYPE': json_data[i]['OBJECT_TYPE'],
                                 'EPOCH': json_data[i]["EPOCH"],
                                 'INCLINATION': json_data[i]['INCLINATION'],
                                 'PERIOD': json_data[i]['PERIOD'],
                                 'APOAPSIS': json_data[i]['APOAPSIS'],
                                 'PERIAPSIS': json_data[i]['PERIAPSIS'],
                                 'RCS': sel_rcs[i],
                                 'TLEday': tle_epc[i],
                                 'H0date': h0[i][0:10],
                                 'H0hour': h0[i][11:],
                                 'D(H0)': dist_h0[i],
                                 'H(dmin)': h_min[i],
                                 'point(dmin)': point_min[i],
                                 'dmin': dist_min[i],
                                 'HF': hf[i],
                                 'nPoints': npoints[i],
                                 'd(HF)': dist_hf[i]})

        csvfile.close()
    except IOError:
        print('error writing the file {}'.format(fname))
        return 1
    return 0


class T32leFileRead:
    def __init__(self, fname):
        fileid = open(fname, 'r')
        tle_string = fileid.read()
        fileid.close()
        tle_lines = tle_string.strip().splitlines()
        lx = ['None', 'None', 'None']
        l = []
        for line in tle_lines:
            if line[0] not in '012':
                print('Erro: As linhas no arquivo TLE/3LE devem iniciar com os caracteres TLE: 1, 2 e 3LE: 0, 1, 2')
                break
            lx[int(line[0])] = line
            if int(line[0]) == 2:
                l.append(lx)
                lx = ['None', 'None', 'None']
        l0 = list(map(str, [row[0] for row in l]))
        l1 = list(map(str, [row[1] for row in l]))
        l2 = list(map(str, [row[2] for row in l]))
        self.l0 = l0
        self.l1 = l1
        self.l2 = l2


class TrnH0FileRead:
    # Esta classe ler todos os arquivos de trajetória da pasta e obtém h0 dos nomes
    def __init__(self, folder_name):
        # colect all file names in folder
        txt_files = glob.glob(folder_name + '/*.trn')

        sel_satnum = []
        sel_h0 = []
        sel_npoints = []
        trajet_all_1 = []

        # for i in range(0, len(txt_files) ): #len(txt_files)
        for filename in txt_files:
            h0dtxt = filename.split('-')
            h0hora = h0dtxt[4].split('T')

            poits = file_read(filename)

            sel_satnum.append(int(h0dtxt[1]))
            sel_h0.append(h0dtxt[2].replace("_", "-") +
                          ' ' + h0hora[0].replace("_", ":"))
            sel_npoints.append(len(poits)-1)

            trajet = []
            for j in range(1, len(poits)):  # ingnora a primeira linha
                line = poits[j].split(',')
                ddd = list(map(float, line))
                trajet.append(ddd)

            trajet_all_1.append(trajet)
        self.trajet_all = trajet_all_1
        self.satnum = sel_satnum
        self.h0 = sel_h0
        self.npoints = sel_npoints


def noradfileread(fname):
    fileid = open(fname, 'r')
    nr_string = fileid.read()
    fileid.close()
    norad = nr_string.strip().splitlines()
    del norad[0]
    satnum = list(map(int, norad))
    return satnum

def file_read(fname):
    fileid = open(fname, 'r')
    txt_string = fileid.read()
    fileid.close()
    list_string = txt_string.strip().splitlines()
    return list_string

def file_read_txt(fname):
    fileid = open(fname, 'r')
    txt_string = fileid.read()
    fileid.close()
    return txt_string

def writetrn(fname, trn):
    with open(fname, "wt") as fp:
        fp.write("1,{},1\n".format(len(trn)))
        for line in trn:
            fp.write("{:.3f},{:.3f},{:.3f}\n".format(
                line[0], line[1], line[2]))
    fp.close()
    return 0

# def writecsv(fname, dados):
#     with open(fname, "wt") as fp:
#         fp.write('NORAD;TLE;H0data;H0hora;D(H0);H(dmin);HR;dmin;HF;HRF;d(HF)\n')
#         for i in range(0, len(dados)):
#             fp.write("{};{};{};{};{:.3f};{};{};{:.3f};{};{};{:.3f}\n".format(
#                 dados[i][0], dados[i][1], dados[i][2], dados[i][3], dados[i][4], dados[i][5], dados[i][6], dados[i][7], dados[i][8], dados[i][9], dados[i][10]))

#     fp.close()
#     return 0

def writedots(fname, tempo, dist, pos):
    with open(fname, "wt") as fp:
        fp.write("#     Hora        D(m)        X(m)        Y(m)        Z(m)\n")
        for i in range(0, len(dist)):
            fp.write("{}    {}  {:.3f}  {:.3f}  {:.3f}  {:.3f}\n".format(
                i+1, tempo[i].value[11:], dist[i], pos[i][0], pos[i][1], pos[i][2]))
    fp.close()
    return 0

def writetle(fname, tles):
    with open(fname, "wt") as fp:
        for line in tles:
            fp.write(line)
    fp.close()
    return 0

def writesatnum(fname, satnum):
    with open(fname, "wt") as fp:
        fp.write("Satnum (NORAD ID)" + "\n")
        for line in satnum:
            fp.write(str(line) + "\n")
    fp.close()
    return 0

def dellfiles(file):
    py_files = glob.glob(file)
    err = 0
    for py_file in py_files:
        try:
            os.remove(py_file)
        except OSError as e:
            print(f"Error:{e.strerror}")
            err = e.strerror
    return err

def dellfile(file):
    err = 0
    try:
        os.remove(file)
    except OSError as e:
        print(f"Error:{e.strerror}: " + file)
        err = e.strerror
    return err

def read_json(file):
    err = 0
    try:
        os.remove(file)
    except OSError as e:
        print(f"Error:{e.strerror}: " + file)
        err = e.strerror
    return err

