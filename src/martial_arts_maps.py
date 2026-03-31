# -*- coding: utf-8 -*-
"""
Martial Arts & Combat Sports Maps module for TerraScout AI.
Curated hardcoded database of martial arts origins, schools, training camps,
competition venues, and cultural landmarks worldwide.
10 map modes with 20+ locations each.
"""

import io
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import pandas as pd
import requests
import html as html_module

# ======================================================================
# HISTORICAL CONTEXT PER MODE
# ======================================================================
MODE_HISTORY = {
    "Karate Origins & Dojos": (
        "Karate ('empty hand') originated in the Ryukyu Kingdom (modern Okinawa, Japan) "
        "during the 17th-19th centuries as a blend of indigenous Okinawan fighting "
        "methods (te) and Chinese martial arts. Three main traditions emerged from the "
        "cities of Shuri, Naha, and Tomari. In the early 20th century, karate was "
        "introduced to mainland Japan by masters like Gichin Funakoshi (Shotokan), "
        "Chojun Miyagi (Goju-ryu), Kenwa Mabuni (Shito-ryu), and Hironori Otsuka "
        "(Wado-ryu). After World War II, karate spread globally through US military "
        "personnel stationed in Japan and Okinawa. Today, karate is practiced in over "
        "190 countries and debuted as an Olympic sport at Tokyo 2020."
    ),
    "Kung Fu Temples & Schools": (
        "Chinese martial arts (wushu/kung fu) have roots spanning over 4,000 years. "
        "The legendary Shaolin Temple in Henan province, founded in 495 AD, became "
        "synonymous with martial arts after the monk Bodhidharma reportedly introduced "
        "exercises that evolved into Shaolin kung fu. Wudang Mountain developed internal "
        "styles emphasizing qi cultivation, including Tai Chi Chuan, Bagua Zhang, and "
        "Xingyi Quan. Wing Chun, created according to legend by a Buddhist nun, became "
        "world-famous through Ip Man and his student Bruce Lee. Chinese martial arts "
        "encompass hundreds of distinct styles, broadly categorized as northern (long-range "
        "kicks) and southern (close-range hand techniques), external (hard) and internal "
        "(soft), and further divided by animal mimicry, religious origin, and regional "
        "tradition."
    ),
    "Muay Thai Camps": (
        "Muay Thai ('Thai boxing') is Thailand's national sport and cultural martial art, "
        "with roots dating back to the Ayutthaya Kingdom (1351-1767). Known as the 'Art "
        "of Eight Limbs' for its use of fists, elbows, knees, and shins, Muay Thai "
        "evolved from battlefield combat techniques (Muay Boran). The sport became "
        "formalized in the early 20th century with the introduction of boxing rings, "
        "gloves, and weight classes. The two most prestigious stadiums are Lumpinee "
        "(operated by the Royal Thai Army) and Rajadamnern (the oldest, opened 1945). "
        "In recent decades, Muay Thai has become a global fitness and combat sport "
        "phenomenon, with training camps across Thailand attracting thousands of "
        "international practitioners annually."
    ),
    "Brazilian Jiu-Jitsu Academies": (
        "Brazilian Jiu-Jitsu (BJJ) was developed in Brazil by the Gracie family, who "
        "adapted techniques from Judo and Japanese Jiu-Jitsu learned from Mitsuyo Maeda "
        "in the 1920s. Helio Gracie refined the art to emphasize leverage and technique "
        "over strength, making it effective for smaller practitioners. The Gracie Challenge "
        "matches and Royce Gracie's victories at the early UFC events (1993-1994) "
        "demonstrated BJJ's effectiveness and sparked a worldwide revolution in martial "
        "arts. Today, BJJ is one of the fastest-growing martial arts globally, with "
        "major organizations like Gracie Barra, Alliance, ATOS, and Checkmat operating "
        "thousands of academies. The IBJJF World Championships and ADCC Submission "
        "Wrestling World Championship are the sport's premier events."
    ),
    "Judo & Olympic Venues": (
        "Judo ('the gentle way') was created in 1882 by Jigoro Kano in Tokyo, Japan. "
        "Kano synthesized techniques from various jujutsu schools and added a philosophy "
        "of mutual welfare and maximum efficiency. The Kodokan, Judo's world headquarters, "
        "remains the spiritual home of the art. Judo became the first Asian martial art "
        "in the Olympic Games at Tokyo 1964 and has been a permanent Olympic sport since "
        "1972. Today, the International Judo Federation has over 200 member nations. "
        "Judo's competitive format emphasizes throwing (nage-waza) and groundwork "
        "(ne-waza), with the ultimate goal of achieving ippon (full point). Countries "
        "like Japan, France, South Korea, Georgia, and Brazil are traditional powerhouses."
    ),
    "Taekwondo Origins": (
        "Taekwondo ('the way of the foot and fist') was developed in South Korea in the "
        "1940s-60s, drawing from traditional Korean martial arts (Taekkyeon, Subak) and "
        "Japanese karate. The 'Nine Kwans' (original martial arts schools) were unified "
        "under the Korea Taekwondo Association. Two main branches exist: World Taekwondo "
        "(WT, Olympic style, headquartered at the Kukkiwon) emphasizing speed and "
        "high kicks, and the International Taekwondo Federation (ITF, founded by "
        "General Choi Hong Hi) focusing on self-defense patterns. Taekwondo became an "
        "Olympic sport at Sydney 2000 and is now practiced by over 80 million people "
        "in 210 countries, making it one of the world's most practiced martial arts."
    ),
    "Fencing & Sword Arts": (
        "Sword fighting traditions span virtually every civilization. European fencing "
        "evolved from medieval swordsmanship into a refined art in Renaissance Italy, "
        "Spain, and France, with schools teaching rapier, longsword, and smallsword. "
        "Modern Olympic fencing uses three weapons: foil, epee, and sabre, and has been "
        "in every modern Olympic Games since 1896. Japanese kendo ('way of the sword') "
        "developed from samurai kenjutsu, formalized in the 18th century with bamboo "
        "swords (shinai) and protective armor (bogu). Korean kumdo shares deep "
        "connections with kendo. HEMA (Historical European Martial Arts) represents a "
        "modern revival of medieval and Renaissance fighting manuals, growing rapidly "
        "since the early 2000s with clubs worldwide studying Fiore, Liechtenauer, and "
        "other historical masters."
    ),
    "Wrestling Traditions": (
        "Wrestling is arguably the world's oldest sport, depicted in cave paintings "
        "dating back 15,000 years. Ancient Sumerian, Egyptian, and Greek civilizations "
        "all practiced wrestling. Greek wrestling (Pale) was an original Olympic event "
        "in 708 BC. Traditional wrestling styles persist worldwide: Turkish oil wrestling "
        "(Kirkpinar, held since 1362), Mongolian wrestling (Bokh), Indian kushti, "
        "Senegalese Laamb, Icelandic Glima, Swiss Schwingen, Korean Ssireum, and "
        "Japanese sumo. Modern Olympic wrestling includes Freestyle and Greco-Roman "
        "styles. Regions like Dagestan (Russia), Iran, and the US college system "
        "(particularly Iowa, Penn State, and Oklahoma State) produce elite wrestlers. "
        "Sumo, Japan's national sport, maintains centuries-old Shinto rituals and "
        "traditions within a professional sporting framework."
    ),
    "Capoeira & Dance Fighting": (
        "Capoeira originated in Brazil among enslaved Africans, combining elements of "
        "fight, dance, acrobatics, and music. Developed primarily in Salvador, Bahia, "
        "it was disguised as dance to avoid persecution by slave owners. Two main "
        "styles exist: Capoeira Angola (traditional, slower, closer to the ground, "
        "codified by Mestre Pastinha) and Capoeira Regional (faster, more acrobatic, "
        "created by Mestre Bimba in the 1930s). The roda (circle) is the fundamental "
        "performance space, accompanied by the berimbau, pandeiro, and atabaque. "
        "UNESCO recognized the Roda de Capoeira as Intangible Cultural Heritage of "
        "Humanity in 2014. Related martial dance traditions include Indonesian Pencak "
        "Silat, French Savate, and Indian Kalaripayattu."
    ),
    "MMA & UFC Venues": (
        "Mixed Martial Arts (MMA) as a modern sport emerged from the Brazilian "
        "Vale Tudo ('anything goes') fights and the founding of the Ultimate Fighting "
        "Championship (UFC) in 1993 by Rorion Gracie and Art Davie. Initially marketed "
        "as a style-vs-style competition, MMA evolved into a sophisticated sport "
        "combining striking (boxing, kickboxing, Muay Thai), wrestling, and grappling "
        "(BJJ, judo). The UFC, now owned by Endeavor, is the world's largest MMA "
        "promotion, hosting events globally from Las Vegas to Abu Dhabi. Other major "
        "promotions include ONE Championship (Asia), Bellator/PFL (USA), and BRAVE CF "
        "(Bahrain). Key training camps like AKA, ATT, Jackson-Wink, and City Kickboxing "
        "have produced multiple champions. The sport continues to grow with new markets "
        "opening in Africa, India, and China."
    ),
}

# ======================================================================
# COLOR PALETTES PER MODE
# ======================================================================
MODE_COLORS = {
    "Karate Origins & Dojos": {
        "birthplace": "#ef4444",
        "headquarters": "#f59e0b",
        "major_school": "#06b6d4",
        "dojo": "#10b981",
        "museum": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Kung Fu Temples & Schools": {
        "temple": "#ef4444",
        "school": "#f59e0b",
        "birthplace": "#8b5cf6",
        "academy": "#06b6d4",
        "museum": "#10b981",
        "default": "#e8ecf4",
    },
    "Muay Thai Camps": {
        "stadium": "#ef4444",
        "camp": "#f59e0b",
        "gym": "#06b6d4",
        "school": "#10b981",
        "museum": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Brazilian Jiu-Jitsu Academies": {
        "founding": "#ef4444",
        "academy": "#f59e0b",
        "competition": "#06b6d4",
        "gym": "#10b981",
        "headquarters": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Judo & Olympic Venues": {
        "birthplace": "#ef4444",
        "headquarters": "#f59e0b",
        "olympic": "#06b6d4",
        "dojo": "#10b981",
        "museum": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Taekwondo Origins": {
        "headquarters": "#ef4444",
        "birthplace": "#f59e0b",
        "academy": "#06b6d4",
        "school": "#10b981",
        "olympic": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Fencing & Sword Arts": {
        "fencing_school": "#ef4444",
        "kendo_dojo": "#f59e0b",
        "hema_club": "#06b6d4",
        "olympic": "#10b981",
        "museum": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Wrestling Traditions": {
        "traditional": "#ef4444",
        "sumo": "#f59e0b",
        "olympic": "#06b6d4",
        "school": "#10b981",
        "venue": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "Capoeira & Dance Fighting": {
        "origin": "#ef4444",
        "academy": "#f59e0b",
        "roda": "#06b6d4",
        "school": "#10b981",
        "cultural": "#8b5cf6",
        "default": "#e8ecf4",
    },
    "MMA & UFC Venues": {
        "ufc_venue": "#ef4444",
        "gym": "#f59e0b",
        "arena": "#06b6d4",
        "training_center": "#10b981",
        "headquarters": "#8b5cf6",
        "default": "#e8ecf4",
    },
}

# ======================================================================
# 1. KARATE ORIGINS & DOJOS
# ======================================================================
KARATE_DATA = [
    {"name": "Shuri Castle - Birthplace of Shuri-te", "lat": 26.2171, "lon": 127.7196, "type": "birthplace", "country": "Japan", "description": "Historic origin of Shuri-te karate style in Okinawa, one of the three original karate traditions."},
    {"name": "Naha - Birthplace of Naha-te", "lat": 26.3344, "lon": 127.6809, "type": "birthplace", "country": "Japan", "description": "Origin of Naha-te karate tradition, precursor to Goju-ryu."},
    {"name": "Tomari - Birthplace of Tomari-te", "lat": 26.3500, "lon": 127.6700, "type": "birthplace", "country": "Japan", "description": "Origin of Tomari-te, the third original Okinawan karate tradition."},
    {"name": "JKA Headquarters Tokyo - Shotokan", "lat": 35.6762, "lon": 139.6503, "type": "headquarters", "country": "Japan", "description": "Japan Karate Association HQ, home of Shotokan karate founded by Gichin Funakoshi."},
    {"name": "Goju-ryu Karate-do Sogenkan", "lat": 26.3360, "lon": 127.7650, "type": "major_school", "country": "Japan", "description": "Major Goju-ryu school in Okinawa founded in the tradition of Chojun Miyagi."},
    {"name": "Wado-ryu HQ - Hironori Otsuka", "lat": 35.6895, "lon": 139.6917, "type": "headquarters", "country": "Japan", "description": "Headquarters of Wado-ryu karate, blending Shotokan with jujutsu."},
    {"name": "Shito-ryu International HQ", "lat": 34.6937, "lon": 135.5023, "type": "headquarters", "country": "Japan", "description": "Osaka HQ of Shito-ryu, founded by Kenwa Mabuni combining Shuri-te and Naha-te."},
    {"name": "Okinawa Karate Kaikan", "lat": 26.3340, "lon": 127.7437, "type": "museum", "country": "Japan", "description": "Official Okinawa karate museum and training center, opened 2017."},
    {"name": "Budokan - Tokyo Martial Arts Center", "lat": 35.6934, "lon": 139.7497, "type": "dojo", "country": "Japan", "description": "Nippon Budokan, Japan premier martial arts arena hosting major karate championships."},
    {"name": "Kyokushin Honbu Dojo - Mas Oyama", "lat": 35.6580, "lon": 139.7016, "type": "headquarters", "country": "Japan", "description": "World headquarters of Kyokushin full-contact karate founded by Masutatsu Oyama."},
    {"name": "ISKF Philadelphia", "lat": 39.9526, "lon": -75.1652, "type": "dojo", "country": "USA", "description": "International Shotokan Karate Federation headquarters, led by Teruyuki Okazaki."},
    {"name": "JKA America - Los Angeles", "lat": 34.0522, "lon": -118.2437, "type": "dojo", "country": "USA", "description": "Major JKA Shotokan dojo in Southern California, spreading traditional karate in the US."},
    {"name": "Gichin Funakoshi Memorial", "lat": 26.3250, "lon": 127.7600, "type": "museum", "country": "Japan", "description": "Memorial to Gichin Funakoshi, father of modern karate, in Okinawa."},
    {"name": "European Karate Federation - Madrid", "lat": 40.4168, "lon": -3.7038, "type": "headquarters", "country": "Spain", "description": "EKF headquarters coordinating karate across Europe."},
    {"name": "WKF World Karate Federation - Madrid", "lat": 40.4530, "lon": -3.6883, "type": "headquarters", "country": "Spain", "description": "World Karate Federation global headquarters governing sport karate."},
    {"name": "Uechi-ryu Karate Honbu Okinawa", "lat": 26.5013, "lon": 127.9439, "type": "major_school", "country": "Japan", "description": "Headquarters of Uechi-ryu, an Okinawan karate style with Chinese roots."},
    {"name": "Shotokan Karate of America - LA", "lat": 34.0195, "lon": -118.4912, "type": "dojo", "country": "USA", "description": "SKA headquarters under Tsutomu Ohshima, one of the oldest US karate organizations."},
    {"name": "Karate-Do Doshinkan - London", "lat": 51.5074, "lon": -0.1278, "type": "dojo", "country": "UK", "description": "Major European Shotokan dojo, one of the largest karate organizations in Britain."},
    {"name": "Australian Karate Federation - Sydney", "lat": -33.8688, "lon": 151.2093, "type": "dojo", "country": "Australia", "description": "AKF headquarters coordinating karate development across Australia."},
    {"name": "Karate Academy Berlin", "lat": 52.5200, "lon": 13.4050, "type": "dojo", "country": "Germany", "description": "Prominent German karate school representing multiple traditional styles."},
    {"name": "Okinawa Shorin-ryu Karate Dojo", "lat": 26.3116, "lon": 127.7728, "type": "major_school", "country": "Japan", "description": "Traditional Shorin-ryu school in Okinawa, direct lineage from Shuri-te masters."},
    {"name": "Karate Canada - Ottawa", "lat": 45.4215, "lon": -75.6972, "type": "headquarters", "country": "Canada", "description": "National karate federation headquarters for Canada."},
    {"name": "Kenkojuku Karate - Paris", "lat": 48.8566, "lon": 2.3522, "type": "dojo", "country": "France", "description": "Major Shotokan karate dojo in Paris, part of global Kenkojuku network."},
    {"name": "Karate South Africa - Johannesburg", "lat": -26.2041, "lon": 28.0473, "type": "dojo", "country": "South Africa", "description": "South African karate federation headquarters, growing karate community in Africa."},
    {"name": "All India Karate-Do Federation - New Delhi", "lat": 28.6139, "lon": 77.2090, "type": "headquarters", "country": "India", "description": "National karate governing body of India, one of the largest karate populations."},
    {"name": "Karate Union of Russia - Moscow", "lat": 55.7558, "lon": 37.6173, "type": "headquarters", "country": "Russia", "description": "Russian karate federation HQ, producing strong international competitors."},
    {"name": "Pan American Karate Federation - Mexico City", "lat": 19.4326, "lon": -99.1332, "type": "headquarters", "country": "Mexico", "description": "PKF headquarters coordinating karate across the Americas."},
    {"name": "Isshinryu Karate Honbu - Okinawa", "lat": 26.4479, "lon": 127.7611, "type": "major_school", "country": "Japan", "description": "Headquarters of Isshinryu karate, founded by Tatsuo Shimabuku in 1956."},
    {"name": "Matsubayashi-ryu Honbu - Naha", "lat": 26.3320, "lon": 127.6900, "type": "major_school", "country": "Japan", "description": "Headquarters of Matsubayashi-ryu (Shorin-ryu) founded by Shoshin Nagamine."},
    {"name": "Brazil Karate Federation - Sao Paulo", "lat": -23.5505, "lon": -46.6333, "type": "headquarters", "country": "Brazil", "description": "Brazilian karate federation, Brazil has one of the strongest karate communities outside Japan."},
]

# ======================================================================
# 2. KUNG FU TEMPLES & SCHOOLS
# ======================================================================
KUNG_FU_DATA = [
    {"name": "Shaolin Temple - Dengfeng", "lat": 34.5076, "lon": 112.9370, "type": "temple", "country": "China", "description": "Legendary birthplace of Shaolin kung fu, founded 495 AD, Zen Buddhism center."},
    {"name": "Wudang Mountain Temples", "lat": 32.4000, "lon": 111.0040, "type": "temple", "country": "China", "description": "Birthplace of Wudang internal martial arts including Tai Chi and Bagua."},
    {"name": "Foshan - Wing Chun Origins", "lat": 23.0218, "lon": 113.1218, "type": "birthplace", "country": "China", "description": "Birthplace of Wing Chun kung fu, home of Ip Man and Wong Fei-hung."},
    {"name": "Ip Man Wing Chun Museum - Foshan", "lat": 23.0265, "lon": 113.1160, "type": "birthplace", "country": "China", "description": "Museum dedicated to Ip Man, grandmaster of Wing Chun and teacher of Bruce Lee."},
    {"name": "Bruce Lee Birthplace - San Francisco", "lat": 37.7955, "lon": -122.4085, "type": "birthplace", "country": "USA", "description": "San Francisco Chinatown, birthplace of Bruce Lee in 1940."},
    {"name": "Jun Fan Gung Fu Institute - Seattle", "lat": 47.6062, "lon": -122.3321, "type": "school", "country": "USA", "description": "Bruce Lee first martial arts school, founded in Seattle 1963."},
    {"name": "Chen Village - Tai Chi Birthplace", "lat": 35.2870, "lon": 113.0790, "type": "birthplace", "country": "China", "description": "Chenjiagou village, origin of Chen-style Tai Chi Chuan, the oldest Tai Chi form."},
    {"name": "Beijing Wushu Team Training Center", "lat": 39.9042, "lon": 116.4074, "type": "academy", "country": "China", "description": "Elite training center for China national wushu competitors."},
    {"name": "Emei Mountain Kung Fu Schools", "lat": 29.5984, "lon": 103.3377, "type": "temple", "country": "China", "description": "Mount Emei, one of the three sacred mountains of Chinese martial arts alongside Shaolin and Wudang."},
    {"name": "Hong Kong Wing Chun Athletic Assoc.", "lat": 22.3193, "lon": 114.1694, "type": "school", "country": "China", "description": "Major Wing Chun organization in Hong Kong, direct lineage from Ip Man."},
    {"name": "Shanghai Jing Wu Athletic Association", "lat": 31.2304, "lon": 121.4737, "type": "school", "country": "China", "description": "Historic Jing Wu (Chin Woo) school, founded 1910 by Huo Yuanjia."},
    {"name": "Tagou Martial Arts School - Dengfeng", "lat": 34.4600, "lon": 112.9600, "type": "academy", "country": "China", "description": "Largest martial arts school in the world with over 35,000 students near Shaolin."},
    {"name": "Kunyu Mountain Shaolin Academy", "lat": 37.3034, "lon": 121.8401, "type": "academy", "country": "China", "description": "Major Shaolin training academy in Shandong province for international students."},
    {"name": "Southern Shaolin Temple - Quanzhou", "lat": 24.8744, "lon": 118.6757, "type": "temple", "country": "China", "description": "Legendary Southern Shaolin Temple, origin of many southern kung fu styles."},
    {"name": "Yip Man Martial Arts Athletic Assoc. - HK", "lat": 22.2800, "lon": 114.1588, "type": "school", "country": "China", "description": "Organization preserving Yip Man Wing Chun tradition in Hong Kong."},
    {"name": "UK Wing Chun Assoc. - London", "lat": 51.5155, "lon": -0.0922, "type": "school", "country": "UK", "description": "Largest Wing Chun organization in the UK."},
    {"name": "Shaolin Temple Cultural Center - London", "lat": 51.5176, "lon": -0.1145, "type": "academy", "country": "UK", "description": "Official Shaolin cultural center bringing Shaolin arts to Europe."},
    {"name": "USA Shaolin Temple - New York", "lat": 40.7195, "lon": -73.9973, "type": "academy", "country": "USA", "description": "Shifu Shi Yan Ming Shaolin Temple in Manhattan, training since 1994."},
    {"name": "Plum Blossom International Federation - LA", "lat": 34.0522, "lon": -118.2437, "type": "school", "country": "USA", "description": "Mei Hua (Plum Blossom) kung fu school preserving traditional northern styles."},
    {"name": "Dragon and Phoenix Kung Fu - Sydney", "lat": -33.8688, "lon": 151.2093, "type": "school", "country": "Australia", "description": "Major traditional Chinese martial arts school in Australia."},
    {"name": "Wushu Federation of India - New Delhi", "lat": 28.6139, "lon": 77.2090, "type": "school", "country": "India", "description": "National federation promoting wushu and kung fu across India."},
    {"name": "Bruce Lee Statue - Hong Kong", "lat": 22.2934, "lon": 114.1739, "type": "museum", "country": "China", "description": "Iconic Bruce Lee statue on the Avenue of Stars, Tsim Sha Tsui."},
    {"name": "International Wushu Federation - Beijing", "lat": 39.9710, "lon": 116.3976, "type": "academy", "country": "China", "description": "IWUF global headquarters governing competitive wushu worldwide."},
    {"name": "Cangzhou Wushu - Hebei", "lat": 38.3106, "lon": 116.8386, "type": "school", "country": "China", "description": "Cangzhou, known as the Hometown of Wushu, with over 50 distinct kung fu styles."},
    {"name": "Guangzhou Hung Gar Kung Fu", "lat": 23.1291, "lon": 113.2644, "type": "school", "country": "China", "description": "Hung Gar (Tiger-Crane) kung fu tradition from Guangzhou, southern powerhouse style."},
    {"name": "Choy Li Fut Museum - Jiangmen", "lat": 22.5789, "lon": 113.0817, "type": "museum", "country": "China", "description": "Museum dedicated to Choy Li Fut kung fu, founded by Chan Heung in 1836."},
    {"name": "Baji Quan Academy - Cangzhou", "lat": 38.3000, "lon": 116.8300, "type": "academy", "country": "China", "description": "Baji Quan (Eight Extremes Fist) academy, famous bodyguard kung fu style."},
    {"name": "Praying Mantis Kung Fu - Yantai", "lat": 37.4638, "lon": 121.4480, "type": "school", "country": "China", "description": "Origin of Northern Praying Mantis kung fu in Shandong province."},
    {"name": "Wing Tsun Universe HQ - Hong Kong", "lat": 22.3000, "lon": 114.1700, "type": "school", "country": "China", "description": "Leung Ting Wing Tsun organization, one of the largest Wing Chun groups globally."},
    {"name": "Tai Chi Heritage Center - Yang Village", "lat": 36.7500, "lon": 114.0000, "type": "birthplace", "country": "China", "description": "Yang family Tai Chi origin, Yang Luchan birthplace in Hebei province."},
]

# ======================================================================
# 3. MUAY THAI CAMPS
# ======================================================================
MUAY_THAI_DATA = [
    {"name": "Lumpinee Boxing Stadium", "lat": 13.7673, "lon": 100.6215, "type": "stadium", "country": "Thailand", "description": "Most prestigious Muay Thai stadium in the world, operated by the Royal Thai Army."},
    {"name": "Rajadamnern Stadium", "lat": 13.7638, "lon": 100.5093, "type": "stadium", "country": "Thailand", "description": "Oldest Muay Thai stadium in Bangkok, opened 1945, hosts legendary bouts."},
    {"name": "Tiger Muay Thai - Phuket", "lat": 7.8940, "lon": 98.3310, "type": "camp", "country": "Thailand", "description": "World-famous Muay Thai and MMA training camp in Chalong, Phuket."},
    {"name": "Fairtex Training Center - Pattaya", "lat": 12.9236, "lon": 100.8825, "type": "camp", "country": "Thailand", "description": "Fairtex flagship gym and Muay Thai training center in Pattaya."},
    {"name": "Sitmonchai Gym - Chiang Mai", "lat": 18.7883, "lon": 98.9853, "type": "gym", "country": "Thailand", "description": "Legendary champion-producing Muay Thai gym in northern Thailand."},
    {"name": "Sor Vorapin Gym - Bangkok", "lat": 13.7509, "lon": 100.5104, "type": "gym", "country": "Thailand", "description": "Historic Bangkok gym near Khao San Road, training fighters since the 1960s."},
    {"name": "Kaewsamrit Gym - Bangkok", "lat": 13.8003, "lon": 100.5535, "type": "gym", "country": "Thailand", "description": "Legendary Muay Thai camp that has produced multiple Lumpinee champions."},
    {"name": "Petchyindee Academy - Bangkok", "lat": 13.7450, "lon": 100.5350, "type": "camp", "country": "Thailand", "description": "Major Muay Thai promotion and training academy with champion fighters."},
    {"name": "Sinbi Muay Thai - Phuket", "lat": 7.8166, "lon": 98.3430, "type": "camp", "country": "Thailand", "description": "Top Muay Thai training camp in Rawai, Phuket for international fighters."},
    {"name": "Yokkao Training Center - Bangkok", "lat": 13.7280, "lon": 100.5271, "type": "gym", "country": "Thailand", "description": "Premium Muay Thai brand gym with world-class facilities in Bangkok."},
    {"name": "Evolve MMA - Singapore", "lat": 1.2830, "lon": 103.8450, "type": "gym", "country": "Singapore", "description": "Asia largest MMA gym with champion-level Muay Thai instruction."},
    {"name": "Saenchai PKSaenchaimuaythaigym", "lat": 13.7370, "lon": 100.5640, "type": "gym", "country": "Thailand", "description": "Training gym of legendary Muay Thai fighter Saenchai."},
    {"name": "Banchamek Gym (Buakaw)", "lat": 13.8480, "lon": 100.5680, "type": "gym", "country": "Thailand", "description": "Training camp of superstar Buakaw Banchamek in Bangkok."},
    {"name": "Muay Thai Institute - Rangsit", "lat": 14.0582, "lon": 100.6063, "type": "school", "country": "Thailand", "description": "Official Muay Thai educational institute near Bangkok, Kru Muay Thai certification."},
    {"name": "Venum Training Camp - Pattaya", "lat": 12.9490, "lon": 100.8860, "type": "camp", "country": "Thailand", "description": "High-end Muay Thai camp in Pattaya affiliated with the Venum brand."},
    {"name": "Kombat Group - Pattaya", "lat": 12.9330, "lon": 100.8910, "type": "camp", "country": "Thailand", "description": "International Muay Thai and fitness training camp in Pattaya."},
    {"name": "Eminent Air Muay Thai - Chiang Mai", "lat": 18.7900, "lon": 98.9700, "type": "camp", "country": "Thailand", "description": "Popular Muay Thai training camp in Chiang Mai for foreign students."},
    {"name": "Muay Thai Grand Prix HQ - London", "lat": 51.5074, "lon": -0.1278, "type": "school", "country": "UK", "description": "Major European Muay Thai promotion and organization based in London."},
    {"name": "CSA Gym (Rafael Cordeiro) - Los Angeles", "lat": 34.1478, "lon": -118.1445, "type": "gym", "country": "USA", "description": "Kings MMA, one of the top Muay Thai and MMA gyms in the USA."},
    {"name": "Attachai Muay Thai Gym - Bangkok", "lat": 13.7580, "lon": 100.5680, "type": "gym", "country": "Thailand", "description": "Technical Muay Thai gym in central Bangkok known for skilled instruction."},
    {"name": "National Muay Thai Museum - Ayutthaya", "lat": 14.3532, "lon": 100.5685, "type": "museum", "country": "Thailand", "description": "Museum dedicated to the history of Muay Thai in the ancient capital of Siam."},
    {"name": "Superbon Training Camp - Bangkok", "lat": 13.7610, "lon": 100.5450, "type": "camp", "country": "Thailand", "description": "Training facility of ONE Championship kickboxing champion Superbon."},
    {"name": "Santai Muay Thai - Chiang Mai", "lat": 18.7700, "lon": 98.9800, "type": "camp", "country": "Thailand", "description": "Authentic traditional Muay Thai camp in the mountains of northern Thailand."},
    {"name": "Rawai Muay Thai - Phuket", "lat": 7.7747, "lon": 98.3248, "type": "camp", "country": "Thailand", "description": "Well-established Muay Thai camp in Rawai area of southern Phuket."},
    {"name": "Sitsongpeenong Bangkok", "lat": 13.7350, "lon": 100.5230, "type": "gym", "country": "Thailand", "description": "Championship Muay Thai gym producing multiple stadium title holders."},
    {"name": "Elite Fight Club - Bangkok", "lat": 13.7420, "lon": 100.5550, "type": "gym", "country": "Thailand", "description": "Modern Muay Thai gym combining traditional Thai boxing with strength training."},
    {"name": "Muay Thai Academy - Melbourne", "lat": -37.8136, "lon": 144.9631, "type": "school", "country": "Australia", "description": "Leading Muay Thai academy in Melbourne bringing authentic Thai boxing to Australia."},
    {"name": "KC Muay Thai - Phnom Penh", "lat": 11.5564, "lon": 104.9282, "type": "gym", "country": "Cambodia", "description": "Pradal Serey (Cambodian kickboxing) and Muay Thai gym in the Cambodian capital."},
    {"name": "Lethwei Nation Gym - Yangon", "lat": 16.8661, "lon": 96.1951, "type": "gym", "country": "Myanmar", "description": "Myanmar bare-knuckle Lethwei gym, the Art of Nine Limbs."},
]

# ======================================================================
# 4. BRAZILIAN JIU-JITSU ACADEMIES
# ======================================================================
BJJ_DATA = [
    {"name": "Gracie Academy Garage - Rio de Janeiro", "lat": -22.9519, "lon": -43.2105, "type": "founding", "country": "Brazil", "description": "Original Gracie family garage where Helio Gracie refined Brazilian Jiu-Jitsu."},
    {"name": "Gracie Barra HQ - Rio de Janeiro", "lat": -22.9894, "lon": -43.1896, "type": "headquarters", "country": "Brazil", "description": "Carlos Gracie Jr. Gracie Barra headquarters, largest BJJ organization worldwide."},
    {"name": "Alliance Jiu-Jitsu HQ - Sao Paulo", "lat": -23.5505, "lon": -46.6333, "type": "headquarters", "country": "Brazil", "description": "Alliance BJJ global HQ, one of the most decorated competition teams."},
    {"name": "Gracie Humaita - Rio de Janeiro", "lat": -22.9560, "lon": -43.1980, "type": "academy", "country": "Brazil", "description": "Iconic Gracie Humaita academy in Botafogo, Rio, the original Gracie BJJ school."},
    {"name": "ATOS Jiu-Jitsu HQ - San Diego", "lat": 32.7157, "lon": -117.1611, "type": "headquarters", "country": "USA", "description": "Andre Galvao ATOS HQ, dominant competition team in San Diego."},
    {"name": "Renzo Gracie Academy - New York", "lat": 40.7484, "lon": -73.9857, "type": "academy", "country": "USA", "description": "Renzo Gracie flagship academy in Manhattan, legendary BJJ school."},
    {"name": "Gracie Academy - Torrance, CA", "lat": 33.8358, "lon": -118.3406, "type": "academy", "country": "USA", "description": "Rorion and Ryron Gracie academy, birthplace of Gracie Combatives."},
    {"name": "Carlson Gracie Academy - Chicago", "lat": 41.8781, "lon": -87.6298, "type": "academy", "country": "USA", "description": "Legacy academy of the legendary Carlson Gracie team."},
    {"name": "Checkmat BJJ HQ - Los Angeles", "lat": 34.0522, "lon": -118.2437, "type": "headquarters", "country": "USA", "description": "Checkmat Jiu-Jitsu headquarters, founded by Leo Vieira and Rico Vieira."},
    {"name": "Cicero Costha BJJ - Sao Paulo", "lat": -23.5627, "lon": -46.6546, "type": "academy", "country": "Brazil", "description": "Training camp of champions including Leandro Lo and multiple world title holders."},
    {"name": "Maracana Stadium - IBJJF Worlds Venue", "lat": -22.9121, "lon": -43.2302, "type": "competition", "country": "Brazil", "description": "Historic venue for Brazilian national BJJ championships."},
    {"name": "Walter Pyramid - IBJJF Worlds", "lat": 33.7876, "lon": -118.1140, "type": "competition", "country": "USA", "description": "Long Beach Walter Pyramid, annual venue for IBJJF World Jiu-Jitsu Championship."},
    {"name": "Ginasio do Ibirapuera - Sao Paulo", "lat": -23.5872, "lon": -46.6601, "type": "competition", "country": "Brazil", "description": "Major venue for BJJ competition events in Sao Paulo."},
    {"name": "Roger Gracie Academy - London", "lat": 51.4975, "lon": -0.1357, "type": "academy", "country": "UK", "description": "Academy of 10x World Champion Roger Gracie in London."},
    {"name": "Nova Uniao - Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "type": "academy", "country": "Brazil", "description": "Andre Pederneiras team, produced BJ Penn, Jose Aldo, and many champions."},
    {"name": "Marcelo Garcia Academy - New York", "lat": 40.7451, "lon": -73.9882, "type": "academy", "country": "USA", "description": "Five-time world champion Marcelo Garcia legendary academy in Manhattan."},
    {"name": "Ribeiro Jiu-Jitsu - San Diego", "lat": 32.7500, "lon": -117.1500, "type": "academy", "country": "USA", "description": "Saulo and Xande Ribeiro world-class BJJ academy in San Diego."},
    {"name": "AOJ (Art of Jiu-Jitsu) - Costa Mesa", "lat": 33.6412, "lon": -117.9187, "type": "academy", "country": "USA", "description": "Gui and Rafa Mendes Art of Jiu-Jitsu, elite competitor academy."},
    {"name": "Gracie Barra - Birmingham UK", "lat": 52.4862, "lon": -1.8904, "type": "gym", "country": "UK", "description": "Largest Gracie Barra academy in the UK."},
    {"name": "GF Team HQ - Rio de Janeiro", "lat": -22.9250, "lon": -43.1750, "type": "academy", "country": "Brazil", "description": "Grappling Fight Team, one of the top competition teams in Brazilian BJJ."},
    {"name": "Unity Jiu-Jitsu - New York", "lat": 40.7408, "lon": -73.9897, "type": "academy", "country": "USA", "description": "Murilo Santana Unity BJJ academy, breeding ground of new champions."},
    {"name": "BJJ Globetrotters HQ - Copenhagen", "lat": 55.6761, "lon": 12.5683, "type": "gym", "country": "Denmark", "description": "World largest affiliation-free BJJ community based in Copenhagen."},
    {"name": "Dream Art BJJ - Sao Paulo", "lat": -23.5400, "lon": -46.6300, "type": "academy", "country": "Brazil", "description": "Dream Art project producing world-class BJJ competitors from Sao Paulo."},
    {"name": "10th Planet Jiu-Jitsu HQ - Los Angeles", "lat": 34.0407, "lon": -118.2468, "type": "academy", "country": "USA", "description": "Eddie Bravo no-gi BJJ system headquarters, rubber guard innovator."},
    {"name": "Gracie Barra Australia - Sydney", "lat": -33.8688, "lon": 151.2093, "type": "gym", "country": "Australia", "description": "Gracie Barra major presence in Australia with multiple academies."},
    {"name": "ADCC Venue - Abu Dhabi", "lat": 24.4539, "lon": 54.3773, "type": "competition", "country": "UAE", "description": "Abu Dhabi Combat Club, host of the most prestigious submission grappling event."},
    {"name": "Fight Sports Miami", "lat": 25.7617, "lon": -80.1918, "type": "academy", "country": "USA", "description": "Roberto Cyborg Abreu Fight Sports flagship academy in Miami."},
    {"name": "Gracie Jiu-Jitsu Academy - Sao Paulo", "lat": -23.5600, "lon": -46.6500, "type": "academy", "country": "Brazil", "description": "Helio Gracie original teaching lineage continuing in Sao Paulo."},
    {"name": "Brasa BJJ - Rio de Janeiro", "lat": -22.9400, "lon": -43.1800, "type": "academy", "country": "Brazil", "description": "Brazilian Soul Association, major BJJ team with global presence."},
]

# ======================================================================
# 5. JUDO & OLYMPIC VENUES
# ======================================================================
JUDO_DATA = [
    {"name": "Kodokan Judo Institute - Tokyo", "lat": 35.7065, "lon": 139.7519, "type": "headquarters", "country": "Japan", "description": "World headquarters of Judo, founded 1882 by Jigoro Kano."},
    {"name": "Jigoro Kano Birthplace - Mikage", "lat": 34.7170, "lon": 135.2608, "type": "birthplace", "country": "Japan", "description": "Birthplace of Jigoro Kano, founder of Judo, in Mikage, Kobe."},
    {"name": "Nippon Budokan - Tokyo", "lat": 35.6934, "lon": 139.7497, "type": "olympic", "country": "Japan", "description": "Venue for 1964 and 2021 Olympic judo events in Tokyo."},
    {"name": "Olympiahalle - Munich 1972", "lat": 48.1734, "lon": 11.5510, "type": "olympic", "country": "Germany", "description": "Venue for 1972 Munich Olympics judo competition."},
    {"name": "ExCeL London - 2012 Olympics", "lat": 51.5075, "lon": 0.0342, "type": "olympic", "country": "UK", "description": "Venue for 2012 London Olympic judo events."},
    {"name": "Palais des Sports - Paris 2024", "lat": 48.8302, "lon": 2.4073, "type": "olympic", "country": "France", "description": "Champ de Mars Arena, venue for 2024 Paris Olympic judo events."},
    {"name": "Sydney Convention Centre - 2000", "lat": -33.8756, "lon": 151.2005, "type": "olympic", "country": "Australia", "description": "Venue for 2000 Sydney Olympic judo competition."},
    {"name": "Georgia World Congress - Atlanta 1996", "lat": 33.7598, "lon": -84.3954, "type": "olympic", "country": "USA", "description": "Venue for 1996 Atlanta Olympic judo events."},
    {"name": "Carioca Arena - Rio 2016", "lat": -22.9756, "lon": -43.3951, "type": "olympic", "country": "Brazil", "description": "Venue for 2016 Rio Olympics judo competition at Barra Olympic Park."},
    {"name": "IJF International Judo Federation - Budapest", "lat": 47.4979, "lon": 19.0402, "type": "headquarters", "country": "Hungary", "description": "International Judo Federation global headquarters."},
    {"name": "Tenri University Judo - Nara", "lat": 34.5965, "lon": 135.8371, "type": "dojo", "country": "Japan", "description": "One of Japan strongest university judo programs, legendary training center."},
    {"name": "Tokai University Judo - Tokyo", "lat": 35.3685, "lon": 139.2682, "type": "dojo", "country": "Japan", "description": "Elite university judo powerhouse that produced multiple Olympic champions."},
    {"name": "INSEP Judo - Paris", "lat": 48.8447, "lon": 2.4486, "type": "dojo", "country": "France", "description": "French National Institute of Sport, elite judo training facility producing champions."},
    {"name": "Korean Judo Association - Seoul", "lat": 37.5172, "lon": 127.0473, "type": "headquarters", "country": "South Korea", "description": "Korean national judo HQ, Korea is a dominant force in international judo."},
    {"name": "Pais Arena Jerusalem - 2017 Worlds", "lat": 31.7510, "lon": 35.2025, "type": "olympic", "country": "Israel", "description": "Venue for 2017 World Judo Championships."},
    {"name": "Bercy Arena - Paris Grand Slam", "lat": 48.8388, "lon": 2.3786, "type": "olympic", "country": "France", "description": "Annual Paris Grand Slam judo venue, one of the premier World Tour events."},
    {"name": "Tsukuba University Judo", "lat": 36.1106, "lon": 140.1014, "type": "dojo", "country": "Japan", "description": "Historic university judo program with deep competitive tradition."},
    {"name": "Pedro Judo Center - Boston", "lat": 42.3601, "lon": -71.0589, "type": "dojo", "country": "USA", "description": "Jimmy Pedro Sr. and Jr. judo training center, produced Olympic medalists."},
    {"name": "Judo Museum - Kodokan Tokyo", "lat": 35.7060, "lon": 139.7525, "type": "museum", "country": "Japan", "description": "Museum inside Kodokan documenting the history and evolution of Judo."},
    {"name": "Uzbekistan Judo Federation - Tashkent", "lat": 41.2995, "lon": 69.2401, "type": "headquarters", "country": "Uzbekistan", "description": "Uzbekistan emerging judo powerhouse with major government support."},
    {"name": "Baku Judo Training Center", "lat": 40.4093, "lon": 49.8671, "type": "dojo", "country": "Azerbaijan", "description": "Major judo training center in Baku, Azerbaijan is a top judo nation."},
    {"name": "All England Judo Championships - Sheffield", "lat": 53.3811, "lon": -1.4701, "type": "olympic", "country": "UK", "description": "Traditional venue for British national judo championships."},
    {"name": "Budokwai Judo Club - London", "lat": 51.4930, "lon": -0.1600, "type": "dojo", "country": "UK", "description": "Oldest martial arts club in Europe, founded 1918, strong judo tradition."},
    {"name": "Kokushikan University Judo - Tokyo", "lat": 35.6271, "lon": 139.6556, "type": "dojo", "country": "Japan", "description": "Powerhouse university judo program producing national and Olympic champions."},
    {"name": "Georgia National Judo Academy - Tbilisi", "lat": 41.7151, "lon": 44.8271, "type": "dojo", "country": "Georgia", "description": "Georgia is a judo superpower with deep cultural roots in wrestling."},
    {"name": "Cuba National Judo Center - Havana", "lat": 23.1136, "lon": -82.3666, "type": "dojo", "country": "Cuba", "description": "Cuban national judo training center, Cuba has won multiple Olympic judo medals."},
    {"name": "Belarusian Judo Federation - Minsk", "lat": 53.9045, "lon": 27.5615, "type": "headquarters", "country": "Belarus", "description": "Belarus judo federation, producing top international competitors."},
    {"name": "Brazilian Judo Confederation - Rio", "lat": -22.9068, "lon": -43.1729, "type": "headquarters", "country": "Brazil", "description": "CBJ headquarters, Brazil is a judo powerhouse with multiple Olympic gold medals."},
    {"name": "Nippon Budokan World Championships 2019", "lat": 35.6934, "lon": 139.7497, "type": "olympic", "country": "Japan", "description": "Venue for 2019 World Judo Championships, returning to judo spiritual home."},
]

# ======================================================================
# 6. TAEKWONDO ORIGINS
# ======================================================================
TAEKWONDO_DATA = [
    {"name": "Kukkiwon (World Taekwondo HQ) - Seoul", "lat": 37.4990, "lon": 127.0274, "type": "headquarters", "country": "South Korea", "description": "World Taekwondo headquarters, the home of sport Taekwondo, built 1972."},
    {"name": "World Taekwondo Federation - Seoul", "lat": 37.5665, "lon": 126.9780, "type": "headquarters", "country": "South Korea", "description": "WT global governing body headquarters for Olympic Taekwondo."},
    {"name": "Choi Hong Hi Memorial - Haenam", "lat": 34.5714, "lon": 126.5977, "type": "birthplace", "country": "South Korea", "description": "Birthplace region of General Choi Hong Hi, founder of ITF Taekwondo."},
    {"name": "ITF Headquarters - Vienna", "lat": 48.2082, "lon": 16.3738, "type": "headquarters", "country": "Austria", "description": "International Taekwondo Federation headquarters for traditional TKD."},
    {"name": "Taekwondowon - Muju", "lat": 35.9061, "lon": 127.6576, "type": "academy", "country": "South Korea", "description": "Grand Taekwondo cultural center and training complex in Muju, South Korea."},
    {"name": "Korean National Training Center - Seoul", "lat": 37.5200, "lon": 127.0800, "type": "academy", "country": "South Korea", "description": "Jincheon National Training Center, elite Taekwondo training for Team Korea."},
    {"name": "Song Moo Kwan - Original Seoul Dojang", "lat": 37.5660, "lon": 126.9784, "type": "school", "country": "South Korea", "description": "Song Moo Kwan, one of the original Nine Kwans of Taekwondo, founded 1944."},
    {"name": "Chung Do Kwan - Seoul", "lat": 37.5700, "lon": 126.9800, "type": "school", "country": "South Korea", "description": "Chung Do Kwan, the largest of the original Nine Kwans, founded 1944."},
    {"name": "Moo Duk Kwan - Seoul", "lat": 37.5570, "lon": 126.9744, "type": "school", "country": "South Korea", "description": "Moo Duk Kwan, one of the original Nine Kwans, founded by Hwang Kee 1945."},
    {"name": "Ji Do Kwan - Seoul", "lat": 37.5640, "lon": 126.9900, "type": "school", "country": "South Korea", "description": "Ji Do Kwan, one of the Nine Kwans of Korean martial arts, founded 1946."},
    {"name": "Oh Do Kwan - Seoul Military", "lat": 37.5580, "lon": 127.0000, "type": "school", "country": "South Korea", "description": "Oh Do Kwan, military-founded Kwan by Choi Hong Hi and Nam Tae-hi."},
    {"name": "Taekwondo Park - T-1 Arena Seoul", "lat": 37.5135, "lon": 127.0598, "type": "academy", "country": "South Korea", "description": "T1 Arena, major Taekwondo competition venue in Seoul."},
    {"name": "ATA Martial Arts HQ - Little Rock", "lat": 34.7465, "lon": -92.2896, "type": "school", "country": "USA", "description": "American Taekwondo Association headquarters, largest TKD org in the Americas."},
    {"name": "US Taekwondo Center - Colorado Springs", "lat": 38.8339, "lon": -104.8214, "type": "headquarters", "country": "USA", "description": "USA Taekwondo national headquarters at the Olympic Training Center."},
    {"name": "Sydney Convention & Exhibition Centre - 2000", "lat": -33.8756, "lon": 151.2005, "type": "olympic", "country": "Australia", "description": "First Olympic Taekwondo competition held at 2000 Sydney Games."},
    {"name": "ExCeL London - 2012 Olympics TKD", "lat": 51.5075, "lon": 0.0342, "type": "olympic", "country": "UK", "description": "2012 London Olympics Taekwondo venue."},
    {"name": "Grand Palais Ephemere Paris - 2024", "lat": 48.8530, "lon": 2.3035, "type": "olympic", "country": "France", "description": "2024 Paris Olympics Taekwondo venue."},
    {"name": "British Taekwondo HQ - Manchester", "lat": 53.4808, "lon": -2.2426, "type": "headquarters", "country": "UK", "description": "British Taekwondo national headquarters and high-performance center."},
    {"name": "Iran Taekwondo Federation - Tehran", "lat": 35.6892, "lon": 51.3890, "type": "headquarters", "country": "Iran", "description": "Iran is one of the most successful Taekwondo nations globally."},
    {"name": "Taekwondo Mexico Federation - Mexico City", "lat": 19.4326, "lon": -99.1332, "type": "headquarters", "country": "Mexico", "description": "Mexican Taekwondo Federation, Mexico is a TKD Olympic powerhouse."},
    {"name": "European Taekwondo Union - Lausanne", "lat": 46.5197, "lon": 6.6323, "type": "headquarters", "country": "Switzerland", "description": "ETU headquarters near the IOC in Lausanne."},
    {"name": "Turkish Taekwondo Federation - Ankara", "lat": 39.9334, "lon": 32.8597, "type": "headquarters", "country": "Turkey", "description": "Turkey national TKD federation, consistent Olympic medal contender."},
    {"name": "Ivory Coast Taekwondo - Abidjan", "lat": 5.3600, "lon": -4.0083, "type": "headquarters", "country": "Ivory Coast", "description": "Cote d'Ivoire TKD federation, Cheick Cisse won Olympic gold in 2016."},
    {"name": "Jordan Taekwondo - Amman", "lat": 31.9454, "lon": 35.9284, "type": "school", "country": "Jordan", "description": "Ahmad Abu-Ghaush won Jordan first ever Olympic gold in TKD at Rio 2016."},
    {"name": "Egyptian Taekwondo Federation - Cairo", "lat": 30.0444, "lon": 31.2357, "type": "headquarters", "country": "Egypt", "description": "Egypt national TKD federation, major force in African and world taekwondo."},
    {"name": "Taekwondo Association of Thailand - Bangkok", "lat": 13.7563, "lon": 100.5018, "type": "headquarters", "country": "Thailand", "description": "Thai TKD association, Panipak Wongpattanakit is a dominant Olympic champion."},
    {"name": "National Taekwondo Center - Chelyabinsk", "lat": 55.1644, "lon": 61.4368, "type": "academy", "country": "Russia", "description": "Major taekwondo training center in Russia, hosted Grand Prix events."},
    {"name": "Dominican Republic TKD - Santo Domingo", "lat": 18.4861, "lon": -69.9312, "type": "school", "country": "Dominican Republic", "description": "Dominican TKD federation, Gabriel Mercedes won Olympic silver in 2008."},
]

# ======================================================================
# 7. FENCING & SWORD ARTS
# ======================================================================
FENCING_DATA = [
    {"name": "Academie d'Armes de Paris", "lat": 48.8566, "lon": 2.3522, "type": "fencing_school", "country": "France", "description": "Historic Parisian fencing academy, France is the cradle of modern fencing."},
    {"name": "Royal Spanish Fencing Federation - Madrid", "lat": 40.4168, "lon": -3.7038, "type": "fencing_school", "country": "Spain", "description": "Spanish fencing HQ, Spain developed the rapier and La Destreza system."},
    {"name": "Italian Fencing Federation - Rome", "lat": 41.9028, "lon": 12.4964, "type": "fencing_school", "country": "Italy", "description": "Italian Fencing Federation HQ, Italy is a dominant force in Olympic fencing."},
    {"name": "Sala d'Armi Musumeci Greco - Milan", "lat": 45.4642, "lon": 9.1900, "type": "fencing_school", "country": "Italy", "description": "Historic Milanese fencing school of the renowned Musumeci Greco family."},
    {"name": "Hungarian Fencing Federation - Budapest", "lat": 47.4979, "lon": 19.0402, "type": "fencing_school", "country": "Hungary", "description": "Hungary is one of the most decorated fencing nations in Olympic history."},
    {"name": "All Japan Kendo Federation - Tokyo", "lat": 35.6762, "lon": 139.6503, "type": "kendo_dojo", "country": "Japan", "description": "Headquarters of the All Japan Kendo Federation, governing Japanese sword arts."},
    {"name": "Noma Dojo - Tokyo", "lat": 35.6780, "lon": 139.7400, "type": "kendo_dojo", "country": "Japan", "description": "One of Tokyo most prestigious kendo training halls."},
    {"name": "International Kendo Federation - Tokyo", "lat": 35.6895, "lon": 139.6917, "type": "kendo_dojo", "country": "Japan", "description": "IKF global headquarters governing kendo, iaido, and jodo worldwide."},
    {"name": "HEMA Alliance HQ - Meyer Freifechter Guild", "lat": 38.6270, "lon": -90.1994, "type": "hema_club", "country": "USA", "description": "Historical European Martial Arts Alliance, major HEMA organization."},
    {"name": "Schola Gladiatoria - London", "lat": 51.5074, "lon": -0.1278, "type": "hema_club", "country": "UK", "description": "Matt Easton premier HEMA school studying historical sword fighting."},
    {"name": "Academie Duello - Vancouver", "lat": 49.2827, "lon": -123.1207, "type": "hema_club", "country": "Canada", "description": "World-class HEMA school teaching Italian longsword and rapier."},
    {"name": "Grand Palais - Paris Olympic Fencing", "lat": 48.8660, "lon": 2.3125, "type": "olympic", "country": "France", "description": "Iconic venue for 2024 Paris Olympic fencing, historic setting."},
    {"name": "ExCeL London - 2012 Olympic Fencing", "lat": 51.5075, "lon": 0.0342, "type": "olympic", "country": "UK", "description": "Venue for 2012 London Olympic fencing events."},
    {"name": "Convention Center - Athens 2004", "lat": 37.9382, "lon": 23.7273, "type": "olympic", "country": "Greece", "description": "Hellinikon Fencing Hall, 2004 Athens Olympic fencing venue."},
    {"name": "Makuhari Messe - Tokyo 2020 Fencing", "lat": 35.6479, "lon": 140.0340, "type": "olympic", "country": "Japan", "description": "2020 Tokyo Olympics fencing venue at Makuhari Messe Hall."},
    {"name": "Russian Fencing Federation - Moscow", "lat": 55.7558, "lon": 37.6173, "type": "fencing_school", "country": "Russia", "description": "Russian fencing HQ, Russia has a storied Olympic fencing tradition."},
    {"name": "German Fencing Federation - Bonn", "lat": 50.7374, "lon": 7.0982, "type": "fencing_school", "country": "Germany", "description": "German Fencing Federation, Germany has a long tradition of Fechtschulen."},
    {"name": "Wallace Collection Sword Museum - London", "lat": 51.5177, "lon": -0.1530, "type": "museum", "country": "UK", "description": "Outstanding collection of European swords and arms spanning centuries."},
    {"name": "Musee de l'Armee - Paris", "lat": 48.8550, "lon": 2.3125, "type": "museum", "country": "France", "description": "World-class arms and armor collection at Les Invalides, Paris."},
    {"name": "Korean Kumdo Association - Seoul", "lat": 37.5665, "lon": 126.9780, "type": "kendo_dojo", "country": "South Korea", "description": "Korean sword arts (kumdo) federation, deeply connected to kendo tradition."},
    {"name": "Fencing Club of Philadelphia", "lat": 39.9526, "lon": -75.1652, "type": "fencing_school", "country": "USA", "description": "One of the oldest fencing clubs in the United States, founded 1873."},
    {"name": "Sydney Sabre Centre", "lat": -33.8688, "lon": 151.2093, "type": "fencing_school", "country": "Australia", "description": "Leading sabre fencing training center in Australia."},
    {"name": "FIE International Fencing Federation - Lausanne", "lat": 46.5197, "lon": 6.6323, "type": "fencing_school", "country": "Switzerland", "description": "Federation Internationale d'Escrime global headquarters."},
    {"name": "Royal Armouries - Leeds", "lat": 53.7928, "lon": -1.5307, "type": "museum", "country": "UK", "description": "UK national museum of arms and armor with extensive sword collections."},
    {"name": "Metropolitan Museum Arms & Armor - NYC", "lat": 40.7794, "lon": -73.9632, "type": "museum", "country": "USA", "description": "World-class arms and armor gallery spanning European and Asian sword traditions."},
    {"name": "Stoccata School of Defence - Sydney", "lat": -33.8700, "lon": 151.2100, "type": "hema_club", "country": "Australia", "description": "HEMA school in Sydney practicing Italian and German longsword traditions."},
    {"name": "Kenjutsu Kobudo - Kyoto", "lat": 35.0116, "lon": 135.7681, "type": "kendo_dojo", "country": "Japan", "description": "Traditional Japanese sword arts school in the ancient capital of Kyoto."},
    {"name": "Polish Fencing Federation - Warsaw", "lat": 52.2297, "lon": 21.0122, "type": "fencing_school", "country": "Poland", "description": "Polish fencing HQ, Poland has a strong tradition in sabre fencing."},
    {"name": "Egyptian Fencing Federation - Cairo", "lat": 30.0444, "lon": 31.2357, "type": "fencing_school", "country": "Egypt", "description": "Egyptian fencing HQ, Egypt dominates African fencing."},
]

# ======================================================================
# 8. WRESTLING TRADITIONS
# ======================================================================
WRESTLING_DATA = [
    {"name": "Kirkpinar Oil Wrestling - Edirne", "lat": 41.6771, "lon": 26.5557, "type": "traditional", "country": "Turkey", "description": "World oldest sporting event, Turkish oil wrestling (yagli gures) held since 1362."},
    {"name": "Sumo Grand Tournament - Ryogoku Kokugikan", "lat": 35.6969, "lon": 139.7934, "type": "sumo", "country": "Japan", "description": "Primary sumo arena in Tokyo, hosts three of six annual Grand Sumo Tournaments."},
    {"name": "Osaka Prefectural Gymnasium - Sumo", "lat": 34.6599, "lon": 135.4965, "type": "sumo", "country": "Japan", "description": "Venue for the March Grand Sumo Tournament in Osaka."},
    {"name": "Aichi Prefectural Gymnasium - Sumo", "lat": 35.1636, "lon": 136.8941, "type": "sumo", "country": "Japan", "description": "Venue for July Grand Sumo Tournament in Nagoya."},
    {"name": "Fukuoka Kokusai Center - Sumo", "lat": 33.5902, "lon": 130.4017, "type": "sumo", "country": "Japan", "description": "Venue for November Grand Sumo Tournament in Fukuoka."},
    {"name": "Naadam Festival - Ulaanbaatar", "lat": 47.9184, "lon": 106.9177, "type": "traditional", "country": "Mongolia", "description": "Mongolian national wrestling (Bokh) at the annual Naadam Festival."},
    {"name": "Akhara Wrestling Pit - Varanasi", "lat": 25.3176, "lon": 83.0068, "type": "traditional", "country": "India", "description": "Traditional kushti mud wrestling akhara in the holy city of Varanasi."},
    {"name": "Kolhapur Wrestling - Maharashtra", "lat": 16.7050, "lon": 74.2433, "type": "traditional", "country": "India", "description": "Historic Indian wrestling center, Kolhapur is the kushti capital of India."},
    {"name": "Ancient Olympia - Wrestling Origins", "lat": 37.6386, "lon": 21.6301, "type": "traditional", "country": "Greece", "description": "Birthplace of ancient Greek wrestling (Pale), an original Olympic event 708 BC."},
    {"name": "UWW Headquarters - Corsier-sur-Vevey", "lat": 46.4620, "lon": 6.8408, "type": "venue", "country": "Switzerland", "description": "United World Wrestling global headquarters near Lausanne."},
    {"name": "Dagestan Wrestling Academy - Makhachkala", "lat": 42.9849, "lon": 47.5047, "type": "school", "country": "Russia", "description": "Legendary wrestling school in Dagestan, producing Khabib, Abdulrashid Sadulaev, and dozens of Olympic champions."},
    {"name": "Nittany Lion Wrestling Club - Penn State", "lat": 40.7982, "lon": -77.8599, "type": "school", "country": "USA", "description": "Penn State, dominant NCAA wrestling program under Cael Sanderson."},
    {"name": "Iowa Hawkeyes Wrestling - Iowa City", "lat": 41.6611, "lon": -91.5302, "type": "school", "country": "USA", "description": "University of Iowa, legendary wrestling program with Dan Gable legacy."},
    {"name": "Oklahoma State Wrestling - Stillwater", "lat": 36.1156, "lon": -97.0584, "type": "school", "country": "USA", "description": "Oklahoma State Cowboys, most NCAA wrestling titles in history."},
    {"name": "Senegal Laamb Wrestling - Dakar", "lat": 14.7167, "lon": -17.4677, "type": "traditional", "country": "Senegal", "description": "Laamb (Senegalese wrestling), the national sport attracting massive audiences."},
    {"name": "Cumberland Wrestling - Grasmere", "lat": 54.4594, "lon": -3.0230, "type": "traditional", "country": "UK", "description": "Annual Grasmere Sports, home of Cumberland and Westmorland wrestling since 1852."},
    {"name": "Ssireum Korean Wrestling - Seoul", "lat": 37.5665, "lon": 126.9780, "type": "traditional", "country": "South Korea", "description": "Ssireum, traditional Korean wrestling, UNESCO Intangible Cultural Heritage."},
    {"name": "Schwingen Swiss Wrestling - Bern", "lat": 46.9480, "lon": 7.4474, "type": "traditional", "country": "Switzerland", "description": "Schwingen, traditional Swiss wrestling held at major folk festivals."},
    {"name": "Iran Wrestling Federation - Tehran", "lat": 35.6892, "lon": 51.3890, "type": "venue", "country": "Iran", "description": "Iran is a dominant force in freestyle and Greco-Roman wrestling."},
    {"name": "Glima Icelandic Wrestling - Reykjavik", "lat": 64.1466, "lon": -21.9426, "type": "traditional", "country": "Iceland", "description": "Glima, traditional Viking-era Icelandic wrestling, still practiced."},
    {"name": "Zurkhaneh - Isfahan, Iran", "lat": 32.6546, "lon": 51.6680, "type": "traditional", "country": "Iran", "description": "Traditional Zurkhaneh (house of strength), ancient Persian wrestling training."},
    {"name": "Champ-de-Mars Arena Paris 2024 Wrestling", "lat": 48.8560, "lon": 2.2980, "type": "venue", "country": "France", "description": "2024 Paris Olympic wrestling venue."},
    {"name": "Pehlwani Wrestling - Lahore", "lat": 31.5204, "lon": 74.3587, "type": "traditional", "country": "Pakistan", "description": "Traditional South Asian pehlwani wrestling in the historic wrestling city of Lahore."},
    {"name": "Lucha Libre Arena Mexico - Mexico City", "lat": 19.4260, "lon": -99.1440, "type": "venue", "country": "Mexico", "description": "Arena Mexico, the Cathedral of Lucha Libre, professional wrestling since 1956."},
    {"name": "Sambo World HQ - Moscow", "lat": 55.7558, "lon": 37.6173, "type": "venue", "country": "Russia", "description": "International Sambo Federation HQ, Russian combat sport combining judo and wrestling."},
    {"name": "Turkish National Wrestling Center - Ankara", "lat": 39.9334, "lon": 32.8597, "type": "school", "country": "Turkey", "description": "Turkey elite wrestling training center, major Olympic wrestling nation."},
    {"name": "Ringer-Bundesliga - Schifferstadt", "lat": 49.3833, "lon": 8.3833, "type": "school", "country": "Germany", "description": "Historic German wrestling center, Schifferstadt is a wrestling powerhouse town."},
    {"name": "Japan Sumo Association HQ - Tokyo", "lat": 35.6970, "lon": 139.7940, "type": "sumo", "country": "Japan", "description": "JSA headquarters governing professional sumo, located near Ryogoku Kokugikan."},
    {"name": "Bo-Taoshi Festival Wrestling - Nagasaki", "lat": 32.7503, "lon": 129.8777, "type": "traditional", "country": "Japan", "description": "Traditional Japanese rough team sport involving wrestling, played at festivals."},
]

# ======================================================================
# 9. CAPOEIRA & DANCE FIGHTING
# ======================================================================
CAPOEIRA_DATA = [
    {"name": "Pelourinho - Salvador, Bahia", "lat": -12.9714, "lon": -38.5124, "type": "origin", "country": "Brazil", "description": "Historic heart of Capoeira in Salvador, Bahia, where enslaved Africans created the art form."},
    {"name": "Forte de Santo Antonio - Capoeira Origins", "lat": -12.9698, "lon": -38.5130, "type": "origin", "country": "Brazil", "description": "Historic fort area in Salvador where early Capoeira was practiced by freed slaves."},
    {"name": "Fundacao Mestre Bimba - Salvador", "lat": -12.9811, "lon": -38.5108, "type": "academy", "country": "Brazil", "description": "Academy honoring Mestre Bimba, creator of Capoeira Regional in the 1930s."},
    {"name": "CECA (Centro Esportivo de Capoeira Angola)", "lat": -12.9730, "lon": -38.5070, "type": "academy", "country": "Brazil", "description": "Mestre Pastinha academy, he codified Capoeira Angola and preserved its traditions."},
    {"name": "FICA (Fundacao Internacional Capoeira Angola)", "lat": -12.9750, "lon": -38.5190, "type": "academy", "country": "Brazil", "description": "International Capoeira Angola Foundation in Salvador, preserving traditional roots."},
    {"name": "Grupo Senzala - Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "type": "academy", "country": "Brazil", "description": "Legendary Capoeira Senzala group founded in Rio, produced numerous mestres."},
    {"name": "Abada Capoeira HQ - Rio de Janeiro", "lat": -22.9519, "lon": -43.2105, "type": "academy", "country": "Brazil", "description": "One of the largest Capoeira organizations in the world, founded by Mestre Camisa."},
    {"name": "Capoeira Luanda - Sao Paulo", "lat": -23.5505, "lon": -46.6333, "type": "school", "country": "Brazil", "description": "Major Capoeira school in Sao Paulo, blending Regional and Angola styles."},
    {"name": "Capoeira Mandinga Academy - Oakland", "lat": 37.8044, "lon": -122.2712, "type": "school", "country": "USA", "description": "Mestre Marcelo Caveirinha Mandinga Academy in the San Francisco Bay Area."},
    {"name": "United Capoeira Association - Los Angeles", "lat": 34.0522, "lon": -118.2437, "type": "school", "country": "USA", "description": "UCA major Capoeira academy in Southern California."},
    {"name": "Capoeira Brasil - New York", "lat": 40.7128, "lon": -74.0060, "type": "school", "country": "USA", "description": "Capoeira Brasil academy in Manhattan, one of the earliest US capoeira schools."},
    {"name": "London School of Capoeira", "lat": 51.5346, "lon": -0.1040, "type": "school", "country": "UK", "description": "One of Europe oldest Capoeira schools, established in London since 1988."},
    {"name": "Paris Capoeira - Centre Culturel", "lat": 48.8566, "lon": 2.3522, "type": "school", "country": "France", "description": "Major Capoeira roda and school community in central Paris."},
    {"name": "Capoeira Ache Berlin", "lat": 52.5200, "lon": 13.4050, "type": "school", "country": "Germany", "description": "Prominent Capoeira group in Berlin with regular rodas and events."},
    {"name": "Capoeira Nago - Tokyo", "lat": 35.6762, "lon": 139.6503, "type": "school", "country": "Japan", "description": "Capoeira academy in Tokyo bringing Brazilian martial dance to Japan."},
    {"name": "Roda de Capoeira - Terreiro de Jesus, Salvador", "lat": -12.9718, "lon": -38.5102, "type": "roda", "country": "Brazil", "description": "Famous outdoor Capoeira roda location in the historic center of Salvador."},
    {"name": "Mercado Modelo Roda - Salvador", "lat": -12.9733, "lon": -38.5133, "type": "roda", "country": "Brazil", "description": "Traditional Capoeira roda spot at the Mercado Modelo market in Salvador."},
    {"name": "Forte da Capoeira - Salvador", "lat": -12.9320, "lon": -38.5009, "type": "cultural", "country": "Brazil", "description": "Official Capoeira cultural center in Santo Antonio Alem do Carmo fort, Salvador."},
    {"name": "Capoeira Mandinga - Shanghai", "lat": 31.2304, "lon": 121.4737, "type": "school", "country": "China", "description": "Capoeira Mandinga branch in Shanghai, part of the global expansion."},
    {"name": "Sydney Capoeira - Bondi", "lat": -33.8915, "lon": 151.2767, "type": "school", "country": "Australia", "description": "Active Capoeira community in Sydney with regular beach rodas."},
    {"name": "Grupo Muzenza - Recife", "lat": -8.0476, "lon": -34.8770, "type": "academy", "country": "Brazil", "description": "Mestre Burgues Muzenza group, major Capoeira organization from Recife."},
    {"name": "Silat - Minangkabau Homeland, Padang", "lat": -0.9471, "lon": 100.4172, "type": "cultural", "country": "Indonesia", "description": "Pencak Silat origins in West Sumatra, Indonesian martial dance-fighting art."},
    {"name": "Savate - Paris Boxing Francaise", "lat": 48.8490, "lon": 2.3470, "type": "cultural", "country": "France", "description": "French Savate (boxe francaise) origins, elegant European kickboxing art."},
    {"name": "Capoeira Batuque - Belo Horizonte", "lat": -19.9167, "lon": -43.9345, "type": "academy", "country": "Brazil", "description": "Mestre Acordeon lineage Capoeira school in Minas Gerais."},
    {"name": "Capoeira Angola Center - Washington DC", "lat": 38.9072, "lon": -77.0369, "type": "school", "country": "USA", "description": "Major Capoeira Angola school in the US capital preserving traditional practice."},
    {"name": "Capoeira Cordao de Ouro - Sao Paulo", "lat": -23.5400, "lon": -46.6400, "type": "academy", "country": "Brazil", "description": "Mestre Suassuna Cordao de Ouro, one of the largest capoeira groups in the world."},
    {"name": "Kalaripayattu Academy - Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366, "type": "cultural", "country": "India", "description": "CVN Kalari, major academy for Kalaripayattu, one of the oldest fighting systems in the world."},
    {"name": "Tahtib Egyptian Stick Fighting - Luxor", "lat": 25.6872, "lon": 32.6396, "type": "cultural", "country": "Egypt", "description": "Traditional Egyptian tahtib stick fighting, practiced since pharaonic times."},
    {"name": "Dambe Boxing - Kano", "lat": 12.0022, "lon": 8.5920, "type": "cultural", "country": "Nigeria", "description": "Traditional Hausa Dambe boxing, West African martial art with ancient roots."},
    {"name": "Capoeira Topazio - Lisbon", "lat": 38.7223, "lon": -9.1393, "type": "school", "country": "Portugal", "description": "Major Capoeira school in Lisbon, connecting Brazil and Portugal through martial dance."},
]

# ======================================================================
# 10. MMA & UFC VENUES
# ======================================================================
MMA_DATA = [
    {"name": "UFC Apex - Las Vegas", "lat": 36.1212, "lon": -115.2032, "type": "ufc_venue", "country": "USA", "description": "UFC primary production facility and arena for Fight Night and Contender Series."},
    {"name": "T-Mobile Arena - Las Vegas", "lat": 36.1028, "lon": -115.1784, "type": "ufc_venue", "country": "USA", "description": "Premier UFC pay-per-view venue on the Las Vegas Strip."},
    {"name": "Etihad Arena - Abu Dhabi (Fight Island)", "lat": 24.4990, "lon": 54.3982, "type": "ufc_venue", "country": "UAE", "description": "UFC Fight Island venue, hosted multiple events during COVID era and beyond."},
    {"name": "Madison Square Garden - New York", "lat": 40.7505, "lon": -73.9934, "type": "ufc_venue", "country": "USA", "description": "Iconic MSG venue for major UFC events since UFC 205 in 2016."},
    {"name": "O2 Arena - London", "lat": 51.5030, "lon": 0.0032, "type": "ufc_venue", "country": "UK", "description": "Primary UFC venue in Europe, hosting multiple Fight Night and PPV events."},
    {"name": "UFC Performance Institute - Las Vegas", "lat": 36.1200, "lon": -115.2000, "type": "training_center", "country": "USA", "description": "State-of-the-art UFC athlete training and recovery facility."},
    {"name": "UFC Performance Institute - Shanghai", "lat": 31.2304, "lon": 121.4737, "type": "training_center", "country": "China", "description": "UFC PI Shanghai, supporting MMA development in Asia."},
    {"name": "American Top Team - Coconut Creek", "lat": 26.2517, "lon": -80.1789, "type": "gym", "country": "USA", "description": "ATT one of the world top MMA gyms, home of Dustin Poirier, Jorge Masvidal."},
    {"name": "Jackson-Wink MMA Academy - Albuquerque", "lat": 35.0844, "lon": -106.6504, "type": "gym", "country": "USA", "description": "Greg Jackson and Mike Winkeljohn gym, trained Jon Jones, Holly Holm."},
    {"name": "City Kickboxing - Auckland", "lat": -36.8485, "lon": 174.7633, "type": "gym", "country": "New Zealand", "description": "Eugene Bareman gym, home of Israel Adesanya and Alexander Volkanovski."},
    {"name": "AKA (American Kickboxing Academy) - San Jose", "lat": 37.3382, "lon": -121.8863, "type": "gym", "country": "USA", "description": "Javier Mendez gym, trained Khabib Nurmagomedov, Daniel Cormier, Cain Velasquez."},
    {"name": "Tristar Gym - Montreal", "lat": 45.5017, "lon": -73.5673, "type": "gym", "country": "Canada", "description": "Firas Zahabi gym, trained Georges St-Pierre, one of MMA top coaches."},
    {"name": "Nova Uniao MMA - Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "type": "gym", "country": "Brazil", "description": "Andre Pederneiras gym, trained Jose Aldo, Renan Barao."},
    {"name": "Qudos Bank Arena - Sydney", "lat": -33.8471, "lon": 151.0694, "type": "arena", "country": "Australia", "description": "Major UFC venue in Sydney for Australian events."},
    {"name": "Jeunesse Arena - Rio de Janeiro", "lat": -22.9828, "lon": -43.3928, "type": "arena", "country": "Brazil", "description": "UFC venue in Rio, hosted multiple Brazilian UFC events."},
    {"name": "Saitama Super Arena - Tokyo", "lat": 35.8950, "lon": 139.6308, "type": "arena", "country": "Japan", "description": "Major MMA venue in Japan, hosted PRIDE FC and UFC events."},
    {"name": "Honda Center - Anaheim", "lat": 33.8078, "lon": -117.8765, "type": "ufc_venue", "country": "USA", "description": "Regular UFC event venue in Southern California."},
    {"name": "Rogers Arena - Vancouver", "lat": 49.2778, "lon": -123.1089, "type": "arena", "country": "Canada", "description": "UFC venue in Vancouver hosting Canadian MMA events."},
    {"name": "RAC Arena - Perth", "lat": -31.9505, "lon": 115.8605, "type": "arena", "country": "Australia", "description": "UFC venue in Perth, hosted UFC 284 and other major events."},
    {"name": "Bellator MMA - San Jose", "lat": 37.3382, "lon": -121.8863, "type": "headquarters", "country": "USA", "description": "Bellator MMA second major US promotion, hosting events worldwide."},
    {"name": "ONE Championship HQ - Singapore", "lat": 1.2830, "lon": 103.8450, "type": "headquarters", "country": "Singapore", "description": "ONE Championship headquarters, Asia largest MMA promotion."},
    {"name": "Dagestan MMA (Eagles MMA) - Makhachkala", "lat": 42.9849, "lon": 47.5047, "type": "gym", "country": "Russia", "description": "Training ground of Khabib Nurmagomedov and many elite Dagestani fighters."},
    {"name": "Tiger Muay Thai MMA - Phuket", "lat": 7.8940, "lon": 98.3310, "type": "gym", "country": "Thailand", "description": "Major MMA training destination in Thailand, trained Petr Yan, Valentina Shevchenko."},
    {"name": "UFC Headquarters - Las Vegas", "lat": 36.1250, "lon": -115.2100, "type": "headquarters", "country": "USA", "description": "UFC corporate headquarters in Las Vegas, Nevada."},
    {"name": "Sanford MMA - Deerfield Beach", "lat": 26.3184, "lon": -80.0998, "type": "gym", "country": "USA", "description": "Henri Hooft and Greg Jones MMA gym, trained multiple UFC champions."},
    {"name": "SBG Ireland (John Kavanagh) - Dublin", "lat": 53.3498, "lon": -6.2603, "type": "gym", "country": "Ireland", "description": "Straight Blast Gym, trained Conor McGregor from amateur to UFC champion."},
    {"name": "Xtreme Couture - Las Vegas", "lat": 36.1500, "lon": -115.1800, "type": "gym", "country": "USA", "description": "Randy Couture MMA gym, trained numerous UFC fighters."},
    {"name": "Fortis MMA - Dallas", "lat": 32.7767, "lon": -96.7970, "type": "gym", "country": "USA", "description": "Sayif Saud gym, trained Drew McIntyre, Ryan Spann, and other UFC fighters."},
    {"name": "PRIDE FC - Saitama Super Arena (Legacy)", "lat": 35.8950, "lon": 139.6308, "type": "arena", "country": "Japan", "description": "Legendary PRIDE Fighting Championships venue, the golden era of Japanese MMA."},
    {"name": "PFL (Professional Fighters League) HQ - NYC", "lat": 40.7580, "lon": -73.9855, "type": "headquarters", "country": "USA", "description": "PFL headquarters, growing MMA promotion with unique season format."},
    {"name": "Brave CF HQ - Manama, Bahrain", "lat": 26.2235, "lon": 50.5876, "type": "headquarters", "country": "Bahrain", "description": "Brave Combat Federation backed by Bahrain royalty, global MMA promotion."},
]

# ======================================================================
# MODE-TO-DATA MAPPING
# ======================================================================
MODE_DATA_MAP = {
    "Karate Origins & Dojos": KARATE_DATA,
    "Kung Fu Temples & Schools": KUNG_FU_DATA,
    "Muay Thai Camps": MUAY_THAI_DATA,
    "Brazilian Jiu-Jitsu Academies": BJJ_DATA,
    "Judo & Olympic Venues": JUDO_DATA,
    "Taekwondo Origins": TAEKWONDO_DATA,
    "Fencing & Sword Arts": FENCING_DATA,
    "Wrestling Traditions": WRESTLING_DATA,
    "Capoeira & Dance Fighting": CAPOEIRA_DATA,
    "MMA & UFC Venues": MMA_DATA,
}

MODE_ICONS = {
    "Karate Origins & Dojos": "\U0001f94b",
    "Kung Fu Temples & Schools": "\U0001f432",
    "Muay Thai Camps": "\U0001f1f9\U0001f1ed",
    "Brazilian Jiu-Jitsu Academies": "\U0001f93c",
    "Judo & Olympic Venues": "\U0001f3c5",
    "Taekwondo Origins": "\U0001f9b6",
    "Fencing & Sword Arts": "\u2694\ufe0f",
    "Wrestling Traditions": "\U0001f4aa",
    "Capoeira & Dance Fighting": "\U0001f3b6",
    "MMA & UFC Venues": "\U0001f3df\ufe0f",
}

MODE_DESCRIPTIONS = {
    "Karate Origins & Dojos": "Okinawan birthplace, Shotokan, Goju-ryu, Kyokushin, and major karate schools worldwide.",
    "Kung Fu Temples & Schools": "Shaolin Temple, Wudang, Wing Chun, Tai Chi origins, and kung fu academies globally.",
    "Muay Thai Camps": "Bangkok stadiums, Phuket camps, and traditional Muay Thai training centers.",
    "Brazilian Jiu-Jitsu Academies": "Gracie family origins, top competition teams, and BJJ academies worldwide.",
    "Judo & Olympic Venues": "Kodokan birthplace, Olympic venues, and elite judo training centers.",
    "Taekwondo Origins": "Kukkiwon, the Nine Kwans, Olympic venues, and global TKD headquarters.",
    "Fencing & Sword Arts": "European fencing schools, kendo dojos, HEMA clubs, and Olympic venues.",
    "Wrestling Traditions": "Turkish oil wrestling, Mongolian Bokh, sumo, kushti, and Greco-Roman traditions.",
    "Capoeira & Dance Fighting": "Salvador Bahia origins, roda locations, and Capoeira schools worldwide.",
    "MMA & UFC Venues": "UFC arenas, major MMA gyms, and combat sports venues globally.",
}


# ======================================================================
# HELPER FUNCTIONS
# ======================================================================
def _get_color(mode: str, loc_type: str) -> str:
    """Return marker color for a given mode and location type."""
    palette = MODE_COLORS.get(mode, {})
    return palette.get(loc_type, palette.get("default", "#e8ecf4"))


def _build_popup(name: str, description: str, country: str, loc_type: str) -> str:
    """Build HTML popup with escaped content."""
    safe_name = html_module.escape(str(name))
    safe_desc = html_module.escape(str(description))
    safe_country = html_module.escape(str(country))
    safe_type = html_module.escape(str(loc_type).replace("_", " ").title())
    return (
        f'<div style="min-width:220px;max-width:320px;font-family:sans-serif;">'
        f'<b style="font-size:13px;color:#06b6d4;">{safe_name}</b><br>'
        f'<span style="font-size:11px;color:#f59e0b;">{safe_type}</span>'
        f' &middot; <span style="font-size:11px;color:#8b97b0;">{safe_country}</span><br>'
        f'<hr style="margin:4px 0;border-color:#2a3550;">'
        f'<span style="font-size:11px;color:#e8ecf4;">{safe_desc}</span>'
        f'</div>'
    )


@st.cache_data(ttl=3600)
def _get_mode_dataframe(mode: str) -> pd.DataFrame:
    """Convert hardcoded data for a mode into a DataFrame."""
    data = MODE_DATA_MAP.get(mode, [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    col_order = ["name", "type", "country", "lat", "lon", "description"]
    existing = [c for c in col_order if c in df.columns]
    return df[existing]


@st.cache_data(ttl=3600)
def _compute_stats(mode: str) -> dict:
    """Compute summary statistics for a mode."""
    data = MODE_DATA_MAP.get(mode, [])
    if not data:
        return {"total": 0, "countries": 0, "types": 0, "top_country": "N/A"}
    df = pd.DataFrame(data)
    total = len(df)
    countries = df["country"].nunique()
    types = df["type"].nunique()
    top_country = df["country"].value_counts().idxmax() if total > 0 else "N/A"
    return {
        "total": total,
        "countries": countries,
        "types": types,
        "top_country": top_country,
    }


def _build_folium_map(mode: str, df: pd.DataFrame) -> folium.Map:
    """Build a dark folium map with CircleMarkers for the given mode data."""
    if df.empty:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    # Determine zoom based on coordinate spread
    lat_spread = df["lat"].max() - df["lat"].min()
    lon_spread = df["lon"].max() - df["lon"].min()
    max_spread = max(lat_spread, lon_spread)
    if max_spread > 100:
        zoom = 2
    elif max_spread > 50:
        zoom = 3
    elif max_spread > 20:
        zoom = 4
    elif max_spread > 10:
        zoom = 5
    else:
        zoom = 6

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for _, row in df.iterrows():
        color = _get_color(mode, row.get("type", "default"))
        popup_html = _build_popup(
            row.get("name", "Unknown"),
            row.get("description", ""),
            row.get("country", "Unknown"),
            row.get("type", "unknown"),
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=html_module.escape(str(row.get("name", ""))),
        ).add_to(m)

    return m


def _build_legend_html(mode: str) -> str:
    """Build an HTML legend for marker colors in the given mode."""
    palette = MODE_COLORS.get(mode, {})
    items = []
    for key, color in palette.items():
        if key == "default":
            continue
        label = html_module.escape(key.replace("_", " ").title())
        items.append(
            f'<span style="display:inline-flex;align-items:center;margin-right:14px;">'
            f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
            f'background:{color};margin-right:5px;"></span>'
            f'<span style="font-size:12px;color:#8b97b0;">{label}</span></span>'
        )
    return " ".join(items)


@st.cache_data(ttl=3600)
def _compute_country_distribution(mode: str) -> pd.DataFrame:
    """Compute country distribution for a given mode."""
    data = MODE_DATA_MAP.get(mode, [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    counts = df["country"].value_counts().reset_index()
    counts.columns = ["Country", "Count"]
    counts["Percentage"] = (counts["Count"] / counts["Count"].sum() * 100).round(1)
    return counts


@st.cache_data(ttl=3600)
def _compute_type_distribution(mode: str) -> pd.DataFrame:
    """Compute location type distribution for a given mode."""
    data = MODE_DATA_MAP.get(mode, [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    counts = df["type"].value_counts().reset_index()
    counts.columns = ["Type", "Count"]
    counts["Type"] = counts["Type"].str.replace("_", " ").str.title()
    counts["Percentage"] = (counts["Count"] / counts["Count"].sum() * 100).round(1)
    return counts


@st.cache_data(ttl=3600)
def _compute_geographic_spread(mode: str) -> dict:
    """Compute geographic spread metrics for a given mode."""
    data = MODE_DATA_MAP.get(mode, [])
    if not data:
        return {
            "lat_range": 0.0,
            "lon_range": 0.0,
            "center_lat": 0.0,
            "center_lon": 0.0,
            "northernmost": "N/A",
            "southernmost": "N/A",
            "easternmost": "N/A",
            "westernmost": "N/A",
        }
    df = pd.DataFrame(data)
    north_idx = df["lat"].idxmax()
    south_idx = df["lat"].idxmin()
    east_idx = df["lon"].idxmax()
    west_idx = df["lon"].idxmin()
    return {
        "lat_range": round(df["lat"].max() - df["lat"].min(), 2),
        "lon_range": round(df["lon"].max() - df["lon"].min(), 2),
        "center_lat": round(df["lat"].mean(), 4),
        "center_lon": round(df["lon"].mean(), 4),
        "northernmost": df.loc[north_idx, "name"],
        "southernmost": df.loc[south_idx, "name"],
        "easternmost": df.loc[east_idx, "name"],
        "westernmost": df.loc[west_idx, "name"],
    }


@st.cache_data(ttl=3600)
def _compute_cross_mode_summary() -> pd.DataFrame:
    """Compute a summary across all modes for the overview panel."""
    rows = []
    for mode_name, data in MODE_DATA_MAP.items():
        df = pd.DataFrame(data)
        rows.append({
            "Mode": mode_name,
            "Locations": len(df),
            "Countries": df["country"].nunique(),
            "Types": df["type"].nunique(),
            "Top Country": df["country"].value_counts().idxmax() if len(df) > 0 else "N/A",
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _get_all_locations_df() -> pd.DataFrame:
    """Get a combined DataFrame of all locations across all modes."""
    all_rows = []
    for mode_name, data in MODE_DATA_MAP.items():
        for entry in data:
            row = dict(entry)
            row["mode"] = mode_name
            all_rows.append(row)
    return pd.DataFrame(all_rows)


def _build_country_bar_html(country_df: pd.DataFrame, mode: str) -> str:
    """Build an HTML horizontal bar chart for country distribution."""
    if country_df.empty:
        return ""
    palette = MODE_COLORS.get(mode, {})
    # Use the first non-default color
    bar_color = "#06b6d4"
    for key, color in palette.items():
        if key != "default":
            bar_color = color
            break
    max_count = country_df["Count"].max()
    bars = []
    for _, row in country_df.head(10).iterrows():
        pct = row["Count"] / max_count * 100
        safe_country = html_module.escape(str(row["Country"]))
        bars.append(
            f'<div style="display:flex;align-items:center;margin:3px 0;">'
            f'<span style="min-width:120px;font-size:12px;color:#8b97b0;">{safe_country}</span>'
            f'<div style="flex:1;background:#1a2235;border-radius:4px;height:16px;overflow:hidden;">'
            f'<div style="width:{pct:.0f}%;background:{bar_color};height:100%;border-radius:4px;'
            f'transition:width 0.3s;"></div></div>'
            f'<span style="min-width:40px;text-align:right;font-size:12px;color:#e8ecf4;'
            f'margin-left:8px;">{row["Count"]}</span></div>'
        )
    return "\n".join(bars)


def _build_type_bar_html(type_df: pd.DataFrame, mode: str) -> str:
    """Build an HTML horizontal bar chart for type distribution."""
    if type_df.empty:
        return ""
    palette = MODE_COLORS.get(mode, {})
    max_count = type_df["Count"].max()
    bars = []
    for _, row in type_df.iterrows():
        pct = row["Count"] / max_count * 100
        safe_type = html_module.escape(str(row["Type"]))
        type_key = str(row["Type"]).lower().replace(" ", "_")
        bar_color = palette.get(type_key, "#06b6d4")
        bars.append(
            f'<div style="display:flex;align-items:center;margin:3px 0;">'
            f'<span style="min-width:120px;font-size:12px;color:#8b97b0;">{safe_type}</span>'
            f'<div style="flex:1;background:#1a2235;border-radius:4px;height:16px;overflow:hidden;">'
            f'<div style="width:{pct:.0f}%;background:{bar_color};height:100%;border-radius:4px;'
            f'transition:width 0.3s;"></div></div>'
            f'<span style="min-width:40px;text-align:right;font-size:12px;color:#e8ecf4;'
            f'margin-left:8px;">{row["Count"]}</span></div>'
        )
    return "\n".join(bars)


# ======================================================================
# MAIN RENDER FUNCTION
# ======================================================================
def render_martial_arts_maps_tab():
    """Render the Martial Arts & Combat Sports Maps tab."""

    # -- Tab header --
    st.markdown(
        '<div class="tab-header amber">'
        "<h4>\U0001f94b Martial Arts & Combat Sports Maps</h4>"
        "<p>Origins and schools of fighting traditions worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Mode selector --
    modes = list(MODE_DATA_MAP.keys())
    mode = st.selectbox(
        "Map Mode",
        modes,
        index=0,
        help="Select a martial art or combat sport to explore on the map.",
    )

    # -- Mode description --
    icon = MODE_ICONS.get(mode, "\U0001f94b")
    desc = MODE_DESCRIPTIONS.get(mode, "")
    st.markdown(
        f'<div style="padding:8px 14px;margin-bottom:10px;border-radius:8px;'
        f'background:rgba(15,23,42,0.65);border:1px solid #2a3550;">'
        f'<span style="font-size:20px;">{icon}</span> '
        f'<span style="color:#e8ecf4;font-size:14px;">{html_module.escape(desc)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # -- Historical context --
    history_text = MODE_HISTORY.get(mode, "")
    if history_text:
        with st.expander("Historical Context", expanded=False):
            st.markdown(
                f'<div style="padding:10px 14px;background:rgba(15,23,42,0.45);'
                f'border-radius:8px;border:1px solid #2a3550;">'
                f'<p style="color:#e8ecf4;font-size:13px;line-height:1.6;">'
                f'{html_module.escape(history_text)}</p></div>',
                unsafe_allow_html=True,
            )

    # -- Stats row --
    stats = _compute_stats(mode)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Locations", stats["total"])
    with col2:
        st.metric("Countries", stats["countries"])
    with col3:
        st.metric("Location Types", stats["types"])
    with col4:
        st.metric("Top Country", stats["top_country"])

    # -- Legend --
    legend_html = _build_legend_html(mode)
    if legend_html:
        st.markdown(
            f'<div style="padding:8px 14px;margin:6px 0 10px 0;border-radius:8px;'
            f'background:rgba(15,23,42,0.5);border:1px solid #2a3550;">'
            f'<span style="font-size:12px;color:#5a6580;margin-right:8px;">Legend:</span>'
            f'{legend_html}</div>',
            unsafe_allow_html=True,
        )

    # -- Build map --
    df = _get_mode_dataframe(mode)
    if df.empty:
        st.warning("No data available for this mode.")
        return

    m = _build_folium_map(mode, df)
    st_html(m._repr_html_(), height=500)

    # -- Data table --
    st.markdown("---")
    st.subheader(f"{icon} {mode} \u2014 Data Table")

    # Optional country filter
    countries = sorted(df["country"].unique().tolist())
    selected_countries = st.multiselect(
        "Filter by Country",
        options=countries,
        default=[],
        help="Leave empty to show all countries.",
    )

    # Optional type filter
    types_list = sorted(df["type"].unique().tolist())
    selected_types = st.multiselect(
        "Filter by Type",
        options=[t.replace("_", " ").title() for t in types_list],
        default=[],
        help="Leave empty to show all types.",
    )

    display_df = df.copy()
    if selected_countries:
        display_df = display_df[display_df["country"].isin(selected_countries)]
    if selected_types:
        # Map back to original type values
        selected_raw = [t.lower().replace(" ", "_") for t in selected_types]
        display_df = display_df[display_df["type"].isin(selected_raw)]

    # Format display DataFrame
    show_df = display_df.copy()
    show_df.columns = [c.replace("_", " ").title() for c in show_df.columns]

    st.dataframe(show_df, use_container_width=True, hide_index=True)

    st.markdown(
        f'<div style="color:#5a6580;font-size:12px;margin-top:4px;">'
        f'Showing {len(display_df)} of {len(df)} locations</div>',
        unsafe_allow_html=True,
    )

    # -- CSV download --
    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_bytes,
        file_name=f"martial_arts_{mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
    )

    # -- Distribution analysis --
    st.markdown("---")
    st.subheader(f"{icon} Distribution Analysis")

    analysis_col1, analysis_col2 = st.columns(2)

    with analysis_col1:
        st.markdown(
            '<p style="color:#06b6d4;font-weight:600;font-size:14px;margin-bottom:8px;">'
            'Country Distribution</p>',
            unsafe_allow_html=True,
        )
        country_dist = _compute_country_distribution(mode)
        country_bar_html = _build_country_bar_html(country_dist, mode)
        if country_bar_html:
            st.markdown(
                f'<div style="padding:10px;background:rgba(15,23,42,0.5);'
                f'border-radius:8px;border:1px solid #2a3550;">'
                f'{country_bar_html}</div>',
                unsafe_allow_html=True,
            )

    with analysis_col2:
        st.markdown(
            '<p style="color:#f59e0b;font-weight:600;font-size:14px;margin-bottom:8px;">'
            'Type Distribution</p>',
            unsafe_allow_html=True,
        )
        type_dist = _compute_type_distribution(mode)
        type_bar_html = _build_type_bar_html(type_dist, mode)
        if type_bar_html:
            st.markdown(
                f'<div style="padding:10px;background:rgba(15,23,42,0.5);'
                f'border-radius:8px;border:1px solid #2a3550;">'
                f'{type_bar_html}</div>',
                unsafe_allow_html=True,
            )

    # -- Geographic spread --
    st.markdown("---")
    st.subheader(f"{icon} Geographic Spread")

    geo_spread = _compute_geographic_spread(mode)
    geo_col1, geo_col2 = st.columns(2)

    with geo_col1:
        st.metric("Latitude Range", f"{geo_spread['lat_range']}\u00b0")
        st.markdown(
            f'<div style="font-size:12px;color:#8b97b0;padding:4px 0;">'
            f'<b style="color:#10b981;">Northernmost:</b> '
            f'{html_module.escape(str(geo_spread["northernmost"]))}<br>'
            f'<b style="color:#06b6d4;">Southernmost:</b> '
            f'{html_module.escape(str(geo_spread["southernmost"]))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with geo_col2:
        st.metric("Longitude Range", f"{geo_spread['lon_range']}\u00b0")
        st.markdown(
            f'<div style="font-size:12px;color:#8b97b0;padding:4px 0;">'
            f'<b style="color:#f59e0b;">Easternmost:</b> '
            f'{html_module.escape(str(geo_spread["easternmost"]))}<br>'
            f'<b style="color:#8b5cf6;">Westernmost:</b> '
            f'{html_module.escape(str(geo_spread["westernmost"]))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="font-size:12px;color:#5a6580;padding:4px 0;">'
        f'Geographic center: {geo_spread["center_lat"]}\u00b0N, '
        f'{geo_spread["center_lon"]}\u00b0E</div>',
        unsafe_allow_html=True,
    )

    # -- Cross-mode overview --
    st.markdown("---")
    st.subheader("\U0001f30d All Modes Overview")

    cross_mode_df = _compute_cross_mode_summary()
    st.dataframe(cross_mode_df, use_container_width=True, hide_index=True)

    total_all = cross_mode_df["Locations"].sum()
    total_countries_all = _get_all_locations_df()["country"].nunique()
    overview_c1, overview_c2, overview_c3 = st.columns(3)
    with overview_c1:
        st.metric("Total All Locations", int(total_all))
    with overview_c2:
        st.metric("Total Countries", int(total_countries_all))
    with overview_c3:
        st.metric("Map Modes", len(MODE_DATA_MAP))

    # -- Location details expander --
    st.markdown("---")
    st.subheader(f"{icon} Location Details")

    for _, row in display_df.iterrows():
        safe_name = html_module.escape(str(row.get("name", "Unknown")))
        safe_desc = html_module.escape(str(row.get("description", "")))
        safe_country = html_module.escape(str(row.get("country", "")))
        safe_type = html_module.escape(
            str(row.get("type", "")).replace("_", " ").title()
        )
        color = _get_color(mode, row.get("type", "default"))

        with st.expander(f"{safe_name} ({safe_country})"):
            detail_cols = st.columns([2, 1])
            with detail_cols[0]:
                st.markdown(
                    f'<span style="color:{color};font-weight:600;">{safe_type}</span>'
                    f' &middot; <span style="color:#8b97b0;">{safe_country}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<p style="color:#e8ecf4;font-size:13px;">{safe_desc}</p>',
                    unsafe_allow_html=True,
                )
            with detail_cols[1]:
                st.markdown(
                    f'<div style="color:#5a6580;font-size:12px;">'
                    f'Lat: {row["lat"]:.4f}<br>Lon: {row["lon"]:.4f}</div>',
                    unsafe_allow_html=True,
                )

    # -- Keyword search --
    st.markdown("---")
    st.subheader(f"{icon} Search Locations")

    search_query = st.text_input(
        "Search by name, description, or country",
        value="",
        placeholder="e.g., Gracie, temple, Olympic, Tokyo...",
        help="Filter locations by keyword across all fields.",
    )

    if search_query.strip():
        query_lower = search_query.strip().lower()
        search_results = df[
            df.apply(
                lambda r: (
                    query_lower in str(r.get("name", "")).lower()
                    or query_lower in str(r.get("description", "")).lower()
                    or query_lower in str(r.get("country", "")).lower()
                    or query_lower in str(r.get("type", "")).lower()
                ),
                axis=1,
            )
        ]
        if search_results.empty:
            st.info(f"No locations found matching '{html_module.escape(search_query)}'.")
        else:
            st.markdown(
                f'<div style="color:#10b981;font-size:13px;margin-bottom:8px;">'
                f'Found {len(search_results)} location(s) matching '
                f'"{html_module.escape(search_query)}"</div>',
                unsafe_allow_html=True,
            )
            search_show = search_results.copy()
            search_show.columns = [
                c.replace("_", " ").title() for c in search_show.columns
            ]
            st.dataframe(search_show, use_container_width=True, hide_index=True)

            # Build a mini-map for search results
            if len(search_results) > 0:
                search_map = _build_folium_map(mode, search_results)
                st_html(search_map._repr_html_(), height=350)

    # -- Global search across all modes --
    st.markdown("---")
    st.subheader("\U0001f50d Cross-Mode Search")

    global_query = st.text_input(
        "Search across ALL martial arts modes",
        value="",
        placeholder="e.g., London, Olympic, Bruce Lee, wrestling...",
        key="global_search",
        help="Search all 10 modes simultaneously.",
    )

    if global_query.strip():
        gq_lower = global_query.strip().lower()
        all_df = _get_all_locations_df()
        global_results = all_df[
            all_df.apply(
                lambda r: (
                    gq_lower in str(r.get("name", "")).lower()
                    or gq_lower in str(r.get("description", "")).lower()
                    or gq_lower in str(r.get("country", "")).lower()
                    or gq_lower in str(r.get("type", "")).lower()
                    or gq_lower in str(r.get("mode", "")).lower()
                ),
                axis=1,
            )
        ]
        if global_results.empty:
            st.info(
                f"No locations found matching '{html_module.escape(global_query)}' "
                f"in any mode."
            )
        else:
            st.markdown(
                f'<div style="color:#06b6d4;font-size:13px;margin-bottom:8px;">'
                f'Found {len(global_results)} location(s) across '
                f'{global_results["mode"].nunique()} mode(s) matching '
                f'"{html_module.escape(global_query)}"</div>',
                unsafe_allow_html=True,
            )
            global_show = global_results[
                ["name", "type", "country", "mode", "lat", "lon", "description"]
            ].copy()
            global_show.columns = [
                c.replace("_", " ").title() for c in global_show.columns
            ]
            st.dataframe(global_show, use_container_width=True, hide_index=True)

            # CSV download for global search results
            global_csv = io.StringIO()
            global_results.to_csv(global_csv, index=False)
            st.download_button(
                label="Download Search Results CSV",
                data=global_csv.getvalue().encode("utf-8"),
                file_name="martial_arts_search_results.csv",
                mime="text/csv",
                key="global_csv_download",
            )

    # -- Footer --
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center;padding:12px;color:#5a6580;font-size:11px;">'
        'Martial Arts &amp; Combat Sports Maps &mdash; TerraScout AI<br>'
        'Curated data covering 10 martial arts traditions across '
        f'{int(total_all)} locations in {int(total_countries_all)} countries.'
        '</div>',
        unsafe_allow_html=True,
    )
