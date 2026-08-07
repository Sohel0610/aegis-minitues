/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, ArrowUp, ArrowDown, Trash2, Plus, FileText, CheckCircle2 } from 'lucide-react';
import { StepProps } from './types';

export const Step8Resolutions: React.FC<StepProps> = (props) => {
  const { 
    formData, 
    setFormData, 
    resolutionTemplates = [], 
    setResolutionTemplates, 
    resTemplateName, 
    setResTemplateName, 
    toast 
  } = props;

  const [searchQuery, setSearchQuery] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Filter templates based on type-search input (Title or Keyword)
  const filteredTemplates = useMemo(() => {
    if (!searchQuery.trim()) return resolutionTemplates;
    const q = searchQuery.toLowerCase();
    return resolutionTemplates.filter(t => 
      t.template_name?.toLowerCase().includes(q) || 
      t.resolution_text?.toLowerCase().includes(q)
    );
  }, [resolutionTemplates, searchQuery]);

  const addResolutionFromTemplate = (template: any) => {
    const newItems = [...(formData.selectedResolutions || [])];
    newItems.push({
      id: Date.now() + Math.random(),
      title: template.template_name,
      text: template.resolution_text
    });
    setFormData(prev => ({
      ...prev,
      selectedResolutions: newItems,
      resolutions: newItems.map((i: any) => i.text).join('\n\n')
    }));
    toast && toast({ title: "Resolution Added", description: `Added "${template.template_name}" to meeting agenda.` });
  };

  const moveResolution = (index: number, direction: 'up' | 'down') => {
    const items = [...(formData.selectedResolutions || [])];
    const targetIdx = direction === 'up' ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= items.length) return;

    const temp = items[index];
    items[index] = items[targetIdx];
    items[targetIdx] = temp;

    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const removeResolutionItem = (index: number) => {
    const items = [...(formData.selectedResolutions || [])];
    items.splice(index, 1);
    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const handleTextChange = (index: number, text: string) => {
    const items = [...(formData.selectedResolutions || [])];
    items[index].text = text;
    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const saveCurrentTextAsTemplate = async () => {
    if (!resTemplateName?.trim() || !formData.resolutions?.trim()) return;
    setIsSaving(true);
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
        if (setResolutionTemplates) {
          setResolutionTemplates(prev => [...prev, data]);
        }
        if (setResTemplateName) setResTemplateName('');
        toast && toast({ title: 'Success', description: 'Resolution template saved successfully!' });
      }
    } catch (err) {
      toast && toast({ title: 'Error', description: 'Failed to save resolution template', variant: 'destructive' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* 1. SEARCH & ADD RESOLUTION TEMPLATES */}
      <Card className="border border-slate-200 shadow-xs rounded-xl bg-white">
        <CardHeader className="border-b border-slate-100 pb-4">
          <CardTitle className="text-base font-bold text-slate-900 flex items-center justify-between">
            <span>Meeting Resolutions Library</span>
            <span className="text-xs font-normal text-slate-500">{resolutionTemplates.length} templates available</span>
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Type to search stored resolutions by title or keyword and add them to the meeting agenda.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          
          {/* Type Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search resolution title or keyword (e.g. Auditor, Financials, Dividend)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-10 bg-white border-slate-200 text-xs rounded-lg focus:border-blue-500"
            />
          </div>

          {/* Filtered Templates Selection Grid */}
          <div className="max-h-48 overflow-y-auto space-y-2 border border-slate-100 rounded-lg p-2 bg-slate-50/50">
            {filteredTemplates.length === 0 ? (
              <div className="text-center py-4 text-xs text-slate-400">
                {searchQuery ? "No resolution templates match your search." : "No resolution templates found."}
              </div>
            ) : (
              filteredTemplates.map((template: any) => (
                <div
                  key={template.id}
                  className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg hover:border-blue-300 transition-colors shadow-2xs"
                >
                  <div className="flex items-center gap-2.5 flex-1 min-w-0 pr-3">
                    <FileText className="h-4 w-4 text-blue-600 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-bold text-slate-800 truncate">{template.template_name}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-md">{template.resolution_text}</div>
                    </div>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => addResolutionFromTemplate(template)}
                    className="h-7 px-3 text-xs font-semibold rounded-md border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 shrink-0"
                  >
                    <Plus className="h-3 w-3 mr-1" /> Add Item
                  </Button>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* 2. RESOLUTION ITEM SEQUENCING (RE-ORDERING) & FORMAT PRESERVATION */}
      <Card className="border border-slate-200 shadow-xs rounded-xl bg-white">
        <CardHeader className="border-b border-slate-100 pb-4">
          <CardTitle className="text-base font-bold text-slate-900">Agenda & Resolution Items (Re-ordering & Formatting)</CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Sequence your resolutions in order of discussion using the Up/Down controls. Text and table formatting is preserved.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-6">

          {/* List of Sequenced Resolution Items */}
          {formData.selectedResolutions && formData.selectedResolutions.length > 0 ? (
            <div className="space-y-4">
              {formData.selectedResolutions.map((item: any, index: number) => (
                <div
                  key={item.id || index}
                  className="border border-slate-200 rounded-xl p-4 bg-slate-50/40 space-y-3 shadow-2xs"
                >
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-xs font-bold text-slate-800 flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px]">
                        {index + 1}
                      </span>
                      {item.title || `Resolution Item ${index + 1}`}
                    </span>

                    {/* Re-ordering Controls */}
                    <div className="flex items-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={index === 0}
                        onClick={() => moveResolution(index, 'up')}
                        className="h-7 w-7 p-0 rounded-md hover:bg-slate-200 text-slate-600 disabled:opacity-30"
                        title="Move Up"
                      >
                        <ArrowUp className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={index === formData.selectedResolutions.length - 1}
                        onClick={() => moveResolution(index, 'down')}
                        className="h-7 w-7 p-0 rounded-md hover:bg-slate-200 text-slate-600 disabled:opacity-30"
                        title="Move Down"
                      >
                        <ArrowDown className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeResolutionItem(index)}
                        className="h-7 w-7 p-0 rounded-md hover:bg-red-100 text-red-600"
                        title="Remove Resolution"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>

                  <textarea
                    rows={4}
                    className="w-full p-3 border border-slate-200 rounded-lg text-xs font-serif bg-white focus:outline-none focus:border-blue-500 leading-relaxed"
                    style={{ whiteSpace: 'pre-wrap' }}
                    value={item.text}
                    onChange={(e) => handleTextChange(index, e.target.value)}
                    placeholder="Enter full statutory resolution text (table/list formatting preserved)..."
                  />
                </div>
              ))}
            </div>
          ) : null}

          {/* Full Compiled Resolution Output Area */}
          <div className="space-y-2 pt-2">
            <Label htmlFor="resolutionsText" className="text-xs font-bold text-slate-800">
              Full Compiled Resolutions Text Block
            </Label>
            <textarea
              id="resolutionsText"
              rows={8}
              className="w-full p-3 border border-slate-200 rounded-lg text-xs font-serif bg-white leading-relaxed focus:border-blue-500 focus:outline-none"
              style={{ whiteSpace: 'pre-wrap' }}
              value={formData.resolutions || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, resolutions: e.target.value }))}
              placeholder="Full text of all resolutions passed during the meeting (preserves line breaks, tabs, and tables)..."
            />
          </div>

          {/* Save Current Resolutions as New Template */}
          <div className="border-t border-slate-100 pt-4 space-y-3">
            <Label className="text-xs font-bold text-slate-800">Save Current Text as Custom Template</Label>
            <div className="flex gap-3">
              <Input
                placeholder="Enter template name (e.g. Adoption of Accounts 2026)..."
                value={resTemplateName || ''}
                onChange={(e) => setResTemplateName && setResTemplateName(e.target.value)}
                className="bg-white border-slate-200 h-9 rounded-lg text-xs flex-1"
              />
              <Button
                type="button"
                variant="outline"
                disabled={!resTemplateName || !formData.resolutions || isSaving}
                onClick={saveCurrentTextAsTemplate}
                className="h-9 px-4 rounded-lg border-slate-300 text-xs font-semibold bg-white hover:bg-slate-50"
              >
                <CheckCircle2 className="h-3.5 w-3.5 mr-1.5 text-blue-600" />
                {isSaving ? "Saving..." : "Save Template"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
