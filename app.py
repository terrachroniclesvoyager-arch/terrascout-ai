import html as html_module
import streamlit as st
import os
import json

# --- PROJ FIX ---
# PROJ_LIB is now handled by start_pocket_gis.bat
# ----------------

# ═══════════════════════════════════════════
# LAZY LOADING OPTIMIZATION
# Modules are now loaded on-demand to reduce startup time from 15-20s to 2-3s
# ═══════════════════════════════════════════
from src.module_loader import load_module_render_function
from src.analyzer import GeoAnalyzer
from src.ui import render_sidebar, render_map, display_results, display_dataframe, render_project_sidebar, render_image_uploader, render_history_gallery
from src.project_manager import ProjectManager
import streamlit.components.v1 as components

try:
    from streamlit_folium import st_folium
    HAS_ST_FOLIUM = True
except ImportError:
    HAS_ST_FOLIUM = False

# --- SESSION PERSISTENCE ---
SESSION_FILE = "output/last_session.json"

def save_session(results):
    try:
        os.makedirs("output", exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(results, f, indent=2)
    except Exception:
        pass

def load_session():
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None

# Page Config
st.set_page_config(
    page_title="TerraScout AI",
    layout="wide",
    page_icon="🌍",
    initial_sidebar_state="expanded"
)


# ═══════════════════════════════════════════
# MODULE REGISTRY
# ═══════════════════════════════════════════
MODULE_REGISTRY = [
    {
        "category": "Analysis & AI",
        "color": "cyan",
        "modules": [
            {"id": "open_buildings",  "icon": "🛖", "name": "Open Buildings AI", "desc": "Instantly overlay Google & Microsoft AI building detections in any remote forest", "render": "_lazy_load"},
            {"id": "remote_explorer", "icon": "🛰️", "name": "Remote Explorer", "desc": "Find pristine structures, logging, airstrips & mining in Amazon, Congo, Borneo & remote areas", "render": "_lazy_load"},
            {"id": "map_analysis",    "icon": "🗺️", "name": "Map Analysis",    "desc": "Draw areas on the map for AI segmentation",       "render": "_inline"},
            {"id": "image_analysis",  "icon": "🖼️", "name": "Image Analysis",  "desc": "Upload aerial/drone images for object detection",  "render": "_inline"},
            {"id": "lidar_upload",    "icon": "📡", "name": "LiDAR Upload",    "desc": "Upload LAS/LAZ for elevation and 3D views",        "render": "_inline"},
            {"id": "map_catalog",     "icon": "🧭", "name": "Map Catalog",     "desc": "4100+ tile layers from NASA, USGS, Esri, OSM & 2403 categories",       "render": "_lazy_load"},
            {"id": "zone_intel",      "icon": "🛰️", "name": "Zone Intelligence", "desc": "Select any area — ALL data layers: terrain, weather, species, infrastructure, risks & real-time", "render": "_lazy_load"},
            {"id": "deep_analysis",   "icon": "🔬", "name": "Deep Zone Analysis", "desc": "Click any point — AI interpolation: terrain, soil, climate, species, water table, geology & risk", "render": "_lazy_load"},
            {"id": "compare_locations", "icon": "📊", "name": "Location Comparison", "desc": "Compare 2-4 locations: elevation, weather, soil, biodiversity & risk", "render": "_lazy_load"},
            {"id": "route_analysis", "icon": "🛤️", "name": "Route Analyzer", "desc": "Analyze elevation, weather & hazards along any route", "render": "_lazy_load"},
            {"id": "ai_scoring", "icon": "🧠", "name": "AI Scoring Engine", "desc": "Multi-dimensional AI scoring: habitability, agriculture, tourism, ecology & construction", "render": "_lazy_load"},
            {"id": "smart_insights", "icon": "💡", "name": "Smart Insights AI", "desc": "AI-powered cross-domain analysis — opportunities, risks & recommendations", "render": "_lazy_load"},
            {"id": "environmental_dna", "icon": "🧬", "name": "Environmental DNA", "desc": "Unique environmental fingerprint with comparison & similarity analysis", "render": "_lazy_load"},
            {"id": "suitability_analyzer", "icon": "🎯", "name": "Suitability Analyzer", "desc": "Purpose-specific land evaluation: farming, solar, wind, housing, conservation", "render": "_lazy_load"},
            {"id": "anomaly_detector", "icon": "🔍", "name": "Anomaly Detector", "desc": "Detect environmental anomalies — statistical deviations from global baselines", "render": "_lazy_load"},
            {"id": "resource_scanner", "icon": "💎", "name": "Resource Scanner", "desc": "Scan for water, soil, solar, wind, minerals & timber potential", "render": "_lazy_load"},
            {"id": "threat_matrix", "icon": "🛡️", "name": "Threat Matrix AI", "desc": "Multi-domain unified threat assessment with cross-correlation analysis", "render": "_lazy_load"},
            {"id": "pattern_recognizer", "icon": "🔬", "name": "Pattern Recognizer AI", "desc": "Multi-dimensional geospatial pattern detection with confidence scoring", "render": "_lazy_load"},
            {"id": "mission_planner", "icon": "📋", "name": "Mission Planner AI", "desc": "AI-powered project planning with environmental intelligence", "render": "_lazy_load"},
            {"id": "correlation_engine", "icon": "🔗", "name": "Correlation Engine AI", "desc": "Cross-domain data correlation discovery across 8 dimensions", "render": "_lazy_load"},
            {"id": "change_detector", "icon": "📈", "name": "Change Detector AI", "desc": "Temporal change detection and environmental trend forecasting", "render": "_lazy_load"},
            {"id": "strategic_report", "icon": "📊", "name": "Strategic Report AI", "desc": "Intelligence-grade comprehensive strategic location assessment", "render": "_lazy_load"},
            {"id": "terrain_classifier", "icon": "🏔️", "name": "Terrain Classifier AI", "desc": "Landform classification with slope, aspect & roughness analysis", "render": "_lazy_load"},
            {"id": "water_intelligence", "icon": "💧", "name": "Water Intelligence AI", "desc": "Water resource analysis: groundwater, drought risk & watershed", "render": "_lazy_load"},
            {"id": "geo_profiler", "icon": "🌐", "name": "Geo Profiler AI", "desc": "10-dimension geographic profiling with reference comparison", "render": "_lazy_load"},
            {"id": "site_ranker", "icon": "🏆", "name": "Site Ranker AI", "desc": "Compare & rank 2-5 locations with weighted multi-criteria scoring", "render": "_lazy_load"},
            {"id": "network_analysis", "icon": "🕸️", "name": "Network Analysis AI", "desc": "Road network connectivity: intersections, bridges, railways, water crossings & reachability", "render": "_lazy_load"},
            {"id": "multi_hazard", "icon": "⚠️", "name": "Multi-Hazard AI", "desc": "Compound disaster scenario modeling with cascading effect analysis", "render": "_lazy_load"},
            {"id": "data_fusion", "icon": "🔀", "name": "Data Fusion AI", "desc": "Unified 10-source data aggregation dashboard with quality scoring", "render": "_lazy_load"},
            {"id": "accessibility_mapper", "icon": "🗺️", "name": "Accessibility Mapper AI", "desc": "6-dimension accessibility scoring: roads, emergency, education, transport, utilities & water", "render": "_lazy_load"},
            {"id": "resource_potential", "icon": "⛏️", "name": "Resource Potential AI", "desc": "8-category natural resource assessment: agriculture, water, solar, wind, mineral, timber, geothermal, tourism", "render": "_lazy_load"},
            {"id": "soil_intelligence", "icon": "🟤", "name": "Soil Intelligence AI", "desc": "Deep soil analysis: texture triangle, fertility index, drainage, erosion & carbon sequestration", "render": "_lazy_load"},
            {"id": "microclimate_ai", "icon": "🌤️", "name": "Microclimate AI", "desc": "Local microclimate: thermal comfort, wind exposure, frost risk, sun & growing season", "render": "_lazy_load"},
            {"id": "environmental_score", "icon": "🏅", "name": "Environmental Score AI", "desc": "ESG-style sustainability rating: natural capital, quality, resilience, integrity & potential", "render": "_lazy_load"},
            {"id": "vulnerability_index", "icon": "🛡️", "name": "Vulnerability Index AI", "desc": "7-domain vulnerability: seismic, hydrological, climate, geological, ecological, infrastructure & compound", "render": "_lazy_load"},
            {"id": "land_use_ai", "icon": "🏗️", "name": "Land Use Intelligence AI", "desc": "10-type land use classification with optimal use recommendations & transition planning", "render": "_lazy_load"},
            {"id": "water_quality_ai", "icon": "🧪", "name": "Water Quality AI", "desc": "8-parameter water quality index: pH, turbidity, DO, nitrate, phosphate, metals, bacterial & salinity", "render": "_lazy_load"},
            {"id": "carbon_footprint", "icon": "🌱", "name": "Carbon & Emissions AI", "desc": "Carbon storage, emission sources, sinks, net balance & sequestration potential", "render": "_lazy_load"},
            {"id": "settlement_ai", "icon": "🏘️", "name": "Settlement Planning AI", "desc": "8-factor settlement evaluation: terrain, water, climate, foundation, hazards, access & resources", "render": "_lazy_load"},
            {"id": "agriculture_ai", "icon": "🌾", "name": "Agricultural Intelligence AI", "desc": "12-crop suitability analysis with soil fertility, climate match & recommendations", "render": "_lazy_load"},
            {"id": "energy_potential", "icon": "⚡", "name": "Energy Potential AI", "desc": "5-source renewable energy: solar, wind, hydro, geothermal & biomass potential", "render": "_lazy_load"},
            {"id": "geo_intelligence", "icon": "🎖️", "name": "Geo Intelligence Briefing", "desc": "10-section intelligence summary: climate, soil, water, bio, seismic, infra & opportunities", "render": "_lazy_load"},
            {"id": "urban_planning_ai", "icon": "🏙️", "name": "Urban Planning AI", "desc": "8-metric urban analysis with 8-zone development suitability & livability scoring", "render": "_lazy_load"},
            {"id": "terrain_traversal", "icon": "🥾", "name": "Terrain Traversal AI", "desc": "5-mode traversability: walking, cycling, vehicle, off-road & heavy vehicle analysis", "render": "_lazy_load"},
            {"id": "noise_pollution", "icon": "🔊", "name": "Noise Pollution AI", "desc": "Environmental noise estimation: traffic, industrial, transport, social & natural quiet index", "render": "_lazy_load"},
            {"id": "biodiversity_hotspot", "icon": "🦜", "name": "Biodiversity Hotspot AI", "desc": "Conservation priority: species richness, habitat quality, ecosystem integrity & genetic diversity", "render": "_lazy_load"},
            {"id": "logistics_ai", "icon": "🚛", "name": "Logistics & Supply Chain AI", "desc": "7-index logistics: road, rail, air, maritime, storage, terrain & weather reliability", "render": "_lazy_load"},
            {"id": "tourism_potential", "icon": "🏖️", "name": "Tourism Potential AI", "desc": "8-type tourism suitability: nature, adventure, cultural, wellness, eco, beach, mountain & rural", "render": "_lazy_load"},
            {"id": "air_quality_ai", "icon": "🌬️", "name": "Air Quality AI", "desc": "Real-time AQI, PM2.5/PM10/O3/NO2/SO2/CO monitoring with health risk assessment", "render": "_lazy_load"},
            {"id": "strategic_value", "icon": "🎯", "name": "Strategic Value AI", "desc": "5-stakeholder strategic land value: government, military, commercial, conservation & research", "render": "_lazy_load"},
            {"id": "contamination_ai", "icon": "☢️", "name": "Contamination Risk AI", "desc": "7-pathway contamination risk: industrial, agricultural, water, soil, air, radiation & biological", "render": "_lazy_load"},
            {"id": "population_density", "icon": "👥", "name": "Population Density AI", "desc": "Building density, amenity richness, urbanization level & service coverage analysis", "render": "_lazy_load"},
            {"id": "mineral_prospecting", "icon": "💎", "name": "Mineral Prospecting AI", "desc": "Geological mineral assessment: gold, copper, iron, lithium, rare earths & deposit probability", "render": "_lazy_load"},
            {"id": "archaeological_ai", "icon": "🏛️", "name": "Archaeological Potential AI", "desc": "Archaeological site discovery: terrain, geology, settlement patterns & preservation conditions", "render": "_lazy_load"},
            {"id": "military_terrain", "icon": "🎖️", "name": "Military Terrain AI", "desc": "KOCOA terrain analysis: observation, cover, obstacles, key terrain & avenues of approach", "render": "_lazy_load"},
            {"id": "health_geography", "icon": "🏥", "name": "Health Geography AI", "desc": "Healthcare access, disease vectors, air quality, water safety & wellness scoring", "render": "_lazy_load"},
            {"id": "privacy_index", "icon": "🔒", "name": "Privacy & Isolation AI", "desc": "Physical isolation, visual/acoustic/digital privacy, access difficulty & light pollution", "render": "_lazy_load"},
            {"id": "survival_score", "icon": "🏕️", "name": "Survival Score AI", "desc": "Wilderness survival: water, shelter, food, climate, navigation, hazards & resources", "render": "_lazy_load"},
            {"id": "real_estate_ai", "icon": "🏠", "name": "Real Estate Intelligence AI", "desc": "8-dimension site assessment: desirability, transport, education, healthcare, commercial & green spaces", "render": "_lazy_load"},
            {"id": "forestry_ai", "icon": "🌲", "name": "Forestry Intelligence AI", "desc": "Forest coverage, growth potential, timber value, fire risk, conservation & harvesting feasibility", "render": "_lazy_load"},
            {"id": "hydrology_ai", "icon": "💧", "name": "Hydrology Intelligence AI", "desc": "Surface water, groundwater, precipitation, drainage, flood risk & water infrastructure", "render": "_lazy_load"},
            {"id": "geopolitical_ai", "icon": "🏴", "name": "Geopolitical Analysis AI", "desc": "Border proximity, strategic infrastructure, resource control, terrain advantage & stability", "render": "_lazy_load"},
            {"id": "renewable_grid", "icon": "⚡", "name": "Renewable Energy Grid AI", "desc": "Solar & wind potential, grid connectivity, installation feasibility & environmental impact", "render": "_lazy_load"},
            {"id": "soil_erosion_ai", "icon": "🏜️", "name": "Soil Erosion Risk AI", "desc": "RUSLE-inspired erosion estimation: rainfall erosivity, erodibility, slope, cover & conservation", "render": "_lazy_load"},
            {"id": "wildlife_corridor", "icon": "🦌", "name": "Wildlife Corridor AI", "desc": "Habitat connectivity: patches, barriers, water corridors, species richness & terrain passability", "render": "_lazy_load"},
            {"id": "infrastructure_age", "icon": "🏚️", "name": "Infrastructure Age AI", "desc": "Building stock age, road quality, utility coverage, maintenance level & modernization", "render": "_lazy_load"},
            {"id": "viewshed_ai", "icon": "👁️", "name": "Viewshed & Panorama AI", "desc": "Visibility analysis: elevation advantage, viewshed coverage, scenic value & atmospheric clarity", "render": "_lazy_load"},
            {"id": "unified_intelligence", "icon": "🧠", "name": "Unified Intelligence AI", "desc": "Master aggregator: 10 domains, cross-correlations, SWOT analysis & decision recommendations", "render": "_lazy_load"},
            {"id": "decision_matrix", "icon": "📋", "name": "Decision Matrix AI", "desc": "8-scenario decision support: residence, agriculture, commercial, conservation, tourism, energy, shelter & research", "render": "_lazy_load"},
            {"id": "intelligence_briefing", "icon": "📊", "name": "Intelligence Briefing", "desc": "Unified briefing: 10 domains, 8 scenarios, cross-correlations, SWOT, recommendations & aggregated charts", "render": "_lazy_load"},
            {"id": "proximity_scanner", "icon": "📡", "name": "Proximity Scanner AI", "desc": "Everything near a point: terrain, weather, soil, water, infrastructure, species, hazards & geology", "render": "_lazy_load"},
            {"id": "smart_zoning", "icon": "🏗️", "name": "Smart Zoning AI", "desc": "AI-powered land use recommendation: 8 scenarios ranked by terrain, soil, climate & infrastructure", "render": "_lazy_load"},
            {"id": "vegetation_index", "icon": "🌿", "name": "Vegetation & Biomass AI", "desc": "Vegetation density, green cover, species diversity, tree cover & synthetic NDVI estimation", "render": "_lazy_load"},
            {"id": "boundary_intel", "icon": "🗺️", "name": "Boundary Intelligence AI", "desc": "Administrative boundaries, jurisdictions, nearby cities, borders & timezone analysis", "render": "_lazy_load"},
            {"id": "signal_coverage", "icon": "📡", "name": "Signal Coverage AI", "desc": "Cell towers, radio infrastructure, internet, emergency comms & satellite visibility", "render": "_lazy_load"},
            {"id": "terrain_mobility", "icon": "🚁", "name": "Terrain Mobility AI", "desc": "Multi-mode traversability: foot, 4x4, truck, tracked, bicycle & helicopter analysis", "render": "_lazy_load"},
            {"id": "resource_mapping", "icon": "💎", "name": "Resource Mapping AI", "desc": "Natural resource survey: water, timber, agricultural, mineral, solar, wind & materials", "render": "_lazy_load"},
            {"id": "threat_assessment", "icon": "⚠️", "name": "Threat Assessment AI", "desc": "Unified threat analysis: seismic, weather, flood, landslide, industrial, wildfire, air & isolation", "render": "_lazy_load"},
            {"id": "livability_score", "icon": "🏘️", "name": "Livability Score AI", "desc": "Quality-of-life: climate, air, healthcare, education, commerce, green spaces, transport & safety", "render": "_lazy_load"},
            {"id": "cross_domain_ai", "icon": "🔗", "name": "Cross-Domain AI", "desc": "Hidden patterns across 6 data domains: 12 correlation detectors, contradictions & insights", "render": "_lazy_load"},
            {"id": "water_security", "icon": "💧", "name": "Water Security AI", "desc": "Water access, groundwater, precipitation, infrastructure, contamination & drought risk", "render": "_lazy_load"},
            {"id": "construction_ai", "icon": "🏗️", "name": "Construction Feasibility AI", "desc": "Site assessment: foundation soil, terrain, seismic zone, access, utilities & weather", "render": "_lazy_load"},
            {"id": "grazing_potential", "icon": "🐄", "name": "Grazing Potential AI", "desc": "Livestock suitability: pasture quality, water, terrain, climate & infrastructure", "render": "_lazy_load"},
            {"id": "landing_zone", "icon": "🚁", "name": "Landing Zone AI", "desc": "Helicopter LZ & drop zone: surface flatness, obstacles, wind, visibility & approach paths", "render": "_lazy_load"},
            {"id": "expedition_planner", "icon": "🧭", "name": "Expedition Planner AI", "desc": "Field mission planning: weather window, terrain, water, shelter, comms & hazards", "render": "_lazy_load"},
            {"id": "radio_propagation", "icon": "📻", "name": "Radio Propagation AI", "desc": "RF signal analysis: path loss, terrain obstruction, coverage radius & frequency planning", "render": "_lazy_load"},
            {"id": "camp_site", "icon": "⛺", "name": "Camp Site Selection AI", "desc": "Camping suitability: ground flatness, drainage, water, cover, wind, wildlife & access", "render": "_lazy_load"},
            {"id": "ground_truth", "icon": "✅", "name": "Ground Truth & Confidence AI", "desc": "Data reliability: OSM coverage, elevation, soil, weather, seismic, geology & biodiversity quality", "render": "_lazy_load"},
            {"id": "mining_suitability", "icon": "⛏️", "name": "Mining Suitability AI", "desc": "Mining feasibility: geology, terrain, soil, infrastructure, environmental constraints & operations", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Earth Science",
        "color": "violet",
        "modules": [
            {"id": "geology",    "icon": "🪨", "name": "Geology",    "desc": "Macrostrat geological formations & lithology",  "render": "_lazy_load"},
            {"id": "elevation",  "icon": "⛰️", "name": "Elevation",  "desc": "Open Topo Data elevation profiles",             "render": "_lazy_load"},
            {"id": "soil",       "icon": "🌱", "name": "Soil Data",  "desc": "ISRIC SoilGrids soil properties worldwide",      "render": "_lazy_load"},
            {"id": "earthquake","icon": "🌋", "name": "Earthquakes","desc": "USGS real-time earthquake data & history",        "render": "_lazy_load"},
            {"id": "ocean",      "icon": "🌊", "name": "Ocean & Marine","desc": "Wave height, swell, sea conditions worldwide",   "render": "_lazy_load"},
            {"id": "extreme_geo","icon": "🌋", "name": "Extreme Geography", "desc": "Deepest caves, highest peaks, largest deserts, volcanic islands, sinkholes & 10 maps", "render": "_lazy_load"},
            {"id": "archaeology_deep", "icon": "🏺", "name": "Archaeology Deep", "desc": "Seven Wonders, megalithic sites, lost cities, pyramids, Roman ruins, fossils & 10 maps", "render": "_lazy_load"},
            {"id": "volcanoes", "icon": "🌋", "name": "Volcanology", "desc": "Active volcanoes, Ring of Fire, supervolcanoes, eruption history & 10 maps", "render": "_lazy_load"},
            {"id": "deserts",  "icon": "🏜️", "name": "Deserts & Arid Lands", "desc": "World deserts, sand seas, oases, salt flats, desert civilizations & 10 maps", "render": "_lazy_load"},
            {"id": "islands",  "icon": "🏝️", "name": "Islands & Archipelagos", "desc": "Largest islands, volcanic islands, atolls, island nations, prison islands & 10 maps", "render": "_lazy_load"},
            {"id": "caves",    "icon": "🕳️", "name": "Caves & Underground", "desc": "Longest caves, cenotes, lava tubes, underground rivers, crystal caves, karst & 10 maps", "render": "_lazy_load"},
            {"id": "waterfalls", "icon": "🌊", "name": "Waterfalls & Rivers", "desc": "Greatest waterfalls, river systems, gorges, rapids, deltas, confluences & 10 maps", "render": "_lazy_load"},
            {"id": "glaciers",   "icon": "🏔️", "name": "Glaciers & Polar",   "desc": "Major glaciers, Antarctic stations, Arctic routes, ice cores, permafrost & 10 maps", "render": "_lazy_load"},
            {"id": "mountains",  "icon": "⛰️", "name": "Mountains & Peaks",  "desc": "Eight-thousanders, Seven Summits, sacred mountains, alpine huts & 10 maps", "render": "_lazy_load"},
            {"id": "fjords",     "icon": "🏔️", "name": "Fjords & Coastlines", "desc": "Norwegian fjords, dramatic coastlines, coral reefs, sea cliffs, tidal phenomena & 10 maps", "render": "_lazy_load"},
            {"id": "waterways",  "icon": "🌊", "name": "Waterways & Rivers", "desc": "World's greatest rivers, canals, deltas, locks, sacred waters, bridges, watersheds & 10 maps", "render": "_lazy_load"},
            {"id": "hidden_structures", "icon": "🛖", "name": "Global Hidden Structures", "desc": "Worldwide database of remote ruins, outposts, mystery structures & 10 maps", "render": "_lazy_load"},
            {"id": "isolated_buildings", "icon": "🏚️", "name": "Local Isolated Structures", "desc": "Scan any local forest or desert for isolated buildings via Overpass API", "render": "_lazy_load"},
            {"id": "timeline", "icon": "📅", "name": "Historical Timeline", "desc": "Temperature, earthquake & deforestation trends over decades", "render": "_lazy_load"},
            {"id": "terrain_3d", "icon": "🏔️", "name": "3D Terrain Viewer", "desc": "Interactive 3D terrain with elevation color-coding", "render": "_lazy_load"},
            {"id": "ocean_proximity", "icon": "🌊", "name": "Ocean Proximity AI", "desc": "Coastal distance, maritime weather, marine infrastructure & ocean influence analysis", "render": "_lazy_load"},
            {"id": "climate_zone", "icon": "🌍", "name": "Climate Zone AI", "desc": "Köppen climate classification, monthly profiles, comfort index & vegetation suitability", "render": "_lazy_load"},
            {"id": "climate_dashboard", "icon": "🌡️", "name": "Climate Dashboard", "desc": "14-day forecast, 5-year trends, monthly profiles & climate classification", "render": "_lazy_load"},
            {"id": "ecosystem_health", "icon": "🌿", "name": "Ecosystem Health Index", "desc": "6-dimension ecosystem health: biodiversity, soil, water, climate, human impact & conservation", "render": "_lazy_load"},
            {"id": "land_capability", "icon": "🏞️", "name": "Land Capability Class", "desc": "USDA 8-class land capability with soil, slope, drainage & climate limitations", "render": "_lazy_load"},
            {"id": "climate_forecast", "icon": "🌦️", "name": "Climate Forecast AI", "desc": "16-day forecast, hourly detail, historical averages, anomalies & comfort index", "render": "_lazy_load"},
            {"id": "elevation_profiler", "icon": "⛰️", "name": "Elevation Profiler AI", "desc": "Advanced terrain profiles, slope analysis, aspect mapping & terrain statistics", "render": "_lazy_load"},
            {"id": "seasonal_analysis", "icon": "🍂", "name": "Seasonal Analysis AI", "desc": "Monthly temperature, precipitation, daylight, wind patterns & best visit month", "render": "_lazy_load"},
            {"id": "soil_health_ai", "icon": "🌱", "name": "Soil Health & Fertility AI", "desc": "Texture triangle, fertility index, depth profile, drainage, carbon storage & remediation", "render": "_lazy_load"},
            {"id": "wind_analysis", "icon": "💨", "name": "Wind Pattern AI", "desc": "Wind rose, energy potential, Beaufort scale, terrain effects & impact assessment", "render": "_lazy_load"},
            {"id": "solar_analysis", "icon": "☀️", "name": "Solar Energy AI", "desc": "Solar irradiance, sunshine hours, panel sizing, shading risk & energy potential", "render": "_lazy_load"},
            {"id": "satellite_imagery", "icon": "🛰️", "name": "Satellite Imagery", "desc": "Real-time satellite views: MODIS, VIIRS, Sentinel-2, NDVI, elevation & date comparison", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Environment & Life",
        "color": "emerald",
        "modules": [
            {"id": "biodiversity", "icon": "🦋", "name": "Biodiversity", "desc": "iNaturalist species observations explorer",       "render": "_lazy_load"},
            {"id": "air_quality",  "icon": "💨", "name": "Air Quality",  "desc": "Open-Meteo real-time air quality monitor",         "render": "_lazy_load"},
            {"id": "wildfires",    "icon": "🔥", "name": "Wildfires",    "desc": "NASA FIRMS active fire tracking",                  "render": "_lazy_load"},
            {"id": "nasa_events",  "icon": "🌍", "name": "NASA Events",  "desc": "Real-time volcanoes, storms, icebergs from EONET","render": "_lazy_load"},
            {"id": "climate",      "icon": "🌡️", "name": "Climate Monitor","desc": "CO2 levels, temperature anomaly, climate history","render": "_lazy_load"},
            {"id": "climate_history", "icon": "🧊", "name": "Paleoclimate", "desc": "Ice ages, glaciation, sea level history, glacier retreat, desertification & 10 maps", "render": "_lazy_load"},
            {"id": "water",        "icon": "💧", "name": "Water",        "desc": "Hydrology features via Overpass API",              "render": "_lazy_load"},
            {"id": "weather",      "icon": "🌤️", "name": "Weather",      "desc": "Open-Meteo weather data & forecasts",              "render": "_lazy_load"},
            {"id": "weather_radar","icon": "📡", "name": "Weather Radar", "desc": "Real-time precipitation radar from RainViewer",   "render": "_lazy_load"},
            {"id": "biogeography", "icon": "🦁", "name": "Biogeography Maps", "desc": "Animal kingdoms, species ranges, coral reefs, rainforests, biodiversity hotspots", "render": "_lazy_load"},
            {"id": "botanical",    "icon": "🌿", "name": "Botanical & Gardens", "desc": "Botanical gardens, national parks, rainforests, endemic plants, cherry blossoms & 10 maps", "render": "_lazy_load"},
            {"id": "cuisine",      "icon": "🍕", "name": "World Cuisine",       "desc": "Cuisine origins, Michelin stars, street food, coffee, tea, chocolate, spice routes & 10 maps", "render": "_lazy_load"},
            {"id": "trad_med",     "icon": "🌱", "name": "Traditional Medicine", "desc": "Chinese medicine, Ayurveda, African healing, Amazonian plants, hot springs & 10 maps", "render": "_lazy_load"},
            {"id": "agriculture", "icon": "🌾", "name": "Agriculture & Food", "desc": "Crop regions, wine zones, fishing areas, livestock, spice routes & 10 food maps", "render": "_lazy_load"},
            {"id": "biodiv_global", "icon": "🌍", "name": "Global Biodiversity Heatmap", "desc": "Species density worldwide with viridis heatmap — mammals, birds, reptiles, plants, fungi & all life", "render": "_lazy_load"},
            {"id": "photography", "icon": "📷", "name": "Photography & Scenic", "desc": "Northern lights, waterfalls, deserts, mountain panoramas, underwater spots & 10 maps", "render": "_lazy_load"},
            {"id": "gastronomy",  "icon": "🍽️", "name": "Gastronomy & Food", "desc": "Michelin stars, coffee culture, wine regions, street food, spice routes & 10 food maps", "render": "_lazy_load"},
            {"id": "animal_maps", "icon": "🦁", "name": "Animal Distribution", "desc": "Zoogeographic realms, big cats, marine megafauna, marsupials, bird flyways, extinct species & 10 maps", "render": "_lazy_load"},
            {"id": "wine",       "icon": "🍷", "name": "Wine, Beer & Spirits", "desc": "Wine regions, craft breweries, whisky distilleries, champagne, terroir & 10 maps", "render": "_lazy_load"},
            {"id": "renewable", "icon": "🌿", "name": "Renewable Energy",   "desc": "Solar farms, wind farms, hydroelectric, geothermal, EV infrastructure & 10 maps", "render": "_lazy_load"},
            {"id": "textile",  "icon": "🧵", "name": "Textile & Fabric",    "desc": "Silk Road, weaving traditions, cotton mills, carpet arts, batik, lace, dye origins & 10 maps", "render": "_lazy_load"},
            {"id": "garden", "icon": "🌺", "name": "Gardens & Parks",     "desc": "Royal gardens, Japanese gardens, urban parks, tulip gardens, sculpture gardens & 10 maps", "render": "_lazy_load"},
            {"id": "spa",     "icon": "♨️", "name": "Hot Springs & Spas",   "desc": "Japanese onsen, Roman baths, Iceland geothermal, Turkish hammam, European spa towns & 10 maps", "render": "_lazy_load"},
            {"id": "pottery", "icon": "🏺", "name": "Pottery & Ceramics",  "desc": "Chinese porcelain, Japanese pottery, Islamic tiles, Delft, majolica, kilns & 10 maps", "render": "_lazy_load"},
            {"id": "dinosaur", "icon": "🦕", "name": "Dinosaurs & Fossils", "desc": "Dig sites, T-Rex, sauropod tracks, Jurassic Coast, amber fossils, mass extinctions & 10 maps", "render": "_lazy_load"},
            {"id": "coral_reef", "icon": "🪸", "name": "Coral Reefs & Oceans", "desc": "Great Barrier Reef, Coral Triangle, Red Sea, Caribbean, bleaching events, restoration & 10 maps", "render": "_lazy_load"},
            {"id": "coffee",     "icon": "☕", "name": "Coffee & Café Culture", "desc": "Coffee belt, espresso heritage, kissaten, specialty roasters, plantations & 10 maps", "render": "_lazy_load"},
            {"id": "honey",      "icon": "🍯", "name": "Honey & Beekeeping", "desc": "Apiaries, bee sanctuaries, manuka honey, urban beekeeping, mead heritage & 10 maps", "render": "_lazy_load"},
            {"id": "olive",     "icon": "🫒", "name": "Olive & Oil Heritage", "desc": "Mediterranean groves, oil mills, ancient olive trees, tasting routes & 10 maps", "render": "_lazy_load"},
            {"id": "bamboo",     "icon": "🎋", "name": "Bamboo & Eco Materials", "desc": "Bamboo forests, architecture, rattan crafts, sustainable building & 10 maps", "render": "_lazy_load"},
            {"id": "rice",       "icon": "🌾", "name": "Rice & Paddy Heritage", "desc": "Ancient rice terraces, paddy fields, rice mills, heritage varieties & 10 maps", "render": "_lazy_load"},
            {"id": "corn",       "icon": "🌽", "name": "Corn & Maize Heritage", "desc": "Ancient maize, modern corn fields, corn belt, popcorn heritage & 10 maps", "render": "_lazy_load"},
            {"id": "wheat",      "icon": "🥖", "name": "Wheat & Grain Heritage", "desc": "Global wheat fields, historic grain mills, ancient grains, breadbaskets & 10 maps", "render": "_lazy_load"},
            {"id": "potato",     "icon": "🥔", "name": "Potato Heritage",      "desc": "Andean origins, global cultivation, historic famines, varieties & 10 maps", "render": "_lazy_load"},
            {"id": "soy",        "icon": "🌱", "name": "Soybean Cultivation",  "desc": "Asian origins, modern soy fields, tofu heritage, tempeh & 10 maps", "render": "_lazy_load"},
            {"id": "cotton",     "icon": "🧵", "name": "Cotton & Textile",     "desc": "Historic cotton mills, global fields, organic cotton, silk road & 10 maps", "render": "_lazy_load"},
            {"id": "spice",       "icon": "🌶️", "name": "Spice Routes & Heritage", "desc": "Spice Islands, Indian markets, saffron, vanilla, pepper, historic spice trade & 10 maps", "render": "_lazy_load"},
            {"id": "salt",        "icon": "🧂", "name": "Salt & Mining Heritage", "desc": "Historic salt mines, evaporation ponds, Himalayan salt, salt trade, salt museums & 10 maps", "render": "_lazy_load"},
            {"id": "habitat_analyzer", "icon": "🦎", "name": "Habitat Analyzer AI", "desc": "8-habitat suitability analysis: forest, grassland, wetland, desert, alpine, coastal, Mediterranean", "render": "_lazy_load"},
        ],
    },
    {
        "category": "People & Society",
        "color": "pink",
        "modules": [
            {"id": "demographics", "icon": "👥", "name": "World Demographics", "desc": "Population, languages, religions, cultures worldwide", "render": "_lazy_load"},
            {"id": "infra_density", "icon": "🏙️", "name": "Infrastructure Density", "desc": "Building counts, road networks, urbanization & population estimates from OSM", "render": "_lazy_load"},
            {"id": "global_health", "icon": "🏥", "name": "Global Health",      "desc": "Disease tracking, WHO indicators, healthcare map",     "render": "_lazy_load"},
            {"id": "medical",      "icon": "💊", "name": "Medical & Health",   "desc": "Hospitals, disease history, life expectancy, pharma, traditional medicine & 10 maps", "render": "_lazy_load"},
            {"id": "world_data",   "icon": "📊", "name": "World Data Maps",   "desc": "Cost of living, education, inequality, CO2, internet & 12 global indicators", "render": "_lazy_load"},
            {"id": "linguistic",   "icon": "🗣️", "name": "Linguistic & Genetic", "desc": "Language families, writing systems, haplogroups, migration, blood types & 10 maps", "render": "_lazy_load"},
            {"id": "pilgrimage",   "icon": "🕌", "name": "Pilgrimage & Religion", "desc": "Sacred sites, pilgrimage routes, temples, churches, mosques, holy mountains & 10 maps", "render": "_lazy_load"},
            {"id": "music_culture","icon": "🎵", "name": "Music & Culture",      "desc": "Music origins, UNESCO intangible heritage, festivals, theaters, dance traditions & 10 maps", "render": "_lazy_load"},
            {"id": "sports",       "icon": "⚽", "name": "Sports & Events",      "desc": "Olympic venues, stadiums, FIFA World Cup, Formula 1, tennis, golf courses & 10 maps", "render": "_lazy_load"},
            {"id": "migration",    "icon": "🚶", "name": "Migration & Diaspora", "desc": "Human migration, refugee flows, Silk Road, exploration voyages, slave trade routes & 10 maps", "render": "_lazy_load"},
            {"id": "cinema",       "icon": "🎬", "name": "Cinema & Film",       "desc": "Film studios, LOTR locations, Bond sites, Star Wars, festivals & 10 movie maps", "render": "_lazy_load"},
            {"id": "fashion",      "icon": "👗", "name": "Fashion & Design",    "desc": "Fashion capitals, luxury brands, textiles, jewelry, perfume, watches & 10 maps", "render": "_lazy_load"},
            {"id": "genetics",     "icon": "🧬", "name": "Genetics & DNA",     "desc": "Y-DNA haplogroups, mtDNA, human migration, Neanderthal DNA, blood types, lactose tolerance & 10 maps", "render": "_lazy_load"},
            {"id": "population", "icon": "👥", "name": "Population Maps",     "desc": "World population, megacities, density, urbanization, growth rates, projections & 10 maps", "render": "_lazy_load"},
            {"id": "religion",   "icon": "🕌", "name": "World Religions",     "desc": "Religion distribution, holy cities, temples, mosques, monasteries, pilgrimage routes & 10 maps", "render": "_lazy_load"},
            {"id": "tattoo",    "icon": "🎨", "name": "Tattoo & Body Art",   "desc": "Tattoo traditions, tribal ink, Japanese irezumi, sacred markings, modern tattoo culture & 10 maps", "render": "_lazy_load"},
            {"id": "festival",  "icon": "🎪", "name": "Festivals & Events",  "desc": "World festivals, Carnival, Oktoberfest, music festivals, film festivals, cultural celebrations & 10 maps", "render": "_lazy_load"},
            {"id": "street_art", "icon": "🎨", "name": "Street Art & Murals", "desc": "Banksy, Wynwood Walls, Berlin murals, political art, 3D street art, graffiti history & 10 maps", "render": "_lazy_load"},
            {"id": "amusement",  "icon": "🎢", "name": "Amusement & Theme Parks", "desc": "Disney, Universal, roller coasters, water parks, zoos, aquariums, casinos & 10 maps", "render": "_lazy_load"},
            {"id": "language",  "icon": "🗣️", "name": "Languages & Scripts",  "desc": "Language families, endangered languages, writing systems, isolates, constructed languages & 10 maps", "render": "_lazy_load"},
            {"id": "martial_arts", "icon": "🥋", "name": "Martial Arts & Combat", "desc": "Karate, Kung Fu, Muay Thai, BJJ, Judo, Taekwondo, fencing, wrestling, capoeira & 10 maps", "render": "_lazy_load"},
            {"id": "games",       "icon": "🎮", "name": "Games & Esports",      "desc": "Game studios, esports arenas, arcade culture, chess, board games, conventions & 10 maps", "render": "_lazy_load"},
            {"id": "perfume",     "icon": "🌸", "name": "Perfume & Fragrance",  "desc": "Grasse, perfume houses, aromatic plants, incense origins, spice routes & 10 maps", "render": "_lazy_load"},
            {"id": "toy",        "icon": "🧸", "name": "Toys & Collectibles",  "desc": "LEGO, toy museums, doll traditions, model trains, teddy bears, action figures & 10 maps", "render": "_lazy_load"},
            {"id": "dance",       "icon": "💃", "name": "Dance & Performing Arts", "desc": "Ballet, flamenco, tango, Indian classical, African dance, hip-hop, Irish dance & 10 maps", "render": "_lazy_load"},
            {"id": "instrument", "icon": "🎻", "name": "Musical Instruments", "desc": "Violin luthiers, piano makers, guitar workshops, organs, bells, drums & 10 maps", "render": "_lazy_load"},
            {"id": "chocolate",   "icon": "🍫", "name": "Chocolate & Confectionery", "desc": "Cacao origins, chocolate factories, Belgian & Swiss heritage, patisseries & 10 maps", "render": "_lazy_load"},
            {"id": "circus",      "icon": "🎪", "name": "Circus & Performance",    "desc": "Historic circuses, street performance, magic schools, carnival, puppets & 10 maps", "render": "_lazy_load"},
            {"id": "horse",      "icon": "🐴", "name": "Horses & Equestrian",    "desc": "Famous racetracks, horse breeds, polo clubs, wild horses, cavalry history & 10 maps", "render": "_lazy_load"},
            {"id": "tea",         "icon": "🍵", "name": "Tea & Tea Culture",      "desc": "Tea plantations, ceremonies, teahouses, origins, varieties, British tea, matcha & 10 maps", "render": "_lazy_load"},
            {"id": "marathon",    "icon": "🏃", "name": "Marathon & Running",    "desc": "World marathon majors, ultramarathons, trail running, parkrun, ironman venues & 10 maps", "render": "_lazy_load"},
            {"id": "candy",       "icon": "🍬", "name": "Candy & Sweets",        "desc": "Candy traditions, chocolate factories, marzipan, gummy bears, cotton candy & 10 maps", "render": "_lazy_load"},
            {"id": "pasta",       "icon": "🍝", "name": "Pasta & Noodles",       "desc": "Italian pasta regions, Asian noodles, dumplings, couscous, gnocchi origins & 10 maps", "render": "_lazy_load"},
            {"id": "carnival",    "icon": "🎭", "name": "Carnival & Festivals",  "desc": "Rio, Venice, Mardi Gras, mask traditions, fire festivals, lantern festivals & 10 maps", "render": "_lazy_load"},
            {"id": "ice_cream",   "icon": "🍦", "name": "Ice Cream & Gelato",   "desc": "Gelato origins, ice cream history, frozen desserts, parlors, artisan makers & 10 maps", "render": "_lazy_load"},
            {"id": "street_food", "icon": "🍢", "name": "Street Food & Markets", "desc": "Bangkok, Tokyo, Mexico City, Istanbul street food, night markets, hawker centers & 10 maps", "render": "_lazy_load"},
            {"id": "waterpark",   "icon": "🏊", "name": "Water Parks & Pools",  "desc": "World's greatest water parks, historic pools, wave machines, lazy rivers & 10 maps", "render": "_lazy_load"},
            {"id": "cheese",      "icon": "🧀", "name": "Cheese & Dairy",       "desc": "French AOC, Italian DOP, Swiss, British, Dutch, Greek, artisan cheese & 10 maps", "render": "_lazy_load"},
            {"id": "mask",       "icon": "🎭", "name": "Traditional Masks",    "desc": "African, Asian, Oceanic, Venetian, Noh, Day of the Dead masks & ceremonies", "render": "_lazy_load"},
            {"id": "bread",       "icon": "🍞", "name": "World Bread Heritage", "desc": "Historic bakeries, sourdough, boulangeries, flatbreads, bread museums & 10 maps", "render": "_lazy_load"},
            {"id": "indigenous", "icon": "🪶", "name": "Indigenous Heritage", "desc": "Aboriginal, Native American, Maori, Sami, tribal lands, rock art & 10 maps", "render": "_lazy_load"},
            {"id": "beer",        "icon": "🍺", "name": "Beer & Brewing",       "desc": "Trappist, German, Czech, British pub, craft beer, hops, Oktoberfest & 10 maps", "render": "_lazy_load"},
            {"id": "food_security", "icon": "🌾", "name": "Food Security AI", "desc": "Agricultural capacity: soil fertility, water availability, crop suitability & food resilience", "render": "_lazy_load"},
            {"id": "cultural_heritage", "icon": "🏛️", "name": "Cultural Heritage AI", "desc": "Cultural heritage assessment: historical sites, traditions, archaeological potential & preservation", "render": "_lazy_load"},
            {"id": "demographic_profiler", "icon": "👥", "name": "Demographic Profiler AI", "desc": "Settlement patterns: building density, services, commerce, recreation & education analysis", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Infrastructure & Territory",
        "color": "amber",
        "modules": [
            {"id": "osm_explorer",  "icon": "🏗️", "name": "OSM Explorer",  "desc": "OpenStreetMap features via Overpass API",        "render": "_lazy_load"},
            {"id": "landuse",      "icon": "🏘️", "name": "Land Use",      "desc": "Urban patterns & land use analysis",             "render": "_lazy_load"},
            {"id": "archaeology",   "icon": "🏛️", "name": "Archaeology",   "desc": "Heritage & archaeological sites explorer",       "render": "_lazy_load"},
            {"id": "lidar_browser", "icon": "📐", "name": "LiDAR Browser", "desc": "OpenTopography & USGS 3DEP datasets",            "render": "_lazy_load"},
            {"id": "energy",        "icon": "⚡", "name": "Energy & Power", "desc": "Power plants, renewables, energy grid infrastructure", "render": "_lazy_load"},
            {"id": "transport",     "icon": "✈️", "name": "Transport Maps", "desc": "Airports, railways, shipping routes, metro, ferries, canals & 12 transport maps", "render": "_lazy_load"},
            {"id": "urban",         "icon": "🏙️", "name": "Urban Analytics", "desc": "Green spaces, hospitals, schools, sports, parking, building heights & 12 city maps", "render": "_lazy_load"},
            {"id": "economics",     "icon": "💰", "name": "Economics & Trade", "desc": "GDP, trade blocs, stock exchanges, shipping ports, oil fields & 10 economic maps", "render": "_lazy_load"},
            {"id": "technology",    "icon": "💻", "name": "Internet & Tech",  "desc": "Submarine cables, data centers, tech hubs, particle accelerators & 10 tech maps", "render": "_lazy_load"},
            {"id": "education",    "icon": "🎓", "name": "Education & Research", "desc": "Universities, libraries, museums, Nobel prizes, science parks, botanical gardens & 10 maps", "render": "_lazy_load"},
            {"id": "cost_living", "icon": "💰", "name": "Cost of Living",      "desc": "Living costs, Big Mac index, salaries, real estate, GDP, tax rates, digital nomad index & 10 maps", "render": "_lazy_load"},
            {"id": "railway",     "icon": "🚂", "name": "Railway & Trains",    "desc": "World railways, high-speed trains, Trans-Siberian, metro systems, scenic routes & 10 maps", "render": "_lazy_load"},
            {"id": "airport",   "icon": "✈️", "name": "Airports & Aviation",  "desc": "Busiest airports, extreme runways, aviation history, military bases, spaceports & 10 maps", "render": "_lazy_load"},
            {"id": "bridge",    "icon": "🌉", "name": "Bridges & Engineering", "desc": "Greatest bridges, tunnels, dams, ancient engineering, mega-construction & 10 maps", "render": "_lazy_load"},
            {"id": "mining",     "icon": "⛏️", "name": "Mining & Resources",  "desc": "World mines, gold, rare earth, oil fields, diamonds, lithium triangle & 10 maps", "render": "_lazy_load"},
            {"id": "prison",   "icon": "🔒", "name": "Prisons & Justice",   "desc": "Famous prisons, Alcatraz, gulags, justice systems, incarceration rates & 10 maps", "render": "_lazy_load"},
            {"id": "clock",    "icon": "🕰️", "name": "Clocks & Timekeeping", "desc": "Clock towers, watchmaking, sundials, atomic clocks, observatories, time capsules & 10 maps", "render": "_lazy_load"},
            {"id": "fortress", "icon": "🏰", "name": "Fortresses & Castles", "desc": "Medieval castles, crusader forts, star forts, great walls, citadels, underground bunkers & 10 maps", "render": "_lazy_load"},
            {"id": "market",  "icon": "🏪", "name": "Markets & Bazaars",   "desc": "Grand bazaars, flea markets, floating markets, night markets, stock exchanges & 10 maps", "render": "_lazy_load"},
            {"id": "coin",    "icon": "🪙", "name": "Coins & Numismatics", "desc": "Ancient mints, coin hoards, numismatic museums, gold rush, cryptocurrency & 10 maps", "render": "_lazy_load"},
            {"id": "jewelry",  "icon": "💎", "name": "Jewelry & Gemstones", "desc": "Diamond mines, gemstone origins, pearl farms, crown jewels, cutting centers & 10 maps", "render": "_lazy_load"},
            {"id": "ancient_weapons", "icon": "⚔️", "name": "Ancient Weapons & Armor", "desc": "Katana forges, European swords, Damascus steel, battlefields, armor workshops & 10 maps", "render": "_lazy_load"},
            {"id": "gemstone", "icon": "💎", "name": "Gemstones & Crystals", "desc": "Diamond, emerald, ruby mines, opal, jade, amber, pearl farms, gem cutting & 10 maps", "render": "_lazy_load"},
            {"id": "ancient",   "icon": "🏺", "name": "Ancient World",       "desc": "Oldest cities, ancient libraries, ports, observatories, mining, cave art, roads & 10 maps", "render": "_lazy_load"},
            {"id": "skyscraper", "icon": "🏙️", "name": "Skyscrapers & Towers", "desc": "Tallest buildings, observation decks, TV towers, sky bridges, iconic skylines & 10 maps", "render": "_lazy_load"},
            {"id": "connectivity_score", "icon": "📶", "name": "Connectivity Score AI", "desc": "Digital infrastructure: cell towers, internet coverage, fiber optic & connectivity index", "render": "_lazy_load"},
            {"id": "transportation_ai", "icon": "🚗", "name": "Transportation AI", "desc": "Transport infrastructure: roads, transit, airports, ports, cycling & pedestrian access", "render": "_lazy_load"},
            {"id": "infrastructure_scan", "icon": "🏗️", "name": "Infrastructure Scan AI", "desc": "10-category infrastructure completeness: healthcare, education, emergency, utilities & more", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Thematic & Composite Maps",
        "color": "violet",
        "modules": [
            {"id": "thematic",      "icon": "🗺️", "name": "Thematic Maps",     "desc": "Languages, religions, cost of living, empires & more composite maps",  "render": "_lazy_load"},
            {"id": "historical",    "icon": "📜", "name": "Historical Maps",   "desc": "Ancient maps overlaid on modern, empire boundaries, historical events","render": "_lazy_load"},
            {"id": "civilization",  "icon": "🏛️", "name": "Civilization Maps", "desc": "Agriculture origins, writing systems, trade routes, colonialism, UNESCO","render": "_lazy_load"},
            {"id": "architecture", "icon": "🏰", "name": "Architecture Maps", "desc": "Castles, skyscrapers, bridges, cathedrals, ancient ruins, modern wonders & 10 maps", "render": "_lazy_load"},
            {"id": "mythology",    "icon": "🐉", "name": "Mythology & Legends", "desc": "Greek, Norse, Egyptian, Celtic, Hindu, Japanese, Mesoamerican myths & cryptid sightings", "render": "_lazy_load"},
            {"id": "paranormal",   "icon": "👽", "name": "Paranormal & UFO",    "desc": "UFO sightings, haunted places, Bermuda Triangle, crop circles, ley lines & 10 maps", "render": "_lazy_load"},
            {"id": "literature",   "icon": "📚", "name": "Literature & Books",  "desc": "Nobel laureates, literary cities, authors, libraries, bookshops, festivals & 10 maps", "render": "_lazy_load"},
            {"id": "empires",     "icon": "👑", "name": "Ancient Empires",     "desc": "Roman, Greek, Egyptian, Mongol, Ottoman, British, Chinese, Persian empires & famous battles", "render": "_lazy_load"},
            {"id": "unesco",      "icon": "🏛️", "name": "UNESCO Heritage",    "desc": "World Heritage, biosphere reserves, geoparks, endangered sites, creative cities & 10 maps", "render": "_lazy_load"},
            {"id": "exploration", "icon": "🧭", "name": "Exploration & Discovery", "desc": "Great expeditions, polar routes, mountain ascents, space launch sites & 10 maps", "render": "_lazy_load"},
            {"id": "trade_routes", "icon": "🐪", "name": "Ancient Trade Routes", "desc": "Silk Road, spice routes, amber road, Viking routes, modern shipping & 10 maps", "render": "_lazy_load"},
            {"id": "crypto",       "icon": "🔐", "name": "Cryptography & Codes", "desc": "Enigma, spy networks, unsolved codes, number stations, treasure maps & 10 maps", "render": "_lazy_load"},
            {"id": "treasure",     "icon": "💎", "name": "Treasure & Lost Cities", "desc": "El Dorado, Atlantis, pirate treasure, sunken gold, lost civilizations & 10 maps", "render": "_lazy_load"},
            {"id": "glass",        "icon": "🔮", "name": "Glass & Crystal Heritage", "desc": "Murano glass, Bohemian crystal, stained glass, glassblowing, Art Nouveau & 10 maps", "render": "_lazy_load"},
            {"id": "ruins",        "icon": "🏚️", "name": "Ruins & Lost Cities",  "desc": "Ancient wonders, Pompeii, megalithic sites, underwater ruins, ghost towns & 10 maps", "render": "_lazy_load"},
            {"id": "calendar",     "icon": "📅", "name": "Calendars & Observatories", "desc": "Stonehenge, Mayan calendars, sun temples, stone circles, modern telescopes & 10 maps", "render": "_lazy_load"},
            {"id": "cryptid",      "icon": "🦎", "name": "Cryptids & Monsters",  "desc": "Loch Ness, Bigfoot, sea serpents, Mothman, dragon legends, werewolves & 10 maps", "render": "_lazy_load"},
            {"id": "myth_locations",     "icon": "⚡", "name": "Myth & Legend Sites", "desc": "Olympus, Norse sites, Egyptian temples, Celtic Avalon, Arthurian legends & 10 maps", "render": "_lazy_load"},
            {"id": "writing",      "icon": "📝", "name": "Ancient Writing",    "desc": "Cuneiform, hieroglyphs, undeciphered scripts, ancient libraries, printing press & 10 maps", "render": "_lazy_load"},
            {"id": "haunted",      "icon": "👻", "name": "Haunted Places",    "desc": "Haunted houses, ghost towns, catacombs, witch trials, abandoned asylums & 10 maps", "render": "_lazy_load"},
            {"id": "conspiracy",   "icon": "🔺", "name": "Mystery & Conspiracy", "desc": "Secret bases, ancient aliens, crop circles, UFO sites, ley lines, lost civilizations & 10 maps", "render": "_lazy_load"},
            {"id": "museum",      "icon": "🏛️", "name": "Museums & Galleries", "desc": "World greatest museums, modern art, science, natural history, war museums & 10 maps", "render": "_lazy_load"},
            {"id": "opera",        "icon": "🎭", "name": "Opera & Theater",     "desc": "Opera houses, Shakespeare, ancient theaters, Broadway, concert halls, composers & 10 maps", "render": "_lazy_load"},
            {"id": "cemetery",     "icon": "⚰️", "name": "Cemeteries & Memorials", "desc": "Famous cemeteries, war memorials, mausoleums, celebrity graves, ossuary & 10 maps", "render": "_lazy_load"},
            {"id": "library",    "icon": "📚", "name": "Libraries & Archives",  "desc": "World greatest libraries, ancient archives, rare books, scriptoriums & 10 maps", "render": "_lazy_load"},
            {"id": "medieval",     "icon": "🏰", "name": "Medieval Heritage",   "desc": "Castles, walled cities, monasteries, cathedrals, Knights Templar, Viking sites & 10 maps", "render": "_lazy_load"},
            {"id": "zodiac",       "icon": "♈", "name": "Astrology & Zodiac",   "desc": "Ancient observatories, zodiac origins, planetariums, ley lines, solstice sites & 10 maps", "render": "_lazy_load"},
            {"id": "calligraphy", "icon": "✒️", "name": "Calligraphy & Writing Art", "desc": "Chinese, Japanese, Arabic calligraphy, illuminated manuscripts, typography & 10 maps", "render": "_lazy_load"},
            {"id": "sculpture",   "icon": "🗿", "name": "Sculpture & Statues",   "desc": "Tallest statues, Greek classics, Renaissance, megalithic monuments, sculpture parks & 10 maps", "render": "_lazy_load"},
            {"id": "robot",      "icon": "🤖", "name": "Robots & AI",          "desc": "Robot factories, AI labs, humanoid robots, Mars rovers, automaton history & 10 maps", "render": "_lazy_load"},
            {"id": "silk_road",   "icon": "🐫", "name": "Silk Road & Caravans", "desc": "Ancient Silk Road, caravanserais, Samarkand, spice routes, maritime silk road & 10 maps", "render": "_lazy_load"},
            {"id": "dragon",     "icon": "🐲", "name": "Dragons & Legends",   "desc": "Dragon legends, dragon-themed sites, medieval bestiaries, komodo, sea serpents & 10 maps", "render": "_lazy_load"},
            {"id": "origami",     "icon": "🦢", "name": "Origami & Paper Arts", "desc": "Japanese origami, paper making history, kirigami, kite traditions, paper architecture & 10 maps", "render": "_lazy_load"},
            {"id": "train_journey", "icon": "🚂", "name": "Epic Train Journeys", "desc": "Trans-Siberian, Orient Express, Glacier Express, Shinkansen, The Ghan & 10 routes", "render": "_lazy_load"},
            {"id": "mythology_deep", "icon": "⚡", "name": "Deep Mythology",    "desc": "Creation myths, underworld legends, trickster gods, divine weapons, sacred animals & 10 maps", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Disasters & Risk",
        "color": "red",
        "modules": [
            {"id": "disaster",  "icon": "⚠️", "name": "Disaster Maps",  "desc": "Tectonic plates, volcanoes, tsunamis, hurricanes, nuclear risk & 10 hazard maps", "render": "_lazy_load"},
            {"id": "military",   "icon": "🎖️", "name": "Military & Geopolitics", "desc": "NATO, nuclear powers, disputed territories, border walls, conflict zones", "render": "_lazy_load"},
            {"id": "pollution",  "icon": "☢️", "name": "Pollution & Crises",  "desc": "Ocean plastic, oil spills, endangered species, nuclear zones, dead zones", "render": "_lazy_load"},
            {"id": "crime_safety",      "icon": "🔒", "name": "Crime & Safety",     "desc": "Peace index, safest cities, travel advisories, piracy, cybercrime & 10 maps", "render": "_lazy_load"},
            {"id": "borders",   "icon": "🏴", "name": "Borders & Conflicts", "desc": "Border walls, disputed territories, DMZ, enclaves, micronations, divided cities & 10 maps", "render": "_lazy_load"},
            {"id": "pandemic", "icon": "🦠", "name": "Pandemics & Disease", "desc": "Black Death, Spanish Flu, COVID-19, cholera, malaria, vaccination coverage & 10 maps", "render": "_lazy_load"},
            {"id": "nuclear",  "icon": "☢️", "name": "Nuclear & Radiation", "desc": "Nuclear plants, Chernobyl, test sites, weapons, waste storage, Hiroshima & 10 maps", "render": "_lazy_load"},
            {"id": "volcano_deep", "icon": "🌋", "name": "Deep Volcanology", "desc": "Supervolcanoes, calderas, lava tubes, submarine volcanoes, volcanic wine & 10 maps", "render": "_lazy_load"},
            {"id": "volcano_live",   "icon": "🌋", "name": "Live Volcanoes",   "desc": "Currently erupting, Ring of Fire, Iceland, Etna, Indonesia, Hawaii, Japan & seismicity", "render": "_lazy_load"},
            {"id": "predictive_risk", "icon": "🔥", "name": "Predictive Risk Model", "desc": "Fire, flood & landslide risk prediction with heatmap", "render": "_lazy_load"},
            {"id": "climate_risk_ai", "icon": "🌡️", "name": "Climate Risk Intelligence", "desc": "14-day climate risk forecast: heat, cold, flood, drought, wind, UV & storm risk", "render": "_lazy_load"},
            {"id": "flood_model", "icon": "🌊", "name": "Flood Risk Model AI", "desc": "Detailed flood risk: precipitation, terrain drainage, soil runoff, water proximity & capacity", "render": "_lazy_load"},
            {"id": "wildfire_model", "icon": "🔥", "name": "Wildfire Risk AI", "desc": "Fire Weather Index: drought, fuel load, terrain fire risk, ignition & suppression difficulty", "render": "_lazy_load"},
            {"id": "seismic_profiler", "icon": "📊", "name": "Seismic Intelligence AI", "desc": "Deep seismic analysis: magnitude distribution, depth profile, ground stability & trend", "render": "_lazy_load"},
            {"id": "disaster_resilience", "icon": "🏰", "name": "Disaster Resilience AI", "desc": "6-disaster resilience: earthquake, flood, wildfire, landslide, storm & drought preparedness", "render": "_lazy_load"},
            {"id": "coastal_analysis", "icon": "🌊", "name": "Coastal Intelligence AI", "desc": "7-index coastal analysis: erosion, sea level rise, storm surge, marine resources & flood risk", "render": "_lazy_load"},
            {"id": "emergency_response", "icon": "🚑", "name": "Emergency Response AI", "desc": "6-index emergency readiness: services, evacuation, shelter, comms, medical & response time", "render": "_lazy_load"},
            {"id": "climate_adaptation", "icon": "🌡️", "name": "Climate Adaptation AI", "desc": "Climate change resilience: heat stress, drought risk, flood adaptation & 30-year trends", "render": "_lazy_load"},
            {"id": "pollution_tracker", "icon": "☢️", "name": "Pollution Tracker AI", "desc": "Environmental pollution: air quality, industrial sources, water & noise pollution tracking", "render": "_lazy_load"},
            {"id": "shelter_analysis", "icon": "🏕️", "name": "Shelter Analysis AI", "desc": "Habitability assessment: terrain, ground stability, water access, weather & hazard exposure", "render": "_lazy_load"},
            {"id": "geological_risk", "icon": "🪨", "name": "Geological Risk AI", "desc": "Ground stability: seismic activity, slope, soil composition, bedrock, karst & volcanic proximity", "render": "_lazy_load"},
            {"id": "security_assessment", "icon": "🛡️", "name": "Security Assessment AI", "desc": "Physical security: surveillance, lighting, emergency services, access control & visibility", "render": "_lazy_load"},
            {"id": "fire_weather", "icon": "🔥", "name": "Fire Weather Index AI", "desc": "Real-time fire danger: weather, drought, fuel load, terrain spread & suppression difficulty", "render": "_lazy_load"},
            {"id": "evacuation_route", "icon": "🚨", "name": "Evacuation Route AI", "desc": "Escape routes, safe zones, chokepoints, transport options & hazard zones for 4 scenarios", "render": "_lazy_load"},
            {"id": "scenario_simulator", "icon": "🎭", "name": "Scenario Simulator AI", "desc": "Simulate flood, earthquake, wildfire, spill & sea level rise with impact projections", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Space & Tracking",
        "color": "indigo",
        "modules": [
            {"id": "space",      "icon": "🚀", "name": "Space & ISS",    "desc": "ISS tracker, astronauts, near-Earth objects, NASA APOD", "render": "_lazy_load"},
            {"id": "astronomy",  "icon": "🔭", "name": "Astronomy Maps", "desc": "Observatories, light pollution, impact craters, launch sites, dark sky reserves", "render": "_lazy_load"},
            {"id": "maritime",   "icon": "⚓", "name": "Maritime & Navigation", "desc": "Lighthouses, shipwrecks, straits, ocean currents, naval battles, exploration voyages", "render": "_lazy_load"},
            {"id": "shipwreck", "icon": "🚢", "name": "Shipwrecks & Disasters", "desc": "Titanic, treasure ships, WW2 wrecks, ghost ships, submarine graves & 10 maps", "render": "_lazy_load"},
            {"id": "lighthouse", "icon": "🏠", "name": "Lighthouses & Beacons", "desc": "Famous lighthouses, ancient beacons, haunted towers, remote & extreme lighthouses & 10 maps", "render": "_lazy_load"},
            {"id": "underwater", "icon": "🤿", "name": "Underwater World",    "desc": "Dive sites, ocean trenches, coral reefs, cenotes, hydrothermal vents, submarine volcanoes & 10 maps", "render": "_lazy_load"},
            {"id": "space_tracker", "icon": "🛸", "name": "Space Exploration",  "desc": "Launch sites, observatories, radio telescopes, meteorite craters, Deep Space Network & 10 maps", "render": "_lazy_load"},
            {"id": "submarine", "icon": "🔱", "name": "Submarines & Deep Sea", "desc": "Submarine bases, deep sea exploration, U-boats, nuclear subs, submersibles & 10 maps", "render": "_lazy_load"},
            {"id": "pirate",    "icon": "🏴‍☠️", "name": "Pirates & Buccaneers", "desc": "Pirate havens, treasure islands, famous raids, corsairs, privateer routes & 10 maps", "render": "_lazy_load"},
            {"id": "telescope", "icon": "🔭", "name": "Telescopes & Observatories", "desc": "Greatest telescopes, radio dishes, dark sky preserves, gravitational wave detectors & 10 maps", "render": "_lazy_load"},
            {"id": "night_vision", "icon": "🌙", "name": "Night Sky & Light Pollution", "desc": "Light pollution map, Bortle scale & best stargazing spots", "render": "_lazy_load"},
            {"id": "night_ops", "icon": "🌑", "name": "Night Operations AI", "desc": "Darkness assessment, Bortle scale, moon phase, cloud forecast & concealment analysis", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Real-Time Monitoring",
        "color": "cyan",
        "modules": [
            {"id": "realtime",  "icon": "📡", "name": "Real-Time Dashboard", "desc": "Live weather, earthquakes, air quality, ocean & solar conditions worldwide", "render": "_lazy_load"},
            {"id": "composite", "icon": "🔄", "name": "Composite Aggregator", "desc": "Multi-source fusion maps: livability, hazard risk, climate vulnerability & 10 composite maps", "render": "_lazy_load"},
            {"id": "global_realtime", "icon": "🌍", "name": "Global Real-Time Intel", "desc": "Live worldwide: earthquakes, fires, aircraft, disasters, ISS, space weather & real-time feeds", "render": "_lazy_load"},
            {"id": "global_dashboard", "icon": "🌐", "name": "Global Data Aggregator", "desc": "Worldwide intelligence: fuel/oil prices, cryptocurrency, currency exchange, weather summary, earthquakes & commodity data", "render": "_lazy_load"},
            {"id": "api_health", "icon": "🏥", "name": "API Health Monitor", "desc": "Real-time monitoring of all external API endpoints: status, response times, rate limits & health diagnostics", "render": "_lazy_load"},
        ],
    },
    {
        "category": "Tools",
        "color": "cyan",
        "modules": [
            {"id": "geocoder", "icon": "📍", "name": "Geocoder", "desc": "Nominatim address & coordinate lookup",    "render": "_lazy_load"},
            {"id": "history",  "icon": "📜", "name": "History",  "desc": "Browse & restore previous analyses",        "render": "_inline"},
            {"id": "ai_chat",  "icon": "🤖", "name": "AI Chat",  "desc": "Ask questions about geospatial analysis",   "render": "_inline"},
            {"id": "report_gen", "icon": "📋", "name": "Report Generator", "desc": "Generate downloadable HTML reports for any location", "render": "_lazy_load"},
        ],
    },
]

# Build flat lookup
_MODULE_LOOKUP = {}
for cat in MODULE_REGISTRY:
    for mod in cat["modules"]:
        if mod["id"] in _MODULE_LOOKUP:
            import logging as _log
            _log.getLogger(__name__).warning(
                f"Duplicate module ID '{mod['id']}' in category '{cat['category']}' "
                f"(already in '{_MODULE_LOOKUP[mod['id']]['category']}')")
        _MODULE_LOOKUP[mod["id"]] = {**mod, "category": cat["category"], "color": cat["color"]}


# ═══════════════════════════════════════════
# INLINE MODULE RENDERERS
# ═══════════════════════════════════════════

def _render_map_analysis(prompt, box_threshold, text_threshold, zoom_level, model_type, tile_size, overlap):
    """Map Analysis - draw areas for AI segmentation."""
    m = render_map()
    output = None
    try:
        if HAS_ST_FOLIUM:
            output = st_folium(m, height=550, width=None, returned_objects=["all_drawings", "last_clicked"], key="map_analysis_folium")
        else:
            raise ImportError("st_folium not available")
    except Exception:
        components.html(m._repr_html_(), height=550)
        st.warning("Interactive drawing unavailable. Install streamlit-folium: `pip install -U streamlit-folium`")

    # --- COORDINATE FEEDBACK ---
    last_clicked = output.get("last_clicked") if output else None
    if last_clicked:
        click_lat = last_clicked.get("lat", last_clicked.get("latitude"))
        click_lng = last_clicked.get("lng", last_clicked.get("longitude"))
        if click_lat is not None and click_lng is not None:
            from src.click_info import build_click_info
            active_rasters = []
            if 'results' in st.session_state:
                img = st.session_state.results.get("image")
                if img:
                    active_rasters.append(img)
            click_info = build_click_info(click_lat, click_lng, active_rasters)
            terrain_html = f' | Terrain: {click_info["terrain"]}' if click_info.get('terrain') else ''
            st.markdown(f"""
            <div class="coord-display">
                <span style="color:#06b6d4; font-weight:700;">Lat</span> {click_info['latitude']:.6f}
                &nbsp;&nbsp;
                <span style="color:#06b6d4; font-weight:700;">Lon</span> {click_info['longitude']:.6f}
                {terrain_html}
            </div>
            """, unsafe_allow_html=True)
            if click_info.get("pixel_data"):
                with st.expander("Band Values at Click Point"):
                    for band_name, val in click_info["pixel_data"].items():
                        st.write(f"**{band_name}**: {val:.1f}")

    # --- CONTROLS & DASHBOARD (below map) ---
    ctrl_col, dash_col = st.columns([1, 1])

    with ctrl_col:
        with st.expander("Analysis Controls", expanded=True):
            drawings = output.get("all_drawings") if output else None

            if drawings and len(drawings) > 0:
                num_areas = len(drawings)

                # Tile estimation
                total_est_tiles = 0
                for drawing in drawings:
                    geometry = drawing["geometry"]
                    coords = geometry["coordinates"][0]
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    bbox = [min(lons), min(lats), max(lons), max(lats)]
                    total_est_tiles += st.session_state.analyzer.estimate_tile_count(bbox, zoom=zoom_level, tile_size=tile_size)

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Selected Areas", num_areas)
                with c2:
                    st.metric("Estimated Tiles", total_est_tiles)

                can_analyze = True
                use_batched = total_est_tiles > 30
                if total_est_tiles > 2000:
                    st.error(f"Area too large ({total_est_tiles:,} tiles). Maximum 2,000 tiles allowed. Select a smaller area or lower zoom.")
                    can_analyze = False
                elif total_est_tiles > 500:
                    est_mb = total_est_tiles * 0.05
                    st.warning(f"Large area ({total_est_tiles:,} tiles, ~{est_mb:.0f} MB). Batched mode will be used.")

                if st.button(f"Analyze {num_areas} Area{'s' if num_areas > 1 else ''}", type="primary", disabled=not can_analyze, help="Run AI segmentation on selected map areas"):
                    if 'results' in st.session_state:
                        del st.session_state.results

                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    partial_download = st.empty()
                    stop_placeholder = st.empty()

                    combined_features = []
                    last_image = None
                    last_mask = None
                    last_csv = None
                    st.session_state.stop_analysis = False

                    def _save_partial(features, output_dir):
                        if not features:
                            return None
                        partial = {"type": "FeatureCollection", "features": features}
                        path = os.path.join(output_dir, "vectors_partial.geojson")
                        with open(path, 'w') as fp:
                            json.dump(partial, fp)
                        return path

                    try:
                        for i, drawing in enumerate(drawings):
                            if stop_placeholder.button("Stop & Export Partial", key=f"stop_{i}"):
                                st.session_state.stop_analysis = True
                            if st.session_state.get("stop_analysis", False):
                                st.warning(f"Stopped after {i}/{num_areas} areas.")
                                break

                            status_text.text(f"Processing area {i+1}/{num_areas}...")

                            geometry = drawing["geometry"]
                            coords = geometry["coordinates"][0]
                            lons = [c[0] for c in coords]
                            lats = [c[1] for c in coords]
                            bbox = [min(lons), min(lats), max(lons), max(lats)]

                            st.session_state.analyzer.download_image(bbox, zoom=zoom_level)
                            st.session_state.analyzer.split_image(tile_size=tile_size, overlap=overlap)

                            if use_batched:
                                def batch_progress(done, total):
                                    frac = ((i + done / max(total, 1)) / num_areas)
                                    progress_bar.progress(min(frac, 1.0))
                                    status_text.text(f"Area {i+1}/{num_areas} - tile {done}/{total}")
                                mask_path = st.session_state.analyzer.analyze_batched(
                                    prompt, box_threshold, text_threshold,
                                    model_type=model_type, batch_size=20,
                                    progress_callback=batch_progress)
                            else:
                                mask_path = st.session_state.analyzer.analyze(prompt, box_threshold, text_threshold, model_type=model_type)

                            gdf, csv_path = st.session_state.analyzer.process_results()

                            if gdf is not None and not gdf.empty:
                                with open(os.path.join(st.session_state.analyzer.output_dir, "vectors.geojson"), 'r') as f:
                                    feat_collection = json.load(f)
                                    combined_features.extend(feat_collection['features'])

                            last_image = st.session_state.analyzer.image_path
                            last_mask = mask_path
                            last_csv = csv_path
                            progress_bar.progress((i + 1) / num_areas)

                            if combined_features:
                                partial_path = _save_partial(combined_features, st.session_state.analyzer.output_dir)
                                if partial_path:
                                    with open(partial_path, 'r') as fp:
                                        partial_download.download_button(
                                            f"Download Partial ({len(combined_features)} features)",
                                            data=fp.read(),
                                            file_name="partial_results.geojson",
                                            mime="application/json",
                                            key=f"partial_dl_{i}"
                                        )

                        stop_placeholder.empty()
                        partial_download.empty()

                        if combined_features:
                            master_geojson = {"type": "FeatureCollection", "features": combined_features}
                            master_vector_path = os.path.join(st.session_state.analyzer.output_dir, "vectors_batch.geojson")
                            with open(master_vector_path, 'w') as f:
                                json.dump(master_geojson, f)

                            st.session_state.results = {
                                "image": last_image, "mask": last_mask,
                                "csv": last_csv, "vector": master_vector_path, "bbox": bbox
                            }
                            st.session_state.last_prompt = prompt
                            save_session(st.session_state.results)

                            from datetime import datetime
                            proj_name = f"{prompt}_{datetime.now().strftime('%H%M')}"
                            proj_id, _ = st.session_state.pm.create_project(proj_name)
                            st.session_state.pm.save_project(proj_id, {
                                "settings": {"prompt": prompt},
                                "image_path": last_image,
                                "mask_path": last_mask,
                                "vector_path": master_vector_path,
                                "csv_path": last_csv
                            })
                            st.rerun()
                        else:
                            st.warning("No objects found in any area.")

                    except Exception as e:
                        st.error("Analysis error:")
                        st.exception(e)
                        if combined_features:
                            partial_path = _save_partial(combined_features, st.session_state.analyzer.output_dir)
                            st.warning(f"Partial: {len(combined_features)} features saved before error.")
                            if partial_path:
                                with open(partial_path, 'r') as fp:
                                    st.download_button(
                                        f"Download Partial ({len(combined_features)} features)",
                                        data=fp.read(),
                                        file_name="partial_results.geojson",
                                        mime="application/json",
                                        key="partial_dl_error"
                                    )
            else:
                st.info("Draw a rectangle on the map to select an analysis area.", icon="🖊️")

    # --- DASHBOARD PANEL (Power BI style) ---
    with dash_col:
        if 'results' in st.session_state:
            res = st.session_state.results
            feature_count = 0
            if res.get("vector") and os.path.exists(res["vector"]):
                try:
                    with open(res["vector"], 'r') as f:
                        fc = json.load(f)
                    feature_count = len(fc.get("features", []))
                except Exception:
                    pass

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Objects Found", feature_count, help="Total detected features")
            with m2:
                st.metric("Prompt", st.session_state.get("last_prompt", "—"))
            with m3:
                area_str = "—"
                if res.get("bbox"):
                    b = res["bbox"]
                    area_str = f"{abs(b[2]-b[0])*111:.1f} x {abs(b[3]-b[1])*111:.1f} km"
                st.metric("Area", area_str)

            display_results(
                res["image"], res["mask"],
                res.get("vector"), res.get("bbox")
            )
            display_dataframe(res.get("csv"))
        else:
            st.markdown("""
            <div class="glass-panel" style="text-align:center; padding:3rem 2rem;">
                <p style="color:#8b97b0; font-size:1.1rem; margin:0;">No analysis results yet</p>
                <p style="color:#8a8a93; font-size:0.85rem; margin:0.5rem 0 0;">Draw an area on the map and click Analyze to see results here</p>
            </div>
            """, unsafe_allow_html=True)


def _render_image_analysis(prompt, box_threshold, text_threshold, model_type):
    """Image Analysis - upload aerial/drone images."""
    st.markdown("""
    <div class="tab-header violet">
        <h4>Image Analysis</h4>
        <p>Upload aerial or drone images for AI-powered segmentation and object detection.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        image_path = render_image_uploader()
    with col2:
        if image_path:
            with st.expander("Analysis Settings", expanded=True):
                st.markdown(f"**Prompt**: {prompt}")
                st.markdown(f"**Model**: {model_type}")
                if st.button("Run Image Analysis", type="primary", help="Detect objects in uploaded image"):
                    with st.spinner("Scanning image..."):
                        try:
                            mask_path = st.session_state.analyzer.analyze_image(image_path, prompt, box_threshold, text_threshold, model_type=model_type)
                            gdf, csv_path = st.session_state.analyzer.process_results()
                            st.session_state.results = {
                                "image": image_path, "mask": mask_path,
                                "csv": csv_path,
                                "vector": os.path.join(st.session_state.analyzer.output_dir, "vectors.geojson"),
                                "bbox": None
                            }
                            st.success("Analysis complete!")
                            st.session_state.last_prompt = prompt
                            save_session(st.session_state.results)
                            from datetime import datetime
                            proj_name = f"{prompt}_{datetime.now().strftime('%H%M')}"
                            proj_id, _ = st.session_state.pm.create_project(proj_name)
                            st.session_state.pm.save_project(proj_id, {
                                "settings": {"prompt": prompt},
                                "image_path": image_path, "mask_path": mask_path,
                                "vector_path": os.path.join(st.session_state.analyzer.output_dir, "vectors.geojson"),
                                "csv_path": csv_path
                            })
                        except Exception as e:
                            st.error(f"Error: {e}")

    if 'results' in st.session_state and st.session_state.results.get("bbox") is None:
        st.divider()
        display_results(
            st.session_state.results["image"],
            st.session_state.results["mask"],
            st.session_state.results.get("vector"),
            st.session_state.results.get("bbox")
        )
        display_dataframe(st.session_state.results.get("csv"))


def _render_lidar_upload():
    """LiDAR Upload - LAS/LAZ point cloud processing."""
    st.markdown("""
    <div class="tab-header amber">
        <h4>LiDAR Point Cloud</h4>
        <p>Upload LAS/LAZ files for elevation heatmaps, 3D visualization, and DEM export.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_lidar = st.file_uploader(
        "Upload LiDAR File",
        type=['las', 'laz'],
        help="LiDAR point cloud in LAS or LAZ format"
    )

    if uploaded_lidar:
        try:
            lidar_dir = "output/lidar"
            os.makedirs(lidar_dir, exist_ok=True)
            # Sanitize filename: strip path components, allow only safe chars
            safe_name = os.path.basename(uploaded_lidar.name)
            safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
            if not safe_name.lower().endswith(('.las', '.laz')):
                safe_name += ".las"
            lidar_path = os.path.join(lidar_dir, safe_name)
            with open(lidar_path, "wb") as f:
                f.write(uploaded_lidar.getbuffer())

            from src.lidar_processor import LidarProcessor
            lp = LidarProcessor()
            try:
                lp.load_point_cloud(lidar_path)
            except ImportError:
                st.error("laspy library not installed")
                st.code("pip install laspy[lazrs]", language="bash")
                st.stop()

            stats = lp.get_statistics()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Points", f"{stats['total_points']:,}")
            c2.metric("Max Elev.", f"{stats['z_max']:.1f} m")
            c3.metric("Min Elev.", f"{stats['z_min']:.1f} m")
            c4.metric("Mean Elev.", f"{stats['z_mean']:.1f} m")

            lidar_view, lidar_3d, lidar_export = st.tabs(["2D Elevation", "3D View", "Export"])

            with lidar_view:
                with st.spinner("Generating elevation map..."):
                    try:
                        elev_img = lp.create_2d_elevation_map(resolution=1.0)
                        st.image(elev_img, caption="Elevation Heatmap", use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not generate map: {e}")

                las = lp.las
                if hasattr(las, 'classification'):
                    import pandas as pd
                    class_labels = {
                        0: "Never Classified", 1: "Unassigned", 2: "Ground",
                        3: "Low Vegetation", 4: "Medium Vegetation", 5: "High Vegetation",
                        6: "Building", 7: "Low Point", 9: "Water",
                        11: "Road Surface", 17: "Bridge Deck",
                    }
                    vc = pd.Series(las.classification).value_counts()
                    class_df = pd.DataFrame({
                        "Classification": [class_labels.get(c, f"Class {c}") for c in vc.index],
                        "Points": vc.values,
                        "%": [f"{(v / stats['total_points'] * 100):.1f}%" for v in vc.values]
                    })
                    with st.expander("Classification Breakdown"):
                        st.dataframe(class_df, use_container_width=True, hide_index=True)

            with lidar_3d:
                with st.spinner("Preparing 3D view..."):
                    try:
                        import pydeck as pdk
                        df_3d = lp.create_3d_pydeck_data(max_points=300_000)
                        cx, cy = float(df_3d["x"].mean()), float(df_3d["y"].mean())
                        layer = pdk.Layer("ScatterplotLayer", data=df_3d,
                            get_position=["x", "y", "z"],
                            get_fill_color=["r", "g", "b", 200],
                            get_radius=0.5, pickable=True)
                        deck = pdk.Deck(layers=[layer],
                            initial_view_state=pdk.ViewState(latitude=cy, longitude=cx, zoom=18, pitch=60, bearing=30),
                            map_provider=None)
                        st.pydeck_chart(deck)
                    except Exception as e:
                        st.warning(f"3D view failed: {e}")

            with lidar_export:
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("Export DEM GeoTIFF", help="Generate Digital Elevation Model"):
                        with st.spinner("Generating DEM..."):
                            dem_path = os.path.join(lidar_dir, "dem_output.tif")
                            lp.export_dem_raster(dem_path, resolution=1.0)
                            with open(dem_path, "rb") as f_dem:
                                st.download_button("Download DEM", f_dem, file_name="dem.tif", mime="image/tiff")
                with ec2:
                    if st.button("Export Point Sample CSV", help="Download 10k random points as CSV"):
                        import pandas as pd
                        import numpy as np
                        las = lp.las
                        sample_size = min(10000, stats['total_points'])
                        indices = np.random.choice(stats['total_points'], sample_size, replace=False)
                        csv_data = pd.DataFrame({
                            "X": las.x[indices], "Y": las.y[indices], "Z": las.z[indices],
                            "Intensity": las.intensity[indices] if hasattr(las, 'intensity') else None,
                            "Class": las.classification[indices] if hasattr(las, 'classification') else None,
                        })
                        csv_path = os.path.join(lidar_dir, f"{uploaded_lidar.name}_sample.csv")
                        csv_data.to_csv(csv_path, index=False)
                        with open(csv_path, "rb") as f_csv:
                            st.download_button("Download CSV", f_csv, file_name=f"{uploaded_lidar.name}_sample.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Error processing LiDAR: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("Upload a LAS/LAZ file to begin LiDAR analysis.")


def _render_history():
    """History - browse and restore previous analyses."""
    st.markdown("""
    <div class="tab-header pink">
        <h4>Analysis History</h4>
        <p>Previous analyses are saved automatically. Click Load to restore results.</p>
    </div>
    """, unsafe_allow_html=True)
    selected = render_history_gallery(st.session_state.pm)
    if selected:
        data = st.session_state.pm.load_project(selected)
        if data:
            files = data.get("files", {})
            st.session_state.results = {
                "image": files.get("image.tif"),
                "mask": files.get("mask.tif"),
                "csv": files.get("data.csv"),
                "vector": files.get("vectors.geojson")
            }
            st.session_state.last_prompt = data.get("prompt", "")
            st.rerun()


def _render_ai_chat():
    """AI Chat - ask questions about geospatial analysis."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>AI Assistant</h4>
        <p>Ask questions about geospatial analysis, data interpretation, or platform usage.</p>
    </div>
    """, unsafe_allow_html=True)
    from src.ai_agent import get_agent
    MAX_CHAT_HISTORY = 200
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    # Evict old messages to prevent memory bloat
    if len(st.session_state.chat_history) > MAX_CHAT_HISTORY:
        st.session_state.chat_history = st.session_state.chat_history[-MAX_CHAT_HISTORY:]
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    user_input = st.chat_input("Ask about TerraScout AI...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        agent = get_agent("rule_based")
        response = agent.run(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


# ═══════════════════════════════════════════
# CATALOG HOME PAGE
# ═══════════════════════════════════════════

def render_catalog_home():
    """Render the catalog home with category sections and module cards (ops-center style)."""
    # Navigation bar
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("\u2190 Command Center", key="catalog_top_back", use_container_width=True):
            st.session_state.current_page = "command_center"
            st.rerun()

    # Total module count
    total_modules = sum(len(cat.get("modules", [])) for cat in MODULE_REGISTRY)
    st.markdown(
        f'<div style="text-align:center;margin-bottom:1.2rem;">'
        f'<h2 style="color:#e0e8f0;margin:0 0 4px;font-family:JetBrains Mono,monospace;">'
        f'MODULE CATALOG</h2>'
        f'<p style="color:#5a7090;margin:0;font-family:JetBrains Mono,monospace;font-size:0.82rem;">'
        f'{total_modules} modules across {len(MODULE_REGISTRY)} categories</p></div>',
        unsafe_allow_html=True,
    )

    # Category quick-jump strip
    cat_names = [cat["category"] for cat in MODULE_REGISTRY]
    _cat_ops = {
        "cyan": "#00f0ff", "violet": "#aa55ff", "emerald": "#00ff88",
        "pink": "#ff66aa", "amber": "#ffaa00", "red": "#ff3344",
        "indigo": "#4488ff", "blue": "#4488ff", "orange": "#ffaa00",
        "teal": "#00f0ff",
    }
    jump_items = []
    for cat in MODULE_REGISTRY:
        c = _cat_ops.get(cat.get("color", ""), "#00f0ff")
        cnt = len(cat.get("modules", []))
        jump_items.append(
            f'<span style="padding:4px 10px;border:1px solid {c}44;border-radius:6px;'
            f'font-size:0.7rem;color:{c};font-family:JetBrains Mono,monospace;'
            f'white-space:nowrap;">{cat["category"]} ({cnt})</span>'
        )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;'
        f'margin-bottom:1.2rem;">{"".join(jump_items)}</div>',
        unsafe_allow_html=True,
    )

    # Inline search
    search_query = st.text_input(
        "Filter modules", placeholder="Type to filter by name...",
        key="catalog_search", label_visibility="collapsed",
    )
    sq = search_query.strip().lower() if search_query else ""

    for cat in MODULE_REGISTRY:
        color = cat["color"]
        modules = cat["modules"]
        # Filter if search active
        if sq:
            modules = [m for m in modules if sq in m.get("name", "").lower() or sq in m.get("desc", "").lower()]
            if not modules:
                continue
        count = len(modules)
        c = _cat_ops.get(color, "#00f0ff")

        st.markdown(
            f'<div style="margin:1rem 0 0.5rem;padding:6px 0;border-bottom:1px solid {c}22;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
            f'color:{c};font-weight:600;text-transform:uppercase;letter-spacing:0.1em;">'
            f'{cat["category"]}</span>'
            f'<span style="color:#5a7090;font-size:0.7rem;margin-left:8px;">({count})</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        cols = st.columns(4)
        for idx, mod in enumerate(modules):
            with cols[idx % 4]:
                st.markdown(
                    f'<div class="module-card {color}">'
                    f'<div class="module-icon">{mod["icon"]}</div>'
                    f'<div class="module-name">{mod["name"]}</div>'
                    f'<div class="module-desc">{mod["desc"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"Open", key=f"nav_{mod['id']}", use_container_width=True):
                    st.session_state.current_page = mod["id"]
                    st.rerun()

    if sq and not any(
        any(sq in m.get("name", "").lower() or sq in m.get("desc", "").lower() for m in cat["modules"])
        for cat in MODULE_REGISTRY
    ):
        st.markdown(
            f'<div style="text-align:center;padding:2rem;color:#5a7090;'
            f'font-family:JetBrains Mono,monospace;">'
            f'No modules match "{html_module.escape(search_query)}"</div>',
            unsafe_allow_html=True,
        )

    # Back to Command Center button at end
    st.markdown("---")
    if st.button("\u2190 Back to Command Center", key="catalog_back_cc", use_container_width=True):
        st.session_state.current_page = "command_center"
        st.rerun()


# ═══════════════════════════════════════════
# MODULE PAGE RENDERER
# ═══════════════════════════════════════════

def render_module_page(page_id, prompt, box_threshold, text_threshold, zoom_level, model_type, tile_size, overlap):
    """Render a single module page with back button and breadcrumb."""
    mod = _MODULE_LOOKUP.get(page_id)
    if not mod:
        st.error(f"Unknown module: {page_id}")
        st.session_state.current_page = "command_center"
        st.rerun()
        return

    # Navigation breadcrumb with back buttons (ops-center style)
    bc1, bc2, bc3 = st.columns([1, 1, 4])
    with bc1:
        if st.button("\u2190 Command Center", key="back_to_cc", use_container_width=True):
            st.session_state.current_page = "command_center"
            st.rerun()
    with bc2:
        if st.button("\u2630 Catalog", key="back_to_catalog", use_container_width=True):
            st.session_state.current_page = "catalog"
            st.rerun()
    with bc3:
        _cat_ops = {
            "cyan": "#00f0ff", "violet": "#aa55ff", "emerald": "#00ff88",
            "pink": "#ff66aa", "amber": "#ffaa00", "red": "#ff3344",
            "indigo": "#4488ff", "blue": "#4488ff", "orange": "#ffaa00",
            "teal": "#00f0ff",
        }
        cat_color = _cat_ops.get(mod.get("color", ""), "#00f0ff")
        st.markdown(
            f'<div style="display:flex;align-items:center;height:100%;padding:0.4rem 0;'
            f'font-family:JetBrains Mono,monospace;">'
            f'<span style="color:#5a7090;font-size:0.72rem;">CMD</span>'
            f'<span style="color:#1a2540;margin:0 0.3rem;">\u203a</span>'
            f'<span style="color:{cat_color};font-size:0.72rem;">{mod["category"]}</span>'
            f'<span style="color:#1a2540;margin:0 0.3rem;">\u203a</span>'
            f'<span style="color:#e0e8f0;font-size:0.78rem;font-weight:600;">'
            f'{mod["icon"]} {mod["name"]}</span></div>',
            unsafe_allow_html=True,
        )

    # Render the module
    render_mode = mod["render"]
    if render_mode == "_inline":
        # Inline modules (rendered directly in app.py)
        if page_id == "map_analysis":
            _render_map_analysis(prompt, box_threshold, text_threshold, zoom_level, model_type, tile_size, overlap)
        elif page_id == "image_analysis":
            _render_image_analysis(prompt, box_threshold, text_threshold, model_type)
        elif page_id == "lidar_upload":
            _render_lidar_upload()
        elif page_id == "history":
            _render_history()
        elif page_id == "ai_chat":
            _render_ai_chat()
    elif render_mode == "_lazy_load":
        # Lazy-loaded modules (loaded on-demand from src/)
        render_fn = load_module_render_function(page_id)
        if render_fn:
            render_fn()
    else:
        # Fallback for legacy direct function references
        st.error(f"⚠️ Invalid render mode for {page_id}: {render_mode}")


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    # Load CSS
    try:
        with open("src/styles_professional.css", "r", encoding="utf-8") as f:
            st.markdown(f.read(), unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    # Force sidebar visible with basic content
    st.sidebar.markdown("# \U0001f30d TERRASCOUT AI")
    st.sidebar.markdown("---")

    # ═══════════════════════════════════════════
    # UNIFIED INTELLIGENCE INIT
    # ═══════════════════════════════════════════
    from src.location_context import init_location_context
    from src.data_hub import init_data_hub
    init_location_context()
    init_data_hub()

    # ═══════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = GeoAnalyzer()
    if 'pm' not in st.session_state:
        st.session_state.pm = ProjectManager()

    # Auto-load previous session
    if 'results' not in st.session_state and 'session_loaded' not in st.session_state:
        previous_session = load_session()
        if previous_session:
            if all(os.path.exists(previous_session.get(k, "")) for k in ["image", "mask"] if previous_session.get(k)):
                st.session_state.results = previous_session
                st.session_state.session_loaded = True
            else:
                st.session_state.session_loaded = True

    # ═══════════════════════════════════════════
    # PAGE ROUTER (determine current page first)
    # ═══════════════════════════════════════════
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # Migrate old "home" to "command_center" (new default)
    if st.session_state.current_page == "home":
        st.session_state.current_page = "command_center"

    current = st.session_state.current_page
    analysis_pages = {"map_analysis", "image_analysis"}

    # ═══════════════════════════════════════════
    # SIDEBAR (contextual)
    # ═══════════════════════════════════════════
    if current in analysis_pages:
        # Full analysis sidebar with SAM controls
        prompt, box_threshold, text_threshold, zoom_level, model_type, hf_token, tile_size, overlap = render_sidebar()
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
        # Project save/load only relevant for SAM analysis sessions
        render_project_sidebar(st.session_state.pm)
    else:
        # ---- OPS-CENTER SIDEBAR ----
        try:
            sb = st.sidebar
            sb.markdown("**Navigation**")

            if current != "command_center":
                if sb.button("\U0001f3e0 Command Center", key="sidebar_nav_cc", use_container_width=True):
                    st.session_state.current_page = "command_center"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#00f0ff;font-weight:600;">'
                    '\U0001f3e0 Command Center</div>',
                    unsafe_allow_html=True,
                )

            if current != "fusion_console":
                if sb.button("\U0001f9e0 Fusion Console", key="sidebar_nav_fusion", use_container_width=True):
                    st.session_state.current_page = "fusion_console"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(255,51,68,0.1);border:1px solid rgba(255,51,68,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#ff3344;font-weight:600;">'
                    '\U0001f9e0 Fusion Console</div>',
                    unsafe_allow_html=True,
                )

            if current != "intelligence_dossier":
                if sb.button("\U0001f4dc Intelligence Dossier", key="sidebar_nav_dossier", use_container_width=True):
                    st.session_state.current_page = "intelligence_dossier"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(170,85,255,0.1);border:1px solid rgba(170,85,255,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#aa55ff;font-weight:600;">'
                    '\U0001f4dc Intelligence Dossier</div>',
                    unsafe_allow_html=True,
                )

            if current != "location_comparator":
                if sb.button("\U0001f4cd Location Comparator", key="sidebar_nav_comparator", use_container_width=True):
                    st.session_state.current_page = "location_comparator"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(0,255,136,0.1);border:1px solid rgba(0,255,136,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#00ff88;font-weight:600;">'
                    '\U0001f4cd Location Comparator</div>',
                    unsafe_allow_html=True,
                )

            if current != "temporal_dashboard":
                if sb.button("\u23f3 Temporal Dashboard", key="sidebar_nav_temporal", use_container_width=True):
                    st.session_state.current_page = "temporal_dashboard"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(255,170,0,0.1);border:1px solid rgba(255,170,0,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#ffaa00;font-weight:600;">'
                    '\u23f3 Temporal Dashboard</div>',
                    unsafe_allow_html=True,
                )

            if current != "executive_brief":
                if sb.button("\U0001f4cb Executive Brief", key="sidebar_nav_execbrief", use_container_width=True):
                    st.session_state.current_page = "executive_brief"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(255,51,68,0.1);border:1px solid rgba(255,51,68,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#ff3344;font-weight:600;">'
                    '\U0001f4cb Executive Brief</div>',
                    unsafe_allow_html=True,
                )

            if current != "strategic_planner":
                if sb.button("\U0001f3af Strategic Planner", key="sidebar_nav_stratplan", use_container_width=True):
                    st.session_state.current_page = "strategic_planner"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(170,68,255,0.1);border:1px solid rgba(170,68,255,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#aa44ff;font-weight:600;">'
                    '\U0001f3af Strategic Planner</div>',
                    unsafe_allow_html=True,
                )

            if current != "globe_intelligence":
                if sb.button("\U0001f310 Global Intelligence Globe", key="sidebar_nav_globe", use_container_width=True):
                    st.session_state.current_page = "globe_intelligence"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#ffd700;font-weight:600;">'
                    '\U0001f310 Global Intelligence Globe</div>',
                    unsafe_allow_html=True,
                )

            if current != "catalog":
                if sb.button("\U0001f4da Module Catalog", key="sidebar_nav_catalog", use_container_width=True):
                    st.session_state.current_page = "catalog"
                    st.rerun()
            else:
                sb.markdown(
                    '<div style="background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.25);'
                    'border-radius:6px;padding:0.45rem 0.7rem;margin:2px 0;'
                    'font-size:0.82rem;color:#00f0ff;font-weight:600;">'
                    '\U0001f4da Module Catalog</div>',
                    unsafe_allow_html=True,
                )

            # Current module info (when on a module page)
            if current not in ("command_center", "catalog", "fusion_console", "intelligence_dossier", "location_comparator", "temporal_dashboard", "executive_brief", "strategic_planner", "globe_intelligence"):
                mod_info = _MODULE_LOOKUP.get(current)
                if mod_info:
                    _cat_ops_sb = {
                        "cyan": "#00f0ff", "violet": "#aa55ff", "emerald": "#00ff88",
                        "pink": "#ff66aa", "amber": "#ffaa00", "red": "#ff3344",
                        "indigo": "#4488ff", "blue": "#4488ff", "orange": "#ffaa00",
                        "teal": "#00f0ff",
                    }
                    mc = _cat_ops_sb.get(mod_info.get("color", ""), "#00f0ff")
                    sb.markdown(
                        f'<div style="background:rgba(0,240,255,0.04);border:1px solid {mc}44;'
                        f'border-radius:6px;padding:0.5rem 0.7rem;margin:0.5rem 0;">'
                        f'<div style="font-size:0.6rem;color:#8b97b0;text-transform:uppercase;'
                        f'letter-spacing:0.08em;">ACTIVE MODULE</div>'
                        f'<div style="margin-top:3px;">'
                        f'<span style="font-size:1.1rem;">{mod_info["icon"]}</span> '
                        f'<span style="color:#e0e8f0;font-weight:600;font-size:0.85rem;">'
                        f'{mod_info["name"]}</span></div>'
                        f'<div style="color:{mc};font-size:0.7rem;margin-top:2px;">'
                        f'{mod_info["category"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Module search
            sb.markdown("---")
            sb.caption("SEARCH MODULES")
            mod_search = sb.text_input(
                "Search modules", placeholder="e.g. soil, flood, tourism...",
                key="sidebar_mod_search", label_visibility="collapsed",
            )
            if mod_search and mod_search.strip():
                query = mod_search.strip().lower()
                matches = [
                    m for m in _MODULE_LOOKUP.values()
                    if query in m.get("name", "").lower() or query in m.get("desc", "").lower()
                ]
                if matches:
                    for m in matches[:10]:
                        if sb.button(
                            f"{m.get('icon', '')} {m['name']}",
                            key=f"search_{m['id']}",
                            use_container_width=True,
                        ):
                            st.session_state.current_page = m["id"]
                            st.rerun()
                else:
                    sb.caption("No modules found.")

            # Category quick-nav
            sb.markdown("---")
            sb.caption("CATEGORIES")
            _sb_cat_ops = {
                "cyan": "#00f0ff", "violet": "#aa55ff", "emerald": "#00ff88",
                "pink": "#ff66aa", "amber": "#ffaa00", "red": "#ff3344",
                "indigo": "#4488ff", "blue": "#4488ff", "orange": "#ffaa00",
                "teal": "#00f0ff",
            }
            for cat in MODULE_REGISTRY:
                cat_count = len(cat.get("modules", []))
                cat_c = _sb_cat_ops.get(cat.get("color", ""), "#00f0ff")
                sb.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:3px 0;">'
                    f'<span style="color:#e0e8f0;font-size:0.78rem;">{cat["category"]}</span>'
                    f'<span style="color:{cat_c};font-size:0.72rem;font-weight:700;">{cat_count}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Bookmarks
            sb.markdown("---")
            from src.bookmarks import render_bookmarks_sidebar
            render_bookmarks_sidebar()
        except Exception as e:
            st.sidebar.error(f"Sidebar error: {e}")

        # Defaults (not used on non-analysis pages)
        prompt, box_threshold, text_threshold = "tree", 0.24, 0.24
        zoom_level, model_type, tile_size, overlap = 19, "vit_b", 1000, 96

    # ═══════════════════════════════════════════
    # RENDER PAGE
    # ═══════════════════════════════════════════
    if current == "command_center":
        from src.command_center import render_command_center
        render_command_center()
    elif current == "fusion_console":
        from src.fusion_console import render_fusion_console
        render_fusion_console()
    elif current == "intelligence_dossier":
        from src.intelligence_dossier import render_intelligence_dossier
        render_intelligence_dossier()
    elif current == "location_comparator":
        from src.location_comparator import render_location_comparator
        render_location_comparator()
    elif current == "temporal_dashboard":
        from src.temporal_dashboard import render_temporal_dashboard
        render_temporal_dashboard()
    elif current == "executive_brief":
        from src.executive_brief import render_executive_brief
        render_executive_brief()
    elif current == "strategic_planner":
        from src.strategic_planner import render_strategic_planner
        render_strategic_planner()
    elif current == "globe_intelligence":
        from src.globe_intelligence import render_globe_intelligence
        render_globe_intelligence()
    elif current == "catalog":
        render_catalog_home()
    else:
        # Show context bar on module pages
        from src.context_bar import render_context_bar
        render_context_bar()

        render_module_page(
            current,
            prompt, box_threshold, text_threshold,
            zoom_level, model_type, tile_size, overlap
        )


if __name__ == "__main__":
    main()
