CREATE TABLE logical_maps (
 id TEXT PRIMARY KEY,
 submission_id TEXT NOT NULL REFERENCES submissions(id),
 logical_index INTEGER NOT NULL CHECK(logical_index BETWEEN 1 AND 5),
 submitted_type TEXT NOT NULL CHECK(submitted_type IN('normal','rehost','unsure')),
 UNIQUE(submission_id,logical_index)
);
ALTER TABLE submissions ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE submissions ADD COLUMN reviewed_structure_json TEXT;
ALTER TABLE folders ADD COLUMN logical_map_id TEXT REFERENCES logical_maps(id);
ALTER TABLE folders ADD COLUMN segment_index INTEGER;
ALTER TABLE folders ADD COLUMN first_file_modified_at TEXT;
ALTER TABLE folders ADD COLUMN last_file_modified_at TEXT;
CREATE INDEX logical_maps_submission ON logical_maps(submission_id);
CREATE UNIQUE INDEX folders_logical_segment ON folders(logical_map_id,segment_index);
CREATE TABLE logical_import_receipts (
 submission_id TEXT NOT NULL REFERENCES submissions(id),
 local_map_id TEXT NOT NULL,
 logical_map_id TEXT NOT NULL,
 reviewed_structure_json TEXT NOT NULL,
 folder_ids_json TEXT NOT NULL,
 created_at INTEGER NOT NULL,
 PRIMARY KEY(submission_id,local_map_id)
);
CREATE TRIGGER logical_receipt_guard BEFORE INSERT ON logical_import_receipts
BEGIN
 SELECT (CASE WHEN
   (SELECT reviewed_structure_json FROM submissions WHERE id=NEW.submission_id) IS NOT NEW.reviewed_structure_json
   OR (SELECT COUNT(*) FROM folders WHERE submission_id=NEW.submission_id AND disposition='imported' AND map_id=NEW.local_map_id) != json_array_length(NEW.folder_ids_json)
   OR (SELECT COUNT(*) FROM folders WHERE submission_id=NEW.submission_id AND disposition='imported' AND map_id=NEW.local_map_id AND id IN (SELECT value FROM json_each(NEW.folder_ids_json))) != json_array_length(NEW.folder_ids_json)
   OR EXISTS(SELECT 1 FROM logical_import_receipts WHERE submission_id=NEW.submission_id AND local_map_id=NEW.local_map_id AND (logical_map_id!=NEW.logical_map_id OR folder_ids_json!=NEW.folder_ids_json))
 THEN RAISE(ABORT,'logical receipt conflict') END);
END;
