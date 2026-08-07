import sqlite3
import os
import pandas as pd
import re

# Paths to the databases
directors_db_path = r"c:\Users\ABHI MANE\Downloads\Aegis_New\Aegis_21-11-2025\backend\public\directors.db"
family_db_path = r"c:\Users\ABHI MANE\Downloads\Aegis_New\Aegis_21-11-2025\backend\public\Director_Family_Information.db"

def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def basic_name_similarity(s1, s2):
    """Calculate similarity between two names based on Levenshtein distance"""
    # Convert to lowercase and remove extra spaces
    s1 = ' '.join(s1.lower().split())
    s2 = ' '.join(s2.lower().split())
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(s1, s2)
    
    # Calculate similarity as a percentage
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    
    similarity = 1 - (distance / max_len)
    return similarity

def extract_name_components(name):
    """
    Extract components from an Indian name.
    Returns: (first_name, middle_names, last_name/surname)
    """
    parts = name.strip().split()
    if len(parts) == 0:
        return ("", [], "")
    elif len(parts) == 1:
        return (parts[0], [], "")
    elif len(parts) == 2:
        return (parts[0], [], parts[1])
    else:
        # For names with 3 or more parts
        return (parts[0], parts[1:-1], parts[-1])

def normalize_name_for_comparison(name):
    """
    Normalize a name for comparison by:
    1. Converting to lowercase
    2. Removing extra spaces
    3. Expanding common abbreviations
    """
    # Convert to lowercase and normalize spaces
    normalized = ' '.join(name.lower().split())
    
    # Expand common abbreviations
    abbreviations = {
        's.': 'singh',
        'k.': 'kumar',
        'r.': 'ram',
        'm.': 'maheshwari',
        'j.': 'jain',
        'g.': 'gupta',
        's.': 'shah',
        'a.': 'agarwal',
        'p.': 'patel',
        'm.': 'mehta',
        'v.': 'verma',
        'd.': 'das',
        'b.': 'bose',
        'c.': 'choudhury',
        'n.': 'nair',
        'r.': 'reddy',
        'k.': 'krishnan',
        'n.': 'nathan',
        's.': 'subramanian',
        'v.': 'varma',
        'p.': 'pillai',
        'r.': 'rao',
        'd.': 'desai',
        's.': 'sharma',
        't.': 'tripathi',
        'm.': 'mishra',
        'p.': 'prasad',
        'd.': 'devi',
        'k.': 'kumari',
        'l.': 'lal',
        'c.': 'chand',
        's.': 'suresh',
        'r.': 'ramesh',
        'm.': 'mohan',
        'a.': 'arora',
        'b.': 'bhatia',
        'g.': 'gandhi',
        'j.': 'joshi',
        'v.': 'vaidya',
        't.': 'trivedi',
        'p.': 'pandey',
        's.': 'srivastava',
        'm.': 'malhotra',
        'b.': 'bansal',
        'g.': 'grover',
        'k.': 'kapoor',
        's.': 'saxena',
        'm.': 'mittal',
        'j.': 'jain',
        'v.': 'varma',
        's.': 'sinha',
        't.': 'tyagi',
        'c.': 'chauhan',
        'r.': 'rawat',
        'b.': 'biswas',
        'd.': 'dutta',
        's.': 'sengupta',
        'm.': 'mukherjee',
        'b.': 'banerjee',
        'c.': 'chakraborty',
        'p.': 'pal',
        'd.': 'dhar',
        'b.': 'bhattacharya',
        'c.': 'chatterjee',
        'g.': 'ganguly',
        'm.': 'majumdar',
        'b.': 'basu',
        'd.': 'dey',
        'm.': 'mondal',
        'r.': 'roy',
        'd.': 'dasgupta',
        'c.': 'chowdhury',
        'b.': 'bagchi',
        'm.': 'mukhopadhyay',
        's.': 'samanta',
        'd.': 'dhar',
        'b.': 'bhowmick',
        'c.': 'chakravarty',
        'm.': 'maitra',
        'd.': 'debnath',
        'b.': 'bose',
        'c.': 'chakrabarti',
        'm.': 'mallick',
        'b.': 'bhattacharjee',
        'd.': 'dutta',
        's.': 'sarkar',
        'm.': 'mandal',
        'c.': 'chanda',
        'd.': 'de',
        'b.': 'bhadra',
        'c.': 'choudhuri',
        'm.': 'manna',
        'b.': 'bhattacharyya',
        'd.': 'dhar',
        'c.': 'chakladar',
        'm.': 'mukherji',
        'b.': 'bandopadhyay',
        'd.': 'dey',
        'c.': 'chaki',
        'm.': 'mukhopadhy',
    }
    
    # Apply abbreviation expansion
    for abbrev, full in abbreviations.items():
        # Replace standalone abbreviations (with word boundaries)
        pattern = r'\b' + re.escape(abbrev) + r'\b'
        normalized = re.sub(pattern, full, normalized)
    
    return normalized

def indian_name_similarity(name1, name2):
    """
    Enhanced similarity function specifically designed for Indian names.
    Handles:
    1. Abbreviated middle names (e.g., 'Abhishek M. Mane' vs 'Abhishek Mahadev Mane')
    2. Surname variations
    3. Case and spacing differences
    4. Common spelling variations
    """
    # Normalize both names
    norm_name1 = normalize_name_for_comparison(name1)
    norm_name2 = normalize_name_for_comparison(name2)
    
    # First try exact match after normalization
    if norm_name1 == norm_name2:
        return 1.0
    
    # Extract components
    first1, middle1, last1 = extract_name_components(norm_name1)
    first2, middle2, last2 = extract_name_components(norm_name2)
    
    # Check if first names match
    first_match = False
    if first1 == first2:
        first_match = True
    else:
        # Try Levenshtein distance for first names
        first_sim = basic_name_similarity(first1, first2)
        first_match = first_sim >= 0.8  # High threshold for first names
    
    if not first_match:
        return 0.0  # If first names don't match, likely not the same person
    
    # Check if last names match
    last_match = False
    if last1 == last2 and last1 != "":
        last_match = True
    elif last1 != "" and last2 != "":
        # Try Levenshtein distance for last names
        last_sim = basic_name_similarity(last1, last2)
        last_match = last_sim >= 0.7  # Medium threshold for last names
    elif last1 == "" and last2 == "":
        # Both have no last names
        last_match = True
    
    # Handle middle names
    middle_score = 0.0
    if len(middle1) == 0 and len(middle2) == 0:
        # Both have no middle names
        middle_score = 1.0
    elif len(middle1) > 0 and len(middle2) > 0:
        # Both have middle names - check for matches
        middle_score = compare_middle_names(middle1, middle2)
    elif len(middle1) > 0 and len(middle2) == 0:
        # name1 has middle names, name2 doesn't
        # This could be an abbreviated form
        middle_score = 0.7  # Partial score
    elif len(middle1) == 0 and len(middle2) > 0:
        # name2 has middle names, name1 doesn't
        # This could be an abbreviated form
        middle_score = 0.7  # Partial score
    
    # Calculate overall similarity
    # Weighted average: first name (40%), last name (40%), middle names (20%)
    if last_match:
        overall_similarity = (0.4 * 1.0) + (0.4 * 1.0) + (0.2 * middle_score)
    else:
        # Last names don't match, reduce confidence
        overall_similarity = (0.5 * 1.0) + (0.3 * 0.5) + (0.2 * middle_score)
    
    return overall_similarity

def compare_middle_names(middle1, middle2):
    """
    Compare middle names, handling abbreviations and partial matches.
    """
    # Convert to sets for easier comparison
    set1 = set(middle1)
    set2 = set(middle2)
    
    # Check for exact matches
    exact_matches = set1.intersection(set2)
    if len(exact_matches) == len(set1) and len(exact_matches) == len(set2):
        return 1.0  # Perfect match
    
    # Check for abbreviation matches
    abbr_matches = 0
    total_comparisons = max(len(set1), len(set2))
    
    for m1 in set1:
        for m2 in set2:
            # Check if one is an abbreviation of the other
            if is_abbreviation(m1, m2) or is_abbreviation(m2, m1):
                abbr_matches += 1
                break
            # Check for close similarity
            elif basic_name_similarity(m1, m2) >= 0.7:
                abbr_matches += 1
                break
    
    if total_comparisons > 0:
        return abbr_matches / total_comparisons
    else:
        return 0.0

def is_abbreviation(abbr, full):
    """
    Check if abbr is an abbreviation of full.
    E.g., 'M.' is an abbreviation of 'Mahadev'
    """
    abbr = abbr.rstrip('.')  # Remove trailing dot
    if len(abbr) == 1:
        return full.lower().startswith(abbr.lower())
    elif len(abbr) > 1:
        # Check if it's a shortened version
        return basic_name_similarity(abbr, full) >= 0.7
    return False

def enhanced_fuzzy_analysis():
    """Enhanced fuzzy matching analysis with improved Indian name handling"""
    # Check if databases exist
    if not os.path.exists(directors_db_path):
        print(f"Directors database not found at: {directors_db_path}")
        return
    
    if not os.path.exists(family_db_path):
        print(f"Family information database not found at: {family_db_path}")
        return
    
    try:
        # Connect to directors database
        directors_conn = sqlite3.connect(directors_db_path)
        directors_cursor = directors_conn.cursor()
        
        # Connect to family information database
        family_conn = sqlite3.connect(family_db_path)
        family_cursor = family_conn.cursor()
        
        # Get all directors from both databases
        directors_cursor.execute("SELECT id, name, din FROM directors ORDER BY name")
        directors_rows = directors_cursor.fetchall()
        
        family_cursor.execute("SELECT Name FROM Sheet1 ORDER BY Name")
        family_rows = family_cursor.fetchall()
        
        directors_list = [row[1] for row in directors_rows]  # Just the names
        family_list = [row[0] for row in family_rows]  # Just the names
        
        # Find exact matches
        exact_matches = [director for director in directors_list if director in family_list]
        
        # Find directors only and family only
        directors_only = [director for director in directors_list if director not in family_list]
        family_only = [family_member for family_member in family_list if family_member not in directors_list]
        
        print(f"Exact matches: {len(exact_matches)}")
        print(f"Directors only: {len(directors_only)}")
        print(f"Family only: {len(family_only)}")
        
        # Enhanced fuzzy matching analysis
        fuzzy_matches = []
        
        # Analyze all directors_only against all family_only
        for director in directors_only:
            best_matches = []
            
            for family_member in family_only:
                similarity = indian_name_similarity(director, family_member)
                if similarity >= 0.5:  # Only consider matches with 50%+ similarity
                    best_matches.append((family_member, similarity))
            
            # Sort by similarity (highest first) and take top 3
            best_matches.sort(key=lambda x: x[1], reverse=True)
            top_matches = best_matches[:3]
            
            if top_matches:
                fuzzy_matches.append((director, top_matches))
        
        # Create detailed report
        report_lines = []
        report_lines.append("# Enhanced Director Matching Analysis (Indian Names)")
        report_lines.append("===================================================")
        report_lines.append("")
        report_lines.append(f"Analysis Date: {pd.Timestamp.now()}")
        report_lines.append("")
        report_lines.append("## Database Statistics")
        report_lines.append(f"- Directors in directors.db: {len(directors_list)}")
        report_lines.append(f"- Directors in Director_Family_Information.db: {len(family_list)}")
        report_lines.append("")
        report_lines.append("## Matching Results")
        report_lines.append(f"- Exact matches: {len(exact_matches)}")
        report_lines.append(f"- Directors only (not in family DB): {len(directors_only)}")
        report_lines.append(f"- Family entries only (not in directors DB): {len(family_only)}")
        report_lines.append(f"- Potential fuzzy matches (score >= 0.5): {len(fuzzy_matches)}")
        report_lines.append("")
        report_lines.append("## Exact Matches")
        report_lines.append("----------------")
        for match in sorted(exact_matches):
            report_lines.append(f"- {match}")
        report_lines.append("")
        report_lines.append("## Directors Only (Not in Family Database)")
        report_lines.append("------------------------------------------")
        for director in sorted(directors_only):
            report_lines.append(f"- {director}")
        report_lines.append("")
        report_lines.append("## Family Entries Only (Not in Directors Database)")
        report_lines.append("--------------------------------------------------")
        for family_member in sorted(family_only):
            report_lines.append(f"- {family_member}")
        report_lines.append("")
        report_lines.append("## Potential Fuzzy Matches (Enhanced Algorithm)")
        report_lines.append("----------------------------------------------")
        
        for director, matches in fuzzy_matches:
            report_lines.append(f"### {director}")
            report_lines.append("| Family Database Entry | Similarity Score |")
            report_lines.append("|----------------------|------------------|")
            for family_member, similarity in matches:
                report_lines.append(f"| {family_member} | {similarity:.2f} |")
            report_lines.append("")
        
        # Write report to file
        report_path = r"c:\Users\ABHI MANE\Downloads\Aegis_New\Aegis_21-11-2025\EnhancedMatchedDirectors.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"\nEnhanced fuzzy matching report written to: {report_path}")
        
        # Also create CSV for easier analysis
        csv_data = []
        for director, matches in fuzzy_matches:
            for family_member, similarity in matches:
                csv_data.append({
                    'Directors DB Name': director,
                    'Family DB Name': family_member,
                    'Similarity Score': round(similarity, 2)
                })
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = r"c:\Users\ABHI MANE\Downloads\Aegis_New\Aegis_21-11-2025\EnhancedMatchedDirectors.csv"
            df.to_csv(csv_path, index=False)
            print(f"CSV version exported to: {csv_path}")
        
        # Close connections
        directors_conn.close()
        family_conn.close()
        
    except Exception as e:
        print(f"Error in enhanced fuzzy analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    enhanced_fuzzy_analysis()