"""
Skyscraper & Tower Explorer module for TerraScout AI.
Displays curated collections of famous skyscrapers, supertall towers,
observation decks, historic buildings, and iconic skylines on interactive maps.
All data is preset — no external API key required.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import html as html_module
from streamlit.components.v1 import html as st_html

# ═══════════════════════════════════════════
# HEIGHT COLOR SCALE
# ═══════════════════════════════════════════
def _height_color(height_m: float) -> str:
    """Return a color based on building height."""
    if height_m >= 600:
        return "#ef4444"   # red — megatall
    elif height_m >= 450:
        return "#f97316"   # orange
    elif height_m >= 300:
        return "#f59e0b"   # amber — supertall
    elif height_m >= 200:
        return "#06b6d4"   # cyan
    elif height_m >= 100:
        return "#10b981"   # green
    return "#8b97b0"       # muted


# ═══════════════════════════════════════════
# PRESET DATA FOR EACH MODE
# ═══════════════════════════════════════════

def _worlds_tallest():
    """World's Tallest Buildings — the top iconic supertalls and megatalls."""
    return [
        {"name": "Burj Khalifa", "lat": 25.1972, "lon": 55.2744, "height_m": 828, "city": "Dubai, UAE", "year": 2010, "desc": "World's tallest building since 2010, 163 floors"},
        {"name": "Merdeka 118", "lat": 3.1416, "lon": 101.7007, "height_m": 679, "city": "Kuala Lumpur, Malaysia", "year": 2023, "desc": "Second tallest building in the world, 118 floors"},
        {"name": "Shanghai Tower", "lat": 31.2357, "lon": 121.5016, "height_m": 632, "city": "Shanghai, China", "year": 2015, "desc": "Tallest building in China, iconic twisted form"},
        {"name": "Abraj Al-Bait Clock Tower", "lat": 21.4189, "lon": 39.8263, "height_m": 601, "city": "Mecca, Saudi Arabia", "year": 2012, "desc": "Tallest clock tower, overlooking the Grand Mosque"},
        {"name": "Ping An Finance Centre", "lat": 22.5333, "lon": 114.0540, "height_m": 599, "city": "Shenzhen, China", "year": 2017, "desc": "Tallest building in Shenzhen, 115 floors"},
        {"name": "Lotte World Tower", "lat": 37.5126, "lon": 127.1026, "height_m": 555, "city": "Seoul, South Korea", "year": 2017, "desc": "Tallest building in South Korea, 123 floors"},
        {"name": "One World Trade Center", "lat": 40.7127, "lon": -74.0134, "height_m": 541, "city": "New York, USA", "year": 2014, "desc": "Tallest building in the Western Hemisphere"},
        {"name": "Guangzhou CTF Finance Centre", "lat": 23.1189, "lon": 113.3220, "height_m": 530, "city": "Guangzhou, China", "year": 2016, "desc": "Mixed-use supertall with world's fastest elevators"},
        {"name": "Taipei 101", "lat": 25.0340, "lon": 121.5645, "height_m": 508, "city": "Taipei, Taiwan", "year": 2004, "desc": "Former tallest building, iconic bamboo-inspired design"},
        {"name": "Shanghai World Financial Center", "lat": 31.2347, "lon": 121.5015, "height_m": 492, "city": "Shanghai, China", "year": 2008, "desc": "Distinctive bottle-opener aperture at summit"},
        {"name": "International Commerce Centre", "lat": 22.3033, "lon": 114.1603, "height_m": 484, "city": "Hong Kong, China", "year": 2010, "desc": "Tallest building in Hong Kong, houses Ritz-Carlton"},
        {"name": "Wuhan Greenland Center", "lat": 30.5679, "lon": 114.2826, "height_m": 476, "city": "Wuhan, China", "year": 2022, "desc": "Supertall in central China with aerodynamic design"},
    ]


def _supertall_300():
    """Supertall Skyscrapers — buildings exceeding 300 meters."""
    return [
        {"name": "Burj Khalifa", "lat": 25.1972, "lon": 55.2744, "height_m": 828, "city": "Dubai, UAE", "year": 2010, "desc": "World's tallest structure at 828m"},
        {"name": "Shanghai Tower", "lat": 31.2357, "lon": 121.5016, "height_m": 632, "city": "Shanghai, China", "year": 2015, "desc": "Twisting 632m tower with nine interior gardens"},
        {"name": "One World Trade Center", "lat": 40.7127, "lon": -74.0134, "height_m": 541, "city": "New York, USA", "year": 2014, "desc": "541m symbolic height for American independence year 1776 ft"},
        {"name": "Lotte World Tower", "lat": 37.5126, "lon": 127.1026, "height_m": 555, "city": "Seoul, South Korea", "year": 2017, "desc": "555m tower inspired by Korean ceramic art forms"},
        {"name": "Taipei 101", "lat": 25.0340, "lon": 121.5645, "height_m": 508, "city": "Taipei, Taiwan", "year": 2004, "desc": "508m pagoda-style tower with tuned mass damper"},
        {"name": "Willis Tower (Sears Tower)", "lat": 41.8789, "lon": -87.6359, "height_m": 442, "city": "Chicago, USA", "year": 1973, "desc": "442m bundled tube design, iconic Chicago landmark"},
        {"name": "Petronas Twin Towers", "lat": 3.1578, "lon": 101.7117, "height_m": 452, "city": "Kuala Lumpur, Malaysia", "year": 1998, "desc": "452m twin towers connected by sky bridge at 170m"},
        {"name": "Zifeng Tower", "lat": 32.0636, "lon": 118.7780, "height_m": 450, "city": "Nanjing, China", "year": 2010, "desc": "450m triangular profile supertall tower"},
        {"name": "432 Park Avenue", "lat": 40.7615, "lon": -73.9718, "height_m": 426, "city": "New York, USA", "year": 2015, "desc": "426m ultra-slim residential tower, slenderness ratio 15:1"},
        {"name": "Marina 101", "lat": 25.0930, "lon": 55.1471, "height_m": 425, "city": "Dubai, UAE", "year": 2017, "desc": "425m residential and hotel supertall in Dubai Marina"},
        {"name": "Princess Tower", "lat": 25.0919, "lon": 55.1458, "height_m": 414, "city": "Dubai, UAE", "year": 2012, "desc": "414m former world's tallest residential building"},
        {"name": "Al Hamra Tower", "lat": 29.3782, "lon": 47.9916, "height_m": 413, "city": "Kuwait City, Kuwait", "year": 2011, "desc": "413m sculpted asymmetric form, tallest carved tower"},
        {"name": "30 Hudson Yards", "lat": 40.7537, "lon": -74.0008, "height_m": 387, "city": "New York, USA", "year": 2019, "desc": "387m with outdoor observation deck 'Edge'"},
        {"name": "The Shard", "lat": 51.5045, "lon": -0.0865, "height_m": 310, "city": "London, UK", "year": 2012, "desc": "310m tallest building in the UK, glass spire design"},
        {"name": "Commerzbank Tower", "lat": 50.1094, "lon": 8.6717, "height_m": 300, "city": "Frankfurt, Germany", "year": 1997, "desc": "300m ecological skyscraper with sky gardens"},
    ]


def _historic_skyscrapers():
    """Historic Skyscrapers — pioneering buildings of the early skyscraper era."""
    return [
        {"name": "Empire State Building", "lat": 40.7484, "lon": -73.9857, "height_m": 443, "city": "New York, USA", "year": 1931, "desc": "Art Deco masterpiece, held tallest record for 40 years"},
        {"name": "Chrysler Building", "lat": 40.7516, "lon": -73.9755, "height_m": 319, "city": "New York, USA", "year": 1930, "desc": "Iconic Art Deco spire with eagle gargoyles"},
        {"name": "Woolworth Building", "lat": 40.7123, "lon": -74.0083, "height_m": 241, "city": "New York, USA", "year": 1913, "desc": "Neo-Gothic 'Cathedral of Commerce', tallest 1913-1930"},
        {"name": "Flatiron Building", "lat": 40.7411, "lon": -73.9897, "height_m": 87, "city": "New York, USA", "year": 1902, "desc": "Triangular Beaux-Arts landmark on Broadway and Fifth Ave"},
        {"name": "Tribune Tower", "lat": 41.8907, "lon": -87.6233, "height_m": 141, "city": "Chicago, USA", "year": 1925, "desc": "Neo-Gothic tower with stones from world landmarks embedded"},
        {"name": "Wrigley Building", "lat": 41.8896, "lon": -87.6247, "height_m": 130, "city": "Chicago, USA", "year": 1924, "desc": "White terra cotta tower inspired by Seville's Giralda"},
        {"name": "Terminal Tower", "lat": 41.4979, "lon": -81.6937, "height_m": 216, "city": "Cleveland, USA", "year": 1930, "desc": "Beaux-Arts landmark, tallest outside NYC until 1964"},
        {"name": "Palmolive Building", "lat": 41.9003, "lon": -87.6257, "height_m": 172, "city": "Chicago, USA", "year": 1929, "desc": "Art Deco tower with Lindbergh Beacon on top"},
        {"name": "Metropolitan Life Tower", "lat": 40.7418, "lon": -73.9876, "height_m": 213, "city": "New York, USA", "year": 1909, "desc": "Modeled after St Mark's Campanile in Venice"},
        {"name": "Singer Building (site)", "lat": 40.7094, "lon": -74.0066, "height_m": 187, "city": "New York, USA", "year": 1908, "desc": "Was world's tallest; demolished 1968 — tallest ever demolished at the time"},
        {"name": "30 St Mary Axe (The Gherkin)", "lat": 51.5145, "lon": -0.0803, "height_m": 180, "city": "London, UK", "year": 2004, "desc": "Norman Foster's iconic pickle-shaped London tower"},
        {"name": "Reliance Building", "lat": 41.8822, "lon": -87.6280, "height_m": 61, "city": "Chicago, USA", "year": 1895, "desc": "Proto-skyscraper, glass curtain wall pioneer"},
    ]


def _twisted_unique():
    """Twisted & Unique Towers — architecturally distinctive designs."""
    return [
        {"name": "Turning Torso", "lat": 55.6133, "lon": 12.9756, "height_m": 190, "city": "Malmo, Sweden", "year": 2005, "desc": "Santiago Calatrava's 90-degree twisting residential tower"},
        {"name": "Shanghai Tower (twist)", "lat": 31.2357, "lon": 121.5016, "height_m": 632, "city": "Shanghai, China", "year": 2015, "desc": "120-degree twist reduces wind load by 24 percent"},
        {"name": "Cayan Tower", "lat": 25.0770, "lon": 55.1340, "height_m": 307, "city": "Dubai, UAE", "year": 2013, "desc": "Full 90-degree twist, world's tallest twisted tower at completion"},
        {"name": "Evolution Tower", "lat": 55.7485, "lon": 37.5357, "height_m": 246, "city": "Moscow, Russia", "year": 2015, "desc": "DNA helix inspired 150-degree twist in Moscow City"},
        {"name": "Absolute World Towers", "lat": 43.5913, "lon": -79.6439, "height_m": 176, "city": "Mississauga, Canada", "year": 2012, "desc": "Nicknamed 'Marilyn Monroe towers' for their curves"},
        {"name": "F&F Tower (Revolution Tower)", "lat": 8.9843, "lon": -79.5172, "height_m": 233, "city": "Panama City, Panama", "year": 2011, "desc": "Dramatic screw-shaped twist in Panama's skyline"},
        {"name": "Capital Gate", "lat": 24.4216, "lon": 54.4344, "height_m": 160, "city": "Abu Dhabi, UAE", "year": 2011, "desc": "18-degree lean — world's furthest leaning man-made tower"},
        {"name": "Agora Garden (Tao Zhu Yin Yuan)", "lat": 25.0282, "lon": 121.5570, "height_m": 93, "city": "Taipei, Taiwan", "year": 2021, "desc": "Double-helix eco tower absorbing 130 tonnes of CO2/year"},
        {"name": "Mode Gakuen Cocoon Tower", "lat": 35.6905, "lon": 139.6953, "height_m": 204, "city": "Tokyo, Japan", "year": 2008, "desc": "Cocoon-shaped educational tower with diagonal lattice"},
        {"name": "Vessel (Hudson Yards)", "lat": 40.7536, "lon": -74.0022, "height_m": 46, "city": "New York, USA", "year": 2019, "desc": "Honeycomb structure with 154 interconnecting flights of stairs"},
        {"name": "Dancing House", "lat": 50.0755, "lon": 14.4148, "height_m": 43, "city": "Prague, Czech Republic", "year": 1996, "desc": "Frank Gehry's deconstructivist 'Fred and Ginger' building"},
        {"name": "Al Dar HQ (The Coin)", "lat": 24.4953, "lon": 54.3944, "height_m": 110, "city": "Abu Dhabi, UAE", "year": 2010, "desc": "World's first circular skyscraper, coin-shaped facade"},
    ]


def _observation_decks():
    """Observation Decks — highest public viewing platforms worldwide."""
    return [
        {"name": "Burj Khalifa - At the Top Sky", "lat": 25.1972, "lon": 55.2744, "height_m": 555, "city": "Dubai, UAE", "year": 2014, "desc": "Highest observation deck at 555m (148th floor)"},
        {"name": "Shanghai Tower - Top of Shanghai", "lat": 31.2357, "lon": 121.5016, "height_m": 562, "city": "Shanghai, China", "year": 2016, "desc": "World's highest observation deck at 562m, 121st floor"},
        {"name": "Ping An Finance Centre - Cloud 9", "lat": 22.5333, "lon": 114.0540, "height_m": 550, "city": "Shenzhen, China", "year": 2017, "desc": "Free Cloud platform at 550m on the 116th floor"},
        {"name": "Lotte World Tower - Seoul Sky", "lat": 37.5126, "lon": 127.1026, "height_m": 500, "city": "Seoul, South Korea", "year": 2017, "desc": "Seoul Sky at 500m with glass floor observation area"},
        {"name": "Canton Tower - Outdoor Deck", "lat": 23.1066, "lon": 113.3243, "height_m": 488, "city": "Guangzhou, China", "year": 2010, "desc": "Open-air deck at 488m with spider walk on exterior"},
        {"name": "One World Observatory", "lat": 40.7127, "lon": -74.0134, "height_m": 386, "city": "New York, USA", "year": 2015, "desc": "Immersive sky portal on 100-102 floors"},
        {"name": "CN Tower - Skypod", "lat": 43.6426, "lon": -79.3871, "height_m": 447, "city": "Toronto, Canada", "year": 1976, "desc": "447m Skypod with glass floor and EdgeWalk at 356m"},
        {"name": "Tokyo Skytree - Tembo Galleria", "lat": 35.7101, "lon": 139.8107, "height_m": 451, "city": "Tokyo, Japan", "year": 2012, "desc": "Tembo Galleria at 451m, spiral ramp viewing corridor"},
        {"name": "Empire State Building - 102nd Floor", "lat": 40.7484, "lon": -73.9857, "height_m": 381, "city": "New York, USA", "year": 1931, "desc": "Renovated 102nd floor enclosed glass observatory"},
        {"name": "The Edge (30 Hudson Yards)", "lat": 40.7537, "lon": -74.0008, "height_m": 335, "city": "New York, USA", "year": 2020, "desc": "Highest outdoor sky deck in Western Hemisphere, glass floor"},
        {"name": "The Shard - The View", "lat": 51.5045, "lon": -0.0865, "height_m": 244, "city": "London, UK", "year": 2013, "desc": "Open-air viewing gallery at 244m, 72nd floor"},
        {"name": "Taipei 101 Observatory", "lat": 25.0340, "lon": 121.5645, "height_m": 382, "city": "Taipei, Taiwan", "year": 2004, "desc": "Indoor and outdoor decks, view 730-tonne tuned mass damper"},
    ]


def _planned_megatall():
    """Planned Megatall Buildings — future supertalls and megatalls."""
    return [
        {"name": "Jeddah Tower", "lat": 22.7247, "lon": 39.0840, "height_m": 1000, "city": "Jeddah, Saudi Arabia", "year": 2028, "desc": "Planned 1km+ megatall, will be world's tallest if completed"},
        {"name": "Dubai Creek Tower", "lat": 25.1985, "lon": 55.3437, "height_m": 928, "city": "Dubai, UAE", "year": 2030, "desc": "Santiago Calatrava design inspired by a lily flower"},
        {"name": "Suzhou Zhongnan Center", "lat": 31.2957, "lon": 120.5853, "height_m": 729, "city": "Suzhou, China", "year": 2029, "desc": "Planned supertall to become tallest in Jiangsu province"},
        {"name": "Greenland Jinmao International Financial Center", "lat": 34.2601, "lon": 108.9428, "height_m": 500, "city": "Xi'an, China", "year": 2027, "desc": "500m tower planned for historic Xi'an skyline"},
        {"name": "PNB 118 (Merdeka 118 completed)", "lat": 3.1416, "lon": 101.7007, "height_m": 679, "city": "Kuala Lumpur, Malaysia", "year": 2023, "desc": "Recently completed 2nd tallest building in the world"},
        {"name": "Nakheel Tower (shelved)", "lat": 25.0890, "lon": 55.1500, "height_m": 1400, "city": "Dubai, UAE", "year": 0, "desc": "Proposed 1.4km tower, shelved after 2009 financial crisis"},
        {"name": "Sky Mile Tower (concept)", "lat": 35.6528, "lon": 139.8396, "height_m": 1600, "city": "Tokyo Bay, Japan", "year": 2045, "desc": "Conceptual 1.6km mega-structure for Tokyo Bay"},
        {"name": "Azerbaijan Tower (concept)", "lat": 40.4093, "lon": 49.8671, "height_m": 1050, "city": "Baku, Azerbaijan", "year": 0, "desc": "Proposed artificial island megatall, currently on hold"},
        {"name": "Bride Tower (concept)", "lat": 30.5079, "lon": 47.7835, "height_m": 1152, "city": "Basra, Iraq", "year": 0, "desc": "Concept for a 1,152m tower in southern Iraq"},
        {"name": "Burj Mubarak Al-Kabir", "lat": 29.2308, "lon": 48.0590, "height_m": 1001, "city": "Subiya, Kuwait", "year": 0, "desc": "Planned centerpiece of Madinat Al-Hareer, currently stalled"},
    ]


def _sky_bridges():
    """Sky Bridges & Skywalks — connected tower bridges and glass walkways."""
    return [
        {"name": "Petronas Towers Sky Bridge", "lat": 3.1578, "lon": 101.7117, "height_m": 170, "city": "Kuala Lumpur, Malaysia", "year": 1998, "desc": "Double-deck sky bridge at 170m connecting the twin towers"},
        {"name": "Sky Bridge 721", "lat": 50.2168, "lon": 16.9382, "height_m": 95, "city": "Dolni Morava, Czech Republic", "year": 2022, "desc": "World's longest suspension pedestrian bridge at 721m span"},
        {"name": "Raffles City Sky Bridge", "lat": 29.5518, "lon": 106.5734, "height_m": 250, "city": "Chongqing, China", "year": 2019, "desc": "Crystal sky bridge linking four towers, 300m horizontal span"},
        {"name": "SkyPark (Marina Bay Sands)", "lat": 1.2838, "lon": 103.8591, "height_m": 200, "city": "Singapore", "year": 2010, "desc": "340m-long rooftop spanning three 55-storey towers with infinity pool"},
        {"name": "Zhangjiajie Glass Bridge", "lat": 29.3468, "lon": 110.4341, "height_m": 260, "city": "Zhangjiajie, China", "year": 2016, "desc": "Glass-bottom bridge 260m above canyon, 430m long"},
        {"name": "Langkawi Sky Bridge", "lat": 6.3829, "lon": 99.6684, "height_m": 660, "city": "Langkawi, Malaysia", "year": 2005, "desc": "Curved pedestrian bridge 660m above sea level"},
        {"name": "Skyway at Linked Hybrid", "lat": 39.9826, "lon": 116.3749, "height_m": 66, "city": "Beijing, China", "year": 2009, "desc": "Steven Holl's eight sky bridges linking residential towers"},
        {"name": "Vessel (Hudson Yards)", "lat": 40.7536, "lon": -74.0022, "height_m": 46, "city": "New York, USA", "year": 2019, "desc": "154 interconnecting flights of stairs forming a honeycomb"},
        {"name": "Skywalk Grand Canyon", "lat": 36.0126, "lon": -113.8108, "height_m": 1219, "city": "Arizona, USA", "year": 2007, "desc": "Glass horseshoe over Grand Canyon, 1219m above river"},
        {"name": "Dare Skywalk (Blackpool Tower)", "lat": 53.8159, "lon": -3.0553, "height_m": 116, "city": "Blackpool, UK", "year": 2011, "desc": "Glass platform 116m above Blackpool promenade"},
        {"name": "Glacier Skywalk", "lat": 52.2173, "lon": -117.2226, "height_m": 280, "city": "Jasper, Canada", "year": 2014, "desc": "Glass-floored walkway 280m above Sunwapta Valley"},
    ]


def _tv_towers():
    """Iconic TV Towers — major broadcasting and communications towers."""
    return [
        {"name": "Tokyo Skytree", "lat": 35.7101, "lon": 139.8107, "height_m": 634, "city": "Tokyo, Japan", "year": 2012, "desc": "World's tallest tower (free-standing), broadcasting + tourism"},
        {"name": "CN Tower", "lat": 43.6426, "lon": -79.3871, "height_m": 553, "city": "Toronto, Canada", "year": 1976, "desc": "Iconic Canadian tower with revolving restaurant and EdgeWalk"},
        {"name": "Canton Tower", "lat": 23.1066, "lon": 113.3243, "height_m": 604, "city": "Guangzhou, China", "year": 2010, "desc": "Hyperboloid lattice tower with outdoor observation platforms"},
        {"name": "Ostankino Tower", "lat": 55.8197, "lon": 37.6117, "height_m": 540, "city": "Moscow, Russia", "year": 1967, "desc": "Tallest free-standing structure in Europe, broadcasting center"},
        {"name": "Oriental Pearl Tower", "lat": 31.2398, "lon": 121.4998, "height_m": 468, "city": "Shanghai, China", "year": 1994, "desc": "Iconic spheres design on Pudong waterfront"},
        {"name": "Milad Tower", "lat": 35.7448, "lon": 51.3753, "height_m": 435, "city": "Tehran, Iran", "year": 2008, "desc": "Tallest tower in Iran, multi-purpose head structure"},
        {"name": "Kuala Lumpur Tower (Menara KL)", "lat": 3.1529, "lon": 101.7038, "height_m": 421, "city": "Kuala Lumpur, Malaysia", "year": 1995, "desc": "Telecommunications tower with revolving restaurant"},
        {"name": "Tianjin Radio and TV Tower", "lat": 39.0835, "lon": 117.2096, "height_m": 415, "city": "Tianjin, China", "year": 1991, "desc": "Set in a lake, lakeside observation tower"},
        {"name": "Berlin TV Tower (Fernsehturm)", "lat": 52.5208, "lon": 13.4094, "height_m": 368, "city": "Berlin, Germany", "year": 1969, "desc": "Iconic Cold War-era symbol at Alexanderplatz"},
        {"name": "Sky Tower Auckland", "lat": -36.8485, "lon": 174.7622, "height_m": 328, "city": "Auckland, New Zealand", "year": 1997, "desc": "Tallest free-standing structure in Southern Hemisphere"},
        {"name": "Stratosphere Tower", "lat": 36.1474, "lon": -115.1566, "height_m": 350, "city": "Las Vegas, USA", "year": 1996, "desc": "Observation tower with thrill rides on the summit"},
        {"name": "Macau Tower", "lat": 22.1802, "lon": 113.5314, "height_m": 338, "city": "Macau, China", "year": 2001, "desc": "Home to world's highest commercial bungee jump at 233m"},
    ]


def _skyline_panoramas():
    """Skyline Panoramas — best city skyline viewpoints worldwide."""
    return [
        {"name": "Victoria Peak", "lat": 22.2759, "lon": 114.1455, "height_m": 552, "city": "Hong Kong, China", "year": 0, "desc": "Legendary panorama of Hong Kong harbor and Kowloon skyline"},
        {"name": "Top of the Rock", "lat": 40.7593, "lon": -73.9794, "height_m": 260, "city": "New York, USA", "year": 1933, "desc": "Unobstructed views of Central Park and Empire State Building"},
        {"name": "The Bund Waterfront", "lat": 31.2400, "lon": 121.4900, "height_m": 5, "city": "Shanghai, China", "year": 0, "desc": "Classic view of Pudong supertall cluster across Huangpu River"},
        {"name": "Marina Bay Promenade", "lat": 1.2816, "lon": 103.8636, "height_m": 5, "city": "Singapore", "year": 0, "desc": "Iconic view of Marina Bay Sands, CBD skyline and ArtScience Museum"},
        {"name": "Frying Pan Park (Rosslyn)", "lat": 38.8976, "lon": -77.0722, "height_m": 30, "city": "Washington D.C., USA", "year": 0, "desc": "DC skyline view with Washington Monument and Capitol dome"},
        {"name": "Seoul Tower (Namsan)", "lat": 37.5512, "lon": 126.9882, "height_m": 480, "city": "Seoul, South Korea", "year": 1975, "desc": "360-degree panorama of Seoul from Namsan Mountain summit"},
        {"name": "Corcovado (Christ the Redeemer)", "lat": -22.9519, "lon": -43.2105, "height_m": 710, "city": "Rio de Janeiro, Brazil", "year": 1931, "desc": "Iconic mountaintop view of Sugarloaf, Copacabana and Guanabara Bay"},
        {"name": "Montparnasse Tower", "lat": 48.8421, "lon": 2.3219, "height_m": 210, "city": "Paris, France", "year": 1973, "desc": "Best Eiffel Tower view — because you can't see Montparnasse from it"},
        {"name": "Galata Tower", "lat": 41.0256, "lon": 28.9741, "height_m": 63, "city": "Istanbul, Turkey", "year": 1348, "desc": "Medieval stone tower with 360-degree Bosphorus and Old City views"},
        {"name": "Sky Garden", "lat": 51.5113, "lon": -0.0836, "height_m": 155, "city": "London, UK", "year": 2015, "desc": "Free public garden at top of 20 Fenchurch St with Thames panorama"},
        {"name": "Lakhta Center Observation", "lat": 59.9868, "lon": 30.1778, "height_m": 360, "city": "Saint Petersburg, Russia", "year": 2019, "desc": "Europe's tallest building observation deck with Gulf of Finland views"},
        {"name": "Eureka Skydeck", "lat": -37.8217, "lon": 144.9644, "height_m": 285, "city": "Melbourne, Australia", "year": 2006, "desc": "The Edge glass cube extending from 285m over Melbourne"},
    ]


def _demolished_buildings():
    """Demolished Famous Buildings — notable structures that no longer exist."""
    return [
        {"name": "World Trade Center (Twin Towers)", "lat": 40.7116, "lon": -74.0132, "height_m": 417, "city": "New York, USA", "year": 1973, "desc": "Destroyed Sept 11, 2001. North Tower 417m, South Tower 415m. Were world's tallest 1970-1973"},
        {"name": "Singer Building", "lat": 40.7094, "lon": -74.0066, "height_m": 187, "city": "New York, USA", "year": 1908, "desc": "Demolished 1968 — tallest building ever peacefully demolished at the time"},
        {"name": "Morrison Hotel", "lat": 41.8811, "lon": -87.6320, "height_m": 160, "city": "Chicago, USA", "year": 1925, "desc": "Once world's largest hotel with 3,400 rooms, demolished 1965"},
        {"name": "Penn Station (original)", "lat": 40.7506, "lon": -73.9935, "height_m": 46, "city": "New York, USA", "year": 1910, "desc": "McKim Mead & White Beaux-Arts masterpiece, demolished 1963. Sparked preservation movement"},
        {"name": "Crystal Palace", "lat": 51.4217, "lon": -0.0755, "height_m": 39, "city": "London, UK", "year": 1851, "desc": "Joseph Paxton's iron and glass exhibition hall, destroyed by fire 1936"},
        {"name": "Pruitt-Igoe Housing", "lat": 38.6396, "lon": -90.2101, "height_m": 40, "city": "St Louis, USA", "year": 1954, "desc": "Modernist housing project, dynamited 1972. Symbol of failed urban planning"},
        {"name": "Deutsche Bank Building", "lat": 40.7103, "lon": -74.0113, "height_m": 158, "city": "New York, USA", "year": 1974, "desc": "Severely damaged on 9/11, deconstructed 2007-2011"},
        {"name": "Kowloon Walled City", "lat": 22.3318, "lon": 114.1893, "height_m": 40, "city": "Hong Kong, China", "year": 1950, "desc": "World's densest settlement, 50,000 people in 0.026 km2, demolished 1993-1994"},
        {"name": "Robin Hood Gardens", "lat": 51.5082, "lon": 0.0046, "height_m": 30, "city": "London, UK", "year": 1972, "desc": "Brutalist housing by Alison & Peter Smithson, demolished 2017-2024"},
        {"name": "Larkin Administration Building", "lat": 42.8802, "lon": -78.8544, "height_m": 25, "city": "Buffalo, USA", "year": 1904, "desc": "Frank Lloyd Wright office masterpiece, demolished 1950"},
    ]


# ═══════════════════════════════════════════
# MODE REGISTRY
# ═══════════════════════════════════════════

MODES = {
    "World's Tallest Buildings": {
        "fn": _worlds_tallest,
        "icon": "building",
        "zoom": 2,
        "center": [25.0, 55.0],
        "desc": "The world's tallest skyscrapers and megatall towers",
    },
    "Supertall Skyscrapers (300m+)": {
        "fn": _supertall_300,
        "icon": "building",
        "zoom": 2,
        "center": [30.0, 50.0],
        "desc": "Every building exceeding 300 meters in height",
    },
    "Historic Skyscrapers": {
        "fn": _historic_skyscrapers,
        "icon": "home",
        "zoom": 3,
        "center": [40.7, -74.0],
        "desc": "Pioneering early skyscrapers and Art Deco towers",
    },
    "Twisted & Unique Towers": {
        "fn": _twisted_unique,
        "icon": "refresh",
        "zoom": 2,
        "center": [30.0, 50.0],
        "desc": "Architecturally distinctive twisting and sculptural designs",
    },
    "Observation Decks": {
        "fn": _observation_decks,
        "icon": "eye-open",
        "zoom": 2,
        "center": [30.0, 50.0],
        "desc": "Highest public viewing platforms and sky observatories",
    },
    "Planned Megatall Buildings": {
        "fn": _planned_megatall,
        "icon": "cloud",
        "zoom": 2,
        "center": [25.0, 50.0],
        "desc": "Future supertalls and megatalls — proposed, under construction, or stalled",
    },
    "Sky Bridges & Skywalks": {
        "fn": _sky_bridges,
        "icon": "road",
        "zoom": 2,
        "center": [20.0, 100.0],
        "desc": "Connected tower bridges, glass walkways, and suspended platforms",
    },
    "Iconic TV Towers": {
        "fn": _tv_towers,
        "icon": "signal",
        "zoom": 2,
        "center": [35.0, 100.0],
        "desc": "Major broadcasting and communications towers worldwide",
    },
    "Skyline Panoramas": {
        "fn": _skyline_panoramas,
        "icon": "picture",
        "zoom": 2,
        "center": [25.0, 50.0],
        "desc": "Best city skyline viewpoints and panoramic observation spots",
    },
    "Demolished Famous Buildings": {
        "fn": _demolished_buildings,
        "icon": "remove",
        "zoom": 3,
        "center": [40.7, -74.0],
        "desc": "Notable structures that have been demolished or destroyed",
    },
}


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════

def render_skyscraper_maps_tab():
    """Main render function for the Skyscraper & Tower Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>\U0001f3d9\ufe0f Skyscraper & Tower Explorer</h4>
        <p>Explore the world's tallest, most iconic, and architecturally stunning towers &mdash; curated collections on interactive dark maps.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    mode = st.selectbox(
        "Map Mode",
        list(MODES.keys()),
        key="sky_mode",
        help="Choose a curated collection of skyscrapers and towers to explore",
    )

    mode_cfg = MODES[mode]
    data = mode_cfg["fn"]()

    if not data:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 2: Stats Dashboard
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {html_module.escape(mode)}")

    heights = [b["height_m"] for b in data if b.get("height_m", 0) > 0]
    years = [b["year"] for b in data if b.get("year", 0) > 0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Buildings", f"{len(data)}")
    with c2:
        st.metric("Tallest", f"{max(heights):,}m" if heights else "\u2014")
    with c3:
        avg_h = int(sum(heights) / len(heights)) if heights else 0
        st.metric("Avg Height", f"{avg_h:,}m" if heights else "\u2014")
    with c4:
        if years:
            st.metric("Year Range", f"{min(years)}\u2013{max(years)}")
        else:
            st.metric("Year Range", "\u2014")

    # ══════════════════════════════════════════
    # SECTION 3: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")

    # Height legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf 600m+ Megatall</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf 450\u2013600m</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf 300\u2013450m Supertall</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf 200\u2013300m</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf 100\u2013200m</span>
        <span style="color:#8b97b0; font-size:0.8rem;">\u25cf &lt;100m</span>
    </div>
    """, unsafe_allow_html=True)

    m = folium.Map(
        location=mode_cfg["center"],
        zoom_start=mode_cfg["zoom"],
        tiles="CartoDB dark_matter",
    )

    marker_cluster = MarkerCluster(
        options={"maxClusterRadius": 35, "disableClusteringAtZoom": 6}
    ).add_to(m)

    for bld in data:
        lat = bld["lat"]
        lon = bld["lon"]
        name = html_module.escape(bld["name"])
        desc = html_module.escape(bld.get("desc", ""))
        city = html_module.escape(bld.get("city", ""))
        height = bld.get("height_m", 0)
        year = bld.get("year", 0)
        color = _height_color(height)

        year_str = str(year) if year > 0 else "Planned / Concept"
        height_str = f"{height:,}m" if height > 0 else "N/A"

        popup_html = f"""
        <div style="max-width:240px; font-family:sans-serif;">
            <strong style="font-size:0.95rem;">{name}</strong><br/>
            <span style="font-size:0.8rem; color:#666;">{city}</span><br/>
            <span style="font-size:0.85rem;"><b>Height:</b> {height_str}</span><br/>
            <span style="font-size:0.85rem;"><b>Year:</b> {year_str}</span><br/>
            <span style="font-size:0.8rem; color:#555;">{desc}</span>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=max(5, min(14, height / 60)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{name} ({height_str})",
        ).add_to(marker_cluster)

    st_html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 4: Building Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Building Details")

    # Sort by height descending
    sorted_data = sorted(data, key=lambda x: x.get("height_m", 0), reverse=True)

    for bld in sorted_data[:15]:
        name = html_module.escape(bld["name"])
        desc = html_module.escape(bld.get("desc", ""))
        city = html_module.escape(bld.get("city", ""))
        height = bld.get("height_m", 0)
        year = bld.get("year", 0)
        color = _height_color(height)
        height_str = f"{height:,}m" if height > 0 else "N/A"
        year_str = str(year) if year > 0 else "Planned"

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:54px; height:54px; border-radius:50%; background:{color}20;
                        display:flex; align-items:center; justify-content:center;
                        margin-right:0.75rem; flex-shrink:0;">
                <span style="color:{color}; font-weight:800; font-size:0.8rem;">{height_str}</span>
            </div>
            <div>
                <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{name}</div>
                <div style="color:#8b97b0; font-size:0.75rem;">{city} &middot; {year_str}</div>
                <div style="color:#5a6580; font-size:0.7rem;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 5: Data Table & Download
    # ══════════════════════════════════════════
    st.markdown("---")

    rows = []
    for bld in sorted_data:
        rows.append({
            "name": bld["name"],
            "city": bld.get("city", ""),
            "height_m": bld.get("height_m", 0),
            "year": bld.get("year", 0) if bld.get("year", 0) > 0 else None,
            "latitude": bld["lat"],
            "longitude": bld["lon"],
            "description": bld.get("desc", ""),
        })

    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)

    safe_mode = mode.replace(" ", "_").replace("'", "").replace("(", "").replace(")", "").replace("+", "plus").lower()
    st.download_button(
        f"Download {len(rows)} Buildings (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"skyscrapers_{safe_mode}.csv",
        mime="text/csv",
        key="sky_download",
    )
