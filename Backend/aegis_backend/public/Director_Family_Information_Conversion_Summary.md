# Director Family Information - Excel to Database Conversion Summary

## Overview
This document summarizes the conversion of the Excel file `Director_Family_Information.xlsx` into a SQLite database format.

## Conversion Details
- **Source File**: `Director_Family_Information.xlsx`
- **Output Database**: `Director_Family_Information.db`
- **Conversion Date**: November 30, 2025
- **Tool Used**: Custom Python script using pandas and sqlite3

## Database Structure

### Table: Sheet1
The database contains one table named "Sheet1" with the following columns:

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Name | TEXT | Director's name |
| Section_2(77)(i) | TEXT | Information related to Section 2(77)(i) |
| Section_2(77)(ii) | TEXT | Information related to Section 2(77)(ii) |
| Section_2(77)(iii) | REAL | Information related to Section 2(77)(iii) |
| Father | TEXT | Father's information |
| Mother | TEXT | Mother's information |
| Son | TEXT | Son's information |
| Son's_Wife | TEXT | Son's wife information |
| Daughter | TEXT | Daughter's information |
| Daughter's_husband | TEXT | Daughter's husband information |
| Brother | TEXT | Brother's information |
| Sister | TEXT | Sister's information |

## Data Statistics
- **Total Records**: 60 directors
- **Fields per Record**: 12 family relationship fields

## Key Observations
1. The data contains family relationship information for directors as required by regulatory compliance (likely Section 2(77) of relevant regulations)
2. Information includes relatives such as father, mother, son, daughter, brother, and sister
3. Some fields contain complex information including HUF (Hindu Undivided Family) details
4. Some entries have "None" or "N.A." values indicating unavailable information
5. Certain fields contain multiline information (e.g., multiple family members listed)

## Database Location
The SQLite database file is located at:
```
c:\Users\ABHI MANE\Downloads\Aegis_New\Aegis_21-11-2025\backend\public\Director_Family_Information.db
```

## Usage
The database can be accessed using any SQLite client or through Python with the sqlite3 module:

```python
import sqlite3
conn = sqlite3.connect('Director_Family_Information.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM Sheet1")
results = cursor.fetchall()
```

## Notes
- All column names have been sanitized by replacing spaces with underscores
- The database preserves all original data from the Excel sheet
- NULL values in the database represent missing information from the original Excel file