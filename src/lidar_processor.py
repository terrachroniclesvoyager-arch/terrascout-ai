import os
import numpy as np
import logging

logger = logging.getLogger(__name__)


class LidarProcessor:
    """Processes LiDAR point cloud data for visualization and export."""

    def __init__(self):
        self.las = None
        self.path = None

    def load_point_cloud(self, path):
        """Loads a LAS/LAZ file with laspy."""
        import laspy
        self.las = laspy.read(path)
        self.path = path
        logger.info(f"Loaded {len(self.las.points):,} points from {path}")
        return self.las

    def get_statistics(self):
        """Returns a statistics dictionary for the loaded point cloud."""
        las = self.las
        return {
            "total_points": len(las.points),
            "x_min": float(las.x.min()),
            "x_max": float(las.x.max()),
            "y_min": float(las.y.min()),
            "y_max": float(las.y.max()),
            "z_min": float(las.z.min()),
            "z_max": float(las.z.max()),
            "z_mean": float(las.z.mean()),
            "x_range": float(las.x.max() - las.x.min()),
            "y_range": float(las.y.max() - las.y.min()),
            "z_range": float(las.z.max() - las.z.min()),
            "version": str(las.header.version),
            "point_format": int(las.point_format.id),
        }

    def create_2d_elevation_map(self, resolution=1.0, colormap="RdYlBu_r"):
        """
        Creates a 2D elevation heatmap image as a numpy RGB array.
        Samples max 2M points for memory safety.
        Returns: numpy array (H, W, 3) uint8
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        from scipy.interpolate import griddata

        las = self.las
        x, y, z = np.array(las.x), np.array(las.y), np.array(las.z)

        # Sample if too many points
        max_pts = 2_000_000
        if len(x) > max_pts:
            idx = np.random.choice(len(x), max_pts, replace=False)
            x, y, z = x[idx], y[idx], z[idx]

        # Create grid
        x_range = x.max() - x.min()
        y_range = y.max() - y.min()
        nx = max(int(x_range / resolution), 10)
        ny = max(int(y_range / resolution), 10)
        # Cap grid size for memory
        nx = min(nx, 2000)
        ny = min(ny, 2000)

        xi = np.linspace(x.min(), x.max(), nx)
        yi = np.linspace(y.min(), y.max(), ny)
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate
        zi = griddata((x, y), z, (xi, yi), method='linear')

        # Render with matplotlib
        fig, ax = plt.subplots(figsize=(10, 10 * y_range / max(x_range, 0.001)))
        ax.set_aspect('equal')
        im = ax.pcolormesh(xi, yi, zi, cmap=colormap, shading='auto')
        plt.colorbar(im, ax=ax, label='Elevation (m)', shrink=0.8)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('Elevation Map')
        plt.tight_layout()

        # Convert to image array
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
        plt.close(fig)

        return img

    def create_3d_pydeck_data(self, max_points=500_000):
        """
        Prepares a DataFrame with x, y, z, r, g, b for pydeck ScatterplotLayer.
        Colors are based on normalized elevation (blue=low, red=high).
        """
        import pandas as pd

        las = self.las
        x, y, z = np.array(las.x), np.array(las.y), np.array(las.z)

        # Sample if needed
        if len(x) > max_points:
            idx = np.random.choice(len(x), max_points, replace=False)
            x, y, z = x[idx], y[idx], z[idx]

        # Normalize elevation to 0-1
        z_min, z_max = z.min(), z.max()
        z_range = z_max - z_min if z_max != z_min else 1.0
        z_norm = (z - z_min) / z_range

        # Color gradient: blue (low) -> green (mid) -> red (high)
        r = (z_norm * 255).astype(np.uint8)
        g = ((1 - np.abs(z_norm - 0.5) * 2) * 200).astype(np.uint8)
        b = ((1 - z_norm) * 255).astype(np.uint8)

        df = pd.DataFrame({
            "x": x,
            "y": y,
            "z": z,
            "r": r,
            "g": g,
            "b": b,
        })

        return df

    def export_dem_raster(self, output_path, resolution=1.0):
        """Exports a DEM GeoTIFF from the point cloud using rasterio."""
        import rasterio
        from rasterio.transform import from_bounds
        from scipy.interpolate import griddata

        las = self.las
        x, y, z = np.array(las.x), np.array(las.y), np.array(las.z)

        # Sample for performance
        max_pts = 2_000_000
        if len(x) > max_pts:
            idx = np.random.choice(len(x), max_pts, replace=False)
            x, y, z = x[idx], y[idx], z[idx]

        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()

        nx = max(int((x_max - x_min) / resolution), 10)
        ny = max(int((y_max - y_min) / resolution), 10)
        nx = min(nx, 4000)
        ny = min(ny, 4000)

        xi = np.linspace(x_min, x_max, nx)
        yi = np.linspace(y_min, y_max, ny)
        xi, yi = np.meshgrid(xi, yi)

        zi = griddata((x, y), z, (xi, yi), method='linear')
        zi = np.nan_to_num(zi, nan=z.min())

        transform = from_bounds(x_min, y_min, x_max, y_max, nx, ny)

        # Flip vertically for correct raster orientation
        zi_flipped = np.flipud(zi)

        with rasterio.open(
            output_path, 'w',
            driver='GTiff',
            height=ny,
            width=nx,
            count=1,
            dtype='float32',
            transform=transform,
            compress='lzw',
        ) as dst:
            dst.write(zi_flipped.astype(np.float32), 1)

        logger.info(f"DEM exported to {output_path}")
        return output_path
