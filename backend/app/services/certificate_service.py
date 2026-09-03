import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import AppException, ConflictError, NotFoundError, ValidationException
from app.models.blockchain_record import BlockchainRecord
from app.models.enums import AnchoringStatus, DisputeStatus
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.schemas.certificate import CertificateMetadataData
from app.services.blockchain_service import BlockchainService, get_blockchain_service
from app.services.verification_service import verify_by_registration_id

REGISTRATION_ID_PATTERN = re.compile(r"^REG-\d{4}-[A-Z0-9]{5}$")


class OwnershipCertificatePDFGenerator:
    """
    Pure-Python, zero-dependency PDF 1.4 Generator for Blockchain Ownership Certificates.
    Produces specification-compliant, deterministic, and securely escaped PDF documents.
    """

    def __init__(self, metadata: CertificateMetadataData):
        self.meta = metadata
        # US Letter dimensions in PostScript points: 612 x 792
        self.width = 612
        self.height = 792

    @staticmethod
    def _escape_pdf_text(text: str) -> str:
        """Escapes text for PDF literal strings (parentheses and backslashes) and sanitizes charset."""
        if not text:
            return ""
        # Convert non-ascii chars to closest ascii or strip
        clean = ""
        for char in str(text):
            code = ord(char)
            if code < 128:
                clean += char
            elif code in (8216, 8217):  # curly single quotes
                clean += "'"
            elif code in (8220, 8221):  # curly double quotes
                clean += '"'
            elif code == 8212:  # em dash
                clean += " -- "
            elif code == 8211:  # en dash
                clean += " - "
            elif code == 8230:  # ellipsis
                clean += "..."
            else:
                clean += "?"

        escaped = clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return escaped

    @staticmethod
    def _wrap_text(text: str, max_chars: int) -> List[str]:
        """Simple line wrapper for bounded text display."""
        if not text:
            return []
        words = text.split(" ")
        lines = []
        current_line = []
        current_len = 0
        for w in words:
            if current_len + len(w) + 1 <= max_chars:
                current_line.append(w)
                current_len += len(w) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [w]
                current_len = len(w)
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def build_pdf(self) -> bytes:
        """Constructs the complete PDF binary payload."""
        stream_cmds: List[str] = []

        # -------------------------------------------------------------
        # 1. Background and Decorative Borders
        # -------------------------------------------------------------
        # Canvas background (very soft off-white/ivory)
        stream_cmds.append("0.985 0.985 0.990 rg")
        stream_cmds.append(f"0 0 {self.width} {self.height} re f")

        # Outer border: Deep Navy (0.08, 0.18, 0.36), 3.0 pt
        stream_cmds.append("0.08 0.18 0.36 RG 3.0 w")
        stream_cmds.append(f"20 20 {self.width - 40} {self.height - 40} re S")

        # Inner border: Elegant Gold/Bronze (0.78, 0.62, 0.22), 1.0 pt
        stream_cmds.append("0.78 0.62 0.22 RG 1.0 w")
        stream_cmds.append(f"26 26 {self.width - 52} {self.height - 52} re S")

        # Top decorative header band (Navy)
        stream_cmds.append("0.08 0.18 0.36 rg")
        stream_cmds.append(f"30 {self.height - 110} {self.width - 60} 74 re f")

        # Thin gold accent line below header band
        stream_cmds.append("0.78 0.62 0.22 RG 2.0 w")
        stream_cmds.append(f"30 {self.height - 112} m {self.width - 30} {self.height - 112} l S")

        # -------------------------------------------------------------
        # 2. Header Text (SIH 2026 & Title)
        # -------------------------------------------------------------
        stream_cmds.append("BT")
        # Organization / Event subtitle
        stream_cmds.append("/F2 11 Tf 0.85 0.75 0.40 rg")
        stream_cmds.append(f"1 0 0 1 45 {self.height - 62} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('SMART INDIA HACKATHON 2026 — CYB05')}) Tj")

        # Main Certificate Title
        stream_cmds.append("/F2 18 Tf 1 1 1 rg")
        stream_cmds.append(f"1 0 0 1 45 {self.height - 85} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('CERTIFICATE OF BLOCKCHAIN OWNERSHIP')}) Tj")

        # Subtitle
        stream_cmds.append("/F1 9 Tf 0.82 0.88 0.96 rg")
        stream_cmds.append(f"1 0 0 1 45 {self.height - 100} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('Cryptographic Student Project Registry & Provenance Record')}) Tj")
        stream_cmds.append("ET")

        # -------------------------------------------------------------
        # 3. Registration ID Highlight Box
        # -------------------------------------------------------------
        reg_box_y = self.height - 165
        stream_cmds.append("0.93 0.95 0.98 rg 0.78 0.62 0.22 RG 1.5 w")
        stream_cmds.append(f"45 {reg_box_y} {self.width - 90} 40 re B")

        stream_cmds.append("BT")
        stream_cmds.append("/F2 9 Tf 0.45 0.35 0.15 rg")
        stream_cmds.append(f"1 0 0 1 60 {reg_box_y + 24} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('REGISTRATION IDENTIFIER')}) Tj")

        stream_cmds.append("/F4 14 Tf 0.08 0.18 0.36 rg")
        stream_cmds.append(f"1 0 0 1 60 {reg_box_y + 8} Tm")
        stream_cmds.append(f"({self._escape_pdf_text(self.meta.registration_id)}) Tj")

        # Status badge on right side of registration box
        status_text = "STATUS: VERIFIED ON-CHAIN"
        if self.meta.dispute_status == "REJECTED":
            status_text = "STATUS: VERIFIED (DISPUTE DISMISSED)"
        stream_cmds.append("/F2 9 Tf 0.12 0.50 0.24 rg")
        stream_cmds.append(f"1 0 0 1 {self.width - 250} {reg_box_y + 14} Tm")
        stream_cmds.append(f"({self._escape_pdf_text(status_text)}) Tj")
        stream_cmds.append("ET")

        # -------------------------------------------------------------
        # 4. Project & Authors Metadata Section
        # -------------------------------------------------------------
        curr_y = reg_box_y - 25

        stream_cmds.append("BT")
        # Section Header
        stream_cmds.append("/F2 12 Tf 0.08 0.18 0.36 rg")
        stream_cmds.append(f"1 0 0 1 45 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('PROJECT RECORD')}) Tj")
        stream_cmds.append("ET")

        # Divider line
        curr_y -= 6
        stream_cmds.append("0.85 0.85 0.88 RG 0.75 w")
        stream_cmds.append(f"45 {curr_y} m {self.width - 45} {curr_y} l S")

        curr_y -= 18

        # Project Title (wrap if long)
        stream_cmds.append("BT")
        stream_cmds.append("/F2 9 Tf 0.40 0.42 0.46 rg")
        stream_cmds.append(f"1 0 0 1 45 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('Project Title:')}) Tj")

        title_lines = self._wrap_text(self.meta.project_title, 65)
        stream_cmds.append("/F2 11 Tf 0.10 0.12 0.18 rg")
        line_offset = 0
        for line in title_lines:
            stream_cmds.append(f"1 0 0 1 145 {curr_y - line_offset} Tm")
            stream_cmds.append(f"({self._escape_pdf_text(line)}) Tj")
            line_offset += 14
        stream_cmds.append("ET")

        curr_y -= max(20, line_offset + 6)

        # Version & Lifecycle Stage
        stream_cmds.append("BT")
        stream_cmds.append("/F2 9 Tf 0.40 0.42 0.46 rg")
        stream_cmds.append(f"1 0 0 1 45 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('Version / Stage:')}) Tj")

        v_stage_str = f"{self.meta.version_tag}   |   Stage: {self.meta.lifecycle_stage}"
        stream_cmds.append("/F1 10 Tf 0.15 0.18 0.22 rg")
        stream_cmds.append(f"1 0 0 1 145 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text(v_stage_str)}) Tj")
        stream_cmds.append("ET")

        curr_y -= 20

        # Authors
        authors_str = ", ".join(self.meta.authors) if self.meta.authors else "Primary Project Author"
        author_lines = self._wrap_text(authors_str, 65)
        stream_cmds.append("BT")
        stream_cmds.append("/F2 9 Tf 0.40 0.42 0.46 rg")
        stream_cmds.append(f"1 0 0 1 45 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('Author(s):')}) Tj")

        stream_cmds.append("/F1 10 Tf 0.15 0.18 0.22 rg")
        a_offset = 0
        for line in author_lines:
            stream_cmds.append(f"1 0 0 1 145 {curr_y - a_offset} Tm")
            stream_cmds.append(f"({self._escape_pdf_text(line)}) Tj")
            a_offset += 13
        stream_cmds.append("ET")

        curr_y -= max(20, a_offset + 6)

        # Institution & Department
        inst_str = self.meta.institution or "Academic Institution"
        if self.meta.department:
            inst_str += f" ({self.meta.department})"
        stream_cmds.append("BT")
        stream_cmds.append("/F2 9 Tf 0.40 0.42 0.46 rg")
        stream_cmds.append(f"1 0 0 1 45 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('Institution:')}) Tj")

        stream_cmds.append("/F1 10 Tf 0.15 0.18 0.22 rg")
        stream_cmds.append(f"1 0 0 1 145 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text(inst_str)}) Tj")
        stream_cmds.append("ET")

        curr_y -= 30

        # -------------------------------------------------------------
        # 5. Cryptographic Anchoring Proofs Section
        # -------------------------------------------------------------
        stream_cmds.append("BT")
        stream_cmds.append("/F2 12 Tf 0.08 0.18 0.36 rg")
        stream_cmds.append(f"1 0 0 1 45 {curr_y} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('CRYPTOGRAPHIC ON-CHAIN PROOFS')}) Tj")
        stream_cmds.append("ET")

        curr_y -= 6
        stream_cmds.append("0.85 0.85 0.88 RG 0.75 w")
        stream_cmds.append(f"45 {curr_y} m {self.width - 45} {curr_y} l S")

        curr_y -= 20

        # Proof items helper
        def draw_proof_item(label: str, value: str, y_pos: int) -> int:
            stream_cmds.append("BT")
            stream_cmds.append("/F2 9 Tf 0.35 0.38 0.42 rg")
            stream_cmds.append(f"1 0 0 1 45 {y_pos} Tm")
            stream_cmds.append(f"({self._escape_pdf_text(label)}) Tj")

            # Value in Courier monospace for hashes/CIDs
            stream_cmds.append("/F3 8.5 Tf 0.08 0.15 0.28 rg")
            stream_cmds.append(f"1 0 0 1 175 {y_pos} Tm")
            stream_cmds.append(f"({self._escape_pdf_text(value or 'N/A')}) Tj")
            stream_cmds.append("ET")
            return y_pos - 18

        curr_y = draw_proof_item("Composite SHA-256:", self.meta.composite_sha256 or "", curr_y)
        curr_y = draw_proof_item("IPFS Root CID:", self.meta.ipfs_root_cid or "", curr_y)
        curr_y = draw_proof_item("Transaction Hash:", self.meta.transaction_hash or "", curr_y)

        # Block Number & Anchored Timestamp
        ts_str = self.meta.anchored_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if self.meta.anchored_timestamp else "N/A"
        blk_str = f"Block #{self.meta.block_number}" if self.meta.block_number else "Confirmed on-chain"
        curr_y = draw_proof_item("Block & Timestamp:", f"{blk_str}   |   {ts_str}", curr_y)

        curr_y -= 15

        # -------------------------------------------------------------
        # 6. Verification Portal & QR Instructions Box
        # -------------------------------------------------------------
        verify_box_y = curr_y - 48
        stream_cmds.append("0.96 0.97 0.98 rg 0.80 0.82 0.88 RG 1.0 w")
        stream_cmds.append(f"45 {verify_box_y} {self.width - 90} 50 re B")

        stream_cmds.append("BT")
        stream_cmds.append("/F2 9 Tf 0.08 0.18 0.36 rg")
        stream_cmds.append(f"1 0 0 1 60 {verify_box_y + 32} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('PUBLIC VERIFICATION PORTAL')}) Tj")

        stream_cmds.append("/F1 8.5 Tf 0.25 0.28 0.32 rg")
        stream_cmds.append(f"1 0 0 1 60 {verify_box_y + 18} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('To verify the integrity and active standing of this project version, inspect:')}) Tj")

        stream_cmds.append("/F4 8.5 Tf 0.08 0.28 0.65 rg")
        stream_cmds.append(f"1 0 0 1 60 {verify_box_y + 6} Tm")
        stream_cmds.append(f"({self._escape_pdf_text(self.meta.verification_url)}) Tj")
        stream_cmds.append("ET")

        # -------------------------------------------------------------
        # 7. System Disclaimer (Mandatory)
        # -------------------------------------------------------------
        disclaimer_y = 52
        stream_cmds.append("BT")
        stream_cmds.append("/F2 7.5 Tf 0.45 0.48 0.52 rg")
        stream_cmds.append(f"1 0 0 1 45 {disclaimer_y + 12} Tm")
        stream_cmds.append(f"({self._escape_pdf_text('AUTHORITATIVE SOURCE & SYSTEM DISCLAIMER:')}) Tj")

        stream_cmds.append("/F1 7.0 Tf 0.50 0.52 0.56 rg")
        stream_cmds.append(f"1 0 0 1 45 {disclaimer_y + 2} Tm")
        disclaimer_text = (
            "Blockchain ownership proof is established solely by the smart contract record in ProjectRegistry.sol. "
            "This certificate is an application-generated, read-only proof document and does not independently create "
            "or alter blockchain ownership."
        )
        stream_cmds.append(f"({self._escape_pdf_text(disclaimer_text)}) Tj")

        stream_cmds.append("/F1 6.5 Tf 0.65 0.68 0.72 rg")
        stream_cmds.append(f"1 0 0 1 45 {disclaimer_y - 8} Tm")
        footer_gen = f"Generated by Student Project Ownership Registry Backend   |   Registration: {self.meta.registration_id}"
        stream_cmds.append(f"({self._escape_pdf_text(footer_gen)}) Tj")
        stream_cmds.append("ET")

        # -------------------------------------------------------------
        # 8. Assemble Specification-Compliant PDF 1.4 File
        # -------------------------------------------------------------
        content_stream = "\n".join(stream_cmds).encode("latin-1", errors="replace")
        stream_len = len(content_stream)

        objects: List[bytes] = []

        # Obj 1: Catalog
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        # Obj 2: Pages
        objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
        # Obj 3: Page
        page_dict = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width} {self.height}] "
            f"/Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R /F4 7 0 R >> >> "
            f"/Contents 8 0 R >>"
        )
        objects.append(page_dict.encode("ascii"))
        # Obj 4: Helvetica (Regular)
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        # Obj 5: Helvetica-Bold
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        # Obj 6: Courier (Regular)
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        # Obj 7: Courier-Bold
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")
        # Obj 8: Content Stream
        objects.append(
            f"<< /Length {stream_len} >>\nstream\n".encode("ascii")
            + content_stream
            + b"\nendstream"
        )

        # Build output buffer with exact byte offsets
        pdf_buf = bytearray()
        pdf_buf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = [0]
        for i, obj in enumerate(objects, 1):
            offsets.append(len(pdf_buf))
            pdf_buf.extend(f"{i} 0 obj\n".encode("ascii"))
            pdf_buf.extend(obj)
            pdf_buf.extend(b"\nendobj\n")

        xref_pos = len(pdf_buf)
        total_objs = len(objects) + 1
        pdf_buf.extend(f"xref\n0 {total_objs}\n".encode("ascii"))
        pdf_buf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf_buf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

        pdf_buf.extend(
            f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
        )

        return bytes(pdf_buf)


async def get_certificate_metadata(
    registration_id: str,
    db: Session,
    blockchain_service: Optional[BlockchainService] = None,
) -> CertificateMetadataData:
    """
    Retrieves trusted certificate metadata for an anchored project version.
    Enforces eligibility, on-chain verification, and dispute validation.
    Strictly READ-ONLY: creates zero database mutations.
    """
    clean_reg_id = (registration_id or "").strip()
    if not REGISTRATION_ID_PATTERN.match(clean_reg_id):
        raise ValidationException(
            code="INVALID_REGISTRATION_ID_FORMAT",
            message=f"Invalid registration ID format '{registration_id}'. Expected format: REG-YYYY-XXXXX.",
            details={"registration_id": registration_id},
        )
    normalized_id = clean_reg_id.upper()

    # 1. Query Database Version Record
    version = db.execute(
        select(ProjectVersion)
        .options(
            selectinload(ProjectVersion.project).selectinload(Project.members),
            selectinload(ProjectVersion.blockchain_record),
        )
        .where(ProjectVersion.registration_id == normalized_id)
    ).scalar_one_or_none()

    if not version:
        raise NotFoundError(
            code="REGISTRATION_NOT_FOUND",
            message=f"Certificate registration ID '{normalized_id}' not found.",
            details={"registration_id": normalized_id},
        )

    # 2. Eligibility Checks
    if version.anchoring_status != AnchoringStatus.ANCHORED:
        raise AppException(
            code="VERSION_NOT_ANCHORED",
            message=f"Cannot generate certificate for a project version in '{version.anchoring_status.value}' status. Version must be ANCHORED.",
            details={"registration_id": normalized_id, "status": version.anchoring_status.value},
            status_code=400,
        )

    record = version.blockchain_record
    if not record:
        raise AppException(
            code="BLOCKCHAIN_RECORD_NOT_FOUND",
            message="No blockchain record found for this anchored project version.",
            details={"registration_id": normalized_id},
            status_code=400,
        )

    # 3. Blockchain & Verification Integrity Check
    verification_res = await verify_by_registration_id(
        db=db,
        registration_id=normalized_id,
    )

    # Cryptographic match verification
    if verification_res.blockchain_proof and not verification_res.blockchain_proof.match_confirmed:
        raise AppException(
            code="CRYPTOGRAPHIC_MISMATCH",
            message=verification_res.message or "Cryptographic verification mismatch against on-chain proof.",
            details={"registration_id": normalized_id, "mismatch": verification_res.message},
            status_code=400,
        )

    # 4. Dispute State Rule Enforcement
    effective_dispute = (
        (verification_res.blockchain_proof.dispute_status if verification_res.blockchain_proof else None)
        or version.dispute_status.value
        if hasattr(version.dispute_status, "value")
        else str(version.dispute_status)
    ).upper()

    if effective_dispute in ("OPEN", "UNDER_REVIEW"):
        raise ConflictError(
            code="ACTIVE_DISPUTE_EXISTS",
            message=f"Cannot generate certificate for project version '{normalized_id}' with an active dispute ({effective_dispute}).",
            details={"registration_id": normalized_id, "dispute_status": effective_dispute},
        )

    if effective_dispute == "RESOLVED":
        raise ConflictError(
            code="DISPUTED_VERSION_CANNOT_GENERATE_CERTIFICATE",
            message=f"Ownership dispute was upheld against project version '{normalized_id}' (RESOLVED). Certificate cannot be generated.",
            details={"registration_id": normalized_id, "dispute_status": effective_dispute},
        )

    # 5. Assemble Authoritative Metadata
    project = version.project
    author_names: List[str] = []
    institution_name = "National Institute of Technology"

    if project and project.members:
        # Sort members: owner first, then contributors
        sorted_members = sorted(project.members, key=lambda m: (not m.is_owner, m.user.full_name if m.user else ""))
        for m in sorted_members:
            if m.user and m.user.full_name:
                author_names.append(m.user.full_name)
                if m.is_owner and m.user.institution_id:
                    institution_name = m.user.institution_id

    if not author_names:
        author_names = ["Verified Project Contributor"]

    tx_hash = (
        (verification_res.blockchain_proof.transaction_hash if verification_res.blockchain_proof else None)
        or record.transaction_hash
    )
    block_num = (
        (verification_res.blockchain_proof.block_number if verification_res.blockchain_proof else None)
        or record.block_number
    )
    anchored_time = (
        (verification_res.blockchain_proof.block_timestamp if verification_res.blockchain_proof else None)
        or record.anchored_timestamp
    )

    base_url = getattr(settings, "APP_BASE_URL", "https://registry.sih2026.edu").rstrip("/")
    verification_url = f"{base_url}/verify/{normalized_id}"
    qr_svg_url = f"{base_url}/api/v1/certificates/{normalized_id}/qr.svg"
    pdf_download_url = f"{base_url}/api/v1/certificates/{normalized_id}/download"

    return CertificateMetadataData(
        registration_id=normalized_id,
        project_title=project.title if project else version.title,
        version_tag=version.version_tag,
        lifecycle_stage=(
            version.lifecycle_stage.value
            if hasattr(version.lifecycle_stage, "value")
            else str(version.lifecycle_stage)
        ),
        authors=author_names,
        institution=institution_name,
        department=project.department if project else None,
        anchored_timestamp=anchored_time,
        transaction_hash=tx_hash,
        block_number=block_num,
        composite_sha256=version.composite_sha256,
        ipfs_root_cid=version.ipfs_root_cid,
        verification_url=verification_url,
        qr_code_svg_url=qr_svg_url,
        pdf_download_url=pdf_download_url,
        dispute_status=effective_dispute,
    )


async def generate_certificate_pdf(
    registration_id: str,
    db: Session,
    blockchain_service: Optional[BlockchainService] = None,
) -> bytes:
    """
    Generates specification-compliant PDF certificate binary for the specified registration ID.
    Enforces complete validation and produces a read-only PDF artifact.
    """
    metadata = await get_certificate_metadata(
        registration_id=registration_id,
        db=db,
        blockchain_service=blockchain_service,
    )
    generator = OwnershipCertificatePDFGenerator(metadata)
    return generator.build_pdf()

