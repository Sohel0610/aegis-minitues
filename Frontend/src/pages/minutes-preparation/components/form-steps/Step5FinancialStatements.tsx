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


export const Step5FinancialStatements: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Financial Statements</CardTitle>
                  <CardDescription>Financial statements approval details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="fsYear">Financial Year *</Label>
                      <Input
                        id="fsYear"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.fsYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, fsYear: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="directorsReportYear">Directors Report Year *</Label>
                      <Input
                        id="directorsReportYear"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.directorsReportYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, directorsReportYear: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rptFinYearRangeFrom">Report Financial Year From *</Label>
                      <Input
                        id="rptFinYearRangeFrom"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.rptFinYearRangeFrom}
                        onChange={(e) => setFormData(prev => ({ ...prev, rptFinYearRangeFrom: parseInt(e.target.value) || (new Date().getFullYear() - 1) }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rptFinYearRangeTo">Report Financial Year To *</Label>
                      <Input
                        id="rptFinYearRangeTo"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.rptFinYearRangeTo}
                        onChange={(e) => setFormData(prev => ({ ...prev, rptFinYearRangeTo: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Signatory 1</h3>
                    <div className="space-y-2">
                      <Label htmlFor="signatory1">Select Director *</Label>
                      <select
                        id="signatory1"
                        value={formData.signatory1Name}
                        onChange={(e) => {
                          const selectedDirector = formData.presentDirectors.find(d => d.name === e.target.value);
                          if (selectedDirector) {
                            setFormData(prev => ({
                              ...prev,
                              signatory1Name: selectedDirector.name,
                              signatory1Din: selectedDirector.din,
                              signatory1Role: 'Director'
                            }));
                          }
                        }}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="">Select a director</option>
                        {formData.presentDirectors.map((director, index) => (
                          <option key={index} value={director.name}>
                            {director.name} (DIN: {director.din})
                          </option>
                        ))}
                      </select>
                      {formData.signatory1Name && (
                        <p className="text-sm text-muted-foreground">
                          Selected: {formData.signatory1Name} - DIN: {formData.signatory1Din}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Signatory 2</h3>
                    <div className="space-y-2">
                      <Label htmlFor="signatory2">Select Director *</Label>
                      <select
                        id="signatory2"
                        value={formData.signatory2Name}
                        onChange={(e) => {
                          const selectedDirector = formData.presentDirectors.find(d => d.name === e.target.value);
                          if (selectedDirector) {
                            setFormData(prev => ({
                              ...prev,
                              signatory2Name: selectedDirector.name,
                              signatory2Din: selectedDirector.din,
                              signatory2Role: 'Director'
                            }));
                          }
                        }}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="">Select a director</option>
                        {formData.presentDirectors.map((director, index) => (
                          <option key={index} value={director.name}>
                            {director.name} (DIN: {director.din})
                          </option>
                        ))}
                      </select>
                      {formData.signatory2Name && (
                        <p className="text-sm text-muted-foreground">
                          Selected: {formData.signatory2Name} - DIN: {formData.signatory2Din}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

            {/* AGM DETAILS - Q1 ONLY */}
    </>
  );
};
