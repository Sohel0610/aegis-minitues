import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, ArrowLeft, Lock, Users, Plus, Edit, Trash2 } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useToast } from "@/components/ui/use-toast";
import { useVertical } from '@/contexts/VerticalContext';


interface Director {
  id: number | null;
  name: string;
  din: string;
  created_at?: string;
  source?: 'disclosure' | 'local';
}

export default function MinutesPreparation() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const location = useLocation();
  const { isAuthenticated, canAdmin } = useAuth();
  const { selectedCompany } = useVertical();
  const isAdminMode = canAdmin('/minutes-preparation');
  const [directors, setDirectors] = useState<Director[]>([]);
  const [isLoadingDirectors, setIsLoadingDirectors] = useState(false);
  const [directorsNotice, setDirectorsNotice] = useState('');
  const [places, setPlaces] = useState<any[]>([]);
  const [isLoadingPlaces, setIsLoadingPlaces] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isAddPlaceOpen, setIsAddPlaceOpen] = useState(false);
  const [editingDirector, setEditingDirector] = useState<Director | null>(null);
  const [formData, setFormData] = useState({ name: '', din: '' });
  const [placeFormData, setPlaceFormData] = useState({ name: '', address: '', is_default: false });
  const [submitting, setSubmitting] = useState(false);

  const activeId = location.pathname.includes('/directors') ? 'directors' : location.pathname.includes('/places') ? 'places' : 'dashboard';
  const navigationItems = getMinutesNavItems(activeId);

  // Fetch directors for the selected entity: read-only from Disclosure DB + local manual entries
  const fetchDirectorsData = async () => {
    if (!isAuthenticated) return;
    if (!selectedCompany?.name) {
      setDirectors([]);
      setDirectorsNotice('');
      return;
    }

    setIsLoadingDirectors(true);
    setDirectorsNotice('');
    try {
      const response = await fetch(`/api/companies/${encodeURIComponent(selectedCompany.name)}/directors`);
      if (response.ok) {
        const result = await response.json();
        setDirectors(Array.isArray(result) ? result : (result.data || []));
        setDirectorsNotice(Array.isArray(result) ? '' : (result.message || ''));
      } else {
        console.error('Failed to fetch directors data');
        setDirectors([]);
        setDirectorsNotice('The directors registry could not be loaded.');
      }
    } catch (error) {
      console.error('Error fetching directors data:', error);
      setDirectors([]);
      setDirectorsNotice('The directors registry could not be loaded.');
    } finally {
      setIsLoadingDirectors(false);
    }
  };

  // Fetch places data
  const fetchPlacesData = async () => {
    setIsLoadingPlaces(true);
    try {
      const response = await fetch('/api/places');
      if (response.ok) {
        const result = await response.json();
        setPlaces(result.data || []);
      }
    } catch (error) {
      console.error('Error fetching places:', error);
    } finally {
      setIsLoadingPlaces(false);
    }
  };

  useEffect(() => {
    fetchDirectorsData();
    fetchPlacesData();
  }, [isAuthenticated, selectedCompany?.name]);

  // Handle navigation to form generator
  const handleNavigateToFormGenerator = () => {
    navigate('/minutes-preparation/form-generator');
  };

  // Filter directors based on search term
  const filteredDirectors = directors.filter(director =>
    director.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (director.din || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAddDirector = async () => {
    if (!formData.name.trim()) {
      toast({ title: "Validation Error", description: "Director name is required", variant: "destructive" });
      return;
    }
    if (!selectedCompany?.name) {
      toast({ title: "No Entity Selected", description: "Please select an entity first (Switch Entity)", variant: "destructive" });
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch(`/api/companies/${encodeURIComponent(selectedCompany.name)}/directors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Failed to add director');

      await fetchDirectorsData();
      setIsAddDialogOpen(false);
      setFormData({ name: '', din: '' });
    } catch (err) {
      console.error('Error adding director:', err);
      toast({ title: "Error", description: "Failed to add director", variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditDirector = async () => {
    if (!editingDirector || !formData.name.trim()) {
      toast({ title: "Validation Error", description: "Director name is required", variant: "destructive" });
      return;
    }
    if (editingDirector.source !== 'local' || editingDirector.id == null || !selectedCompany?.name) {
      toast({ title: "Read-only", description: "Registry directors from the Disclosure database cannot be edited", variant: "destructive" });
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch(`/api/companies/${encodeURIComponent(selectedCompany.name)}/directors/${editingDirector.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Failed to update director');

      await fetchDirectorsData();
      setIsEditDialogOpen(false);
      setEditingDirector(null);
      setFormData({ name: '', din: '' });
    } catch (err) {
      console.error('Error updating director:', err);
      toast({ title: "Error", description: "Failed to update director", variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteDirector = async (director: Director) => {
    if (director.source !== 'local' || director.id == null || !selectedCompany?.name) {
      toast({ title: "Read-only", description: "Registry directors from the Disclosure database cannot be deleted", variant: "destructive" });
      return;
    }
    if (!confirm('Are you sure you want to delete this director?')) return;

    try {
      const response = await fetch(`/api/companies/${encodeURIComponent(selectedCompany.name)}/directors/${director.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to delete director');

      await fetchDirectorsData();
    } catch (err) {
      console.error('Error deleting director:', err);
      toast({ title: "Error", description: "Failed to delete director", variant: "destructive" });
    }
  };

  const openEditDialog = (director: Director) => {
    setEditingDirector(director);
    setFormData({ name: director.name, din: director.din });
    setIsEditDialogOpen(true);
  };

  const handleAddPlace = async () => {
    if (!placeFormData.name.trim() || !placeFormData.address.trim()) {
      toast({ title: "Validation Error", description: "Please fill in place name and address", variant: "destructive" });
      return;
    }
    try {
      setSubmitting(true);
      const res = await fetch('/api/places', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(placeFormData)
      });
      if (res.ok) {
        toast({ title: "Success", description: "Meeting place added successfully" });
        setIsAddPlaceOpen(false);
        setPlaceFormData({ name: '', address: '', is_default: false });
        fetchPlacesData();
      }
    } catch (err) {
      toast({ title: "Error", description: "Failed to add place", variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePlace = async (id: number) => {
    if (!confirm('Are you sure you want to delete this meeting place?')) return;
    try {
      const res = await fetch(`/api/places/${id}`, { method: 'DELETE' });
      if (res.ok) {
        toast({ title: "Success", description: "Meeting place deleted" });
        fetchPlacesData();
      }
    } catch (err) {
      toast({ title: "Error", description: "Failed to delete place", variant: "destructive" });
    }
  };

  return (
    <ProductDashboardLayout
      productName="Governance Records"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="container mx-auto py-4">
        {/* Places List Section */}
        {location.pathname === '/minutes-preparation/places' ? (
          <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-4">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Meeting Places Master</h1>
                <p className="text-xs text-slate-500">Manage statutory meeting locations across Adani Business Units</p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => {
                    setPlaceFormData({ name: '', address: '', is_default: false });
                    setIsAddPlaceOpen(true);
                  }}
                  className="gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs h-9"
                >
                  <Plus className="h-4 w-4" /> Add Meeting Place
                </Button>
              </div>
            </div>

            <Card className="border border-slate-200 shadow-xs bg-white rounded-xl">
              <CardContent className="p-0">
                {isLoadingPlaces ? (
                  <div className="p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto"></div>
                    <p className="mt-2 text-xs text-slate-500">Loading meeting places...</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-200 bg-slate-50">
                          <th className="px-4 py-3 font-semibold text-slate-800 text-xs">Place Name</th>
                          <th className="px-4 py-3 font-semibold text-slate-800 text-xs">Full Address</th>
                          <th className="px-4 py-3 font-semibold text-slate-800 text-xs text-center">Default</th>
                          <th className="px-4 py-3 font-semibold text-slate-800 text-xs text-center">Actions</th>
                        </tr>
                      </thead>
                        <tbody className="divide-y divide-slate-100 bg-white">
                          {places.length > 0 ? (
                            places.map((place) => (
                              <tr key={place.id} className="hover:bg-slate-50 transition-colors">
                                <td className="px-4 py-3 font-bold text-slate-900 text-xs">{place.name}</td>
                                <td className="px-4 py-3 text-slate-600 text-xs">{place.address}</td>
                                <td className="px-4 py-3 text-center">
                                  {place.is_default ? (
                                    <span className="bg-green-100 text-green-800 text-[10px] font-bold px-2 py-0.5 rounded-full">Default</span>
                                  ) : (
                                    <span className="text-slate-400 text-xs">-</span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-center">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleDeletePlace(place.id)}
                                    className="h-8 px-2 text-red-600 hover:bg-red-50 text-xs font-semibold"
                                  >
                                    <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                                  </Button>
                                </td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={4} className="text-center py-8 text-slate-500 text-xs">
                                No meeting places defined yet. Click "Add Meeting Place" to create one.
                              </td>
                            </tr>
                          )}
                        </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : location.pathname === '/minutes-preparation/directors' && isAuthenticated ? (
          <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-4">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Directors Registry</h1>
                <p className="text-xs text-slate-500">
                  {selectedCompany?.name
                    ? `Directors of ${selectedCompany.name} — registry data is read-only; manual additions are stored locally`
                    : 'Select an entity (Switch Entity) to view its board directors'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Search directors..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full md:w-64"
                />
                <Button
                  onClick={() => {
                    setFormData({ name: '', din: '' });
                    setIsAddDialogOpen(true);
                  }}
                  className="gap-2 whitespace-nowrap"
                >
                  <Plus className="h-4 w-4" />
                  Add Director
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                {isLoadingDirectors ? (
                  <div className="p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
                    <p className="mt-2">Loading directors...</p>
                  </div>
                ) : (
                  <div className="max-h-[calc(100vh-200px)] overflow-y-auto rounded-md border border-slate-200">
                    <table className="w-full text-sm text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="sticky top-0 bg-slate-100/95 backdrop-blur-sm px-4 py-3 font-semibold text-slate-800 z-30 shadow-sm border-b border-slate-200">Name</th>
                          <th className="sticky top-0 bg-slate-100/95 backdrop-blur-sm px-4 py-3 font-semibold text-slate-800 z-30 shadow-sm border-b border-slate-200">DIN</th>
                          <th className="sticky top-0 bg-slate-100/95 backdrop-blur-sm px-4 py-3 font-semibold text-slate-800 z-30 shadow-sm border-b border-slate-200">Source</th>
                          <th className="sticky top-0 bg-slate-100/95 backdrop-blur-sm px-4 py-3 font-semibold text-slate-800 z-30 shadow-sm border-b border-slate-200 text-center">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {filteredDirectors.length > 0 ? (
                          filteredDirectors.map((director, idx) => (
                            <tr key={director.id != null ? `local-${director.id}` : `reg-${idx}`} className="hover:bg-slate-50 transition-colors">
                              <td className="px-4 py-3 font-medium text-slate-900">{director.name}</td>
                              <td className="px-4 py-3 text-slate-600">{director.din || '—'}</td>
                              <td className="px-4 py-3 text-slate-600">
                                {director.source === 'local' ? (
                                  <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700 border border-blue-200">Manual</span>
                                ) : (
                                  <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-600 border border-slate-200">Registry</span>
                                )}
                              </td>
                              <td className="px-4 py-3">
                                <div className="flex gap-2 justify-center">
                                  {director.source === 'local' ? (
                                    <>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => openEditDialog(director)}
                                        className="gap-1 h-8 text-xs"
                                      >
                                        <Edit className="h-3 w-3" />
                                        Edit
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="destructive"
                                        onClick={() => handleDeleteDirector(director)}
                                        className="gap-1 h-8 text-xs bg-red-500 hover:bg-red-600"
                                      >
                                        <Trash2 className="h-3 w-3" />
                                        Delete
                                      </Button>
                                    </>
                                  ) : (
                                    <span className="text-xs text-slate-400 flex items-center gap-1"><Lock className="h-3 w-3" /> Read-only</span>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={4} className="text-center py-8 text-slate-500">
                              {!selectedCompany?.name
                                ? 'Please select an entity using "Switch Entity" to view its directors.'
                                : searchTerm
                                  ? 'No directors found matching your search.'
                                  : directorsNotice || `No director relationships are stored for ${selectedCompany.name}.`}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

        ) : (
          <>
            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8 max-w-5xl mx-auto">
              {/* Generate Minutes Card */}
              <Card className="hover:shadow-lg transition-all hover:border-blue-300 group cursor-pointer" onClick={handleNavigateToFormGenerator}>
                <CardHeader>
                  <div className="flex justify-center mb-4 p-3 bg-blue-50 rounded-full w-fit mx-auto group-hover:bg-blue-100 transition-colors">
                    <FileText className="h-10 w-10 text-blue-500" />
                  </div>
                  <CardTitle className="text-center">Generate Minutes</CardTitle>
                  <CardDescription className="text-center group-hover:text-blue-600">
                    Create professional meeting minutes from templates
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-center">
                  <Button className="w-full">Open Generator</Button>
                </CardContent>
              </Card>

              {/* Chatbot Card */}
              <Card className="hover:shadow-lg transition-all hover:border-purple-300 group cursor-pointer" onClick={() => navigate('/minutes-preparation/chatbot')}>
                <CardHeader>
                  <div className="flex justify-center mb-4 p-3 bg-purple-50 rounded-full w-fit mx-auto group-hover:bg-purple-100 transition-colors">
                    <FileText className="h-10 w-10 text-purple-500" />
                  </div>
                  <CardTitle className="text-center">Meeting Assistant</CardTitle>
                  <CardDescription className="text-center group-hover:text-purple-600">
                    Interact with your meeting data using AI
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-center">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700">Open Chatbot</Button>
                </CardContent>
              </Card>
            </div>

            {/* Information Section */}
            <Card className="max-w-4xl mx-auto mt-12">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl">Minutes Generation</CardTitle>
                <CardDescription>
                  Generate professional meeting minutes with our template-based system
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="mb-4">
                  This tool allows you to generate meeting minutes quickly and efficiently using predefined templates.
                </p>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">How it works:</h3>
                  <ul className="text-left list-disc pl-5 space-y-1 text-sm">
                    <li>Select a quarterly template (Q1-Q4)</li>
                    <li>Fill in the required information in the form</li>
                    <li>Generate and download your professional meeting minutes document</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>



      {/* Add Director Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent className="bg-white">
          <DialogHeader>
            <DialogTitle>Add New Director</DialogTitle>
            <DialogDescription>
              Enter the details of the new director below.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="add-name">Director Name *</Label>
              <Input
                id="add-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter director name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-din">DIN *</Label>
              <Input
                id="add-din"
                value={formData.din}
                onChange={(e) => setFormData(prev => ({ ...prev, din: e.target.value }))}
                placeholder="Enter DIN number"
                maxLength={8}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setIsAddDialogOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddDirector}
              disabled={submitting}
            >
              {submitting ? 'Adding...' : 'Add Director'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Director Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="bg-white">
          <DialogHeader>
            <DialogTitle>Edit Director</DialogTitle>
            <DialogDescription>
              Update the director's information below.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Director Name *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter director name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-din">DIN *</Label>
              <Input
                id="edit-din"
                value={formData.din}
                onChange={(e) => setFormData(prev => ({ ...prev, din: e.target.value }))}
                placeholder="Enter DIN number"
                maxLength={8}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setIsEditDialogOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleEditDirector}
              disabled={submitting}
            >
              {submitting ? 'Updating...' : 'Update Director'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Meeting Place Dialog */}
      <Dialog open={isAddPlaceOpen} onOpenChange={setIsAddPlaceOpen}>
        <DialogContent className="bg-white">
          <DialogHeader>
            <DialogTitle>Add Meeting Place</DialogTitle>
            <DialogDescription>
              Enter details for the new meeting location.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="place-name">Place / Venue Name *</Label>
              <Input
                id="place-name"
                value={placeFormData.name}
                onChange={(e) => setPlaceFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g. Adani Corporate House"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="place-address">Full Address *</Label>
              <Input
                id="place-address"
                value={placeFormData.address}
                onChange={(e) => setPlaceFormData(prev => ({ ...prev, address: e.target.value }))}
                placeholder="e.g. Shantigram, Near Vaishnodevi Circle, SG Highway, Ahmedabad - 382421"
              />
            </div>
            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="place-default"
                checked={placeFormData.is_default}
                onChange={(e) => setPlaceFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <Label htmlFor="place-default" className="text-xs text-slate-700 cursor-pointer">
                Set as default meeting place for new minutes
              </Label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setIsAddPlaceOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddPlace}
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {submitting ? 'Saving...' : 'Save Place'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </ProductDashboardLayout>
  );
};
