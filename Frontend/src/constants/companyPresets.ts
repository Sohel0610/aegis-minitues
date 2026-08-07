/**
 * Shared company presets for the Minutes Preparation module.
 * 
 * Single source of truth — imported by MinutesGenerator and FormBasedGenerator
 * to ensure consistent company data across the module.
 */

export interface CompanyDirector {
  name: string;
  din: string;
}

export interface CompanyPreset {
  name: string;
  address: string;
  directors: CompanyDirector[];
}

export const companyPresets: CompanyPreset[] = [
  {
    name: "Adani Enterprises Limited",
    address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Rajesh Adani", din: "00222020" },
      { name: "Pranav Adani", din: "00222021" },
    ],
  },
  {
    name: "Adani Enterprises Ltd.",
    address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Rajesh Adani", din: "00222020" },
      { name: "Pranav Adani", din: "00222021" },
    ],
  },
  {
    name: "Adani Green Energy Limited",
    address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Sagar Adani", din: "00222025" },
      { name: "Vneet S. Jaain", din: "00222026" },
    ],
  },
  {
    name: "Adani Green Energy Ltd.",
    address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Sagar Adani", din: "00222025" },
      { name: "Vneet S. Jaain", din: "00222026" },
    ],
  },
  {
    name: "Adani Ports and SEZ Limited",
    address: "Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Karan Adani", din: "00222022" },
      { name: "Ashwani Gupta", din: "00222023" },
    ],
  },
  {
    name: "Adani Ports and Special Economic Zone Ltd.",
    address: "Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Karan Adani", din: "00222022" },
      { name: "Ashwani Gupta", din: "00222023" },
    ],
  },
  {
    name: "Adani Total Gas Ltd.",
    address: "Adani Corporate House, Shantigram, S. G. Highway, Ahmedabad - 382421",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Pranav Adani", din: "00222021" },
      { name: "Suresh P. Manglani", din: "00222024" },
      { name: "Shweta Shroff", din: "00222027" },
    ],
  },
  {
    name: "Adani Total Gas Limited",
    address: "Adani Corporate House, Shantigram, S. G. Highway, Ahmedabad - 382421",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Pranav Adani", din: "00222021" },
      { name: "Suresh P. Manglani", din: "00222024" },
      { name: "Shweta Shroff", din: "00222027" },
    ],
  },
  {
    name: "Adani Power Ltd.",
    address: "Shikhar, Near Mithakhali Six Roads, Navrangpura, Ahmedabad - 380009",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Anil Sardana", din: "00222028" },
      { name: "Shersingh B. Khyalia", din: "00222029" },
    ],
  },
  {
    name: "Adani Energy Solutions Ltd.",
    address: "Adani Corporate House, Shantigram, S. G. Highway, Ahmedabad - 382421",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Kandarp Patel", din: "00222030" },
    ],
  },
  {
    name: "Adani Logistics Ltd.",
    address: "Adani Corporate House, Shantigram, S. G. Highway, Ahmedabad - 382421",
    directors: [
      { name: "Karan Adani", din: "00222022" },
      { name: "Vikram Jaisinghani", din: "00222031" },
    ],
  },
  {
    name: "Adani Wilmar Ltd.",
    address: "Fortune House, Near Navrangpura Railway Crossing, Ahmedabad - 380009",
    directors: [
      { name: "Kuok Khoon Hong", din: "00222032" },
      { name: "Angshu Mallick", din: "00222033" },
    ],
  },
  {
    name: "Adani Digital Labs Private Ltd.",
    address: "Adani Corporate House, Shantigram, S. G. Highway, Ahmedabad - 382421",
    directors: [
      { name: "Nitin Sethi", din: "00222034" },
      { name: "Sudipta Bhattacharya", din: "00222035" },
    ],
  },
];

