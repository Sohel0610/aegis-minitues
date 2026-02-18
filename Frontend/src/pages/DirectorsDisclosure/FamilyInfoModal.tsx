import { useState, useEffect } from "react";
import { X, User, Users, Heart, Home, Building2, FileText, AlertCircle, Save, Edit3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  pan_number?: string;
}

interface DirectorFamilyInfo {
  director_name: string;
  matched_family_name: string;
  match_score: number;
  section_2_77_i: string | null;
  section_2_77_ii: string | null;
  section_2_77_ii_pan?: string | null;
  section_2_77_iii: string | null;
  family_members: FamilyMember[];
  created_at: string;
}

interface FamilyInfoModalProps {
  directorName: string;
  isOpen: boolean;
  onClose: () => void;
}

const FamilyInfoModal = ({ directorName, isOpen, onClose }: FamilyInfoModalProps) => {
  const [familyInfo, setFamilyInfo] = useState<DirectorFamilyInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedFamilyInfo, setEditedFamilyInfo] = useState<DirectorFamilyInfo | null>(null);

  // Define the specific family relationships to display as per project specification
  const specifiedRelationships = [
    "Father", "Mother", "Son", "Son's Wife",
    "Daughter", "Daughter's Husband", "Brother", "Sister"
  ];

  useEffect(() => {
    if (isOpen && directorName) {
      fetchFamilyInfo();
    }
  }, [isOpen, directorName]);

  const fetchFamilyInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/directors/${encodeURIComponent(directorName)}/family-info`);

      if (!response.ok) {
        if (response.status === 404) {
          // Initialize with empty family info if not found
          const emptyFamilyInfo: DirectorFamilyInfo = {
            director_name: directorName,
            matched_family_name: "",
            match_score: 0,
            section_2_77_i: null,
            section_2_77_ii: null,
            section_2_77_iii: null,
            family_members: [],
            created_at: new Date().toISOString()
          };
          setFamilyInfo(emptyFamilyInfo);
          setEditedFamilyInfo(emptyFamilyInfo);
        } else {
          setError("Failed to fetch family information");
        }
        return;
      }

      const data = await response.json();
      setFamilyInfo(data);
      setEditedFamilyInfo(data);
    } catch (err) {
      console.error("Error fetching family info:", err);
      setError("An error occurred while fetching family information");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      if (!editedFamilyInfo) return;

      const response = await fetch(`/api/directors/${encodeURIComponent(directorName)}/family-info`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          section_2_77_i: editedFamilyInfo.section_2_77_i,
          section_2_77_ii: editedFamilyInfo.section_2_77_ii,
          section_2_77_ii_pan: editedFamilyInfo.section_2_77_ii_pan,
          section_2_77_iii: editedFamilyInfo.section_2_77_iii,
          family_members: editedFamilyInfo.family_members
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save family information');
      }

      const updatedData = await response.json();
      setFamilyInfo(updatedData);
      setEditedFamilyInfo(updatedData);
      setIsEditing(false);
    } catch (err) {
      console.error("Error saving family info:", err);
      setError("An error occurred while saving family information");
    }
  };

  const handleInputChange = (field: keyof DirectorFamilyInfo, value: string | null) => {
    if (editedFamilyInfo) {
      setEditedFamilyInfo({
        ...editedFamilyInfo,
        [field]: value
      });
    }
  };

  const handleFamilyMemberChange = (relationship: string, field: keyof FamilyMember, value: string) => {
    if (editedFamilyInfo) {
      // Find member by relationship
      const existingIndex = editedFamilyInfo.family_members.findIndex(
        member => member.relationship === relationship
      );

      if (existingIndex >= 0) {
        // Update existing member
        const updatedMembers = [...editedFamilyInfo.family_members];
        updatedMembers[existingIndex] = {
          ...updatedMembers[existingIndex],
          [field]: value
        };

        setEditedFamilyInfo({
          ...editedFamilyInfo,
          family_members: updatedMembers
        });
      } else {
        // Add new member if it has content
        if (value.trim() !== "") {
          const newMember: FamilyMember = {
            relationship,
            details: field === 'details' ? value : "",
            pan_number: field === 'pan_number' ? value : ""
          };

          setEditedFamilyInfo({
            ...editedFamilyInfo,
            family_members: [...editedFamilyInfo.family_members, newMember]
          });
        }
      }
    }
  };

  const addAdditionalMember = () => {
    if (editedFamilyInfo) {
      const newMember: FamilyMember = {
        relationship: "Other",
        details: "",
        pan_number: ""
      };
      setEditedFamilyInfo({
        ...editedFamilyInfo,
        family_members: [...editedFamilyInfo.family_members, newMember]
      });
    }
  };

  const removeAdditionalMember = (index: number) => {
    if (editedFamilyInfo) {
      const updatedMembers = [...editedFamilyInfo.family_members];
      updatedMembers.splice(index, 1);
      setEditedFamilyInfo({
        ...editedFamilyInfo,
        family_members: updatedMembers
      });
    }
  };

  const updateMemberRelationship = (oldRelationship: string, newRelationship: string) => {
    if (editedFamilyInfo) {
      const updatedMembers = editedFamilyInfo.family_members.map(member =>
        member.relationship === oldRelationship ? { ...member, relationship: newRelationship } : member
      );
      setEditedFamilyInfo({
        ...editedFamilyInfo,
        family_members: updatedMembers
      });
    }
  };


  const getRelationshipIcon = (relationship: string) => {
    switch (relationship.toLowerCase()) {
      case "father":
        return <User className="h-4 w-4" />;
      case "mother":
        return <User className="h-4 w-4" />;
      case "son":
        return <User className="h-4 w-4" />;
      case "daughter":
        return <User className="h-4 w-4" />;
      case "brother":
        return <Users className="h-4 w-4" />;
      case "sister":
        return <Users className="h-4 w-4" />;
      case "wife":
      case "son's wife":
        return <Heart className="h-4 w-4" />;
      case "husband":
      case "daughter's husband":
        return <Heart className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getRelationshipColor = (relationship: string) => {
    switch (relationship.toLowerCase()) {
      case "father":
      case "mother":
        return "bg-blue-100 text-blue-800";
      case "son":
      case "daughter":
        return "bg-green-100 text-green-800";
      case "brother":
      case "sister":
        return "bg-purple-100 text-purple-800";
      case "wife":
      case "husband":
      case "son's wife":
      case "daughter's husband":
        return "bg-pink-100 text-pink-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Get the details for a specific relationship
  const getFamilyMember = (relationship: string): FamilyMember | null => {
    if (!editedFamilyInfo) return null;

    return editedFamilyInfo.family_members.find(
      m => m.relationship === relationship
    ) || null;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-white">
        <DialogHeader>
          <div className="flex justify-between items-center pr-12">
            <DialogTitle className="flex items-center gap-3 text-xl" style={{ color: '#75479C' }}>
              <Users className="h-6 w-6" />
              Family Information
            </DialogTitle>
            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <Button
                    onClick={handleSave}
                    className="gap-2"
                    style={{
                      backgroundColor: '#0B74B0',
                      borderColor: '#0B74B0',
                      color: 'white'
                    }}
                  >
                    <Save className="h-4 w-4" />
                    Save
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIsEditing(false);
                      setEditedFamilyInfo(familyInfo);
                    }}
                  >
                    Cancel
                  </Button>
                </>
              ) : (
                <Button
                  onClick={() => setIsEditing(true)}
                  className="gap-2"
                  style={{
                    backgroundColor: '#75479C',
                    borderColor: '#75479C',
                    color: 'white'
                  }}
                >
                  <Edit3 className="h-4 w-4" />
                  Edit
                </Button>
              )}
            </div>
          </div>
          <DialogDescription style={{ color: '#666666' }}>
            {directorName}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <span className="ml-2">Loading family information...</span>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 mx-auto mb-4" style={{ color: "#EF4444" }} />
              <h3 className="text-lg font-semibold mb-2" style={{ color: "#000000" }}>Family Information Not Available</h3>
              <p className="mb-4" style={{ color: "#666666" }}>{error}</p>
              <Button
                onClick={fetchFamilyInfo}
                style={{
                  backgroundColor: '#75479C',
                  borderColor: '#75479C',
                  color: 'white'
                }}
              >
                Retry
              </Button>
            </div>
          ) : editedFamilyInfo ? (
            <div className="prose max-w-none">
              <div className="p-6 rounded-lg border bg-white" style={{ color: '#000000' }}>
                {/* Section 2(77) Information */}
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Building2 className="h-5 w-5" style={{ color: "#0B74B0" }} />
                      Regulatory Disclosures (Section 2(77))
                    </CardTitle>
                    <CardDescription>
                      Information as per Companies Act, 2013
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {isEditing ? (
                      <>
                        <div>
                          <label className="block text-sm font-medium mb-1">Section 2(77)(i) – HUF</label>
                          <Textarea
                            value={editedFamilyInfo.section_2_77_i || ""}
                            onChange={(e) => handleInputChange("section_2_77_i", e.target.value)}
                            placeholder="Enter information for Section 2(77)(i) – HUF"
                            className="min-h-[80px]"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Section 2(77)(i) – Wife’s name</label>
                          <div className="space-y-2">
                            <Textarea
                              value={editedFamilyInfo.section_2_77_ii || ""}
                              onChange={(e) => handleInputChange("section_2_77_ii", e.target.value)}
                              placeholder="Enter Wife's name"
                              className="min-h-[60px]"
                            />
                            <Input
                              value={editedFamilyInfo.section_2_77_ii_pan || ""}
                              onChange={(e) => handleInputChange("section_2_77_ii_pan", e.target.value)}
                              placeholder="Wife's PAN Number (Optional)"
                              className="text-sm"
                            />
                          </div>
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <h4 className="font-medium text-sm mb-1">Section 2(77)(i) – HUF</h4>
                          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                            {editedFamilyInfo.section_2_77_i || "Not specified"}
                          </p>
                        </div>
                        <div>
                          <h4 className="font-medium text-sm mb-1">Section 2(77)(i) – Wife’s name</h4>
                          <div className="bg-gray-50 p-3 rounded space-y-1">
                            <p className="text-sm text-gray-700">
                              {editedFamilyInfo.section_2_77_ii || "Not specified"}
                            </p>
                            {editedFamilyInfo.section_2_77_ii_pan && (
                              <Badge variant="outline" className="text-[10px] py-0 h-4 border-gray-300">
                                PAN: {editedFamilyInfo.section_2_77_ii_pan}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Family Members */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Home className="h-5 w-5" style={{ color: "#BD3861" }} />
                      Family Members
                    </CardTitle>
                    <CardDescription>
                      Immediate and extended family relationships
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {isEditing ? (
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {specifiedRelationships.map((relationship) => (
                            <div key={relationship} className="flex items-start gap-3 p-3 rounded-lg border bg-gray-50/30">
                              <div className="mt-0.5">
                                {getRelationshipIcon(relationship)}
                              </div>
                              <div className="flex-grow">
                                <Badge className={`${getRelationshipColor(relationship)} mb-2`}>
                                  {relationship}
                                </Badge>
                                <div className="space-y-2">
                                  <Input
                                    value={getFamilyMember(relationship)?.details || ""}
                                    onChange={(e) => handleFamilyMemberChange(relationship, 'details', e.target.value)}
                                    placeholder={`Enter ${relationship} Name`}
                                    className="text-sm bg-white"
                                  />
                                  <Input
                                    value={getFamilyMember(relationship)?.pan_number || ""}
                                    onChange={(e) => handleFamilyMemberChange(relationship, 'pan_number', e.target.value)}
                                    placeholder="PAN Number (Optional)"
                                    className="text-xs h-8 bg-white"
                                  />
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Additional Family Members Section */}
                        <div className="pt-4 border-t">
                          <div className="flex justify-between items-center mb-4">
                            <h4 className="font-semibold text-sm">Additional Family Members</h4>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={addAdditionalMember}
                              className="h-8 gap-2 text-xs border-dashed border-gray-400"
                            >
                              <Users className="h-3 w-3" />
                              Add Family Member
                            </Button>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {editedFamilyInfo.family_members
                              .filter(m => !specifiedRelationships.includes(m.relationship))
                              .map((member, idx) => {
                                // Find actual index in full array for removal
                                const actualIdx = editedFamilyInfo.family_members.findIndex(m => m === member);
                                return (
                                  <div key={`extra-${idx}`} className="flex items-start gap-3 p-3 rounded-lg border border-dashed bg-gray-50/10">
                                    <div className="flex-grow space-y-2">
                                      <div className="flex gap-2">
                                        <Input
                                          value={member.relationship}
                                          onChange={(e) => updateMemberRelationship(member.relationship, e.target.value)}
                                          placeholder="Relationship (e.g. Spouse)"
                                          className="text-xs h-7 font-semibold"
                                          style={{ width: '120px' }}
                                        />
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          className="h-7 w-7 text-red-400 hover:text-red-600 ml-auto"
                                          onClick={() => removeAdditionalMember(actualIdx)}
                                        >
                                          <X className="h-3 w-3" />
                                        </Button>
                                      </div>
                                      <Input
                                        value={member.details}
                                        onChange={(e) => handleFamilyMemberChange(member.relationship, 'details', e.target.value)}
                                        placeholder="Name"
                                        className="text-sm"
                                      />
                                      <Input
                                        value={member.pan_number || ""}
                                        onChange={(e) => handleFamilyMemberChange(member.relationship, 'pan_number', e.target.value)}
                                        placeholder="PAN Number (Optional)"
                                        className="text-xs h-8"
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {editedFamilyInfo.family_members.map((member, idx) => (
                          <div key={idx} className="flex items-start gap-3 p-3 rounded-lg border">
                            <div className="mt-1">
                              {getRelationshipIcon(member.relationship)}
                            </div>
                            <div className="flex-grow">
                              <Badge className={`${getRelationshipColor(member.relationship)} mb-1`}>
                                {member.relationship}
                              </Badge>
                              <div>
                                <p className="text-sm font-medium">{member.details || "Not specified"}</p>
                                {member.pan_number && (
                                  <div className="mt-1 flex items-center gap-2">
                                    <Badge variant="outline" className="text-[10px] py-0 h-4 border-gray-300">
                                      PAN: {member.pan_number}
                                    </Badge>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <Users className="h-12 w-12 mx-auto text-gray-400 mb-2" />
              <h3 className="text-lg font-semibold mb-2" style={{ color: "#000000" }}>No Family Information</h3>
              <p style={{ color: "#666666" }}>No family information is available for this director.</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FamilyInfoModal;