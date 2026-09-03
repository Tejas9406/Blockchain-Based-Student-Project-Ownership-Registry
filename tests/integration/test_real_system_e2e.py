"""
Real System End-to-End Integration Validation Script
Blockchain-Based Student Project Ownership Registry (SIH 2026 - CYB05)

Executes actual HTTP requests against live FastAPI server on http://127.0.0.1:8000,
live PostgreSQL on localhost:5433, and live Hardhat EVM Node on http://127.0.0.1:8545.
"""

import hashlib
import io
import json
import os
import sys
import time
import uuid
import httpx
import psycopg2
from web3 import Web3

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
DB_URL = os.getenv("DATABASE_URL", "postgresql://registry_user:registry_password_dev@localhost:5433/project_registry_db")

results = {}

def log_step(name, status, details=""):
    results[name] = {"status": status, "details": details}
    print(f"[{status}] {name}: {details}")

def run_e2e_validation():
    print("================================================================")
    print("STARTING PHASE 3 REAL SYSTEM E2E INTEGRATION VALIDATION")
    print("================================================================\n")

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # -------------------------------------------------------------------------
    # STEP 2 & 6: Health & Service Availability
    # -------------------------------------------------------------------------
    try:
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health check returned {health_resp.status_code}"
        health_data = health_resp.json()
        assert health_data["status"] == "ok"
        assert health_data["database"]["connected"] is True
        assert health_data["blockchain"]["connected"] is True
        contract_address = health_data["blockchain"]["contract_address"]
        relayer_address = health_data["blockchain"]["relayer_address"]
        log_step("Services Availability", "PASS", f"FastAPI OK, DB Connected, Blockchain connected at {contract_address}")
    except Exception as e:
        log_step("Services Availability", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 7: Real Authentication Flow
    # -------------------------------------------------------------------------
    unique_suffix = uuid.uuid4().hex[:8]
    student_email = f"student_{unique_suffix}@institution.edu"
    student_pwd = f"SecurePass_{unique_suffix}!123"
    student_name = f"Test Student {unique_suffix}"

    try:
        # 1. Register
        reg_resp = client.post("/auth/register", json={
            "email": student_email,
            "password": student_pwd,
            "full_name": student_name,
            "role": "STUDENT",
            "institution_id": "NIT-2026-001",
            "department": "Computer Science & Engineering"
        })
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
        student_user = reg_resp.json()["data"]
        student_id = student_user["public_id"]

        # 2. Login
        login_resp = client.post("/auth/login", json={
            "email": student_email,
            "password": student_pwd
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        auth_tokens = login_resp.json()["data"]
        access_token = auth_tokens["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Call Authenticated /auth/me
        me_resp = client.get("/auth/me", headers=auth_headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["email"] == student_email

        # 4. Confirm unauthenticated request is rejected (401)
        unauth_resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert unauth_resp.status_code == 401

        log_step("Authentication Flow", "PASS", f"Registered {student_id}, logged in, validated session and 401 guard.")
    except Exception as e:
        log_step("Authentication Flow", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 8: Real Project Creation Flow
    # -------------------------------------------------------------------------
    try:
        proj_resp = client.post("/projects", headers=auth_headers, json={
            "title": f"Decentralized IPFS Research Platform {unique_suffix}",
            "abstract": "A tamper-proof system for registering student research outputs on blockchain.",
            "category": "Blockchain & Web3",
            "department": "Computer Science & Engineering",
            "academic_year": "2025-2026",
            "current_lifecycle_stage": "DESIGN",
            "visibility": "PUBLIC"
        })
        assert proj_resp.status_code == 201, f"Project creation failed: {proj_resp.text}"
        project_data = proj_resp.json()["data"]
        project_id = project_data["public_id"]
        assert project_id.startswith("PRJ-")
        assert len(project_id.split("-")) == 3

        # Verify directly in PostgreSQL
        pg_conn = psycopg2.connect(DB_URL)
        cur = pg_conn.cursor()
        cur.execute("SELECT id, public_id, title, status FROM projects WHERE public_id = %s", (project_id,))
        db_proj = cur.fetchone()
        assert db_proj is not None
        assert db_proj[1] == project_id
        cur.close()
        pg_conn.close()

        log_step("Project Creation Flow", "PASS", f"Project {project_id} created and verified in PostgreSQL.")
    except Exception as e:
        log_step("Project Creation Flow", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 9: Real Team Member Flow
    # -------------------------------------------------------------------------
    peer_email = f"peer_{unique_suffix}@institution.edu"
    peer_pwd = f"PeerPass_{unique_suffix}!123"
    try:
        # Register peer user
        peer_reg = client.post("/auth/register", json={
            "email": peer_email,
            "password": peer_pwd,
            "full_name": f"Peer Researcher {unique_suffix}",
            "role": "STUDENT",
            "institution_id": "NIT-2026-002",
            "department": "Computer Science & Engineering"
        })
        peer_id = peer_reg.json()["data"]["public_id"]

        # Add member to project
        add_member_resp = client.post(f"/projects/{project_id}/members", headers=auth_headers, json={
            "user_public_id": peer_id,
            "role_in_project": "CONTRIBUTOR",
            "contribution_percentage": 40.0
        })
        assert add_member_resp.status_code == 201, f"Add member failed: {add_member_resp.text}"

        # Retrieve members list
        members_resp = client.get(f"/projects/{project_id}/members", headers=auth_headers)
        assert members_resp.status_code == 200
        members_list = members_resp.json()["data"]
        assert any(m["user"]["public_id"] == peer_id for m in members_list)

        # Duplicate member rejection check (409)
        dup_member_resp = client.post(f"/projects/{project_id}/members", headers=auth_headers, json={
            "user_public_id": peer_id,
            "role_in_project": "CONTRIBUTOR",
            "contribution_percentage": 20.0
        })
        assert dup_member_resp.status_code == 409

        log_step("Team Member Flow", "PASS", f"Added member {peer_id} with 40% contribution, 409 duplicate verified.")
    except Exception as e:
        log_step("Team Member Flow", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 10: Real Artifact Upload Flow
    # -------------------------------------------------------------------------
    artifact_content = f"Official Architecture Specification v1 - Project {unique_suffix}\nDeterministic Test Content.".encode("utf-8")
    expected_artifact_sha256 = hashlib.sha256(artifact_content).hexdigest()

    try:
        files = {"file": ("architecture_v1.txt", io.BytesIO(artifact_content), "text/plain")}
        data = {
            "artifact_category": "DESIGN_SPEC",
            "project_id": project_id
        }
        upload_resp = client.post("/artifacts/upload", headers=auth_headers, files=files, data=data)
        assert upload_resp.status_code == 201, f"Artifact upload failed: {upload_resp.text}"
        artifact_data = upload_resp.json()["data"]
        artifact_id = artifact_data["public_id"]
        assert artifact_data["sha256_hash"].lower() == expected_artifact_sha256.lower()

        log_step("Artifact Flow", "PASS", f"Uploaded {artifact_id}, verified SHA-256 {expected_artifact_sha256[:12]}...")
    except Exception as e:
        log_step("Artifact Flow", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 11 & 12: Real Milestone Version & Blockchain Anchoring Flow
    # -------------------------------------------------------------------------
    try:
        idempotency_key = str(uuid.uuid4())
        version_resp = client.post(
            f"/projects/{project_id}/versions",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json={
                "version_tag": "v1.0",
                "lifecycle_stage": "DESIGN",
                "title": "System Architecture & Threat Model",
                "description": "Initial architectural specifications and threat analysis.",
                "artifact_ids": [artifact_id]
            }
        )
        assert version_resp.status_code == 201, f"Version creation failed: {version_resp.text}"
        version_data = version_resp.json()["data"]
        registration_id = version_data["registration_id"]
        version_id = version_data["public_id"]
        anchoring_status = version_data["anchoring_status"]

        assert registration_id.startswith("REG-")
        assert anchoring_status == "ANCHORED", f"Expected ANCHORED, got {anchoring_status}"
        assert version_data["blockchain_record"] is not None
        tx_hash = version_data["blockchain_record"]["transaction_hash"]
        block_num = version_data["blockchain_record"]["block_number"]
        composite_sha256 = version_data["composite_sha256"]
        root_cid = version_data["ipfs_root_cid"]

        # Verify on-chain state via Web3
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        assert w3.is_connected(), "Web3 cannot connect to Hardhat"
        with open("backend/app/abi/ProjectRegistry.json", "r") as f:
            contract_abi = json.load(f)["abi"]
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        proof = contract.functions.getProjectVersion(registration_id).call()
        # proof struct: [recordId, registrationId, compositeHash, ipfsRootCID, versionIndex, lifecycleStage, author, coAuthors, anchoredTimestamp, blockNumber, disputeState, exists]
        assert proof[1] == registration_id
        assert proof[2].hex() == composite_sha256.lower()
        assert proof[3] == root_cid
        assert proof[4] == 1  # versionIndex
        assert proof[5] == 1  # LifecycleStage.DESIGN (1)

        log_step("Blockchain Anchoring Flow", "PASS", f"Anchored {registration_id} on-chain in block {block_num} (Tx: {tx_hash[:16]}...)")
    except Exception as e:
        import traceback
        log_step("Blockchain Anchoring Flow", "FAIL", f"{e}\n{traceback.format_exc()}")
        return

    # -------------------------------------------------------------------------
    # STEP 13: Real Verification Flow
    # -------------------------------------------------------------------------
    try:
        # 1. Verify by Registration ID
        verify_reg_resp = client.get(f"/verification/verify-registration/{registration_id}")
        assert verify_reg_resp.status_code == 200, f"Verify reg failed: {verify_reg_resp.text}"
        verify_reg_data = verify_reg_resp.json()["data"]
        assert verify_reg_data["is_valid"] is True
        assert verify_reg_data["blockchain_proof"]["match_confirmed"] is True

        # 2. Verify by Hash
        verify_hash_resp = client.post("/verification/verify-hash", json={"sha256_hash": composite_sha256})
        assert verify_hash_resp.status_code == 200, f"Verify hash failed: {verify_hash_resp.text}"
        assert verify_hash_resp.json()["data"]["is_valid"] is True

        # 3. Verify by File Upload
        verify_file_resp = client.post(
            "/verification/verify-file",
            files={"file": ("architecture_v1.txt", io.BytesIO(artifact_content), "text/plain")}
        )
        assert verify_file_resp.status_code == 200, f"Verify file failed: {verify_file_resp.text}"
        assert verify_file_resp.json()["data"]["is_valid"] is True

        log_step("Verification Flow", "PASS", f"Registration ID, Hash, and File verification all validated true.")
    except Exception as e:
        import traceback
        log_step("Verification Flow", "FAIL", f"{e}\n{traceback.format_exc()}")
        return

    # -------------------------------------------------------------------------
    # STEP 14: Real Certificate Flow
    # -------------------------------------------------------------------------
    try:
        # 1. Certificate Metadata
        cert_meta_resp = client.get(f"/certificates/{registration_id}")
        assert cert_meta_resp.status_code == 200, f"Cert meta failed: {cert_meta_resp.text}"
        cert_meta = cert_meta_resp.json()["data"]
        assert cert_meta["registration_id"] == registration_id
        assert cert_meta["project_title"] == f"Decentralized IPFS Research Platform {unique_suffix}"
        assert cert_meta["version_tag"] == "v1.0"

        # 2. Certificate PDF Download
        pdf_resp = client.get(f"/certificates/{registration_id}/download")
        assert pdf_resp.status_code == 200, f"PDF download failed: {pdf_resp.status_code}"
        assert pdf_resp.headers.get("content-type") == "application/pdf"
        assert len(pdf_resp.content) > 1000, "PDF binary is too small or empty"
        assert pdf_resp.content.startswith(b"%PDF-"), "File does not start with PDF magic header"

        log_step("Certificate Flow", "PASS", f"Generated metadata & downloaded valid PDF certificate ({len(pdf_resp.content)} bytes).")
    except Exception as e:
        log_step("Certificate Flow", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 15: Real Dispute Flow
    # -------------------------------------------------------------------------
    claimant_email = f"claimant_{unique_suffix}@institution.edu"
    claimant_pwd = f"ClaimPass_{unique_suffix}!123"
    try:
        # Register claimant
        claimant_reg = client.post("/auth/register", json={
            "email": claimant_email,
            "password": claimant_pwd,
            "full_name": f"Prior Art Author {unique_suffix}",
            "role": "STUDENT",
            "institution_id": "NIT-2024-999",
            "department": "Computer Science & Engineering"
        })
        claimant_login = client.post("/auth/login", json={"email": claimant_email, "password": claimant_pwd})
        claimant_headers = {"Authorization": f"Bearer {claimant_login.json()['data']['access_token']}"}

        # File dispute
        dispute_resp = client.post("/disputes", headers=claimant_headers, json={
            "registration_id": registration_id,
            "dispute_type": "PLAGIARISM",
            "claim_description": "Our team published this architecture and dataset in 2024 prior to this registration.",
            "evidence_url": "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"
        })
        assert dispute_resp.status_code == 201, f"Dispute creation failed: {dispute_resp.text}"
        dispute_data = dispute_resp.json()["data"]
        dispute_id = dispute_data["public_id"]
        assert dispute_data["status"] == "OPEN"
        dispute_tx = dispute_data["transaction_hash"]

        # Verify dispute standing reflected in Verification endpoint
        verify_dispute = client.get(f"/verification/verify-registration/{registration_id}")
        assert verify_dispute.json()["data"]["blockchain_proof"]["dispute_status"] == "OPEN"

        log_step("Dispute Flow", "PASS", f"Created dispute {dispute_id} on-chain (Tx: {dispute_tx[:16]}...), verification reflects OPEN.")
    except Exception as e:
        log_step("Dispute Flow", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 16: Real Admin Adjudication
    # -------------------------------------------------------------------------
    admin_email = f"admin_{unique_suffix}@institution.edu"
    admin_pwd = f"AdminPass_{unique_suffix}!123"
    try:
        # Register User then promote to ADMIN in database
        admin_reg = client.post("/auth/register", json={
            "email": admin_email,
            "password": admin_pwd,
            "full_name": f"Institutional Administrator {unique_suffix}",
            "role": "STUDENT",
            "institution_id": "NIT-ADMIN-01",
            "department": "Institutional Review Board"
        })
        assert admin_reg.status_code == 201, f"Admin reg failed: {admin_reg.text}"
        admin_uid = admin_reg.json()["data"]["public_id"]
        
        # Elevate role to ADMIN in DB
        admin_conn = psycopg2.connect(DB_URL)
        with admin_conn.cursor() as admin_cur:
            admin_cur.execute("UPDATE users SET role = 'ADMIN' WHERE public_id = %s", (admin_uid,))
        admin_conn.commit()
        admin_conn.close()

        admin_login = client.post("/auth/login", json={"email": admin_email, "password": admin_pwd})
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

        # Adjudicate dispute as REJECTED
        adj_resp = client.patch(
            f"/admin/disputes/{dispute_id}/adjudicate",
            headers=admin_headers,
            json={
                "resolution_status": "REJECTED",
                "resolution_notes": "Official Review: Prior art claims examined; original authorship confirmed with verifiable git timestamps."
            }
        )
        assert adj_resp.status_code == 200, f"Adjudication failed: {adj_resp.text}"
        adj_data = adj_resp.json()["data"]
        assert adj_data["status"] == "REJECTED"
        assert adj_data["resolution_notes"] is not None

        # Verify on-chain dispute resolution state
        proof_after_adj = contract.functions.getProjectVersion(registration_id).call()
        assert proof_after_adj[10] == 4  # DisputeStatus.REJECTED (4)

        log_step("Admin Adjudication Flow", "PASS", f"Dispute {dispute_id} adjudicated as REJECTED on-chain and in PostgreSQL.")
    except Exception as e:
        import traceback
        log_step("Admin Adjudication Flow", "FAIL", f"{e}\n{traceback.format_exc()}")
        return

    # -------------------------------------------------------------------------
    # STEP 17: Post-Adjudication Verification & Certificate
    # -------------------------------------------------------------------------
    try:
        post_verify = client.get(f"/verification/verify-registration/{registration_id}")
        assert post_verify.status_code == 200
        post_data = post_verify.json()["data"]
        assert post_data["blockchain_proof"]["dispute_status"] == "REJECTED"
        assert post_data["is_valid"] is True
        assert post_data["blockchain_proof"]["match_confirmed"] is True

        post_cert = client.get(f"/certificates/{registration_id}")
        assert post_cert.status_code == 200
        assert post_cert.json()["data"]["dispute_status"] == "REJECTED"

        log_step("Post-Adjudication Verification", "PASS", f"Registration remains immutable and valid; dispute standing shows REJECTED.")
    except Exception as e:
        log_step("Post-Adjudication Verification", "FAIL", str(e))
        return

    # -------------------------------------------------------------------------
    # STEP 18: Failure & Recovery Testing
    # -------------------------------------------------------------------------
    try:
        # 1. Missing registration query -> 404
        missing_reg = client.get("/verification/verify-registration/REG-2026-99999")
        assert missing_reg.status_code == 404, f"Expected 404, got {missing_reg.status_code}"

        # Malformed registration query -> 422
        inv_reg = client.get("/verification/verify-registration/REG-9999-INVALID")
        assert inv_reg.status_code == 422, f"Expected 422, got {inv_reg.status_code}"

        # 2. Student attempting admin adjudication -> 403 Forbidden
        unauth_adj = client.patch(
            f"/admin/disputes/{dispute_id}/adjudicate",
            headers=auth_headers,
            json={"resolution_status": "RESOLVED", "resolution_notes": "Unauthorized attempt"}
        )
        assert unauth_adj.status_code == 403

        # 3. Invalid lifecycle stage creation -> 422 Unprocessable Entity
        bad_lifecycle = client.post(
            f"/projects/{project_id}/versions",
            headers=auth_headers,
            json={
                "version_tag": "v2.0",
                "lifecycle_stage": "DEVELOPMENT",  # Invalid enum value
                "title": "Invalid Lifecycle Test",
                "artifact_ids": [artifact_id]
            }
        )
        assert bad_lifecycle.status_code == 422

        log_step("Failure & Recovery Tests", "PASS", f"Verified 404 on missing record, 403 on non-admin adjudication, 422 on invalid lifecycle enum.")
    except Exception as e:
        import traceback
        log_step("Failure & Recovery Tests", "FAIL", f"{e}\n{traceback.format_exc()}")
        return

    # -------------------------------------------------------------------------
    # STEP 19: Full Reconciliation Check
    # -------------------------------------------------------------------------
    try:
        pg_conn = psycopg2.connect(DB_URL)
        cur = pg_conn.cursor()
        cur.execute("""
            SELECT pv.registration_id, pv.composite_sha256, pv.ipfs_root_cid, pv.version_index, pv.lifecycle_stage, br.transaction_hash
            FROM project_versions pv
            JOIN blockchain_records br ON br.version_id = pv.id
            WHERE pv.registration_id = %s
        """, (registration_id,))
        db_record = cur.fetchone()
        cur.close()
        pg_conn.close()

        assert db_record is not None
        db_reg, db_hash, db_cid, db_idx, db_stage, db_tx = db_record

        # Compare DB with Chain proof
        assert db_reg == proof[1]
        assert db_hash.lower() == proof[2].hex()
        assert db_cid == proof[3]
        assert db_idx == proof[4]
        assert db_stage == "DESIGN" and proof[5] == 1
        assert db_tx.lower() == tx_hash.lower()

        log_step("Reconciliation Check", "PASS", f"100% exact parity between PostgreSQL and Smart Contract proof fields.")
    except Exception as e:
        import traceback
        log_step("Reconciliation Check", "FAIL", f"{e}\n{traceback.format_exc()}")
        return

    print("\n================================================================")
    print("ALL REAL SYSTEM E2E FLOWS EXECUTED SUCCESSFULLY!")
    print("================================================================")

if __name__ == "__main__":
    run_e2e_validation()
