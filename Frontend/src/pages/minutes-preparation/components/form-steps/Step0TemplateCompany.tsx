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


export const Step0TemplateCompany: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Template & Company Information</CardTitle>
                  <CardDescription>Select template and enter company details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="template">Template *</Label>
                    <Select
                      value={formData.template}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, template: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a template" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        <SelectItem value="Q1">Q1 Meeting Template</SelectItem>
                        <SelectItem value="Q2">Q2 Meeting Template</SelectItem>
                        <SelectItem value="Q3">Q3 Meeting Template</SelectItem>
                        <SelectItem value="Q4">Q4 Meeting Template</SelectItem>
                        <SelectItem value="custom">Manual Upload (Custom)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.template === 'custom' && (
                    <div className="space-y-4">
                      <Label>Upload Custom DOCX Template *</Label>
                      <div
                        className={`relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 text-center ${formData.customTemplateFilename ? 'border-green-200 bg-green-50' : 'border-blue-200 bg-blue-50/30'
                          }`}
                      >
                        <input
                          id="customTemplate"
                          type="file"
                          accept=".docx"
                          onChange={handleCustomTemplateUpload}
                          disabled={isUploadingTemplate}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <div className="flex flex-col items-center gap-2">
                          {isUploadingTemplate ? (
                            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
                          ) : formData.customTemplateFilename ? (
                            <div className="bg-green-100 p-3 rounded-full">
                              <CheckCircle className="h-6 w-6 text-green-600" />
                            </div>
                          ) : (
                            <div className="bg-blue-100 p-3 rounded-full">
                              <Upload className="h-6 w-6 text-blue-600" />
                            </div>
                          )}

                          <div>
                            <p className="font-medium text-gray-900">
                              {formData.customTemplateFilename ? 'Template Uploaded' : 'Drop your template here or click to browse'}
                            </p>
                            <p className="text-sm text-gray-500">
                              {formData.customTemplateFilename || 'Only .docx files with [Placeholders] supported'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="companyName">Company Name *</Label>
                    <Select
                      value={isOtherCompany ? 'other' : formData.companyName}
                      onValueChange={(value) => {
                        if (value === 'other') {
                          setIsOtherCompany(true);
                        } else {
                          setIsOtherCompany(false);
                          const selected = companyPresets.find(c => c.name === value);
                          setFormData(prev => ({
                            ...prev,
                            companyName: value,
                            ...(selected ? {
                              meetingPlace: selected.address,
                              presentDirectors: selected.directors,
                              chairmanName: selected.directors[0]?.name || ''
                            } : {})
                          }));
                        }
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select company" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        {companyPresets.map(c => (
                          <SelectItem key={c.name} value={c.name}>{c.name}</SelectItem>
                        ))}
                        <SelectItem value="other">Other / Custom</SelectItem>
                      </SelectContent>
                    </Select>

                    {isOtherCompany && (
                      <Input
                        id="companyName"
                        value={formData.companyName}
                        onChange={(e) => setFormData(prev => ({ ...prev, companyName: e.target.value }))}
                        placeholder="Enter custom company name"
                        className={`mt-2 ${!formData.companyName.trim() ? 'border-red-500' : ''}`}
                      />
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="meetingNumber">Meeting Number</Label>
                    <Input
                      id="meetingNumber"
                      type="number"
                      min="1"
                      value={formData.meetingNumber ? parseInt(formData.meetingNumber.replace(/(st|nd|rd|th)$/, '')) || '' : ''}
                      onChange={(e) => {
                        const num = parseInt(e.target.value);
                        if (!isNaN(num)) {
                          const ordinal = numberToOrdinal(num);
                          setFormData(prev => ({ ...prev, meetingNumber: ordinal }));
                        } else {
                          setFormData(prev => ({ ...prev, meetingNumber: '' }));
                        }
                      }}
                      placeholder="e.g., 5"
                    />
                    <p className="text-sm text-muted-foreground">
                      Enter a number and it will be automatically converted to ordinal (e.g., 5 → 5th)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="meetingType">Meeting Type</Label>
                    <Select
                      value={formData.meetingType}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, meetingType: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select meeting type" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        <SelectItem value="Board Meeting">Board Meeting</SelectItem>
                        <SelectItem value="Annual General Meeting">Annual General Meeting</SelectItem>
                        <SelectItem value="Extraordinary General Meeting">Extraordinary General Meeting</SelectItem>
                        <SelectItem value="Committee Meeting">Committee Meeting</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.meetingType === 'Committee Meeting' && (
                    <div className="space-y-2">
                      <Label htmlFor="committeeName">Committee Name</Label>
                      <Input
                        id="committeeName"
                        value={formData.committeeName}
                        onChange={(e) => setFormData(prev => ({ ...prev, committeeName: e.target.value }))}
                        placeholder="e.g., Audit Committee"
                      />
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="meetingDate">Meeting Date *</Label>
                      <Input
                        id="meetingDate"
                        type="date"
                        value={formData.meetingDate}
                        onChange={(e) => {
                          setFormData(prev => ({ ...prev, meetingDate: e.target.value }));
                          if (e.target.value) {
                            const dayName = new Date(e.target.value).toLocaleDateString('en-US', { weekday: 'long' });
                            setFormData(prev => ({ ...prev, meetingDay: dayName }));
                          }
                        }}
                        className={!formData.meetingDate ? 'border-red-500' : ''}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="meetingDay">Meeting Day</Label>
                      <Input
                        id="meetingDay"
                        value={formData.meetingDay}
                        readOnly
                        placeholder="Auto-calculated from date"
                        className="bg-gray-50"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timeCommenced">Meeting Start Time</Label>
                    <Input
                      id="timeCommenced"
                      type="time"
                      value={formData.timeCommenced}
                      onChange={(e) => setFormData(prev => ({ ...prev, timeCommenced: e.target.value }))}
                    />
                  </div>
                </CardContent>
              </Card>

            {/* MEETING DETAILS */}
    </>
  );
};
