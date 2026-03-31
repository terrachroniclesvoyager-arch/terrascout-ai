# -*- coding: utf-8 -*-
"""
Horses & Equestrian Maps module for TerraScout AI.
Famous racetracks, horse breeds, polo clubs, equestrian heritage worldwide.
All data is curated (no external API required).
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#06b6d4"
SECONDARY_TEXT = "#8b97b0"

# ═══════════════════════════════════════════════════════════════
# 1. WORLD FAMOUS RACETRACKS
# ═══════════════════════════════════════════════════════════════
RACETRACKS = [
    {"name": "Churchill Downs", "lat": 38.2025, "lon": -85.7706, "country": "USA", "city": "Louisville, KY", "founded": 1875, "famous_race": "Kentucky Derby", "surface": "Dirt", "length_m": 2012, "capacity": 170000, "notes": "Home of the Kentucky Derby, the most famous horse race in the US"},
    {"name": "Epsom Downs", "lat": 51.3127, "lon": -0.2614, "country": "UK", "city": "Epsom, Surrey", "founded": 1661, "famous_race": "The Derby Stakes", "surface": "Turf", "length_m": 2414, "capacity": 120000, "notes": "Home of The Derby, the original classic flat race"},
    {"name": "Longchamp Racecourse", "lat": 48.8566, "lon": 2.2300, "country": "France", "city": "Paris", "founded": 1857, "famous_race": "Prix de l'Arc de Triomphe", "surface": "Turf", "length_m": 2400, "capacity": 50000, "notes": "Premier French racecourse in the Bois de Boulogne"},
    {"name": "Tokyo Racecourse", "lat": 35.6614, "lon": 139.4831, "country": "Japan", "city": "Fuchu, Tokyo", "founded": 1933, "famous_race": "Japan Cup", "surface": "Turf/Dirt", "length_m": 2400, "capacity": 223000, "notes": "Largest capacity racecourse in the world"},
    {"name": "Meydan Racecourse", "lat": 25.1652, "lon": 55.3055, "country": "UAE", "city": "Dubai", "founded": 2010, "famous_race": "Dubai World Cup", "surface": "Dirt/Turf", "length_m": 2400, "capacity": 80000, "notes": "Home of the world's richest race day"},
    {"name": "Flemington Racecourse", "lat": -37.7886, "lon": 144.9120, "country": "Australia", "city": "Melbourne", "founded": 1840, "famous_race": "Melbourne Cup", "surface": "Turf", "length_m": 2400, "capacity": 120000, "notes": "The race that stops a nation"},
    {"name": "Ascot Racecourse", "lat": 51.4087, "lon": -0.6767, "country": "UK", "city": "Ascot, Berkshire", "founded": 1711, "famous_race": "Royal Ascot", "surface": "Turf", "length_m": 2816, "capacity": 80000, "notes": "Founded by Queen Anne, attended by the Royal Family"},
    {"name": "Santa Anita Park", "lat": 34.1397, "lon": -118.0469, "country": "USA", "city": "Arcadia, CA", "founded": 1934, "famous_race": "Santa Anita Handicap", "surface": "Dirt/Turf", "length_m": 2012, "capacity": 26000, "notes": "The Great Race Place with stunning San Gabriel Mountains backdrop"},
    {"name": "Pimlico Race Course", "lat": 39.3492, "lon": -76.6536, "country": "USA", "city": "Baltimore, MD", "founded": 1870, "famous_race": "Preakness Stakes", "surface": "Dirt", "length_m": 1609, "capacity": 120000, "notes": "Second jewel of the US Triple Crown"},
    {"name": "Belmont Park", "lat": 40.6716, "lon": -73.7185, "country": "USA", "city": "Elmont, NY", "founded": 1905, "famous_race": "Belmont Stakes", "surface": "Dirt/Turf", "length_m": 2414, "capacity": 100000, "notes": "Test of the Champion, third jewel of the Triple Crown"},
    {"name": "Newmarket Racecourse", "lat": 52.2450, "lon": 0.3853, "country": "UK", "city": "Newmarket, Suffolk", "founded": 1636, "famous_race": "1000/2000 Guineas", "surface": "Turf", "length_m": 3621, "capacity": 20000, "notes": "Headquarters of British horseracing since the 17th century"},
    {"name": "Sha Tin Racecourse", "lat": 22.3964, "lon": 114.2042, "country": "Hong Kong", "city": "Sha Tin", "founded": 1978, "famous_race": "Hong Kong Cup", "surface": "Turf/AWT", "length_m": 2000, "capacity": 85000, "notes": "Premier racecourse of the Hong Kong Jockey Club"},
    {"name": "Leopardstown Racecourse", "lat": 53.2688, "lon": -6.2060, "country": "Ireland", "city": "Dublin", "founded": 1888, "famous_race": "Irish Champion Stakes", "surface": "Turf", "length_m": 2400, "capacity": 25000, "notes": "Ireland's premier flat and jump racecourse"},
    {"name": "Randwick Racecourse", "lat": -33.9042, "lon": 151.2383, "country": "Australia", "city": "Sydney", "founded": 1833, "famous_race": "The Everest", "surface": "Turf", "length_m": 2400, "capacity": 40000, "notes": "Home of Australian Turf Club and the world's richest turf race"},
    {"name": "Kranji Racecourse", "lat": 1.4172, "lon": 103.7644, "country": "Singapore", "city": "Singapore", "founded": 2000, "famous_race": "Singapore Gold Cup", "surface": "Turf/Polytrack", "length_m": 2000, "capacity": 30000, "notes": "Southeast Asia's premier racing venue"},
    {"name": "Hippodrome de Chantilly", "lat": 49.1896, "lon": 2.4715, "country": "France", "city": "Chantilly", "founded": 1834, "famous_race": "Prix du Jockey Club", "surface": "Turf", "length_m": 2400, "capacity": 20000, "notes": "Set in the forests of Chantilly, heart of French horse country"},
    {"name": "Saratoga Race Course", "lat": 43.0804, "lon": -73.7749, "country": "USA", "city": "Saratoga Springs, NY", "founded": 1863, "famous_race": "Travers Stakes", "surface": "Dirt/Turf", "length_m": 2012, "capacity": 50000, "notes": "Oldest sporting venue of any kind in the US, the Graveyard of Champions"},
    {"name": "San Isidro Racecourse", "lat": -34.4708, "lon": -58.5136, "country": "Argentina", "city": "Buenos Aires", "founded": 1935, "famous_race": "Gran Premio Carlos Pellegrini", "surface": "Turf", "length_m": 2400, "capacity": 100000, "notes": "South America's most prestigious racecourse"},
    {"name": "Meydan (Nad Al Sheba)", "lat": 25.1010, "lon": 55.3190, "country": "UAE", "city": "Dubai", "founded": 1986, "famous_race": "Dubai Millennium Stakes", "surface": "Dirt", "length_m": 2000, "capacity": 10000, "notes": "Original home of Dubai World Cup before Meydan"},
    {"name": "Nakayama Racecourse", "lat": 35.7603, "lon": 139.9483, "country": "Japan", "city": "Funabashi, Chiba", "founded": 1920, "famous_race": "Arima Kinen", "surface": "Turf/Dirt", "length_m": 1840, "capacity": 165000, "notes": "Host of the Grand Prix, Japan's most popular race by fan vote"},
    {"name": "Curragh Racecourse", "lat": 53.1531, "lon": -6.8097, "country": "Ireland", "city": "Kildare", "founded": 1727, "famous_race": "Irish Derby", "surface": "Turf", "length_m": 2414, "capacity": 40000, "notes": "Home of all five Irish Classics on the plains of Kildare"},
    {"name": "Aintree Racecourse", "lat": 53.4764, "lon": -2.9581, "country": "UK", "city": "Liverpool", "founded": 1829, "famous_race": "Grand National", "surface": "Turf", "length_m": 7141, "capacity": 75000, "notes": "Home of the world's most famous steeplechase"},
    {"name": "Cheltenham Racecourse", "lat": 51.9148, "lon": -2.0715, "country": "UK", "city": "Cheltenham", "founded": 1815, "famous_race": "Cheltenham Gold Cup", "surface": "Turf", "length_m": 3200, "capacity": 67500, "notes": "Premier National Hunt festival venue, the Olympics of jump racing"},
    {"name": "Happy Valley Racecourse", "lat": 22.2735, "lon": 114.1840, "country": "Hong Kong", "city": "Happy Valley", "founded": 1846, "famous_race": "Happy Valley Trophy", "surface": "Turf", "length_m": 1450, "capacity": 55000, "notes": "Iconic city racecourse surrounded by skyscrapers"},
    {"name": "Greyville Racecourse", "lat": -29.8485, "lon": 31.0289, "country": "South Africa", "city": "Durban", "founded": 1844, "famous_race": "Vodacom Durban July", "surface": "Turf/Poly", "length_m": 2400, "capacity": 50000, "notes": "Africa's greatest horse racing event"},
    {"name": "Del Mar Racetrack", "lat": 32.9758, "lon": -117.2652, "country": "USA", "city": "Del Mar, CA", "founded": 1937, "famous_race": "Pacific Classic", "surface": "Dirt/Turf", "length_m": 1810, "capacity": 44000, "notes": "Where the turf meets the surf, co-founded by Bing Crosby"},
    {"name": "Gulfstream Park", "lat": 25.9710, "lon": -80.1463, "country": "USA", "city": "Hallandale Beach, FL", "founded": 1939, "famous_race": "Pegasus World Cup", "surface": "Dirt/Turf", "length_m": 1810, "capacity": 20000, "notes": "Home to one of the richest races in the world"},
    {"name": "Haydock Park", "lat": 53.4888, "lon": -2.6344, "country": "UK", "city": "Newton-le-Willows", "founded": 1899, "famous_race": "Sprint Cup", "surface": "Turf", "length_m": 2000, "capacity": 20000, "notes": "Premier dual-purpose racecourse in North West England"},
    {"name": "Champ de Mars", "lat": -20.1609, "lon": 57.5084, "country": "Mauritius", "city": "Port Louis", "founded": 1812, "famous_race": "Maiden Cup", "surface": "Turf", "length_m": 1500, "capacity": 20000, "notes": "Second oldest racecourse in the Southern Hemisphere"},
    {"name": "Hipodromo de la Zarzuela", "lat": 40.4547, "lon": -3.7783, "country": "Spain", "city": "Madrid", "founded": 1941, "famous_race": "Gran Premio de Madrid", "surface": "Turf/Dirt", "length_m": 2400, "capacity": 15000, "notes": "Architectural masterpiece with dramatic cantilevered roof"},
]

# ═══════════════════════════════════════════════════════════════
# 2. HORSE BREED ORIGINS
# ═══════════════════════════════════════════════════════════════
HORSE_BREEDS = [
    {"name": "Arabian", "lat": 24.7136, "lon": 46.6753, "country": "Saudi Arabia", "region": "Arabian Peninsula", "type": "Hot-blooded", "height_hh": "14.1-15.1", "uses": "Endurance, racing, showing", "population_est": "1,000,000+", "notes": "Oldest pure breed, foundation of most modern breeds"},
    {"name": "Thoroughbred", "lat": 52.2450, "lon": 0.3853, "country": "UK", "region": "England", "type": "Hot-blooded", "height_hh": "15.2-17.0", "uses": "Flat racing, steeplechase", "population_est": "500,000+", "notes": "Developed from three foundation stallions: Byerly Turk, Darley Arabian, Godolphin Arabian"},
    {"name": "Andalusian (PRE)", "lat": 36.7213, "lon": -4.4214, "country": "Spain", "region": "Andalusia", "type": "Warm-blooded", "height_hh": "15.0-16.2", "uses": "Dressage, bullfighting, film", "population_est": "200,000", "notes": "Pure Spanish Horse, known for spectacular collected movements"},
    {"name": "Friesian", "lat": 53.1641, "lon": 5.7817, "country": "Netherlands", "region": "Friesland", "type": "Warm-blooded", "height_hh": "15.0-17.0", "uses": "Driving, dressage, film", "population_est": "60,000", "notes": "Striking black coat, feathered legs, nearly went extinct in early 1900s"},
    {"name": "Akhal-Teke", "lat": 38.9697, "lon": 59.5563, "country": "Turkmenistan", "region": "Karakum Desert", "type": "Hot-blooded", "height_hh": "14.2-16.0", "uses": "Endurance, racing, dressage", "population_est": "6,600", "notes": "Golden metallic sheen coat, one of the oldest breeds, extreme endurance"},
    {"name": "Lipizzan", "lat": 45.5469, "lon": 14.2136, "country": "Slovenia", "region": "Lipica", "type": "Warm-blooded", "height_hh": "14.2-15.2", "uses": "Classical dressage, haute ecole", "population_est": "11,000", "notes": "Famous for the Spanish Riding School of Vienna, born dark then turn white"},
    {"name": "Mustang", "lat": 39.4917, "lon": -117.5664, "country": "USA", "region": "Nevada/Western US", "type": "Feral", "height_hh": "13.0-16.0", "uses": "Riding, ranch work", "population_est": "86,000", "notes": "Descended from Spanish colonial horses, symbol of the American West"},
    {"name": "Icelandic Horse", "lat": 64.9631, "lon": -19.0208, "country": "Iceland", "region": "Iceland", "type": "Cold-blooded", "height_hh": "12.2-14.0", "uses": "Trail riding, tolt gait", "population_est": "80,000", "notes": "Five gaited, incredibly sure-footed, purest breed due to island isolation since 900 AD"},
    {"name": "Clydesdale", "lat": 55.7655, "lon": -3.9620, "country": "UK", "region": "Lanarkshire, Scotland", "type": "Cold-blooded", "height_hh": "16.0-18.0", "uses": "Draft, showing, parades", "population_est": "5,000", "notes": "Famous Budweiser horses, feathered hooves, gentle giants"},
    {"name": "Marwari", "lat": 26.2986, "lon": 73.0169, "country": "India", "region": "Rajasthan", "type": "Hot-blooded", "height_hh": "14.2-15.2", "uses": "Ceremonial, polo, riding", "population_est": "3,000", "notes": "Distinctive inward-curving ears, loyal desert warrior horse of the Rajputs"},
    {"name": "Percheron", "lat": 48.3657, "lon": 0.8700, "country": "France", "region": "Le Perche, Normandy", "type": "Cold-blooded", "height_hh": "15.0-19.0", "uses": "Draft, farm work, logging", "population_est": "300,000", "notes": "Most popular draft breed worldwide, powerful yet elegant"},
    {"name": "Quarter Horse", "lat": 32.7767, "lon": -96.7970, "country": "USA", "region": "Texas/Virginia", "type": "Warm-blooded", "height_hh": "14.0-16.0", "uses": "Ranching, barrel racing, rodeo", "population_est": "3,000,000+", "notes": "World's most popular breed, fastest horse over quarter mile"},
    {"name": "Hanoverian", "lat": 52.3759, "lon": 9.7320, "country": "Germany", "region": "Hanover", "type": "Warm-blooded", "height_hh": "15.3-17.1", "uses": "Dressage, show jumping, eventing", "population_est": "200,000", "notes": "Premier Olympic sport horse, founded 1735 by George II of England"},
    {"name": "Camargue", "lat": 43.5000, "lon": 4.5000, "country": "France", "region": "Camargue, Provence", "type": "Warm-blooded", "height_hh": "13.1-14.3", "uses": "Herding, riding", "population_est": "8,000", "notes": "Ancient white horses of the Rhone delta marshes, ridden by gardians"},
    {"name": "Mongolian Horse", "lat": 47.9213, "lon": 106.9075, "country": "Mongolia", "region": "Mongolian Steppe", "type": "Cold-blooded", "height_hh": "12.0-14.0", "uses": "Racing, herding, kumis", "population_est": "4,200,000", "notes": "The horse that built the Mongol Empire, semi-wild herds, incredibly tough"},
    {"name": "Lusitano", "lat": 38.7223, "lon": -9.1393, "country": "Portugal", "region": "Portugal", "type": "Warm-blooded", "height_hh": "15.0-16.1", "uses": "Bullfighting, dressage, driving", "population_est": "30,000", "notes": "Noble Portuguese breed, sister to Andalusian, exceptional courage"},
    {"name": "Appaloosa", "lat": 46.4108, "lon": -116.0252, "country": "USA", "region": "Nez Perce, Idaho", "type": "Warm-blooded", "height_hh": "14.2-16.0", "uses": "Trail, western, showing", "population_est": "700,000", "notes": "Distinctive spotted coat patterns, bred by the Nez Perce tribe"},
    {"name": "Criollo", "lat": -34.6037, "lon": -58.3816, "country": "Argentina", "region": "South America", "type": "Warm-blooded", "height_hh": "14.0-15.0", "uses": "Polo, ranch, endurance", "population_est": "500,000", "notes": "Toughest horse in the world, Tschiffely's Ride 10,000 miles Buenos Aires to Washington"},
    {"name": "Shire", "lat": 52.8305, "lon": -1.3327, "country": "UK", "region": "English Midlands", "type": "Cold-blooded", "height_hh": "16.0-19.0", "uses": "Draft, showing, brewing", "population_est": "2,000", "notes": "Tallest horse breed, once pulled brewery wagons, now critically endangered"},
    {"name": "Haflinger", "lat": 46.6250, "lon": 11.4374, "country": "Italy/Austria", "region": "South Tyrol", "type": "Cold-blooded", "height_hh": "13.2-15.0", "uses": "Draft, riding, driving", "population_est": "250,000", "notes": "Chestnut with flaxen mane, sure-footed alpine breed, all trace to stallion Folie"},
    {"name": "Przewalski's Horse", "lat": 47.0000, "lon": 93.0000, "country": "Mongolia", "region": "Hustai National Park", "type": "Wild", "height_hh": "12.0-14.2", "uses": "Conservation, wild", "population_est": "2,000", "notes": "Only truly wild horse species, never domesticated, saved from extinction in zoos"},
    {"name": "Paso Fino", "lat": 18.2208, "lon": -66.5901, "country": "Puerto Rico", "region": "Caribbean", "type": "Warm-blooded", "height_hh": "13.0-15.2", "uses": "Trail riding, showing", "population_est": "50,000", "notes": "Incredibly smooth four-beat lateral gait, descended from Spanish horses"},
    {"name": "Knabstrupper", "lat": 55.5305, "lon": 11.7803, "country": "Denmark", "region": "Knabstrup, Zealand", "type": "Warm-blooded", "height_hh": "15.2-16.0", "uses": "Circus, dressage, driving", "population_est": "3,000", "notes": "Spotted coat patterns similar to Appaloosa, baroque type circus horse"},
    {"name": "Shetland Pony", "lat": 60.3880, "lon": -1.1500, "country": "UK", "region": "Shetland Islands", "type": "Cold-blooded", "height_hh": "7.0-11.2", "uses": "Children's pony, therapy", "population_est": "100,000", "notes": "Smallest British breed, incredibly strong for size, once worked in coal mines"},
    {"name": "Trakehner", "lat": 54.6350, "lon": 21.8300, "country": "Germany/Russia", "region": "East Prussia", "type": "Warm-blooded", "height_hh": "15.2-17.0", "uses": "Eventing, dressage", "population_est": "35,000", "notes": "Lightest warmblood, survived legendary 1945 Trek across frozen Baltic in WWII"},
    {"name": "Nokota", "lat": 47.6, "lon": -103.5, "country": "USA", "region": "North Dakota", "type": "Feral", "height_hh": "14.2-17.0", "uses": "Endurance, ranch, trail", "population_est": "1,000", "notes": "Rare breed from Theodore Roosevelt National Park, descended from Sitting Bull's horses"},
    {"name": "Banker Horse", "lat": 35.0682, "lon": -75.9813, "country": "USA", "region": "Outer Banks, NC", "type": "Feral", "height_hh": "13.0-14.2", "uses": "Conservation, wild", "population_est": "400", "notes": "Feral Colonial Spanish horses on barrier islands since 1500s, survive hurricanes"},
    {"name": "Brumby", "lat": -36.5, "lon": 148.0, "country": "Australia", "region": "Australian Alps", "type": "Feral", "height_hh": "14.0-16.0", "uses": "Feral/conservation debate", "population_est": "400,000", "notes": "Australia's iconic feral horses, the Man from Snowy River, contentious conservation issue"},
    {"name": "Kathiawari", "lat": 22.0, "lon": 70.0, "country": "India", "region": "Kathiawar Peninsula", "type": "Hot-blooded", "height_hh": "14.0-15.0", "uses": "Mounted police, riding", "population_est": "5,000", "notes": "Related to Marwari with inward-curving ears, desert-bred warrior horse"},
    {"name": "Fjord Horse", "lat": 61.0, "lon": 7.0, "country": "Norway", "region": "Western Norway", "type": "Cold-blooded", "height_hh": "13.2-14.2", "uses": "Draft, riding, therapy", "population_est": "80,000", "notes": "One of oldest breeds, distinctive dun color with dark dorsal stripe, Viking horse"},
]

# ═══════════════════════════════════════════════════════════════
# 3. POLO CLUBS WORLDWIDE
# ═══════════════════════════════════════════════════════════════
POLO_CLUBS = [
    {"name": "Guards Polo Club", "lat": 51.4117, "lon": -0.6148, "country": "UK", "city": "Windsor", "founded": 1955, "fields": 12, "level": "Elite", "notes": "World's premier polo club, hosts the Queen's Cup and Gold Cup"},
    {"name": "Argentine Polo Association (AAP)", "lat": -34.5625, "lon": -58.4158, "country": "Argentina", "city": "Buenos Aires", "founded": 1893, "fields": 6, "level": "Elite", "notes": "Governing body of Argentine polo, hosts the Open Championship"},
    {"name": "Palm Beach International Polo Club", "lat": 26.6368, "lon": -80.2428, "country": "USA", "city": "Wellington, FL", "founded": 2004, "fields": 7, "level": "Elite", "notes": "America's premier polo venue, hosts US Open Polo Championship"},
    {"name": "Cowdray Park Polo Club", "lat": 51.0107, "lon": -0.7045, "country": "UK", "city": "Midhurst, Sussex", "founded": 1910, "fields": 8, "level": "Elite", "notes": "Hosts the prestigious Gold Cup, oldest polo trophy in UK"},
    {"name": "Hurlingham Club", "lat": -34.5800, "lon": -58.4500, "country": "Argentina", "city": "Buenos Aires", "founded": 1888, "fields": 4, "level": "Elite", "notes": "Historic polo club, world headquarters of polo rules"},
    {"name": "Dubai Polo & Equestrian Club", "lat": 25.0636, "lon": 55.2370, "country": "UAE", "city": "Dubai", "founded": 2004, "fields": 4, "level": "Elite", "notes": "Middle East's premier polo destination with luxury amenities"},
    {"name": "Jaipur Polo Club", "lat": 26.9124, "lon": 75.7873, "country": "India", "city": "Jaipur", "founded": 1918, "fields": 3, "level": "Elite", "notes": "Royal heritage polo in the Pink City, patronized by Maharajas"},
    {"name": "Santa Maria Polo Club", "lat": 36.2072, "lon": -6.1200, "country": "Spain", "city": "Sotogrande", "founded": 1965, "fields": 11, "level": "Elite", "notes": "Largest polo complex in Europe, hosts Gold Cup of Sotogrande"},
    {"name": "Ellerston Polo", "lat": -31.8500, "lon": 150.5500, "country": "Australia", "city": "Upper Hunter Valley", "founded": 1996, "fields": 6, "level": "Elite", "notes": "Kerry Packer's private polo estate, now elite tournament venue"},
    {"name": "Royal County of Berkshire Polo Club", "lat": 51.4220, "lon": -0.7300, "country": "UK", "city": "Winkfield, Berkshire", "founded": 1985, "fields": 10, "level": "Elite", "notes": "One of the top polo clubs in England, Royal patronage"},
    {"name": "Cirencester Park Polo Club", "lat": 51.7148, "lon": -1.9700, "country": "UK", "city": "Cirencester", "founded": 1894, "fields": 10, "level": "High-Goal", "notes": "One of the oldest polo clubs in England, Prince Charles played here"},
    {"name": "Club de Polo La Martina", "lat": -34.7000, "lon": -58.8000, "country": "Argentina", "city": "Open Door, Buenos Aires", "founded": 1980, "fields": 5, "level": "Elite", "notes": "Home of La Martina brand, breeding and training center"},
    {"name": "Singapore Polo Club", "lat": 1.3262, "lon": 103.8292, "country": "Singapore", "city": "Singapore", "founded": 1886, "fields": 3, "level": "High-Goal", "notes": "Southeast Asia's oldest polo club, colonial heritage venue"},
    {"name": "Royal Pahang Polo Club", "lat": 3.8126, "lon": 103.3260, "country": "Malaysia", "city": "Pekan", "founded": 1926, "fields": 2, "level": "High-Goal", "notes": "Royal Malaysian polo, patronized by Sultan of Pahang"},
    {"name": "Lahore Polo Club", "lat": 31.5204, "lon": 74.3587, "country": "Pakistan", "city": "Lahore", "founded": 1860, "fields": 4, "level": "High-Goal", "notes": "One of the oldest polo clubs in Asia, hosts Pakistan Open"},
    {"name": "Gilgit Polo Ground", "lat": 35.9194, "lon": 74.3083, "country": "Pakistan", "city": "Gilgit", "founded": 1890, "fields": 1, "level": "Traditional", "notes": "World's highest polo ground at 7,500 ft, unique free-style polo tradition"},
    {"name": "Shandur Polo Ground", "lat": 36.0700, "lon": 72.0500, "country": "Pakistan", "city": "Chitral/Gilgit border", "founded": 1936, "fields": 1, "level": "Traditional", "notes": "Highest polo ground in the world at 12,200 ft, no rules freestyle polo"},
    {"name": "Veuve Clicquot Polo Classic (Liberty State)", "lat": 40.6925, "lon": -74.0505, "country": "USA", "city": "Jersey City, NJ", "founded": 2008, "fields": 1, "level": "Exhibition", "notes": "Annual celebrity polo event with Manhattan skyline backdrop"},
    {"name": "Royal Johor Polo Club", "lat": 1.4556, "lon": 103.7550, "country": "Malaysia", "city": "Johor Bahru", "founded": 1884, "fields": 3, "level": "High-Goal", "notes": "Historic Southeast Asian polo venue with royal patronage"},
    {"name": "Ham Polo Club", "lat": 51.4395, "lon": -0.3133, "country": "UK", "city": "Richmond, London", "founded": 1926, "fields": 3, "level": "Medium-Goal", "notes": "Only polo club in Greater London, accessible and community-focused"},
    {"name": "Val de Vie Polo Club", "lat": -33.8400, "lon": 18.9700, "country": "South Africa", "city": "Paarl, Western Cape", "founded": 2008, "fields": 4, "level": "High-Goal", "notes": "Africa's premier polo estate in the Cape Winelands"},
    {"name": "Calcutta Polo Club", "lat": 22.5468, "lon": 88.3590, "country": "India", "city": "Kolkata", "founded": 1862, "fields": 2, "level": "High-Goal", "notes": "Oldest polo club in the world, where modern polo rules were formalized"},
    {"name": "Manipur Polo Ground", "lat": 24.8170, "lon": 93.9368, "country": "India", "city": "Imphal", "founded": 1850, "fields": 1, "level": "Traditional", "notes": "Birthplace of modern polo (sagol kangjei), oldest polo ground in the world"},
    {"name": "National Polo Center", "lat": 26.6590, "lon": -80.2640, "country": "USA", "city": "Wellington, FL", "founded": 2019, "fields": 12, "level": "Elite", "notes": "State-of-the-art 240-acre polo facility, hosts USPA tournaments"},
    {"name": "Emlor Polo", "lat": 51.5900, "lon": -1.7500, "country": "UK", "city": "Malmesbury, Wiltshire", "founded": 2006, "fields": 6, "level": "High-Goal", "notes": "Major British polo academy and tournament venue"},
]

# ═══════════════════════════════════════════════════════════════
# 4. HISTORIC CAVALRY & WAR HORSE SITES
# ═══════════════════════════════════════════════════════════════
CAVALRY_SITES = [
    {"name": "Battle of Balaclava - Charge of the Light Brigade", "lat": 44.5319, "lon": 33.6003, "country": "Ukraine", "year": 1854, "era": "Crimean War", "cavalry_type": "British Light Cavalry", "notes": "Disastrous charge of 670 horsemen against Russian guns, immortalized by Tennyson"},
    {"name": "Battle of Austerlitz", "lat": 49.1500, "lon": 16.7667, "country": "Czech Republic", "year": 1805, "era": "Napoleonic Wars", "cavalry_type": "French & Russian Cavalry", "notes": "Napoleon's greatest victory, decisive cavalry charges on the Pratzen Heights"},
    {"name": "Battle of Waterloo", "lat": 50.6803, "lon": 4.4114, "country": "Belgium", "year": 1815, "era": "Napoleonic Wars", "cavalry_type": "French/British/Prussian", "notes": "Napoleon's final defeat, massive cavalry charges by Marshal Ney"},
    {"name": "Battle of Gettysburg - Pickett's Charge", "lat": 39.8125, "lon": -77.2311, "country": "USA", "year": 1863, "era": "American Civil War", "cavalry_type": "Confederate Cavalry", "notes": "Largest cavalry battle in the Western Hemisphere on East Cavalry Field"},
    {"name": "Battle of Beersheba", "lat": 31.2518, "lon": 34.7913, "country": "Israel", "year": 1917, "era": "World War I", "cavalry_type": "Australian Light Horse", "notes": "Last great successful cavalry charge in history, 800 horsemen took the town"},
    {"name": "Battle of Gaugamela", "lat": 36.5600, "lon": 43.4500, "country": "Iraq", "year": -331, "era": "Ancient", "cavalry_type": "Macedonian Companions", "notes": "Alexander the Great's Companion cavalry crushed the Persian Empire"},
    {"name": "Battle of Cannae", "lat": 41.3050, "lon": 16.1330, "country": "Italy", "year": -216, "era": "Ancient", "cavalry_type": "Carthaginian/Numidian", "notes": "Hannibal's cavalry envelopment destroyed 8 Roman legions, textbook double encirclement"},
    {"name": "Battle of Hastings", "lat": 50.9147, "lon": 0.4878, "country": "UK", "year": 1066, "era": "Medieval", "cavalry_type": "Norman Knights", "notes": "William the Conqueror's mounted knights defeated Saxon infantry, changed English history"},
    {"name": "Battle of Agincourt", "lat": 50.4630, "lon": 2.1430, "country": "France", "year": 1415, "era": "Medieval", "cavalry_type": "French Knights", "notes": "French mounted knights defeated by English longbowmen in muddy terrain"},
    {"name": "Battle of Panipat (First)", "lat": 29.3909, "lon": 76.9635, "country": "India", "year": 1526, "era": "Mughal", "cavalry_type": "Mughal Cavalry", "notes": "Babur's cavalry and artillery defeated the Delhi Sultanate, founded the Mughal Empire"},
    {"name": "Battle of Mohacs", "lat": 45.9903, "lon": 18.6806, "country": "Hungary", "year": 1526, "era": "Ottoman Wars", "cavalry_type": "Ottoman Sipahi", "notes": "Ottoman cavalry destroyed the Hungarian kingdom in 90 minutes"},
    {"name": "Battle of Pavia", "lat": 45.1847, "lon": 9.1582, "country": "Italy", "year": 1525, "era": "Italian Wars", "cavalry_type": "French Gendarmes", "notes": "French King Francis I captured after his cavalry charge failed against Spanish firearms"},
    {"name": "Battle of Blenheim", "lat": 48.6328, "lon": 10.6000, "country": "Germany", "year": 1704, "era": "War of Spanish Succession", "cavalry_type": "British/Allied Cavalry", "notes": "Duke of Marlborough's cavalry broke the French center"},
    {"name": "Battle of Wagram", "lat": 48.2953, "lon": 16.5631, "country": "Austria", "year": 1809, "era": "Napoleonic Wars", "cavalry_type": "French Cuirassiers", "notes": "Massive cavalry battle, 300,000+ troops engaged, Napoleon's hard-won victory"},
    {"name": "Spanish Riding School of Vienna", "lat": 48.2082, "lon": 16.3669, "country": "Austria", "year": 1572, "era": "Renaissance", "cavalry_type": "Habsburg Classical Riding", "notes": "Oldest riding school in the world, preserving classical dressage with Lipizzan stallions"},
    {"name": "Cavalry Museum, Saumur", "lat": 47.2600, "lon": -0.0766, "country": "France", "year": 1763, "era": "Modern", "cavalry_type": "French Cavalry School", "notes": "Cadre Noir, France's elite riding academy, preserving classical equitation"},
    {"name": "Battle of Isandlwana", "lat": -28.3567, "lon": 30.6500, "country": "South Africa", "year": 1879, "era": "Anglo-Zulu War", "cavalry_type": "British/Zulu", "notes": "Devastating British defeat, mounted infantry failed against Zulu impis"},
    {"name": "Battle of the Catalaunian Plains", "lat": 48.5000, "lon": 4.0000, "country": "France", "year": 451, "era": "Late Roman", "cavalry_type": "Roman/Visigoth vs Hunnic", "notes": "Attila the Hun defeated, one of the largest cavalry battles in ancient history"},
    {"name": "Battle of Kalka River", "lat": 47.2500, "lon": 37.5000, "country": "Ukraine", "year": 1223, "era": "Mongol Invasion", "cavalry_type": "Mongol Horse Archers", "notes": "First Mongol invasion of Europe, devastating horse archer tactics"},
    {"name": "Little Bighorn Battlefield", "lat": 45.5694, "lon": -107.4264, "country": "USA", "year": 1876, "era": "Indian Wars", "cavalry_type": "US 7th Cavalry", "notes": "Custer's Last Stand, US cavalry annihilated by Lakota, Cheyenne, and Arapaho warriors"},
    {"name": "Charge at Moreuil Wood", "lat": 49.7500, "lon": 2.4667, "country": "France", "year": 1918, "era": "World War I", "cavalry_type": "Canadian Cavalry", "notes": "Last great cavalry charge on the Western Front, Canadian cavalry saved Amiens"},
    {"name": "Battle of Eylau", "lat": 54.3830, "lon": 20.5170, "country": "Russia", "year": 1807, "era": "Napoleonic Wars", "cavalry_type": "French Cuirassiers", "notes": "Murat's legendary cavalry charge of 11,000 horsemen saved the French army in a blizzard"},
    {"name": "Terracotta Army Cavalry", "lat": 34.3847, "lon": 109.2785, "country": "China", "year": -210, "era": "Ancient China", "cavalry_type": "Qin Dynasty Cavalry", "notes": "Life-sized terracotta cavalry horses guarding Emperor Qin Shi Huang's tomb"},
    {"name": "Battle of Kadesh", "lat": 34.5700, "lon": 36.5100, "country": "Syria", "year": -1274, "era": "Ancient", "cavalry_type": "Egyptian/Hittite Chariots", "notes": "Largest chariot battle in history, Ramesses II vs Hittites, 5,000+ chariots engaged"},
    {"name": "Battle of Leuctra", "lat": 38.3700, "lon": 23.0500, "country": "Greece", "year": -371, "era": "Ancient Greece", "cavalry_type": "Theban Sacred Band", "notes": "Epaminondas's oblique order with elite cavalry broke Spartan dominance forever"},
]

# ═══════════════════════════════════════════════════════════════
# 5. EQUESTRIAN OLYMPIC VENUES
# ═══════════════════════════════════════════════════════════════
OLYMPIC_VENUES = [
    {"name": "Greenwich Park (2012)", "lat": 51.4769, "lon": -0.0005, "country": "UK", "city": "London", "year": 2012, "events": "Dressage, Eventing, Jumping", "gold_nations": "UK, Germany, Switzerland", "notes": "Historic Royal Park with stunning backdrop, Charlotte Dujardin's legendary dressage"},
    {"name": "Deodoro Olympic Equestrian Centre (2016)", "lat": -22.8567, "lon": -43.3919, "country": "Brazil", "city": "Rio de Janeiro", "year": 2016, "events": "Dressage, Eventing, Jumping", "gold_nations": "UK, France, Germany", "notes": "Purpose-built facility in Deodoro military area, tropical conditions challenged horses"},
    {"name": "Baji Koen (Equestrian Park) (2020)", "lat": 35.6719, "lon": 139.5267, "country": "Japan", "city": "Tokyo", "year": 2020, "events": "Dressage, Eventing, Jumping", "gold_nations": "UK, Germany, Sweden", "notes": "Also used for 1964 Olympics, Jessica von Bredow-Werndl's dressage gold"},
    {"name": "Hong Kong Equestrian Venue (2008)", "lat": 22.2700, "lon": 114.1800, "country": "China", "city": "Hong Kong", "year": 2008, "events": "Dressage, Eventing, Jumping", "gold_nations": "Netherlands, Germany, Canada", "notes": "Equestrian events held in Hong Kong due to quarantine regulations"},
    {"name": "Markopoulo Olympic Equestrian Centre (2004)", "lat": 37.8833, "lon": 23.9500, "country": "Greece", "city": "Athens", "year": 2004, "events": "Dressage, Eventing, Jumping", "gold_nations": "Germany, France, USA", "notes": "Anky van Grunsven's third consecutive individual dressage gold"},
    {"name": "Sydney International Equestrian Centre (2000)", "lat": -33.7989, "lon": 150.7462, "country": "Australia", "city": "Sydney", "year": 2000, "events": "Dressage, Eventing, Jumping", "gold_nations": "Australia, Netherlands, Germany", "notes": "Penrith facility, Australia's eventing gold on home soil"},
    {"name": "Georgia International Horse Park (1996)", "lat": 33.6842, "lon": -83.9122, "country": "USA", "city": "Conyers, GA", "year": 1996, "events": "Dressage, Eventing, Jumping", "gold_nations": "Germany, Australia, USA", "notes": "Purpose-built facility near Atlanta, extreme heat challenged riders"},
    {"name": "Real Club de Polo de Barcelona (1992)", "lat": 41.3851, "lon": 2.1288, "country": "Spain", "city": "Barcelona", "year": 1992, "events": "Dressage, Eventing, Jumping", "gold_nations": "Germany, Australia, Netherlands", "notes": "Nicole Uphoff's second consecutive dressage gold on Rembrandt"},
    {"name": "Stockholm Olympic Stadium (1912 & 1956)", "lat": 59.3456, "lon": 18.0789, "country": "Sweden", "city": "Stockholm", "year": 1956, "events": "Dressage, Eventing, Jumping", "gold_nations": "Sweden, Germany, UK", "notes": "1956 equestrian events held in Stockholm instead of Melbourne due to quarantine laws"},
    {"name": "National Equestrian Center Fontainebleau (1924)", "lat": 48.4009, "lon": 2.7018, "country": "France", "city": "Fontainebleau", "year": 1924, "events": "Dressage, Eventing, Jumping", "gold_nations": "Sweden, Netherlands, Switzerland", "notes": "Equestrian events in the famous Forest of Fontainebleau"},
    {"name": "Berlin Olympic Equestrian Venue (1936)", "lat": 52.5147, "lon": 13.2395, "country": "Germany", "city": "Berlin", "year": 1936, "events": "Dressage, Eventing, Jumping", "gold_nations": "Germany, multiple", "notes": "First Olympics to feature all three equestrian disciplines in modern format"},
    {"name": "Helsinki Olympic Equestrian Venue (1952)", "lat": 60.1875, "lon": 24.9264, "country": "Finland", "city": "Helsinki", "year": 1952, "events": "Dressage, Eventing, Jumping", "gold_nations": "Sweden, France, UK", "notes": "First Olympics where civilian women competed in equestrian events"},
    {"name": "Rome Olympic Equestrian Venue (1960)", "lat": 41.9379, "lon": 12.4652, "country": "Italy", "city": "Rome", "year": 1960, "events": "Dressage, Eventing, Jumping", "gold_nations": "USSR, Australia, Germany", "notes": "Piazza di Siena venue in Villa Borghese gardens"},
    {"name": "Mexico City Equestrian Venue (1968)", "lat": 19.4036, "lon": -99.0950, "country": "Mexico", "city": "Mexico City", "year": 1968, "events": "Dressage, Eventing, Jumping", "gold_nations": "USSR, UK, Germany", "notes": "High altitude challenged both horses and riders at 7,300+ feet"},
    {"name": "Munich Olympic Equestrian Venue (1972)", "lat": 48.1685, "lon": 11.5466, "country": "Germany", "city": "Munich", "year": 1972, "events": "Dressage, Eventing, Jumping", "gold_nations": "West Germany, UK, Italy", "notes": "Nymphenburg Park venue, Liselott Linsenhoff first woman to win individual dressage gold"},
    {"name": "Bromont Olympic Equestrian Centre (1976)", "lat": 45.3167, "lon": -72.1333, "country": "Canada", "city": "Bromont, QC", "year": 1976, "events": "Dressage, Eventing, Jumping", "gold_nations": "West Germany, USA, France", "notes": "Purpose-built in Quebec countryside, eventing endurance phase was grueling"},
    {"name": "Seoul Olympic Equestrian Venue (1988)", "lat": 37.5200, "lon": 127.0100, "country": "South Korea", "city": "Seoul", "year": 1988, "events": "Dressage, Eventing, Jumping", "gold_nations": "West Germany, France, New Zealand", "notes": "Mark Todd and Charisma won eventing gold, considered greatest event horse ever"},
    {"name": "Chateau de Versailles (2024)", "lat": 48.8049, "lon": 2.1204, "country": "France", "city": "Versailles", "year": 2024, "events": "Dressage, Eventing, Jumping", "gold_nations": "Germany, UK, multiple", "notes": "Spectacular venue at the Palace of Versailles gardens, most stunning equestrian backdrop ever"},
    {"name": "Aachen Soers (World Equestrian Festival)", "lat": 50.7753, "lon": 6.1000, "country": "Germany", "city": "Aachen", "year": 2006, "events": "WEG - All disciplines", "gold_nations": "Germany, multiple", "notes": "Host of 2006 World Equestrian Games, considered the greatest horse show in the world"},
    {"name": "Tryon International Equestrian Center (2018 WEG)", "lat": 35.2400, "lon": -82.2200, "country": "USA", "city": "Tryon, NC", "year": 2018, "events": "WEG - All disciplines", "gold_nations": "Germany, UK, USA", "notes": "First WEG in USA, 1,500-acre facility in the Blue Ridge Mountains foothills"},
]

# ═══════════════════════════════════════════════════════════════
# 6. WILD HORSE POPULATIONS
# ═══════════════════════════════════════════════════════════════
WILD_HORSES = [
    {"name": "Nevada Mustangs", "lat": 39.4917, "lon": -117.5664, "country": "USA", "region": "Great Basin, Nevada", "population": 50000, "status": "Managed", "breed": "Mustang", "notes": "Largest wild horse population in the US, BLM manages herds across Great Basin"},
    {"name": "Przewalski's Horses - Hustai", "lat": 47.7500, "lon": 107.0000, "country": "Mongolia", "region": "Hustai National Park", "population": 400, "status": "Reintroduced", "breed": "Przewalski's Horse", "notes": "Successfully reintroduced from captive breeding, only truly wild horse species"},
    {"name": "Brumbies - Kosciuszko", "lat": -36.4556, "lon": 148.2631, "country": "Australia", "region": "Snowy Mountains, NSW", "population": 18000, "status": "Controversial", "breed": "Brumby", "notes": "Iconic feral horses in Australian Alps, contentious conservation vs heritage debate"},
    {"name": "Chincoteague Ponies", "lat": 37.9305, "lon": -75.3538, "country": "USA", "region": "Assateague Island, VA", "population": 300, "status": "Managed", "breed": "Chincoteague Pony", "notes": "Famous from Misty of Chincoteague novel, annual swim and auction since 1925"},
    {"name": "Camargue White Horses", "lat": 43.5000, "lon": 4.5000, "country": "France", "region": "Camargue Delta", "population": 5000, "status": "Semi-wild", "breed": "Camargue", "notes": "Ancient white horses of the Rhone delta, managed by gardians (cowboys)"},
    {"name": "Namib Desert Horses", "lat": -26.5333, "lon": 15.8000, "country": "Namibia", "region": "Garub, Namib Desert", "population": 150, "status": "Endangered", "breed": "Namib Feral", "notes": "Only feral desert horses in Africa, surviving in extreme conditions since WWI era"},
    {"name": "Banker Horses - Outer Banks", "lat": 35.0682, "lon": -75.9813, "country": "USA", "region": "Outer Banks, NC", "population": 400, "status": "Protected", "breed": "Banker Horse", "notes": "Colonial Spanish horses on barrier islands since 1500s, survive hurricanes and storms"},
    {"name": "Exmoor Ponies", "lat": 51.1400, "lon": -3.5600, "country": "UK", "region": "Exmoor, Devon/Somerset", "population": 4000, "status": "Endangered", "breed": "Exmoor Pony", "notes": "Britain's oldest native breed, genetically closest to prehistoric wild horses"},
    {"name": "Sable Island Horses", "lat": 43.9337, "lon": -59.9149, "country": "Canada", "region": "Sable Island, Nova Scotia", "population": 500, "status": "Protected", "breed": "Sable Island Horse", "notes": "Feral horses on a remote sandbar island 300km off Nova Scotia, protected by law since 1960"},
    {"name": "Danube Delta Horses", "lat": 45.2500, "lon": 29.7500, "country": "Romania", "region": "Letea Forest, Danube Delta", "population": 4500, "status": "Semi-wild", "breed": "Letea Horse", "notes": "Feral horses in Europe's largest wetland, descended from Tatar horses"},
    {"name": "Nokota Horses", "lat": 47.6000, "lon": -103.5000, "country": "USA", "region": "Theodore Roosevelt NP, ND", "population": 200, "status": "Managed", "breed": "Nokota", "notes": "Descendants of Sitting Bull's horses, managed in national park badlands"},
    {"name": "Retuertas Horses", "lat": 36.9700, "lon": -6.4300, "country": "Spain", "region": "Donana National Park", "population": 300, "status": "Endangered", "breed": "Retuertas", "notes": "Possibly Europe's oldest horse breed, living wild in Donana marshlands"},
    {"name": "Kaimanawa Horses", "lat": -39.0000, "lon": 175.9167, "country": "New Zealand", "region": "Kaimanawa Ranges", "population": 300, "status": "Managed", "breed": "Kaimanawa", "notes": "Wild horses in volcanic plateau, mustered every 2 years to manage population"},
    {"name": "Giara Horses", "lat": 39.7500, "lon": 8.9167, "country": "Italy", "region": "Giara di Gesturi, Sardinia", "population": 700, "status": "Protected", "breed": "Giara Pony", "notes": "Ancient Sardinian ponies living on a high basalt plateau since prehistoric times"},
    {"name": "Dulmen Ponies", "lat": 51.8333, "lon": 7.2833, "country": "Germany", "region": "Merfelder Bruch, Westphalia", "population": 400, "status": "Managed", "breed": "Dulmen Pony", "notes": "Last wild ponies in Germany, annual roundup since 1907 by Duke of Croy"},
    {"name": "Garrano Ponies", "lat": 41.7500, "lon": -8.2500, "country": "Portugal", "region": "Peneda-Geres National Park", "population": 1500, "status": "Endangered", "breed": "Garrano", "notes": "Ancient Iberian pony, depicted in Paleolithic cave art, critically endangered"},
    {"name": "Konik Horses - Oostvaardersplassen", "lat": 52.4333, "lon": 5.3667, "country": "Netherlands", "region": "Flevoland", "population": 1100, "status": "Semi-wild", "breed": "Konik", "notes": "Polish primitive horses used in rewilding projects, closest living relative to Tarpan"},
    {"name": "Misaki Horses", "lat": 31.3667, "lon": 131.3667, "country": "Japan", "region": "Cape Toi, Miyazaki", "population": 100, "status": "Protected", "breed": "Misaki", "notes": "National Natural Monument of Japan, feral since 1697, smallest wild horse population in Japan"},
    {"name": "Pottoka Ponies", "lat": 43.2500, "lon": -1.5000, "country": "Spain/France", "region": "Basque Country/Pyrenees", "population": 2500, "status": "Endangered", "breed": "Pottoka", "notes": "Ancient Basque pony, semi-wild in Pyrenees, may date to Paleolithic era"},
    {"name": "Alberta Wildies", "lat": 52.0000, "lon": -115.5000, "country": "Canada", "region": "Rocky Mountain Foothills, AB", "population": 1000, "status": "Controversial", "breed": "Feral mixed", "notes": "Feral horses in Alberta foothills, protected by provincial law since 2011"},
    {"name": "Skyros Ponies", "lat": 38.9000, "lon": 24.5500, "country": "Greece", "region": "Skyros Island", "population": 250, "status": "Critically Endangered", "breed": "Skyros Pony", "notes": "Tiny ancient Greek pony, may be depicted on Parthenon frieze, under 200 on island"},
    {"name": "Carneddau Ponies", "lat": 53.2000, "lon": -3.9500, "country": "UK", "region": "Snowdonia, Wales", "population": 300, "status": "Semi-wild", "breed": "Carneddau", "notes": "Ancient Welsh mountain ponies roaming the Carneddau range for over 500 years"},
    {"name": "Chilcotin Wild Horses", "lat": 52.0000, "lon": -123.5000, "country": "Canada", "region": "Brittany Triangle, BC", "population": 1500, "status": "Managed", "breed": "Feral mixed", "notes": "Remote wild horses in British Columbia interior, descended from ranching stock"},
    {"name": "Sorraias", "lat": 38.8000, "lon": -7.8000, "country": "Portugal", "region": "Sorraia River Valley", "population": 200, "status": "Critically Endangered", "breed": "Sorraia", "notes": "Extremely rare primitive Iberian horse, grulla/dun with zebra striping on legs"},
    {"name": "Eriskay Ponies", "lat": 57.0700, "lon": -7.3000, "country": "UK", "region": "Eriskay, Outer Hebrides", "population": 420, "status": "Endangered", "breed": "Eriskay Pony", "notes": "Rarest Scottish pony, grey ponies of the Hebridean islands, used by crofters for centuries"},
]

# ═══════════════════════════════════════════════════════════════
# 7. HORSE RACING TRIPLE CROWNS
# ═══════════════════════════════════════════════════════════════
TRIPLE_CROWNS = [
    {"name": "Kentucky Derby (US Triple Crown Leg 1)", "lat": 38.2025, "lon": -85.7706, "country": "USA", "city": "Louisville, KY", "track": "Churchill Downs", "distance": "1.25 miles", "surface": "Dirt", "first_run": 1875, "tc_winners": 13, "last_tc": "Justify (2018)", "notes": "The Run for the Roses, first Saturday in May, mint juleps and elaborate hats"},
    {"name": "Preakness Stakes (US Triple Crown Leg 2)", "lat": 39.3492, "lon": -76.6536, "country": "USA", "city": "Baltimore, MD", "track": "Pimlico", "distance": "1.1875 miles", "surface": "Dirt", "first_run": 1873, "tc_winners": 13, "last_tc": "Justify (2018)", "notes": "The Run for the Black-Eyed Susans, weather vane tradition, Infield Fest"},
    {"name": "Belmont Stakes (US Triple Crown Leg 3)", "lat": 40.6716, "lon": -73.7185, "country": "USA", "city": "Elmont, NY", "track": "Belmont Park", "distance": "1.5 miles", "surface": "Dirt", "first_run": 1867, "tc_winners": 13, "last_tc": "Justify (2018)", "notes": "Test of the Champion, longest of three legs, Secretariat's 31-length victory in 1973"},
    {"name": "2000 Guineas (UK Triple Crown Leg 1)", "lat": 52.2450, "lon": 0.3853, "country": "UK", "city": "Newmarket", "track": "Rowley Mile", "distance": "1 mile", "surface": "Turf", "first_run": 1809, "tc_winners": 15, "last_tc": "Nijinsky (1970)", "notes": "First British Classic, test of speed over the Rowley Mile straight course"},
    {"name": "The Derby (UK Triple Crown Leg 2)", "lat": 51.3127, "lon": -0.2614, "country": "UK", "city": "Epsom", "track": "Epsom Downs", "distance": "1.5 miles", "surface": "Turf", "first_run": 1780, "tc_winners": 15, "last_tc": "Nijinsky (1970)", "notes": "The original Derby, Blue Riband of the Turf, undulating course with Tattenham Corner"},
    {"name": "St Leger Stakes (UK Triple Crown Leg 3)", "lat": 53.5228, "lon": -1.1040, "country": "UK", "city": "Doncaster", "track": "Doncaster", "distance": "1.75 miles", "surface": "Turf", "first_run": 1776, "tc_winners": 15, "last_tc": "Nijinsky (1970)", "notes": "Oldest Classic, world's oldest horse race still run, test of stamina"},
    {"name": "Poule d'Essai des Poulains (French TC Leg 1)", "lat": 48.8566, "lon": 2.2300, "country": "France", "city": "Paris", "track": "Longchamp", "distance": "1600m", "surface": "Turf", "first_run": 1840, "tc_winners": 6, "last_tc": "Zarkava (2008 filly TC)", "notes": "French 2000 Guineas equivalent, colts classic on the Seine"},
    {"name": "Prix du Jockey Club (French TC Leg 2)", "lat": 49.1896, "lon": 2.4715, "country": "France", "city": "Chantilly", "track": "Chantilly", "distance": "2100m", "surface": "Turf", "first_run": 1836, "tc_winners": 6, "last_tc": "Camelot (near-miss 2012)", "notes": "French Derby equivalent, run amid the forests of Chantilly"},
    {"name": "Prix Royal-Oak (French TC Leg 3)", "lat": 48.8566, "lon": 2.2300, "country": "France", "city": "Paris", "track": "Longchamp", "distance": "3100m", "surface": "Turf", "first_run": 1861, "tc_winners": 6, "last_tc": "N/A (rare)", "notes": "French St Leger equivalent, grueling test of stamina at Longchamp"},
    {"name": "Satsuki Sho (Japanese TC Leg 1)", "lat": 35.7603, "lon": 139.9483, "country": "Japan", "city": "Funabashi", "track": "Nakayama", "distance": "2000m", "surface": "Turf", "first_run": 1939, "tc_winners": 8, "last_tc": "Contrail (2020)", "notes": "Japanese 2000 Guineas, springtime classic at Nakayama"},
    {"name": "Tokyo Yushun (Japanese TC Leg 2)", "lat": 35.6614, "lon": 139.4831, "country": "Japan", "city": "Fuchu", "track": "Tokyo", "distance": "2400m", "surface": "Turf", "first_run": 1932, "tc_winners": 8, "last_tc": "Contrail (2020)", "notes": "Japanese Derby, the most prestigious race in Japanese racing"},
    {"name": "Kikuka Sho (Japanese TC Leg 3)", "lat": 34.9132, "lon": 135.6965, "country": "Japan", "city": "Kyoto", "track": "Kyoto", "distance": "3000m", "surface": "Turf", "first_run": 1938, "tc_winners": 8, "last_tc": "Contrail (2020)", "notes": "Japanese St Leger, autumn classic at Kyoto, ultimate stamina test"},
    {"name": "Queen's Plate (Canadian TC Leg 1)", "lat": 43.7161, "lon": -79.6028, "country": "Canada", "city": "Toronto", "track": "Woodbine", "distance": "1.25 miles", "surface": "Synthetic", "first_run": 1860, "tc_winners": 7, "last_tc": "With Approval (1989)", "notes": "North America's oldest continuously run thoroughbred stakes race"},
    {"name": "Prince of Wales Stakes (Canadian TC Leg 2)", "lat": 42.9849, "lon": -79.0656, "country": "Canada", "city": "Fort Erie, ON", "track": "Fort Erie", "distance": "1.1875 miles", "surface": "Dirt", "first_run": 1929, "tc_winners": 7, "last_tc": "With Approval (1989)", "notes": "Second jewel of the Canadian Triple Crown at Fort Erie"},
    {"name": "Breeders' Stakes (Canadian TC Leg 3)", "lat": 43.7161, "lon": -79.6028, "country": "Canada", "city": "Toronto", "track": "Woodbine", "distance": "1.5 miles", "surface": "Turf", "first_run": 1889, "tc_winners": 7, "last_tc": "With Approval (1989)", "notes": "Longest of the Canadian Triple Crown legs, turf surface unique among TCs"},
    {"name": "Gran Premio Jockey Club (Argentine TC Leg 1)", "lat": -34.4708, "lon": -58.5136, "country": "Argentina", "city": "Buenos Aires", "track": "San Isidro", "distance": "2000m", "surface": "Turf", "first_run": 1883, "tc_winners": 10, "last_tc": "Recent", "notes": "Opening classic of South American racing season"},
    {"name": "Gran Premio Nacional (Argentine TC Leg 2)", "lat": -34.6158, "lon": -58.4333, "country": "Argentina", "city": "Buenos Aires", "track": "Palermo", "distance": "2500m", "surface": "Turf", "first_run": 1884, "tc_winners": 10, "last_tc": "Recent", "notes": "Argentine Derby at the Palermo Hippodrome, heart of BA"},
    {"name": "Gran Premio Carlos Pellegrini (Argentine TC Leg 3)", "lat": -34.4708, "lon": -58.5136, "country": "Argentina", "city": "Buenos Aires", "track": "San Isidro", "distance": "2400m", "surface": "Turf", "first_run": 1887, "tc_winners": 10, "last_tc": "Recent", "notes": "South America's most prestigious race, crowning jewel of Argentine racing"},
    {"name": "Australian Guineas (AUS TC Leg 1)", "lat": -37.8483, "lon": 144.9765, "country": "Australia", "city": "Melbourne", "track": "Flemington", "distance": "1600m", "surface": "Turf", "first_run": 1868, "tc_winners": 4, "last_tc": "Might and Power era", "notes": "First leg of the informal Australian Triple Crown at Flemington"},
    {"name": "Melbourne Cup (AUS Triple Crown Leg)", "lat": -37.7886, "lon": 144.9120, "country": "Australia", "city": "Melbourne", "track": "Flemington", "distance": "3200m", "surface": "Turf", "first_run": 1861, "tc_winners": 4, "last_tc": "Makybe Diva (3 Cups)", "notes": "The race that stops a nation, public holiday in Melbourne, 3200m handicap"},
    {"name": "Caulfield Cup (AUS Triple Crown Leg)", "lat": -37.8767, "lon": 145.0222, "country": "Australia", "city": "Melbourne", "track": "Caulfield", "distance": "2400m", "surface": "Turf", "first_run": 1879, "tc_winners": 4, "last_tc": "Vintage era", "notes": "Caulfield Cup-Melbourne Cup double is the most coveted Australian double"},
    {"name": "Cox Plate (Iconic AUS Race)", "lat": -37.8400, "lon": 144.8608, "country": "Australia", "city": "Melbourne", "track": "Moonee Valley", "distance": "2040m", "surface": "Turf", "first_run": 1922, "tc_winners": 0, "last_tc": "N/A (standalone)", "notes": "Weight-for-age championship, tight Moonee Valley circuit, Winx won 4 consecutive"},
    {"name": "SA Triple Tiara Leg - Doha 3000 Guineas", "lat": -26.1076, "lon": 28.0567, "country": "South Africa", "city": "Johannesburg", "track": "Turffontein", "distance": "1600m", "surface": "Turf", "first_run": 1902, "tc_winners": 5, "last_tc": "Recent", "notes": "First leg of South African Triple Crown at the Turffontein course"},
    {"name": "Hong Kong Triple Crown Leg 1 - Stewards Cup", "lat": 22.3964, "lon": 114.2042, "country": "Hong Kong", "city": "Sha Tin", "track": "Sha Tin", "distance": "1600m", "surface": "Turf", "first_run": 1993, "tc_winners": 2, "last_tc": "Recent", "notes": "Opening leg of HK Triple Crown, premier Group 1 mile race in Asia"},
    {"name": "Dubai World Cup", "lat": 25.1652, "lon": 55.3055, "country": "UAE", "city": "Dubai", "track": "Meydan", "distance": "2000m", "surface": "Dirt", "first_run": 1996, "tc_winners": 0, "last_tc": "N/A (standalone)", "notes": "World's richest race day ($30M+ purse), night racing under lights at Meydan"},
]

# ═══════════════════════════════════════════════════════════════
# 8. STUD FARMS & BREEDING CENTERS
# ═══════════════════════════════════════════════════════════════
STUD_FARMS = [
    {"name": "Coolmore Stud", "lat": 52.4500, "lon": -8.0833, "country": "Ireland", "city": "Fethard, Co. Tipperary", "founded": 1975, "specialty": "Thoroughbred", "famous_horses": "Galileo, Sadler's Wells", "notes": "World's largest thoroughbred breeding operation, global empire spanning 3 continents"},
    {"name": "Darley (Dalham Hall Stud)", "lat": 52.2500, "lon": 0.3750, "country": "UK", "city": "Newmarket", "founded": 1981, "specialty": "Thoroughbred", "famous_horses": "Dubawi, Frankel (retired here)", "notes": "Sheikh Mohammed's global breeding operation, Godolphin racing arm"},
    {"name": "Juddmonte Farms", "lat": 52.2400, "lon": 0.3700, "country": "UK", "city": "Newmarket", "founded": 1980, "specialty": "Thoroughbred", "famous_horses": "Frankel, Enable", "notes": "Prince Khalid bin Abdullah's operation, bred the unbeaten Frankel"},
    {"name": "Claiborne Farm", "lat": 38.2100, "lon": -84.2200, "country": "USA", "city": "Paris, KY", "founded": 1910, "specialty": "Thoroughbred", "famous_horses": "Secretariat (buried here), Bold Ruler", "notes": "Legendary Bluegrass farm where Secretariat is buried, family-run since 1910"},
    {"name": "Ashford Stud (Coolmore America)", "lat": 38.2306, "lon": -84.7100, "country": "USA", "city": "Versailles, KY", "founded": 1982, "specialty": "Thoroughbred", "famous_horses": "American Pharoah, Uncle Mo", "notes": "Coolmore's American arm in the heart of Kentucky horse country"},
    {"name": "Haras de Saint-Pair", "lat": 48.8200, "lon": 0.1500, "country": "France", "city": "Normandy", "founded": 1920, "specialty": "Thoroughbred", "famous_horses": "Multiple classic winners", "notes": "Historic Norman stud in the heart of French breeding country"},
    {"name": "National Stud (UK)", "lat": 52.2350, "lon": 0.3650, "country": "UK", "city": "Newmarket", "founded": 1916, "specialty": "Thoroughbred", "famous_horses": "Mill Reef, Oh So Sharp", "notes": "Government-founded to ensure quality bloodlines, now educational center too"},
    {"name": "Shadai Stallion Station", "lat": 42.9000, "lon": 142.5000, "country": "Japan", "city": "Shizunai, Hokkaido", "founded": 1962, "specialty": "Thoroughbred", "famous_horses": "Deep Impact, Sunday Silence", "notes": "Japan's most important stud farm, home of the legendary Sunday Silence"},
    {"name": "Gestut Schlenderhan", "lat": 50.8333, "lon": 6.9000, "country": "Germany", "city": "Bergheim", "founded": 1869, "specialty": "Thoroughbred", "famous_horses": "Monsun, Acatenango", "notes": "Germany's oldest and most prestigious private stud, 150+ years of breeding"},
    {"name": "Real Yeguada de la Cartuja", "lat": 36.7400, "lon": -6.1600, "country": "Spain", "city": "Jerez de la Frontera", "founded": 1476, "specialty": "Andalusian (PRE)", "notes": "Oldest stud farm in Europe, Carthusian monks preserved the purest Spanish bloodlines", "famous_horses": "Carthusian Andalusians"},
    {"name": "Tersk Stud", "lat": 44.1167, "lon": 43.5833, "country": "Russia", "city": "Mineralnye Vody", "founded": 1921, "specialty": "Arabian", "famous_horses": "Aswan, Menes, Muscat", "notes": "Premier Russian Arabian stud, Stalin ordered preservation of prize Arabians"},
    {"name": "Al Shaqab", "lat": 25.3200, "lon": 51.4400, "country": "Qatar", "city": "Doha", "founded": 1992, "specialty": "Arabian", "famous_horses": "Multiple World Champions", "notes": "Qatar Foundation's world-class Arabian breeding and equestrian center"},
    {"name": "El Zahraa Stud", "lat": 30.0500, "lon": 31.2400, "country": "Egypt", "city": "Cairo", "founded": 1928, "specialty": "Egyptian Arabian", "famous_horses": "Nazeer, Morafic", "notes": "Egypt's national stud, guardian of pure Egyptian Arabian bloodlines"},
    {"name": "Wentworth Stud", "lat": -33.8900, "lon": 150.5200, "country": "Australia", "city": "Dural, NSW", "founded": 1947, "specialty": "Arabian", "famous_horses": "Dorodnic, Dorodnica", "notes": "One of Australia's oldest Arabian studs, preserving Crabbet bloodlines"},
    {"name": "Pompadour National Stud", "lat": 45.4000, "lon": 1.3833, "country": "France", "city": "Pompadour, Correze", "founded": 1761, "specialty": "Anglo-Arab", "famous_horses": "Anglo-Arabian stallions", "notes": "Founded by Marquise de Pompadour, France's national Anglo-Arab breeding center"},
    {"name": "Celle State Stud", "lat": 52.6236, "lon": 10.0856, "country": "Germany", "city": "Celle, Lower Saxony", "founded": 1735, "specialty": "Hanoverian", "famous_horses": "Foundation Hanoverian stallions", "notes": "Birthplace of the Hanoverian breed, 300 stallions at peak, founded by George II"},
    {"name": "Lipica Stud Farm", "lat": 45.5469, "lon": 14.2136, "country": "Slovenia", "city": "Lipica", "founded": 1580, "specialty": "Lipizzan", "famous_horses": "Lipizzan foundation bloodlines", "notes": "Original Lipizzan stud farm founded by Archduke Charles, home of the white dancing horses"},
    {"name": "Piber Federal Stud", "lat": 47.0833, "lon": 15.0167, "country": "Austria", "city": "Piber, Styria", "founded": 1920, "specialty": "Lipizzan", "famous_horses": "Spanish Riding School stallions", "notes": "Breeds all stallions for the Spanish Riding School of Vienna"},
    {"name": "Marbach State Stud", "lat": 48.4833, "lon": 9.6167, "country": "Germany", "city": "Gomadingen", "founded": 1573, "specialty": "Warmblood/Arabian", "famous_horses": "Swabian-bred warmbloods", "notes": "Oldest state stud in Germany, beautiful Swabian Alb location, over 450 years old"},
    {"name": "Calumet Farm", "lat": 38.1100, "lon": -84.5100, "country": "USA", "city": "Lexington, KY", "founded": 1924, "specialty": "Thoroughbred", "famous_horses": "Alydar, Citation, Whirlaway", "notes": "Iconic Bluegrass farm with white fences and red devil weathervanes, 8 Kentucky Derby winners"},
    {"name": "Aga Khan Studs", "lat": 48.5100, "lon": 2.3200, "country": "France", "city": "Aiglemont, Gouvieux", "founded": 1920, "specialty": "Thoroughbred", "famous_horses": "Shergar, Sinndar, Zarkava", "notes": "Four generations of Aga Khans breeding champions, one of the great European operations"},
    {"name": "Pin National Stud (Haras du Pin)", "lat": 48.7333, "lon": 0.1500, "country": "France", "city": "Le Pin-au-Haras", "founded": 1715, "specialty": "Multiple breeds", "famous_horses": "Percheron, Norman Cob stallions", "notes": "The Versailles of Horse Country, Louis XIV's grand stud, spectacular architecture"},
    {"name": "Arrowfield Stud", "lat": -32.2167, "lon": 150.8333, "country": "Australia", "city": "Upper Hunter Valley", "founded": 1954, "specialty": "Thoroughbred", "famous_horses": "Snitzel, Redoute's Choice", "notes": "Australia's premier thoroughbred stud in the Hunter Valley wine region"},
    {"name": "Lane's End Farm", "lat": 38.2000, "lon": -84.3100, "country": "USA", "city": "Versailles, KY", "founded": 1979, "specialty": "Thoroughbred", "famous_horses": "A.P. Indy, Curlin", "notes": "Premier Kentucky stallion farm, A.P. Indy dynasty, bourbon country"},
    {"name": "Ballylinch Stud", "lat": 52.6600, "lon": -7.2200, "country": "Ireland", "city": "Thomastown, Co. Kilkenny", "founded": 1978, "specialty": "Thoroughbred", "famous_horses": "Lope de Vega", "notes": "Premium Irish stud on the banks of the River Nore, Aga Khan associated"},
]

# ═══════════════════════════════════════════════════════════════
# 9. HORSE MUSEUMS & MONUMENTS
# ═══════════════════════════════════════════════════════════════
HORSE_MUSEUMS = [
    {"name": "National Horse Racing Museum", "lat": 52.2450, "lon": 0.4050, "country": "UK", "city": "Newmarket", "type": "Museum", "focus": "Thoroughbred racing history", "notes": "In the headquarters of British racing, tours of historic training yards"},
    {"name": "Kentucky Horse Park", "lat": 38.1500, "lon": -84.5000, "country": "USA", "city": "Lexington, KY", "type": "Park/Museum", "focus": "All horse breeds and disciplines", "notes": "1,200-acre park with International Museum of the Horse, Man o' War buried here"},
    {"name": "Bronze Horseman (Peter the Great)", "lat": 59.9364, "lon": 30.3022, "country": "Russia", "city": "St. Petersburg", "type": "Monument", "focus": "Equestrian statue", "notes": "Iconic 1782 equestrian statue of Peter the Great, symbol of St. Petersburg"},
    {"name": "Spanish Riding School Museum", "lat": 48.2082, "lon": 16.3669, "country": "Austria", "city": "Vienna", "type": "Museum/School", "focus": "Classical dressage", "notes": "Performing Lipizzan stallions since 1572, Baroque art of haute ecole"},
    {"name": "Musee Vivant du Cheval (Living Horse Museum)", "lat": 49.1900, "lon": 2.4850, "country": "France", "city": "Chantilly", "type": "Museum", "focus": "Horse art and breeds", "notes": "In the Great Stables of Chantilly, said to be the most beautiful stables in the world"},
    {"name": "National Museum of Racing and Hall of Fame", "lat": 43.0780, "lon": -73.7850, "country": "USA", "city": "Saratoga Springs, NY", "type": "Museum", "focus": "American thoroughbred racing", "notes": "Hall of Fame for jockeys, trainers, and horses, adjacent to Saratoga Race Course"},
    {"name": "Australian National Equine Museum", "lat": -33.9042, "lon": 151.2383, "country": "Australia", "city": "Randwick, Sydney", "type": "Museum", "focus": "Australian racing heritage", "notes": "Inside Randwick Racecourse, housing Phar Lap memorabilia"},
    {"name": "Phar Lap Display (Melbourne Museum)", "lat": -37.8033, "lon": 144.9717, "country": "Australia", "city": "Melbourne", "type": "Museum exhibit", "focus": "Phar Lap's preserved hide", "notes": "Taxidermied hide of Australia's most famous racehorse, national treasure"},
    {"name": "The Uffington White Horse", "lat": 51.5777, "lon": -1.5667, "country": "UK", "city": "Oxfordshire", "type": "Monument/Hill figure", "focus": "Prehistoric horse carving", "notes": "3,000-year-old Bronze Age chalk horse carved into hillside, 110m long"},
    {"name": "Crazy Horse Memorial", "lat": 43.8364, "lon": -103.6253, "country": "USA", "city": "Black Hills, SD", "type": "Monument", "focus": "Native American horse culture", "notes": "Mountain carving of Crazy Horse on horseback, larger than Mt. Rushmore when complete"},
    {"name": "Equus (Horse) Statue at Meydan", "lat": 25.1652, "lon": 55.3055, "country": "UAE", "city": "Dubai", "type": "Monument", "focus": "Modern equestrian art", "notes": "Spectacular horse sculptures at the world's richest racecourse"},
    {"name": "Museo del Enganche (Carriage Museum)", "lat": 37.3886, "lon": -5.9953, "country": "Spain", "city": "Seville", "type": "Museum", "focus": "Horse carriages", "notes": "Royal carriages and equestrian heritage at the Plaza de Espana"},
    {"name": "National Horseracing Museum of Japan", "lat": 35.6614, "lon": 139.4831, "country": "Japan", "city": "Fuchu, Tokyo", "type": "Museum", "focus": "Japanese racing history", "notes": "Inside Tokyo Racecourse, chronicles the history of racing in Japan"},
    {"name": "Cavalry Museum (Musee de la Cavalerie)", "lat": 47.2600, "lon": -0.0766, "country": "France", "city": "Saumur", "type": "Museum", "focus": "French cavalry & Cadre Noir", "notes": "French military riding tradition, home of the Cadre Noir elite riders"},
    {"name": "Marcus Aurelius Equestrian Statue", "lat": 41.8932, "lon": 12.4828, "country": "Italy", "city": "Rome", "type": "Monument", "focus": "Roman equestrian statue", "notes": "Greatest surviving ancient bronze equestrian statue, Capitoline Museums, c. 175 AD"},
    {"name": "Terracotta Cavalry Horses", "lat": 34.3847, "lon": 109.2785, "country": "China", "city": "Xi'an", "type": "Archaeological site", "focus": "Ancient war horses", "notes": "600+ life-sized terracotta horses from Emperor Qin's army, 2,200 years old"},
    {"name": "Kelpies Sculpture", "lat": 56.0167, "lon": -3.7500, "country": "UK", "city": "Falkirk, Scotland", "type": "Monument", "focus": "Horse-headed sculptures", "notes": "30-meter-tall steel horse head sculptures, largest equine sculptures in the world"},
    {"name": "Janjanbureh Horse Monument", "lat": 13.5400, "lon": -14.7700, "country": "Gambia", "city": "Janjanbureh", "type": "Monument", "focus": "Colonial horse heritage", "notes": "Commemorating the role of horses in West African trade and transport"},
    {"name": "Przewalski Horse Museum", "lat": 47.7500, "lon": 107.0000, "country": "Mongolia", "city": "Hustai National Park", "type": "Museum", "focus": "Wild horse conservation", "notes": "Documenting the rescue and reintroduction of the world's last truly wild horse"},
    {"name": "Haras National du Pin (Horse Museum)", "lat": 48.7333, "lon": 0.1500, "country": "France", "city": "Le Pin-au-Haras", "type": "Museum/Stud", "focus": "French horse breeds", "notes": "The Versailles of the Horse, 250-hectare estate with carriage museum and stud"},
    {"name": "Arab Horse Museum", "lat": 25.3548, "lon": 51.1839, "country": "Qatar", "city": "Al Shaqab, Doha", "type": "Museum", "focus": "Arabian horse heritage", "notes": "World-class museum of Arabian horse breed history and Bedouin culture"},
    {"name": "Elgin Marbles - Parthenon Horse", "lat": 51.5194, "lon": -0.1270, "country": "UK", "city": "London", "type": "Museum exhibit", "focus": "Ancient Greek horse art", "notes": "Parthenon frieze showing cavalcade of horsemen, British Museum, c. 440 BC"},
    {"name": "Turkmen Horse Museum", "lat": 37.9600, "lon": 58.3261, "country": "Turkmenistan", "city": "Ashgabat", "type": "Museum", "focus": "Akhal-Teke breed", "notes": "Dedicated to the legendary golden Akhal-Teke, national symbol of Turkmenistan"},
    {"name": "Lipizzan Heritage Museum", "lat": 45.5469, "lon": 14.2136, "country": "Slovenia", "city": "Lipica", "type": "Museum", "focus": "Lipizzan breed history", "notes": "At the original Lipica stud, tracing the breed from 1580 to present"},
    {"name": "Musee du Cheval (Tarbes)", "lat": 43.2333, "lon": 0.0833, "country": "France", "city": "Tarbes", "type": "Museum", "focus": "Pyrenean horse culture", "notes": "Haras national stud museum, Anglo-Arab breeding heritage of southwestern France"},
    {"name": "Statue of Genghis Khan", "lat": 47.8078, "lon": 107.5303, "country": "Mongolia", "city": "Tsonjin Boldog", "type": "Monument", "focus": "Mongol horse empire", "notes": "40m tall stainless steel equestrian statue, world's tallest equestrian statue"},
]

# ═══════════════════════════════════════════════════════════════
# 10. NOMADIC HORSE CULTURES
# ═══════════════════════════════════════════════════════════════
NOMADIC_CULTURES = [
    {"name": "Mongolian Nomads", "lat": 47.9213, "lon": 106.9075, "country": "Mongolia", "region": "Mongolian Steppe", "tradition": "Naadam Festival Racing", "horse_breed": "Mongolian Horse", "population": "1,000,000+ nomads", "notes": "Children as young as 5 race horses 15-30km, horse culture central to identity, 4M+ horses"},
    {"name": "Kazakh Eagle Hunters", "lat": 48.5000, "lon": 89.0000, "country": "Mongolia/Kazakhstan", "region": "Altai Mountains", "tradition": "Kokpar, Eagle Hunting on horseback", "horse_breed": "Kazakh Horse", "population": "200,000 Kazakh nomads", "notes": "Golden eagle hunting from horseback, kokpar (dead goat polo), ancient Turkic tradition"},
    {"name": "Bedouin Horse Culture", "lat": 23.8859, "lon": 45.0792, "country": "Saudi Arabia", "region": "Arabian Desert", "tradition": "Tent sharing with horses", "horse_breed": "Arabian", "population": "Declining nomadic", "notes": "Bred the Arabian horse over millennia, horses lived inside Bedouin tents, ultimate bond"},
    {"name": "Comanche Horse Warriors", "lat": 34.6000, "lon": -98.4000, "country": "USA", "region": "Southern Plains", "tradition": "Lords of the Southern Plains", "horse_breed": "Spanish Mustang", "population": "17,000 tribal members", "notes": "Greatest horse warriors in North America, transformed by the horse from 1700s onward"},
    {"name": "Gaucho Culture", "lat": -34.6037, "lon": -58.3816, "country": "Argentina", "region": "Pampas", "tradition": "Pato, cattle herding, rodeo", "horse_breed": "Criollo", "population": "Cultural tradition", "notes": "South American cowboys, born in the saddle, national symbol of Argentina and Uruguay"},
    {"name": "Csikos (Hungarian Cowboys)", "lat": 47.0000, "lon": 21.5000, "country": "Hungary", "region": "Hortobagy Puszta", "tradition": "10-horse hitch, Puszta Five", "horse_breed": "Nonius, Shagya Arabian", "population": "Cultural tradition", "notes": "Standing Roman-riding on 5 horses simultaneously, UNESCO Intangible Heritage of Hortobagy"},
    {"name": "Buzkashi Players", "lat": 36.7000, "lon": 69.0000, "country": "Afghanistan", "region": "Northern Afghanistan", "tradition": "Buzkashi (goat grabbing)", "horse_breed": "Central Asian breeds", "population": "Cultural tradition", "notes": "National sport, horsemen fight over headless goat carcass, extreme mounted competition"},
    {"name": "Turkmen Horse Culture", "lat": 38.9697, "lon": 59.5563, "country": "Turkmenistan", "region": "Karakum Desert", "tradition": "Akhal-Teke racing, At Chabysh", "horse_breed": "Akhal-Teke", "population": "5M+ population", "notes": "Horse on national emblem and currency, Akhal-Teke is the golden symbol of Turkmenistan"},
    {"name": "Kyrgyz Horse Games", "lat": 42.8746, "lon": 74.5698, "country": "Kyrgyzstan", "region": "Tien Shan Mountains", "tradition": "Kok-boru, Kyz Kuumai", "horse_breed": "Kyrgyz Horse", "population": "Cultural tradition", "notes": "Dead goat polo (kok-boru) is national sport, bride chasing (kyz kuumai) on horseback"},
    {"name": "Maasai Horse Culture (recent)", "lat": -2.5000, "lon": 36.0000, "country": "Kenya/Tanzania", "region": "East African Rift", "tradition": "Safari guide riding", "horse_breed": "Various", "population": "1M+ Maasai", "notes": "Traditional cattle herders now also using horses for eco-tourism and conservation patrols"},
    {"name": "Camargue Gardians", "lat": 43.5000, "lon": 4.5000, "country": "France", "region": "Camargue Delta", "tradition": "Bull herding, Abrivado", "horse_breed": "Camargue", "population": "Cultural tradition", "notes": "French cowboys herding black bulls on white Camargue horses through marshes and surf"},
    {"name": "Tibetan Horsemen", "lat": 31.5000, "lon": 91.0000, "country": "China/Tibet", "region": "Tibetan Plateau", "tradition": "Nagqu Horse Festival", "horse_breed": "Tibetan Pony", "population": "6M+ Tibetans", "notes": "Highest horse culture in the world, Nagqu festival at 15,000 ft, horse archery and racing"},
    {"name": "Lakota Horse Culture", "lat": 44.0000, "lon": -102.0000, "country": "USA", "region": "Great Plains, South Dakota", "tradition": "Buffalo hunting on horseback", "horse_breed": "Indian Pony/Paint", "population": "170,000 tribal members", "notes": "Horse transformed Plains Indian life, spiritual connection between warrior and horse"},
    {"name": "Rajput Horse Warriors", "lat": 26.9124, "lon": 75.7873, "country": "India", "region": "Rajasthan", "tradition": "Marwari horse festivals", "horse_breed": "Marwari, Kathiawari", "population": "Cultural tradition", "notes": "Rajput warriors and their Marwari horses, elaborate horse fairs at Pushkar and Nagaur"},
    {"name": "Fulani Horsemen", "lat": 12.0000, "lon": -1.5000, "country": "West Africa", "region": "Sahel", "tradition": "Durbar festivals, cattle herding", "horse_breed": "Barb, Dongola", "population": "40M+ Fulani", "notes": "Spectacular Durbar processions with ornately dressed horses, largest nomadic group in world"},
    {"name": "Nez Perce Horse Culture", "lat": 46.4108, "lon": -116.0252, "country": "USA", "region": "Idaho/Pacific NW", "tradition": "Appaloosa breeding", "horse_breed": "Appaloosa", "population": "3,500 tribal members", "notes": "Created the Appaloosa breed through selective breeding, sophisticated horse management"},
    {"name": "Scythian Horse Warriors", "lat": 48.0000, "lon": 68.0000, "country": "Kazakhstan", "region": "Eurasian Steppe (ancient)", "tradition": "Mounted archery, burial with horses", "horse_breed": "Steppe horses", "population": "Ancient civilization", "notes": "Legendary horse archers of antiquity, buried with gold-adorned horses, frozen tombs preserved"},
    {"name": "Cossack Horsemen", "lat": 47.2357, "lon": 39.7015, "country": "Russia", "region": "Don River/Southern Russia", "tradition": "Djigitovka (trick riding)", "horse_breed": "Don Horse, Budyonny", "population": "Cultural tradition", "notes": "Legendary mounted warriors, trick riding standing in saddle, shashka sword horsemanship"},
    {"name": "Aboriginal Stockmen", "lat": -15.0000, "lon": 133.0000, "country": "Australia", "region": "Northern Territory", "tradition": "Cattle mustering, rodeo", "horse_breed": "Stock Horse", "population": "Cultural tradition", "notes": "Indigenous Australians became legendary horsemen on cattle stations, backbone of the outback"},
    {"name": "Chilean Huasos", "lat": -33.4489, "lon": -70.6693, "country": "Chile", "region": "Central Valley", "tradition": "Rodeo, cattle herding", "horse_breed": "Chilean Horse", "population": "Cultural tradition", "notes": "Chilean cowboys with distinctive chamanto ponchos, rodeo is Chile's national sport"},
    {"name": "Vaquero Tradition", "lat": 20.6597, "lon": -103.3496, "country": "Mexico", "region": "Jalisco/Central Mexico", "tradition": "Charreada (Mexican rodeo)", "horse_breed": "Azteca, Quarter Horse", "population": "Cultural tradition", "notes": "Original cowboys predating American cowboys, charreada is Mexico's national sport"},
    {"name": "Polo Tradition of Manipur", "lat": 24.8170, "lon": 93.9368, "country": "India", "region": "Manipur, NE India", "tradition": "Sagol Kangjei (original polo)", "horse_breed": "Manipuri Pony", "population": "Cultural tradition", "notes": "Birthplace of polo, sagol kangjei played for centuries, Manipuri ponies are 12-13 hands"},
    {"name": "Berber Horsemen (Fantasia)", "lat": 33.5731, "lon": -7.5898, "country": "Morocco", "region": "Maghreb", "tradition": "Fantasia/Tbourida", "horse_breed": "Barb", "population": "Cultural tradition", "notes": "Spectacular cavalry charge ritual with synchronized musket firing, UNESCO recognized"},
    {"name": "Yakut Horse People", "lat": 62.0000, "lon": 130.0000, "country": "Russia", "region": "Sakha Republic, Siberia", "tradition": "Kumis drinking, winter survival", "horse_breed": "Yakut Horse", "population": "500,000 Yakut people", "notes": "Horses survive -60C in Siberia, world's most cold-adapted breed, kumis (fermented mare's milk)"},
    {"name": "Basotho Pony Culture", "lat": -29.3100, "lon": 28.4900, "country": "Lesotho", "region": "Mountain Kingdom", "tradition": "Mountain racing, transport", "horse_breed": "Basotho Pony", "population": "2M+ population", "notes": "Mountain kingdom accessible only by pony, annual horse racing festival at Molimo Nthuse"},
]


# ═══════════════════════════════════════════════════════════════
# POPUP BUILDER
# ═══════════════════════════════════════════════════════════════
def _popup_html(title, fields):
    """Build a rich HTML popup string."""
    esc = html_module.escape
    rows = ""
    for label, value in fields:
        rows += f"<tr><td style='padding:3px 8px;color:#06b6d4;font-weight:600;white-space:nowrap;'>{esc(str(label))}</td><td style='padding:3px 8px;color:#e8ecf4;'>{esc(str(value))}</td></tr>"
    return f"""
    <div style="font-family:Inter,system-ui,sans-serif;background:#111827;border:1px solid #2a3550;border-radius:10px;padding:12px;min-width:260px;max-width:340px;">
        <div style="font-size:14px;font-weight:700;color:#06b6d4;margin-bottom:8px;border-bottom:1px solid #2a3550;padding-bottom:6px;">{esc(str(title))}</div>
        <table style="font-size:12px;border-collapse:collapse;">{rows}</table>
    </div>"""


def _build_map(data, popup_fn, center=None, zoom=2):
    """Build a folium map from data list using popup_fn to generate popups."""
    if center is None:
        lats = [d["lat"] for d in data]
        lons = [d["lon"] for d in data]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")
    for item in data:
        popup_content = popup_fn(item)
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=folium.Popup(popup_content, max_width=360),
            icon=folium.Icon(color="green", icon="info-sign"),
        ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_racetracks():
    data = RACETRACKS
    countries = list(set(d["country"] for d in data))
    total_capacity = sum(d["capacity"] for d in data)
    oldest = min(data, key=lambda d: d["founded"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Racetracks", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Total Capacity", f"{total_capacity:,}")
    c4.metric("Oldest", f"{oldest['name']} ({oldest['founded']})")

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Founded", d["founded"]),
            ("Famous Race", d["famous_race"]),
            ("Surface", d["surface"]),
            ("Track Length", f"{d['length_m']}m"),
            ("Capacity", f"{d['capacity']:,}"),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Racetracks CSV", csv, "racetracks.csv", "text/csv")


def _render_breeds():
    data = HORSE_BREEDS
    types = {}
    for d in data:
        types[d["type"]] = types.get(d["type"], 0) + 1
    countries = list(set(d["country"] for d in data))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Breeds", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Hot-blooded", types.get("Hot-blooded", 0))
    c4.metric("Cold-blooded", types.get("Cold-blooded", 0))

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("Country", d["country"]),
            ("Region", d["region"]),
            ("Type", d["type"]),
            ("Height", d["height_hh"] + " hh"),
            ("Uses", d["uses"]),
            ("Population", d["population_est"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Horse Breeds CSV", csv, "horse_breeds.csv", "text/csv")


def _render_polo():
    data = POLO_CLUBS
    countries = list(set(d["country"] for d in data))
    elite = sum(1 for d in data if d["level"] == "Elite")
    oldest = min(data, key=lambda d: d["founded"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Polo Clubs", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Elite Venues", elite)
    c4.metric("Oldest", f"{oldest['name'][:20]}... ({oldest['founded']})")

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Founded", d["founded"]),
            ("Fields", d["fields"]),
            ("Level", d["level"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Polo Clubs CSV", csv, "polo_clubs.csv", "text/csv")


def _render_cavalry():
    data = CAVALRY_SITES
    eras = {}
    for d in data:
        eras[d["era"]] = eras.get(d["era"], 0) + 1
    countries = list(set(d["country"] for d in data))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Battle Sites", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Eras Covered", len(eras))
    c4.metric("Oldest", "Battle of Kadesh (1274 BC)")

    def popup_fn(d):
        yr = f"{abs(d['year'])} {'BC' if d['year'] < 0 else 'AD'}"
        return _popup_html(d["name"], [
            ("Country", d["country"]),
            ("Year", yr),
            ("Era", d["era"]),
            ("Cavalry", d["cavalry_type"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Cavalry Sites CSV", csv, "cavalry_sites.csv", "text/csv")


def _render_olympics():
    data = OLYMPIC_VENUES
    countries = list(set(d["country"] for d in data))
    years = sorted(set(d["year"] for d in data))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venues", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Years Span", f"{years[0]}-{years[-1]}")
    c4.metric("Latest", "Versailles 2024")

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Year", d["year"]),
            ("Events", d["events"]),
            ("Gold Nations", d["gold_nations"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Olympic Venues CSV", csv, "olympic_equestrian.csv", "text/csv")


def _render_wild_horses():
    data = WILD_HORSES
    total_pop = sum(d["population"] for d in data)
    countries = list(set(d["country"] for d in data))
    endangered = sum(1 for d in data if "Endangered" in d["status"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wild Populations", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Est. Total Horses", f"{total_pop:,}")
    c4.metric("Endangered", endangered)

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("Country", d["country"]),
            ("Region", d["region"]),
            ("Population", f"{d['population']:,}"),
            ("Status", d["status"]),
            ("Breed", d["breed"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Wild Horses CSV", csv, "wild_horses.csv", "text/csv")


def _render_triple_crowns():
    data = TRIPLE_CROWNS
    countries = list(set(d["country"] for d in data))
    surfaces = list(set(d["surface"] for d in data))
    oldest = min(data, key=lambda d: d["first_run"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TC Races", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Surface Types", len(surfaces))
    c4.metric("Oldest Race", f"{oldest['name'][:18]}... ({oldest['first_run']})")

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("Track", d["track"]),
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Distance", d["distance"]),
            ("Surface", d["surface"]),
            ("First Run", d["first_run"]),
            ("TC Winners", d["tc_winners"]),
            ("Last TC", d["last_tc"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Triple Crowns CSV", csv, "triple_crowns.csv", "text/csv")


def _render_stud_farms():
    data = STUD_FARMS
    countries = list(set(d["country"] for d in data))
    specialties = list(set(d["specialty"] for d in data))
    oldest = min(data, key=lambda d: d["founded"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stud Farms", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Breed Specialties", len(specialties))
    c4.metric("Oldest", f"{oldest['name'][:18]}... ({oldest['founded']})")

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Founded", d["founded"]),
            ("Specialty", d["specialty"]),
            ("Famous Horses", d["famous_horses"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Stud Farms CSV", csv, "stud_farms.csv", "text/csv")


def _render_museums():
    data = HORSE_MUSEUMS
    countries = list(set(d["country"] for d in data))
    types = list(set(d["type"] for d in data))
    museums = sum(1 for d in data if "Museum" in d["type"])
    monuments = sum(1 for d in data if "Monument" in d["type"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Museums", museums)
    c4.metric("Monuments", monuments)

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Type", d["type"]),
            ("Focus", d["focus"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Horse Museums CSV", csv, "horse_museums.csv", "text/csv")


def _render_nomadic():
    data = NOMADIC_CULTURES
    countries = list(set(d["country"] for d in data))
    breeds = list(set(d["horse_breed"] for d in data))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Horse Cultures", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Horse Breeds", len(breeds))
    c4.metric("Oldest Tradition", "Scythian (~800 BC)")

    def popup_fn(d):
        return _popup_html(d["name"], [
            ("Country", d["country"]),
            ("Region", d["region"]),
            ("Tradition", d["tradition"]),
            ("Horse Breed", d["horse_breed"]),
            ("Population", d["population"]),
            ("Notes", d["notes"]),
        ])
    m = _build_map(data, popup_fn, zoom=2)
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(data).drop(columns=["lat", "lon"])
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Nomadic Cultures CSV", csv, "nomadic_horse_cultures.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def render_horse_maps_tab():
    """Main entry point for the Horses & Equestrian Explorer tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>Horses & Equestrian Explorer</h4>'
        '<p>Famous racetracks, horse breeds, polo clubs, equestrian heritage worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Select Map Mode", [
        "World Famous Racetracks",
        "Horse Breed Origins",
        "Polo Clubs Worldwide",
        "Historic Cavalry & War Horse Sites",
        "Equestrian Olympic Venues",
        "Wild Horse Populations",
        "Horse Racing Triple Crowns",
        "Stud Farms & Breeding Centers",
        "Horse Museums & Monuments",
        "Nomadic Horse Cultures",
    ], key="horse_maps_mode")

    if mode == "World Famous Racetracks":
        _render_racetracks()
    elif mode == "Horse Breed Origins":
        _render_breeds()
    elif mode == "Polo Clubs Worldwide":
        _render_polo()
    elif mode == "Historic Cavalry & War Horse Sites":
        _render_cavalry()
    elif mode == "Equestrian Olympic Venues":
        _render_olympics()
    elif mode == "Wild Horse Populations":
        _render_wild_horses()
    elif mode == "Horse Racing Triple Crowns":
        _render_triple_crowns()
    elif mode == "Stud Farms & Breeding Centers":
        _render_stud_farms()
    elif mode == "Horse Museums & Monuments":
        _render_museums()
    elif mode == "Nomadic Horse Cultures":
        _render_nomadic()
