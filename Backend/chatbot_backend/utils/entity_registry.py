
"""
Entity Registry - MATCHES YOUR DATABASE FORMAT
Maps canonical company names to known aliases
"""

ENTITY_REGISTRY = {
    # --- ADANI GROUP (Using "Ltd" to match database) ---
    "Adani Green Energy Ltd": [
        "adani green energy",
        "adani green energy ltd",
        "adani green energy limited",
        "agel",
        "adani green",
        "aani green",  # Typo handling
        "adani green enrgy",  # Typo handling
        "green energy",
        "adani green energy l t d",  # spacing typo
        "adani greenenergy",
    ],
    "Adani Power Ltd": [
        "adani power",
        "adani power ltd",
        "adani power limited",
        "aani power",  # Typo handling
        "adani powr",  # Typo handling
        "adani pwr",  # Typo handling
        "adani power l t d",  # spacing typo
    ],
    "Adani Enterprises Ltd": [
        "adani enterprises",
        "adani enterprises ltd",
        "adani enterprises limited",
        "ael",
        "adani ent",
        "adani enterprise",  # singular variant
        "adani ent ltd",
    ],
    "Adani Energy Solutions Ltd": [
        "adani energy solutions",
        "adani energy solutions ltd",
        "adani energy solutions limited",
        "aesl",
        "adani transmission",           # former name / business
        "adani transmission ltd",
        "adani transmission limited",
        "adani energy",                 # shortened
        "adani energy solution",        # singular
    ],

    # --- OTHER COMPANIES (Expanded) ---
    "AWL Agri Business Ltd": [
        "awl agri business",
        "awl agri business ltd",
        "awl agri business limited",
        "adani wilmar",                 # former/common brand association
        "adani wilmar ltd",
        "adani wilmar limited",
        "awl",
        "fortune foods",                # consumer brand link
        "fortune",
        "awl agri",                     # shortened
        "awl agribusines",              # typo
    ],
    "Tata Power Company Ltd": [
        "tata power",
        "tata power company",
        "tata power company ltd",
        "tata power company limited",
        "tprel",                        # Tata Power Renewable Energy Ltd (contextual)
        "tpc",
        "tata power ltd",
    ],
    "Life Insurance Corporation of India (LIC)": [
        "lic",
        "life insurance corporation",
        "life insurance corporation of india",
        "lic india",
        "lic ltd",
        "life insurance corp of india",
        "life insurance corporation of india (lic)",
    ],
    "Hindustan Unilever Ltd (HUL)": [
        "hul",
        "hindustan unilever",
        "hindustan unilever ltd",
        "hindustan unilever limited",
        "unilever india",
        "h u l",                        # spacing typo/variant
        "hindustan unilvr",             # typo
    ],
    "Mahindra & Mahindra Ltd": [
        "mahindra & mahindra",
        "mahindra and mahindra",
        "mahindra & mahindra ltd",
        "mahindra & mahindra limited",
        "m&m",
        "mahindra",
        "mahindra ltd",
        "mahindra and mahindra ltd",
    ],
    "ITC Ltd": [
        "itc",
        "itc limited",
        "itc ltd",
        "itc india",
        "i t c",                        # spacing
    ],
    "Tata Motors Ltd": [
        "tata motors",
        "tata motors ltd",
        "tata motors limited",
        "tml",
        "tata motor",                   # singular variant
    ],
    "Bharti Airtel Ltd": [
        "bharti airtel",
        "airtel",
        "bharti airtel ltd",
        "bharti airtel limited",
        "airtel india",
        "bharti",
        "barti airtel",                 # typo
    ],
    "Larsen & Toubro Ltd (L&T)": [
        "larsen & toubro",
        "larsen and toubro",
        "l&t",
        "l and t",
        "larsen & toubro ltd",
        "larsen & toubro limited",
        "larsen toubro",
        "lt",
    ],
    "Reliance Industries Ltd": [
        "reliance",
        "reliance industries",
        "ril",
        "reliance industries limited",
        "reliance industries ltd",
        "reliance ind",
        "reliance ind ltd",
    ],
    "State Bank of India (SBI)": [
        "sbi",
        "state bank of india",
        "sbi bank",
        "state bank",
        "state bank of india (sbi)",
    ],
    "Premier Energies Ltd": [
        "premier energies",
        "premier energies ltd",
        "premier energies limited",
        "premier energy",               # singular
    ],
    "Acme Solar Holdings Ltd": [
        "acme solar",
        "acme solar holdings",
        "acme solar holdings ltd",
        "acme solar holdings limited",
        "acme",
        "acme solar ltd",
        "acme solar holding",           # singular typo
    ],
    "Gateway Distriparks Ltd": [
        "gateway distriparks",
        "gateway distriparks ltd",
        "gateway distriparks limited",
        "gateway",
        "gateway distripark",           # singular
    ],
    "Waaree Energies Ltd": [
        "waaree energies",
        "waaree energies ltd",
        "waaree energies limited",
        "waaree",
        "waaree solar",                 # common context
        "waree energies",               # typo
    ],
    "PSP Projects Ltd": [
        "psp projects",
        "psp projects ltd",
        "psp projects limited",
        "psp",
        "psp project",                  # singular
    ],
    "GMR Airports Ltd": [
        "gmr airports",
        "gmr airports ltd",
        "gmr airports limited",
        "gmr",
        "gmrairport",                   # nse symbol reference
        "gmr airport",                  # singular
    ],
    "JSW Energy Ltd": [
        "jsw energy",
        "jsw energy ltd",
        "jsw energy limited",
        "jsw",
        "jsw enery",                    # typo
    ],
    "Torrent Power Ltd": [
        "torrent power",
        "torrent power ltd",
        "torrent power limited",
        "torrent",
        "torrent powr",                 # typo
    ],
    "Tata Steel Ltd": [
        "tata steel",
        "tata steel ltd",
        "tata steel limited",
        "tatasteel",
        "tsl",
    ],
    "JSW Infrastructure Ltd": [
        "jsw infrastructure",
        "jsw infrastructure ltd",
        "jsw infrastructure limited",
        "jsw infra",
        "jsw infra ltd",
        "jswinfra",
    ],
    "HDFC Bank Ltd": [
        "hdfc bank",
        "hdfc bank ltd",
        "hdfc bank limited",
        "hdfc",
        "h d f c bank",
    ],
    "ACC Ltd": [
        "acc",
        "acc ltd",
        "acc limited",
        "acc cement",
        "a c c",
    ],
    "Inox Wind Ltd": [
        "inox wind",
        "inox wind ltd",
        "inox wind limited",
        "inox",
        "inoxwnd",                      # ticker-like
    ],
    "Container Corporation of India Ltd (CONCOR)": [
        "container corporation of india",
        "container corporation of india ltd",
        "container corporation of india limited",
        "concor",
        "c o n c o r",                  # spacing
        "container corp of india",      # abbreviated
    ],
    "Sanghi Industries Ltd": [
        "sanghi industries",
        "sanghi industries ltd",
        "sanghi industries limited",
        "sanghi",
        "sanghi cements",               # common context
    ],
    "Ambuja Cements Ltd": [
        "ambuja cements",
        "ambuja cements ltd",
        "ambuja cements limited",
        "ambuja cement",                # singular
        "ambuja",
        "ambuja ltd",
    ],
    "Suzlon Energy Ltd": [
        "suzlon energy",
        "suzlon energy ltd",
        "suzlon energy limited",
        "suzlon",
        "suzln",                        # typo
    ],
    "NTPC Ltd": [
        "ntpc",
        "ntpc ltd",
        "ntpc limited",
        "national thermal power corporation",
        "n t p c",
    ],
    "Piramal Finance Ltd": [
        "piramal finance",
        "piramal finance ltd",
        "piramal finance limited",
        "piramal capital & housing finance",
        "piramal capital and housing finance",
        "piramal capital",
        "piramal housing finance",
        "p chfl",
        "piramal fin",                  # shortened
    ],
    "Aditya Birla Housing Finance Ltd": [
        "aditya birla housing finance",
        "aditya birla housing finance ltd",
        "aditya birla housing finance limited",
        "abhfl",
        "aditya birla finance",
        "aditya birla hf",              # shortened
        "ab housing finance",
    ],

    # --- ORIGINAL KEYS PRESENT IN YOUR TEMPLATE (kept for completeness) ---
    "Adani Total Gas Ltd": [
        "adani gas",
        "adani total gas",
        "adani gas ltd",
        "adani total gas limited",
        "atgl",
        "aani gas",  # Typo handling
    ],
    "Adani Ports and SEZ Ltd": [
        "adani ports",
        "adani ports and sez",
        "adani ports & sez",
        "adani ports and special economic zone",
        "apsez",
        "adani port",                   # singular
    ],
}
