import re

form_file = "Frontend/src/pages/minutes-preparation/FormBasedGenerator.tsx"
with open(form_file, "r") as f:
    content = f.read()

# 1. Add imports at the top
import_block = """import { useToast } from "@/components/ui/use-toast";
import {
  Step0TemplateCompany, Step1MeetingDetails, Step2Attendance, Step3LegalDisclosures,
  Step4AuditorPayment, Step5FinancialStatements, Step6AGMDetails, Step7SignOffDetails,
  Step8Resolutions, Step9Review
} from './components/form-steps';
"""
content = content.replace("import Stepper from '@/components/Stepper';", import_block + "import Stepper from '@/components/Stepper';")

# 2. Add useToast inside the component
content = content.replace("const navigate = useNavigate();", "const navigate = useNavigate();\n  const { toast } = useToast();")

# 3. Add stepProps before return
step_props = """
  const stepProps = {
    formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets,
    isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates,
    setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal,
    isStepValid, toast
  };

  return (
"""
content = content.replace("  return (\n    <ProductDashboardLayout", step_props + "    <ProductDashboardLayout")

# 4. Replace the steps with components
replacement_jsx = """
            {currentStep === 0 && <Step0TemplateCompany {...stepProps} />}
            {currentStep === 1 && <Step1MeetingDetails {...stepProps} />}
            {currentStep === 2 && <Step2Attendance {...stepProps} />}
            {formData.template === 'Q1' && currentStep === 3 && <Step3LegalDisclosures {...stepProps} />}
            {formData.template === 'Q1' && currentStep === 4 && <Step4AuditorPayment {...stepProps} />}
            {formData.template === 'Q1' && currentStep === 5 && <Step5FinancialStatements {...stepProps} />}
            {formData.template === 'Q1' && currentStep === 6 && <Step6AGMDetails {...stepProps} />}
            {((formData.template === 'Q1' && currentStep === 7) || (formData.template !== 'Q1' && currentStep === 3)) && <Step7SignOffDetails {...stepProps} />}
            {((formData.template === 'Q1' && currentStep === 8) || (formData.template !== 'Q1' && currentStep === 4)) && <Step8Resolutions {...stepProps} />}
            {((formData.template === 'Q1' && currentStep === 9) || (formData.template !== 'Q1' && currentStep === 5)) && <Step9Review {...stepProps} />}
"""

start_idx = content.find("<form onSubmit={handleSubmit}>")
end_idx = content.find("{/* Navigation */}", start_idx)

if start_idx != -1 and end_idx != -1:
    prefix = content[:start_idx + len("<form onSubmit={handleSubmit}>")]
    suffix = content[end_idx:]
    content = prefix + replacement_jsx + "\n            " + suffix
else:
    print("Could not find start or end tags")

# 5. Fix alerts -> toast in the remaining handlers
content = content.replace('alert("Please upload a .docx file");', 'toast({title: "Invalid File", description: "Please upload a .docx file", variant: "destructive"});')
content = content.replace('alert("Template uploaded successfully!");', 'toast({title: "Success", description: "Template uploaded successfully!"});')
content = content.replace('alert(`Upload failed: ${err.detail || \'Unknown error\'}`);', 'toast({title: "Upload failed", description: err.detail || \'Unknown error\', variant: "destructive"});')
content = content.replace('alert("Failed to upload template");', 'toast({title: "Error", description: "Failed to upload template", variant: "destructive"});')
content = content.replace("alert(result.message || 'Document generated successfully!');", "toast({title: 'Success', description: result.message || 'Document generated successfully!'});")
content = content.replace("alert(`Error generating document: ${error.message || 'Please try again.'}`);", "toast({title: 'Error generating document', description: error.message || 'Please try again.', variant: 'destructive'});")
content = content.replace("alert('Resolution template saved successfully!');", "toast({title: 'Success', description: 'Resolution template saved successfully!'});")
content = content.replace("alert('Failed to save resolution template');", "toast({title: 'Error', description: 'Failed to save resolution template', variant: 'destructive'});")

with open(form_file, "w") as f:
    f.write(content)

print("Rewrote FormBasedGenerator successfully.")
