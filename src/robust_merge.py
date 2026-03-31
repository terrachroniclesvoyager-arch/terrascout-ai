import os
import glob
import logging
import numpy as np
import rasterio
from rasterio.merge import merge

logger = logging.getLogger(__name__)

# Maximum files to open simultaneously during merge
_CHUNK_SIZE = 50


def merge_masks(masks_dir, output_filename="merged.tif"):
    """
    Merges all tile masks using rasterio (no GDAL dependency).
    Uses method='max' to preserve detections in mask overlaps.

    For large tile sets (>50 files), merges in chunks to avoid
    exhausting file handles and RAM.

    Args:
        masks_dir (str): Directory containing mask tiles.
        output_filename (str): Name of the output merged file.

    Returns:
        str: Path to the merged file.
    """
    # Find all mask files
    search_pattern = os.path.join(masks_dir, "*_mask.tif")
    mask_files = sorted(glob.glob(search_pattern))

    if not mask_files:
        # Fallback: try tile_*.tif pattern
        search_pattern_alt = os.path.join(masks_dir, "tile_*.tif")
        mask_files = sorted(glob.glob(search_pattern_alt))
        mask_files = [f for f in mask_files if "merged" not in os.path.basename(f)]

    if not mask_files:
        raise FileNotFoundError(f"No mask tiles found in {masks_dir}")

    logger.info(f"Found {len(mask_files)} mask tiles to merge.")

    output_path = os.path.join(masks_dir, output_filename)

    # Small set: merge all at once (original fast path)
    if len(mask_files) <= _CHUNK_SIZE:
        return _merge_files(mask_files, output_path)

    # Large set: chunked streaming merge
    logger.info(f"Large tile set ({len(mask_files)}), using chunked merge in batches of {_CHUNK_SIZE}")
    temp_files = []
    try:
        for i in range(0, len(mask_files), _CHUNK_SIZE):
            chunk = mask_files[i : i + _CHUNK_SIZE]
            chunk_num = i // _CHUNK_SIZE + 1
            total_chunks = (len(mask_files) + _CHUNK_SIZE - 1) // _CHUNK_SIZE

            if total_chunks == 1:
                # Only one chunk, merge directly
                return _merge_files(chunk, output_path)

            # Merge this chunk to a temp file
            temp_path = os.path.join(masks_dir, f"_chunk_{chunk_num}.tif")
            logger.info(f"Merging chunk {chunk_num}/{total_chunks} ({len(chunk)} tiles)")
            _merge_files(chunk, temp_path)
            temp_files.append(temp_path)

        # Final merge of all chunk results
        logger.info(f"Merging {len(temp_files)} chunk results into final output")
        _merge_files(temp_files, output_path)
        return output_path

    finally:
        # Clean up temp chunk files
        for tf in temp_files:
            try:
                if os.path.exists(tf):
                    os.remove(tf)
            except OSError:
                pass


def _merge_files(file_paths, output_path):
    """Merge a list of raster files into output_path using max method."""
    src_files = []
    try:
        for f in file_paths:
            src_files.append(rasterio.open(f))

        # Merge using max method to preserve detections in overlapping regions
        mosaic, out_transform = merge(src_files, method='max')

        # Write output
        out_meta = src_files[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_transform,
            "compress": "lzw",
            "dtype": "uint8"
        })

        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic.astype(np.uint8))

        logger.info(f"Merged {len(file_paths)} files -> {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error during merge: {e}")
        raise
    finally:
        # Always close source files
        for src in src_files:
            src.close()


if __name__ == "__main__":
    masks_directory = "output/masks"
    if os.path.exists(masks_directory):
        merge_masks(masks_directory)
