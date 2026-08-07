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


export const Step7SignOffDetails: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>
(formData.template === 'Q1' && currentStep === 7) || (formData.template !== 'Q1' && currentStep === 3)) && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Sign-off Details</CardTitle>
                  <CardDescription>Recording and signing information</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="recordingDate">Recording Date *</Label>
                    <Input
                      id="recordingDate"
                      type="date"
                      value={formData.recordingDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, recordingDate: e.target.value }))}
                      className={!formData.recordingDate ? 'border-red-500' : ''}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signingDate">Signing Date *</Label>
                    <Input
                      id="signingDate"
                      type="date"
                      value={formData.signingDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, signingDate: e.target.value }))}
                      className={!formData.signingDate ? 'border-red-500' : ''}
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="signingPlace">Signing Place *</Label>
                    <Select
                      value={formData.signingPlace === 'Ahmedabad' ? 'Ahmedabad' : 'Other'}
                      onValueChange={(val) => {
                        if (val === 'Ahmedabad') {
                          setFormData(prev => ({ ...prev, signingPlace: 'Ahmedabad' }));
                        } else {
                          setFormData(prev => ({ ...prev, signingPlace: '' }));
                        }
                      }}
                    >
                      <SelectTrigger className="bg-white">
                        <SelectValue placeholder="Select signing place" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        <SelectItem value="Ahmedabad">Ahmedabad</SelectItem>
                        <SelectItem value="Other">Custom Address</SelectItem>
                      </SelectContent>
                    </Select>

                    {formData.signingPlace !== 'Ahmedabad' && (
                      <div className="mt-2 animate-in fade-in slide-in-from-top-1">
                        <Input
                          id="signingPlaceCustom"
                          value={formData.signingPlace}
                          onChange={(e) => setFormData(prev => ({ ...prev, signingPlace: e.target.value }))}
                          placeholder="Enter custom signing place address"
                          className={!formData.signingPlace.trim() ? 'border-red-500' : ''}
                        />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

            {/* RESOLUTIONS */}
    </>
  );
};
