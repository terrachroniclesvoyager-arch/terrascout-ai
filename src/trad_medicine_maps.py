# -*- coding: utf-8 -*-
"""
TerraScout AI - Traditional Medicine Explorer Module
Provides 10 map modes covering traditional medicine, healing practices,
and ethnobotany across world cultures and history.

Map Modes:
  1. Traditional Chinese Medicine
  2. Ayurvedic Medicine Centers
  3. African Traditional Healing
  4. Amazonian Plant Medicine
  5. Aboriginal & Indigenous Medicine
  6. Tibetan Medicine
  7. Greek & Roman Medicine
  8. Medieval European Herbalism
  9. Hot Springs & Thermal Healing
 10. UNESCO Intangible Medicine Heritage
"""

import html
import io

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# ---------------------------------------------------------------------------
# 1. Traditional Chinese Medicine
# ---------------------------------------------------------------------------
TCM_SITES = [
    {"name": "Huangdi Neijing Origin - Shaanxi", "lat": 34.26, "lon": 108.94, "type": "Foundational Text", "era": "~300 BCE", "desc": "Legendary origin region of the Yellow Emperor's Classic of Internal Medicine", "country": "China"},
    {"name": "Beijing University of Chinese Medicine", "lat": 39.96, "lon": 116.43, "type": "Academic Center", "era": "1956 CE", "desc": "Premier TCM university and teaching hospital", "country": "China"},
    {"name": "Shanghai University of TCM", "lat": 31.18, "lon": 121.43, "type": "Academic Center", "era": "1956 CE", "desc": "Major TCM research and clinical training institution", "country": "China"},
    {"name": "Guangzhou University of Chinese Medicine", "lat": 23.05, "lon": 113.40, "type": "Academic Center", "era": "1956 CE", "desc": "South China center of TCM education and Lingnan herbal medicine", "country": "China"},
    {"name": "Chengdu University of TCM", "lat": 30.67, "lon": 104.07, "type": "Academic Center", "era": "1956 CE", "desc": "Sichuan TCM hub; strong in herbal pharmacology", "country": "China"},
    {"name": "Nanjing University of Chinese Medicine", "lat": 32.06, "lon": 118.78, "type": "Academic Center", "era": "1954 CE", "desc": "One of the earliest modern TCM universities", "country": "China"},
    {"name": "Mawangdui Tomb - Changsha", "lat": 28.23, "lon": 112.94, "type": "Archaeological Site", "era": "168 BCE", "desc": "Han dynasty tomb with earliest acupuncture and herbal texts", "country": "China"},
    {"name": "Mount Emei Medicinal Herbs", "lat": 29.52, "lon": 103.33, "type": "Herbal Region", "era": "Ancient", "desc": "Sacred Buddhist mountain with over 3,000 medicinal plant species", "country": "China"},
    {"name": "Anguo Herbal Medicine Market", "lat": 38.42, "lon": 115.33, "type": "Herbal Market", "era": "Song Dynasty", "desc": "Largest traditional herbal medicine market in northern China", "country": "China"},
    {"name": "Bozhou Herbal Medicine Market", "lat": 33.85, "lon": 115.78, "type": "Herbal Market", "era": "Ancient", "desc": "Birthplace of Hua Tuo; largest herbal medicine trading center", "country": "China"},
    {"name": "Dunhuang Medical Manuscripts", "lat": 40.14, "lon": 94.66, "type": "Archaeological Site", "era": "4th-10th c. CE", "desc": "Cave library with ancient medical scrolls and acupuncture charts", "country": "China"},
    {"name": "Li Shizhen Memorial - Qichun", "lat": 30.15, "lon": 115.68, "type": "Memorial", "era": "1518 CE", "desc": "Birthplace of Li Shizhen, author of Bencao Gangmu (Materia Medica)", "country": "China"},
    {"name": "Hua Tuo Memorial - Bozhou", "lat": 33.87, "lon": 115.76, "type": "Memorial", "era": "145 CE", "desc": "Birthplace of Hua Tuo, pioneer of anesthesia and surgery in TCM", "country": "China"},
    {"name": "Longmen Grottoes - TCM Carvings", "lat": 34.55, "lon": 112.47, "type": "Cultural Heritage", "era": "493 CE", "desc": "Buddhist grottoes containing medicinal prescriptions carved in stone", "country": "China"},
    {"name": "Sun Simiao Temple - Yaowang Shan", "lat": 35.08, "lon": 109.08, "type": "Memorial", "era": "581 CE", "desc": "Temple honoring the King of Medicine, author of Qianjin Yaofang", "country": "China"},
    {"name": "Tongrentang Pharmacy - Beijing", "lat": 39.90, "lon": 116.39, "type": "Historic Pharmacy", "era": "1669 CE", "desc": "Imperial pharmacy serving Qing dynasty emperors; still operating", "country": "China"},
    {"name": "Hong Kong School of Chinese Medicine", "lat": 22.34, "lon": 114.17, "type": "Academic Center", "era": "1999 CE", "desc": "Modern TCM education hub blending Eastern and Western approaches", "country": "China"},
    {"name": "Changbai Mountain Herbal Region", "lat": 42.00, "lon": 128.07, "type": "Herbal Region", "era": "Ancient", "desc": "Manchurian mountains rich in ginseng, reishi, and rare herbs", "country": "China"},
    {"name": "Kunming Institute of Botany", "lat": 25.04, "lon": 102.72, "type": "Research Center", "era": "1938 CE", "desc": "Major center for ethnobotanical research and Yunnan medicinal plants", "country": "China"},
    {"name": "Taiwan Chinese Medicine Research Institute", "lat": 25.03, "lon": 121.56, "type": "Research Center", "era": "1963 CE", "desc": "Government institute for TCM research and standardization", "country": "Taiwan"},
    {"name": "Zhang Zhongjing Memorial - Nanyang", "lat": 32.99, "lon": 112.53, "type": "Memorial", "era": "150 CE", "desc": "Birthplace of Zhang Zhongjing, author of Shanghan Lun (Treatise on Cold Damage)", "country": "China"},
    {"name": "Wudang Mountain Taoist Medicine", "lat": 32.40, "lon": 111.00, "type": "Sacred Site", "era": "Ancient", "desc": "Taoist mountain center of internal alchemy and qigong healing practices", "country": "China"},
    {"name": "Shennongjia Medicinal Forest", "lat": 31.75, "lon": 110.68, "type": "Herbal Region", "era": "Ancient", "desc": "Named after Shennong, legendary divine farmer who tested medicinal herbs", "country": "China"},
]

# ---------------------------------------------------------------------------
# 2. Ayurvedic Medicine Centers
# ---------------------------------------------------------------------------
AYURVEDIC_SITES = [
    {"name": "Kottakkal Arya Vaidya Sala", "lat": 11.00, "lon": 75.99, "type": "Treatment Center", "era": "1902 CE", "desc": "World-famous Ayurveda hospital and medicine manufacturer in Kerala", "country": "India"},
    {"name": "Banaras Hindu University - Ayurveda", "lat": 25.27, "lon": 82.99, "type": "Academic Center", "era": "1927 CE", "desc": "Major center for Ayurvedic research and education in Varanasi", "country": "India"},
    {"name": "Jamnagar Ayurvedic University", "lat": 22.47, "lon": 70.07, "type": "Academic Center", "era": "1952 CE", "desc": "Gujarat Ayurved University, India's first Ayurvedic university", "country": "India"},
    {"name": "Sushruta Birthplace - Varanasi", "lat": 25.32, "lon": 83.01, "type": "Historical Origin", "era": "~600 BCE", "desc": "Ancient origin of Sushruta Samhita, the foundational surgery text", "country": "India"},
    {"name": "Charaka Origin - Taxila", "lat": 33.74, "lon": 72.79, "type": "Historical Origin", "era": "~300 BCE", "desc": "Taxila university where Charaka composed the Charaka Samhita", "country": "Pakistan"},
    {"name": "Nalanda - Medical Studies", "lat": 25.13, "lon": 85.44, "type": "Ancient University", "era": "5th c. CE", "desc": "Ancient Buddhist university that taught Ayurvedic medicine", "country": "India"},
    {"name": "Siddha Medicine Centre - Chennai", "lat": 13.06, "lon": 80.24, "type": "Treatment Center", "era": "Ancient", "desc": "Center of Tamil Siddha medicine tradition, sister system to Ayurveda", "country": "India"},
    {"name": "Thrissur Ayurveda College", "lat": 10.52, "lon": 76.22, "type": "Academic Center", "era": "1889 CE", "desc": "One of the oldest Ayurvedic colleges, established during British Raj", "country": "India"},
    {"name": "Mysore Ayurveda Hospital", "lat": 12.31, "lon": 76.66, "type": "Treatment Center", "era": "1908 CE", "desc": "Historic government Ayurvedic hospital in Karnataka", "country": "India"},
    {"name": "Trivandrum Ayurveda College", "lat": 8.52, "lon": 76.94, "type": "Academic Center", "era": "1889 CE", "desc": "Premier Kerala Ayurveda college and Panchakarma treatment center", "country": "India"},
    {"name": "Haridwar Patanjali Yogpeeth", "lat": 29.91, "lon": 78.11, "type": "Treatment Center", "era": "2006 CE", "desc": "Large-scale Ayurveda and yoga wellness campus", "country": "India"},
    {"name": "Dhanvantari Temple - Kerala", "lat": 10.36, "lon": 76.21, "type": "Sacred Site", "era": "Ancient", "desc": "Temple dedicated to Dhanvantari, the god of Ayurveda", "country": "India"},
    {"name": "Sigiriya Herbal Gardens", "lat": 7.96, "lon": 80.76, "type": "Herbal Garden", "era": "5th c. CE", "desc": "Ancient Sinhalese royal gardens with medicinal plant cultivation", "country": "Sri Lanka"},
    {"name": "Nepal Ayurveda Centre - Kathmandu", "lat": 27.71, "lon": 85.32, "type": "Treatment Center", "era": "1933 CE", "desc": "Nepali Ayurveda center blending Himalayan herbal traditions", "country": "Nepal"},
    {"name": "Sorig Khang - Dharamsala", "lat": 32.22, "lon": 76.32, "type": "Treatment Center", "era": "1960s CE", "desc": "Tibetan-Ayurvedic hybrid medicine center near Dalai Lama residence", "country": "India"},
    {"name": "CCRAS New Delhi", "lat": 28.63, "lon": 77.22, "type": "Research Center", "era": "1978 CE", "desc": "Central Council for Research in Ayurvedic Sciences", "country": "India"},
    {"name": "Coimbatore Ayurveda College", "lat": 11.01, "lon": 76.97, "type": "Academic Center", "era": "1947 CE", "desc": "Tamil Nadu government college of Indian medicine", "country": "India"},
    {"name": "Rajasthan Ayurveda University - Jodhpur", "lat": 26.29, "lon": 73.02, "type": "Academic Center", "era": "2003 CE", "desc": "State university dedicated entirely to Ayurvedic education", "country": "India"},
    {"name": "Unani Medicine Centre - Lucknow", "lat": 26.85, "lon": 80.95, "type": "Treatment Center", "era": "Mughal Era", "desc": "Historic center of Unani (Greco-Arab) medicine in India", "country": "India"},
    {"name": "Bangladesh Unani & Ayurvedic Board", "lat": 23.73, "lon": 90.39, "type": "Regulatory Body", "era": "1972 CE", "desc": "Government body regulating traditional medicine in Bangladesh", "country": "Bangladesh"},
    {"name": "Ashtanga Hridayam Origin - Kerala", "lat": 10.85, "lon": 76.27, "type": "Historical Origin", "era": "7th c. CE", "desc": "Traditional origin region of Vagbhata's Ashtanga Hridayam compendium", "country": "India"},
    {"name": "Siddha Medicine - Rameswaram", "lat": 9.29, "lon": 79.31, "type": "Treatment Center", "era": "Ancient", "desc": "Tamil Siddha medicine center near sacred pilgrimage temple", "country": "India"},
]

# ---------------------------------------------------------------------------
# 3. African Traditional Healing
# ---------------------------------------------------------------------------
AFRICAN_HEALING_SITES = [
    {"name": "Zulu Sangoma Training - KwaZulu-Natal", "lat": -29.86, "lon": 31.02, "type": "Sangoma Center", "era": "Ancient", "desc": "Heartland of Zulu diviner-healers (izangoma) tradition", "country": "South Africa"},
    {"name": "Cape Town Kirstenbosch - Muthi Garden", "lat": -33.99, "lon": 18.43, "type": "Medicinal Garden", "era": "1913 CE", "desc": "Botanical garden with dedicated indigenous medicinal plant section", "country": "South Africa"},
    {"name": "Faladougou Traditional Healers - Mali", "lat": 12.65, "lon": -8.00, "type": "Healer Community", "era": "Ancient", "desc": "Major center of Mande traditional healing and herbal knowledge", "country": "Mali"},
    {"name": "Yoruba Babalawo Center - Ile-Ife", "lat": 7.48, "lon": 4.56, "type": "Divination Center", "era": "Ancient", "desc": "Sacred city of Ifa divination and Yoruba traditional medicine", "country": "Nigeria"},
    {"name": "Abomey Vodun Healing - Benin", "lat": 7.18, "lon": 1.99, "type": "Vodun Center", "era": "Ancient", "desc": "Center of Vodun spiritual healing and herbal traditions", "country": "Benin"},
    {"name": "Kumasi Herbal Market - Ghana", "lat": 6.69, "lon": -1.62, "type": "Herbal Market", "era": "Ancient", "desc": "Kejetia market with extensive traditional medicine trading section", "country": "Ghana"},
    {"name": "PROMETRA Senegal - Fatick", "lat": 14.33, "lon": -16.40, "type": "Research Center", "era": "1971 CE", "desc": "Organization promoting African traditional medicine research", "country": "Senegal"},
    {"name": "Muhimbili Traditional Medicine - Dar es Salaam", "lat": -6.80, "lon": 39.27, "type": "Research Center", "era": "1974 CE", "desc": "Institute of Traditional Medicine at Muhimbili University", "country": "Tanzania"},
    {"name": "Mbeya Herbalist Network - Tanzania", "lat": -8.90, "lon": 33.46, "type": "Healer Network", "era": "Ancient", "desc": "Regional network of traditional herbalists in Southern Highlands", "country": "Tanzania"},
    {"name": "Makerere University PROMETRA - Uganda", "lat": 0.33, "lon": 32.57, "type": "Academic Center", "era": "1989 CE", "desc": "Integration of traditional medicine into medical curriculum", "country": "Uganda"},
    {"name": "Nairobi Herbal Clinic District", "lat": -1.29, "lon": 36.82, "type": "Herbal Market", "era": "Modern", "desc": "Concentrated area of traditional herbalists and remedy shops", "country": "Kenya"},
    {"name": "Ethiopian Traditional Medicine - Addis Ababa", "lat": 9.02, "lon": 38.75, "type": "Research Center", "era": "Ancient", "desc": "Center for Ethiopian debtera and herbal medicine traditions", "country": "Ethiopia"},
    {"name": "Antananarivo Traditional Healers - Madagascar", "lat": -18.91, "lon": 47.52, "type": "Healer Community", "era": "Ancient", "desc": "Hub of Malagasy ombiasa healers and unique endemic plant medicine", "country": "Madagascar"},
    {"name": "Iboga Healing Center - Gabon", "lat": 0.39, "lon": 9.45, "type": "Sacred Plant Center", "era": "Ancient", "desc": "Center of Bwiti spiritual healing and iboga root traditions", "country": "Gabon"},
    {"name": "Casablanca Herbal Souk", "lat": 33.59, "lon": -7.59, "type": "Herbal Market", "era": "Medieval", "desc": "Traditional Moroccan herbalists and apothecary market", "country": "Morocco"},
    {"name": "Fez Attarine Herbal Quarter", "lat": 34.06, "lon": -5.00, "type": "Herbal Market", "era": "14th c. CE", "desc": "Historic herbalists quarter in the Fez medina", "country": "Morocco"},
    {"name": "Maputo Traditional Healers Assoc.", "lat": -25.97, "lon": 32.58, "type": "Healer Network", "era": "Modern", "desc": "Organization of Mozambican curandeiros and herbalists", "country": "Mozambique"},
    {"name": "Durban Muthi Market", "lat": -29.86, "lon": 31.03, "type": "Herbal Market", "era": "Ancient", "desc": "One of the largest traditional medicine markets in southern Africa", "country": "South Africa"},
    {"name": "WHO Afro Traditional Medicine - Brazzaville", "lat": -4.27, "lon": 15.28, "type": "Regulatory Body", "era": "2000 CE", "desc": "WHO African Regional Office for traditional medicine policy", "country": "Congo"},
    {"name": "Cameroon Ethnobotany Centre - Yaounde", "lat": 3.87, "lon": 11.52, "type": "Research Center", "era": "1990s CE", "desc": "Central African ethnobotanical research and plant documentation", "country": "Cameroon"},
    {"name": "Soweto Sangoma Market", "lat": -26.27, "lon": 27.85, "type": "Herbal Market", "era": "Modern", "desc": "Urban traditional medicine market serving Johannesburg township communities", "country": "South Africa"},
    {"name": "Timbuktu Herbal Manuscripts", "lat": 16.77, "lon": -3.01, "type": "Research Center", "era": "13th c. CE", "desc": "Ancient Malian manuscripts containing herbal medicine and healing formulas", "country": "Mali"},
    {"name": "Zanzibar Spice Healing Route", "lat": -6.17, "lon": 39.19, "type": "Herbal Market", "era": "Medieval", "desc": "Swahili coast spice trade with deep roots in traditional healing", "country": "Tanzania"},
]

# ---------------------------------------------------------------------------
# 4. Amazonian Plant Medicine
# ---------------------------------------------------------------------------
AMAZONIAN_MEDICINE_SITES = [
    {"name": "Iquitos Ayahuasca Center", "lat": -3.75, "lon": -73.25, "type": "Ayahuasca Center", "era": "Ancient", "desc": "Major hub for ayahuasca ceremonies and Shipibo-Conibo healing", "country": "Peru"},
    {"name": "Takiwasi Center - Tarapoto", "lat": -6.49, "lon": -76.37, "type": "Treatment Center", "era": "1992 CE", "desc": "Pioneering center combining ayahuasca with addiction treatment", "country": "Peru"},
    {"name": "Temple of the Way of Light - Iquitos", "lat": -3.80, "lon": -73.30, "type": "Retreat Center", "era": "2007 CE", "desc": "Shipibo curandero-led ayahuasca healing center", "country": "Peru"},
    {"name": "Manaus Ethnobotany Institute", "lat": -3.12, "lon": -60.02, "type": "Research Center", "era": "1954 CE", "desc": "INPA Amazonian research institute studying medicinal plants", "country": "Brazil"},
    {"name": "Santo Daime - Ceu do Mapia", "lat": -7.35, "lon": -69.00, "type": "Spiritual Community", "era": "1982 CE", "desc": "Headquarters of the Santo Daime ayahuasca spiritual movement", "country": "Brazil"},
    {"name": "UDV Temple - Brasilia", "lat": -15.80, "lon": -47.86, "type": "Spiritual Community", "era": "1961 CE", "desc": "Headquarters of Uniao do Vegetal ayahuasca church", "country": "Brazil"},
    {"name": "Sacha Runa Ethnobotany - Ecuador", "lat": -1.47, "lon": -78.00, "type": "Research Center", "era": "1990s CE", "desc": "Kichwa community-based ethnobotanical research station", "country": "Ecuador"},
    {"name": "Yasuni Biosphere - Waorani Territory", "lat": -1.00, "lon": -76.00, "type": "Indigenous Territory", "era": "Ancient", "desc": "Waorani traditional plant medicine in one of Earth's most biodiverse areas", "country": "Ecuador"},
    {"name": "Leticia - Tikuna Medicine", "lat": -4.21, "lon": -69.94, "type": "Indigenous Center", "era": "Ancient", "desc": "Tikuna indigenous healing traditions at the triple border region", "country": "Colombia"},
    {"name": "Putumayo Yage Tradition - Sibundoy", "lat": 1.20, "lon": -76.92, "type": "Ayahuasca Center", "era": "Ancient", "desc": "Kamsa and Inga communities with centuries-old yage ceremonies", "country": "Colombia"},
    {"name": "Belem Ver-o-Peso Herbal Market", "lat": -1.45, "lon": -48.50, "type": "Herbal Market", "era": "17th c. CE", "desc": "Iconic market with vast Amazonian medicinal plant section", "country": "Brazil"},
    {"name": "Coca Leaf Tradition - La Paz", "lat": -16.50, "lon": -68.15, "type": "Sacred Plant Center", "era": "Ancient", "desc": "Center of Andean coca leaf medicine and yatiri healing", "country": "Bolivia"},
    {"name": "Shipibo-Conibo Territory - Ucayali", "lat": -8.38, "lon": -74.53, "type": "Indigenous Territory", "era": "Ancient", "desc": "Homeland of Shipibo master plant healers and icaros traditions", "country": "Peru"},
    {"name": "Achuar Territory - Pastaza", "lat": -2.50, "lon": -76.50, "type": "Indigenous Territory", "era": "Ancient", "desc": "Achuar people's traditional plant knowledge and dream healing", "country": "Ecuador"},
    {"name": "Yanomami Territory - Roraima", "lat": 2.80, "lon": -63.50, "type": "Indigenous Territory", "era": "Ancient", "desc": "Yanomami shamanic healing with yakoana snuff and forest plants", "country": "Brazil"},
    {"name": "Machu Picchu Medicinal Terraces", "lat": -13.16, "lon": -72.55, "type": "Archaeological Site", "era": "15th c. CE", "desc": "Inca agricultural terraces used for medicinal plant cultivation", "country": "Peru"},
    {"name": "UNAM Ethnobotany - Mexico City", "lat": 19.33, "lon": -99.19, "type": "Research Center", "era": "1960 CE", "desc": "Major Latin American center for ethnobotanical research", "country": "Mexico"},
    {"name": "Oaxaca Mazatec Healing - Huautla", "lat": 18.13, "lon": -96.85, "type": "Sacred Plant Center", "era": "Ancient", "desc": "Center of Mazatec mushroom healing and Maria Sabina tradition", "country": "Mexico"},
    {"name": "Suriname Maroon Herbal Medicine", "lat": 4.00, "lon": -55.17, "type": "Healer Community", "era": "17th c. CE", "desc": "Maroon communities preserving African-Amazonian herbal synthesis", "country": "Suriname"},
    {"name": "Georgetown Amerindian Medicine", "lat": 6.80, "lon": -58.16, "type": "Indigenous Center", "era": "Ancient", "desc": "Guyanese Amerindian traditional plant knowledge repository", "country": "Guyana"},
    {"name": "San Pedro Cactus Tradition - Cusco", "lat": -13.52, "lon": -71.97, "type": "Sacred Plant Center", "era": "Ancient", "desc": "Andean huachuma (San Pedro) cactus healing ceremonies", "country": "Peru"},
    {"name": "Raposa Serra do Sol - Roraima", "lat": 3.80, "lon": -60.50, "type": "Indigenous Territory", "era": "Ancient", "desc": "Macuxi and Wapichana peoples' traditional plant healing practices", "country": "Brazil"},
]

# ---------------------------------------------------------------------------
# 5. Aboriginal & Indigenous Medicine
# ---------------------------------------------------------------------------
INDIGENOUS_MEDICINE_SITES = [
    {"name": "Kakadu Bush Medicine - NT", "lat": -12.83, "lon": 132.87, "type": "Bush Medicine", "era": "60,000+ yrs", "desc": "Aboriginal Bininj/Mungguy people's bush medicine traditions", "country": "Australia"},
    {"name": "Uluru Traditional Healing", "lat": -25.34, "lon": 131.04, "type": "Sacred Healing Site", "era": "60,000+ yrs", "desc": "Anangu traditional healing connected to Tjukurpa (Dreamtime)", "country": "Australia"},
    {"name": "Arnhem Land Medicine Plants", "lat": -12.30, "lon": 134.80, "type": "Bush Medicine", "era": "60,000+ yrs", "desc": "Yolngu people's extensive pharmacopoeia of native plants", "country": "Australia"},
    {"name": "Kimberly Bush Medicine", "lat": -17.30, "lon": 125.80, "type": "Bush Medicine", "era": "60,000+ yrs", "desc": "Bunuba and Gija traditional plant healing knowledge", "country": "Australia"},
    {"name": "Royal Botanic Gardens - Aboriginal Trail", "lat": -33.87, "lon": 151.22, "type": "Educational Site", "era": "Modern", "desc": "Dedicated Aboriginal bush medicine plant trail and education", "country": "Australia"},
    {"name": "Navajo Nation Medicine - Window Rock", "lat": 35.68, "lon": -109.05, "type": "Indigenous Center", "era": "Ancient", "desc": "Center of Dine (Navajo) hataalii healing ceremonies and plant medicine", "country": "USA"},
    {"name": "Cherokee Medicine - Qualla Boundary", "lat": 35.51, "lon": -83.31, "type": "Indigenous Center", "era": "Ancient", "desc": "Eastern Cherokee traditional plant medicine and healing practices", "country": "USA"},
    {"name": "Lakota Medicine Wheel - Bighorn", "lat": 44.83, "lon": -107.92, "type": "Sacred Healing Site", "era": "~1200 CE", "desc": "Ancient medicine wheel used in healing ceremonies and vision quests", "country": "USA"},
    {"name": "Haudenosaunee Medicine - Onondaga", "lat": 42.97, "lon": -76.12, "type": "Indigenous Center", "era": "Ancient", "desc": "Iroquois (Haudenosaunee) herbal medicine and False Face healing", "country": "USA"},
    {"name": "Maori Rongoa - Rotorua", "lat": -38.14, "lon": 176.25, "type": "Traditional Healing", "era": "Ancient", "desc": "Maori rongoa (traditional medicine) practice and native plant healing", "country": "New Zealand"},
    {"name": "Samoan Fono Healing - Apia", "lat": -13.83, "lon": -171.76, "type": "Traditional Healing", "era": "Ancient", "desc": "Samoan taulasea traditional healers and fofo massage therapy", "country": "Samoa"},
    {"name": "Tongan Traditional Medicine - Nukualofa", "lat": -21.21, "lon": -175.15, "type": "Traditional Healing", "era": "Ancient", "desc": "Tongan traditional faito'o plant medicine and spiritual healing", "country": "Tonga"},
    {"name": "Hawaiian Lomilomi - Kona", "lat": 19.64, "lon": -155.99, "type": "Traditional Healing", "era": "Ancient", "desc": "Native Hawaiian kahuna healing, lomilomi massage, and la'au lapa'au", "country": "USA"},
    {"name": "Inuit Medicine - Iqaluit", "lat": 63.75, "lon": -68.51, "type": "Indigenous Center", "era": "Ancient", "desc": "Inuit traditional healing knowledge and Arctic medicinal plants", "country": "Canada"},
    {"name": "Cree Medicine Lodge - Manitoba", "lat": 53.73, "lon": -98.81, "type": "Sacred Healing Site", "era": "Ancient", "desc": "Cree Nation traditional medicine lodge and sweat lodge healing", "country": "Canada"},
    {"name": "Mapuche Machi Healing - Temuco", "lat": -38.74, "lon": -72.60, "type": "Traditional Healing", "era": "Ancient", "desc": "Mapuche machi (shaman-healer) traditions and native plant medicine", "country": "Chile"},
    {"name": "Ainu Medicine - Hokkaido", "lat": 42.92, "lon": 141.35, "type": "Traditional Healing", "era": "Ancient", "desc": "Ainu people's traditional plant medicine and ekashi healing wisdom", "country": "Japan"},
    {"name": "Sami Traditional Healing - Kautokeino", "lat": 69.01, "lon": 23.04, "type": "Traditional Healing", "era": "Ancient", "desc": "Sami noaidi healing traditions and Arctic plant medicine", "country": "Norway"},
    {"name": "Torres Strait Islander Medicine", "lat": -10.57, "lon": 142.22, "type": "Bush Medicine", "era": "Ancient", "desc": "Torres Strait Islander traditional healing and marine-based remedies", "country": "Australia"},
    {"name": "Okinawan Longevity Medicine", "lat": 26.33, "lon": 127.80, "type": "Traditional Healing", "era": "Ancient", "desc": "Ryukyuan traditional herbal medicine contributing to extreme longevity", "country": "Japan"},
    {"name": "Mi'kmaq Medicine - Nova Scotia", "lat": 44.65, "lon": -63.57, "type": "Indigenous Center", "era": "Ancient", "desc": "Mi'kmaq Nation traditional plant medicine and ceremonial healing", "country": "Canada"},
    {"name": "Andaman Tribal Medicine - Port Blair", "lat": 11.67, "lon": 92.74, "type": "Indigenous Center", "era": "Ancient", "desc": "Great Andamanese and Jarawa traditional healing with island plants", "country": "India"},
    {"name": "Fijian Traditional Medicine - Suva", "lat": -18.14, "lon": 178.44, "type": "Traditional Healing", "era": "Ancient", "desc": "Fijian traditional healers using Pacific island medicinal plants", "country": "Fiji"},
]

# ---------------------------------------------------------------------------
# 6. Tibetan Medicine
# ---------------------------------------------------------------------------
TIBETAN_MEDICINE_SITES = [
    {"name": "Men-Tsee-Khang - Dharamsala", "lat": 32.22, "lon": 76.32, "type": "Medical Institute", "era": "1961 CE", "desc": "Tibetan Medical and Astrological Institute in exile, founded by Dalai Lama", "country": "India"},
    {"name": "Lhasa Mentsikhang", "lat": 29.65, "lon": 91.13, "type": "Medical Institute", "era": "1916 CE", "desc": "Historic Tibetan medical college in Lhasa, Tibet", "country": "China"},
    {"name": "Chakpori Medical College Site", "lat": 29.65, "lon": 91.10, "type": "Historical Site", "era": "1696 CE", "desc": "Site of the original Iron Hill medical college, destroyed in 1959", "country": "China"},
    {"name": "Samye Monastery - Medical Tradition", "lat": 29.32, "lon": 91.50, "type": "Monastery", "era": "779 CE", "desc": "First Buddhist monastery in Tibet, center of early medical teaching", "country": "China"},
    {"name": "Labrang Monastery - Medical College", "lat": 35.19, "lon": 102.51, "type": "Monastery", "era": "1784 CE", "desc": "Major Gelug monastery with renowned Tibetan medical school", "country": "China"},
    {"name": "Tashi Lhunpo Medical Center", "lat": 29.27, "lon": 88.88, "type": "Monastery", "era": "1447 CE", "desc": "Panchen Lama's monastery with traditional medical practice", "country": "China"},
    {"name": "Yuthog Yontan Gonpo Memorial", "lat": 29.66, "lon": 91.12, "type": "Memorial", "era": "8th c. CE", "desc": "Honoring the father of Tibetan medicine, author of Four Medical Tantras", "country": "China"},
    {"name": "Rebkong Sowa Rigpa Center", "lat": 35.52, "lon": 102.01, "type": "Treatment Center", "era": "Ancient", "desc": "Amdo Tibetan traditional medicine and thangka medical paintings", "country": "China"},
    {"name": "Derge Printing House - Medical Texts", "lat": 31.80, "lon": 98.58, "type": "Cultural Heritage", "era": "1729 CE", "desc": "Historic printing house preserving Tibetan medical woodblock texts", "country": "China"},
    {"name": "Achi Association Tibetan Medicine - Nepal", "lat": 27.72, "lon": 85.31, "type": "Treatment Center", "era": "1990s CE", "desc": "Tibetan medicine clinic serving Kathmandu community", "country": "Nepal"},
    {"name": "Buryat Tibetan Medicine - Ulan-Ude", "lat": 51.83, "lon": 107.60, "type": "Treatment Center", "era": "18th c. CE", "desc": "Russian Buryat continuation of Tibetan medical tradition", "country": "Russia"},
    {"name": "Mongolian Traditional Medicine - Ulaanbaatar", "lat": 47.92, "lon": 106.91, "type": "Academic Center", "era": "Ancient", "desc": "Mongolian adaptation of Tibetan medical tradition", "country": "Mongolia"},
    {"name": "Ladakh Amchi Medicine - Leh", "lat": 34.16, "lon": 77.58, "type": "Treatment Center", "era": "Ancient", "desc": "Ladakhi amchi (traditional doctor) practice of Sowa Rigpa", "country": "India"},
    {"name": "Sikkim Tibetan Medicine Centre", "lat": 27.33, "lon": 88.62, "type": "Treatment Center", "era": "Modern", "desc": "Sikkimese preservation of Tibetan medical knowledge", "country": "India"},
    {"name": "Bhutan Traditional Medicine Hospital", "lat": 27.47, "lon": 89.64, "type": "Treatment Center", "era": "1978 CE", "desc": "National Institute of Traditional Medicine in Thimphu", "country": "Bhutan"},
    {"name": "Qinghai Tibetan Medicine Hospital", "lat": 36.62, "lon": 101.78, "type": "Treatment Center", "era": "Modern", "desc": "Large-scale Tibetan medicine hospital on the Qinghai Plateau", "country": "China"},
    {"name": "Gansu Tibetan Medicine College", "lat": 34.73, "lon": 103.57, "type": "Academic Center", "era": "Modern", "desc": "Chinese government-supported Tibetan medicine education", "country": "China"},
    {"name": "Vienna Tibetan Medicine Centre", "lat": 48.21, "lon": 16.37, "type": "Treatment Center", "era": "2004 CE", "desc": "European center for Tibetan medicine practice and research", "country": "Austria"},
    {"name": "Kunphen Tibetan Medical Centre - Kathmandu", "lat": 27.70, "lon": 85.32, "type": "Treatment Center", "era": "1989 CE", "desc": "Boudhanath-area Tibetan medical clinic and herbal dispensary", "country": "Nepal"},
    {"name": "Chagpori Tibetan Medical Institute - Darjeeling", "lat": 27.04, "lon": 88.26, "type": "Medical Institute", "era": "1992 CE", "desc": "Revived Chakpori tradition; free medical care for local communities", "country": "India"},
    {"name": "Kalmykia Tibetan Medicine - Elista", "lat": 46.31, "lon": 44.27, "type": "Treatment Center", "era": "18th c. CE", "desc": "European Kalmyk Buddhist continuation of Tibetan medical tradition", "country": "Russia"},
    {"name": "Sera Monastery Medical School", "lat": 29.70, "lon": 91.13, "type": "Monastery", "era": "1419 CE", "desc": "Great Gelug monastery with traditional medical teaching lineage", "country": "China"},
    {"name": "Drepung Monastery Medical Tradition", "lat": 29.67, "lon": 91.07, "type": "Monastery", "era": "1416 CE", "desc": "Once the world's largest monastery; preserved medical text collection", "country": "China"},
]

# ---------------------------------------------------------------------------
# 7. Greek & Roman Medicine
# ---------------------------------------------------------------------------
GREEK_ROMAN_MEDICINE_SITES = [
    {"name": "Epidaurus Asclepion", "lat": 37.60, "lon": 23.08, "type": "Healing Temple", "era": "6th c. BCE", "desc": "Most famous Asclepion; patients slept in the abaton for dream-healing", "country": "Greece"},
    {"name": "Kos Asclepion", "lat": 36.87, "lon": 27.00, "type": "Healing Temple", "era": "4th c. BCE", "desc": "Asclepion on Hippocrates' island; major medical training center", "country": "Greece"},
    {"name": "Hippocrates Plane Tree - Kos", "lat": 36.89, "lon": 27.09, "type": "Historical Site", "era": "5th c. BCE", "desc": "Legendary tree where Hippocrates taught medicine to students", "country": "Greece"},
    {"name": "Pergamon Asclepion", "lat": 39.11, "lon": 27.17, "type": "Healing Temple", "era": "4th c. BCE", "desc": "Major healing center where Galen trained; sacred spring and therapy tunnels", "country": "Turkey"},
    {"name": "Galen's Birthplace - Pergamon", "lat": 39.12, "lon": 27.18, "type": "Historical Origin", "era": "129 CE", "desc": "Birthplace of Galen, most influential physician after Hippocrates", "country": "Turkey"},
    {"name": "Athens Asclepion - South Slope", "lat": 37.97, "lon": 23.73, "type": "Healing Temple", "era": "5th c. BCE", "desc": "Asclepion below the Acropolis with sacred spring", "country": "Greece"},
    {"name": "Corinth Asclepion", "lat": 37.91, "lon": 22.88, "type": "Healing Temple", "era": "4th c. BCE", "desc": "Healing sanctuary with dining rooms for therapeutic meals", "country": "Greece"},
    {"name": "Butrint Asclepion - Albania", "lat": 39.75, "lon": 20.02, "type": "Healing Temple", "era": "4th c. BCE", "desc": "Greek-Roman healing site in UNESCO World Heritage city", "country": "Albania"},
    {"name": "Bath Roman Spa - Aquae Sulis", "lat": 51.38, "lon": -2.36, "type": "Thermal Healing", "era": "60 CE", "desc": "Roman thermal bath complex dedicated to Sulis Minerva", "country": "UK"},
    {"name": "Baiae Roman Medical Resort", "lat": 40.82, "lon": 14.08, "type": "Thermal Healing", "era": "2nd c. BCE", "desc": "Luxury Roman thermal resort used for medical treatment", "country": "Italy"},
    {"name": "Dioscorides Heritage - Anazarbus", "lat": 37.25, "lon": 35.90, "type": "Historical Origin", "era": "40 CE", "desc": "Homeland of Dioscorides, author of De Materia Medica", "country": "Turkey"},
    {"name": "Alexandria School of Medicine", "lat": 31.20, "lon": 29.92, "type": "Ancient School", "era": "3rd c. BCE", "desc": "Greatest medical school of antiquity; Herophilus and Erasistratus taught here", "country": "Egypt"},
    {"name": "Rome Tiber Island - Temple of Aesculapius", "lat": 41.89, "lon": 12.48, "type": "Healing Temple", "era": "291 BCE", "desc": "Island hospital-temple; still a hospital site (Fatebenefratelli)", "country": "Italy"},
    {"name": "Pompeii Surgeon's House", "lat": 40.75, "lon": 14.49, "type": "Archaeological Site", "era": "79 CE", "desc": "House of the Surgeon with preserved Roman surgical instruments", "country": "Italy"},
    {"name": "Trier Roman Baths - Medical Complex", "lat": 49.75, "lon": 6.64, "type": "Thermal Healing", "era": "4th c. CE", "desc": "Largest Roman baths north of the Alps with healing functions", "country": "Germany"},
    {"name": "Cnidus Medical School", "lat": 36.69, "lon": 27.37, "type": "Ancient School", "era": "7th c. BCE", "desc": "Rival school to Hippocratic Cos; emphasis on diagnosis and prognosis", "country": "Turkey"},
    {"name": "Emporiae Asclepion - Spain", "lat": 42.13, "lon": 3.12, "type": "Healing Temple", "era": "3rd c. BCE", "desc": "Greek colonial healing center on the Iberian coast", "country": "Spain"},
    {"name": "Cyrene Medical Tradition - Libya", "lat": 32.82, "lon": 21.86, "type": "Ancient School", "era": "6th c. BCE", "desc": "Greek colony known for silphium, an ancient medicinal plant now extinct", "country": "Libya"},
    {"name": "Salerno Medical School", "lat": 40.68, "lon": 14.77, "type": "Ancient School", "era": "9th c. CE", "desc": "Schola Medica Salernitana: first great European medical school, bridging Greek-Roman and Arab medicine", "country": "Italy"},
    {"name": "Constantinople Hospital - Pantokrator", "lat": 41.02, "lon": 28.96, "type": "Historical Hospital", "era": "1136 CE", "desc": "Byzantine hospital preserving Galenic medicine with specialized wards", "country": "Turkey"},
    {"name": "Cos Asklepieion Medical Library", "lat": 36.87, "lon": 27.01, "type": "Ancient School", "era": "3rd c. BCE", "desc": "Medical library at the Kos Asclepion housing Hippocratic treatises", "country": "Greece"},
    {"name": "Aesculapius Temple - Agrigento", "lat": 37.29, "lon": 13.59, "type": "Healing Temple", "era": "5th c. BCE", "desc": "Greek colonial Asclepion in the Valley of the Temples, Sicily", "country": "Italy"},
]

# ---------------------------------------------------------------------------
# 8. Medieval European Herbalism
# ---------------------------------------------------------------------------
MEDIEVAL_HERBALISM_SITES = [
    {"name": "Hildegard von Bingen - Rupertsberg", "lat": 49.95, "lon": 7.88, "type": "Monastery", "era": "1150 CE", "desc": "Abbey of Hildegard, author of Physica and Causae et Curae herbal texts", "country": "Germany"},
    {"name": "Salerno Physic Garden", "lat": 40.68, "lon": 14.77, "type": "Physic Garden", "era": "10th c. CE", "desc": "Herb garden of the Schola Medica Salernitana, first European medical school", "country": "Italy"},
    {"name": "Padua Botanical Garden", "lat": 45.40, "lon": 11.88, "type": "Physic Garden", "era": "1545 CE", "desc": "World's oldest academic botanical garden, UNESCO World Heritage Site", "country": "Italy"},
    {"name": "Oxford Physic Garden", "lat": 51.75, "lon": -1.25, "type": "Physic Garden", "era": "1621 CE", "desc": "Britain's oldest botanical garden, originally for medicinal plant study", "country": "UK"},
    {"name": "Chelsea Physic Garden - London", "lat": 51.48, "lon": -0.16, "type": "Physic Garden", "era": "1673 CE", "desc": "Founded by Society of Apothecaries for apprentice training", "country": "UK"},
    {"name": "Monte Cassino - Benedictine Medicine", "lat": 41.49, "lon": 13.81, "type": "Monastery", "era": "529 CE", "desc": "Birthplace of Benedictine monastic medicine and herb cultivation", "country": "Italy"},
    {"name": "St. Gall Monastery - Physic Garden Plan", "lat": 47.42, "lon": 9.38, "type": "Monastery", "era": "820 CE", "desc": "Famous medieval plan showing ideal monastery herb garden layout", "country": "Switzerland"},
    {"name": "Cluny Abbey Herbarium", "lat": 46.43, "lon": 4.66, "type": "Monastery", "era": "910 CE", "desc": "Cluniac monastery with influential herbal medicine tradition", "country": "France"},
    {"name": "Montpellier Medical Faculty", "lat": 43.61, "lon": 3.87, "type": "Medical School", "era": "1220 CE", "desc": "One of the oldest European medical schools; Arab-Latin herbal synthesis", "country": "France"},
    {"name": "Bologna Medical Faculty", "lat": 44.50, "lon": 11.35, "type": "Medical School", "era": "1088 CE", "desc": "Europe's oldest university, pioneered anatomy alongside herbal medicine", "country": "Italy"},
    {"name": "Plague Doctor Quarter - Venice", "lat": 45.44, "lon": 12.34, "type": "Historical Site", "era": "14th c. CE", "desc": "Center of plague doctor tradition and miasma-based herbal treatments", "country": "Italy"},
    {"name": "Lazzaretto Nuovo - Venice", "lat": 45.43, "lon": 12.39, "type": "Historical Site", "era": "1468 CE", "desc": "First quarantine station; medicinal fumigation and herbal treatments", "country": "Italy"},
    {"name": "Nuremberg Apothecary District", "lat": 49.45, "lon": 11.08, "type": "Apothecary", "era": "14th c. CE", "desc": "Historic center of German apothecary trade and herbal pharmacy", "country": "Germany"},
    {"name": "Leiden Hortus Botanicus", "lat": 52.16, "lon": 4.49, "type": "Physic Garden", "era": "1590 CE", "desc": "Dutch botanical garden for medicinal plant study, established by Clusius", "country": "Netherlands"},
    {"name": "Cordoba Caliphate - House of Wisdom Medicine", "lat": 37.88, "lon": -4.78, "type": "Medical School", "era": "10th c. CE", "desc": "Islamic Iberian center translating Greek medical texts and advancing herbalism", "country": "Spain"},
    {"name": "Toledo Translation School", "lat": 39.86, "lon": -4.02, "type": "Translation Center", "era": "12th c. CE", "desc": "Translated Arabic medical texts (Avicenna, Rhazes) into Latin for Europe", "country": "Spain"},
    {"name": "Paris Faculty of Medicine", "lat": 48.85, "lon": 2.34, "type": "Medical School", "era": "1253 CE", "desc": "Medieval Sorbonne medical faculty with scholastic herbal tradition", "country": "France"},
    {"name": "Walahfrid Strabo's Garden - Reichenau", "lat": 47.70, "lon": 9.06, "type": "Monastery", "era": "842 CE", "desc": "Monk who wrote Hortulus, a famous medieval herbal garden poem", "country": "Germany"},
    {"name": "Pisa Botanical Garden", "lat": 43.72, "lon": 10.40, "type": "Physic Garden", "era": "1544 CE", "desc": "One of Europe's oldest botanical gardens, founded by Luca Ghini", "country": "Italy"},
    {"name": "Edinburgh Physic Garden", "lat": 55.96, "lon": -3.21, "type": "Physic Garden", "era": "1670 CE", "desc": "Royal Botanic Garden Edinburgh, originally a small physic garden", "country": "UK"},
    {"name": "Wroclaw Apothecary Museum", "lat": 51.11, "lon": 17.03, "type": "Apothecary", "era": "14th c. CE", "desc": "Preserved medieval apothecary with original herbal remedy collection", "country": "Poland"},
    {"name": "Uppsala Botanical Garden", "lat": 59.86, "lon": 17.63, "type": "Physic Garden", "era": "1655 CE", "desc": "Linnaeus's garden where modern botanical classification began", "country": "Sweden"},
    {"name": "Florence Orto Botanico", "lat": 43.78, "lon": 11.26, "type": "Physic Garden", "era": "1545 CE", "desc": "Medici-era botanical garden for medicinal plant teaching", "country": "Italy"},
]

# ---------------------------------------------------------------------------
# 9. Hot Springs & Thermal Healing
# ---------------------------------------------------------------------------
HOT_SPRINGS_SITES = [
    {"name": "Beppu Onsen - Japan", "lat": 33.28, "lon": 131.49, "type": "Onsen", "era": "Ancient", "desc": "Japan's largest hot spring complex with 2,800+ vents; eight major bath areas", "country": "Japan"},
    {"name": "Kusatsu Onsen - Japan", "lat": 36.62, "lon": 138.60, "type": "Onsen", "era": "Ancient", "desc": "Acidic sulfur springs renowned for skin healing; yumomi water cooling tradition", "country": "Japan"},
    {"name": "Dogo Onsen - Matsuyama", "lat": 33.85, "lon": 132.79, "type": "Onsen", "era": "3000 yrs", "desc": "One of Japan's oldest hot springs, mentioned in the Kojiki (712 CE)", "country": "Japan"},
    {"name": "Blue Lagoon - Iceland", "lat": 63.88, "lon": -22.45, "type": "Geothermal Spa", "era": "1992 CE", "desc": "Silica-rich geothermal lagoon famous for psoriasis treatment", "country": "Iceland"},
    {"name": "Landmannalaugar - Iceland", "lat": 63.99, "lon": -19.06, "type": "Natural Hot Spring", "era": "Ancient", "desc": "Highland geothermal area with natural bathing in rhyolite mountains", "country": "Iceland"},
    {"name": "Szechenyi Baths - Budapest", "lat": 47.52, "lon": 19.08, "type": "Thermal Bath", "era": "1913 CE", "desc": "Largest medicinal bath in Europe; 18 pools with therapeutic mineral water", "country": "Hungary"},
    {"name": "Gellert Baths - Budapest", "lat": 47.48, "lon": 19.05, "type": "Thermal Bath", "era": "1918 CE", "desc": "Art Nouveau thermal bath with Ottoman-era spring heritage", "country": "Hungary"},
    {"name": "Terme di Saturnia - Tuscany", "lat": 42.65, "lon": 11.51, "type": "Natural Hot Spring", "era": "Etruscan Era", "desc": "Sulfurous 37.5C cascading waterfalls used since Etruscan times", "country": "Italy"},
    {"name": "Ischia Thermal Island - Italy", "lat": 40.73, "lon": 13.90, "type": "Thermal Island", "era": "8th c. BCE", "desc": "Volcanic island with 100+ thermal springs; Greek colony for healing", "country": "Italy"},
    {"name": "Bath Roman Spa - UK", "lat": 51.38, "lon": -2.36, "type": "Roman Bath", "era": "60 CE", "desc": "Only natural hot spring in Britain; Roman temple and bathing complex", "country": "UK"},
    {"name": "Pamukkale - Hierapolis", "lat": 37.92, "lon": 29.12, "type": "Thermal Terrace", "era": "2nd c. BCE", "desc": "UNESCO travertine terraces; ancient Greco-Roman therapeutic spa city", "country": "Turkey"},
    {"name": "Karlovy Vary - Czech Republic", "lat": 50.23, "lon": 12.87, "type": "Spa Town", "era": "1370 CE", "desc": "Famous spa town with 13 mineral springs for drinking cures", "country": "Czech Republic"},
    {"name": "Baden-Baden - Germany", "lat": 48.76, "lon": 8.24, "type": "Spa Town", "era": "Roman Era", "desc": "Historic spa town with Roman Caracalla baths and Friedrichsbad", "country": "Germany"},
    {"name": "Vichy Thermal Springs - France", "lat": 46.13, "lon": 3.42, "type": "Spa Town", "era": "Roman Era", "desc": "Famous French thermal town with mineral water drinking cures", "country": "France"},
    {"name": "Rotorua Geothermal - New Zealand", "lat": -38.14, "lon": 176.25, "type": "Geothermal Spa", "era": "Ancient", "desc": "Maori healing tradition using volcanic mud baths and hot pools", "country": "New Zealand"},
    {"name": "Hot Springs National Park - Arkansas", "lat": 34.52, "lon": -93.05, "type": "National Park", "era": "Ancient", "desc": "Historic bathhouse row; Native Americans used springs for centuries", "country": "USA"},
    {"name": "Banjar Hot Springs - Bali", "lat": -8.22, "lon": 115.15, "type": "Natural Hot Spring", "era": "Ancient", "desc": "Sacred Balinese sulfur springs in tropical jungle setting", "country": "Indonesia"},
    {"name": "Hammam Al-Andalus - Granada", "lat": 37.18, "lon": -3.60, "type": "Hammam", "era": "Moorish Era", "desc": "Restored Arab baths following Moorish thermal healing tradition", "country": "Spain"},
    {"name": "Jigokudani Monkey Park - Nagano", "lat": 36.73, "lon": 138.46, "type": "Natural Hot Spring", "era": "Ancient", "desc": "Volcanic hot springs where Japanese macaques bathe for health", "country": "Japan"},
    {"name": "Salar de Uyuni Hot Springs - Bolivia", "lat": -22.33, "lon": -67.53, "type": "Natural Hot Spring", "era": "Ancient", "desc": "Sol de Manana geothermal springs at 4,800m on the Altiplano", "country": "Bolivia"},
    {"name": "Rudas Baths - Budapest", "lat": 47.49, "lon": 19.05, "type": "Thermal Bath", "era": "1550 CE", "desc": "Ottoman-era thermal bath with original Turkish dome still intact", "country": "Hungary"},
    {"name": "Hierve el Agua - Oaxaca", "lat": 16.87, "lon": -96.28, "type": "Natural Hot Spring", "era": "Ancient", "desc": "Petrified mineral waterfalls and Zapotec sacred bathing pools", "country": "Mexico"},
    {"name": "Manikaran Hot Springs - Himachal", "lat": 32.03, "lon": 77.35, "type": "Natural Hot Spring", "era": "Ancient", "desc": "Sacred Sikh and Hindu hot springs in the Parvati Valley", "country": "India"},
]

# ---------------------------------------------------------------------------
# 10. UNESCO Intangible Medicine Heritage
# ---------------------------------------------------------------------------
UNESCO_MEDICINE_HERITAGE = [
    {"name": "Acupuncture & Moxibustion of TCM", "lat": 39.91, "lon": 116.40, "year": 2010, "type": "Medical Practice", "desc": "Traditional Chinese acupuncture and moxibustion inscribed by UNESCO", "country": "China"},
    {"name": "Sowa Rigpa - Traditional Tibetan Medicine", "lat": 29.65, "lon": 91.13, "year": 2018, "type": "Medical System", "desc": "Knowledge and practices of Tibetan medicine; body humor balance", "country": "China"},
    {"name": "Yoga - Intangible Heritage", "lat": 28.63, "lon": 77.22, "year": 2016, "type": "Healing Practice", "desc": "Indian philosophical and healing practice; UNESCO inscribed", "country": "India"},
    {"name": "Al-Katt Al-Asiri - Traditional Healing Art", "lat": 18.22, "lon": 42.51, "year": 2017, "type": "Traditional Art/Healing", "desc": "Saudi Arabian traditional healing art and interior decoration knowledge", "country": "Saudi Arabia"},
    {"name": "Mediterranean Diet - Healing Food", "lat": 37.97, "lon": 23.73, "year": 2013, "type": "Food Medicine", "desc": "Dietary healing tradition recognized across Mediterranean countries", "country": "Greece"},
    {"name": "Traditional Korean Medicine - Donguibogam", "lat": 37.57, "lon": 126.98, "year": 2009, "type": "Medical Text", "desc": "Donguibogam medical encyclopedia by Heo Jun inscribed in Memory of the World", "country": "South Korea"},
    {"name": "Jamu - Indonesian Traditional Medicine", "lat": -6.21, "lon": 106.85, "year": 2023, "type": "Herbal Medicine", "desc": "Indonesian traditional herbal medicine and wellness system", "country": "Indonesia"},
    {"name": "Traditional Mexican Medicine - Curanderismo", "lat": 19.43, "lon": -99.13, "year": 2018, "type": "Medical System", "desc": "Mexican traditional healing blending indigenous and colonial practices", "country": "Mexico"},
    {"name": "Khmer Traditional Medicine", "lat": 11.56, "lon": 104.93, "year": 2022, "type": "Medical System", "desc": "Cambodian Kru Khmer traditional healing and herbal knowledge", "country": "Cambodia"},
    {"name": "Turkish Coffee & Healing Tradition", "lat": 41.02, "lon": 28.98, "year": 2013, "type": "Healing Custom", "desc": "Turkish coffee culture with traditional medicinal associations", "country": "Turkey"},
    {"name": "Taekkyon - Korean Martial Healing", "lat": 37.57, "lon": 127.00, "year": 2011, "type": "Martial Healing", "desc": "Traditional Korean martial art with therapeutic movement practices", "country": "South Korea"},
    {"name": "Iftar Healing & Fasting Tradition", "lat": 24.47, "lon": 54.37, "year": 2023, "type": "Healing Custom", "desc": "Social practice of Iftar with traditional healing food preparation", "country": "UAE"},
    {"name": "Hammam Culture - Turkish Baths", "lat": 41.01, "lon": 28.97, "year": 2012, "type": "Bathing Healing", "desc": "Turkish bath culture as social and therapeutic tradition", "country": "Turkey"},
    {"name": "Vietnamese Traditional Medicine - Thuoc Nam", "lat": 21.03, "lon": 105.85, "year": 2019, "type": "Herbal Medicine", "desc": "Vietnamese Southern medicine tradition using local medicinal plants", "country": "Vietnam"},
    {"name": "Thai Traditional Massage - Nuad Thai", "lat": 13.75, "lon": 100.49, "year": 2019, "type": "Healing Practice", "desc": "Thai massage inscribed as intangible heritage; Wat Pho tradition", "country": "Thailand"},
    {"name": "Zhusuan - Chinese Abacus for Medical Calc", "lat": 34.26, "lon": 108.94, "year": 2013, "type": "Medical Tool", "desc": "Chinese abacus used historically for pharmacological calculations", "country": "China"},
    {"name": "Reggae Music - Rastafari Healing", "lat": 18.11, "lon": -77.30, "year": 2018, "type": "Healing Music", "desc": "Jamaican reggae music with Rastafari spiritual healing dimensions", "country": "Jamaica"},
    {"name": "Cossack Herbal Tradition - Ukraine", "lat": 47.84, "lon": 35.14, "year": 2021, "type": "Herbal Medicine", "desc": "Ukrainian Cossack tradition of herbal medicine and steppe remedies", "country": "Ukraine"},
    {"name": "Finnish Sauna - Therapeutic Bathing", "lat": 60.17, "lon": 24.94, "year": 2020, "type": "Bathing Healing", "desc": "Finnish sauna culture as wellness and healing tradition", "country": "Finland"},
    {"name": "Baul Songs - Bengali Healing Music", "lat": 23.81, "lon": 90.41, "year": 2008, "type": "Healing Music", "desc": "Mystical Bengali songs used in spiritual and physical healing", "country": "Bangladesh"},
    {"name": "Kankurang Healing Ritual - Gambia", "lat": 13.45, "lon": -16.58, "year": 2008, "type": "Healing Ritual", "desc": "Mandinka initiation and healing ritual using forest spirits", "country": "Gambia"},
    {"name": "Vimbuza Healing Dance - Malawi", "lat": -13.97, "lon": 33.79, "year": 2008, "type": "Healing Dance", "desc": "Tumbuka healing dance for mental and spiritual afflictions", "country": "Malawi"},
    {"name": "Fujian Puppet Theatre - Healing Plays", "lat": 24.87, "lon": 118.68, "year": 2012, "type": "Healing Performance", "desc": "Traditional puppet theatre with ritual healing story performances", "country": "China"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MAP TYPES, DESCRIPTIONS, AND BUILDER REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

MAP_TYPES = [
    "Traditional Chinese Medicine",
    "Ayurvedic Medicine Centers",
    "African Traditional Healing",
    "Amazonian Plant Medicine",
    "Aboriginal & Indigenous Medicine",
    "Tibetan Medicine",
    "Greek & Roman Medicine",
    "Medieval European Herbalism",
    "Hot Springs & Thermal Healing",
    "UNESCO Intangible Medicine Heritage",
]

MAP_DESCRIPTIONS = {
    MAP_TYPES[0]: "Map acupuncture origins, herbal medicine markets, TCM universities, and historic sites of Traditional Chinese Medicine spanning thousands of years.",
    MAP_TYPES[1]: "Explore Ayurvedic medicine origins from ancient Charaka and Sushruta texts to modern treatment centers across the Indian subcontinent.",
    MAP_TYPES[2]: "Discover African traditional healing centers including Sangoma traditions, Yoruba Babalawo divination, herbal markets, and ethnobotany research.",
    MAP_TYPES[3]: "Journey through Amazonian plant medicine traditions including ayahuasca ceremony centers, ethnobotanical research, and indigenous healing territories.",
    MAP_TYPES[4]: "Explore Aboriginal Australian bush medicine, Native American healing, Maori rongoa, and indigenous healing practices worldwide.",
    MAP_TYPES[5]: "Map Tibetan Sowa Rigpa medical centers, monastery medical colleges, and the Himalayan healing tradition from Tibet to the diaspora.",
    MAP_TYPES[6]: "Visit ancient Asclepions, the schools of Hippocrates and Galen, Roman thermal healing, and the foundations of Western medicine.",
    MAP_TYPES[7]: "Trace medieval European herbal medicine through monastery gardens, physic gardens, apothecary routes, plague doctor quarters, and medical schools.",
    MAP_TYPES[8]: "Explore the world's greatest thermal healing sites: Japanese onsen, Roman baths, Icelandic geothermal spas, and balneotherapy centers.",
    MAP_TYPES[9]: "Map UNESCO-recognized intangible heritage practices related to traditional medicine, healing arts, and therapeutic cultural traditions.",
}

MAP_COLORS = {
    MAP_TYPES[0]: "#ef4444",   # red
    MAP_TYPES[1]: "#f59e0b",   # amber
    MAP_TYPES[2]: "#10b981",   # emerald
    MAP_TYPES[3]: "#22c55e",   # green
    MAP_TYPES[4]: "#8b5cf6",   # violet
    MAP_TYPES[5]: "#ec4899",   # pink
    MAP_TYPES[6]: "#06b6d4",   # cyan
    MAP_TYPES[7]: "#f97316",   # orange
    MAP_TYPES[8]: "#3b82f6",   # blue
    MAP_TYPES[9]: "#a855f7",   # purple
}

MAP_ICONS = {
    MAP_TYPES[0]: "leaf",
    MAP_TYPES[1]: "heart",
    MAP_TYPES[2]: "tree",
    MAP_TYPES[3]: "seedling",
    MAP_TYPES[4]: "feather-alt",
    MAP_TYPES[5]: "om",
    MAP_TYPES[6]: "landmark",
    MAP_TYPES[7]: "mortar-pestle",
    MAP_TYPES[8]: "hot-tub",
    MAP_TYPES[9]: "award",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _base_map(center=None, zoom=2):
    """Return a dark-themed Folium map."""
    if center is None:
        center = [20, 0]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _safe_popup(fields: dict, max_width: int = 280) -> folium.Popup:
    """Build an HTML popup with html.escape applied to all string values."""
    lines = []
    for key, val in fields.items():
        safe_val = html.escape(str(val)) if val else ""
        if key == "_title":
            lines.append(f"<b>{safe_val}</b>")
        else:
            lines.append(f"{html.escape(str(key))}: {safe_val}")
    body = "<br>".join(lines)
    popup_html = f'<div style="max-width:{max_width}px; font-size:0.85rem;">{body}</div>'
    return folium.Popup(popup_html, max_width=max_width)


# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_tcm_map():
    """Map 1 -- Traditional Chinese Medicine."""
    m = _base_map(center=[35, 105], zoom=4)
    type_colors = {
        "Foundational Text": "#ef4444",
        "Academic Center": "#06b6d4",
        "Archaeological Site": "#f59e0b",
        "Herbal Region": "#10b981",
        "Herbal Market": "#22c55e",
        "Memorial": "#ec4899",
        "Cultural Heritage": "#8b5cf6",
        "Historic Pharmacy": "#f97316",
        "Research Center": "#3b82f6",
    }
    for site in TCM_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(TCM_SITES)


def _build_ayurvedic_map():
    """Map 2 -- Ayurvedic Medicine Centers."""
    m = _base_map(center=[22, 78], zoom=5)
    type_colors = {
        "Treatment Center": "#f59e0b",
        "Academic Center": "#06b6d4",
        "Historical Origin": "#ef4444",
        "Ancient University": "#8b5cf6",
        "Sacred Site": "#ec4899",
        "Herbal Garden": "#10b981",
        "Research Center": "#3b82f6",
        "Regulatory Body": "#64748b",
    }
    for site in AYURVEDIC_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(AYURVEDIC_SITES)


def _build_african_healing_map():
    """Map 3 -- African Traditional Healing."""
    m = _base_map(center=[5, 20], zoom=3)
    type_colors = {
        "Sangoma Center": "#8b5cf6",
        "Medicinal Garden": "#10b981",
        "Healer Community": "#f59e0b",
        "Divination Center": "#ec4899",
        "Vodun Center": "#ef4444",
        "Herbal Market": "#22c55e",
        "Research Center": "#06b6d4",
        "Healer Network": "#f97316",
        "Academic Center": "#3b82f6",
        "Sacred Plant Center": "#a855f7",
        "Regulatory Body": "#64748b",
    }
    for site in AFRICAN_HEALING_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(AFRICAN_HEALING_SITES)


def _build_amazonian_map():
    """Map 4 -- Amazonian Plant Medicine."""
    m = _base_map(center=[-5, -65], zoom=4)
    type_colors = {
        "Ayahuasca Center": "#22c55e",
        "Treatment Center": "#f59e0b",
        "Retreat Center": "#10b981",
        "Research Center": "#06b6d4",
        "Spiritual Community": "#8b5cf6",
        "Indigenous Territory": "#ef4444",
        "Indigenous Center": "#ec4899",
        "Herbal Market": "#f97316",
        "Sacred Plant Center": "#a855f7",
        "Archaeological Site": "#3b82f6",
        "Healer Community": "#64748b",
    }
    for site in AMAZONIAN_MEDICINE_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(AMAZONIAN_MEDICINE_SITES)


def _build_indigenous_map():
    """Map 5 -- Aboriginal & Indigenous Medicine."""
    m = _base_map(center=[10, 30], zoom=2)
    type_colors = {
        "Bush Medicine": "#10b981",
        "Sacred Healing Site": "#ef4444",
        "Educational Site": "#06b6d4",
        "Indigenous Center": "#f59e0b",
        "Traditional Healing": "#8b5cf6",
    }
    for site in INDIGENOUS_MEDICINE_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(INDIGENOUS_MEDICINE_SITES)


def _build_tibetan_map():
    """Map 6 -- Tibetan Medicine."""
    m = _base_map(center=[32, 90], zoom=4)
    type_colors = {
        "Medical Institute": "#ec4899",
        "Historical Site": "#ef4444",
        "Monastery": "#8b5cf6",
        "Memorial": "#f59e0b",
        "Treatment Center": "#10b981",
        "Cultural Heritage": "#06b6d4",
        "Academic Center": "#3b82f6",
    }
    for site in TIBETAN_MEDICINE_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(TIBETAN_MEDICINE_SITES)


def _build_greek_roman_map():
    """Map 7 -- Greek & Roman Medicine."""
    m = _base_map(center=[38, 20], zoom=4)
    type_colors = {
        "Healing Temple": "#06b6d4",
        "Historical Site": "#f59e0b",
        "Historical Origin": "#ef4444",
        "Ancient School": "#8b5cf6",
        "Thermal Healing": "#3b82f6",
        "Archaeological Site": "#f97316",
        "Historical Hospital": "#ec4899",
    }
    for site in GREEK_ROMAN_MEDICINE_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(GREEK_ROMAN_MEDICINE_SITES)


def _build_medieval_herbalism_map():
    """Map 8 -- Medieval European Herbalism."""
    m = _base_map(center=[47, 8], zoom=4)
    type_colors = {
        "Monastery": "#8b5cf6",
        "Physic Garden": "#10b981",
        "Medical School": "#06b6d4",
        "Historical Site": "#ef4444",
        "Apothecary": "#f97316",
        "Translation Center": "#f59e0b",
    }
    for site in MEDIEVAL_HERBALISM_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(MEDIEVAL_HERBALISM_SITES)


def _build_hot_springs_map():
    """Map 9 -- Hot Springs & Thermal Healing."""
    m = _base_map(center=[30, 20], zoom=2)
    type_colors = {
        "Onsen": "#ef4444",
        "Geothermal Spa": "#3b82f6",
        "Natural Hot Spring": "#10b981",
        "Thermal Bath": "#f59e0b",
        "Thermal Island": "#ec4899",
        "Roman Bath": "#8b5cf6",
        "Thermal Terrace": "#06b6d4",
        "Spa Town": "#f97316",
        "National Park": "#22c55e",
        "Hammam": "#a855f7",
    }
    for site in HOT_SPRINGS_SITES:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Era": site["era"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(HOT_SPRINGS_SITES)


def _build_unesco_medicine_map():
    """Map 10 -- UNESCO Intangible Medicine Heritage."""
    m = _base_map(center=[20, 30], zoom=2)
    type_colors = {
        "Medical Practice": "#ef4444",
        "Medical System": "#06b6d4",
        "Healing Practice": "#10b981",
        "Traditional Art/Healing": "#f59e0b",
        "Food Medicine": "#22c55e",
        "Medical Text": "#8b5cf6",
        "Herbal Medicine": "#10b981",
        "Healing Custom": "#f97316",
        "Martial Healing": "#ec4899",
        "Bathing Healing": "#3b82f6",
        "Medical Tool": "#64748b",
        "Healing Music": "#a855f7",
        "Healing Ritual": "#ef4444",
        "Healing Dance": "#f59e0b",
        "Healing Performance": "#ec4899",
    }
    for site in UNESCO_MEDICINE_HERITAGE:
        color = type_colors.get(site["type"], "#8b97b0")
        popup = _safe_popup({
            "_title": site["name"],
            "Type": site["type"],
            "Year Inscribed": site["year"],
            "Description": site["desc"],
            "Country": site["country"],
        })
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=popup,
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(UNESCO_MEDICINE_HERITAGE)


# Builder registry
MAP_BUILDERS = {
    MAP_TYPES[0]: _build_tcm_map,
    MAP_TYPES[1]: _build_ayurvedic_map,
    MAP_TYPES[2]: _build_african_healing_map,
    MAP_TYPES[3]: _build_amazonian_map,
    MAP_TYPES[4]: _build_indigenous_map,
    MAP_TYPES[5]: _build_tibetan_map,
    MAP_TYPES[6]: _build_greek_roman_map,
    MAP_TYPES[7]: _build_medieval_herbalism_map,
    MAP_TYPES[8]: _build_hot_springs_map,
    MAP_TYPES[9]: _build_unesco_medicine_map,
}


# ═══════════════════════════════════════════════════════════════════════════════
# INFO PANELS (Expander content for each map type)
# ═══════════════════════════════════════════════════════════════════════════════

_INFO_PANELS = {
    MAP_TYPES[0]: (
        "About Traditional Chinese Medicine",
        "Traditional Chinese Medicine (TCM) is a comprehensive medical system with over 2,500 years of "
        "documented history. Core practices include acupuncture, herbal medicine (using thousands of "
        "natural substances), moxibustion, cupping, and tui na massage. Key texts include the Huangdi "
        "Neijing (Yellow Emperor's Classic) and Li Shizhen's Bencao Gangmu (Compendium of Materia Medica) "
        "with 1,892 medicinal substances. TCM is based on concepts of qi, yin-yang balance, and the "
        "five elements. Today over 100,000 TCM practitioners work in China alone, and the WHO included "
        "TCM in its International Classification of Diseases (ICD-11) in 2019."
    ),
    MAP_TYPES[1]: (
        "About Ayurvedic Medicine",
        "Ayurveda ('Science of Life') is one of the world's oldest medical systems, originating in India "
        "over 3,000 years ago. It is based on the concept of three doshas (Vata, Pitta, Kapha) and aims "
        "to balance mind, body, and spirit. Foundational texts include the Charaka Samhita (internal "
        "medicine) and Sushruta Samhita (surgery -- describing 300+ surgical procedures). Ayurveda uses "
        "over 8,000 herbal formulations, Panchakarma detoxification, yoga, and dietary therapy. India's "
        "AYUSH ministry now oversees 785,000+ registered Ayurvedic practitioners."
    ),
    MAP_TYPES[2]: (
        "About African Traditional Healing",
        "Africa has the world's most diverse traditional medicine systems, with an estimated 80% of the "
        "population relying on traditional healers. Major traditions include South African sangomas "
        "(diviner-healers), Yoruba babalawo (Ifa divination), West African herbalists, and Malagasy "
        "ombiasa. The continent is home to over 5,000 known medicinal plant species. The WHO Africa "
        "Regional Strategy for Traditional Medicine (2013) promotes integration with modern healthcare. "
        "Key organizations like PROMETRA work to document and preserve these ancient knowledge systems."
    ),
    MAP_TYPES[3]: (
        "About Amazonian Plant Medicine",
        "The Amazon basin contains the world's richest pharmacopoeia with over 80,000 plant species, "
        "of which indigenous peoples use thousands medicinally. Ayahuasca (Banisteriopsis caapi + "
        "Psychotria viridis) is the best-known sacred plant medicine, used by dozens of indigenous "
        "groups for healing, divination, and spiritual communion. Shamanic traditions include the "
        "Shipibo-Conibo icaros (healing songs), Mazatec mushroom ceremonies, and Andean coca leaf "
        "medicine. Ethnobotanists estimate that indigenous knowledge has led to 25% of modern "
        "pharmaceutical drugs."
    ),
    MAP_TYPES[4]: (
        "About Aboriginal & Indigenous Medicine",
        "Aboriginal Australians hold the world's oldest continuous medical tradition, spanning over "
        "60,000 years. Bush medicine uses eucalyptus, tea tree, emu bush, and hundreds of other native "
        "plants. Native American traditions include the medicine wheel, sweat lodge healing, and "
        "extensive herbal pharmacopoeia. Maori rongoa uses native New Zealand plants like kawakawa, "
        "manuka, and harakeke. These systems share common themes: connection to land, spiritual "
        "healing dimensions, and holistic approaches to health."
    ),
    MAP_TYPES[5]: (
        "About Tibetan Medicine",
        "Tibetan Medicine (Sowa Rigpa, 'Science of Healing') is a sophisticated system codified in the "
        "rGyud-bZhi (Four Medical Tantras) by Yuthog Yontan Gonpo in the 8th century. It synthesizes "
        "Indian Ayurveda, Chinese medicine, and native Tibetan Bon practices. Diagnosis uses pulse "
        "reading, urine analysis, and tongue examination. Treatment includes herbal formulas (using "
        "Himalayan plants), moxibustion, cupping, and spiritual practices. Sowa Rigpa was inscribed "
        "on the UNESCO Intangible Cultural Heritage list in 2018."
    ),
    MAP_TYPES[6]: (
        "About Greek & Roman Medicine",
        "Ancient Greek and Roman medicine laid the foundations of Western medical science. Hippocrates "
        "(460-370 BCE) established medicine as a rational discipline separate from religion. The "
        "Asclepions were healing temples where patients underwent 'incubation' (temple sleep) for "
        "dream-based diagnosis. Galen (129-216 CE) systematized anatomy, pharmacology, and the "
        "four humors theory that dominated European medicine for 1,500 years. Dioscorides' "
        "De Materia Medica catalogued 600 medicinal plants and remained the standard reference "
        "until the Renaissance."
    ),
    MAP_TYPES[7]: (
        "About Medieval European Herbalism",
        "Medieval European medicine was centered in monasteries, where monks preserved classical texts "
        "and cultivated physic gardens. Key figures include Hildegard von Bingen (who documented "
        "200+ herbal remedies), Walahfrid Strabo (Hortulus), and the physicians of the Schola Medica "
        "Salernitana. The Black Death (1347-1351) spurred plague doctors and new herbal fumigation "
        "techniques. The translation movement in Toledo and Cordoba brought Arabic medical knowledge "
        "(Avicenna's Canon of Medicine) into European practice. The founding of botanical gardens "
        "in Padua (1545) and Pisa (1544) marked the transition to Renaissance empirical medicine."
    ),
    MAP_TYPES[8]: (
        "About Hot Springs & Thermal Healing",
        "Balneotherapy (therapeutic bathing) is among humanity's oldest healing practices. Japanese "
        "onsen culture has used volcanic hot springs for centuries, with strict bathing etiquette and "
        "regional specialties. Roman thermae were engineering marvels combining hot, warm, and cold "
        "pools with massage and exercise. Budapest's 120+ thermal springs made it 'City of Spas.' "
        "Modern research confirms benefits for musculoskeletal conditions, skin diseases (especially "
        "psoriasis at the Blue Lagoon), and cardiovascular health. Mineral compositions vary widely: "
        "sulfur, silica, radium, bicarbonate, and chloride springs each offer different benefits."
    ),
    MAP_TYPES[9]: (
        "About UNESCO Intangible Medicine Heritage",
        "UNESCO's Intangible Cultural Heritage programme recognizes traditional practices at risk of "
        "disappearing. Several inscribed elements relate directly to traditional medicine and healing: "
        "acupuncture and moxibustion (2010), yoga (2016), Nuad Thai massage (2019), Finnish sauna "
        "culture (2020), and Sowa Rigpa Tibetan medicine (2018). The Donguibogam Korean medical "
        "encyclopedia is inscribed in the Memory of the World register. These recognitions help "
        "protect and promote traditional medical knowledge while encouraging intergenerational "
        "transmission of healing practices."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def _render_stats(selected_map: str):
    """Render summary statistics metrics for the selected map type."""

    if selected_map == MAP_TYPES[0]:
        # TCM
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(TCM_SITES))
        types = len(set(s["type"] for s in TCM_SITES))
        c2.metric("Site Types", types)
        markets = sum(1 for s in TCM_SITES if "Market" in s["type"])
        c3.metric("Herbal Markets", markets)
        academic = sum(1 for s in TCM_SITES if "Academic" in s["type"])
        c4.metric("Academic Centers", academic)

    elif selected_map == MAP_TYPES[1]:
        # Ayurveda
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(AYURVEDIC_SITES))
        countries = len(set(s["country"] for s in AYURVEDIC_SITES))
        c2.metric("Countries", countries)
        treatment = sum(1 for s in AYURVEDIC_SITES if "Treatment" in s["type"])
        c3.metric("Treatment Centers", treatment)
        academic = sum(1 for s in AYURVEDIC_SITES if "Academic" in s["type"])
        c4.metric("Academic Centers", academic)

    elif selected_map == MAP_TYPES[2]:
        # African
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(AFRICAN_HEALING_SITES))
        countries = len(set(s["country"] for s in AFRICAN_HEALING_SITES))
        c2.metric("Countries", countries)
        markets = sum(1 for s in AFRICAN_HEALING_SITES if "Market" in s["type"])
        c3.metric("Herbal Markets", markets)
        research = sum(1 for s in AFRICAN_HEALING_SITES if "Research" in s["type"])
        c4.metric("Research Centers", research)

    elif selected_map == MAP_TYPES[3]:
        # Amazonian
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(AMAZONIAN_MEDICINE_SITES))
        countries = len(set(s["country"] for s in AMAZONIAN_MEDICINE_SITES))
        c2.metric("Countries", countries)
        indigenous = sum(1 for s in AMAZONIAN_MEDICINE_SITES if "Indigenous" in s["type"])
        c3.metric("Indigenous Territories", indigenous)
        ayahuasca = sum(1 for s in AMAZONIAN_MEDICINE_SITES if "Ayahuasca" in s["type"])
        c4.metric("Ayahuasca Centers", ayahuasca)

    elif selected_map == MAP_TYPES[4]:
        # Indigenous
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(INDIGENOUS_MEDICINE_SITES))
        countries = len(set(s["country"] for s in INDIGENOUS_MEDICINE_SITES))
        c2.metric("Countries", countries)
        bush = sum(1 for s in INDIGENOUS_MEDICINE_SITES if "Bush" in s["type"])
        c3.metric("Bush Medicine Sites", bush)
        sacred = sum(1 for s in INDIGENOUS_MEDICINE_SITES if "Sacred" in s["type"])
        c4.metric("Sacred Healing Sites", sacred)

    elif selected_map == MAP_TYPES[5]:
        # Tibetan
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(TIBETAN_MEDICINE_SITES))
        countries = len(set(s["country"] for s in TIBETAN_MEDICINE_SITES))
        c2.metric("Countries", countries)
        monasteries = sum(1 for s in TIBETAN_MEDICINE_SITES if "Monastery" in s["type"])
        c3.metric("Monasteries", monasteries)
        institutes = sum(1 for s in TIBETAN_MEDICINE_SITES if "Institute" in s["type"])
        c4.metric("Medical Institutes", institutes)

    elif selected_map == MAP_TYPES[6]:
        # Greek & Roman
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(GREEK_ROMAN_MEDICINE_SITES))
        countries = len(set(s["country"] for s in GREEK_ROMAN_MEDICINE_SITES))
        c2.metric("Countries", countries)
        temples = sum(1 for s in GREEK_ROMAN_MEDICINE_SITES if "Temple" in s["type"])
        c3.metric("Healing Temples", temples)
        schools = sum(1 for s in GREEK_ROMAN_MEDICINE_SITES if "School" in s["type"])
        c4.metric("Medical Schools", schools)

    elif selected_map == MAP_TYPES[7]:
        # Medieval
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(MEDIEVAL_HERBALISM_SITES))
        countries = len(set(s["country"] for s in MEDIEVAL_HERBALISM_SITES))
        c2.metric("Countries", countries)
        gardens = sum(1 for s in MEDIEVAL_HERBALISM_SITES if "Garden" in s["type"])
        c3.metric("Physic Gardens", gardens)
        monasteries = sum(1 for s in MEDIEVAL_HERBALISM_SITES if "Monastery" in s["type"])
        c4.metric("Monasteries", monasteries)

    elif selected_map == MAP_TYPES[8]:
        # Hot Springs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sites", len(HOT_SPRINGS_SITES))
        countries = len(set(s["country"] for s in HOT_SPRINGS_SITES))
        c2.metric("Countries", countries)
        onsen = sum(1 for s in HOT_SPRINGS_SITES if s["type"] == "Onsen")
        c3.metric("Japanese Onsen", onsen)
        roman = sum(1 for s in HOT_SPRINGS_SITES if "Roman" in s["type"] or "Roman" in s["era"])
        c4.metric("Roman-Era Sites", roman)

    elif selected_map == MAP_TYPES[9]:
        # UNESCO
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Heritage Items", len(UNESCO_MEDICINE_HERITAGE))
        countries = len(set(s["country"] for s in UNESCO_MEDICINE_HERITAGE))
        c2.metric("Countries", countries)
        oldest = min(s["year"] for s in UNESCO_MEDICINE_HERITAGE)
        c3.metric("Earliest Inscription", str(oldest))
        newest = max(s["year"] for s in UNESCO_MEDICINE_HERITAGE)
        c4.metric("Latest Inscription", str(newest))


# ═══════════════════════════════════════════════════════════════════════════════
# LEGEND RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def _render_legend(selected_map: str):
    """Render a color-coded legend for the current map."""
    # Collect unique types from the data set
    data_map = {
        MAP_TYPES[0]: TCM_SITES,
        MAP_TYPES[1]: AYURVEDIC_SITES,
        MAP_TYPES[2]: AFRICAN_HEALING_SITES,
        MAP_TYPES[3]: AMAZONIAN_MEDICINE_SITES,
        MAP_TYPES[4]: INDIGENOUS_MEDICINE_SITES,
        MAP_TYPES[5]: TIBETAN_MEDICINE_SITES,
        MAP_TYPES[6]: GREEK_ROMAN_MEDICINE_SITES,
        MAP_TYPES[7]: MEDIEVAL_HERBALISM_SITES,
        MAP_TYPES[8]: HOT_SPRINGS_SITES,
        MAP_TYPES[9]: UNESCO_MEDICINE_HERITAGE,
    }
    sites = data_map.get(selected_map, [])
    if not sites:
        return

    # Get all unique types
    type_set = sorted(set(s["type"] for s in sites))

    # Pick color from the map builder's color dict - reconstruct minimal lookup
    all_type_colors = {
        "Foundational Text": "#ef4444", "Academic Center": "#06b6d4",
        "Archaeological Site": "#f59e0b", "Herbal Region": "#10b981",
        "Herbal Market": "#22c55e", "Memorial": "#ec4899",
        "Cultural Heritage": "#8b5cf6", "Historic Pharmacy": "#f97316",
        "Research Center": "#3b82f6", "Treatment Center": "#f59e0b",
        "Historical Origin": "#ef4444", "Ancient University": "#8b5cf6",
        "Sacred Site": "#ec4899", "Herbal Garden": "#10b981",
        "Regulatory Body": "#64748b", "Sangoma Center": "#8b5cf6",
        "Medicinal Garden": "#10b981", "Healer Community": "#f59e0b",
        "Divination Center": "#ec4899", "Vodun Center": "#ef4444",
        "Healer Network": "#f97316", "Sacred Plant Center": "#a855f7",
        "Ayahuasca Center": "#22c55e", "Retreat Center": "#10b981",
        "Spiritual Community": "#8b5cf6", "Indigenous Territory": "#ef4444",
        "Indigenous Center": "#ec4899", "Bush Medicine": "#10b981",
        "Sacred Healing Site": "#ef4444", "Educational Site": "#06b6d4",
        "Traditional Healing": "#8b5cf6", "Medical Institute": "#ec4899",
        "Historical Site": "#ef4444", "Monastery": "#8b5cf6",
        "Healing Temple": "#06b6d4", "Ancient School": "#8b5cf6",
        "Thermal Healing": "#3b82f6", "Historical Hospital": "#ec4899",
        "Physic Garden": "#10b981", "Medical School": "#06b6d4",
        "Apothecary": "#f97316", "Translation Center": "#f59e0b",
        "Onsen": "#ef4444", "Geothermal Spa": "#3b82f6",
        "Natural Hot Spring": "#10b981", "Thermal Bath": "#f59e0b",
        "Thermal Island": "#ec4899", "Roman Bath": "#8b5cf6",
        "Thermal Terrace": "#06b6d4", "Spa Town": "#f97316",
        "National Park": "#22c55e", "Hammam": "#a855f7",
        "Medical Practice": "#ef4444", "Medical System": "#06b6d4",
        "Healing Practice": "#10b981", "Traditional Art/Healing": "#f59e0b",
        "Food Medicine": "#22c55e", "Medical Text": "#8b5cf6",
        "Herbal Medicine": "#10b981", "Healing Custom": "#f97316",
        "Martial Healing": "#ec4899", "Bathing Healing": "#3b82f6",
        "Medical Tool": "#64748b", "Healing Music": "#a855f7",
        "Healing Ritual": "#ef4444", "Healing Dance": "#f59e0b",
        "Healing Performance": "#ec4899", "Sacred Site": "#ef4444",
    }

    legend_items = " ".join([
        f'<span style="color:{all_type_colors.get(t, "#8b97b0")}; font-size:0.8rem;">'
        f'&#9679; {html.escape(t)}</span>'
        for t in type_set
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{legend_items}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def render_trad_medicine_maps_tab():
    """Render the Traditional Medicine Explorer tab in the Streamlit app."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>Traditional Medicine Explorer</h4>"
        "<p>Map traditional medicine systems, healing practices, ethnobotany, "
        "and therapeutic heritage across world cultures and history.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Controls ──
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_map = st.selectbox(
            "Select Medicine Tradition",
            MAP_TYPES,
            index=0,
            key="trad_medicine_map_type",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button(
            "Generate Map",
            key="trad_medicine_generate",
            type="primary",
        )

    st.caption(MAP_DESCRIPTIONS.get(selected_map, ""))

    if not generate:
        st.info(
            "Select a traditional medicine map type and click **Generate Map** "
            "to explore healing traditions worldwide."
        )
        return

    # ── Build Map ──
    with st.spinner(f"Building {selected_map} map..."):
        builder = MAP_BUILDERS.get(selected_map)
        if builder is None:
            st.error("Unknown map type.")
            return
        m, df = builder()

    # ── Summary Statistics ──
    st.markdown("---")
    st.subheader("Summary Statistics")
    _render_stats(selected_map)

    # ── Legend ──
    st.markdown("---")
    _render_legend(selected_map)

    # ── Folium Map ──
    st.subheader(f"{selected_map} Map")
    components.html(m._repr_html_(), height=500)

    # ── Data Table ──
    st.markdown("---")
    st.subheader("Data Table")
    st.dataframe(df, use_container_width=True)

    # ── CSV Download ──
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_data = csv_buf.getvalue()
    file_label = selected_map.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"trad_medicine_{file_label}.csv",
        mime="text/csv",
        key="trad_medicine_csv_download",
    )

    # ── Info Panel ──
    st.markdown("---")
    _render_info_panel(selected_map)


def _render_info_panel(selected_map: str):
    """Render an information expander for the given map type."""
    title, body = _INFO_PANELS.get(selected_map, ("Info", "No additional information."))
    with st.expander(title, expanded=False):
        st.markdown(body)


# ═══════════════════════════════════════════════════════════════════════════════
# Standalone testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(page_title="Traditional Medicine Explorer", layout="wide")
    render_trad_medicine_maps_tab()
