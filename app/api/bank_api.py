from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.shared.bank_config import get_bank_config, list_available_banks


router = APIRouter()


class BankInfoResponse(BaseModel):
    bank_id: str = Field(..., alias="bankId")
    bank_name: str = Field(..., alias="bankName")
    bank_name_short: str = Field(..., alias="bankNameShort")
    currency: str
    languages: list[str]
    branding: dict

    class Config:
        populate_by_name = True


class BankListResponse(BaseModel):
    banks: list[dict[str, str]]


@router.get("/bank/info/{bank_id}", response_model=BankInfoResponse)
async def get_bank_info(bank_id: str) -> BankInfoResponse:
    """Get bank configuration for demo purposes."""
    config = get_bank_config(bank_id)
    return BankInfoResponse(
        bankId=config.bank_id,
        bankName=config.bank_name,
        bankNameShort=config.bank_name_short,
        currency=config.currency,
        languages=config.languages,
        branding={
            "primaryColor": config.branding.primary_color,
            "secondaryColor": config.branding.secondary_color,
            "accentColor": config.branding.accent_color,
            "logoUrl": config.branding.logo_url,
            "faviconUrl": config.branding.favicon_url,
            "tagline": config.branding.tagline,
            "websiteUrl": config.branding.website_url,
        },
    )


@router.get("/bank/list", response_model=BankListResponse)
async def list_banks() -> BankListResponse:
    """List all available banks for demo purposes."""
    return BankListResponse(banks=list_available_banks())
