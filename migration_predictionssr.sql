UPDATE bodb_prediction s
INNER JOIN (SELECT prediction_id, ssr_id FROM bodb_predictionssr) c ON s.document_ptr_id=c.prediction_id
SET s.ssr_id=c.ssr_id;
