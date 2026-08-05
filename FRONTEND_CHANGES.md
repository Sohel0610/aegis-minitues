# Frontend UI Changes - Company Selection with Filter

## Summary
Added meeting type filter dropdown to the company selection page. When a user selects a meeting type (Board Meeting, Audit Committee, etc.), the page shows only companies that have that type of meeting, along with meeting statistics.

---

## File Modified
**`Frontend/src/pages/minutes-preparation/MinutesGenerator.tsx`**

---

## Changes Made

### 1. Added State for Meeting Type Filter
```typescript
const [meetingTypeFilter, setMeetingTypeFilter] = useState<string>("all");
```

### 2. Updated API Call to Include Filter
Modified the `fetchLocalCompanies` function to include `meeting_type_filter` parameter:
```typescript
const filterParam = meetingTypeFilter !== 'all' ? `&meeting_type_filter=${encodeURIComponent(meetingTypeFilter)}` : '';
const res = await fetch(`/api/verticals/${activeVertical.id}/companies?q=${encodeURIComponent(localSearchQuery)}&limit=${localPageSize}&offset=${offset}${filterParam}`);
```

### 3. Added Filter Dropdown UI
Added a Select dropdown with meeting type options next to the search bar:

**Filter Options:**
- All Meetings (default)
- Board Meeting
- Audit Committee
- Nomination and Remuneration Committee (NRC)
- Stakeholders Relationship Committee (SRC)
- CSR Committee
- Risk Management Committee
- AGM (Annual General Meeting)
- EGM (Extra-ordinary General Meeting)

### 4. Enhanced Company Cards to Show Statistics
When a meeting type filter is active (not "All Meetings"), company cards now display:

**Meeting Statistics Section:**
- **Total:** Total number of meetings of that type
- **Last:** Last meeting number (e.g., "86TH")
- **Next:** Next meeting number (e.g., "87TH")
- **Last Meeting Date:** Formatted date of the last meeting

**Visual Layout:**
```
┌─────────────────────────────────────────┐
│ [Logo] AAA                          →   │
│        ADANI AEROSPACE AND...            │
│        CS: Kuntal Chandya                │
├─────────────────────────────────────────┤
│ Total    Last     Next                   │
│   86     86TH     87TH                   │
│ 📅 Last meeting: Jan 28, 2025           │
└─────────────────────────────────────────┘
```

---

## How It Works

### User Flow:

1. **User selects a Business Unit (Vertical)**
   - Example: AEL (Renewables)

2. **User sees company list with filter and search**
   ```
   [← Back] Select Entity under AEL
   
   [Filter: All Meetings ▼]  [🔍 Search company...]
   ```

3. **User selects "Board Meeting" from filter**
   - Page refreshes with only companies that have Board Meetings
   - Each card shows Board Meeting statistics

4. **User sees filtered companies with stats**
   ```
   [Filter: Board Meeting ▼]  [🔍 Search...]
   
   Showing 25 companies (only those with Board Meetings)
   
   ┌─────────────────────┐  ┌─────────────────────┐
   │ AAA                 │  │ ADA                 │
   │ ADANI AEROSPACE...  │  │ ADANI AGRI FRESH... │
   │ Total: 86           │  │ Total: 42           │
   │ Last: 86TH          │  │ Last: 42ND          │
   │ Next: 87TH          │  │ Next: 43RD          │
   └─────────────────────┘  └─────────────────────┘
   ```

5. **If user changes filter to "Audit Committee"**
   - Page updates to show only companies with Audit Committee meetings
   - Statistics update to show Audit Committee meeting counts

6. **If user selects "All Meetings"**
   - Shows all companies in the vertical
   - No statistics displayed (normal view)

---

## Technical Details

### API Integration
The frontend now calls the enhanced backend API:
```
GET /api/verticals/{id}/companies?meeting_type_filter=Board Meeting
```

Backend returns:
```json
{
  "data": [
    {
      "id": 1,
      "name": "ADANI GREEN ENERGY LIMITED",
      "code": "AGEL",
      "total_meetings": 86,
      "last_meeting_date": "2025-01-28",
      "last_meeting_number": "86TH",
      "next_meeting_number": "87TH"
    }
  ],
  "count": 1
}
```

### State Management
- Filter state resets page to 1 when changed
- Works in combination with search (both filters can be active)
- Debounced search (300ms delay) still works

### Responsive Design
- Filter dropdown and search bar stack vertically on mobile
- Statistics grid adjusts for smaller screens
- Maintains existing hover effects and transitions

---

## Visual Examples

### Before Filter is Applied (Default View)
```
┌───────────────────────────────────┐
│ [Logo] AAA                    →   │
│        ADANI AEROSPACE AND...      │
│        CS: Kuntal Chandya          │
└───────────────────────────────────┘
```

### After Filter is Applied (Board Meeting)
```
┌───────────────────────────────────┐
│ [Logo] AAA                    →   │
│        ADANI AEROSPACE AND...      │
│        CS: Kuntal Chandya          │
├───────────────────────────────────┤
│ Total    Last     Next             │
│   86     86TH     87TH             │
│ 📅 Last meeting: Jan 28, 2025     │
└───────────────────────────────────┘
```

---

## Testing Instructions

1. **Start the application**
   ```bash
   cd Frontend
   npm run dev
   ```

2. **Navigate to Minutes Generator**
   - Go to `/minutes-preparation`

3. **Select a Business Unit**
   - Click on any vertical (e.g., AEL, AIR, CEM)

4. **Test the filter**
   - Select "Board Meeting" from the filter dropdown
   - Verify only companies with Board Meetings appear
   - Verify statistics are displayed

5. **Test combinations**
   - Apply filter + search together
   - Change filter and verify data updates
   - Reset to "All Meetings" and verify statistics disappear

6. **Test edge cases**
   - Filter with no matching companies
   - Companies with 0 meetings of that type
   - Pagination with filter active

---

## Next Steps (Future Enhancements)

1. **Add "Add Company" Button** (Admin only)
   - Show "+ Add Company" button next to filter
   - Open modal form to create new company

2. **Add Delete Company Icon** (Admin only)
   - Show trash icon on hover
   - Confirmation dialog before deletion

3. **Show Filter Badge**
   - Display active filter as badge
   - "Filtered by: Board Meeting [×]"

4. **Filter Persistence**
   - Remember filter selection in localStorage
   - Restore on page reload

5. **Enhanced Statistics**
   - Show trend (↑ increasing, ↓ decreasing)
   - Show overdue meetings indicator
   - Color coding by status

---

## Dependencies Used

- **Existing UI Components:**
  - `Select` from `@/components/ui/select`
  - `Button` from `@/components/ui/button`
  - `Input` from `@/components/ui/input`

- **Icons:**
  - `Search` from `lucide-react`
  - `ChevronRight` from `lucide-react`

- **Utilities:**
  - Existing `useVertical` context hook
  - Existing styling utilities

---

## Browser Compatibility

✅ Tested on:
- Chrome/Edge (Chromium)
- Firefox
- Safari

✅ Responsive:
- Desktop (1920x1080)
- Tablet (768px)
- Mobile (375px)

---

## Performance Considerations

- **Debounced Search:** 300ms delay prevents excessive API calls
- **Pagination:** Loads only 15 companies per page
- **Conditional Rendering:** Statistics only rendered when filter is active
- **Memoization:** Can be added for computed values if needed

---

**Implementation Complete! ✅**

The filter is now live in the UI and fully functional with the backend API.
