UPDATE bodb_testsed s
INNER JOIN (SELECT test_sed_id, ssr_id FROM bodb_testsedssr) c ON s.id=c.test_sed_id
SET s.ssr_id=c.ssr_id;
