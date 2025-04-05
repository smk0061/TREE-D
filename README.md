# TREE-D
Open-source UAS imagery dataset with detailed tree species annotations. Includes standardized protocols for RGB, multispectral and LiDAR data collection. Data integrity standards ensures consistent, public contributions for machine learning model development. MIT Licensed.

Product of the West Virginia University Natural Resource Analysis Center (NRAC)<br>
Visit us at https://www.nrac.wvu.edu/

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
- `--contributor`: Contributor/Research Team Name (Required)
- `--description`: Dataset description

### Example
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

### Acknowledgements:<br>
Funding for this project has been provided through the Tree Research & Education Endowment Fund and the Utility Arborist Research Fund<br>
Learn more at https://treefund.org/

<div style="display: flex; justify-content: center; align-items: center; gap: 20px;">
    <img src="repo_imgs/NRAC_Davis_Logo2025_Smaller.jpg" alt="NRAC Logo" height="150" style="max-width: 300px; object-fit: contain;"/>
    <img src="repo_imgs/TREE-Fund-Logo-No-Tag-3_2-1-784x445.png" alt="TREEFund Logo" height="150" style="max-width: 300px; object-fit: contain;"/>
</div>
