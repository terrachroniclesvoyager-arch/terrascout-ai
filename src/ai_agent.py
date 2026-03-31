"""
AI Agent architecture for Pocket GIS AI.
Provides rule-based guidance now, with LLM integration stub for future use.
"""
from abc import ABC, abstractmethod
import re


class BaseAgent(ABC):
    """Abstract base agent for all AI assistants."""

    @abstractmethod
    def parse_intent(self, user_input):
        """Parses user input and returns an intent string."""
        pass

    @abstractmethod
    def execute(self, intent, context=None):
        """Executes an action based on the parsed intent."""
        pass

    @abstractmethod
    def format_response(self, result):
        """Formats the execution result into a user-friendly message."""
        pass

    def run(self, user_input, context=None):
        """Full pipeline: parse -> execute -> format."""
        intent = self.parse_intent(user_input)
        result = self.execute(intent, context)
        return self.format_response(result)


class RuleBasedAgent(BaseAgent):
    """Keyword-based agent that maps user queries to predefined responses."""

    INTENT_MAP = {
        "analyze": {
            "keywords": ["analyze", "analizza", "scan", "detect", "find", "cerca", "segmenta"],
            "response": (
                "To run an analysis:\n"
                "1. Go to the **Map Analysis** tab\n"
                "2. Draw a rectangle on the area you want to analyze\n"
                "3. Set your **text prompt** in the sidebar (e.g., 'tree', 'building', 'road')\n"
                "4. Click **Analyze**\n\n"
                "For uploaded images, use the **Image Analysis** tab instead."
            ),
        },
        "export": {
            "keywords": ["export", "download", "save", "esporta", "scarica", "salva"],
            "response": (
                "Export options:\n"
                "- **CSV**: Available after analysis in the Results section\n"
                "- **GeoJSON**: Automatically saved with each analysis\n"
                "- **DEM/DSM**: Available in the LiDAR tab after uploading a .LAS file\n"
                "- **Projects**: Save your work using the Projects panel in the sidebar"
            ),
        },
        "compare": {
            "keywords": ["compare", "confronta", "diff", "difference", "change"],
            "response": (
                "To compare analyses:\n"
                "1. Run multiple analyses on the same or different areas\n"
                "2. Check the **History** tab to see all saved analyses\n"
                "3. Load any previous analysis to review results\n\n"
                "Multi-temporal comparison is planned for a future release."
            ),
        },
        "navigate": {
            "keywords": ["navigate", "map", "zoom", "move", "go to", "mappa", "vai"],
            "response": (
                "Map navigation:\n"
                "- **Zoom**: Use scroll wheel or +/- buttons\n"
                "- **Pan**: Click and drag\n"
                "- **Layers**: Use the layer control (top right) to switch between Satellite, Dark, OSM, Terrain\n"
                "- **Draw**: Click the rectangle tool to select an area for analysis\n"
                "- **Click**: Click anywhere to see coordinate info"
            ),
        },
        "info": {
            "keywords": ["info", "help", "aiuto", "how", "come", "what", "cosa", "guide", "guida"],
            "response": (
                "**Pocket GIS AI** - Quick Guide:\n\n"
                "**Tabs:**\n"
                "- **Map Analysis**: Draw rectangles on satellite imagery, run AI segmentation\n"
                "- **Image Analysis**: Upload your own aerial/drone images\n"
                "- **LiDAR Analysis**: Upload .LAS/.LAZ point clouds for 2D/3D visualization\n"
                "- **History**: Browse and reload past analyses\n"
                "- **AI Assistant**: You are here! Ask questions about how to use the app\n\n"
                "**Sidebar Settings:**\n"
                "- **Text Prompt**: What to detect (tree, building, road, etc.)\n"
                "- **Thresholds**: Adjust detection sensitivity\n"
                "- **AI Model**: MobileSAM (fast), SAM 1 (standard), SAM 2 (best quality)\n"
                "- **Tile Size**: Larger = fewer tiles, more memory"
            ),
        },
        "lidar": {
            "keywords": ["lidar", "las", "laz", "point cloud", "elevation", "dem", "dsm", "chm", "3d"],
            "response": (
                "LiDAR features:\n"
                "1. Upload a **.LAS** or **.LAZ** file in the LiDAR tab\n"
                "2. View statistics: point count, elevation range, classification\n"
                "3. **2D Elevation Map**: Color-coded heatmap of terrain\n"
                "4. **3D Point Cloud**: Interactive 3D viewer\n"
                "5. **Export DEM**: Download elevation raster as GeoTIFF"
            ),
        },
        "model": {
            "keywords": ["model", "sam", "mobilesam", "modello", "speed", "quality", "veloce"],
            "response": (
                "Available AI models:\n"
                "- **MobileSAM** (default): Fastest, ~0.5s/tile on CPU. Best for quick scans\n"
                "- **SAM 1**: Standard quality, ~2s/tile on CPU. Good balance\n"
                "- **SAM 2**: Best quality, ~3s/tile on CPU. Use for precision work\n\n"
                "Change the model in the sidebar under **AI Model**."
            ),
        },
    }

    def parse_intent(self, user_input):
        text = user_input.lower().strip()
        for intent_key, intent_data in self.INTENT_MAP.items():
            for keyword in intent_data["keywords"]:
                if keyword in text:
                    return intent_key
        return "info"  # Default to help

    def execute(self, intent, context=None):
        intent_data = self.INTENT_MAP.get(intent, self.INTENT_MAP["info"])
        return intent_data["response"]

    def format_response(self, result):
        return result


class LLMAgent(BaseAgent):
    """Stub for future LLM-powered agent (Ollama/OpenAI/Anthropic)."""

    def __init__(self, provider="ollama", model_name=None, api_key=None):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

    def parse_intent(self, user_input):
        raise NotImplementedError("LLM agent not yet implemented. Use RuleBasedAgent for now.")

    def execute(self, intent, context=None):
        raise NotImplementedError("LLM agent not yet implemented.")

    def format_response(self, result):
        raise NotImplementedError("LLM agent not yet implemented.")


def get_agent(agent_type="rule_based"):
    """Factory function to create the appropriate agent."""
    if agent_type == "rule_based":
        return RuleBasedAgent()
    elif agent_type == "llm":
        return LLMAgent()
    else:
        return RuleBasedAgent()
