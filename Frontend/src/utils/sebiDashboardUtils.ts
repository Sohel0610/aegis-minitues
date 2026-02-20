
import { SEBIExcelSummary } from "@/services/sebiService";

// Helper to check if cache is valid (unused currently but kept for future)
export const isCacheValid = (cachedData: any, cacheDuration: number = 5 * 60 * 1000) => {
    if (!cachedData || !cachedData.timestamp) return false;
    const now = Date.now();
    return (now - cachedData.timestamp) < cacheDuration;
};

export const parseDate = (s: any): Date | null => {
    if (!s) return null;
    if (s instanceof Date) return s;
    if (typeof s === 'number') return new Date(s);
    const v = String(s);
    if (/^\d{4}-\d{2}-\d{2}$/.test(v)) {
        const [y, m, d] = v.split('-').map(Number);
        return new Date(y, m - 1, d);
    }
    if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(v)) {
        const [d, m, y] = v.split('-').map(Number);
        return new Date(y, m - 1, d);
    }
    if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(v)) {
        const [m, d, y] = v.split('/').map(Number);
        return new Date(y, m - 1, d);
    }
    const dt = new Date(v);
    return isNaN(dt.getTime()) ? null : dt;
};

// Process data for charts
export const processDataForSEBIData = (data: SEBIExcelSummary[]) => {
    // Group data by date for daily trend
    const dailyMap: { [key: string]: number } = {};

    data.forEach(item => {
        const date = item.date_key;
        if (date) {
            try {
                const parts = date.split('-');
                if (parts.length === 3) {
                    const day = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1;
                    const year = parseInt(parts[2], 10);

                    const dateObj = new Date(year, month, day);
                    if (!isNaN(dateObj.getTime())) {
                        const formattedDate = dateObj.toISOString().split('T')[0];
                        if (!dailyMap[formattedDate]) {
                            dailyMap[formattedDate] = 0;
                        }
                        dailyMap[formattedDate] += 1;
                    }
                }
            } catch (e) {
                console.warn("Skipping invalid date:", date);
            }
        }
    });

    let dailyChartData = Object.keys(dailyMap).map(date => ({
        date,
        total_entities: dailyMap[date]
    })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    let latestDateObj: Date | null = null;
    if (dailyChartData.length > 0) {
        latestDateObj = new Date(dailyChartData[dailyChartData.length - 1].date);
    }

    let filteredDailyChartData = dailyChartData;
    if (latestDateObj) {
        const latestMonth = latestDateObj.getMonth();
        const latestYear = latestDateObj.getFullYear();

        filteredDailyChartData = dailyChartData.filter(item => {
            const itemDate = new Date(item.date);
            return itemDate.getMonth() === latestMonth && itemDate.getFullYear() === latestYear;
        });
    }

    const monthlyMap: { [key: string]: number } = {};
    const monthYearSet = new Set<string>();

    data.forEach(item => {
        const date = item.date_key;
        if (date) {
            try {
                const parts = date.split('-');
                if (parts.length === 3) {
                    const day = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1;
                    const year = parseInt(parts[2], 10);

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
                console.warn("Skipping invalid date:", date);
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
                entity_name: "SEBI"
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
                    entity_name: "SEBI"
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
                    if (isNaN(dateObj.getTime())) return;

                    if (dateObj.getMonth() === latestMonth && dateObj.getFullYear() === latestYear) {
                        const dayOfMonth = dateObj.getDate();
                        const weekNumber = Math.ceil(dayOfMonth / 7);
                        const weekKey = `Week ${weekNumber}`;

                        if (!weeklyMap[weekKey]) {
                            weeklyMap[weekKey] = 0;
                        }
                        weeklyMap[weekKey] += item.total_entities;
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
            const entityName = "SEBI Notification";
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
            entity_name: "SEBI"
        }));

        return {
            daily: filteredDailyChartData,
            monthly: monthlyChartData,
            weekly: [],
            entity: []
        };
    }
};

export const transformSEBIDataForExcelView = (data: SEBIExcelSummary[]) => {
    const rows = data
        .filter(item => item.pdf_link !== 'NIL' && item.summary !== 'NIL')
        .map(item => ({
            "Date": item.date_key,
            "PDF Link": item.pdf_link,
            "Summary": item.summary
        }));

    rows.sort((a, b) => {
        const da = parseDate(a["Date"]);
        const db = parseDate(b["Date"]);
        const ta = da ? da.getTime() : 0;
        const tb = db ? db.getTime() : 0;
        return tb - ta;
    });
    return rows;
};

export const getLatestMonthYear = (data: any[]) => {
    if (!data || data.length === 0) {
        const monthNames = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];
        const now = new Date();
        return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
    }

    let max: Date | null = null;
    for (const row of data) {
        const d = parseDate(row["Date"] || row["date"] || row["date_key"] || row["Date Key"] || row["Run Date"] || row["Run_Date"]);
        if (d && (!max || d > max)) max = d;
    }

    if (max) {
        const monthNames = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];
        return `${monthNames[max.getMonth()]} ${max.getFullYear()}`;
    }

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    const now = new Date();
    return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
};
