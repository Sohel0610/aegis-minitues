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


export const Step3LegalDisclosures: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Disclosures</CardTitle>
                  <CardDescription>Disclosures under the Companies Act</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-3">Interest Disclosures</h3>
                    <MultiDirectorSelector
                      id="interestDisclosures"
                      label="Select Directors with Interest Disclosures"
                      value={formData.interestDisclosures}
                      onChange={(directors) => setFormData(prev => ({ ...prev, interestDisclosures: directors }))}
                      placeholder="Type to search and add directors"
                    />
                  </div>

                  <div>
                    <h3 className="text-lg font-medium mb-3">Disqualification Declarations</h3>
                    <MultiDirectorSelector
                      id="disqualificationDeclarations"
                      label="Select Directors with Disqualification Declarations"
                      value={formData.disqualificationDeclarations}
                      onChange={(directors) => setFormData(prev => ({ ...prev, disqualificationDeclarations: directors }))}
                      placeholder="Type to search and add directors"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="previousMinutesDate">Previous Minutes Date</Label>
                    <Input
                      id="previousMinutesDate"
                      type="date"
                      value={formData.previousMinutesDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, previousMinutesDate: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-4 border-t pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="text-base">Disclosure of Interest (Section 184)</Label>
                        <p className="text-sm text-muted-foreground">Is there a disclosure of interest for this meeting?</p>
                      </div>
                      <div className="flex bg-gray-100 p-1 rounded-md">
                        <Button
                          type="button"
                          variant={formData.hasSection184Disclosure ? "default" : "ghost"}
                          size="sm"
                          onClick={() => setFormData(prev => ({ ...prev, hasSection184Disclosure: true }))}
                        >
                          Yes
                        </Button>
                        <Button
                          type="button"
                          variant={!formData.hasSection184Disclosure ? "default" : "ghost"}
                          size="sm"
                          onClick={() => setFormData(prev => ({ ...prev, hasSection184Disclosure: false, section184Subject: '', section184Text: '' }))}
                        >
                          No
                        </Button>
                      </div>
                    </div>

                    {formData.hasSection184Disclosure && (
                      <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
                        <div className="space-y-2">
                          <Label htmlFor="sec184Subject">Select Subject Line</Label>
                          <Select
                            value={formData.section184Subject}
                            onValueChange={(val) => {
                              const selected = section184SubjectLines.find(s => s.subject === val);
                              setFormData(prev => ({
                                ...prev,
                                section184Subject: val,
                                section184Text: selected ? selected.text : ''
                              }));
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Choose a subject line" />
                            </SelectTrigger>
                            <SelectContent className="bg-white">
                              {section184SubjectLines.map((line, i) => (
                                <SelectItem key={i} value={line.subject}>{line.subject}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="sec184Text">Disclosure Text</Label>
                          <textarea
                            id="sec184Text"
                            rows={4}
                            className="w-full p-3 border rounded-md text-sm"
                            value={formData.section184Text}
                            onChange={(e) => setFormData(prev => ({ ...prev, section184Text: e.target.value }))}
                            placeholder="Text will auto-populate based on subject line..."
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

            {/* AUDITOR PAYMENT - Q1 ONLY */}
    </>
  );
};
