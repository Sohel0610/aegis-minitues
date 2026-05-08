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
      { name: "Vinod Adani", din: "00222020" },
      { name: "Ashish Kundra", din: "00222021" },
    ],
  },
  {
    name: "Adani Green Energy Limited",
    address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Vinod Adani", din: "00222020" },
      { name: "Ashish Kundra", din: "00222021" },
    ],
  },
  {
    name: "Adani Ports and SEZ Limited",
    address: "Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421",
    directors: [
      { name: "Gautam Adani", din: "00222019" },
      { name: "Karan Adani", din: "00222022" },
    ],
  },
];
