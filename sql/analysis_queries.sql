USE portcast_data_quality;

-- 1. Inspect rows flagged by the validation process
SELECT issue_type, COUNT(*) AS issue_count
FROM data_quality_issues
GROUP BY issue_type
ORDER BY issue_count DESC;

-- 2. Show all containers with issues
SELECT source_row, container_id, issue_type, details
FROM data_quality_issues
ORDER BY source_row, issue_type;

-- 3. Count clean shipment records by origin
SELECT origin, COUNT(*) AS shipment_count
FROM clean_shipments
GROUP BY origin
ORDER BY shipment_count DESC;

-- 4. Check that the clean dataset has no duplicate container IDs
SELECT container_id, COUNT(*) AS record_count
FROM clean_shipments
GROUP BY container_id
HAVING COUNT(*) > 1;
