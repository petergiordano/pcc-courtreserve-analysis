# Archived CSV Files - Duplicates

**Archive Date**: October 27, 2025
**Reason**: Duplicate/older versions of CSV exports from CourtReserve

---

## Archived Files

### 1. CheckinReports2025-10-26_03-36-PM.csv
- **Size**: 598,823 bytes (1,756 records)
- **Date Range**: October 1-26, 2025 (26 days)
- **Reason**: Partial export superseded by fuller version
- **Kept Instead**: `CheckinReports2025-10-26_09-55-PM.csv` (5.4MB, 15,513 records, Mar 1-Oct 26)

### 2. EventRegistrantsReports2025-10-27_04-14-AM.csv
- **Size**: 5,138,969 bytes (13,165 records)
- **Date Range**: February 5-October 26, 2025 (264 days)
- **Reason**: Exact duplicate (same content, different filename)
- **Kept Instead**: `EventRegistrantsReports2025-10-27_04-14-AM 2.csv` (identical)

### 3. ReservationReport_2025-10-26_03-50-PM.csv
- **Size**: 922,529 bytes (2,227 records)
- **Date Range**: October 1-26, 2025 (26 days)
- **Reason**: Partial export superseded by fuller version
- **Kept Instead**: `ReservationReport_2025-10-27_04-10-AM 2.csv` (1.3MB, 4,609 records, Jan 29-Oct 26)

### 4. ReservationReport_2025-10-27_04-10-AM.csv
- **Size**: 1,343,124 bytes (4,609 records)
- **Date Range**: January 29-October 26, 2025 (271 days)
- **Reason**: Exact duplicate (same content, different filename)
- **Kept Instead**: `ReservationReport_2025-10-27_04-10-AM 2.csv` (identical)

### 5. SalesReport2025-10-26_09-29-PM.csv
- **Size**: 3,465 bytes (62 records)
- **Reason**: Earlier version superseded by updated export
- **Kept Instead**: `SalesReport2025-10-26_09-30-PM.csv` (3,829 bytes, 75 records)

---

## Analysis Impact

None of the archived files were used in the primary JTBD analysis. The analysis used the most comprehensive versions:

- **CheckinReports**: Used `CheckinReports2025-10-26_09-55-PM.csv` (15,513 records, Mar-Oct)
- **Reservations**: Used `ReservationReport_2025-10-27_04-10-AM 2.csv` (4,609 records, Jan-Oct)
- **Event Registrants**: Not used in primary analysis
- **Sales Report**: Not used in primary analysis

---

## Recovery Instructions

If needed, these files can be recovered from this archive directory. They are preserved for audit/validation purposes.

**To restore a file:**
```bash
cp archive/csv-duplicates/[filename].csv .
```

---

**Archived By**: Claude Code (Anthropic)
**Archive Date**: October 27, 2025
