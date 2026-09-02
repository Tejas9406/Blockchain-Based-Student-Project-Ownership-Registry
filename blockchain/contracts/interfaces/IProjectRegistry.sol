// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IProjectRegistry
 * @dev Interface for the Blockchain-Based Student Project Ownership Registry (SIH 2026 CYB05).
 * Frozen specification strictly conforming to docs/blockchain/BLOCKCHAIN_DESIGN.md.
 */
interface IProjectRegistry {
    // =========================================================================
    // ENUMS & STRUCTS
    // =========================================================================

    enum LifecycleStage {
        IDEA,
        DESIGN,
        PROTOTYPE,
        FINAL
    }

    enum DisputeStatus {
        NONE,
        OPEN,
        UNDER_REVIEW,
        RESOLVED,
        REJECTED
    }

    struct VersionProof {
        uint256 recordId;
        string registrationId;
        bytes32 compositeHash;
        string ipfsRootCID;
        uint16 versionIndex;
        LifecycleStage lifecycleStage;
        address author;
        address[] coAuthors;
        uint256 anchoredTimestamp;
        uint256 blockNumber;
        DisputeStatus disputeState;
        bool exists;
    }

    // =========================================================================
    // EVENTS
    // =========================================================================

    event ProjectVersionRegistered(
        uint256 indexed recordId,
        string indexed registrationId,
        bytes32 indexed compositeHash,
        string ipfsRootCID,
        uint16 versionIndex,
        LifecycleStage stage,
        address author,
        address relayer,
        uint256 timestamp
    );

    event DisputeLogged(
        string indexed registrationId,
        address indexed claimant,
        string evidenceCID,
        uint256 timestamp
    );

    event DisputeResolved(
        string indexed registrationId,
        DisputeStatus newStatus,
        address adjudicatedBy,
        uint256 timestamp
    );

    // =========================================================================
    // CORE REGISTRY FUNCTIONS
    // =========================================================================

    /**
     * @notice Anchors an immutable project version snapshot on-chain.
     * @param registrationId Unique certificate ID (e.g., "REG-2026-A8F92")
     * @param compositeHash 32-byte deterministic SHA-256 digest
     * @param ipfsRootCID Root IPFS directory CID
     * @param versionIndex Sequential version number (1, 2, 3...)
     * @param stage Milestone lifecycle stage
     * @param author Project owner student wallet address
     * @param coAuthors List of team member wallet addresses
     * @return recordId The assigned global record ID
     */
    function registerProjectVersion(
        string calldata registrationId,
        bytes32 compositeHash,
        string calldata ipfsRootCID,
        uint16 versionIndex,
        LifecycleStage stage,
        address author,
        address[] calldata coAuthors
    ) external returns (uint256 recordId);

    /**
     * @notice Trustless public verification endpoint.
     * @param registrationId The certificate registration identifier
     * @param expectedHash The SHA-256 hash to verify against the on-chain anchor
     * @return isValid True if hash matches and record exists
     * @return anchoredTimestamp The block timestamp of registration
     * @return ipfsRootCID The associated IPFS storage CID
     * @return author The project owner wallet address
     * @return disputeState The active dispute standing
     */
    function verifyProjectVersion(
        string calldata registrationId,
        bytes32 expectedHash
    ) external view returns (
        bool isValid,
        uint256 anchoredTimestamp,
        string memory ipfsRootCID,
        address author,
        DisputeStatus disputeState
    );

    /**
     * @notice Retrieves full on-chain version proof struct.
     * @param registrationId The certificate registration identifier
     */
    function getProjectVersion(
        string calldata registrationId
    ) external view returns (VersionProof memory);

    /**
     * @notice Logs an on-chain dispute notice against an anchored version.
     * @param registrationId The disputed certificate identifier
     * @param evidenceCID IPFS CID pointing to claimant's evidence dossier
     */
    function raiseDispute(
        string calldata registrationId,
        string calldata evidenceCID
    ) external;

    /**
     * @notice Adjudicates a dispute (Restricted to Authorized Admin/Contract Owner).
     * @param registrationId The disputed certificate identifier
     * @param status The final resolution status
     */
    function resolveDispute(
        string calldata registrationId,
        DisputeStatus status
    ) external;
}
