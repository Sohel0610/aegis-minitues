
import React from "react";
import { FileText } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface NotificationDetailsModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    record: any | null;
}

const NotificationDetailsModal: React.FC<NotificationDetailsModalProps> = ({
    isOpen,
    onOpenChange,
    record,
}) => {
    if (!record) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto w-full bg-white">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-3 text-xl font-mono text-[#010741]">
                        <FileText className="h-6 w-6 text-[#E4A6CB]" />
                        Notification Details
                    </DialogTitle>
                    <DialogDescription className="text-[#46798E] font-semibold">
                        Detailed information for the selected notification record
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 mt-4 w-full">
                    {/* Entity Information */}
                    <div className="grid grid-cols-1 gap-4 w-full">
                        <Card className="w-full bg-white border-2 border-[#46798E] shadow-[0_4px_15px_rgba(70,121,142,0.2)]">
                            <CardHeader className="pb-3 bg-[#46798E] rounded-t-lg">
                                <CardTitle className="text-sm font-mono text-white">Entity Details</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3 pt-4">
                                <div>
                                    <span className="text-xs font-mono font-semibold text-[#010741]">Details:</span>
                                    <div className="mt-2 space-y-2">
                                        {Object.entries(record).map(([key, value]) => (
                                            <div key={key} className="text-sm">
                                                <span className="font-medium text-[#46798E]">{key}:</span>{" "}
                                                <span className="text-[#010741]">{String(value)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-between items-center pt-4 border-t w-full">
                        <div className="text-xs font-mono font-semibold text-[#46798E]">
                            Record viewed at {new Date().toLocaleString()}
                        </div>
                        <div className="flex gap-3">
                            <Button
                                onClick={() => onOpenChange(false)}
                                className="font-semibold text-white shadow-[0_3px_12px_rgba(1,7,65,0.3)]"
                                style={{
                                    background: 'linear-gradient(135deg, #010741, #46798E)',
                                    borderColor: '#010741',
                                }}
                            >
                                Close
                            </Button>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default NotificationDetailsModal;
