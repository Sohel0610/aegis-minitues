import React from 'react';

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
