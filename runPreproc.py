import os
import numpy as np
import pandas as pd
import nibabel as nib
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

    acceptableTerms = ['pythonPath','calPreprocPath','blue','opticalorder','segnum','createmcref','createmask','blueout','uvout','debug','workdir','mcrefblue','mcrefuv','mask']


    if not all([k in acceptableTerms for k in ipDict.keys()]):
        raise Exception('At least one of the keys in this dictionary is not an acceptable term for the preprocessing pipeline:',ipDict)


    cmd = '{0[pythonPath]} {0[calPreprocPath]} '.format(ipDict)+' '.join(['--%s %s' % kv for kv in ipDict.items() if not any(kv[0] == aT for aT in ['pythonPath','calPreprocPath'])])






# What runs, when you run the script from the command line
if __name__ == '__main__':

   

    # Input arguments    
    parser=argparse.ArgumentParser(description='Run script to iterate over organized calcium data and run preprocessing')
    parser.add_argument('organizedDataPath',type = str, help="Path to the bids like organized data")
    parser.add_argument('outputDir',type=str,help="Path to output directory")
    parser.add_argument('humanMadeMasks',type=str,help='Path to where we keep the manually made masks')
    parser.add_argument('pythonPath',type=str,help="Path to python version to run")
    parser.add_argument('biswebCaPath',type=str,help='Path to bisweb calcium preproc script')
    

    args=parser.parse_args()

    # Setup input and output directories 
    ipdir=args.organizedDataPath
    opdir=args.outputDir

    # Paths to python install and bisweb install to use
    pythonPath=args.pythonPath
    biswebCaPath=args.biswebCaPath
    humanMadeMasks = args.humanMadeMasks


    #ftags = ['PV_animal64_ses-2',
    #     'SOM_animal35_ses-1',
    #     'VIP_animal24_ses-1',
    #     'GLIA_animal59_ses-1']


    # Edit this to restrict the data it runs on
    ftags = ['SLC']


    # Walk through input directory
    for root,dirs,fs in os.walk(ipdir):
        for f in sorted(fs):
            #if f.endswith('.tif'):
            #if f.endswith('.tif') and ('EPI1' in f) and ('part-00' in f) and ('SLC' in f) and ('animal55' in f) and ('ses-1' in f) :
            if f.endswith('.tif') and any([ft in f for ft in ftags]):
                #print('Reading: ',f)

                # Instantiate input dictionary to run bisweb script
                ipDict={}


                # Parse input path and extract labels
                ippath=os.path.join(root,f)
                idPath=root.replace(ipdir,'')

                # Gather all trigger order csvs in this folder into list
                csvs=list(sorted(glob.glob(os.path.join(root,'*Optical.csv'))))
                # Gather all tiffs in this folder into list
                tiffs=list(sorted(glob.glob(os.path.join(root,'*.tif'))))
                
                # For some reason extract these labels again from the filename
                celltype, animalNum, sesh, dte, epiNum, stim, partNum = f.split('.')[0].split('_')
                epiNum=int(epiNum.replace('EPI',''))
                partNum = int(partNum.split('-')[-1])+1

                trigFile = ippath.replace('.tif','OpticalOrder.csv')


                # Insert more general ipDict key value pairs
                ipDict['pythonPath'] = pythonPath
                ipDict['calPreprocPath'] = biswebCaPath
                ipDict['blue'] = ippath
                ipDict['opticalorder'] = trigFile
                ipDict['segnum'] = str(partNum)
                ipDict['blueout'] = os.path.join(oppath,'blue_out.nii.gz')
                ipDict['uvout'] = os.path.join(oppath,'uv_out.nii.gz')
                ipDict['debug'] = True
                ipDict['workdir'] = oppath

                # Insert key value pairs specific to particular images
                # For the first image in an SLC session, generally acceptable to auto generate mask, also keep this MCRef for later
                # images in the same session
                if ('EPI1' in f) and ('part-00' in f) and ('SLC' in f):
                    ipDict['createmask'] = True
                    ipDict['createmcref'] = True

                # Other images in SLC session; use prior mask and MCRef
                elif ('EPI1' not in f) and ('part-00' not in f) and ('SLC' in f):
                    ipDict['createmask'] = False
                    ipDict['createmcref'] = False
                    pathToFirst = oppath.replace('EPI'+str(epiNum), 'EPI1').replace('part-0'+str(partNum-1), 'part-00').replace(stim,'REST')
                    print('pathToFirst: ',pathToFirst)
                    ipDict['mcrefblue'] = os.path.join(pathToFirst, 'calcium_blue_movie_smooth_mcRef.nii.gz') 
                    ipDict['mcrefuv'] =  os.path.join(pathToFirst, 'calcium_uv_movie_smooth_mcRef.nii.gz') 
                    ipDict['mask'] = os.path.join(pathToFirst, 'MSEMask.nii.gz') 
                    
                # For non SLC images, that are first in their session, we want to use their MCRef
                # but we want a human made mask
                elif ('SLC' not in f) and ('EPI1' in f) and ('part-00' in f):
                    ipDict['createmask'] = False
                    ipDict['createmcref'] = True
                    
                    ipDict['mask'] = os.path.join(humanMadeMasks, cellType+'_'+animalNum+'_'+ses+'_'+dte+'_EPI1_REST_part-00mcRef_maskEdit.nii.gz')
                
                # For non SLC images, that are  not first in their session, we want to use prior MCRef
                # and we want a human made mask
                elif ('SLC' not in f) and not all([f2 in f for f2 in ['EPI1','part-00']]):
                    ipDict['createmask'] = False
                    ipDict['createmcref'] = False

                    pathToFirst = oppath.replace('EPI'+str(epiNum), 'EPI1').replace('part-0'+str(partNum-1), 'part-00').replace(stim,'REST')
                    print('pathToFirst: ',pathToFirst)
                    ipDict['mcrefblue'] = os.path.join(pathToFirst, 'calcium_blue_movie_smooth_mcRef.nii.gz') 
                    ipDict['mcrefuv'] =  os.path.join(pathToFirst, 'calcium_uv_movie_smooth_mcRef.nii.gz')
                    ipDict['mask'] = os.path.join(humanMadeMasks, cellType+'_'+animalNum+'_'+ses+'_'+dte+'_EPI1_REST_part-00mcRef_maskEdit.nii.gz')

                else:
                    raise Exception('This tif file doesnt match the expected criteria')

                lastFile = os.path.join(oppath,'blue_out.nii.gz')

                if not os.path.isfile(lastFile):
                    oppath=os.path.join(opdir,cellType,ses,animalNum,'ca2/',f.split('.')[0])
                    if not os.path.isdir(oppath):
                        os.makedirs(oppath)
                    print('Calculating for ',ippath)
                    runBiswebCa2(ipDict)
