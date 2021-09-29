# Calcium Scripts
## A guide to taking two wavelength widefield optical imaging data through some quality control and preprocessing steps

### Installation

If you want to use the python scripts you need to install python and have the packages detailed in install/environmentGeneral.txt installed as well. The easiest way to do this, is to install miniconda, and then use te command conda install enviromentGeneral.txt

If you want to run the preprocessing singularity image you need to install [singularity]()

The you can download this [file]() or build the image using the specification file in install/thing.txt and run the following command:
```

```


### Running the code
 
1) First the data should be in a BIDs like format (but not quite), for now the scripts enclosed only support the following directory structure:

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

2) Once the code is in this format, you can now start buidling a directoy containing nifti files and csvs, corresponding to the wavelength specific data and trigger timing respectively.

```
python ~/gitrepos/ca2dataScripts/genTrigsNii.py organizedData/ preprocDir/ qcFigs/ triggerFix.csv '*/*/*/*/' 0

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

As well as this, there will be quality control figures present in the qcFigs directory. You should look at each of these to ensure that the automatic split worked appropriately. 

If the data cannot be be split automatically, there will not be any correspodning files in the output directory. However, there are semi-automatic features that can split the data
with your supervision. Upon first pass of the data the code will create a spreadsheet named as you have set it, in this case "triggerFix.csv". The spreadsheet will be populated with the names of the files in your input directory automatically, and will look something like this:

|    | Img  &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;    |   CrossedTrigs |   autoFix |   simpFix |   sdFlag |   sdVal |   writeImgs |   manualOverwrite |   splitMethod |   dbscanEps |
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



3) Preprocessing

The preprocessing code is currenty best used as a singularity container. It is available for download [here]() 

It can be used as follows:

```

```

The arguments are detailed here:



And here is a description of the outputs:


There is a script (in progress) to provide easy preprocessing of the bids like directory output from genTrigs.py. It requires the following:



And can be used like so:
```

```

