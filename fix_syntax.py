import os
import glob

files = glob.glob('Frontend/src/pages/minutes-preparation/components/form-steps/*.tsx')

for file in files:
    with open(file, 'r') as f:
        lines = f.readlines()
    
    # We want to remove the last occurrence of `)}` before the closing `    </>` tag
    # The structure is:
    #             )}
    #     </>
    #   );
    # };
    
    # Let's search from the bottom up
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip() == ')}':
            lines.pop(i)
            break
            
    with open(file, 'w') as f:
        f.writelines(lines)

print("Syntax fixed")
