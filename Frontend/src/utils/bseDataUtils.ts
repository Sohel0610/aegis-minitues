
import { ExcelData } from "@/services/bseAlertsService";

// Helper to parse date strings
export const parseDate = (dateStr: string | number | Date): Date | null => {
    if (!dateStr) return null;

    try {
        if (dateStr instanceof Date) return dateStr;
        if (typeof dateStr === 'number') return new Date(dateStr);

        // String parsing
        if (typeof dateStr === 'string') {
            const trimmedStr = dateStr.trim();

            // YYYY-MM-DD
            if (/^\d{4}-\d{2}-\d{2}$/.test(trimmedStr)) {
                return new Date(trimmedStr);
            }

            // DD-MM-YYYY
            if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(trimmedStr)) {
                const [day, month, year] = trimmedStr.split('-').map(Number);
                return new Date(year, month - 1, day);
            }

            // MM/DD/YYYY
            if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(trimmedStr)) {
                const [month, day, year] = trimmedStr.split('/').map(Number);
                return new Date(year, month - 1, day);
            }

            // YYYY/MM/DD
            if (/^\d{4}\/\d{1,2}\/\d{1,2}$/.test(trimmedStr)) {
                const [year, month, day] = trimmedStr.split('/').map(Number);
                return new Date(year, month - 1, day);
            }

            const date = new Date(trimmedStr);
            if (!isNaN(date.getTime())) return date;
        }
    } catch (e) {
        console.error("Error parsing date:", dateStr, e);
    }

    return null;
};

// Process data for charts
export const processDataForBSEData = (data: any[]) => {
    // Group data by date for daily trend
    const dailyMap: { [key: string]: number } = {};

    data.forEach(item => {
        const date = item.date_key;
        if (date) {
            if (!dailyMap[date]) {
                dailyMap[date] = 0;
            }
            dailyMap[date] += 1;
        }
    });

    // Convert to array format for daily data and sort by date
    let dailyChartData = Object.keys(dailyMap).map(date => ({
        date,
        total_notifications: dailyMap[date]
    })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    // Get the latest date to determine the latest month
    let latestDateObj: Date | null = null;
    if (dailyChartData.length > 0) {
        latestDateObj = new Date(dailyChartData[dailyChartData.length - 1].date);
    }

    // Filter daily data to only show the latest month
    let filteredDailyChartData = dailyChartData;
    if (latestDateObj) {
        const latestMonth = latestDateObj.getMonth();
        const latestYear = latestDateObj.getFullYear();

        filteredDailyChartData = dailyChartData.filter(item => {
            const itemDate = new Date(item.date);
            return itemDate.getMonth() === latestMonth && itemDate.getFullYear() === latestYear;
        });
    }

    // Group data by month/year for monthly chart (all months across all years)
    const monthlyMap: { [key: string]: number } = {};
    const monthYearSet = new Set<string>();

    data.forEach(item => {
        const date = item.date_key;
        if (date) {
            try {
                const parts = date.split('-');
                if (parts.length === 3) {
                    const year = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1;
                    const day = parseInt(parts[2], 10);

                    const dateObj = new Date(year, month, day);
                    if (!isNaN(dateObj.getTime())) {
                        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                        const monthName = monthNames[month] || 'Unknown';
                        const key = `${monthName}-${year}`;

                        monthYearSet.add(key);

                        if (!monthlyMap[key]) {
                            monthlyMap[key] = 0;
                        }
                        monthlyMap[key] += 1;
                    }
                }
            } catch (e) {
                console.error("Error parsing date for monthly data:", date, e);
            }
        }
    });

    const sortedMonthYears = Array.from(monthYearSet).sort((a, b) => {
        const [monthA, yearA] = a.split('-');
        const [monthB, yearB] = b.split('-');

        if (yearA !== yearB) {
            return parseInt(yearA) - parseInt(yearB);
        }

        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return monthNames.indexOf(monthA) - monthNames.indexOf(monthB);
    });

    let minYear = Infinity;
    let maxYear = -Infinity;

    if (sortedMonthYears.length > 0) {
        sortedMonthYears.forEach(key => {
            const [, year] = key.split('-');
            const yearNum = parseInt(year);
            if (yearNum < minYear) minYear = yearNum;
            if (yearNum > maxYear) maxYear = yearNum;
        });

        const completeMonthYearSet = new Set<string>();
        for (let year = minYear; year <= maxYear; year++) {
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            monthNames.forEach(month => {
                completeMonthYearSet.add(`${month}-${year}`);
            });
        }

        completeMonthYearSet.forEach(key => {
            if (!monthlyMap[key]) {
                monthlyMap[key] = 0;
            }
        });

        const completeSortedMonthYears = Array.from(completeMonthYearSet).sort((a, b) => {
            const [monthA, yearA] = a.split('-');
            const [monthB, yearB] = b.split('-');

            if (yearA !== yearB) {
                return parseInt(yearA) - parseInt(yearB);
            }

            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return monthNames.indexOf(monthA) - monthNames.indexOf(monthB);
        });

        const monthlyChartData = completeSortedMonthYears.map(key => {
            const [month, year] = key.split('-');
            return {
                month,
                year,
                total_notifications: monthlyMap[key] || 0,
                entity_name: "BSE"
            };
        });

        if (monthlyChartData.length === 0) {
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const displayYear = new Date().getFullYear().toString();

            return {
                daily: filteredDailyChartData,
                monthly: monthNames.map(month => ({
                    month,
                    year: displayYear,
                    total_notifications: 0,
                    entity_name: "BSE"
                })),
                weekly: [],
                entity: []
            };
        }

        const weeklyMap: { [key: string]: number } = {};

        if (latestDateObj) {
            const latestMonth = latestDateObj.getMonth();
            const latestYear = latestDateObj.getFullYear();

            dailyChartData.forEach(item => {
                try {
                    const dateObj = new Date(item.date);
                    if (dateObj.getMonth() === latestMonth && dateObj.getFullYear() === latestYear) {
                        const dayOfMonth = dateObj.getDate();
                        const weekNumber = Math.ceil(dayOfMonth / 7);
                        const weekKey = `Week ${weekNumber}`;

                        if (!weeklyMap[weekKey]) {
                            weeklyMap[weekKey] = 0;
                        }
                        weeklyMap[weekKey] += item.total_notifications;
                    }
                } catch (e) {
                    console.error("Error parsing date:", item.date, e);
                }
            });
        }

        const weeklyTimeData = Object.keys(weeklyMap).map(week => ({
            week,
            total_notifications: weeklyMap[week]
        })).sort((a, b) => a.week.localeCompare(b.week));

        const entityMap: { [key: string]: number } = {};
        data.forEach(item => {
            const entityName = item.entity_name || "Unknown Entity";
            if (!entityMap[entityName]) {
                entityMap[entityName] = 0;
            }
            entityMap[entityName] += 1;
        });

        const weeklyEntityData = Object.keys(entityMap).map(entity => ({
            week: entity,
            total_notifications: entityMap[entity]
        })).sort((a, b) => b.total_notifications - a.total_notifications);

        return {
            daily: filteredDailyChartData,
            monthly: monthlyChartData,
            weekly: weeklyTimeData,
            entity: weeklyEntityData
        };
    } else {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const displayYear = new Date().getFullYear().toString();

        const monthlyChartData = monthNames.map(month => ({
            month,
            year: displayYear,
            total_notifications: 0,
            entity_name: "BSE"
        }));

        return {
            daily: filteredDailyChartData,
            monthly: monthlyChartData,
            weekly: [],
            entity: []
        };
    }
};

export const transformBSEDataForExcelView = (data: any[]) => {
    return data.map(item => ({
        "SrNo": item.id,
        "Name of Entity": item.entity_name || "Unknown Entity",
        "Link to Intimation": item.pdf_link,
        "Nature of Intimation": item.nature || "N/A",
        "Summary of Intimation": item.summary,
        "Date": item.date_key
    }));
};

export const getMonthYearFromFirstRow = (data: any[]) => {
    if (!data || data.length === 0) {
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        const now = new Date();
        return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
    }

    const firstRow = data[0];
    let dateStr = firstRow["Date"];

    if (!dateStr) {
        const possibleDateColumns = ["Date", "date", "date_key", "Date Key", "Run Date", "Run_Date"];
        for (const col of possibleDateColumns) {
            if (firstRow[col]) {
                dateStr = firstRow[col];
                break;
            }
        }
    }

    const dateObj = parseDate(dateStr);
    if (dateObj) {
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        return `${monthNames[dateObj.getMonth()]} ${dateObj.getFullYear()}`;
    }

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const now = new Date();
    return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
};

export const filterDataByLatestMonth = (data: any[]) => {
    if (!data || data.length === 0) return data;

    let latestDate: Date | null = null;
    data.forEach(item => {
        const dateValue = item["Date"];
        const itemDate = parseDate(dateValue);

        if (itemDate && (!latestDate || itemDate > latestDate)) {
            latestDate = itemDate;
        }
    });

    if (!latestDate) return data;

    const latestMonth = latestDate.getMonth();
    const latestYear = latestDate.getFullYear();

    return data.filter(item => {
        const dateValue = item["Date"];
        const itemDate = parseDate(dateValue);

        if (!itemDate) return false;

        return itemDate.getMonth() === latestMonth && itemDate.getFullYear() === latestYear;
    });
};
