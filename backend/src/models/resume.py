"""Re-export schemas from common for backward compatibility."""
from common.schema.resume import (
    ResumeSchema,
    JointRequirementsSchema,
    MatchReport,
    PatchAction,
    PatchList,
    ContactInfo,
    Skill,
    ExperienceBullet,
    ExperienceEntry,
    EducationEntry,
    ProjectEntry,
    CertificationEntry,
)

__all__ = [
    "ResumeSchema",
    "JointRequirementsSchema",
    "MatchReport",
    "PatchAction",
    "PatchList",
    "ContactInfo",
    "Skill",
    "ExperienceBullet",
    "ExperienceEntry",
    "EducationEntry",
    "ProjectEntry",
    "CertificationEntry",
]