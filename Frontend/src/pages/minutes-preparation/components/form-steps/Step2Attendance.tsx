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


export const Step2Attendance: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Attendance</CardTitle>
                  <CardDescription>Directors and other attendees present at the meeting</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-3">Directors Present</h3>
                    <MultiDirectorSelector
                      id="presentDirectors"
                      label="Select Present Directors"
                      value={formData.presentDirectors}
                      onChange={(directors) => setFormData(prev => ({ ...prev, presentDirectors: directors }))}
                      placeholder="Type to search and add directors"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="chairmanName">Chairman Name</Label>
                    <select
                      id="chairmanName"
                      value={formData.chairmanName}
                      onChange={(e) => setFormData(prev => ({ ...prev, chairmanName: e.target.value }))}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    >
                      <option value="">Select Chairman</option>
                      {formData.presentDirectors.map((director, index) => (
                        <option key={index} value={director.name}>
                          {director.name} (DIN: {director.din})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="companySecretary">Company Secretary / Officer</Label>
                    <Input
                      id="companySecretary"
                      value={formData.companySecretary}
                      onChange={(e) => setFormData(prev => ({ ...prev, companySecretary: e.target.value }))}
                      placeholder="Enter company secretary or officer name"
                    />
                  </div>

                  <div>
                    <h3 className="text-lg font-medium mb-3">Others in Attendance</h3>
                    <div className="space-y-3">
                      {formData.inAttendance.map((attendee, index) => (
                        <div key={index} className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 border rounded-md">
                          <Input
                            placeholder="Name"
                            value={attendee.name}
                            onChange={(e) => {
                              const newInAttendance = [...formData.inAttendance];
                              newInAttendance[index].name = e.target.value;
                              setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                            }}
                          />
                          <Input
                            placeholder="Role"
                            value={attendee.role}
                            onChange={(e) => {
                              const newInAttendance = [...formData.inAttendance];
                              newInAttendance[index].role = e.target.value;
                              setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                            }}
                          />
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            onClick={() => {
                              const newInAttendance = [...formData.inAttendance];
                              newInAttendance.splice(index, 1);
                              setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                            }}
                            className="md:col-span-2"
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setFormData(prev => ({
                            ...prev,
                            inAttendance: [...prev.inAttendance, { name: '', role: '' }]
                          }));
                        }}
                      >
                        Add Attendee
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

            {/* DISCLOSURES - Q1 ONLY */}
    </>
  );
};
