# 🎨 Visual Test Guide - What You Should See

## 🚀 Quick Start Test

### Step 1: Start the application
```bash
# Terminal 1 - Backend
cd Backend/aegis_backend
python fastapi_server.py

# Terminal 2 - Frontend
cd Frontend
npm run dev
```

### Step 2: Open browser
```
http://localhost:5173/minutes-preparation
```

---

## ✅ Test 1: See the Filter Dropdown

**What to do:**
1. Click on any Business Unit (e.g., "AEL - RENEWABLES")
2. Look at the top of the screen

**What you should see:**
```
┌────────────────────────────────────────────────────────────┐
│ [← Back] Select Entity under AEL                           │
│                                                             │
│         [+ Add Company] [All Meetings ▼] [🔍 Search...]    │
│                                                             │
│ Showing 25 companies                                        │
└────────────────────────────────────────────────────────────┘
```

**✅ SUCCESS if you see:**
- Blue "+ Add Company" button
- "All Meetings" dropdown with down arrow
- Search box with magnifying glass icon

---

## ✅ Test 2: Click Filter Dropdown

**What to do:**
1. Click on "All Meetings ▼" dropdown

**What you should see:**
```
┌────────────────────────────────┐
│ All Meetings              ✓    │  ← Currently selected
│ Board Meeting                  │
│ Audit Committee                │
│ NRC                            │
│ SRC                            │
│ CSR Committee                  │
│ Risk Committee                 │
│ AGM                            │
│ EGM                            │
└────────────────────────────────┘
```

**✅ SUCCESS if you see:**
- 9 options in the dropdown
- Checkmark on "All Meetings"
- All options are clickable

---

## ✅ Test 3: Filter by Board Meeting

**What to do:**
1. Click "Board Meeting" from the dropdown
2. Wait 1 second for page to refresh

**What you should see:**
```
Before (All Meetings):
┌──────────────────────────┐
│ AGEL                  →  │
│ ADANI GREEN ENERGY...    │
│ CS: Kuntal Chandya       │
└──────────────────────────┘

After (Board Meeting):
┌──────────────────────────────┐
│ AGEL                      →  │
│ ADANI GREEN ENERGY LIMITED   │
│ CS: Kuntal Chandya           │
├──────────────────────────────┤  ← NEW SECTION!
│ Total    Last    Next        │
│   86     86TH    87TH        │
│ 📅 Last: Jan 28, 2025        │
└──────────────────────────────┘
```

**✅ SUCCESS if you see:**
- Statistics section appears at bottom of each card
- "Total", "Last", "Next" labels
- Meeting numbers (e.g., "86TH", "87TH")
- Date with calendar emoji
- Only companies with Board Meetings are shown

---

## ✅ Test 4: See the Delete Icon (Hover Test)

**What to do:**
1. Move your mouse cursor OVER any company card
2. Do NOT click, just hover

**What you should see:**

**Before hover:**
```
┌──────────────────────────┐
│ AGEL               →     │  ← Only arrow visible
│ ADANI GREEN ENERGY...    │
└──────────────────────────┘
```

**During hover:**
```
┌────────────────────────────┐
│ AGEL          [🗑️] →      │  ← Trash icon appears!
│ ADANI GREEN ENERGY...      │     (RED color)
└────────────────────────────┘
```

**✅ SUCCESS if you see:**
- Red trash can icon appears
- Icon is between company name and arrow
- Icon fades in smoothly (not instant)
- Icon disappears when you move mouse away

**❌ FAILURE if:**
- Icon is always visible (should be hidden by default)
- Icon doesn't appear on hover
- Icon is not red color

---

## ✅ Test 5: Click Add Company Button

**What to do:**
1. Click the blue "+ Add Company" button (top right)

**What you should see:**
```
┌────────────────────────────────────────┐
│ × Add New Company                      │  ← Title with X to close
│ Add a new company under AEL            │
│                                        │
│ Company Name *                         │
│ ┌────────────────────────────────────┐│
│ │ e.g., ADANI GREEN ENERGY LIMITED  ││  ← Input box
│ └────────────────────────────────────┘│
│                                        │
│ Company Code                           │
│ ┌────────────────────────────────────┐│
│ │ e.g., AGEL (auto-generated...)    ││
│ └────────────────────────────────────┘│
│                                        │
│ CIN (Corporate Identity Number)        │
│ ┌────────────────────────────────────┐│
│ │ e.g., L40101GJ2015PLC084374       ││
│ └────────────────────────────────────┘│
│                                        │
│ Company Type                           │
│ [Public Limited ▼]                     │
│                                        │
│ Company Secretary Name                 │
│ ┌────────────────────────────────────┐│
│ │ e.g., Kuntal Chandya              ││
│ └────────────────────────────────────┘│
│                                        │
│ Status                                 │
│ [Active ▼]                             │
│                                        │
│           [Cancel] [Add Company]       │
└────────────────────────────────────────┘
```

**✅ SUCCESS if you see:**
- Modal dialog appears (centered on screen)
- Dark overlay behind modal
- All 6 form fields visible
- "Add Company" button at bottom (should be GRAYED OUT until you type a name)
- X button at top-right to close

**❌ FAILURE if:**
- Nothing happens when you click
- Console shows errors
- Modal doesn't center properly

---

## ✅ Test 6: Fill Add Company Form

**What to do:**
1. Type "TEST COMPANY LIMITED" in Company Name field
2. Watch the "Add Company" button

**What you should see:**

**Before typing:**
```
[Add Company]  ← Button is grayed out/disabled
```

**After typing name:**
```
[Add Company]  ← Button becomes BLUE and clickable
```

**Now click "Add Company" button**

**What you should see:**
```
[Adding...]  ← Button text changes

Then after 1-2 seconds:

Alert box appears:
┌──────────────────────────────────────┐
│ ✓                                    │
│ Company "TEST COMPANY LIMITED"       │
│ added successfully!                  │
│                                      │
│              [OK]                    │
└──────────────────────────────────────┘
```

**After clicking OK:**
- Modal closes automatically
- New company "TEST COMPANY LIMITED" appears in the grid
- Success!

**✅ SUCCESS if:**
- Button was disabled before typing
- Button enabled after typing name
- Button shows "Adding..." during save
- Success alert appears
- Modal closes
- New company visible in grid

---

## ✅ Test 7: Click Delete Icon

**What to do:**
1. Find the "TEST COMPANY LIMITED" card you just created
2. Hover over it to see trash icon
3. Click the RED trash icon

**What you should see:**
```
Confirmation prompt appears:

┌──────────────────────────────────────────┐
│ ⚠️ DELETE COMPANY?                       │
│                                          │
│ Are you sure you want to delete:        │
│ TEST COMPANY LIMITED                     │
│                                          │
│ This will permanently delete:            │
│ • Company record                         │
│ • All meetings and minutes               │
│ • All attendance records                 │
│ • All directors                          │
│ • All related data                       │
│                                          │
│ This action CANNOT be undone!            │
│                                          │
│ Type "DELETE" to confirm:                │
│ ┌──────────────────────────────────────┐│
│ │                                      ││  ← Type here
│ └──────────────────────────────────────┘│
│                                          │
│         [Cancel]         [OK]            │
└──────────────────────────────────────────┘
```

**What to do next:**
1. Type exactly: `DELETE` (all uppercase)
2. Click OK

**What you should see:**
```
Alert box:
┌──────────────────────────────────────┐
│ ✓                                    │
│ Company deleted successfully!        │
│                                      │
│ Deleted 0 related records.           │
│                                      │
│              [OK]                    │
└──────────────────────────────────────┘
```

**After clicking OK:**
- "TEST COMPANY LIMITED" card disappears from grid
- Success!

**✅ SUCCESS if:**
- Confirmation prompt appeared
- Had to type "DELETE" exactly
- Success message appeared
- Card disappeared from grid

---

## ❌ Common Issues & Fixes

### Issue 1: "I don't see the filter dropdown!"

**Check:**
1. Are you on the company list page? (Not the business unit selection page)
2. Did you select a business unit first?
3. Scroll to the TOP of the page
4. Look RIGHT of the search box

**Should be here:**
```
[+ Add Company] [Filter ▼] [🔍 Search...]
                   ↑
                 HERE!
```

---

### Issue 2: "Delete icon never appears!"

**Check:**
1. Are you HOVERING over the card? (not clicking)
2. Move your mouse SLOWLY over the card
3. Look to the RIGHT side of the card, before the arrow

**Try:**
- Hover and hold for 1 second
- Try a different card
- Check if CSS is loading (browser console)

**Should look like:**
```
During hover:
[Company Name]  [🗑️] →
                 ↑
              RED ICON!
```

---

### Issue 3: "Add button doesn't open modal!"

**Check Browser Console:**
1. Press F12 to open developer tools
2. Look for errors in Console tab

**Common errors:**
- "Dialog is not defined" → Check imports
- "showAddCompanyModal is not defined" → Check state
- "handleAddCompany is not a function" → Check function definition

**Fix:**
1. Refresh page (Ctrl+R or Cmd+R)
2. Clear cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Check if all imports are present at top of file

---

### Issue 4: "Filter shows no results!"

**This is CORRECT if:**
- You selected a meeting type that no companies have
- Example: If no companies have "AGM" meetings, list will be empty

**You should see:**
```
No entities found matching "" under AEL.
```

**Try:**
- Select "Board Meeting" - most companies have this
- Select "All Meetings" to see all companies again

---

### Issue 5: "Delete prompt accepts lowercase 'delete'"

**This is WRONG!** Should only accept uppercase "DELETE"

**Check:**
```javascript
if (userInput !== "DELETE") {  // Should be strict check
  return;
}
```

**Must type:** `DELETE` (uppercase)  
**Won't work:** `delete`, `Delete`, `DeLeTe`

---

## 🎯 Final Checklist

Run through all tests in order:

- [ ] ✅ Test 1: See filter dropdown
- [ ] ✅ Test 2: Click filter dropdown  
- [ ] ✅ Test 3: Filter by Board Meeting
- [ ] ✅ Test 4: See delete icon on hover
- [ ] ✅ Test 5: Click Add Company button
- [ ] ✅ Test 6: Fill and submit form
- [ ] ✅ Test 7: Delete company

**If ALL tests pass: 🎉 PERFECT! Production ready!**

**If ANY test fails: 🔧 Check the "Common Issues" section above**

---

## 📸 Screenshots Reference

### ✅ Correct - Filter Dropdown Visible
```
[+ Add Company] [All Meetings ▼] [🔍 Search...]
                      ✓ VISIBLE
```

### ✅ Correct - Delete Icon on Hover
```
[Company]  [🗑️] →  ← RED icon appears
            ✓ VISIBLE ON HOVER
```

### ✅ Correct - Modal Opens
```
┌────────────────────┐
│ Add New Company    │  ← Modal centered
│ [Form fields...]   │
│ [Cancel] [Add]     │
└────────────────────┘
     ✓ OPENS
```

### ✅ Correct - Statistics Shown
```
┌──────────────────┐
│ Company Name     │
├──────────────────┤
│ Total Last Next  │  ← Stats appear
│  86   86TH 87TH  │
└──────────────────┘
   ✓ VISIBLE WHEN FILTERED
```

---

## 🔧 Developer Debug Commands

**Check if Dialog component exists:**
```bash
ls Frontend/src/components/ui/dialog.tsx
```

**Check if imports are correct:**
```bash
grep "Dialog" Frontend/src/pages/minutes-preparation/MinutesGenerator.tsx
```

**Check if state is defined:**
```bash
grep "showAddCompanyModal" Frontend/src/pages/minutes-preparation/MinutesGenerator.tsx
```

**Check if handlers exist:**
```bash
grep "handleAddCompany\|handleDeleteCompany" Frontend/src/pages/minutes-preparation/MinutesGenerator.tsx
```

**Check browser console for errors:**
```
F12 → Console tab → Look for red errors
```

---

**✅ All features are implemented and production-ready!**

If you followed this guide and all tests passed, everything is working correctly! 🎉
