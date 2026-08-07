/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useMemo } from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Search, X as CloseIcon, Plus } from 'lucide-react';

interface Director {
  id?: number;
  name: string;
  din: string;
  status?: string;
  designation?: string;
  role?: string;
  created_at?: string;
}

interface MultiDirectorSelectorProps {
  id: string;
  label: string;
  value: Director[];
  onChange: (directors: Director[]) => void;
  placeholder?: string;
  companyName?: string;
}

const MultiDirectorSelector: React.FC<MultiDirectorSelectorProps> = ({ 
  id, 
  label, 
  value, 
  onChange, 
  placeholder = "Search director name or DIN...",
  companyName
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [companyDirectors, setCompanyDirectors] = useState<Director[]>([]);
  const [masterDirectors, setMasterDirectors] = useState<Director[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch company-specific directors on mount or when companyName changes
  useEffect(() => {
    if (!companyName) return;

    const fetchCompanyDirectors = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/companies/${encodeURIComponent(companyName)}/directors`);
        if (response.ok) {
          const result = await response.json();
          const directors = Array.isArray(result.data) ? result.data : [];
          const mapped = directors.map((d: any) => ({
            name: d.name,
            din: d.din || '',
            designation: d.designation || d.role || 'Director',
            role: d.designation || d.role || 'Director',
            status: 'Present' as const,
          }));
          setCompanyDirectors(mapped);

          // Auto-select company board when parent list is empty
          if (value.length === 0 && mapped.length > 0) {
            onChange(mapped);
          }
        }
      } catch (err) {
        console.error('Error fetching company directors:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCompanyDirectors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyName]);

  // Fetch master directors when search term is entered
  useEffect(() => {
    if (!searchTerm) {
      setMasterDirectors([]);
      return;
    }
    
    const fetchMasterDirectors = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/directors-master`);
        if (response.ok) {
          const result = await response.json();
          const directors = Array.isArray(result.data) ? result.data : [];
          const mapped = directors.map((d: any) => ({
            name: d.name,
            din: d.din
          }));
          setMasterDirectors(mapped);
        } else {
          setError('Failed to fetch directors');
          setMasterDirectors([]);
        }
      } catch (err) {
        console.error('Error fetching directors:', err);
        setError('Error fetching directors');
        setMasterDirectors([]);
      } finally {
        setIsLoading(false);
      }
    };

    const debounceTimer = setTimeout(() => {
      fetchMasterDirectors();
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const availableDirectors = useMemo(() => {
    const selectedNames = new Set(value.map(d => d.name.toLowerCase()));
    const combined = [...companyDirectors, ...masterDirectors];
    const uniqueMap = new Map<string, Director>();
    
    combined.forEach(d => {
      if (!selectedNames.has(d.name.toLowerCase()) && !uniqueMap.has(d.name.toLowerCase())) {
        uniqueMap.set(d.name.toLowerCase(), d);
      }
    });

    const list = Array.from(uniqueMap.values());
    if (!searchTerm) {
      return list.slice(0, 10);
    }
    const term = searchTerm.toLowerCase();
    return list.filter(d => d.name.toLowerCase().includes(term) || d.din.includes(term)).slice(0, 20);
  }, [companyDirectors, masterDirectors, value, searchTerm]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setSearchTerm(newValue);
    setIsOpen(true);
  };

  const handleDirectorSelect = (director: Director) => {
    if (!value.some(d => d.name.toLowerCase() === director.name.toLowerCase())) {
      onChange([...value, director]);
    }
    setInputValue('');
    setSearchTerm('');
    setIsOpen(false);
  };

  const removeDirector = (index: number) => {
    const newValue = [...value];
    newValue.splice(index, 1);
    onChange(newValue);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputBlur = () => {
    setTimeout(() => setIsOpen(false), 200);
  };

  const unselectedCompanyDirectors = useMemo(() => {
    const selectedNames = new Set(value.map(d => d.name.toLowerCase()));
    return companyDirectors.filter(d => !selectedNames.has(d.name.toLowerCase()));
  }, [companyDirectors, value]);

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <Label htmlFor={id} className="text-xs font-semibold text-slate-700">
          {label}
        </Label>
        <span className="text-[11px] text-slate-500 font-medium">
          {value.length} {value.length === 1 ? 'director' : 'directors'} selected
        </span>
      </div>
      
      {/* Registered Board Members for selected company */}
      {companyName && unselectedCompanyDirectors.length > 0 && (
        <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 space-y-1.5">
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-700">
            <span>Registered Board Members for {companyName}:</span>
            <button
              type="button"
              onClick={() => onChange([...value, ...unselectedCompanyDirectors])}
              className="text-[11px] text-blue-600 hover:underline font-semibold"
            >
              + Add All ({unselectedCompanyDirectors.length})
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {unselectedCompanyDirectors.map((director, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleDirectorSelect(director)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
              >
                <Plus className="h-3 w-3 text-slate-400" />
                {director.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected Directors Chips */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5 p-2 bg-slate-50/50 rounded-lg border border-slate-200/60">
          {value.map((director, index) => (
            <div 
              key={`${director.name}-${index}`} 
              className="flex items-center bg-white border border-slate-200 shadow-2xs rounded-md px-2.5 py-1 text-xs text-slate-800 gap-1.5"
            >
              <span className="font-semibold text-slate-800">{director.name}</span>
              {director.din && (
                <span className="text-[10px] text-slate-400 font-mono">#{director.din}</span>
              )}
              <button
                type="button"
                className="h-4 w-4 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700 transition-colors ml-0.5"
                onClick={() => removeDirector(index)}
              >
                <CloseIcon className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
      
      {/* Input with dropdown */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <Input
            id={id}
            value={inputValue}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            placeholder={placeholder}
            className="pl-9 h-9 bg-white border-slate-200 focus:border-blue-500 rounded-lg text-xs"
          />
        </div>
        
        {isOpen && (isLoading || error || availableDirectors.length > 0) && (
          <Card className="absolute top-full left-0 right-0 mt-1 z-50 max-h-60 overflow-y-auto shadow-2xl bg-white text-slate-900 border border-slate-200 rounded-lg">
            <CardContent className="p-0">
              {isLoading && (
                <div className="p-3 text-center text-xs text-slate-500">
                  Searching directors registry...
                </div>
              )}
              
              {error && (
                <div className="p-3 text-center text-xs text-red-500 font-medium">
                  {error}
                </div>
              )}
              
              {!isLoading && !error && availableDirectors.length > 0 && (
                availableDirectors.map((director, index) => (
                  <div
                    key={`${director.din}-${index}`}
                    className="flex items-center justify-between p-2.5 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-b-0 transition-colors"
                    onMouseDown={() => handleDirectorSelect(director)}
                  >
                    <span className="font-semibold text-xs text-slate-800">{director.name}</span>
                    {director.din && (
                      <span className="text-xs text-slate-400 font-mono">#{director.din}</span>
                    )}
                  </div>
                ))
              )}
              
              {!isLoading && !error && availableDirectors.length === 0 && searchTerm && (
                <div className="p-3 text-center text-xs text-slate-400">
                  No matching directors found.
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MultiDirectorSelector;