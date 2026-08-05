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

const namesLooselyMatch = (a?: string, b?: string) => {
  const norm = (s: string) =>
    s
      .toLowerCase()
      .replace(/\b(mr|mrs|ms|dr)\b\.?/g, '')
      .replace(/[^a-z]/g, '');
  if (!a || !b) return false;
  const x = norm(a);
  const y = norm(b);
  return x === y || x.includes(y) || y.includes(x);
};

/** Prefer designation Chair; else previous-meeting chairman only if that person is Present. */
const pickChairman = (dirs: any[], preferred?: string) => {
  const isChair = (d: any) => {
    const desig = `${d?.designation || d?.role || ''}`.toLowerCase();
    return desig.includes('chair');
  };
  const byRole = dirs.find(isChair);
  if (byRole?.name) return byRole.name;
  if (preferred) {
    const pref = dirs.find((d) => namesLooselyMatch(d.name, preferred));
    if (pref?.name) return pref.name;
  }
  return '';
};

const meetingTypeForChairman = (formData: any) => {
  if (formData.committeeName) return formData.committeeName;
  return formData.meetingType || 'Board Meeting';
};

export const Step2Attendance: React.FC<StepProps> = (props) => {
  const { formData, setFormData } = props;
  const [loadingDirectors, setLoadingDirectors] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [chairmanSource, setChairmanSource] = useState<string | null>(null);
  const loadedForCompanyRef = useRef<string>('');

  // Auto-load directors + meeting chairman (from previous minutes / template for this company + type)
  useEffect(() => {
    const company = (formData.companyName || '').trim();
    if (!company) return;
    const mType = meetingTypeForChairman(formData);
    const cacheKey = `${company}||${mType}||${formData.template || ''}`;
    if (loadedForCompanyRef.current === cacheKey && (formData.presentDirectors || []).length > 0 && formData.chairmanName) {
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoadingDirectors(true);
      setLoadError(null);
      try {
        const requests: Promise<Response>[] = [
          fetch(`/api/companies/${encodeURIComponent(company)}/directors`),
          fetch(
            `/api/companies/${encodeURIComponent(company)}/default-chairman?meeting_type=${encodeURIComponent(mType)}`
          ),
        ];
        if (formData.template && formData.template !== 'custom') {
          requests.push(fetch(`/api/templates/${encodeURIComponent(formData.template)}/chairman`));
        }

        const responses = await Promise.all(requests);
        const dirRes = responses[0];
        const chairRes = responses[1];
        const templateChairRes = responses[2];

        const dirData = dirRes.ok ? await dirRes.json() : { data: [] };
        const chairData = chairRes.ok ? await chairRes.json() : { chairman_name: '' };
        const templateChairData =
          templateChairRes && templateChairRes.ok ? await templateChairRes.json() : { chairman_name: '' };

        // Prefer company-scoped sources; template chair only counts if that person is on THIS board
        const companyPreferred = (chairData.chairman_name || dirData.default_chairman || '').trim();
        const templatePreferred = (templateChairData.chairman_name || '').trim();

        const directors = (Array.isArray(dirData.data) ? dirData.data : []).map((d: any) => {
          const base = {
            name: d.name,
            din: d.din || '',
            designation: d.designation || d.role || 'Director',
            role: d.designation || d.role || 'Director',
            status: 'Present',
            source: d.source,
          };
          const matchPreferred =
            (companyPreferred && namesLooselyMatch(base.name, companyPreferred)) ||
            (templatePreferred && namesLooselyMatch(base.name, templatePreferred));
          if (matchPreferred) {
            return { ...base, designation: 'Chairman', role: 'Chairman' };
          }
          return base;
        });

        // Only auto-select a chairman who is actually on this company's director list
        const preferredChair = (() => {
          if (
            companyPreferred &&
            directors.some((d: any) => namesLooselyMatch(d.name, companyPreferred))
          ) {
            return companyPreferred;
          }
          if (
            templatePreferred &&
            directors.some((d: any) => namesLooselyMatch(d.name, templatePreferred))
          ) {
            return templatePreferred;
          }
          return '';
        })();

        if (cancelled) return;
        loadedForCompanyRef.current = cacheKey;
        setChairmanSource(
          preferredChair
            ? companyPreferred && namesLooselyMatch(preferredChair, companyPreferred)
              ? chairData.source || 'previous_minutes'
              : 'template'
            : null
        );

        setFormData((prev) => {
          const existing = prev.presentDirectors || [];
          // Drop outsiders previously injected (e.g. Raj Kumar Jain from another company's template)
          const cleanedExisting = existing.filter((d: any) =>
            directors.some((reg: any) => namesLooselyMatch(reg.name, d.name))
          );
          const shouldReplace =
            cleanedExisting.length === 0 ||
            prev.companyName !== company ||
            existing.length !== cleanedExisting.length;
          const nextDirs =
            shouldReplace && directors.length > 0
              ? directors
              : cleanedExisting.map((d: any) => {
                  const isPref = preferredChair && namesLooselyMatch(d.name, preferredChair);
                  return {
                    ...d,
                    status: d.status || 'Present',
                    designation: isPref ? 'Chairman' : d.designation || d.role || 'Director',
                    role: isPref ? 'Chairman' : d.role || d.designation || 'Director',
                  };
                });

          const present = nextDirs.filter((d: any) => d.status !== 'Leave of Absence');
          let chair = pickChairman(present, preferredChair);
          // Keep draft chairman only if they are still a Present director of this company
          if (!chair && prev.chairmanName?.trim()) {
            const kept = present.find((d: any) => namesLooselyMatch(d.name, prev.chairmanName));
            if (kept) chair = kept.name;
          }
          return {
            ...prev,
            presentDirectors: nextDirs,
            chairmanName: chair,
            signingChairmanName: chair || '',
          };
        });

        if (!directors.length) {
          setLoadError(
            'No directors found for this company. Search/add manually, or run the Minutes director seed (see minutes_guide.md).'
          );
        }
      } catch (err) {
        console.error(err);
        if (!cancelled) setLoadError('Could not load company directors / chairman. Check API / seed data.');
      } finally {
        if (!cancelled) setLoadingDirectors(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [formData.companyName, formData.meetingType, formData.committeeName, formData.template, setFormData]);

  // Keep chairman valid on attendance toggles.
  // If the chosen chairman goes on Leave of Absence, keep their name so marking them
  // Present again restores the auto-filled box (do not blank and force re-pick).
  useEffect(() => {
    const allDirs = formData.presentDirectors || [];
    if (!allDirs.length) return;

    const chairName = (formData.chairmanName || '').trim();
    const onBoard = allDirs.some((d: any) => namesLooselyMatch(d.name, chairName));

    // Still on this company's list (Present or LOA) — leave name alone; UI handles LOA
    if (chairName && onBoard) return;

    const present = allDirs.filter((d: any) => d.status !== 'Leave of Absence');
    const pick = pickChairman(present);

    // Clear outsiders / empty → only auto-set when a Chair designation exists
    if ((chairName && !onBoard) || pick) {
      setFormData((prev) => ({
        ...prev,
        chairmanName: pick,
        signingChairmanName: pick,
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
            
            {/* Chairman — auto-filled; select only if absent */}
            <div className="space-y-2">
              <Label htmlFor="chairmanName" className="text-xs font-semibold text-slate-700">
                Meeting Chairman *
              </Label>
              {(() => {
                const chairName = formData.chairmanName || '';
                const chairDirector = (formData.presentDirectors || []).find((d: any) =>
                  namesLooselyMatch(d.name, chairName)
                );
                const chairAbsent = Boolean(
                  chairName && chairDirector && (chairDirector.status || 'Present') !== 'Present'
                );
                const needsManualSelect = !chairName || chairAbsent;

                if (!needsManualSelect) {
                  return (
                    <>
                      <div className="h-9 px-3 rounded-lg border border-emerald-200 bg-emerald-50 flex items-center text-xs font-semibold text-emerald-800">
                        {chairName}
                        {chairDirector?.din ? ` (DIN: ${chairDirector.din})` : ''}
                      </div>
                      <p className="text-[11px] text-emerald-700">
                        Auto-filled{chairmanSource ? ` from ${chairmanSource === 'template' || chairmanSource === 'template_seed' ? 'company template' : 'previous minutes'}` : ''}. Change only if this person is on Leave of Absence.
                      </p>
                    </>
                  );
                }

                return (
                  <>
                    {chairAbsent && (
                      <p className="text-[11px] text-amber-700">
                        Default chairman ({chairName}) is on Leave of Absence — select a temporary chairman.
                      </p>
                    )}
                    {!chairName && (
                      <p className="text-[11px] text-slate-500">
                        No previous chairman found for this company/meeting type — please select.
                      </p>
                    )}
                    <Select
                      value={chairAbsent ? undefined : (formData.chairmanName || undefined)}
                      onValueChange={(val) =>
                        setFormData((prev) => ({ ...prev, chairmanName: val, signingChairmanName: val }))
                      }
                    >
                      <SelectTrigger className="bg-white border-slate-200 h-9 rounded-lg text-xs font-medium focus:ring-0">
                        <SelectValue placeholder="Select temporary Chairman from present directors" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        {(!formData.presentDirectors ||
                          formData.presentDirectors.filter((d: any) => (d.status || 'Present') === 'Present').length === 0) ? (
                          <SelectItem value="none" disabled className="text-xs">
                            Mark directors Present first
                          </SelectItem>
                        ) : (
                          formData.presentDirectors
                            .filter((d: any) => (d.status || 'Present') === 'Present')
                            .map((director: any, index: number) => (
                              <SelectItem key={index} value={director.name} className="text-xs">
                                {director.name}
                                {director.designation || director.role
                                  ? ` · ${director.designation || director.role}`
                                  : ''}
                                {director.din ? ` (DIN: ${director.din})` : ''}
                              </SelectItem>
                            ))
                        )}
                      </SelectContent>
                    </Select>
                  </>
                );
              })()}
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
