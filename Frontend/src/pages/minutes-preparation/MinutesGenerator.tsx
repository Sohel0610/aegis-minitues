/* eslint-disable @typescript-eslint/no-explicit-any */

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Clock, Download, FileText, Home, History, FileSpreadsheet, Plus, Upload, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText as FileTextIcon } from 'lucide-react';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { companyPresets } from '@/constants/companyPresets';

const MinutesGenerator = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState<any[]>([]);

  // Calendarization state
  const [calendarData, setCalendarData] = useState({
    bu: '',
    meetingDate: '',
    meetingTime: '',
    meetingType: 'Board Meeting',
    committeeName: ''
  });

  // Fetch history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/api/generated-minutes');
        if (res.ok) {
          const data = await res.json();
          setHistory(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch history", err);
      }
    };
    fetchHistory();
  }, []);

  // Presets (shared)

  const meetingTypes = [
    { value: "Board Meeting", label: "Board Meeting" },
    { value: "Committee Meeting", label: "Committee Meeting" },
    { value: "Annual General Meeting", label: "Annual General Meeting" },
    { value: "Extraordinary General Meeting", label: "Extraordinary General Meeting" }
  ];

  const handleGenerateClick = () => {
    const selectedCompany = companyPresets.find(c => c.name === calendarData.bu);
    const stateToPass = {
      companyName: calendarData.bu,
      meetingDate: calendarData.meetingDate,
      meetingDay: calendarData.meetingDate ? new Date(calendarData.meetingDate).toLocaleDateString('en-US', { weekday: 'long' }) : '',
      meetingType: calendarData.meetingType,
      committeeName: calendarData.committeeName,
      timeCommenced: calendarData.meetingTime,
      // Pre-fill company details if preset found
      ...(selectedCompany ? {
        meetingPlace: selectedCompany.address,
        presentDirectors: selectedCompany.directors,
        chairmanName: selectedCompany.directors[0]?.name || ''
      } : {})
    };
    navigate('/minutes-preparation/form-generator', { state: stateToPass });
  };

  // Define navigation items for this product
  const navigationItems = getMinutesNavItems();

  return (
    <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
      <div className="container mx-auto py-6">
        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-bold">Generate Minutes</h1>
            <p className="text-muted-foreground">Select Business Unit and Schedule to generate minutes</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Meeting Scheduling
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Business Unit (BU) / Company</Label>
                  <Select value={calendarData.bu} onValueChange={(v) => setCalendarData({ ...calendarData, bu: v })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Business Unit" />
                    </SelectTrigger>
                    <SelectContent>
                      {companyPresets.map((c, i) => <SelectItem key={i} value={c.name}>{c.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Meeting Type</Label>
                  <Select value={calendarData.meetingType} onValueChange={(v) => setCalendarData({ ...calendarData, meetingType: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {meetingTypes.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                {calendarData.meetingType === 'Committee Meeting' && (
                  <div className="space-y-2">
                    <Label>Committee Name</Label>
                    <Input
                      placeholder="e.g. Audit Committee"
                      value={calendarData.committeeName}
                      onChange={(e) => setCalendarData({ ...calendarData, committeeName: e.target.value })}
                    />
                  </div>
                )}
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Input type="date" value={calendarData.meetingDate} onChange={(e) => setCalendarData({ ...calendarData, meetingDate: e.target.value })} />
                  {calendarData.meetingDate && (
                    <p className="text-sm font-medium text-blue-600">
                      Day: {new Date(calendarData.meetingDate).toLocaleDateString('en-US', { weekday: 'long' })}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Time</Label>
                  <Input type="time" value={calendarData.meetingTime} onChange={(e) => setCalendarData({ ...calendarData, meetingTime: e.target.value })} />
                </div>
              </div>
              <div className="pt-4 border-t">
                <p className="text-sm text-muted-foreground mb-3">
                  Have a specific format? You can manually upload your own template in the next step.
                </p>
                <div className="flex gap-4">
                  <Button
                    className="flex-1"
                    disabled={!calendarData.bu || !calendarData.meetingDate}
                    onClick={handleGenerateClick}
                  >
                    Continue to Generate Minutes
                  </Button>
                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                    onClick={() => {
                      navigate('/minutes-preparation/form-generator', {
                        state: {
                          ...calendarData,
                          template: 'custom',
                          companyName: calendarData.bu
                        }
                      });
                    }}
                  >
                    <Upload className="h-4 w-4" />
                    Use Custom Template
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Past Created Meetings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company</TableHead>
                    <TableHead>Meeting Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center">No past meetings found.</TableCell>
                    </TableRow>
                  ) : (
                    history.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.company_name}</TableCell>
                        <TableCell>{item.meeting_type}</TableCell>
                        <TableCell>{item.meeting_date}</TableCell>
                        <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                        <TableCell>
                          <Button variant="outline" size="sm" onClick={() => {
                            const link = document.createElement('a');
                            link.href = item.download_url;
                            link.download = item.file_path;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                          }}>
                            <Download className="h-4 w-4 mr-1" /> Download
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </ProductDashboardLayout>
  );
};
export default MinutesGenerator;
