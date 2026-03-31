# -*- coding: utf-8 -*-
"""
Haunted Places & Ghost Maps module for TerraScout AI.
Explore haunted locations worldwide with curated data and interactive dark maps.
Covers famous haunted houses, castles, ghost towns, hotels, catacombs,
battlefields, poltergeist sites, witch trial locations, abandoned asylums,
and haunted prisons.
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


# ---------------------------------------------------------------------------
# Mode 1: Famous Haunted Houses
# ---------------------------------------------------------------------------
FAMOUS_HAUNTED_HOUSES = [
    {"name": "Winchester Mystery House", "lat": 37.3184, "lon": -121.9511,
     "country": "USA", "city": "San Jose, CA",
     "description": "Built by Sarah Winchester, widow of the rifle magnate. Construction continued 24/7 for 38 years to appease restless spirits. Features stairs to nowhere, doors opening to walls, and 161 rooms."},
    {"name": "Borley Rectory", "lat": 52.0764, "lon": 0.7381,
     "country": "England", "city": "Borley, Essex",
     "description": "Once called 'the most haunted house in England' by paranormal researcher Harry Price. Reports of phantom coaches, ghostly nuns, and mysterious writings on walls before it burned in 1939."},
    {"name": "Amityville Horror House", "lat": 40.6668, "lon": -73.4148,
     "country": "USA", "city": "Amityville, NY",
     "description": "Site of the 1974 DeFeo family murders. The Lutz family fled 28 days after moving in, reporting green slime, demonic voices, and swarms of flies in winter."},
    {"name": "Myrtles Plantation", "lat": 30.5921, "lon": -91.4518,
     "country": "USA", "city": "St. Francisville, LA",
     "description": "Built in 1796, said to be home to at least 12 ghosts including Chloe, a former slave whose spirit appears in a famous photograph wearing a green turban."},
    {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759,
     "country": "England", "city": "London",
     "description": "Nearly 1000 years of executions, torture, and imprisonment. Ghosts include Anne Boleyn carrying her severed head, the Princes in the Tower, and Lady Jane Grey."},
    {"name": "Monte Cristo Homestead", "lat": -34.7537, "lon": 148.6264,
     "country": "Australia", "city": "Junee, NSW",
     "description": "Australia's most haunted house. A stable boy burned to death, a maid fell from the balcony, a caretaker's son was chained in the carriage house for 40 years. Cold spots and apparitions persist."},
    {"name": "Rose Hall Great House", "lat": 18.5115, "lon": -77.8677,
     "country": "Jamaica", "city": "Montego Bay",
     "description": "Home of Annie Palmer, the 'White Witch of Rose Hall,' who reportedly murdered three husbands using voodoo and witchcraft. Her spirit is said to still roam the estate."},
    {"name": "Bhangarh Fort", "lat": 27.0926, "lon": 76.2834,
     "country": "India", "city": "Rajasthan",
     "description": "Cursed by a tantric priest, this 17th-century fort is officially closed after sunset by the Archaeological Survey of India. Visitors report shadows, screams, and a feeling of being watched."},
    {"name": "Ancient Ram Inn", "lat": 51.7635, "lon": -2.1680,
     "country": "England", "city": "Wotton-under-Edge",
     "description": "Built in 1145 on a pagan burial ground and ley line intersection. Reports include a spectral high priestess, incubus attacks, and the discovery of children's bones under the staircase."},
    {"name": "LaLaurie Mansion", "lat": 29.9617, "lon": -90.0631,
     "country": "USA", "city": "New Orleans, LA",
     "description": "Home of Madame Delphine LaLaurie, whose secret torture chamber was discovered in 1834 after a fire. Screams and moans are still heard from the former attic prison."},
    {"name": "Aokigahara House Ruins", "lat": 35.4735, "lon": 138.6221,
     "country": "Japan", "city": "Fujikawaguchiko",
     "description": "Scattered ruins in Japan's 'Suicide Forest' at the base of Mt. Fuji, associated with yurei (ghosts) in Japanese mythology. The forest's dense canopy blocks wind, creating eerie silence."},
    {"name": "Raynham Hall", "lat": 52.7963, "lon": 0.8350,
     "country": "England", "city": "Norfolk",
     "description": "Home of the famous 'Brown Lady' ghost, captured in a 1936 photograph considered one of the most credible ghost photos ever taken. The spectre is believed to be Lady Dorothy Walpole."},
    {"name": "Franklin Castle", "lat": 41.4847, "lon": -81.7108,
     "country": "USA", "city": "Cleveland, OH",
     "description": "Built in 1881 by Hannes Tiedemann, who lost four children, his mother, and wife within three years. Hidden rooms, secret passages, and the sounds of crying babies haunt the Victorian mansion."},
    {"name": "Changi Hospital", "lat": 1.3894, "lon": 103.9770,
     "country": "Singapore", "city": "Singapore",
     "description": "Abandoned military hospital used as a prison camp during WWII Japanese occupation. Night visitors report shadowy figures, screams of pain, and the sounds of marching soldiers."},
    {"name": "Casa Loma", "lat": 43.6780, "lon": -79.4094,
     "country": "Canada", "city": "Toronto",
     "description": "Gothic revival castle built in 1914. The ghost of Sir Henry Pellatt's wife is seen in the tower, and a spectral white lady drifts through the secret passages and underground tunnels."},
    {"name": "Whaley House", "lat": 32.7549, "lon": -117.1719,
     "country": "USA", "city": "San Diego, CA",
     "description": "Built on the site of a public gallowsfield. Yankee Jim Robinson, hanged there in 1852, still makes heavy footstep sounds. The US Commerce Department officially recognizes it as haunted."},
    {"name": "Leap Castle", "lat": 52.9647, "lon": -7.8081,
     "country": "Ireland", "city": "Coolderry, Offaly",
     "description": "Known for the 'Bloody Chapel' where a priest was murdered by his own brother during mass. An oubliette filled with skeletal remains was found, and a foul elemental creature stalks the halls."},
    {"name": "Palazzo Dario", "lat": 45.4299, "lon": 12.3325,
     "country": "Italy", "city": "Venice",
     "description": "A cursed 15th-century palazzo on the Grand Canal. Multiple owners have died violently or gone bankrupt, earning it the name 'the house that kills.' No one dares live there long."},
    {"name": "Belcourt Castle", "lat": 41.4628, "lon": -71.3015,
     "country": "USA", "city": "Newport, RI",
     "description": "A 60-room mansion where visitors have been physically pushed by unseen forces. Haunted suits of armor emit screams, and ghostly monks chant in the Gothic ballroom."},
    {"name": "Glamis Castle", "lat": 56.6158, "lon": -3.0050,
     "country": "Scotland", "city": "Angus",
     "description": "Childhood home of the Queen Mother, reputedly the most haunted castle in Scotland. A secret room holds the 'Monster of Glamis,' and the ghost of a tongueless woman roams the grounds."},
    {"name": "Chateau de Trecesson", "lat": 47.9559, "lon": -2.3091,
     "country": "France", "city": "Campeneac, Brittany",
     "description": "A bride was buried alive in her wedding dress in the grounds by unknown assailants. Her white ghost now walks near the moat at night, forever seeking her groom."},
]

# ---------------------------------------------------------------------------
# Mode 2: Haunted Castles of Europe
# ---------------------------------------------------------------------------
HAUNTED_CASTLES = [
    {"name": "Edinburgh Castle", "lat": 55.9486, "lon": -3.1999, "country": "Scotland", "city": "Edinburgh", "description": "A headless drummer, the ghost of a piper lost in tunnels, and spectral prisoners from the Napoleonic wars. A 2001 scientific investigation detected unexplained phenomena in multiple rooms."},
    {"name": "Chateau de Brissac", "lat": 47.3544, "lon": -0.4506, "country": "France", "city": "Brissac-Quince", "description": "The tallest castle in France, haunted by 'La Dame Verte' (the Green Lady), murdered by her husband in the 15th century after he caught her with a lover. Her moaning face has empty eye sockets."},
    {"name": "Houska Castle", "lat": 50.4889, "lon": 14.6322, "country": "Czech Republic", "city": "Blatce", "description": "Built over a bottomless pit believed to be a gateway to Hell. Constructed not to keep people out, but to seal something in. Half-animal demons were said to crawl from the hole."},
    {"name": "Bran Castle", "lat": 45.5152, "lon": 25.3672, "country": "Romania", "city": "Bran, Transylvania", "description": "Associated with Vlad the Impaler and the Dracula legend. Perched on a 200-foot cliff, secret passages connect rooms. Visitors report cold spots and the feeling of being followed through dark corridors."},
    {"name": "Moosham Castle", "lat": 47.2311, "lon": 13.7044, "country": "Austria", "city": "Unternberg", "description": "Known as the 'Witches Castle.' Hundreds of women were tortured and executed here during witch trials. Deer and cattle were found mutilated in the courtyard, blamed on werewolf spirits."},
    {"name": "Predjama Castle", "lat": 45.8156, "lon": 14.1269, "country": "Slovenia", "city": "Predjama", "description": "Built into the mouth of a cave, home of knight-robber Erasmus. Besieged for a year, he was betrayed and killed. His ghost haunts the cave passages behind the castle walls."},
    {"name": "Chillingham Castle", "lat": 55.5233, "lon": -1.9136, "country": "England", "city": "Northumberland", "description": "The most haunted castle in England. The Blue Boy appears as a flash of blue light, and the torturer John Sage still drags chains through the dungeon where he killed thousands of Scots."},
    {"name": "Castello di Montebello", "lat": 43.9550, "lon": 12.4067, "country": "Italy", "city": "Poggio Torriana", "description": "Home of Azzurrina, an albino girl who vanished during a storm in 1375. Every five years on the solstice, her crying is heard in the ice storage room where she disappeared."},
    {"name": "Dragsholm Castle", "lat": 55.7428, "lon": 11.5081, "country": "Denmark", "city": "Horreved", "description": "Haunted by three ghosts: the Grey Lady (a servant), the White Lady (a nobleman's daughter walled up alive), and the Earl of Bothwell, whose ghost rides through the courtyard."},
    {"name": "Castle of Good Hope", "lat": -33.9265, "lon": 18.4271, "country": "South Africa", "city": "Cape Town", "description": "The oldest colonial building in South Africa. The ghost of Governor van Noodt, who died of a stroke right after sentencing soldiers to death, walks the battlements."},
    {"name": "Warwick Castle", "lat": 52.2793, "lon": -1.5848, "country": "England", "city": "Warwick", "description": "Sir Fulke Greville was murdered by his manservant in 1628 and his ghost haunts the tower where he died. Visitors report being grabbed by invisible hands in the dungeons."},
    {"name": "Frankenstein Castle", "lat": 49.8139, "lon": 8.6497, "country": "Germany", "city": "Darmstadt", "description": "May have inspired Mary Shelley's novel. Alchemist Johann Konrad Dippel allegedly experimented on corpses here. On Halloween, a phantom is seen near the old tower."},
    {"name": "Wolfsegg Castle", "lat": 49.0769, "lon": 11.9956, "country": "Germany", "city": "Wolfsegg", "description": "The 'Woman in White' has been seen since the 14th century, believed to be a murdered lady of the castle. A cave beneath contains bones from the Ice Age and unexplained cold drafts."},
    {"name": "Zvikov Castle", "lat": 49.4408, "lon": 14.1953, "country": "Czech Republic", "city": "Zvikov", "description": "The Zvikov imp haunts the castle, making electronic devices malfunction, animals refuse to enter certain rooms, and fires ignite spontaneously. Documented disturbances go back centuries."},
    {"name": "Eltz Castle", "lat": 50.2053, "lon": 7.3367, "country": "Germany", "city": "Wierschem", "description": "Owned by one family for 850 years. Countess Agnes, who died defending the castle in the 15th century in full armor, walks the halls. Her suit of armor is displayed in the treasury."},
    {"name": "Berry Pomeroy Castle", "lat": 50.4509, "lon": -3.6261, "country": "England", "city": "Devon", "description": "Two ghosts haunt these ruins: the White Lady (Margaret Pomeroy, starved to death by her jealous sister) and the Blue Lady, who lures visitors to the dangerous ruined tower."},
    {"name": "Akershus Fortress", "lat": 59.9075, "lon": 10.7356, "country": "Norway", "city": "Oslo", "description": "Medieval fortress and WWII execution site. A demon dog guards the gate, and the ghost of a woman with no face appears in the corridors."},
    {"name": "Roogenwalde Castle", "lat": 54.0686, "lon": 16.0336, "country": "Poland", "city": "Darlowo", "description": "Duke Eric I of Pomerania, forced to abdicate, lived and died here. His restless ghost rattles chains and moves furniture, unable to find peace after losing his kingdom."},
    {"name": "Boldt Castle", "lat": 44.3422, "lon": -75.9225, "country": "USA", "city": "Heart Island, NY", "description": "George Boldt built this castle for his beloved wife, but she died before it was completed. He never returned. Workers report seeing the ghost of a woman in white gazing from the tower."},
    {"name": "Larnach Castle", "lat": -45.8639, "lon": 170.6225, "country": "New Zealand", "city": "Dunedin", "description": "William Larnach shot himself in Parliament after his third wife had an affair with his son. His first wife haunts the ballroom, and weeping is heard in the tower at midnight."},
]

# ---------------------------------------------------------------------------
# Mode 3: Ghost Towns Worldwide
# ---------------------------------------------------------------------------
GHOST_TOWNS = [
    {"name": "Pripyat", "lat": 51.4045, "lon": 30.0542, "country": "Ukraine", "city": "Chernobyl Exclusion Zone", "description": "Abandoned overnight after the 1986 Chernobyl nuclear disaster. 49,000 residents fled leaving behind ferris wheels, schools, and swimming pools now reclaimed by nature and radiation."},
    {"name": "Craco", "lat": 40.3825, "lon": 16.4403, "country": "Italy", "city": "Basilicata", "description": "Perched on a cliff since the 8th century, abandoned due to recurring landslides, earthquakes, and floods. A haunting medieval skyline used as a filming location for multiple movies."},
    {"name": "Kolmanskop", "lat": -26.7044, "lon": 15.2286, "country": "Namibia", "city": "Luderitz", "description": "A diamond mining town swallowed by the Namib Desert. Sand dunes pour through doors and windows of once-lavish German colonial houses with a ballroom, bowling alley, and hospital."},
    {"name": "Bodie", "lat": 38.2133, "lon": -119.0147, "country": "USA", "city": "Mono County, CA", "description": "Gold rush ghost town frozen in a state of 'arrested decay.' Visitors who take artifacts report the Curse of Bodie: terrible luck until the stolen item is returned by mail."},
    {"name": "Hashima Island (Gunkanjima)", "lat": 32.6275, "lon": 129.7386, "country": "Japan", "city": "Nagasaki", "description": "A concrete battleship island, once the most densely populated place on Earth. Abandoned in 1974, its crumbling apartment blocks inspired the villain's lair in a Bond film."},
    {"name": "Centralia", "lat": 40.8042, "lon": -76.3403, "country": "USA", "city": "Pennsylvania", "description": "An underground coal fire has burned since 1962, venting toxic smoke through cracks in abandoned roads. The few remaining residents live atop an inferno that may burn for 250 more years."},
    {"name": "Oradour-sur-Glane", "lat": 45.9333, "lon": 1.0333, "country": "France", "city": "Haute-Vienne", "description": "Preserved exactly as the Nazis left it after the 1944 massacre of 642 villagers. Burnt-out cars, shattered buildings, and the church where women and children were killed remain untouched."},
    {"name": "Varosha", "lat": 35.1092, "lon": 33.9586, "country": "Cyprus", "city": "Famagusta", "description": "Once a glamorous beach resort frequented by movie stars, sealed off since the 1974 Turkish invasion. Hotels and high-rises stand empty behind barbed wire, frozen in the 1970s."},
    {"name": "Kayakoy", "lat": 36.5842, "lon": 29.0908, "country": "Turkey", "city": "Fethiye", "description": "3,500 stone houses abandoned after the 1923 Greek-Turkish population exchange. An entire hillside of roofless churches and homes stands as a ghost village and museum of peace."},
    {"name": "Fordlandia", "lat": -3.8333, "lon": -55.5000, "country": "Brazil", "city": "Para", "description": "Henry Ford's failed utopian rubber plantation in the Amazon. American-style houses, a hospital, and a golf course rot in the jungle after tropical diseases and worker revolts doomed it."},
    {"name": "Wittenoom", "lat": -22.2372, "lon": 118.3381, "country": "Australia", "city": "Western Australia", "description": "Australia's most contaminated town, abandoned due to deadly blue asbestos dust. Over 2,000 former residents have died of mesothelioma. The government has erased it from maps."},
    {"name": "Kadykchan", "lat": 63.0833, "lon": 135.5833, "country": "Russia", "city": "Magadan Oblast", "description": "A Soviet coal mining town in the frozen wilderness, abandoned after a mine explosion and the collapse of the USSR. Buildings full of Soviet-era belongings sit in permafrost silence."},
    {"name": "Agdam", "lat": 39.9894, "lon": 46.9303, "country": "Azerbaijan", "city": "Agdam District", "description": "Once home to 40,000 people, systematically destroyed during the Nagorno-Karabakh conflict. Known as the 'Hiroshima of the Caucasus,' only the mosque minaret still stands among ruins."},
    {"name": "Imber", "lat": 51.2394, "lon": -2.0531, "country": "England", "city": "Salisbury Plain", "description": "Residents were evicted in 1943 so the military could use the village for training. They were never allowed to return. The church is opened once a year for a memorial service."},
    {"name": "Thurmond", "lat": 38.0762, "lon": -80.8551, "country": "USA", "city": "West Virginia", "description": "Once a booming railroad town with a notorious row of saloons. Now has a population of 5. The beautiful Amtrak station still operates, serving a town that barely exists."},
    {"name": "Belchite", "lat": 41.3033, "lon": -0.7461, "country": "Spain", "city": "Aragon", "description": "Destroyed in a brutal 1937 Spanish Civil War battle. Franco ordered the ruins preserved as a propaganda monument. Bullet-scarred churches and collapsed buildings remain exactly as they fell."},
    {"name": "Pyramiden", "lat": 78.6553, "lon": 16.3278, "country": "Norway", "city": "Svalbard", "description": "A Soviet coal mining settlement in the Arctic, abandoned in 1998. The northernmost Lenin bust watches over empty apartment blocks. Polar bears now outnumber the zero human residents."},
    {"name": "Garnet", "lat": 46.7850, "lon": -113.3464, "country": "USA", "city": "Montana", "description": "Montana's best-preserved gold mining ghost town. In winter, caretakers report music and voices from the empty hotel, and shadows moving in buildings where no one has lived for a century."},
    {"name": "Ani", "lat": 40.5067, "lon": 43.5728, "country": "Turkey", "city": "Kars Province", "description": "Medieval Armenian capital with a population once exceeding 100,000. Abandoned after Mongol and earthquake devastation. Cathedral ruins and city walls stand on a dramatic gorge."},
    {"name": "Canfranc Station", "lat": 42.7517, "lon": -0.5194, "country": "Spain", "city": "Huesca, Aragon", "description": "A colossal 240m-long railway station in the Pyrenees, once used to smuggle Nazi gold. Closed after a train derailment in 1970, its 365 windows stare blankly across the valley."},
]

# ---------------------------------------------------------------------------
# Mode 4: Haunted Hotels & Inns
# ---------------------------------------------------------------------------
HAUNTED_HOTELS = [
    {"name": "The Stanley Hotel", "lat": 40.3831, "lon": -105.5194, "country": "USA", "city": "Estes Park, CO", "description": "Inspired Stephen King's 'The Shining.' Room 217 is most haunted: the ghost of housekeeper Elizabeth Wilson tucks guests into bed. Piano music plays by itself in the ballroom."},
    {"name": "Hotel Cecil (Stay on Main)", "lat": 34.0444, "lon": -118.2509, "country": "USA", "city": "Los Angeles, CA", "description": "Notorious for serial killer residents (Richard Ramirez, Jack Unterweger) and the mysterious death of Elisa Lam in 2013, found in a rooftop water tank."},
    {"name": "The Langham Hotel", "lat": 51.5170, "lon": -0.1443, "country": "England", "city": "London", "description": "Room 333 is haunted by a Victorian gentleman who appears before guests, a German prince who killed himself there, and Napoleon III. BBC employees working late have reported encounters."},
    {"name": "Taj Mahal Palace Hotel", "lat": 18.9220, "lon": 72.8332, "country": "India", "city": "Mumbai", "description": "The architect reportedly killed himself after seeing his design altered. His ghost wanders the old wing. The 2008 terrorist attack added another layer of tragedy and reported spectral activity."},
    {"name": "Fairmont Banff Springs Hotel", "lat": 51.1672, "lon": -115.5681, "country": "Canada", "city": "Banff, Alberta", "description": "A bride fell down the stone staircase and died; her ghost dances in the ballroom in her wedding gown. A bellman named Sam McAuley continues helping guests decades after his death."},
    {"name": "Hotel del Salto", "lat": 4.7562, "lon": -74.0301, "country": "Colombia", "city": "Bogota", "description": "Built in 1928 overlooking Tequendama Falls, a sacred indigenous site. The abandoned hotel overlooking the misty gorge was a magnet for paranormal activity before museum conversion."},
    {"name": "Crescent Hotel", "lat": 36.4064, "lon": -93.7374, "country": "USA", "city": "Eureka Springs, AR", "description": "America's most haunted hotel. A cancer hospital quack stored bodies in the basement. Ghost of nurse in room 218, a cat in the lobby, and a stonemason who fell during construction."},
    {"name": "Russell Hotel", "lat": -33.8786, "lon": 151.2106, "country": "Australia", "city": "Sydney", "description": "Built in 1887, a sailor haunts the upper floors. Guests wake to see a figure in naval attire sitting on their bed. Staff find empty rooms with lights on and beds messed up."},
    {"name": "Ballygally Castle Hotel", "lat": 54.8750, "lon": -5.8639, "country": "Northern Ireland", "city": "Ballygally, Antrim", "description": "Lady Isobel Shaw, locked in a tower room by her husband who stole her baby, fell to her death trying to escape. She knocks on guest doors at night, then vanishes."},
    {"name": "Skirrid Mountain Inn", "lat": 51.8333, "lon": -3.0333, "country": "Wales", "city": "Abergavenny", "description": "The oldest pub in Wales (900+ years). Over 180 people were hanged from the beam above the staircase. Rope burn marks are still visible."},
    {"name": "Hotel & Burchiello", "lat": 45.4181, "lon": 12.0117, "country": "Italy", "city": "Oriago di Mira", "description": "This Venetian villa hotel along the Brenta Canal is haunted by a young servant girl who drowned after being spurned. Wet footprints appear on the floor in dry weather."},
    {"name": "Ackergill Tower", "lat": 58.4631, "lon": -3.0886, "country": "Scotland", "city": "Wick, Caithness", "description": "Helen Gunn, kidnapped by a rival clan chief, threw herself from the tower rather than submit. Her ghost in a green dress appears at the tower window."},
    {"name": "Queen Mary Hotel", "lat": 33.7528, "lon": -118.1903, "country": "USA", "city": "Long Beach, CA", "description": "This retired ocean liner turned hotel has a haunted pool where two women drowned in the 1930s. A young girl named Jackie is heard laughing and splashing in the drained pool."},
    {"name": "Dragsholm Slot Hotel", "lat": 55.7428, "lon": 11.5081, "country": "Denmark", "city": "Horreved", "description": "Now a luxury hotel. The skeleton of the White Lady was found bricked into a wall during renovations, confirming the legend."},
    {"name": "Lizzie Borden Bed & Breakfast", "lat": 41.7015, "lon": -71.1548, "country": "USA", "city": "Fall River, MA", "description": "Site of the 1892 axe murders of Andrew and Abby Borden. Guests can sleep in the room where Abby was found. EVP recordings capture whispers."},
    {"name": "Dalhousie Castle Hotel", "lat": 55.8708, "lon": -3.0864, "country": "Scotland", "city": "Bonnyrigg, Midlothian", "description": "A 13th-century castle where Lady Catherine haunts the dungeon after being locked away and starved to death. Grey Lady sightings are frequent."},
    {"name": "Falaknuma Palace Hotel", "lat": 17.3316, "lon": 78.4670, "country": "India", "city": "Hyderabad", "description": "Built by a Nizam who was tricked into giving it away, his sorrowful ghost wanders the Venetian mosaic halls. Staff report lights flickering and cold presences."},
    {"name": "Tequendama Falls Hotel", "lat": 4.5570, "lon": -74.2940, "country": "Colombia", "city": "Soacha", "description": "Overlooking sacred falls where the indigenous Muisca believed they could transform into eagles. Apparitions were reported constantly during its decades of abandonment."},
    {"name": "The Marshall House", "lat": 32.0782, "lon": -81.0908, "country": "USA", "city": "Savannah, GA", "description": "Used as a Union hospital during the Civil War, limbs were tossed from windows. Guests see soldier apparitions, hear footsteps, and find faucets running."},
    {"name": "Inveraray Castle Hotel Area", "lat": 56.2308, "lon": -5.0736, "country": "Scotland", "city": "Inveraray, Argyll", "description": "The castle and surrounding inns are haunted by a harpist hanged by Montrose's men in 1644. His ghostly harp music is heard before a death in the Campbell family."},
]

# ---------------------------------------------------------------------------
# Mode 5: Catacombs & Crypts
# ---------------------------------------------------------------------------
CATACOMBS_CRYPTS = [
    {"name": "Paris Catacombs", "lat": 48.8339, "lon": 2.3322, "country": "France", "city": "Paris", "description": "200 miles of tunnels lined with the bones of 6 million Parisians. Transferred from overflowing cemeteries starting in 1786. Explorers report shadow figures and voices in unmapped sections."},
    {"name": "Capuchin Catacombs", "lat": 38.1117, "lon": 13.3386, "country": "Italy", "city": "Palermo, Sicily", "description": "8,000 mummified bodies line the walls in their best clothes. The preserved body of 2-year-old Rosalia Lombardo (1920) is called 'Sleeping Beauty.'"},
    {"name": "Sedlec Ossuary (Bone Church)", "lat": 49.9614, "lon": 15.2881, "country": "Czech Republic", "city": "Kutna Hora", "description": "A chandelier made from every bone in the human body. 40,000-70,000 skeletons artistically arranged into coats of arms, garlands, and decorations."},
    {"name": "London Catacombs (West Norwood)", "lat": 51.4314, "lon": -0.0862, "country": "England", "city": "London", "description": "95 catacombs beneath West Norwood Cemetery, built in 1837 for London's elite. Hidden for decades, their rediscovery revealed forgotten coffins."},
    {"name": "Catacombs of San Gennaro", "lat": 40.8636, "lon": 14.2478, "country": "Italy", "city": "Naples", "description": "Two levels of early Christian catacombs dating to the 2nd century. Stunning Byzantine frescoes adorn burial niches."},
    {"name": "Brno Ossuary", "lat": 49.1922, "lon": 16.6089, "country": "Czech Republic", "city": "Brno", "description": "Second largest ossuary in Europe after Paris, holding over 50,000 skeletons. Rediscovered in 2001 under a square, sealed and forgotten for centuries."},
    {"name": "Catacombs of Kom el-Shoqafa", "lat": 31.1801, "lon": 29.8936, "country": "Egypt", "city": "Alexandria", "description": "A Roman-era catacomb blending Egyptian, Greek, and Roman death rituals. Discovered in 1900 when a donkey fell through the ground."},
    {"name": "San Francisco Columbarium", "lat": 37.7736, "lon": -122.4572, "country": "USA", "city": "San Francisco, CA", "description": "A stunning Neo-Classical rotunda housing thousands of cremated remains. Stained glass windows illuminate urns. Whispered conversations are heard in empty halls."},
    {"name": "Capuchin Crypt", "lat": 41.9043, "lon": 12.4886, "country": "Italy", "city": "Rome", "description": "Five crypts decorated with the bones of 3,700 Capuchin monks. Skeletal monks in robes, bone chandeliers, and a plaque reading 'What you are now, we once were.'"},
    {"name": "Catacombs of St. Callixtus", "lat": 41.8572, "lon": 12.5136, "country": "Italy", "city": "Rome", "description": "12 miles of tunnels on four levels, burial site of 16 popes and dozens of martyrs. Half a million Christians were interred here."},
    {"name": "Skull Chapel (Kaplica Czaszek)", "lat": 50.4547, "lon": 16.2975, "country": "Poland", "city": "Czermna", "description": "Walls and ceiling covered with 3,000 skulls and bones, including victims of the Thirty Years War. The priest who built it has his own skull on the altar."},
    {"name": "Wewelsburg Crypt", "lat": 51.6069, "lon": 8.6506, "country": "Germany", "city": "Buren", "description": "A circular crypt in the basement of Himmler's SS castle, designed for occult rituals. The dark history of forced labor and death cults makes it chilling."},
    {"name": "Catacombs of Priscilla", "lat": 41.9289, "lon": 12.5128, "country": "Italy", "city": "Rome", "description": "Known as the 'Queen of Catacombs,' containing the oldest known image of the Madonna and Child. 8 miles of subterranean galleries."},
    {"name": "Monastery of San Francisco Catacombs", "lat": -12.0461, "lon": -77.0268, "country": "Peru", "city": "Lima", "description": "Beneath the baroque monastery, crypts hold an estimated 25,000 bones arranged in geometric patterns. Served as Lima's cemetery until 1808."},
    {"name": "St. Michan's Church Crypts", "lat": 53.3475, "lon": -6.2786, "country": "Ireland", "city": "Dublin", "description": "Mummified remains preserved by limestone and dry air for 800 years. Bram Stoker visited as a child, possibly inspiring Dracula."},
    {"name": "Hallstatt Bone House", "lat": 47.5622, "lon": 13.6493, "country": "Austria", "city": "Hallstatt", "description": "Over 1,200 painted skulls decorated with flower crowns and the deceased's name. A tradition since the 12th century due to limited cemetery space."},
    {"name": "Fontanelle Cemetery Caves", "lat": 40.8589, "lon": 14.2417, "country": "Italy", "city": "Naples", "description": "A vast cave ossuary holding bones of plague victims. Neapolitans 'adopted' anonymous skulls, polishing and praying to them in exchange for miracles."},
    {"name": "Catacombs of Milos", "lat": 36.7142, "lon": 24.4222, "country": "Greece", "city": "Milos Island", "description": "One of the best preserved early Christian catacombs, carved into volcanic rock in the 1st century AD. Three corridors hold nearly 2,000 burial niches."},
    {"name": "Rabat Catacombs (St. Paul)", "lat": 35.8803, "lon": 14.3994, "country": "Malta", "city": "Rabat", "description": "Extensive Roman catacombs where St. Paul allegedly sheltered. Underground chambers hold early Christian, Jewish, and pagan burials side by side."},
    {"name": "Catacombs of San Giovanni", "lat": 37.0722, "lon": 15.2886, "country": "Italy", "city": "Syracuse, Sicily", "description": "A labyrinth of tunnels beneath the ruined church of San Giovanni. The crypt of San Marciano is the oldest Christian place of worship in Europe."},
]

# ---------------------------------------------------------------------------
# Mode 6: Haunted Battlefields
# ---------------------------------------------------------------------------
HAUNTED_BATTLEFIELDS = [
    {"name": "Gettysburg Battlefield", "lat": 39.8111, "lon": -77.2256, "country": "USA", "city": "Gettysburg, PA", "description": "51,000 casualties over three days in 1863. Devil's Den, the Wheatfield, and Little Round Top produce reports of ghostly cannon fire and phantom soldiers."},
    {"name": "Culloden Battlefield", "lat": 57.4764, "lon": -4.0970, "country": "Scotland", "city": "Inverness", "description": "The last pitched battle on British soil (1746). On the anniversary, ghostly Highlanders are seen re-fighting the doomed charge."},
    {"name": "Somme Battlefield", "lat": 50.0117, "lon": 2.6889, "country": "France", "city": "Albert, Picardy", "description": "Over 1 million casualties in 1916. British and German ghosts are seen in trenches. At Newfoundland Park, a ghostly caribou is spotted near the memorial at dawn."},
    {"name": "Verdun Battlefield", "lat": 49.2061, "lon": 5.4336, "country": "France", "city": "Verdun", "description": "300 days of fighting, 700,000 casualties in 1916. The Ossuary of Douaumont holds remains of 130,000 unidentified soldiers visible through windows."},
    {"name": "Gallipoli Battlefield", "lat": 40.2500, "lon": 26.2833, "country": "Turkey", "city": "Gelibolu Peninsula", "description": "250,000 Allied and Turkish casualties in the 1915-16 campaign. ANZAC Cove visitors report seeing soldiers wading ashore at dawn."},
    {"name": "Antietam Battlefield", "lat": 39.4739, "lon": -77.7439, "country": "USA", "city": "Sharpsburg, MD", "description": "Bloodiest single day in American history: 22,717 casualties on Sept 17, 1862. Blue lights appear over the Burnside Bridge at night."},
    {"name": "Passchendaele Battlefield", "lat": 50.8972, "lon": 3.0111, "country": "Belgium", "city": "Passendale", "description": "500,000 casualties in a sea of mud in 1917. Farmers still unearth bones and shells annually. Phantom soldiers are seen struggling through mist."},
    {"name": "Little Bighorn Battlefield", "lat": 45.5697, "lon": -107.4263, "country": "USA", "city": "Crow Agency, MT", "description": "Custer's Last Stand, 1876. Rangers report ghostly cavalry charges and disembodied war cries. A soldier's figure is seen on Last Stand Hill."},
    {"name": "Bosworth Field", "lat": 52.6119, "lon": -1.3972, "country": "England", "city": "Leicestershire", "description": "Where Richard III lost his crown and life in 1485. His remains were found under a parking lot in 2012. His ghost gallops across the field."},
    {"name": "Ypres (Ieper)", "lat": 50.8514, "lon": 2.8833, "country": "Belgium", "city": "Ypres", "description": "Center of WWI's most devastating battles. The Menin Gate lists 54,896 names. At the nightly Last Post ceremony, ghostly figures join the living."},
    {"name": "Normandy D-Day Beaches", "lat": 49.3633, "lon": -0.8731, "country": "France", "city": "Arromanches", "description": "Over 10,000 Allied casualties on June 6, 1944. Omaha Beach visitors report hearing gunfire and screams at dawn."},
    {"name": "Chickamauga Battlefield", "lat": 34.9239, "lon": -85.2617, "country": "USA", "city": "Fort Oglethorpe, GA", "description": "34,000 casualties in 1863. 'Old Green Eyes,' a creature with glowing eyes, has been spotted since the battle, along with a headless horseman."},
    {"name": "Marston Moor Battlefield", "lat": 53.9611, "lon": -1.2822, "country": "England", "city": "Long Marston, Yorkshire", "description": "Decisive English Civil War battle (1644). On the anniversary, phantom Cavaliers and Roundheads clash in the moonlight."},
    {"name": "Thermopylae Battlefield", "lat": 38.7964, "lon": 22.5358, "country": "Greece", "city": "Thermopylae", "description": "Where 300 Spartans held the pass against Persia in 480 BC. Locals hear ancient war cries and the clash of bronze shields at night."},
    {"name": "Isandlwana Battlefield", "lat": -28.3550, "lon": 30.6453, "country": "South Africa", "city": "KwaZulu-Natal", "description": "1,300 British soldiers overwhelmed by 20,000 Zulu warriors in 1879. Night visitors hear the thunder of approaching warriors."},
    {"name": "Agincourt Battlefield", "lat": 50.4631, "lon": 2.1436, "country": "France", "city": "Azincourt", "description": "Henry V's outnumbered English longbowmen slaughtered the French nobility on Oct 25, 1415. Phantom horses and armored knights are glimpsed in foggy fields."},
    {"name": "Bannockburn Battlefield", "lat": 56.0875, "lon": -3.9139, "country": "Scotland", "city": "Stirling", "description": "Robert the Bruce's decisive 1314 victory. The clash of arms is heard near the Borestone, and a mounted knight is seen near the monument at dusk."},
    {"name": "Stalingrad (Mamayev Kurgan)", "lat": 48.7417, "lon": 44.5372, "country": "Russia", "city": "Volgograd", "description": "Two million casualties in the deadliest battle in history (1942-43). Bones and ordnance still surface from the hill each spring."},
    {"name": "Waterloo Battlefield", "lat": 50.6803, "lon": 4.4122, "country": "Belgium", "city": "Waterloo", "description": "Napoleon's final defeat on June 18, 1815. 47,000 casualties in a single day. Farmers have uncovered musket balls and skeletal remains for two centuries."},
]

# ---------------------------------------------------------------------------
# Mode 7: Poltergeist Locations
# ---------------------------------------------------------------------------
POLTERGEIST_LOCATIONS = [
    {"name": "Enfield Poltergeist House", "lat": 51.6519, "lon": -0.0772, "country": "England", "city": "Enfield, London", "description": "The 1977-78 case: furniture moved, toys flew, and 11-year-old Janet Hodgson spoke in the voice of a dead man. Police and researchers witnessed events."},
    {"name": "Rosenheim Poltergeist Office", "lat": 47.8561, "lon": 12.1289, "country": "Germany", "city": "Rosenheim, Bavaria", "description": "In 1967, lights swung violently, paintings rotated, phones dialed the speaking clock hundreds of times per minute. Centered around secretary Annemarie Schneider."},
    {"name": "Amherst Poltergeist House", "lat": 45.8333, "lon": -64.2167, "country": "Canada", "city": "Amherst, Nova Scotia", "description": "The 1878-79 Great Amherst Mystery: Esther Cox swelled up, objects flew, fires started spontaneously, and words appeared carved in walls."},
    {"name": "South Shields Poltergeist House", "lat": 55.0003, "lon": -1.4320, "country": "England", "city": "South Shields", "description": "A 2006 case where toys stacked into pyramids, threatening texts came from inside the house, and a rocking chair moved violently on its own."},
    {"name": "Stambovsky Ghost House", "lat": 41.2317, "lon": -73.9039, "country": "USA", "city": "Nyack, NY", "description": "The only legally recognized haunted house in the US. A court ruled the owner must disclose the haunting to buyers."},
    {"name": "Pontefract Poltergeist House", "lat": 53.6917, "lon": -1.3117, "country": "England", "city": "Pontefract, Yorkshire", "description": "The Black Monk of Pontefract (1966-69): pools of water appeared, furniture threw itself downstairs, and the daughter was dragged up stairs by her throat."},
    {"name": "Borley Poltergeist Site", "lat": 52.0764, "lon": 0.7381, "country": "England", "city": "Borley, Essex", "description": "The most investigated poltergeist case in British history. 2,000 paranormal incidents were logged before the rectory burned."},
    {"name": "Bell Witch Cave", "lat": 36.4997, "lon": -87.0339, "country": "USA", "city": "Adams, TN", "description": "The Bell Witch (1817-21): an invisible entity beat John Bell to death, tormented the family with screams. Even Andrew Jackson reportedly witnessed events."},
    {"name": "Humpty Doo Poltergeist Farm", "lat": -12.5667, "lon": 131.1333, "country": "Australia", "city": "Humpty Doo, NT", "description": "A 1998 case where rocks pelted a home nightly for weeks. Police witnessed stones curving impossibly through the air from no visible source."},
    {"name": "San Pedro Poltergeist House", "lat": 33.7358, "lon": -118.2922, "country": "USA", "city": "San Pedro, CA", "description": "In 1989, a woman was attacked by invisible hands leaving bite marks. Researcher Barry Conrad filmed objects flying across rooms."},
    {"name": "Mackenzie Poltergeist Tomb", "lat": 55.9475, "lon": -3.1860, "country": "Scotland", "city": "Edinburgh", "description": "In Greyfriars Kirkyard, the tomb of Bloody Mackenzie has caused over 450 documented attacks since 1998: bruises, scratches, and broken fingers."},
    {"name": "Canneto di Caronia", "lat": 38.0253, "lon": 14.4547, "country": "Italy", "city": "Caronia, Sicily", "description": "In 2004, electronics and furniture spontaneously burst into flame. The Italian government evacuated the village. Scientists found no explanation."},
    {"name": "Tina Resch Poltergeist House", "lat": 39.9612, "lon": -82.9988, "country": "USA", "city": "Columbus, OH", "description": "In 1984, objects flew around 14-year-old Tina Resch in front of newspaper photographers. A famous photo shows a phone in mid-flight."},
    {"name": "Sauchie Poltergeist House", "lat": 56.1197, "lon": -3.8056, "country": "Scotland", "city": "Sauchie, Clackmannanshire", "description": "An 11-year-old in 1960 was the focus: a sideboard moved by itself, a linen chest rocked violently. Her teacher and doctor were witnesses."},
    {"name": "Thornton Road Poltergeist", "lat": 53.7972, "lon": -1.7594, "country": "England", "city": "Bradford, Yorkshire", "description": "A 1970s case where objects materialized from thin air, puddles formed on ceilings, and coins dropped from nowhere. Investigated by the SPR."},
    {"name": "Bridgeport Poltergeist House", "lat": 41.1865, "lon": -73.1952, "country": "USA", "city": "Bridgeport, CT", "description": "In 1974, police witnessed a 300-pound refrigerator slide across the floor and a TV set levitate. Investigated by Ed and Lorraine Warren."},
    {"name": "Battersea Poltergeist House", "lat": 51.4772, "lon": -0.1703, "country": "England", "city": "Battersea, London", "description": "From 1956-68, the Hitchings family endured 'Donald,' an entity that moved furniture, wrote messages, and slashed clothing."},
    {"name": "Guarulhos Poltergeist House", "lat": -23.4628, "lon": -46.5333, "country": "Brazil", "city": "Guarulhos, Sao Paulo", "description": "A 1973 case where stones pelted a home from inside. Objects moved violently and a 12-year-old girl was the apparent focus."},
    {"name": "Poona Poltergeist", "lat": 18.5204, "lon": 73.8567, "country": "India", "city": "Pune, Maharashtra", "description": "A well-documented 1928 case. Stones materialized inside sealed rooms, objects flew horizontally, and furniture cracked without human contact."},
]

# ---------------------------------------------------------------------------
# Mode 8: Witch Trial Sites
# ---------------------------------------------------------------------------
WITCH_TRIAL_SITES = [
    {"name": "Salem Witch Trial Memorial", "lat": 42.5128, "lon": -70.8956, "country": "USA", "city": "Salem, MA", "description": "In 1692, mass hysteria led to 20 executions and 200 accusations. Gallows Hill was only confirmed in 2016."},
    {"name": "Pendle Hill", "lat": 53.8706, "lon": -2.2775, "country": "England", "city": "Lancashire", "description": "In 1612, twelve accused witches were tried: ten were hanged. The Demdike and Chattox families had feuded for years."},
    {"name": "Bamberg Witch Trials Site", "lat": 49.8988, "lon": 10.9028, "country": "Germany", "city": "Bamberg", "description": "Between 1626-31, Prince-Bishop von Dornheim burned over 600 people in a specially built Witch Prison (Drudenhaus). The mayor was tortured and executed."},
    {"name": "Trier Witch Trials Site", "lat": 49.7557, "lon": 6.6394, "country": "Germany", "city": "Trier", "description": "The largest witch trials in European history (1581-1593). So many were executed that two villages were left with only one woman each."},
    {"name": "Loudon Witch Trials (Ursuline Convent)", "lat": 47.0022, "lon": 0.2317, "country": "France", "city": "Loudun", "description": "In 1634, priest Urbain Grandier was burned alive after nuns claimed demonic possession. Public exorcisms attended by thousands."},
    {"name": "North Berwick Witch Trials", "lat": 56.0586, "lon": -2.7200, "country": "Scotland", "city": "North Berwick", "description": "In 1590, over 70 people were accused of using witchcraft to sink King James VI's ship. Confessions extracted under horrific torture."},
    {"name": "Vardoe Witch Trial Memorial", "lat": 70.3714, "lon": 31.1100, "country": "Norway", "city": "Vardoe", "description": "91 people burned between 1600-1692 in the Finnmark witch trials. The Steilneset Memorial honors the victims in this Arctic town."},
    {"name": "Zugarramurdi Witch Caves", "lat": 43.2633, "lon": -1.5378, "country": "Spain", "city": "Zugarramurdi, Navarre", "description": "In 1610, the Spanish Inquisition tried 53 alleged witches from this Basque village. The caves where they supposedly held sabbaths are now a museum."},
    {"name": "Triora Witch Trial Site", "lat": 44.0339, "lon": 7.7678, "country": "Italy", "city": "Triora, Liguria", "description": "The 'Salem of Europe.' In 1587-89, over 30 women were accused during famine. The town now has a witchcraft museum."},
    {"name": "Fulda Witch Trials Site", "lat": 50.5528, "lon": 9.6778, "country": "Germany", "city": "Fulda", "description": "Balthasar von Dernbach prosecuted over 250 witches between 1603-06. The witch judge was eventually executed himself."},
    {"name": "Bury St Edmunds Witch Trials", "lat": 52.2465, "lon": 0.7183, "country": "England", "city": "Bury St Edmunds, Suffolk", "description": "In 1645, Matthew Hopkins, the Witchfinder General, condemned 18 people using sleep deprivation and swimming tests."},
    {"name": "Islandmagee Witch Trial Site", "lat": 54.8000, "lon": -5.6833, "country": "Northern Ireland", "city": "Islandmagee, Antrim", "description": "The last witch trial in Ireland (1711). Eight women convicted of tormenting a young girl with fits and vomiting pins."},
    {"name": "Mora Witch Trial Site", "lat": 61.0125, "lon": 14.5422, "country": "Sweden", "city": "Mora, Dalarna", "description": "In 1669, 71 people were executed including 15 children in the Dalarna witch craze. Children testified about flying to a mythical sabbath."},
    {"name": "Wurzburg Witch Trials Site", "lat": 49.7913, "lon": 9.9534, "country": "Germany", "city": "Wurzburg", "description": "Over 900 people burned between 1623-31, including 19 priests and children as young as three. Among the deadliest witch hunts in history."},
    {"name": "Perugia Witch Trial Site", "lat": 43.1107, "lon": 12.3908, "country": "Italy", "city": "Perugia", "description": "Matteuccia di Francesco was tried in 1428 in one of the earliest recorded Italian witch trials. Burned at the stake."},
    {"name": "Connecticut Witch Trial Memorial", "lat": 41.7658, "lon": -72.6734, "country": "USA", "city": "Hartford, CT", "description": "America's first witch execution: Alse Young was hanged in 1647, 45 years before Salem."},
    {"name": "Bideford Witch Trial Site", "lat": 51.0175, "lon": -4.2083, "country": "England", "city": "Bideford, Devon", "description": "Temperance Lloyd, Susannah Edwards, and Mary Trembles were the last women hanged for witchcraft in England (1682)."},
    {"name": "Paisley Witch Trial Site", "lat": 55.8464, "lon": -4.4236, "country": "Scotland", "city": "Paisley", "description": "In 1697, seven people were executed. The victims were buried beneath a horseshoe, rediscovered under a road in 2008."},
    {"name": "Oudewater Witch Weighing House", "lat": 52.0236, "lon": 4.8694, "country": "Netherlands", "city": "Oudewater", "description": "The only town where accused witches could get a fair weighing and receive a certificate of innocence. Still operates."},
    {"name": "Ellwangen Witch Trial Site", "lat": 48.9617, "lon": 10.1317, "country": "Germany", "city": "Ellwangen", "description": "In 1611-12, over 400 people were tried in one of Germany's fiercest witch panics. Mass denunciation chains named ever more witches."},
]

# ---------------------------------------------------------------------------
# Mode 9: Abandoned Asylums
# ---------------------------------------------------------------------------
ABANDONED_ASYLUMS = [
    {"name": "Danvers State Hospital", "lat": 42.5754, "lon": -70.9422, "country": "USA", "city": "Danvers, MA", "description": "A massive Gothic Kirkbride building (1878) where lobotomies and overcrowding (2,360 patients for 600 beds) created a hellscape. Inspired Arkham Asylum."},
    {"name": "Waverly Hills Sanatorium", "lat": 38.1617, "lon": -85.8264, "country": "USA", "city": "Louisville, KY", "description": "A tuberculosis hospital where an estimated 63,000 died. The 'body chute' tunnel transported corpses. Shadow people and Room 502 are infamous."},
    {"name": "Trans-Allegheny Lunatic Asylum", "lat": 38.9245, "lon": -80.4548, "country": "USA", "city": "Weston, WV", "description": "The largest hand-cut stone building in North America. Designed for 250 patients, it held 2,400 at peak. Paranormal tours operate nightly."},
    {"name": "Beelitz-Heilstatten", "lat": 52.2578, "lon": 12.9264, "country": "Germany", "city": "Beelitz, Brandenburg", "description": "A massive hospital complex where Hitler recovered from a WWI wound. Later a Soviet military hospital. 60 buildings crumble in the forest."},
    {"name": "Lier Mental Hospital", "lat": 59.7833, "lon": 10.2500, "country": "Norway", "city": "Lier", "description": "Norway's most haunted hospital. Patients were subjected to experimental treatments. Abandoned wards still contain medical equipment and records."},
    {"name": "Severalls Hospital", "lat": 51.9111, "lon": 0.9178, "country": "England", "city": "Colchester, Essex", "description": "Opened in 1913, notorious for overcrowding and insulin shock therapy. Asbestos contamination prevented quick demolition."},
    {"name": "Athens Lunatic Asylum (The Ridges)", "lat": 39.3328, "lon": -82.1031, "country": "USA", "city": "Athens, OH", "description": "Patient Margaret Schilling went missing in 1978, found dead 42 days later. Her body left a permanent stain on the floor."},
    {"name": "Whittingham Asylum", "lat": 53.8347, "lon": -2.6756, "country": "England", "city": "Preston, Lancashire", "description": "Once the largest mental hospital in England with its own church, railway, and farm. 1960s scandals revealed systematic abuse."},
    {"name": "Willard Asylum", "lat": 42.6822, "lon": -76.8586, "country": "USA", "city": "Willard, NY", "description": "Patients checked in but never left. When it closed, 400 suitcases were found in the attic, packed by patients who believed they would go home."},
    {"name": "Aradale Mental Hospital", "lat": -37.2811, "lon": 142.9075, "country": "Australia", "city": "Ararat, Victoria", "description": "Australia's largest and most haunted asylum. 13,000 patients died here. Shadows move in the mortuary and cold spots fill isolation cells."},
    {"name": "Denbigh Mental Hospital", "lat": 53.1858, "lon": -3.4214, "country": "Wales", "city": "Denbigh", "description": "A sprawling Victorian asylum. Its tower dominates the town. Explorers report disembodied screams and slamming doors."},
    {"name": "Greystone Park Psychiatric Hospital", "lat": 40.8289, "lon": -74.4706, "country": "USA", "city": "Parsippany, NJ", "description": "Once treated 7,500 patients in a building designed for 600. Mass graves of unclaimed patients were found on the grounds."},
    {"name": "St. Brigid's Psychiatric Hospital", "lat": 53.6222, "lon": -6.2436, "country": "Ireland", "city": "Ballinasloe, Galway", "description": "At peak in the 1950s, it housed over 2,000 patients. Ireland had the most psychiatric patients per capita of any country."},
    {"name": "Cane Hill Asylum", "lat": 51.3283, "lon": -0.0947, "country": "England", "city": "Coulsdon, Surrey", "description": "Once housed Charlie Chaplin's mother and David Bowie's brother. Demolished in 2010 after years of decay and arson."},
    {"name": "Pennhurst State School", "lat": 40.1383, "lon": -75.5658, "country": "USA", "city": "Spring City, PA", "description": "Horrific abuse was exposed in a 1968 TV expose. A landmark lawsuit led to deinstitutionalization nationwide."},
    {"name": "Hellingly Hospital", "lat": 50.8978, "lon": 0.2450, "country": "England", "city": "Hailsham, East Sussex", "description": "Connected by its own narrow-gauge railway, this 1903 asylum had a bakery, laundry, and power station. One of the most explored abandoned sites."},
]

# ---------------------------------------------------------------------------
# Mode 10: Haunted Prisons
# ---------------------------------------------------------------------------
HAUNTED_PRISONS = [
    {"name": "Eastern State Penitentiary", "lat": 39.9683, "lon": -75.1727, "country": "USA", "city": "Philadelphia, PA", "description": "Al Capone's cell is haunted by screams begging 'Jimmy' to leave him alone. Cellblock 12 has shadow figures and phantom footsteps in guard towers."},
    {"name": "Alcatraz Federal Penitentiary", "lat": 37.8267, "lon": -122.4233, "country": "USA", "city": "San Francisco, CA", "description": "Cell 14D once held an inmate who screamed about a creature with glowing eyes; he was found dead with handprints on his throat."},
    {"name": "Port Arthur Prison", "lat": -43.1475, "lon": 147.8531, "country": "Australia", "city": "Port Arthur, Tasmania", "description": "A brutal convict settlement where the 'Model Prison' used total silence and isolation to break minds. Ghost tours report spectral figures."},
    {"name": "Kilmainham Gaol", "lat": 53.3419, "lon": -6.3100, "country": "Ireland", "city": "Dublin", "description": "Where leaders of the 1916 Easter Rising were executed by firing squad. Cell doors slam by themselves in the freezing corridors."},
    {"name": "Bodmin Jail", "lat": 50.4753, "lon": -4.7211, "country": "England", "city": "Bodmin, Cornwall", "description": "Over 50 public hangings took place here. Visitors photograph unexplained orbs and report being pushed on stairs."},
    {"name": "Ohio State Reformatory", "lat": 40.7833, "lon": -82.5119, "country": "USA", "city": "Mansfield, OH", "description": "Filming location for 'The Shawshank Redemption.' The warden's wife was shot here and the warden killed himself. Both ghosts remain."},
    {"name": "Old Melbourne Gaol", "lat": -37.8077, "lon": 144.9653, "country": "Australia", "city": "Melbourne", "description": "Ned Kelly was hanged here in 1880. Over 130 prisoners were executed; their ghosts create cold spots and the sound of creaking ropes."},
    {"name": "Chateau d'If", "lat": 43.2800, "lon": 5.3253, "country": "France", "city": "Marseille", "description": "The island prison from 'The Count of Monte Cristo.' Real prisoners suffered for decades. Huguenot prisoners scratched calendars into walls."},
    {"name": "Old Geelong Gaol", "lat": -38.1500, "lon": 144.3617, "country": "Australia", "city": "Geelong, Victoria", "description": "A bluestone prison where hangings occurred in the courtyard. The ghost of a hanged bushranger walks the gallows wing."},
    {"name": "Shepton Mallet Prison", "lat": 51.1833, "lon": -2.5436, "country": "England", "city": "Shepton Mallet, Somerset", "description": "England's oldest prison (1610-2013). American GIs were executed here during WWII. Active with residual hauntings."},
    {"name": "Yuma Territorial Prison", "lat": 32.7250, "lon": -114.6164, "country": "USA", "city": "Yuma, AZ", "description": "A brutal desert prison where 111 inmates died from 1876-1909. The Dark Cell is ice cold in Arizona heat. A woman in white appears at dusk."},
    {"name": "Moundsville Penitentiary", "lat": 39.9206, "lon": -80.7417, "country": "USA", "city": "Moundsville, WV", "description": "Gothic stone fortress where 36 men were executed. The Shadow Man appears in the boiler room and the Sugar Shack replays violent incidents."},
    {"name": "Fremantle Prison", "lat": -32.0556, "lon": 115.7528, "country": "Australia", "city": "Fremantle, WA", "description": "Built by convict labor in the 1850s. 44 prisoners were hanged. Night tours encounter cold spots and shadows in tunnels beneath the prison."},
    {"name": "Cork City Gaol", "lat": 51.8969, "lon": -8.4917, "country": "Ireland", "city": "Cork", "description": "A castle-like prison now a museum with wax figures in cells. Visitors report figures moving when not watched and whispered Irish prayers."},
    {"name": "Old Provost Dungeon", "lat": 32.7764, "lon": -79.9300, "country": "USA", "city": "Charleston, SC", "description": "A Revolutionary War prison where patriots were starved in the basement dungeon. Their cries are heard through stone walls."},
    {"name": "Inveraray Jail", "lat": 56.2317, "lon": -5.0728, "country": "Scotland", "city": "Inveraray, Argyll", "description": "A 19th-century jail preserved as a museum. Visitors sitting in the dock feel overwhelming despair from those sentenced here."},
]


# ---------------------------------------------------------------------------
# Mode -> data mapping
# ---------------------------------------------------------------------------
MODE_OPTIONS = [
    "Famous Haunted Houses",
    "Haunted Castles of Europe",
    "Ghost Towns Worldwide",
    "Haunted Hotels & Inns",
    "Catacombs & Crypts",
    "Haunted Battlefields",
    "Poltergeist Locations",
    "Witch Trial Sites",
    "Abandoned Asylums",
    "Haunted Prisons",
]

MODE_DATA = {
    "Famous Haunted Houses": FAMOUS_HAUNTED_HOUSES,
    "Haunted Castles of Europe": HAUNTED_CASTLES,
    "Ghost Towns Worldwide": GHOST_TOWNS,
    "Haunted Hotels & Inns": HAUNTED_HOTELS,
    "Catacombs & Crypts": CATACOMBS_CRYPTS,
    "Haunted Battlefields": HAUNTED_BATTLEFIELDS,
    "Poltergeist Locations": POLTERGEIST_LOCATIONS,
    "Witch Trial Sites": WITCH_TRIAL_SITES,
    "Abandoned Asylums": ABANDONED_ASYLUMS,
    "Haunted Prisons": HAUNTED_PRISONS,
}

MODE_ICONS = {
    "Famous Haunted Houses": ("home", "darkred"),
    "Haunted Castles of Europe": ("tower", "purple"),
    "Ghost Towns Worldwide": ("warning-sign", "gray"),
    "Haunted Hotels & Inns": ("bed", "darkblue"),
    "Catacombs & Crypts": ("arrow-down", "black"),
    "Haunted Battlefields": ("flag", "red"),
    "Poltergeist Locations": ("flash", "orange"),
    "Witch Trial Sites": ("fire", "darkgreen"),
    "Abandoned Asylums": ("plus-sign", "cadetblue"),
    "Haunted Prisons": ("lock", "darkpurple"),
}

MODE_CIRCLE_COLORS = {
    "Famous Haunted Houses": "#dc2626",
    "Haunted Castles of Europe": "#8b5cf6",
    "Ghost Towns Worldwide": "#6b7280",
    "Haunted Hotels & Inns": "#3b82f6",
    "Catacombs & Crypts": "#1e293b",
    "Haunted Battlefields": "#ef4444",
    "Poltergeist Locations": "#f97316",
    "Witch Trial Sites": "#16a34a",
    "Abandoned Asylums": "#06b6d4",
    "Haunted Prisons": "#7c3aed",
}


# ---------------------------------------------------------------------------
# Overpass API helper
# ---------------------------------------------------------------------------
OVERPASS_API = "https://overpass-api.de/api/interpreter"


@st.cache_data(ttl=3600)
def fetch_overpass_haunted(lat: float, lon: float, radius_m: int = 5000) -> list:
    """Query Overpass API for nearby historic/abandoned features."""
    query = (
        f"[out:json][timeout:15];"
        f"(node[\"historic\"](around:{radius_m},{lat},{lon});"
        f"node[\"abandoned\"](around:{radius_m},{lat},{lon});"
        f"node[\"ruins\"=\"yes\"](around:{radius_m},{lat},{lon});"
        f"node[\"tourism\"=\"attraction\"][\"historic\"](around:{radius_m},{lat},{lon}););"
        f"out center 50;"
    )
    try:
        resp = requests.post(OVERPASS_API, data={"data": query}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name", tags.get("historic", "Unknown"))
            results.append({
                "name": name,
                "lat": el.get("lat", 0),
                "lon": el.get("lon", 0),
                "type": tags.get("historic", tags.get("abandoned", "unknown")),
                "description": tags.get("description", tags.get("note", "")),
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_overpass_cemeteries(lat: float, lon: float, radius_m: int = 10000) -> list:
    """Query Overpass API for cemeteries and graveyards near a point."""
    query = (
        f"[out:json][timeout:15];"
        f"(node[\"landuse\"=\"cemetery\"](around:{radius_m},{lat},{lon});"
        f"node[\"amenity\"=\"grave_yard\"](around:{radius_m},{lat},{lon});"
        f"way[\"landuse\"=\"cemetery\"](around:{radius_m},{lat},{lon}););"
        f"out center 30;"
    )
    try:
        resp = requests.post(OVERPASS_API, data={"data": query}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name", "Unnamed Cemetery")
            lat_val = el.get("lat") or el.get("center", {}).get("lat", 0)
            lon_val = el.get("lon") or el.get("center", {}).get("lon", 0)
            if lat_val and lon_val:
                results.append({
                    "name": name, "lat": lat_val, "lon": lon_val,
                    "type": "cemetery",
                    "description": tags.get("description", ""),
                })
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------
def _build_haunted_map(df: pd.DataFrame, mode: str,
                       show_nearby: bool = False,
                       center_lat: float = None,
                       center_lon: float = None) -> folium.Map:
    """Build a dark-themed folium map with haunted location markers."""
    if center_lat is not None and center_lon is not None:
        center = [center_lat, center_lon]
        zoom = 6
    elif len(df) > 0:
        center = [df["lat"].mean(), df["lon"].mean()]
        zoom = 3
    else:
        center = [20.0, 0.0]
        zoom = 2

    m = folium.Map(location=center, zoom_start=zoom,
                   tiles="CartoDB dark_matter", control_scale=True)

    icon_name, icon_color = MODE_ICONS.get(mode, ("info-sign", "gray"))
    circle_color = MODE_CIRCLE_COLORS.get(mode, "#ef4444")

    for _, row in df.iterrows():
        safe_name = html_module.escape(str(row.get("name", "Unknown")))
        safe_desc = html_module.escape(str(row.get("description", "")))
        safe_country = html_module.escape(str(row.get("country", "")))
        safe_city = html_module.escape(str(row.get("city", "")))

        popup_html = (
            f'<div style="min-width:220px;max-width:320px;font-family:Arial,sans-serif;">'
            f'<h4 style="margin:0 0 6px 0;color:#e8ecf4;background:#1a1a2e;padding:6px 8px;border-radius:4px;">{safe_name}</h4>'
            f'<p style="margin:2px 0;font-size:12px;color:#8b97b0;"><b>{safe_city}, {safe_country}</b></p>'
            f'<p style="margin:6px 0;font-size:11px;color:#c9d1d9;line-height:1.4;">{safe_desc}</p>'
            f'</div>'
        )

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=safe_name,
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="glyphicon"),
        ).add_to(m)

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8, color=circle_color, fill=True,
            fill_color=circle_color, fill_opacity=0.35, weight=1,
        ).add_to(m)

    if show_nearby and len(df) > 0:
        ref_lat = center_lat if center_lat else df.iloc[0]["lat"]
        ref_lon = center_lon if center_lon else df.iloc[0]["lon"]
        nearby = fetch_overpass_haunted(ref_lat, ref_lon, radius_m=10000)
        for feat in nearby:
            feat_name = html_module.escape(str(feat.get("name", "Historic site")))
            feat_type = html_module.escape(str(feat.get("type", "")))
            feat_desc = html_module.escape(str(feat.get("description", "")))
            popup_nearby = (
                f'<div style="min-width:160px;font-family:Arial,sans-serif;">'
                f'<h4 style="margin:0 0 4px 0;color:#06b6d4;font-size:13px;">{feat_name}</h4>'
                f'<p style="margin:2px 0;font-size:11px;color:#8b97b0;">Type: {feat_type}</p>'
                f'<p style="margin:4px 0;font-size:11px;color:#c9d1d9;">'
                f'{feat_desc if feat_desc else "No description available."}</p>'
                f'<p style="font-size:10px;color:#5a6580;margin-top:4px;">Source: OpenStreetMap</p>'
                f'</div>'
            )
            folium.CircleMarker(
                location=[feat["lat"], feat["lon"]],
                radius=5, color="#06b6d4", fill=True,
                fill_color="#06b6d4", fill_opacity=0.4, weight=1,
                popup=folium.Popup(popup_nearby, max_width=280),
                tooltip=feat_name,
            ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def _show_stats(df: pd.DataFrame, mode: str):
    """Render a row of metric cards for the current dataset."""
    total = len(df)
    countries = df["country"].nunique() if "country" in df.columns else 0
    avg_lat = df["lat"].mean() if len(df) > 0 else 0
    hemisphere = "Northern" if avg_lat >= 0 else "Southern"

    lats = df["lat"].tolist()
    lons = df["lon"].tolist()
    regions = set()
    for la, lo in zip(lats, lons):
        if la > 15 and -30 < lo < 60:
            regions.add("Europe")
        elif la > 15 and lo < -30:
            regions.add("North America")
        elif la < -10 and lo > 100:
            regions.add("Oceania")
        elif la < 0 and lo < -30:
            regions.add("South America")
        elif la > 0 and lo > 60:
            regions.add("Asia")
        elif la < 35 and 10 < lo < 55:
            regions.add("Africa")
        else:
            regions.add("Other")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Locations", total)
    with col2:
        st.metric("Countries", countries)
    with col3:
        st.metric("Regions", len(regions))
    with col4:
        st.metric("Hemisphere", hemisphere)


# ---------------------------------------------------------------------------
# Haunting intensity scoring
# ---------------------------------------------------------------------------
MODE_INTENSITY = {
    "Famous Haunted Houses": {"paranormal_reports": 9, "historical_deaths": 7, "public_access": 8, "documented_evidence": 6, "cultural_fame": 10},
    "Haunted Castles of Europe": {"paranormal_reports": 8, "historical_deaths": 9, "public_access": 7, "documented_evidence": 5, "cultural_fame": 9},
    "Ghost Towns Worldwide": {"paranormal_reports": 5, "historical_deaths": 8, "public_access": 6, "documented_evidence": 4, "cultural_fame": 7},
    "Haunted Hotels & Inns": {"paranormal_reports": 8, "historical_deaths": 6, "public_access": 10, "documented_evidence": 7, "cultural_fame": 8},
    "Catacombs & Crypts": {"paranormal_reports": 6, "historical_deaths": 10, "public_access": 7, "documented_evidence": 3, "cultural_fame": 8},
    "Haunted Battlefields": {"paranormal_reports": 7, "historical_deaths": 10, "public_access": 9, "documented_evidence": 5, "cultural_fame": 9},
    "Poltergeist Locations": {"paranormal_reports": 10, "historical_deaths": 2, "public_access": 3, "documented_evidence": 9, "cultural_fame": 7},
    "Witch Trial Sites": {"paranormal_reports": 5, "historical_deaths": 9, "public_access": 8, "documented_evidence": 4, "cultural_fame": 8},
    "Abandoned Asylums": {"paranormal_reports": 9, "historical_deaths": 8, "public_access": 4, "documented_evidence": 6, "cultural_fame": 7},
    "Haunted Prisons": {"paranormal_reports": 9, "historical_deaths": 8, "public_access": 7, "documented_evidence": 7, "cultural_fame": 8},
}


def _compute_intensity_score(mode: str) -> float:
    """Return an overall haunting intensity score (0-10) for a mode."""
    vals = MODE_INTENSITY.get(mode, {})
    if not vals:
        return 0.0
    return round(sum(vals.values()) / len(vals), 1)


def _intensity_label(score: float) -> str:
    """Return a text label for a numeric intensity score."""
    if score >= 8.5:
        return "Extreme"
    elif score >= 7.0:
        return "High"
    elif score >= 5.5:
        return "Moderate"
    elif score >= 4.0:
        return "Low"
    return "Minimal"


def _show_mode_comparison() -> pd.DataFrame:
    """Build a comparison DataFrame of all 10 modes with intensity scores."""
    rows = []
    for mode_name in MODE_OPTIONS:
        score = _compute_intensity_score(mode_name)
        details = MODE_INTENSITY.get(mode_name, {})
        count = len(MODE_DATA.get(mode_name, []))
        country_set = set(loc.get("country", "") for loc in MODE_DATA.get(mode_name, []))
        country_set.discard("")
        rows.append({
            "Mode": mode_name, "Locations": count, "Countries": len(country_set),
            "Paranormal": details.get("paranormal_reports", 0),
            "Deaths": details.get("historical_deaths", 0),
            "Access": details.get("public_access", 0),
            "Evidence": details.get("documented_evidence", 0),
            "Fame": details.get("cultural_fame", 0),
            "Overall": score, "Rating": _intensity_label(score),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------
def render_haunted_maps_tab():
    """Render the Haunted Places & Ghost Maps tab for TerraScout AI."""

    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001F47B Haunted Places & Ghost Maps</h4>'
        '<p>Explore haunted locations worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Controls ----
    ctrl_col1, ctrl_col2 = st.columns([2, 1])
    with ctrl_col1:
        mode = st.selectbox(
            "Map Mode", MODE_OPTIONS, index=0,
            help="Choose a category of haunted locations to explore.",
        )
    with ctrl_col2:
        show_nearby = st.checkbox(
            "Show nearby OSM features", value=False,
            help="Query OpenStreetMap for historic/abandoned features near the first location.",
        )

    # ---- Build DataFrame ----
    raw_data = MODE_DATA.get(mode, [])
    df = pd.DataFrame(raw_data)

    if df.empty:
        st.warning("No data available for this mode.")
        return

    # ---- Filter controls ----
    with st.expander("Filter & Search", expanded=False):
        search_col, country_col = st.columns(2)
        with search_col:
            search_text = st.text_input(
                "Search by name", "", placeholder="Type a location name...",
                key="haunted_search",
            )
        with country_col:
            all_countries = sorted(df["country"].unique().tolist())
            selected_countries = st.multiselect(
                "Filter by country", all_countries, default=[],
                key="haunted_country_filter",
            )

    if search_text:
        df = df[df["name"].str.contains(search_text, case=False, na=False)]
    if selected_countries:
        df = df[df["country"].isin(selected_countries)]

    if df.empty:
        st.info("No locations match your filters. Try broadening your search.")
        return

    # ---- Stats row ----
    _show_stats(df, mode)
    st.markdown("---")

    # ---- Map ----
    st.subheader(f"Map: {mode}")
    haunted_map = _build_haunted_map(df, mode, show_nearby=show_nearby)
    st_html(haunted_map._repr_html_(), height=500)
    st.markdown("---")

    # ---- Location Spotlight ----
    st.subheader("Location Spotlight")
    location_names = df["name"].tolist()
    selected_location = st.selectbox(
        "Select a location for details", location_names, index=0,
        key="haunted_spotlight",
    )

    if selected_location:
        loc_row = df[df["name"] == selected_location].iloc[0]
        spot_col1, spot_col2 = st.columns([1, 2])
        with spot_col1:
            st.metric("Country", loc_row.get("country", "N/A"))
            st.metric("City / Region", loc_row.get("city", "N/A"))
            st.metric("Latitude", f"{loc_row['lat']:.4f}")
            st.metric("Longitude", f"{loc_row['lon']:.4f}")
        with spot_col2:
            st.markdown(f"**{html_module.escape(str(loc_row['name']))}**")
            st.markdown(html_module.escape(str(loc_row.get("description", ""))))

        # Mini-map
        mini_map = folium.Map(
            location=[loc_row["lat"], loc_row["lon"]],
            zoom_start=12, tiles="CartoDB dark_matter", control_scale=True,
        )
        icon_name, icon_color = MODE_ICONS.get(mode, ("info-sign", "gray"))
        circle_color = MODE_CIRCLE_COLORS.get(mode, "#ef4444")
        safe_name = html_module.escape(str(loc_row["name"]))

        folium.Marker(
            location=[loc_row["lat"], loc_row["lon"]],
            tooltip=safe_name,
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="glyphicon"),
        ).add_to(mini_map)
        folium.CircleMarker(
            location=[loc_row["lat"], loc_row["lon"]],
            radius=14, color=circle_color, fill=True,
            fill_color=circle_color, fill_opacity=0.25, weight=2,
        ).add_to(mini_map)

        st_html(mini_map._repr_html_(), height=350)

        # Nearby OSM lookup
        with st.expander("Nearby historic features from OpenStreetMap"):
            if st.button("Fetch nearby features", key="haunted_nearby_btn"):
                with st.spinner("Querying Overpass API..."):
                    nearby = fetch_overpass_haunted(loc_row["lat"], loc_row["lon"], radius_m=5000)
                if nearby:
                    st.dataframe(pd.DataFrame(nearby), width=700)
                else:
                    st.info("No nearby historic features found in OpenStreetMap.")

            if st.button("Fetch nearby cemeteries", key="haunted_cemetery_btn"):
                with st.spinner("Querying Overpass API for cemeteries..."):
                    cemeteries = fetch_overpass_cemeteries(loc_row["lat"], loc_row["lon"], radius_m=10000)
                if cemeteries:
                    st.dataframe(pd.DataFrame(cemeteries), width=700)
                else:
                    st.info("No cemeteries found nearby in OpenStreetMap.")

    st.markdown("---")

    # ---- Data Table ----
    st.subheader("Data Table")
    display_df = df[["name", "country", "city", "lat", "lon", "description"]].copy()
    display_df.columns = ["Name", "Country", "City", "Latitude", "Longitude", "Description"]

    st.dataframe(
        display_df, width=None, height=400,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Country": st.column_config.TextColumn("Country", width="small"),
            "City": st.column_config.TextColumn("City", width="medium"),
            "Latitude": st.column_config.NumberColumn("Lat", format="%.4f"),
            "Longitude": st.column_config.NumberColumn("Lon", format="%.4f"),
            "Description": st.column_config.TextColumn("Description", width="large"),
        },
    )

    # ---- CSV Download ----
    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    st.download_button(
        label=f"Download {mode} CSV", data=csv_bytes,
        file_name=f"haunted_{mode.lower().replace(' ', '_')}.csv",
        mime="text/csv", key="haunted_csv_download",
    )

    st.markdown("---")

    # ---- Haunting Intensity Panel ----
    st.subheader("Haunting Intensity")
    intensity_score = _compute_intensity_score(mode)
    intensity_rating = _intensity_label(intensity_score)
    intensity_details = MODE_INTENSITY.get(mode, {})

    int_col1, int_col2, int_col3 = st.columns(3)
    with int_col1:
        st.metric("Overall Intensity", f"{intensity_score} / 10")
        st.metric("Rating", intensity_rating)
    with int_col2:
        st.metric("Paranormal Reports", f"{intensity_details.get('paranormal_reports', 0)} / 10")
        st.metric("Historical Deaths", f"{intensity_details.get('historical_deaths', 0)} / 10")
        st.metric("Documented Evidence", f"{intensity_details.get('documented_evidence', 0)} / 10")
    with int_col3:
        st.metric("Public Access", f"{intensity_details.get('public_access', 0)} / 10")
        st.metric("Cultural Fame", f"{intensity_details.get('cultural_fame', 0)} / 10")

    bar_pct = int(intensity_score * 10)
    bar_color = (
        "#ef4444" if intensity_score >= 8.0
        else "#f97316" if intensity_score >= 6.5
        else "#eab308" if intensity_score >= 5.0
        else "#22c55e"
    )
    st.markdown(
        f'<div style="background:#1a2235;border-radius:6px;height:24px;overflow:hidden;margin:8px 0 16px 0;">'
        f'<div style="width:{bar_pct}%;height:100%;background:{bar_color};border-radius:6px;transition:width 0.5s;"></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---- Mode Comparison Table ----
    with st.expander("Compare All 10 Modes", expanded=False):
        comparison_df = _show_mode_comparison()
        st.dataframe(
            comparison_df, width=None, height=420,
            column_config={
                "Mode": st.column_config.TextColumn("Mode", width="medium"),
                "Locations": st.column_config.NumberColumn("Locations"),
                "Countries": st.column_config.NumberColumn("Countries"),
                "Paranormal": st.column_config.NumberColumn("Paranormal /10"),
                "Deaths": st.column_config.NumberColumn("Deaths /10"),
                "Access": st.column_config.NumberColumn("Access /10"),
                "Evidence": st.column_config.NumberColumn("Evidence /10"),
                "Fame": st.column_config.NumberColumn("Fame /10"),
                "Overall": st.column_config.NumberColumn("Score", format="%.1f"),
                "Rating": st.column_config.TextColumn("Rating"),
            },
        )

        total_all = sum(len(MODE_DATA[m]) for m in MODE_OPTIONS)
        all_countries = set()
        for m in MODE_OPTIONS:
            for loc in MODE_DATA[m]:
                all_countries.add(loc.get("country", ""))
        all_countries.discard("")
        avg_score = round(
            sum(_compute_intensity_score(m) for m in MODE_OPTIONS) / len(MODE_OPTIONS), 1
        )
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        with sum_col1:
            st.metric("Total Locations (All Modes)", total_all)
        with sum_col2:
            st.metric("Unique Countries (All Modes)", len(all_countries))
        with sum_col3:
            st.metric("Average Intensity", f"{avg_score} / 10")

    # ---- Footer ----
    st.caption(
        "Data sources: Curated historical records, OpenStreetMap (Overpass API). "
        "Descriptions are based on documented accounts and folklore. "
        "Coordinates are approximate. Intensity scores are editorial estimates."
    )
