"""
Telescope & Observatory Explorer module for TerraScout AI.
Preset-based explorer for the world's greatest telescopes, observatories,
radio arrays, space telescope ground control, dark sky preserves, and more.
No API key required -- all data is curated and embedded.
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
import requests
import html as html_module
import streamlit.components.v1 as components

# ═══════════════════════════════════════════
# MODE COLORS & ICONS
# ═══════════════════════════════════════════
MODE_COLORS = {
    "World's Greatest Telescopes": "#06b6d4",
    "Radio Telescopes": "#8b5cf6",
    "Space Telescope Ground Control": "#3b82f6",
    "Historic Observatories": "#f59e0b",
    "Next Generation Telescopes": "#10b981",
    "Dark Sky Preserves": "#1e293b",
    "Planetariums & Science Centers": "#ec4899",
    "Meteorite Impact Observatories": "#ef4444",
    "Gravitational Wave Detectors": "#a855f7",
    "Solar Observatories": "#f97316",
}

# ═══════════════════════════════════════════
# PRESET DATA — 10 CATEGORIES
# ═══════════════════════════════════════════

WORLDS_GREATEST_TELESCOPES = [
    {"name": "W. M. Keck Observatory", "lat": 19.8264, "lon": -155.4744,
     "desc": "Twin 10m segmented mirrors atop Mauna Kea, Hawaii. Among the world's most scientifically productive telescopes."},
    {"name": "Very Large Telescope (VLT)", "lat": -24.6275, "lon": -70.4042,
     "desc": "ESO's flagship: four 8.2m Unit Telescopes on Cerro Paranal, Chile. Interferometric mode combines all four."},
    {"name": "Hubble Space Telescope Ground Support (Goddard)", "lat": 38.9955, "lon": -76.8525,
     "desc": "NASA Goddard Space Flight Center, Greenbelt MD. Primary ground control & science operations for HST."},
    {"name": "Subaru Telescope", "lat": 19.8255, "lon": -155.4761,
     "desc": "NAOJ 8.2m optical-infrared telescope on Mauna Kea with Hyper Suprime-Cam wide-field imager."},
    {"name": "Gemini North", "lat": 19.8238, "lon": -155.4690,
     "desc": "One of the twin 8.1m Gemini telescopes on Mauna Kea, Hawaii. Optimized for infrared observations."},
    {"name": "Gemini South", "lat": -30.2407, "lon": -70.7366,
     "desc": "Southern twin 8.1m Gemini telescope on Cerro Pachon, Chile. Full-sky coverage with Gemini North."},
    {"name": "Gran Telescopio Canarias (GTC)", "lat": 28.7567, "lon": -17.8920,
     "desc": "10.4m segmented mirror on La Palma, Canary Islands. Currently the world's largest single-aperture optical telescope."},
    {"name": "Large Binocular Telescope (LBT)", "lat": 32.7013, "lon": -109.8891,
     "desc": "Twin 8.4m mirrors on Mt. Graham, Arizona. Combined light-gathering equivalent to an 11.8m telescope."},
    {"name": "Southern African Large Telescope (SALT)", "lat": -32.3758, "lon": 20.8107,
     "desc": "11m segmented primary mirror in Sutherland, South Africa. Largest optical telescope in the Southern Hemisphere."},
    {"name": "Magellan Telescopes (Baade & Clay)", "lat": -29.0146, "lon": -70.6926,
     "desc": "Twin 6.5m telescopes at Las Campanas Observatory, Chile. Carnegie Institution flagships."},
]

RADIO_TELESCOPES = [
    {"name": "Arecibo Observatory (collapsed 2020)", "lat": 18.3464, "lon": -66.7528,
     "desc": "Iconic 305m dish in Puerto Rico. Collapsed Dec 2020 after cable failures. Operated 1963-2020."},
    {"name": "FAST (Five-hundred-meter Aperture Spherical Telescope)", "lat": 25.6529, "lon": 106.8566,
     "desc": "World's largest single-dish radio telescope (500m) in Guizhou, China. Operational since 2020."},
    {"name": "Karl G. Jansky Very Large Array (VLA)", "lat": 34.0784, "lon": -107.6184,
     "desc": "27 x 25m dishes in Y-configuration on the Plains of San Agustin, New Mexico. NRAO flagship."},
    {"name": "Atacama Large Millimeter Array (ALMA)", "lat": -23.0193, "lon": -67.7532,
     "desc": "66 high-precision antennas at 5,000m altitude in the Chilean Andes. Premier mm/sub-mm interferometer."},
    {"name": "Square Kilometre Array (SKA) - South Africa", "lat": -30.7215, "lon": 21.4107,
     "desc": "SKA-Mid site in the Karoo, South Africa. 197 dishes for mid-frequency radio astronomy. Under construction."},
    {"name": "Square Kilometre Array (SKA) - Australia", "lat": -26.6970, "lon": 116.6310,
     "desc": "SKA-Low site in Western Australia. 131,072 low-frequency antennas. Under construction."},
    {"name": "Jodrell Bank Observatory", "lat": 53.2367, "lon": -2.3085,
     "desc": "Home of the 76m Lovell Telescope near Manchester, UK. UNESCO World Heritage Site since 2019."},
    {"name": "Parkes Observatory (Murriyang)", "lat": -32.9984, "lon": 148.2636,
     "desc": "64m dish in New South Wales, Australia. Received Apollo 11 TV signals. Now CSIRO's Murriyang."},
    {"name": "Green Bank Observatory", "lat": 38.4330, "lon": -79.8397,
     "desc": "100m Green Bank Telescope (GBT), the world's largest fully steerable radio dish. West Virginia."},
    {"name": "Effelsberg Radio Telescope", "lat": 50.5247, "lon": 6.8836,
     "desc": "100m dish near Bonn, Germany. Max Planck Institute. One of the largest fully steerable radio telescopes."},
]

SPACE_TELESCOPE_GROUND_CONTROL = [
    {"name": "James Webb Space Telescope MOC (STScI)", "lat": 39.3319, "lon": -76.6227,
     "desc": "Space Telescope Science Institute, Baltimore MD. Mission Operations Center for JWST and HST science."},
    {"name": "JWST Mission Operations (Goddard)", "lat": 38.9955, "lon": -76.8525,
     "desc": "NASA Goddard Space Flight Center, Greenbelt MD. Flight operations and engineering for JWST."},
    {"name": "Hubble Control Center (Goddard)", "lat": 38.9970, "lon": -76.8520,
     "desc": "Hubble Space Telescope flight operations at Goddard. Manages spacecraft health and commanding."},
    {"name": "Chandra X-ray Center (CXC)", "lat": 42.3814, "lon": -71.1281,
     "desc": "Smithsonian Astrophysical Observatory, Cambridge MA. Operations center for Chandra X-ray Observatory."},
    {"name": "Spitzer Science Center (IPAC/Caltech)", "lat": 34.1375, "lon": -118.1256,
     "desc": "IPAC at Caltech, Pasadena CA. Managed Spitzer Space Telescope operations (2003-2020). Now IRSA."},
    {"name": "ESA ESOC - Mission Control", "lat": 49.8706, "lon": 8.6261,
     "desc": "European Space Operations Centre, Darmstadt, Germany. Controls XMM-Newton, Gaia, and other ESA missions."},
    {"name": "ESA ESAC - Science Archive", "lat": 40.4444, "lon": -3.9528,
     "desc": "European Space Astronomy Centre near Madrid, Spain. Science operations for Gaia, XMM-Newton, Euclid."},
    {"name": "NASA Deep Space Network - Goldstone", "lat": 35.4267, "lon": -116.8900,
     "desc": "DSN complex in the Mojave Desert, CA. Communicates with interplanetary spacecraft including JWST."},
    {"name": "NASA Deep Space Network - Canberra", "lat": -35.4014, "lon": 148.9817,
     "desc": "DSN Canberra complex near Tidbinbilla, Australia. Provides 24/7 spacecraft communication coverage."},
    {"name": "NASA Deep Space Network - Madrid", "lat": 40.4314, "lon": -4.2481,
     "desc": "DSN Robledo complex near Madrid, Spain. Third node of the global Deep Space Network."},
]

HISTORIC_OBSERVATORIES = [
    {"name": "Royal Observatory Greenwich", "lat": 51.4769, "lon": -0.0005,
     "desc": "Established 1675 by Charles II. Home of the Prime Meridian and Greenwich Mean Time. Now a museum."},
    {"name": "Pulkovo Observatory", "lat": 59.7716, "lon": 30.3264,
     "desc": "Founded 1839 near St. Petersburg, Russia. Principal observatory of the Russian Academy of Sciences."},
    {"name": "Mount Wilson Observatory", "lat": 34.2258, "lon": -118.0573,
     "desc": "100-inch Hooker Telescope (1917-1992 as primary). Where Hubble proved galaxies exist beyond the Milky Way."},
    {"name": "Lick Observatory", "lat": 37.3414, "lon": -121.6429,
     "desc": "Founded 1888 on Mount Hamilton, California. First permanently occupied mountaintop observatory."},
    {"name": "Yerkes Observatory", "lat": 42.5703, "lon": -88.5561,
     "desc": "Home of the 40-inch refractor (1897), the largest refracting telescope ever used for research. Williams Bay, WI."},
    {"name": "Paris Observatory", "lat": 48.8362, "lon": 2.3365,
     "desc": "Founded 1667, the oldest working observatory in the world. Avenue de l'Observatoire, Paris."},
    {"name": "Vatican Observatory (Castel Gandolfo)", "lat": 41.7469, "lon": 12.6510,
     "desc": "Papal observatory founded 1891. Research group now based at Vatican Advanced Technology Telescope, Arizona."},
    {"name": "Leiden Observatory", "lat": 52.1544, "lon": 4.4833,
     "desc": "Founded 1633 at Leiden University, Netherlands. One of the oldest university observatories still active."},
    {"name": "Berlin Observatory (historic site)", "lat": 52.5133, "lon": 13.3928,
     "desc": "Founded 1700. Where Neptune was first observed by Galle in 1846 from Le Verrier's predictions."},
    {"name": "Lowell Observatory", "lat": 35.2029, "lon": -111.6646,
     "desc": "Flagstaff, Arizona. Founded 1894 by Percival Lowell. Pluto was discovered here in 1930 by Clyde Tombaugh."},
]

NEXT_GENERATION_TELESCOPES = [
    {"name": "Extremely Large Telescope (ELT)", "lat": -24.5893, "lon": -70.1916,
     "desc": "ESO's 39m behemoth on Cerro Armazones, Chile. First light expected ~2028. Will be the world's largest optical telescope."},
    {"name": "Thirty Meter Telescope (TMT)", "lat": 19.8283, "lon": -155.4722,
     "desc": "Planned 30m segmented mirror on Mauna Kea, Hawaii. International collaboration. Site controversy ongoing."},
    {"name": "Giant Magellan Telescope (GMT)", "lat": -29.0400, "lon": -70.6919,
     "desc": "Seven 8.4m mirrors (24.5m equivalent) at Las Campanas, Chile. Under construction, first light ~2029."},
    {"name": "Vera C. Rubin Observatory (LSST)", "lat": -30.2444, "lon": -70.7494,
     "desc": "8.4m survey telescope on Cerro Pachon, Chile. Will image the entire visible sky every few nights."},
    {"name": "Nancy Grace Roman Space Telescope (ops at Goddard)", "lat": 38.9955, "lon": -76.8525,
     "desc": "NASA's next flagship space telescope. 2.4m mirror with wide-field infrared instrument. Launch planned ~2027."},
    {"name": "DKIST - Daniel K. Inouye Solar Telescope", "lat": 20.7067, "lon": -156.2564,
     "desc": "4m solar telescope on Haleakala, Maui. The world's largest solar telescope. Operational since 2022."},
    {"name": "SKA Observatory Headquarters", "lat": 53.2343, "lon": -2.3072,
     "desc": "Jodrell Bank, UK. HQ for the Square Kilometre Array project, the world's largest radio telescope."},
    {"name": "Cherenkov Telescope Array (CTA) - North", "lat": 28.7622, "lon": -17.8906,
     "desc": "La Palma, Canary Islands. Northern CTA site for very-high-energy gamma-ray astronomy."},
    {"name": "Cherenkov Telescope Array (CTA) - South", "lat": -24.6833, "lon": -70.3167,
     "desc": "Cerro Paranal, Chile. Southern CTA site with dozens of telescopes. Under construction."},
    {"name": "European Solar Telescope (EST)", "lat": 28.7586, "lon": -17.8814,
     "desc": "Planned 4.2m solar telescope for La Palma, Canary Islands. European next-gen solar physics facility."},
]

DARK_SKY_PRESERVES = [
    {"name": "Natural Bridges National Monument", "lat": 37.6088, "lon": -110.0015,
     "desc": "Utah, USA. First International Dark Sky Park (2007). Bortle Class 2 skies. Stunning Milky Way views."},
    {"name": "NamibRand Nature Reserve", "lat": -24.9000, "lon": 15.9500,
     "desc": "Namibia. Africa's first International Dark Sky Reserve. One of the darkest places on Earth."},
    {"name": "Aoraki Mackenzie International Dark Sky Reserve", "lat": -43.8860, "lon": 170.5028,
     "desc": "New Zealand. Gold-tier Dark Sky Reserve. Mt. John Observatory sits within. Southern Hemisphere showpiece."},
    {"name": "Brecon Beacons (Bannau Brycheiniog)", "lat": 51.8833, "lon": -3.4333,
     "desc": "Wales, UK. International Dark Sky Reserve. One of the best stargazing sites in the British Isles."},
    {"name": "Kerry International Dark Sky Reserve", "lat": 51.7667, "lon": -10.1000,
     "desc": "County Kerry, Ireland. Gold-tier Dark Sky Reserve on the Iveragh Peninsula. Pristine Atlantic skies."},
    {"name": "Jasper National Park Dark Sky Preserve", "lat": 52.8734, "lon": -117.8035,
     "desc": "Alberta, Canada. Largest accessible Dark Sky Preserve in the world (11,228 km2)."},
    {"name": "Pic du Midi International Dark Sky Reserve", "lat": 42.9372, "lon": 0.1411,
     "desc": "French Pyrenees. Home to a historic high-altitude observatory and exceptional dark skies."},
    {"name": "Zselic Starry Sky Park", "lat": 46.2667, "lon": 17.6833,
     "desc": "Hungary. One of Europe's first International Dark Sky Parks. Educational facility on site."},
    {"name": "Galloway Forest Dark Sky Park", "lat": 55.1000, "lon": -4.5000,
     "desc": "Scotland, UK. First Dark Sky Park in the UK. Bortle Class 2-3 skies in the Southern Uplands."},
    {"name": "Atacama Desert (ALMA region)", "lat": -23.0193, "lon": -67.7532,
     "desc": "Northern Chile. Among the driest, darkest skies on Earth. Home to many world-class observatories."},
    {"name": "Mauna Kea Summit Area", "lat": 19.8207, "lon": -155.4681,
     "desc": "Hawaii, USA. 4,205m altitude with exceptionally stable, dark, dry skies. Premier telescope site."},
    {"name": "Big Bend National Park", "lat": 29.2500, "lon": -103.2500,
     "desc": "Texas, USA. International Dark Sky Park. Some of the darkest skies in North America."},
]

PLANETARIUMS_SCIENCE_CENTERS = [
    {"name": "Hayden Planetarium (AMNH)", "lat": 40.7812, "lon": -73.9735,
     "desc": "American Museum of Natural History, New York City. Iconic 26m dome with Zeiss projector."},
    {"name": "Adler Planetarium", "lat": 41.8663, "lon": -87.6068,
     "desc": "Chicago, Illinois. America's first planetarium (1930). On the shores of Lake Michigan."},
    {"name": "Griffith Observatory", "lat": 34.1184, "lon": -118.3004,
     "desc": "Los Angeles, California. Free-admission icon overlooking Hollywood. Zeiss projector and public telescopes."},
    {"name": "National Air and Space Museum", "lat": 38.8882, "lon": -77.0199,
     "desc": "Smithsonian, Washington DC. Albert Einstein Planetarium and spaceflight artifact collection."},
    {"name": "Planetario di Milano", "lat": 45.4735, "lon": 9.1972,
     "desc": "Italy's largest planetarium in the Giardini Indro Montanelli, Milan. Built 1930."},
    {"name": "Cite de l'Espace", "lat": 43.5867, "lon": 1.4914,
     "desc": "Toulouse, France. Space science center with planetarium, IMAX dome, and full-scale Ariane 5 rocket."},
    {"name": "Deutsches Museum Planetarium", "lat": 48.1299, "lon": 11.5833,
     "desc": "Munich, Germany. One of the oldest planetariums in the world, inside the Deutsches Museum."},
    {"name": "Beijing Planetarium", "lat": 39.9369, "lon": 116.3476,
     "desc": "China's first planetarium (1957). Expanded with new dome theater. Major public astronomy hub in Beijing."},
    {"name": "Nehru Planetarium (Delhi)", "lat": 28.6014, "lon": 77.2089,
     "desc": "Teen Murti Estate, New Delhi, India. One of five Nehru Planetariums across India."},
    {"name": "Melbourne Planetarium (Scienceworks)", "lat": -37.8244, "lon": 144.8998,
     "desc": "Museums Victoria, Melbourne, Australia. Digital fulldome theater with southern sky programs."},
    {"name": "Cosmonaut Training Center (Star City)", "lat": 55.8797, "lon": 38.1175,
     "desc": "Zvyozdny Gorodok, Russia. Yuri Gagarin Cosmonaut Training Center. Where cosmonauts train for space."},
    {"name": "H.R. MacMillan Space Centre", "lat": 49.2764, "lon": -123.1444,
     "desc": "Vancouver, Canada. Planetarium and space science center in Vanier Park."},
]

METEORITE_IMPACT_OBSERVATORIES = [
    {"name": "Barringer Meteor Crater", "lat": 35.0278, "lon": -111.0225,
     "desc": "Arizona, USA. 1.2 km diameter, ~50,000 years old. Best-preserved impact crater on Earth. Visitor center."},
    {"name": "Sudbury Basin", "lat": 46.6000, "lon": -81.1833,
     "desc": "Ontario, Canada. 1.85 Ga impact structure, ~130 km. Second-largest confirmed impact on Earth. Rich nickel ores."},
    {"name": "Chicxulub Crater (center)", "lat": 21.3983, "lon": -89.5167,
     "desc": "Yucatan, Mexico. ~180 km diameter, ~66 Ma. The K-Pg extinction event impact. Buried under sediment."},
    {"name": "Wolfe Creek Crater", "lat": -19.1725, "lon": 127.7975,
     "desc": "Western Australia. ~880m diameter, ~120,000 years old. Well-preserved, sacred to Djaru people."},
    {"name": "Vredefort Crater", "lat": -27.0000, "lon": 27.5000,
     "desc": "South Africa. ~300 km original diameter, ~2.02 Ga. Largest verified impact structure on Earth. UNESCO site."},
    {"name": "Nördlinger Ries", "lat": 48.8500, "lon": 10.6167,
     "desc": "Bavaria, Germany. ~24 km diameter, ~14.8 Ma. Town of Nordlingen built inside the crater. Suevite rock."},
    {"name": "Manicouagan Reservoir", "lat": 51.3833, "lon": -68.7000,
     "desc": "Quebec, Canada. ~100 km, ~214 Ma. 'Eye of Quebec' visible from space. Ring-shaped hydroelectric reservoir."},
    {"name": "Popigai Crater", "lat": 71.6500, "lon": 111.6500,
     "desc": "Siberia, Russia. ~100 km diameter, ~35.7 Ma. Contains impact diamonds. One of the largest confirmed craters."},
    {"name": "Chesapeake Bay Impact Crater", "lat": 37.2833, "lon": -76.0333,
     "desc": "Virginia, USA. ~85 km diameter, ~35 Ma. Buried beneath Chesapeake Bay. Discovered 1983."},
    {"name": "Kaali Crater Field", "lat": 58.3742, "lon": 22.6692,
     "desc": "Saaremaa Island, Estonia. Group of 9 meteorite craters. Main crater ~110m. Impact ~1500-400 BC."},
]

GRAVITATIONAL_WAVE_DETECTORS = [
    {"name": "LIGO Hanford Observatory", "lat": 46.4551, "lon": -119.4076,
     "desc": "Richland, Washington. One of twin LIGO detectors with 4 km arms. First detection of gravitational waves (2015)."},
    {"name": "LIGO Livingston Observatory", "lat": 30.5629, "lon": -90.7742,
     "desc": "Livingston, Louisiana. Second LIGO detector, 4 km arms. Together with Hanford, enables sky localization."},
    {"name": "Virgo Interferometer", "lat": 43.6314, "lon": 10.5045,
     "desc": "Cascina near Pisa, Italy. European gravitational wave detector with 3 km arms. EGO collaboration."},
    {"name": "KAGRA (Kamioka)", "lat": 36.4133, "lon": 137.3100,
     "desc": "Kamioka mine, Gifu Prefecture, Japan. Underground cryogenic detector with 3 km arms. First underground GW detector."},
    {"name": "GEO600", "lat": 52.2464, "lon": 9.8083,
     "desc": "Near Hanover, Germany. 600m arm interferometer. Technology testbed for advanced GW detector techniques."},
    {"name": "LIGO India (proposed site)", "lat": 19.6133, "lon": 74.0569,
     "desc": "Aundha, Maharashtra, India. Planned third LIGO detector. Will greatly improve sky localization of GW events."},
    {"name": "Einstein Telescope (proposed - Sardinia)", "lat": 40.4333, "lon": 9.4500,
     "desc": "Sos Enattos mine, Sardinia, Italy. Candidate site for the underground next-gen European GW observatory."},
    {"name": "Einstein Telescope (proposed - Meuse-Rhine)", "lat": 50.7167, "lon": 5.9167,
     "desc": "Border of Netherlands, Belgium, Germany. Second candidate site for the Einstein Telescope. Deep underground."},
    {"name": "Cosmic Explorer (proposed - concept)", "lat": 35.0000, "lon": -107.0000,
     "desc": "Proposed next-gen US detector with 40 km arms. Concept stage. Would detect GW sources across the observable universe."},
    {"name": "NANOGrav (Arecibo legacy + GBT)", "lat": 38.4330, "lon": -79.8397,
     "desc": "Pulsar Timing Array using GBT and other radio telescopes. Detected nanohertz gravitational wave background in 2023."},
]

SOLAR_OBSERVATORIES = [
    {"name": "Sacramento Peak / Sunspot Observatory", "lat": 32.7872, "lon": -105.8203,
     "desc": "Sunspot, New Mexico. NSO facility with Dunn Solar Telescope. High-altitude solar research since 1947."},
    {"name": "Big Bear Solar Observatory", "lat": 34.2583, "lon": -116.9225,
     "desc": "Big Bear Lake, California. NJIT's 1.6m New Solar Telescope on an island for seeing stability."},
    {"name": "Teide Observatory", "lat": 28.3000, "lon": -16.5100,
     "desc": "Tenerife, Canary Islands. IAC facility with solar and stellar telescopes at 2,390m altitude."},
    {"name": "Daniel K. Inouye Solar Telescope (DKIST)", "lat": 20.7067, "lon": -156.2564,
     "desc": "Haleakala, Maui, Hawaii. World's largest solar telescope (4m). Resolves features as small as 20 km on the Sun."},
    {"name": "Swedish Solar Telescope (SST)", "lat": 28.7600, "lon": -17.8800,
     "desc": "Roque de los Muchachos, La Palma. 1m vacuum solar telescope with exceptional image quality."},
    {"name": "Solar and Heliospheric Observatory (SOHO) ops", "lat": 38.9955, "lon": -76.8525,
     "desc": "Operations at NASA Goddard. SOHO orbits L1 since 1995 monitoring the Sun. ESA/NASA joint mission."},
    {"name": "Solar Dynamics Observatory (SDO) ops", "lat": 38.9955, "lon": -76.8525,
     "desc": "Operations at NASA Goddard. SDO provides ultra-high-definition imaging of the Sun since 2010."},
    {"name": "Kodaikanal Solar Observatory", "lat": 10.2311, "lon": 77.4655,
     "desc": "Kodaikanal, India. Indian Institute of Astrophysics. Solar observations since 1899. Historic sunspot records."},
    {"name": "Huairou Solar Observing Station", "lat": 40.3939, "lon": 116.5928,
     "desc": "Beijing suburbs, China. NAOC facility. Solar magnetic field observations and space weather monitoring."},
    {"name": "Learmonth Solar Observatory", "lat": -22.2186, "lon": 114.0967,
     "desc": "North West Cape, Australia. Part of USAF Solar Observing Optical Network (SOON). Space weather data."},
]

# Master lookup of all mode datasets
ALL_MODES = {
    "World's Greatest Telescopes": WORLDS_GREATEST_TELESCOPES,
    "Radio Telescopes": RADIO_TELESCOPES,
    "Space Telescope Ground Control": SPACE_TELESCOPE_GROUND_CONTROL,
    "Historic Observatories": HISTORIC_OBSERVATORIES,
    "Next Generation Telescopes": NEXT_GENERATION_TELESCOPES,
    "Dark Sky Preserves": DARK_SKY_PRESERVES,
    "Planetariums & Science Centers": PLANETARIUMS_SCIENCE_CENTERS,
    "Meteorite Impact Observatories": METEORITE_IMPACT_OBSERVATORIES,
    "Gravitational Wave Detectors": GRAVITATIONAL_WAVE_DETECTORS,
    "Solar Observatories": SOLAR_OBSERVATORIES,
}


# ═══════════════════════════════════════════
# OPTIONAL: Wikipedia summary fetch (cached)
# ═══════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fetch_wiki_summary(name: str) -> str:
    """Try to fetch a short Wikipedia summary for an observatory name."""
    try:
        resp = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_"),
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("extract", "")
    except Exception:
        pass
    return ""


# ═══════════════════════════════════════════
# HELPER: build folium map for a given dataset
# ═══════════════════════════════════════════
def _build_map(sites: list, color: str, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map with clustered markers for the given sites."""
    # Compute centroid
    if sites:
        avg_lat = sum(s["lat"] for s in sites) / len(sites)
        avg_lon = sum(s["lon"] for s in sites) / len(sites)
    else:
        avg_lat, avg_lon = 20.0, 0.0

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Sites").add_to(m)

    for site in sites:
        safe_name = html_module.escape(site["name"])
        safe_desc = html_module.escape(site["desc"])

        popup_html = (
            f'<div style="min-width:200px;max-width:280px;font-family:sans-serif;">'
            f'<strong style="color:{color};font-size:0.95rem;">{safe_name}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#333;">{safe_desc}</span><br/>'
            f'<span style="font-size:0.72rem;color:#666;">'
            f'{site["lat"]:.4f}, {site["lon"]:.4f}</span>'
            f'</div>'
        )

        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=safe_name,
        ).add_to(cluster)

    return m


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_telescope_maps_tab():
    """Main render function for the Telescope & Observatory Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header red">
        <h4>Telescope & Observatory Explorer</h4>
        <p>Explore the world's greatest telescopes, radio arrays, space telescope ground control centers,
        dark sky preserves, gravitational wave detectors, and more &mdash; curated global dataset, no API key needed.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    mode = st.selectbox(
        "Map Mode",
        list(ALL_MODES.keys()),
        key="telescope_mode",
    )

    color = MODE_COLORS.get(mode, "#06b6d4")
    sites = ALL_MODES[mode]

    st.markdown("---")

    # ══════════════════════════════════════════
    # SECTION 2: Stats Row
    # ══════════════════════════════════════════
    st.markdown(f"#### {html_module.escape(mode)}")

    # Compute basic stats
    lats = [s["lat"] for s in sites]
    lons = [s["lon"] for s in sites]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Sites", len(sites))
    with c2:
        n_hemisphere = sum(1 for la in lats if la >= 0)
        st.metric("Northern Hemisphere", n_hemisphere)
    with c3:
        s_hemisphere = sum(1 for la in lats if la < 0)
        st.metric("Southern Hemisphere", s_hemisphere)
    with c4:
        countries = set()
        for s in sites:
            # Extract country hint from description (after last period-space, or parenthesized)
            desc = s["desc"]
            for token in desc.replace(".", ",").split(","):
                token = token.strip()
            # simple heuristic: count unique longitude quadrants
        lon_spread = max(lons) - min(lons) if lons else 0
        st.metric("Longitude Spread", f"{lon_spread:.0f} deg")

    # ══════════════════════════════════════════
    # SECTION 3: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")

    # Color legend
    st.markdown(
        f'<div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem;">'
        f'<span style="color:{color};font-size:0.85rem;">&#9679; {html_module.escape(mode)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(sites, color)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 4: Site Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Site Directory")

    for site in sites:
        safe_name = html_module.escape(site["name"])
        safe_desc = html_module.escape(site["desc"])

        st.markdown(f"""
        <div class="bio-card" style="display:flex;align-items:center;margin-bottom:0.65rem;">
            <div style="width:10px;height:60px;border-radius:5px;background:{color};
                        margin-right:0.85rem;flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="color:#e8ecf4;font-weight:700;font-size:0.9rem;">{safe_name}</div>
                <div style="color:#8b97b0;font-size:0.8rem;">{safe_desc}</div>
                <div style="color:#5a6580;font-size:0.72rem;">{site['lat']:.4f}, {site['lon']:.4f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 5: Data Table & Download
    # ══════════════════════════════════════════
    st.markdown("---")

    rows = []
    for site in sites:
        rows.append({
            "name": site["name"],
            "latitude": site["lat"],
            "longitude": site["lon"],
            "description": site["desc"],
            "category": mode,
        })

    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    safe_filename = mode.lower().replace(" ", "_").replace("'", "").replace("&", "and")
    st.download_button(
        f"Download {len(rows)} {html_module.escape(mode)} Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"telescopes_{safe_filename}.csv",
        mime="text/csv",
        key="telescope_download",
    )

    # ══════════════════════════════════════════
    # SECTION 6: Wikipedia Lookup (optional detail)
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Quick Wikipedia Lookup")
    selected_site = st.selectbox(
        "Select a site for more info",
        [s["name"] for s in sites],
        key="telescope_wiki_select",
    )

    if st.button("Fetch Wikipedia Summary", key="telescope_wiki_btn", width="stretch"):
        with st.spinner(f"Looking up {selected_site}..."):
            summary = _fetch_wiki_summary(selected_site)
        if summary:
            st.markdown(f"""
            <div class="bio-card" style="padding:1rem;">
                <div style="color:#e8ecf4;font-weight:700;margin-bottom:0.5rem;">
                    {html_module.escape(selected_site)}
                </div>
                <div style="color:#8b97b0;font-size:0.85rem;line-height:1.5;">
                    {html_module.escape(summary)}
                </div>
                <div style="margin-top:0.5rem;">
                    <a href="https://en.wikipedia.org/wiki/{selected_site.replace(' ', '_')}"
                       target="_blank" style="color:#06b6d4;font-size:0.8rem;">
                       Read full article on Wikipedia
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No Wikipedia summary found for this site. Try a different name or check the article manually.")
