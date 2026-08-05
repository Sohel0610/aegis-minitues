/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Trash2, Plus, CheckCircle2, XCircle, UserCheck, Loader2 } from 'lucide-react';
import MultiDirectorSelector from '@/components/MultiDirectorSelector';
import { StepProps } from './types';

const pickChairman = (dirs: any[], preferred?: string) => {
  if (preferred && dirs.some((d) => d.name === preferred)) return preferred;
  const byRole = dirs.find((d: any) => `${d.designation || d.role || ''}`.toLowerCase().includes('chair'));
  return byRole?.name || dirs[0]?.name || '';
};

export const Step2Attendance: React.FC<StepProps> = (props) => {
  const { formData, setFormData } = props;
  const [loadingDirectors, setLoadingDirectors] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const loadedForCompanyRef = useRef<string>('');

  // Auto-load directors + default chairman for the selected company
  useEffect(() => {
    const company = (formData.companyName || '').trim();
    if (!company) return;
    if (loadedForCompanyRef.current === company && (formData.presentDirectors || []).length > 0) {
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoadingDirectors(true);
      setLoadError(null);
      try {
        const res = await fetch(`/api/companies/${encodeURIComponent(company)}/directors`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const directors = (Array.isArray(data.data) ? data.data : []).map((d: any) => ({
          name: d.name,
          din: d.din || '',
          designation: d.designation || d.role || 'Director',
          role: d.designation || d.role || 'Director',
          status: 'Present',
          source: d.source,
        }));
        if (cancelled) return;
        loadedForCompanyRef.current = company;

        setFormData((prev) => {
          const existing = prev.presentDirectors || [];
          const shouldReplace =
            existing.length === 0 ||
            prev.companyName !== company;

          const nextDirs =
            shouldReplace && directors.length > 0
              ? directors
              : existing.map((d: any) => ({
                  ...d,
                  status: d.status || 'Present',
                  designation: d.designation || d.role || 'Director',
                }));

          const present = nextDirs.filter((d: any) => d.status !== 'Leave of Absence');
          const chair = pickChairman(present, data.default_chairman);
          return {
            ...prev,
            presentDirectors: nextDirs,
            chairmanName: chair || prev.chairmanName,
            signingChairmanName: chair || prev.signingChairmanName,
          };
        });

        if (!directors.length) {
          setLoadError(
            'No directors found for this company. Search/add manually, or run the Minutes director seed (see minutes_guide.md).'
          );
        }
      } catch (err) {
        console.error(err);
        if (!cancelled) setLoadError('Could not load company directors. Check API / seed data.');
      } finally {
        if (!cancelled) setLoadingDirectors(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [formData.companyName, setFormData]);

  // Keep chairman valid when attendance toggles change
  useEffect(() => {
    const dirs = (formData.presentDirectors || []).filter((d: any) => d.status !== 'Leave of Absence');
    if (!dirs.length) return;
    const hasCurrent = dirs.some((d: any) => d.name === formData.chairmanName);
    if (formData.chairmanName && hasCurrent) return;
    const pick = pickChairman(dirs);
    if (pick) {
      setFormData((prev) => ({
        ...prev,
        chairmanName: pick,
        signingChairmanName: prev.signingChairmanName || pick,
      }));
    }
  }, [formData.presentDirectors, formData.chairmanName, setFormData]);

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
              Auto-loaded from the company registry for <strong className="text-slate-800">{formData.companyName || "the company"}</strong>. Adjust attendance and chairman as needed.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {loadingDirectors && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-50 text-slate-600 border border-slate-200">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Loading…
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-green-50 text-green-700 border border-green-200/60">
              <UserCheck className="h-3.5 w-3.5" />
              {(formData.presentDirectors || []).filter((d: any) => d.status !== 'Leave of Absence').length} Present
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {loadError && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              {loadError}
            </div>
          )}

          {/* MultiDirectorSelector with company directors */}
          <MultiDirectorSelector
            id="presentDirectors"
            label="Directors Registry Search *"
            value={formData.presentDirectors || []}
            onChange={(directors) => {
              // Ensure default status is 'Present' for new entries
              const formatted = directors.map(d => ({
                ...d,
                status: d.status || 'Present',
                designation: (d as any).designation || (d as any).role || 'Director',
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
                        {director.name}
                        {director.designation || director.role ? ` · ${director.designation || director.role}` : ''}
                        {director.din ? ` (DIN: ${director.din})` : ''}
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
