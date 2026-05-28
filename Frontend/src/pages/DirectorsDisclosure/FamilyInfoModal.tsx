import { useState, useEffect } from "react";
import { X, Users, Heart, Home, Building2, AlertCircle, Save, Edit3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";

interface FamilyMember {
  relationship: string;
  details: string;
  pan?: string;
}

interface DirectorFamilyInfo {
  director_name: string;
  section_2_77_i: string | null;
  section_2_77_ii: string | null;
  spouse_pan?: string | null;
  section_2_77_iii: string | null;
  family_members: FamilyMember[];
  is_submitted: boolean;
  [key: string]: any;
}

interface FamilyInfoModalProps {
  directorName: string;
  din: string;
  isOpen: boolean;
  onClose: () => void;
}

const FamilyInfoModal = ({ directorName, din, isOpen, onClose }: FamilyInfoModalProps) => {
  const [familyInfo, setFamilyInfo] = useState<DirectorFamilyInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedFamilyInfo, setEditedFamilyInfo] = useState<DirectorFamilyInfo | null>(null);

  const specifiedRelationships = [
    "Father", "Mother", "Son", "Son's Wife",
    "Daughter", "Daughter's Husband", "Brother", "Sister"
  ];

  useEffect(() => {
    if (isOpen && (din || directorName)) {
      fetchFamilyInfo();
    }
  }, [isOpen, din, directorName]);

  const fetchFamilyInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const identifier = din || directorName;
      const response = await fetch(`/api/directors/${encodeURIComponent(identifier)}/family-info`);
      if (!response.ok) {
        if (response.status === 404) {
          setError("No family information found for this director.");
          setLoading(false);
          return;
        }
        throw new Error("Failed to fetch family information");
      }
      const data = await response.json();
      setFamilyInfo(data);
      setEditedFamilyInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      if (!editedFamilyInfo) return;
      const identifier = din || directorName;
      const response = await fetch(`/api/directors/${encodeURIComponent(identifier)}/family-info`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editedFamilyInfo),
      });
      if (!response.ok) throw new Error("Failed to update family information");
      const updatedData = await response.json();
      setFamilyInfo(updatedData);
      setIsEditing(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save changes");
    }
  };

  const handleInputChange = (field: string, value: string) => {
    if (!editedFamilyInfo) return;
    setEditedFamilyInfo({ ...editedFamilyInfo, [field]: value });
  };

  const getRelationshipIcon = (relationship: string) => {
    switch (relationship) {
      case "Father":
      case "Mother":
      case "Brother":
      case "Sister":
        return <Users className="h-4 w-4" style={{ color: "#75479C" }} />;
      default:
        return <Heart className="h-4 w-4" style={{ color: "#BD3861" }} />;
    }
  };

  const getRelationshipColor = (relationship: string) => {
    switch (relationship) {
      case "Father": return "bg-blue-100 text-blue-700";
      case "Mother": return "bg-pink-100 text-pink-700";
      case "Son": return "bg-indigo-100 text-indigo-700";
      case "Daughter": return "bg-rose-100 text-rose-700";
      case "Brother": return "bg-cyan-100 text-cyan-700";
      case "Sister": return "bg-violet-100 text-violet-700";
      default: return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0 border-none shadow-2xl">
        <DialogHeader className="p-6 pb-2 bg-white sticky top-0 z-10 border-b">
          <div className="flex justify-between items-center">
            <div>
              <DialogTitle className="text-2xl font-black tracking-tight" style={{ color: "#000000" }}>
                FAMILY INFORMATION
              </DialogTitle>
              <DialogDescription className="font-medium text-gray-500">
                {directorName} (DIN: {din})
              </DialogDescription>
            </div>
            <div className="flex gap-2">
              {!isEditing ? (
                <Button onClick={() => setIsEditing(true)} className="gap-2 font-black uppercase text-[11px] tracking-wider" style={{ backgroundColor: '#75479C', color: 'white' }}>
                  <Edit3 className="h-4 w-4" />
                  Edit Disclosure
                </Button>
              ) : (
                <>
                  <Button variant="outline" onClick={() => { setEditedFamilyInfo(familyInfo); setIsEditing(false); }} className="font-black uppercase text-[11px] tracking-wider">
                    Cancel
                  </Button>
                  <Button onClick={handleSave} className="gap-2 font-black uppercase text-[11px] tracking-wider" style={{ backgroundColor: '#10B981', color: 'white' }}>
                    <Save className="h-4 w-4" />
                    Save Changes
                  </Button>
                </>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="flex-grow overflow-y-auto p-6 bg-gray-50/50">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mb-4"></div>
              <p className="text-gray-500 font-medium">Fetching secure disclosure data...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12 bg-white rounded-2xl border border-red-100 shadow-sm">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-500" />
              <h3 className="text-lg font-bold mb-2">Notice</h3>
              <p className="text-gray-600 mb-6 px-10">{error}</p>
              <Button onClick={fetchFamilyInfo} variant="outline">Try Again</Button>
            </div>
          ) : editedFamilyInfo ? (
            <div className="space-y-6 pb-10">
              <Card className="border-none shadow-sm overflow-hidden ring-1 ring-gray-100">
                <CardHeader className="bg-white border-b border-gray-50">
                  <CardTitle className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-gray-400">
                    <Building2 className="h-4 w-4" />
                    Regulatory Disclosures (Section 2(77))
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6 space-y-6 bg-white">
                  <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase text-gray-400 tracking-tighter">Section 2(77)(i) – HUF Information</label>
                      {isEditing ? (
                        <Textarea value={editedFamilyInfo.section_2_77_i || ""} onChange={(e) => handleInputChange("section_2_77_i", e.target.value)} className="bg-gray-50/50 border-gray-100 min-h-[80px] text-sm" />
                      ) : (
                        <div className="p-4 rounded-xl bg-gray-50/50 border border-gray-100 text-sm font-medium text-gray-700">{editedFamilyInfo.section_2_77_i || "Nil"}</div>
                      )}
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase text-gray-400 tracking-tighter">Section 2(77)(ii) – Spouse Details</label>
                      {isEditing ? (
                        <div className="space-y-2">
                          <Input value={editedFamilyInfo.section_2_77_ii || ""} onChange={(e) => handleInputChange("section_2_77_ii", e.target.value)} placeholder="Spouse Name" className="bg-gray-50/50 border-gray-100" />
                          <Input value={editedFamilyInfo.spouse_pan || ""} onChange={(e) => handleInputChange("spouse_pan", e.target.value)} placeholder="Spouse PAN" className="bg-gray-50/50 border-gray-100 text-xs" />
                        </div>
                      ) : (
                        <div className="p-4 rounded-xl bg-gray-50/50 border border-gray-100 flex flex-col gap-2">
                          <p className="text-sm font-bold text-gray-800">{editedFamilyInfo.section_2_77_ii || "Nil"}</p>
                          {editedFamilyInfo.spouse_pan && <Badge variant="outline" className="w-fit text-[10px] font-mono border-gray-200">PAN: {editedFamilyInfo.spouse_pan}</Badge>}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-none shadow-sm overflow-hidden ring-1 ring-gray-100">
                <CardHeader className="bg-white border-b border-gray-50">
                  <CardTitle className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-gray-400">
                    <Home className="h-4 w-4" />
                    Immediate Relatives
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6 bg-white">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {specifiedRelationships.map((relationship) => {
                      const members = editedFamilyInfo.family_members.filter(m => m.relationship === relationship);
                      return (
                        <div key={relationship} className="flex flex-col gap-3 p-4 rounded-xl border bg-gray-50/30">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Badge className={`${getRelationshipColor(relationship)} font-black text-[10px] uppercase tracking-wider`}>{relationship}</Badge>
                            </div>
                            {isEditing && (
                              <Button variant="ghost" size="sm" onClick={() => {
                               const newMember = { relationship, details: "", pan: "" };
                               setEditedFamilyInfo({ ...editedFamilyInfo, family_members: [...editedFamilyInfo.family_members, newMember] });
                              }} className="h-6 text-[9px] uppercase font-black text-purple-600">+ ADD</Button>
                            )}
                          </div>
                          <div className="space-y-4 pt-1">
                            {members.length > 0 ? members.map((member, idx) => {
                              const absIdx = editedFamilyInfo.family_members.indexOf(member);
                              return (
                                <div key={idx} className="space-y-2 pb-3 last:pb-0 border-b last:border-0 border-gray-100">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">{relationship} {members.length > 1 ? (idx + 1) : ""}</span>
                                    {isEditing && members.length > 1 && (
                                      <Button variant="ghost" size="icon" className="h-4 w-4 text-red-300 hover:text-red-500" onClick={() => {
                                        const newMembers = [...editedFamilyInfo.family_members];
                                        newMembers.splice(absIdx, 1);
                                        setEditedFamilyInfo({ ...editedFamilyInfo, family_members: newMembers });
                                      }}><X size={10} /></Button>
                                    )}
                                  </div>
                                  {isEditing ? (
                                    <div className="space-y-2">
                                      <Input value={member.details} onChange={(e) => {
                                        const newMembers = [...editedFamilyInfo.family_members];
                                        newMembers[absIdx] = { ...member, details: e.target.value };
                                        setEditedFamilyInfo({ ...editedFamilyInfo, family_members: newMembers });
                                      }} placeholder="Full Name" className="text-sm bg-white h-9" />
                                      <Input value={member.pan || ""} onChange={(e) => {
                                        const newMembers = [...editedFamilyInfo.family_members];
                                        newMembers[absIdx] = { ...member, pan: e.target.value };
                                        setEditedFamilyInfo({ ...editedFamilyInfo, family_members: newMembers });
                                      }} placeholder="PAN" className="text-[10px] h-7 bg-white/50 border-dashed" />
                                    </div>
                                  ) : (
                                    <div className="flex flex-col gap-1">
                                      <p className="text-sm font-bold text-gray-800">{member.details || "Not specified"}</p>
                                      {member.pan && <Badge variant="outline" className="w-fit text-[9px] font-mono py-0 h-4 border-blue-50 text-blue-500 bg-blue-50/30">PAN: {member.pan}</Badge>}
                                    </div>
                                  )}
                                </div>
                              );
                            }) : <p className="text-[11px] text-gray-400 italic">No record found</p>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Users className="h-12 w-12 text-gray-200 mb-4" />
              <h3 className="text-lg font-bold text-gray-800">No Profile Data</h3>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FamilyInfoModal;
