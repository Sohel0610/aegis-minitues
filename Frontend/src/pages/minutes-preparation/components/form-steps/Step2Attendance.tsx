/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Trash2, Plus, CheckCircle2, XCircle, UserCheck } from 'lucide-react';
import MultiDirectorSelector from '@/components/MultiDirectorSelector';
import { StepProps } from './types';

export const Step2Attendance: React.FC<StepProps> = (props) => {
  const { formData, setFormData } = props;

  const toggleDirectorStatus = (index: number) => {
    const updated = [...(formData.presentDirectors || [])];
    if (updated[index]) {
      const currentStatus = updated[index].status || 'Present';
      updated[index].status = currentStatus === 'Present' ? 'Leave of Absence' : 'Present';
      setFormData(prev => ({ ...prev, presentDirectors: updated }));
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border border-slate-200 shadow-xs rounded-xl bg-white">
        <CardHeader className="border-b border-slate-100 pb-4 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">Directors & Board Attendance</CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Select directors present and record attendance status for <strong className="text-slate-800">{formData.companyName || "the company"}</strong>.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-green-50 text-green-700 border border-green-200/60">
              <UserCheck className="h-3.5 w-3.5" />
              {(formData.presentDirectors || []).filter((d: any) => d.status !== 'Leave of Absence').length} Present
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          
          {/* MultiDirectorSelector with company directors */}
          <MultiDirectorSelector
            id="presentDirectors"
            label="Directors Registry Search *"
            value={formData.presentDirectors || []}
            onChange={(directors) => {
              // Ensure default status is 'Present' for new entries
              const formatted = directors.map(d => ({
                ...d,
                status: d.status || 'Present'
              }));
              setFormData(prev => ({ ...prev, presentDirectors: formatted }));
            }}
            placeholder="Search director name or DIN from company master..."
            companyName={formData.companyName}
          />

          {/* Director Individual Attendance Status Table */}
          {formData.presentDirectors && formData.presentDirectors.length > 0 && (
            <div className="space-y-2 border-t border-slate-100 pt-4">
              <Label className="text-xs font-semibold text-slate-700">Individual Person-wise Attendance Status</Label>
              <div className="space-y-2">
                {formData.presentDirectors.map((director: any, index: number) => {
                  const isPresent = (director.status || 'Present') === 'Present';
                  return (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${isPresent ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                          {director.name ? director.name.charAt(0) : 'D'}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900">{director.name}</div>
                          {director.din && <div className="text-[10px] text-slate-500 font-mono">DIN: {director.din}</div>}
                        </div>
                      </div>

                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => toggleDirectorStatus(index)}
                        className={`h-7 px-3 text-xs font-semibold rounded-md flex items-center gap-1.5 transition-all ${
                          isPresent
                            ? 'bg-green-50 border-green-300 text-green-700 hover:bg-green-100'
                            : 'bg-amber-50 border-amber-300 text-amber-700 hover:bg-amber-100'
                        }`}
                      >
                        {isPresent ? (
                          <>
                            <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                            Present
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3.5 w-3.5 text-amber-600" />
                            Leave of Absence
                          </>
                        )}
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            
            {/* Chairman Selection */}
            <div className="space-y-2">
              <Label htmlFor="chairmanName" className="text-xs font-semibold text-slate-700">
                Meeting Chairman *
              </Label>
              <Select
                value={formData.chairmanName}
                onValueChange={(val) => setFormData(prev => ({ ...prev, chairmanName: val }))}
              >
                <SelectTrigger className="bg-white border-slate-200 h-9 rounded-lg text-xs font-medium focus:ring-0">
                  <SelectValue placeholder="Select Chairman from present directors" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {(!formData.presentDirectors || formData.presentDirectors.length === 0) ? (
                    <SelectItem value="none" disabled className="text-xs">Select directors above first</SelectItem>
                  ) : (
                    formData.presentDirectors.map((director: any, index: number) => (
                      <SelectItem key={index} value={director.name} className="text-xs">
                        {director.name} {director.din ? `(DIN: ${director.din})` : ''}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Company Secretary Input */}
            <div className="space-y-2">
              <Label htmlFor="companySecretary" className="text-xs font-semibold text-slate-700">
                Company Secretary / Officer
              </Label>
              <Input
                id="companySecretary"
                value={formData.companySecretary || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, companySecretary: e.target.value }))}
                placeholder="Enter Company Secretary name..."
                className="bg-white border-slate-200 h-9 rounded-lg text-xs"
              />
            </div>
          </div>

        </CardContent>
      </Card>

      {/* Others in Attendance Section */}
      <Card className="border border-slate-200 shadow-xs rounded-xl bg-white">
        <CardHeader className="border-b border-slate-100 pb-4 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900">Others in Attendance & External Guests</CardTitle>
            <CardDescription className="text-xs text-slate-500">Key officers, statutory auditors, external consultants, and invitees</CardDescription>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setFormData(prev => ({
                ...prev,
                inAttendance: [...(prev.inAttendance || []), { name: '', role: '', organization: '' }]
              }));
            }}
            className="rounded-lg text-xs font-medium border-slate-200 text-slate-700 hover:bg-slate-50"
          >
            <Plus className="h-3.5 w-3.5 mr-1" /> Add Guest Attendee
          </Button>
        </CardHeader>

        <CardContent className="p-6">
          {(!formData.inAttendance || formData.inAttendance.length === 0) ? (
            <div className="text-center py-6 text-slate-400 text-xs">
              No additional officers or invitees added.
            </div>
          ) : (
            <div className="space-y-3">
              {formData.inAttendance.map((attendee: any, index: number) => (
                <div 
                  key={index} 
                  className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200/80 rounded-lg"
                >
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                    <Input
                      placeholder="Full Name (e.g. Rahul Sharma)"
                      value={attendee.name}
                      onChange={(e) => {
                        const newInAttendance = [...formData.inAttendance];
                        newInAttendance[index].name = e.target.value;
                        setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                      }}
                      className="bg-white border-slate-200 h-8 rounded-md text-xs"
                    />
                    <Input
                      placeholder="Role / Designation (e.g. Statutory Auditor)"
                      value={attendee.role}
                      onChange={(e) => {
                        const newInAttendance = [...formData.inAttendance];
                        newInAttendance[index].role = e.target.value;
                        setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                      }}
                      className="bg-white border-slate-200 h-8 rounded-md text-xs"
                    />
                    <Input
                      placeholder="Organization / Firm (e.g. SRBC & CO LLP)"
                      value={attendee.organization || ''}
                      onChange={(e) => {
                        const newInAttendance = [...formData.inAttendance];
                        newInAttendance[index].organization = e.target.value;
                        setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                      }}
                      className="bg-white border-slate-200 h-8 rounded-md text-xs"
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const newInAttendance = [...formData.inAttendance];
                      newInAttendance.splice(index, 1);
                      setFormData(prev => ({ ...prev, inAttendance: newInAttendance }));
                    }}
                    className="h-8 w-8 p-0 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded-md shrink-0"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
