# TREE-D
Open-source UAS imagery dataset with detailed tree species annotations. Includes standardized protocols for RGB, multispectral and LiDAR data collection. Data integrity standards ensures consistent, public contributions for machine learning model development. MIT Licensed.

Product of the West Virginia University Natural Resource Analysis Center (NRAC)<br>
Visit us at https://www.nrac.wvu.edu/ or contact lnkinder@mail.wvu.edu with contributions.

*This is an early version of this product. Future work will involve creating a web portal for submitting contributions and generating custom datasets with selected species and image attributes.*<br>
*The <b>Species Dictionary</b> is still under construction. Contributions will still be accepted but will be changed in the future to match `id` values.*

## Requirements
### System Requirements
- Python 3.6+

### Python Dependencies
- geopandas
- pandas
- rasterio
- shapely

## Clone the Repository
```bash
git clone https://github.com/smk0061/TREE-D.git
cd TREE-D
```

## Usage
```bash
python tree-d_ann_creation.py \
    shapefile_path \
    image_folder \
    output_json \
    --taxonomy taxonomy.csv \
    --image-metadata image_metadata.csv \
    --contributor "Your Name" \
    --description "Your dataset description"
```

### Required Arguments
- `shapefile_path`: Path to input shapefile with tree crown polygons
- `image_folder`: Folder containing source imagery
- `output_json`: Path for generated JSON annotation file
- `--taxonomy`: CSV file with taxonomic information
- `--image-metadata`: CSV file with image metadata
- `--contributor`: Contributor/Research Team Name
- `--description`: Dataset description

### Script Example
```bash
python tree-d_ann_creation.py \
    data/tree_crowns.shp \
    data/imagery \
    output/tree_annotations.json \
    --taxonomy data/species_taxonomy.csv \
    --image-metadata data/image_metadata.csv \
    --contributor "NRAC Research Team" \
    --description "WVU Forest Mapping Project 2025"
```

### Required Input Files
#### Taxonomy CSV
The taxonomy CSV defines the taxonomic hierarchy for included families/genera/species.
#### Required columns:
- `id`: Numeric identifier for taxonomy (referenced in shapefile). See <b>Species Dictionary</b> for more information.
- `family`: Taxonomic family name (required).
#### Optional columns:
- `genus`: Genus name (defaults to "Unspecified" if missing).
- `species`: Species name (defaults to "sp." if missing).
#### Example taxonomy.csv:
```bash
id,family,genus,species
1,Pinaceae,Pinus,strobus
2,Fagaceae,Quercus,rubra
3,Aceraceae,Acer,saccharum
4,Juglandaceae,,
```
#### Image Metadata CSV
The image metadata CSV defines the image attributes and sensor specifications.
#### Required columns:
- `file_name`: Exact filename of the image (with extension).
- `sensor`: Camera or sensor used.
#### Example for RGB image:
```bash
file_name,sensor,image_type,date_captured
WVUResearchForest.tif,Sentera6X,RGB,2025-08-21
```
#### Example for multispectral image:
```bash
file_name,sensor,image_type,date_captured,blue_wavelength,blue_bandwidth,green_wavelength,green_bandwidth,red_wavelength,red_bandwidth,redEdge_wavelength,redEdge_bandwidth,nir_wavelength,nir_bandwidth
MS_WVUResearchForest.tif,Sentera6X,Multispectral,2025-08-21,475,30,550,20,670,30,715,10,840,20
```
#### Shapefile Requirements
- Must contain polygon geometries for tree crowns.
- Each polygon must have a `species_id` attribute that matches an `id` in the taxonomy CSV.
### Acknowledgements:<br>
Funding for this project has been provided through the Tree Research & Education Endowment Fund and the Utility Arborist Research Fund<br>
Learn more at https://treefund.org/

<div style="display: flex; justify-content: center; align-items: center; gap: 20px;">
    <img src="repo_imgs/NRAC_Davis_Logo2025_Smaller.jpg" alt="NRAC Logo" height="150" style="max-width: 300px; object-fit: contain;"/>
    <img src="repo_imgs/TREE-Fund-Logo-No-Tag-3_2-1-784x445.png" alt="TREEFund Logo" height="150" style="max-width: 300px; object-fit: contain;"/>
</div>
