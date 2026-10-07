PRAGMA foreign_keys=ON;
CREATE TABLE storage (
 id INTEGER PRIMARY KEY CHECK(id=1), stored_bytes INTEGER NOT NULL DEFAULT 0 CHECK(stored_bytes>=0),
 reserved_bytes INTEGER NOT NULL DEFAULT 0 CHECK(reserved_bytes>=0), cap_bytes INTEGER NOT NULL DEFAULT 9663676416,
 reconcile_lock TEXT, lock_until INTEGER NOT NULL DEFAULT 0, scan_cursor TEXT, scan_bytes INTEGER NOT NULL DEFAULT 0,
 last_reconciled INTEGER, warning INTEGER NOT NULL DEFAULT 0
);
INSERT INTO storage(id) VALUES(1);
CREATE TABLE options (id INTEGER PRIMARY KEY CHECK(id=1), json TEXT NOT NULL);
CREATE TABLE settings (key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT INTO options VALUES(1,'{"teams":[{"slug":"blue","name":"UAH Blue"},{"slug":"white","name":"UAH White"}],"seasons":[{"slug":"fall-2026","name":"Fall 2026"}]}');
CREATE TABLE submissions (
 id TEXT PRIMARY KEY, display_id TEXT NOT NULL UNIQUE,
 team_slug TEXT NOT NULL, team_name TEXT NOT NULL, season_slug TEXT NOT NULL, season_name TEXT NOT NULL,
 opponent TEXT NOT NULL, match_date TEXT NOT NULL, submitter TEXT NOT NULL, discord TEXT NOT NULL DEFAULT '',
 rehost TEXT NOT NULL CHECK(rehost IN('no','yes','unsure')), notes TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL CHECK(status IN('uploading','pending','reviewing','imported','rejected','failed')),
 created_at INTEGER NOT NULL, submitted_at INTEGER, terminal_at INTEGER, objects_deleted_at INTEGER,
 expires_at INTEGER NOT NULL, token_hash TEXT NOT NULL, declared_bytes INTEGER NOT NULL,
 reserved_bytes INTEGER NOT NULL, actual_bytes INTEGER NOT NULL DEFAULT 0, verify_cursor INTEGER NOT NULL DEFAULT 0,
 review_reason TEXT NOT NULL DEFAULT '', admin_notes TEXT NOT NULL DEFAULT ''
 ,cleanup_lease_until INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE folders (
 id TEXT PRIMARY KEY, submission_id TEXT NOT NULL REFERENCES submissions(id), name TEXT NOT NULL,
 ordinal INTEGER NOT NULL, disposition TEXT CHECK(disposition IN('imported','rejected')),
 map_id TEXT, import_team TEXT, import_season TEXT, reason TEXT,
 UNIQUE(submission_id,name), UNIQUE(submission_id,ordinal)
);
CREATE TABLE files (
 id TEXT PRIMARY KEY, submission_id TEXT NOT NULL REFERENCES submissions(id), folder_id TEXT NOT NULL REFERENCES folders(id),
 name TEXT NOT NULL, object_key TEXT NOT NULL UNIQUE, ordinal INTEGER NOT NULL,
 declared_size INTEGER NOT NULL CHECK(declared_size>0), sha256 TEXT NOT NULL,
 actual_size INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'waiting' CHECK(status IN('waiting','uploading','uploaded','deleted')),
 lease TEXT, lease_until INTEGER NOT NULL DEFAULT 0,
 UNIQUE(folder_id,name), UNIQUE(submission_id,ordinal)
);
CREATE INDEX submissions_status ON submissions(status,created_at);
CREATE INDEX files_submission ON files(submission_id,ordinal);
CREATE INDEX folders_submission ON folders(submission_id);
CREATE TABLE rate_limits (hash TEXT NOT NULL, window INTEGER NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(hash,window));
CREATE TABLE alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, level INTEGER NOT NULL, at INTEGER NOT NULL);
CREATE TABLE reconcile_seen (object_key TEXT PRIMARY KEY,size INTEGER NOT NULL);
CREATE TRIGGER reserve_submission BEFORE INSERT ON submissions BEGIN
 SELECT (CASE WHEN (SELECT lock_until FROM storage WHERE id=1)>unixepoch() THEN RAISE(ABORT,'reconcile_busy') END);
 SELECT (CASE WHEN (SELECT stored_bytes+reserved_bytes+NEW.declared_bytes>cap_bytes FROM storage WHERE id=1) THEN RAISE(ABORT,'inbox_full') END);
END;
CREATE TRIGGER reservation_created AFTER INSERT ON submissions BEGIN
 UPDATE storage SET reserved_bytes=reserved_bytes+NEW.reserved_bytes WHERE id=1;
END;
CREATE TRIGGER file_stored AFTER UPDATE OF actual_size ON files WHEN OLD.actual_size=0 AND NEW.actual_size>0 BEGIN
 UPDATE submissions SET actual_bytes=actual_bytes+NEW.actual_size, reserved_bytes=reserved_bytes-NEW.declared_size WHERE id=NEW.submission_id;
 UPDATE storage SET stored_bytes=stored_bytes+NEW.actual_size,reserved_bytes=reserved_bytes-NEW.declared_size WHERE id=1;
END;

CREATE TABLE maintenance (id INTEGER PRIMARY KEY CHECK(id=1), owner TEXT, expires INTEGER NOT NULL DEFAULT 0);
INSERT INTO maintenance(id) VALUES(1);
