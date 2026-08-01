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


export const Step6AGMDetails: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>AGM Details</CardTitle>
                  <CardDescription>Annual General Meeting information</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="agmNumber">AGM Number *</Label>
                    <Input
                      id="agmNumber"
                      name="agmNumber"
                      type="number"
                      min="1"
                      value={formData.agmNumber ? parseInt(formData.agmNumber.replace(/(st|nd|rd|th)$/, '')) || '' : ''}
                      onChange={(e) => {
                        const num = parseInt(e.target.value);
                        if (!isNaN(num)) {
                          // Convert to ordinal and update state
                          const ordinal = numberToOrdinal(num);
                          setFormData(prev => ({ ...prev, agmNumber: ordinal }));
                        } else {
                          setFormData(prev => ({ ...prev, agmNumber: '' }));
                        }
                      }}
                      placeholder="e.g., 10"
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                    />
                    <p className="text-xs text-slate-500">
                      Enter a number and it will be automatically converted to ordinal (e.g., 10 → 10th)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agmDate">AGM Date *</Label>
                    <Input
                      id="agmDate"
                      name="agmDate"
                      type="date"
                      value={formData.agmYear && formData.agmMonth && formData.agmDay ?
                        `${formData.agmYear}-${String(formData.agmMonth).padStart(2, '0')}-${String(formData.agmDay).padStart(2, '0')}` : ''}
                      onChange={(e) => {
                        const date = new Date(e.target.value);
                        if (!isNaN(date.getTime())) {
                          setFormData(prev => ({
                            ...prev,
                            agmYear: date.getFullYear(),
                            agmMonth: (date.getMonth() + 1),
                            agmDay: date.getDate(),
                            agmDayName: date.toLocaleDateString('en-US', { weekday: 'long' }),
                            agmMonthName: date.toLocaleDateString('en-US', { month: 'long' })
                          }));
                        }
                      }}
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                    />
                    <p className="text-xs text-slate-500">
                      Select the AGM date
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agmTime">AGM Time (9 AM - 6 PM) *</Label>
                    <Input
                      id="agmTime"
                      name="agmTime"
                      type="time"
                      min="09:00"
                      max="18:00"
                      value={formData.agmTime}
                      onChange={(e) => setFormData(prev => ({ ...prev, agmTime: e.target.value }))}
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                    />
                    <p className="text-sm text-muted-foreground">
                      Select the time of the AGM (9:00 AM to 6:00 PM only)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agmDayName">AGM Day Name</Label>
                    <Input
                      id="agmDayName"
                      name="agmDayName"
                      value={formData.agmDayName}
                      onChange={(e) => setFormData(prev => ({ ...prev, agmDayName: e.target.value }))}
                      placeholder="e.g., Friday"
                      readOnly
                    />
                    <p className="text-sm text-muted-foreground">
                      Automatically populated based on the selected date
                    </p>
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="registeredOfficeAddress">Registered Office Address *</Label>
                    <PlaceSelector
                      id="registeredOfficeAddress"
                      label="Registered Office Address"
                      value={formData.registeredOfficeAddress}
                      onChange={(value) => setFormData(prev => ({ ...prev, registeredOfficeAddress: value }))}
                      placeholder="Select address or add custom address"
                    />
                    <p className="text-sm text-muted-foreground">
                      Default: Adani Corporate House, Ahmedabad
                    </p>
                  </div>
                </CardContent>
              </Card>

            {/* SIGN-OFF DETAILS */}
    </>
  );
};
