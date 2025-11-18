import os
import csv
from collections import defaultdict
from flask import current_app


def _extract_header_title_from_text(text: str) -> str:
    """Use the ResumeExtractor from ats_components to get a consistent header title."""
    try:
        from ats_components import ResumeExtractor
        extractor = ResumeExtractor()
        return extractor.extract_header_title(text)
    except Exception:
        # Fallback to a minimal safe return
        if not text:
            return ''
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return (lines[1] if len(lines) > 1 else (lines[0] if lines else '')).strip()


def export_all_resumes_csv(app, db, models, out_path=None):
    """Export resumes and related info to a single CSV file.

    - app: Flask app
    - db: SQLAlchemy (flask_sqlalchemy) instance
    - models: dict-like mapping of model names to classes (expects keys: Resume, ContactInfo, MatchedSkill, MissingSkill)
    - out_path: optional path to CSV file; defaults to exports/all_resumes.csv in app root
    """
    Resume = models['Resume']
    ContactInfo = models.get('ContactInfo')
    MatchedSkill = models.get('MatchedSkill')
    MissingSkill = models.get('MissingSkill')

    if out_path is None:
        base = app.root_path
        out_dir = os.path.join(base, 'exports')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'all_resumes.csv')

    # Query in app context
    with app.app_context():
        try:
            resumes = Resume.query.order_by(Resume.upload_timestamp).all()

            # Preload matched and missing skills to avoid N+1
            matched_rows = MatchedSkill.query.all() if MatchedSkill is not None else []
            missing_rows = MissingSkill.query.all() if MissingSkill is not None else []

            matched_map = defaultdict(list)
            for m in matched_rows:
                try:
                    matched_map[str(m.resume_id)].append(m.skill_name)
                except Exception:
                    pass

            missing_map = defaultdict(list)
            for m in missing_rows:
                try:
                    missing_map[str(m.resume_id)].append(m.skill_name)
                except Exception:
                    pass

            # Write CSV
            fieldnames = [
                'id', 'filename', 'file_type', 'file_size', 'upload_timestamp',
                'job_title',
                'overall_score', 'classification', 'skills_score', 'header_score',
                'experience_score', 'projects_score', 'education_score', 'format_score',
                'matched_skills_count', 'missing_skills_count', 'matched_skills', 'missing_skills',
                'job_description_text', 'verdict', 'text_length'
            ]

            # Write with BOM for Excel-friendly utf-8
            with open(out_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for r in resumes:
                    rid = str(r.id)
                    matched = matched_map.get(rid, [])
                    missing = missing_map.get(rid, [])

                    row = {
                        'job_title': (getattr(r, 'header_job_title', None) or _extract_header_title_from_text(r.extracted_text or '')),
                        'id': rid,
                        'filename': r.filename,
                        'file_type': r.file_type,
                        'file_size': r.file_size,
                        'upload_timestamp': r.upload_timestamp.isoformat() if hasattr(r.upload_timestamp, 'isoformat') else str(r.upload_timestamp),
                        'overall_score': r.overall_score,
                        'classification': r.classification,
                        'skills_score': r.skills_score,
                        'header_score': r.header_score,
                        'experience_score': r.experience_score,
                        'projects_score': r.projects_score,
                        'education_score': r.education_score,
                        'format_score': r.format_score,
                        'matched_skills_count': r.matched_skills_count,
                        'missing_skills_count': r.missing_skills_count,
                        'matched_skills': ';'.join(matched),
                        'missing_skills': ';'.join(missing),
                        'job_description_text': (r.job_description_text or '').replace('\n', '\\n'),
                        'verdict': (r.verdict or '').replace('\n', '\\n'),
                        'text_length': r.text_length
                    }
                    writer.writerow(row)

        except Exception as e:
            # If the DB schema doesn't include the new column, fall back to a raw query to avoid crashing
            msg = str(e).lower()
            try:
                current_app.logger.error(f"Failed to export CSV using ORM query: {e}. Attempting raw fallback.")
            except Exception:
                print(f"Failed to export CSV using ORM query: {e}. Attempting raw fallback.")

            try:
                # Select explicit columns that are safe across older schemas
                from sqlalchemy import text as _sql_text
                sql = _sql_text("SELECT id, filename, file_type, file_size, upload_timestamp, overall_score, classification, skills_score, header_score, experience_score, projects_score, education_score, format_score, matched_skills_count, missing_skills_count, job_description_text, verdict, text_length, extracted_text FROM resumes ORDER BY upload_timestamp")
                results = db.session.execute(sql).fetchall()

                # Preload matched/missing skills
                matched_rows = MatchedSkill.query.all() if MatchedSkill is not None else []
                missing_rows = MissingSkill.query.all() if MissingSkill is not None else []
                matched_map = defaultdict(list)
                for m in matched_rows:
                    try:
                        matched_map[str(m.resume_id)].append(m.skill_name)
                    except Exception:
                        pass
                missing_map = defaultdict(list)
                for m in missing_rows:
                    try:
                        missing_map[str(m.resume_id)].append(m.skill_name)
                    except Exception:
                        pass

                fieldnames = [
                    'id', 'filename', 'file_type', 'file_size', 'upload_timestamp',
                    'job_title',
                    'overall_score', 'classification', 'skills_score', 'header_score',
                    'experience_score', 'projects_score', 'education_score', 'format_score',
                    'matched_skills_count', 'missing_skills_count', 'matched_skills', 'missing_skills',
                    'job_description_text', 'verdict', 'text_length'
                ]

                with open(out_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for row_tuple in results:
                        # results are tuples in the same order as the SELECT
                        r_id = str(row_tuple[0])
                        extracted_text = row_tuple[18] if len(row_tuple) > 18 else ''
                        matched = matched_map.get(r_id, [])
                        missing = missing_map.get(r_id, [])

                        row = {
                            'job_title': _extract_header_title_from_text(extracted_text or ''),
                            'id': r_id,
                            'filename': row_tuple[1],
                            'file_type': row_tuple[2],
                            'file_size': row_tuple[3],
                            'upload_timestamp': row_tuple[4].isoformat() if hasattr(row_tuple[4], 'isoformat') else str(row_tuple[4]),
                            'overall_score': row_tuple[5],
                            'classification': row_tuple[6],
                            'skills_score': row_tuple[7],
                            'header_score': row_tuple[8],
                            'experience_score': row_tuple[9],
                            'projects_score': row_tuple[10],
                            'education_score': row_tuple[11],
                            'format_score': row_tuple[12],
                            'matched_skills_count': row_tuple[13],
                            'missing_skills_count': row_tuple[14],
                            'matched_skills': ';'.join(matched),
                            'missing_skills': ';'.join(missing),
                            'job_description_text': (row_tuple[15] or '').replace('\n', '\\n'),
                            'verdict': (row_tuple[16] or '').replace('\n', '\\n'),
                            'text_length': row_tuple[17]
                        }
                        writer.writerow(row)

            except Exception as e2:
                try:
                    current_app.logger.error(f"Failed fallback CSV export: {e2}")
                except Exception:
                    print(f"Failed fallback CSV export: {e2}")


def register_export_listeners(app):
    """Register SQLAlchemy event listeners to auto-export CSV on changes."""
    # Import here to avoid circular imports
    from models import db, Resume, MatchedSkill, MissingSkill, ContactInfo
    
    models = {
        'Resume': Resume,
        'MatchedSkill': MatchedSkill,
        'MissingSkill': MissingSkill,
        'ContactInfo': ContactInfo
    }
    
    return _register_export_listeners_internal(app, db, models)

def _register_export_listeners_internal(app, db, models):
    """Internal function to register SQLAlchemy event listeners."""
    try:
        from sqlalchemy import event
    except Exception:
        return

    Resume = models['Resume']
    MatchedSkill = models.get('MatchedSkill')
    MissingSkill = models.get('MissingSkill')
    ContactInfo = models.get('ContactInfo')

    def regen(mapper, connection, target):
        try:
            export_all_resumes_csv(app, db, models)
        except Exception as e:
            try:
                app.logger.error(f"Error regenerating CSV: {e}")
            except Exception:
                print(f"Error regenerating CSV: {e}")

    # Listen to inserts/updates/deletes on key models
    event.listen(Resume, 'after_insert', regen)
    event.listen(Resume, 'after_update', regen)
    event.listen(Resume, 'after_delete', regen)

    # If skill mappings change, regen as well
    if MatchedSkill is not None:
        event.listen(MatchedSkill, 'after_insert', regen)
        event.listen(MatchedSkill, 'after_update', regen)
        event.listen(MatchedSkill, 'after_delete', regen)

    if MissingSkill is not None:
        event.listen(MissingSkill, 'after_insert', regen)
        event.listen(MissingSkill, 'after_update', regen)
        event.listen(MissingSkill, 'after_delete', regen)

    if ContactInfo is not None:
        event.listen(ContactInfo, 'after_insert', regen)
        event.listen(ContactInfo, 'after_update', regen)
        event.listen(ContactInfo, 'after_delete', regen)

    # Create initial export
    export_all_resumes_csv(app, db, models)
