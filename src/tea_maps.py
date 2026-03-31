"""
Tea & Tea Culture Explorer module for TerraScout AI.
Displays hardcoded locations for tea gardens, ceremony traditions,
historic trade routes, tea heritage sites, and famous teahouses worldwide.
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

# ========================================================================
# COLOR PALETTE
# ========================================================================
TEA_COLORS = {
    "green": "#10b981",
    "black": "#8b5cf6",
    "oolong": "#f59e0b",
    "white": "#e2e8f0",
    "pu-erh": "#b45309",
    "herbal": "#ec4899",
    "matcha": "#22c55e",
    "chai": "#f97316",
    "yerba": "#16a34a",
    "heritage": "#06b6d4",
    "route": "#ef4444",
    "teahouse": "#a855f7",
}

# ========================================================================
# HARDCODED DATA SETS
# ========================================================================

CHINESE_TEA_REGIONS = [
    {"name": "Longjing Village, Hangzhou", "lat": 30.22, "lon": 120.10, "province": "Zhejiang", "tea": "Dragon Well (Longjing)", "type": "Green", "elevation_m": 150, "notes": "China's most famous green tea; pan-fired, flat leaves"},
    {"name": "Wuyi Mountains", "lat": 27.72, "lon": 117.68, "province": "Fujian", "tea": "Da Hong Pao", "type": "Oolong", "elevation_m": 650, "notes": "UNESCO site; legendary Big Red Robe oolong"},
    {"name": "Anxi County", "lat": 25.06, "lon": 117.98, "province": "Fujian", "tea": "Tieguanyin", "type": "Oolong", "elevation_m": 500, "notes": "Iron Goddess of Mercy; floral oolong"},
    {"name": "Yunnan Xishuangbanna", "lat": 22.00, "lon": 100.80, "province": "Yunnan", "tea": "Pu-erh", "type": "Pu-erh", "elevation_m": 1200, "notes": "Ancient tea trees; fermented aged tea"},
    {"name": "Menghai County", "lat": 21.96, "lon": 100.45, "province": "Yunnan", "tea": "Shou Pu-erh", "type": "Pu-erh", "elevation_m": 1100, "notes": "Home of Menghai Tea Factory (TAETEA)"},
    {"name": "Phoenix Mountain (Fenghuang)", "lat": 23.92, "lon": 116.63, "province": "Guangdong", "tea": "Dan Cong", "type": "Oolong", "elevation_m": 1100, "notes": "Single-trunk tea trees; aromatic oolong"},
    {"name": "Huangshan (Yellow Mountain)", "lat": 30.13, "lon": 118.16, "province": "Anhui", "tea": "Huangshan Maofeng", "type": "Green", "elevation_m": 800, "notes": "Misty peaks produce delicate green tea"},
    {"name": "Keemun County (Qimen)", "lat": 29.85, "lon": 117.72, "province": "Anhui", "tea": "Keemun Black", "type": "Black", "elevation_m": 400, "notes": "China's premier black tea; malty and smooth"},
    {"name": "Dongting Mountain, Taihu", "lat": 31.07, "lon": 120.38, "province": "Jiangsu", "tea": "Bi Luo Chun", "type": "Green", "elevation_m": 300, "notes": "Green Snail Spring; fruity aroma from nearby fruit trees"},
    {"name": "Lu Mountain (Lushan)", "lat": 29.56, "lon": 115.98, "province": "Jiangxi", "tea": "Lushan Yunwu", "type": "Green", "elevation_m": 1100, "notes": "Cloud Mist tea from perpetually foggy peaks"},
    {"name": "Anji County", "lat": 30.63, "lon": 119.68, "province": "Zhejiang", "tea": "Anji Bai Cha", "type": "Green", "elevation_m": 400, "notes": "White-leaf green tea; rich in amino acids"},
    {"name": "Fuding City", "lat": 27.33, "lon": 120.20, "province": "Fujian", "tea": "Fuding White Tea", "type": "White", "elevation_m": 600, "notes": "Birthplace of Silver Needle (Baihao Yinzhen)"},
    {"name": "Zhenghe County", "lat": 27.37, "lon": 118.86, "province": "Fujian", "tea": "Zhenghe White Peony", "type": "White", "elevation_m": 500, "notes": "White Peony (Bai Mudan); fuller flavor"},
    {"name": "Laoshan, Qingdao", "lat": 36.17, "lon": 120.62, "province": "Shandong", "tea": "Laoshan Green", "type": "Green", "elevation_m": 300, "notes": "Northernmost Chinese green tea; mineral-rich"},
    {"name": "Enshi Prefecture", "lat": 30.27, "lon": 109.49, "province": "Hubei", "tea": "Enshi Yulu", "type": "Green", "elevation_m": 800, "notes": "Rare steamed green tea; jade-dew style"},
    {"name": "Yixing", "lat": 31.35, "lon": 119.82, "province": "Jiangsu", "tea": "Yixing Red Tea", "type": "Black", "elevation_m": 200, "notes": "Famous for purple-clay teapots; local red tea"},
    {"name": "Jingmai Mountain", "lat": 22.10, "lon": 100.00, "province": "Yunnan", "tea": "Ancient Tree Pu-erh", "type": "Pu-erh", "elevation_m": 1400, "notes": "2.8 million ancient tea plants; UNESCO candidate"},
    {"name": "Lincang Bingdao", "lat": 23.73, "lon": 100.00, "province": "Yunnan", "tea": "Bingdao Pu-erh", "type": "Pu-erh", "elevation_m": 1500, "notes": "Most expensive pu-erh village; sweet and cooling"},
    {"name": "Yiwu Tea Mountain", "lat": 22.05, "lon": 101.48, "province": "Yunnan", "tea": "Yiwu Sheng Pu-erh", "type": "Pu-erh", "elevation_m": 1300, "notes": "Historic start of Ancient Tea Horse Road"},
    {"name": "Taiping County", "lat": 30.50, "lon": 118.17, "province": "Anhui", "tea": "Taiping Houkui", "type": "Green", "elevation_m": 700, "notes": "Monkey King tea; longest flat green tea leaves"},
    {"name": "Junshan Island, Dongting Lake", "lat": 29.38, "lon": 113.00, "province": "Hunan", "tea": "Junshan Yinzhen", "type": "Yellow", "elevation_m": 50, "notes": "Rare yellow tea; only from this tiny island"},
    {"name": "Mengding Mountain", "lat": 30.08, "lon": 103.02, "province": "Sichuan", "tea": "Mengding Ganlu", "type": "Green", "elevation_m": 1000, "notes": "Legendary origin of cultivated tea; Sweet Dew"},
    {"name": "Lapsang Village, Tongmu", "lat": 27.75, "lon": 117.72, "province": "Fujian", "tea": "Lapsang Souchong", "type": "Black", "elevation_m": 1000, "notes": "Birthplace of black tea; pine-smoked"},
    {"name": "Jinjunmei, Tongmu", "lat": 27.73, "lon": 117.70, "province": "Fujian", "tea": "Jin Jun Mei", "type": "Black", "elevation_m": 1200, "notes": "Golden eyebrow; premium bud-only black tea"},
    {"name": "Bulang Mountain", "lat": 21.62, "lon": 100.30, "province": "Yunnan", "tea": "Lao Banzhang Pu-erh", "type": "Pu-erh", "elevation_m": 1700, "notes": "King of Pu-erh; powerful and bitter-sweet"},
    {"name": "Dianxi Fengqing", "lat": 24.58, "lon": 99.92, "province": "Yunnan", "tea": "Dianhong Golden Tips", "type": "Black", "elevation_m": 1500, "notes": "Yunnan gold; malty with honey notes"},
    {"name": "Emeishan", "lat": 29.60, "lon": 103.33, "province": "Sichuan", "tea": "Zhuyeqing", "type": "Green", "elevation_m": 1000, "notes": "Bamboo Leaf Green; flat buds from sacred mountain"},
    {"name": "Xinyang", "lat": 32.13, "lon": 114.07, "province": "Henan", "tea": "Xinyang Maojian", "type": "Green", "elevation_m": 400, "notes": "Top 10 Chinese tea; hairy tips green tea"},
    {"name": "Liu'an County", "lat": 31.75, "lon": 116.50, "province": "Anhui", "tea": "Liu'an Guapian", "type": "Green", "elevation_m": 600, "notes": "Melon Seed tea; only leaves, no buds"},
    {"name": "Wuzhou, Guangxi", "lat": 23.48, "lon": 111.28, "province": "Guangxi", "tea": "Liu Bao", "type": "Dark", "elevation_m": 300, "notes": "Aged dark tea; betel nut aroma, post-fermented"},
]

JAPANESE_TEA_GARDENS = [
    {"name": "Uji, Kyoto", "lat": 34.89, "lon": 135.80, "region": "Kansai", "tea": "Uji Matcha & Gyokuro", "type": "Matcha/Green", "notes": "Japan's most prestigious tea region since 1191"},
    {"name": "Shizuoka City", "lat": 34.98, "lon": 138.38, "region": "Chubu", "tea": "Shizuoka Sencha", "type": "Green", "notes": "40% of Japan's tea; views of Mt. Fuji"},
    {"name": "Kagoshima, Chiran", "lat": 31.38, "lon": 130.44, "region": "Kyushu", "tea": "Chiran Sencha", "type": "Green", "notes": "Second largest producer; deep steamed sencha"},
    {"name": "Nishio, Aichi", "lat": 34.85, "lon": 137.06, "region": "Chubu", "tea": "Nishio Matcha", "type": "Matcha", "notes": "Produces most of Japan's matcha powder"},
    {"name": "Yame, Fukuoka", "lat": 33.21, "lon": 130.56, "region": "Kyushu", "tea": "Yame Gyokuro", "type": "Gyokuro", "notes": "Highest grade gyokuro; shade-grown luxury"},
    {"name": "Sayama, Saitama", "lat": 35.85, "lon": 139.41, "region": "Kanto", "tea": "Sayama-cha", "type": "Green", "notes": "Fire-roasted finish; robust Kanto-style sencha"},
    {"name": "Mie Prefecture (Ise)", "lat": 34.73, "lon": 136.51, "region": "Kansai", "tea": "Ise-cha Kabusecha", "type": "Green", "notes": "Third largest producer; semi-shaded kabusecha"},
    {"name": "Miyazaki Prefecture", "lat": 31.91, "lon": 131.42, "region": "Kyushu", "tea": "Miyazaki Sencha", "type": "Green", "notes": "Warm climate; early harvest shincha"},
    {"name": "Kumamoto, Kikuchi", "lat": 33.00, "lon": 130.80, "region": "Kyushu", "tea": "Kumamoto Tamaryokucha", "type": "Green", "notes": "Curled-leaf green tea; sweet and mild"},
    {"name": "Wazuka, Kyoto", "lat": 34.79, "lon": 135.89, "region": "Kansai", "tea": "Wazuka Tencha", "type": "Matcha base", "notes": "Picturesque tea terraces; tencha for matcha"},
    {"name": "Kirishima, Kagoshima", "lat": 31.88, "lon": 130.87, "region": "Kyushu", "tea": "Kirishima Organic Sencha", "type": "Green", "notes": "Volcanic soil; renowned organic teas"},
    {"name": "Totsukawa, Nara", "lat": 34.01, "lon": 135.72, "region": "Kansai", "tea": "Yamato-cha", "type": "Green", "notes": "Mountain tea from remote Nara villages"},
    {"name": "Kawane, Shizuoka", "lat": 35.05, "lon": 138.08, "region": "Chubu", "tea": "Kawane Sencha", "type": "Green", "notes": "Mountain stream terraces; premium single-origin"},
    {"name": "Makinohara, Shizuoka", "lat": 34.73, "lon": 138.22, "region": "Chubu", "tea": "Makinohara Deep Steam", "type": "Green", "notes": "Largest tea plateau in Japan; fukamushi-cha"},
    {"name": "Tsukigase, Nara", "lat": 34.73, "lon": 136.02, "region": "Kansai", "tea": "Tsukigase Hojicha", "type": "Roasted Green", "notes": "Famous roasted tea; plum blossom village"},
    {"name": "Aso, Kumamoto", "lat": 32.88, "lon": 131.10, "region": "Kyushu", "tea": "Aso Kogen-cha", "type": "Green", "notes": "Highland tea near active caldera; mineral-rich"},
    {"name": "Honyama, Shizuoka", "lat": 35.07, "lon": 138.30, "region": "Chubu", "tea": "Honyama Sencha", "type": "Green", "notes": "Warring States-era origins; crisp mountain tea"},
    {"name": "Ashikubo, Shizuoka", "lat": 35.10, "lon": 138.25, "region": "Chubu", "tea": "Ashikubo Hon-gyokuro", "type": "Gyokuro", "notes": "Tiny micro-region; competition-winning gyokuro"},
    {"name": "Sashima, Ibaraki", "lat": 36.07, "lon": 139.85, "region": "Kanto", "tea": "Sashima-cha", "type": "Green", "notes": "Historic export tea; first Japanese tea to reach West"},
    {"name": "Iribancha Region, Tokushima", "lat": 33.94, "lon": 134.35, "region": "Shikoku", "tea": "Awa Bancha", "type": "Fermented", "notes": "Rare lactic-fermented tea; unique to Shikoku"},
    {"name": "Shimada, Shizuoka", "lat": 34.84, "lon": 138.18, "region": "Chubu", "tea": "Shimada Gyokuro", "type": "Gyokuro", "notes": "Oi River valley; award-winning shade-grown teas"},
    {"name": "Tanegashima, Kagoshima", "lat": 30.47, "lon": 131.00, "region": "Kyushu", "tea": "Tanegashima Shincha", "type": "Green", "notes": "Japan's earliest harvest; subtropical island tea"},
    {"name": "Kyotanabe, Kyoto", "lat": 34.82, "lon": 135.77, "region": "Kansai", "tea": "Kyotanabe Gyokuro", "type": "Gyokuro", "notes": "Oldest gyokuro production area in Japan"},
    {"name": "Ogawa, Saitama", "lat": 36.06, "lon": 139.27, "region": "Kanto", "tea": "Ogawa-cha Organic", "type": "Green", "notes": "Pioneer of organic tea farming in Japan"},
    {"name": "Yakushima Island", "lat": 30.35, "lon": 130.50, "region": "Kyushu", "tea": "Yakushima Wild Tea", "type": "Green", "notes": "Ancient forest island; wild tea plants over 300 yrs"},
]

INDIAN_TEA_ESTATES = [
    {"name": "Makaibari Estate, Darjeeling", "lat": 27.05, "lon": 88.28, "state": "West Bengal", "tea": "Darjeeling First Flush", "type": "Black", "elevation_m": 1500, "notes": "World's first tea factory (1859); biodynamic"},
    {"name": "Happy Valley Estate, Darjeeling", "lat": 27.04, "lon": 88.26, "state": "West Bengal", "tea": "Darjeeling Muscatel", "type": "Black", "elevation_m": 2100, "notes": "Est. 1854; visitor-friendly; muscatel flavor"},
    {"name": "Castleton Estate, Darjeeling", "lat": 27.02, "lon": 88.30, "state": "West Bengal", "tea": "Castleton Moonlight", "type": "Black/White", "elevation_m": 1600, "notes": "Record-breaking auction prices; iconic estate"},
    {"name": "Margaret's Hope, Darjeeling", "lat": 27.00, "lon": 88.25, "state": "West Bengal", "tea": "Second Flush Muscatel", "type": "Black", "elevation_m": 1800, "notes": "Named after planter's daughter; classic muscatel"},
    {"name": "Assam Mangalam Estate", "lat": 26.80, "lon": 94.20, "state": "Assam", "tea": "Assam Orthodox TGFOP", "type": "Black", "elevation_m": 90, "notes": "Rich malty Assam; golden tips"},
    {"name": "Halmari Estate, Assam", "lat": 26.88, "lon": 93.90, "state": "Assam", "tea": "Halmari Gold CTC", "type": "Black", "elevation_m": 100, "notes": "World's best CTC tea (multiple awards)"},
    {"name": "Manohari Estate, Assam", "lat": 27.48, "lon": 95.78, "state": "Assam", "tea": "Manohari Gold Tips", "type": "Black", "elevation_m": 120, "notes": "Most expensive Indian tea; gold-leaf buds"},
    {"name": "Munnar, Kolukkumalai", "lat": 10.07, "lon": 77.24, "state": "Kerala", "tea": "High-Grown Nilgiri", "type": "Black", "elevation_m": 2400, "notes": "World's highest tea plantation; jeep-access only"},
    {"name": "Tata Tea Museum, Munnar", "lat": 10.09, "lon": 77.06, "state": "Kerala", "tea": "Kannan Devan", "type": "Black", "elevation_m": 1600, "notes": "Heritage museum; Tata family's iconic plantation"},
    {"name": "Ooty, Nilgiri Hills", "lat": 11.41, "lon": 76.69, "state": "Tamil Nadu", "tea": "Nilgiri Frost Tea", "type": "Black", "elevation_m": 2200, "notes": "Winter frost creates unique brisk flavor"},
    {"name": "Coonoor, Nilgiris", "lat": 11.35, "lon": 76.80, "state": "Tamil Nadu", "tea": "Highfield Nilgiri", "type": "Black", "elevation_m": 1800, "notes": "Sim's Park adjacent; aromatic high-grown"},
    {"name": "Valparai, Anamalais", "lat": 10.33, "lon": 76.97, "state": "Tamil Nadu", "tea": "Anamalai Green", "type": "Green", "elevation_m": 1100, "notes": "Rainforest corridor; wildlife-friendly plantation"},
    {"name": "Kangra Valley", "lat": 32.10, "lon": 76.27, "state": "Himachal Pradesh", "tea": "Kangra Green/White", "type": "Green", "elevation_m": 1300, "notes": "GI-tagged; Himalayan green tea since 1849"},
    {"name": "Palampur, Kangra", "lat": 32.11, "lon": 76.54, "state": "Himachal Pradesh", "tea": "Palampur CTC", "type": "Black", "elevation_m": 1200, "notes": "Tea capital of NW India; Dhauladhar backdrop"},
    {"name": "Dooars, Jalpaiguri", "lat": 26.68, "lon": 88.95, "state": "West Bengal", "tea": "Dooars CTC", "type": "Black", "elevation_m": 150, "notes": "Plains tea; backbone of Indian CTC production"},
    {"name": "Cachar, Barak Valley", "lat": 24.83, "lon": 92.78, "state": "Assam", "tea": "Cachar Orthodox", "type": "Black", "elevation_m": 50, "notes": "Southern Assam plains; spicy character"},
    {"name": "Wayanad", "lat": 11.69, "lon": 76.08, "state": "Kerala", "tea": "Wayanad Green", "type": "Green", "elevation_m": 900, "notes": "Western Ghats; organic tribal tea gardens"},
    {"name": "Dibrugarh, Upper Assam", "lat": 27.47, "lon": 94.91, "state": "Assam", "tea": "Upper Assam FTGFOP", "type": "Black", "elevation_m": 110, "notes": "Tea capital of India; strongest Assam teas"},
    {"name": "Temi Tea Garden, Sikkim", "lat": 27.24, "lon": 88.53, "state": "Sikkim", "tea": "Temi Organic", "type": "Black", "elevation_m": 1500, "notes": "Only tea estate in Sikkim; fully organic"},
    {"name": "Sonitpur, Tezpur", "lat": 26.63, "lon": 92.80, "state": "Assam", "tea": "Tezpur Green", "type": "Green", "elevation_m": 80, "notes": "Brahmaputra valley; emerging specialty greens"},
    {"name": "Idukki, High Ranges", "lat": 9.85, "lon": 76.97, "state": "Kerala", "tea": "High Range BOPF", "type": "Black", "elevation_m": 1600, "notes": "Spice-country tea; cardamom-adjacent estates"},
    {"name": "Tripura State Gardens", "lat": 23.83, "lon": 91.28, "state": "Tripura", "tea": "Tripura CTC", "type": "Black", "elevation_m": 60, "notes": "Northeast frontier; small-holder gardens"},
    {"name": "Jorhat, Tocklai", "lat": 26.75, "lon": 94.22, "state": "Assam", "tea": "Tocklai Research Tea", "type": "Black", "elevation_m": 95, "notes": "World's oldest tea research station (1911)"},
    {"name": "Kotagiri, Nilgiris", "lat": 11.42, "lon": 76.86, "state": "Tamil Nadu", "tea": "Kotagiri Specialty", "type": "Black", "elevation_m": 1900, "notes": "Cool-climate; aromatic and brisk Nilgiri"},
    {"name": "Deolo Hill, Kalimpong", "lat": 27.07, "lon": 88.47, "state": "West Bengal", "tea": "Kalimpong Green", "type": "Green", "elevation_m": 1250, "notes": "Overlooking Teesta valley; boutique green teas"},
]

SRI_LANKAN_TEA_HIGHLANDS = [
    {"name": "Nuwara Eliya", "lat": 6.97, "lon": 80.77, "district": "Nuwara Eliya", "tea": "High-Grown Ceylon", "elevation_m": 1868, "flavor": "Light, delicate, floral", "notes": "Champagne of Ceylon tea; highest estates"},
    {"name": "Pedro Estate", "lat": 6.96, "lon": 80.76, "district": "Nuwara Eliya", "tea": "Pedro FBOP", "elevation_m": 1700, "flavor": "Crisp, bright liquor", "notes": "Famous visitor estate; est. 1885"},
    {"name": "Lover's Leap Estate", "lat": 6.98, "lon": 80.78, "district": "Nuwara Eliya", "tea": "Lover's Leap OP", "elevation_m": 1800, "flavor": "Muscatel, champagne-like", "notes": "Named after romantic legend; iconic label"},
    {"name": "Dimbula Valley", "lat": 6.95, "lon": 80.65, "district": "Nuwara Eliya", "tea": "Dimbula BOP", "elevation_m": 1250, "flavor": "Full body, mellow", "notes": "West-slope; monsoon creates seasonal flush"},
    {"name": "Haputale", "lat": 6.77, "lon": 80.95, "district": "Badulla", "tea": "Uva Highland OP", "elevation_m": 1431, "flavor": "Brisk, pungent, exotic", "notes": "Knuckles range; Lipton's Seat viewpoint"},
    {"name": "Ella Tea Estates", "lat": 6.87, "lon": 81.05, "district": "Badulla", "tea": "Ella Premium", "elevation_m": 1041, "flavor": "Balanced, fruity", "notes": "Popular tourist area; scenic train route"},
    {"name": "Bandarawela", "lat": 6.83, "lon": 80.98, "district": "Badulla", "tea": "Bandarawela FBOP", "elevation_m": 1230, "flavor": "Smooth, round", "notes": "Uva district gem; mild climate"},
    {"name": "Kandy Region", "lat": 7.29, "lon": 80.64, "district": "Kandy", "tea": "Mid-Grown Kandy", "elevation_m": 650, "flavor": "Strong, full-bodied", "notes": "Mid-elevation; robust character"},
    {"name": "Ruhuna (Galle)", "lat": 6.25, "lon": 80.35, "district": "Galle", "tea": "Low-Grown Ruhuna", "elevation_m": 200, "flavor": "Dark, malty, sweet", "notes": "Southern coast lowland; strong breakfast tea"},
    {"name": "Ratnapura", "lat": 6.68, "lon": 80.40, "district": "Ratnapura", "tea": "Sabaragamuwa BOP", "elevation_m": 300, "flavor": "Sweet, caramel notes", "notes": "Gem capital; unique terroir from gem-bearing soil"},
    {"name": "Matale", "lat": 7.47, "lon": 80.62, "district": "Matale", "tea": "Matale Medium", "elevation_m": 500, "flavor": "Spicy, aromatic", "notes": "Spice garden adjacent; cinnamon influence"},
    {"name": "Bogawantalawa Valley", "lat": 6.80, "lon": 80.63, "district": "Nuwara Eliya", "tea": "Golden Valley FBOPF", "elevation_m": 1400, "flavor": "Delicate, golden", "notes": "Golden Valley of Ceylon; premium single-origin"},
    {"name": "Uva Highlands, Badulla", "lat": 6.98, "lon": 81.05, "district": "Badulla", "tea": "Uva BOP", "elevation_m": 1500, "flavor": "Unique pungent character", "notes": "Cachan wind creates distinctive Uva flavor"},
    {"name": "Maskeliya", "lat": 6.83, "lon": 80.55, "district": "Nuwara Eliya", "tea": "Adam's Peak Ceylon", "elevation_m": 1200, "flavor": "Elegant, bright", "notes": "Near Sri Pada (Adam's Peak); pilgrimage route"},
    {"name": "Lindula", "lat": 6.95, "lon": 80.68, "district": "Nuwara Eliya", "tea": "Lindula BOPF", "elevation_m": 1600, "flavor": "Clean, sparkling", "notes": "Between Nuwara Eliya and Hatton; pristine air"},
    {"name": "Hatton", "lat": 6.90, "lon": 80.60, "district": "Nuwara Eliya", "tea": "Hatton Plantation OP", "elevation_m": 1271, "flavor": "Rich, balanced", "notes": "Gateway to tea country; plantation heritage"},
    {"name": "Deniyaya", "lat": 6.34, "lon": 80.55, "district": "Matara", "tea": "Sinharaja Buffer OP", "elevation_m": 460, "flavor": "Earthy, complex", "notes": "Adjacent to Sinharaja rainforest; biodiversity"},
    {"name": "Balangoda", "lat": 6.65, "lon": 80.70, "district": "Ratnapura", "tea": "Balangoda FBOP", "elevation_m": 600, "flavor": "Smooth, malty", "notes": "Ancient human history; Sabaragamuwa tea zone"},
    {"name": "Pussellawa", "lat": 7.11, "lon": 80.55, "district": "Kandy", "tea": "Mid-Grown Pussellawa", "elevation_m": 900, "flavor": "Moderate strength, aromatic", "notes": "Scenic route Kandy to Nuwara Eliya"},
    {"name": "Nawalapitiya", "lat": 7.05, "lon": 80.53, "district": "Kandy", "tea": "Nawalapitiya BOP", "elevation_m": 550, "flavor": "Strong body, dark liquor", "notes": "Transport hub for tea country; mid-grown"},
    {"name": "Agarapatana", "lat": 6.85, "lon": 80.63, "district": "Nuwara Eliya", "tea": "Agarapatana Premium OP", "elevation_m": 1400, "flavor": "Floral, light", "notes": "Remote high estate; exclusive micro-lot teas"},
    {"name": "Kelani Valley", "lat": 6.98, "lon": 80.45, "district": "Kegalle", "tea": "Kelani Valley FBOP", "elevation_m": 350, "flavor": "Bold, punchy", "notes": "River valley terroir; low-to-mid transition zone"},
    {"name": "Galaha", "lat": 7.17, "lon": 80.58, "district": "Kandy", "tea": "Galaha Silver Tips", "elevation_m": 1050, "flavor": "Subtle, sweet, silvery", "notes": "Premium white tea production; small batches"},
    {"name": "Dickoya", "lat": 6.88, "lon": 80.58, "district": "Nuwara Eliya", "tea": "Dickoya FBOPF Ex Sp", "elevation_m": 1300, "flavor": "Bright, citrusy", "notes": "Castlereagh reservoir views; high-quality factories"},
    {"name": "Talawakelle", "lat": 6.93, "lon": 80.65, "district": "Nuwara Eliya", "tea": "Talawakelle OP1", "elevation_m": 1200, "flavor": "Classic Ceylon, balanced", "notes": "St. Clair's Falls nearby; scenic estate roads"},
]

TEA_CEREMONY_TRADITIONS = [
    {"name": "Urasenke School, Kyoto", "lat": 35.03, "lon": 135.76, "country": "Japan", "tradition": "Chado (Way of Tea)", "style": "Matcha / Wabi-cha", "notes": "Most influential tea school; founded by Sen no Rikyu's grandson"},
    {"name": "Omotesenke School, Kyoto", "lat": 35.03, "lon": 135.75, "country": "Japan", "tradition": "Chado (Way of Tea)", "style": "Matcha / Thin tea focus", "notes": "Second major tea school; thinner whisked matcha"},
    {"name": "Mushanokoji-senke, Kyoto", "lat": 35.02, "lon": 135.76, "country": "Japan", "tradition": "Chado (Way of Tea)", "style": "Matcha / Intimate gatherings", "notes": "Third Sen family school; smallest and most intimate"},
    {"name": "Kinkaku-ji Tea Garden, Kyoto", "lat": 35.04, "lon": 135.73, "country": "Japan", "tradition": "Temple Tea", "style": "Matcha in Zen setting", "notes": "Golden Pavilion; Ashikaga-era tea aesthetics"},
    {"name": "Tai-an Teahouse, Oyamazaki", "lat": 34.90, "lon": 135.68, "country": "Japan", "tradition": "National Treasure Teahouse", "style": "Wabi-cha / 2-tatami room", "notes": "Only surviving teahouse by Sen no Rikyu; smallest"},
    {"name": "Gongfu Cha, Chaozhou", "lat": 23.66, "lon": 116.63, "country": "China", "tradition": "Gongfu Tea Ceremony", "style": "Oolong / Small-pot method", "notes": "Origin of kung fu tea; tiny cups, multiple infusions"},
    {"name": "Chinese Tea House, Yu Garden, Shanghai", "lat": 31.23, "lon": 121.49, "country": "China", "tradition": "Huxinting Teahouse", "style": "Shanghai-style service", "notes": "Oldest teahouse in Shanghai (1784); zigzag bridge"},
    {"name": "Lao She Teahouse, Beijing", "lat": 39.90, "lon": 116.39, "country": "China", "tradition": "Beijing Opera Tea", "style": "Performance tea culture", "notes": "Named after famous writer; opera, acrobatics & tea"},
    {"name": "Sichuan Teahouse Culture, Chengdu", "lat": 30.57, "lon": 104.07, "country": "China", "tradition": "Gaiwan Teahouse", "style": "Covered-bowl / Social tea", "notes": "Ear-cleaning, mahjong & tea; long-spout pouring"},
    {"name": "Moroccan Mint Tea, Marrakech", "lat": 31.63, "lon": -8.00, "country": "Morocco", "tradition": "Atay / Berber Tea", "style": "Gunpowder green + mint + sugar", "notes": "Poured from height for foam; symbol of hospitality"},
    {"name": "Fez Medina Teahouses", "lat": 34.06, "lon": -4.97, "country": "Morocco", "tradition": "Moroccan Tea Service", "style": "Silver teapot ceremony", "notes": "Served 3 glasses: bitter as life, sweet as love, gentle as death"},
    {"name": "Russian Samovar Tradition, Moscow", "lat": 55.75, "lon": 37.62, "country": "Russia", "tradition": "Samovar Tea", "style": "Zavarka concentrate + hot water", "notes": "Central to Russian social life; brass samovars since 1700s"},
    {"name": "Turkish Tea Gardens, Istanbul", "lat": 41.01, "lon": 28.98, "country": "Turkey", "tradition": "Cay Culture", "style": "Double teapot (caydanlik)", "notes": "Highest per-capita tea consumption; tulip glasses"},
    {"name": "Rize Tea Plantations", "lat": 41.02, "lon": 40.52, "country": "Turkey", "tradition": "Black Sea Cay", "style": "Turkish black tea", "notes": "Turkey's tea capital; steep green hillside gardens"},
    {"name": "British Afternoon Tea, London", "lat": 51.50, "lon": -0.14, "country": "UK", "tradition": "Afternoon Tea", "style": "Black tea + tiered service", "notes": "Started by Duchess of Bedford (1840s); scones, sandwiches"},
    {"name": "Darjeeling Tea Lounge", "lat": 27.04, "lon": 88.26, "country": "India", "tradition": "Colonial Hill Station Tea", "style": "First Flush tasting", "notes": "British Raj legacy; Himalayan tea tasting tradition"},
    {"name": "Chaiwala Culture, Mumbai", "lat": 19.08, "lon": 72.88, "country": "India", "tradition": "Masala Chai", "style": "Spiced milk tea / Street tea", "notes": "Ubiquitous street chai; cardamom, ginger, cinnamon"},
    {"name": "Taiwanese Gongfu, Taipei", "lat": 25.03, "lon": 121.53, "country": "Taiwan", "tradition": "Taiwanese Tea Art", "style": "High-mountain oolong ceremony", "notes": "Revival of Chinese gongfu; competition-style brewing"},
    {"name": "Maokong Tea Houses, Taipei", "lat": 24.97, "lon": 121.59, "country": "Taiwan", "tradition": "Mountain Teahouse", "style": "Oolong / Iron Goddess", "notes": "Gondola to mountaintop teahouses; Taipei night views"},
    {"name": "Korean Dado, Boseong", "lat": 34.77, "lon": 127.08, "country": "South Korea", "tradition": "Dado (Way of Tea)", "style": "Korean green tea ceremony", "notes": "Korea's largest tea plantation; Jeonnam province"},
    {"name": "Insadong Tea Street, Seoul", "lat": 37.57, "lon": 126.99, "country": "South Korea", "tradition": "Traditional Teahouse", "style": "Herbal & green teas", "notes": "Cultural district; traditional hanok teahouses"},
    {"name": "Persian Tea Culture, Isfahan", "lat": 32.65, "lon": 51.68, "country": "Iran", "tradition": "Chai-khaneh", "style": "Black tea with nabat (sugar)", "notes": "Teahouse culture central to social life; hookah & tea"},
    {"name": "Tibetan Butter Tea, Lhasa", "lat": 29.65, "lon": 91.10, "country": "Tibet/China", "tradition": "Po Cha", "style": "Yak butter + salt + tea", "notes": "Essential high-altitude drink; social bonding ritual"},
    {"name": "Sri Lankan Tea Tasting, Kandy", "lat": 7.29, "lon": 80.64, "country": "Sri Lanka", "tradition": "Estate Tea Tasting", "style": "Ceylon grading system", "notes": "Professional cupping; OP, BOP, FBOP grading ritual"},
    {"name": "Argentine Mate Circle, Buenos Aires", "lat": -34.60, "lon": -58.38, "country": "Argentina", "tradition": "Mate Ceremony", "style": "Yerba mate / Shared gourd", "notes": "Communal circle; bombilla straw; social bonding"},
    {"name": "Saharawi Tea Ritual, Western Sahara", "lat": 24.50, "lon": -13.00, "country": "Western Sahara", "tradition": "Atay Saharan", "style": "Three rounds of green tea", "notes": "Desert hospitality; three servings vary in strength"},
    {"name": "Thai Cha Yen Culture, Bangkok", "lat": 13.75, "lon": 100.50, "country": "Thailand", "tradition": "Thai Tea", "style": "Orange-hued iced milk tea", "notes": "Street stall staple; Ceylon tea with condensed milk"},
    {"name": "Hong Kong Milk Tea, Kowloon", "lat": 22.32, "lon": 114.17, "country": "Hong Kong", "tradition": "Silk Stocking Milk Tea", "style": "Strong black tea + evaporated milk", "notes": "Strained through cloth; dai pai dong tradition"},
    {"name": "East Frisian Tea, Leer", "lat": 53.23, "lon": 7.46, "country": "Germany", "tradition": "Ostfriesentee", "style": "Strong black + cream + kluntje", "notes": "UNESCO intangible heritage; three-layer tasting"},
    {"name": "Myanmar Laphet Thoke, Yangon", "lat": 16.87, "lon": 96.20, "country": "Myanmar", "tradition": "Pickled Tea Leaf Salad", "style": "Fermented tea leaves eaten", "notes": "Tea as food; social offering; peace-making dish"},
]

HISTORIC_TEA_TRADE_ROUTES = [
    {"name": "Canton (Guangzhou) - Export Hub", "lat": 23.13, "lon": 113.26, "route": "Maritime Tea Route", "era": "1600s-1800s", "notes": "Main port for tea exports to Europe; Thirteen Factories"},
    {"name": "Fuzhou - Black Tea Port", "lat": 26.07, "lon": 119.30, "route": "Maritime Tea Route", "era": "1840s-1900s", "notes": "Treaty port for Fujian black tea exports"},
    {"name": "London Tea Auction, Mincing Lane", "lat": 51.51, "lon": -0.08, "route": "Maritime Tea Route", "era": "1679-1998", "notes": "World tea trading center for 300 years; Plantation House"},
    {"name": "Boston Harbor - Tea Party", "lat": 42.35, "lon": -71.05, "route": "Maritime Tea Route", "era": "1773", "notes": "342 chests of tea dumped; sparked American Revolution"},
    {"name": "Amsterdam - VOC Tea Trade", "lat": 52.37, "lon": 4.90, "route": "Maritime Tea Route", "era": "1610-1800s", "notes": "First European tea imports; Dutch East India Company"},
    {"name": "Puer City, Yunnan", "lat": 22.78, "lon": 100.97, "route": "Tea Horse Road (Southern)", "era": "7th century-1950s", "notes": "Starting point; tea compressed into cakes for transport"},
    {"name": "Dali, Yunnan", "lat": 25.60, "lon": 100.23, "route": "Tea Horse Road", "era": "Tang Dynasty onward", "notes": "Major waystation; Bai minority tea-horse market"},
    {"name": "Lijiang, Yunnan", "lat": 26.87, "lon": 100.23, "route": "Tea Horse Road", "era": "Song Dynasty onward", "notes": "Naxi trading town; UNESCO World Heritage crossroads"},
    {"name": "Shangri-La (Zhongdian)", "lat": 27.83, "lon": 99.70, "route": "Tea Horse Road", "era": "Ancient-1950s", "notes": "High pass gateway; Tibetan-Chinese tea exchange"},
    {"name": "Lhasa, Tibet", "lat": 29.65, "lon": 91.17, "route": "Tea Horse Road", "era": "7th century onward", "notes": "Destination for Sichuan/Yunnan tea; butter tea culture"},
    {"name": "Ya'an, Sichuan", "lat": 29.98, "lon": 103.00, "route": "Tea Horse Road (Northern)", "era": "Tang Dynasty onward", "notes": "Sichuan route origin; brick tea for Tibet trade"},
    {"name": "Kangding, Sichuan", "lat": 30.05, "lon": 101.97, "route": "Tea Horse Road (Northern)", "era": "Song-Qing Dynasty", "notes": "Love Song City; critical Sino-Tibetan trade gateway"},
    {"name": "Kolkata (Calcutta) Port", "lat": 22.57, "lon": 88.35, "route": "British India Tea Route", "era": "1830s-present", "notes": "Assam & Darjeeling tea exports; auction center"},
    {"name": "Colombo Port", "lat": 6.93, "lon": 79.84, "route": "Ceylon Tea Route", "era": "1870s-present", "notes": "Ceylon tea export hub; Colombo Tea Traders' Assoc."},
    {"name": "Yokohama Port", "lat": 35.44, "lon": 139.64, "route": "Japanese Tea Route", "era": "1859-present", "notes": "First Japanese tea exports to West; silk & tea trade"},
    {"name": "Mombasa, Kenya", "lat": -4.05, "lon": 39.67, "route": "African Tea Route", "era": "1920s-present", "notes": "World's largest tea auction by volume since 1957"},
    {"name": "Suez Canal", "lat": 30.43, "lon": 32.35, "route": "Maritime Tea Route", "era": "1869-present", "notes": "Shortened Asia-Europe tea route by 4,300 miles"},
    {"name": "Cape Town - Tea Clipper Stop", "lat": -33.92, "lon": 18.42, "route": "Clipper Ship Route", "era": "1840s-1870s", "notes": "Resupply point for tea clippers racing to London"},
    {"name": "Xiamen (Amoy)", "lat": 24.48, "lon": 118.09, "route": "Maritime Tea Route", "era": "1684-1900s", "notes": "Fujian oolong export port; word 'tea' from Amoy dialect"},
    {"name": "Macau - Portuguese Tea Trade", "lat": 22.20, "lon": 113.55, "route": "Maritime Tea Route", "era": "1550s-1800s", "notes": "First European tea contact; Catherine of Braganza"},
    {"name": "Odessa - Russian Tea Import", "lat": 46.48, "lon": 30.73, "route": "Russian Tea Route", "era": "1800s", "notes": "Black Sea port for Chinese tea via caravan and ship"},
    {"name": "Kyakhta, Russia-Mongolia Border", "lat": 50.36, "lon": 106.45, "route": "Russian Caravan Tea Route", "era": "1727-1860s", "notes": "China-Russia tea-for-furs trade; Caravan Tea origin"},
    {"name": "Nizhny Novgorod Fair", "lat": 56.33, "lon": 43.97, "route": "Russian Tea Route", "era": "1700s-1900s", "notes": "Largest tea bazaar in Russia; annual trade fair"},
    {"name": "Chittagong Port", "lat": 22.33, "lon": 91.83, "route": "Bengal Tea Route", "era": "1860s-present", "notes": "Bangladesh tea exports; Sylhet tea auction feeder"},
    {"name": "Singapore - Entrepot", "lat": 1.35, "lon": 103.82, "route": "Maritime Tea Route", "era": "1819-present", "notes": "Redistribution hub for Southeast Asian tea trade"},
    {"name": "Nagasaki - Dutch Tea Trade", "lat": 32.75, "lon": 129.88, "route": "Japanese Tea Route", "era": "1641-1854", "notes": "Only port open to Dutch; early tea exports via Dejima"},
    {"name": "Hamburg - European Tea Hub", "lat": 53.55, "lon": 10.00, "route": "European Tea Route", "era": "1600s-present", "notes": "Major European tea import port; blending center"},
    {"name": "Galle Fort, Sri Lanka", "lat": 6.03, "lon": 80.22, "route": "Ceylon Tea Route", "era": "1600s-1900s", "notes": "Colonial spice & tea port; Dutch-British trade"},
    {"name": "Antwerp - Tea Re-export", "lat": 51.22, "lon": 4.40, "route": "European Tea Route", "era": "1600s-present", "notes": "Belgian tea blending and re-export center"},
    {"name": "Darjeeling Railway Hub", "lat": 27.04, "lon": 88.26, "route": "British India Tea Route", "era": "1881-present", "notes": "Toy train carried tea down to Siliguri; UNESCO railway"},
]

AFRICAN_TEA_GROWING = [
    {"name": "Kericho, Kenya", "lat": -0.37, "lon": 35.28, "country": "Kenya", "tea": "Kenyan CTC Black", "elevation_m": 2000, "notes": "World's 3rd largest producer; year-round harvesting"},
    {"name": "Nandi Hills, Kenya", "lat": 0.10, "lon": 35.18, "country": "Kenya", "tea": "Nandi Highland CTC", "elevation_m": 1800, "notes": "Equatorial highlands; consistent quality"},
    {"name": "Mount Kenya Slopes", "lat": -0.15, "lon": 37.30, "country": "Kenya", "tea": "Mt. Kenya Purple Tea", "elevation_m": 2100, "notes": "Unique anthocyanin-rich purple cultivar (TRFK 306)"},
    {"name": "Limuru, Kiambu", "lat": -1.10, "lon": 36.65, "country": "Kenya", "tea": "Limuru Green", "elevation_m": 2200, "notes": "Near Nairobi; premium green tea production"},
    {"name": "Mulanje Mountain, Malawi", "lat": -15.93, "lon": 35.65, "country": "Malawi", "tea": "Malawi Black CTC", "elevation_m": 900, "notes": "Africa's oldest tea industry (1878); Satemwa Estate"},
    {"name": "Thyolo, Malawi", "lat": -16.07, "lon": 35.17, "country": "Malawi", "tea": "Thyolo Orthodox Black", "elevation_m": 800, "notes": "Premium orthodox production; small-holder focus"},
    {"name": "Lushoto, Tanzania", "lat": -4.78, "lon": 38.28, "country": "Tanzania", "tea": "Usambara Highland", "elevation_m": 1400, "notes": "Usambara Mountains; German colonial plantings"},
    {"name": "Mufindi, Tanzania", "lat": -8.63, "lon": 35.30, "country": "Tanzania", "tea": "Mufindi Green & Black", "elevation_m": 1800, "notes": "Southern Highlands; Unilever origins; Luponde estate"},
    {"name": "Gisenyi, Rwanda", "lat": -1.70, "lon": 29.26, "country": "Rwanda", "tea": "Rwanda Highland CTC", "elevation_m": 1700, "notes": "Thousand hills terroir; post-conflict recovery crop"},
    {"name": "Nyungwe Forest Edge, Rwanda", "lat": -2.43, "lon": 29.25, "country": "Rwanda", "tea": "Nyungwe Hand-Rolled", "elevation_m": 2000, "notes": "Rainforest-adjacent; artisanal white tea"},
    {"name": "Teza, Burundi", "lat": -3.33, "lon": 29.62, "country": "Burundi", "tea": "Burundi Highland", "elevation_m": 1800, "notes": "Small but growing industry; cooperative model"},
    {"name": "Cyangugu, Rwanda", "lat": -2.48, "lon": 28.90, "country": "Rwanda", "tea": "Cyangugu Premium CTC", "elevation_m": 1600, "notes": "Lake Kivu shores; volcanic soil richness"},
    {"name": "Cameroon Highlands, Tole", "lat": 4.12, "lon": 9.23, "country": "Cameroon", "tea": "Cameroon Black CTC", "elevation_m": 800, "notes": "Mt. Cameroon slopes; Tole Tea Estate since 1954"},
    {"name": "Chipinge, Zimbabwe", "lat": -20.19, "lon": 32.63, "country": "Zimbabwe", "tea": "Zimbabwe Highveld", "elevation_m": 1100, "notes": "Eastern Highlands; Tanganda Tea Company"},
    {"name": "Limpopo, South Africa", "lat": -23.40, "lon": 30.05, "country": "South Africa", "tea": "South African Black", "elevation_m": 600, "notes": "Sapekoe Estate; southernmost conventional tea"},
    {"name": "Tzaneen, Limpopo", "lat": -23.83, "lon": 30.17, "country": "South Africa", "tea": "Tzaneen CTC", "elevation_m": 700, "notes": "Subtropical Limpopo valley; robust character"},
    {"name": "Rize-like Slopes, Ethiopia", "lat": 7.00, "lon": 36.50, "country": "Ethiopia", "tea": "Ethiopian Highland", "elevation_m": 1800, "notes": "Jimma zone; emerging specialty tea origin"},
    {"name": "Nandi County Smallholders, Kenya", "lat": 0.17, "lon": 35.10, "country": "Kenya", "tea": "Smallholder KTDA Tea", "elevation_m": 1900, "notes": "650,000+ small farmers via KTDA cooperative"},
    {"name": "Njombe, Tanzania", "lat": -9.33, "lon": 34.77, "country": "Tanzania", "tea": "Njombe CTC Black", "elevation_m": 1900, "notes": "Southern highlands; Lupembe Tea Estate"},
    {"name": "Sotik, Bomet County, Kenya", "lat": -0.68, "lon": 35.12, "country": "Kenya", "tea": "Sotik Highland", "elevation_m": 1850, "notes": "Bomet tea belt; strong malty character"},
    {"name": "Rungwe, Tanzania", "lat": -9.13, "lon": 33.67, "country": "Tanzania", "tea": "Rungwe Volcanic Tea", "elevation_m": 1600, "notes": "Near Mt. Rungwe volcano; mineral-rich soil"},
    {"name": "Kibuye, Rwanda", "lat": -2.06, "lon": 29.35, "country": "Rwanda", "tea": "Kibuye Green", "elevation_m": 1700, "notes": "Lake Kivu terraces; premium green tea trials"},
    {"name": "Ugandan Tea Estates, Fort Portal", "lat": 0.66, "lon": 30.27, "country": "Uganda", "tea": "Ugandan CTC Black", "elevation_m": 1500, "notes": "Rwenzori foothills; Toro kingdom heritage"},
    {"name": "Tooro Tea, Kabarole", "lat": 0.60, "lon": 30.25, "country": "Uganda", "tea": "Tooro Mountain Tea", "elevation_m": 1400, "notes": "Mountains of the Moon; emerging specialty origin"},
    {"name": "Mozambique, Gurue", "lat": -15.45, "lon": 37.02, "country": "Mozambique", "tea": "Gurue Highland", "elevation_m": 1000, "notes": "Mt. Namuli; Portuguese colonial era plantings reviving"},
]

SOUTH_AMERICAN_YERBA_MATE = [
    {"name": "Misiones Province, Argentina", "lat": -27.37, "lon": -55.90, "country": "Argentina", "product": "Yerba Mate (Ilex paraguariensis)", "type": "Traditional Mate", "notes": "Argentina's main production zone; red laterite soil"},
    {"name": "Corrientes Province, Argentina", "lat": -28.47, "lon": -58.83, "country": "Argentina", "product": "Yerba Mate con Palo", "type": "Traditional Mate", "notes": "Gentler flavor; includes stems (con palo)"},
    {"name": "Obera, Misiones", "lat": -27.48, "lon": -55.13, "country": "Argentina", "product": "Obera Select Mate", "type": "Premium Mate", "notes": "Annual Mate Festival; immigrant agricultural heritage"},
    {"name": "Apostoles, Misiones", "lat": -27.91, "lon": -55.75, "country": "Argentina", "product": "Apostoles Organic Mate", "type": "Organic Mate", "notes": "Ukrainian-Polish settlers; cooperative model"},
    {"name": "Parana State, Brazil", "lat": -24.95, "lon": -51.50, "country": "Brazil", "product": "Chimarrao", "type": "Green Mate", "notes": "Fine-ground fresh green mate; Southern Brazilian style"},
    {"name": "Santa Catarina, Brazil", "lat": -27.25, "lon": -50.23, "country": "Brazil", "product": "Erva-Mate Catarina", "type": "Green Mate", "notes": "Atlantic Forest region; shade-grown native mate"},
    {"name": "Rio Grande do Sul, Brazil", "lat": -29.17, "lon": -54.90, "country": "Brazil", "product": "Gaucho Chimarrao", "type": "Green Mate", "notes": "Gaucho culture; cuia gourd & bomba straw"},
    {"name": "Mato Grosso do Sul, Brazil", "lat": -22.23, "lon": -54.80, "country": "Brazil", "product": "Terere (Iced Mate)", "type": "Cold Mate", "notes": "Iced mate with herbs; Guarani influence"},
    {"name": "Amambay, Paraguay", "lat": -22.55, "lon": -56.00, "country": "Paraguay", "product": "Ka'a (Guarani Mate)", "type": "Traditional Mate", "notes": "Birthplace of mate; indigenous Guarani cultivation"},
    {"name": "Itapua, Paraguay", "lat": -27.00, "lon": -55.83, "country": "Paraguay", "product": "Paraguayan Organic Mate", "type": "Organic Mate", "notes": "Jesuit mission heritage; forest-grown mate"},
    {"name": "San Pedro Department, Paraguay", "lat": -24.10, "lon": -56.60, "country": "Paraguay", "product": "San Pedro Yerba", "type": "Traditional Mate", "notes": "Small-farm production; terere with cold water"},
    {"name": "Canindeyú, Paraguay", "lat": -24.05, "lon": -55.67, "country": "Paraguay", "product": "Wild Forest Mate", "type": "Wild Harvest", "notes": "Native forest yerba; Mbaracayu reserve adjacent"},
    {"name": "Tacuarembo, Uruguay", "lat": -31.72, "lon": -55.98, "country": "Uruguay", "product": "Uruguayan Mate", "type": "Traditional Mate", "notes": "Highest per-capita mate consumption in the world"},
    {"name": "Montevideo", "lat": -34.90, "lon": -56.19, "country": "Uruguay", "product": "Urban Mate Culture", "type": "Social Mate", "notes": "Everyone carries mate and thermos; national identity"},
    {"name": "Rivera, Uruguay", "lat": -30.90, "lon": -55.53, "country": "Uruguay", "product": "Rivera Border Mate", "type": "Traditional Mate", "notes": "Brazil-Uruguay border; blended mate traditions"},
    {"name": "Trinidad Jesuit Mission, Paraguay", "lat": -27.13, "lon": -55.72, "country": "Paraguay", "product": "Mission-era Yerba", "type": "Heritage", "notes": "UNESCO ruins; Jesuits organized first mate plantations"},
    {"name": "Curitiba, Parana", "lat": -25.43, "lon": -49.27, "country": "Brazil", "product": "Curitiba Mate Parks", "type": "Urban Culture", "notes": "Mate consumption in city parks; cultural icon of Parana"},
    {"name": "San Ignacio Mini, Argentina", "lat": -27.26, "lon": -55.53, "country": "Argentina", "product": "Jesuit Heritage Mate", "type": "Heritage", "notes": "UNESCO Jesuit ruins; mate trade history center"},
    {"name": "Posadas, Misiones", "lat": -27.37, "lon": -55.90, "country": "Argentina", "product": "Misiones Provincial Mate", "type": "Traditional Mate", "notes": "Provincial capital; Mate Route tourism"},
    {"name": "Florianopolis, Brazil", "lat": -27.60, "lon": -48.55, "country": "Brazil", "product": "Floripa Beach Mate", "type": "Cold Mate", "notes": "Beach terere culture; iced mate with fruit"},
    {"name": "Eldorado, Misiones", "lat": -26.40, "lon": -54.63, "country": "Argentina", "product": "Eldorado Plantation Mate", "type": "Estate Mate", "notes": "German settler plantations; Rosamonte brand origin"},
    {"name": "Iguazu Falls Region", "lat": -25.69, "lon": -54.44, "country": "Argentina/Brazil", "product": "Triple Frontier Mate", "type": "Cross-border", "notes": "Mate unites 3 nations; tourist mate experiences"},
    {"name": "Concepcion, Paraguay", "lat": -23.40, "lon": -57.43, "country": "Paraguay", "product": "Northern Paraguayan Yerba", "type": "Traditional Mate", "notes": "Rio Paraguay commerce; historical mate transport"},
    {"name": "Yaboty Biosphere, Misiones", "lat": -27.10, "lon": -53.90, "country": "Argentina", "product": "Rainforest Shade Mate", "type": "Shade-Grown", "notes": "Atlantic Forest reserve; barbacua-dried mate"},
    {"name": "Caa Pora, Misiones", "lat": -27.80, "lon": -55.40, "country": "Argentina", "product": "Caa Pora Heritage Mate", "type": "Heritage", "notes": "Name means 'beautiful herb' in Guarani; origin area"},
]

TEA_MUSEUMS_AND_HERITAGE = [
    {"name": "China National Tea Museum, Hangzhou", "lat": 30.23, "lon": 120.12, "country": "China", "type": "Museum", "notes": "Only national-level tea museum; Longjing area; 5 exhibit halls"},
    {"name": "UK Tea & Coffee Museum (former), London", "lat": 51.50, "lon": -0.07, "country": "UK", "type": "Heritage Site", "notes": "Bramah Museum legacy; British tea history since 1650s"},
    {"name": "Tata Tea Museum, Munnar", "lat": 10.09, "lon": 77.06, "country": "India", "type": "Museum", "notes": "Colonial-era machinery; Kannan Devan Hills history"},
    {"name": "Ceylon Tea Museum, Kandy", "lat": 7.26, "lon": 80.62, "country": "Sri Lanka", "type": "Museum", "notes": "Hantane Estate factory; James Taylor exhibits"},
    {"name": "James Taylor's Bungalow, Loolecondra", "lat": 7.24, "lon": 80.60, "country": "Sri Lanka", "type": "Heritage Site", "notes": "Father of Ceylon tea (1867); first tea planted here"},
    {"name": "Urasenke Tea Museum, Kyoto", "lat": 35.03, "lon": 135.76, "country": "Japan", "type": "Museum", "notes": "Konnichian tearoom; Sen family treasures since 1600s"},
    {"name": "Shizuoka Tea Museum, O-Cha no Sato", "lat": 34.82, "lon": 138.13, "country": "Japan", "type": "Museum", "notes": "World tea cultures; panoramic tea field views"},
    {"name": "Boseong Tea Museum, South Korea", "lat": 34.77, "lon": 127.08, "country": "South Korea", "type": "Museum", "notes": "Korean green tea heritage; photogenic terraced fields"},
    {"name": "Makaibari Tea Museum, Darjeeling", "lat": 27.05, "lon": 88.28, "country": "India", "type": "Museum", "notes": "World's first tea factory (1859); biodynamic pioneer"},
    {"name": "Boston Tea Party Ships & Museum", "lat": 42.35, "lon": -71.05, "country": "USA", "type": "Museum", "notes": "Interactive re-enactment; floating museum on Congress St. Bridge"},
    {"name": "Twining's Tea Shop, London", "lat": 51.51, "lon": -0.11, "country": "UK", "type": "Heritage Shop", "notes": "Oldest tea shop (1706); Strand; 300+ years continuous trade"},
    {"name": "Fortnum & Mason, London", "lat": 51.51, "lon": -0.14, "country": "UK", "type": "Heritage Shop", "notes": "Royal warrant since 1707; iconic Piccadilly tea hall"},
    {"name": "Mariage Freres Museum, Paris", "lat": 48.86, "lon": 2.36, "country": "France", "type": "Museum", "notes": "French tea history since 1854; Le Marais; 500+ teas"},
    {"name": "Robert Bruce Discovery Site, Assam", "lat": 26.98, "lon": 95.32, "country": "India", "type": "Heritage Site", "notes": "Scottish adventurer found native tea plants (1823)"},
    {"name": "Dilmah Tea Innovation Centre, Sri Lanka", "lat": 6.88, "lon": 79.90, "country": "Sri Lanka", "type": "Museum/Centre", "notes": "Modern tea science; Merrill J. Fernando's legacy"},
    {"name": "Ten Ren Tea Museum, Taipei", "lat": 25.04, "lon": 121.53, "country": "Taiwan", "type": "Museum", "notes": "Taiwanese tea art; oolong expertise since 1953"},
    {"name": "Lipton's Seat, Haputale", "lat": 6.78, "lon": 80.93, "country": "Sri Lanka", "type": "Heritage Viewpoint", "notes": "Sir Thomas Lipton's panoramic tea estate viewpoint"},
    {"name": "Darjeeling Himalayan Railway Museum", "lat": 27.04, "lon": 88.26, "country": "India", "type": "Heritage", "notes": "UNESCO; toy train built for tea transport (1881)"},
    {"name": "Tea Horse Road Museum, Lijiang", "lat": 26.87, "lon": 100.23, "country": "China", "type": "Museum", "notes": "Ancient caravan route artifacts; Naxi culture center"},
    {"name": "Menghai Tea Factory (TAETEA), Yunnan", "lat": 21.96, "lon": 100.45, "country": "China", "type": "Heritage Factory", "notes": "Est. 1940; birthplace of modern pu-erh production"},
    {"name": "Ahmad Tea Heritage Museum, London", "lat": 51.44, "lon": -0.21, "country": "UK", "type": "Museum", "notes": "Family tea blending history; Ceylon & Assam focus"},
    {"name": "Tea Museum, Macao", "lat": 22.20, "lon": 113.55, "country": "Macau", "type": "Museum", "notes": "Portuguese-Chinese tea trade; 400+ years of exchange"},
    {"name": "Korean Tea Culture Park, Boseong", "lat": 34.76, "lon": 127.07, "country": "South Korea", "type": "Heritage Park", "notes": "Open-air tea fields; traditional dado demonstrations"},
    {"name": "Samovar Museum, Tula", "lat": 54.20, "lon": 37.62, "country": "Russia", "type": "Museum", "notes": "500+ samovars; Russian tea-drinking culture history"},
    {"name": "Happy Valley Tea Estate Heritage Tour", "lat": 27.04, "lon": 88.26, "country": "India", "type": "Heritage Tour", "notes": "Factory walk-through; orthodox production since 1854"},
]

FAMOUS_TEAHOUSES = [
    {"name": "Maison de The Mariage Freres, Paris", "lat": 48.86, "lon": 2.36, "country": "France", "style": "French Salon de The", "est": "1854", "notes": "500+ teas; colonial-era elegance; Le Marais district"},
    {"name": "TWG Tea Salon, Marina Bay, Singapore", "lat": 1.28, "lon": 103.86, "country": "Singapore", "style": "Luxury Tea Salon", "est": "2008", "notes": "800+ single-estate teas; opulent colonial decor"},
    {"name": "Claridge's, London", "lat": 51.51, "lon": -0.15, "country": "UK", "style": "Luxury Afternoon Tea", "est": "1856", "notes": "Art Deco grandeur; champagne afternoon tea"},
    {"name": "The Ritz, London", "lat": 51.51, "lon": -0.14, "country": "UK", "style": "Classic Afternoon Tea", "est": "1906", "notes": "Palm Court; most iconic British afternoon tea"},
    {"name": "Bettys, Harrogate", "lat": 53.99, "lon": -1.54, "country": "UK", "style": "Yorkshire Tea Room", "est": "1919", "notes": "Swiss-Yorkshire fusion; Frederick Belmont's legacy"},
    {"name": "Ippodo Tea, Kyoto", "lat": 35.01, "lon": 135.77, "country": "Japan", "style": "Traditional Matcha Bar", "est": "1717", "notes": "300+ year lineage; Teramachi street; prepare your own matcha"},
    {"name": "Camellia Sinensis, Montreal", "lat": 45.52, "lon": -73.57, "country": "Canada", "style": "Specialty Tea House", "est": "2003", "notes": "Direct-import rarities; education-focused tasting bar"},
    {"name": "Samovar Tea Lounge, San Francisco", "lat": 37.77, "lon": -122.42, "country": "USA", "style": "Modern Zen Teahouse", "est": "2001", "notes": "Yerba Buena; meditation & tea; Asian-fusion pairing"},
    {"name": "Huxinting Teahouse, Shanghai", "lat": 31.23, "lon": 121.49, "country": "China", "style": "Classical Chinese", "est": "1784", "notes": "Mid-lake pavilion; zigzag bridge; Yu Garden"},
    {"name": "Lao She Teahouse, Beijing", "lat": 39.90, "lon": 116.39, "country": "China", "style": "Performance Teahouse", "est": "1988", "notes": "Opera, acrobatics & tea; cultural landmark"},
    {"name": "Hexi Corridor Tea Room, Chengdu", "lat": 30.66, "lon": 104.07, "country": "China", "style": "Sichuan Gaiwan House", "est": "Traditional", "notes": "Bamboo chairs; ear-cleaning; covered-bowl tea"},
    {"name": "Smith & Hsu, Taipei", "lat": 25.04, "lon": 121.54, "country": "Taiwan", "style": "Modern Tea Salon", "est": "2005", "notes": "Minimalist design; Taiwanese & European tea sets"},
    {"name": "Babington's Tea Rooms, Rome", "lat": 41.91, "lon": 12.48, "country": "Italy", "style": "English Tea Room", "est": "1893", "notes": "Spanish Steps; run by founding family descendants"},
    {"name": "Tea Chapter, Singapore", "lat": 1.28, "lon": 103.84, "country": "Singapore", "style": "Chinese Gongfu House", "est": "1989", "notes": "Queen Elizabeth II visited; Tanjong Pagar shophouse"},
    {"name": "Dobra Tea, Burlington VT", "lat": 44.48, "lon": -73.21, "country": "USA", "style": "Czech-Global Teahouse", "est": "2005", "notes": "100+ loose teas; floor-seating rooms; world tea culture"},
    {"name": "Yojiya Cafe, Kyoto", "lat": 35.00, "lon": 135.78, "country": "Japan", "style": "Matcha Cafe", "est": "2003", "notes": "Gion geisha district; matcha latte art; garden views"},
    {"name": "Cafe Sabarsky, New York", "lat": 40.78, "lon": -73.96, "country": "USA", "style": "Viennese Tea Cafe", "est": "2001", "notes": "Neue Galerie; Klimt-adjacent; Viennese sachertorte & tea"},
    {"name": "La Mosquee de Paris Tearoom", "lat": 48.84, "lon": 2.36, "country": "France", "style": "Moorish Mint Tea", "est": "1926", "notes": "Courtyard fountain; Moroccan mint tea & pastries"},
    {"name": "Cha House, Hong Kong", "lat": 22.28, "lon": 114.15, "country": "Hong Kong", "style": "Modern Chinese Tea", "est": "2010", "notes": "Flagstaff House Museum of Tea Ware; park setting"},
    {"name": "t Zonnetje, Amsterdam", "lat": 52.37, "lon": 4.88, "country": "Netherlands", "style": "Dutch Tearoom", "est": "1930", "notes": "Canal-side; oldest Amsterdam tearoom; 200 blends"},
    {"name": "Palais des Thes, Paris", "lat": 48.85, "lon": 2.36, "country": "France", "style": "French Tea Boutique", "est": "1987", "notes": "Direct sourcing from 30 countries; Le Marais flagship"},
    {"name": "Postcard Teas, London", "lat": 51.51, "lon": -0.14, "country": "UK", "style": "Single-Origin Micro-shop", "est": "2005", "notes": "Dering Street; tiny shop; farmer-direct rare teas"},
    {"name": "Lucky Chan Tea House, Chiang Mai", "lat": 18.79, "lon": 98.98, "country": "Thailand", "style": "Northern Thai Tea House", "est": "2012", "notes": "Lanna-style wooden house; Thai oolong & matcha"},
    {"name": "In Pursuit of Tea Tasting Room, NYC", "lat": 40.72, "lon": -74.00, "country": "USA", "style": "Gongfu Tasting Bar", "est": "1999", "notes": "Tribeca; sourcing trips to China & Japan; rare oolongs"},
    {"name": "Song Fang Maison de The, Shanghai", "lat": 31.22, "lon": 121.47, "country": "China", "style": "French-Chinese Fusion", "est": "2009", "notes": "Old French Concession; beautiful packaging; 100+ Chinese teas"},
    {"name": "Cafe Central, Vienna", "lat": 48.21, "lon": 16.37, "country": "Austria", "style": "Viennese Kaffeehaus", "est": "1876", "notes": "Habsburg-era grandeur; tea selection alongside coffee culture"},
    {"name": "Jugetsudo, Paris", "lat": 48.85, "lon": 2.33, "country": "France", "style": "Japanese Tea Bar", "est": "2008", "notes": "Maruyama Nori since 1854; Saint-Germain; gyokuro & matcha"},
    {"name": "The Lanesborough, London", "lat": 51.50, "lon": -0.15, "country": "UK", "style": "Luxury Afternoon Tea", "est": "1991", "notes": "Regency splendour; Peggy Porschen pastries & rare Darjeeling"},
    {"name": "Nan Lian Garden Tea House, Hong Kong", "lat": 22.34, "lon": 114.20, "country": "Hong Kong", "style": "Tang Dynasty Style", "est": "2006", "notes": "Chi Lin Nunnery complex; lotus pond; Song-dynasty ceramics"},
    {"name": "Harney & Sons SoHo, New York", "lat": 40.72, "lon": -74.00, "country": "USA", "style": "American Tea Tasting Room", "est": "2010", "notes": "Master blender family; 300+ blends; Victorian-modern"},
]


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def _make_popup(title, fields):
    """Build a styled HTML popup string for folium markers."""
    safe_title = html_module.escape(str(title))
    rows = ""
    for label, value in fields:
        safe_val = html_module.escape(str(value))
        rows += f"<tr><td style='padding:2px 6px;font-weight:600;color:#06b6d4;'>{html_module.escape(str(label))}</td><td style='padding:2px 6px;color:#e8ecf4;'>{safe_val}</td></tr>"
    return f"""
    <div style="font-family:'Segoe UI',system-ui,sans-serif;background:#1a2235;border:1px solid #2a3550;border-radius:8px;padding:10px;min-width:220px;max-width:320px;">
        <div style="font-size:13px;font-weight:700;color:#10b981;margin-bottom:6px;border-bottom:1px solid #2a3550;padding-bottom:4px;">{safe_title}</div>
        <table style="font-size:11px;border-collapse:collapse;">{rows}</table>
    </div>"""


def _create_map(data, lat_key="lat", lon_key="lon", popup_fn=None, color="#10b981", zoom=4, center=None):
    """Create a folium map from a list of dicts."""
    if not data:
        return None
    if center is None:
        avg_lat = sum(d[lat_key] for d in data) / len(data)
        avg_lon = sum(d[lon_key] for d in data) / len(data)
        center = [avg_lat, avg_lon]
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")
    for item in data:
        popup_html = popup_fn(item) if popup_fn else html_module.escape(str(item.get("name", "")))
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=html_module.escape(str(item.get("name", ""))),
        ).add_to(m)
    return m


def _render_map(m):
    """Render a folium map inside Streamlit."""
    if m is not None:
        st_html(m._repr_html_(), height=500)
    else:
        st.warning("No data to display on the map.")


def _show_download(df, filename_prefix):
    """Provide a CSV download button."""
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{filename_prefix}.csv",
        mime="text/csv",
        key=f"dl_{filename_prefix}",
    )


# ========================================================================
# MODE RENDERERS
# ========================================================================

def _render_chinese_tea():
    data = CHINESE_TEA_REGIONS
    provinces = sorted(set(d["province"] for d in data))
    types = sorted(set(d["type"] for d in data))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tea Regions", len(data))
    c2.metric("Provinces", len(provinces))
    c3.metric("Tea Types", len(types))
    c4.metric("Avg Elevation", f"{int(sum(d['elevation_m'] for d in data)/len(data))}m")

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Tea", d["tea"]),
            ("Type", d["type"]),
            ("Province", d["province"]),
            ("Elevation", f"{d['elevation_m']}m"),
            ("Notes", d["notes"]),
        ])

    type_colors = {"Green": "#22c55e", "Black": "#8b5cf6", "Oolong": "#f59e0b",
                   "White": "#e2e8f0", "Pu-erh": "#b45309", "Yellow": "#facc15",
                   "Dark": "#78716c"}
    m = folium.Map(location=[28, 105], zoom_start=5, tiles="CartoDB dark_matter")
    for item in data:
        clr = type_colors.get(item["type"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "chinese_tea_regions")


def _render_japanese_tea():
    data = JAPANESE_TEA_GARDENS
    regions = sorted(set(d["region"] for d in data))
    types = sorted(set(d["type"] for d in data))

    c1, c2, c3 = st.columns(3)
    c1.metric("Tea Gardens", len(data))
    c2.metric("Regions", len(regions))
    c3.metric("Tea Styles", len(types))

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Tea", d["tea"]),
            ("Type", d["type"]),
            ("Region", d["region"]),
            ("Notes", d["notes"]),
        ])

    region_colors = {"Kansai": "#22c55e", "Chubu": "#06b6d4", "Kyushu": "#f59e0b",
                     "Kanto": "#8b5cf6", "Shikoku": "#ec4899"}
    m = folium.Map(location=[35, 136], zoom_start=6, tiles="CartoDB dark_matter")
    for item in data:
        clr = region_colors.get(item["region"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "japanese_tea_gardens")


def _render_indian_tea():
    data = INDIAN_TEA_ESTATES
    states = sorted(set(d["state"] for d in data))
    types = sorted(set(d["type"] for d in data))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tea Estates", len(data))
    c2.metric("States", len(states))
    c3.metric("Tea Types", len(types))
    c4.metric("Max Elevation", f"{max(d['elevation_m'] for d in data)}m")

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Tea", d["tea"]),
            ("Type", d["type"]),
            ("State", d["state"]),
            ("Elevation", f"{d['elevation_m']}m"),
            ("Notes", d["notes"]),
        ])

    state_colors = {"West Bengal": "#f59e0b", "Assam": "#ef4444", "Kerala": "#22c55e",
                    "Tamil Nadu": "#8b5cf6", "Himachal Pradesh": "#06b6d4",
                    "Sikkim": "#ec4899", "Tripura": "#a855f7"}
    m = folium.Map(location=[22, 82], zoom_start=5, tiles="CartoDB dark_matter")
    for item in data:
        clr = state_colors.get(item["state"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "indian_tea_estates")


def _render_sri_lankan_tea():
    data = SRI_LANKAN_TEA_HIGHLANDS
    districts = sorted(set(d["district"] for d in data))
    max_elev = max(d["elevation_m"] for d in data)
    min_elev = min(d["elevation_m"] for d in data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tea Estates", len(data))
    c2.metric("Districts", len(districts))
    c3.metric("Highest Estate", f"{max_elev}m")
    c4.metric("Elevation Range", f"{min_elev}-{max_elev}m")

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Tea", d["tea"]),
            ("District", d["district"]),
            ("Elevation", f"{d['elevation_m']}m"),
            ("Flavor", d["flavor"]),
            ("Notes", d["notes"]),
        ])

    def _elev_color(elev):
        if elev >= 1200:
            return "#22c55e"
        elif elev >= 600:
            return "#f59e0b"
        return "#ef4444"

    m = folium.Map(location=[7.0, 80.6], zoom_start=8, tiles="CartoDB dark_matter")
    for item in data:
        clr = _elev_color(item["elevation_m"])
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:#1a2235;
    border:1px solid #2a3550;border-radius:8px;padding:10px;font-size:12px;color:#e8ecf4;">
        <b>Ceylon Tea Elevation</b><br>
        <span style="color:#22c55e;">&#9679;</span> High-grown (&ge;1200m)<br>
        <span style="color:#f59e0b;">&#9679;</span> Mid-grown (600-1199m)<br>
        <span style="color:#ef4444;">&#9679;</span> Low-grown (&lt;600m)
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "sri_lankan_tea_highlands")


def _render_tea_ceremonies():
    data = TEA_CEREMONY_TRADITIONS
    countries = sorted(set(d["country"] for d in data))
    traditions = sorted(set(d["tradition"] for d in data))

    c1, c2, c3 = st.columns(3)
    c1.metric("Ceremony Sites", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Traditions", len(traditions))

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Country", d["country"]),
            ("Tradition", d["tradition"]),
            ("Style", d["style"]),
            ("Notes", d["notes"]),
        ])

    country_colors = {
        "Japan": "#22c55e", "China": "#ef4444", "Morocco": "#f59e0b",
        "Russia": "#3b82f6", "Turkey": "#f97316", "UK": "#8b5cf6",
        "India": "#ec4899", "Taiwan": "#06b6d4", "South Korea": "#14b8a6",
        "Iran": "#a855f7", "Tibet/China": "#b45309", "Sri Lanka": "#16a34a",
        "Argentina": "#64748b", "Western Sahara": "#d97706", "Thailand": "#eab308",
        "Hong Kong": "#fb7185", "Germany": "#475569", "Myanmar": "#84cc16",
    }

    m = folium.Map(location=[25, 60], zoom_start=3, tiles="CartoDB dark_matter")
    for item in data:
        clr = country_colors.get(item["country"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "tea_ceremony_traditions")


def _render_trade_routes():
    data = HISTORIC_TEA_TRADE_ROUTES
    routes = sorted(set(d["route"] for d in data))

    c1, c2, c3 = st.columns(3)
    c1.metric("Trade Locations", len(data))
    c2.metric("Route Networks", len(routes))
    c3.metric("Eras Covered", "7th C - Present")

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Route", d["route"]),
            ("Era", d["era"]),
            ("Notes", d["notes"]),
        ])

    route_colors = {
        "Maritime Tea Route": "#3b82f6",
        "Tea Horse Road": "#b45309",
        "Tea Horse Road (Southern)": "#d97706",
        "Tea Horse Road (Northern)": "#f59e0b",
        "British India Tea Route": "#8b5cf6",
        "Ceylon Tea Route": "#22c55e",
        "Japanese Tea Route": "#ef4444",
        "African Tea Route": "#f97316",
        "Clipper Ship Route": "#06b6d4",
        "Russian Tea Route": "#ec4899",
        "Russian Caravan Tea Route": "#fb7185",
        "European Tea Route": "#a855f7",
        "Bengal Tea Route": "#14b8a6",
    }

    m = folium.Map(location=[25, 60], zoom_start=3, tiles="CartoDB dark_matter")
    for item in data:
        clr = route_colors.get(item["route"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)

    # Draw route lines for Tea Horse Road
    thr_points = [(d["lat"], d["lon"]) for d in data if "Tea Horse Road" in d["route"]]
    if len(thr_points) >= 2:
        folium.PolyLine(
            locations=thr_points,
            color="#d97706",
            weight=2,
            opacity=0.6,
            dash_array="8 4",
        ).add_to(m)

    # Draw Maritime route lines
    maritime_points = [(d["lat"], d["lon"]) for d in data if d["route"] == "Maritime Tea Route"]
    if len(maritime_points) >= 2:
        folium.PolyLine(
            locations=maritime_points,
            color="#3b82f6",
            weight=2,
            opacity=0.5,
            dash_array="6 6",
        ).add_to(m)

    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "historic_tea_trade_routes")


def _render_african_tea():
    data = AFRICAN_TEA_GROWING
    countries = sorted(set(d["country"] for d in data))
    avg_elev = int(sum(d["elevation_m"] for d in data) / len(data))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tea Regions", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Avg Elevation", f"{avg_elev}m")
    c4.metric("Highest Estate", f"{max(d['elevation_m'] for d in data)}m")

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Country", d["country"]),
            ("Tea", d["tea"]),
            ("Elevation", f"{d['elevation_m']}m"),
            ("Notes", d["notes"]),
        ])

    country_colors = {
        "Kenya": "#22c55e", "Malawi": "#f59e0b", "Tanzania": "#3b82f6",
        "Rwanda": "#8b5cf6", "Burundi": "#ec4899", "Cameroon": "#f97316",
        "Zimbabwe": "#a855f7", "South Africa": "#06b6d4", "Ethiopia": "#ef4444",
        "Uganda": "#14b8a6", "Mozambique": "#b45309",
    }

    m = folium.Map(location=[-3, 33], zoom_start=4, tiles="CartoDB dark_matter")
    for item in data:
        clr = country_colors.get(item["country"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "african_tea_growing")


def _render_yerba_mate():
    data = SOUTH_AMERICAN_YERBA_MATE
    countries = sorted(set(d["country"] for d in data))
    types = sorted(set(d["type"] for d in data))

    c1, c2, c3 = st.columns(3)
    c1.metric("Mate Locations", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Mate Styles", len(types))

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Country", d["country"]),
            ("Product", d["product"]),
            ("Type", d["type"]),
            ("Notes", d["notes"]),
        ])

    country_colors = {
        "Argentina": "#75aadb", "Brazil": "#22c55e", "Paraguay": "#ef4444",
        "Uruguay": "#3b82f6", "Argentina/Brazil": "#f59e0b",
    }

    m = folium.Map(location=[-27, -55], zoom_start=5, tiles="CartoDB dark_matter")
    for item in data:
        clr = country_colors.get(item["country"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "south_american_yerba_mate")


def _render_tea_museums():
    data = TEA_MUSEUMS_AND_HERITAGE
    countries = sorted(set(d["country"] for d in data))
    types = sorted(set(d["type"] for d in data))

    c1, c2, c3 = st.columns(3)
    c1.metric("Heritage Sites", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Site Types", len(types))

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Country", d["country"]),
            ("Type", d["type"]),
            ("Notes", d["notes"]),
        ])

    type_colors = {
        "Museum": "#06b6d4", "Heritage Site": "#f59e0b",
        "Heritage Shop": "#8b5cf6", "Museum/Centre": "#22c55e",
        "Heritage Viewpoint": "#ec4899", "Heritage": "#a855f7",
        "Heritage Factory": "#ef4444", "Heritage Park": "#14b8a6",
        "Heritage Tour": "#f97316",
    }

    m = folium.Map(location=[25, 60], zoom_start=3, tiles="CartoDB dark_matter")
    for item in data:
        clr = type_colors.get(item["type"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "tea_museums_heritage")


def _render_teahouses():
    data = FAMOUS_TEAHOUSES
    countries = sorted(set(d["country"] for d in data))
    styles = sorted(set(d["style"] for d in data))

    c1, c2, c3 = st.columns(3)
    c1.metric("Famous Teahouses", len(data))
    c2.metric("Countries", len(countries))
    c3.metric("Styles", len(styles))

    def popup_fn(d):
        return _make_popup(d["name"], [
            ("Country", d["country"]),
            ("Style", d["style"]),
            ("Established", d["est"]),
            ("Notes", d["notes"]),
        ])

    country_colors = {
        "France": "#3b82f6", "Singapore": "#ef4444", "UK": "#8b5cf6",
        "Japan": "#22c55e", "Canada": "#f97316", "USA": "#06b6d4",
        "China": "#f59e0b", "Taiwan": "#ec4899", "Italy": "#14b8a6",
        "Netherlands": "#f97316", "Thailand": "#eab308", "Austria": "#a855f7",
        "Hong Kong": "#fb7185",
    }

    m = folium.Map(location=[30, 20], zoom_start=3, tiles="CartoDB dark_matter")
    for item in data:
        clr = country_colors.get(item["country"], "#10b981")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=clr,
            fill=True, fill_color=clr, fill_opacity=0.8,
            popup=folium.Popup(popup_fn(item), max_width=340),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "famous_teahouses_worldwide")


# ========================================================================
# MAIN ENTRY POINT
# ========================================================================

MODE_MAP = {
    "Chinese Tea Regions": _render_chinese_tea,
    "Japanese Tea Gardens": _render_japanese_tea,
    "Indian Tea Estates": _render_indian_tea,
    "Sri Lankan Tea Highlands": _render_sri_lankan_tea,
    "Tea Ceremony Traditions": _render_tea_ceremonies,
    "Historic Tea Trade Routes": _render_trade_routes,
    "African Tea Growing": _render_african_tea,
    "South American Yerba Mate": _render_yerba_mate,
    "Tea Museums & Heritage": _render_tea_museums,
    "Famous Teahouses Worldwide": _render_teahouses,
}


def render_tea_maps_tab():
    """Main entry point for the Tea & Tea Culture Explorer tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>&#127861; Tea & Tea Culture Explorer</h4>'
        '<p>Tea gardens, ceremony traditions, trade routes & tea heritage worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "&#127861; Select Map Mode",
        list(MODE_MAP.keys()),
        key="tea_maps_mode",
    )

    st.markdown("---")

    renderer = MODE_MAP.get(mode)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown mode: {mode}")
