/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CheckCircle, Upload, Trash, Plus, Building, Calendar, Users, Hash, Clock } from 'lucide-react';
import { Textarea } from "@/components/ui/textarea";
import PlaceSelector from '@/components/PlaceSelector';
import MultiDirectorSelector from '@/components/MultiDirectorSelector';

import { StepProps } from './types';


export const Step9Review: React.FC<StepProps> = (props) => {
  const { formData, setFormData, isOtherCompany, setIsOtherCompany, companyPresets, isUploadingTemplate, handleCustomTemplateUpload, resolutionTemplates, setResolutionTemplates, resTemplateName, setResTemplateName, numberToOrdinal, isStepValid, toast } = props;

  return (
    <>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Review Your Information</CardTitle>
          <CardDescription>Please review all information before generating the document</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Building className="h-5 w-5" />
                Company Information
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <p><span className="font-medium">Company:</span> {formData.companyName || 'Not provided'}</p>
                <p><span className="font-medium">Template:</span> {formData.template || 'Not provided'}</p>
                <p><span className="font-medium">Meeting #:</span> {formData.meetingNumber || 'Not provided'}</p>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Meeting Details
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <p><span className="font-medium">Date:</span> {formData.meetingDate || 'Not provided'}</p>
                <p><span className="font-medium">Day:</span> {formData.meetingDay || 'Not provided'}</p>
                <p><span className="font-medium">Time:</span> {formData.timeCommenced} - {formData.timeConcluded}</p>
                <p><span className="font-medium">Place:</span> {formData.meetingPlace || 'Not provided'}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Users className="h-5 w-5" />
              Attendance
            </h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="font-medium mb-2">Directors Present:</p>
              <ul className="list-disc pl-5 space-y-1">
                {formData.presentDirectors.map((director: any, index: number) => (
                  <li key={index}>
                    {director.name} (DIN: {director.din || 'Not provided'})
                  </li>
                ))}
              </ul>
              <p className="font-medium mt-3 mb-2">Chairman:</p>
              <p>{formData.chairmanName || 'Not provided'}</p>
            </div>
          </div>

          {formData.template === 'Q1' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Hash className="h-5 w-5" />
                  AGM Details
                </h3>
                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                  <p><span className="font-medium">AGM #:</span> {formData.agmNumber || 'Not provided'}</p>
                  <p><span className="font-medium">Date:</span> {formData.agmDay}/{formData.agmMonth}/{formData.agmYear}</p>
                  <p><span className="font-medium">Place:</span> {formData.registeredOfficeAddress || 'Not provided'}</p>
                  <p><span className="font-medium">Time:</span> {formData.agmTime || 'Not provided'}</p>
                  <p><span className="font-medium">Day:</span> {formData.agmDayName || 'Not provided'}</p>
                </div>
              </div>
            </div>
          )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Sign-off Details
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                        <p><span className="font-medium">Recording Date:</span> {formData.recordingDate || 'Not provided'}</p>
                        <p><span className="font-medium">Signing Date:</span> {formData.signingDate || 'Not provided'}</p>
                        <p><span className="font-medium">Signing Place:</span> {formData.signingPlace || 'Not provided'}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-5 w-5 text-blue-600" />
                      <h3 className="font-semibold text-blue-800">Ready to Generate</h3>
                    </div>
                    <p className="text-sm text-blue-700">
                      All information has been reviewed. Click the "Generate Document" button below to create your meeting minutes document.
                    </p>
                  </div>
                </CardContent>
              </Card>
    </>
  );
};
