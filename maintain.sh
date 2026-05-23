#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SYSTEM HEALTH CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 ~/projects/malloc-training/brain.db \
"SELECT 'projects' as tbl, COUNT(*) as rows FROM projects
UNION ALL SELECT 'concepts', COUNT(*) FROM concepts
UNION ALL SELECT 'patterns', COUNT(*) FROM patterns
UNION ALL SELECT 'decisions', COUNT(*) FROM decisions
UNION ALL SELECT 'weakness_patterns', COUNT(*) FROM weakness_patterns
UNION ALL SELECT 'project_narrative', COUNT(*) FROM project_narrative
UNION ALL SELECT 'project_full_detail', COUNT(*) FROM project_full_detail
UNION ALL SELECT 'mind_model', COUNT(*) FROM mind_model
UNION ALL SELECT 'transfer_exams', COUNT(*) FROM transfer_exams
UNION ALL SELECT 'adversarial_exams', COUNT(*) FROM adversarial_exams
UNION ALL SELECT 'quiz_records', COUNT(*) FROM quiz_records
UNION ALL SELECT 'lab_handouts', COUNT(*) FROM lab_handouts
UNION ALL SELECT 'external_validation', COUNT(*) FROM external_validation
UNION ALL SELECT 'mood_logs', COUNT(*) FROM mood_logs;"

echo ""
echo "Pending gaps:"
sqlite3 ~/projects/malloc-training/brain.db \
"SELECT '  ID ' || id || ' — Phase ' || phase || ' | ' || lab || ' | ' || gap_location
 FROM adversarial_exams WHERE resolved = 'pending';"

echo ""
echo "Git status:"
cd ~/projects/malloc-training && git status --short
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
