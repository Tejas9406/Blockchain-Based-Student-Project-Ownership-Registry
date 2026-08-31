from typing import Optional
from pydantic import BaseModel, Field


class DatabaseStatus(BaseModel):
    connected: bool = Field(..., description="Whether PostgreSQL database connection is active")
    details: str = Field(..., description="Status message or error details from database check")


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", description="Overall health status")
    service: str = Field(default="backend", description="Service identifier")
    environment: Optional[str] = Field(default=None, description="Current runtime environment")
    version: Optional[str] = Field(default=None, description="API version")
    database: Optional[DatabaseStatus] = Field(default=None, description="Diagnostic database state")
