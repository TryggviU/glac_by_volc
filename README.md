# Glaciers by volcanoes - `glac_by_volc`

Repository for code\* used to locate glaciers within a radial distance from volcanoes, and perform analysis on the geometries and dynamics of those glaciers. 

> \*The code will be made available upon publication of results.



## Methods

### Locate glaciers by volcanoes

We locate glaciers within the vicinity of volcanoes by comparing two databases: The ``Volcanoes of the World'' of the [Smithsonian Global Volcanism Program (GVP)](https://volcano.si.edu/volcanolist_holocene.cfm) -- a complete list of Earth's Holocene volcanoes; and the [Randolph Glacier Inventory (RGI) version 7.0](http://www.glims.org/rgi_user_guide/welcome.html) -- a dataset containing outlines and information for all glaciers in the World, excluding the ice sheets of Greenland and Antarctica, in the year 2000. We locate all RGI glacier geometries within a radial search area around each GVP volcano with Python scripts utilising the geospatial data package [GeoPandas](https://geopandas.org/). The code effectively accomplishes the same as that of [Edwards et al. (2020)](https://doi.org/10.1016/j.gloplacha.2020.103356) who used a search radius of 5 km, but does so automatically and allows the user to specify the search radius. Besides downloading this repository and the data (see [Data](#data)), the code is fully automated, with optional user inputs.

### Relative glacier elevations

Though we intend to look at glaciers on a global scale, it is necessary to look at each individual glacier within a local context to discern any anomalies or trends. [Howcutt et al. (2023)](https://doi.org/10.1130/G51411.1) looked at the elevation of glaciers surrounding several volcanoes in South America. They used the deviance of the mean ELA of glaciers on a volcano, $\bar{z}\_{\rm ELA}^{\rm volcanic}$, compared to the mean ELA of nearby glaciers, $\bar{z}\_{\rm ELA}^{\rm proximal}$, as

$$\Delta \bar{z}\_{\rm ELA} = \bar{z}\_{\rm ELA}^{\rm volcanic} - \bar{z}\_{\rm ELA}^{\rm proximal}.$$

We adopt the methodology of [Howcutt et al. (2023)](https://doi.org/10.1130/G51411.1), but adapt it to use the median glacier elevations, $\tilde{z}$, instead of ELAs. We compute the relative median elevation for each ($i$-th) individual glacier in a given region

$$\Delta \tilde{z}\_{i} = \tilde{z}\_{i} - \bar{\tilde{{z}}},$$

where 

$$\bar{\tilde{z}} = \frac{1}{n} \sum_{i=1}^{n} \tilde{z}\_i$$

is the average median glacier elevation within the region, comprising of $n$ glaciers.

### Timeseries of glacier area

The code extracts glacier area from both synthetic aperature radar (SAR) and multispectral/optical images from Sentinel 1 and 2, respectively [(Barella et al., 2022)](https://doi.org/10.1109/JSTARS.2022.3179050). The SAR scenes are processed into InSAR pairs, and glacier geometries are extracted by applying a threshold to the coherence maps between pairs. The optical scenes are stitched into cloud- and snow-free mosaics, and snow and ice pixels in the mosaic are extracted by: (i) applying a threshold to the [normalized difference snow index (NDSI)](https://custom-scripts.sentinel-hub.com/sentinel-2/ndsi/) that is computed from the sensor's bands, and (ii) a combinations of band thresholds according to the [Level-2A Algorithm](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm-overview).



## Data

### RGI and GPV

Prior to any analysis, it is assumed that the user has previously downloaded the global glacier and volcano datasets from:
 - [Randolph Glacier Inventory (RGI)](http://www.glims.org/rgi_user_guide/welcome.html): The version used during the developement of the code is v7.0.
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
 - Storage: 500 GB. ATH!: This is only enough for complete satellite analysis of a few volcanoes (spanning 2015-2023), as the compressed data for a single volcano can be of up to ~20 GB per year.

The code was developed on a Windows machine, but should work for other operating systems (Linux/macOS) as well. The [tool scripts](./tools) used for directory/data organization and preparation were written in `PowerShell`, which may require the installation of appropriate terminals on Linux/macOS machines. If that is not feasible, those scripts could else be easily translated to `bash`.
