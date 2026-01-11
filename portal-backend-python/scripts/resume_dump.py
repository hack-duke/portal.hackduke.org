from db import get_local_session
from sqlalchemy import text

QUERY = """
SELECT file_s3_key
FROM response R
JOIN application A ON R.application_id = A.id
WHERE file_s3_key IS NOT NULL
AND form_key = '2026-cfg-application'
"""

session = get_local_session()
result = session.execute(
    text(QUERY)
)