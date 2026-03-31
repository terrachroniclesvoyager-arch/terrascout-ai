# -*- coding: utf-8 -*-
"""
TerraScout AI - Robotics & AI Centers Explorer Module
Provides 10 interactive map modes covering global robotics and AI infrastructure:

    1. AI Research Labs           - Major corporate & academic AI research facilities
    2. Robot Manufacturing Plants - Industrial robot & humanoid robot factories
    3. Autonomous Vehicle Hubs    - Self-driving car & truck development centers
    4. Drone Innovation Centers   - UAV R&D, drone delivery, and testing facilities
    5. Space Robotics Facilities  - Orbital robotics, planetary rovers, and satellite servicing
    6. Medical Robotics Centers   - Surgical robotics, rehabilitation, and medical AI
    7. Industrial Automation Hubs - Smart factory, PLC, and automation R&D centers
    8. AI Startup Ecosystems      - Top cities and incubators for AI startups
    9. Quantum Computing Centers  - Quantum hardware labs and research institutes
   10. Robot Museums & Exhibitions - Museums, expos, and public showcases of robotics

All data is hardcoded; no API keys required.
"""

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DARK_TILE = "CartoDB dark_matter"
MAP_HEIGHT = 500
DEFAULT_ZOOM = 2
DEFAULT_CENTER = [20, 0]

POPUP_CSS = """
<style>
.robot-popup {{
    font-family: 'Segoe UI', sans-serif;
    min-width: 220px;
    color: #e8ecf4;
    background: #111827;
    border: 1px solid #2a3550;
    border-radius: 8px;
    padding: 10px;
}}
.robot-popup h4 {{
    margin: 0 0 6px 0;
    color: #06b6d4;
    font-size: 14px;
}}
.robot-popup .field {{
    font-size: 12px;
    margin: 2px 0;
    color: #8b97b0;
}}
.robot-popup .field b {{
    color: #e8ecf4;
}}
</style>
"""

# ---------------------------------------------------------------------------
# MODE 1: AI Research Labs
# ---------------------------------------------------------------------------
AI_RESEARCH_LABS = [
    {"name": "DeepMind", "city": "London", "country": "UK", "lat": 51.5332, "lon": -0.1255,
     "parent": "Alphabet / Google", "focus": "AGI, AlphaFold, Reinforcement Learning",
     "founded": 2010, "staff_est": 2500, "notable": "AlphaGo, AlphaFold, Gemini"},
    {"name": "OpenAI", "city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194,
     "parent": "OpenAI Inc.", "focus": "Large Language Models, DALL-E, Safety",
     "founded": 2015, "staff_est": 1500, "notable": "GPT-4, ChatGPT, DALL-E 3"},
    {"name": "Meta FAIR", "city": "Menlo Park", "country": "USA", "lat": 37.4530, "lon": -122.1817,
     "parent": "Meta Platforms", "focus": "Computer Vision, NLP, Open Source AI",
     "founded": 2013, "staff_est": 800, "notable": "LLaMA, Segment Anything, DINO"},
    {"name": "Google Brain / Google DeepMind", "city": "Mountain View", "country": "USA", "lat": 37.4220, "lon": -122.0841,
     "parent": "Alphabet / Google", "focus": "Transformers, TPU, Multimodal AI",
     "founded": 2011, "staff_est": 1800, "notable": "Transformer paper, BERT, Gemini"},
    {"name": "Microsoft Research AI", "city": "Redmond", "country": "USA", "lat": 47.6740, "lon": -122.1215,
     "parent": "Microsoft", "focus": "NLP, AI for Science, Responsible AI",
     "founded": 1991, "staff_est": 1200, "notable": "Turing-NLG, Florence, Copilot"},
    {"name": "IBM Research AI", "city": "Yorktown Heights", "country": "USA", "lat": 41.2137, "lon": -73.8032,
     "parent": "IBM", "focus": "Watson, Hybrid AI, Trustworthy AI",
     "founded": 1945, "staff_est": 3000, "notable": "Watson, Deep Blue, IBM Granite"},
    {"name": "Anthropic", "city": "San Francisco", "country": "USA", "lat": 37.7850, "lon": -122.4000,
     "parent": "Anthropic", "focus": "AI Safety, Constitutional AI, Large Models",
     "founded": 2021, "staff_est": 800, "notable": "Claude, Constitutional AI"},
    {"name": "Baidu Research", "city": "Beijing", "country": "China", "lat": 40.0565, "lon": 116.3079,
     "parent": "Baidu", "focus": "NLP, Autonomous Driving, PaddlePaddle",
     "founded": 2014, "staff_est": 1000, "notable": "ERNIE, Apollo, PaddlePaddle"},
    {"name": "Tencent AI Lab", "city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579,
     "parent": "Tencent", "focus": "NLP, Computer Vision, Game AI",
     "founded": 2016, "staff_est": 600, "notable": "Hunyuan, GameAI, Medical AI"},
    {"name": "Alibaba DAMO Academy", "city": "Hangzhou", "country": "China", "lat": 30.2741, "lon": 120.1551,
     "parent": "Alibaba Group", "focus": "NLP, Vision, AI Chips",
     "founded": 2017, "staff_est": 700, "notable": "Qwen, M6, Hanguang 800"},
    {"name": "Samsung AI Center", "city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780,
     "parent": "Samsung Electronics", "focus": "On-device AI, Computer Vision, Robotics",
     "founded": 2017, "staff_est": 500, "notable": "Bixby, Gauss, On-device LLM"},
    {"name": "RIKEN Center for AIP", "city": "Tokyo", "country": "Japan", "lat": 35.7107, "lon": 139.7349,
     "parent": "RIKEN", "focus": "Machine Learning Theory, Robotics AI",
     "founded": 2016, "staff_est": 300, "notable": "Fugaku AI, AIP challenge"},
    {"name": "Mila - Quebec AI Institute", "city": "Montreal", "country": "Canada", "lat": 45.5280, "lon": -73.5768,
     "parent": "Academic Consortium", "focus": "Deep Learning, RL, Generative Models",
     "founded": 1993, "staff_est": 1000, "notable": "Yoshua Bengio, GFlowNets"},
    {"name": "Vector Institute", "city": "Toronto", "country": "Canada", "lat": 43.6605, "lon": -79.3960,
     "parent": "Academic/Industry", "focus": "Deep Learning, Healthcare AI",
     "founded": 2017, "staff_est": 600, "notable": "Geoffrey Hinton, Health AI"},
    {"name": "Alan Turing Institute", "city": "London", "country": "UK", "lat": 51.5300, "lon": -0.1278,
     "parent": "UK Research Council", "focus": "Data Science, AI Ethics, Cybersecurity",
     "founded": 2015, "staff_est": 500, "notable": "National AI strategy, Turing Fellows"},
    {"name": "DFKI", "city": "Kaiserslautern", "country": "Germany", "lat": 49.4274, "lon": 7.7536,
     "parent": "German Federal/State", "focus": "NLP, Robotics, Smart Data",
     "founded": 1988, "staff_est": 1400, "notable": "Largest nonprofit AI lab in world"},
    {"name": "Inria", "city": "Paris", "country": "France", "lat": 48.8316, "lon": 2.3050,
     "parent": "French Government", "focus": "Machine Learning, Computer Vision, Robotics",
     "founded": 1967, "staff_est": 3500, "notable": "Scikit-learn contributors, OATML"},
    {"name": "KAIST AI", "city": "Daejeon", "country": "South Korea", "lat": 36.3741, "lon": 127.3654,
     "parent": "KAIST", "focus": "Robotics AI, NLP, Vision",
     "founded": 2019, "staff_est": 250, "notable": "KoGPT, Autonomous systems"},
    {"name": "Tsinghua KEG Lab", "city": "Beijing", "country": "China", "lat": 39.9994, "lon": 116.3267,
     "parent": "Tsinghua University", "focus": "Knowledge Graphs, LLMs, AI4Science",
     "founded": 1996, "staff_est": 200, "notable": "GLM, ChatGLM, AMiner"},
    {"name": "Stanford HAI", "city": "Stanford", "country": "USA", "lat": 37.4275, "lon": -122.1697,
     "parent": "Stanford University", "focus": "Human-Centered AI, Policy, Ethics",
     "founded": 2019, "staff_est": 200, "notable": "AI Index Report, Foundation Models"},
    {"name": "MIT CSAIL", "city": "Cambridge", "country": "USA", "lat": 42.3616, "lon": -71.0906,
     "parent": "MIT", "focus": "Robotics, NLP, Systems, Vision",
     "founded": 2003, "staff_est": 800, "notable": "Largest CS lab at MIT"},
    {"name": "Berkeley AI Research (BAIR)", "city": "Berkeley", "country": "USA", "lat": 37.8753, "lon": -122.2577,
     "parent": "UC Berkeley", "focus": "RL, Robot Learning, NLP, Vision",
     "founded": 2014, "staff_est": 300, "notable": "RLHF foundations, Pieter Abbeel"},
    {"name": "CMU Robotics Institute", "city": "Pittsburgh", "country": "USA", "lat": 40.4435, "lon": -79.9456,
     "parent": "Carnegie Mellon University", "focus": "Robotics, Autonomous Systems, ML",
     "founded": 1979, "staff_est": 600, "notable": "First robotics PhD, DARPA challenges"},
    {"name": "ETH Zurich AI Center", "city": "Zurich", "country": "Switzerland", "lat": 47.3763, "lon": 8.5483,
     "parent": "ETH Zurich", "focus": "ML Theory, Computer Vision, Robotics",
     "founded": 2020, "staff_est": 300, "notable": "Robust ML, 3D Vision"},
    {"name": "NVIDIA Research", "city": "Santa Clara", "country": "USA", "lat": 37.3707, "lon": -121.9577,
     "parent": "NVIDIA", "focus": "GPU AI, Autonomous Vehicles, Graphics AI",
     "founded": 2006, "staff_est": 700, "notable": "CUDA, cuDNN, Omniverse"},
    {"name": "xAI", "city": "San Francisco", "country": "USA", "lat": 37.7900, "lon": -122.3920,
     "parent": "xAI Corp", "focus": "Large Language Models, Reasoning",
     "founded": 2023, "staff_est": 300, "notable": "Grok, Colossus cluster"},
    {"name": "Mistral AI", "city": "Paris", "country": "France", "lat": 48.8690, "lon": 2.3323,
     "parent": "Mistral AI", "focus": "Open-weight LLMs, Efficient Inference",
     "founded": 2023, "staff_est": 200, "notable": "Mistral 7B, Mixtral"},
    {"name": "Stability AI", "city": "London", "country": "UK", "lat": 51.5145, "lon": -0.0825,
     "parent": "Stability AI", "focus": "Open-source Generative AI, Diffusion Models",
     "founded": 2020, "staff_est": 200, "notable": "Stable Diffusion"},
]

# ---------------------------------------------------------------------------
# MODE 2: Robot Manufacturing Plants
# ---------------------------------------------------------------------------
ROBOT_MANUFACTURING = [
    {"name": "FANUC Headquarters & Factory", "city": "Oshino", "country": "Japan", "lat": 35.4622, "lon": 138.8180,
     "company": "FANUC", "type": "Industrial Robots", "robots_year": 750000,
     "products": "CNC, Industrial Arms, Cobots", "founded": 1972},
    {"name": "ABB Robotics", "city": "Vasteras", "country": "Sweden", "lat": 59.6099, "lon": 16.5448,
     "company": "ABB", "type": "Industrial Robots", "robots_year": 500000,
     "products": "IRB series, YuMi Cobots", "founded": 1988},
    {"name": "KUKA Robotics HQ", "city": "Augsburg", "country": "Germany", "lat": 48.3925, "lon": 10.8987,
     "company": "KUKA (Midea)", "type": "Industrial Robots", "robots_year": 400000,
     "products": "KR series, LBR iiwa Cobot", "founded": 1898},
    {"name": "Yaskawa Electric (Motoman)", "city": "Kitakyushu", "country": "Japan", "lat": 33.8834, "lon": 130.8751,
     "company": "Yaskawa", "type": "Industrial Robots", "robots_year": 500000,
     "products": "Motoman GP, HC Cobots, Drives", "founded": 1915},
    {"name": "Universal Robots", "city": "Odense", "country": "Denmark", "lat": 55.3954, "lon": 10.3886,
     "company": "Universal Robots (Teradyne)", "type": "Collaborative Robots", "robots_year": 75000,
     "products": "UR3e, UR5e, UR10e, UR16e, UR20, UR30", "founded": 2005},
    {"name": "Boston Dynamics HQ", "city": "Waltham", "country": "USA", "lat": 42.3765, "lon": -71.2356,
     "company": "Boston Dynamics (Hyundai)", "type": "Mobile Robots", "robots_year": 5000,
     "products": "Spot, Stretch, Atlas", "founded": 1992},
    {"name": "Tesla Bot (Optimus) Gigafactory", "city": "Austin", "country": "USA", "lat": 30.2214, "lon": -97.6166,
     "company": "Tesla", "type": "Humanoid Robots", "robots_year": 1000,
     "products": "Optimus Gen 2, Factory Bots", "founded": 2021},
    {"name": "Figure AI HQ", "city": "Sunnyvale", "country": "USA", "lat": 37.3688, "lon": -122.0363,
     "company": "Figure AI", "type": "Humanoid Robots", "robots_year": 500,
     "products": "Figure 01, Figure 02", "founded": 2022},
    {"name": "Agility Robotics Factory", "city": "Salem", "country": "USA", "lat": 44.9429, "lon": -123.0351,
     "company": "Agility Robotics", "type": "Humanoid/Bipedal", "robots_year": 10000,
     "products": "Digit", "founded": 2015},
    {"name": "SoftBank Robotics", "city": "Tokyo", "country": "Japan", "lat": 35.6600, "lon": 139.7280,
     "company": "SoftBank", "type": "Service Robots", "robots_year": 30000,
     "products": "Pepper, NAO, Whiz", "founded": 2014},
    {"name": "DJI Headquarters", "city": "Shenzhen", "country": "China", "lat": 22.5745, "lon": 113.9745,
     "company": "DJI", "type": "Drones / Robots", "robots_year": 5000000,
     "products": "Phantom, Mavic, RoboMaster", "founded": 2006},
    {"name": "Kawasaki Heavy Industries Robotics", "city": "Akashi", "country": "Japan", "lat": 34.6434, "lon": 134.9972,
     "company": "Kawasaki", "type": "Industrial Robots", "robots_year": 200000,
     "products": "RS, CX, BX series", "founded": 1969},
    {"name": "Denso Wave (QR Code & Robots)", "city": "Agui", "country": "Japan", "lat": 34.9374, "lon": 136.8924,
     "company": "Denso (Toyota Group)", "type": "Small Industrial Robots", "robots_year": 150000,
     "products": "VS series, COBOTTA", "founded": 1976},
    {"name": "Epson Robots", "city": "Suwa", "country": "Japan", "lat": 36.0461, "lon": 138.1093,
     "company": "Seiko Epson", "type": "SCARA Robots", "robots_year": 120000,
     "products": "T-series SCARA, C-series 6-axis", "founded": 1984},
    {"name": "Staubli Robotics", "city": "Faverges", "country": "France", "lat": 45.7430, "lon": 6.2888,
     "company": "Staubli", "type": "Industrial Robots", "robots_year": 50000,
     "products": "TX2, TS2 SCARA", "founded": 1982},
    {"name": "Comau Robotics", "city": "Turin", "country": "Italy", "lat": 45.0352, "lon": 7.0731,
     "company": "Comau (Stellantis)", "type": "Industrial Robots", "robots_year": 60000,
     "products": "Racer, Aura, MATE exoskeleton", "founded": 1973},
    {"name": "Nachi-Fujikoshi Robotics", "city": "Toyama", "country": "Japan", "lat": 36.6831, "lon": 137.2112,
     "company": "Nachi-Fujikoshi", "type": "Industrial Robots", "robots_year": 80000,
     "products": "MZ series, SRA welding", "founded": 1928},
    {"name": "Doosan Robotics", "city": "Suwon", "country": "South Korea", "lat": 37.2636, "lon": 127.0286,
     "company": "Doosan Group", "type": "Collaborative Robots", "robots_year": 10000,
     "products": "M, H, A series cobots", "founded": 2015},
    {"name": "Techman Robot (TM Robot)", "city": "Taoyuan", "country": "Taiwan", "lat": 24.9897, "lon": 121.3118,
     "company": "Quanta/Techman", "type": "Collaborative Robots", "robots_year": 20000,
     "products": "TM5, TM12, TM14 with built-in vision", "founded": 2016},
    {"name": "SIASUN Robot", "city": "Shenyang", "country": "China", "lat": 41.8057, "lon": 123.4315,
     "company": "SIASUN", "type": "Industrial/Service Robots", "robots_year": 100000,
     "products": "SR, GCR, mobile platforms", "founded": 2000},
    {"name": "Estun Automation", "city": "Nanjing", "country": "China", "lat": 32.0603, "lon": 118.7969,
     "company": "Estun", "type": "Industrial Robots", "robots_year": 50000,
     "products": "ER series, Cloos welding", "founded": 1993},
    {"name": "Omron Robotics", "city": "Kyoto", "country": "Japan", "lat": 34.9937, "lon": 135.7519,
     "company": "Omron", "type": "Mobile/Collaborative Robots", "robots_year": 40000,
     "products": "LD/MD mobile, TM cobots (collab)", "founded": 1933},
    {"name": "iRobot HQ", "city": "Bedford", "country": "USA", "lat": 42.4906, "lon": -71.2760,
     "company": "iRobot", "type": "Consumer Robots", "robots_year": 10000000,
     "products": "Roomba, Braava", "founded": 1990},
    {"name": "Unitree Robotics", "city": "Hangzhou", "country": "China", "lat": 30.2590, "lon": 120.1300,
     "company": "Unitree", "type": "Quadruped/Humanoid", "robots_year": 20000,
     "products": "Go2, B2, H1, G1 humanoid", "founded": 2016},
    {"name": "1X Technologies (formerly Halodi)", "city": "Moss", "country": "Norway", "lat": 59.4370, "lon": 10.6590,
     "company": "1X Technologies", "type": "Humanoid Robots", "robots_year": 500,
     "products": "EVE, NEO humanoid", "founded": 2014},
]

# ---------------------------------------------------------------------------
# MODE 3: Autonomous Vehicle Hubs
# ---------------------------------------------------------------------------
AUTONOMOUS_VEHICLE_HUBS = [
    {"name": "Waymo HQ", "city": "Mountain View", "country": "USA", "lat": 37.4220, "lon": -122.0841,
     "company": "Waymo (Alphabet)", "focus": "Robotaxi, Trucking", "level": "L4",
     "fleet_size": 700, "test_miles_m": 20, "status": "Commercial"},
    {"name": "Cruise HQ", "city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194,
     "company": "Cruise (GM)", "focus": "Robotaxi", "level": "L4",
     "fleet_size": 300, "test_miles_m": 5, "status": "Paused/Restructuring"},
    {"name": "Tesla Autopilot HQ", "city": "Palo Alto", "country": "USA", "lat": 37.3947, "lon": -122.1503,
     "company": "Tesla", "focus": "FSD, Robotaxi (Cybercab)", "level": "L2+",
     "fleet_size": 5000000, "test_miles_m": 1000, "status": "Active development"},
    {"name": "Aurora Innovation", "city": "Pittsburgh", "country": "USA", "lat": 40.4406, "lon": -79.9959,
     "company": "Aurora", "focus": "Autonomous Trucking", "level": "L4",
     "fleet_size": 100, "test_miles_m": 4, "status": "Pilot commercial"},
    {"name": "Zoox (Amazon)", "city": "Foster City", "country": "USA", "lat": 37.5585, "lon": -122.2711,
     "company": "Zoox (Amazon)", "focus": "Purpose-built Robotaxi", "level": "L4",
     "fleet_size": 50, "test_miles_m": 2, "status": "Testing"},
    {"name": "Motional (Aptiv + Hyundai)", "city": "Boston", "country": "USA", "lat": 42.3601, "lon": -71.0589,
     "company": "Motional", "focus": "Robotaxi", "level": "L4",
     "fleet_size": 100, "test_miles_m": 3, "status": "Pilot Las Vegas"},
    {"name": "Nuro", "city": "Mountain View", "country": "USA", "lat": 37.4149, "lon": -122.0782,
     "company": "Nuro", "focus": "Autonomous Delivery", "level": "L4",
     "fleet_size": 50, "test_miles_m": 1, "status": "Active"},
    {"name": "Baidu Apollo Park", "city": "Beijing", "country": "China", "lat": 40.0515, "lon": 116.2830,
     "company": "Baidu", "focus": "Robotaxi (Apollo Go)", "level": "L4",
     "fleet_size": 500, "test_miles_m": 10, "status": "Commercial"},
    {"name": "Pony.ai HQ", "city": "Guangzhou", "country": "China", "lat": 23.1291, "lon": 113.2644,
     "company": "Pony.ai", "focus": "Robotaxi, Robotruck", "level": "L4",
     "fleet_size": 250, "test_miles_m": 6, "status": "Commercial pilot"},
    {"name": "AutoX (Shenzhen)", "city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579,
     "company": "AutoX", "focus": "Fully driverless Robotaxi", "level": "L4",
     "fleet_size": 100, "test_miles_m": 3, "status": "Testing"},
    {"name": "WeRide", "city": "Guangzhou", "country": "China", "lat": 23.1300, "lon": 113.2590,
     "company": "WeRide", "focus": "Robotaxi, Robobus, Robosweeper", "level": "L4",
     "fleet_size": 200, "test_miles_m": 4, "status": "Commercial pilot"},
    {"name": "Mobileye HQ", "city": "Jerusalem", "country": "Israel", "lat": 31.7530, "lon": 35.2106,
     "company": "Mobileye (Intel)", "focus": "ADAS, AV Chips, Robotaxi", "level": "L2-L4",
     "fleet_size": 80, "test_miles_m": 2, "status": "Active"},
    {"name": "Yandex Self-Driving", "city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173,
     "company": "Yandex (now Avride)", "focus": "Robotaxi, Delivery Robots", "level": "L4",
     "fleet_size": 170, "test_miles_m": 3, "status": "Active"},
    {"name": "Navya", "city": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357,
     "company": "Navya", "focus": "Autonomous Shuttles", "level": "L4",
     "fleet_size": 200, "test_miles_m": 1, "status": "Active"},
    {"name": "EasyMile", "city": "Toulouse", "country": "France", "lat": 43.6047, "lon": 1.4442,
     "company": "EasyMile", "focus": "Autonomous Shuttles, Tractors", "level": "L4",
     "fleet_size": 150, "test_miles_m": 1, "status": "Active"},
    {"name": "Oxbotica", "city": "Oxford", "country": "UK", "lat": 51.7520, "lon": -1.2577,
     "company": "Oxbotica", "focus": "Universal Autonomy Software", "level": "L4",
     "fleet_size": 30, "test_miles_m": 1, "status": "Active"},
    {"name": "Kodiak Robotics", "city": "Mountain View", "country": "USA", "lat": 37.4050, "lon": -122.0780,
     "company": "Kodiak", "focus": "Autonomous Trucking", "level": "L4",
     "fleet_size": 50, "test_miles_m": 2, "status": "Active"},
    {"name": "TuSimple", "city": "San Diego", "country": "USA", "lat": 32.7157, "lon": -117.1611,
     "company": "TuSimple", "focus": "Autonomous Trucking", "level": "L4",
     "fleet_size": 70, "test_miles_m": 3, "status": "Restructuring"},
    {"name": "Gatik", "city": "Mountain View", "country": "USA", "lat": 37.4000, "lon": -122.0800,
     "company": "Gatik", "focus": "Middle-mile Autonomous Delivery", "level": "L4",
     "fleet_size": 40, "test_miles_m": 1, "status": "Commercial"},
    {"name": "Torc Robotics (Daimler)", "city": "Blacksburg", "country": "USA", "lat": 37.2296, "lon": -80.4139,
     "company": "Torc (Daimler Truck)", "focus": "Autonomous Trucking", "level": "L4",
     "fleet_size": 50, "test_miles_m": 2, "status": "Active"},
    {"name": "May Mobility", "city": "Ann Arbor", "country": "USA", "lat": 42.2808, "lon": -83.7430,
     "company": "May Mobility", "focus": "Autonomous Shuttles", "level": "L4",
     "fleet_size": 30, "test_miles_m": 1, "status": "Active"},
    {"name": "Momenta", "city": "Beijing", "country": "China", "lat": 39.9842, "lon": 116.3067,
     "company": "Momenta", "focus": "Autonomous Driving Solutions", "level": "L3-L4",
     "fleet_size": 100, "test_miles_m": 2, "status": "Active"},
    {"name": "Plus.ai", "city": "Cupertino", "country": "USA", "lat": 37.3230, "lon": -122.0322,
     "company": "Plus", "focus": "Autonomous Trucking", "level": "L4",
     "fleet_size": 60, "test_miles_m": 1, "status": "Active"},
    {"name": "Einride", "city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686,
     "company": "Einride", "focus": "Electric Autonomous Freight", "level": "L4",
     "fleet_size": 40, "test_miles_m": 1, "status": "Active"},
    {"name": "Woven by Toyota", "city": "Tokyo", "country": "Japan", "lat": 35.6817, "lon": 139.7670,
     "company": "Toyota", "focus": "Woven City, Autonomous Driving", "level": "L3-L4",
     "fleet_size": 100, "test_miles_m": 5, "status": "Active"},
]

# ---------------------------------------------------------------------------
# MODE 4: Drone Innovation Centers
# ---------------------------------------------------------------------------
DRONE_INNOVATION_CENTERS = [
    {"name": "DJI Innovation HQ", "city": "Shenzhen", "country": "China", "lat": 22.5745, "lon": 113.9745,
     "company": "DJI", "focus": "Consumer & Enterprise Drones", "employees": 14000, "founded": 2006,
     "products": "Mavic, Phantom, Matrice, Agras"},
    {"name": "Skydio HQ", "city": "San Mateo", "country": "USA", "lat": 37.5630, "lon": -122.3255,
     "company": "Skydio", "focus": "AI-powered Autonomous Drones", "employees": 700, "founded": 2014,
     "products": "Skydio X10, X2E, S2+"},
    {"name": "Wing (Alphabet)", "city": "Palo Alto", "country": "USA", "lat": 37.4419, "lon": -122.1430,
     "company": "Wing (Alphabet)", "focus": "Drone Delivery", "employees": 500, "founded": 2012,
     "products": "Wing delivery drones"},
    {"name": "Amazon Prime Air", "city": "Seattle", "country": "USA", "lat": 47.6062, "lon": -122.3321,
     "company": "Amazon", "focus": "Drone Delivery", "employees": 800, "founded": 2013,
     "products": "MK30 delivery drone"},
    {"name": "Zipline HQ", "city": "South San Francisco", "country": "USA", "lat": 37.6547, "lon": -122.4077,
     "company": "Zipline", "focus": "Medical & Logistics Delivery", "employees": 2000, "founded": 2014,
     "products": "Zip P1, Zip P2, Platform 2"},
    {"name": "Joby Aviation", "city": "Santa Cruz", "country": "USA", "lat": 36.9741, "lon": -122.0308,
     "company": "Joby Aviation", "focus": "eVTOL Air Taxi", "employees": 2000, "founded": 2009,
     "products": "Joby S4 eVTOL"},
    {"name": "Lilium", "city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820,
     "company": "Lilium", "focus": "eVTOL Jet", "employees": 800, "founded": 2015,
     "products": "Lilium Jet"},
    {"name": "Volocopter", "city": "Bruchsal", "country": "Germany", "lat": 49.1244, "lon": 8.5980,
     "company": "Volocopter", "focus": "Urban Air Mobility", "employees": 600, "founded": 2011,
     "products": "VoloCity, VoloRegion"},
    {"name": "EHang", "city": "Guangzhou", "country": "China", "lat": 23.1291, "lon": 113.2644,
     "company": "EHang", "focus": "Autonomous Aerial Vehicles", "employees": 500, "founded": 2014,
     "products": "EH216-S"},
    {"name": "Archer Aviation", "city": "San Jose", "country": "USA", "lat": 37.3382, "lon": -121.8863,
     "company": "Archer", "focus": "eVTOL Air Taxi", "employees": 1000, "founded": 2018,
     "products": "Midnight eVTOL"},
    {"name": "Parrot HQ", "city": "Paris", "country": "France", "lat": 48.8620, "lon": 2.3470,
     "company": "Parrot", "focus": "Micro-drones, Defense", "employees": 500, "founded": 1994,
     "products": "ANAFI USA, ANAFI Ai"},
    {"name": "Autel Robotics", "city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579,
     "company": "Autel", "focus": "Enterprise & Consumer Drones", "employees": 2000, "founded": 2014,
     "products": "EVO II, Dragonfish, Alpha"},
    {"name": "AeroVironment", "city": "Arlington", "country": "USA", "lat": 38.8799, "lon": -77.1068,
     "company": "AeroVironment", "focus": "Military Small UAS", "employees": 3000, "founded": 1971,
     "products": "Switchblade, Puma, Raven"},
    {"name": "Insitu (Boeing)", "city": "Bingen", "country": "USA", "lat": 45.7116, "lon": -121.4688,
     "company": "Insitu (Boeing)", "focus": "Military ISR Drones", "employees": 900, "founded": 1994,
     "products": "ScanEagle, Integrator"},
    {"name": "General Atomics ASI", "city": "San Diego", "country": "USA", "lat": 32.8801, "lon": -117.2340,
     "company": "General Atomics", "focus": "MALE UAS, Military", "employees": 12000, "founded": 1992,
     "products": "MQ-9 Reaper, MQ-1C Gray Eagle"},
    {"name": "Turkish Aerospace (Baykar)", "city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784,
     "company": "Baykar", "focus": "Military UCAV", "employees": 4000, "founded": 2000,
     "products": "Bayraktar TB2, Akinci, Kizilelma"},
    {"name": "IAI Malat (Heron)", "city": "Haifa", "country": "Israel", "lat": 32.7940, "lon": 34.9896,
     "company": "Israel Aerospace Industries", "focus": "Military & Tactical UAS", "employees": 15000, "founded": 1953,
     "products": "Heron, Harop, Mini Harpy"},
    {"name": "Elbit Systems UAS", "city": "Haifa", "country": "Israel", "lat": 32.8050, "lon": 34.9860,
     "company": "Elbit Systems", "focus": "Military & Border UAS", "employees": 18000, "founded": 1966,
     "products": "Hermes 450/900, Skylark"},
    {"name": "Airbus Zephyr (Solar HAPS)", "city": "Farnborough", "country": "UK", "lat": 51.2750, "lon": -0.7590,
     "company": "Airbus", "focus": "High-Altitude Pseudo-Satellite", "employees": 130000, "founded": 2003,
     "products": "Zephyr S/T"},
    {"name": "Vertical Aerospace", "city": "Bristol", "country": "UK", "lat": 51.4545, "lon": -2.5879,
     "company": "Vertical Aerospace", "focus": "eVTOL", "employees": 400, "founded": 2016,
     "products": "VX4"},
    {"name": "Wisk Aero (Boeing)", "city": "Mountain View", "country": "USA", "lat": 37.3994, "lon": -122.0584,
     "company": "Wisk (Boeing)", "focus": "Autonomous Air Taxi", "employees": 500, "founded": 2019,
     "products": "Wisk Generation 6"},
    {"name": "Beta Technologies", "city": "Burlington", "country": "USA", "lat": 44.4759, "lon": -73.2121,
     "company": "Beta Technologies", "focus": "eVTOL / eCTOL", "employees": 700, "founded": 2017,
     "products": "ALIA"},
    {"name": "Matternet", "city": "Mountain View", "country": "USA", "lat": 37.3960, "lon": -122.0790,
     "company": "Matternet", "focus": "Medical Drone Delivery", "employees": 100, "founded": 2011,
     "products": "Matternet M2"},
    {"name": "Flytrex", "city": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lon": 34.7818,
     "company": "Flytrex", "focus": "Food Drone Delivery", "employees": 100, "founded": 2013,
     "products": "Flytrex drone delivery"},
    {"name": "Quantum Systems", "city": "Gilching", "country": "Germany", "lat": 48.1073, "lon": 11.2995,
     "company": "Quantum Systems", "focus": "Hybrid eVTOL Survey Drones", "employees": 200, "founded": 2015,
     "products": "Trinity F90+, Vector"},
]

# ---------------------------------------------------------------------------
# MODE 5: Space Robotics Facilities
# ---------------------------------------------------------------------------
SPACE_ROBOTICS = [
    {"name": "NASA JPL - Mars Rover Lab", "city": "Pasadena", "country": "USA", "lat": 34.2013, "lon": -118.1714,
     "agency": "NASA/JPL", "focus": "Planetary Rovers & Landers",
     "notable": "Curiosity, Perseverance, Ingenuity", "founded": 1936},
    {"name": "NASA Goddard - Satellite Servicing", "city": "Greenbelt", "country": "USA", "lat": 38.9911, "lon": -76.8527,
     "agency": "NASA GSFC", "focus": "On-Orbit Servicing Robotics",
     "notable": "OSAM-1, Restore-L, Hubble servicing", "founded": 1959},
    {"name": "NASA JSC - Robonaut Lab", "city": "Houston", "country": "USA", "lat": 29.5593, "lon": -95.0900,
     "agency": "NASA JSC", "focus": "Humanoid Space Robots",
     "notable": "Robonaut 2, ATHLETE rover", "founded": 1961},
    {"name": "MDA Space (Canadarm)", "city": "Brampton", "country": "Canada", "lat": 43.7315, "lon": -79.7624,
     "agency": "MDA / CSA", "focus": "Space Manipulator Arms",
     "notable": "Canadarm, Canadarm2, Dextre", "founded": 1969},
    {"name": "ESA ESTEC - Robotics Lab", "city": "Noordwijk", "country": "Netherlands", "lat": 52.2186, "lon": 4.4203,
     "agency": "ESA", "focus": "Planetary Robotics R&D",
     "notable": "ExoMars rover, ESA telerobotics", "founded": 1968},
    {"name": "DLR Institute of Robotics", "city": "Oberpfaffenhofen", "country": "Germany", "lat": 48.0845, "lon": 11.2795,
     "agency": "DLR", "focus": "Space Telemanipulation, CIMON",
     "notable": "ROKVISS, CIMON-2, SpaceJustin", "founded": 1963},
    {"name": "JAXA Sagamihara - Hayabusa", "city": "Sagamihara", "country": "Japan", "lat": 35.5572, "lon": 139.3959,
     "agency": "JAXA/ISAS", "focus": "Sample Return Robotics",
     "notable": "Hayabusa2, MINERVA-II rovers", "founded": 1964},
    {"name": "CNSA Aerospace City", "city": "Beijing", "country": "China", "lat": 39.9100, "lon": 116.4074,
     "agency": "CNSA/CAST", "focus": "Lunar & Mars Rovers",
     "notable": "Zhurong, Yutu-2, Chang'e landers", "founded": 1968},
    {"name": "ISRO URSC", "city": "Bangalore", "country": "India", "lat": 12.9340, "lon": 77.5136,
     "agency": "ISRO", "focus": "Lunar Lander Robotics",
     "notable": "Chandrayaan-3 Pragyan rover", "founded": 1972},
    {"name": "Maxar (SSL) Robotics", "city": "Palo Alto", "country": "USA", "lat": 37.3975, "lon": -122.1468,
     "agency": "Maxar", "focus": "Robotic Arms for Space",
     "notable": "OSAM-1 arm, RSGS program", "founded": 1957},
    {"name": "Northrop Grumman MEV", "city": "Dulles", "country": "USA", "lat": 38.9531, "lon": -77.4483,
     "agency": "Northrop Grumman", "focus": "Mission Extension Vehicles",
     "notable": "MEV-1, MEV-2 satellite life extension", "founded": 1939},
    {"name": "Astroscale", "city": "Tokyo", "country": "Japan", "lat": 35.6580, "lon": 139.7016,
     "agency": "Astroscale", "focus": "Space Debris Removal Robotics",
     "notable": "ELSA-d, ADRAS-J", "founded": 2013},
    {"name": "ClearSpace", "city": "Lausanne", "country": "Switzerland", "lat": 46.5197, "lon": 6.6323,
     "agency": "ClearSpace (ESA partner)", "focus": "Active Debris Removal",
     "notable": "ClearSpace-1 mission", "founded": 2018},
    {"name": "Gitai Japan", "city": "Tokyo", "country": "Japan", "lat": 35.6620, "lon": 139.7050,
     "agency": "GITAI", "focus": "In-Space Robotic Labor",
     "notable": "S2 autonomous robot arm on ISS", "founded": 2016},
    {"name": "Motiv Space Systems", "city": "Pasadena", "country": "USA", "lat": 34.1478, "lon": -118.1445,
     "agency": "Motiv Space", "focus": "Space Robotic Arms",
     "notable": "xLink robotic arm, Mars 2020 arm", "founded": 2014},
    {"name": "Roscosmos TsNIIMash", "city": "Korolev", "country": "Russia", "lat": 55.9193, "lon": 37.8542,
     "agency": "Roscosmos", "focus": "Space Station Robotics",
     "notable": "ERA arm (ISS), Lunokhod heritage", "founded": 1946},
    {"name": "CNES Toulouse - Space Robotics", "city": "Toulouse", "country": "France", "lat": 43.6047, "lon": 1.4442,
     "agency": "CNES", "focus": "Autonomous Navigation in Space",
     "notable": "ATV rendezvous, Mars sample return", "founded": 1961},
    {"name": "Airbus Defence & Space - Mars Rover", "city": "Stevenage", "country": "UK", "lat": 51.9050, "lon": -0.1785,
     "agency": "Airbus", "focus": "Planetary Rover Assembly",
     "notable": "ExoMars Rosalind Franklin rover", "founded": 1963},
    {"name": "Intuitive Machines", "city": "Houston", "country": "USA", "lat": 29.7244, "lon": -95.4380,
     "agency": "Intuitive Machines", "focus": "Lunar Landers & Micro-Rovers",
     "notable": "Nova-C Odysseus lander", "founded": 2013},
    {"name": "Astrobotic", "city": "Pittsburgh", "country": "USA", "lat": 40.4579, "lon": -79.9628,
     "agency": "Astrobotic", "focus": "Lunar Delivery & Rovers",
     "notable": "Peregrine lander, Griffin lander", "founded": 2007},
    {"name": "ispace", "city": "Tokyo", "country": "Japan", "lat": 35.6700, "lon": 139.7400,
     "agency": "ispace", "focus": "Commercial Lunar Landers",
     "notable": "HAKUTO-R lander & rover", "founded": 2010},
    {"name": "SpaceX Starship (Mars)", "city": "Boca Chica", "country": "USA", "lat": 25.9972, "lon": -97.1558,
     "agency": "SpaceX", "focus": "Mars Transport & In-Situ Robotics",
     "notable": "Starship, Mechazilla catch system", "founded": 2002},
    {"name": "Blue Origin New Glenn", "city": "Cape Canaveral", "country": "USA", "lat": 28.5249, "lon": -80.6534,
     "agency": "Blue Origin", "focus": "Lunar Lander (Blue Moon)",
     "notable": "Blue Moon MK2, New Glenn", "founded": 2000},
    {"name": "Avio - Vega Launcher", "city": "Colleferro", "country": "Italy", "lat": 41.7269, "lon": 13.0075,
     "agency": "Avio/ESA", "focus": "Launch Vehicle Automation",
     "notable": "Vega-C, automated launch systems", "founded": 1994},
    {"name": "Indian Space Research - Vyommitra", "city": "Thiruvananthapuram", "country": "India", "lat": 8.5241, "lon": 76.9366,
     "agency": "ISRO/VSSC", "focus": "Humanoid Space Robot",
     "notable": "Vyommitra robot for Gaganyaan", "founded": 1962},
]

# ---------------------------------------------------------------------------
# MODE 6: Medical Robotics Centers
# ---------------------------------------------------------------------------
MEDICAL_ROBOTICS_CENTERS = [
    {"name": "Intuitive Surgical HQ", "city": "Sunnyvale", "country": "USA", "lat": 37.3861, "lon": -122.0248,
     "company": "Intuitive Surgical", "specialty": "Robotic Surgery",
     "products": "da Vinci Xi/SP, Ion", "procedures_k": 14000, "founded": 1995},
    {"name": "Medtronic Surgical Robotics", "city": "Minneapolis", "country": "USA", "lat": 44.9778, "lon": -93.2650,
     "company": "Medtronic", "specialty": "Surgical Robotics",
     "products": "Hugo RAS system", "procedures_k": 500, "founded": 1949},
    {"name": "Stryker Mako Robotics", "city": "Kalamazoo", "country": "USA", "lat": 42.2917, "lon": -85.5872,
     "company": "Stryker", "specialty": "Orthopedic Robotic Surgery",
     "products": "Mako SmartRobotics", "procedures_k": 2000, "founded": 1941},
    {"name": "Zimmer Biomet ROSA", "city": "Warsaw", "country": "USA", "lat": 41.2381, "lon": -85.8531,
     "company": "Zimmer Biomet", "specialty": "Spine & Knee Robotics",
     "products": "ROSA ONE Spine, ROSA Knee", "procedures_k": 800, "founded": 1927},
    {"name": "Johnson & Johnson (Auris/Monarch)", "city": "Redwood City", "country": "USA", "lat": 37.4852, "lon": -122.2364,
     "company": "J&J / Auris Health", "specialty": "Robotic Bronchoscopy",
     "products": "Monarch Platform", "procedures_k": 200, "founded": 2007},
    {"name": "CMR Surgical (Versius)", "city": "Cambridge", "country": "UK", "lat": 52.2053, "lon": 0.1218,
     "company": "CMR Surgical", "specialty": "Minimal-access Surgery",
     "products": "Versius Surgical Robot", "procedures_k": 100, "founded": 2014},
    {"name": "Accuray (CyberKnife)", "city": "Sunnyvale", "country": "USA", "lat": 37.3739, "lon": -122.0169,
     "company": "Accuray", "specialty": "Robotic Radiosurgery",
     "products": "CyberKnife S7, Radixact", "procedures_k": 3000, "founded": 1990},
    {"name": "Mazor Robotics (Medtronic)", "city": "Caesarea", "country": "Israel", "lat": 32.5025, "lon": 34.8903,
     "company": "Mazor/Medtronic", "specialty": "Spine Surgery Robotics",
     "products": "Mazor X Stealth", "procedures_k": 500, "founded": 2001},
    {"name": "Ekso Bionics", "city": "San Rafael", "country": "USA", "lat": 37.9735, "lon": -122.5311,
     "company": "Ekso Bionics", "specialty": "Rehabilitation Exoskeletons",
     "products": "EksoNR, EksoUE", "procedures_k": 300, "founded": 2005},
    {"name": "ReWalk Robotics", "city": "Yokneam", "country": "Israel", "lat": 32.6592, "lon": 35.1009,
     "company": "ReWalk / Lifeward", "specialty": "Wearable Exoskeletons",
     "products": "ReWalk Personal 6.0, ReStore", "procedures_k": 100, "founded": 2001},
    {"name": "Cyberdyne (HAL)", "city": "Tsukuba", "country": "Japan", "lat": 36.0830, "lon": 140.1117,
     "company": "Cyberdyne", "specialty": "Cyborg-type Exoskeletons",
     "products": "HAL (Hybrid Assistive Limb)", "procedures_k": 200, "founded": 2004},
    {"name": "Renishaw Neuromate", "city": "Wotton-under-Edge", "country": "UK", "lat": 51.6372, "lon": -2.3497,
     "company": "Renishaw", "specialty": "Neurosurgical Robotics",
     "products": "neuromate stereotactic robot", "procedures_k": 50, "founded": 1973},
    {"name": "Corindus (Siemens Healthineers)", "city": "Waltham", "country": "USA", "lat": 42.3765, "lon": -71.2356,
     "company": "Siemens Healthineers", "specialty": "Vascular Robotic Surgery",
     "products": "CorPath GRX", "procedures_k": 100, "founded": 2002},
    {"name": "Procept BioRobotics", "city": "Redwood City", "country": "USA", "lat": 37.4852, "lon": -122.2300,
     "company": "Procept BioRobotics", "specialty": "Urological Robotics",
     "products": "AquaBeam Robotic System", "procedures_k": 50, "founded": 2009},
    {"name": "Think Surgical", "city": "Fremont", "country": "USA", "lat": 37.5485, "lon": -121.9886,
     "company": "Think Surgical", "specialty": "Orthopedic Active Robots",
     "products": "TSolution One, TMINI", "procedures_k": 30, "founded": 1988},
    {"name": "Vicarious Surgical", "city": "Waltham", "country": "USA", "lat": 42.3950, "lon": -71.2565,
     "company": "Vicarious Surgical", "specialty": "Miniaturized Surgical Robots",
     "products": "VR-controlled micro-surgical robot", "procedures_k": 5, "founded": 2014},
    {"name": "Asensus (Senhance)", "city": "Durham", "country": "USA", "lat": 35.9940, "lon": -78.8986,
     "company": "Asensus Surgical", "specialty": "Digital Laparoscopy",
     "products": "Senhance Surgical System", "procedures_k": 50, "founded": 2006},
    {"name": "Shanghai MicroPort MedBot", "city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737,
     "company": "MicroPort MedBot", "specialty": "Multi-specialty Surgical Robots",
     "products": "Toumai, Honghu (orthopedic)", "procedures_k": 200, "founded": 2014},
    {"name": "Tinavi Medical", "city": "Beijing", "country": "China", "lat": 39.9627, "lon": 116.4220,
     "company": "Tinavi Medical", "specialty": "Orthopedic Surgical Robot",
     "products": "TiRobot", "procedures_k": 100, "founded": 2005},
    {"name": "Myomo", "city": "Cambridge", "country": "USA", "lat": 42.3736, "lon": -71.1097,
     "company": "Myomo", "specialty": "Powered Orthotics",
     "products": "MyoPro arm orthosis", "procedures_k": 20, "founded": 2004},
    {"name": "Bionik Laboratories", "city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832,
     "company": "Bionik Labs", "specialty": "Rehabilitation Robotics",
     "products": "InMotion ARM/HAND", "procedures_k": 30, "founded": 2010},
    {"name": "Hocoma (DIH Group)", "city": "Volketswil", "country": "Switzerland", "lat": 47.3890, "lon": 8.6830,
     "company": "Hocoma / DIH", "specialty": "Neurorehabilitation Robotics",
     "products": "Lokomat, Armeo, Erigo", "procedures_k": 500, "founded": 2000},
    {"name": "Brainlab", "city": "Munich", "country": "Germany", "lat": 48.1005, "lon": 11.6073,
     "company": "Brainlab", "specialty": "Surgical Navigation & Robotics",
     "products": "Cirq robotic alignment, Curve navigation", "procedures_k": 1500, "founded": 1989},
    {"name": "Avatera Medical", "city": "Jena", "country": "Germany", "lat": 50.9271, "lon": 11.5892,
     "company": "Avatera Medical", "specialty": "Surgical Robotics (EU)",
     "products": "avatera robotic surgical system", "procedures_k": 10, "founded": 2010},
    {"name": "Rob Surgical (Bitrack)", "city": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686,
     "company": "Rob Surgical", "specialty": "Laparoscopic Robotic Surgery",
     "products": "Bitrack system", "procedures_k": 5, "founded": 2012},
]

# ---------------------------------------------------------------------------
# MODE 7: Industrial Automation Hubs
# ---------------------------------------------------------------------------
INDUSTRIAL_AUTOMATION_HUBS = [
    {"name": "Siemens Digital Industries", "city": "Nuremberg", "country": "Germany", "lat": 49.4521, "lon": 11.0767,
     "company": "Siemens", "focus": "PLCs, SCADA, Digital Twin",
     "revenue_b": 20.5, "employees": 72000, "products": "SIMATIC, TIA Portal, MindSphere"},
    {"name": "Rockwell Automation HQ", "city": "Milwaukee", "country": "USA", "lat": 43.0389, "lon": -87.9065,
     "company": "Rockwell Automation", "focus": "Industrial Control & IoT",
     "revenue_b": 8.0, "employees": 28000, "products": "Allen-Bradley, FactoryTalk, Plex"},
    {"name": "Schneider Electric Automation", "city": "Rueil-Malmaison", "country": "France", "lat": 48.8766, "lon": 2.1810,
     "company": "Schneider Electric", "focus": "Energy + Automation",
     "revenue_b": 36.0, "employees": 150000, "products": "Modicon, EcoStruxure, AVEVA"},
    {"name": "ABB Industrial Automation", "city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417,
     "company": "ABB", "focus": "Robotics, Process Automation",
     "revenue_b": 32.0, "employees": 105000, "products": "ABB Ability, AC500, 800xA"},
    {"name": "Honeywell Process Solutions", "city": "Houston", "country": "USA", "lat": 29.7604, "lon": -95.3698,
     "company": "Honeywell", "focus": "Process Control, DCS",
     "revenue_b": 36.6, "employees": 95000, "products": "Experion PKS, Forge"},
    {"name": "Emerson Automation", "city": "St. Louis", "country": "USA", "lat": 38.6270, "lon": -90.1994,
     "company": "Emerson", "focus": "Process & Discrete Automation",
     "revenue_b": 15.2, "employees": 85000, "products": "DeltaV, Ovation, PACSystems"},
    {"name": "Mitsubishi Electric Factory Automation", "city": "Nagoya", "country": "Japan", "lat": 35.1802, "lon": 136.9066,
     "company": "Mitsubishi Electric", "focus": "Factory Automation, CNC",
     "revenue_b": 40.0, "employees": 149000, "products": "MELSEC, iQ-R, e-F@ctory"},
    {"name": "Omron Industrial Automation", "city": "Kyoto", "country": "Japan", "lat": 34.9937, "lon": 135.7519,
     "company": "Omron", "focus": "Sensing, Control, Robotics",
     "revenue_b": 7.0, "employees": 28000, "products": "NX/NJ controllers, Sysmac"},
    {"name": "Keyence Corporation", "city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023,
     "company": "Keyence", "focus": "Sensors, Vision, Measurement",
     "revenue_b": 7.5, "employees": 10000, "products": "IV series, LJ-X8000, KV PLC"},
    {"name": "Beckhoff Automation", "city": "Verl", "country": "Germany", "lat": 51.8759, "lon": 8.5064,
     "company": "Beckhoff", "focus": "PC-based Control, EtherCAT",
     "revenue_b": 1.8, "employees": 6000, "products": "TwinCAT 3, CX/CP controllers"},
    {"name": "B&R Industrial Automation (ABB)", "city": "Eggelsberg", "country": "Austria", "lat": 48.0778, "lon": 13.0392,
     "company": "B&R (ABB)", "focus": "Machine & Factory Automation",
     "revenue_b": 1.5, "employees": 4000, "products": "X20, ACOPOS, mapp Technology"},
    {"name": "Bosch Rexroth", "city": "Lohr am Main", "country": "Germany", "lat": 49.9892, "lon": 9.5738,
     "company": "Bosch Rexroth", "focus": "Motion Control, Hydraulics, IoT",
     "revenue_b": 7.0, "employees": 31000, "products": "ctrlX AUTOMATION, IndraMotion"},
    {"name": "Yokogawa Electric", "city": "Musashino", "country": "Japan", "lat": 35.7180, "lon": 139.5600,
     "company": "Yokogawa", "focus": "Process Automation, DCS",
     "revenue_b": 3.5, "employees": 17000, "products": "CENTUM VP, ProSafe-RS"},
    {"name": "Phoenix Contact", "city": "Blomberg", "country": "Germany", "lat": 51.9422, "lon": 9.0880,
     "company": "Phoenix Contact", "focus": "Connectors, PLCs, IIoT",
     "revenue_b": 3.5, "employees": 20000, "products": "PLCnext, QUINT power"},
    {"name": "Festo", "city": "Esslingen", "country": "Germany", "lat": 48.7425, "lon": 9.3056,
     "company": "Festo", "focus": "Pneumatic & Electric Automation",
     "revenue_b": 3.6, "employees": 20000, "products": "VTEM, BionicSoftArm, CPX-E"},
    {"name": "Pilz", "city": "Ostfildern", "country": "Germany", "lat": 48.7261, "lon": 9.2506,
     "company": "Pilz", "focus": "Safety Automation, Safe Robotics",
     "revenue_b": 0.4, "employees": 2500, "products": "PNOZ, PSS 4000, PNOZmulti 2"},
    {"name": "Delta Electronics", "city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654,
     "company": "Delta Electronics", "focus": "Drives, Motion, Robots",
     "revenue_b": 13.0, "employees": 80000, "products": "AS PLC, ASDA servo, SCARA"},
    {"name": "Wago", "city": "Minden", "country": "Germany", "lat": 52.2884, "lon": 8.9168,
     "company": "Wago", "focus": "Connection Technology, IIoT",
     "revenue_b": 1.2, "employees": 9000, "products": "PFC200, TOPJOB S, 750 I/O"},
    {"name": "Turck", "city": "Mulheim an der Ruhr", "country": "Germany", "lat": 51.4272, "lon": 6.8825,
     "company": "Turck", "focus": "Sensors, Fieldbus, RFID",
     "revenue_b": 0.8, "employees": 5000, "products": "BL20, IMX, TBEN modules"},
    {"name": "Danfoss Drives", "city": "Nordborg", "country": "Denmark", "lat": 55.0593, "lon": 9.7506,
     "company": "Danfoss", "focus": "Variable Frequency Drives",
     "revenue_b": 11.0, "employees": 42000, "products": "VLT, VACON, iC7"},
    {"name": "Cognex Corporation", "city": "Natick", "country": "USA", "lat": 42.2834, "lon": -71.3468,
     "company": "Cognex", "focus": "Machine Vision, Barcode Readers",
     "revenue_b": 1.0, "employees": 2400, "products": "In-Sight, DataMan, VisionPro"},
    {"name": "IFM Electronic", "city": "Essen", "country": "Germany", "lat": 51.4556, "lon": 7.0116,
     "company": "IFM", "focus": "Industrial Sensors, IoT",
     "revenue_b": 1.3, "employees": 9000, "products": "IO-Link, moneo, efector"},
    {"name": "Advantech", "city": "Taipei", "country": "Taiwan", "lat": 25.0795, "lon": 121.5721,
     "company": "Advantech", "focus": "Industrial IoT, Edge Computing",
     "revenue_b": 2.2, "employees": 8000, "products": "WISE-PaaS, UNO, ADAM"},
    {"name": "National Instruments (Emerson)", "city": "Austin", "country": "USA", "lat": 30.3880, "lon": -97.7260,
     "company": "NI (Emerson)", "focus": "Test & Measurement, HIL",
     "revenue_b": 1.7, "employees": 7500, "products": "LabVIEW, PXI, CompactRIO"},
    {"name": "Sick AG", "city": "Waldkirch", "country": "Germany", "lat": 48.0959, "lon": 7.9587,
     "company": "Sick", "focus": "Industrial Sensors, LiDAR",
     "revenue_b": 2.2, "employees": 12000, "products": "LMS, TiM LiDAR, Inspector"},
]

# ---------------------------------------------------------------------------
# MODE 8: AI Startup Ecosystems
# ---------------------------------------------------------------------------
AI_STARTUP_ECOSYSTEMS = [
    {"name": "San Francisco Bay Area", "city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194,
     "ai_startups": 3500, "unicorns": 45, "total_funding_b": 120,
     "key_players": "OpenAI, Anthropic, Databricks, Scale AI", "incubators": "Y Combinator, a16z"},
    {"name": "New York City AI Hub", "city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060,
     "ai_startups": 1200, "unicorns": 15, "total_funding_b": 35,
     "key_players": "Hugging Face, Runway, Jasper", "incubators": "Cornell Tech, Techstars NYC"},
    {"name": "London AI Corridor", "city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278,
     "ai_startups": 1800, "unicorns": 12, "total_funding_b": 25,
     "key_players": "DeepMind, Stability AI, Wayve, Synthesia", "incubators": "Entrepreneur First, Seedcamp"},
    {"name": "Beijing AI Zone", "city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074,
     "ai_startups": 2500, "unicorns": 25, "total_funding_b": 60,
     "key_players": "Baidu, ByteDance, SenseTime, Megvii", "incubators": "Zhongguancun, Tsinghua X-Lab"},
    {"name": "Shanghai AI Center", "city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737,
     "ai_startups": 1500, "unicorns": 12, "total_funding_b": 30,
     "key_players": "Alibaba, Yitu, CloudWalk", "incubators": "Zhangjiang AI Island"},
    {"name": "Toronto-Waterloo AI Corridor", "city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832,
     "ai_startups": 800, "unicorns": 8, "total_funding_b": 12,
     "key_players": "Cohere, Ada, Waabi, Vector Institute", "incubators": "MaRS, CDL, Velocity"},
    {"name": "Tel Aviv AI Ecosystem", "city": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lon": 34.7818,
     "ai_startups": 900, "unicorns": 10, "total_funding_b": 15,
     "key_players": "AI21 Labs, Run:ai, Hailo", "incubators": "8200 EISP, TheHive"},
    {"name": "Paris AI Scene", "city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522,
     "ai_startups": 700, "unicorns": 6, "total_funding_b": 10,
     "key_players": "Mistral AI, Hugging Face (FR), Dataiku", "incubators": "Station F, BPI France"},
    {"name": "Berlin AI Hub", "city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050,
     "ai_startups": 600, "unicorns": 5, "total_funding_b": 8,
     "key_players": "Aleph Alpha, Merantix, Ada Health", "incubators": "Factory Berlin, HTGF"},
    {"name": "Bangalore AI Hub", "city": "Bangalore", "country": "India", "lat": 12.9716, "lon": 77.5946,
     "ai_startups": 1000, "unicorns": 8, "total_funding_b": 10,
     "key_players": "Ola Krutrim, Sarvam AI, Fractal", "incubators": "NASSCOM, T-Hub, IISc"},
    {"name": "Singapore AI Cluster", "city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198,
     "ai_startups": 500, "unicorns": 4, "total_funding_b": 6,
     "key_players": "Grab AI, Trax, ViSenze", "incubators": "AI Singapore, Block71"},
    {"name": "Seoul AI Valley", "city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780,
     "ai_startups": 600, "unicorns": 5, "total_funding_b": 7,
     "key_players": "Naver, Kakao Brain, Upstage", "incubators": "K-Startup Grand Challenge"},
    {"name": "Tokyo AI District", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503,
     "ai_startups": 500, "unicorns": 3, "total_funding_b": 5,
     "key_players": "Preferred Networks, ABEJA, PKSHA", "incubators": "NVIDIA Inception Japan"},
    {"name": "Boston / Cambridge AI", "city": "Boston", "country": "USA", "lat": 42.3601, "lon": -71.0589,
     "ai_startups": 900, "unicorns": 10, "total_funding_b": 20,
     "key_players": "DataRobot, Neurala, Tulip", "incubators": "MIT delta v, MassChallenge"},
    {"name": "Montreal AI Ecosystem", "city": "Montreal", "country": "Canada", "lat": 45.5017, "lon": -73.5673,
     "ai_startups": 500, "unicorns": 3, "total_funding_b": 5,
     "key_players": "Element AI, Mila spinoffs", "incubators": "Mila, CDL Montreal"},
    {"name": "Shenzhen AI Manufacturing", "city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579,
     "ai_startups": 1200, "unicorns": 10, "total_funding_b": 20,
     "key_players": "DJI, UBTech, Tencent AI", "incubators": "HAX, Shenzhen Open Innovation Lab"},
    {"name": "Seattle AI Hub", "city": "Seattle", "country": "USA", "lat": 47.6062, "lon": -122.3321,
     "ai_startups": 700, "unicorns": 8, "total_funding_b": 15,
     "key_players": "Amazon AWS AI, Allen AI, Xnor", "incubators": "Allen AI Incubator, Madrona"},
    {"name": "Austin AI Scene", "city": "Austin", "country": "USA", "lat": 30.2672, "lon": -97.7431,
     "ai_startups": 400, "unicorns": 4, "total_funding_b": 6,
     "key_players": "CognitiveScale, SparkCognition, data.world", "incubators": "Capital Factory, ATI"},
    {"name": "Amsterdam AI Hub", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041,
     "ai_startups": 400, "unicorns": 3, "total_funding_b": 4,
     "key_players": "Adyen AI, TomTom AI, Ahold Delhaize AI", "incubators": "ACE Incubator, YES!Delft"},
    {"name": "Munich AI Cluster", "city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820,
     "ai_startups": 350, "unicorns": 3, "total_funding_b": 4,
     "key_players": "Celonis, Lilium AI, appliedAI", "incubators": "UnternehmerTUM, TUM AI"},
    {"name": "Zurich AI & ML", "city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417,
     "ai_startups": 300, "unicorns": 2, "total_funding_b": 3,
     "key_players": "Scandit, DeepCode, LatticeFlow", "incubators": "ETH AI Center, Kickstart"},
    {"name": "Stockholm AI", "city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686,
     "ai_startups": 300, "unicorns": 3, "total_funding_b": 3,
     "key_players": "Klarna AI, Sana Labs, Peltarion", "incubators": "STING, KTH Innovation"},
    {"name": "Dubai AI Hub", "city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708,
     "ai_startups": 250, "unicorns": 2, "total_funding_b": 3,
     "key_players": "G42, Presight AI, DarkMatter", "incubators": "Hub71, DIFC Fintech Hive"},
    {"name": "Sao Paulo AI Hub", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333,
     "ai_startups": 300, "unicorns": 2, "total_funding_b": 2,
     "key_players": "Loft, Creditas AI, Semantix", "incubators": "Cubo Itau, InovaBra"},
    {"name": "Helsinki AI", "city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384,
     "ai_startups": 200, "unicorns": 2, "total_funding_b": 2,
     "key_players": "Silo AI, Curious AI, Aiven", "incubators": "Aalto Startup Center, Maria01"},
]

# ---------------------------------------------------------------------------
# MODE 9: Quantum Computing Centers
# ---------------------------------------------------------------------------
QUANTUM_COMPUTING_CENTERS = [
    {"name": "IBM Quantum Network Hub", "city": "Yorktown Heights", "country": "USA", "lat": 41.2137, "lon": -73.8032,
     "org": "IBM", "qubits": 1121, "type": "Superconducting",
     "system": "IBM Condor (1121-qubit), Heron", "founded": 2016},
    {"name": "Google Quantum AI Lab", "city": "Santa Barbara", "country": "USA", "lat": 34.4208, "lon": -119.6982,
     "org": "Google / Alphabet", "qubits": 105, "type": "Superconducting",
     "system": "Willow (105-qubit), Sycamore", "founded": 2014},
    {"name": "Microsoft Azure Quantum (Station Q)", "city": "Santa Barbara", "country": "USA", "lat": 34.4135, "lon": -119.8488,
     "org": "Microsoft", "qubits": 12, "type": "Topological (Majorana)",
     "system": "Majorana 1 topological qubit", "founded": 2012},
    {"name": "Amazon AWS Center for Quantum Computing", "city": "Pasadena", "country": "USA", "lat": 34.1478, "lon": -118.1445,
     "org": "Amazon / Caltech", "qubits": 50, "type": "Superconducting",
     "system": "Ocelot (cat qubit), Braket cloud", "founded": 2019},
    {"name": "IonQ HQ", "city": "College Park", "country": "USA", "lat": 38.9897, "lon": -76.9378,
     "org": "IonQ", "qubits": 36, "type": "Trapped Ion",
     "system": "IonQ Forte Enterprise (36 AQ)", "founded": 2015},
    {"name": "Quantinuum (Honeywell)", "city": "Broomfield", "country": "USA", "lat": 39.9205, "lon": -105.0867,
     "org": "Quantinuum", "qubits": 56, "type": "Trapped Ion",
     "system": "H2 (56-qubit), TKET compiler", "founded": 2021},
    {"name": "Rigetti Computing", "city": "Berkeley", "country": "USA", "lat": 37.8716, "lon": -122.2727,
     "org": "Rigetti", "qubits": 84, "type": "Superconducting",
     "system": "Ankaa-3 (84-qubit)", "founded": 2013},
    {"name": "D-Wave Systems", "city": "Burnaby", "country": "Canada", "lat": 49.2488, "lon": -122.9805,
     "org": "D-Wave", "qubits": 5000, "type": "Quantum Annealing",
     "system": "Advantage2 (1200+ qubit), Advantage (5000+)", "founded": 1999},
    {"name": "Xanadu Quantum Technologies", "city": "Toronto", "country": "Canada", "lat": 43.6426, "lon": -79.3871,
     "org": "Xanadu", "qubits": 216, "type": "Photonic",
     "system": "Borealis (216-mode photonic)", "founded": 2016},
    {"name": "PsiQuantum", "city": "Palo Alto", "country": "USA", "lat": 37.4419, "lon": -122.1430,
     "org": "PsiQuantum", "qubits": 1000000, "type": "Photonic (goal)",
     "system": "Photonic fusion-based (in development)", "founded": 2016},
    {"name": "IQM Quantum Computers", "city": "Espoo", "country": "Finland", "lat": 60.2055, "lon": 24.6559,
     "org": "IQM", "qubits": 150, "type": "Superconducting",
     "system": "IQM Spark, IQM Radiance", "founded": 2018},
    {"name": "Oxford Quantum Circuits", "city": "Oxford", "country": "UK", "lat": 51.7520, "lon": -1.2577,
     "org": "OQC", "qubits": 32, "type": "Superconducting (Coaxmon)",
     "system": "OQC Lucy, Toshiko 32Q", "founded": 2017},
    {"name": "Pasqal", "city": "Palaiseau", "country": "France", "lat": 48.7147, "lon": 2.2079,
     "org": "Pasqal", "qubits": 300, "type": "Neutral Atom",
     "system": "300-atom processor", "founded": 2019},
    {"name": "QuEra Computing", "city": "Boston", "country": "USA", "lat": 42.3601, "lon": -71.0589,
     "org": "QuEra", "qubits": 256, "type": "Neutral Atom",
     "system": "Aquila (256-qubit neutral atom)", "founded": 2018},
    {"name": "Alibaba Quantum Laboratory", "city": "Hangzhou", "country": "China", "lat": 30.2741, "lon": 120.1551,
     "org": "Alibaba / DAMO", "qubits": 72, "type": "Superconducting",
     "system": "Fluxonium qubit processor", "founded": 2017},
    {"name": "USTC Hefei Quantum Lab", "city": "Hefei", "country": "China", "lat": 31.8206, "lon": 117.2272,
     "org": "USTC / CAS", "qubits": 113, "type": "Photonic & Superconducting",
     "system": "Jiuzhang (photonic), Zuchongzhi (66Q)", "founded": 2017},
    {"name": "Baidu Quantum", "city": "Beijing", "country": "China", "lat": 40.0565, "lon": 116.3079,
     "org": "Baidu", "qubits": 36, "type": "Superconducting",
     "system": "Qianshi (10Q), Lianxiang (36Q)", "founded": 2018},
    {"name": "RIKEN Quantum Computing Center", "city": "Wako", "country": "Japan", "lat": 35.7863, "lon": 139.6102,
     "org": "RIKEN", "qubits": 64, "type": "Superconducting",
     "system": "IBM-RIKEN 64-qubit system", "founded": 2021},
    {"name": "Forschungszentrum Julich (PGI)", "city": "Julich", "country": "Germany", "lat": 50.9060, "lon": 6.3644,
     "org": "FZJ / PGI", "qubits": 100, "type": "Superconducting & Trapped Ion",
     "system": "JUNIQ (cloud quantum), OpenSuperQPlus", "founded": 2019},
    {"name": "QuTech (TU Delft)", "city": "Delft", "country": "Netherlands", "lat": 52.0116, "lon": 4.3571,
     "org": "QuTech / TU Delft", "qubits": 25, "type": "Spin Qubit & NV Center",
     "system": "Quantum Internet demo, spin qubit processors", "founded": 2014},
    {"name": "Centre for Quantum Technologies", "city": "Singapore", "country": "Singapore", "lat": 1.2966, "lon": 103.7764,
     "org": "CQT / NUS", "qubits": 20, "type": "Trapped Ion & Photonic",
     "system": "Ion trap systems, QKD networks", "founded": 2007},
    {"name": "Sydney Quantum Academy", "city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093,
     "org": "SQA (4 universities)", "qubits": 10, "type": "Silicon Spin Qubit",
     "system": "Silicon quantum dot processors", "founded": 2020},
    {"name": "Atom Computing", "city": "Berkeley", "country": "USA", "lat": 37.8753, "lon": -122.2577,
     "org": "Atom Computing", "qubits": 1225, "type": "Neutral Atom",
     "system": "1225-site neutral atom array", "founded": 2018},
    {"name": "Alpine Quantum Technologies", "city": "Innsbruck", "country": "Austria", "lat": 47.2692, "lon": 11.4041,
     "org": "AQT", "qubits": 24, "type": "Trapped Ion",
     "system": "PINE system (24-qubit trapped ion)", "founded": 2017},
    {"name": "National Quantum Computing Centre", "city": "Harwell", "country": "UK", "lat": 51.5714, "lon": -1.3155,
     "org": "NQCC / UKRI", "qubits": 50, "type": "Multiple",
     "system": "Testbed for UK quantum hardware", "founded": 2020},
]

# ---------------------------------------------------------------------------
# MODE 10: Robot Museums & Exhibitions
# ---------------------------------------------------------------------------
ROBOT_MUSEUMS = [
    {"name": "Miraikan (National Museum of Emerging Science)", "city": "Tokyo", "country": "Japan",
     "lat": 35.6190, "lon": 139.7764, "type": "Science Museum",
     "highlights": "ASIMO demos, Alter-3 android, Geo-Cosmos", "visitors_k": 1500, "opened": 2001},
    {"name": "Robot Museum at AIST", "city": "Tsukuba", "country": "Japan",
     "lat": 36.0572, "lon": 140.1299, "type": "Research Exhibition",
     "highlights": "AIST humanoids, HRP series, paro robot", "visitors_k": 100, "opened": 2006},
    {"name": "Deutsches Museum - Robotics Hall", "city": "Munich", "country": "Germany",
     "lat": 48.1298, "lon": 11.5832, "type": "Technology Museum",
     "highlights": "Industrial robot history, KUKA demos, AI exhibits", "visitors_k": 1500, "opened": 1903},
    {"name": "Science Museum - Robots Exhibition", "city": "London", "country": "UK",
     "lat": 51.4978, "lon": -0.1745, "type": "Science Museum",
     "highlights": "500-year robot history, Pepper, Zeno", "visitors_k": 3300, "opened": 1857},
    {"name": "MIT Museum - Robots & Beyond", "city": "Cambridge", "country": "USA",
     "lat": 42.3622, "lon": -71.0857, "type": "University Museum",
     "highlights": "Kismet, MIT robotics history, AI art", "visitors_k": 200, "opened": 1971},
    {"name": "Computer History Museum", "city": "Mountain View", "country": "USA",
     "lat": 37.4144, "lon": -122.0775, "type": "Technology Museum",
     "highlights": "AI & robotics gallery, autonomous vehicle exhibit", "visitors_k": 500, "opened": 1996},
    {"name": "Carnegie Science Center - Roboworld", "city": "Pittsburgh", "country": "USA",
     "lat": 40.4455, "lon": -80.0185, "type": "Science Center",
     "highlights": "Largest robot exhibition in USA, interactive robots", "visitors_k": 600, "opened": 1991},
    {"name": "ROBOTS Exhibition (travelling)", "city": "Various", "country": "International",
     "lat": 51.5074, "lon": -0.1278, "type": "Travelling Exhibition",
     "highlights": "Science Museum's touring 500-year robot show", "visitors_k": 800, "opened": 2017},
    {"name": "Tekniska Museet - Robotics Gallery", "city": "Stockholm", "country": "Sweden",
     "lat": 59.3299, "lon": 18.0980, "type": "Technology Museum",
     "highlights": "Interactive robots, ABB industrial demos", "visitors_k": 350, "opened": 1936},
    {"name": "Cite des Sciences - Robot Exhibition", "city": "Paris", "country": "France",
     "lat": 48.8956, "lon": 2.3872, "type": "Science Museum",
     "highlights": "NAO, Pepper, surgical robots, exoskeletons", "visitors_k": 2500, "opened": 1986},
    {"name": "NEMO Science Museum", "city": "Amsterdam", "country": "Netherlands",
     "lat": 52.3738, "lon": 4.9123, "type": "Science Museum",
     "highlights": "Robotics lab, AI playground, interactive tech", "visitors_k": 670, "opened": 1997},
    {"name": "Museo Nazionale della Scienza e della Tecnologia", "city": "Milan", "country": "Italy",
     "lat": 45.4629, "lon": 9.1707, "type": "Science & Technology Museum",
     "highlights": "Leonardo da Vinci automata, modern robotics", "visitors_k": 500, "opened": 1953},
    {"name": "Henn-na Hotel (Robot Hotel)", "city": "Nagasaki", "country": "Japan",
     "lat": 33.0878, "lon": 129.7893, "type": "Robot Hotel / Experience",
     "highlights": "Robot receptionists, porters, cloakroom, cleaning", "visitors_k": 200, "opened": 2015},
    {"name": "EXPO 2025 Osaka - Robot Pavilion", "city": "Osaka", "country": "Japan",
     "lat": 34.6559, "lon": 135.4262, "type": "World Expo Pavilion",
     "highlights": "Humanoids, AI assistants, next-gen robotics", "visitors_k": 5000, "opened": 2025},
    {"name": "Boston Dynamics AI Institute - Demo Lab", "city": "Cambridge", "country": "USA",
     "lat": 42.3630, "lon": -71.0872, "type": "Corporate Demo",
     "highlights": "Atlas, Spot, Stretch live demonstrations", "visitors_k": 50, "opened": 2023},
    {"name": "IEEE Robots & Automation (ICRA) Annual Expo", "city": "Various", "country": "International",
     "lat": 40.7128, "lon": -74.0060, "type": "Annual Conference",
     "highlights": "World's top robotics conference exhibition", "visitors_k": 5000, "opened": 1984},
    {"name": "Automate Show (A3 Association)", "city": "Chicago", "country": "USA",
     "lat": 41.8781, "lon": -87.6298, "type": "Trade Show",
     "highlights": "Largest N. American robotics trade show", "visitors_k": 30000, "opened": 1977},
    {"name": "iREX (International Robot Exhibition)", "city": "Tokyo", "country": "Japan",
     "lat": 35.6310, "lon": 139.7662, "type": "Trade Show",
     "highlights": "World's largest robot trade fair, biennial", "visitors_k": 150000, "opened": 1973},
    {"name": "RoboCup Venue (annual)", "city": "Various", "country": "International",
     "lat": 48.8566, "lon": 2.3522, "type": "Competition/Exhibition",
     "highlights": "Robot soccer, rescue, @home, industrial leagues", "visitors_k": 40000, "opened": 1997},
    {"name": "Automatica Munich", "city": "Munich", "country": "Germany",
     "lat": 48.1382, "lon": 11.6890, "type": "Trade Fair",
     "highlights": "Leading European automation trade fair (biennial)", "visitors_k": 45000, "opened": 2004},
    {"name": "China International Robot Show (CIROS)", "city": "Shanghai", "country": "China",
     "lat": 31.1939, "lon": 121.4916, "type": "Trade Show",
     "highlights": "Largest Chinese robotics exposition", "visitors_k": 60000, "opened": 2012},
    {"name": "World Robot Conference", "city": "Beijing", "country": "China",
     "lat": 39.7600, "lon": 116.6800, "type": "Conference/Exhibition",
     "highlights": "Annual robot expo + competitions, 500+ exhibitors", "visitors_k": 250000, "opened": 2015},
    {"name": "Exploratorium - Tinkering Studio", "city": "San Francisco", "country": "USA",
     "lat": 37.8016, "lon": -122.3976, "type": "Science Museum",
     "highlights": "Hands-on robotics, art-bots, coding workshops", "visitors_k": 850, "opened": 1969},
    {"name": "Copernicus Science Centre", "city": "Warsaw", "country": "Poland",
     "lat": 52.2419, "lon": 21.0285, "type": "Science Centre",
     "highlights": "Robot theatre, interactive AI exhibits", "visitors_k": 1000, "opened": 2010},
    {"name": "VEX Robotics World Championship", "city": "Dallas", "country": "USA",
     "lat": 32.7767, "lon": -96.7970, "type": "Competition",
     "highlights": "Largest youth robotics competition globally", "visitors_k": 30000, "opened": 2007},
]


# ---------------------------------------------------------------------------
# Data map (mode name -> data list)
# ---------------------------------------------------------------------------
MODE_DATA_MAP = {
    "AI Research Labs": AI_RESEARCH_LABS,
    "Robot Manufacturing Plants": ROBOT_MANUFACTURING,
    "Autonomous Vehicle Hubs": AUTONOMOUS_VEHICLE_HUBS,
    "Drone Innovation Centers": DRONE_INNOVATION_CENTERS,
    "Space Robotics Facilities": SPACE_ROBOTICS,
    "Medical Robotics Centers": MEDICAL_ROBOTICS_CENTERS,
    "Industrial Automation Hubs": INDUSTRIAL_AUTOMATION_HUBS,
    "AI Startup Ecosystems": AI_STARTUP_ECOSYSTEMS,
    "Quantum Computing Centers": QUANTUM_COMPUTING_CENTERS,
    "Robot Museums & Exhibitions": ROBOT_MUSEUMS,
}

# Icon & color per mode
MODE_STYLE = {
    "AI Research Labs":           {"icon": "brain",         "color": "#06b6d4", "prefix": "fa"},
    "Robot Manufacturing Plants": {"icon": "industry",      "color": "#f59e0b", "prefix": "fa"},
    "Autonomous Vehicle Hubs":    {"icon": "car",           "color": "#10b981", "prefix": "fa"},
    "Drone Innovation Centers":   {"icon": "paper-plane",   "color": "#8b5cf6", "prefix": "fa"},
    "Space Robotics Facilities":  {"icon": "rocket",        "color": "#ec4899", "prefix": "fa"},
    "Medical Robotics Centers":   {"icon": "heartbeat",     "color": "#ef4444", "prefix": "fa"},
    "Industrial Automation Hubs": {"icon": "cogs",          "color": "#f97316", "prefix": "fa"},
    "AI Startup Ecosystems":      {"icon": "lightbulb-o",   "color": "#22d3ee", "prefix": "fa"},
    "Quantum Computing Centers":  {"icon": "atom",          "color": "#a78bfa", "prefix": "fa"},
    "Robot Museums & Exhibitions":{"icon": "university",    "color": "#34d399", "prefix": "fa"},
}


# ---------------------------------------------------------------------------
# Helper: build popup HTML
# ---------------------------------------------------------------------------
def _popup_html(title: str, fields: dict, color: str = "#06b6d4") -> str:
    """Build a dark-themed popup with escaped values."""
    rows = ""
    for label, value in fields.items():
        rows += f'<div class="field"><b>{html_module.escape(str(label))}:</b> {html_module.escape(str(value))}</div>'
    return f"""
    <div style="font-family:'Segoe UI',sans-serif;min-width:230px;color:#e8ecf4;
                background:#111827;border:1px solid #2a3550;border-radius:8px;padding:10px;">
        <h4 style="margin:0 0 6px 0;color:{color};font-size:14px;">
            {html_module.escape(str(title))}
        </h4>
        {rows}
    </div>
    """


# ---------------------------------------------------------------------------
# Helper: render map + stats + dataframe for a mode
# ---------------------------------------------------------------------------
def _render_mode(mode: str, data: list):
    """Render metrics, folium map, dataframe, and CSV download for a mode."""
    style = MODE_STYLE.get(mode, {"icon": "map-marker", "color": "#06b6d4", "prefix": "fa"})
    color = style["color"]
    icon_name = style["icon"]
    prefix = style["prefix"]

    # --- Metrics ---
    _render_metrics(mode, data, color)

    # --- Map ---
    m = folium.Map(location=DEFAULT_CENTER, zoom_start=DEFAULT_ZOOM, tiles=DARK_TILE)

    for item in data:
        lat = item.get("lat", 0)
        lon = item.get("lon", 0)
        name = item.get("name", "Unknown")

        popup_fields = _get_popup_fields(mode, item)
        popup_content = _popup_html(name, popup_fields, color)

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=name,
            icon=folium.Icon(color="darkblue", icon=icon_name, prefix=prefix),
        ).add_to(m)

    st_html(m._repr_html_(), height=MAP_HEIGHT)

    # --- DataFrame ---
    df = pd.DataFrame(data)
    st.markdown(f"### Data Table ({len(df)} entries)")
    st.dataframe(df, use_container_width=True)

    # --- CSV download ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {mode} CSV",
        data=csv,
        file_name=f"robot_maps_{mode.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key=f"dl_{mode}",
    )


# ---------------------------------------------------------------------------
# Metrics per mode
# ---------------------------------------------------------------------------
def _render_metrics(mode: str, data: list, color: str):
    """Show st.metric() cards relevant to each mode."""
    n = len(data)

    if mode == "AI Research Labs":
        countries = len(set(d["country"] for d in data))
        total_staff = sum(d.get("staff_est", 0) for d in data)
        avg_year = int(sum(d.get("founded", 2000) for d in data) / n)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Labs", n)
        c2.metric("Countries", countries)
        c3.metric("Est. Staff", f"{total_staff:,}")
        c4.metric("Avg Founded", avg_year)

    elif mode == "Robot Manufacturing Plants":
        countries = len(set(d["country"] for d in data))
        total_robots = sum(d.get("robots_year", 0) for d in data)
        types = len(set(d.get("type", "") for d in data))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Manufacturers", n)
        c2.metric("Countries", countries)
        c3.metric("Cumul. Robots/yr", f"{total_robots:,}")
        c4.metric("Robot Types", types)

    elif mode == "Autonomous Vehicle Hubs":
        countries = len(set(d["country"] for d in data))
        total_miles = sum(d.get("test_miles_m", 0) for d in data)
        total_fleet = sum(d.get("fleet_size", 0) for d in data)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AV Companies", n)
        c2.metric("Countries", countries)
        c3.metric("Test Miles (M)", f"{total_miles:,}")
        c4.metric("Total Fleet", f"{total_fleet:,}")

    elif mode == "Drone Innovation Centers":
        countries = len(set(d["country"] for d in data))
        total_emp = sum(d.get("employees", 0) for d in data)
        avg_year = int(sum(d.get("founded", 2000) for d in data) / n)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Drone Centers", n)
        c2.metric("Countries", countries)
        c3.metric("Total Employees", f"{total_emp:,}")
        c4.metric("Avg Founded", avg_year)

    elif mode == "Space Robotics Facilities":
        countries = len(set(d["country"] for d in data))
        agencies = len(set(d.get("agency", "") for d in data))
        avg_year = int(sum(d.get("founded", 2000) for d in data) / n)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Facilities", n)
        c2.metric("Countries", countries)
        c3.metric("Agencies/Orgs", agencies)
        c4.metric("Avg Founded", avg_year)

    elif mode == "Medical Robotics Centers":
        countries = len(set(d["country"] for d in data))
        total_procs = sum(d.get("procedures_k", 0) for d in data)
        specialties = len(set(d.get("specialty", "") for d in data))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Companies", n)
        c2.metric("Countries", countries)
        c3.metric("Procedures (k)", f"{total_procs:,}")
        c4.metric("Specialties", specialties)

    elif mode == "Industrial Automation Hubs":
        countries = len(set(d["country"] for d in data))
        total_rev = sum(d.get("revenue_b", 0) for d in data)
        total_emp = sum(d.get("employees", 0) for d in data)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Companies", n)
        c2.metric("Countries", countries)
        c3.metric("Combined Rev ($B)", f"{total_rev:,.1f}")
        c4.metric("Total Employees", f"{total_emp:,}")

    elif mode == "AI Startup Ecosystems":
        countries = len(set(d["country"] for d in data))
        total_startups = sum(d.get("ai_startups", 0) for d in data)
        total_unicorns = sum(d.get("unicorns", 0) for d in data)
        total_funding = sum(d.get("total_funding_b", 0) for d in data)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ecosystems", n)
        c2.metric("AI Startups", f"{total_startups:,}")
        c3.metric("Unicorns", total_unicorns)
        c4.metric("Total Funding ($B)", f"{total_funding:,}")

    elif mode == "Quantum Computing Centers":
        countries = len(set(d["country"] for d in data))
        max_qubits = max(d.get("qubits", 0) for d in data)
        types = len(set(d.get("type", "") for d in data))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("QC Centers", n)
        c2.metric("Countries", countries)
        c3.metric("Max Qubits", f"{max_qubits:,}")
        c4.metric("Qubit Types", types)

    elif mode == "Robot Museums & Exhibitions":
        countries = len(set(d["country"] for d in data))
        total_visitors = sum(d.get("visitors_k", 0) for d in data)
        types = len(set(d.get("type", "") for d in data))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Venues", n)
        c2.metric("Countries", countries)
        c3.metric("Annual Visitors (k)", f"{total_visitors:,}")
        c4.metric("Venue Types", types)

    else:
        st.metric("Locations", n)


# ---------------------------------------------------------------------------
# Popup fields per mode
# ---------------------------------------------------------------------------
def _get_popup_fields(mode: str, item: dict) -> dict:
    """Return ordered dict of label->value for popup display."""
    if mode == "AI Research Labs":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Parent Org": item.get("parent", ""),
            "Focus": item.get("focus", ""),
            "Founded": item.get("founded", ""),
            "Est. Staff": f"{item.get('staff_est', 0):,}",
            "Notable Work": item.get("notable", ""),
        }
    elif mode == "Robot Manufacturing Plants":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Company": item.get("company", ""),
            "Type": item.get("type", ""),
            "Cumul. Robots/yr": f"{item.get('robots_year', 0):,}",
            "Products": item.get("products", ""),
            "Founded": item.get("founded", ""),
        }
    elif mode == "Autonomous Vehicle Hubs":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Company": item.get("company", ""),
            "Focus": item.get("focus", ""),
            "Autonomy Level": item.get("level", ""),
            "Fleet Size": f"{item.get('fleet_size', 0):,}",
            "Test Miles (M)": item.get("test_miles_m", ""),
            "Status": item.get("status", ""),
        }
    elif mode == "Drone Innovation Centers":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Company": item.get("company", ""),
            "Focus": item.get("focus", ""),
            "Employees": f"{item.get('employees', 0):,}",
            "Founded": item.get("founded", ""),
            "Products": item.get("products", ""),
        }
    elif mode == "Space Robotics Facilities":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Agency": item.get("agency", ""),
            "Focus": item.get("focus", ""),
            "Notable": item.get("notable", ""),
            "Founded": item.get("founded", ""),
        }
    elif mode == "Medical Robotics Centers":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Company": item.get("company", ""),
            "Specialty": item.get("specialty", ""),
            "Products": item.get("products", ""),
            "Procedures (k)": f"{item.get('procedures_k', 0):,}",
            "Founded": item.get("founded", ""),
        }
    elif mode == "Industrial Automation Hubs":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Company": item.get("company", ""),
            "Focus": item.get("focus", ""),
            "Revenue ($B)": item.get("revenue_b", ""),
            "Employees": f"{item.get('employees', 0):,}",
            "Products": item.get("products", ""),
        }
    elif mode == "AI Startup Ecosystems":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "AI Startups": f"{item.get('ai_startups', 0):,}",
            "Unicorns": item.get("unicorns", ""),
            "Total Funding ($B)": item.get("total_funding_b", ""),
            "Key Players": item.get("key_players", ""),
            "Incubators": item.get("incubators", ""),
        }
    elif mode == "Quantum Computing Centers":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Organization": item.get("org", ""),
            "Qubits": f"{item.get('qubits', 0):,}",
            "Type": item.get("type", ""),
            "System": item.get("system", ""),
            "Founded": item.get("founded", ""),
        }
    elif mode == "Robot Museums & Exhibitions":
        return {
            "City": f"{item.get('city', '')}, {item.get('country', '')}",
            "Type": item.get("type", ""),
            "Highlights": item.get("highlights", ""),
            "Annual Visitors (k)": f"{item.get('visitors_k', 0):,}",
            "Opened": item.get("opened", ""),
        }
    else:
        return {k: v for k, v in item.items() if k not in ("lat", "lon")}


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================
def render_robot_maps_tab():
    """Render the Robotics & AI Centers Explorer tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        "<h4>Robotics & AI Centers Explorer</h4>"
        "<p>AI research labs, robot factories, automation hubs & tech innovation worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        list(MODE_DATA_MAP.keys()),
        key="robot_maps_mode",
    )

    data = MODE_DATA_MAP.get(mode, [])
    if not data:
        st.warning("No data available for this mode.")
        return

    _render_mode(mode, data)
