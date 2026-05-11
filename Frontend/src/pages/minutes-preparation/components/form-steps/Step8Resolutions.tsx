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


export const Step8Resolutions: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>
(formData.template === 'Q1' && currentStep === 8) || (formData.template !== 'Q1' && currentStep === 4)) && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Meeting Resolutions</CardTitle>
                  <CardDescription>Select stored resolutions or add new ones for the meeting</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="resPicker">Select from Stored Resolutions</Label>
                    <Select
                      onValueChange={(val) => {
                        const template = resolutionTemplates.find(t => t.id.toString() === val);
                        if (template) {
                          setFormData(prev => ({
                            ...prev,
                            resolutions: prev.resolutions
                              ? prev.resolutions + "\n\n" + template.resolution_text
                              : template.resolution_text
                          }));
                        }
                      }}
                    >
                      <SelectTrigger className="bg-white">
                        <SelectValue placeholder="Choose a resolution template..." />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        {resolutionTemplates.map((t) => (
                          <SelectItem key={t.id} value={t.id.toString()}>{t.template_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-muted-foreground">Selecting a template will append it to the text area below.</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="resolutionsText">Resolution Details</Label>
                    <textarea
                      id="resolutionsText"
                      rows={10}
                      className="w-full p-3 border rounded-md text-sm font-serif"
                      value={formData.resolutions}
                      onChange={(e) => setFormData(prev => ({ ...prev, resolutions: e.target.value }))}
                      placeholder="Enter resolutions passed during the meeting..."
                    />
                  </div>

                  <div className="border-t pt-4 space-y-4">
                    <h4 className="text-sm font-medium">Save current text as new template</h4>
                    <div className="flex gap-4">
                      <div className="flex-1 space-y-1">
                        <Input
                          placeholder="Template Name"
                          value={resTemplateName}
                          onChange={(e) => setResTemplateName(e.target.value)}
                        />
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={!resTemplateName || !formData.resolutions}
                        onClick={async () => {
                          try {
                            const res = await fetch('/api/resolutions', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                template_name: resTemplateName,
                                resolution_text: formData.resolutions
                              })
                            });
                            if (res.ok) {
                              const data = await res.json();
                              setResolutionTemplates(prev => [...prev, data]);
                              setResTemplateName('');
                              toast({title: 'Success', description: 'Resolution template saved successfully!'});
                            }
                          } catch (err) {
                            toast({title: 'Error', description: 'Failed to save resolution template', variant: 'destructive'});
                          }
                        }}
                      >
                        Save Template
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

            {/* REVIEW & GENERATE */}
    </>
  );
};
