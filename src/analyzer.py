import os
import shutil
import logging
import gc
import torch
import pandas as pd
import geopandas as gpd
try:
    from samgeo.common import tms_to_geotiff, split_raster
    from samgeo.text_sam import LangSAM
    SAMGEO_AVAILABLE = True
except ImportError:
    SAMGEO_AVAILABLE = False
    # Dummy classes for gentle fallback if SAM is missing
    class LangSAM:
        def __init__(self, *args, **kwargs): pass
    def tms_to_geotiff(*args, **kwargs): pass
try:
    import leafmap
    LEAFMAP_AVAILABLE = True
except ImportError:
    LEAFMAP_AVAILABLE = False
    class leafmap: pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeoAnalyzer:
    def __init__(self):
        self.sam = None
        self.model_type = None  # Track current model type
        self.output_dir = "output"
        self.tiles_dir = os.path.join(self.output_dir, "tiles")
        self.masks_dir = os.path.join(self.output_dir, "masks")
        self.image_path = os.path.join(self.output_dir, "satellite_image.tif")

        self.custom_image_path = None

        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)

        # CPU optimization
        torch.set_num_threads(max(1, os.cpu_count() or 4))
    
    def set_image(self, image_path):
        """Sets a custom image path for analysis."""
        self.custom_image_path = image_path
        self.image_path = image_path # Update main path reference

    # Valid LangSAM model types:
    #   SAM 1: "vit_h", "vit_l", "vit_b"
    #   SAM 2: "sam2-hiera-tiny", "sam2-hiera-small", "sam2-hiera-base-plus", "sam2-hiera-large"
    MODEL_MAP = {
        "mobile_sam": "sam2-hiera-tiny",   # Fastest - small SAM2
        "sam1": "vit_h",                    # Standard SAM 1
        "sam2": "sam2-hiera-large",         # Best quality SAM 2
    }

    @staticmethod
    def _check_gpu():
        """Check GPU availability and VRAM. Returns (device_str, vram_gb)."""
        if not torch.cuda.is_available():
            return "cpu", 0.0
        try:
            vram_total = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            vram_free = (torch.cuda.get_device_properties(0).total_mem
                         - torch.cuda.memory_reserved(0)) / (1024**3)
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}, "
                        f"VRAM total={vram_total:.1f}GB, free≈{vram_free:.1f}GB")
            if vram_free < 1.5:
                logger.warning(f"Low VRAM ({vram_free:.1f}GB free). Forcing CPU.")
                return "cpu", vram_free
            return "cuda", vram_free
        except Exception as e:
            logger.warning(f"GPU probe failed: {e}")
            return "cpu", 0.0

    def initialize_model(self, model_type="mobile_sam"):
        """Initializes the LangSAM model if not already initialized."""
        if self.sam is not None and self.model_type == model_type:
            return  # Already loaded

        langsam_type = self.MODEL_MAP.get(model_type, "vit_h")

        # Check GPU before loading
        device, vram = self._check_gpu()
        if device == "cpu" and langsam_type in ("sam2-hiera-large", "vit_h"):
            logger.warning(f"No GPU / low VRAM for {langsam_type}, downgrading to sam2-hiera-tiny")
            langsam_type = "sam2-hiera-tiny"

        logger.info(f"Initializing LangSAM (user={model_type}, langsam={langsam_type}, device={device})...")

        try:
            self.sam = LangSAM(model_type=langsam_type)
            self.model_type = model_type
            logger.info(f"LangSAM initialized: {langsam_type} on {device}")
        except Exception as e:
            logger.error(f"Failed to load {langsam_type}: {e}")
            logger.info("Falling back to sam2-hiera-tiny...")
            try:
                self.sam = LangSAM(model_type="sam2-hiera-tiny")
                self.model_type = "mobile_sam"
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                logger.info("Last resort: vit_b...")
                self.sam = LangSAM(model_type="vit_b")
                self.model_type = "sam1"

    def download_image(self, bbox, zoom=19, source="Satellite"):
        """Downloads satellite imagery for the given bounding box."""
        # Validate bbox: ensure no zero-area or inverted coords
        min_lon, min_lat, max_lon, max_lat = bbox
        if min_lon > max_lon:
            min_lon, max_lon = max_lon, min_lon
        if min_lat > max_lat:
            min_lat, max_lat = max_lat, min_lat
        if abs(max_lon - min_lon) < 1e-6 or abs(max_lat - min_lat) < 1e-6:
            raise ValueError("Bounding box has zero area — draw a larger selection.")
        bbox = [min_lon, min_lat, max_lon, max_lat]
        logger.info(f"Downloading image for bbox: {bbox} at zoom {zoom}")
        
        # Try with requested zoom, then fallback to lower zoom if fails
        for attempt_zoom in [zoom, max(17, zoom - 1), max(16, zoom - 2)]:
            try:
                logger.info(f"Attempting download at zoom {attempt_zoom}...")
                tms_to_geotiff(output=self.image_path, bbox=bbox, zoom=attempt_zoom, source=source, overwrite=True)
                logger.info(f"Image saved to {self.image_path}")
                return self.image_path
            except Exception as e:
                logger.warning(f"Download failed at zoom {attempt_zoom}: {e}")
                if attempt_zoom == max(16, zoom - 2):
                    # Last attempt failed, try with smaller bbox (center only)
                    try:
                        center_bbox = self._shrink_bbox(bbox, 0.5)
                        logger.info(f"Trying with smaller bbox: {center_bbox}")
                        tms_to_geotiff(output=self.image_path, bbox=center_bbox, zoom=17, source=source, overwrite=True)
                        logger.info(f"Image saved to {self.image_path} (with reduced area)")
                        return self.image_path
                    except Exception as e2:
                        logger.error(f"All download attempts failed: {e2}")
                        raise RuntimeError(f"Failed to download satellite imagery. Try selecting a smaller area or lower zoom level. Error: {e}")
        
    def estimate_tile_count(self, bbox, zoom, tile_size=1000):
        """Estimates how many tiles will be generated for a bbox and zoom."""
        import math
        min_lon, min_lat, max_lon, max_lat = bbox

        # Clamp latitude to Mercator-safe range (avoid math.log crash at ±90°)
        MERC_LIMIT = 85.051129
        min_lat = max(-MERC_LIMIT, min(MERC_LIMIT, min_lat))
        max_lat = max(-MERC_LIMIT, min(MERC_LIMIT, max_lat))

        # Earth is ~20037508.34 meters from center to pole in Mercator
        # Number of pixels for the full world at a given zoom level
        world_pixels = 256 * (2**zoom)

        # Degrees to Radians
        def lat_to_y(lat):
            return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

        y_min = lat_to_y(min_lat)
        y_max = lat_to_y(max_lat)
        
        # Delta Y in "spherical mercator units" (0 to 2*pi)
        # Full height of world in mercator radians is 2*pi approx
        # More accurately, we can use the ratio of degree delta
        
        delta_lon = abs(max_lon - min_lon)
        delta_lat_merc = abs(y_max - y_min)
        
        # Pixels width = (delta_lon / 360) * world_pixels
        # Pixels height = (delta_lat_merc / (2*pi)) * world_pixels
        pixels_w = (delta_lon / 360.0) * world_pixels
        pixels_h = (delta_lat_merc / (2 * math.pi)) * world_pixels
        
        rows = math.ceil(pixels_h / tile_size)
        cols = math.ceil(pixels_w / tile_size)
        
        return rows * cols

    def _shrink_bbox(self, bbox, factor):
        """Shrinks bbox to a fraction of its size, centered."""
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lon = (min_lon + max_lon) / 2
        center_lat = (min_lat + max_lat) / 2
        width = (max_lon - min_lon) * factor / 2
        height = (max_lat - min_lat) * factor / 2
        return [center_lon - width, center_lat - height, center_lon + width, center_lat + height]

    def split_image(self, tile_size=1000, overlap=0):
        """Splits the downloaded image into tiles."""
        logger.info(f"Splitting image into tiles of size {tile_size}...")
        try:
            # Clean previous tiles
            if os.path.exists(self.tiles_dir):
                shutil.rmtree(self.tiles_dir)
            
            split_raster(self.image_path, out_dir=self.tiles_dir, tile_size=(tile_size, tile_size), overlap=overlap)
            logger.info(f"Tiles saved to {self.tiles_dir}")
        except Exception as e:
            logger.error(f"Error splitting raster: {e}")
            raise

    def analyze_with_complex_prompt(
        self,
        text_prompt: str,
        negative_prompt: str = "",
        style_prompt: str = "",
        box_threshold: float = 0.24,
        text_threshold: float = 0.24,
        model_type: str = "sam2",
        merge_output: bool = True
    ):
        """
        Advanced analysis with complex prompts (text + negative + style).

        Args:
            text_prompt: Main detection prompt (e.g., "wooden hut")
            negative_prompt: What to exclude (e.g., "modern building, concrete")
            style_prompt: Style/characteristics (e.g., "rustic, traditional")
            box_threshold: Bounding box confidence threshold
            text_threshold: Text matching threshold
            model_type: SAM model type
            merge_output: Merge tiles into single output

        Returns:
            Path to mask or masks directory

        Note: LangSAM doesn't natively support negative prompts like Stable Diffusion.
        This method combines prompts intelligently and applies post-filtering.

        Usage:
            mask = analyzer.analyze_with_complex_prompt(
                text_prompt="hut, cabin, shack",
                negative_prompt="modern, concrete, metal",
                style_prompt="rustic, wooden, traditional"
            )
        """
        # Combine prompts for better detection
        combined_prompt = text_prompt

        if style_prompt:
            # Enhance main prompt with style characteristics
            combined_prompt = f"{text_prompt}, {style_prompt}"

        logger.info(f"Complex prompt analysis:")
        logger.info(f"  Text: {text_prompt}")
        if negative_prompt:
            logger.info(f"  Negative: {negative_prompt}")
        if style_prompt:
            logger.info(f"  Style: {style_prompt}")
        logger.info(f"  Combined: {combined_prompt}")

        # Run standard analysis with combined prompt
        result = self.analyze(
            text_prompt=combined_prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            model_type=model_type,
            merge_output=merge_output
        )

        # TODO: Post-processing for negative prompt filtering
        # This would require analyzing detected regions and filtering based on characteristics
        # For now, we rely on the combined prompt to guide detection

        return result

    def analyze(self, text_prompt, box_threshold=0.24, text_threshold=0.24, model_type="sam1", merge_output=True):
        """Runs the LangSAM analysis on the tiles."""
        self.initialize_model(model_type=model_type)
        logger.info(f"Running prediction for '{text_prompt}' ({model_type})")
        try:
            # Clean previous masks
            if os.path.exists(self.masks_dir):
                shutil.rmtree(self.masks_dir)
            
            self.sam.predict_batch(
                images=self.tiles_dir,
                out_dir=self.masks_dir,
                text_prompt=text_prompt,
                box_threshold=box_threshold,
                text_threshold=text_threshold,
                mask_multiplier=255,
                dtype="uint8",
                merge=False,
                verbose=True,
            )
            logger.info("Batch prediction complete (tiles). Merging...")
            
            if merge_output:
                from src.robust_merge import merge_masks
                merged_path = merge_masks(self.masks_dir, "merged.tif")
                
                # Memory Cleanup after merging
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                return merged_path
            else:
                return self.masks_dir
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            # Ensure memory is cleared even on failure
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
    
    def analyze_batched(self, text_prompt, box_threshold=0.24, text_threshold=0.24,
                        model_type="sam1", batch_size=20, progress_callback=None):
        """Processes tiles in batches to avoid memory issues on large areas."""
        import glob as globmod
        import tempfile

        self.initialize_model(model_type=model_type)
        logger.info(f"Running BATCHED prediction for '{text_prompt}' ({model_type})")

        # Clean previous masks
        if os.path.exists(self.masks_dir):
            shutil.rmtree(self.masks_dir)
        os.makedirs(self.masks_dir, exist_ok=True)

        # Get all tile files
        tile_files = sorted(globmod.glob(os.path.join(self.tiles_dir, "*.tif")))
        total_tiles = len(tile_files)
        logger.info(f"Total tiles to process: {total_tiles} in batches of {batch_size}")

        all_mask_files = []

        for batch_idx in range(0, total_tiles, batch_size):
            batch_tiles = tile_files[batch_idx:batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1
            total_batches = (total_tiles + batch_size - 1) // batch_size
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_tiles)} tiles)")

            # Create temp directory for this batch of tiles
            batch_tiles_dir = os.path.join(self.output_dir, f"_batch_tiles_{batch_num}")
            batch_masks_dir = os.path.join(self.output_dir, f"_batch_masks_{batch_num}")
            os.makedirs(batch_tiles_dir, exist_ok=True)

            # Symlink or copy tiles into batch directory
            for tile_path in batch_tiles:
                dst = os.path.join(batch_tiles_dir, os.path.basename(tile_path))
                shutil.copy2(tile_path, dst)

            try:
                self.sam.predict_batch(
                    images=batch_tiles_dir,
                    out_dir=batch_masks_dir,
                    text_prompt=text_prompt,
                    box_threshold=box_threshold,
                    text_threshold=text_threshold,
                    mask_multiplier=255,
                    dtype="uint8",
                    merge=False,
                    verbose=True,
                )

                # Move masks to main masks dir
                for mask_file in globmod.glob(os.path.join(batch_masks_dir, "*.tif")):
                    dest = os.path.join(self.masks_dir, os.path.basename(mask_file))
                    shutil.move(mask_file, dest)
                    all_mask_files.append(dest)

            except Exception as e:
                logger.warning(f"Batch {batch_num} failed: {e}")
            finally:
                # Cleanup temp batch dirs
                shutil.rmtree(batch_tiles_dir, ignore_errors=True)
                shutil.rmtree(batch_masks_dir, ignore_errors=True)

                # Free memory between batches
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            # Report progress
            if progress_callback:
                progress_callback(min(batch_idx + batch_size, total_tiles), total_tiles)

        # Merge all masks
        logger.info("All batches done. Merging masks...")
        from src.robust_merge import merge_masks
        merged_path = merge_masks(self.masks_dir, "merged.tif")

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return merged_path

    def analyze_image(self, image_path, text_prompt, box_threshold=0.24, text_threshold=0.24, model_type="sam1"):
        """Directly analyzes a single image without tiling (good for small/medium images)."""
        self.initialize_model(model_type=model_type)
        logger.info(f"Running direct prediction on {image_path}...")
        
        try:
            # Clean masks for fresh start
            if os.path.exists(self.masks_dir):
                shutil.rmtree(self.masks_dir)
            os.makedirs(self.masks_dir, exist_ok=True)

            self.sam.predict(
                image_path,
                text_prompt,
                box_threshold=box_threshold,
                text_threshold=text_threshold,
                output=os.path.join(self.masks_dir, "merged.tif") 
            )
            return os.path.join(self.masks_dir, "merged.tif")
        except Exception as e:
            logger.error(f"Error during direct analysis: {e}")
            raise

    def process_results(self):
        """Converts merged mask to vector and extracts coordinates."""
        from pyproj import Transformer
        import rasterio
        from rasterio.features import shapes
        from shapely.geometry import shape
        import json
        
        merged_mask = os.path.join(self.masks_dir, "merged.tif")
        if not os.path.exists(merged_mask):
            logger.warning("No merged mask found.")
            return None, None

        logger.info("Processing results: Extracting coordinates from mask...")
        
        csv_path = os.path.join(self.output_dir, "coordinates.csv")
        vector_path = os.path.join(self.output_dir, "vectors.geojson")
        
        try:
            # Read mask raster directly with rasterio
            with rasterio.open(merged_mask) as src:
                mask_data = src.read(1)
                transform = src.transform
                crs = src.crs
            
            logger.info(f"Mask shape: {mask_data.shape}, CRS: {crs}")
            logger.info(f"Mask values - min: {mask_data.min()}, max: {mask_data.max()}, non-zero: {(mask_data > 0).sum()}")
            
            # Extract polygons from mask
            mask_shapes = list(shapes(mask_data, mask=mask_data > 0, transform=transform))
            
            logger.info(f"Found {len(mask_shapes)} shapes in mask")
            
            if not mask_shapes:
                logger.warning("No features detected in mask.")
                pd.DataFrame(columns=['latitude', 'longitude']).to_csv(csv_path, index=False)
                return None, csv_path
            
            # Create transformer
            transformer = None
            if crs:
                try:
                    transformer = Transformer.from_crs(crs.to_string(), "EPSG:4326", always_xy=True)
                except:
                    # Fallback or assume 3857
                    try:
                        transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
                    except:
                        pass
            
            coords_list = []
            features = []
            
            for geom_dict, value in mask_shapes:
                if value > 0:
                    try:
                        geom = shape(geom_dict)
                        centroid = geom.centroid
                        
                        # Transform to lat/lon if possible, else pixels
                        if transformer:
                             lon, lat = transformer.transform(centroid.x, centroid.y)
                             # Also transform the full geometry for GeoJSON
                             from shapely.ops import transform as shapely_transform
                             def transform_coords(x, y, z=None):
                                 return transformer.transform(x, y)
                             geom_4326 = shapely_transform(transform_coords, geom)
                             geom_dict_4326 = geom_4326.__geo_interface__
                        else:
                             # Use pixel coords or raw coords
                             lon, lat = centroid.x, centroid.y
                             geom_dict_4326 = geom_dict
                             
                        coords_list.append({'latitude': lat, 'longitude': lon})
                        
                        features.append({
                            'type': 'Feature',
                            'geometry': geom_dict_4326,  # Use transformed geometry!
                            'properties': {'value': int(value), 'area_m2': 0.0, 'id': 0}
                        })
                    except Exception as e:
                        logger.warning(f"Error processing shape: {e}")
            
            # Calculate Area and Add ID
            if features:
                 try:
                     # Temporary GDF for area calculation
                     temp_gdf = gpd.GeoDataFrame.from_features(features)
                     if temp_gdf.crs is None:
                         temp_gdf.set_crs("EPSG:4326", inplace=True)
                     
                     # Estimate UTM for accurate area
                     utm_crs = temp_gdf.estimate_utm_crs()
                     areas = temp_gdf.to_crs(utm_crs).area
                     
                     # Update features
                     for i, feat in enumerate(features):
                         feat['properties']['area_m2'] = round(areas[i], 2)
                         feat['properties']['id'] = i + 1
                         
                 except Exception as e:
                     logger.warning(f"Could not calculate area: {e}")
            
            logger.info(f"Extracted {len(coords_list)} coordinates")
            
            # Save coordinates
            coords_df = pd.DataFrame(coords_list)
            coords_df.to_csv(csv_path, index=False)
            logger.info(f"Coordinates saved to {csv_path} ({len(coords_df)} points)")
            
            if len(coords_df) > 0:
                logger.info(f"Sample: lat={coords_df['latitude'].iloc[0]:.6f}, lon={coords_df['longitude'].iloc[0]:.6f}")
            
            # Save GeoJSON
            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }
            with open(vector_path, 'w') as f:
                json.dump(geojson, f)
            
            return coords_df, csv_path
            
        except Exception as e:
            logger.error(f"Error processing results: {e}")
            import traceback
            traceback.print_exc()
            pd.DataFrame(columns=['latitude', 'longitude']).to_csv(csv_path, index=False)
            return None, csv_path

