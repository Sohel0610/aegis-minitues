import os

form_file = "Frontend/src/pages/minutes-preparation/FormBasedGenerator.tsx"
output_dir = "Frontend/src/pages/minutes-preparation/components/form-steps"

# First, let's pull from git to get the original FormBasedGenerator.tsx back!
os.system("git checkout Frontend/src/pages/minutes-preparation/FormBasedGenerator.tsx")

with open(form_file, "r") as f:
    lines = f.readlines()

common_imports = """import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CheckCircle, Upload, Trash, Plus } from 'lucide-react';
import { Textarea } from "@/components/ui/textarea";
import PlaceSelector from '@/components/PlaceSelector';
import MultiDirectorSelector from '@/components/MultiDirectorSelector';

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
}
"""

step_info = [
    ("Step0TemplateCompany", 502, 708),
    ("Step1MeetingDetails", 709, 743),
    ("Step2Attendance", 744, 845),
    ("Step3LegalDisclosures", 846, 955),
    ("Step4AuditorPayment", 956, 1008),
    ("Step5FinancialStatements", 1009, 1139),
    ("Step6AGMDetails", 1140, 1274),
    ("Step7SignOffDetails", 1275, 1341),
    ("Step8Resolutions", 1342, 1431),
    ("Step9Review", 1432, 1532)
]

for step_name, start, end in step_info:
    step_lines = lines[start-1:end]
    
    # Strip the conditional wrapper. E.g. `{currentStep === 0 && (`
    if step_lines and "&&" in step_lines[0]:
        step_lines[0] = step_lines[0].split("(", 1)[1] if "(" in step_lines[0] else ""
    
    # Remove the trailing `)}`
    if step_lines and step_lines[-1].strip() == ")}":
        step_lines = step_lines[:-1]
    elif step_lines and ")}" in step_lines[-1]:
        step_lines[-1] = step_lines[-1].replace(")}", "")

    content = "".join(step_lines)
    
    file_content = f"{common_imports}\n\nexport const {step_name}: React.FC<StepProps> = (props) => {{\n"
    file_content += "  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid } = props;\n\n"
    file_content += f"  return (\n    <>\n{content}    </>\n  );\n}};\n"
    
    with open(f"{output_dir}/{step_name}.tsx", "w") as out_f:
        out_f.write(file_content)

print("Steps re-extracted cleanly.")
