import sys
import struct
import numpy
import os
import math


def read(name, type, nb, dictionary, file):

    if type == 'int32':
        #dictionary[name] = int.from_bytes(file.read(4), byteorder=sys.byteorder, signed=True)
        dictionary[name] = struct.unpack("i", file.read(4))[0]
    if type == 'float32':
        dictionary[name] = struct.unpack('f', file.read(4))[0]
    if type == 'uint8':
        l = []
        for i in range(nb):
            l.append(chr(struct.unpack('B', file.read(1))[0]))
        dictionary[name] = l
    if type == 'uint16':
        l = []
        for i in range(nb):
            l.append((struct.unpack('H', file.read(2)))[0])
        dictionary[name] = l
    if type == 'short':
        dictionary[name] = struct.unpack('h', file.read(2))[0]

    return dictionary

def read_header(file_name):

    file = open(file_name, "rb")

    i = [
            ['file_size', 'int32', 1], ['checksum_header', 'int32', 1], ['check_data', 'int32', 1],
            ['lenheader', 'int32', 1], ['versionid', 'float32', 1], ['filetype', 'int32', 1], ['filesubtype', 'int32', 1],
            ['datatype', 'int32', 1], ['sizeof', 'int32', 1], ['framewidth', 'int32', 1], ['frameheight', 'int32', 1],
            ['nframesperstim', 'int32', 1], ['nstimuli', 'int32', 1], ['initialxbinfactor', 'int32', 1],
            ['initialybinfactor', 'int32', 1],['xbinfactor', 'int32', 1], ['ybinfactor', 'int32', 1],
            ['username', 'uint8', 32],['recordingdate', 'uint8', 16],['x1roi', 'int32', 1],
            ['y1roi', 'int32', 1], ['x2roi', 'int32', 1], ['y2roi', 'int32', 1],['stimoffs', 'int32', 1],
            ['stimsize', 'int32', 1], ['frameoffs', 'int32', 1], ['framesize', 'int32', 1], ['refoffs', 'int32', 1],
            ['refsize', 'int32', 1], ['refwidth', 'int32', 1], ['refheight', 'int32', 1], ['whichblocks', 'uint16', 16],
            ['whichframe', 'uint16', 16], ['loclip', 'int32', 1], ['hiclip', 'int32', 1], ['lopass', 'int32', 1],
            ['hipass', 'int32', 1], ['operationsperformed', 'uint8', 64], ['magnifiaction', 'float32', 1],
            ['gain', 'uint16', 1], ['wavelength', 'uint16', 1], ['exposuretime', 'int32', 1], ['nrepetitions', 'int32', 1],
            ['acquisitiondelay', 'int32', 1], ['interstiminterval', 'int32', 1], ['creationdate', 'uint8', 16],
            ['datafilename', 'uint8', 64], ['orareserved', 'uint8', 256]
        ]

    dic = {}
    for x in i:
        dic = read(name=x[0], type=x[1], nb=x[2], dictionary=dic, file=file)

    if dic['filesubtype'] == 13:
        i = [
                ["includesrefframe", "int32", 1], ["temp", "uint8", 128], ["ntrials", "int32", 1],
                ["scalefactors", "int32", 1], ["cameragain", "short", 1], ["ampgain", "short", 1],
                ["samplingrate", "short", 1], ["average", "short", 1], ["exposuretime", "short", 1],
                ["samplingaverage", "short", 1], ["presentaverage", "short", 1], ["framesperstim", "short", 1],
                ["trialsperblock", "short", 1], ["sizeofanalogbufferinfbyteorder=sys.byteorderrames", "short", 1],
                ["cameratrials", "short", 1], ["filler", "uint8", 106], ["dyedaqreserved", "uint8", 106]
            ]
        for x in i:
            dic = read(name=x[0], type=x[1], nb=x[2], dictionary=dic, file=file)
        #nottested
        #  p.listofstimuli=temp(1:max(find(temp~=0)))';  % up to first non-zero stimulus
        dic["listofstimuli"] = dic["temp"][0:numpy.argwhere(x!=0).max(0)]
    else:
        i = [
                ["includesrefframe", "int32", 1], ["listofstimuli", "uint8", 256], ["nvideoframesperdataframe", "int32", 1],
                ["ntrials", "int32", 1], ["scalefactor", "int32", 1], ["meanampgain", "float32", 1],
                ["meanampdc", "float32", 1], ["vdaqreserved", "uint8", 256]
            ]
        for x in i:
            dic = read(name=x[0], type=x[1], nb=x[2], dictionary=dic, file=file)
    i = [["user", "uint8", 256], ["comment", "uint8", 256], ["refscalefactor", "int32", 1]]
    for x in i:
        dic = read(name=x[0], type=x[1], nb=x[2], dictionary=dic, file=file)
    dic["actuallength"] = os.stat(file_name).st_size
    file.close()

    return dic


def load(*arg):

    # file(s) name(s) can  be one (or multiple string)
    nblocks = len(arg)
    header = read_header(arg[0])
    nstim = header['nstimuli']
    ni = header['framewidth']
    nj = header['frameheight']
    nfr = header['nframesperstim']
    lenh = header['lenheader']
    framesize = header['framesize']
    filesize = header['file_size']
    dtype = header['datatype']
    gain = header['meanampgain']
    dc = header['meanampdc']
    scalefactor = header['scalefactor']

    # [["dtype","nbytes","datatype","type_out"],[...]]
    l = [
            [11, 1, "uchar", "uint8","B"], [12, 2, "ushort", "uint16", "H"],
            [13, 4, "ulong", "uint32","I"], [14, 4, "float", "single", "f"]
        ]

    for i in l:
        if dtype == i[0]:
            nbytes, datatype, type_out, struct_type = i[1], i[2], i[3], i[4]

    if framesize != ni * nj * nbytes:
        print("BAD HEADER!!! framesize does not match framewidth*frameheight*nbytes!")
        framesize = ni * nj * nbytes
    if (filesize - lenh) > (framesize * nfr * nstim):
        nfr2 = nfr + 1
        includesrefframe = True
    else:
        nfr2 = nfr
        includesrefframe = False
    
    nbin = nblocks
    conds = [i for i in range(1, nstim + 1)]
    ncond = len(conds)
    data = [[[numpy.zeros((ni, nj, nfr), type_out)] for x in range(ncond)] for i in range(nbin)]
    for k in range(1, nbin + 1):
        bin = numpy.arange(math.floor((k - 1 / nbin * nblocks) + 1), math.floor((k / nbin * nblocks) + 1))
        sbin = bin.size
        for j in range(1, sbin + 1):
            file = open(arg[int((bin[j - 1] - 1))], 'rb')
            for i in range(1, ncond + 1):

                framestart = conds[i - 1] * nfr2 - nfr
                offset = framestart * ni * nj * nbytes + lenh
                file.seek(offset, 0)

                a = [(struct.unpack(struct_type, file.read(nbytes)))[0] for m in range(ni * nj * nfr)]
                a = numpy.reshape(numpy.array(a, dtype=type_out, order='F'), (ni * nj, nfr), order='F')
                a = numpy.reshape(a, (ni, nj, nfr), order='F')
                
                if includesrefframe:
                        #not tested
                        framestart = (conds[i]-1)*nfr2
                        offset = framestart*ni*nj*nbytes + lenh

                        file.seek(offset)

                        ref = [(struct.unpack(struct_type, file.read(nbytes)))[0] for m in range(ni * nj)]
                        ref = numpy.array(ref, dtype=type_out)
                        for y in range(len(ref)):
                            ref[y] *= scalefactor
                        ref = numpy.reshape(ref, (ni, nj))
                        b = numpy.tile(ref, [1, 1, nfr])
                        for y in range(len(a)):
                            b.append([])
                            for x in range(len(a[y])):
                                b[y+1].append([])
                                for frame in range(len(a[y][x])):
                                    b[y+1][x][frame] = (a[y][x][frame]/gain) - (scalefactor*dc/gain)
                        a = b
                if sbin == 1:
                    data[k - 1][i - 1] = a
                else:
                    #not tested
                    for y in range(len(a)):
                        for x in range(len(a[y])):
                            a[y][x] /= sbin
                    data[k - 1][i - 1] = data[k - 1][i - 1] + a / sbin

            file.close()

    ### data format [block][stim][width][height][frame]]
    ### data structure should be [block][stim][frame][width][height] in order to be easy to use with neo
    ### each file is a block
    ### each stim could be a segment
    ### then an image sequence [frame][width][height]
    ### image need to be rotated

    # changing order of data for compatibility
    # [block][stim][width][height][frame]]
    # to
    # [block][stim][frame][width][height]

    for block in range(len(data)):
        for stim in range(len(data[block])):
            a = []
            for frame in range(header['nframesperstim']):
                a.append([])
                for width in range(len(data[block][stim])):
                    a[frame].append([])
                    for height in range(len(data[block][stim][width])):
                        a[frame][width].append(data[block][stim][width][height][frame])
                # rotation of data to be the same as thomas deneux screenshot
                a[frame] = numpy.rot90(numpy.fliplr(a[frame]))
            data[block][stim] = a

    return data, header
