"""
TREE-D Annotation Generator
============================================

This script converts shapefiles containing tree crown polygons into a structured JSON 
annotation format for the UAV TREE-D dataset.

Features:
- Processes shapefiles with polygon features for tree crowns
- Extracts image metadata from image
- Supports taxonomy information for different tree species
- Generates standardized JSON format for machine learning applications
- Handles both standard RGB and multispectral imagery
- Defines spectral bands and their properties

Requirements:
- Python 3.6+
- geopandas
- pandas
- rasterio
- shapely

Usage:
    python tree-d_ann_creation.py shapefile_path image_folder output_json \
        --taxonomy taxonomy.csv \
        --image-metadata image_metadata.csv \
        [--contributor "Your Name"] \
        [--description "Dataset description"]

Copyright (c) 2025
License: MIT

Product of the West Virginia University Natural Resource Analysis Center (NRAC)

Acknowledgements:
Funding for this project has been provided through the Tree Research & Education Endowment Fund and the Utility Arborist Research Fund.
Learn more at https://treefund.org/
"""

import os
import json
import argparse
import glob
from datetime import datetime
from pathlib import Path
import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import Polygon, mapping

def print_status(message, message_type="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{message_type}] {message}")


def process_image(img_path, image_id, image_metadata=None):
    file_name = os.path.basename(img_path)
    
    try:
        with rasterio.open(img_path) as src:
            width = src.width
            height = src.height
            resolution = src.transform[0]
            count = src.count
        
        image = {
            "id": image_id,
            "file_name": file_name,
            "width": width,
            "height": height,
            "date_captured": "",
            "julian_day": "",
            "time_captured": "",
            "license": 1,
            "sensor": "",
            "altitude": 0,
            "resolution": resolution,
            "state": "",
            "county": "",
            "location_description": ""
        }
        
        if not image_metadata or file_name not in image_metadata:
            print_status(f"Required metadata missing for image: {file_name}", "ERROR")
            return None
        
        meta = image_metadata[file_name]
        
        required_fields = ["sensor"]
        for field in required_fields:
            if field not in meta:
                print_status(f"Required field '{field}' missing from metadata for {file_name}", "ERROR")
                return None
        
        for key, value in meta.items():
            if key == 'file_name':
                continue
            
            if '_' in key and key.split('_')[0] in ["blue", "green", "red", "redEdge", "nir"] + [f"band_{i}" for i in range(1, 20)]:
                continue
            else:
                image[key] = value
        
        image_type = meta.get("image_type", "RGB").lower()
        image["spectral_bands"] = {}
        
        if image_type == "rgb":
            if count >= 3:
                image["spectral_bands"] = {
                    "red": {"order": 1},
                    "green": {"order": 2},
                    "blue": {"order": 3}
                }
                
                for band in ["red", "green", "blue"]:
                    if f"{band}_wavelength" in meta:
                        image["spectral_bands"][band]["wavelength"] = meta[f"{band}_wavelength"]
                    if f"{band}_bandwidth" in meta:
                        image["spectral_bands"][band]["bandwidth"] = meta[f"{band}_bandwidth"]
            else:
                print_status(f"RGB image {file_name} has fewer than 3 bands ({count})", "WARNING")
                
        elif image_type == "multispectral":
            available_bands = set()
            for key in meta.keys():
                if '_' in key:
                    band_name = key.split('_')[0]
                    if band_name in ["blue", "green", "red", "redEdge", "nir"] or band_name.startswith("band_"):
                        available_bands.add(band_name)
            
            if not available_bands:
                print_status(f"No band information found for multispectral image {file_name}", "ERROR")
                return None
            
            for i, band_name in enumerate(sorted(available_bands)):
                wavelength = meta.get(f"{band_name}_wavelength")
                bandwidth = meta.get(f"{band_name}_bandwidth")
                
                if wavelength is None or bandwidth is None:
                    print_status(f"Skipping band {band_name} due to missing wavelength or bandwidth", "WARNING")
                    continue
                
                image["spectral_bands"][band_name] = {
                    "wavelength": wavelength,
                    "bandwidth": bandwidth,
                    "order": i + 1
                }
            
            if not image["spectral_bands"]:
                print_status(f"No valid bands found for multispectral image {file_name}", "ERROR")
                return None
        else:
            print_status(f"Unknown image type '{image_type}' for {file_name}. Must be 'RGB' or 'Multispectral'.", "ERROR")
            return None
        
        return image
        
    except Exception as e:
        print_status(f"Error reading {img_path}: {e}", "ERROR")
        return None


def shapefile_to_json_annotations(
    shapefile_path,
    image_folder,
    output_json_path,
    taxonomy_csv,
    image_metadata_csv,
    dataset_info=None
):
    start_time = datetime.now()
    print_status(f"Running: {start_time}")
    
    json_data = {
        "info": {
            "description": "TREE-D Contribution",
            "url": "https://github.com/smk0061/TREE-D",
            "version": "1.0",
            "year": str(datetime.now().year),
            "contributor": "",
            "date_created": datetime.now().strftime("%Y-%m-%d")
        },
        "licenses": [
            {
                "id": 1,
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            }
        ],
        "categories": [],
        "images": [],
        "annotations": []
    }
    
    if dataset_info:
        json_data["info"].update(dataset_info)
    
    try:
        if not os.path.exists(taxonomy_csv):
            print_status(f"Taxonomy CSV not found: {taxonomy_csv}", "ERROR")
            return False
            
        df_taxonomy = pd.read_csv(taxonomy_csv)
        print_status(f"Loaded taxonomy data with {len(df_taxonomy)} species")
        
        required_columns = ["id", "family"]
        missing_columns = [col for col in required_columns if col not in df_taxonomy.columns]
        if missing_columns:
            print_status(f"Taxonomy CSV missing required columns: {missing_columns}", "ERROR")
            return False
        
        if "genus" not in df_taxonomy.columns:
            print_status("No genus column found in taxonomy CSV. Adding 'Unspecified' as default genus.", "WARNING")
            df_taxonomy["genus"] = "Unspecified"
        
        if "species" not in df_taxonomy.columns:
            print_status("No species column found in taxonomy CSV. Adding 'sp.' as default species.", "WARNING")
            df_taxonomy["species"] = "sp."
        
        species_id_map = {}
        
        for _, row in df_taxonomy.iterrows():
            species_id = row["id"]
            family = row["family"]
            genus = row["genus"]
            species = row["species"]
            
            if not family:
                print_status(f"Missing family for taxonomy ID {species_id}. Family is required.", "ERROR")
                return False
                
            if not genus or genus.lower() == "unspecified":
                genus = "Unspecified"
                
            if not species:
                species = "sp."
                
            if genus == "Unspecified" and species != "sp.":
                print_status(f"Setting species to 'sp.' for entry with Unspecified genus (ID: {species_id})", "WARNING")
                species = "sp."
            
            category_id = species_id
            
            category = {
                "id": category_id,
                "family": family,
                "genus": genus,
                "species": species
            }
            
            json_data["categories"].append(category)
            species_id_map[species_id] = category_id
            
    except Exception as e:
        print_status(f"Error processing taxonomy CSV: {e}", "ERROR")
        return False
    
    try:
        if not os.path.exists(image_metadata_csv):
            print_status(f"Image metadata CSV not found: {image_metadata_csv}", "ERROR")
            return False
            
        df_image_meta = pd.read_csv(image_metadata_csv)
        print_status(f"Loaded image metadata with {len(df_image_meta)} entries")
        
        if "file_name" not in df_image_meta.columns:
            print_status("Image metadata CSV must contain a 'file_name' column", "ERROR")
            return False
        
        image_metadata = {}
        for _, row in df_image_meta.iterrows():
            file_name = row["file_name"]
            image_metadata[file_name] = row.to_dict()
            
    except Exception as e:
        print_status(f"Error processing image metadata CSV: {e}", "ERROR")
        return False
    
    ortho_image_path = None
    for ext in ['.tif', '.tiff', '.jpg', '.jpeg', '.png']:
        matches = glob.glob(os.path.join(image_folder, f'*{ext}'))
        if matches:
            ortho_image_path = matches[0]
            break
    
    if not ortho_image_path:
        print_status(f"No image found in {image_folder}", "ERROR")
        return False
    
    ortho_image_name = os.path.basename(ortho_image_path)
    print_status(f"Found image: {ortho_image_name}")
    
    image_id = 1
    image = process_image(ortho_image_path, image_id, image_metadata)
    
    if not image:
        print_status(f"Error processing image", "ERROR")
        return False
    
    json_data["images"].append(image)
    print_status("Image processed successfully")
    
    try:
        print_status(f"Reading shapefile: {shapefile_path}")
        gdf = gpd.read_file(shapefile_path)
        print_status(f"Loaded shapefile with {len(gdf)} features")
        
        required_columns = ["species_id"]
        missing_columns = [col for col in required_columns if col not in gdf.columns]
        if missing_columns:
            print_status(f"Shapefile missing required columns: {missing_columns}", "ERROR")
            return False
        
    except Exception as e:
        print_status(f"Error loading shapefile: {e}", "ERROR")
        return False
    
    print_status("Processing annotations for image")
    
    try:
        with rasterio.open(ortho_image_path) as src:
            transform = src.transform
    except Exception as e:
        print_status(f"Error opening image: {e}", "ERROR")
        return False
    
    annotation_id = 1
    skipped_count = 0
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        if not isinstance(geom, Polygon):
            print_status(f"Skipping non-polygon geometry at index {idx}", "WARNING")
            skipped_count += 1
            continue
        
        species_id = row.get('species_id')
        if species_id in species_id_map:
            category_id = species_id_map[species_id]
        else:
            print_status(f"Species ID {species_id} not found in taxonomy mapping. Skipping.", "WARNING")
            skipped_count += 1
            continue
            
        try:
            geo_coords = list(geom.exterior.coords)
            pixel_coords = []
            
            for x, y in geo_coords:
                px, py = ~transform * (x, y)
                pixel_coords.append((px, py))
            
            from shapely.geometry import Polygon as ShapelyPolygon
            pixel_poly = ShapelyPolygon(pixel_coords)
            
            coords = list(pixel_poly.exterior.coords)
            flat_coords = []
            for coord in coords:
                flat_coords.extend([coord[0], coord[1]])
            segmentation = [flat_coords]
            
            minx, miny, maxx, maxy = pixel_poly.bounds
            bbox = [minx, miny, maxx - minx, maxy - miny]
            
            area = pixel_poly.area
            
        except Exception as e:
            print_status(f"Error converting coordinates for polygon at index {idx}: {e}", "WARNING")
            skipped_count += 1
            continue
        
        annotation = {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": category_id,
            "segmentation": segmentation,
            "area": area,
            "bbox": bbox,
            "iscrowd": 0
        }
        
        json_data["annotations"].append(annotation)
        annotation_id += 1
    
    with open(output_json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print_status(f"Converted {len(json_data['annotations'])} annotations to {output_json_path}")
    print_status(f"Skipped {skipped_count} features")
    print_status(f"Dataset includes 1 image and {len(json_data['categories'])} species")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print_status(f"Conversion completed in {duration.total_seconds():.2f} seconds")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Convert shapefiles to TREE-D JSON format',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('shapefile', help='Path to input shapefile')
    parser.add_argument('image_folder', help='Path to folder containing the image')
    parser.add_argument('output', help='Path to output JSON file')
    parser.add_argument('--taxonomy', required=True, help='Path to CSV file with taxonomic information')
    parser.add_argument('--image-metadata', required=True, help='Path to CSV file with additional image metadata')
    
    parser.add_argument('--url', help='URL for the dataset', default="https://github.com/smk0061/TREE-D")
    parser.add_argument('--description', help='Description of the dataset', default="TREE-D Contribution")
    parser.add_argument('--contributor', help='Name of the contributor')
    
    args = parser.parse_args()
    
    dataset_info = {
        "description": args.description,
        "url": args.url,
        "contributor": args.contributor if args.contributor else ""
    }
    
    success = shapefile_to_json_annotations(
        args.shapefile,
        args.image_folder,
        args.output,
        taxonomy_csv=args.taxonomy,
        image_metadata_csv=args.image_metadata,
        dataset_info=dataset_info
    )
    
    if success:
        print_status("TREE-D JSON created successfully")
    else:
        print_status("Conversion failed", "ERROR")
        exit(1)


if __name__ == "__main__":
    main()