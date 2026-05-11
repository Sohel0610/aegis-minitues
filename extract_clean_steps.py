import os

form_file = "original_form.tsx"
output_dir = "Frontend/src/pages/minutes-preparation/components/form-steps"
os.makedirs(output_dir, exist_ok=True)

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
    toast?: any;
}
"""

step_info = [
    ("Step0TemplateCompany", 535, 741),
    ("Step1MeetingDetails", 742, 776),
    ("Step2Attendance", 777, 878),
    ("Step3LegalDisclosures", 879, 988),
    ("Step4AuditorPayment", 989, 1041),
    ("Step5FinancialStatements", 1042, 1172),
    ("Step6AGMDetails", 1173, 1307),
    ("Step7SignOffDetails", 1308, 1374),
    ("Step8Resolutions", 1375, 1464),
    ("Step9Review", 1465, 1565) # I am estimating 1465-1565 for step 9
]

# Let's adjust step 9 end line: we just find the `{/* Navigation */}` comment
end_step_9 = len(lines)
for i, line in enumerate(lines):
    if "{/* Navigation */}" in line:
        end_step_9 = i - 1
        break
step_info[-1] = ("Step9Review", 1465, end_step_9)

for step_name, start, end in step_info:
    step_lines = lines[start-1:end]
    
    # Strip the conditional wrapper
    if step_lines and "&&" in step_lines[0]:
        step_lines[0] = step_lines[0].split("(", 1)[1] if "(" in step_lines[0] else ""
    
    # Remove the trailing `)}`
    if step_lines and step_lines[-1].strip() == ")}":
        step_lines = step_lines[:-1]
    elif step_lines and ")}" in step_lines[-1]:
        step_lines[-1] = step_lines[-1].replace(")}", "")
    # Check one more line up if trailing `)}` is at the end of the previous line
    elif step_lines and len(step_lines) > 1 and step_lines[-2].strip() == ")}":
        step_lines = step_lines[:-2]

    content = "".join(step_lines)
    
    # Replace alerts with toasts
    content = content.replace('alert("Please upload a .docx file");', 'toast({title: "Invalid File", description: "Please upload a .docx file", variant: "destructive"});')
    content = content.replace('alert("Template uploaded successfully!");', 'toast({title: "Success", description: "Template uploaded successfully!"});')
    content = content.replace('alert(`Upload failed: ${err.detail || \'Unknown error\'}`);', 'toast({title: "Upload failed", description: err.detail || \'Unknown error\', variant: "destructive"});')
    content = content.replace('alert("Failed to upload template");', 'toast({title: "Error", description: "Failed to upload template", variant: "destructive"});')
    content = content.replace("alert(result.message || 'Document generated successfully!');", "toast({title: 'Success', description: result.message || 'Document generated successfully!'});")
    content = content.replace("alert(`Error generating document: ${error.message || 'Please try again.'}`);", "toast({title: 'Error generating document', description: error.message || 'Please try again.', variant: 'destructive'});")
    content = content.replace("alert('Resolution template saved successfully!');", "toast({title: 'Success', description: 'Resolution template saved successfully!'});")
    content = content.replace("alert('Failed to save resolution template');", "toast({title: 'Error', description: 'Failed to save resolution template', variant: 'destructive'});")

    file_content = f"{common_imports}\n\nexport const {step_name}: React.FC<StepProps> = (props) => {{\n"
    file_content += "  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;\n\n"
    file_content += f"  return (\n    <>\n{content}    </>\n  );\n}};\n"
    
    with open(f"{output_dir}/{step_name}.tsx", "w") as out_f:
        out_f.write(file_content)

print("Clean components extracted!")
