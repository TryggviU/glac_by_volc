# Glaciers by volcanoes - glac_by_volc

Repository for code used to locate glaciers within a radial distance from volcanoes, and perform analysis on the geometries and dynamics of those glaciers. 



## Processing

### Locate glaciers by volcanoes

The code effectively accomplishes the same as that of [Edwards et al. (2020)](https://doi.org/10.1016/j.gloplacha.2020.103356), but does so automatically and allows the user to specify the search radius. Besides downloading this repository and the data (see [Data](#data)), the code is fully automated, with optional user inputs.

### Timeseries of glacier area

The code extracts glacier area from both synthetic aperature radar (SAR) and multispectral/optical images from Sentinel 1 and 2, respectively. The SAR scenes are processed into InSAR pairs, and glacier geometries are extracted by applying a threshold to the coherence maps between pairs. The optical scenes are stitched into cloud- and snow-free mosaics, and snow and ice pixels in the mosaic are extracted by: (i) applying a threshold to the [normalized difference snow index (NDSI)](https://custom-scripts.sentinel-hub.com/sentinel-2/ndsi/) that is computed from the sensor's bands, and (ii) a combinations of band thresholds according to the [Level-2A Algorithm](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm-overview).



## Data

### RGI and GPV

Prior to any analysis, it is assumed that the user has previously downloaded the global glacier and volcano datasets from:
 - [Randolphs Glacier Inventory (RGI)](http://www.glims.org/rgi_user_guide/welcome.html): The version used during the developement of the code is v7.0.
 - [Global Volcanism Program (GVP)](https://volcano.si.edu/volcanolist_holocene.cfm): The GVP data is downloaded as an Microsoft Excel file by default, and the user must convert it to a `.csv` file prior to executing scripts.

and stored the data within their respective subdirectories, [data/RGI](./data/RGI) and [data/GVP](./data/GVP). The resulting processed data is then stored within the subdirectory [data_processed](./data_processed).

### Satellite imagery

The code uses the facilities made available by 
 - [Alaska Satellite Facility (ASF)](https://asf.alaska.edu/): to produce InSAR products from Sentinel 1 scenes of an area of interest.
 - [Google Earth Engine (GEE)](https://earthengine.google.com/): to produce cloud free mosaics from Sentinel 2 scenes of an area of interest.



## Hardware

All the code presented in this repository was developed and executed on a relatively basic labtop with the following specs:
 - System Model:	HP ZBook Power 15.6 inch G9 Mobile Workstation PC
 - OS: Windows 10 Enterprise
 - Processor:	12th Gen Intel(R) Core(TM) i7-12800H, 2400 Mhz, 14 Core(s), 20 Logical Processor(s)
 - Memory: 32 GB
 - Storage: 500 GB. This is only enough for complete analysis of a few volcanoes (spanning 2015-2023), as the compressed data for a single volcano can be of up to ~20 GB per year.

The code was developed on a Windows machine, but should work for other operating systems (Linux/macOS) as well. The [tool scripts](./src/tools/ps1) used for directory/data organization and preparation were written in `PowerShell`, which may require the installation of appropriate terminals on Linux/macOS machines. If that is not feasible, those scripts could else be easily translated to `bash`.
