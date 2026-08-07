const fs = require('fs');

// Read the original file with utf16le encoding
const orig = fs.readFileSync('C:\\Users\\Cogni\\.gemini\\antigravity\\scratch\\EmployeeComplianceLedger_original.txt', 'utf16le');
const origLines = orig.split(/\r?\n/);
// The exact missing block of code. Let's find it dynamically in the original string!
const blockStartStr = '<div style={{ flex: 1, padding: "20px 24px", overflowY: "auto", maxHeight: "520px" }}>';
const blockEndStr = '      {/* ── Tab 2: RAW SERVICENOW FEED (Flat ledger list) ── */}';

const origStartIdx = orig.indexOf(blockStartStr);
const origEndIdx = orig.indexOf(blockEndStr);

if (origStartIdx === -1 || origEndIdx === -1) {
    console.log("Could not find block bounds in original file");
    process.exit(1);
}

const cleanBlock = orig.substring(origStartIdx, origEndIdx);

// Now read the corrupted target file
const targetPath = 'C:\\Cognitbotz\\AEGIS_Servicenow\\Frontend\\src\\pages\\InsiderTrading\\EmployeeComplianceLedger.tsx';
const target = fs.readFileSync(targetPath, 'utf8');

// The corrupted block was inserted directly after:
const insertPointStr = 'onClick={() => setDetailTab("DECLARATION")}';
const insertPointStart = target.indexOf(insertPointStr);

// Find the start of the corruption
// It should be on the next line after the closing </div> of the buttons.
// Let's just find the first null byte.
const nullByteIdx = target.indexOf('\0', insertPointStart);

// Let's find the line start of the corruption.
let corruptionStart = nullByteIdx;
while (corruptionStart > 0 && target[corruptionStart - 1] !== '\n') {
    corruptionStart--;
}

// Find the end of the corruption by searching for the Tab 2 comment (which might be the modified one without "(Flat ledger list)")
const targetEndStr = '{/* ── Tab 2: RAW SERVICENOW FEED ── */}';
let corruptionEnd = target.indexOf(targetEndStr);
while (corruptionEnd > 0 && target[corruptionEnd - 1] !== '\n') {
    corruptionEnd--;
}

if (nullByteIdx !== -1 && corruptionEnd !== -1) {
    const newContent = target.substring(0, corruptionStart) + cleanBlock + target.substring(corruptionEnd);
    fs.writeFileSync(targetPath, newContent);
    console.log("Successfully replaced corrupted block with clean block!");
} else {
    console.log("Could not find corruption bounds in target file");
}
