import os, sys, shutil
import pandas as pd
import re
import logging
import time
import subprocess as subp
from scipy import io,signal
import numpy as np
import glob
import pdb
import argparse 
import natsort

import PIL
from PIL import Image,ImageSequence

from datetime import datetime
from dateutil.relativedelta import relativedelta


from skimage import filters
from sklearn import cluster
import nibabel as nb
import matplotlib
import logging


if (os.name == 'posix' and "DISPLAY" in os.environ) or (os.name == 'nt'):
    from matplotlib import pyplot as plt
    import seaborn as sns

elif os.name == 'posix' and "DISPLAY" not in os.environ:
    matplotlib.use('agg')
    from matplotlib import pyplot as plt
    import seaborn as sns

def matToTable(matPath, trigSuffix = '1', cyanSuffix = '3', uvSuffix = '4', ledSuffix = '12', pawSuffix = '13'):
    
    dct=io.loadmat(matPath)
   

    err=''

    try: 
        trigFlag = dct['head'+trigSuffix]['max'].squeeze() > 30000
        led1Flag = dct['head'+cyanSuffix]['max'].squeeze() > 30000
        led2Flag = dct['head'+uvSuffix]['max'].squeeze() > 30000
    except KeyError as e:
        logging.exception(e)
        return False, False, 0, e

    if trigFlag and led1Flag and led2Flag:
        chan1bin=dct['chan'+trigSuffix].squeeze() > 30000;
        findx=np.where(chan1bin)
        findx=findx[0]
        firstTrigStart=findx[0]
        lastTrigStart=findx[-249]

        if (lastTrigStart - firstTrigStart)/25000 > 550:

            #chan1xbin=chan1bin(findx(1):findx(end)+24749);
            #y=downsample(chan1xbin,250);

            chan3bin=np.squeeze(dct['chan'+cyanSuffix] > 30000)
            chan3bin=chan3bin[firstTrigStart:lastTrigStart+24999]
            chan3bin=chan3bin*2

            chan4bin=np.squeeze(dct['chan'+uvSuffix] > 30000)
            chan4bin=chan4bin[firstTrigStart:lastTrigStart+24999]






            if chan4bin.shape[0] > chan3bin.shape[0]:
                chan4bin = chan4bin[:chan3bin.shape[0]]
            elif chan4bin.shape[0] < chan3bin.shape[0]:
                chan3bin = chan3bin[:chan4bin.shape[0]]
        

            combineLED=chan3bin+chan4bin
            combineLEDDiff = np.diff(combineLED)
            combineLEDNonzeroDiff = np.where(combineLEDDiff)[0]

            compressCombineLED = combineLED[combineLEDNonzeroDiff]

            nonZeroTrigs = np.where(compressCombineLED)[0]

            opticalOrder = compressCombineLED[nonZeroTrigs]        
               

            consecutiveTriggers=np.sum(np.diff(opticalOrder.squeeze()) == 0) 

            opTableOptical=pd.DataFrame({'opticalOrder':opticalOrder})
        else:
            err = err+'#length of trig channel less than 550 sec#'
            opTableOptical = False
            consecutiveTriggers = 0
    else:
        err = err+'#trig/led1/led2 channel empty#'
        opTableOptical = False
        consecutiveTriggers = 0 

    try:
        ledStimFlag = dct['head'+ledSuffix]['max'].squeeze() > 30000
        pawStimFlag = dct['head'+pawSuffix]['max'].squeeze() > 30000
    except KeyError as e:
        logging.exception(e)
        return opTableOptical, False, consecutiveTriggers, e

    chan1=dct['chan'+trigSuffix].squeeze() 
    chan1DS=signal.resample_poly(chan1,1,25000) 
    chan1DSBin = chan1DS > 200

    opTableStim=pd.DataFrame({})


    if ledStimFlag and (chan1DSBin.sum() > 200):
        #print('Max val LED stim channel: ', dct['head12']['max'])
        chan12=dct['chan'+ledSuffix].squeeze()
        chan12DS=signal.resample_poly(chan12,960,1000000)
        chan12DSBin = chan12DS > 10000
        chan12DSBin=chan12DSBin.astype(int)

        chan12DSBin=chan12DSBin[:chan1DSBin.shape[0]]
        chan12DSBin=chan12DSBin[chan1DSBin]
        opTableStim['ledStim'] = chan12DSBin
    else:
        err = err+'#ledStim channel empty or fewer than 200 triggers#'
        #print('Max val LED stim channel: ', dct['head12']['max'])
        #print('Num trigs in downsampled channel 1: ', chan1DSBin.sum())
         

    if pawStimFlag and (chan1DSBin.sum() == 600):
        chan13=dct['chan'+pawSuffix].squeeze()
        chan13DS=signal.resample_poly(chan13,960,1000000)
        chan13DSBin = chan13DS > 10000
        chan13DSBin=chan13DSBin.astype(int)
        chan13DSBin=chan13DSBin[:chan1DSBin.shape[0]]
        chan13DSBin=chan13DSBin[chan1DSBin]
        opTableStim['pawStim'] = chan13DSBin
    #else:
    #    err = err+'#pawStim channel empty or not exactly 600 triggers#'

    if len(opTableStim.columns) == 0:
        opTableStim = False   

    if err == '':
        err = '#no error#'

    return opTableOptical, opTableStim, consecutiveTriggers, err


def matToTable2(matPath, trigSuffix = '1', cyanSuffix = '3', uvSuffix = '4', ledSuffix = '12', pawSuffix = '13'):
    
    dct=io.loadmat(matPath)

    try: 
        #trigFlag = dct['head1']['max'].squeeze() > 30000
        led1Flag = dct['head'+cyanSuffix]['max'].squeeze() > 30000
        led2Flag = dct['head'+uvSuffix]['max'].squeeze() > 30000
    except KeyError:
        return False, False, 0,None

    if led1Flag and led2Flag:
        
        
        chan3bin=np.squeeze(dct['chan'+cyanSuffix] > 30000)
        chan3bin=chan3bin*2

        chan4bin=np.squeeze(dct['chan'+uvSuffix] > 30000)
    
        if chan4bin.shape[0] > chan3bin.shape[0]:
            chan4bin = chan4bin[:chan3bin.shape[0]]
        elif chan4bin.shape[0] < chan3bin.shape[0]:
            chan3bin = chan3bin[:chan4bin.shape[0]]


        combineLED=chan3bin+chan4bin
        combineLEDDiff = np.diff(combineLED)
        combineLEDNonzeroDiff = np.where(combineLEDDiff)[0]

        compressCombineLED = combineLED[combineLEDNonzeroDiff]

        nonZeroTrigs = np.where(compressCombineLED)[0]

        opticalOrder = compressCombineLED[nonZeroTrigs]        

        whereConsec = np.diff(opticalOrder.squeeze()) == 0
        
        sumConsecTrigs=np.sum(np.diff(opticalOrder.squeeze()) == 0) 
        
        whereConsec = np.insert(whereConsec,False,False,axis=0)

        if len(whereConsec) != len(opticalOrder):
            raise Exception('Consecutive trigger mask different length to trigger array')

        opTableOptical=pd.DataFrame({'opticalOrder':opticalOrder})
    else:
        opTableOptical = False
        sumConsecTrigs = 0
        whereConsec = None

    return opTableOptical,False,sumConsecTrigs,whereConsec



def getNframesTif(tifPath):
    img = Image.open(tifPath)
    
    try:
        nFrames = img.n_frames
    except SyntaxError as e:
        logging.exception(e)
        nFrames = 'unknown'
 
    return nFrames


def makeMontage(imgFpath,inds,opname,trigs):
    #inds=np.squeeze(inds)
    img = Image.open(imgFpath)
    imgl = []
    for page in ImageSequence.Iterator(img):
        imgl.append(page.convert(mode='F'))

    if len(trigs) != len(imgl):
        return False

    movie = np.empty((imgl[0].size[1], imgl[0].size[0], len(imgl))) #np arrays have 1st index as rows
    for i in range(len(imgl)):
        movie[:,:,i] = np.array(imgl[i])

    for j,ind in enumerate(inds):
        plt.figure(figsize = [10,8]) 
        for iFig in range(-3,3):
            plt.subplot(2,3,iFig+4)
            plt.imshow(np.squeeze(movie[:,:,ind+iFig]))
            if ind+iFig == ind-1:  
                plt.title('Dropped Frame '+str(ind+iFig)+' Trig Num: '+str(trigs[ind+iFig]))
            else:
                plt.title('Frame '+str(ind+iFig)+' Trig Num: '+str(trigs[ind+iFig]))
        plt.tight_layout()
        plt.savefig(opname+'Frames'+str(ind)+'.png')
        plt.close()

    plt.clf()
    plt.figure()

    movieRes = movie.reshape([512*500,-1])
    meanTS = movieRes.mean(axis =0)


    maskLabel = np.squeeze(trigs.copy()).astype('int') #np.array([2 if x % 2 else 1 for x in range(0,len(meanTS))])
    lenTS = len(meanTS)
    timeVector = np.linspace(1,lenTS,lenTS)

    if maskLabel.shape[0] != lenTS:
        with open(opname+'triginderr.txt','w') as f:
            f.write('')
        #return None

        while maskLabel.shape[0] < lenTS:
            if maskLabel[-1] == 1:
                maskLabel = np.append(maskLabel,1)
            else:
                maskLabel = np.append(maskLabel,2)

    fig, ax = plt.subplots()

    breakDown = [[1, 'blue', 'Cyan'],[2, 'yellow', 'Ultraviolet']]

    for bD in breakDown:
        trigLabel, color, chanLabel = bD
        #pdb.set_trace()
        timeVectorMask = timeVector[maskLabel == trigLabel]
        meanTSMask = meanTS[maskLabel == trigLabel]
        ax.scatter(timeVectorMask, meanTSMask, c=color, label=chanLabel, alpha=0.3, marker = '.')

    ax.legend()
    plt.savefig(opname+'TS.png')
    plt.close()


    trigsNew = np.squeeze(trigs.copy()).astype('int')

    for indN in inds:
        trigsNew[indN-1] = 3

    maskLabel = trigsNew

    while maskLabel.shape[0] < lenTS:
        if maskLabel[-1] == 1:
            maskLabel = np.append(maskLabel,1)
        else:
            maskLabel = np.append(maskLabel,2)


    fig, ax = plt.subplots()

    breakDown = [[1, 'blue', 'Cyan'],[2, 'yellow', 'Ultraviolet'],[3, 'red', 'Dropped']]

    for bD in breakDown:
        trigLabel, color, chanLabel = bD
        timeVectorMask = timeVector[maskLabel == trigLabel]
        meanTSMask = meanTS[maskLabel == trigLabel]
        ax.scatter(timeVectorMask, meanTSMask, c=color, label=chanLabel, alpha=0.3, marker = '.')

    ax.legend()
    plt.savefig(opname+'TSFix.png')
    plt.close()

def produceEstimateTriggers(ipTiff, histSd = 8,histSd2 = 8,saveMean=True, splitMethod = 'filter', dbscanEps = 100):

    opMeanPath = ipTiff.split('.')[0]+'MeanTS.npy'

    if not os.path.isfile(opMeanPath):

        img = Image.open(ipTiff)
        imgl = []



        try:
            for page in ImageSequence.Iterator(img):
                imgl.append(page.convert(mode='F'))
        except TypeError as e:
            logging.exception(e)
            return False,False,False


        movie = np.empty((imgl[0].size[1], imgl[0].size[0], len(imgl))) #np arrays have 1st index as rows
        for i in range(len(imgl)):
            movie[:,:,i] = np.array(imgl[i])

        movieRes = movie.reshape([512*500,-1])
        meanTS = movieRes.mean(axis = 0)

        if saveMean:
            np.save(opMeanPath,meanTS)

    else:
        meanTS = np.load(opMeanPath)



    #try:#

    #    thresh = filters.threshold_minimum(meanTS)
    #except RuntimeError as e:
    #    print(e)
    #    pdb.set_trace()
    #    return False,False,False

    #upperMed = np.median(meanTS[meanTS > thresh])
    #upperStd = meanTS[meanTS > thresh].std()

    #lowerMed = np.median(meanTS[meanTS < thresh])
    #lowerStd = meanTS[meanTS < thresh].std()



    if splitMethod == 'filter':
        meanTsMean = meanTS.mean()
        meanTsStd  = meanTS.std()

        adjustedMeanTS = meanTS.copy()



        adjustedMeanTS[adjustedMeanTS > (meanTsMean + meanTsStd*histSd2)] = np.nan
        adjustedMeanTS[adjustedMeanTS < (meanTsMean - meanTsStd*histSd2)] = np.nan


        try:
            adjustedThresh = filters.threshold_minimum(adjustedMeanTS[~np.isnan(adjustedMeanTS)])
        except RuntimeError as e:
            print(e,'Trying different filter')
            try:
                adjustedThresh = filters.threshold_mean(adjustedMeanTS[~np.isnan(adjustedMeanTS)])
                if np.isnan(adjustedThresh):
                    print('Warning: could not find auto threshold')
                    return False,False,False

            except RuntimeError as e:

                return False,False,False



        colorAuto = meanTS.copy()

        colorAuto[meanTS > adjustedThresh] = 1                    
        colorAuto[meanTS <= adjustedThresh] = 2


        upperMed = np.median(meanTS[meanTS > adjustedThresh])
        upperStd = meanTS[meanTS > adjustedThresh].std()

        lowerMed = np.median(meanTS[meanTS < adjustedThresh])
        lowerStd = meanTS[meanTS < adjustedThresh].std()


        colorAuto[meanTS > (upperMed + upperStd*histSd)] = 3

        colorAuto[meanTS < (lowerMed - lowerStd*histSd)] = 3

    elif splitMethod == 'dbscan':
        clust = cluster.DBSCAN(eps=dbscanEps,min_samples=100).fit(np.vstack(meanTS))

        if len(np.unique(clust.labels_)) == 3:

            colorAuto = meanTS.copy()

            colorAuto[clust.labels_ == -1] = 3

            clus1 = meanTS[clust.labels_ == 0].mean()
            clus2 = meanTS[clust.labels_ == 1].mean()

            if clus1 > clus2:
                colorAuto[clust.labels_ == 0] = 1
                colorAuto[clust.labels_ == 1] = 2
            else:
                colorAuto[clust.labels_ == 0] = 2
                colorAuto[clust.labels_ == 1] = 1

        else:
            print('Clustering solution gave greater than or fewer than 3 clusters')
            return False,False,False

    else:
        raise Exception('splitMethod must be "filter" or "dbscan"')

    opCsv = pd.DataFrame({'opticalOrder':list(map(int,colorAuto))})

    
    return meanTS, colorAuto, opCsv




def makeWriteOpticalCsvs(connDct,opOpticalTable,csvPaths):

    try:
        lengths = [getNframesTif(cD) for cD in sorted(connDct[k])]
    except (AttributeError,TypeError) as e:
        logging.exception(e)
        lengths = ['unknown']
    except PIL.UnidentifiedImageError as e:
        logging.exception(e)
        lengths = ['unknown']
    if any(le == 'unknown' for le in lengths):
        print('images attached to',k,'cannot be read')

    else:

        for ind,imgPath in enumerate(connDct[k]):
            if ind  == 0:
                subOpticalTable = opTableOptical.loc[:lengths[0]-1]
                #print(imgPath,lengths,lengths[0]-1,subOpticalTable.shape,opTableOptical.shape)
            elif ind == 1:
                subOpticalTable = opTableOptical.loc[lengths[0]:lengths[0]+lengths[1]-1]
                #print(imgPath,lengths,lengths[0],lengths[0]+lengths[1]-1,subOpticalTable.shape,opTableOptical.shape)
            elif ind == 2:
                subOpticalTable = opTableOptical.loc[lengths[0]+lengths[1]:np.sum(lengths)]
                #print(imgPath,lengths,lengths[0]+lengths[1],subOpticalTable.shape,opTableOptical.shape)
            else:
                raise Exception('too many tifs assigned to this smr file',k)

            subOpticalTable.reset_index(inplace=True,drop=True)
            subOpticalTable.columns = ['opticalOrder']
            #csvOpName = connDct[k][ind].replace('.tif','OpticalOrder.csv')
            csvOpName = csvPaths[ind]
            subOpticalTable.to_csv(csvOpName)
            print('#### Wrote Optical Triggers to: ',csvOpName)


def autoTrigs(connDct, outputTrigs = False, trigOpDir = None, figDir = '', histSd = 8, writeFiles = [1,1,1], histSd2 = 8, splitMethod = 'filter', dbscanEps = 100):


    if type(connDct) == dict:
        if (type(outputTrigs) == str) and (trigOpDir == None):
            raise Exception('If you want to output triggers please specify a directory')

        for ind,imgPath in enumerate(connDct[k]):
            if not os.path.isfile(imgPath):
                return None



            opname = imgPath.split('/')[-1].split('.')[0]  
            pltOpName = os.path.join(figDir,opname+'meanTSAuto.png')


            if (not os.path.isfile(pltOpName)) or outputTrigs:

                meanTS, colorAuto, opCsv = produceEstimateTriggers(imgPath, histSd = histSd,histSd2 = histSd2,splitMethod = splitMethod,dbscanEps = dbscanEps)

                if type(meanTS) == bool:
                    return False

                xvals = np.linspace(1,len(meanTS),len(meanTS))

                val1 = meanTS[0]
                val2 = meanTS[1]

                if val1 < val2:
                    colSimp = [1 if i % 2 else 2 for i in range(0,len(meanTS)) ]
                else:
                    colSimp = [2 if i % 2 else 1 for i in range(0,len(meanTS)) ]


                if not os.path.isfile(pltOpName):

                    plt.figure(figsize = [20,10])
                    plt.subplot(1,2,1)

                    for cA in np.unique(colorAuto):
                        if cA == 1:
                            col = 'b'
                        elif cA == 2:
                            col = 'y'
                        elif cA == 3:
                            col = 'r'



                        newTS = meanTS[colorAuto == cA]
                        xvalsSub = xvals[colorAuto == cA]

                        plt.scatter(xvalsSub,newTS, marker = '.',c=col)



                    plt.subplot(1,2,2)
                    for cS in np.unique(colSimp):
                        if cS == 1:
                            col = 'b'
                        elif cS == 2:
                            col = 'y'

                        newTS = meanTS[colSimp == cS]
                        xvalsSub = xvals[colSimp == cS]
                        plt.scatter(xvalsSub,newTS, marker = '.',c=col)

                    plt.savefig(pltOpName)
                    plt.close()
                    plt.clf()

                else:
                    print('File already exists: ',pltOpName)
                                


                if outputTrigs:
                    
                    csvOpName = os.path.join(trigOpDir,'OpticalOrder.csv')
                    #if not os.path.isfile(csvOpName):
                    if writeFiles[ind] == 1:
                        if outputTrigs == 'simp':
                            opCsvSimp = pd.DataFrame({'opticalOrder':list(map(int,colSimp))})
                            opCsvSimp.to_csv(csvOpName)
                            print('##### Wrote simple auto triggers to ',csvOpName,'  #####')

                        elif outputTrigs == 'hist':
                            opCsvAuto = pd.DataFrame({'opticalOrder':list(map(int,colorAuto))})
                            opCsvAuto.to_csv(csvOpName)
                            print('##### Wrote automatic histogram based triggers to ',csvOpName,'  #####')
                        elif outputTrigs == False:
                            pass
                        else:
                            raise Exception('Variable "outputTrigs" must be set to "False", "simp", or "hist"')
                    #elif os.path.isfile(csvOpName):
                    #    print('Trigger Csv already exists: ',csvOpName)


    elif type(connDct) == str:
        if (type(outputTrigs) == str) and (trigOpDir == None):
            raise Exception('If you want to output triggers please specify a directory')

        imgPath = connDct
        if not os.path.isfile(imgPath):
            return None



        opname = imgPath.split('/')[-1].split('.')[0]  
        pltOpName = os.path.join(figDir,opname+'meanTSAuto.png')


        if (not os.path.isfile(pltOpName)) or outputTrigs:

            meanTS, colorAuto, opCsv = produceEstimateTriggers(imgPath, histSd = histSd,histSd2 = histSd2,splitMethod = splitMethod,dbscanEps = dbscanEps)

            if type(meanTS) == bool:
                return False

            xvals = np.linspace(1,len(meanTS),len(meanTS))

            val1 = meanTS[0]
            val2 = meanTS[1]

            if val1 < val2:
                colSimp = [1 if i % 2 else 2 for i in range(0,len(meanTS)) ]
            else:
                colSimp = [2 if i % 2 else 1 for i in range(0,len(meanTS)) ]


            if not os.path.isfile(pltOpName):

                plt.figure(figsize = [20,10])
                plt.subplot(1,2,1)

                for cA in np.unique(colorAuto):
                    if cA == 1:
                        col = 'b'
                    elif cA == 2:
                        col = 'y'
                    elif cA == 3:
                        col = 'r'



                    newTS = meanTS[colorAuto == cA]
                    xvalsSub = xvals[colorAuto == cA]

                    plt.scatter(xvalsSub,newTS, marker = '.',c=col)
                    plt.xlabel('autoFix')



                plt.subplot(1,2,2)
                for cS in np.unique(colSimp):
                    if cS == 1:
                        col = 'b'
                    elif cS == 2:
                        col = 'y'

                    newTS = meanTS[colSimp == cS]
                    xvalsSub = xvals[colSimp == cS]
                    plt.scatter(xvalsSub,newTS, marker = '.',c=col)
                    plt.xlabel('simpFix')

                plt.savefig(pltOpName)
                plt.close()
                plt.clf()

            else:
                print('File already exists: ',pltOpName)
                            


            if outputTrigs:
                
                csvOpName = os.path.join(trigOpDir,'OpticalOrder.csv')
                if outputTrigs == 'simp':
                    opCsvSimp = pd.DataFrame({'opticalOrder':list(map(int,colSimp))})
                    opCsvSimp.to_csv(csvOpName)
                    print('##### Wrote simple auto triggers to ',csvOpName,'  #####')

                elif outputTrigs == 'hist':
                    opCsvAuto = pd.DataFrame({'opticalOrder':list(map(int,colorAuto))})
                    opCsvAuto.to_csv(csvOpName)
                    print('##### Wrote automatic histogram based triggers to ',csvOpName,'  #####')
                elif outputTrigs == False:
                    pass
                else:
                    raise Exception('Variable "outputTrigs" must be set to "False", "simp", or "hist"')

    else:
        print('Input type of first argument not recognized')


def mcRefFromTif(tifPath, trigFilePath):

    img = Image.open(tifPath)
    imgl = []
    for page in ImageSequence.Iterator(img):
        imgl.append(page.convert(mode='F'))

    movie = np.empty((imgl[0].size[1], imgl[0].size[0], len(imgl))) #np arrays have 1st index as rows
    for i in range(len(imgl)):
        movie[:,:,i] = np.array(imgl[i])

    inputTrigs=pd.read_csv(trigFilePath,index_col=0)
    opticalOrder=inputTrigs['opticalOrder'].values

    
    blueMovie = movie[:,:,opticalOrder == 1]
    #uvMovie = movie[:,:,opticalOrder == 2]

    blueMovieSize = blueMovie.shape
    #uvMovieSize = uvMovie.shape

    midFrameBlue = round(blueMovieSize[2]/2)
    mcRefFrame=blueMovie[:,:,midFrameBlue]
    
    return mcRefFrame

def splitTif(tifPath, trigFilePath, mcRef = False):

    img = Image.open(tifPath)
    imgl = []
    for page in ImageSequence.Iterator(img):
        imgl.append(page.convert(mode='F'))

    movie = np.empty((imgl[0].size[1], imgl[0].size[0], len(imgl))) #np arrays have 1st index as rows
    for i in range(len(imgl)):
        movie[:,:,i] = np.array(imgl[i])

    inputTrigs=pd.read_csv(trigFilePath,index_col=0)

    opticalOrder=inputTrigs['opticalOrder'].values

    opticalOrder = opticalOrder[:len(imgl)]


    if movie.shape[2] != len(opticalOrder):
        print('Triggers are not the same length as the movie, cannot split')
        if mcRef:
            return False,False,False,
        else:
            return False,False
    
    blueMovie = movie[:,:,opticalOrder == 1]
    uvMovie = movie[:,:,opticalOrder == 2]

    blueMovieSize = blueMovie.shape
    uvMovieSize = uvMovie.shape

    if mcRef:
        midFrameBlue = round(blueMovieSize[2]/2)
        mcRefFrame=blueMovie[:,:,midFrameBlue]
        
        return blueMovie,uvMovie,mcRefFrame

    else:
        return blueMovie,uvMovie
    
def saveNiiLPS(arr,opname):
    
    arr = arr.squeeze()
    
    imgShape = arr.shape

    if len(imgShape) == 2:
        arr = arr[:,:,np.newaxis,np.newaxis]

    elif len(imgShape) == 3:
        imgX,imgY,imgT = imgShape
        arr = np.reshape(arr,[imgX,imgY,1,imgT])

    elif len(imgShape) == 4:
        pass



    # Op nifti configs
    dimsOp = [0.025,0.025,0.025,1]
    aff = np.eye(4)
    aff[1,1] = -1
    aff[2,2] = -1
    aff = aff * 0.025
    aff[3,3] = 1

    out_image = nb.Nifti1Image(arr, aff)
    out_image.header.set_zooms(dimsOp)
    
    out_image = out_image.slicer[::-1,:,::-1,:]
    
    nb.save(out_image, opname)
    
    
    return opname




def makeMontageCheckTrig(imgFpath,opname,trigs,optimeseries = False,saveMean=True):
    #inds=np.squeeze(inds)


    pltOpName = opname+'TSWithTrigs.png'

    if not os.path.isfile(pltOpName):


        opMeanPath = imgFpath.split('.')[0]+'MeanTS.npy'

        if not os.path.isfile(opMeanPath):

            img = Image.open(imgFpath)
            imgl = []

            try:
                for page in ImageSequence.Iterator(img):
                    imgl.append(page.convert(mode='F'))
            except TypeError as e:
                logging.exception(e)
                return False

            if len(trigs) != len(imgl):
                return False

            movie = np.empty((imgl[0].size[1], imgl[0].size[0], len(imgl))) #np arrays have 1st index as rows
            for i in range(len(imgl)):
                movie[:,:,i] = np.array(imgl[i])

            movieRes = movie.reshape([512*500,-1])
            meanTS = movieRes.mean(axis = 0)

            if saveMean:
                np.save(opMeanPath,meanTS)

        else:
            meanTS = np.load(opMeanPath)



        maskLabel = np.squeeze(trigs.copy()).astype('int') 

        lenTS = len(meanTS)

        timeVector = np.linspace(1,lenTS,lenTS)


        if len(maskLabel) > lenTS:
            maskLabel = maskLabel[:lenTS]
        elif len(maskLabel) < lenTS:
            while maskLabel.shape[0] < lenTS:
                if maskLabel[-1] == 1:
                    maskLabel = np.append(maskLabel,1)
                else:
                    maskLabel = np.append(maskLabel,2)
            #raise Exception('Length of ts does not match trigs')


        fig, ax = plt.subplots()

        breakDown = [[1, 'blue', 'Cyan'],[2, 'yellow', 'Ultraviolet'],[3, 'red', 'Dropped']]

        for bD in breakDown:
            trigLabel, color, chanLabel = bD
            timeVectorMask = timeVector[maskLabel == trigLabel]
            meanTSMask = meanTS[maskLabel == trigLabel]
            ax.scatter(timeVectorMask, meanTSMask, c=color, label=chanLabel, alpha=0.3, marker = '.')

        ax.legend()
        plt.savefig(pltOpName)
        if optimeseries:
            np.save(pltOpName.replace('.png','.npy'), meanTS)
        plt.clf()
        plt.close()

    else:
        print('File already exists: ',pltOpName)


def rawPlot(imgFpath,opname,optimeseries = False,saveMean=True):
    #inds=np.squeeze(inds)


    pltOpName = opname+'TSOnly.png'

    if not os.path.isfile(pltOpName):


        opMeanPath = imgFpath.split('.')[0]+'MeanTS.npy'

        if not os.path.isfile(opMeanPath):

            img = Image.open(imgFpath)
            imgl = []

            try:
                for page in ImageSequence.Iterator(img):
                    imgl.append(page.convert(mode='F'))
            except TypeError as e:
                logging.exception(e)
                return False


            movie = np.empty((imgl[0].size[1], imgl[0].size[0], len(imgl))) #np arrays have 1st index as rows
            for i in range(len(imgl)):
                movie[:,:,i] = np.array(imgl[i])

            movieRes = movie.reshape([512*500,-1])
            meanTS = movieRes.mean(axis = 0)

            if saveMean:
                np.save(opMeanPath,meanTS)

        else:
            meanTS = np.load(opMeanPath)





        lenTS = len(meanTS)

        timeVector = np.linspace(1,lenTS,lenTS)




        fig, ax = plt.subplots()

        ax.scatter(timeVector, meanTS, marker = '.')

        ax.legend()
        plt.savefig(pltOpName)
        if optimeseries:
            np.save(pltOpName.replace('.png','.npy'), meanTS)
        plt.clf()
        plt.close()

    else:
        print('File already exists: ',pltOpName)





def relDelToSecs(relDelObj):

    secCount = 0

    if relDelObj.seconds != 0:
        secCount = secCount +relDelObj.seconds

    if relDelObj.minutes != 0:
        secCount = secCount +relDelObj.minutes*60

    if relDelObj.hours != 0:
        raise Exception('Smr files and tif file time stamps too far away')

    if relDelObj.days != 0:
        raise Exception('Smr files and tif file time stamps too far away')

    if relDelObj.weeks != 0:
        raise Exception('Smr files and tif file time stamps too far away')

    if relDelObj.months != 0:
        raise Exception('Smr files and tif file time stamps too far away')

    return secCount

    

if __name__ == '__main__':


    # Define organized data dir, file structure to iterate over
    # And csv for allowing trig drop correction

    parser=argparse.ArgumentParser(description='Run script to create trigger files and split wavelengths into seperate niftis')
    parser.add_argument('orgDir',type = str, help="Path to organized data directory")
    parser.add_argument('opDir',type=str,help="Path to output directory, often the preprocessing directory")
    parser.add_argument('trigQcDir',type=str,help="Path to folder to put Quality control figures")
    parser.add_argument('trigReplaceDf',type=str,help='Path to csv file which controls the semi automatic generation of trigger files')
    parser.add_argument('--matchTemplate',type=str,help='a string to feed to glob to match certain sessions/cell types for example: SLC/ses-*/animal*/ca2/ will do all SLC data',default='*/*/*/*/')
    parser.add_argument('--refImage',type=str,help='1 to create ref images, 0 otherwise',default=0)
    parser.add_argument('--refImage100',type=str,help='1 to create images of 100 frames centered around the ref images, 0 otherwise',default=0)


    # Read in arguments and assign to variables
    args=parser.parse_args()

    orgDir=args.orgDir
    opDir=args.opDir
    trigQcDir=args.trigQcDir
    trigReplaceDfPath=args.trigReplaceDf
    trigFixQcDir=os.path.join(trigQcDir,'triggerFix')
    matchTemplate=args.matchTemplate
    refImageFlag = int(args.refImage)
    refImg100Flag = int(args.refImage100)

    if not os.path.isdir(trigFixQcDir):
        os.makedirs(trigFixQcDir)

    if not os.path.isdir(os.path.join (trigQcDir,'triggerReplace')):
        os.makedirs(os.path.join (trigQcDir,'triggerReplace'))

    # Which directories to look at....
    #sesGlobStr = os.path.join(opdir,'*/ses-*/animal*/ca2/')
    sesGlobStr = os.path.join(orgDir,matchTemplate)

    sesGlob = natsort.natsorted(glob.glob(sesGlobStr))

    if os.path.isfile(trigReplaceDfPath):
        print('Reading existing csv:',trigReplaceDfPath)
        trigReplaceDf = pd.read_csv(trigReplaceDfPath)

    else:
        print('No csv found, generating csv automatically:',trigReplaceDfPath)
        cols = ['Img','CrossedTrigs','autoFix','simpFix','sdFlag','sdVal','writeImgs','manualOverwrite','splitMethod','dbscanEps']
        trigReplaceDf = pd.DataFrame(columns = cols)

        tifFileNames = [f.split('/')[-1].split('.')[0] for f in natsort.natsorted(glob.glob(sesGlobStr+'/*.tif'))]
        trigReplaceDf.Img = tifFileNames

        trigReplaceDf.to_csv(trigReplaceDfPath,index=False)
        





    # This is the ideal template for what tiff files will exist in the organized directory
    # e.g. seven EPIs, with three parts each
    template = [['EPI'+str(eN)+'_','part-0'+str(pn)] for eN in range(1,20) for pn in range(0,3)]



    # Go through each session directory
    for sesh in sesGlob:

        # Grab the .mat trigger files and the tiffs
        spikeMats = natsort.natsorted(glob.glob(sesh+'*.mat'))
        tifFiles = natsort.natsorted(glob.glob(sesh+'*.tif'))



        print('Trying to automatically create triggers for : ', sesh)
        #print(spikeMats)
        #print(tifFiles)

        # Order the tiff files as per the ideal template
        newOrderTifs = []
        for temp in template:
            tfsTemp = [tF for tF in tifFiles if all(te in tF for te in temp)]
            if len(tfsTemp) == 1:
                newOrderTifs.append(tfsTemp[0])
            else:
                newOrderTifs.append('')
    



        # Delete any empty entries in newOrderTifs from the back
        while newOrderTifs[-1] == '' and len(newOrderTifs) > 1:
            del newOrderTifs[-1]

        # This dictionary will be used to match mat files to tif files
        connDct = {}

        

        # Ideal scenario, numMats*3 = numTifs
        if len(spikeMats)*3 == len(newOrderTifs):
            for i,sM in enumerate(spikeMats):
                startInd = i*3
                connDct[sM] = newOrderTifs[startInd:startInd+3]

        # Nonideal scenarios
        elif len(spikeMats) == 6 and len(newOrderTifs) == 21:
                dateTimes = [sM.split('/')[-1].split('_')[3] for sM in spikeMats]
                dateTimes = [datetime.strptime(dT,'%Y-%m-%d-%H-%M-%S') for dT in dateTimes]
                dTDiff = np.diff(dateTimes)
                smrNumDiff = np.diff([int(sM.split('_')[-1].split('.')[0]) for sM in spikeMats])
                dTMax = np.argmax(dTDiff)
                smrMax = np.argmax(smrNumDiff)

                if dTMax == smrMax:
                    spikeMats.insert(dTMax+1,'')
                    for i,sM in enumerate(spikeMats):
                        startInd = i*3
                        connDct[sM] = newOrderTifs[startInd:startInd+3]

        elif len(spikeMats) == 8 and len(template) == 8:
            for i,sM in enumerate(spikeMats):
                startInd = i*3
                connDct[sM] = newOrderTifs[startInd:startInd+3]

        # If we dont have a full compliment of tifs, but the number of .mat files
        # matches up then do it
        elif (len(newOrderTifs) < 21) and len(spikeMats)*3 == len(newOrderTifs):

            for i,sM in enumerate(spikeMats):
                startInd = i*3
                connDct[sM] = newOrderTifs[startInd:startInd+3]

        # Abject failure to match
        else:

            try:

                spikeMatTimes = [datetime.strptime(sM.split('_')[-2], '%Y-%m-%d-%H-%M-%S') for sM in spikeMats]
                tiffTimes = [datetime.fromtimestamp(os.path.getmtime(tF)) for tF in tifFiles]


                try:
                    matchIndices = [np.argmin([abs(relDelToSecs(relativedelta(sMT,tT))) for tT in tiffTimes]) for sMT in spikeMatTimes]



                    # Order the tiff files as per the ideal template
                    newOrderTifs = []
                    for temp in template:
                        tfsTemp = [tF for tF in tifFiles if all(te in tF for te in temp)]
                        if len(tfsTemp) == 1:
                            newOrderTifs.append(tfsTemp[0])
                        else:
                            newOrderTifs.append('')
                
                    while newOrderTifs[-1] == '' and len(newOrderTifs) > 1:
                        del newOrderTifs[-1]

                    #pdb.set_trace()

                    newMatchIndices = [newOrderTifs.index(tifFiles[ind]) for ind in matchIndices]


                    # This dictionary will be used to match mat files to tif files
                    connDct = {}

                    for i,Num in enumerate(matchIndices):
                        connDct[spikeMats[i]] = newOrderTifs[Num:Num+3]
                except:
                    print('Error: Could not create connDct')
                    connDct = {}

            except ValueError as e:
                logging.exception(e)
                connDct = {}


        # Assuming there are matches we now try to create csvs with trigger details    
        if len(connDct.keys()) > 0: # and any(x2 in sesh for x2 in ['animal73','animal56','animal57','animal55']):
            for k in connDct.keys():



                # If we have three image parts
                if len(connDct[k]) == 3 and os.path.isfile(k) and all([os.path.isfile(cN) for cN in connDct[k]]):# and all(['EPI1' in cN for cN in connDct[k]]):

                    print('### Splitting out data for the following files: ')
                    print(k)
                    print(''.join([c+'\n' for c in connDct[k]]))
                    # Generate dataframe from mat file
                    opTableOptical,opTableStim,consecTrigs,err = matToTable(k)


                    # If that didnt work try to do without channel 1 in smr file
                    if type(opTableOptical) != pd.core.frame.DataFrame:
                        opTableOptical,opTableStim,consecTrigs,consecTrigMask = matToTable2(k)


                    # Write stim file if it was determined

                        

                    firstImageName = connDct[k][0].split('/')[-1]


                    cellType, animalNum, sesh, dte, epiNum, stim, partNum = firstImageName.split('.')[0].split('_')
                    epiNum=int(epiNum.replace('EPI',''))
                    partNum = int(partNum.split('-')[-1])+1
    
                    opStimDir = os.path.join(opDir,cellType,sesh,animalNum,'ca2/',firstImageName.split('.')[0].split('_part')[0])
                    opPathStim = os.path.join(opStimDir,'Stim.csv')
                    
                    if not os.path.isdir(opStimDir):
                        os.makedirs(opStimDir)
                        

                    if type(opTableStim) == pd.core.frame.DataFrame and not os.path.isfile(opPathStim):
                        opTableStim.to_csv(opPathStim)

                    tifLengths = [getNframesTif(cD) for cD in sorted(connDct[k])]

                    # First pass at writing triggers
                    if type(opTableOptical) == pd.core.frame.DataFrame and opTableOptical['opticalOrder'].shape[0] == np.sum(tifLengths):

                        # If there are no consecutive triggers
                        if consecTrigs == 0 and all([os.path.isfile(cN) for cN in connDct[k]]):
                            # Generate output names for csvs, and check if they already exist

                            #opCsvNames = [os.path.isfile(cN.replace('.tif','OpticalOrder.csv')) for cN in connDct[k]]
                            opCsvNames = []


                            # Generate output csv names, and create output directory if it doesnt exist
                            for cN in connDct[k]:
                                firstImageName = cN.split('/')[-1]
                                # For some reason extract these labels again from the filename
                                cellType, animalNum, sesh, dte, epiNum, stim, partNum = firstImageName.split('.')[0].split('_')
                                epiNum=int(epiNum.replace('EPI',''))
                                partNum = int(partNum.split('-')[-1])+1
                                
                                opDirCsv = os.path.join(opDir,cellType,sesh,animalNum,'ca2/',firstImageName.split('.')[0].split('_part')[0],'part-'+str(partNum-1).zfill(2))
                                if not os.path.isdir(opDirCsv):
                                    os.makedirs(opDirCsv)

                                opPathCsv = os.path.join(opDirCsv,'OpticalOrder.csv')

                                opCsvNames.append(opPathCsv)


                            # Generate dataframe for each image and write them
                            if not all([os.path.isfile(oCN) for oCN in opCsvNames]):
                                print('Writing trigger csvs for ', k)
                                makeWriteOpticalCsvs(connDct,opTableOptical,opCsvNames)

                            else:
                                print('Trigger csvs already created for ',k)


                            # If writing triggers was successful, read in tiff, split into signal and physio noise, and write out as nii
                            if all([os.path.isfile(oCN) for oCN in opCsvNames]):
                                for i,cN in enumerate(connDct[k]):


                                    
                                    firstImageName = cN.split('/')[-1]
                                    # For some reason extract these labels again from the filename
                                    cellType, animalNum, sesh, dte, epiNum, stim, partNum = firstImageName.split('.')[0].split('_')
                                    epiNum=int(epiNum.replace('EPI',''))
                                    partNum = int(partNum.split('-')[-1])+1
                                    
                                    opDirImage = os.path.join(opDir,cellType,sesh,animalNum,'ca2/',firstImageName.split('.')[0].split('_part')[0],'part-'+str(partNum-1).zfill(2))





                                    opPathSignal = os.path.join(opDirImage,'rawsignl.nii.gz')
                                    opPathNoise = os.path.join(opDirImage,'rawnoise.nii.gz') 

                                    if not os.path.isfile(opPathSignal) or not os.path.isfile(opPathNoise):
                                        print('Now splitting tif files')
                                        print('##### Reading in tif and splitting: ', cN)
                                        signalMovie, noiseMovie = splitTif(cN, opCsvNames[i], mcRef = False)
                                        if type(signalMovie) == bool:
                                            print('could not split data')

                                        else:
                                            print('##### Writing data to: ', opPathSignal)
                                            saveNiiLPS(signalMovie, opPathSignal)

                                            print('##### Writing data to: ', opPathNoise)
                                            saveNiiLPS(noiseMovie, opPathNoise)

                                    else:
                                        print('Nii files already exist: ', opPathSignal, opPathNoise)

                                    qcFigDir = os.path.join(trigQcDir,cellType)
                                    qcFigPath = os.path.join(qcFigDir,firstImageName.split('.')[0])
                                    if not os.path.isdir(qcFigDir):
                                        os.makedirs(qcFigDir)

                                    if not os.path.isfile(qcFigPath+'TSWithTrigs.png'):
                                        print('##### Making QC Fig: ', qcFigPath)
                                        trigs = pd.read_csv(opCsvNames[i])['opticalOrder'].values
                                        makeMontageCheckTrig(cN,qcFigPath,trigs)




                    else:
                        # Need semi auto script for these
                        print(k,'Couldnt automatically split tif files')
                        if type(opTableOptical) != pd.core.frame.DataFrame:
                            print('Function matToTable')
                        if opTableOptical['opticalOrder'].shape[0] != np.sum(tifLengths):
                            print('Triggers were not the same length as the imaging data: trigger length is ',opTableOptical['opticalOrder'].shape[0],'number of optical frames is ',np.sum(tifLengths))

                        for i,cN in enumerate(connDct[k]):
                            firstImageName = cN.split('/')[-1].split('.')[0]
                            if firstImageName not in trigReplaceDf.Img.values:
                                 tempDf = pd.DataFrame(columns = trigReplaceDf.columns)
                                 tempDf.Img = [firstImageName]
                                 tempDf.CrossedTrigs = [1]
                                 trigReplaceDf = trigReplaceDf.append(tempDf)

                            elif firstImageName in trigReplaceDf.Img.values:
                                processFlag = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].CrossedTrigs.values
                                if len(processFlag) > 0:
                                    processFlag = processFlag[0]
                                else:
                                    processFlag = 0

                                if processFlag != 1:
                                    row =  trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].index[0]
                                    trigReplaceDf.loc[row,'CrossedTrigs'] = 1


                        print('Modifying trigger csv to produce suggested fixes in trigFix directory')                            






        # Lets try to take the .mat files and create one csv per tif file with the
        # correct optical order

        print('Trying semi automatic triggers')





        for imgPath in newOrderTifs:

            fname = imgPath.split('/')[-1]

            fnameNoSuff = fname.split('.')[0]

            print(fnameNoSuff)


            if fnameNoSuff in trigReplaceDf.Img.values:



                cellType, animalNum, sesh, dte, epiNum, stim, partNum = fname.split('.')[0].split('_')
                epiNum=int(epiNum.replace('EPI',''))
                partNum = int(partNum.split('-')[-1])+1
                
                opDirCsv = os.path.join(opDir,cellType,sesh,animalNum,'ca2/',fname.split('.')[0].split('_part')[0],'part-'+str(partNum-1).zfill(2))

                trigPath = os.path.join(opDirCsv,'OpticalOrder.csv')

                processFlag = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].CrossedTrigs.values


                if len(processFlag) > 0:
                    processFlag = processFlag[0]
                    autoFlag = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].autoFix.values[0]
                    simpFlag = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].simpFix.values[0]
                    writeManual = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].manualOverwrite.values[0]
                    splitMethod = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].splitMethod.values[0]

                    if autoFlag == 1 and simpFlag == 1:
                        raise Exception('Cant have both an auto and simple trig fix, they will overwrite')

                else:
                    processFlag = 0


                writeFiles = [0,0,0]
                if processFlag == 1:
                    print('This image is tagged for semi auto processing: ', fname)
                    opname = imgPath.split('/')[-1].split('.')[0]
                    opname = os.path.join(trigFixQcDir,opname)
                    rawPlot(imgPath,opname)

                    if os.path.isfile(trigPath):

                        trigs = pd.read_csv(trigPath)['opticalOrder']
                        if len(trigs.values) > 0:
                            opname = imgPath.split('/')[-1].split('.')[0]
                            opname = os.path.join(trigFixQcDir,opname+'Before')
                            makeMontageCheckTrig(imgPath,opname,trigs.values)


                            
                    if autoFlag == 1 and ((type(splitMethod) != str) or (splitMethod == 'filter')):
                        if not os.path.isdir(opDirCsv):
                            os.makedirs(opDirCsv)


                        sdFlag = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].sdFlag.values[0]
                        sdFlag2 = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].sdFlag.values[0]


                        if sdFlag == 1:
                            sdVal = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].sdVal.values[0]
                        else:
                            sdVal = 8

                        if sdFlag2 == 1:
                            sdVal2 = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].sdVal.values[0]
                        else:
                            sdVal2 = 3
                            
                        autoTrigs(imgPath,outputTrigs = 'hist', figDir = trigFixQcDir,histSd = sdVal,histSd2 = sdVal2,trigOpDir = opDirCsv)


                    elif simpFlag == 1:
                        if not os.path.isdir(opDirCsv):
                            os.makedirs(opDirCsv)
                        autoTrigs(imgPath,outputTrigs = 'simp', figDir = trigFixQcDir,writeFiles = writeFiles,trigOpDir = opDirCsv)


                    elif writeManual == 1:
                        print('Copy manually edited csv into place')
                        manualPath = os.path.join(trigQcDir,'triggerReplace', cellType, sesh, animalNum, 'ca2/', fname.split('.')[0].split('_part')[0],'part-'+str(partNum-1).zfill(2), 'OpticalOrder.csv')
                        shutil.copy(manualPath,trigPath)

                    elif splitMethod == 'dbscan':
                        if not os.path.isdir(opDirCsv):
                            os.makedirs(opDirCsv)

                        dbscanEps = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].dbscanEps.values[0]

                        if not np.isnan(dbscanEps):
                            autoTrigs(imgPath,outputTrigs = 'hist', figDir = trigFixQcDir,trigOpDir = opDirCsv,splitMethod = 'dbscan',dbscanEps = dbscanEps)
                        else:
                            autoTrigs(imgPath,outputTrigs = 'hist', figDir = trigFixQcDir,trigOpDir = opDirCsv,splitMethod = 'dbscan')
                        

                    else:
                        sdFlag = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].sdFlag.values[0]
                        if sdFlag == 1:
                            sdVal = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].sdVal.values[0]
                            autoTrigs(imgPath,outputTrigs = False, figDir = trigFixQcDir,histSd = sdVal)
                        else:
                            autoTrigs(imgPath,outputTrigs = False, figDir = trigFixQcDir)

        

                    if os.path.isfile(trigPath) and ((autoFlag == 1) or (simpFlag == 1) or (writeManual == 1) or (splitMethod == 'dbscan')):
                        trigs = pd.read_csv(trigPath)['opticalOrder']
                        opname = imgPath.split('/')[-1].split('.')[0]
                        opname = os.path.join(trigFixQcDir,opname+'After')
                        makeMontageCheckTrig(imgPath,opname,trigs.values,optimeseries = True)

                        writeImgs = trigReplaceDf[trigReplaceDf.Img == fname.replace('.tif','')].writeImgs.values[0]

                            
                        firstImageName = imgPath.split('/')[-1]
                        if writeImgs == 1:
                            
                            # For some reason extract these labels again from the filename
                            cellType, animalNum, sesh, dte, epiNum, stim, partNum = firstImageName.split('.')[0].split('_')
                            epiNum=int(epiNum.replace('EPI',''))
                            partNum = int(partNum.split('-')[-1])+1
                            
                            opDirImage = os.path.join(opDir,cellType,sesh,animalNum,'ca2/',firstImageName.split('.')[0].split('_part')[0],'part-'+str(partNum-1).zfill(2))


                            opPathSignal = os.path.join(opDirImage,'rawsignl.nii.gz')
                            opPathNoise = os.path.join(opDirImage,'rawnoise.nii.gz') 

                            #if not os.path.isfile(opPathSignal) or not os.path.isfile(opPathNoise):
                            print('##### Reading in tif and splitting: ', imgPath)
                            signalMovie, noiseMovie = splitTif(imgPath, trigPath, mcRef = False)

                            if type(signalMovie) == bool:
                                print('could not split data')

                            else:
                                print('##### Writing data to: ', opPathSignal)
                                saveNiiLPS(signalMovie, opPathSignal)

                                print('##### Writing data to: ', opPathNoise)
                                saveNiiLPS(noiseMovie, opPathNoise)

                                #else:
                                #    print('Files already exist: ', opPathSignal, opPathNoise)

                        qcFigDir = os.path.join(trigQcDir,cellType)
                        qcFigPath = os.path.join(qcFigDir,firstImageName.split('.')[0])
                        if not os.path.isdir(qcFigDir):
                            os.makedirs(qcFigDir)

                        if not os.path.isfile(qcFigPath+'TSWithTrigs.png'):
                            print('##### Making QC Fig: ', qcFigPath)
                            trigs = pd.read_csv(trigPath)['opticalOrder'].values
                            makeMontageCheckTrig(imgPath,qcFigPath,trigs)


    # To Delete Preprocessing in bash:
    #for line in `cat qcFigs/preprocCheck/pvTriggerIssues.csv | tail -n +2`;do sesh=`echo $line | awk -F, '{print $1}'`; newTrigs=`echo $line | awk -F, '{print $2}'`; if [[ $newTrigs == 1 ]];then ls PreprocessedData/*/*/*/*/$sesh/*;fi;done


    if refImageFlag == 1:

        print('Creating reference images')

        sesGlobStr = os.path.join(opDir,matchTemplate)
        sesGlob = glob.glob(sesGlobStr)

        for sG in sesGlob:
            for root,dirs,fs in os.walk(sG):
                for f in fs:
                    if f == 'rawsignl.nii.gz' and all([x in root for x in ['EPI1_','part-00']]):

                        opname = os.path.join(root,'rawsignl_moco_refimg.nii.gz')
                        opname100 = os.path.join(root,'rawsignl_moco_refimg100.nii.gz')

                        if not os.path.isfile(opname) or (not os.path.isfile(opname100) and refImg100Flag == 1): 

                            ippath = os.path.join(root,f)
                            imgObj = nb.Nifti1Image.load(ippath)
                            imgData = imgObj.get_fdata().squeeze()

                            midFrame = round(imgData.shape[2]/2)

                            mcRefArr = imgData[:,:,midFrame]


                            opImg = nb.Nifti1Image(mcRefArr, imgObj.affine, header = imgObj.header)


                            print('Saving moco ref image:', opname)
                            nb.save(opImg, opname)

                            if refImg100Flag == 1:
                                mcRefArr100 = imgData[:,:,midFrame-50:midFrame+50]
                                opImg100 = nb.Nifti1Image(mcRefArr100, imgObj.affine, header = imgObj.header)


                                print('Saving moco ref 100 frames image:', opname100)
                                nb.save(opImg, opname100)



                        else:
                            print('File already exits:', opname)




                       

