# -*- coding: utf-8 -*-
"""
Literature & Books Maps module for TerraScout AI.
Curated geographic datasets of Nobel laureates, literary cities, famous authors,
fictional places, libraries, publishers, bookshops, poetry, comics, and book festivals.
All data is embedded -- no external API required.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

# ═══════════════════════════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════

MODE_LIST = [
    "Nobel Literature Laureates",
    "Literary Cities",
    "Famous Authors' Homes",
    "Fictional Places",
    "World's Greatest Libraries",
    "Publishing Houses",
    "Bookshop Capitals",
    "Poetry Origins",
    "Comic & Manga Capitals",
    "Book Festivals",
]

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTES
# ═══════════════════════════════════════════════════════════════

MODE_COLORS = {
    "Nobel Literature Laureates": "#f59e0b",
    "Literary Cities": "#8b5cf6",
    "Famous Authors' Homes": "#06b6d4",
    "Fictional Places": "#ec4899",
    "World's Greatest Libraries": "#10b981",
    "Publishing Houses": "#f97316",
    "Bookshop Capitals": "#38bdf8",
    "Poetry Origins": "#a855f7",
    "Comic & Manga Capitals": "#ef4444",
    "Book Festivals": "#14b8a6",
}

CONTINENT_COLORS = {
    "Europe": "#8b5cf6",
    "North America": "#06b6d4",
    "South America": "#10b981",
    "Asia": "#f59e0b",
    "Africa": "#ef4444",
    "Oceania": "#ec4899",
    "Middle East": "#f97316",
}

# ═══════════════════════════════════════════════════════════════
# 1. NOBEL LITERATURE LAUREATES (~50)
# ═══════════════════════════════════════════════════════════════

NOBEL_LAUREATES = [
    {"name": "Sully Prudhomme", "year": 1901, "country": "France", "city": "Paris", "lat": 48.8566, "lon": 2.3522, "continent": "Europe"},
    {"name": "Theodor Mommsen", "year": 1902, "country": "Germany", "city": "Garding", "lat": 54.3317, "lon": 8.7826, "continent": "Europe"},
    {"name": "Bjornstjerne Bjornson", "year": 1903, "country": "Norway", "city": "Kvikne", "lat": 62.5500, "lon": 10.3167, "continent": "Europe"},
    {"name": "Frederic Mistral", "year": 1904, "country": "France", "city": "Maillane", "lat": 43.8333, "lon": 4.7833, "continent": "Europe"},
    {"name": "Henryk Sienkiewicz", "year": 1905, "country": "Poland", "city": "Wola Okrzejska", "lat": 51.5833, "lon": 21.8833, "continent": "Europe"},
    {"name": "Giosue Carducci", "year": 1906, "country": "Italy", "city": "Valdicastello", "lat": 43.9667, "lon": 10.2333, "continent": "Europe"},
    {"name": "Rudyard Kipling", "year": 1907, "country": "UK", "city": "Bombay (Mumbai)", "lat": 19.0760, "lon": 72.8777, "continent": "Asia"},
    {"name": "Rudolf Eucken", "year": 1908, "country": "Germany", "city": "Aurich", "lat": 53.4708, "lon": 7.4842, "continent": "Europe"},
    {"name": "Selma Lagerlof", "year": 1909, "country": "Sweden", "city": "Marbacka", "lat": 59.7500, "lon": 13.1667, "continent": "Europe"},
    {"name": "Paul Heyse", "year": 1910, "country": "Germany", "city": "Berlin", "lat": 52.5200, "lon": 13.4050, "continent": "Europe"},
    {"name": "Maurice Maeterlinck", "year": 1911, "country": "Belgium", "city": "Ghent", "lat": 51.0543, "lon": 3.7174, "continent": "Europe"},
    {"name": "Gerhart Hauptmann", "year": 1912, "country": "Germany", "city": "Szczawno-Zdroj", "lat": 50.7939, "lon": 16.2417, "continent": "Europe"},
    {"name": "Rabindranath Tagore", "year": 1913, "country": "India", "city": "Kolkata", "lat": 22.5726, "lon": 88.3639, "continent": "Asia"},
    {"name": "Romain Rolland", "year": 1915, "country": "France", "city": "Clamecy", "lat": 47.4600, "lon": 3.5200, "continent": "Europe"},
    {"name": "Wladyslaw Reymont", "year": 1924, "country": "Poland", "city": "Kobiele Wielkie", "lat": 51.1500, "lon": 19.8833, "continent": "Europe"},
    {"name": "George Bernard Shaw", "year": 1925, "country": "Ireland", "city": "Dublin", "lat": 53.3498, "lon": -6.2603, "continent": "Europe"},
    {"name": "Grazia Deledda", "year": 1926, "country": "Italy", "city": "Nuoro", "lat": 40.3210, "lon": 9.3312, "continent": "Europe"},
    {"name": "Henri Bergson", "year": 1927, "country": "France", "city": "Paris", "lat": 48.8606, "lon": 2.3376, "continent": "Europe"},
    {"name": "Thomas Mann", "year": 1929, "country": "Germany", "city": "Lubeck", "lat": 53.8655, "lon": 10.6866, "continent": "Europe"},
    {"name": "Sinclair Lewis", "year": 1930, "country": "USA", "city": "Sauk Centre", "lat": 45.7375, "lon": -94.9525, "continent": "North America"},
    {"name": "Erik Axel Karlfeldt", "year": 1931, "country": "Sweden", "city": "Folkarna", "lat": 60.3833, "lon": 16.0333, "continent": "Europe"},
    {"name": "John Galsworthy", "year": 1932, "country": "UK", "city": "Kingston Hill", "lat": 51.4085, "lon": -0.2628, "continent": "Europe"},
    {"name": "Luigi Pirandello", "year": 1934, "country": "Italy", "city": "Agrigento", "lat": 37.3111, "lon": 13.5766, "continent": "Europe"},
    {"name": "Eugene O'Neill", "year": 1936, "country": "USA", "city": "New York", "lat": 40.7128, "lon": -74.0060, "continent": "North America"},
    {"name": "Pearl Buck", "year": 1938, "country": "USA", "city": "Hillsboro", "lat": 38.1368, "lon": -80.2196, "continent": "North America"},
    {"name": "T.S. Eliot", "year": 1948, "country": "USA/UK", "city": "St. Louis", "lat": 38.6270, "lon": -90.1994, "continent": "North America"},
    {"name": "William Faulkner", "year": 1949, "country": "USA", "city": "New Albany", "lat": 34.4940, "lon": -89.0078, "continent": "North America"},
    {"name": "Ernest Hemingway", "year": 1954, "country": "USA", "city": "Oak Park", "lat": 41.8850, "lon": -87.7845, "continent": "North America"},
    {"name": "Albert Camus", "year": 1957, "country": "France", "city": "Dreal", "lat": 36.2764, "lon": 7.3956, "continent": "Africa"},
    {"name": "Boris Pasternak", "year": 1958, "country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173, "continent": "Europe"},
    {"name": "Salvatore Quasimodo", "year": 1959, "country": "Italy", "city": "Modica", "lat": 36.8580, "lon": 14.7606, "continent": "Europe"},
    {"name": "John Steinbeck", "year": 1962, "country": "USA", "city": "Salinas", "lat": 36.6777, "lon": -121.6555, "continent": "North America"},
    {"name": "Jean-Paul Sartre", "year": 1964, "country": "France", "city": "Paris", "lat": 48.8500, "lon": 2.3400, "continent": "Europe"},
    {"name": "Pablo Neruda", "year": 1971, "country": "Chile", "city": "Parral", "lat": -36.1393, "lon": -71.8271, "continent": "South America"},
    {"name": "Gabriel Garcia Marquez", "year": 1982, "country": "Colombia", "city": "Aracataca", "lat": 10.5910, "lon": -74.1899, "continent": "South America"},
    {"name": "Wole Soyinka", "year": 1986, "country": "Nigeria", "city": "Abeokuta", "lat": 7.1475, "lon": 3.3619, "continent": "Africa"},
    {"name": "Naguib Mahfouz", "year": 1988, "country": "Egypt", "city": "Cairo", "lat": 30.0444, "lon": 31.2357, "continent": "Africa"},
    {"name": "Octavio Paz", "year": 1990, "country": "Mexico", "city": "Mexico City", "lat": 19.4326, "lon": -99.1332, "continent": "North America"},
    {"name": "Toni Morrison", "year": 1993, "country": "USA", "city": "Lorain", "lat": 41.4528, "lon": -82.1824, "continent": "North America"},
    {"name": "Kenzaburo Oe", "year": 1994, "country": "Japan", "city": "Ose", "lat": 33.4500, "lon": 132.8833, "continent": "Asia"},
    {"name": "Seamus Heaney", "year": 1995, "country": "Ireland", "city": "Castledawson", "lat": 54.7500, "lon": -6.5667, "continent": "Europe"},
    {"name": "Jose Saramago", "year": 1998, "country": "Portugal", "city": "Azinhaga", "lat": 39.3605, "lon": -8.5342, "continent": "Europe"},
    {"name": "Gunter Grass", "year": 1999, "country": "Germany", "city": "Danzig (Gdansk)", "lat": 54.3520, "lon": 18.6466, "continent": "Europe"},
    {"name": "V.S. Naipaul", "year": 2001, "country": "Trinidad", "city": "Chaguanas", "lat": 10.5168, "lon": -61.4115, "continent": "South America"},
    {"name": "Orhan Pamuk", "year": 2006, "country": "Turkey", "city": "Istanbul", "lat": 41.0082, "lon": 28.9784, "continent": "Europe"},
    {"name": "Mario Vargas Llosa", "year": 2010, "country": "Peru", "city": "Arequipa", "lat": -16.4090, "lon": -71.5375, "continent": "South America"},
    {"name": "Mo Yan", "year": 2012, "country": "China", "city": "Gaomi", "lat": 36.3833, "lon": 119.7500, "continent": "Asia"},
    {"name": "Alice Munro", "year": 2013, "country": "Canada", "city": "Wingham", "lat": 43.8881, "lon": -81.3114, "continent": "North America"},
    {"name": "Bob Dylan", "year": 2016, "country": "USA", "city": "Duluth", "lat": 46.7867, "lon": -92.1005, "continent": "North America"},
    {"name": "Kazuo Ishiguro", "year": 2017, "country": "Japan/UK", "city": "Nagasaki", "lat": 32.7503, "lon": 129.8779, "continent": "Asia"},
    {"name": "Abdulrazak Gurnah", "year": 2021, "country": "Tanzania", "city": "Zanzibar", "lat": -6.1659, "lon": 39.2026, "continent": "Africa"},
]

# ═══════════════════════════════════════════════════════════════
# 2. LITERARY CITIES (~30)
# ═══════════════════════════════════════════════════════════════

LITERARY_CITIES = [
    {"city": "Edinburgh", "country": "UK", "lat": 55.9533, "lon": -3.1883, "designation": "UNESCO City of Literature (2004)", "note": "Home of Sir Walter Scott, Arthur Conan Doyle, J.K. Rowling", "continent": "Europe"},
    {"city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "designation": "UNESCO City of Literature (2008)", "note": "Vibrant literary festivals and publishing scene", "continent": "Oceania"},
    {"city": "Iowa City", "country": "USA", "lat": 41.6611, "lon": -91.5302, "designation": "UNESCO City of Literature (2008)", "note": "Iowa Writers' Workshop, oldest creative writing MFA", "continent": "North America"},
    {"city": "Dublin", "country": "Ireland", "lat": 53.3498, "lon": -6.2603, "designation": "UNESCO City of Literature (2010)", "note": "Joyce, Yeats, Beckett, Wilde, Shaw", "continent": "Europe"},
    {"city": "Reykjavik", "country": "Iceland", "lat": 64.1466, "lon": -21.9426, "designation": "UNESCO City of Literature (2011)", "note": "Highest books published per capita", "continent": "Europe"},
    {"city": "Norwich", "country": "UK", "lat": 52.6309, "lon": 1.2974, "designation": "UNESCO City of Literature (2012)", "note": "UEA Creative Writing program", "continent": "Europe"},
    {"city": "Krakow", "country": "Poland", "lat": 50.0647, "lon": 19.9450, "designation": "UNESCO City of Literature (2013)", "note": "Wislawa Szymborska, Czeslaw Milosz connections", "continent": "Europe"},
    {"city": "Heidelberg", "country": "Germany", "lat": 49.3988, "lon": 8.6724, "designation": "UNESCO City of Literature (2014)", "note": "German Romanticism birthplace", "continent": "Europe"},
    {"city": "Granada", "country": "Spain", "lat": 37.1773, "lon": -3.5986, "designation": "UNESCO City of Literature (2014)", "note": "Federico Garcia Lorca's birthplace region", "continent": "Europe"},
    {"city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "designation": "UNESCO City of Literature (2014)", "note": "Kafka, Kundera, Hrabal", "continent": "Europe"},
    {"city": "Baghdad", "country": "Iraq", "lat": 33.3152, "lon": 44.3661, "designation": "UNESCO City of Literature (2015)", "note": "One Thousand and One Nights origin", "continent": "Middle East"},
    {"city": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "designation": "UNESCO City of Literature (2015)", "note": "Carlos Ruiz Zafon, Cervantes connections", "continent": "Europe"},
    {"city": "Ljubljana", "country": "Slovenia", "lat": 46.0569, "lon": 14.5058, "designation": "UNESCO City of Literature (2015)", "note": "Rich poetic tradition", "continent": "Europe"},
    {"city": "Montevideo", "country": "Uruguay", "lat": -34.9011, "lon": -56.1645, "designation": "UNESCO City of Literature (2015)", "note": "Eduardo Galeano, Mario Benedetti", "continent": "South America"},
    {"city": "Nottingham", "country": "UK", "lat": 52.9548, "lon": -1.1581, "designation": "UNESCO City of Literature (2015)", "note": "Lord Byron, D.H. Lawrence heritage", "continent": "Europe"},
    {"city": "Obidos", "country": "Portugal", "lat": 39.3622, "lon": -9.1571, "designation": "Literary Village", "note": "Medieval village turned literary haven with bookshops", "continent": "Europe"},
    {"city": "Hay-on-Wye", "country": "UK", "lat": 52.0748, "lon": -3.1244, "designation": "Town of Books", "note": "Famous for its many bookshops and literary festival", "continent": "Europe"},
    {"city": "Concord", "country": "USA", "lat": 42.4604, "lon": -71.3489, "designation": "Literary Landmark", "note": "Thoreau, Emerson, Alcott, Hawthorne homes", "continent": "North America"},
    {"city": "Stratford-upon-Avon", "country": "UK", "lat": 52.1917, "lon": -1.7083, "designation": "Shakespeare's Birthplace", "note": "William Shakespeare born and buried here", "continent": "Europe"},
    {"city": "Weimar", "country": "Germany", "lat": 50.9795, "lon": 11.3235, "designation": "Classical Literary City", "note": "Goethe and Schiller's home city", "continent": "Europe"},
    {"city": "St. Petersburg", "country": "Russia", "lat": 59.9343, "lon": 30.3351, "designation": "Literary Capital", "note": "Dostoevsky, Pushkin, Gogol, Akhmatova", "continent": "Europe"},
    {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "designation": "World Literary Capital", "note": "Hugo, Balzac, Proust; Lost Generation hub", "continent": "Europe"},
    {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "designation": "World Literary Capital", "note": "Dickens, Woolf, Shakespeare's Globe", "continent": "Europe"},
    {"city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "designation": "World Literary Capital", "note": "Harlem Renaissance, Beat poets, publishing HQ", "continent": "North America"},
    {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "designation": "UNESCO City of Design / Literary Heritage", "note": "Borges, Cortazar; El Ateneo Grand Splendid", "continent": "South America"},
    {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "designation": "Major Literary Center", "note": "Murakami, Mishima, Kawabata heritage", "continent": "Asia"},
    {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "designation": "Literary Hub of India", "note": "Tagore, Bankim Chandra, College Street bookshops", "continent": "Asia"},
    {"city": "Havana", "country": "Cuba", "lat": 23.1136, "lon": -82.3666, "designation": "Literary Heritage City", "note": "Hemingway's adopted home, Carpentier, Lezama Lima", "continent": "North America"},
    {"city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "designation": "Literary Heritage City", "note": "Naguib Mahfouz's Cairo Trilogy setting", "continent": "Africa"},
    {"city": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "designation": "Classical Literary City", "note": "The Tale of Genji, classical Japanese poetry", "continent": "Asia"},
]

# ═══════════════════════════════════════════════════════════════
# 3. FAMOUS AUTHORS' HOMES (~50)
# ═══════════════════════════════════════════════════════════════

AUTHORS_HOMES = [
    {"author": "William Shakespeare", "birth_year": 1564, "city": "Stratford-upon-Avon", "country": "UK", "lat": 52.1917, "lon": -1.7083, "genre": "Drama/Poetry", "continent": "Europe"},
    {"author": "Miguel de Cervantes", "birth_year": 1547, "city": "Alcala de Henares", "country": "Spain", "lat": 40.4820, "lon": -3.3635, "genre": "Novel", "continent": "Europe"},
    {"author": "Jane Austen", "birth_year": 1775, "city": "Steventon", "country": "UK", "lat": 51.2350, "lon": -1.2310, "genre": "Novel", "continent": "Europe"},
    {"author": "Charles Dickens", "birth_year": 1812, "city": "Portsmouth", "country": "UK", "lat": 50.8198, "lon": -1.0880, "genre": "Novel", "continent": "Europe"},
    {"author": "Leo Tolstoy", "birth_year": 1828, "city": "Yasnaya Polyana", "country": "Russia", "lat": 54.0764, "lon": 37.5256, "genre": "Novel", "continent": "Europe"},
    {"author": "Fyodor Dostoevsky", "birth_year": 1821, "city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "genre": "Novel", "continent": "Europe"},
    {"author": "Victor Hugo", "birth_year": 1802, "city": "Besancon", "country": "France", "lat": 47.2378, "lon": 6.0241, "genre": "Novel/Poetry", "continent": "Europe"},
    {"author": "Emily Bronte", "birth_year": 1818, "city": "Thornton", "country": "UK", "lat": 53.8138, "lon": -1.8334, "genre": "Novel", "continent": "Europe"},
    {"author": "Mark Twain", "birth_year": 1835, "city": "Florida, Missouri", "country": "USA", "lat": 39.2953, "lon": -91.8999, "genre": "Novel/Humor", "continent": "North America"},
    {"author": "Emily Dickinson", "birth_year": 1830, "city": "Amherst", "country": "USA", "lat": 42.3732, "lon": -72.5199, "genre": "Poetry", "continent": "North America"},
    {"author": "Oscar Wilde", "birth_year": 1854, "city": "Dublin", "country": "Ireland", "lat": 53.3392, "lon": -6.2617, "genre": "Drama/Novel", "continent": "Europe"},
    {"author": "Franz Kafka", "birth_year": 1883, "city": "Prague", "country": "Czech Republic", "lat": 50.0880, "lon": 14.4208, "genre": "Novel", "continent": "Europe"},
    {"author": "James Joyce", "birth_year": 1882, "city": "Dublin", "country": "Ireland", "lat": 53.3340, "lon": -6.2535, "genre": "Novel", "continent": "Europe"},
    {"author": "Marcel Proust", "birth_year": 1871, "city": "Auteuil, Paris", "country": "France", "lat": 48.8470, "lon": 2.2580, "genre": "Novel", "continent": "Europe"},
    {"author": "Virginia Woolf", "birth_year": 1882, "city": "London", "country": "UK", "lat": 51.4966, "lon": -0.1764, "genre": "Novel", "continent": "Europe"},
    {"author": "Ernest Hemingway", "birth_year": 1899, "city": "Oak Park", "country": "USA", "lat": 41.8850, "lon": -87.7845, "genre": "Novel", "continent": "North America"},
    {"author": "F. Scott Fitzgerald", "birth_year": 1896, "city": "St. Paul", "country": "USA", "lat": 44.9537, "lon": -93.0900, "genre": "Novel", "continent": "North America"},
    {"author": "Jorge Luis Borges", "birth_year": 1899, "city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "genre": "Short Story", "continent": "South America"},
    {"author": "Pablo Neruda", "birth_year": 1904, "city": "Parral", "country": "Chile", "lat": -36.1393, "lon": -71.8271, "genre": "Poetry", "continent": "South America"},
    {"author": "Gabriel Garcia Marquez", "birth_year": 1927, "city": "Aracataca", "country": "Colombia", "lat": 10.5910, "lon": -74.1899, "genre": "Novel", "continent": "South America"},
    {"author": "Chinua Achebe", "birth_year": 1930, "city": "Ogidi", "country": "Nigeria", "lat": 6.1728, "lon": 6.8388, "genre": "Novel", "continent": "Africa"},
    {"author": "Haruki Murakami", "birth_year": 1949, "city": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "genre": "Novel", "continent": "Asia"},
    {"author": "Yasunari Kawabata", "birth_year": 1899, "city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "genre": "Novel", "continent": "Asia"},
    {"author": "Rabindranath Tagore", "birth_year": 1861, "city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "genre": "Poetry/Novel", "continent": "Asia"},
    {"author": "Dante Alighieri", "birth_year": 1265, "city": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "genre": "Poetry", "continent": "Europe"},
    {"author": "Giovanni Boccaccio", "birth_year": 1313, "city": "Certaldo", "country": "Italy", "lat": 43.5482, "lon": 11.0393, "genre": "Novel/Poetry", "continent": "Europe"},
    {"author": "Giacomo Leopardi", "birth_year": 1798, "city": "Recanati", "country": "Italy", "lat": 43.4038, "lon": 13.5498, "genre": "Poetry", "continent": "Europe"},
    {"author": "Johann Wolfgang von Goethe", "birth_year": 1749, "city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821, "genre": "Poetry/Novel", "continent": "Europe"},
    {"author": "Hans Christian Andersen", "birth_year": 1805, "city": "Odense", "country": "Denmark", "lat": 55.4038, "lon": 10.4024, "genre": "Fairy Tales", "continent": "Europe"},
    {"author": "Anton Chekhov", "birth_year": 1860, "city": "Taganrog", "country": "Russia", "lat": 47.2362, "lon": 38.8969, "genre": "Drama/Short Story", "continent": "Europe"},
    {"author": "Herman Melville", "birth_year": 1819, "city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "genre": "Novel", "continent": "North America"},
    {"author": "Edgar Allan Poe", "birth_year": 1809, "city": "Boston", "country": "USA", "lat": 42.3601, "lon": -71.0589, "genre": "Poetry/Horror", "continent": "North America"},
    {"author": "Walt Whitman", "birth_year": 1819, "city": "West Hills", "country": "USA", "lat": 40.8168, "lon": -73.4318, "genre": "Poetry", "continent": "North America"},
    {"author": "Toni Morrison", "birth_year": 1931, "city": "Lorain", "country": "USA", "lat": 41.4528, "lon": -82.1824, "genre": "Novel", "continent": "North America"},
    {"author": "Isabel Allende", "birth_year": 1942, "city": "Lima", "country": "Peru", "lat": -12.0464, "lon": -77.0428, "genre": "Novel", "continent": "South America"},
    {"author": "Yukio Mishima", "birth_year": 1925, "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "genre": "Novel/Drama", "continent": "Asia"},
    {"author": "Lu Xun", "birth_year": 1881, "city": "Shaoxing", "country": "China", "lat": 30.0000, "lon": 120.5833, "genre": "Short Story", "continent": "Asia"},
    {"author": "Naguib Mahfouz", "birth_year": 1911, "city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "genre": "Novel", "continent": "Africa"},
    {"author": "Wole Soyinka", "birth_year": 1934, "city": "Abeokuta", "country": "Nigeria", "lat": 7.1475, "lon": 3.3619, "genre": "Drama/Poetry", "continent": "Africa"},
    {"author": "Mikhail Bulgakov", "birth_year": 1891, "city": "Kyiv", "country": "Ukraine", "lat": 50.4501, "lon": 30.5234, "genre": "Novel", "continent": "Europe"},
    {"author": "Alexandre Dumas", "birth_year": 1802, "city": "Villers-Cotterets", "country": "France", "lat": 49.2530, "lon": 3.0890, "genre": "Novel", "continent": "Europe"},
    {"author": "Gustave Flaubert", "birth_year": 1821, "city": "Rouen", "country": "France", "lat": 49.4432, "lon": 1.0999, "genre": "Novel", "continent": "Europe"},
    {"author": "Hermann Hesse", "birth_year": 1877, "city": "Calw", "country": "Germany", "lat": 48.7148, "lon": 8.7404, "genre": "Novel", "continent": "Europe"},
    {"author": "Italo Calvino", "birth_year": 1923, "city": "Santiago de las Vegas", "country": "Cuba", "lat": 22.9667, "lon": -82.3833, "genre": "Novel", "continent": "North America"},
    {"author": "Fernando Pessoa", "birth_year": 1888, "city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393, "genre": "Poetry", "continent": "Europe"},
    {"author": "Murasaki Shikibu", "birth_year": 978, "city": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "genre": "Novel", "continent": "Asia"},
    {"author": "Rumi", "birth_year": 1207, "city": "Balkh", "country": "Afghanistan", "lat": 36.7550, "lon": 66.8975, "genre": "Poetry", "continent": "Asia"},
    {"author": "Omar Khayyam", "birth_year": 1048, "city": "Nishapur", "country": "Iran", "lat": 36.2139, "lon": 58.7961, "genre": "Poetry", "continent": "Middle East"},
    {"author": "R.K. Narayan", "birth_year": 1906, "city": "Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "genre": "Novel", "continent": "Asia"},
    {"author": "Ngugi wa Thiong'o", "birth_year": 1938, "city": "Kamiriithu", "country": "Kenya", "lat": -1.0893, "lon": 36.6628, "genre": "Novel", "continent": "Africa"},
]

# ═══════════════════════════════════════════════════════════════
# 4. FICTIONAL PLACES (~30)
# ═══════════════════════════════════════════════════════════════

FICTIONAL_PLACES = [
    {"fictional_name": "Macondo", "book": "One Hundred Years of Solitude", "author": "G. Garcia Marquez", "real_place": "Aracataca, Colombia", "lat": 10.5910, "lon": -74.1899, "continent": "South America"},
    {"fictional_name": "Yoknapatawpha County", "book": "Absalom, Absalom!", "author": "William Faulkner", "real_place": "Lafayette County, Mississippi", "lat": 34.3665, "lon": -89.5186, "continent": "North America"},
    {"fictional_name": "Manderley", "book": "Rebecca", "author": "Daphne du Maurier", "real_place": "Menabilly, Cornwall", "lat": 50.3356, "lon": -4.7183, "continent": "Europe"},
    {"fictional_name": "221B Baker Street", "book": "Sherlock Holmes", "author": "Arthur Conan Doyle", "real_place": "London, UK", "lat": 51.5238, "lon": -0.1585, "continent": "Europe"},
    {"fictional_name": "The Shire", "book": "The Lord of the Rings", "author": "J.R.R. Tolkien", "real_place": "Sarehole, Birmingham", "lat": 52.4369, "lon": -1.8563, "continent": "Europe"},
    {"fictional_name": "Hogwarts", "book": "Harry Potter", "author": "J.K. Rowling", "real_place": "Edinburgh / Alnwick Castle", "lat": 55.4155, "lon": -1.7057, "continent": "Europe"},
    {"fictional_name": "Barchester", "book": "Barchester Towers", "author": "Anthony Trollope", "real_place": "Salisbury, UK", "lat": 51.0688, "lon": -1.7945, "continent": "Europe"},
    {"fictional_name": "Egdon Heath", "book": "Return of the Native", "author": "Thomas Hardy", "real_place": "Dorset heathland, UK", "lat": 50.7197, "lon": -2.0944, "continent": "Europe"},
    {"fictional_name": "Wuthering Heights", "book": "Wuthering Heights", "author": "Emily Bronte", "real_place": "Top Withens, Yorkshire", "lat": 53.8340, "lon": -2.0230, "continent": "Europe"},
    {"fictional_name": "Green Gables", "book": "Anne of Green Gables", "author": "L.M. Montgomery", "real_place": "Cavendish, PEI, Canada", "lat": 46.4920, "lon": -63.3874, "continent": "North America"},
    {"fictional_name": "Narnia (Lamp Post)", "book": "The Chronicles of Narnia", "author": "C.S. Lewis", "real_place": "Rostrevor, N. Ireland", "lat": 54.1000, "lon": -6.2000, "continent": "Europe"},
    {"fictional_name": "Dracula's Castle", "book": "Dracula", "author": "Bram Stoker", "real_place": "Bran Castle, Romania", "lat": 45.5150, "lon": 25.3672, "continent": "Europe"},
    {"fictional_name": "Treasure Island", "book": "Treasure Island", "author": "R.L. Stevenson", "real_place": "Unst, Shetland (inspiration)", "lat": 60.7500, "lon": -0.8667, "continent": "Europe"},
    {"fictional_name": "Lilliput", "book": "Gulliver's Travels", "author": "Jonathan Swift", "real_place": "Lilliput, Dublin Bay area", "lat": 53.2969, "lon": -6.1400, "continent": "Europe"},
    {"fictional_name": "Yoknapatawpha / Jefferson", "book": "The Sound and the Fury", "author": "William Faulkner", "real_place": "Oxford, Mississippi", "lat": 34.3665, "lon": -89.5186, "continent": "North America"},
    {"fictional_name": "Cannery Row", "book": "Cannery Row", "author": "John Steinbeck", "real_place": "Monterey, California", "lat": 36.6137, "lon": -121.8984, "continent": "North America"},
    {"fictional_name": "Casterbridge", "book": "The Mayor of Casterbridge", "author": "Thomas Hardy", "real_place": "Dorchester, Dorset, UK", "lat": 50.7154, "lon": -2.4376, "continent": "Europe"},
    {"fictional_name": "Illyria", "book": "Twelfth Night", "author": "William Shakespeare", "real_place": "Dalmatian Coast, Croatia", "lat": 43.5081, "lon": 16.4402, "continent": "Europe"},
    {"fictional_name": "Lisbeth Salander's Stockholm", "book": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson", "real_place": "Sodermalm, Stockholm", "lat": 59.3150, "lon": 18.0714, "continent": "Europe"},
    {"fictional_name": "Elsinore", "book": "Hamlet", "author": "William Shakespeare", "real_place": "Kronborg Castle, Denmark", "lat": 56.0389, "lon": 12.6214, "continent": "Europe"},
    {"fictional_name": "Malgudi", "book": "Swami and Friends", "author": "R.K. Narayan", "real_place": "Mysore, India", "lat": 12.2958, "lon": 76.6394, "continent": "Asia"},
    {"fictional_name": "Heart of Darkness River", "book": "Heart of Darkness", "author": "Joseph Conrad", "real_place": "Congo River, DR Congo", "lat": -4.3250, "lon": 15.3222, "continent": "Africa"},
    {"fictional_name": "Brideshead", "book": "Brideshead Revisited", "author": "Evelyn Waugh", "real_place": "Castle Howard, Yorkshire", "lat": 54.1253, "lon": -0.9066, "continent": "Europe"},
    {"fictional_name": "Earthsea", "book": "A Wizard of Earthsea", "author": "Ursula K. Le Guin", "real_place": "Oregon Coast (inspiration)", "lat": 44.6368, "lon": -124.0535, "continent": "North America"},
    {"fictional_name": "Samsa's Prague", "book": "The Metamorphosis", "author": "Franz Kafka", "real_place": "Old Town, Prague", "lat": 50.0880, "lon": 14.4208, "continent": "Europe"},
    {"fictional_name": "Combray", "book": "In Search of Lost Time", "author": "Marcel Proust", "real_place": "Illiers-Combray, France", "lat": 48.2956, "lon": 1.2461, "continent": "Europe"},
    {"fictional_name": "Gormenghast", "book": "Gormenghast Trilogy", "author": "Mervyn Peake", "real_place": "Sark, Channel Islands", "lat": 49.4319, "lon": -2.3614, "continent": "Europe"},
    {"fictional_name": "West Egg", "book": "The Great Gatsby", "author": "F. Scott Fitzgerald", "real_place": "Great Neck, Long Island", "lat": 40.8007, "lon": -73.7285, "continent": "North America"},
    {"fictional_name": "Hundred Acre Wood", "book": "Winnie-the-Pooh", "author": "A.A. Milne", "real_place": "Ashdown Forest, Sussex", "lat": 51.0617, "lon": 0.0450, "continent": "Europe"},
    {"fictional_name": "Neverland", "book": "Peter Pan", "author": "J.M. Barrie", "real_place": "Kensington Gardens, London", "lat": 51.5069, "lon": -0.1794, "continent": "Europe"},
]

# ═══════════════════════════════════════════════════════════════
# 5. WORLD'S GREATEST LIBRARIES (~40)
# ═══════════════════════════════════════════════════════════════

GREAT_LIBRARIES = [
    {"name": "Library of Congress", "city": "Washington D.C.", "country": "USA", "lat": 38.8887, "lon": -77.0047, "founded": 1800, "collection": "170+ million items", "continent": "North America"},
    {"name": "British Library", "city": "London", "country": "UK", "lat": 51.5299, "lon": -0.1272, "founded": 1753, "collection": "170+ million items", "continent": "Europe"},
    {"name": "Bibliotheque nationale de France", "city": "Paris", "country": "France", "lat": 48.8336, "lon": 2.3756, "founded": 1461, "collection": "40+ million items", "continent": "Europe"},
    {"name": "New York Public Library", "city": "New York", "country": "USA", "lat": 40.7532, "lon": -73.9822, "founded": 1895, "collection": "55+ million items", "continent": "North America"},
    {"name": "Russian State Library", "city": "Moscow", "country": "Russia", "lat": 55.7513, "lon": 37.6100, "founded": 1862, "collection": "47+ million items", "continent": "Europe"},
    {"name": "National Library of China", "city": "Beijing", "country": "China", "lat": 39.9437, "lon": 116.3186, "founded": 1909, "collection": "37+ million items", "continent": "Asia"},
    {"name": "National Diet Library", "city": "Tokyo", "country": "Japan", "lat": 35.6785, "lon": 139.7454, "founded": 1948, "collection": "45+ million items", "continent": "Asia"},
    {"name": "Library of Alexandria (Bibliotheca)", "city": "Alexandria", "country": "Egypt", "lat": 31.2089, "lon": 29.9092, "founded": 2002, "collection": "8+ million items (revival)", "continent": "Africa"},
    {"name": "Vatican Apostolic Library", "city": "Vatican City", "country": "Vatican", "lat": 41.9029, "lon": 12.4534, "founded": 1475, "collection": "1.1 million printed books, 80k manuscripts", "continent": "Europe"},
    {"name": "Bodleian Library", "city": "Oxford", "country": "UK", "lat": 51.7537, "lon": -1.2541, "founded": 1602, "collection": "13+ million items", "continent": "Europe"},
    {"name": "Trinity College Library", "city": "Dublin", "country": "Ireland", "lat": 53.3438, "lon": -6.2546, "founded": 1592, "collection": "7 million items, Book of Kells", "continent": "Europe"},
    {"name": "Royal Library of Denmark", "city": "Copenhagen", "country": "Denmark", "lat": 55.6736, "lon": 12.5822, "founded": 1648, "collection": "35+ million items", "continent": "Europe"},
    {"name": "National Library of Australia", "city": "Canberra", "country": "Australia", "lat": -35.2965, "lon": 149.1295, "founded": 1901, "collection": "10+ million items", "continent": "Oceania"},
    {"name": "Biblioteca Nacional de Espana", "city": "Madrid", "country": "Spain", "lat": 40.4237, "lon": -3.6894, "founded": 1712, "collection": "30+ million items", "continent": "Europe"},
    {"name": "Staatsbibliothek zu Berlin", "city": "Berlin", "country": "Germany", "lat": 52.5085, "lon": 13.3710, "founded": 1661, "collection": "25+ million items", "continent": "Europe"},
    {"name": "Royal Library of Sweden", "city": "Stockholm", "country": "Sweden", "lat": 59.3426, "lon": 18.0714, "founded": 1661, "collection": "18+ million items", "continent": "Europe"},
    {"name": "Library and Archives Canada", "city": "Ottawa", "country": "Canada", "lat": 45.4295, "lon": -75.6906, "founded": 1953, "collection": "54+ million items", "continent": "North America"},
    {"name": "National Library of India", "city": "Kolkata", "country": "India", "lat": 22.5364, "lon": 88.3417, "founded": 1836, "collection": "2.2+ million items", "continent": "Asia"},
    {"name": "Strahov Monastery Library", "city": "Prague", "country": "Czech Republic", "lat": 50.0860, "lon": 14.3886, "founded": 1143, "collection": "200k+ historic volumes", "continent": "Europe"},
    {"name": "Austrian National Library", "city": "Vienna", "country": "Austria", "lat": 48.2065, "lon": 16.3665, "founded": 1368, "collection": "12+ million items", "continent": "Europe"},
    {"name": "Biblioteca Nazionale Centrale", "city": "Florence", "country": "Italy", "lat": 43.7672, "lon": 11.2628, "founded": 1714, "collection": "6+ million items", "continent": "Europe"},
    {"name": "Biblioteca Apostolica Vaticana", "city": "Vatican City", "country": "Vatican", "lat": 41.9035, "lon": 12.4550, "founded": 1475, "collection": "Ancient manuscripts collection", "continent": "Europe"},
    {"name": "National Library of Brazil", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9098, "lon": -43.1729, "founded": 1810, "collection": "9+ million items", "continent": "South America"},
    {"name": "Bavarian State Library", "city": "Munich", "country": "Germany", "lat": 48.1497, "lon": 11.5799, "founded": 1558, "collection": "10+ million items", "continent": "Europe"},
    {"name": "National Library of South Africa", "city": "Cape Town", "country": "South Africa", "lat": -33.9285, "lon": 18.4164, "founded": 1818, "collection": "4+ million items", "continent": "Africa"},
    {"name": "Admont Abbey Library", "city": "Admont", "country": "Austria", "lat": 47.5742, "lon": 14.4613, "founded": 1776, "collection": "Largest monastery library in the world", "continent": "Europe"},
    {"name": "Joanina Library", "city": "Coimbra", "country": "Portugal", "lat": 40.2074, "lon": -8.4259, "founded": 1728, "collection": "Baroque masterpiece, 60k+ volumes", "continent": "Europe"},
    {"name": "Royal Portuguese Reading Room", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9060, "lon": -43.1820, "founded": 1837, "collection": "350k+ Portuguese volumes", "continent": "South America"},
    {"name": "George Peabody Library", "city": "Baltimore", "country": "USA", "lat": 39.2975, "lon": -76.6152, "founded": 1878, "collection": "300k+ volumes in atrium", "continent": "North America"},
    {"name": "Stuttgart City Library", "city": "Stuttgart", "country": "Germany", "lat": 48.7901, "lon": 9.1860, "founded": 2011, "collection": "Modern architectural gem", "continent": "Europe"},
    {"name": "Tianjin Binhai Library", "city": "Tianjin", "country": "China", "lat": 39.0456, "lon": 117.7856, "founded": 2017, "collection": "1.2 million books, futuristic design", "continent": "Asia"},
    {"name": "National Library of Korea", "city": "Seoul", "country": "South Korea", "lat": 37.4946, "lon": 127.0066, "founded": 1945, "collection": "12+ million items", "continent": "Asia"},
    {"name": "National Library of Argentina", "city": "Buenos Aires", "country": "Argentina", "lat": -34.5825, "lon": -58.3965, "founded": 1810, "collection": "4+ million items; Borges was director", "continent": "South America"},
    {"name": "El Ateneo Grand Splendid", "city": "Buenos Aires", "country": "Argentina", "lat": -34.5955, "lon": -58.3966, "founded": 2000, "collection": "Theatre-turned-bookstore, 120k books", "continent": "South America"},
    {"name": "Sainte-Genevieve Library", "city": "Paris", "country": "France", "lat": 48.8466, "lon": 2.3462, "founded": 1851, "collection": "2+ million items", "continent": "Europe"},
    {"name": "Helsinki Central Library Oodi", "city": "Helsinki", "country": "Finland", "lat": 60.1741, "lon": 24.9383, "founded": 2018, "collection": "Modern public library masterpiece", "continent": "Europe"},
    {"name": "National Library of Israel", "city": "Jerusalem", "country": "Israel", "lat": 31.7767, "lon": 35.1968, "founded": 1892, "collection": "5+ million items", "continent": "Middle East"},
    {"name": "Rampur Raza Library", "city": "Rampur", "country": "India", "lat": 28.7930, "lon": 79.0250, "founded": 1774, "collection": "Rare Mughal manuscripts", "continent": "Asia"},
    {"name": "Abbey Library of Saint Gall", "city": "St. Gallen", "country": "Switzerland", "lat": 47.4233, "lon": 9.3774, "founded": 612, "collection": "UNESCO site, oldest library in Switzerland", "continent": "Europe"},
    {"name": "National Library of Mexico", "city": "Mexico City", "country": "Mexico", "lat": 19.3262, "lon": -99.1761, "founded": 1867, "collection": "1.2+ million items", "continent": "North America"},
]

# ═══════════════════════════════════════════════════════════════
# 6. PUBLISHING HOUSES (~30)
# ═══════════════════════════════════════════════════════════════

PUBLISHING_HOUSES = [
    {"name": "Penguin Random House", "city": "New York", "country": "USA", "lat": 40.7580, "lon": -73.9740, "founded": 1927, "note": "World's largest trade publisher", "continent": "North America"},
    {"name": "HarperCollins", "city": "New York", "country": "USA", "lat": 40.7549, "lon": -73.9840, "founded": 1817, "note": "Big Five publisher, owned by News Corp", "continent": "North America"},
    {"name": "Simon & Schuster", "city": "New York", "country": "USA", "lat": 40.7614, "lon": -73.9776, "founded": 1924, "note": "Major US publisher", "continent": "North America"},
    {"name": "Hachette Livre", "city": "Paris", "country": "France", "lat": 48.8750, "lon": 2.3194, "founded": 1826, "note": "Largest publisher in France", "continent": "Europe"},
    {"name": "Macmillan Publishers", "city": "London", "country": "UK", "lat": 51.5340, "lon": -0.1199, "founded": 1843, "note": "Big Five member, Flatiron imprint", "continent": "Europe"},
    {"name": "Oxford University Press", "city": "Oxford", "country": "UK", "lat": 51.7546, "lon": -1.2554, "founded": 1586, "note": "Oldest university press in the world", "continent": "Europe"},
    {"name": "Cambridge University Press", "city": "Cambridge", "country": "UK", "lat": 52.2053, "lon": 0.1218, "founded": 1534, "note": "World's oldest publishing house", "continent": "Europe"},
    {"name": "Gallimard", "city": "Paris", "country": "France", "lat": 48.8554, "lon": 2.3268, "founded": 1911, "note": "Proust, Camus, Sartre publisher", "continent": "Europe"},
    {"name": "Feltrinelli", "city": "Milan", "country": "Italy", "lat": 45.4668, "lon": 9.1905, "founded": 1954, "note": "Published Doctor Zhivago first edition", "continent": "Europe"},
    {"name": "Mondadori", "city": "Milan", "country": "Italy", "lat": 45.4750, "lon": 9.1780, "founded": 1907, "note": "Italy's largest publisher", "continent": "Europe"},
    {"name": "Springer Nature", "city": "Berlin", "country": "Germany", "lat": 52.5090, "lon": 13.3890, "founded": 1842, "note": "Major academic publisher", "continent": "Europe"},
    {"name": "Shueisha", "city": "Tokyo", "country": "Japan", "lat": 35.6987, "lon": 139.7138, "founded": 1925, "note": "Weekly Shonen Jump publisher", "continent": "Asia"},
    {"name": "Kodansha", "city": "Tokyo", "country": "Japan", "lat": 35.7147, "lon": 139.7258, "founded": 1909, "note": "Japan's largest publisher", "continent": "Asia"},
    {"name": "Planeta", "city": "Barcelona", "country": "Spain", "lat": 41.3962, "lon": 2.1620, "founded": 1949, "note": "Largest Spanish-language publisher", "continent": "Europe"},
    {"name": "Suhrkamp Verlag", "city": "Berlin", "country": "Germany", "lat": 52.5244, "lon": 13.3910, "founded": 1950, "note": "Hesse, Brecht, Handke publisher", "continent": "Europe"},
    {"name": "Bloomsbury Publishing", "city": "London", "country": "UK", "lat": 51.5235, "lon": -0.1268, "founded": 1986, "note": "Published Harry Potter", "continent": "Europe"},
    {"name": "Einaudi", "city": "Turin", "country": "Italy", "lat": 45.0703, "lon": 7.6869, "founded": 1933, "note": "Primo Levi, Calvino publisher", "continent": "Europe"},
    {"name": "Faber & Faber", "city": "London", "country": "UK", "lat": 51.5200, "lon": -0.1150, "founded": 1929, "note": "T.S. Eliot was director; poetry leader", "continent": "Europe"},
    {"name": "Alma Littera", "city": "Vilnius", "country": "Lithuania", "lat": 54.6872, "lon": 25.2797, "founded": 1990, "note": "Largest Baltic publisher", "continent": "Europe"},
    {"name": "Norstedts", "city": "Stockholm", "country": "Sweden", "lat": 59.3290, "lon": 18.0626, "founded": 1823, "note": "Sweden's oldest publisher", "continent": "Europe"},
    {"name": "Penguin India", "city": "New Delhi", "country": "India", "lat": 28.6139, "lon": 77.2090, "founded": 1985, "note": "Major English-language publisher in India", "continent": "Asia"},
    {"name": "Record (Grupo Editorial)", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9068, "lon": -43.1729, "founded": 1942, "note": "Major Brazilian publisher", "continent": "South America"},
    {"name": "Fondo de Cultura Economica", "city": "Mexico City", "country": "Mexico", "lat": 19.3528, "lon": -99.1909, "founded": 1934, "note": "Major Latin American academic publisher", "continent": "North America"},
    {"name": "Allen & Unwin", "city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "founded": 1976, "note": "Largest independent publisher in Australia", "continent": "Oceania"},
    {"name": "Adelphi", "city": "Milan", "country": "Italy", "lat": 45.4730, "lon": 9.1870, "founded": 1962, "note": "Literary cult publisher of Italy", "continent": "Europe"},
    {"name": "Gyldendal", "city": "Copenhagen", "country": "Denmark", "lat": 55.6785, "lon": 12.5745, "founded": 1770, "note": "Denmark's largest publisher", "continent": "Europe"},
    {"name": "People's Literature Publishing", "city": "Beijing", "country": "China", "lat": 39.9280, "lon": 116.3890, "founded": 1951, "note": "China's foremost literary publisher", "continent": "Asia"},
    {"name": "Dar Al Shorouk", "city": "Cairo", "country": "Egypt", "lat": 30.0470, "lon": 31.2370, "founded": 1968, "note": "Leading Arabic literary publisher", "continent": "Africa"},
    {"name": "Kwani Trust", "city": "Nairobi", "country": "Kenya", "lat": -1.2864, "lon": 36.8172, "founded": 2003, "note": "Pioneering East African literary publisher", "continent": "Africa"},
    {"name": "Tusquets Editores", "city": "Barcelona", "country": "Spain", "lat": 41.3890, "lon": 2.1590, "founded": 1969, "note": "Literary fiction focus, Planeta group", "continent": "Europe"},
]

# ═══════════════════════════════════════════════════════════════
# 7. BOOKSHOP CAPITALS (~30)
# ═══════════════════════════════════════════════════════════════

BOOKSHOP_CAPITALS = [
    {"city": "Hay-on-Wye", "country": "UK", "lat": 52.0748, "lon": -3.1244, "note": "Town of Books, 20+ bookshops in tiny town", "famous_shop": "Richard Booth's Bookshop", "continent": "Europe"},
    {"city": "Paris", "country": "France", "lat": 48.8530, "lon": 2.3470, "note": "Shakespeare and Company, Left Bank bouquinistes", "famous_shop": "Shakespeare and Company", "continent": "Europe"},
    {"city": "Buenos Aires", "country": "Argentina", "lat": -34.5955, "lon": -58.3966, "note": "El Ateneo Grand Splendid, 700+ bookshops", "famous_shop": "El Ateneo Grand Splendid", "continent": "South America"},
    {"city": "Tokyo", "country": "Japan", "lat": 35.6950, "lon": 139.7710, "note": "Jimbocho district, 170+ bookshops", "famous_shop": "Jimbocho Book Town", "continent": "Asia"},
    {"city": "Lisbon", "country": "Portugal", "lat": 38.7117, "lon": -9.1426, "note": "Livraria Bertrand, world's oldest bookshop (1732)", "famous_shop": "Livraria Bertrand", "continent": "Europe"},
    {"city": "Porto", "country": "Portugal", "lat": 41.1466, "lon": -8.6155, "note": "Livraria Lello, JK Rowling inspiration", "famous_shop": "Livraria Lello", "continent": "Europe"},
    {"city": "London", "country": "UK", "lat": 51.5168, "lon": -0.1300, "note": "Charing Cross Road, Foyles, Hatchard's", "famous_shop": "Foyles", "continent": "Europe"},
    {"city": "New York", "country": "USA", "lat": 40.7335, "lon": -73.9905, "note": "Strand Book Store, 18 miles of books", "famous_shop": "Strand Book Store", "continent": "North America"},
    {"city": "Amsterdam", "country": "Netherlands", "lat": 52.3667, "lon": 4.8945, "note": "Oudemanhuispoort book market and shops", "famous_shop": "The American Book Center", "continent": "Europe"},
    {"city": "Prague", "country": "Czech Republic", "lat": 50.0879, "lon": 14.4210, "note": "Globe Bookstore, Kafka-related shops", "famous_shop": "Globe Bookstore and Cafe", "continent": "Europe"},
    {"city": "Barcelona", "country": "Spain", "lat": 41.3851, "lon": 2.1734, "note": "La Central, Llibreria Catalonia", "famous_shop": "La Central del Raval", "continent": "Europe"},
    {"city": "Edinburgh", "country": "UK", "lat": 55.9502, "lon": -3.1903, "note": "UNESCO City of Literature bookshop trail", "famous_shop": "Topping & Company", "continent": "Europe"},
    {"city": "Maastricht", "country": "Netherlands", "lat": 50.8514, "lon": 5.6910, "note": "Boekhandel Dominicanen in 13th-century church", "famous_shop": "Boekhandel Dominicanen", "continent": "Europe"},
    {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3520, "note": "College Street, largest secondhand book market in world", "famous_shop": "College Street Book Market", "continent": "Asia"},
    {"city": "Montevideo", "country": "Uruguay", "lat": -34.9058, "lon": -56.1913, "note": "Tristan Narvaja market and literary cafes", "famous_shop": "Tristan Narvaja Book Stalls", "continent": "South America"},
    {"city": "Obidos", "country": "Portugal", "lat": 39.3622, "lon": -9.1571, "note": "Medieval village with bookshops in every corner", "famous_shop": "Livraria de Santiago", "continent": "Europe"},
    {"city": "Redu", "country": "Belgium", "lat": 50.0042, "lon": 5.1578, "note": "Book Village with 20+ shops in tiny hamlet", "famous_shop": "Village du Livre", "continent": "Europe"},
    {"city": "Bredevoort", "country": "Netherlands", "lat": 51.9447, "lon": 6.6156, "note": "Dutch Book Town", "famous_shop": "Boekenstad Bredevoort", "continent": "Europe"},
    {"city": "Wigtown", "country": "UK", "lat": 54.8660, "lon": -4.4430, "note": "Scotland's National Book Town", "famous_shop": "The Bookshop Wigtown", "continent": "Europe"},
    {"city": "San Francisco", "country": "USA", "lat": 37.7975, "lon": -122.4064, "note": "City Lights Bookstore, Beat Generation HQ", "famous_shop": "City Lights Bookstore", "continent": "North America"},
    {"city": "Portland", "country": "USA", "lat": 45.5231, "lon": -122.6765, "note": "Powell's City of Books, world's largest indie bookstore", "famous_shop": "Powell's City of Books", "continent": "North America"},
    {"city": "Sedbergh", "country": "UK", "lat": 54.3230, "lon": -2.5290, "note": "England's Book Town", "famous_shop": "Westwood Books", "continent": "Europe"},
    {"city": "Stillwater", "country": "USA", "lat": 45.0564, "lon": -92.8057, "note": "Minnesota book town with multiple shops", "famous_shop": "Loome Theological Booksellers", "continent": "North America"},
    {"city": "Seoul", "country": "South Korea", "lat": 37.5706, "lon": 126.9853, "note": "Bosu-dong Book Street, Cheonggyecheon shops", "famous_shop": "Kyobo Book Centre", "continent": "Asia"},
    {"city": "Melbourne", "country": "Australia", "lat": -37.8130, "lon": 144.9670, "note": "Block Arcade and inner-city secondhand shops", "famous_shop": "Readings Carlton", "continent": "Oceania"},
    {"city": "Cape Town", "country": "South Africa", "lat": -33.9258, "lon": 18.4232, "note": "Clarke's Bookshop, Book Lounge", "famous_shop": "Clarke's Bookshop", "continent": "Africa"},
    {"city": "Istanbul", "country": "Turkey", "lat": 41.0115, "lon": 28.9760, "note": "Sahaflar Bazaar, oldest book market", "famous_shop": "Sahaflar Carsisi", "continent": "Europe"},
    {"city": "Beijing", "country": "China", "lat": 39.9196, "lon": 116.4180, "note": "Liulichang Cultural Street booksellers", "famous_shop": "Liulichang Book Market", "continent": "Asia"},
    {"city": "Fjaerland", "country": "Norway", "lat": 61.4030, "lon": 6.7614, "note": "Norwegian Book Town in fjord setting", "famous_shop": "Den Norske Bokbyen", "continent": "Europe"},
    {"city": "Clunes", "country": "Australia", "lat": -37.2942, "lon": 143.7868, "note": "Australia's first Book Town", "famous_shop": "Clunes Book Town shops", "continent": "Oceania"},
]

# ═══════════════════════════════════════════════════════════════
# 8. POETRY ORIGINS (~25)
# ═══════════════════════════════════════════════════════════════

POETRY_ORIGINS = [
    {"tradition": "Epic Poetry (Sumerian)", "region": "Mesopotamia", "country": "Iraq", "lat": 31.3260, "lon": 45.6360, "era": "c. 2100 BCE", "key_work": "Epic of Gilgamesh", "continent": "Middle East"},
    {"tradition": "Sanskrit Poetry", "region": "Vedic India", "country": "India", "lat": 25.3176, "lon": 82.9739, "era": "c. 1500 BCE", "key_work": "Rigveda hymns", "continent": "Asia"},
    {"tradition": "Chinese Classical Poetry", "region": "Yellow River", "country": "China", "lat": 34.2583, "lon": 108.9286, "era": "c. 1000 BCE", "key_work": "Shijing (Book of Songs)", "continent": "Asia"},
    {"tradition": "Greek Lyric Poetry", "region": "Lesbos / Athens", "country": "Greece", "lat": 39.1037, "lon": 26.5483, "era": "c. 600 BCE", "key_work": "Sappho's fragments", "continent": "Europe"},
    {"tradition": "Latin Poetry", "region": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "era": "c. 240 BCE", "key_work": "Virgil's Aeneid", "continent": "Europe"},
    {"tradition": "Arabic Qasida", "region": "Arabian Peninsula", "country": "Saudi Arabia", "lat": 24.7136, "lon": 46.6753, "era": "c. 500 CE", "key_work": "Mu'allaqat (Hanging Poems)", "continent": "Middle East"},
    {"tradition": "Persian Ghazal", "region": "Greater Iran", "country": "Iran", "lat": 32.6546, "lon": 51.6680, "era": "c. 900 CE", "key_work": "Rumi, Hafez ghazals", "continent": "Middle East"},
    {"tradition": "Japanese Haiku", "region": "Kyoto / Edo", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "era": "c. 1600s", "key_work": "Matsuo Basho's haiku", "continent": "Asia"},
    {"tradition": "Troubadour Lyric", "region": "Occitania / Provence", "country": "France", "lat": 43.6047, "lon": 1.4442, "era": "c. 1100 CE", "key_work": "William IX of Aquitaine poems", "continent": "Europe"},
    {"tradition": "Italian Sonnet", "region": "Sicily / Tuscany", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "era": "c. 1230 CE", "key_work": "Petrarch's Canzoniere", "continent": "Europe"},
    {"tradition": "Old English Poetry", "region": "Wessex / Northumbria", "country": "UK", "lat": 51.0632, "lon": -1.3080, "era": "c. 700 CE", "key_work": "Beowulf", "continent": "Europe"},
    {"tradition": "Norse Eddaic Poetry", "region": "Iceland / Scandinavia", "country": "Iceland", "lat": 64.1466, "lon": -21.9426, "era": "c. 800 CE", "key_work": "Poetic Edda", "continent": "Europe"},
    {"tradition": "Hebrew Poetry", "region": "Jerusalem / Judea", "country": "Israel", "lat": 31.7683, "lon": 35.2137, "era": "c. 1000 BCE", "key_work": "Psalms, Song of Solomon", "continent": "Middle East"},
    {"tradition": "Tamil Sangam Poetry", "region": "Madurai", "country": "India", "lat": 9.9252, "lon": 78.1198, "era": "c. 300 BCE", "key_work": "Sangam anthologies", "continent": "Asia"},
    {"tradition": "Korean Sijo", "region": "Goryeo / Joseon", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "era": "c. 1300 CE", "key_work": "Hwang Jini's sijo", "continent": "Asia"},
    {"tradition": "Swahili Poetry", "region": "East African Coast", "country": "Tanzania", "lat": -6.1659, "lon": 39.2026, "era": "c. 1600s", "key_work": "Utendi wa Tambuka", "continent": "Africa"},
    {"tradition": "Nahuatl Flower Songs", "region": "Tenochtitlan", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "era": "c. 1400s", "key_work": "Nezahualcoyotl's poems", "continent": "North America"},
    {"tradition": "Griot Oral Poetry", "region": "West Africa (Mali)", "country": "Mali", "lat": 12.6392, "lon": -8.0029, "era": "c. 1200 CE", "key_work": "Epic of Sundiata", "continent": "Africa"},
    {"tradition": "Russian Verse", "region": "St. Petersburg / Moscow", "country": "Russia", "lat": 59.9343, "lon": 30.3351, "era": "c. 1800s", "key_work": "Pushkin's Eugene Onegin", "continent": "Europe"},
    {"tradition": "Urdu Ghazal", "region": "Delhi / Lucknow", "country": "India", "lat": 28.6139, "lon": 77.2090, "era": "c. 1700s", "key_work": "Mirza Ghalib's ghazals", "continent": "Asia"},
    {"tradition": "German Romanticism", "region": "Heidelberg / Jena", "country": "Germany", "lat": 49.3988, "lon": 8.6724, "era": "c. 1790s", "key_work": "Holderlin, Novalis poems", "continent": "Europe"},
    {"tradition": "Modernist Poetry", "region": "London / Paris", "country": "UK/France", "lat": 51.5074, "lon": -0.1278, "era": "c. 1910s", "key_work": "T.S. Eliot's The Waste Land", "continent": "Europe"},
    {"tradition": "Beat Poetry", "region": "San Francisco / New York", "country": "USA", "lat": 37.7975, "lon": -122.4064, "era": "c. 1950s", "key_work": "Ginsberg's Howl", "continent": "North America"},
    {"tradition": "Negritude Poetry", "region": "Paris / Martinique", "country": "France/Senegal", "lat": 14.6928, "lon": -17.4467, "era": "c. 1930s", "key_work": "Cesaire, Senghor poems", "continent": "Africa"},
    {"tradition": "Chilean Anti-poetry", "region": "Santiago", "country": "Chile", "lat": -33.4489, "lon": -70.6693, "era": "c. 1950s", "key_work": "Nicanor Parra's antipoems", "continent": "South America"},
]

# ═══════════════════════════════════════════════════════════════
# 9. COMIC & MANGA CAPITALS (~25)
# ═══════════════════════════════════════════════════════════════

COMIC_MANGA_CAPITALS = [
    {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "tradition": "Manga", "note": "Global manga capital; Shueisha, Kodansha, Shogakukan HQs", "continent": "Asia"},
    {"city": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "tradition": "Manga", "note": "International Manga Museum, Osamu Tezuka connections", "continent": "Asia"},
    {"city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "tradition": "Manga", "note": "Den-Den Town otaku district", "continent": "Asia"},
    {"city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "tradition": "Manhwa/Webtoon", "note": "Webtoon revolution origin; Naver, Kakao HQs", "continent": "Asia"},
    {"city": "Brussels", "country": "Belgium", "lat": 50.8503, "lon": 4.3517, "tradition": "Bande dessinee", "note": "Comic strip capital; Tintin, Smurfs origin; Comic Strip Route", "continent": "Europe"},
    {"city": "Angouleme", "country": "France", "lat": 45.6500, "lon": 0.1600, "tradition": "Bande dessinee", "note": "Festival International de la BD, comic murals city", "continent": "Europe"},
    {"city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "tradition": "Comics", "note": "Marvel and DC birthplace; comic book capital", "continent": "North America"},
    {"city": "Detroit", "country": "USA", "lat": 42.3314, "lon": -83.0458, "tradition": "Comics", "note": "Underground comix movement", "continent": "North America"},
    {"city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194, "tradition": "Underground Comix", "note": "R. Crumb, underground comix scene", "continent": "North America"},
    {"city": "Lucca", "country": "Italy", "lat": 43.8429, "lon": 10.5027, "tradition": "Fumetti", "note": "Lucca Comics & Games, Europe's largest comic convention", "continent": "Europe"},
    {"city": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "tradition": "Comics", "note": "Ficomic Barcelona, vibrant comic scene", "continent": "Europe"},
    {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "tradition": "Historietas", "note": "Mafalda's home; Quino, Breccia heritage", "continent": "South America"},
    {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "tradition": "Historietas", "note": "Golden age of Mexican comics; El Santo, Memin Pinguin", "continent": "North America"},
    {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "tradition": "Comics", "note": "Amar Chitra Katha, Tinkle comics origin", "continent": "Asia"},
    {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "tradition": "Comics", "note": "2000 AD, Beano, Alan Moore heritage", "continent": "Europe"},
    {"city": "Charleroi", "country": "Belgium", "lat": 50.4108, "lon": 4.4446, "tradition": "Bande dessinee", "note": "Marcinelle school; Spirou, Lucky Luke", "continent": "Europe"},
    {"city": "Saitama", "country": "Japan", "lat": 35.8617, "lon": 139.6455, "tradition": "Manga", "note": "Home to many manga artists; Tokiwa-so connections", "continent": "Asia"},
    {"city": "Portland", "country": "USA", "lat": 45.5152, "lon": -122.6784, "tradition": "Indie Comics", "note": "Dark Horse Comics HQ, indie comics hub", "continent": "North America"},
    {"city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "tradition": "Manhua", "note": "Taiwanese manga scene and conventions", "continent": "Asia"},
    {"city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579, "tradition": "Manhua/Donghua", "note": "Chinese webcomic and animation hub", "continent": "Asia"},
    {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "tradition": "Bande dessinee", "note": "Moebius, BD publishers, Cite de la BD influence", "continent": "Europe"},
    {"city": "Zagreb", "country": "Croatia", "lat": 45.8150, "lon": 15.9819, "tradition": "Comics", "note": "Zagreb school of animation and comics", "continent": "Europe"},
    {"city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "tradition": "Comics", "note": "Helsinki Comics Festival, Nordic comics hub", "continent": "Europe"},
    {"city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "tradition": "Comics", "note": "Comic Republic, African superhero comics", "continent": "Africa"},
    {"city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "tradition": "Comics", "note": "Monica's Gang; CCXP world's largest comic con", "continent": "South America"},
]

# ═══════════════════════════════════════════════════════════════
# 10. BOOK FESTIVALS (~30)
# ═══════════════════════════════════════════════════════════════

BOOK_FESTIVALS = [
    {"name": "Hay Festival", "city": "Hay-on-Wye", "country": "UK", "lat": 52.0748, "lon": -3.1244, "month": "May-June", "founded": 1988, "note": "Bill Clinton called it 'Woodstock of the mind'", "continent": "Europe"},
    {"name": "Edinburgh International Book Festival", "city": "Edinburgh", "country": "UK", "lat": 55.9533, "lon": -3.1883, "month": "August", "founded": 1983, "note": "World's largest public book festival", "continent": "Europe"},
    {"name": "Frankfurt Book Fair", "city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821, "month": "October", "founded": 1454, "note": "World's largest trade fair for books", "continent": "Europe"},
    {"name": "London Book Fair", "city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "month": "March", "founded": 1971, "note": "Major global publishing rights fair", "continent": "Europe"},
    {"name": "Bologna Children's Book Fair", "city": "Bologna", "country": "Italy", "lat": 44.4949, "lon": 11.3426, "month": "March-April", "founded": 1964, "note": "World's largest children's publishing event", "continent": "Europe"},
    {"name": "Salon du Livre de Paris", "city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "month": "March", "founded": 1981, "note": "France's premier book fair", "continent": "Europe"},
    {"name": "Jaipur Literature Festival", "city": "Jaipur", "country": "India", "lat": 26.9124, "lon": 75.7873, "month": "January", "founded": 2006, "note": "World's largest free literary festival", "continent": "Asia"},
    {"name": "Brooklyn Book Festival", "city": "New York", "country": "USA", "lat": 40.6892, "lon": -73.9857, "month": "September", "founded": 2006, "note": "NYC's largest free literary event", "continent": "North America"},
    {"name": "Guadalajara International Book Fair", "city": "Guadalajara", "country": "Mexico", "lat": 20.6597, "lon": -103.3496, "month": "November-December", "founded": 1987, "note": "Largest book fair in Latin America", "continent": "North America"},
    {"name": "Buenos Aires International Book Fair", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "month": "April-May", "founded": 1975, "note": "One million+ visitors annually", "continent": "South America"},
    {"name": "Gothenburg Book Fair", "city": "Gothenburg", "country": "Sweden", "lat": 57.7089, "lon": 11.9746, "month": "September", "founded": 1985, "note": "Scandinavia's largest book fair", "continent": "Europe"},
    {"name": "International Kolkata Book Fair", "city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "month": "January-February", "founded": 1976, "note": "World's largest non-trade book fair", "continent": "Asia"},
    {"name": "Sharjah International Book Fair", "city": "Sharjah", "country": "UAE", "lat": 25.3463, "lon": 55.4209, "month": "November", "founded": 1982, "note": "Largest book fair in the Arab world", "continent": "Middle East"},
    {"name": "Salone del Libro di Torino", "city": "Turin", "country": "Italy", "lat": 45.0703, "lon": 7.6869, "month": "May", "founded": 1988, "note": "Italy's largest book fair", "continent": "Europe"},
    {"name": "BookExpo America", "city": "New York", "country": "USA", "lat": 40.7527, "lon": -73.9772, "month": "May-June", "founded": 1947, "note": "Major North American publishing event", "continent": "North America"},
    {"name": "Seoul International Book Fair", "city": "Seoul", "country": "South Korea", "lat": 37.5126, "lon": 127.0596, "month": "June", "founded": 1954, "note": "Major East Asian publishing event", "continent": "Asia"},
    {"name": "Beijing International Book Fair", "city": "Beijing", "country": "China", "lat": 39.9925, "lon": 116.4730, "month": "August", "founded": 1986, "note": "China's largest international book fair", "continent": "Asia"},
    {"name": "Cape Town Book Fair", "city": "Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "month": "September", "founded": 2006, "note": "Africa's largest book fair", "continent": "Africa"},
    {"name": "Cheltenham Literature Festival", "city": "Cheltenham", "country": "UK", "lat": 51.8993, "lon": -2.0783, "month": "October", "founded": 1949, "note": "World's oldest literature festival", "continent": "Europe"},
    {"name": "Adelaide Writers' Week", "city": "Adelaide", "country": "Australia", "lat": -34.9285, "lon": 138.6007, "month": "March", "founded": 1960, "note": "Australia's premier literary festival", "continent": "Oceania"},
    {"name": "St Malo Etonnants Voyageurs", "city": "Saint-Malo", "country": "France", "lat": 48.6493, "lon": -2.0007, "month": "June", "founded": 1990, "note": "Travel and adventure literature festival", "continent": "Europe"},
    {"name": "Istanbul Tanpinar Literature Festival", "city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "month": "April", "founded": 2014, "note": "Turkey's international literary gathering", "continent": "Europe"},
    {"name": "Cairo International Book Fair", "city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "month": "January-February", "founded": 1969, "note": "Oldest and largest book fair in Arab world", "continent": "Africa"},
    {"name": "Taipei International Book Exhibition", "city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "month": "February", "founded": 1987, "note": "Major East Asian book exhibition", "continent": "Asia"},
    {"name": "PEN World Voices Festival", "city": "New York", "country": "USA", "lat": 40.7484, "lon": -73.9967, "month": "May", "founded": 2005, "note": "International literary festival for free expression", "continent": "North America"},
    {"name": "Lagos Book & Art Festival", "city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "month": "November", "founded": 2014, "note": "Growing African literary event", "continent": "Africa"},
    {"name": "Festival Internacional de Poesia de Medellin", "city": "Medellin", "country": "Colombia", "lat": 6.2476, "lon": -75.5658, "month": "June-July", "founded": 1991, "note": "World's largest poetry festival", "continent": "South America"},
    {"name": "Singapore Writers Festival", "city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "month": "November", "founded": 1986, "note": "Multilingual literary festival", "continent": "Asia"},
    {"name": "Festivaletteratura Mantova", "city": "Mantua", "country": "Italy", "lat": 45.1564, "lon": 10.7914, "month": "September", "founded": 1997, "note": "Italy's beloved literary festival", "continent": "Europe"},
    {"name": "Melbourne Writers Festival", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "month": "August", "founded": 1986, "note": "Leading Australian literary festival", "continent": "Oceania"},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _get_dataset(mode: str):
    """Return (data_list, columns_for_display) for the chosen mode."""
    if mode == "Nobel Literature Laureates":
        return NOBEL_LAUREATES, ["name", "year", "country", "city", "continent"]
    elif mode == "Literary Cities":
        return LITERARY_CITIES, ["city", "country", "designation", "note", "continent"]
    elif mode == "Famous Authors' Homes":
        return AUTHORS_HOMES, ["author", "birth_year", "city", "country", "genre", "continent"]
    elif mode == "Fictional Places":
        return FICTIONAL_PLACES, ["fictional_name", "book", "author", "real_place", "continent"]
    elif mode == "World's Greatest Libraries":
        return GREAT_LIBRARIES, ["name", "city", "country", "founded", "collection", "continent"]
    elif mode == "Publishing Houses":
        return PUBLISHING_HOUSES, ["name", "city", "country", "founded", "note", "continent"]
    elif mode == "Bookshop Capitals":
        return BOOKSHOP_CAPITALS, ["city", "country", "famous_shop", "note", "continent"]
    elif mode == "Poetry Origins":
        return POETRY_ORIGINS, ["tradition", "region", "country", "era", "key_work", "continent"]
    elif mode == "Comic & Manga Capitals":
        return COMIC_MANGA_CAPITALS, ["city", "country", "tradition", "note", "continent"]
    elif mode == "Book Festivals":
        return BOOK_FESTIVALS, ["name", "city", "country", "month", "founded", "note", "continent"]
    return [], []


def _label_field(mode: str) -> str:
    """Return the primary label field for markers."""
    if mode == "Nobel Literature Laureates":
        return "name"
    elif mode == "Literary Cities":
        return "city"
    elif mode == "Famous Authors' Homes":
        return "author"
    elif mode == "Fictional Places":
        return "fictional_name"
    elif mode == "World's Greatest Libraries":
        return "name"
    elif mode == "Publishing Houses":
        return "name"
    elif mode == "Bookshop Capitals":
        return "city"
    elif mode == "Poetry Origins":
        return "tradition"
    elif mode == "Comic & Manga Capitals":
        return "city"
    elif mode == "Book Festivals":
        return "name"
    return "name"


def _popup_html(item: dict, mode: str) -> str:
    """Build an HTML popup string for a folium marker, with escaped content."""
    lines = []
    if mode == "Nobel Literature Laureates":
        lines.append(f"<strong>{escape(item.get('name', ''))}</strong>")
        lines.append(f"Nobel Prize: {escape(str(item.get('year', '')))}")
        lines.append(f"{escape(item.get('city', ''))}, {escape(item.get('country', ''))}")
    elif mode == "Literary Cities":
        lines.append(f"<strong>{escape(item.get('city', ''))}</strong>")
        lines.append(f"{escape(item.get('designation', ''))}")
        lines.append(f"{escape(item.get('note', ''))}")
    elif mode == "Famous Authors' Homes":
        lines.append(f"<strong>{escape(item.get('author', ''))}</strong>")
        lines.append(f"Born: {escape(str(item.get('birth_year', '')))}")
        lines.append(f"{escape(item.get('city', ''))}, {escape(item.get('country', ''))}")
        lines.append(f"Genre: {escape(item.get('genre', ''))}")
    elif mode == "Fictional Places":
        lines.append(f"<strong>{escape(item.get('fictional_name', ''))}</strong>")
        lines.append(f"Book: {escape(item.get('book', ''))}")
        lines.append(f"Author: {escape(item.get('author', ''))}")
        lines.append(f"Real: {escape(item.get('real_place', ''))}")
    elif mode == "World's Greatest Libraries":
        lines.append(f"<strong>{escape(item.get('name', ''))}</strong>")
        lines.append(f"{escape(item.get('city', ''))}, {escape(item.get('country', ''))}")
        lines.append(f"Founded: {escape(str(item.get('founded', '')))}")
        lines.append(f"{escape(item.get('collection', ''))}")
    elif mode == "Publishing Houses":
        lines.append(f"<strong>{escape(item.get('name', ''))}</strong>")
        lines.append(f"{escape(item.get('city', ''))}, {escape(item.get('country', ''))}")
        lines.append(f"Founded: {escape(str(item.get('founded', '')))}")
        lines.append(f"{escape(item.get('note', ''))}")
    elif mode == "Bookshop Capitals":
        lines.append(f"<strong>{escape(item.get('city', ''))}</strong>")
        lines.append(f"Famous: {escape(item.get('famous_shop', ''))}")
        lines.append(f"{escape(item.get('note', ''))}")
    elif mode == "Poetry Origins":
        lines.append(f"<strong>{escape(item.get('tradition', ''))}</strong>")
        lines.append(f"Region: {escape(item.get('region', ''))}")
        lines.append(f"Era: {escape(item.get('era', ''))}")
        lines.append(f"Key work: {escape(item.get('key_work', ''))}")
    elif mode == "Comic & Manga Capitals":
        lines.append(f"<strong>{escape(item.get('city', ''))}</strong>")
        lines.append(f"Tradition: {escape(item.get('tradition', ''))}")
        lines.append(f"{escape(item.get('note', ''))}")
    elif mode == "Book Festivals":
        lines.append(f"<strong>{escape(item.get('name', ''))}</strong>")
        lines.append(f"{escape(item.get('city', ''))}, {escape(item.get('country', ''))}")
        lines.append(f"When: {escape(item.get('month', ''))}")
        lines.append(f"Since: {escape(str(item.get('founded', '')))}")
        lines.append(f"{escape(item.get('note', ''))}")

    body = "<br/>".join(lines)
    return f'<div style="min-width:180px;max-width:250px;font-size:0.85rem;">{body}</div>'


@st.cache_data(ttl=3600)
def _build_dataframe(mode: str, continent_filter: str) -> pd.DataFrame:
    """Build a filtered DataFrame for the chosen mode and continent."""
    data, cols = _get_dataset(mode)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if continent_filter and continent_filter != "All":
        df = df[df["continent"] == continent_filter]
    return df


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_literature_maps_tab():
    """Main render function for the Literature & Books Maps tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Literature & Books Maps</h4>
        <p>Explore the geography of world literature: Nobel laureates, literary cities, famous authors, fictional places, great libraries, publishers, bookshops, poetry traditions, comics, and book festivals.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode & Controls
    # ══════════════════════════════════════════
    st.markdown("#### Map Mode")

    mode = st.selectbox(
        "Choose a literary map",
        MODE_LIST,
        key="lit_mode",
        help="Select one of 10 curated literary geography datasets",
    )

    color = MODE_COLORS.get(mode, "#8b5cf6")

    # Continent filter
    data_list, display_cols = _get_dataset(mode)
    all_continents = sorted(set(item.get("continent", "Unknown") for item in data_list))
    continent_options = ["All"] + all_continents

    col1, col2 = st.columns([1, 1])
    with col1:
        continent_filter = st.selectbox(
            "Filter by continent",
            continent_options,
            key="lit_continent",
        )
    with col2:
        marker_size = st.slider("Marker size", 4, 16, 8, key="lit_marker_size")

    # Build button
    if st.button("Load Map", key="lit_load", type="primary"):
        st.session_state.lit_params = {
            "mode": mode,
            "continent": continent_filter,
            "marker_size": marker_size,
        }

    if "lit_params" not in st.session_state:
        st.info("Choose a literary map mode and click **Load Map** to explore the world of books and literature.")
        return

    params = st.session_state.lit_params
    cur_mode = params["mode"]
    cur_continent = params["continent"]
    cur_marker_size = params["marker_size"]
    cur_color = MODE_COLORS.get(cur_mode, "#8b5cf6")

    # ══════════════════════════════════════════
    # SECTION 2: Build Data
    # ══════════════════════════════════════════
    df = _build_dataframe(cur_mode, cur_continent)

    if df.empty:
        st.warning("No entries match the selected filter. Try a different continent or mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Statistics
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {escape(cur_mode)} Overview")

    # Continent breakdown
    continent_counts = df["continent"].value_counts().to_dict()
    n_cols = min(len(continent_counts) + 1, 6)
    stat_cols = st.columns(n_cols)
    stat_cols[0].metric("Total Entries", len(df))
    for i, (cont, cnt) in enumerate(sorted(continent_counts.items(), key=lambda x: -x[1])):
        if i + 1 < n_cols:
            stat_cols[i + 1].metric(cont, cnt)

    # Extra per-mode stats
    if cur_mode == "Nobel Literature Laureates" and "year" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Earliest Nobel", int(df["year"].min()))
        c2.metric("Latest Nobel", int(df["year"].max()))
        c3.metric("Countries", df["country"].nunique())
    elif cur_mode == "Famous Authors' Homes" and "birth_year" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Earliest Born", int(df["birth_year"].min()))
        c2.metric("Latest Born", int(df["birth_year"].max()))
        c3.metric("Genres", df["genre"].nunique())
    elif cur_mode == "World's Greatest Libraries" and "founded" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Oldest Founded", int(df["founded"].min()))
        c2.metric("Newest Founded", int(df["founded"].max()))
        c3.metric("Countries", df["country"].nunique())
    elif cur_mode == "Publishing Houses" and "founded" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Oldest", int(df["founded"].min()))
        c2.metric("Newest", int(df["founded"].max()))
        c3.metric("Countries", df["country"].nunique())
    elif cur_mode == "Book Festivals" and "founded" in df.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Oldest Festival", int(df["founded"].min()))
        c2.metric("Newest Festival", int(df["founded"].max()))
        c3.metric("Countries", df["country"].nunique())
    elif cur_mode in ("Literary Cities", "Bookshop Capitals", "Comic & Manga Capitals"):
        c1, c2 = st.columns(2)
        c1.metric("Countries", df["country"].nunique())
        c2.metric("Continents", df["continent"].nunique())
    elif cur_mode == "Poetry Origins" and "era" in df.columns:
        c1, c2 = st.columns(2)
        c1.metric("Traditions", len(df))
        c2.metric("Countries", df["country"].nunique())
    elif cur_mode == "Fictional Places":
        c1, c2 = st.columns(2)
        c1.metric("Authors", df["author"].nunique())
        c2.metric("Countries/Regions", df["continent"].nunique())

    # ══════════════════════════════════════════
    # SECTION 4: Legend
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")

    # Continent color legend
    present_continents = df["continent"].unique().tolist()
    legend_items = " ".join([
        f'<span style="color:{CONTINENT_COLORS.get(c, cur_color)}; font-size:0.8rem;">&#9679; {escape(c)}</span>'
        for c in sorted(present_continents)
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 5: Folium Map
    # ══════════════════════════════════════════
    avg_lat = df["lat"].mean()
    avg_lon = df["lon"].mean()

    # Determine zoom
    lat_range = df["lat"].max() - df["lat"].min()
    lon_range = df["lon"].max() - df["lon"].min()
    span = max(lat_range, lon_range)
    if span > 100:
        zoom = 2
    elif span > 50:
        zoom = 3
    elif span > 20:
        zoom = 4
    elif span > 10:
        zoom = 5
    else:
        zoom = 6

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=zoom, tiles="CartoDB dark_matter")

    label_key = _label_field(cur_mode)

    for _, row in df.iterrows():
        item = row.to_dict()
        popup_content = _popup_html(item, cur_mode)
        continent = item.get("continent", "")
        marker_color = CONTINENT_COLORS.get(continent, cur_color)
        label = str(item.get(label_key, ""))

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=cur_marker_size,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.8,
            weight=1.5,
            popup=folium.Popup(popup_content, max_width=280),
            tooltip=escape(label),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    # ══════════════════════════════════════════
    # SECTION 6: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Data Table")

    # Only show display columns
    show_cols = [c for c in display_cols if c in df.columns]
    display_df = df[show_cols].reset_index(drop=True)
    display_df.index = display_df.index + 1

    st.dataframe(display_df, width="stretch")

    # ══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ══════════════════════════════════════════
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    st.download_button(
        label=f"Download {cur_mode} CSV",
        data=csv_bytes,
        file_name=f"literature_{cur_mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
        key="lit_csv_download",
    )

    # ══════════════════════════════════════════
    # SECTION 8: Matplotlib continent chart
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Distribution by Continent")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#111827")

        cont_series = df["continent"].value_counts().sort_values(ascending=True)
        bar_colors = [CONTINENT_COLORS.get(c, cur_color) for c in cont_series.index]

        cont_series.plot.barh(ax=ax, color=bar_colors, edgecolor="none")

        ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
        ax.set_ylabel("")
        ax.set_title(f"{cur_mode} by Continent", color="#e8ecf4", fontsize=12, pad=10)
        ax.tick_params(colors="#8b97b0", labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        st.info("Install matplotlib for continent distribution charts.")
