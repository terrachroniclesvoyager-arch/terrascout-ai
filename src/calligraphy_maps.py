# -*- coding: utf-8 -*-
"""
Calligraphy & Writing Art Explorer module for TerraScout AI.
Curated data covering calligraphy traditions, illuminated manuscripts,
typography heritage, ink art, writing schools, and script history sites
across the globe. All data is hardcoded -- no API key required.
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

# =====================================================================
# DATA: 1. Chinese Calligraphy Heritage (30 locations)
# =====================================================================
CHINESE_CALLIGRAPHY = [
    {"name": "Shaoxing Lanting Pavilion (Orchid Pavilion)", "city": "Shaoxing", "country": "China", "lat": 29.996, "lon": 120.564, "tradition": "Xingshu (Running Script)", "era": "Eastern Jin (353 AD)", "master": "Wang Xizhi", "notes": "Site of the legendary Preface to the Orchid Pavilion Gathering"},
    {"name": "Xi'an Beilin (Forest of Steles)", "city": "Xi'an", "country": "China", "lat": 34.253, "lon": 108.948, "tradition": "Multiple scripts", "era": "Han-Qing Dynasty", "master": "Various", "notes": "Over 3,000 stone steles with calligraphy spanning 2,000 years"},
    {"name": "Shanghai Museum Calligraphy Gallery", "city": "Shanghai", "country": "China", "lat": 31.229, "lon": 121.473, "tradition": "All major scripts", "era": "Shang-Qing Dynasty", "master": "Various", "notes": "Premier collection of Chinese calligraphy from oracle bones to modern"},
    {"name": "National Palace Museum", "city": "Taipei", "country": "Taiwan", "lat": 25.102, "lon": 121.549, "tradition": "All Chinese scripts", "era": "Song-Qing Dynasty", "master": "Various", "notes": "Houses finest collection of imperial calligraphy treasures"},
    {"name": "Beijing Palace Museum (Forbidden City)", "city": "Beijing", "country": "China", "lat": 39.917, "lon": 116.397, "tradition": "Imperial calligraphy", "era": "Ming-Qing Dynasty", "master": "Emperor Qianlong & others", "notes": "Imperial calligraphy studios and archives"},
    {"name": "Hangzhou West Lake - Su Dongpo Memorial", "city": "Hangzhou", "country": "China", "lat": 30.247, "lon": 120.142, "tradition": "Xingshu", "era": "Northern Song", "master": "Su Shi (Su Dongpo)", "notes": "Memorial to one of the Four Great Calligraphers of Song"},
    {"name": "Meishan - Sansu Shrine", "city": "Meishan", "country": "China", "lat": 30.042, "lon": 103.831, "tradition": "Xingshu & Kaishu", "era": "Song Dynasty", "master": "Three Su Masters", "notes": "Ancestral hall of Su Xun, Su Shi, and Su Zhe"},
    {"name": "Qufu - Temple of Confucius", "city": "Qufu", "country": "China", "lat": 35.597, "lon": 116.986, "tradition": "Seal & Clerical Script", "era": "Han Dynasty onward", "master": "Various", "notes": "Ancient steles with calligraphy dedicated to Confucius"},
    {"name": "Dunhuang Mogao Caves", "city": "Dunhuang", "country": "China", "lat": 40.037, "lon": 94.802, "tradition": "Sutra calligraphy", "era": "4th-14th century", "master": "Buddhist monks", "notes": "Thousands of hand-copied sutras discovered in Cave 17"},
    {"name": "Luoyang Longmen Grottoes", "city": "Luoyang", "country": "China", "lat": 34.568, "lon": 112.470, "tradition": "Kaishu (Regular Script)", "era": "Northern Wei-Tang", "master": "Various", "notes": "Inscription calligraphy on 2,345 caves and niches"},
    {"name": "Taishan Mountain Inscriptions", "city": "Tai'an", "country": "China", "lat": 36.254, "lon": 117.107, "tradition": "Multiple scripts", "era": "Qin Dynasty onward", "master": "Emperor Qin Shihuang & others", "notes": "Cliff inscriptions from earliest unification of China"},
    {"name": "Suzhou - Wen Zhengming Garden Studio", "city": "Suzhou", "country": "China", "lat": 31.319, "lon": 120.631, "tradition": "Small Regular Script", "era": "Ming Dynasty", "master": "Wen Zhengming", "notes": "Humble Administrator's Garden linked to the calligrapher-painter"},
    {"name": "Nanjing - Zhongshan Mausoleum Steles", "city": "Nanjing", "country": "China", "lat": 32.059, "lon": 118.856, "tradition": "Clerical & Regular Script", "era": "Six Dynasties-Modern", "master": "Various", "notes": "Calligraphic inscriptions across historic monuments"},
    {"name": "Chengdu Du Fu Thatched Cottage", "city": "Chengdu", "country": "China", "lat": 30.640, "lon": 104.028, "tradition": "Poetry-calligraphy", "era": "Tang Dynasty", "master": "Du Fu legacy", "notes": "Calligraphic renderings of Du Fu poems through centuries"},
    {"name": "Anyang - Yinxu Oracle Bone Site", "city": "Anyang", "country": "China", "lat": 36.122, "lon": 114.303, "tradition": "Jiaguwen (Oracle Bone Script)", "era": "Shang Dynasty (c. 1200 BC)", "master": "Shang scribes", "notes": "Birthplace of Chinese writing; earliest Chinese characters"},
    {"name": "Hubei Provincial Museum - Baoshan Chu Slips", "city": "Wuhan", "country": "China", "lat": 30.566, "lon": 114.362, "tradition": "Chu bamboo slip script", "era": "Warring States", "master": "Chu scribes", "notes": "Bamboo slip calligraphy from the Chu state"},
    {"name": "Yan Zhenqing Temple", "city": "Fei County, Shandong", "country": "China", "lat": 35.271, "lon": 117.965, "tradition": "Kaishu (Regular Script)", "era": "Tang Dynasty", "master": "Yan Zhenqing", "notes": "Dedicated to the master of powerful structured regular script"},
    {"name": "Ouyang Xun Memorial Hall", "city": "Changsha", "country": "China", "lat": 28.189, "lon": 112.967, "tradition": "Kaishu (Regular Script)", "era": "Tang Dynasty", "master": "Ouyang Xun", "notes": "Memorial for the calligrapher whose Jiucheng Palace stele is canonical"},
    {"name": "Huashan Mountain Inscriptions", "city": "Huayin", "country": "China", "lat": 34.475, "lon": 110.088, "tradition": "Cliff calligraphy", "era": "Various dynasties", "master": "Various", "notes": "Sacred mountain with millennia of cliff inscriptions"},
    {"name": "China National Silk Museum", "city": "Hangzhou", "country": "China", "lat": 30.231, "lon": 120.144, "tradition": "Silk calligraphy", "era": "Han Dynasty onward", "master": "Various", "notes": "Earliest calligraphy on silk from Mawangdui tombs"},
    {"name": "Zhaoqing - Duanyan Inkstone Museum", "city": "Zhaoqing", "country": "China", "lat": 23.047, "lon": 112.458, "tradition": "Ink & tools", "era": "Tang Dynasty onward", "master": "Artisans", "notes": "Duan inkstones, the most prized calligraphy tool"},
    {"name": "Xuanzhou - Xuan Paper Cultural Park", "city": "Jingxian", "country": "China", "lat": 30.648, "lon": 118.416, "tradition": "Paper-making", "era": "Tang Dynasty onward", "master": "Artisans", "notes": "Origin of Xuan paper, essential for Chinese calligraphy"},
    {"name": "Huzhou - Chinese Brush Museum", "city": "Huzhou", "country": "China", "lat": 30.872, "lon": 120.087, "tradition": "Brush-making", "era": "Qin Dynasty onward", "master": "Meng Tian legend", "notes": "Birthplace of the calligraphy brush; Four Treasures of the Study"},
    {"name": "She County - Hui Ink Museum", "city": "She County", "country": "China", "lat": 29.874, "lon": 118.437, "tradition": "Ink-making", "era": "Tang Dynasty onward", "master": "Artisans", "notes": "Hui ink: finest soot-based calligraphy ink in China"},
    {"name": "Linyi - Wang Xizhi Birthplace Museum", "city": "Linyi", "country": "China", "lat": 35.058, "lon": 118.344, "tradition": "Xingshu", "era": "Eastern Jin Dynasty", "master": "Wang Xizhi", "notes": "Birthplace of the Sage of Calligraphy"},
    {"name": "Guilin Cliff Inscriptions", "city": "Guilin", "country": "China", "lat": 25.273, "lon": 110.290, "tradition": "Cliff calligraphy", "era": "Tang-Qing Dynasty", "master": "Various", "notes": "Over 2,000 cliff inscriptions in the karst landscape"},
    {"name": "Kaifeng - Bianjing Calligraphy District", "city": "Kaifeng", "country": "China", "lat": 34.798, "lon": 114.308, "tradition": "Song calligraphy", "era": "Northern Song", "master": "Huang Tingjian & Mi Fu", "notes": "Former capital where the Four Song Masters flourished"},
    {"name": "Zhenjiang Jiao Mountain Steles", "city": "Zhenjiang", "country": "China", "lat": 32.230, "lon": 119.575, "tradition": "Stele calligraphy", "era": "Tang-Song", "master": "Various", "notes": "Stele garden with major calligraphic works"},
    {"name": "Changzhou - Bi Yuan Calligraphy Site", "city": "Changzhou", "country": "China", "lat": 31.811, "lon": 119.974, "tradition": "Stele school revival", "era": "Qing Dynasty", "master": "Bi Yuan", "notes": "Center of the Qing stele-school calligraphy movement"},
    {"name": "Hong Kong Museum of Art - Xubaizhai Collection", "city": "Hong Kong", "country": "China", "lat": 22.294, "lon": 114.170, "tradition": "All Chinese scripts", "era": "Song-Qing", "master": "Various", "notes": "Xubaizhai donation of masterwork calligraphy and painting"},
]

# =====================================================================
# DATA: 2. Japanese Shodo Traditions (30 locations)
# =====================================================================
JAPANESE_SHODO = [
    {"name": "Tokyo National Museum - Heiseikan Gallery", "city": "Tokyo", "country": "Japan", "lat": 35.719, "lon": 139.776, "tradition": "Shodo (all styles)", "era": "Nara-Modern", "master": "National collection", "notes": "Japan's most comprehensive calligraphy collection"},
    {"name": "Naritasan Shinsho-ji Temple", "city": "Narita", "country": "Japan", "lat": 35.784, "lon": 140.318, "tradition": "Buddhist calligraphy", "era": "Heian onward", "master": "Temple monks", "notes": "Annual calligraphy festival; massive New Year brushwork events"},
    {"name": "Kyoto National Museum", "city": "Kyoto", "country": "Japan", "lat": 34.989, "lon": 135.773, "tradition": "Kana & Kanji calligraphy", "era": "Heian-Edo", "master": "Various", "notes": "Houses Important Cultural Properties of Japanese calligraphy"},
    {"name": "Tofuku-ji Zen Temple", "city": "Kyoto", "country": "Japan", "lat": 34.976, "lon": 135.774, "tradition": "Zen calligraphy (Bokuseki)", "era": "Kamakura-Muromachi", "master": "Zen abbots", "notes": "Premier collection of Zen calligraphic works (bokuseki)"},
    {"name": "Daitoku-ji Temple", "city": "Kyoto", "country": "Japan", "lat": 35.045, "lon": 135.746, "tradition": "Zen calligraphy", "era": "Muromachi", "master": "Ikkyu Sojun", "notes": "Ikkyu's wild Zen brushwork preserved in sub-temples"},
    {"name": "Shoren-in Temple", "city": "Kyoto", "country": "Japan", "lat": 35.006, "lon": 135.785, "tradition": "Shoren-in school (Oie-ryu)", "era": "Heian onward", "master": "Prince Son'en", "notes": "Origin of Oie-ryu calligraphy, dominant Japanese writing school"},
    {"name": "Nara National Museum", "city": "Nara", "country": "Japan", "lat": 34.684, "lon": 135.840, "tradition": "Early Japanese scripts", "era": "Nara period", "master": "Kukai & others", "notes": "Shoso-in documents; earliest Japanese calligraphy masterworks"},
    {"name": "Koya-san Mount Koya", "city": "Koya", "country": "Japan", "lat": 34.213, "lon": 135.581, "tradition": "Shingon Buddhist calligraphy", "era": "Heian", "master": "Kukai (Kobo Daishi)", "notes": "Kukai: one of Three Great Calligraphers of Japan (Sanpitsu)"},
    {"name": "Sagano Bamboo Forest - Tenryu-ji", "city": "Kyoto", "country": "Japan", "lat": 35.016, "lon": 135.674, "tradition": "Zen calligraphy", "era": "Muromachi", "master": "Muso Soseki", "notes": "Temple founded by calligrapher-monk Muso Soseki"},
    {"name": "Enku-do Museum", "city": "Seki, Gifu", "country": "Japan", "lat": 35.496, "lon": 136.918, "tradition": "Buddhist calligraphy", "era": "Edo", "master": "Enku", "notes": "Calligraphy and prayer inscriptions by itinerant monk Enku"},
    {"name": "Idemitsu Museum of Arts", "city": "Tokyo", "country": "Japan", "lat": 35.674, "lon": 139.762, "tradition": "Zen & literary calligraphy", "era": "Various", "master": "Sengai Gibon & others", "notes": "Sengai's whimsical Zen calligraphy and Zenga paintings"},
    {"name": "Sumida Hokusai Museum", "city": "Tokyo", "country": "Japan", "lat": 35.696, "lon": 139.804, "tradition": "Ukiyo-e lettering", "era": "Edo", "master": "Katsushika Hokusai", "notes": "Hokusai's calligraphic titling and inscriptions on prints"},
    {"name": "Nara - Todai-ji Great Eastern Temple", "city": "Nara", "country": "Japan", "lat": 34.689, "lon": 135.840, "tradition": "Sutra copying (Shakyou)", "era": "Nara period", "master": "Imperial scribes", "notes": "Origin of Japanese sutra-copying tradition; Shoso-in treasures"},
    {"name": "Kumano Nachi Shrine", "city": "Nachikatsuura", "country": "Japan", "lat": 33.672, "lon": 135.889, "tradition": "Shrine calligraphy", "era": "Heian", "master": "Shrine priests", "notes": "Sacred calligraphic talismans (ofuda) and pilgrim stamps"},
    {"name": "Ise Grand Shrine", "city": "Ise", "country": "Japan", "lat": 34.455, "lon": 136.726, "tradition": "Sacred calligraphy", "era": "Antiquity", "master": "Shrine tradition", "notes": "Japan's most sacred site; ritual calligraphy traditions"},
    {"name": "Fukuoka - Hakata Traditional Craft Center", "city": "Fukuoka", "country": "Japan", "lat": 33.590, "lon": 130.401, "tradition": "Brush and ink craft", "era": "Modern", "master": "Artisans", "notes": "Hakata's fude (calligraphy brush) crafting tradition"},
    {"name": "Kumano Brush Village", "city": "Kumano, Hiroshima", "country": "Japan", "lat": 34.334, "lon": 132.575, "tradition": "Brush-making", "era": "Edo onward", "master": "Artisans", "notes": "Produces 80% of Japan's calligraphy brushes"},
    {"name": "Kamakura - Engaku-ji Temple", "city": "Kamakura", "country": "Japan", "lat": 35.338, "lon": 139.550, "tradition": "Zen calligraphy", "era": "Kamakura", "master": "Mugaku Sogen", "notes": "Chinese Zen master's calligraphy brought to Kamakura"},
    {"name": "Ryoan-ji Temple", "city": "Kyoto", "country": "Japan", "lat": 35.034, "lon": 135.718, "tradition": "Zen brushwork", "era": "Muromachi", "master": "Zen monks", "notes": "Zen rock garden embodies calligraphic spatial concepts"},
    {"name": "Osaka - Nakanoshima Museum of Art", "city": "Osaka", "country": "Japan", "lat": 34.691, "lon": 135.492, "tradition": "Modern calligraphy", "era": "Modern-Contemporary", "master": "Inoue Yuichi & others", "notes": "Avant-garde calligraphy by post-war Japanese masters"},
    {"name": "Saitama - Omiya Bonsai Art Museum", "city": "Saitama", "country": "Japan", "lat": 35.906, "lon": 139.635, "tradition": "Bonsai naming calligraphy", "era": "Edo-Modern", "master": "Various", "notes": "Traditional naming scrolls and calligraphic bonsai displays"},
    {"name": "Nara - Kasuga Grand Shrine", "city": "Nara", "country": "Japan", "lat": 34.681, "lon": 135.849, "tradition": "Dedicatory calligraphy", "era": "Nara onward", "master": "Shrine calligraphers", "notes": "Thousands of stone and bronze lanterns with calligraphic inscriptions"},
    {"name": "Matsue - Lafcadio Hearn Memorial", "city": "Matsue", "country": "Japan", "lat": 35.475, "lon": 133.048, "tradition": "Literary calligraphy", "era": "Meiji", "master": "Lafcadio Hearn/Koizumi Yakumo", "notes": "East-West calligraphic and literary fusion"},
    {"name": "Sendai - Zuigan-ji Temple", "city": "Matsushima", "country": "Japan", "lat": 38.373, "lon": 141.062, "tradition": "Zen calligraphy", "era": "Kamakura-Edo", "master": "Date Masamune patronage", "notes": "Fine calligraphic scrolls from Date clan patronage"},
    {"name": "Gifu - Cormorant Fishing Museum", "city": "Gifu", "country": "Japan", "lat": 35.434, "lon": 136.784, "tradition": "Fan calligraphy", "era": "Various", "master": "Various", "notes": "Calligraphic traditions on Gifu fans and lanterns"},
    {"name": "Kanazawa - Ishikawa Prefectural Museum", "city": "Kanazawa", "country": "Japan", "lat": 36.562, "lon": 136.657, "tradition": "Kaga calligraphy", "era": "Edo", "master": "Maeda clan scribes", "notes": "Maeda domain calligraphy and literary arts collection"},
    {"name": "Nagasaki - Sofuku-ji Temple", "city": "Nagasaki", "country": "Japan", "lat": 32.742, "lon": 129.882, "tradition": "Chinese-Japanese calligraphy", "era": "Edo", "master": "Chinese monks in Japan", "notes": "Obaku Zen calligraphy by Chinese emigre monks"},
    {"name": "Shizuoka - MOA Museum of Art", "city": "Atami", "country": "Japan", "lat": 35.089, "lon": 139.072, "tradition": "Japanese calligraphy", "era": "Heian-Edo", "master": "Various", "notes": "National Treasure calligraphy scrolls and screens"},
    {"name": "Himeji Castle Calligraphy Museum", "city": "Himeji", "country": "Japan", "lat": 34.839, "lon": 134.694, "tradition": "Samurai calligraphy", "era": "Sengoku-Edo", "master": "Samurai scribes", "notes": "Castle documents and samurai calligraphic arts"},
    {"name": "Yokohama Museum of Art", "city": "Yokohama", "country": "Japan", "lat": 35.458, "lon": 139.632, "tradition": "Modern calligraphy art", "era": "Showa-Heisei", "master": "Various", "notes": "Contemporary calligraphic art exhibitions"},
]

# =====================================================================
# DATA: 3. Arabic & Islamic Calligraphy (30 locations)
# =====================================================================
ARABIC_CALLIGRAPHY = [
    {"name": "Topkapi Palace - Sacred Relics", "city": "Istanbul", "country": "Turkey", "lat": 41.013, "lon": 28.983, "tradition": "Thuluth, Naskh, Diwani", "era": "Ottoman Empire", "master": "Seyh Hamdullah & others", "notes": "Imperial calligraphy collection; earliest Quran manuscripts"},
    {"name": "Hagia Sophia Calligraphic Roundels", "city": "Istanbul", "country": "Turkey", "lat": 41.009, "lon": 28.980, "tradition": "Thuluth monumental", "era": "19th century", "master": "Kazasker Mustafa Izzet", "notes": "Eight massive calligraphic roundels, largest in the Islamic world"},
    {"name": "Museum of Turkish & Islamic Arts", "city": "Istanbul", "country": "Turkey", "lat": 41.005, "lon": 28.975, "tradition": "All Ottoman scripts", "era": "Ottoman period", "master": "Various", "notes": "Over 15,000 calligraphic works and Quran manuscripts"},
    {"name": "Sultan Ahmed Mosque (Blue Mosque)", "city": "Istanbul", "country": "Turkey", "lat": 41.005, "lon": 28.977, "tradition": "Architectural calligraphy", "era": "1609-1616", "master": "Seyyid Kasim Gubari", "notes": "Interior tile calligraphy in Iznik ceramics with Quranic verses"},
    {"name": "Alhambra Palace", "city": "Granada", "country": "Spain", "lat": 37.177, "lon": -3.590, "tradition": "Nasrid calligraphy (Kufic & Thuluth)", "era": "13th-14th century", "master": "Nasrid artisans", "notes": "Stucco calligraphy covering walls; 'There is no conqueror but God'"},
    {"name": "Al-Azhar Mosque", "city": "Cairo", "country": "Egypt", "lat": 30.045, "lon": 31.263, "tradition": "Naskh & Thuluth", "era": "Fatimid (970 AD)", "master": "Various", "notes": "One of the oldest mosques; major center of Islamic calligraphy education"},
    {"name": "Museum of Islamic Art Cairo", "city": "Cairo", "country": "Egypt", "lat": 30.042, "lon": 31.257, "tradition": "All Islamic scripts", "era": "7th-19th century", "master": "Various", "notes": "Largest collection of Islamic calligraphy in the Arab world"},
    {"name": "Great Mosque of Cordoba (Mezquita)", "city": "Cordoba", "country": "Spain", "lat": 37.879, "lon": -4.779, "tradition": "Kufic & Andalusian scripts", "era": "8th-10th century", "master": "Umayyad artisans", "notes": "Carved stucco and mosaic calligraphy in Umayyad Andalusian style"},
    {"name": "Sheikh Zayed Grand Mosque", "city": "Abu Dhabi", "country": "UAE", "lat": 24.413, "lon": 54.475, "tradition": "Thuluth, Naskh, Kufic", "era": "2007", "master": "Mohamed Mandi & others", "notes": "Modern masterpiece with calligraphy by 11 artists from 7 nations"},
    {"name": "Sharjah Calligraphy Museum", "city": "Sharjah", "country": "UAE", "lat": 25.357, "lon": 55.387, "tradition": "Arabic calligraphy", "era": "Contemporary", "master": "Various", "notes": "Dedicated calligraphy museum; annual Sharjah Calligraphy Biennial"},
    {"name": "Islamic Arts Museum Malaysia", "city": "Kuala Lumpur", "country": "Malaysia", "lat": 3.143, "lon": 101.690, "tradition": "Southeast Asian Islamic scripts", "era": "Various", "master": "Various", "notes": "Quran gallery with calligraphy from across the Islamic world"},
    {"name": "Imam Reza Shrine Complex", "city": "Mashhad", "country": "Iran", "lat": 36.289, "lon": 59.612, "tradition": "Nastaliq & Thuluth", "era": "Timurid onward", "master": "Various", "notes": "Extensive tile calligraphy in Persian Nastaliq and Arabic Thuluth"},
    {"name": "Shah Mosque (Masjed-e Shah)", "city": "Isfahan", "country": "Iran", "lat": 32.654, "lon": 51.678, "tradition": "Nastaliq & Thuluth", "era": "Safavid (1611-1629)", "master": "Alireza Abbasi", "notes": "Finest Safavid tile calligraphy; inscriptions by royal calligrapher"},
    {"name": "Fez Bou Inania Madrasa", "city": "Fez", "country": "Morocco", "lat": 34.062, "lon": -4.982, "tradition": "Maghribi script", "era": "Marinid (1351-1356)", "master": "Marinid artisans", "notes": "Finest example of carved stucco Maghribi calligraphy"},
    {"name": "Al-Qarawiyyin University Library", "city": "Fez", "country": "Morocco", "lat": 34.064, "lon": -4.973, "tradition": "Maghribi manuscript calligraphy", "era": "859 AD onward", "master": "Various scribes", "notes": "Oldest university library in the world; priceless manuscript collection"},
    {"name": "Samarkand - Registan Square", "city": "Samarkand", "country": "Uzbekistan", "lat": 39.655, "lon": 66.976, "tradition": "Kufic & Thuluth tile work", "era": "Timurid (15th-17th century)", "master": "Timurid artisans", "notes": "Monumental portal calligraphy on three madrasas"},
    {"name": "Dome of the Rock", "city": "Jerusalem", "country": "Israel/Palestine", "lat": 31.778, "lon": 35.236, "tradition": "Kufic (exterior), Thuluth (interior)", "era": "691 AD; renovated Ottoman", "master": "Various", "notes": "Oldest surviving Islamic calligraphic inscriptions on architecture"},
    {"name": "Masjid al-Haram (Great Mosque of Mecca)", "city": "Mecca", "country": "Saudi Arabia", "lat": 21.423, "lon": 39.826, "tradition": "Thuluth & Naskh", "era": "Various expansions", "master": "Various", "notes": "Holiest site in Islam; kiswah of the Kaaba has gold calligraphy"},
    {"name": "Masjid an-Nabawi (Prophet's Mosque)", "city": "Medina", "country": "Saudi Arabia", "lat": 24.468, "lon": 39.611, "tradition": "Thuluth & Naskh", "era": "Various", "master": "Various", "notes": "Quranic calligraphy throughout the mosque and Green Dome"},
    {"name": "Hassan II Mosque", "city": "Casablanca", "country": "Morocco", "lat": 33.609, "lon": -7.632, "tradition": "Maghribi & Thuluth", "era": "1993", "master": "Moroccan artisans", "notes": "Modern Moroccan calligraphy on the world's tallest minaret"},
    {"name": "Sakip Sabanci Museum", "city": "Istanbul", "country": "Turkey", "lat": 41.107, "lon": 29.057, "tradition": "Ottoman calligraphy", "era": "Ottoman-Republic", "master": "Hamid Aytac & others", "notes": "Finest private collection of Ottoman calligraphy"},
    {"name": "Wazir Khan Mosque", "city": "Lahore", "country": "Pakistan", "lat": 31.582, "lon": 74.325, "tradition": "Nastaliq & Thuluth tile", "era": "Mughal (1634-1641)", "master": "Mughal artisans", "notes": "Finest tile calligraphy in Mughal architecture"},
    {"name": "Badshahi Mosque", "city": "Lahore", "country": "Pakistan", "lat": 31.588, "lon": 74.310, "tradition": "Thuluth & Naskh", "era": "Mughal (1673)", "master": "Mughal artisans", "notes": "Red sandstone and marble inlay calligraphy"},
    {"name": "Taj Mahal", "city": "Agra", "country": "India", "lat": 27.175, "lon": 78.042, "tradition": "Thuluth inlay", "era": "Mughal (1632-1653)", "master": "Amanat Khan", "notes": "Quranic calligraphy in black marble inlay; master calligrapher credited"},
    {"name": "Selimiye Mosque", "city": "Edirne", "country": "Turkey", "lat": 41.678, "lon": 26.559, "tradition": "Thuluth monumental", "era": "Ottoman (1568-1574)", "master": "Sinan / calligraphers", "notes": "Mimar Sinan's masterpiece with integrated calligraphic program"},
    {"name": "National Museum of Qatar", "city": "Doha", "country": "Qatar", "lat": 25.287, "lon": 51.549, "tradition": "Arabic calligraphy", "era": "Modern display", "master": "Various", "notes": "Contemporary curation of Arab calligraphic heritage"},
    {"name": "Ben Youssef Madrasa", "city": "Marrakech", "country": "Morocco", "lat": 31.633, "lon": -7.987, "tradition": "Maghribi carved stucco", "era": "Saadian (16th century)", "master": "Moroccan artisans", "notes": "Elaborate stucco calligraphy panels with Quranic text"},
    {"name": "Suleymaniye Mosque", "city": "Istanbul", "country": "Turkey", "lat": 41.016, "lon": 28.964, "tradition": "Thuluth & Naskh", "era": "Ottoman (1550-1557)", "master": "Ahmed Karahisari", "notes": "Calligraphy by Ahmed Karahisari, master of the golden age"},
    {"name": "King Abdulaziz Center (Ithra)", "city": "Dhahran", "country": "Saudi Arabia", "lat": 26.321, "lon": 50.133, "tradition": "Contemporary Arabic calligraphy", "era": "Modern", "master": "Various", "notes": "Promotes modern Arabic calligraphic art and design"},
    {"name": "Bibliotheca Alexandrina", "city": "Alexandria", "country": "Egypt", "lat": 31.209, "lon": 29.909, "tradition": "Arabic calligraphy & scripts", "era": "Modern revival", "master": "Various", "notes": "Exterior carved with scripts from 120 human languages"},
]

# =====================================================================
# DATA: 4. Medieval Illuminated Manuscripts (30 locations)
# =====================================================================
ILLUMINATED_MANUSCRIPTS = [
    {"name": "Trinity College Library - Book of Kells", "city": "Dublin", "country": "Ireland", "lat": 53.344, "lon": -6.257, "tradition": "Insular majuscule", "era": "c. 800 AD", "master": "Columban monks", "notes": "Ireland's greatest treasure; masterpiece of insular illumination"},
    {"name": "British Library - Lindisfarne Gospels", "city": "London", "country": "UK", "lat": 51.530, "lon": -0.127, "tradition": "Insular script", "era": "c. 700 AD", "master": "Eadfrith of Lindisfarne", "notes": "Finest example of Hiberno-Saxon illuminated manuscript art"},
    {"name": "Bodleian Library, Oxford", "city": "Oxford", "country": "UK", "lat": 51.754, "lon": -1.254, "tradition": "Latin manuscript scripts", "era": "Medieval", "master": "Various scriptoria", "notes": "Major collection of illuminated manuscripts from European monasteries"},
    {"name": "Bibliotheque nationale de France", "city": "Paris", "country": "France", "lat": 48.834, "lon": 2.376, "tradition": "Gothic textura & bastarda", "era": "Medieval-Renaissance", "master": "Limbourg Brothers & others", "notes": "Tres Riches Heures du Duc de Berry and vast manuscript holdings"},
    {"name": "Musee Conde - Tres Riches Heures", "city": "Chantilly", "country": "France", "lat": 49.194, "lon": 2.484, "tradition": "International Gothic", "era": "c. 1412-1416", "master": "Limbourg Brothers", "notes": "The most famous illuminated manuscript in art history"},
    {"name": "Vatican Apostolic Library", "city": "Vatican City", "country": "Vatican", "lat": 41.905, "lon": 12.454, "tradition": "Latin & Greek scripts", "era": "4th century onward", "master": "Various", "notes": "80,000 manuscripts including Codex Vaticanus and papal documents"},
    {"name": "Abbey Library of St. Gall", "city": "St. Gallen", "country": "Switzerland", "lat": 47.423, "lon": 9.377, "tradition": "Carolingian minuscule", "era": "8th-12th century", "master": "St. Gall monks", "notes": "UNESCO World Heritage; finest surviving Carolingian scriptorium"},
    {"name": "Stiftsbibliothek Admont", "city": "Admont", "country": "Austria", "lat": 47.573, "lon": 14.461, "tradition": "Romanesque illumination", "era": "12th century", "master": "Admont monks", "notes": "World's largest monastic library; outstanding manuscript illumination"},
    {"name": "Chester Beatty Library", "city": "Dublin", "country": "Ireland", "lat": 53.342, "lon": -6.268, "tradition": "Multi-tradition manuscripts", "era": "2nd-19th century", "master": "Various", "notes": "Papyri, Qurans, East Asian scrolls, and European manuscripts"},
    {"name": "Morgan Library & Museum", "city": "New York", "country": "USA", "lat": 40.749, "lon": -73.981, "tradition": "Medieval European scripts", "era": "9th-16th century", "master": "Various", "notes": "World-class illuminated manuscripts including Lindau Gospels cover"},
    {"name": "Getty Museum - Manuscripts Collection", "city": "Los Angeles", "country": "USA", "lat": 34.078, "lon": -118.474, "tradition": "Gothic & Renaissance scripts", "era": "9th-16th century", "master": "Various", "notes": "Outstanding collection of European illuminated manuscripts"},
    {"name": "Walters Art Museum", "city": "Baltimore", "country": "USA", "lat": 39.296, "lon": -76.616, "tradition": "Byzantine & Western scripts", "era": "Medieval", "master": "Various", "notes": "Strong holdings in Armenian, Ethiopian, and Western manuscripts"},
    {"name": "Lindisfarne Priory", "city": "Lindisfarne", "country": "UK", "lat": 55.669, "lon": -1.800, "tradition": "Insular script origin", "era": "7th-8th century", "master": "Eadfrith", "notes": "Holy Island where the Lindisfarne Gospels were created"},
    {"name": "Iona Abbey", "city": "Iona", "country": "UK (Scotland)", "lat": 56.333, "lon": -6.407, "tradition": "Insular majuscule", "era": "6th-9th century", "master": "Columba & followers", "notes": "Likely origin of the Book of Kells; Columban monastic scriptorium"},
    {"name": "Kells Priory", "city": "Kells", "country": "Ireland", "lat": 53.726, "lon": -6.879, "tradition": "Insular script", "era": "9th century", "master": "Columban monks", "notes": "Where the Book of Kells was kept for centuries after Iona"},
    {"name": "Cluny Abbey Ruins", "city": "Cluny", "country": "France", "lat": 46.434, "lon": 4.660, "tradition": "Cluniac illumination", "era": "10th-12th century", "master": "Cluniac monks", "notes": "Center of medieval European manuscript production; Romanesque art"},
    {"name": "Bayerische Staatsbibliothek", "city": "Munich", "country": "Germany", "lat": 48.150, "lon": 11.579, "tradition": "Ottonian & Gothic illumination", "era": "Medieval", "master": "Reichenau school", "notes": "Major collection including Ottonian and Carolingian illuminated works"},
    {"name": "Stiftsbibliothek Melk Abbey", "city": "Melk", "country": "Austria", "lat": 48.228, "lon": 15.332, "tradition": "Romanesque to Baroque scripts", "era": "12th century onward", "master": "Benedictine monks", "notes": "Danubian Benedictine scriptorium; featured in The Name of the Rose"},
    {"name": "Biblioteca Medicea Laurenziana", "city": "Florence", "country": "Italy", "lat": 43.774, "lon": 11.253, "tradition": "Humanist scripts", "era": "Renaissance", "master": "Various", "notes": "Medici manuscript collection in Michelangelo-designed library"},
    {"name": "Chartres Cathedral Treasury", "city": "Chartres", "country": "France", "lat": 48.447, "lon": 1.488, "tradition": "Gothic liturgical scripts", "era": "12th-13th century", "master": "Chartres scriptoria", "notes": "Liturgical manuscripts associated with the great Gothic cathedral"},
    {"name": "Durham Cathedral Library", "city": "Durham", "country": "UK", "lat": 54.773, "lon": -1.576, "tradition": "Anglo-Saxon & Norman scripts", "era": "7th-12th century", "master": "Various", "notes": "Pre-Conquest manuscripts including Durham Cassiodorus"},
    {"name": "Matenadaran Institute", "city": "Yerevan", "country": "Armenia", "lat": 40.193, "lon": 44.521, "tradition": "Armenian uncial (Erkatagir)", "era": "5th century onward", "master": "Mesrop Mashtots school", "notes": "World's largest repository of Armenian manuscripts (23,000+)"},
    {"name": "Biblioteca Marciana", "city": "Venice", "country": "Italy", "lat": 45.434, "lon": 12.339, "tradition": "Byzantine & Gothic scripts", "era": "Medieval-Renaissance", "master": "Various", "notes": "Cardinal Bessarion's Greek manuscript collection"},
    {"name": "Royal Library of Belgium", "city": "Brussels", "country": "Belgium", "lat": 50.843, "lon": 4.358, "tradition": "Flemish illumination", "era": "15th century", "master": "Flemish Masters", "notes": "Burgundian court manuscripts with gold-leaf illumination"},
    {"name": "Winchester Cathedral Library", "city": "Winchester", "country": "UK", "lat": 51.061, "lon": -1.314, "tradition": "Winchester school", "era": "10th-11th century", "master": "Winchester monks", "notes": "Winchester Bible and Anglo-Saxon illuminated manuscript tradition"},
    {"name": "Scriptorium de Toulouse", "city": "Toulouse", "country": "France", "lat": 43.604, "lon": 1.444, "tradition": "Gothic textura", "era": "13th-14th century", "master": "Dominican scribes", "notes": "Major Dominican manuscript production center"},
    {"name": "Erfurt - Amploniana Collection", "city": "Erfurt", "country": "Germany", "lat": 50.978, "lon": 11.029, "tradition": "Scholastic manuscripts", "era": "14th century", "master": "Amplonius Rating", "notes": "Largest surviving medieval personal library; UNESCO Memory of World"},
    {"name": "National Library of Sweden", "city": "Stockholm", "country": "Sweden", "lat": 59.343, "lon": 18.072, "tradition": "Norse-Latin scripts", "era": "Medieval", "master": "Various", "notes": "Codex Gigas (Devil's Bible), the largest surviving medieval manuscript"},
    {"name": "Beinecke Library, Yale", "city": "New Haven", "country": "USA", "lat": 41.311, "lon": -72.927, "tradition": "Various medieval scripts", "era": "Medieval", "master": "Various", "notes": "Voynich Manuscript and major medieval codex collection"},
    {"name": "Escorial Royal Library", "city": "San Lorenzo de El Escorial", "country": "Spain", "lat": 40.589, "lon": -4.148, "tradition": "Renaissance & Mozarabic scripts", "era": "Medieval-Renaissance", "master": "Various", "notes": "Philip II's vast manuscript collection; Mozarabic codices"},
]

# =====================================================================
# DATA: 5. Typography & Printing Heritage (30 locations)
# =====================================================================
TYPOGRAPHY_PRINTING = [
    {"name": "Gutenberg Museum", "city": "Mainz", "country": "Germany", "lat": 50.000, "lon": 8.272, "tradition": "Movable type printing", "era": "1450s", "master": "Johannes Gutenberg", "notes": "Birthplace of movable type; two original Gutenberg Bibles on display"},
    {"name": "Plantin-Moretus Museum", "city": "Antwerp", "country": "Belgium", "lat": 51.217, "lon": 4.396, "tradition": "Renaissance typography", "era": "16th-17th century", "master": "Christophe Plantin", "notes": "UNESCO World Heritage; oldest surviving printing presses in the world"},
    {"name": "St Bride Library", "city": "London", "country": "UK", "lat": 51.514, "lon": -0.106, "tradition": "Typography & printing", "era": "15th century onward", "master": "Various", "notes": "World's finest collection of printing and typography materials"},
    {"name": "Museo Bodoniano", "city": "Parma", "country": "Italy", "lat": 44.803, "lon": 10.329, "tradition": "Neoclassical typography", "era": "18th century", "master": "Giambattista Bodoni", "notes": "Original Bodoni typefaces, punches, matrices, and presses"},
    {"name": "Imprimerie Nationale", "city": "Paris", "country": "France", "lat": 48.845, "lon": 2.294, "tradition": "French royal typography", "era": "1538 onward", "master": "Garamond & others", "notes": "French national printing office; Garamond's original punches"},
    {"name": "Klingspor Museum", "city": "Offenbach", "country": "Germany", "lat": 50.101, "lon": 8.771, "tradition": "Modern typography", "era": "19th-20th century", "master": "Rudolf Koch & others", "notes": "International collection of modern book art and typography"},
    {"name": "Museum of Printing (Musee de l'Imprimerie)", "city": "Lyon", "country": "France", "lat": 45.763, "lon": 4.834, "tradition": "Early French printing", "era": "15th century onward", "master": "Various", "notes": "Lyon was one of Europe's first major printing centers"},
    {"name": "Jikji Birthplace - Cheongju", "city": "Cheongju", "country": "South Korea", "lat": 36.637, "lon": 127.489, "tradition": "Movable metal type", "era": "1377", "master": "Buddhist monks", "notes": "Jikji: world's oldest surviving movable metal type book, predating Gutenberg"},
    {"name": "William Morris Gallery", "city": "London", "country": "UK", "lat": 51.588, "lon": -0.013, "tradition": "Arts & Crafts typography", "era": "Victorian", "master": "William Morris", "notes": "Kelmscott Press and the Arts and Crafts revival of fine printing"},
    {"name": "Hamilton Wood Type Museum", "city": "Two Rivers, WI", "country": "USA", "lat": 44.154, "lon": -87.569, "tradition": "Wood type manufacture", "era": "19th century", "master": "Various", "notes": "World's largest collection of wood type; 1.5 million pieces"},
    {"name": "Museum of Printing - Haverhill", "city": "Haverhill, MA", "country": "USA", "lat": 42.776, "lon": -71.077, "tradition": "American printing history", "era": "Colonial-Modern", "master": "Various", "notes": "Comprehensive collection of American printing technology"},
    {"name": "Cary Graphic Arts Collection (RIT)", "city": "Rochester, NY", "country": "USA", "lat": 43.084, "lon": -77.680, "tradition": "Graphic arts & typography", "era": "15th century onward", "master": "Various", "notes": "Major research collection of printing and graphic arts at RIT"},
    {"name": "Erik Spiekermann's Galerie p98a", "city": "Berlin", "country": "Germany", "lat": 52.502, "lon": 13.326, "tradition": "Contemporary letterpress", "era": "Modern", "master": "Erik Spiekermann", "notes": "Experimental letterpress studio and gallery"},
    {"name": "Letterform Archive", "city": "San Francisco", "country": "USA", "lat": 37.766, "lon": -122.399, "tradition": "Lettering & typography", "era": "Various", "master": "Various", "notes": "Non-profit library of lettering, typography, and graphic design"},
    {"name": "Enschede Typefoundry (Museum Enschede)", "city": "Haarlem", "country": "Netherlands", "lat": 52.382, "lon": 4.637, "tradition": "Dutch typography", "era": "18th century onward", "master": "Enschede family", "notes": "One of the oldest typefoundries; still operational since 1703"},
    {"name": "Museo della Stampa - Soncino", "city": "Soncino", "country": "Italy", "lat": 45.400, "lon": 9.869, "tradition": "Hebrew & incunabula printing", "era": "15th century", "master": "Soncino family", "notes": "Major early printing of Hebrew texts; first printed Hebrew Bible"},
    {"name": "Subiaco - Santa Scolastica Monastery", "city": "Subiaco", "country": "Italy", "lat": 41.925, "lon": 13.098, "tradition": "First Italian printing", "era": "1465", "master": "Sweynheym & Pannartz", "notes": "Site of the first printing press in Italy"},
    {"name": "Deutsches Buch- und Schriftmuseum", "city": "Leipzig", "country": "Germany", "lat": 51.324, "lon": 12.395, "tradition": "German publishing & type", "era": "15th century onward", "master": "Various", "notes": "World's oldest museum of books and writing; part of German National Library"},
    {"name": "Tipoteca Italiana", "city": "Cornuda", "country": "Italy", "lat": 45.836, "lon": 11.981, "tradition": "Italian typography", "era": "19th-20th century", "master": "Various", "notes": "Living museum of Italian typographic heritage with working presses"},
    {"name": "Printing Museum Houston", "city": "Houston, TX", "country": "USA", "lat": 29.720, "lon": -95.458, "tradition": "American printing", "era": "15th century onward", "master": "Various", "notes": "One of the largest printing history museums in North America"},
    {"name": "Type Museum (former)", "city": "London", "country": "UK", "lat": 51.472, "lon": -0.116, "tradition": "British typography", "era": "Various", "master": "Various", "notes": "Historic type-founding equipment; now preserved as Type Archive"},
    {"name": "National Print Museum", "city": "Dublin", "country": "Ireland", "lat": 53.336, "lon": -6.225, "tradition": "Irish printing history", "era": "18th century onward", "master": "Various", "notes": "History of printing in Ireland from hand-press to digital"},
    {"name": "Fondazione Arnaldo Pomodoro", "city": "Milan", "country": "Italy", "lat": 45.453, "lon": 9.165, "tradition": "Sculptural typography", "era": "Contemporary", "master": "Arnaldo Pomodoro", "notes": "Intersection of sculpture and typographic forms"},
    {"name": "Basel Paper Mill (Basler Papiermuhle)", "city": "Basel", "country": "Switzerland", "lat": 47.556, "lon": 7.594, "tradition": "Paper, print & type", "era": "Medieval onward", "master": "Various", "notes": "Working museum of paper-making, printing, and bookbinding"},
    {"name": "Caxton's Printing Site", "city": "London (Westminster)", "country": "UK", "lat": 51.499, "lon": -0.128, "tradition": "First English printing press", "era": "1476", "master": "William Caxton", "notes": "First book printed in English; Westminster Abbey vicinity"},
    {"name": "Aldine Press Site", "city": "Venice", "country": "Italy", "lat": 45.438, "lon": 12.338, "tradition": "Venetian Renaissance printing", "era": "1494-1515", "master": "Aldus Manutius", "notes": "Inventor of italic type, the pocket book, and the semicolon"},
    {"name": "Stempel Typefoundry Site", "city": "Frankfurt", "country": "Germany", "lat": 50.103, "lon": 8.680, "tradition": "German type founding", "era": "1895-1985", "master": "Various", "notes": "Produced Hermann Zapf's Palatino, Optima, and other iconic typefaces"},
    {"name": "Monotype Works (historic)", "city": "Salfords, Surrey", "country": "UK", "lat": 51.232, "lon": -0.165, "tradition": "Monotype system", "era": "1897 onward", "master": "Monotype Corporation", "notes": "Produced Times New Roman, Gill Sans, and many classic typefaces"},
    {"name": "Bauer Typefoundry Site", "city": "Frankfurt", "country": "Germany", "lat": 50.109, "lon": 8.682, "tradition": "Art Nouveau & Modern type", "era": "1837-1972", "master": "Various", "notes": "Created Futura (Paul Renner) and other iconic modern typefaces"},
    {"name": "Doves Press / Bookcraft Site", "city": "Hammersmith, London", "country": "UK", "lat": 51.489, "lon": -0.233, "tradition": "Private press movement", "era": "1900-1916", "master": "T.J. Cobden-Sanderson", "notes": "Famous Doves Type thrown into the Thames; recovered 2015"},
]

# =====================================================================
# DATA: 6. Korean Hangul Heritage Sites (25 locations)
# =====================================================================
KOREAN_HANGUL = [
    {"name": "National Hangeul Museum", "city": "Seoul", "country": "South Korea", "lat": 37.522, "lon": 126.980, "tradition": "Hangeul history", "era": "1443 onward", "master": "King Sejong legacy", "notes": "Dedicated museum for the Korean alphabet; interactive exhibits"},
    {"name": "Sejong the Great Statue & Square", "city": "Seoul", "country": "South Korea", "lat": 37.572, "lon": 126.977, "tradition": "Hangeul creation", "era": "1443 (Joseon)", "master": "King Sejong", "notes": "Monument to the creator of Hangeul; underground exhibition hall"},
    {"name": "Gyeongbokgung Palace - Jiphyeonjeon Hall", "city": "Seoul", "country": "South Korea", "lat": 37.580, "lon": 126.977, "tradition": "Hangeul invention", "era": "1443", "master": "King Sejong & scholars", "notes": "Hall of Worthies where Hangeul was developed"},
    {"name": "National Museum of Korea", "city": "Seoul", "country": "South Korea", "lat": 37.524, "lon": 126.981, "tradition": "Korean scripts & artifacts", "era": "Prehistoric-Modern", "master": "Various", "notes": "Major collection of Hangeul woodblock prints and calligraphy"},
    {"name": "Haeinsa Temple - Tripitaka Koreana", "city": "Hapcheon", "country": "South Korea", "lat": 35.802, "lon": 128.100, "tradition": "Woodblock carving", "era": "13th century", "master": "Goryeo artisans", "notes": "81,258 woodblocks of Buddhist scriptures; UNESCO World Heritage"},
    {"name": "Changdeokgung Palace Secret Garden", "city": "Seoul", "country": "South Korea", "lat": 37.579, "lon": 126.991, "tradition": "Royal calligraphy", "era": "Joseon Dynasty", "master": "Joseon kings", "notes": "Royal calligraphic inscriptions throughout the palace"},
    {"name": "Jongmyo Shrine", "city": "Seoul", "country": "South Korea", "lat": 37.574, "lon": 126.994, "tradition": "Ritual calligraphy", "era": "Joseon Dynasty", "master": "Court calligraphers", "notes": "Royal ancestral tablets with formal Hangeul and Hanja inscriptions"},
    {"name": "Korean Stone Art Museum", "city": "Seoul", "country": "South Korea", "lat": 37.525, "lon": 127.008, "tradition": "Stone inscriptions", "era": "Three Kingdoms-Joseon", "master": "Various", "notes": "Stone steles and inscriptions from Korean history"},
    {"name": "Gwangjuyo Kiln Sites", "city": "Gwangju, Gyeonggi", "country": "South Korea", "lat": 37.413, "lon": 127.235, "tradition": "Ceramic calligraphy", "era": "Joseon Dynasty", "master": "Royal potters", "notes": "White porcelain with Hangeul and Hanja calligraphic decoration"},
    {"name": "Andong Hahoe Folk Village", "city": "Andong", "country": "South Korea", "lat": 36.537, "lon": 128.519, "tradition": "Confucian calligraphy", "era": "Joseon Dynasty", "master": "Ryu clan scholars", "notes": "Living heritage village with Confucian calligraphy culture"},
    {"name": "Yeongju Buseoksa Temple", "city": "Yeongju", "country": "South Korea", "lat": 36.994, "lon": 128.680, "tradition": "Buddhist calligraphy", "era": "Silla Dynasty (676 AD)", "master": "Uisang", "notes": "One of Korea's oldest temples; ancient inscriptions"},
    {"name": "Bulguksa Temple", "city": "Gyeongju", "country": "South Korea", "lat": 35.790, "lon": 129.332, "tradition": "Silla Buddhist calligraphy", "era": "8th century", "master": "Silla artisans", "notes": "UNESCO site with stone inscriptions from Unified Silla period"},
    {"name": "Seokguram Grotto", "city": "Gyeongju", "country": "South Korea", "lat": 35.796, "lon": 129.349, "tradition": "Buddhist inscriptions", "era": "8th century", "master": "Silla artisans", "notes": "Granite grotto with dedicatory inscriptions"},
    {"name": "Cheongju Early Printing Museum", "city": "Cheongju", "country": "South Korea", "lat": 36.635, "lon": 127.491, "tradition": "Movable metal type", "era": "1377", "master": "Buddhist monks", "notes": "Site where Jikji was printed; UNESCO Memory of the World"},
    {"name": "Confucian Academy (Seonggyungwan)", "city": "Seoul", "country": "South Korea", "lat": 37.588, "lon": 126.999, "tradition": "Confucian scholarly calligraphy", "era": "Joseon Dynasty", "master": "Joseon scholars", "notes": "Highest Confucian academy; center of Hanja calligraphy training"},
    {"name": "Dosan Seowon Confucian Academy", "city": "Andong", "country": "South Korea", "lat": 36.724, "lon": 128.844, "tradition": "Neo-Confucian calligraphy", "era": "Joseon (1574)", "master": "Yi Hwang (Toegye)", "notes": "Academy of Korea's greatest Confucian calligrapher-philosopher"},
    {"name": "Ojukheon House (Yulgok Birthplace)", "city": "Gangneung", "country": "South Korea", "lat": 37.778, "lon": 128.879, "tradition": "Joseon scholarly calligraphy", "era": "Joseon Dynasty", "master": "Shin Saimdang & Yi I", "notes": "Home of master calligrapher Shin Saimdang, featured on 50000 won note"},
    {"name": "Gwangju National Museum", "city": "Gwangju", "country": "South Korea", "lat": 35.167, "lon": 126.885, "tradition": "Korean calligraphy arts", "era": "Various", "master": "Various", "notes": "Regional calligraphy and Hangeul typography exhibition"},
    {"name": "Jinju National Museum", "city": "Jinju", "country": "South Korea", "lat": 35.187, "lon": 128.072, "tradition": "Imjin War documents", "era": "Joseon Dynasty", "master": "Various", "notes": "Calligraphic war documents and edicts from the Imjin War era"},
    {"name": "Damyang Soswaewon Garden", "city": "Damyang", "country": "South Korea", "lat": 35.309, "lon": 126.966, "tradition": "Literati calligraphy", "era": "Joseon (1530s)", "master": "Yang San-bo", "notes": "Garden of poetic calligraphy inscriptions and literati culture"},
    {"name": "Buyeo National Museum", "city": "Buyeo", "country": "South Korea", "lat": 36.278, "lon": 126.910, "tradition": "Baekje calligraphy", "era": "Baekje Kingdom", "master": "Baekje artisans", "notes": "Inscribed artifacts from the ancient Baekje Kingdom"},
    {"name": "Gongju National Museum", "city": "Gongju", "country": "South Korea", "lat": 36.461, "lon": 127.119, "tradition": "Baekje inscriptions", "era": "Baekje Kingdom", "master": "Various", "notes": "King Muryeong tomb inscriptions and Baekje era calligraphy"},
    {"name": "Jeju Stone Culture Park", "city": "Jeju", "country": "South Korea", "lat": 33.433, "lon": 126.818, "tradition": "Jeju stone inscriptions", "era": "Various", "master": "Jeju artisans", "notes": "Volcanic stone inscriptions unique to Jeju Island culture"},
    {"name": "Korean Calligraphy Museum", "city": "Seoul (Gangnam)", "country": "South Korea", "lat": 37.510, "lon": 127.024, "tradition": "Korean calligraphy", "era": "Modern", "master": "Various", "notes": "Contemporary Korean calligraphy exhibitions and workshops"},
    {"name": "Incheon Open Port Museum", "city": "Incheon", "country": "South Korea", "lat": 37.473, "lon": 126.623, "tradition": "Modern Hangeul typography", "era": "19th-20th century", "master": "Various", "notes": "Early modern Korean printing and Hangeul typography development"},
]

# =====================================================================
# DATA: 7. Tibetan & Sanskrit Writing (25 locations)
# =====================================================================
TIBETAN_SANSKRIT = [
    {"name": "Potala Palace", "city": "Lhasa", "country": "China (Tibet)", "lat": 29.658, "lon": 91.117, "tradition": "Uchen & Umey Tibetan scripts", "era": "7th century onward", "master": "Thonmi Sambhota", "notes": "Massive collection of Tibetan Buddhist manuscripts and gold lettering"},
    {"name": "Jokhang Temple", "city": "Lhasa", "country": "China (Tibet)", "lat": 29.653, "lon": 91.132, "tradition": "Tibetan Buddhist calligraphy", "era": "7th century", "master": "Various lamas", "notes": "Holiest Tibetan temple; ancient inscriptions and prayer texts"},
    {"name": "Drepung Monastery", "city": "Lhasa", "country": "China (Tibet)", "lat": 29.665, "lon": 91.074, "tradition": "Sutra calligraphy", "era": "1416 onward", "master": "Gelug monks", "notes": "Largest Tibetan monastery; vast manuscript collection"},
    {"name": "Sera Monastery", "city": "Lhasa", "country": "China (Tibet)", "lat": 29.685, "lon": 91.133, "tradition": "Scholastic calligraphy", "era": "1419 onward", "master": "Gelug monks", "notes": "Major center of Tibetan Buddhist manuscript production"},
    {"name": "Tashilhunpo Monastery", "city": "Shigatse", "country": "China (Tibet)", "lat": 29.274, "lon": 88.882, "tradition": "Panchen Lama calligraphy", "era": "1447 onward", "master": "Panchen Lamas", "notes": "Gold-lettered Kangyur and Tengyur manuscript collections"},
    {"name": "Labrang Monastery", "city": "Xiahe", "country": "China (Gansu)", "lat": 35.191, "lon": 102.511, "tradition": "Amdo Tibetan calligraphy", "era": "1709 onward", "master": "Amdo scholars", "notes": "One of the six great Gelug monasteries; large printing house"},
    {"name": "Dharamsala - Library of Tibetan Works & Archives", "city": "Dharamsala", "country": "India", "lat": 32.222, "lon": 76.322, "tradition": "Tibetan calligraphy preservation", "era": "1970 onward", "master": "Exile scholars", "notes": "Preserves Tibetan calligraphic traditions in exile"},
    {"name": "Norbulingka Institute", "city": "Dharamsala", "country": "India", "lat": 32.200, "lon": 76.295, "tradition": "Tibetan arts & calligraphy", "era": "Modern", "master": "Various", "notes": "Center for preserving Tibetan calligraphy, thangka, and woodblock printing"},
    {"name": "Nalanda University Ruins", "city": "Rajgir", "country": "India", "lat": 25.136, "lon": 85.443, "tradition": "Sanskrit manuscripts", "era": "5th-12th century", "master": "Buddhist scholars", "notes": "Ancient world's greatest center of Sanskrit manuscript production"},
    {"name": "Sarnath - Dhamek Stupa Inscriptions", "city": "Sarnath", "country": "India", "lat": 25.381, "lon": 83.023, "tradition": "Gupta-era Brahmi script", "era": "5th century", "master": "Gupta artisans", "notes": "Ashoka pillar and Gupta-era Sanskrit inscriptions"},
    {"name": "Bhaktapur - National Art Museum", "city": "Bhaktapur", "country": "Nepal", "lat": 27.672, "lon": 85.428, "tradition": "Newari & Sanskrit manuscripts", "era": "Medieval", "master": "Newar scribes", "notes": "Palm leaf and paper manuscripts in Newari, Sanskrit, and Tibetan"},
    {"name": "Swayambhunath Stupa", "city": "Kathmandu", "country": "Nepal", "lat": 27.715, "lon": 85.291, "tradition": "Sanskrit & Tibetan inscriptions", "era": "5th century onward", "master": "Various", "notes": "Ancient inscriptions in multiple South Asian scripts"},
    {"name": "Hemis Monastery", "city": "Hemis, Ladakh", "country": "India", "lat": 33.915, "lon": 77.697, "tradition": "Ladakhi Tibetan calligraphy", "era": "1672 onward", "master": "Drukpa monks", "notes": "Rich manuscript collection; annual masked festival with calligraphy"},
    {"name": "Thiksey Monastery", "city": "Thiksey, Ladakh", "country": "India", "lat": 34.053, "lon": 77.583, "tradition": "Tibetan calligraphy", "era": "15th century", "master": "Gelug monks", "notes": "12-story monastery with extensive prayer text calligraphy"},
    {"name": "Boudhanath Stupa Area", "city": "Kathmandu", "country": "Nepal", "lat": 27.722, "lon": 85.362, "tradition": "Tibetan manuscript tradition", "era": "Various", "master": "Tibetan exile monks", "notes": "Surrounding monasteries preserve Tibetan calligraphy traditions"},
    {"name": "Sanchi Great Stupa", "city": "Sanchi", "country": "India", "lat": 23.479, "lon": 77.739, "tradition": "Brahmi & Sanskrit inscriptions", "era": "3rd century BC - 12th century", "master": "Buddhist artisans", "notes": "Ashoka-era Brahmi inscriptions on one of India's oldest stupas"},
    {"name": "Ajanta Caves", "city": "Aurangabad", "country": "India", "lat": 20.552, "lon": 75.700, "tradition": "Sanskrit cave inscriptions", "era": "2nd century BC - 6th century", "master": "Buddhist monks", "notes": "Dedicatory inscriptions in ancient Brahmi and later scripts"},
    {"name": "Ellora Caves", "city": "Aurangabad", "country": "India", "lat": 20.026, "lon": 75.179, "tradition": "Multi-script inscriptions", "era": "6th-11th century", "master": "Hindu, Buddhist, Jain artisans", "notes": "Sanskrit, Prakrit, and Kannada inscriptions across 34 caves"},
    {"name": "Bodh Gaya - Mahabodhi Temple", "city": "Bodh Gaya", "country": "India", "lat": 24.696, "lon": 84.991, "tradition": "Buddhist inscriptions", "era": "3rd century BC onward", "master": "Various", "notes": "Site of Buddha's enlightenment; ancient Brahmi & Sanskrit inscriptions"},
    {"name": "National Museum New Delhi", "city": "New Delhi", "country": "India", "lat": 28.612, "lon": 77.219, "tradition": "Sanskrit & Indian scripts", "era": "Various", "master": "Various", "notes": "Major collection of manuscripts in Sanskrit, Pali, Prakrit, and more"},
    {"name": "Alchi Monastery", "city": "Alchi, Ladakh", "country": "India", "lat": 34.227, "lon": 77.168, "tradition": "Kashmiri-Tibetan calligraphy", "era": "11th century", "master": "Rinchen Zangpo school", "notes": "Oldest surviving murals in Ladakh with unique calligraphic inscriptions"},
    {"name": "Rumtek Monastery", "city": "Gangtok", "country": "India", "lat": 27.290, "lon": 88.649, "tradition": "Kagyu Tibetan calligraphy", "era": "1966 (rebuilt)", "master": "Karmapa lineage", "notes": "Seat of the Karmapa; manuscript and printing traditions"},
    {"name": "Tawang Monastery", "city": "Tawang", "country": "India", "lat": 27.586, "lon": 91.865, "tradition": "Monpa-Tibetan calligraphy", "era": "17th century", "master": "Gelug monks", "notes": "Largest monastery in India; extensive manuscript library"},
    {"name": "Oriental Research Institute Mysore", "city": "Mysore", "country": "India", "lat": 12.309, "lon": 76.655, "tradition": "Sanskrit manuscript preservation", "era": "Various", "master": "Various", "notes": "Over 70,000 Sanskrit palm leaf and paper manuscripts"},
    {"name": "Sakya Monastery", "city": "Sakya", "country": "China (Tibet)", "lat": 28.898, "lon": 88.013, "tradition": "Sakya calligraphy", "era": "1073 onward", "master": "Sakya scholars", "notes": "Wall of 84,000 scrolls; one of the largest manuscript repositories"},
]

# =====================================================================
# DATA: 8. Celtic & Insular Script Sites (25 locations)
# =====================================================================
CELTIC_INSULAR = [
    {"name": "Clonmacnoise Monastic Site", "city": "Clonmacnoise", "country": "Ireland", "lat": 53.326, "lon": -7.986, "tradition": "Irish majuscule", "era": "6th-12th century", "master": "Columban monks", "notes": "Major Irish scriptorium; high crosses with Gaelic inscriptions"},
    {"name": "Skellig Michael", "city": "Skellig Islands", "country": "Ireland", "lat": 51.770, "lon": -10.539, "tradition": "Early insular script", "era": "6th-8th century", "master": "Island hermit monks", "notes": "Remote island monastery; earliest insular manuscript production"},
    {"name": "Glendalough Monastic City", "city": "Glendalough", "country": "Ireland", "lat": 53.011, "lon": -6.329, "tradition": "Irish uncial script", "era": "6th century onward", "master": "St. Kevin's monks", "notes": "Major scriptorium in the Wicklow Mountains valley"},
    {"name": "Kells - St. Columba's Church", "city": "Kells", "country": "Ireland", "lat": 53.726, "lon": -6.880, "tradition": "Insular majuscule", "era": "9th century", "master": "Iona/Kells monks", "notes": "Historic site where the Book of Kells was housed for centuries"},
    {"name": "Durrow Abbey Site", "city": "Durrow", "country": "Ireland", "lat": 53.380, "lon": -7.549, "tradition": "Insular minuscule", "era": "7th century", "master": "Columban monks", "notes": "Origin of the Book of Durrow, earliest fully decorated insular gospel book"},
    {"name": "Armagh - St. Patrick's Cathedral", "city": "Armagh", "country": "Northern Ireland", "lat": 54.350, "lon": -6.654, "tradition": "Irish ecclesiastical script", "era": "5th century onward", "master": "St. Patrick tradition", "notes": "Ecclesiastical capital of Ireland; Book of Armagh produced here"},
    {"name": "Lindisfarne (Holy Island)", "city": "Lindisfarne", "country": "England", "lat": 55.669, "lon": -1.800, "tradition": "Insular majuscule", "era": "7th century", "master": "Eadfrith", "notes": "Where the Lindisfarne Gospels were created c. 700 AD"},
    {"name": "Jarrow - Bede's World", "city": "Jarrow", "country": "England", "lat": 54.980, "lon": -1.471, "tradition": "Anglo-Saxon script", "era": "7th-8th century", "master": "Venerable Bede", "notes": "Bede's monastery; Codex Amiatinus produced here, largest early Bible"},
    {"name": "Monkwearmouth-Jarrow", "city": "Sunderland", "country": "England", "lat": 54.914, "lon": -1.383, "tradition": "Northumbrian insular script", "era": "7th century", "master": "Benedict Biscop", "notes": "Twin monastery that trained Bede and produced major manuscripts"},
    {"name": "Canterbury Cathedral Library", "city": "Canterbury", "country": "England", "lat": 51.280, "lon": 1.083, "tradition": "Anglo-Saxon & Carolingian scripts", "era": "6th-11th century", "master": "Augustine's mission monks", "notes": "Augustine of Canterbury brought Roman script tradition to England"},
    {"name": "Aberlemno Pictish Stones", "city": "Aberlemno", "country": "Scotland", "lat": 56.703, "lon": -2.804, "tradition": "Pictish ogham & symbols", "era": "7th-9th century", "master": "Pictish carvers", "notes": "Finest surviving Pictish symbol stones with ogham inscriptions"},
    {"name": "Meigle Sculptured Stone Museum", "city": "Meigle", "country": "Scotland", "lat": 56.600, "lon": -3.169, "tradition": "Pictish inscriptions", "era": "8th-10th century", "master": "Pictish artisans", "notes": "Collection of 26 Pictish cross-slabs with inscribed script"},
    {"name": "Whithorn Priory", "city": "Whithorn", "country": "Scotland", "lat": 54.734, "lon": -4.413, "tradition": "Early Christian Latin scripts", "era": "5th century", "master": "St. Ninian's mission", "notes": "Earliest Christian site in Scotland; Latinus Stone (c. 450 AD)"},
    {"name": "St. Davids Cathedral", "city": "St. Davids", "country": "Wales", "lat": 51.882, "lon": -5.269, "tradition": "Welsh insular script", "era": "6th century onward", "master": "St. David's monks", "notes": "Center of Welsh monastic calligraphy and manuscript production"},
    {"name": "Penmon Priory", "city": "Anglesey", "country": "Wales", "lat": 53.307, "lon": -4.051, "tradition": "Celtic crosses & inscriptions", "era": "6th-12th century", "master": "Welsh monks", "notes": "Fine Celtic cross with interlace patterns and inscriptions"},
    {"name": "Llantwit Major - Illtud's Monastery", "city": "Llantwit Major", "country": "Wales", "lat": 51.408, "lon": -3.484, "tradition": "Welsh Latin inscriptions", "era": "5th-7th century", "master": "St. Illtud's monks", "notes": "Major early Welsh scriptorium; Pillar of Samson cross"},
    {"name": "Breton Calvaries - Guimiliau", "city": "Guimiliau", "country": "France (Brittany)", "lat": 48.489, "lon": -3.998, "tradition": "Breton inscriptions", "era": "16th-17th century", "master": "Breton artisans", "notes": "Carved granite calvaries with Breton and Latin inscriptions"},
    {"name": "Carnac Stones Area", "city": "Carnac", "country": "France (Brittany)", "lat": 47.584, "lon": -3.077, "tradition": "Pre-Celtic megalithic marks", "era": "Neolithic (4500-3300 BC)", "master": "Unknown", "notes": "Possible proto-writing marks on megaliths; debated interpretation"},
    {"name": "Newgrange Passage Tomb", "city": "Newgrange", "country": "Ireland", "lat": 53.695, "lon": -6.475, "tradition": "Megalithic art / proto-writing", "era": "c. 3200 BC", "master": "Neolithic builders", "notes": "Spiral and geometric carvings predating Celts; proto-symbolic marks"},
    {"name": "Ogham Stone Collection - Kilmalkedar", "city": "Dingle Peninsula", "country": "Ireland", "lat": 52.181, "lon": -10.203, "tradition": "Ogham script", "era": "5th-7th century", "master": "Early Irish scribes", "notes": "Ogham stones with early Irish alphabetic inscriptions"},
    {"name": "National Museum of Scotland", "city": "Edinburgh", "country": "Scotland", "lat": 55.947, "lon": -3.190, "tradition": "Pictish & Celtic scripts", "era": "Various", "master": "Various", "notes": "Major collection of Pictish symbol stones and early Christian inscriptions"},
    {"name": "Bangor Abbey Site", "city": "Bangor", "country": "Northern Ireland", "lat": 54.660, "lon": -5.670, "tradition": "Insular antiphonary", "era": "7th century", "master": "Bangor monks", "notes": "Origin of the Antiphonary of Bangor, earliest Irish liturgical manuscript"},
    {"name": "Bobbio Abbey", "city": "Bobbio", "country": "Italy", "lat": 44.770, "lon": 9.387, "tradition": "Irish insular script on continent", "era": "7th century", "master": "St. Columbanus", "notes": "Irish monks brought insular script to Italy; famous palimpsests"},
    {"name": "Luxeuil Abbey", "city": "Luxeuil-les-Bains", "country": "France", "lat": 47.818, "lon": 6.381, "tradition": "Luxeuil minuscule", "era": "7th-8th century", "master": "St. Columbanus", "notes": "Irish-founded monastery; developed distinctive Luxeuil minuscule script"},
    {"name": "Echternach Abbey", "city": "Echternach", "country": "Luxembourg", "lat": 49.815, "lon": 6.421, "tradition": "Insular-Continental script", "era": "698 AD onward", "master": "St. Willibrord (Irish-trained)", "notes": "Echternach Gospels produced here; fusion of insular and Continental styles"},
]

# =====================================================================
# DATA: 9. Modern Lettering & Graffiti Art (25 locations)
# =====================================================================
MODERN_LETTERING = [
    {"name": "Wynwood Walls", "city": "Miami", "country": "USA", "lat": 25.801, "lon": -80.199, "tradition": "Graffiti lettering / muralism", "era": "2009 onward", "master": "Various international artists", "notes": "World's premier outdoor graffiti and lettering art district"},
    {"name": "5Pointz (Historic Site)", "city": "New York", "country": "USA", "lat": 40.742, "lon": -73.924, "tradition": "Graffiti wildstyle lettering", "era": "1993-2013", "master": "Meres One & others", "notes": "Legendary 'Graffiti Mecca'; demolished 2014 but legacy endures"},
    {"name": "Leake Street Arches (Banksy Tunnel)", "city": "London", "country": "UK", "lat": 51.502, "lon": -0.114, "tradition": "Graffiti & street lettering", "era": "2008 onward", "master": "Banksy & rotating artists", "notes": "Legal graffiti tunnel beneath Waterloo Station"},
    {"name": "Hosier Lane", "city": "Melbourne", "country": "Australia", "lat": -37.816, "lon": 144.969, "tradition": "Street art lettering", "era": "Modern", "master": "Various", "notes": "Melbourne's most famous street art laneway; constant rotation"},
    {"name": "East Side Gallery (Berlin Wall)", "city": "Berlin", "country": "Germany", "lat": 52.505, "lon": 13.440, "tradition": "Political lettering & murals", "era": "1990 onward", "master": "International artists", "notes": "1.3km of Berlin Wall with painted calligraphic and political works"},
    {"name": "Shoreditch / Brick Lane Street Art", "city": "London", "country": "UK", "lat": 51.522, "lon": -0.072, "tradition": "Graffiti lettering", "era": "1990s onward", "master": "Ben Eine & others", "notes": "Ben Eine's alphabetic shutters and diverse lettering art"},
    {"name": "Bushwick Collective", "city": "New York", "country": "USA", "lat": 40.698, "lon": -73.923, "tradition": "Mural lettering", "era": "2011 onward", "master": "Various curated artists", "notes": "Curated outdoor gallery of large-scale lettering and murals"},
    {"name": "Vila Madalena - Beco do Batman", "city": "Sao Paulo", "country": "Brazil", "lat": -23.554, "lon": -46.693, "tradition": "Brazilian graffiti lettering", "era": "1980s onward", "master": "Os Gemeos & others", "notes": "Vibrant alley showcasing Brazilian graffiti lettering traditions"},
    {"name": "Harajuku - Design Festa Gallery", "city": "Tokyo", "country": "Japan", "lat": 35.672, "lon": 139.705, "tradition": "Japanese typography art", "era": "Modern", "master": "Various", "notes": "Fusion of Japanese calligraphy and modern typographic art"},
    {"name": "Belleville Street Art District", "city": "Paris", "country": "France", "lat": 48.870, "lon": 2.385, "tradition": "European lettering art", "era": "Modern", "master": "Various", "notes": "Major Parisian street art and typographic mural area"},
    {"name": "Centro de Arte Urbano - Fabrica de Armas", "city": "Toledo", "country": "Spain", "lat": 39.858, "lon": -4.024, "tradition": "Spanish urban calligraphy", "era": "Modern", "master": "Various", "notes": "Converted weapons factory with urban calligraphy installations"},
    {"name": "Ghent Street Art Trail", "city": "Ghent", "country": "Belgium", "lat": 51.053, "lon": 3.720, "tradition": "Belgian graffiti lettering", "era": "Modern", "master": "ROA & others", "notes": "City-supported street art and lettering trail through historic city"},
    {"name": "Detroit Eastern Market Murals", "city": "Detroit", "country": "USA", "lat": 42.349, "lon": -83.040, "tradition": "American mural lettering", "era": "Modern", "master": "Various", "notes": "Revitalized market district with large typographic murals"},
    {"name": "Valparaiso Open-Air Gallery", "city": "Valparaiso", "country": "Chile", "lat": -33.047, "lon": -71.612, "tradition": "South American lettering art", "era": "Modern", "master": "Various", "notes": "Hillside city covered in calligraphic and typographic murals"},
    {"name": "Lodhi Art District", "city": "New Delhi", "country": "India", "lat": 28.590, "lon": 77.225, "tradition": "Indian urban lettering", "era": "2016 onward", "master": "Various international artists", "notes": "India's first public art district with calligraphic murals"},
    {"name": "Kakaako Ward Village Murals", "city": "Honolulu", "country": "USA", "lat": 21.296, "lon": -157.861, "tradition": "Pacific Island lettering", "era": "Modern (POW! WOW!)", "master": "Various", "notes": "Annual POW! WOW! mural festival with typographic works"},
    {"name": "Reykjavik Street Art Walk", "city": "Reykjavik", "country": "Iceland", "lat": 64.147, "lon": -21.943, "tradition": "Nordic lettering art", "era": "Modern", "master": "Various", "notes": "Icelandic rune-inspired contemporary lettering on buildings"},
    {"name": "Taipei Ximending Graffiti Area", "city": "Taipei", "country": "Taiwan", "lat": 25.042, "lon": 121.507, "tradition": "East Asian graffiti", "era": "Modern", "master": "Various", "notes": "Fusion of Chinese calligraphy and Western graffiti styles"},
    {"name": "Bogota Graffiti District", "city": "Bogota", "country": "Colombia", "lat": 4.597, "lon": -74.076, "tradition": "Colombian lettering art", "era": "2011 onward (legalized)", "master": "DJ Lu & Toxicomano", "notes": "Legalized graffiti district with bold typographic murals"},
    {"name": "Thessaloniki Street Art", "city": "Thessaloniki", "country": "Greece", "lat": 40.626, "lon": 22.949, "tradition": "Greek lettering art", "era": "Modern", "master": "Various", "notes": "Ancient Greek letter forms reinterpreted in modern street art"},
    {"name": "Stavanger Street Art - Nuart Festival", "city": "Stavanger", "country": "Norway", "lat": 58.969, "lon": 5.733, "tradition": "Nordic graffiti lettering", "era": "2001 onward", "master": "Various Nuart artists", "notes": "Annual Nuart festival brings world-class lettering artists"},
    {"name": "George Town Street Art", "city": "George Town, Penang", "country": "Malaysia", "lat": 5.414, "lon": 100.340, "tradition": "Multicultural lettering", "era": "2012 onward", "master": "Ernest Zacharevic & others", "notes": "UNESCO heritage zone with Chinese, Malay, and Tamil lettering art"},
    {"name": "Cape Town Woodstock Murals", "city": "Cape Town", "country": "South Africa", "lat": -33.928, "lon": 18.446, "tradition": "African lettering art", "era": "Modern", "master": "Faith47 & others", "notes": "Vibrant neighborhood with African-inspired calligraphic murals"},
    {"name": "Buenos Aires Colegiales Art Walk", "city": "Buenos Aires", "country": "Argentina", "lat": -34.574, "lon": -58.446, "tradition": "Argentine lettering", "era": "Modern", "master": "Various", "notes": "Fileteado porteño traditional lettering and modern graffiti fusion"},
    {"name": "Tashkeel Art Center", "city": "Dubai", "country": "UAE", "lat": 25.185, "lon": 55.254, "tradition": "Arabic graffiti (calligraffiti)", "era": "Modern", "master": "eL Seed & others", "notes": "Center promoting Arabic calligraffiti blending tradition and street art"},
]

# =====================================================================
# DATA: 10. Calligraphy Museums & Schools (25 locations)
# =====================================================================
CALLIGRAPHY_MUSEUMS = [
    {"name": "National Art Museum of China", "city": "Beijing", "country": "China", "lat": 39.928, "lon": 116.406, "tradition": "Chinese calligraphy", "era": "Modern exhibitions", "master": "National collection", "notes": "Regular major calligraphy exhibitions from national holdings"},
    {"name": "Taipei Calligraphy Research Center", "city": "Taipei", "country": "Taiwan", "lat": 25.033, "lon": 121.521, "tradition": "Chinese calligraphy education", "era": "Modern", "master": "Various", "notes": "Leading center for Chinese calligraphy research and classes"},
    {"name": "IRCICA (Islamic Culture Center)", "city": "Istanbul", "country": "Turkey", "lat": 41.005, "lon": 28.974, "tradition": "Islamic calligraphy", "era": "Modern", "master": "Various", "notes": "International center for Islamic arts; calligraphy competitions"},
    {"name": "House of Calligraphy (Dar al-Khatt)", "city": "Sharjah", "country": "UAE", "lat": 25.358, "lon": 55.388, "tradition": "Arabic calligraphy training", "era": "Modern", "master": "Various", "notes": "Dedicated facility for Arabic calligraphy education and exhibition"},
    {"name": "Musee des Lettres et Manuscrits (historic)", "city": "Paris", "country": "France", "lat": 48.855, "lon": 2.324, "tradition": "European lettering heritage", "era": "Various", "master": "Various", "notes": "Historical manuscripts and calligraphic letters from famous figures"},
    {"name": "Reed and Quill Calligraphy Academy", "city": "London", "country": "UK", "lat": 51.514, "lon": -0.078, "tradition": "Western calligraphy education", "era": "Modern", "master": "Various", "notes": "Premier school for Western calligraphy and lettering in Britain"},
    {"name": "Society of Scribes & Illuminators", "city": "London", "country": "UK", "lat": 51.512, "lon": -0.090, "tradition": "Western calligraphy", "era": "1921 onward", "master": "Edward Johnston legacy", "notes": "Founded in the tradition of Edward Johnston; promotes calligraphic arts"},
    {"name": "International Exhibition of Calligraphy Museum", "city": "Sokolniki, Moscow", "country": "Russia", "lat": 55.789, "lon": 37.672, "tradition": "World calligraphy", "era": "Modern", "master": "Various", "notes": "Unique museum dedicated to calligraphy from all world traditions"},
    {"name": "Musashino Art University", "city": "Tokyo", "country": "Japan", "lat": 35.738, "lon": 139.570, "tradition": "Japanese calligraphy & design", "era": "Modern", "master": "Faculty", "notes": "Leading university for Japanese calligraphy and typography education"},
    {"name": "Sotheby's Calligraphy Department", "city": "London", "country": "UK", "lat": 51.510, "lon": -0.140, "tradition": "Calligraphy auctions", "era": "Modern", "master": "Various", "notes": "Major auction house for historical calligraphy and manuscripts"},
    {"name": "Christie's Islamic Art Department", "city": "London", "country": "UK", "lat": 51.509, "lon": -0.139, "tradition": "Islamic calligraphy sales", "era": "Modern", "master": "Various", "notes": "Regular auctions of Islamic calligraphic masterworks"},
    {"name": "Ditchling Museum of Art + Craft", "city": "Ditchling", "country": "UK", "lat": 50.919, "lon": -0.110, "tradition": "Edward Johnston & Gill", "era": "20th century", "master": "Edward Johnston, Eric Gill", "notes": "Home of Johnston (London Underground typeface) and Gill (Gill Sans)"},
    {"name": "Aoyama Book Center - Calligraphy Section", "city": "Tokyo", "country": "Japan", "lat": 35.665, "lon": 139.712, "tradition": "Japanese calligraphy books", "era": "Modern", "master": "Various", "notes": "Premier bookshop for calligraphy instruction manuals and art books"},
    {"name": "Type Directors Club", "city": "New York", "country": "USA", "lat": 40.721, "lon": -74.002, "tradition": "Typography excellence", "era": "1946 onward", "master": "Various", "notes": "Promotes worldwide typographic excellence; annual awards"},
    {"name": "Herb Lubalin Study Center (Cooper Union)", "city": "New York", "country": "USA", "lat": 40.729, "lon": -73.991, "tradition": "American graphic lettering", "era": "Modern", "master": "Herb Lubalin archive", "notes": "Archive of Lubalin's revolutionary typographic and lettering work"},
    {"name": "Klingspor Museum", "city": "Offenbach", "country": "Germany", "lat": 50.101, "lon": 8.771, "tradition": "International calligraphy", "era": "Modern", "master": "Rudolf Koch & others", "notes": "Museum for international book art and calligraphy"},
    {"name": "Khatt Foundation", "city": "Amsterdam", "country": "Netherlands", "lat": 52.370, "lon": 4.892, "tradition": "Arabic typography & design", "era": "Modern", "master": "Huda Smitshuijzen AbiFares", "notes": "Promotes Arabic typography and cross-cultural typographic design"},
    {"name": "Penman's Paradise Museum", "city": "Zanerian College, Columbus OH", "country": "USA", "lat": 39.961, "lon": -83.000, "tradition": "American penmanship", "era": "19th-20th century", "master": "Zaner & Bloser", "notes": "Historic collection of American penmanship and Spencerian script"},
    {"name": "IAMPETH (Penmen's Association)", "city": "Various (USA HQ)", "country": "USA", "lat": 41.881, "lon": -87.623, "tradition": "Master penmanship", "era": "1949 onward", "master": "Various master penmen", "notes": "Association of Master Penmen; preserves Copperplate and Spencerian arts"},
    {"name": "National Calligraphy Museum of Azerbaijan", "city": "Baku", "country": "Azerbaijan", "lat": 40.366, "lon": 49.837, "tradition": "Azerbaijani & Islamic calligraphy", "era": "Modern", "master": "Various", "notes": "Collection of Islamic calligraphy from Azerbaijan and wider Muslim world"},
    {"name": "China Calligraphy Museum (planned)", "city": "Beijing", "country": "China", "lat": 39.930, "lon": 116.410, "tradition": "Chinese calligraphy", "era": "Modern", "master": "China Calligraphers Association", "notes": "National center for Chinese calligraphy art and education"},
    {"name": "Aga Khan Museum", "city": "Toronto", "country": "Canada", "lat": 43.729, "lon": -79.330, "tradition": "Islamic calligraphy", "era": "Various", "master": "Various", "notes": "Major Islamic art museum with significant calligraphy collection"},
    {"name": "Benaki Museum of Islamic Art", "city": "Athens", "country": "Greece", "lat": 37.977, "lon": 23.721, "tradition": "Islamic calligraphy", "era": "Various", "master": "Various", "notes": "Greek collection of Islamic calligraphy spanning centuries"},
    {"name": "Musee de la Calligraphie", "city": "Marrakech", "country": "Morocco", "lat": 31.631, "lon": -7.985, "tradition": "Moroccan calligraphy", "era": "Modern", "master": "Various", "notes": "Museum in historic Medina dedicated to Moroccan calligraphic art"},
    {"name": "Freer Gallery of Art (Smithsonian)", "city": "Washington DC", "country": "USA", "lat": 38.888, "lon": -77.027, "tradition": "Asian calligraphy", "era": "Various", "master": "Various", "notes": "Extensive Asian calligraphy collection including Chinese, Japanese, Korean"},
]

# =====================================================================
# MODE-DATA MAPPING
# =====================================================================
MODE_DATA_MAP = {
    "Chinese Calligraphy Heritage": CHINESE_CALLIGRAPHY,
    "Japanese Shodo Traditions": JAPANESE_SHODO,
    "Arabic & Islamic Calligraphy": ARABIC_CALLIGRAPHY,
    "Medieval Illuminated Manuscripts": ILLUMINATED_MANUSCRIPTS,
    "Typography & Printing Heritage": TYPOGRAPHY_PRINTING,
    "Korean Hangul Heritage Sites": KOREAN_HANGUL,
    "Tibetan & Sanskrit Writing": TIBETAN_SANSKRIT,
    "Celtic & Insular Script Sites": CELTIC_INSULAR,
    "Modern Lettering & Graffiti Art": MODERN_LETTERING,
    "Calligraphy Museums & Schools": CALLIGRAPHY_MUSEUMS,
}

MODE_COLORS = {
    "Chinese Calligraphy Heritage": "#ef4444",
    "Japanese Shodo Traditions": "#ec4899",
    "Arabic & Islamic Calligraphy": "#10b981",
    "Medieval Illuminated Manuscripts": "#f59e0b",
    "Typography & Printing Heritage": "#3b82f6",
    "Korean Hangul Heritage Sites": "#8b5cf6",
    "Tibetan & Sanskrit Writing": "#f97316",
    "Celtic & Insular Script Sites": "#06b6d4",
    "Modern Lettering & Graffiti Art": "#a855f7",
    "Calligraphy Museums & Schools": "#14b8a6",
}

MODE_ICONS = {
    "Chinese Calligraphy Heritage": "pencil",
    "Japanese Shodo Traditions": "paint-brush",
    "Arabic & Islamic Calligraphy": "mosque",
    "Medieval Illuminated Manuscripts": "book",
    "Typography & Printing Heritage": "print",
    "Korean Hangul Heritage Sites": "font",
    "Tibetan & Sanskrit Writing": "om",
    "Celtic & Insular Script Sites": "cross",
    "Modern Lettering & Graffiti Art": "spray-can",
    "Calligraphy Museums & Schools": "university",
}


# =====================================================================
# HELPER: build popup HTML
# =====================================================================
def _popup_html(item: dict, color: str) -> str:
    """Build a rich HTML popup for a calligraphy site marker."""
    name = html_module.escape(str(item.get("name", "")))
    city = html_module.escape(str(item.get("city", "")))
    country = html_module.escape(str(item.get("country", "")))
    tradition = html_module.escape(str(item.get("tradition", "")))
    era = html_module.escape(str(item.get("era", "")))
    master = html_module.escape(str(item.get("master", "")))
    notes = html_module.escape(str(item.get("notes", "")))

    extra_rows = ""
    # Some modes have extra fields
    for key in ("length_km", "status", "year_started", "claimants", "area_km2", "since"):
        val = item.get(key)
        if val is not None:
            label = html_module.escape(key.replace("_", " ").title())
            extra_rows += f'<tr><td style="color:#8b97b0;padding:2px 6px;">{label}</td><td style="padding:2px 6px;">{html_module.escape(str(val))}</td></tr>'

    return f"""
    <div style="font-family:Inter,Arial,sans-serif;width:300px;background:#111827;color:#e8ecf4;
                border:1px solid {color};border-radius:8px;padding:12px;">
        <h4 style="margin:0 0 6px 0;color:{color};font-size:14px;">{name}</h4>
        <table style="font-size:12px;width:100%;border-collapse:collapse;">
            <tr><td style="color:#8b97b0;padding:2px 6px;">City</td><td style="padding:2px 6px;">{city}</td></tr>
            <tr><td style="color:#8b97b0;padding:2px 6px;">Country</td><td style="padding:2px 6px;">{country}</td></tr>
            <tr><td style="color:#8b97b0;padding:2px 6px;">Tradition</td><td style="padding:2px 6px;">{tradition}</td></tr>
            <tr><td style="color:#8b97b0;padding:2px 6px;">Era</td><td style="padding:2px 6px;">{era}</td></tr>
            <tr><td style="color:#8b97b0;padding:2px 6px;">Master/Origin</td><td style="padding:2px 6px;">{master}</td></tr>
            {extra_rows}
        </table>
        <p style="font-size:11px;color:#8b97b0;margin:6px 0 0 0;border-top:1px solid #2a3550;padding-top:6px;">
            {notes}
        </p>
    </div>
    """


# =====================================================================
# HELPER: build folium map
# =====================================================================
def _build_map(data: list, color: str, icon_name: str) -> folium.Map:
    """Create a dark-themed folium map with markers for all items."""
    if not data:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    avg_lat = sum(d["lat"] for d in data) / len(data)
    avg_lon = sum(d["lon"] for d in data) / len(data)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )

    for item in data:
        popup_content = _popup_html(item, color)
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=item["name"],
            icon=folium.Icon(color="darkred" if color.startswith("#e") else "purple",
                             icon="info-sign"),
        ).add_to(m)

    return m


# =====================================================================
# HELPER: build DataFrame
# =====================================================================
def _build_dataframe(data: list) -> pd.DataFrame:
    """Convert a list of dicts to a cleaned DataFrame."""
    df = pd.DataFrame(data)
    # Standardise column names for display
    col_rename = {
        "name": "Name",
        "city": "City",
        "country": "Country",
        "tradition": "Tradition",
        "era": "Era",
        "master": "Master/Origin",
        "notes": "Notes",
        "lat": "Latitude",
        "lon": "Longitude",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
    return df


# =====================================================================
# MODE DESCRIPTIONS
# =====================================================================
MODE_DESCRIPTIONS = {
    "Chinese Calligraphy Heritage": (
        "Explore the birthplaces, museums, and sacred sites of Chinese calligraphy "
        "spanning over 3,000 years -- from Shang Dynasty oracle bone inscriptions to "
        "the Four Treasures of the Study. Includes stele forests, ink and paper "
        "production sites, and memorials to legendary masters like Wang Xizhi, "
        "Yan Zhenqing, and Su Dongpo."
    ),
    "Japanese Shodo Traditions": (
        "Discover the art of Japanese Shodo (the Way of Writing) across temples, "
        "museums, and craft villages. Features Zen calligraphy (bokuseki), Heian-era "
        "kana masterworks, sutra-copying traditions, and the brush-making center "
        "of Kumano. Includes sites linked to the Three Great Calligraphers (Sanpitsu) "
        "and modern avant-garde calligraphy."
    ),
    "Arabic & Islamic Calligraphy": (
        "Journey through the Islamic world's finest calligraphic traditions -- from "
        "the Dome of the Rock's Kufic inscriptions to Ottoman Thuluth masterworks "
        "in Istanbul, Safavid Nastaliq in Isfahan, and Maghribi script in Fez. "
        "Includes mosques, madrasas, museums, and the Taj Mahal's Quranic inlay."
    ),
    "Medieval Illuminated Manuscripts": (
        "Visit the scriptoria, libraries, and monasteries where Europe's greatest "
        "illuminated manuscripts were created and preserved. From the Book of Kells "
        "in Dublin to the Tres Riches Heures in Chantilly, the Codex Gigas in "
        "Stockholm, and the Armenian Matenadaran in Yerevan."
    ),
    "Typography & Printing Heritage": (
        "Trace the history of movable type from Gutenberg's workshop in Mainz to "
        "Korea's Jikji printing site, Aldus Manutius in Venice, and modern "
        "typefoundries. Includes museums, historic press sites, and centres "
        "preserving typefaces from Bodoni to Futura."
    ),
    "Korean Hangul Heritage Sites": (
        "Celebrate the Korean alphabet -- Hangeul -- created by King Sejong in 1443. "
        "Explore palaces, temples, Confucian academies, and museums preserving "
        "Korea's rich calligraphic heritage from the Three Kingdoms period through "
        "the Joseon Dynasty to modern Hangeul typography."
    ),
    "Tibetan & Sanskrit Writing": (
        "Explore the manuscript traditions of Tibetan Buddhism and the Sanskrit "
        "writing heritage of South Asia. From the Potala Palace's gold-lettered "
        "sutras to Nalanda's ancient scriptorium, Dunhuang-adjacent Tibetan caves, "
        "and Ladakhi monastery libraries."
    ),
    "Celtic & Insular Script Sites": (
        "Discover the origins of insular script in the monasteries of Ireland, "
        "Scotland, and Northumbria. From Skellig Michael and Iona to Lindisfarne "
        "and Bobbio, follow the monks who created the Book of Kells and carried "
        "their unique scripts across Europe."
    ),
    "Modern Lettering & Graffiti Art": (
        "Survey the world's most vibrant street art and graffiti lettering districts. "
        "From Wynwood Walls in Miami to Berlin's East Side Gallery, Melbourne's "
        "Hosier Lane, Sao Paulo's Beco do Batman, and Dubai's calligraffiti movement. "
        "Includes legal walls, mural festivals, and urban typographic art."
    ),
    "Calligraphy Museums & Schools": (
        "Find the world's dedicated calligraphy museums, schools, auction houses, "
        "research centres, and professional organisations. From the National Hangeul "
        "Museum in Seoul to IRCICA in Istanbul, the Society of Scribes in London, "
        "and the Freer Gallery in Washington DC."
    ),
}

# =====================================================================
# FOLIUM ICON COLOUR MAPPING
# =====================================================================
_FOLIUM_ICON_COLORS = {
    "Chinese Calligraphy Heritage": "red",
    "Japanese Shodo Traditions": "pink",
    "Arabic & Islamic Calligraphy": "green",
    "Medieval Illuminated Manuscripts": "orange",
    "Typography & Printing Heritage": "blue",
    "Korean Hangul Heritage Sites": "purple",
    "Tibetan & Sanskrit Writing": "orange",
    "Celtic & Insular Script Sites": "cadetblue",
    "Modern Lettering & Graffiti Art": "darkpurple",
    "Calligraphy Museums & Schools": "darkgreen",
}


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_calligraphy_maps_tab():
    """Render the Calligraphy & Writing Art Explorer tab."""
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>Calligraphy & Writing Art Explorer</h4>'
        '<p>Calligraphy traditions, illuminated manuscripts, typography heritage & ink art</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    mode = st.selectbox("Select Map Mode", [
        "Chinese Calligraphy Heritage",
        "Japanese Shodo Traditions",
        "Arabic & Islamic Calligraphy",
        "Medieval Illuminated Manuscripts",
        "Typography & Printing Heritage",
        "Korean Hangul Heritage Sites",
        "Tibetan & Sanskrit Writing",
        "Celtic & Insular Script Sites",
        "Modern Lettering & Graffiti Art",
        "Calligraphy Museums & Schools",
    ], key="calligraphy_maps_mode")

    # ---- Mode description ----
    description = MODE_DESCRIPTIONS.get(mode, "")
    if description:
        st.info(description)

    data = MODE_DATA_MAP.get(mode, [])
    color = MODE_COLORS.get(mode, "#06b6d4")
    icon_name = MODE_ICONS.get(mode, "info-sign")
    folium_color = _FOLIUM_ICON_COLORS.get(mode, "purple")

    # ---- Filter controls ----
    st.markdown("---")
    st.subheader("Filter & Search")
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        search_term = st.text_input(
            "Search sites by name or notes",
            value="",
            key="calligraphy_search",
            placeholder="e.g. Gutenberg, Wang Xizhi, Kells...",
        )

    with filter_col2:
        all_countries = sorted({d.get("country", "Unknown") for d in data})
        selected_countries = st.multiselect(
            "Filter by country",
            options=all_countries,
            default=[],
            key="calligraphy_country_filter",
        )

    # Apply filters
    filtered_data = data
    if search_term.strip():
        term_lower = search_term.strip().lower()
        filtered_data = [
            d for d in filtered_data
            if term_lower in d.get("name", "").lower()
            or term_lower in d.get("notes", "").lower()
            or term_lower in d.get("tradition", "").lower()
            or term_lower in d.get("master", "").lower()
            or term_lower in d.get("city", "").lower()
        ]
    if selected_countries:
        filtered_data = [
            d for d in filtered_data
            if d.get("country", "Unknown") in selected_countries
        ]

    # ---- Stats metrics ----
    st.markdown("---")
    countries = list({d.get("country", "Unknown") for d in filtered_data})
    traditions = list({d.get("tradition", "Unknown") for d in filtered_data})
    eras = list({d.get("era", "Unknown") for d in filtered_data})
    masters = list({d.get("master", "Unknown") for d in filtered_data})

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Total Sites", len(filtered_data))
    mc2.metric("Countries", len(countries))
    mc3.metric("Traditions", len(traditions))
    mc4.metric("Eras Covered", len(eras))

    mc5, mc6, mc7, mc8 = st.columns(4)
    mc5.metric("Masters / Origins", len(masters))
    mc6.metric("Mode", mode.split()[0])
    mc7.metric("Filtered", f"{len(filtered_data)}/{len(data)}")
    mc8.metric("Map Markers", len(filtered_data))

    # ---- Map ----
    st.markdown("---")
    st.subheader(f"Map: {mode}")

    if not filtered_data:
        st.warning("No sites match the current filters. Try broadening your search.")
        empty_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        st_html(empty_map._repr_html_(), height=500)
    else:
        # Build the map with filtered data
        avg_lat = sum(d["lat"] for d in filtered_data) / len(filtered_data)
        avg_lon = sum(d["lon"] for d in filtered_data) / len(filtered_data)

        fmap = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=3 if len(filtered_data) > 5 else 6,
            tiles="CartoDB dark_matter",
        )

        for item in filtered_data:
            popup_content = _popup_html(item, color)
            folium.Marker(
                location=[item["lat"], item["lon"]],
                popup=folium.Popup(popup_content, max_width=320),
                tooltip=html_module.escape(item.get("name", "")),
                icon=folium.Icon(color=folium_color, icon="info-sign"),
            ).add_to(fmap)

        st_html(fmap._repr_html_(), height=500)

    # ---- Country breakdown ----
    st.markdown("---")
    st.subheader("Country Breakdown")
    country_counts = {}
    for d in filtered_data:
        c = d.get("country", "Unknown")
        country_counts[c] = country_counts.get(c, 0) + 1

    if country_counts:
        country_df = pd.DataFrame(
            sorted(country_counts.items(), key=lambda x: x[1], reverse=True),
            columns=["Country", "Sites"],
        )
        bc1, bc2 = st.columns([2, 3])
        with bc1:
            st.dataframe(country_df, use_container_width=True)
        with bc2:
            st.bar_chart(country_df.set_index("Country"))

    # ---- Tradition breakdown ----
    st.markdown("---")
    st.subheader("Traditions & Scripts")
    tradition_counts = {}
    for d in filtered_data:
        t = d.get("tradition", "Unknown")
        tradition_counts[t] = tradition_counts.get(t, 0) + 1

    if tradition_counts:
        tradition_df = pd.DataFrame(
            sorted(tradition_counts.items(), key=lambda x: x[1], reverse=True),
            columns=["Tradition", "Sites"],
        )
        tc1, tc2 = st.columns([2, 3])
        with tc1:
            st.dataframe(tradition_df, use_container_width=True)
        with tc2:
            st.bar_chart(tradition_df.set_index("Tradition"))

    # ---- Era breakdown ----
    st.markdown("---")
    st.subheader("Historical Eras")
    era_counts = {}
    for d in filtered_data:
        e = d.get("era", "Unknown")
        era_counts[e] = era_counts.get(e, 0) + 1

    if era_counts:
        era_df = pd.DataFrame(
            sorted(era_counts.items(), key=lambda x: x[1], reverse=True),
            columns=["Era", "Sites"],
        )
        st.dataframe(era_df, use_container_width=True)

    # ---- Detailed site cards ----
    st.markdown("---")
    st.subheader("Site Details")
    for idx, item in enumerate(filtered_data):
        with st.expander(
            f"{idx + 1}. {item.get('name', 'Unknown')} -- {item.get('city', '')}, {item.get('country', '')}",
            expanded=False,
        ):
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown(f"**Tradition:** {html_module.escape(str(item.get('tradition', 'N/A')))}")
                st.markdown(f"**Era:** {html_module.escape(str(item.get('era', 'N/A')))}")
                st.markdown(f"**Master / Origin:** {html_module.escape(str(item.get('master', 'N/A')))}")
            with dc2:
                st.markdown(f"**Latitude:** {item.get('lat', 'N/A')}")
                st.markdown(f"**Longitude:** {item.get('lon', 'N/A')}")
                st.markdown(f"**Country:** {html_module.escape(str(item.get('country', 'N/A')))}")
            st.markdown(f"**Notes:** {html_module.escape(str(item.get('notes', '')))}")

            # Mini map for individual site
            mini_map = folium.Map(
                location=[item["lat"], item["lon"]],
                zoom_start=12,
                tiles="CartoDB dark_matter",
            )
            folium.Marker(
                location=[item["lat"], item["lon"]],
                popup=item.get("name", ""),
                icon=folium.Icon(color=folium_color, icon="info-sign"),
            ).add_to(mini_map)
            st_html(mini_map._repr_html_(), height=250)

    # ---- Full data table ----
    st.markdown("---")
    st.subheader("Full Data Table")
    df = _build_dataframe(filtered_data)
    st.dataframe(df, use_container_width=True)

    # ---- CSV download ----
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buf.getvalue(),
        file_name=f"calligraphy_{mode.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )

    # ---- Footer note ----
    st.markdown("---")
    st.caption(
        "Data is curated and hardcoded. Coordinates are approximate. "
        "Some sites may have restricted access or seasonal availability. "
        "All calligraphy traditions represented here span millennia of human "
        "creative achievement in the art of beautiful writing."
    )
