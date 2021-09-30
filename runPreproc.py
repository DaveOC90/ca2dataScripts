import os
import numpy as np
import pandas as pd
import nibabel as nb
import scipy as sp
import os
import pdb
import glob
import argparse


def runBiswebCa2(ipDict):

    '''
    Run the bisweb script via the command line here
    Provide all arguments for the script in the input
    dictionary
    '''

    acceptableTerms = ['pythonPath','calPreprocPath','signal','noise','opticalorder','segnum','createmcref','createmask','signalout','noiseout','debug','workdir','mcrefsignal','mcrefnoise','mask','runoption']


    if not all([k in acceptableTerms for k in ipDict.keys()]):
        raise Exception('At least one of the keys in this dictionary is not an acceptable term for the preprocessing pipeline:',ipDict)

    
    cmd = 'singularity exec ' + ipDict['calPreprocPath'] + ' calciumPreprocess2.py '+' '.join(['--%s %s' % kv for kv in ipDict.items() if not any(kv[0] == aT for aT in ['calPreprocPath'])])
    print(cmd)
    os.system(cmd)

    #with open('joblistglob.txt','a') as f:
    #    f.write(cmd+'\n')



def concatNiftis(ippaths,oppath):

    fileObjs = [nb.Nifti1Image.load(ip) for ip in ippaths]

    opArr = np.concatenate([fO.get_fdata() for fO in fileObjs],axis=-1)

    opImg = nb.Nifti1Image(opArr,fileObjs[0].affine)

    nb.save(opImg,oppath)



# What runs, when you run the script from the command line
if __name__ == '__main__':

   

    # Input arguments    
    parser=argparse.ArgumentParser(description='Run script to iterate over organized calcium data and run preprocessing')
    parser.add_argument('outputDir',type=str,help="Path to output directory")
    parser.add_argument('humanMadeMasks',type=str,help='Path to where we keep the manually made masks')
    parser.add_argument('singPath',type=str,help='Path to bisweb calcium preproc singularity file')
    parser.add_argument('--tag',type=str,help='substring to run only subset of data',default='ses') 

    args=parser.parse_args()

    # Setup input and output directories 
    #ipdir=args.organizedDataPath
    opdir=args.outputDir

    # Paths to python install and bisweb install to use
    biswebCaPath=args.singPath
    humanMadeMasks = args.humanMadeMasks
    ftags = args.tag.split(',')
    

    # Walk through input directory
    for root,dirs,fs in sorted(os.walk(opdir)):
        for f in sorted(fs):
            if f == 'rawsignl.nii.gz' and all([ft in root for ft in ftags]):

                print('Reading: ',root)
                # Instantiate input dictionary to run bisweb script
                ipDict={}



                # Parse input path and extract labels
                ippath=os.path.join(root,f)
                
                # For some reason extract these labels again from the filename
                cellType, animalNum, sesh, dte, epiNum, stim  = root.split('/')[-2].split('_')
                partNum = root.split('/')[-1]

                epiNum=int(epiNum.replace('EPI',''))
                partNum = int(partNum.split('-')[-1])+1
    
                # Insert more general ipDict key value pairs
                ipDict['calPreprocPath'] = biswebCaPath
                ipDict['signal'] = ippath
                ipDict['noise'] = ippath.replace('signl','noise')
                ipDict['segnum'] = str(partNum)
                ipDict['signalout'] = os.path.join(root,'signl_out.nii.gz')
                ipDict['noiseout'] = os.path.join(root,'noise_out.nii.gz')
                ipDict['debug'] = True
                ipDict['workdir'] = root
                ipDict['runoption'] = 'spatial'

                pathToFirst = root.replace('EPI'+str(epiNum), 'EPI1').replace('part-0'+str(partNum-1), 'part-00').replace(stim,'*')

                pathToFirst = glob.glob(pathToFirst)

                if len(pathToFirst) == 1:
                    pathToFirst = pathToFirst[0]

                else:
                    pathToFirst='none'
                    print('Couldnt figure out path to first image preproc')




                # Insert key value pairs specific to particular images
                # For the first image in an SLC session, generally acceptable to auto generate mask, also keep this MCRef for later
                # images in the same session
                if ('EPI1_' in root) and ('part-00' in root):

                    ipDict['createmask'] = False
                    ipDict['createmcref'] = True
                    ipDict['mask'] = os.path.join(humanMadeMasks,cellType,cellType+'_'+animalNum+'_'+sesh.replace('-','-0')+'_RotOptical_maskRPI.nii.gz')


                    # /ca2data/PreprocessedData/mcRefFiles/SLC/SLC_animal03_ses-01_RotOptical_maskRPI.nii.gz
                    ## TEMP ADD ###
                    #ipDict['truncrun'] = True



                # Other images in SLC session; use prior mask and MCRef
                elif (('EPI1_' not in root) or ('part-00' not in root)):
                    ipDict['createmask'] = False

                    ipDict['createmcref'] = False

                    #print('pathToFirst: ',pathToFirst)
                    ipDict['mcrefsignal'] = os.path.join(pathToFirst, 'rawsignl_smooth16_moco_refimg.nii.gz') 
                    ipDict['mcrefnoise'] =  os.path.join(pathToFirst, 'rawnoise_smooth16_moco_refimg.nii.gz') 
                    ipDict['mask'] = os.path.join(humanMadeMasks,cellType,cellType+'_'+animalNum+'_'+sesh.replace('-','-0')+'_RotOptical_maskRPI.nii.gz')
                    


                else:
                    raise Exception('This tif file doesnt match the expected criteria',f)

                lastFile = os.path.join(root,'signl_out.nii.gz')


                checkIpsList = ['signal','noise','mask']

                if 'mcrefsignal' in ipDict.keys():
                    checkIpsList = checkIpsList + ['mcrefsignal','mcrefnoise']


                

                checkIps = [os.path.isfile(ipDict[ipF]) for ipF in checkIpsList]
 
                ipDict2 = ipDict
                del ipDict2['mask']

                checkIps2 = [os.path.isfile(ipDict2[ipF]) for ipF in checkIpsList if ipF != 'mask']

                if all(checkIps2) and not os.path.isfile(lastFile):

                    print('Calculating for ',ippath)
                    runBiswebCa2(ipDict2)

                #spatialSignlFilePath = os.path.join(opdir,cellType,sesh,animalNum,'ca2/',f.split('.')[0].split('_part')[0],'part-*','signl_out.nii.gz')
                spatialSignlFilePath = os.path.join('/'.join(root.split('/')[:-1]),'part-*', 'signl_out.nii.gz')
                #spatialNoiseFilePath = os.path.join(opdir,cellType,sesh,animalNum,'ca2/',f.split('.')[0].split('_part')[0],'part-*','noise_out.nii.gz')
                spatialNoiseFilePath = os.path.join('/'.join(root.split('/')[:-1]),'part-*', 'noise_out.nii.gz')

                spatialSignlFiles = sorted(glob.glob(spatialSignlFilePath))
                spatialNoiseFiles = sorted(glob.glob(spatialNoiseFilePath))



                if len(spatialSignlFiles) == 3 and len(spatialNoiseFiles) == 3:

                    #oppath=os.path.join(opdir,cellType,sesh,animalNum,'ca2/',f.split('.')[0].split('_part')[0])
                    oppath = os.path.join('/'.join(root.split('/')[:-1]))

                    threePartSignlPath = os.path.join('/'.join(root.split('/')[:-1]),'rawsignl_smooth4_mococombo_threeparts.nii.gz')
                    threePartNoisePath = os.path.join('/'.join(root.split('/')[:-1]),'rawnoise_smooth4_mococombo_threeparts.nii.gz')

                    if not os.path.isfile(threePartSignlPath):
                        concatNiftis(spatialSignlFiles,threePartSignlPath)
                    if not os.path.isfile(threePartNoisePath):
                        concatNiftis(spatialNoiseFiles,threePartNoisePath)
                



                    # Instantiate input dictionary to run bisweb script
                    ipDict={}


                    # Insert more general ipDict key value pairs
                    ipDict['pythonPath'] = pythonPath
                    ipDict['calPreprocPath'] = biswebCaPath
                    ipDict['signal'] = threePartSignlPath
                    ipDict['noise'] = threePartNoisePath
                    ipDict['signalout'] = os.path.join('/'.join(root.split('/')[:-1]),'signl_out.nii.gz')
                    ipDict['noiseout'] = os.path.join('/'.join(root.split('/')[:-1]),'noise_out.nii.gz')
                    ipDict['debug'] = True
                    ipDict['workdir'] = '/'.join(root.split('/')[:-1])
                    ipDict['runoption'] = 'temporal'

                    ipDict['createmask'] = False
                    ipDict['createmcref'] = False
                    #ipDict['mask'] = os.path.join('/ca2data/PreprocessedData/mcRefFiles/',cellType,cellType+'_'+animalNum+'_'+sesh.replace('-','-0')+'_RotOptical_maskRPI.nii.gz')
                    ipDict['mask'] = os.path.join(humanMadeMasks,cellType,cellType+'_'+animalNum+'_'+sesh.replace('-','-0')+'_RotOptical_maskRPI.nii.gz')

                    lastFile = os.path.join('/'.join(root.split('/')[:-1]),'signl_out.nii.gz')

                    checkIpsList = ['signal','noise','mask']

                    checkIps = [os.path.isfile(ipDict[ipF]) for ipF in checkIpsList]
 
             
                    if all(checkIps) and not os.path.isfile(lastFile):
                        if not os.path.isdir(oppath):
                            os.makedirs(oppath)
                        print('Running temporal preprocessing for ', f.split('.')[0].split('_part')[0])
                        runBiswebCa2(ipDict)

