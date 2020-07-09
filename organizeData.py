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

from PIL import Image
from datetime import datetime

def smrMatConv(ippath,oppath):

    process = subp.Popen(["matlab","-nosplash","-nodesktop","-r","[x]=convertSMRtoMAT('"+ippath+"','"+oppath+"');display(x);exit"], stdout=subp.PIPE, stderr=subp.PIPE)
    stdout, stderr = process.communicate()
    process.kill()

    return stdout,stderr 

def matToTable(matPath):
    
    dct=io.loadmat(matPath)
    
    trigFlag = dct['head1']['max'].squeeze() > 30000
    led1Flag = dct['head3']['max'].squeeze() > 30000
    led2Flag = dct['head4']['max'].squeeze() > 30000

    if trigFlag and led1Flag and led2Flag:
        chan1bin=dct['chan1'].squeeze() > 30000;
        findx=np.where(chan1bin)
        findx=findx[0]
        firstTrigStart=findx[0]
        lastTrigStart=findx[-249]

        if (lastTrigStart - firstTrigStart)/25000 > 550:

            #chan1xbin=chan1bin(findx(1):findx(end)+24749);
            #y=downsample(chan1xbin,250);

            chan3bin=np.squeeze(dct['chan3'] > 30000)
            chan3bin=chan3bin[firstTrigStart:lastTrigStart+24999]
            chan3bin=chan3bin*2

            chan4bin=np.squeeze(dct['chan4'] > 30000)
            chan4bin=chan4bin[firstTrigStart:lastTrigStart+24999]
        

            combineLED=chan3bin+chan4bin
            combineLEDDiff = np.diff(combineLED)
            combineLEDNonzeroDiff = np.where(combineLEDDiff)[0]

            compressCombineLED = combineLED[combineLEDNonzeroDiff]

            nonZeroTrigs = np.where(compressCombineLED)[0]

            opticalOrder = compressCombineLED[nonZeroTrigs]        

            consecutiveTriggers=np.sum(np.diff(opticalOrder.squeeze()) == 0) 

            opTableOptical=pd.DataFrame({'opticalOrder':opticalOrder})
        else:
            opTableOptical = False
    else:
        opTableOptical = False
 

    ledStimFlag = dct['head12']['max'].squeeze() > 30000
    pawStimFlag = dct['head13']['max'].squeeze() > 30000

    chan1=dct['chan1'].squeeze() 
    chan1DS=signal.resample_poly(chan1,1,25000) 
    chan1DSBin = chan1DS > 200

    opTableStim=pd.DataFrame({})


    if ledStimFlag and (chan1DSBin.sum() > 200):
        chan12=dct['chan12'].squeeze()
        chan12DS=signal.resample_poly(chan12,960,1000000)
        chan12DSBin = chan12DS > 10000
        chan12DSBin=chan12DSBin.astype(int)
        chan12DSBin=chan12DSBin[chan1DSBin]
        opTableStim['ledStim'] = chan12DSBin
         

    if pawStimFlag and (chan1DSBin.sum() == 600):
        chan13=dct['chan13'].squeeze()
        chan13DS=signal.resample_poly(chan13,960,1000000)
        chan13DSBin = chan13DS > 10000
        chan13DSBin=chan13DSBin.astype(int)
        chan13DSBin=chan13DSBin[chan1DSBin]
        opTableStim['pawStim'] = chan13DSBin

    if len(opTableStim.columns) == 0:
        opTableStim = False   


    return opTableOptical, opTableStim


def matchSMRtoFMRI(ipdir,dfpaths,multi_cellDir,loggingObj):

    def dateTimeRe(ipstr):
        dateRe=list(set(re.findall('[0-9]{8}_[0-9]{6}',ipstr)))
        if len(dateRe) == 1:
            dateRe=dateRe[0]
        else:
            dateRe=''
        return dateRe

    def matchSmrNum(ipstr,compare):

        ipStrList=ipstr.split(',')

        if (len(ipStrList) > 1) and any([compare in isl for isl in ipStrList]):
            return True
        else: 
            return False

    #fs=glob.glob('*.csv')
    dfList=[]
    for f in dfpaths:
        df=pd.read_csv(f)
        firstCol = df.columns[0]
        df = df[[firstCol,'#','Final ID','Spike2_filenames']]
        df = df.rename({firstCol:'UniqueID'},axis=1)
        dfList.append(df)

    bigDf=pd.concat(dfList)
    bigDf.dropna(subset=['#'],inplace=True)
    bigDf.dropna(subset=['Spike2_filenames'],inplace=True)
    bigDf['dateTime'] = bigDf.UniqueID.apply(lambda x : dateTimeRe(x)).values
    bigDf['date'] = bigDf.dateTime.str.split('_').apply(lambda x : x[0])
    
        
    bigDfarr=bigDf[['dateTime','Spike2_filenames']].values

    for root,dirs,fs in os.walk(ipdir):
        for f in fs:
            if f.endswith('Stim.csv'):
                ippath=os.path.join(root,f)
                cellType,animalNum,sesh,dateTime,smrNum = f.split('_')
                seshNum=sesh.split('-')[1]
                smrNum=str(int(smrNum.replace('Stim.csv','')))
                smrDate=''.join(dateTime.split('-')[:3])
                smrTime=''.join(dateTime.split('-')[3:])
                smrDateTime = smrDate+'_'+smrTime
                

                dateTimeMatch = bigDf.date == smrDate
                smrNumMatch = bigDf.Spike2_filenames.apply(lambda x : matchSmrNum(x,smrNum))


                matches = np.sum(dateTimeMatch & smrNumMatch)

                if matches == 1:
                    bigDfsubset=bigDf[dateTimeMatch & smrNumMatch]
                    newNum=bigDfsubset['#'].values.astype(str)[0].replace('*','')
                    if '.' in newNum:
                        newNum=newNum.split('.')[0]
                    

                    existingPath=os.path.join(multi_cellDir,cellType,'session'+seshNum,'BIS_output_'+cellType+newNum.zfill(2)+'-'+seshNum.zfill(2)+'/')

                    opdir=os.path.join(existingPath,'stimOrder/')
                    oppath=os.path.join(opdir,f)

                    if os.path.isdir(existingPath):
                        if not os.path.isdir(opdir):
                            os.makedirs(opdir)
                        if not os.path.isfile(oppath):
                            shutil.copy(ippath,oppath)

                else:
                    bigDfsubset=bigDf[dateTimeMatch & smrNumMatch]
                    print(cellType,f,smrDate,smrNum)
                    print(bigDfsubset)


def parseTifFilepath(gatherDict,fpath,exceptionDf,loggingObj):
    # Check date
    dateRe=list(set(re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}',fpath)))

    msgList = []
    msg = ''

    if len(dateRe) > 1:
        msg=' '.join(['More than one session date: ', ' '.join(dateRe)])
        #loggingObj.info(msg)
        dateRe = 'Unknown'
    elif len(dateRe) < 1:
        msg=' '.join(['No session date that matches RE pattern'])
        #loggingObj.info(msg)
        dateRe = 'Unknown'
    else:
        dateRe=dateRe[0].replace('_','-')

    msgList.append(msg)

    # Check round
    roundRe=list(set(map(lambda x : x.lower(), re.findall('round[0-9]',fpath,flags=re.IGNORECASE))))

    if len(roundRe) > 1:
        msg=' '.join(['More than one round number: ', ' '.join(roundRe)])
        #loggingObj.info(msg)
        roundRe='Unknown'
    elif len(roundRe) < 1:
        msg=' '.join(['No round number that matches RE pattern'])
        #loggingObj.info(msg)
        roundRe='Unknown'
    else:
        roundRe=int(roundRe[0].lower().replace('round',''))


    msgList.append(msg)

    # Check animal number 
    animalRe=list(set(map(lambda x : x.lower(), re.findall('mouse[0-9]+|animal[0-9]+',fpath,flags=re.IGNORECASE))))

    if len(animalRe) > 1:
        msg=' '.join(['More than one animal number: ', ' '.join(animalRe)])
        #loggingObj.info(msg)
        animalRe='Unknown'
    elif len(animalRe) < 1:
        msg=' '.join(['No animal number that matches RE pattern'])
        #loggingObj.info(msg)
        animalRe='Unknown'
    else:
        animalRe=animalRe[0].lower().replace('mouse','animal')

    
    msgList.append(msg)

    # Check EPI num and Rest/LED

    endRePattern='|'.join(['[0-9]{4}-[0-9]{2}-[0-9]{2}_EPI[1-9]_'+sT+'.tif$' for sT in ['REST','LED','VISUAL','REST@000[12]','LED@000[12]','VISUAL@000[12]']])

    endRe=re.findall(endRePattern,fpath)

    if len(endRe) == 0:
        msg=' '.join(['Filename does not match the expected structure'])
        #loggingObj.info(msg)
        endRe='Unknown'
        epiNum='Unknown'
        scanType='Unknown'
        atNum='Unknown'
    else:
        endRe=endRe[0]
        epiNum=int(endRe.split('EPI')[-1].split('_')[0])
        if '@' in endRe:
            atNum=int(endRe.split('@')[-1].split('.')[0])
            scanType=endRe.split('_')[-1].split('@')[0]
        else:
            atNum=0
            scanType=endRe.split('_')[-1].split('.')[0]

    msgList.append(msg)

    cellType=[cellDict[k] for k in cellDict if k in fpath][0]
         
    gatherDict[fpath]['cellType'] = cellType
    gatherDict[fpath]['animalNumber'] = animalRe
    gatherDict[fpath]['sessionDate'] = dateRe
    gatherDict[fpath]['roundNum'] = roundRe
    gatherDict[fpath]['epiNum'] = epiNum
    gatherDict[fpath]['scanType'] = scanType
    gatherDict[fpath]['imageSection'] = atNum
    gatherDict[fpath]['makeSymLink'] = int(0)

    atts=['cellType','animalNumber','sessionDate','roundNum','epiNum','scanType','imageSection','makeSymLink'] 


    if np.sum(exceptionDf.fpaths.str.contains(fpath)) == 1:
        subDf=exceptionDf[exceptionDf.fpaths == fpath]
        for att in atts:
            if att in exceptionDf.columns:
                attIsNan = exceptionDf[exceptionDf.fpaths == fpath][att].isna().values[0]
                unknownFlag =  gatherDict[fpath][att] == 'Unknown'
                if attIsNan and not unknownFlag:
                    exceptionDf.loc[exceptionDf.fpaths == fpath,att] = gatherDict[fpath][att]



    if np.sum(exceptionDf.fpaths.str.contains(fpath)) == 1:
        subDf=exceptionDf[exceptionDf.fpaths == fpath]
        subDf=subDf.dropna(axis=1,how='all')
        for att in atts:
            if (att in subDf.columns) and ('Ignore' not in subDf.columns):
                subDf2=subDf.dropna(subset=[att],axis=0)
                gatherDict[fpath][att] = subDf2[att].values[0]
    else:
        raise Exception('Fpath for',fpath,' has either no entry or more than one entry in exception DF')

    if any([gatherDict[fpath][x] == 'Unknown' for x in atts]):
        msgList = '-'.join(msgList)
        msg = fpath + ' ' + msgList
        loggingObj.info(msg)

        msgNan = exceptionDf[exceptionDf.fpaths == fpath]['Fpath'].isna().values[0]

        if msgNan:
            exceptionDf.loc[exceptionDf.fpaths == fpath,'Fpath'] = msg

    return gatherDict,loggingObj

def parseSmrFilepath(gatherDict,fpath,exceptionDf,loggingObj):
    msgList = []
    msg = ''

    # Check date
    dateRe=list(set(re.findall('[0-9]{4}_[0-9]{2}_[0-9]{2}',fpath)))

    if len(dateRe) > 1:
        msg=' '.join(['More than one session date: ', ' '.join(dateRe)])
        #logging.info(msg)
        dateRe = 'Unknown'
    elif len(dateRe) < 1:
        msg=' '.join(['No session date that matches RE pattern'])
        #logging.info(msg)
        dateRe = 'Unknown'
    else:
        dateRe=dateRe[0].replace('_','-')

    msgList.append(msg)

    # Check session
    roundRe=list(set(map(lambda x : x.lower(), re.findall('session[1-3]',fpath,flags=re.IGNORECASE))))

    if len(roundRe) > 1:
        msg=' '.join(['More than one round number: ', ' '.join(roundRe)])
        #logging.info(msg)
        roundRe='Unknown'
    elif len(roundRe) < 1:
        msg=' '.join(['No round number that matches RE pattern'])
        #logging.info(msg)
        roundRe='Unknown'
    else:
        roundRe=int(roundRe[0].lower().replace('session',''))

    msgList.append(msg)

    # Check animal number 
    animalRe=list(set(map(lambda x : x.lower(), re.findall('mouse[0-9]+|animal[0-9]+',fpath,flags=re.IGNORECASE))))

    if len(animalRe) > 1:
        msg=' '.join(['More than one animal number: ', ' '.join(animalRe)])
        #logging.info(msg)
        animalRe='Unknown'
    elif len(animalRe) < 1:
        msg=' '.join(['No animal number that matches RE pattern'])
        #logging.info(msg)
        animalRe='Unknown'
    else:
        animalRe=animalRe[0].lower().replace('mouse','animal')

    msgList.append(msg)


    # Check SMR Num and file time
    ### To be coded!
    #smrREPattern = 'new[0-9]{3,4}|TT[0-9]{3,4}|TT-[0-9]{3}|test-[0-9]{3,4}'
    #smrNumRe=list(set(map(lambda x : x.lower(), re.findall(smrREPattern,fpath,flags=re.IGNORECASE))))
    #if len(smrNumRe) > 1:
    #    msg=' '.join(['More than one smr number: ', ' '.join(animalRe)])
        #logging.info(msg)
    #    smrNumRe='Unknown'
    #elif len(smrNumRe) < 1:
    #    msg=' '.join(['No smr number that matches RE pattern'])
        #logging.info(msg)
    #    smrNumRe='Unknown'
    #else:
    #    smrNumRe=smrNumRe[0].lower().replace('tt-','').replace('test-','').replace('new','').replace('tt','')

    smrNumRe, msg = getSMRNum(fpath)

    msgList.append(msg)

    smrModTimeNum =  os.path.getmtime(fpath)
    smrModTime =  time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(smrModTimeNum))

    smrModDate =  time.strftime('%Y-%m-%d', time.localtime(smrModTimeNum))

    if smrModDate != dateRe:
        dateRe='Unknown'
        msg=' '.join(['The session date does not match the file modification time'])
        #logging.info(msg)

    msgList.append(msg)

    cellType=[cellDict[k] for k in cellDict if k in fpath][0]
         
    gatherDict[fpath]['cellType'] = cellType
    gatherDict[fpath]['animalNumber'] = animalRe
    gatherDict[fpath]['sessionDate'] = dateRe
    gatherDict[fpath]['roundNum'] = roundRe
    gatherDict[fpath]['smrNum'] = smrNumRe
    gatherDict[fpath]['modTime'] = smrModTime
    gatherDict[fpath]['makeSymLink'] = int(0)

    atts=['cellType','animalNumber','sessionDate','roundNum','smrNum','modTime','makeSymLink']


    if np.sum(exceptionDf.fpaths.str.contains(fpath)) == 1:
        subDf=exceptionDf[exceptionDf.fpaths == fpath]
        for att in atts:
            if att in exceptionDf.columns:
                attIsNan = exceptionDf[exceptionDf.fpaths == fpath][att].isna().values[0]
                unknownFlag =  gatherDict[fpath][att] == 'Unknown'
                if attIsNan and not unknownFlag:
                    exceptionDf.loc[exceptionDf.fpaths == fpath,att] = gatherDict[fpath][att]
            

    if np.sum(exceptionDf.fpaths.str.contains(fpath)) == 1:
        subDf=exceptionDf[exceptionDf.fpaths == fpath]
        subDf=subDf.dropna(axis=1,how='all')
        for att in atts:
            if (att in subDf.columns) and ('Ignore' not in subDf.columns):
                subDf2=subDf.dropna(subset=[att],axis=0)
                gatherDict[fpath][att] = subDf2[att].values[0]

    else:
        raise Exception('Fpath for',fpath,' has either no entry or more than one entry in exception DF')

    if any([gatherDict[fpath][x] == 'Unknown' for x in atts]):
        
        msgList = '-'.join(msgList)
        msg = fpath + ' ' + msgList
        loggingObj.info(msg)

        msgNan = exceptionDf[exceptionDf.fpaths == fpath]['Fpath'].isna().values[0]

        if msgNan:
            exceptionDf.loc[exceptionDf.fpaths == fpath,'Fpath'] = msg

    return gatherDict, loggingObj, exceptionDf



def getSMRNum(fpath):

    ## Problem case 1: TT-2019-066.smr
    smrREPattern = 'TT-2019-[0-9]{3}'
    smrNumRe=list(set(map(lambda x : x.lower(), re.findall(smrREPattern,fpath,flags=re.IGNORECASE))))

    msg = ''

    if len(smrNumRe) > 1:
        msg=' '.join(['More than one smr number: ', ' '.join(smrNumRe)])
        #logging.info(msg)
        smrNumRe='Unknown'
        return smrNumRe, msg

    elif len(smrNumRe) < 1:
        pass

    else:
        smrNumRe=smrNumRe[0].lower().replace('tt-2019-','')
        return smrNumRe,msg


    smrREPattern = 'new[0-9]{3,4}|TT[0-9]{3,4}|TT-[0-9]{3}|test-[0-9]{3,4}'
    smrNumRe=list(set(map(lambda x : x.lower(), re.findall(smrREPattern,fpath,flags=re.IGNORECASE))))

    if len(smrNumRe) > 1:
        msg=' '.join(['More than one smr number: ', ' '.join(animalRe)])
        #logging.info(msg)
        smrNumRe='Unknown'
    elif len(smrNumRe) < 1:
        msg=' '.join(['No smr number that matches RE pattern'])
        #logging.info(msg)
        smrNumRe='Unknown'
    else:
        smrNumRe=smrNumRe[0].lower().replace('tt-','').replace('test-','').replace('new','').replace('tt','')

    return smrNumRe, msg


def getNframesTif(tifPath):
    img = Image.open(tifPath)
    return img.n_frames




if __name__ == '__main__':

    ##$  Config Start  $##


    parser=argparse.ArgumentParser(description='Run script to create an output folder with tifs and trigger files organzied')
    parser.add_argument('loggingFilePath',type = str, help="Path to log file, or where you would like to create log file, include filename in both instances")
    parser.add_argument('exceptionDataFrame',type=str,help="Path to exception dataframe, or where you would like to create exception dataframe, include filename in both instances")
    parser.add_argument('tiffPath',type=str,help="Path to folder containing tiff files")
    parser.add_argument('smrPath',type=str,help='Path to filder containing smr files')
    parser.add_argument('outputPath',type=str,help='Where to put organized data')


    args=parser.parse_args()

    loggingFilePath=args.loggingFilePath
    exceptionDataFrame=args.exceptionDataFrame
    tiffPath=args.tiffPath
    smrPath=args.smrPath
    outputPath=args.outputPath

    # Instantiate Log File
    logging.basicConfig(filename=loggingFilePath,level=logging.DEBUG,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    cellDict = { 'Aldh1l1_ai162' : 'GLIA',
        'PV_ai162' : 'PV',
        'slcTigre1' : 'SLC',
        'som_ai162' : 'SOM', 
        'vip_ai162' : 'VIP',
        'GLIA' : 'GLIA',
        'PV' : 'PV',
        'SLC' : 'SLC',
        'SOM' : 'SOM', 
        'VIP' : 'VIP',}
       
    exceptionDf = pd.read_csv(exceptionDataFrame,dtype={'roundNum': object,'smrNum':object,'epiNum':object,'partNum':object})


    ipdirs = [tiffPath, smrPath]
    opdir=outputPath

    gatherDict={}


    # Parse Input Calcium Directory
    for ipdir in ipdirs:
        for root, dirs, fs in os.walk(ipdir):
            for f in fs:
                if f.endswith('.tif'):
                    
                   
                    fpath=os.path.join(root,f)
                    gatherDict[fpath]={}
                    if fpath not in exceptionDf.fpaths.values:
                        exceptionDf = exceptionDf.append({'fpaths':fpath,'makeSymLink':0},ignore_index=True)
                    
                    gatherDict,logging=parseTifFilepath(gatherDict,fpath,exceptionDf,logging)


                elif f.endswith('.smr'):

                    fpath=os.path.join(root,f)
                    gatherDict[fpath]={}
                    if fpath not in exceptionDf.fpaths.values:
                        exceptionDf = exceptionDf.append({'fpaths':fpath,'makeSymLink':0},ignore_index=True)
                    

                    gatherDict,logging,exceptionDf=parseSmrFilepath(gatherDict,fpath,exceptionDf,logging)


    exceptionDf.to_csv(exceptionDataFrame,index=False)

    # Build Output Directory
    didntCopy=0
    for k in gatherDict:
        makeSL = gatherDict[k]['makeSymLink']

        if makeSL == 1:        

            if k.endswith('.tif'):
                allParamsKnown=all([gatherDict[k][subk] != 'Unknown' for subk in gatherDict[k]])

                if allParamsKnown:

                    ipFile=k

                    cellType = gatherDict[k]['cellType']
                    animalNum = gatherDict[k]['animalNumber'] 
                    sesDate = gatherDict[k]['sessionDate'] 
                    sesNum = gatherDict[k]['roundNum']
                    epiNum = gatherDict[k]['epiNum']
                    scanType = gatherDict[k]['scanType']
                    imageSegment = gatherDict[k]['imageSection']

                    opPath=os.path.join(opdir, cellType, 'ses-'+str(sesNum), animalNum, 'ca2')
                    opFilename= '_'.join([cellType,animalNum,'ses-'+str(sesNum),sesDate,'EPI'+str(epiNum),scanType,'part-'+str(imageSegment).zfill(2)])+'.tif'


                    if not os.path.isdir(opPath):
                        os.makedirs(opPath)

                    
                    opLink=os.path.join(opPath,opFilename)
                    if not os.path.isfile(opLink):
                        os.symlink(k,opLink)

                else:
                    print('Part of output directory unspecified for: ',k) 
                    didntCopy=didntCopy+1

            elif k.endswith('.smr'):
                allParamsKnown=all([gatherDict[k][subk] != 'Unknown' for subk in gatherDict[k]])

                if allParamsKnown:

                    ipFile=k

                    cellType = gatherDict[k]['cellType']
                    animalNum = gatherDict[k]['animalNumber'] 
                    sesDate = gatherDict[k]['sessionDate'] 
                    sesNum = gatherDict[k]['roundNum']
                    smrNum = gatherDict[k]['smrNum']
                    modTime = gatherDict[k]['modTime']
                    opPath=os.path.join(opdir, cellType, 'ses-'+str(sesNum), animalNum, 'ca2')
                    opFilename= '_'.join([cellType,animalNum,'ses-'+str(sesNum),modTime,str(smrNum)])+'.smr'


                    if not os.path.isdir(opPath):
                        msg=' '.join([k, ' doesnt seem to match any tif'])
                        logging.info(msg)
                        didntCopy=didntCopy+1
                         

                    else:
                        opLink=os.path.join(opPath,opFilename)
                        if not os.path.isfile(opLink):
                            os.symlink(k,opLink)
                            out,err = smrMatConv(opLink,opLink.replace('.smr','.mat'))

                else:
                    print('Part of output directory unspecified for: ',k) 
                    didntCopy=didntCopy+1
        else:
            print('Marked dont copy: ',k) 
            didntCopy=didntCopy+1
 

    if didntCopy != 0:
        print('Didnt create symlinks for ',didntCopy,' files')


    # Create trigger order files
    sesGlobStr = os.path.join(opdir,'*/ses-*/animal*/ca2/')
    sesGlob = glob.glob(sesGlobStr)


    template = [['EPI'+str(eN),'part-0'+str(pn)] for eN in range(1,8) for pn in range(0,3)]

    for sesh in sesGlob:
        spikeMats = sorted(glob.glob(sesh+'*.mat'))
        tifFiles = sorted(glob.glob(sesh+'*.tif'))

        print(sesh)
        print(spikeMats)
        print(tifFiles)

        newOrderTifs = []
        for temp in template:
            tfsTemp = [tF for tF in tifFiles if all(te in tF for te in temp)]
            if len(tfsTemp) == 1:
                 newOrderTifs.append(tfsTemp[0])
            else:
                newOrderTifs.append('')
    
        connDct = {}
    
        if len(spikeMats) == 7:
            for i,sM in enumerate(spikeMats):
                startInd = i*3
                connDct[sM] = newOrderTifs[startInd:startInd+3]
        elif (len(spikeMats) < 7) and (len(spikeMats) > 0):
            print('Not enough spikeMats')
            dateTimes = [sM.split('/')[-1].split('_')[3] for sM in spikeMats]
            dateTimes = [datetime.strptime(dT,'%Y-%m-%d-%H-%M-%S') for dT in dateTimes]
            print(dateTimes)
        else:
            print('either too many spikeMats or 0')
    
        if len(connDct.keys()) > 0 and 'animal73' in sesh:
            for k in connDct.keys():
                if len(connDct[k]) == 3:
                    print(k,connDct[k])
                    opTableOptical,opTableStim = matToTable(k)


                    lengths = [getNframesTif(cD) for cD in sorted(connDct[k])]

                    if type(opTableOptical) == pd.core.frame.DataFrame:
                        for ind,imgPath in enumerate(connDct[k]):
                            if ind  == 0:
                                subOpticalTable = opTableOptical.loc[:lengths[0]-1]
                            elif ind == 1:
                                subOpticalTable = opTableOptical.loc[lengths[0]:lengths[0]+lengths[1]-1]
                            elif ind == 2:
                                subOpticalTable = opTableOptical.loc[lengths[0]+lengths[1]:]
                            else:
                                raise Exception('too many tifs assigned to this smr file',k)

                            subOpticalTable.reset_index(inplace=True)
                            subOpticalTable.to_csv(connDct[k][ind].replace('.tif','OpticalOrder.csv'))

                            
