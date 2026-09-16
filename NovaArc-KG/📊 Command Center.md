# 🎛️ NovaArc Command Center — Live KG Analytics

## 🔥 Top 10 Most Connected Denial Codes

```dataview
TABLE 
  length(file.outlinks) AS "Connections",
  category AS "Category",
  severity AS "Severity"
FROM #carc/code
SORT length(file.outlinks) DESC
LIMIT 10
```

## 🩺 Critical Scenarios (High Priority)

```dataview
LIST
FROM #scenario/clinical
WHERE severity = "critical"
```

## 📋 CMS-1500 Box Coverage Heatmap

```dataview
TABLE 
  file.link AS "Requirement",
  cms_box AS "Box #",
  frequency AS "Freq"
FROM #form/cms1500
SORT frequency DESC
```

## 🎯 Category → Denial Count

```dataview
TABLE 
  length(rows) AS "Total Denials"
FROM #carc/code
GROUP BY category
SORT length(rows) DESC
```
