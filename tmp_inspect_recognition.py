import os
import inspect
from datetime import datetime
from repositories.recognition_repo import RecognitionRepository

repo = RecognitionRepository()
print("DATABASE_URL_SET=", bool(os.environ.get("DATABASE_URL")))
print("DATABASE_URL=", os.environ.get("DATABASE_URL"))
print("is_postgres=", repo._is_postgres())
print("_db_timestamp_value source:\n", inspect.getsource(RecognitionRepository._db_timestamp_value))

now = datetime.now()
manila_now = datetime.now().astimezone()
print("local_now=", now.isoformat())
print("system_tz_now=", manila_now.isoformat())
