import re
from typing import Optional
from backend.app.models.responses import GSTINVerification

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


class GSTINVerificationService:
    """Provider seam for GST identity checks; never treats syntax as registration proof."""

    def validate_format(self, gstin: Optional[str]) -> bool:
        if not gstin:
            return False
        value = gstin.strip().upper()
        if not GSTIN_PATTERN.fullmatch(value):
            return False
        return self._checksum_is_valid(value)

    @staticmethod
    def _checksum_is_valid(gstin: str) -> bool:
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        factor = 2
        total = 0
        for char in reversed(gstin[:14]):
            code = chars.index(char)
            product = code * factor
            total += product // 36 + product % 36
            factor = 1 if factor == 2 else 2
        check = (36 - (total % 36)) % 36
        return chars[check] == gstin[-1]

    def verify(self, gstin: Optional[str]) -> GSTINVerification:
        if not gstin:
            return GSTINVerification(
                status="UNVERIFIED",
                message="No GSTIN was supplied by the registry record."
            )
        normalized = gstin.strip().upper()
        if not self.validate_format(normalized):
            return GSTINVerification(
                gstin=normalized,
                status="GSTIN_INVALID",
                verification_source="LOCAL_FORMAT_CHECK",
                message="GSTIN failed local format/checksum validation; registration was not checked."
            )
        return GSTINVerification(
            gstin=normalized,
            status="VERIFICATION_UNAVAILABLE",
            verification_source="NO_AUTHORIZED_PROVIDER_CONFIGURED",
            message="GSTIN format is valid, but authoritative GST registration verification is unavailable."
        )

    def verify_authoritatively(self, gstin: str) -> GSTINVerification:
        """Reserved for an authorized GSTN/GSP adapter; deliberately fails closed today."""
        result = self.verify(gstin)
        if result.status == "VERIFICATION_UNAVAILABLE":
            result.message = "No authorized GSTN/GSP provider is configured; vendor remains unverified."
        return result
