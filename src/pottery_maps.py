# -*- coding: utf-8 -*-
"""
Pottery & Ceramics Maps module for TerraScout AI.
Maps 10 thematic views of global pottery traditions: ancient kilns,
porcelain factories, tile art, ceramic heritage and museums worldwide.
All data is curated; no external API key required.
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


# =====================================================================
# PALETTE CONSTANTS
# =====================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_CARD = "#1a2235"
_BORDER = "#2a3550"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_ACCENT = "#06b6d4"


# =====================================================================
# MODE COLORS & DESCRIPTIONS
# =====================================================================
MODE_COLORS = {
    "Chinese Porcelain Kilns": "#ef4444",
    "Japanese Pottery Traditions": "#f59e0b",
    "Ancient Greek Pottery Sites": "#06b6d4",
    "Islamic Tile Art Centers": "#10b981",
    "European Porcelain Factories": "#8b5cf6",
    "Pre-Columbian Pottery": "#ec4899",
    "African Pottery Traditions": "#f97316",
    "Delft & Majolica Centers": "#3b82f6",
    "Modern Studio Pottery": "#a855f7",
    "Ceramic Museums Worldwide": "#14b8a6",
}

MODE_DESCRIPTIONS = {
    "Chinese Porcelain Kilns": "Historic kiln sites that produced China's legendary ceramics, from Tang sancai to Ming blue-and-white.",
    "Japanese Pottery Traditions": "Regional pottery traditions (yakimono) including raku, Bizen, Seto, Arita and more.",
    "Ancient Greek Pottery Sites": "Attic, Corinthian, and other workshops that produced iconic black-figure and red-figure pottery.",
    "Islamic Tile Art Centers": "Cities renowned for glazed tile work (zellige, Iznik, kashikari) across the Islamic world.",
    "European Porcelain Factories": "Major European porcelain manufactories from Meissen to Sevres to Wedgwood.",
    "Pre-Columbian Pottery": "Moche, Nazca, Maya and other ancient American ceramic traditions.",
    "African Pottery Traditions": "Living pottery traditions across the African continent, from Nok terracotta to modern workshops.",
    "Delft & Majolica Centers": "Tin-glazed earthenware traditions: Dutch Delftware, Italian maiolica, Portuguese azulejo.",
    "Modern Studio Pottery": "Key centers and figures of the 20th-21st century studio pottery movement.",
    "Ceramic Museums Worldwide": "Museums devoted to ceramics, porcelain, and pottery collections around the globe.",
}


# =====================================================================
# 1. CHINESE PORCELAIN KILNS (30 locations)
# =====================================================================
def _chinese_porcelain_kilns_data():
    return [
        {"name": "Jingdezhen, Jiangxi", "lat": 29.27, "lon": 117.18,
         "country": "China", "era": "Han dynasty onward",
         "type": "Porcelain capital",
         "notes": "Porcelain capital of the world for over 1,700 years; Ming blue-and-white masterpieces"},
        {"name": "Longquan, Zhejiang", "lat": 28.07, "lon": 119.14,
         "country": "China", "era": "Northern Song",
         "type": "Celadon",
         "notes": "Famous celadon glazes with jade-like green color; exported across Asia"},
        {"name": "Dehua, Fujian", "lat": 25.49, "lon": 118.24,
         "country": "China", "era": "Ming dynasty",
         "type": "Blanc de Chine",
         "notes": "Renowned for ivory-white porcelain (blanc de Chine); Guanyin figurines"},
        {"name": "Yixing, Jiangsu", "lat": 31.34, "lon": 119.82,
         "country": "China", "era": "Song dynasty",
         "type": "Zisha stoneware",
         "notes": "Purple clay (zisha) teapots prized by tea connoisseurs for centuries"},
        {"name": "Cizhou, Hebei", "lat": 36.38, "lon": 114.18,
         "country": "China", "era": "Song-Jin",
         "type": "Painted stoneware",
         "notes": "Bold black-and-white painted slip decoration; folk pottery tradition"},
        {"name": "Ru Kiln (Ruzhou), Henan", "lat": 33.98, "lon": 112.84,
         "country": "China", "era": "Northern Song",
         "type": "Imperial celadon",
         "notes": "Rarest of the Five Great Kilns; sky-blue crackle glaze; fewer than 100 pieces survive"},
        {"name": "Jun Kiln (Yuzhou), Henan", "lat": 34.16, "lon": 113.48,
         "country": "China", "era": "Song dynasty",
         "type": "Opalescent glaze",
         "notes": "Purple-splashed opalescent glazes; each piece uniquely colored by kiln atmosphere"},
        {"name": "Guan Kiln (Hangzhou), Zhejiang", "lat": 30.25, "lon": 120.17,
         "country": "China", "era": "Southern Song",
         "type": "Imperial celadon",
         "notes": "Official court kiln producing crackle-glazed celadon for the Southern Song emperors"},
        {"name": "Ge Kiln (Longquan area)", "lat": 28.10, "lon": 119.20,
         "country": "China", "era": "Song dynasty",
         "type": "Crackle ware",
         "notes": "Distinctive double-crackle glaze pattern; one of the legendary Five Great Kilns"},
        {"name": "Ding Kiln (Quyang), Hebei", "lat": 38.63, "lon": 114.70,
         "country": "China", "era": "Tang-Song",
         "type": "White porcelain",
         "notes": "Finest white-glazed porcelain of the Song; mold-impressed decoration"},
        {"name": "Yaozhou Kiln, Shaanxi", "lat": 34.90, "lon": 108.98,
         "country": "China", "era": "Song dynasty",
         "type": "Olive celadon",
         "notes": "Olive-green celadon with carved floral decoration; Northern Song masterwork"},
        {"name": "Changsha Kiln (Tongguan), Hunan", "lat": 28.56, "lon": 112.85,
         "country": "China", "era": "Tang dynasty",
         "type": "Underglaze painted",
         "notes": "Pioneered underglaze painting technique; exported to Middle East via maritime trade"},
        {"name": "Xing Kiln (Neiqiu), Hebei", "lat": 37.28, "lon": 114.51,
         "country": "China", "era": "Sui-Tang",
         "type": "White porcelain",
         "notes": "Earliest high-quality white porcelain alongside Ding Kiln; Tang dynasty fame"},
        {"name": "Jizhou Kiln, Jiangxi", "lat": 27.13, "lon": 114.98,
         "country": "China", "era": "Song dynasty",
         "type": "Tenmoku / leaf ware",
         "notes": "Leaf-decorated tea bowls and paper-cut resist designs; tenmoku glazes"},
        {"name": "Jian Kiln (Jianyang), Fujian", "lat": 27.33, "lon": 118.12,
         "country": "China", "era": "Song dynasty",
         "type": "Tenmoku tea bowls",
         "notes": "Hare's fur and oil-spot tenmoku bowls treasured in Japanese tea ceremony"},
        {"name": "Shiwan Kiln, Guangdong", "lat": 23.01, "lon": 113.10,
         "country": "China", "era": "Song dynasty",
         "type": "Figurines & stoneware",
         "notes": "Expressive ceramic figurines and roof ornaments; Foshan pottery district"},
        {"name": "Liling, Hunan", "lat": 27.65, "lon": 113.50,
         "country": "China", "era": "Qing dynasty",
         "type": "Underglaze colors",
         "notes": "Major modern porcelain center; underglaze five-color technique"},
        {"name": "Chaozhou, Guangdong", "lat": 23.66, "lon": 116.62,
         "country": "China", "era": "Tang dynasty",
         "type": "Export porcelain",
         "notes": "Prolific export kiln center; teaware and tableware for Southeast Asian trade"},
        {"name": "Quanzhou, Fujian", "lat": 24.87, "lon": 118.68,
         "country": "China", "era": "Song-Yuan",
         "type": "Maritime export",
         "notes": "Major port for ceramic exports along the Maritime Silk Road"},
        {"name": "Linru (Ru'an), Henan", "lat": 33.73, "lon": 112.83,
         "country": "China", "era": "Song dynasty",
         "type": "Celadon",
         "notes": "Important celadon production area in the Ru kiln tradition"},
        {"name": "Yue Kiln (Shanglinhu), Zhejiang", "lat": 29.90, "lon": 121.22,
         "country": "China", "era": "Eastern Han-Song",
         "type": "Proto-celadon",
         "notes": "Birthplace of celadon; secret-color porcelain (mise) for Tang court"},
        {"name": "Hutian Kiln (Jingdezhen)", "lat": 29.30, "lon": 117.20,
         "country": "China", "era": "Five Dynasties-Yuan",
         "type": "Qingbai porcelain",
         "notes": "Produced bluish-white (qingbai) porcelain; precursor to Ming blue-and-white"},
        {"name": "Nanfeng, Jiangxi", "lat": 27.22, "lon": 116.52,
         "country": "China", "era": "Song dynasty",
         "type": "Black-glazed ware",
         "notes": "Black-glazed stoneware and tenmoku production center"},
        {"name": "Cizao (Jinjiang), Fujian", "lat": 24.78, "lon": 118.58,
         "country": "China", "era": "Song-Yuan",
         "type": "Export celadon",
         "notes": "Major coastal kiln complex exporting celadon and qingbai ware to Southeast Asia"},
        {"name": "Dangyang (Yutang), Hubei", "lat": 30.83, "lon": 111.78,
         "country": "China", "era": "Sui-Tang",
         "type": "Celadon",
         "notes": "Celadon production center in central China; supplied inland markets"},
        {"name": "Gongyi (Gongxian), Henan", "lat": 34.75, "lon": 113.02,
         "country": "China", "era": "Tang dynasty",
         "type": "Sancai (three-color)",
         "notes": "Major production center for Tang sancai lead-glazed tomb figures and vessels"},
        {"name": "Tongling, Anhui", "lat": 30.95, "lon": 117.81,
         "country": "China", "era": "Ming dynasty",
         "type": "White porcelain",
         "notes": "White porcelain production linked to Jingdezhen supply networks"},
        {"name": "Zibo (Boshan), Shandong", "lat": 36.81, "lon": 117.83,
         "country": "China", "era": "Song dynasty",
         "type": "Glass & ceramics",
         "notes": "Historic ceramics and glass production center; colored-glaze tradition"},
        {"name": "Pingding, Shanxi", "lat": 37.79, "lon": 113.63,
         "country": "China", "era": "Song-Jin",
         "type": "Black ware",
         "notes": "Black-glazed and iron-rust ware production; northern stoneware tradition"},
        {"name": "Wuzhou (Jinhua), Zhejiang", "lat": 29.08, "lon": 119.65,
         "country": "China", "era": "Tang-Song",
         "type": "Wuzhou celadon",
         "notes": "Regional celadon production rivaling Yue kilns; export ware for Japan"},
    ]


# =====================================================================
# 2. JAPANESE POTTERY TRADITIONS (30 locations)
# =====================================================================
def _japanese_pottery_traditions_data():
    return [
        {"name": "Arita, Saga", "lat": 33.20, "lon": 129.88,
         "country": "Japan", "era": "1616",
         "type": "Porcelain (Imari)",
         "notes": "Birthplace of Japanese porcelain; Kakiemon and Nabeshima styles; exported as Imari ware"},
        {"name": "Bizen, Okayama", "lat": 34.74, "lon": 134.18,
         "country": "Japan", "era": "Kamakura period",
         "type": "Unglazed stoneware",
         "notes": "One of the Six Ancient Kilns; natural ash glaze from 10+ day wood firings"},
        {"name": "Seto, Aichi", "lat": 35.22, "lon": 137.08,
         "country": "Japan", "era": "Kamakura period",
         "type": "Glazed stoneware",
         "notes": "Setomono became generic Japanese word for ceramics; Six Ancient Kilns"},
        {"name": "Mino (Toki), Gifu", "lat": 35.35, "lon": 137.18,
         "country": "Japan", "era": "Momoyama period",
         "type": "Shino / Oribe",
         "notes": "Shino white glaze and Oribe green glaze; wabi-sabi tea ceremony aesthetics"},
        {"name": "Tokoname, Aichi", "lat": 34.88, "lon": 136.85,
         "country": "Japan", "era": "Heian period",
         "type": "Red clay stoneware",
         "notes": "Six Ancient Kilns; famous for vermilion kyusu teapots and maneki-neko cats"},
        {"name": "Shigaraki, Shiga", "lat": 34.85, "lon": 136.07,
         "country": "Japan", "era": "Kamakura period",
         "type": "Rustic stoneware",
         "notes": "Six Ancient Kilns; tanuki statues; ash-glazed natural effects prized in tea ceremony"},
        {"name": "Echizen, Fukui", "lat": 35.91, "lon": 136.20,
         "country": "Japan", "era": "Heian period",
         "type": "Utilitarian stoneware",
         "notes": "Six Ancient Kilns; large storage jars and mortar vessels; natural ash deposits"},
        {"name": "Tamba (Sasayama), Hyogo", "lat": 35.08, "lon": 135.22,
         "country": "Japan", "era": "Kamakura period",
         "type": "Stoneware",
         "notes": "Six Ancient Kilns; 800 years of continuous production; climbing kilns (noborigama)"},
        {"name": "Karatsu, Saga", "lat": 33.44, "lon": 129.97,
         "country": "Japan", "era": "Momoyama period",
         "type": "Korean-style stoneware",
         "notes": "Korean potters brought after Imjin War; e-garatsu painted ware; tea ceremony favorite"},
        {"name": "Hagi, Yamaguchi", "lat": 34.41, "lon": 131.40,
         "country": "Japan", "era": "1604",
         "type": "Soft-glazed stoneware",
         "notes": "Korean-origin ware prized for tea ceremony; glaze crazes beautifully with age"},
        {"name": "Kutani (Kaga), Ishikawa", "lat": 36.30, "lon": 136.35,
         "country": "Japan", "era": "1655",
         "type": "Overglaze enameled porcelain",
         "notes": "Bold five-color overglaze enamels (red, green, yellow, purple, navy); vivid designs"},
        {"name": "Kyoto (Kiyomizu)", "lat": 34.99, "lon": 135.78,
         "country": "Japan", "era": "Edo period",
         "type": "Kyo-yaki",
         "notes": "Elegant Kyoto ceramics; Ninsei and Kenzan master lineages; overglaze enamels"},
        {"name": "Mashiko, Tochigi", "lat": 36.47, "lon": 140.10,
         "country": "Japan", "era": "1853",
         "type": "Folk pottery",
         "notes": "Hamada Shoji made it the heart of mingei folk craft movement; earthy glazes"},
        {"name": "Onta, Oita", "lat": 33.25, "lon": 131.12,
         "country": "Japan", "era": "1705",
         "type": "Mingei folk pottery",
         "notes": "Tiny village of 10 families using traditional techniques; UNESCO recognized"},
        {"name": "Satsuma (Kagoshima)", "lat": 31.60, "lon": 130.55,
         "country": "Japan", "era": "1598",
         "type": "Cream-glazed stoneware",
         "notes": "Korean-origin; gold-decorated Satsuma ware became hugely popular in the West"},
        {"name": "Tobe, Ehime", "lat": 33.74, "lon": 132.80,
         "country": "Japan", "era": "1777",
         "type": "Blue-and-white porcelain",
         "notes": "Simple indigo blue on white; folk art porcelain for daily use"},
        {"name": "Kasama, Ibaraki", "lat": 36.35, "lon": 140.23,
         "country": "Japan", "era": "1770",
         "type": "Stoneware",
         "notes": "Kanto region's oldest kiln area; now a vibrant contemporary ceramics town"},
        {"name": "Hasami, Nagasaki", "lat": 33.13, "lon": 129.90,
         "country": "Japan", "era": "1599",
         "type": "Porcelain tableware",
         "notes": "Mass-produced porcelain bowls; supplied most of Edo period daily porcelain"},
        {"name": "Iga (Iga-Ueno), Mie", "lat": 34.77, "lon": 136.13,
         "country": "Japan", "era": "Momoyama period",
         "type": "Rustic stoneware",
         "notes": "Bidoro (glass-like) natural ash effects; related to Shigaraki tradition"},
        {"name": "Banko (Yokkaichi), Mie", "lat": 34.96, "lon": 136.62,
         "country": "Japan", "era": "1736",
         "type": "Purple clay teapots",
         "notes": "Banko-yaki purple clay similar to Chinese Yixing; heat-resistant donabe pots"},
        {"name": "Agano, Fukuoka", "lat": 33.72, "lon": 130.87,
         "country": "Japan", "era": "1602",
         "type": "Tea ceremony ware",
         "notes": "Korean potter Sonkai established kiln under Hosokawa lord; flowing ash glazes"},
        {"name": "Takatori, Fukuoka", "lat": 33.55, "lon": 130.62,
         "country": "Japan", "era": "1600",
         "type": "Tea ceremony ware",
         "notes": "Korean-origin kiln patronized by Kobori Enshu; thin elegant forms"},
        {"name": "Koishiwara, Fukuoka", "lat": 33.38, "lon": 130.93,
         "country": "Japan", "era": "1682",
         "type": "Mingei folk pottery",
         "notes": "Chattering (tobikanna) decoration technique; folk art pottery village"},
        {"name": "Ryumonji, Kagoshima", "lat": 31.48, "lon": 130.68,
         "country": "Japan", "era": "1598",
         "type": "Black Satsuma",
         "notes": "Kuro-Satsuma black-glazed ware for everyday use; Korean potter heritage"},
        {"name": "Otani, Tokushima", "lat": 34.10, "lon": 134.50,
         "country": "Japan", "era": "1780",
         "type": "Large-scale stoneware",
         "notes": "Enormous indigo vats and water jars; two-person rope-turning technique"},
        {"name": "Mikawachi, Nagasaki", "lat": 33.17, "lon": 129.75,
         "country": "Japan", "era": "1598",
         "type": "Hirado porcelain",
         "notes": "Delicate white porcelain with blue painting; micro-carved openwork decoration"},
        {"name": "Izushi, Hyogo", "lat": 35.45, "lon": 134.87,
         "country": "Japan", "era": "1764",
         "type": "White porcelain",
         "notes": "Refined white porcelain without painting; pure minimalist beauty"},
        {"name": "Mumyoi (Sado Island)", "lat": 38.03, "lon": 138.37,
         "country": "Japan", "era": "1819",
         "type": "Red clay pottery",
         "notes": "Made from iron-rich Sado gold mine clay; deep red burnished surface"},
        {"name": "Soma, Fukushima", "lat": 37.80, "lon": 140.92,
         "country": "Japan", "era": "1690",
         "type": "Double-walled stoneware",
         "notes": "Soma-yaki with running horse motif and unique double-walled insulating cups"},
        {"name": "Obori Soma, Fukushima", "lat": 37.77, "lon": 140.72,
         "country": "Japan", "era": "1690",
         "type": "Crackle-glazed stoneware",
         "notes": "Blue crackle-glazed ware with galloping horse design; insulating double walls"},
    ]


# =====================================================================
# 3. ANCIENT GREEK POTTERY SITES (28 locations)
# =====================================================================
def _ancient_greek_pottery_sites_data():
    return [
        {"name": "Kerameikos, Athens", "lat": 37.98, "lon": 23.72,
         "country": "Greece", "era": "c. 1000-300 BC",
         "type": "Black-figure & red-figure",
         "notes": "Potters' quarter of Athens; word 'ceramic' derives from Kerameikos; Attic masterpieces"},
        {"name": "Corinth", "lat": 37.91, "lon": 22.88,
         "country": "Greece", "era": "c. 700-550 BC",
         "type": "Protocorinthian",
         "notes": "Earliest Greek figure painting on pottery; orientalizing animal friezes"},
        {"name": "Argos", "lat": 37.63, "lon": 22.73,
         "country": "Greece", "era": "c. 700-600 BC",
         "type": "Geometric ware",
         "notes": "Monumental kraters with geometric horse and warrior motifs"},
        {"name": "Laconia (Sparta)", "lat": 37.08, "lon": 22.43,
         "country": "Greece", "era": "c. 600-500 BC",
         "type": "Laconian black-figure",
         "notes": "Distinctive black-figure kylix cups; Arkesilas Painter masterworks"},
        {"name": "Boeotia (Tanagra)", "lat": 38.35, "lon": 23.53,
         "country": "Greece", "era": "c. 300 BC",
         "type": "Terracotta figurines",
         "notes": "Tanagra figurines of draped women; mass-produced elegant small sculptures"},
        {"name": "Aegina", "lat": 37.75, "lon": 23.43,
         "country": "Greece", "era": "c. 500 BC",
         "type": "Trade pottery",
         "notes": "Major pottery trade hub; distributed Attic and Corinthian wares across Mediterranean"},
        {"name": "Rhodes", "lat": 36.43, "lon": 28.22,
         "country": "Greece", "era": "c. 700-500 BC",
         "type": "Fikellura ware",
         "notes": "Wild Goat Style and Fikellura ware; East Greek orientalizing pottery"},
        {"name": "Miletus", "lat": 37.53, "lon": 27.28,
         "country": "Turkey", "era": "c. 650-500 BC",
         "type": "Wild Goat Style",
         "notes": "Major production center of Wild Goat Style pottery; Ionian Greek tradition"},
        {"name": "Ephesus", "lat": 37.95, "lon": 27.36,
         "country": "Turkey", "era": "c. 600-300 BC",
         "type": "Ionian pottery",
         "notes": "Pottery workshops near Artemis temple; Ionian Greek tradition"},
        {"name": "Clazomenae", "lat": 38.37, "lon": 26.78,
         "country": "Turkey", "era": "c. 550-500 BC",
         "type": "Black-figure sarcophagi",
         "notes": "Unique painted terracotta sarcophagi with mythological scenes"},
        {"name": "Metapontum", "lat": 40.38, "lon": 16.82,
         "country": "Italy", "era": "c. 500-300 BC",
         "type": "South Italian red-figure",
         "notes": "Lucanian red-figure workshop; Magna Graecia pottery production"},
        {"name": "Taranto (Tarentum)", "lat": 40.48, "lon": 17.23,
         "country": "Italy", "era": "c. 400-300 BC",
         "type": "Apulian red-figure",
         "notes": "Largest production of South Italian red-figure pottery; monumental kraters"},
        {"name": "Paestum", "lat": 40.42, "lon": 15.01,
         "country": "Italy", "era": "c. 350-300 BC",
         "type": "Paestan red-figure",
         "notes": "Asteas and Python painters; comic theatrical scenes on bell kraters"},
        {"name": "Syracuse, Sicily", "lat": 37.08, "lon": 15.29,
         "country": "Italy", "era": "c. 500-300 BC",
         "type": "Sicilian red-figure",
         "notes": "Greek colony with vibrant pottery workshops; Sicilian red-figure tradition"},
        {"name": "Canosa di Puglia", "lat": 41.22, "lon": 16.07,
         "country": "Italy", "era": "c. 300 BC",
         "type": "Polychrome Canosan ware",
         "notes": "Elaborate polychrome funerary vases with three-dimensional attachments"},
        {"name": "Gnathia (Egnazia)", "lat": 40.89, "lon": 17.39,
         "country": "Italy", "era": "c. 350-250 BC",
         "type": "Gnathian ware",
         "notes": "Painted decoration over black glaze; final phase of South Italian pottery"},
        {"name": "Lipari, Sicily", "lat": 38.47, "lon": 14.95,
         "country": "Italy", "era": "c. 300 BC",
         "type": "Polychrome vases",
         "notes": "Lipari Painter polychrome funerary vases; excellent preservation in tombs"},
        {"name": "Knossos, Crete", "lat": 35.30, "lon": 25.16,
         "country": "Greece", "era": "c. 2000-1400 BC",
         "type": "Minoan Kamares ware",
         "notes": "Elaborate Kamares polychrome pottery; Marine Style with octopi and dolphins"},
        {"name": "Phaistos, Crete", "lat": 35.05, "lon": 24.81,
         "country": "Greece", "era": "c. 1900-1600 BC",
         "type": "Kamares polychrome",
         "notes": "Kamares Cave discoveries; finest Middle Minoan polychrome pottery"},
        {"name": "Mycenae", "lat": 37.73, "lon": 22.76,
         "country": "Greece", "era": "c. 1400-1100 BC",
         "type": "Mycenaean stirrup jars",
         "notes": "Pictorial Style pottery with chariots and warriors; trade across Mediterranean"},
        {"name": "Lefkandi, Euboea", "lat": 38.44, "lon": 23.72,
         "country": "Greece", "era": "c. 1000-800 BC",
         "type": "Protogeometric ware",
         "notes": "Key transition from Mycenaean to Geometric style; concentric circles motif"},
        {"name": "Eretria, Euboea", "lat": 38.40, "lon": 23.79,
         "country": "Greece", "era": "c. 600-400 BC",
         "type": "Euboean pottery",
         "notes": "Distributed Greek pottery westward to Al Mina and Pithekoussai"},
        {"name": "Pithekoussai (Ischia)", "lat": 40.73, "lon": 13.90,
         "country": "Italy", "era": "c. 770-700 BC",
         "type": "Colonial Greek pottery",
         "notes": "Earliest Greek colony in the West; Nestor's Cup inscription on local pottery"},
        {"name": "Cumae", "lat": 40.85, "lon": 14.05,
         "country": "Italy", "era": "c. 750-500 BC",
         "type": "Colonial Euboean ware",
         "notes": "Greek colony pottery workshops; intermediary for Etruscan pottery influence"},
        {"name": "Naukratis, Egypt", "lat": 30.90, "lon": 30.60,
         "country": "Egypt", "era": "c. 630-300 BC",
         "type": "Greek trade pottery",
         "notes": "Greek trading colony in Egypt; concentration of imported Greek pottery sherds"},
        {"name": "Al Mina, Turkey", "lat": 36.19, "lon": 35.93,
         "country": "Turkey", "era": "c. 800-300 BC",
         "type": "Greek trade ware",
         "notes": "Near Antioch; key depot for Euboean and Corinthian trade pottery in the Levant"},
        {"name": "Vulci, Etruria", "lat": 42.42, "lon": 11.63,
         "country": "Italy", "era": "c. 600-400 BC",
         "type": "Etruscan & imported Attic",
         "notes": "Thousands of Attic vases found in Etruscan tombs; Francois Vase context"},
        {"name": "Cerveteri (Caere), Etruria", "lat": 42.00, "lon": 12.10,
         "country": "Italy", "era": "c. 650-400 BC",
         "type": "Etruscan bucchero",
         "notes": "Black bucchero ware unique to Etruscans; also major importer of Greek pottery"},
    ]


# =====================================================================
# 4. ISLAMIC TILE ART CENTERS (30 locations)
# =====================================================================
def _islamic_tile_art_centers_data():
    return [
        {"name": "Iznik, Turkey", "lat": 40.43, "lon": 29.72,
         "country": "Turkey", "era": "15th-17th c.",
         "type": "Iznik tiles",
         "notes": "Ottoman golden age tiles; cobalt blue, turquoise, tomato-red Armenian bole glaze"},
        {"name": "Kutahya, Turkey", "lat": 39.42, "lon": 29.97,
         "country": "Turkey", "era": "14th c. onward",
         "type": "Kutahya ceramics",
         "notes": "Continued Ottoman tile tradition after Iznik declined; still active today"},
        {"name": "Isfahan, Iran", "lat": 32.65, "lon": 51.68,
         "country": "Iran", "era": "Safavid 16th-17th c.",
         "type": "Haft-rangi tiles",
         "notes": "Shah Mosque and Sheikh Lotfollah Mosque; seven-color tile masterpieces"},
        {"name": "Kashan, Iran", "lat": 33.98, "lon": 51.44,
         "country": "Iran", "era": "12th-14th c.",
         "type": "Lustre tiles (kashi)",
         "notes": "Word 'kashi' (tile) derives from Kashan; lustre-painted star-and-cross tiles"},
        {"name": "Tabriz, Iran", "lat": 38.08, "lon": 46.29,
         "country": "Iran", "era": "Ilkhanid 13th c.",
         "type": "Mosaic tiles",
         "notes": "Blue Mosque and Ilkhanid tilework; tile-mosaic (muarraq) tradition"},
        {"name": "Samarkand, Uzbekistan", "lat": 39.65, "lon": 66.96,
         "country": "Uzbekistan", "era": "Timurid 14th-15th c.",
         "type": "Majolica & mosaic",
         "notes": "Registan Square madrasas; turquoise and cobalt blue tile domes of Tamerlane"},
        {"name": "Bukhara, Uzbekistan", "lat": 39.77, "lon": 64.42,
         "country": "Uzbekistan", "era": "16th c.",
         "type": "Carved terracotta & tile",
         "notes": "Kalyan Minaret and Mir-i-Arab Madrasa; geometric tile panels"},
        {"name": "Fez, Morocco", "lat": 34.03, "lon": -5.00,
         "country": "Morocco", "era": "14th c. onward",
         "type": "Zellige mosaic",
         "notes": "Bou Inania Madrasa; hand-cut geometric zellige tile mosaics in vivid colors"},
        {"name": "Marrakech, Morocco", "lat": 31.63, "lon": -8.00,
         "country": "Morocco", "era": "12th c. onward",
         "type": "Zellige",
         "notes": "Saadian Tombs and Ben Youssef Madrasa; Moorish zellige tradition continues"},
        {"name": "Meknes, Morocco", "lat": 33.89, "lon": -5.55,
         "country": "Morocco", "era": "17th c.",
         "type": "Zellige",
         "notes": "Moulay Ismail's imperial city; Bab Mansour monumental zellige gate"},
        {"name": "Granada, Spain", "lat": 37.18, "lon": -3.60,
         "country": "Spain", "era": "13th-15th c.",
         "type": "Nasrid alicatado",
         "notes": "Alhambra Palace; alicatado tile mosaics and carved stucco; Nasrid apex"},
        {"name": "Seville, Spain", "lat": 37.39, "lon": -5.98,
         "country": "Spain", "era": "12th-16th c.",
         "type": "Mudéjar azulejos",
         "notes": "Real Alcazar; Mudéjar tile tradition blending Islamic and Christian motifs"},
        {"name": "Multan, Pakistan", "lat": 30.20, "lon": 71.47,
         "country": "Pakistan", "era": "13th c. onward",
         "type": "Kashikari tiles",
         "notes": "City of Saints; blue kashikari tile-covered Sufi shrines and mosques"},
        {"name": "Lahore, Pakistan", "lat": 31.55, "lon": 74.35,
         "country": "Pakistan", "era": "Mughal 16th-17th c.",
         "type": "Kashikari & pietra dura",
         "notes": "Wazir Khan Mosque; finest kashikari tilework; Mughal period masterpiece"},
        {"name": "Herat, Afghanistan", "lat": 34.35, "lon": 62.20,
         "country": "Afghanistan", "era": "Timurid 15th c.",
         "type": "Tile mosaic",
         "notes": "Friday Mosque tile restoration; Timurid calligraphic and floral tile panels"},
        {"name": "Delhi, India", "lat": 28.61, "lon": 77.21,
         "country": "India", "era": "Mughal 16th-17th c.",
         "type": "Mughal tile panels",
         "notes": "Humayun's Tomb and Red Fort; glazed tile inlay in Mughal architecture"},
        {"name": "Shiraz, Iran", "lat": 29.59, "lon": 52.58,
         "country": "Iran", "era": "Zand 18th c.",
         "type": "Haft-rangi tiles",
         "notes": "Nasir al-Mulk Pink Mosque; stained glass and rose-colored tiles"},
        {"name": "Konya, Turkey", "lat": 37.87, "lon": 32.48,
         "country": "Turkey", "era": "Seljuk 13th c.",
         "type": "Seljuk tile mosaic",
         "notes": "Karatay Madrasa and Ince Minare; turquoise Seljuk tile interiors"},
        {"name": "Cairo, Egypt", "lat": 30.04, "lon": 31.24,
         "country": "Egypt", "era": "Mamluk 13th-16th c.",
         "type": "Lustre & underglaze tiles",
         "notes": "Sultan Hassan Mosque and Al-Aqmar Mosque; Mamluk tilework heritage"},
        {"name": "Tunis, Tunisia", "lat": 36.81, "lon": 10.18,
         "country": "Tunisia", "era": "Hafsid 13th c.",
         "type": "Tunisian tiles",
         "notes": "Medina of Tunis; geometric and floral painted tiles in traditional houses"},
        {"name": "Tlemcen, Algeria", "lat": 34.88, "lon": -1.31,
         "country": "Algeria", "era": "Zianid 13th c.",
         "type": "Zellige & carved stucco",
         "notes": "Mansourah ruins and Great Mosque; Andalusian-Maghrebi tile tradition"},
        {"name": "Yazd, Iran", "lat": 31.90, "lon": 54.37,
         "country": "Iran", "era": "Timurid 15th c.",
         "type": "Tile mosaic",
         "notes": "Jameh Mosque with soaring tile-covered minarets; desert city of windcatchers"},
        {"name": "Mashhad, Iran", "lat": 36.30, "lon": 59.60,
         "country": "Iran", "era": "Timurid-Safavid",
         "type": "Shrine tilework",
         "notes": "Imam Reza Shrine; gilded and tiled sacred complex; continuous tile restoration"},
        {"name": "Thatta, Pakistan", "lat": 24.75, "lon": 67.92,
         "country": "Pakistan", "era": "Mughal 17th c.",
         "type": "Sindhi kashikari",
         "notes": "Shah Jahan Mosque; geometric blue-and-white tile patterns unique to Sindh"},
        {"name": "Uch Sharif, Pakistan", "lat": 29.23, "lon": 71.05,
         "country": "Pakistan", "era": "13th c.",
         "type": "Kashikari glazed tiles",
         "notes": "Sufi shrine of Bibi Jawindi; octagonal tomb with brilliant blue tilework"},
        {"name": "Edirne, Turkey", "lat": 41.68, "lon": 26.56,
         "country": "Turkey", "era": "Ottoman 15th c.",
         "type": "Iznik tiles",
         "notes": "Selimiye Mosque by Sinan; extensive Iznik tile panels in Ottoman masterwork"},
        {"name": "Bursa, Turkey", "lat": 40.18, "lon": 29.06,
         "country": "Turkey", "era": "Early Ottoman 14th c.",
         "type": "Cuerda seca tiles",
         "notes": "Green Mosque and Green Tomb; earliest Ottoman tilework using cuerda seca technique"},
        {"name": "Khiva, Uzbekistan", "lat": 41.38, "lon": 60.36,
         "country": "Uzbekistan", "era": "19th c.",
         "type": "Majolica tiles",
         "notes": "Ichan Kala walled city; Kalta Minor minaret covered in turquoise tiles"},
        {"name": "Damascus, Syria", "lat": 33.51, "lon": 36.29,
         "country": "Syria", "era": "Umayyad 8th c.",
         "type": "Glass mosaic & tile",
         "notes": "Umayyad Mosque gold-glass mosaics; foundational Islamic decorative tradition"},
        {"name": "Cordoba, Spain", "lat": 37.88, "lon": -4.78,
         "country": "Spain", "era": "Umayyad 10th c.",
         "type": "Caliphate tiles",
         "notes": "Mezquita horseshoe arches; Medina Azahara palace tile fragments; Umayyad legacy"},
    ]


# =====================================================================
# 5. EUROPEAN PORCELAIN FACTORIES (30 locations)
# =====================================================================
def _european_porcelain_factories_data():
    return [
        {"name": "Meissen, Saxony", "lat": 51.16, "lon": 13.47,
         "country": "Germany", "founded": 1710,
         "type": "Hard-paste porcelain",
         "notes": "First European hard-paste porcelain; crossed swords mark; Bottger's invention"},
        {"name": "Sevres, Paris", "lat": 48.83, "lon": 2.21,
         "country": "France", "founded": 1740,
         "type": "Soft-paste / hard-paste",
         "notes": "Royal French manufactory; bleu celeste and rose Pompadour; still active"},
        {"name": "Wedgwood (Stoke-on-Trent)", "lat": 53.00, "lon": -2.18,
         "country": "UK", "founded": 1759,
         "type": "Jasperware / creamware",
         "notes": "Josiah Wedgwood's neoclassical jasperware; industrialized pottery production"},
        {"name": "Royal Copenhagen", "lat": 55.68, "lon": 12.57,
         "country": "Denmark", "founded": 1775,
         "type": "Blue Fluted porcelain",
         "notes": "Flora Danica service and Blue Fluted pattern; three-wave hallmark"},
        {"name": "Herend, Hungary", "lat": 47.13, "lon": 17.75,
         "country": "Hungary", "founded": 1826,
         "type": "Hand-painted porcelain",
         "notes": "Victoria butterfly pattern; Queen Victoria ordered at 1851 Great Exhibition"},
        {"name": "Royal Doulton (Stoke-on-Trent)", "lat": 52.99, "lon": -2.17,
         "country": "UK", "founded": 1815,
         "type": "Stoneware / bone china",
         "notes": "Character jugs, figurines, and hotel china; Lambeth and Burslem factories"},
        {"name": "Capodimonte, Naples", "lat": 40.87, "lon": 14.25,
         "country": "Italy", "founded": 1743,
         "type": "Soft-paste porcelain",
         "notes": "Charles VII's royal factory; delicate figurines and snuff boxes"},
        {"name": "Doccia (Ginori), Florence", "lat": 43.81, "lon": 11.18,
         "country": "Italy", "founded": 1737,
         "type": "Hard-paste porcelain",
         "notes": "Marchese Ginori's factory; now Richard-Ginori; neoclassical and baroque styles"},
        {"name": "Berlin (KPM)", "lat": 52.52, "lon": 13.35,
         "country": "Germany", "founded": 1763,
         "type": "Hard-paste porcelain",
         "notes": "Konigliche Porzellan-Manufaktur; Frederick the Great's patronage; scepter mark"},
        {"name": "Nymphenburg, Munich", "lat": 48.16, "lon": 11.50,
         "country": "Germany", "founded": 1747,
         "type": "Hard-paste porcelain",
         "notes": "Bustelli's commedia dell'arte figurines; still hand-producing in the palace"},
        {"name": "Vienna (Augarten)", "lat": 48.22, "lon": 16.38,
         "country": "Austria", "founded": 1718,
         "type": "Hard-paste porcelain",
         "notes": "Second oldest European porcelain factory; Du Paquier period; beehive mark"},
        {"name": "Rosenthal (Selb)", "lat": 50.17, "lon": 12.13,
         "country": "Germany", "founded": 1879,
         "type": "Art porcelain",
         "notes": "Modernist designs; collaborations with Versace, Bulgari; Studio-Line series"},
        {"name": "Limoges, France", "lat": 45.83, "lon": 1.26,
         "country": "France", "founded": 1771,
         "type": "Hard-paste porcelain",
         "notes": "Kaolin discovered nearby; numerous factories; Limoges boxes and tableware"},
        {"name": "Delft, Netherlands", "lat": 52.01, "lon": 4.36,
         "country": "Netherlands", "founded": 1653,
         "type": "Tin-glazed earthenware",
         "notes": "Blue-and-white Delftware imitating Chinese porcelain; De Porceleyne Fles active"},
        {"name": "Worcester (Royal Worcester)", "lat": 52.19, "lon": -2.22,
         "country": "UK", "founded": 1751,
         "type": "Soft-paste / bone china",
         "notes": "Dr. Wall period masterpieces; scale blue ground; porcelain museum"},
        {"name": "Derby (Royal Crown Derby)", "lat": 52.92, "lon": -1.47,
         "country": "UK", "founded": 1750,
         "type": "Bone china",
         "notes": "Imari patterns and figurines; oldest English china factory still producing"},
        {"name": "Minton (Stoke-on-Trent)", "lat": 53.01, "lon": -2.16,
         "country": "UK", "founded": 1793,
         "type": "Majolica / bone china",
         "notes": "Thomas Minton's factory; Victorian majolica and pate-sur-pate technique"},
        {"name": "Spode (Stoke-on-Trent)", "lat": 53.00, "lon": -2.17,
         "country": "UK", "founded": 1770,
         "type": "Bone china / transfer print",
         "notes": "Josiah Spode perfected bone china formula and blue transfer printing"},
        {"name": "Furstenberg, Germany", "lat": 51.73, "lon": 9.40,
         "country": "Germany", "founded": 1747,
         "type": "Hard-paste porcelain",
         "notes": "Weser Renaissance castle factory; still producing; second oldest German factory"},
        {"name": "Ludwigsburg, Germany", "lat": 48.90, "lon": 9.19,
         "country": "Germany", "founded": 1758,
         "type": "Hard-paste porcelain",
         "notes": "Duke Karl Eugen's factory; rococo figurines; interlaced C mark"},
        {"name": "Frankenthal, Germany", "lat": 49.53, "lon": 8.35,
         "country": "Germany", "founded": 1755,
         "type": "Hard-paste porcelain",
         "notes": "Paul Hannong's factory; exquisite figurines; closed 1799 during French Revolution"},
        {"name": "Hochst, Germany", "lat": 50.10, "lon": 8.55,
         "country": "Germany", "founded": 1746,
         "type": "Hard-paste porcelain / faience",
         "notes": "Electoral wheel mark; charming figurines; revived in 20th century"},
        {"name": "Chelsea, London", "lat": 51.49, "lon": -0.17,
         "country": "UK", "founded": 1745,
         "type": "Soft-paste porcelain",
         "notes": "Red anchor period finest; botanical plates; merged with Derby 1770"},
        {"name": "Bow, London", "lat": 51.53, "lon": 0.00,
         "country": "UK", "founded": 1747,
         "type": "Soft-paste porcelain",
         "notes": "New Canton factory; bone ash formula; blue-and-white Chinese-style designs"},
        {"name": "Vista Alegre, Portugal", "lat": 40.59, "lon": -8.60,
         "country": "Portugal", "founded": 1824,
         "type": "Hard-paste porcelain",
         "notes": "Portugal's premier porcelain; royal commissions; still active in Ilhavo"},
        {"name": "Bing & Grondahl, Copenhagen", "lat": 55.67, "lon": 12.58,
         "country": "Denmark", "founded": 1853,
         "type": "Porcelain figurines",
         "notes": "Christmas plates from 1895; merged with Royal Copenhagen; seagull dinnerware"},
        {"name": "Gustavsberg, Sweden", "lat": 59.33, "lon": 18.39,
         "country": "Sweden", "founded": 1825,
         "type": "Stoneware / porcelain",
         "notes": "Wilhelm Kage and Stig Lindberg Scandinavian modernism; Argenta series"},
        {"name": "Arabia, Helsinki", "lat": 60.21, "lon": 24.98,
         "country": "Finland", "founded": 1873,
         "type": "Stoneware / porcelain",
         "notes": "Kaj Franck and Birger Kaipiainen designs; Finnish modernist ceramics icon"},
        {"name": "Saint-Cloud, France", "lat": 48.85, "lon": 2.22,
         "country": "France", "founded": 1693,
         "type": "Soft-paste porcelain",
         "notes": "Earliest French porcelain factory; blanc de chine imitations; closed 1766"},
        {"name": "Vincennes, France", "lat": 48.85, "lon": 2.44,
         "country": "France", "founded": 1740,
         "type": "Soft-paste porcelain",
         "notes": "Predecessor to Sevres; Madame de Pompadour's patronage; porcelain flowers"},
    ]


# =====================================================================
# 6. PRE-COLUMBIAN POTTERY (28 locations)
# =====================================================================
def _pre_columbian_pottery_data():
    return [
        {"name": "Moche Valley, Peru", "lat": -8.11, "lon": -79.04,
         "country": "Peru", "era": "100-700 AD",
         "type": "Moche portrait vessels",
         "notes": "Realistic portrait stirrup-spout vessels; erotic pottery; warrior-priest imagery"},
        {"name": "Nazca Valley, Peru", "lat": -14.84, "lon": -75.13,
         "country": "Peru", "era": "100 BC-800 AD",
         "type": "Polychrome painted",
         "notes": "Up to 15 colors on a single vessel; trophy head and mythical being imagery"},
        {"name": "Chavin de Huantar, Peru", "lat": -9.59, "lon": -77.18,
         "country": "Peru", "era": "900-200 BC",
         "type": "Stirrup-spout vessels",
         "notes": "Early stirrup-spout form; incised feline and raptor motifs; ceremonial pottery"},
        {"name": "Chan Chan, Peru", "lat": -8.10, "lon": -79.07,
         "country": "Peru", "era": "900-1470 AD",
         "type": "Chimu blackware",
         "notes": "Reduced-fired black pottery; mass-produced in molds; Chimu Empire capital"},
        {"name": "Cusco, Peru", "lat": -13.53, "lon": -71.97,
         "country": "Peru", "era": "1400-1533 AD",
         "type": "Inca aribalo",
         "notes": "Standardized pointed-base aribalo jars; geometric polychrome designs; chicha beer"},
        {"name": "Teotihuacan, Mexico", "lat": 19.69, "lon": -98.84,
         "country": "Mexico", "era": "100 BC-550 AD",
         "type": "Thin Orange ware",
         "notes": "Thin Orange pottery traded across Mesoamerica; cylindrical tripod vases"},
        {"name": "Monte Alban, Mexico", "lat": 17.04, "lon": -96.77,
         "country": "Mexico", "era": "500 BC-800 AD",
         "type": "Zapotec funerary urns",
         "notes": "Elaborate funerary urns with deity figures; Zapotec grey ware tradition"},
        {"name": "Cholula, Mexico", "lat": 19.06, "lon": -98.30,
         "country": "Mexico", "era": "200-1521 AD",
         "type": "Polychrome lacquer ware",
         "notes": "Mixteca-Puebla polychrome style; codex-style painted pottery; largest pyramid base"},
        {"name": "Palenque, Mexico", "lat": 17.48, "lon": -92.05,
         "country": "Mexico", "era": "600-800 AD",
         "type": "Maya polychrome",
         "notes": "Classic Maya palace pottery; painted cylinders depicting courtly scenes"},
        {"name": "Tikal, Guatemala", "lat": 17.22, "lon": -89.62,
         "country": "Guatemala", "era": "300-900 AD",
         "type": "Maya polychrome cylinders",
         "notes": "Elaborate painted cylinder vases with mythology and palace scenes; cacao vessels"},
        {"name": "Copan, Honduras", "lat": 14.84, "lon": -89.14,
         "country": "Honduras", "era": "400-800 AD",
         "type": "Maya painted pottery",
         "notes": "Copador polychrome style; fine-painted bowls exchanged between elite Maya courts"},
        {"name": "Jama-Coaque (Manabi), Ecuador", "lat": 0.30, "lon": -80.10,
         "country": "Ecuador", "era": "350 BC-1531 AD",
         "type": "Figurines & whistles",
         "notes": "Elaborate seated figurines with ornate headdresses; ceramic whistles and stamps"},
        {"name": "Valdivia (Santa Elena), Ecuador", "lat": -2.23, "lon": -80.90,
         "country": "Ecuador", "era": "3500-1800 BC",
         "type": "Earliest American pottery",
         "notes": "Among the oldest known pottery in the Americas; Venus figurines"},
        {"name": "San Agustin, Colombia", "lat": 1.88, "lon": -76.27,
         "country": "Colombia", "era": "100-900 AD",
         "type": "Funerary pottery",
         "notes": "Elaborately modeled pottery placed in megalithic tombs; painted effigy vessels"},
        {"name": "Tairona (Santa Marta), Colombia", "lat": 11.24, "lon": -74.20,
         "country": "Colombia", "era": "200-1600 AD",
         "type": "Tairona black ware",
         "notes": "Burnished black pottery with animal forms; incense burners and bat effigies"},
        {"name": "Marajoara (Marajo Island), Brazil", "lat": -1.00, "lon": -49.50,
         "country": "Brazil", "era": "400-1300 AD",
         "type": "Painted funerary urns",
         "notes": "Large polychrome funerary urns; geometric designs; Amazonian chiefdom pottery"},
        {"name": "Santarem, Brazil", "lat": -2.44, "lon": -54.71,
         "country": "Brazil", "era": "1000-1500 AD",
         "type": "Tapajonic vessels",
         "notes": "Highly decorated vessels with caryatid figures; Tapajos River complex pottery"},
        {"name": "Pueblo Bonito (Chaco Canyon), USA", "lat": 36.06, "lon": -107.96,
         "country": "USA", "era": "850-1150 AD",
         "type": "Ancestral Puebloan",
         "notes": "Black-on-white geometric painted pottery; cylinder jars with cacao residues"},
        {"name": "Mesa Verde, USA", "lat": 37.18, "lon": -108.49,
         "country": "USA", "era": "600-1300 AD",
         "type": "Ancestral Puebloan",
         "notes": "Black-on-white mugs and bowls; corrugated grey utility ware; cliff dwelling sites"},
        {"name": "Mimbres Valley, USA", "lat": 32.90, "lon": -108.00,
         "country": "USA", "era": "1000-1150 AD",
         "type": "Mimbres painted bowls",
         "notes": "Stunning figurative black-on-white bowls depicting animals and mythological scenes"},
        {"name": "Casas Grandes (Paquime), Mexico", "lat": 30.37, "lon": -107.95,
         "country": "Mexico", "era": "1200-1450 AD",
         "type": "Ramos polychrome",
         "notes": "Interlocking geometric painted designs; effigy vessels; Mesoamerican-Southwest link"},
        {"name": "Mata Ortiz, Mexico", "lat": 30.25, "lon": -108.05,
         "country": "Mexico", "era": "1970s onward",
         "type": "Revival pottery",
         "notes": "Juan Quezada revived Casas Grandes pottery tradition; now thriving artisan village"},
        {"name": "Tiwanaku, Bolivia", "lat": -16.55, "lon": -68.67,
         "country": "Bolivia", "era": "500-1000 AD",
         "type": "Kero vessels",
         "notes": "Puma and condor motif drinking keros; polychrome portrait vessels"},
        {"name": "Wari (Ayacucho), Peru", "lat": -13.16, "lon": -74.22,
         "country": "Peru", "era": "600-1000 AD",
         "type": "Oversized face-neck jars",
         "notes": "Large ceremonial jars with face-neck design; polychrome trophy head iconography"},
        {"name": "Recuay (Ancash), Peru", "lat": -9.53, "lon": -77.46,
         "country": "Peru", "era": "200 BC-600 AD",
         "type": "Kaolin white ware",
         "notes": "Distinctive white kaolin-based pottery with modeled warriors and llamas"},
        {"name": "Shipibo-Conibo (Ucayali), Peru", "lat": -8.38, "lon": -74.53,
         "country": "Peru", "era": "Pre-contact to present",
         "type": "Geometric painted pottery",
         "notes": "Intricate geometric designs related to ayahuasca visions; living tradition"},
        {"name": "La Tolita, Ecuador", "lat": 1.27, "lon": -78.97,
         "country": "Ecuador", "era": "600 BC-400 AD",
         "type": "Figurines & masks",
         "notes": "Gold and ceramic combined pieces; elaborate deity masks and figurines"},
        {"name": "Capacha, Mexico", "lat": 19.37, "lon": -103.69,
         "country": "Mexico", "era": "1500 BC",
         "type": "Earliest W. Mexico pottery",
         "notes": "Stirrup-spout vessels suggesting ancient Pacific contact; earliest Western Mexican pottery"},
    ]


# =====================================================================
# 7. AFRICAN POTTERY TRADITIONS (28 locations)
# =====================================================================
def _african_pottery_traditions_data():
    return [
        {"name": "Nok, Nigeria", "lat": 9.67, "lon": 8.00,
         "country": "Nigeria", "era": "500 BC-200 AD",
         "type": "Terracotta sculpture",
         "notes": "Earliest sub-Saharan sculpture tradition; life-sized terracotta heads"},
        {"name": "Ife, Nigeria", "lat": 7.49, "lon": 4.55,
         "country": "Nigeria", "era": "12th-14th c.",
         "type": "Terracotta & bronze heads",
         "notes": "Naturalistic royal portraits in terracotta; Yoruba artistic tradition"},
        {"name": "Djenne-Djenno, Mali", "lat": 13.91, "lon": -4.55,
         "country": "Mali", "era": "250 BC-1400 AD",
         "type": "Terracotta figurines",
         "notes": "Oldest known sub-Saharan city; equestrian figures and kneeling terracottas"},
        {"name": "Suleja, Nigeria", "lat": 9.18, "lon": 7.18,
         "country": "Nigeria", "era": "Traditional",
         "type": "Gbagyi water pots",
         "notes": "Gbagyi women potters; large water storage pots with incised geometric decoration"},
        {"name": "Bamessing, Cameroon", "lat": 6.00, "lon": 10.28,
         "country": "Cameroon", "era": "Traditional",
         "type": "Prestige pottery",
         "notes": "Royal prestige vessels for Grassfields kingdoms; palm wine drinking vessels"},
        {"name": "Segou, Mali", "lat": 13.44, "lon": -5.67,
         "country": "Mali", "era": "Traditional",
         "type": "Bamana pottery",
         "notes": "Bamana women potters; large decorated jars; ritual ceramic objects"},
        {"name": "Lozi (Barotseland), Zambia", "lat": -15.30, "lon": 23.13,
         "country": "Zambia", "era": "Traditional",
         "type": "Black burnished ware",
         "notes": "Lozi women create distinctive black-burnished pottery using graphite"},
        {"name": "Vume, Ghana", "lat": 6.38, "lon": 0.37,
         "country": "Ghana", "era": "Traditional",
         "type": "Ewe pottery",
         "notes": "Ewe potters produce large water coolers and ritual ceramic figures"},
        {"name": "Nupe (Bida), Nigeria", "lat": 9.08, "lon": 6.02,
         "country": "Nigeria", "era": "Traditional",
         "type": "Nupe pottery",
         "notes": "Complex sgrafitto decoration; large water storage vessels; women potters"},
        {"name": "Kerma, Sudan", "lat": 19.60, "lon": 30.41,
         "country": "Sudan", "era": "2500-1500 BC",
         "type": "Nubian black-topped ware",
         "notes": "Ancient Nubian red-and-black pottery; among the finest prehistoric African ceramics"},
        {"name": "Meroe, Sudan", "lat": 16.94, "lon": 33.75,
         "country": "Sudan", "era": "300 BC-350 AD",
         "type": "Meroitic painted ware",
         "notes": "Fine painted pottery with Egyptian and African motifs; Kushite royal necropolis"},
        {"name": "Faras, Sudan", "lat": 22.20, "lon": 31.50,
         "country": "Sudan", "era": "Nubian Christian period",
         "type": "Christian Nubian ware",
         "notes": "Painted Christian pottery from medieval Nubia; cross and floral motifs"},
        {"name": "Shai Hills, Ghana", "lat": 5.95, "lon": -0.07,
         "country": "Ghana", "era": "Traditional",
         "type": "Shai pottery",
         "notes": "Ga-Dangme women potters; ritual and domestic pottery tradition"},
        {"name": "Limpopo (Venda), South Africa", "lat": -22.97, "lon": 30.45,
         "country": "South Africa", "era": "Traditional",
         "type": "Venda pottery",
         "notes": "VhaVenda women potters; graphite-burnished ceremonial vessels"},
        {"name": "Lydenburg, South Africa", "lat": -25.10, "lon": 30.47,
         "country": "South Africa", "era": "500 AD",
         "type": "Lydenburg Heads",
         "notes": "Earliest known southern African sculpture; seven terracotta heads found in 1957"},
        {"name": "KwaZulu-Natal, South Africa", "lat": -29.86, "lon": 31.03,
         "country": "South Africa", "era": "Traditional",
         "type": "Zulu beer pots",
         "notes": "Ukhamba beer pots with incised and burnished decoration; amasumpa raised bumps"},
        {"name": "Mopti, Mali", "lat": 14.49, "lon": -4.19,
         "country": "Mali", "era": "Traditional",
         "type": "Fulani pottery",
         "notes": "Fulani/Peul women potters of the inner Niger delta; milk vessels and cooking pots"},
        {"name": "Katiola, Cote d'Ivoire", "lat": 8.14, "lon": -5.10,
         "country": "Cote d'Ivoire", "era": "Traditional",
         "type": "Mangoro pottery",
         "notes": "Major pottery center; large decorated jars and cooking vessels; women potters"},
        {"name": "Axum, Ethiopia", "lat": 14.13, "lon": 38.73,
         "country": "Ethiopia", "era": "100 BC-700 AD",
         "type": "Aksumite pottery",
         "notes": "Red-burnished and painted Aksumite wares; trade connections to Roman world"},
        {"name": "Harar, Ethiopia", "lat": 9.31, "lon": 42.12,
         "country": "Ethiopia", "era": "Traditional",
         "type": "Harari basketry pottery",
         "notes": "Brightly colored basket-wrapped pottery; jebena coffee pots"},
        {"name": "Chibale, Zambia", "lat": -14.20, "lon": 29.80,
         "country": "Zambia", "era": "Traditional",
         "type": "Lala pottery",
         "notes": "Lala women potters using coil-and-scrape technique; ritual mbusa vessels"},
        {"name": "Timbuktu, Mali", "lat": 16.77, "lon": -3.01,
         "country": "Mali", "era": "Medieval",
         "type": "Saharan trade pottery",
         "notes": "Trans-Saharan trade brought diverse ceramic traditions; glazed ware imports"},
        {"name": "Igbo-Ukwu, Nigeria", "lat": 6.02, "lon": 7.02,
         "country": "Nigeria", "era": "9th c. AD",
         "type": "Ritual ceramics",
         "notes": "Elaborate pottery found alongside famous bronzes; ritual regalia vessels"},
        {"name": "Lalibela, Ethiopia", "lat": 12.03, "lon": 39.04,
         "country": "Ethiopia", "era": "12th c. AD",
         "type": "Ethiopian pottery",
         "notes": "Traditional pottery production alongside rock-hewn churches; mesob pot forms"},
        {"name": "Great Zimbabwe", "lat": -20.27, "lon": 30.93,
         "country": "Zimbabwe", "era": "11th-15th c.",
         "type": "Graphite-burnished ware",
         "notes": "Graphite-burnished pottery and soapstone birds; Zimbabwe tradition pottery"},
        {"name": "Kilwa Kisiwani, Tanzania", "lat": -8.96, "lon": 39.52,
         "country": "Tanzania", "era": "11th-15th c.",
         "type": "Swahili coast pottery",
         "notes": "Local and imported pottery in Swahili trade port; Chinese celadon sherds found"},
        {"name": "Mombasa, Kenya", "lat": -4.05, "lon": 39.67,
         "country": "Kenya", "era": "Medieval",
         "type": "Swahili pottery",
         "notes": "Local Swahili pottery alongside Chinese, Persian and Indian imports"},
        {"name": "Mapungubwe, South Africa", "lat": -22.19, "lon": 29.25,
         "country": "South Africa", "era": "1075-1220 AD",
         "notes": "First class society in southern Africa; pottery found with gold artifacts",
         "type": "Iron Age pottery"},
    ]


# =====================================================================
# 8. DELFT & MAJOLICA CENTERS (28 locations)
# =====================================================================
def _delft_majolica_centers_data():
    return [
        {"name": "Delft, Netherlands", "lat": 52.01, "lon": 4.36,
         "country": "Netherlands", "era": "1650s onward",
         "type": "Delftware",
         "notes": "Blue-and-white tin-glazed earthenware imitating Chinese porcelain; De Porceleyne Fles"},
        {"name": "Haarlem, Netherlands", "lat": 52.38, "lon": 4.64,
         "country": "Netherlands", "era": "1570s",
         "type": "Early Delftware",
         "notes": "Italian maiolica potters settled here; precursor to Delft tradition"},
        {"name": "Makkum, Netherlands", "lat": 53.06, "lon": 5.40,
         "country": "Netherlands", "era": "1594",
         "type": "Tichelaar Makkum",
         "notes": "Royal Tichelaar Makkum; oldest company in the Netherlands; Frisian tiles"},
        {"name": "Faenza, Italy", "lat": 44.29, "lon": 11.88,
         "country": "Italy", "era": "15th c.",
         "type": "Faience / maiolica",
         "notes": "Word 'faience' derives from Faenza; International Museum of Ceramics"},
        {"name": "Deruta, Italy", "lat": 42.98, "lon": 12.42,
         "country": "Italy", "era": "14th c. onward",
         "type": "Lustre maiolica",
         "notes": "Golden lustre and blue-and-white maiolica; still an active pottery town"},
        {"name": "Gubbio, Italy", "lat": 43.35, "lon": 12.58,
         "country": "Italy", "era": "16th c.",
         "type": "Ruby lustre maiolica",
         "notes": "Maestro Giorgio's ruby lustre technique; most prized Italian maiolica"},
        {"name": "Urbino, Italy", "lat": 43.72, "lon": 12.64,
         "country": "Italy", "era": "16th c.",
         "type": "Istoriato maiolica",
         "notes": "Narrative painted maiolica (istoriato); Nicola da Urbino and Xanto Avelli masters"},
        {"name": "Castelli, Italy", "lat": 42.49, "lon": 13.72,
         "country": "Italy", "era": "16th c.",
         "type": "Painted maiolica",
         "notes": "Grue and Gentili families; landscape-painted maiolica plates; Abruzzo tradition"},
        {"name": "Montelupo Fiorentino, Italy", "lat": 43.73, "lon": 11.02,
         "country": "Italy", "era": "14th-17th c.",
         "type": "Tuscan maiolica",
         "notes": "Major Florentine maiolica center; bold arlecchino (harlequin) painted patterns"},
        {"name": "Caltagirone, Sicily", "lat": 37.24, "lon": 14.51,
         "country": "Italy", "era": "Medieval onward",
         "type": "Sicilian maiolica",
         "notes": "142-step ceramic staircase; tradition from Arab through Norman to baroque periods"},
        {"name": "Lisbon, Portugal", "lat": 38.72, "lon": -9.14,
         "country": "Portugal", "era": "16th c. onward",
         "type": "Azulejos",
         "notes": "Azulejo tile panels covering entire buildings; Museu Nacional do Azulejo"},
        {"name": "Porto, Portugal", "lat": 41.16, "lon": -8.63,
         "country": "Portugal", "era": "18th c.",
         "type": "Blue azulejos",
         "notes": "Sao Bento Railway Station; Igreja do Carmo; blue-and-white azulejo narratives"},
        {"name": "Aveiro, Portugal", "lat": 40.64, "lon": -8.65,
         "country": "Portugal", "era": "18th c.",
         "type": "Azulejo panels",
         "notes": "Art Nouveau azulejo-covered buildings; railway station historical panels"},
        {"name": "Talavera de la Reina, Spain", "lat": 39.96, "lon": -4.83,
         "country": "Spain", "era": "16th c.",
         "type": "Talavera pottery",
         "notes": "Royal tin-glazed pottery; influenced Mexican Talavera; UNESCO Intangible Heritage"},
        {"name": "Manises, Spain", "lat": 39.49, "lon": -0.46,
         "country": "Spain", "era": "14th-15th c.",
         "type": "Hispano-Moresque lustre",
         "notes": "Golden lustre pottery exported across Europe; Mudéjar tradition apex"},
        {"name": "Puebla, Mexico", "lat": 19.04, "lon": -98.20,
         "country": "Mexico", "era": "16th c. onward",
         "type": "Talavera poblana",
         "notes": "Spanish Talavera tradition transplanted; UNESCO protected; vivid polychrome tiles"},
        {"name": "Strasbourg, France", "lat": 48.57, "lon": 7.75,
         "country": "France", "era": "18th c.",
         "type": "Hannong faience",
         "notes": "Hannong family faience with naturalistically painted flowers; trompe-l'oeil"},
        {"name": "Rouen, France", "lat": 49.44, "lon": 1.10,
         "country": "France", "era": "17th-18th c.",
         "type": "Rouen faience",
         "notes": "Blue-and-white 'style rayonnant' radiating patterns; major French faience center"},
        {"name": "Nevers, France", "lat": 46.99, "lon": 3.16,
         "country": "France", "era": "16th c.",
         "type": "Nevers faience",
         "notes": "Italian potters brought maiolica technique; distinctive bleu persan decoration"},
        {"name": "Moustiers-Sainte-Marie, France", "lat": 43.85, "lon": 6.22,
         "country": "France", "era": "17th-18th c.",
         "type": "Moustiers faience",
         "notes": "Delicate blue-painted faience; Clerissy family workshop; grotesque decoration"},
        {"name": "Quimper, France", "lat": 48.00, "lon": -4.10,
         "country": "France", "era": "1690",
         "type": "Quimper faience",
         "notes": "Breton faience with peasant figures; HB-Henriot factory still producing"},
        {"name": "Bassano del Grappa, Italy", "lat": 45.77, "lon": 11.73,
         "country": "Italy", "era": "16th c.",
         "type": "Veneto maiolica",
         "notes": "Maiolica production center in the Veneto; drug jars and pharmacy ware"},
        {"name": "Vietri sul Mare, Italy", "lat": 40.67, "lon": 14.73,
         "country": "Italy", "era": "15th c.",
         "type": "Amalfi Coast ceramics",
         "notes": "Colorful hand-painted tiles and tableware; German artists colony in 1920s"},
        {"name": "Alcobaca, Portugal", "lat": 39.55, "lon": -8.98,
         "country": "Portugal", "era": "18th c.",
         "type": "Portuguese faience",
         "notes": "Monastery region faience tradition; blue-and-white Portuguese pottery"},
        {"name": "Nove, Italy", "lat": 45.72, "lon": 11.68,
         "country": "Italy", "era": "18th c.",
         "type": "Veneto maiolica & porcelain",
         "notes": "Antonibon factory; transition from maiolica to porcelain; museo della ceramica"},
        {"name": "Arnhem, Netherlands", "lat": 51.98, "lon": 5.91,
         "country": "Netherlands", "era": "17th c.",
         "type": "Delftware",
         "notes": "Smaller Delftware production center; tiles and domestic wares"},
        {"name": "Sintra, Portugal", "lat": 38.80, "lon": -9.39,
         "country": "Portugal", "era": "15th-16th c.",
         "type": "Pena Palace azulejos",
         "notes": "National Palace moorish and manueline tiles; green and rope-twist patterns"},
        {"name": "Santo Stefano di Camastra, Sicily", "lat": 38.01, "lon": 14.35,
         "country": "Italy", "era": "17th c.",
         "type": "Sicilian painted tiles",
         "notes": "Coastal Sicilian ceramics town; colorful balcony tiles and decorative panels"},
    ]


# =====================================================================
# 9. MODERN STUDIO POTTERY (28 locations)
# =====================================================================
def _modern_studio_pottery_data():
    return [
        {"name": "St Ives, Cornwall, UK", "lat": 50.21, "lon": -5.48,
         "country": "UK", "era": "1920",
         "type": "Leach Pottery",
         "notes": "Bernard Leach and Shoji Hamada founded the Studio Pottery movement here"},
        {"name": "Mashiko, Japan", "lat": 36.47, "lon": 140.10,
         "country": "Japan", "era": "1930",
         "type": "Mingei pottery",
         "notes": "Hamada Shoji's home; mingei (folk craft) philosophy shaped global ceramics"},
        {"name": "Cranbrook, Michigan, USA", "lat": 42.57, "lon": -83.39,
         "country": "USA", "era": "1932",
         "type": "Art pottery education",
         "notes": "Maija Grotell taught generations of American ceramic artists here"},
        {"name": "Alfred, New York, USA", "lat": 42.25, "lon": -77.79,
         "country": "USA", "era": "1900",
         "type": "Academic ceramics",
         "notes": "Alfred University School of Ceramics; oldest ceramic engineering school in the US"},
        {"name": "Black Mountain College, NC, USA", "lat": 35.62, "lon": -82.47,
         "country": "USA", "era": "1933",
         "type": "Experimental ceramics",
         "notes": "Josef Albers, Robert Turner; interdisciplinary approach influenced ceramic art"},
        {"name": "Ojai, California, USA", "lat": 34.45, "lon": -119.24,
         "country": "USA", "era": "1950s",
         "type": "California studio pottery",
         "notes": "Beatrice Wood 'Mama of Dada' worked here; lustre glazes and figurative vessels"},
        {"name": "Vallauris, France", "lat": 43.58, "lon": 7.05,
         "country": "France", "era": "1948",
         "type": "Picasso ceramics",
         "notes": "Pablo Picasso transformed this town; Madoura pottery; ceramic art revival"},
        {"name": "Voulkos Studio (Los Angeles), USA", "lat": 34.05, "lon": -118.24,
         "country": "USA", "era": "1954",
         "type": "Abstract Expressionist ceramics",
         "notes": "Peter Voulkos broke ceramics from craft into fine art; Otis Art Institute"},
        {"name": "Farnham, Surrey, UK", "lat": 51.21, "lon": -0.80,
         "country": "UK", "era": "1948",
         "type": "Academic ceramics",
         "notes": "West Surrey College of Art; Henry Hammond, Colin Pearson taught here"},
        {"name": "Bizen, Japan", "lat": 34.74, "lon": 134.18,
         "country": "Japan", "era": "20th c. revival",
         "type": "Living National Treasures",
         "notes": "Fujiwara Kei and Kaneshige Toyo revived Bizen as fine art; National Treasures"},
        {"name": "Shigaraki, Japan", "lat": 34.85, "lon": 136.07,
         "country": "Japan", "era": "Modern revival",
         "type": "Contemporary sculpture",
         "notes": "MIHO Museum and Shigaraki Ceramic Cultural Park; large-scale ceramic sculpture"},
        {"name": "Stoke-on-Trent, UK", "lat": 53.00, "lon": -2.18,
         "country": "UK", "era": "Continuous",
         "type": "Industrial & studio pottery",
         "notes": "The Potteries capital; six towns of ceramics; studio potters alongside industry"},
        {"name": "Tokoname, Japan", "lat": 34.88, "lon": 136.85,
         "country": "Japan", "era": "Modern",
         "type": "Contemporary teapots",
         "notes": "INAX ceramics research; modern artists reinterpreting traditional kyusu forms"},
        {"name": "Icheon, South Korea", "lat": 37.27, "lon": 127.44,
         "country": "South Korea", "era": "20th c.",
         "type": "Celadon revival",
         "notes": "UNESCO City of Crafts; revived Goryeo celadon tradition; ceramics village"},
        {"name": "Bat Trang, Vietnam", "lat": 20.97, "lon": 105.91,
         "country": "Vietnam", "era": "15th c. onward",
         "type": "Vietnamese ceramics",
         "notes": "Historic ceramics village near Hanoi; 700-year tradition; modern tourist workshops"},
        {"name": "Yingge, Taiwan", "lat": 24.95, "lon": 121.35,
         "country": "Taiwan", "era": "1805",
         "type": "Taiwanese ceramics",
         "notes": "200+ pottery studios; New Taipei Ceramics Museum; Old Street pottery market"},
        {"name": "Seagrove, North Carolina, USA", "lat": 35.55, "lon": -79.78,
         "country": "USA", "era": "1700s",
         "type": "Folk pottery tradition",
         "notes": "Oldest pottery-making community in the US; 80+ potters along Pottery Highway"},
        {"name": "Penland, North Carolina, USA", "lat": 35.91, "lon": -82.10,
         "country": "USA", "era": "1929",
         "type": "Craft school",
         "notes": "Penland School of Craft; influential ceramics residency and workshop programs"},
        {"name": "Helena, Montana, USA", "lat": 46.60, "lon": -112.04,
         "country": "USA", "era": "1950s",
         "type": "Archie Bray Foundation",
         "notes": "Archie Bray Foundation for the Ceramic Arts; Voulkos and Autio began here"},
        {"name": "Jingdezhen, China (modern)", "lat": 29.27, "lon": 117.18,
         "country": "China", "era": "21st c. revival",
         "type": "International residencies",
         "notes": "Pottery Workshop residency attracts global artists; ancient city reinvented"},
        {"name": "Aberystwyth, Wales, UK", "lat": 52.42, "lon": -4.08,
         "country": "UK", "era": "1960s",
         "type": "Welsh studio pottery",
         "notes": "Aberystwyth Arts Centre ceramics gallery; Phil Rogers and Welsh pottery tradition"},
        {"name": "Shiwan, Guangdong, China", "lat": 23.01, "lon": 113.10,
         "country": "China", "era": "Contemporary",
         "type": "Figurative ceramics",
         "notes": "Ancient kiln district reinvented with contemporary artists and galleries"},
        {"name": "Seto, Japan", "lat": 35.22, "lon": 137.08,
         "country": "Japan", "era": "Modern",
         "type": "Contemporary setomono",
         "notes": "Annual ceramics festival draws 500,000; modern interpretations of ancient traditions"},
        {"name": "Grottaglie, Italy", "lat": 40.54, "lon": 17.44,
         "country": "Italy", "era": "Medieval onward",
         "type": "Pugliese ceramics",
         "notes": "Quartiere delle ceramiche with dozens of workshops; traditional and contemporary"},
        {"name": "Boleslawiec, Poland", "lat": 51.26, "lon": 15.57,
         "country": "Poland", "era": "14th c. onward",
         "type": "Bunzlau pottery",
         "notes": "Stamped peacock-eye pattern stoneware; annual ceramics festival; export worldwide"},
        {"name": "Westerwald, Germany", "lat": 50.55, "lon": 7.85,
         "country": "Germany", "era": "16th c.",
         "type": "Salt-glazed stoneware",
         "notes": "Kannenbacker region; blue-grey salt-glazed stoneware tradition; Hohr-Grenzhausen"},
        {"name": "Gmunden, Austria", "lat": 47.92, "lon": 13.80,
         "country": "Austria", "era": "16th c.",
         "type": "Gmundner ceramics",
         "notes": "Distinctive green-flamed pattern on white; Traunsee lakeside ceramics tradition"},
        {"name": "Sifnos, Greece", "lat": 36.97, "lon": 24.72,
         "country": "Greece", "era": "Ancient to present",
         "type": "Cycladic pottery",
         "notes": "Island pottery tradition since antiquity; chimney pot designs; tourist revival"},
    ]


# =====================================================================
# 10. CERAMIC MUSEUMS WORLDWIDE (30 locations)
# =====================================================================
def _ceramic_museums_worldwide_data():
    return [
        {"name": "Victoria & Albert Museum, London", "lat": 51.50, "lon": -0.17,
         "country": "UK", "founded": 1852,
         "type": "Comprehensive ceramics",
         "notes": "Largest ceramics gallery in the world; 36,000+ objects from all periods and regions"},
        {"name": "Musee National de Ceramique, Sevres", "lat": 48.83, "lon": 2.21,
         "country": "France", "founded": 1824,
         "type": "French & world ceramics",
         "notes": "Attached to Sevres Manufactory; 50,000 pieces spanning 5,000 years"},
        {"name": "Museo Internazionale delle Ceramiche, Faenza", "lat": 44.29, "lon": 11.88,
         "country": "Italy", "founded": 1908,
         "type": "International maiolica",
         "notes": "UNESCO designation; Picasso, Matisse, Chagall donated ceramic works"},
        {"name": "National Palace Museum, Taipei", "lat": 25.10, "lon": 121.55,
         "country": "Taiwan", "founded": 1925,
         "type": "Chinese imperial ceramics",
         "notes": "Finest Song dynasty ceramics collection; Ru ware and Qing imperial porcelain"},
        {"name": "Jingdezhen Ceramic Museum", "lat": 29.27, "lon": 117.18,
         "country": "China", "founded": 1954,
         "type": "Chinese porcelain history",
         "notes": "Ancient kiln ruins and comprehensive porcelain history in the porcelain capital"},
        {"name": "Shanghai Museum", "lat": 31.23, "lon": 121.47,
         "country": "China", "founded": 1952,
         "type": "Chinese ceramics gallery",
         "notes": "Major Chinese ceramics gallery; Tang sancai to Qing famille rose masterpieces"},
        {"name": "Zwinger (Porzellansammlung), Dresden", "lat": 51.05, "lon": 13.73,
         "country": "Germany", "founded": 1715,
         "type": "Meissen & Asian porcelain",
         "notes": "Augustus the Strong's porcelain obsession; 20,000 pieces of Meissen and Asian ware"},
        {"name": "Hetjens Museum, Dusseldorf", "lat": 51.23, "lon": 6.77,
         "country": "Germany", "founded": 1909,
         "type": "8,000 years of ceramics",
         "notes": "German Museum of Ceramics; covers 8,000 years from prehistoric to contemporary"},
        {"name": "Museu Nacional do Azulejo, Lisbon", "lat": 38.73, "lon": -9.11,
         "country": "Portugal", "founded": 1965,
         "type": "Portuguese tiles (azulejos)",
         "notes": "In Madre de Deus Convent; 500 years of Portuguese tile art history"},
        {"name": "Museum of Ceramic Art, Hyogo (MCAH)", "lat": 35.05, "lon": 135.05,
         "country": "Japan", "founded": 2005,
         "type": "Ancient to modern ceramics",
         "notes": "Largest ceramics museum in western Japan; Tanba ware and global collection"},
        {"name": "Arita Porcelain Park Museum", "lat": 33.20, "lon": 129.88,
         "country": "Japan", "founded": 1996,
         "type": "Arita/Imari porcelain",
         "notes": "History of Japanese porcelain with European-influenced architecture"},
        {"name": "Museum Princessehof, Leeuwarden", "lat": 53.20, "lon": 5.80,
         "country": "Netherlands", "founded": 1917,
         "type": "Asian & Dutch ceramics",
         "notes": "Dutch national ceramics museum; Nanne Ottema's Asian collection"},
        {"name": "Potteries Museum, Stoke-on-Trent", "lat": 53.03, "lon": -2.18,
         "country": "UK", "founded": 1981,
         "type": "Staffordshire pottery",
         "notes": "World's greatest Staffordshire pottery collection; Spitfire gallery"},
        {"name": "Gardiner Museum, Toronto", "lat": 43.67, "lon": -79.39,
         "country": "Canada", "founded": 1984,
         "type": "European & pre-Columbian",
         "notes": "Only museum in Canada dedicated to ceramics; Mesoamerican and European porcelain"},
        {"name": "Musee Ariana, Geneva", "lat": 46.22, "lon": 6.14,
         "country": "Switzerland", "founded": 1884,
         "type": "Swiss & world ceramics",
         "notes": "20,000 objects; European porcelain, Islamic ceramics and Swiss stoneware"},
        {"name": "Rijksmuseum, Amsterdam", "lat": 52.36, "lon": 4.88,
         "country": "Netherlands", "founded": 1800,
         "type": "Delftware collection",
         "notes": "Exceptional Delftware collection; VOC-era Chinese export porcelain"},
        {"name": "Topkapi Palace, Istanbul", "lat": 41.01, "lon": 28.98,
         "country": "Turkey", "founded": 1924,
         "type": "Chinese & Iznik ceramics",
         "notes": "10,700 Chinese ceramics and Iznik tiles; second largest Chinese porcelain collection"},
        {"name": "Metropolitan Museum of Art, New York", "lat": 40.78, "lon": -73.96,
         "country": "USA", "founded": 1870,
         "type": "Global ceramics",
         "notes": "Comprehensive ceramics across departments; Islamic, Asian, European, American"},
        {"name": "Freer Gallery of Art, Washington DC", "lat": 38.89, "lon": -77.03,
         "country": "USA", "founded": 1923,
         "type": "Asian ceramics",
         "notes": "Charles Lang Freer's collection of Chinese and Japanese ceramics; Smithsonian"},
        {"name": "Museo de la Ceramica, Barcelona", "lat": 41.39, "lon": 2.15,
         "country": "Spain", "founded": 1966,
         "type": "Spanish ceramics",
         "notes": "Hispano-Moresque lustre ware; Catalan traditions; now part of Museu del Disseny"},
        {"name": "Iznik Foundation Museum, Istanbul", "lat": 41.01, "lon": 28.96,
         "country": "Turkey", "founded": 1993,
         "type": "Iznik tile revival",
         "notes": "Reviving traditional Iznik tile techniques; workshops and museum exhibition"},
        {"name": "Joseon White Porcelain Museum, Gwangju", "lat": 37.36, "lon": 127.32,
         "country": "South Korea", "founded": 2002,
         "type": "Korean white porcelain",
         "notes": "Site of Joseon dynasty royal kilns; Bunwon-ri kiln excavation artifacts"},
        {"name": "National Museum of Ceramics, Valencia", "lat": 39.47, "lon": -0.37,
         "country": "Spain", "founded": 1947,
         "type": "Spanish ceramics",
         "notes": "Gonzalez Marti Museum in Marquis de Dos Aguas Palace; 5,000+ pieces"},
        {"name": "Korean Ceramic Museum, Icheon", "lat": 37.27, "lon": 127.44,
         "country": "South Korea", "founded": 2002,
         "type": "Korean celadon & porcelain",
         "notes": "Goryeo celadon and Joseon buncheong; annual World Ceramics Biennale"},
        {"name": "Museu da Ceramica, Caldas da Rainha", "lat": 39.41, "lon": -9.14,
         "country": "Portugal", "founded": 1983,
         "type": "Portuguese art pottery",
         "notes": "Rafael Bordallo Pinheiro's naturalistic ceramics; Portuguese faience history"},
        {"name": "Keramiekmuseum, Tegelen", "lat": 51.34, "lon": 6.14,
         "country": "Netherlands", "founded": 1970,
         "type": "Dutch & industrial ceramics",
         "notes": "Limburg ceramics tradition; brickmaking and decorative tile history"},
        {"name": "Seto Ceramic & Glass Art Center", "lat": 35.22, "lon": 137.08,
         "country": "Japan", "founded": 2005,
         "type": "Japanese ceramics",
         "notes": "Modern gallery in historic Seto kiln district; contemporary ceramic art exhibitions"},
        {"name": "Museo de la Talavera, Puebla", "lat": 19.04, "lon": -98.20,
         "country": "Mexico", "founded": 1990,
         "type": "Talavera pottery",
         "notes": "History of Puebla Talavera; production process and historic pieces"},
        {"name": "Museum of Islamic Art, Doha", "lat": 25.29, "lon": 51.54,
         "country": "Qatar", "founded": 2008,
         "type": "Islamic ceramics",
         "notes": "I.M. Pei building; exceptional Islamic pottery, lustre ware, and Iznik tiles"},
        {"name": "Musee des Arts Decoratifs, Paris", "lat": 48.86, "lon": 2.33,
         "country": "France", "founded": 1905,
         "type": "Decorative ceramics",
         "notes": "French faience, porcelain, and Art Nouveau ceramics in the Louvre wing"},
    ]


# =====================================================================
# DATA LOADER DISPATCH
# =====================================================================
def _load_mode_data(mode: str) -> list:
    """Return the list of location dicts for a given mode."""
    dispatch = {
        "Chinese Porcelain Kilns": _chinese_porcelain_kilns_data,
        "Japanese Pottery Traditions": _japanese_pottery_traditions_data,
        "Ancient Greek Pottery Sites": _ancient_greek_pottery_sites_data,
        "Islamic Tile Art Centers": _islamic_tile_art_centers_data,
        "European Porcelain Factories": _european_porcelain_factories_data,
        "Pre-Columbian Pottery": _pre_columbian_pottery_data,
        "African Pottery Traditions": _african_pottery_traditions_data,
        "Delft & Majolica Centers": _delft_majolica_centers_data,
        "Modern Studio Pottery": _modern_studio_pottery_data,
        "Ceramic Museums Worldwide": _ceramic_museums_worldwide_data,
    }
    fn = dispatch.get(mode)
    return fn() if fn else []


# =====================================================================
# POPUP BUILDER
# =====================================================================
def _build_popup(row: dict, mode: str, color: str) -> str:
    """Build a styled HTML popup for a folium CircleMarker."""
    name = html_module.escape(str(row.get("name", "")))
    country = html_module.escape(str(row.get("country", "")))
    notes = html_module.escape(str(row.get("notes", "")))

    extra_lines = []
    if "era" in row and row["era"]:
        extra_lines.append(
            f"<b>Era:</b> {html_module.escape(str(row['era']))}"
        )
    if "type" in row and row["type"]:
        extra_lines.append(
            f"<b>Type:</b> {html_module.escape(str(row['type']))}"
        )
    if "founded" in row and row["founded"] is not None:
        extra_lines.append(
            f"<b>Founded:</b> {html_module.escape(str(row['founded']))}"
        )

    extra_html = "<br>".join(extra_lines)
    if extra_html:
        extra_html = f"<br>{extra_html}"

    popup_html = (
        f'<div style="font-family:Segoe UI,Arial,sans-serif;min-width:220px;'
        f'max-width:310px;background:#1a2235;color:#e8ecf4;'
        f'padding:10px 14px;border-radius:8px;'
        f'border:1px solid {color}50;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.4);">'
        f'<div style="font-size:13px;font-weight:700;color:{color};'
        f'margin-bottom:5px;line-height:1.3;">{name}</div>'
        f'<div style="font-size:11px;color:#8b97b0;margin-bottom:4px;">'
        f'{country}</div>'
        f'{extra_html}'
        f'<div style="font-size:11px;margin-top:6px;color:#a0aec0;'
        f'line-height:1.45;">{notes}</div>'
        f'</div>'
    )
    return popup_html


# =====================================================================
# FOLIUM DARK MAP BUILDER
# =====================================================================
def _build_map(df: pd.DataFrame, mode: str) -> folium.Map:
    """Build a CartoDB dark_matter folium map with styled CircleMarkers."""
    color = MODE_COLORS.get(mode, "#06b6d4")

    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    lat_spread = df["lat"].max() - df["lat"].min()
    lon_spread = df["lon"].max() - df["lon"].min()
    total_spread = lat_spread + lon_spread
    if total_spread > 200:
        zoom = 2
    elif total_spread > 100:
        zoom = 2
    elif total_spread > 50:
        zoom = 3
    elif total_spread > 20:
        zoom = 4
    else:
        zoom = 5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    for _, row in df.iterrows():
        popup_content = _build_popup(row.to_dict(), mode, color)
        tooltip_text = html_module.escape(str(row.get("name", "")))

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.70,
            weight=2,
            popup=folium.Popup(popup_content, max_width=330),
            tooltip=tooltip_text,
        ).add_to(m)

    return m


# =====================================================================
# STATS DASHBOARD
# =====================================================================
def _render_stats(df: pd.DataFrame, mode: str):
    """Render a row of st.metric widgets summarizing the current dataset."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Locations", len(df))

    with col2:
        n_countries = df["country"].nunique() if "country" in df.columns else 0
        st.metric("Countries", n_countries)

    with col3:
        if mode == "Chinese Porcelain Kilns" and "type" in df.columns:
            st.metric("Kiln Types", df["type"].nunique())
        elif mode == "Japanese Pottery Traditions" and "type" in df.columns:
            st.metric("Styles", df["type"].nunique())
        elif mode == "Ancient Greek Pottery Sites" and "era" in df.columns:
            st.metric("Eras Covered", df["era"].nunique())
        elif mode == "Islamic Tile Art Centers" and "era" in df.columns:
            st.metric("Periods", df["era"].nunique())
        elif mode == "European Porcelain Factories" and "founded" in df.columns:
            oldest = int(df["founded"].min())
            st.metric("Oldest Factory", str(oldest))
        elif mode == "Pre-Columbian Pottery" and "era" in df.columns:
            st.metric("Time Periods", df["era"].nunique())
        elif mode == "African Pottery Traditions" and "type" in df.columns:
            st.metric("Traditions", df["type"].nunique())
        elif mode == "Delft & Majolica Centers" and "type" in df.columns:
            st.metric("Ware Types", df["type"].nunique())
        elif mode == "Modern Studio Pottery" and "type" in df.columns:
            st.metric("Movements", df["type"].nunique())
        elif mode == "Ceramic Museums Worldwide" and "founded" in df.columns:
            oldest = int(df["founded"].min())
            st.metric("Oldest Museum", str(oldest))
        else:
            st.metric("Records", len(df))

    with col4:
        lat_range = df["lat"].max() - df["lat"].min()
        st.metric("Lat Spread", f"{lat_range:.1f}\u00b0")


# =====================================================================
# COUNTRY FILTER HELPER
# =====================================================================
def _apply_country_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Optional country filter selectbox."""
    if "country" not in df.columns:
        return df
    countries = sorted(df["country"].unique().tolist())
    countries.insert(0, "All Countries")
    selected = st.selectbox(
        "Filter by Country",
        countries,
        key="pottery_maps_country_filter",
    )
    if selected != "All Countries":
        df = df[df["country"] == selected].reset_index(drop=True)
    return df


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_pottery_maps_tab():
    """Render the Pottery & Ceramics Maps tab for TerraScout AI."""

    # ---- Tab header ----
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>\U0001f3fa Pottery & Ceramics Explorer</h4>'
        '<p>Ancient kilns, porcelain factories, tile art traditions '
        '& ceramic heritage worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    modes = [
        "Chinese Porcelain Kilns",
        "Japanese Pottery Traditions",
        "Ancient Greek Pottery Sites",
        "Islamic Tile Art Centers",
        "European Porcelain Factories",
        "Pre-Columbian Pottery",
        "African Pottery Traditions",
        "Delft & Majolica Centers",
        "Modern Studio Pottery",
        "Ceramic Museums Worldwide",
    ]
    selected_mode = st.selectbox(
        "\U0001f3fa Select Map Mode", modes, key="pottery_maps_mode"
    )

    # Show mode description
    description = MODE_DESCRIPTIONS.get(selected_mode, "")
    if description:
        st.caption(description)

    # ---- Load data ----
    raw = _load_mode_data(selected_mode)
    if not raw:
        st.warning("No data available for this mode.")
        return

    df = pd.DataFrame(raw)

    # ---- Country filter ----
    df_filtered = _apply_country_filter(df)

    if df_filtered.empty:
        st.info("No locations match the selected filter.")
        return

    # ---- Stats dashboard ----
    st.markdown("---")
    _render_stats(df_filtered, selected_mode)
    st.markdown("---")

    # ---- Folium map ----
    with st.spinner(f"Building {selected_mode} map..."):
        m = _build_map(df_filtered, selected_mode)
        st_html(m._repr_html_(), height=500)

    # ---- Data table ----
    st.subheader(f"{selected_mode} Data ({len(df_filtered)} locations)")

    col_order = [c for c in df_filtered.columns if c != "notes"]
    if "notes" in df_filtered.columns:
        col_order.append("notes")
    st.dataframe(df_filtered[col_order], use_container_width=True)

    # ---- CSV download ----
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    safe_name = selected_mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        label=f"Download {selected_mode} CSV",
        data=csv_bytes,
        file_name=f"pottery_maps_{safe_name}.csv",
        mime="text/csv",
        key=f"pottery_maps_dl_{safe_name}",
    )

    # ---- Location search / highlight ----
    st.markdown("---")
    search_term = st.text_input(
        "Search locations",
        placeholder="Type a name or keyword to highlight...",
        key="pottery_maps_search",
    )
    if search_term and search_term.strip():
        term_lower = search_term.strip().lower()
        matches = df_filtered[
            df_filtered["name"].str.lower().str.contains(term_lower, na=False)
            | df_filtered["notes"].str.lower().str.contains(term_lower, na=False)
        ]
        if not matches.empty:
            st.success(
                f"Found {len(matches)} location(s) matching "
                f"'{html_module.escape(search_term.strip())}':"
            )
            for _, match_row in matches.iterrows():
                escaped_name = html_module.escape(str(match_row["name"]))
                escaped_notes = html_module.escape(str(match_row.get("notes", "")))
                color = MODE_COLORS.get(selected_mode, "#06b6d4")
                st.markdown(
                    f'<div style="border-left:3px solid {color};'
                    f'padding:6px 12px;margin-bottom:6px;'
                    f'background:#111827;border-radius:4px;">'
                    f'<span style="color:{color};font-weight:600;">'
                    f'{escaped_name}</span><br>'
                    f'<span style="color:#8b97b0;font-size:12px;">'
                    f'{escaped_notes}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                f"No locations matching '{html_module.escape(search_term.strip())}'."
            )

    # ---- About this dataset ----
    with st.expander("About this dataset"):
        color = MODE_COLORS.get(selected_mode, "#06b6d4")

        detail_lines = []
        if selected_mode == "Chinese Porcelain Kilns":
            detail_lines = [
                "China's porcelain tradition spans over 2,000 years from the Eastern Han dynasty.",
                "Jingdezhen has been the porcelain capital since the Yuan dynasty (1271-1368).",
                "The Five Great Kilns of the Song dynasty (Ru, Guan, Ge, Jun, Ding) are legendary.",
                "Chinese ceramics were exported along the Maritime Silk Road to Africa, the Middle East, and Europe.",
            ]
        elif selected_mode == "Japanese Pottery Traditions":
            detail_lines = [
                "Japanese pottery (yakimono) spans from Jomon earthenware (14,000 BC) to modern studio art.",
                "The Six Ancient Kilns (Bizen, Seto, Tokoname, Echizen, Shigaraki, Tamba) date to the Kamakura period.",
                "Korean potters brought after the Imjin War (1592-1598) founded many prestigious kiln traditions.",
                "Wabi-sabi aesthetics transformed rough tea bowls into the most prized ceramic objects in Japan.",
            ]
        elif selected_mode == "Ancient Greek Pottery Sites":
            detail_lines = [
                "Greek pottery evolved from Geometric through black-figure to red-figure technique.",
                "The word 'ceramic' derives from the Kerameikos potters' quarter of Athens.",
                "South Italian Greek colonies produced vast quantities of red-figure pottery.",
                "Greek pottery provides invaluable evidence for mythology, daily life, and trade networks.",
            ]
        elif selected_mode == "Islamic Tile Art Centers":
            detail_lines = [
                "Islamic tile art developed mosaic, cuerda seca, and underglaze painted techniques.",
                "Iznik tiles in Ottoman Turkey reached their artistic peak in the 16th century.",
                "Moroccan zellige involves hand-cutting thousands of tiny tile pieces into geometric mosaics.",
                "The word 'azulejo' comes from Arabic az-zulayj meaning polished stone.",
            ]
        elif selected_mode == "European Porcelain Factories":
            detail_lines = [
                "Johann Friedrich Bottger produced the first European hard-paste porcelain at Meissen in 1710.",
                "The secret of porcelain making spread across Europe throughout the 18th century.",
                "Josiah Wedgwood industrialized pottery production and invented jasperware in 1774.",
                "Bone china, developed by Josiah Spode c.1800, became the British standard for fine tableware.",
            ]
        elif selected_mode == "Pre-Columbian Pottery":
            detail_lines = [
                "The Americas developed pottery independently, with some of the earliest known at Valdivia, Ecuador.",
                "Moche portrait vessels are among the most realistic ceramic portraits ever made.",
                "Maya polychrome cylinder vases depict mythological narratives and palace scenes.",
                "Ancestral Puebloan black-on-white pottery shows sophisticated geometric design systems.",
            ]
        elif selected_mode == "African Pottery Traditions":
            detail_lines = [
                "Nok terracotta (500 BC) is the earliest known sculptural tradition in sub-Saharan Africa.",
                "African pottery is predominantly made by women using coil-building techniques.",
                "Many traditions are still living, passed from mother to daughter for centuries.",
                "Nubian black-topped pottery from Kerma (2500 BC) is among the finest prehistoric ceramics anywhere.",
            ]
        elif selected_mode == "Delft & Majolica Centers":
            detail_lines = [
                "Tin-glazed earthenware spread from the Islamic world to Italy (maiolica) then north to Delft.",
                "Delftware emerged in the 1650s as Dutch potters imitated Chinese blue-and-white porcelain.",
                "Portuguese azulejos evolved from Moorish geometric tiles to baroque narrative panels.",
                "Faenza gave its name to faience; Deruta and Gubbio perfected lustre painting in Italy.",
            ]
        elif selected_mode == "Modern Studio Pottery":
            detail_lines = [
                "Bernard Leach and Shoji Hamada founded the Studio Pottery movement at St Ives in 1920.",
                "Peter Voulkos broke ceramics into the fine art world with Abstract Expressionist sculpture in the 1950s.",
                "The mingei (folk craft) philosophy championed beauty in everyday handmade objects.",
                "Today ceramics has fully entered the contemporary art world with museum exhibitions and record auction prices.",
            ]
        elif selected_mode == "Ceramic Museums Worldwide":
            detail_lines = [
                "The V&A in London holds the world's largest ceramics collection with 36,000+ objects.",
                "The National Palace Museum in Taipei has the finest Song dynasty ceramics collection.",
                "Many porcelain factories maintain their own museums documenting centuries of production.",
                "Dedicated ceramics museums preserve knowledge of techniques, glazes, and cultural contexts.",
            ]

        details_html = "<br>".join(
            html_module.escape(line) for line in detail_lines
        )

        st.markdown(
            f'<div style="border-left:3px solid {color};padding-left:12px;'
            f'color:#8b97b0;font-size:13px;line-height:1.6;">'
            f'<b style="color:{color};">{html_module.escape(selected_mode)}</b><br>'
            f'{html_module.escape(description)}<br><br>'
            f'{details_html}<br><br>'
            f'<b>Total Locations:</b> {len(df)} curated entries<br>'
            f'<b>Countries Covered:</b> '
            f'{df["country"].nunique() if "country" in df.columns else "N/A"}<br>'
            f'<b>Source:</b> Curated ceramic and art historical references<br>'
            f'<b>Data:</b> Hardcoded — no external API calls required'
            f'</div>',
            unsafe_allow_html=True,
        )


# =====================================================================
# Standalone testing
# =====================================================================
if __name__ == "__main__":
    render_pottery_maps_tab()
