import os
import json
import shutil
import glob
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectManager:
    def __init__(self, base_dir="projects"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
    def create_project(self, project_name):
        """Creates a new project directory."""
        # Sanitize name
        project_id = "".join([c for c in project_name if c.isalnum() or c in (' ', '_', '-')]).rstrip()
        project_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_id = f"{project_id}_{project_timestamp}"
        
        path = os.path.join(self.base_dir, final_id)
        os.makedirs(path, exist_ok=True)
        return final_id, path

    def _generate_thumbnail(self, image_path, project_path, max_size=300):
        """Generates a thumbnail from the satellite image."""
        thumb_path = os.path.join(project_path, "thumbnail.png")
        try:
            from PIL import Image
            import rasterio
            
            # Check if it's a GeoTIFF
            if image_path.lower().endswith(('.tif', '.tiff')):
                with rasterio.open(image_path) as src:
                    # Read RGB bands (or first 3 bands)
                    if src.count >= 3:
                        r, g, b = src.read(1), src.read(2), src.read(3)
                        import numpy as np
                        rgb = np.dstack((r, g, b))
                        # Normalize to 0-255 if needed
                        if rgb.max() > 255:
                            rgb = (rgb / rgb.max() * 255).astype('uint8')
                        else:
                            rgb = rgb.astype('uint8')
                        img = Image.fromarray(rgb)
                    else:
                        data = src.read(1)
                        import numpy as np
                        data = ((data - data.min()) / (data.max() - data.min()) * 255).astype('uint8')
                        img = Image.fromarray(data)
            else:
                img = Image.open(image_path)
            
            # Create thumbnail
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            img.save(thumb_path, "PNG")
            return thumb_path
            
        except Exception as e:
            logger.warning(f"Could not generate thumbnail: {e}")
            return None

    def _count_objects(self, vector_path):
        """Counts the number of detected objects from the vector file."""
        try:
            with open(vector_path, 'r') as f:
                data = json.load(f)
                return len(data.get('features', []))
        except:
            return 0

    def save_project(self, project_id, state_data):
        """
        Saves the current session state to the project directory.
        state_data should contain:
        - prompt, settings (dict)
        - image_path, mask_path, vector_path, csv_path (str)
        """
        project_path = os.path.join(self.base_dir, project_id)
        if not os.path.exists(project_path):
             os.makedirs(project_path, exist_ok=True)
             
        # Definition of files to copy
        files_to_save = {
            "image.tif": state_data.get("image_path"),
            "mask.tif": state_data.get("mask_path"),
            "vectors.geojson": state_data.get("vector_path"),
            "data.csv": state_data.get("csv_path")
        }
        
        saved_files = {}
        
        for name, src_path in files_to_save.items():
            if src_path and os.path.exists(src_path):
                dst_path = os.path.join(project_path, name)
                shutil.copy2(src_path, dst_path)
                saved_files[name] = dst_path
            else:
                saved_files[name] = None
        
        # Generate thumbnail
        thumb_path = None
        if state_data.get("image_path") and os.path.exists(state_data["image_path"]):
            thumb_path = self._generate_thumbnail(state_data["image_path"], project_path)
            if thumb_path:
                saved_files["thumbnail.png"] = thumb_path
        
        # Count objects
        object_count = 0
        if state_data.get("vector_path") and os.path.exists(state_data["vector_path"]):
            object_count = self._count_objects(state_data["vector_path"])
                
        # Save Metadata
        metadata = {
            "id": project_id,
            "created_at": datetime.now().isoformat(),
            "settings": state_data.get("settings", {}),
            "files": saved_files,
            "object_count": object_count,
            "prompt": state_data.get("settings", {}).get("prompt", "unknown")
        }
        
        meta_path = os.path.join(project_path, "metadata.json")
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=4)
            
        return meta_path

    def list_projects(self):
        """Returns a list of available projects."""
        projects = []
        if not os.path.exists(self.base_dir):
            return []
            
        for d in os.listdir(self.base_dir):
            path = os.path.join(self.base_dir, d)
            meta = os.path.join(path, "metadata.json")
            if os.path.isdir(path) and os.path.exists(meta):
                try:
                    with open(meta, 'r') as f:
                        data = json.load(f)
                        # Add thumbnail path
                        thumb = os.path.join(path, "thumbnail.png")
                        if os.path.exists(thumb):
                            data["thumbnail"] = thumb
                        projects.append(data)
                except:
                    continue
        # Sort by date desc
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return projects

    def load_project(self, project_id):
        """Loads project metadata."""
        path = os.path.join(self.base_dir, project_id, "metadata.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None
    
    def delete_project(self, project_id):
        """Deletes a project and all its files."""
        path = os.path.join(self.base_dir, project_id)
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
        return False
