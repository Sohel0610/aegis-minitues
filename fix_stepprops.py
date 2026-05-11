import os
import glob

components_dir = "Frontend/src/pages/minutes-preparation/components/form-steps"

types_content = """import React from 'react';

export interface StepProps {
    formData: any;
    setFormData: React.Dispatch<React.SetStateAction<any>>;
    isOtherCompany?: boolean;
    setIsOtherCompany?: React.Dispatch<React.SetStateAction<boolean>>;
    companyPresets?: any[];
    isUploadingTemplate?: boolean;
    handleCustomTemplateUpload?: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
    resolutionTemplates?: any[];
    setResolutionTemplates?: React.Dispatch<React.SetStateAction<any[]>>;
    resTemplateName?: string;
    setResTemplateName?: React.Dispatch<React.SetStateAction<string>>;
    numberToOrdinal?: (num: number) => string;
    isStepValid?: () => boolean;
    toast?: any;
}
"""

with open(f"{components_dir}/types.ts", "w") as f:
    f.write(types_content)

files = glob.glob(f"{components_dir}/Step*.tsx")

for file in files:
    with open(file, "r") as f:
        content = f.read()
    
    # We want to replace the whole interface block
    start_str = "export interface StepProps {"
    end_str = "toast?: any;\n}"
    
    start_idx = content.find(start_str)
    end_idx = content.find(end_str)
    
    if start_idx != -1 and end_idx != -1:
        end_idx += len(end_str)
        # Check if the next line is empty or just whitespace and include it
        # Actually just replace the block with the import
        prefix = content[:start_idx]
        suffix = content[end_idx:]
        
        # ensure there is import React, though it should be at the top
        new_content = prefix + "import { StepProps } from './types';" + suffix
        with open(file, "w") as f:
            f.write(new_content)

print("StepProps extracted to types.ts")
