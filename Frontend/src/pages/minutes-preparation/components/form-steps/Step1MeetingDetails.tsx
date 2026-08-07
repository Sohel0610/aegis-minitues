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


export const Step1MeetingDetails: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Meeting Details</CardTitle>
                  <CardDescription>Enter meeting date, time, and location</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="timeConcluded">Meeting Conclusion Time</Label>
                    <Input
                      id="timeConcluded"
                      type="time"
                      value={formData.timeConcluded}
                      onChange={(e) => setFormData(prev => ({ ...prev, timeConcluded: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="meetingPlace">Meeting Place *</Label>
                    <PlaceSelector
                      id="meetingPlace"
                      label="Meeting Place"
                      value={formData.meetingPlace}
                      onChange={(value) => setFormData(prev => ({ ...prev, meetingPlace: value }))}
                      placeholder="Select Adani Corporate House or add custom place"
                    />
                    <p className="text-sm text-muted-foreground">
                      Default: Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421, Gujarat, India
                    </p>
                  </div>
                </CardContent>
              </Card>

            {/* ATTENDANCE */}
    </>
  );
};
