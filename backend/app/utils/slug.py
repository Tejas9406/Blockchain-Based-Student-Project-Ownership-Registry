import re
import secrets
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


def slugify(text: str, max_length: int = 200) -> str:
    """
    Converts a title into a URL-friendly, lowercase kebab-case slug.
    
    Examples:
        "AI Medical Diagnostics v2.0!" -> "ai-medical-diagnostics-v2-0"
        "Blockchain & Student Registry" -> "blockchain-student-registry"
    """
    # Normalize and convert to lowercase
    slug = text.lower().strip()
    
    # Replace any non-alphanumeric characters (excluding spaces and hyphens) with empty string
    slug = re.sub(r"[^\w\s-]", "", slug)
    
    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    
    # Collapse multiple consecutive hyphens into a single hyphen
    slug = re.sub(r"-+", "-", slug)
    
    # Strip leading and trailing hyphens
    slug = slug.strip("-")
    
    # Truncate to max_length without breaking in the middle of a word if possible
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
        
    return slug or "project"


def generate_unique_slug(db: Session, title: str, exclude_project_id: Optional[str] = None) -> str:
    """
    Generates a guaranteed unique slug for a Project in the database.
    If 'my-project' exists, attempts 'my-project-2', 'my-project-3', etc.
    """
    base_slug = slugify(title)
    candidate_slug = base_slug
    counter = 1

    while True:
        query = select(Project).where(Project.slug == candidate_slug)
        if exclude_project_id:
            query = query.where(Project.public_id != exclude_project_id)
            
        existing = db.execute(query).scalar_one_or_none()
        if not existing:
            return candidate_slug
            
        counter += 1
        if counter <= 100:
            candidate_slug = f"{base_slug}-{counter}"
        else:
            # Fallback to random hex suffix for extreme collision cases
            suffix = secrets.token_hex(3)
            candidate_slug = f"{base_slug}-{suffix}"
