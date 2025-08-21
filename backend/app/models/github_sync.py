from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.database import Base

class GitHubSync(Base):
    __tablename__ = "github_sync"

    id = Column(Integer, primary_key=True)
    repository = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    token = Column(String, nullable=False) # Will be stored encrypted
    auto_sync = Column(Boolean, default=False)
    sync_interval = Column(Integer, default=60) # In minutes
    include_files = Column(JSON) # List of glob patterns
    exclude_files = Column(JSON) # List of glob patterns
    conflict_resolution = Column(String, default="manual")
