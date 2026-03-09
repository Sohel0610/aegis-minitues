/**
 * InsiderTradingFilterBar
 * Shared filter UI (Company, Batch, Depository) used across all Insider Trading tabs.
 */
import { Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useInsiderTradingFilters } from "@/contexts/InsiderTradingFilterContext";

const InsiderTradingFilterBar = () => {
    const { filters, filterOptions, setCompany, setBatch, setDepository, clearFilters } = useInsiderTradingFilters();

    if (!filterOptions) return null;

    return (
        <div className="mb-6 bg-white border rounded-md shadow-sm">
            <div className="p-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <Filter className="h-5 w-5 text-[#75479C]" />
                        <div>
                            <h3 className="text-base font-semibold text-gray-900">Filters</h3>
                            <p className="text-xs text-gray-500">Applied across all tabs</p>
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
                        {/* Batch filter */}
                        <Select value={filters.batch} onValueChange={setBatch}>
                            <SelectTrigger className="w-full md:w-[200px] bg-white">
                                <SelectValue placeholder="Select Period" />
                            </SelectTrigger>
                            <SelectContent className="bg-white" style={{ backgroundColor: "#ffffff" }}>
                                {filterOptions.batches.map((b) => (
                                    <SelectItem key={b.batch_name} value={b.batch_name}>
                                        {b.batch_name} {b.older_date && b.latest_date ? `(${b.older_date} → ${b.latest_date})` : ""}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        {/* Company filter */}
                        <Select value={filters.company} onValueChange={setCompany}>
                            <SelectTrigger className="w-full md:w-[220px] bg-white">
                                <SelectValue placeholder="Select Company" />
                            </SelectTrigger>
                            <SelectContent className="bg-white" style={{ backgroundColor: "#ffffff" }}>
                                {filterOptions.companies.map((c) => (
                                    <SelectItem key={c} value={c}>{c}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        {/* Depository filter */}
                        <Select value={filters.depository} onValueChange={setDepository}>
                            <SelectTrigger className="w-full md:w-[160px] bg-white">
                                <SelectValue placeholder="Select Depository" />
                            </SelectTrigger>
                            <SelectContent className="bg-white" style={{ backgroundColor: "#ffffff" }}>
                                {filterOptions.depositories.map((d) => (
                                    <SelectItem key={d} value={d}>{d}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        <Button variant="outline" onClick={clearFilters}>
                            Clear
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InsiderTradingFilterBar;
