const fs = require('fs');
const orig = fs.readFileSync('C:\\Users\\Cogni\\.gemini\\antigravity\\scratch\\EmployeeComplianceLedger_original.txt', 'utf8').split(/\r?\n/);
// In EmployeeComplianceLedger_original.txt, the detail tab buttons are around line 487-488.
// The actual content starts around line 491 and goes down to 688.
const missingBlock = orig.slice(491, 688).join('\n');

const targetPath = 'C:\\Cognitbotz\\AEGIS_Servicenow\\Frontend\\src\\pages\\InsiderTrading\\EmployeeComplianceLedger.tsx';
let lines = fs.readFileSync(targetPath, 'utf8').split(/\r?\n/);
const idx = lines.findIndex(l => l.includes('Pre-clearance (') && l.includes('onClick={() => setDetailTab("PRECLEARANCE")}'));

if(idx !== -1) {
  // Insert after the tab buttons and the closing div of the buttons
  lines.splice(idx + 3, 0, missingBlock);
  fs.writeFileSync(targetPath, lines.join('\n'));
  console.log('Fixed successfully');
} else {
  console.log('Could not find insertion point');
}
