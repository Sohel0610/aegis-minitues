"""
Entity Registry - EXPANDED with Common Misspellings
Maps canonical company names to known aliases and common typos
"""
 
ENTITY_REGISTRY = {
    # --- ADANI GROUP (Using "Ltd" to match database) ---
    "Adani Green Energy Ltd": [
        "adani green energy",
        "adani green energy ltd",
        "adani green energy limited",
        "agel",
        "adani green",
        "adnai green",  # Common typo
        "adani green",  # Typo handling
        "adani green enrgy",  # Typo handling
        "adanni green",  # Typo handling
        "green energy",
    ],
    "Adani Power Ltd": [
        "adani power",
        "adani power ltd",
        "adani power limited",
        "adnai power",  # Typo handling
        "adani powr",  # Typo handling
        "adanni power",  # Typo handling
    ],
    "Adani Total Gas Ltd": [
        "adani gas",
        "adani total gas",
        "adani gas ltd",
        "adani total gas limited",
        "atgl",
        "adnai gas",  # Typo handling
        "adanni gas",  # Typo handling
    ],
    "Adani Ports and SEZ Ltd": [
        "adani ports",
        "adani ports and sez",
        "adani ports & sez",
        "adani ports and special economic zone",
        "apsez",
        "adnai ports",  # Typo handling
    ],
    "Adani Transmission Ltd": [
        "adani transmission",
        "adani transmission ltd",
        "adani transmission limited",
        "adnai transmission",  # Typo handling
    ],
    "Adani Enterprises Ltd": [
        "adani enterprises",
        "adani enterprises ltd",
        "adani enterprises limited",
        "adnai enterprises",  # Typo handling
    ],
    
    # --- RELIANCE GROUP ---
    "Reliance Industries Ltd": [
        "reliance",
        "reliance industries",
        "ril",
        "reliance industries limited",
        "reliance industries ltd",
        "relince",  # Common typo
        "relianse",  # Common typo
        "reliance ind",
    ],
    "Reliance Power Ltd": [
        "reliance power",
        "reliance power ltd",
        "reliance power limited",
        "relince power",  # Typo handling
    ],
    "Reliance Infrastructure Ltd": [
        "reliance infrastructure",
        "reliance infra",
        "reliance infrastructure ltd",
    ],
    
    # --- TATA GROUP ---
    "Tata Motors Ltd": [
        "tata motors",
        "tata motors ltd",
        "tata motors limited",
        "tatamotors",
    ],
    "Tata Steel Ltd": [
        "tata steel",
        "tata steel ltd",
        "tata steel limited",
    ],
    "Tata Power Ltd": [
        "tata power",
        "tata power ltd",
        "tata power limited",
    ],
    "Tata Consultancy Services Ltd": [
        "tcs",
        "tata consultancy services",
        "tata consultancy",
        "tata consultancy services ltd",
    ],
    
    # --- TELECOM ---
    "Bharti Airtel Ltd": [
        "bharti airtel",
        "airtel",
        "bharti airtel ltd",
        "bharti airtel limited",
        "bharti",
    ],
    "Vodafone Idea Ltd": [
        "vodafone idea",
        "vodafone",
        "idea",
        "vi",
        "vodafone idea ltd",
    ],
    
    # --- IT COMPANIES ---
    "Infosys Ltd": [
        "infosys",
        "infosys ltd",
        "infosys limited",
        "infy",
        "infosyss",  # Typo handling
    ],
    "Wipro Ltd": [
        "wipro",
        "wipro ltd",
        "wipro limited",
        "wipro technologies",
    ],
    "HCL Technologies Ltd": [
        "hcl",
        "hcl technologies",
        "hcl tech",
        "hcl technologies ltd",
    ],
    "Tech Mahindra Ltd": [
        "tech mahindra",
        "tech mahindra ltd",
        "techmahindra",
    ],
    
    # --- BANKS ---
    "HDFC Bank Ltd": [
        "hdfc bank",
        "hdfc",
        "hdfc bank ltd",
        "hdfc bank limited",
    ],
    "ICICI Bank Ltd": [
        "icici bank",
        "icici",
        "icici bank ltd",
        "icici bank limited",
    ],
    "State Bank of India": [
        "sbi",
        "state bank of india",
        "state bank",
        "sbi bank",
    ],
    "Axis Bank Ltd": [
        "axis bank",
        "axis",
        "axis bank ltd",
    ],
    
    # --- ENERGY & POWER ---
    "Premier Energies Ltd": [
        "premier energies",
        "premier energies ltd",
        "premier energies limited",
        "premier energy",
    ],
    "NTPC Ltd": [
        "ntpc",
        "ntpc ltd",
        "ntpc limited",
        "national thermal power corporation",
    ],
    "Power Grid Corporation of India Ltd": [
        "power grid",
        "powergrid",
        "power grid corporation",
        "pgcil",
    ],
    
    # --- AUTOMOBILES ---
    "Maruti Suzuki India Ltd": [
        "maruti suzuki",
        "maruti",
        "maruti suzuki india",
        "msil",
    ],
    "Mahindra & Mahindra Ltd": [
        "mahindra",
        "m&m",
        "mahindra and mahindra",
        "mahindra & mahindra",
    ],
    
    # --- PHARMA ---
    "Sun Pharmaceutical Industries Ltd": [
        "sun pharma",
        "sun pharmaceutical",
        "sun pharma industries",
    ],
    "Dr Reddy's Laboratories Ltd": [
        "dr reddy",
        "dr reddys",
        "dr reddy's laboratories",
        "dr reddys labs",
    ],
    
    # --- FMCG ---
    "ITC Ltd": [
        "itc",
        "itc ltd",
        "itc limited",
    ],
    "Hindustan Unilever Ltd": [
        "hul",
        "hindustan unilever",
        "hindustan unilever ltd",
        "unilever india",
    ],
}