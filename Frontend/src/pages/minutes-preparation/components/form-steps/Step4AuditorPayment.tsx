/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CheckCircle, Upload, Trash, Plus } from 'lucide-react';
import { Textarea } from "@/components/ui/textarea";
import PlaceSelector from '@/components/PlaceSelector';
import MultiDirectorSelector from '@/components/MultiDirectorSelector';

import { StepProps } from './types';


export const Step4AuditorPayment: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Auditor Payment</CardTitle>
                  <CardDescription>Statutory auditor's payment details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="auditorPaymentNumber">Payment Amount *</Label>
                      <Input
                        id="auditorPaymentNumber"
                        type="number"
                        value={formData.auditorPaymentNumber || ''}
                        onChange={(e) => {
                          const val = parseInt(e.target.value) || 0;
                          setFormData(prev => ({
                            ...prev,
                            auditorPaymentNumber: val,
                            auditorPaymentWords: numberToWords(val)
                          }));
                        }}
                        placeholder="e.g., 50000"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="auditorPaymentWords">Amount in Words *</Label>
                      <Input
                        id="auditorPaymentWords"
                        value={formData.auditorPaymentWords}
                        onChange={(e) => setFormData(prev => ({ ...prev, auditorPaymentWords: e.target.value }))}
                        placeholder="e.g., Fifty Thousand Only"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="auditorPaymentYear">Payment Year *</Label>
                      <Input
                        id="auditorPaymentYear"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.auditorPaymentYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, auditorPaymentYear: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

            {/* FINANCIAL STATEMENTS - Q1 ONLY */}
    </>
  );
};
