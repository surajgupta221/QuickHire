from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Screening(Base):
    __tablename__ = "screenings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Job Details
    job_title = Column(String, nullable=False)
    jd_text = Column(Text, nullable=False)
    location = Column(String, nullable=True)

    # Skills (optional) - can be used to enhance scoring
    must_have_skills = Column(String, nullable=True)  # comma separated
    good_to_have_skills = Column(String, nullable=True)  # comma separated

    # Results
    total_candidates = Column(Integer, default=0)
    results = Column(JSON, nullable=True)  # stores all scores

    # Status
    status = Column(String, default="pending")  # pending/processing/completed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Screening {self.job_title}>"