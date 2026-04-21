
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { History, Search, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface ChangeLog {
    id: number;
    director_name: string;
    change_type: string;
    description: string;
    changed_at: string;
}

const DirectorDisclosureChanges = () => {
    const [changes, setChanges] = useState<ChangeLog[]>([]);
    const [filteredChanges, setFilteredChanges] = useState<ChangeLog[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState<string>("");

    useEffect(() => {
        fetchChanges();
    }, []);

    useEffect(() => {
        if (searchTerm.trim() === "") {
            setFilteredChanges(changes);
        } else {
            const filtered = changes.filter(
                (change) =>
                    change.director_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    change.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    change.change_type.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredChanges(filtered);
        }
    }, [searchTerm, changes]);

    const fetchChanges = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetch('/api/director-disclosure-changes');

            if (!response.ok) {
                throw new Error('Failed to fetch changes');
            }

            const data = await response.json();
            setChanges(data.data || []);
            setFilteredChanges(data.data || []);
        } catch (err) {
            console.error('Error fetching changes:', err);
            setError(err instanceof Error ? err.message : 'Failed to load changes');
        } finally {
            setLoading(false);
        }
    };

    const getChangeTypeColor = (type: string) => {
        switch (type.toLowerCase()) {
            case 'profile update':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'new disclosure':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'family info update':
                return 'bg-purple-100 text-purple-800 border-purple-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6" style={{ background: "#ffffff" }}>
                <div className="text-center">
                    <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: "#75479C" }} />
                    <p className="text-lg" style={{ color: "#000000" }}>Loading changes...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6" style={{ background: "#ffffff" }}>
                <div className="text-center p-6 max-w-md">
                    <AlertCircle className="h-12 w-12 mx-auto mb-4" style={{ color: "#EF4444" }} />
                    <h2 className="text-xl font-bold mb-2" style={{ color: "#000000" }}>Error Loading Data</h2>
                    <p className="mb-4" style={{ color: "#000000" }}>{error}</p>
                    <Button
                        onClick={fetchChanges}
                        style={{
                            backgroundColor: '#75479C',
                            borderColor: '#75479C',
                            color: 'white'
                        }}
                    >
                        Retry
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-6" style={{ background: "#ffffff" }}>
            <motion.div
                initial={{ opacity: 0, y: -30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white mb-8">
                    <CardHeader className="p-8 border-b border-gray-50 bg-gray-50/10">
                        <div className="flex items-center gap-4 mb-8">
                            <History className="h-9 w-9 text-[#75479C]" />
                            <div>
                                <CardTitle className="text-3xl font-black text-gray-900 tracking-tight">
                                    Director disclosure history
                                </CardTitle>
                                <CardDescription className="text-gray-500 font-medium">
                                    Track comprehensive audit trail of registry modifications
                                </CardDescription>
                            </div>
                        </div>

                        {/* Search Bar */}
                        <div className="flex items-center gap-4">
                            <div className="relative flex-1 w-full max-w-2xl">
                                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <Input
                                    placeholder="Search history by director name or description..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-12 h-14 rounded-2xl border-gray-100 bg-gray-50 focus:bg-white transition-all text-lg"
                                />
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="mb-4 text-sm" style={{ color: '#666666' }}>
                            Showing {filteredChanges.length} of {changes.length} records
                        </div>
                        <div className="rounded-[1.5rem] border border-gray-100 overflow-hidden shadow-sm">
                            <Table>
                                <TableHeader>
                                    <TableRow className="bg-gray-50 active:bg-gray-50">
                                        <TableHead className="py-5 pl-8 text-[10px] font-black text-gray-500 uppercase tracking-widest w-[200px]">Date & time</TableHead>
                                        <TableHead className="py-5 text-[10px] font-black text-gray-500 uppercase tracking-widest w-[250px]">Director name</TableHead>
                                        <TableHead className="py-5 text-[10px] font-black text-gray-500 uppercase tracking-widest w-[180px]">Change type</TableHead>
                                        <TableHead className="py-5 pr-8 text-[10px] font-black text-gray-500 uppercase tracking-widest">Description</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredChanges.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-8" style={{ color: '#666666' }}>
                                                {searchTerm ? 'No changes found matching your search' : 'No changes recorded yet'}
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        filteredChanges.map((change) => (
                                            <TableRow key={change.id} className="hover:bg-gray-50">
                                                <TableCell className="font-medium whitespace-nowrap">
                                                    {new Date(change.changed_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell className="font-medium">{change.director_name}</TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant="outline"
                                                        className={`font-normal ${getChangeTypeColor(change.change_type)}`}
                                                    >
                                                        {change.change_type}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-gray-600">{change.description}</TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
            <footer className="mt-20 pt-10 border-t border-gray-100 text-center opacity-30">
                <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Aegis Institutional Risk & Compliance Terminal</span>
            </footer>
        </div>
    );
};

export default DirectorDisclosureChanges;
