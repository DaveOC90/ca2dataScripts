# Calcium Scripts
## A guide to taking two wavelength widefield optical imaging data through some quality control and preprocessing steps

## Installation

### Python Scripts
If you want to use the python scripts you need to install python and have the packages detailed in install/environmentGeneral.txt installed as well. The easiest way to do this, is to install miniconda, and then use te command conda install enviromentGeneral.txt

### BIS integrated preprocessing pipeline
For the time being, the easiest way to use the preprocessing pipeline is to do so via a singularity image. 

First you need to install [singularity]()

Then you can download this [file]() or build the image using the specification file in install/thing.txt and run the following command:

```
singularity build ubuntuBIS.sif ../biswebSing.recipe
```

Once you have the image either downloaded or built you can proceed with the run instructions.

## Running the code

### Input data (tif files and smr files)
First the data should be in a BIDs like format (but not quite), for now the scripts enclosed only support the following directory structure:

```
SLC/
SLC/ses-2
SLC/ses-2/animal06
SLC/ses-2/animal06/ca2
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-00.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-01.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-02.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI2_LED_part-00.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI2_LED_part-01.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI2_LED_part-02.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI3_REST_part-00.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI3_REST_part-01.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI3_REST_part-02.tif
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17-16-06-51_619.mat
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17-16-35-57_621.mat
SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17-16-58-16_623.mat

```

Essentially the code expects data in the following pseudo format, for Tif Files: 
```
{datasetName}/ses-{sessionLabel}/{subID}/ca2/{datasetName}_{subID}_ses-{sessionLabel}_{date}_{runNumber}_{taskLabel}_part-{partNumber}.tif
```
and for electrical recording files: 
```
{datasetName}/ses-{sessionLabel}/{subID}/ca2/{datasetName}_{subID}_ses-{sessionLabel}_{date}.mat
```

The scripts are overly prescritptive at the moment, but will be made more general with time.


### Splitting wavelengths

Now we cam start buidling a directory containing nifti files and csvs, corresponding to the wavelength specific data and trigger timing respectively. The following command will aid us:

```
python genTrigsNii.py organizedData/ preprocDir/ qcFigs/ triggerFix.csv '*/*/*/*/' 0

```

This code wil try to split out the tif files into "signal" and "noise" automatically. If the automatic split is successful, there will now be nifti and csv data in the output directory in thg following format: 

```
preprocDir/SLC
preprocDir/SLC/ses-2
preprocDir/SLC/ses-2/animal06
preprocDir/SLC/ses-2/animal06/ca2
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-00
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-00/OpticalOrder.csv
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-00/rawsignl.nii.gz
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-00/rawnoise.nii.gz
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-01
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-01/OpticalOrder.csv
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-01/rawsignl.nii.gz
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-01/rawnoise.nii.gz
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-02
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-02/OpticalOrder.csv
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-02/rawsignl.nii.gz
preprocDir/SLC/ses-2/animal06/ca2/SLC_animal06_ses-2_2019-01-17_EPI1_REST/part-02/rawnoise.nii.gz
```

As well as this, there will be quality control figures present in the qcFigs directory. You should look at each of these to ensure that the automatic split worked appropriately. Below are two examples, one correct, one incorrect, of "successfully split" data. For the incorrect example, you should use the semi automated functions detailed later.

Correct           |  Incorrect
:-------------------------:|:-------------------------:
![](figs/correct.png)  |  ![](figs/incorrect.png)

If the data cannot be be split automatically, there will not be any correspodning files in the output directory. However, there are semi-automatic features that can split the data
with your supervision. Upon first pass of the data the code will create a spreadsheet named as you have set it, in this case "triggerFix.csv". The spreadsheet will be populated with the names of the files in your input directory automatically, and will look something like this:

|    | Img                                             |   CrossedTrigs |   autoFix |   simpFix |   sdFlag |   sdVal |   writeImgs |   manualOverwrite |   splitMethod |   dbscanEps |
|---:|:------------------------------------------------|---------------:|----------:|----------:|---------:|--------:|------------:|------------------:|--------------:|------------:|
|  0 | SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-00 |                |           |           |          |         |             |                   |               |             |
|  1 | SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-01 |                |           |           |          |         |             |                   |               |             |
|  2 | SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-02 |                |           |           |          |         |             |                   |               |             |
|  3 | SLC_animal06_ses-2_2019-01-17_EPI2_LED_part-00  |                |           |           |          |         |             |                   |               |             |
|  4 | SLC_animal06_ses-2_2019-01-17_EPI2_LED_part-01  |                |           |           |          |         |             |                   |               |             |
|  5 | SLC_animal06_ses-2_2019-01-17_EPI2_LED_part-02  |                |           |           |          |         |             |                   |               |             |
|  6 | SLC_animal06_ses-2_2019-01-17_EPI3_REST_part-00 |                |           |           |          |         |             |                   |               |             |
|  7 | SLC_animal06_ses-2_2019-01-17_EPI3_REST_part-01 |                |           |           |          |         |             |                   |               |             |
|  8 | SLC_animal06_ses-2_2019-01-17_EPI3_REST_part-02 |                |           |           |          |         |             |                   |               |             |


For any data that could not be split automatically you should put a "1" in the "CrossedTrigs" column next to the filename. You can then rerun the code and it will generate a first pass at two different methods for generating wavelegnth labels for the data based on the mean timeseries of the tif file. The "simpFix" method assumes that the wavelengths were acquired in a simple interleaved fashion, without any error: cyan,uv,cyan,uv.... etc. The second method (autoFix) is useful in the case that there is a skipped frame at some point (in which case the order of the wavelengths will swap at some point). It is based on the mean intensity of each frame, and assumes that there are two distributions of data (cyan and uv) with significantly different means. In this case it will assign all frames in the distribution with the higher mean intensity to cyan, and the lower inensity to uv. The code will generate plots of both methods applied to the data and deposit them in the directory called qcFigs/triggerFIx (autogenerated). You can look at these and if either the auto fix or the simp fix gives satisfactory results you can then put a "1" in the "writeImgs" column in the spreadsheet, rerun the code and the nifti files will be written to the output directory.

Data with dropped trigger:
![](figs/droppedTrigs.png) 

Proposed fixes (autoFix vs simpFix):
![](figs/droppedTrigsFix.png)


For example in the above image, if you are happy with the autoFix solution, you can edit the csv file like so:
|    | Img                                             |   CrossedTrigs |   autoFix |   simpFix |   sdFlag |   sdVal |   writeImgs |   manualOverwrite |   splitMethod |   dbscanEps |
|---:|:------------------------------------------------|---------------:|----------:|----------:|---------:|--------:|------------:|------------------:|--------------:|------------:|
|  0 | SLC_animal06_ses-2_2019-01-17_EPI1_REST_part-00 |        1       |     1     |           |          |         |     1       |                   |               |             |
Then rerun the code, and the data will output with the correct split of cyan and uv. 

Addional notes:

- The autoFix method works off of the distribution of the data, but can be thrown off if the cyan and uv distributions are far in terms of mean magnitude and artifactual frame is relatively close, or vice versa. In one of these cases you can put a "1" in the sdFlag column, and then enter a value in the sdVal column. The default sdVal is 8, a higher value will include artifactual frames which have relatively high/low magnitudes, and a lower value will exlcude those with magnitudes closer to the non-artifactual dat.
If the data is too challenging to split using the above methods, it is possible to manually create a trigger file. You can put it is this directory:

- Under the directory the folder structure should be similar to the output directory. In this case the file will be copied into the output directory, provided there is a one in the "manualOverwrite" column.

- The splitMethod and dbscanEps columns are part of a function that is under development, please ignore. 

3) Preprocessing

The preprocessing code is currenty best used as a singularity container. It is available for download [here]() 

It can be used as follows:

```
singularity exec ubuntuBIS.simg python3 calciumPreprocess2.py --signal data/SLC/ses-1/animal01/ca2/SLC_animal01_ses-1_2019-01-09_EPI1_REST/part-02/rawsignl.nii.gz --noise data/SLC/ses-1/animal01/ca2/SLC_animal01_ses-1_2019-01-09_EPI1_REST/part-02/rawnoise.nii.gz --signalout data/SLC/ses-1/animal01/ca2/SLC_animal01_ses-1_2019-01-09_EPI1_REST/part-02/signl_out.nii.gz --noiseout data/SLC/ses-1/animal01/ca2/SLC_animal01_ses-1_2019-01-09_EPI1_REST/part-02/noise_out.nii.gz --debug True --workdir data/SLC/ses-1/animal01/ca2/SLC_animal01_ses-1_2019-01-09_EPI1_REST/part-02/ --runoption spatial --createmask False --createmcref True --mask data/SLC_animal01_ses-01_RotOptical_maskRPI.nii.gz
```

The arguments are detailed here:



And here is a description of the outputs:


There is a script cal runPreproc.py (in progress) to provide easy preprocessing of the bids like directory output from genTrigs.py. It requires the following:



And can be used like so:
```

```

The way the data is setup at the moment, it is required that we do spatial prepreprocessing first, then stitch together three image parts, and do temporal processing. This script will perform these operations sequentially. 

