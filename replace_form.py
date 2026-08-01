import re

form_file = "Frontend/src/pages/minutes-preparation/FormBasedGenerator.tsx"

with open(form_file, "r") as f:
    content = f.read()

import_stmt = """import {
  Step0TemplateCompany,
  Step1MeetingDetails,
  Step2Attendance,
  Step3LegalDisclosures,
  Step4AuditorPayment,
  Step5FinancialStatements,
  Step6AGMDetails,
  Step7SignOffDetails,
  Step8Resolutions,
  Step9Review
} from './components/form-steps';
"""
lines = content.split('\n')
lines.insert(16, import_stmt)
content = '\n'.join(lines)

step_props_stmt = """
  const stepProps = {
    formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets,
    isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates,
    setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal,
    isStepValid
  };

  return (
"""
content = content.replace("  return (\n    <ProductDashboardLayout", step_props_stmt + "    <ProductDashboardLayout")

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
if start_idx != -1:
    nav_idx = content.find("{/* Navigation Buttons */}", start_idx)
    if nav_idx != -1:
        prefix = content[:start_idx + len("<form onSubmit={handleSubmit}>")]
        suffix = content[nav_idx:]
        content = prefix + replacement_jsx + "\n            " + suffix

with open(form_file, "w") as f:
    f.write(content)

print("FormBasedGenerator updated with isStepValid!")
