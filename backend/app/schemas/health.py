from typing import Optional
from pydantic import BaseModel, Field


class DatabaseStatus(BaseModel):
    connected: bool = Field(..., description="Whether PostgreSQL database connection is active")
    details: str = Field(..., description="Status message or error details from database check")


class BlockchainStatus(BaseModel):
    connected: bool = Field(..., description="Whether Web3 RPC node is reachable")
    chain_id: Optional[int] = Field(default=None, description="Active EVM network chain ID")
    latest_block: Optional[int] = Field(default=None, description="Latest mined block number")
    contract_address: Optional[str] = Field(default=None, description="Bound smart contract address")
    relayer_address: Optional[str] = Field(default=None, description="Derived platform relayer wallet address")


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", description="Overall health status")
    service: str = Field(default="backend", description="Service identifier")
    environment: Optional[str] = Field(default=None, description="Current runtime environment")
    version: Optional[str] = Field(default=None, description="API version")
    database: Optional[DatabaseStatus] = Field(default=None, description="Diagnostic database state")
    blockchain: Optional[BlockchainStatus] = Field(default=None, description="Diagnostic blockchain state")
