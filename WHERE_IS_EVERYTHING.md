# 📍 Where Is Everything? - Visual Guide

## Quick Answer to "Where is add and delete company?"

---

## 🎯 **ADD COMPANY BUTTON**

### Location:
```
Page: /minutes-preparation → Select Business Unit → Company List

Position: Top-right, next to the filter dropdown

Visual Layout:
┌──────────────────────────────────────────────────────────────┐
│ [← Back] Select Entity under AEL                             │
│                                                               │
│                    [+ Add Company] [Filter ▼] [🔍 Search...] │ ← HERE!
└──────────────────────────────────────────────────────────────┘
```

### What It Looks Like:
```
Button Style:
┌──────────────────┐
│ + Add Company    │  ← Blue button with plus icon
└──────────────────┘
```

### When You Click It:
Opens a modal form with these fields:
- Company Name (required)
- Company Code (optional)
- CIN Number
- Company Type (dropdown)
- Secretary Name
- Status (dropdown)

---

## 🗑️ **DELETE COMPANY ICON**

### Location:
```
Page: /minutes-preparation → Select Business Unit → Company List

Position: On each company card (RIGHT SIDE, appears on HOVER)

Visual Layout:
┌────────────────────────────────────────┐
│ [Logo] AAA              [🗑️] →        │ ← Trash icon (hover to see)
│        ADANI AEROSPACE AND DEFENCE...  │
│        CS: Kuntal Chandya              │
└────────────────────────────────────────┘
```

### What It Looks Like:

**Default (NOT hovering):**
```
┌────────────────────────────────┐
│ [Logo] AAA                 →   │  ← No trash icon visible
│        ADANI AEROSPACE...      │
└────────────────────────────────┘
```

**On Hover (trash icon appears):**
```
┌──────────────────────────────────┐
│ [Logo] AAA         [🗑️] →       │  ← Trash icon visible! (red)
│        ADANI AEROSPACE...        │
└──────────────────────────────────┘
```

### When You Click It:
Shows confirmation prompt:
```
⚠️ DELETE COMPANY?

Are you sure you want to delete:
ADANI GREEN ENERGY LIMITED

This will permanently delete:
• Company record
• All meetings and minutes
• All attendance records
• All directors
• All related data

This action CANNOT be undone!

Type "DELETE" to confirm: _____
```

---

## 🎬 **Step-by-Step User Journey**

### To Add a Company:

**Step 1:** Go to Minutes Preparation
```
http://localhost:5173/minutes-preparation
```

**Step 2:** Select a Business Unit
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ AEL         │  │ AIR         │  │ CEM         │
│ RENEWABLES  │  │ AIRPORTS    │  │ CEMENT      │
└─────────────┘  └─────────────┘  └─────────────┘
        ↑
     Click here
```

**Step 3:** Find the Add Button (Top-right)
```
┌──────────────────────────────────────────────────┐
│ [← Back] Select Entity under AEL                 │
│                                                   │
│              [+ Add Company] [Filter ▼] [Search] │ ← Click here!
└──────────────────────────────────────────────────┘
```

**Step 4:** Fill the Form
```
┌────────────────────────────────────┐
│  Add New Company                   │
│  Add a new company under AEL       │
│                                    │
│  Company Name *                    │
│  ┌──────────────────────────────┐ │
│  │ ADANI SOLAR POWER LIMITED    │ │ ← Type here
│  └──────────────────────────────┘ │
│                                    │
│  Company Code                      │
│  ┌──────────────────────────────┐ │
│  │ ASPL                         │ │ ← Or leave empty
│  └──────────────────────────────┘ │
│                                    │
│  ... more fields ...               │
│                                    │
│  [Cancel]  [Add Company]           │ ← Click to submit
└────────────────────────────────────┘
```

**Step 5:** Success!
```
✅ Company "ADANI SOLAR POWER LIMITED" added successfully!

New company appears in the list:
┌────────────────────────────┐
│ ASPL                    →  │  ← Your new company!
│ ADANI SOLAR POWER LIMITED  │
└────────────────────────────┘
```

---

### To Delete a Company:

**Step 1:** Go to the company list (same as above)

**Step 2:** Hover over ANY company card
```
Before hover:
┌────────────────────────────┐
│ AAA                     →  │
│ ADANI AEROSPACE...         │
└────────────────────────────┘

After hover:
┌──────────────────────────────┐
│ AAA            [🗑️] →       │ ← Trash icon appears!
│ ADANI AEROSPACE...           │
└──────────────────────────────┘
```

**Step 3:** Click the Trash Icon
```
Confirmation appears:
┌──────────────────────────────────────┐
│ ⚠️ DELETE COMPANY?                   │
│                                      │
│ Are you sure you want to delete:    │
│ ADANI GREEN ENERGY LIMITED           │
│                                      │
│ This will permanently delete:        │
│ • Company record                     │
│ • All meetings and minutes           │
│ • All attendance records             │
│ • All directors                      │
│ • All related data                   │
│                                      │
│ This action CANNOT be undone!        │
│                                      │
│ Type "DELETE" to confirm:            │
│ ┌────────────────────────────────┐  │
│ │ DELETE                         │  │ ← Type exactly "DELETE"
│ └────────────────────────────────┘  │
│                                      │
│ [Cancel]  [OK]                       │
└──────────────────────────────────────┘
```

**Step 4:** Success!
```
✅ Company deleted successfully!

Deleted 245 related records.

The company disappears from the list immediately.
```

---

## 🔍 **FILTER DROPDOWN**

### Location:
```
Same page as Add button, between Add button and Search

┌──────────────────────────────────────────────────┐
│ [+ Add Company] [Filter ▼] [🔍 Search...]       │
│                      ↑                           │
│                   HERE!                          │
└──────────────────────────────────────────────────┘
```

### What It Looks Like:
```
Closed:
┌──────────────────────┐
│ All Meetings      ▼  │
└──────────────────────┘

Opened:
┌──────────────────────────────┐
│ All Meetings              ✓  │
│ Board Meeting                │
│ Audit Committee              │
│ NRC                          │
│ SRC                          │
│ CSR Committee                │
│ Risk Committee               │
│ AGM                          │
│ EGM                          │
└──────────────────────────────┘
```

### When You Select "Board Meeting":
Companies filter to show only those with Board Meetings, and cards show statistics:

```
BEFORE (Filter: All Meetings):
┌────────────────────────────┐
│ AAA                     →  │
│ ADANI AEROSPACE...         │
│ CS: Kuntal Chandya         │
└────────────────────────────┘

AFTER (Filter: Board Meeting):
┌────────────────────────────────┐
│ AAA                         →  │
│ ADANI AEROSPACE...             │
│ CS: Kuntal Chandya             │
├────────────────────────────────┤
│ Total    Last      Next        │ ← Statistics appear!
│   86     86TH      87TH        │
│ 📅 Last: Jan 28, 2025          │
└────────────────────────────────┘
```

---

## 📱 **Mobile View**

### On Mobile (Screen < 640px):

```
┌──────────────────────────┐
│ [← Back] Select Entity   │
│                          │
│ [+ Add Company]          │ ← Full width
│ [Filter: All Meetings ▼] │ ← Full width
│ [🔍 Search...]           │ ← Full width
│                          │
│ ┌────────────────────┐   │
│ │ AAA           [🗑️]│   │ ← Cards stack
│ │ ADANI AERO...     │   │
│ └────────────────────┘   │
│                          │
│ ┌────────────────────┐   │
│ │ ADA           [🗑️]│   │
│ │ ADANI AGRI...     │   │
│ └────────────────────┘   │
└──────────────────────────┘
```

---

## 🎨 **Color Coding**

### Add Company Button:
- **Background:** Blue (#2563EB)
- **Hover:** Darker Blue (#1D4ED8)
- **Text:** White
- **Icon:** White Plus (+)

### Delete Icon:
- **Background:** Light Red (#FEF2F2)
- **Border:** Red (#FEE2E2)
- **Icon:** Red (#DC2626)
- **Hover Background:** Solid Red (#DC2626)
- **Hover Icon:** White

### Filter Dropdown:
- **Background:** White
- **Border:** Light Gray (#E2E8F0)
- **Text:** Dark Gray (#334155)
- **Selected:** Blue checkmark

### Statistics:
- **Total Count:** Black (#0F172A)
- **Last Meeting:** Blue (#0057B8)
- **Next Meeting:** Green (#10B981)
- **Date:** Gray (#64748B)

---

## ⚠️ **Common Issues & Solutions**

### "I don't see the Add button!"
**Solution:**
1. Make sure you've selected a Business Unit first
2. Scroll to the top of the page
3. Look at the TOP-RIGHT corner
4. It's next to the Filter dropdown

### "I don't see the Delete icon!"
**Solution:**
1. You need to HOVER your mouse over a company card
2. The trash icon appears ONLY when hovering
3. It's on the RIGHT side of the card, before the arrow
4. Try moving your mouse slowly over the card

### "The filter doesn't show statistics!"
**Solution:**
1. Statistics only show when a SPECIFIC meeting type is selected
2. "All Meetings" does NOT show statistics
3. Select "Board Meeting" or any other specific type
4. Statistics appear at the bottom of each card

### "Delete confirmation doesn't work!"
**Solution:**
1. You must type exactly: **DELETE** (all caps)
2. Not "delete" (lowercase) ❌
3. Not "Delete" (mixed case) ❌
4. Must be: **DELETE** (all caps) ✅
5. Then click OK

---

## 🧪 **Quick Test Checklist**

### Test Add Company:
- [ ] Navigate to /minutes-preparation
- [ ] Click a Business Unit
- [ ] See "+ Add Company" button at top-right
- [ ] Click it
- [ ] Modal opens
- [ ] Fill company name
- [ ] Click "Add Company"
- [ ] See success message
- [ ] New company appears in list

### Test Delete Company:
- [ ] Go to company list
- [ ] Hover over any company card
- [ ] See trash icon appear (red)
- [ ] Click trash icon
- [ ] See confirmation prompt
- [ ] Type "DELETE"
- [ ] Click OK
- [ ] See success message
- [ ] Company disappears from list

### Test Filter:
- [ ] Go to company list
- [ ] Click filter dropdown
- [ ] Select "Board Meeting"
- [ ] See only companies with Board Meetings
- [ ] See statistics on each card (Total, Last, Next)
- [ ] Select "All Meetings"
- [ ] See all companies without statistics

---

## 📍 **Exact File Locations**

### Frontend Code:
```
File: Frontend/src/pages/minutes-preparation/MinutesGenerator.tsx

Line ~86:    State for meetingTypeFilter
Line ~89:    State for showAddCompanyModal
Line ~98:    Handler: handleAddCompany()
Line ~142:   Handler: handleDeleteCompany()
Line ~372:   UI: Add Company Button
Line ~382:   UI: Filter Dropdown
Line ~422:   UI: Company Cards
Line ~463:   UI: Delete Trash Icon
Line ~1075:  UI: Add Company Modal
```

### Backend Code:
```
File: Backend/aegis_backend/routes/minutes.py

Line ~50:    GET /companies with filter
Line ~120:   POST /companies (create)
Line ~180:   PUT /companies (update)
Line ~240:   DELETE /companies (delete)
Line ~310:   GET /audit-logs
Line ~380:   GET /companies/{id}/audit-history
```

### Audit Logger:
```
File: Backend/aegis_backend/utils/audit_logger.py

Line ~1:     Audit logging utility
Line ~10:    log_audit() function
Line ~40:    Database insert logic
```

---

## 🎯 **One-Sentence Summary**

**"The '+ Add Company' button is at the top-right next to the filter, and the delete trash icon appears when you hover over any company card."**

---

## 📸 **Screenshots Reference**

### Full Page View:
```
┌─────────────────────────────────────────────────────────────┐
│ AEGIS MINUTES GENERATOR                    [User Menu ▼]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [← Back] Select Entity under AEL                            │
│                                                              │
│                 [+ Add Company] [Filter ▼] [🔍 Search...]   │ ← TOP BAR
│                                                              │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│ │ AAA      [🗑️]→│  │ ADA      [🗑️]→│  │ AEL      [🗑️]→│    │
│ │ ADANI AERO... │  │ ADANI AGRI... │  │ ADANI ENG...  │    │
│ │ CS: K. Chan.. │  │ CS: R. Shah   │  │ CS: M. Patel  │    │
│ │───────────────│  │───────────────│  │───────────────│    │
│ │ Total: 86     │  │ Total: 42     │  │ Total: 65     │    │ ← STATS
│ │ Last: 86TH    │  │ Last: 42ND    │  │ Last: 65TH    │    │
│ │ Next: 87TH    │  │ Next: 43RD    │  │ Next: 66TH    │    │
│ └───────────────┘  └───────────────┘  └───────────────┘    │
│                                                              │
│ Page 1 of 3                                      [Next >]   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**✅ Everything is in place and working!**

Now you know exactly where to find the Add and Delete company features! 🎉
