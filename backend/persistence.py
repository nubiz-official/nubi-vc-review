"""SQLite persistence for NuBI VC Review v2."""
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class PersistenceManager:
    """Manages SQLite storage for analyses."""

    def __init__(self, db_path: str = "nubi_vc_review.db"):
        """Initialize database."""
        self.db_path = db_path
        self.persistent_conn = None
        if db_path == ":memory:":
            self.persistent_conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _get_connection(self):
        """Get database connection."""
        if self.persistent_conn:
            return self.persistent_conn, False
        return sqlite3.connect(self.db_path), True

    def _init_db(self):
        """Create tables if they don't exist."""
        conn, should_close = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    template_type TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT,
                    updated_at TEXT,
                    metadata JSON,
                    phase1_analysis JSON,
                    phase2_validations JSON,
                    report_final JSON
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL,
                    timestamp TEXT,
                    action TEXT,
                    actor TEXT,
                    notes TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON analyses(company_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON analyses(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON analyses(created_at)")
            conn.commit()
        finally:
            if should_close:
                conn.close()

    def save_analysis(self, analysis_id: str, data: Dict[str, Any]) -> bool:
        """Save complete analysis object."""
        try:
            metadata = data.get("metadata", {})
            now = datetime.utcnow().isoformat()
            conn, should_close = self._get_connection()

            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO analyses
                    (id, company_name, template_type, status, created_at, updated_at, metadata, phase1_analysis, phase2_validations, report_final)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    metadata.get("company_name", "Unknown"),
                    metadata.get("template_type", "general_investment_review"),
                    metadata.get("status", "draft"),
                    metadata.get("created_at", now),
                    now,
                    json.dumps(metadata),
                    json.dumps(data.get("phase1_analysis", {})),
                    json.dumps(data.get("phase2_validations", {})),
                    json.dumps(data.get("report_final", {}))
                ))
                conn.commit()
            finally:
                if should_close:
                    conn.close()
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete analysis."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT metadata, phase1_analysis, phase2_validations, report_final
                    FROM analyses WHERE id = ?
                """, (analysis_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    "metadata": json.loads(row[0]) if row[0] else {},
                    "phase1_analysis": json.loads(row[1]) if row[1] else {},
                    "phase2_validations": json.loads(row[2]) if row[2] else {},
                    "report_final": json.loads(row[3]) if row[3] else {}
                }
            finally:
                if should_close:
                    conn.close()
        except Exception as e:
            print(f"Error retrieving analysis: {e}")
            return None

    def list_analyses(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List all analyses, optionally filtered by status."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                if status:
                    cursor.execute("""
                        SELECT id, company_name, template_type, status, created_at, updated_at
                        FROM analyses WHERE status = ? ORDER BY created_at DESC LIMIT ?
                    """, (status, limit))
                else:
                    cursor.execute("""
                        SELECT id, company_name, template_type, status, created_at, updated_at
                        FROM analyses ORDER BY created_at DESC LIMIT ?
                    """, (limit,))
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "company_name": row[1],
                        "template_type": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "updated_at": row[5]
                    }
                    for row in rows
                ]
            finally:
                if should_close:
                    conn.close()
        except Exception as e:
            print(f"Error listing analyses: {e}")
            return []

    def update_status(self, analysis_id: str, new_status: str, reviewer: Optional[str] = None) -> bool:
        """Update analysis status."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()
                cursor.execute("""
                    UPDATE analyses SET status = ?, updated_at = ? WHERE id = ?
                """, (new_status, now, analysis_id))
                self.add_audit_entry(
                    analysis_id,
                    f"status_changed_to_{new_status}",
                    reviewer or "system",
                    f"Status changed to {new_status}"
                )
                conn.commit()
            finally:
                if should_close:
                    conn.close()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

    def add_audit_entry(
        self,
        analysis_id: str,
        action: str,
        actor: str,
        notes: Optional[str] = None
    ) -> bool:
        """Add entry to audit trail."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                timestamp = datetime.utcnow().isoformat()
                cursor.execute("""
                    INSERT INTO audit_trail (analysis_id, timestamp, action, actor, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (analysis_id, timestamp, action, actor, notes))
                conn.commit()
            finally:
                if should_close:
                    conn.close()
            return True
        except Exception as e:
            print(f"Error adding audit entry: {e}")
            return False

    def get_audit_trail(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Retrieve audit trail for analysis."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, action, actor, notes FROM audit_trail
                    WHERE analysis_id = ? ORDER BY timestamp ASC
                """, (analysis_id,))
                rows = cursor.fetchall()
                return [
                    {
                        "timestamp": row[0],
                        "action": row[1],
                        "actor": row[2],
                        "notes": row[3]
                    }
                    for row in rows
                ]
            finally:
                if should_close:
                    conn.close()
        except Exception as e:
            print(f"Error retrieving audit trail: {e}")
            return []

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete analysis and its audit trail."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM audit_trail WHERE analysis_id = ?", (analysis_id,))
                cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
                conn.commit()
            finally:
                if should_close:
                    conn.close()
            return True
        except Exception as e:
            print(f"Error deleting analysis: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            conn, should_close = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM analyses")
                total = cursor.fetchone()[0]
                cursor.execute("SELECT status, COUNT(*) FROM analyses GROUP BY status")
                by_status = {row[0]: row[1] for row in cursor.fetchall()}
                return {
                    "total_analyses": total,
                    "by_status": by_status
                }
            finally:
                if should_close:
                    conn.close()
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total_analyses": 0, "by_status": {}}
