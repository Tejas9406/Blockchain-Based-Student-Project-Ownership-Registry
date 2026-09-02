// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import { IProjectRegistry } from "./interfaces/IProjectRegistry.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { Ownable2Step } from "@openzeppelin/contracts/access/Ownable2Step.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ProjectRegistry
 * @dev Production implementation of the Blockchain-Based Student Project Ownership Registry.
 *
 * System Mandate:
 * - Immutable proof of existence, ownership, and integrity for academic projects and IP.
 * - Zero raw artifact storage on-chain; only 32-byte cryptographic hashes and IPFS CIDs.
 * - Gas Relayer architecture separating transaction gas payer (msg.sender) from project authors.
 * - Conforms strictly to docs/blockchain/BLOCKCHAIN_DESIGN.md and docs/architecture/INTEGRATION_CONTRACT.md.
 */
contract ProjectRegistry is IProjectRegistry, Ownable2Step, ReentrancyGuard {
    // =========================================================================
    // CUSTOM ERRORS
    // =========================================================================

    /// @notice Thrown when a caller is neither the authorized relayer nor the contract owner.
    error UnauthorizedRelayer(address caller);

    /// @notice Thrown when attempting to register with an empty registration ID string.
    error EmptyRegistrationId();

    /// @notice Thrown when attempting to register a duplicate registration ID.
    error RegistrationIdAlreadyExists(string registrationId);

    /// @notice Thrown when composite hash is zero (0x0).
    error ZeroCompositeHash();

    /// @notice Thrown when IPFS root CID string is empty.
    error EmptyIpfsRootCID();

    /// @notice Thrown when version index is zero (must be >= 1).
    error InvalidVersionIndex();

    /// @notice Thrown when query or mutation targets a non-existent registration ID.
    error VersionNotFound(string registrationId);

    /// @notice Thrown when dispute evidence CID string is empty.
    error EmptyDisputeEvidence();

    /// @notice Thrown when a dispute is raised while an existing dispute is already active.
    error ActiveDisputeExists(string registrationId, DisputeStatus currentState);

    /// @notice Thrown when attempting to resolve a dispute with an invalid target status.
    error InvalidDisputeResolutionStatus(DisputeStatus status);

    /// @notice Thrown when setting the relayer to address(0).
    error InvalidRelayerAddress();

    // =========================================================================
    // EVENTS (Administrative)
    // =========================================================================

    /// @notice Emitted when the platform gas relayer address is updated by the contract owner.
    event RelayerUpdated(address indexed previousRelayer, address indexed newRelayer);

    // =========================================================================
    // STORAGE LAYOUT
    // =========================================================================

    /// @dev Sequential global record index counter.
    uint256 private _recordCounter;

    /// @dev Primary lookup mapping from unique registration ID to immutable VersionProof.
    mapping(string => VersionProof) private _versions;

    /// @dev Reverse mapping from global recordId to unique registration ID.
    mapping(uint256 => string) private _recordIdToRegistrationId;

    /// @notice The designated platform gas relayer address authorized to submit proof registrations.
    address public relayer;

    // =========================================================================
    // MODIFIERS
    // =========================================================================

    /**
     * @dev Restricts invocation to the authorized gas relayer or contract owner.
     * Prevents arbitrary untrusted accounts from polluting the immutable registry.
     */
    modifier onlyRelayer() {
        if (msg.sender != relayer && msg.sender != owner()) {
            revert UnauthorizedRelayer(msg.sender);
        }
        _;
    }

    // =========================================================================
    // CONSTRUCTOR
    // =========================================================================

    /**
     * @notice Initializes the ProjectRegistry with an initial owner and authorized relayer.
     * @param initialOwner The primary administrative contract owner (uses Ownable2Step).
     * @param initialRelayer The initial backend gas relayer wallet authorized to submit proofs.
     */
    constructor(address initialOwner, address initialRelayer) Ownable(initialOwner) {
        if (initialRelayer == address(0)) {
            revert InvalidRelayerAddress();
        }
        relayer = initialRelayer;
        emit RelayerUpdated(address(0), initialRelayer);
    }

    // =========================================================================
    // RELAYER ADMINISTRATION
    // =========================================================================

    /**
     * @notice Updates the designated platform gas relayer address.
     * @dev Administrative function outside the frozen public registry interface.
     * Protected by Ownable2Step (only contract owner can call).
     * @param newRelayer The new relayer wallet address (cannot be address(0)).
     */
    function setRelayer(address newRelayer) external onlyOwner {
        if (newRelayer == address(0)) {
            revert InvalidRelayerAddress();
        }
        address previousRelayer = relayer;
        relayer = newRelayer;
        emit RelayerUpdated(previousRelayer, newRelayer);
    }

    // =========================================================================
    // CORE REGISTRY FUNCTIONS
    // =========================================================================

    /**
     * @inheritdoc IProjectRegistry
     * @dev ReentrancyGuard is applied as required by INTEGRATION_CONTRACT.md Section 5.1
     * to protect state-changing registry boundaries.
     */
    function registerProjectVersion(
        string calldata registrationId,
        bytes32 compositeHash,
        string calldata ipfsRootCID,
        uint16 versionIndex,
        LifecycleStage stage,
        address author,
        address[] calldata coAuthors
    ) external onlyRelayer nonReentrant returns (uint256 recordId) {
        // Validation Checks
        if (bytes(registrationId).length == 0) {
            revert EmptyRegistrationId();
        }
        if (_versions[registrationId].exists) {
            revert RegistrationIdAlreadyExists(registrationId);
        }
        if (compositeHash == bytes32(0)) {
            revert ZeroCompositeHash();
        }
        if (bytes(ipfsRootCID).length == 0) {
            revert EmptyIpfsRootCID();
        }
        if (versionIndex == 0) {
            revert InvalidVersionIndex();
        }

        // Increment sequential global counter
        uint256 newRecordId = ++_recordCounter;

        // Persist immutable VersionProof
        _versions[registrationId] = VersionProof({
            recordId: newRecordId,
            registrationId: registrationId,
            compositeHash: compositeHash,
            ipfsRootCID: ipfsRootCID,
            versionIndex: versionIndex,
            lifecycleStage: stage,
            author: author,
            coAuthors: coAuthors,
            anchoredTimestamp: block.timestamp,
            blockNumber: block.number,
            disputeState: DisputeStatus.NONE,
            exists: true
        });

        // Store reverse lookup index
        _recordIdToRegistrationId[newRecordId] = registrationId;

        // Emit canonical registration event with actual transaction sender as relayer
        emit ProjectVersionRegistered(
            newRecordId,
            registrationId,
            compositeHash,
            ipfsRootCID,
            versionIndex,
            stage,
            author,
            msg.sender,
            block.timestamp
        );

        return newRecordId;
    }

    /**
     * @inheritdoc IProjectRegistry
     * @dev Trustless view function. MUST NOT revert on missing registration ID or hash mismatch.
     * Returns isValid = false if not found or if hashes do not match.
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
    ) {
        VersionProof storage proof = _versions[registrationId];

        // Safe return on missing record (zero mutation, no revert)
        if (!proof.exists) {
            return (false, 0, "", address(0), DisputeStatus.NONE);
        }

        // Compare cryptographic anchor with verifier's expected composite digest
        bool matches = (proof.compositeHash == expectedHash);

        return (
            matches,
            proof.anchoredTimestamp,
            proof.ipfsRootCID,
            proof.author,
            proof.disputeState
        );
    }

    /**
     * @inheritdoc IProjectRegistry
     * @dev Reverts with VersionNotFound if registrationId does not exist on-chain.
     */
    function getProjectVersion(
        string calldata registrationId
    ) external view returns (VersionProof memory) {
        VersionProof storage proof = _versions[registrationId];
        if (!proof.exists) {
            revert VersionNotFound(registrationId);
        }
        return proof;
    }

    /**
     * @inheritdoc IProjectRegistry
     * @dev Anyone can log a dispute against an anchored version with evidence.
     * Prevents raising a new dispute if one is already OPEN or UNDER_REVIEW.
     */
    function raiseDispute(
        string calldata registrationId,
        string calldata evidenceCID
    ) external nonReentrant {
        VersionProof storage proof = _versions[registrationId];
        if (!proof.exists) {
            revert VersionNotFound(registrationId);
        }
        if (bytes(evidenceCID).length == 0) {
            revert EmptyDisputeEvidence();
        }
        if (proof.disputeState == DisputeStatus.OPEN || proof.disputeState == DisputeStatus.UNDER_REVIEW) {
            revert ActiveDisputeExists(registrationId, proof.disputeState);
        }

        proof.disputeState = DisputeStatus.OPEN;

        emit DisputeLogged(
            registrationId,
            msg.sender,
            evidenceCID,
            block.timestamp
        );
    }

    /**
     * @inheritdoc IProjectRegistry
     * @dev Adjudicates a dispute. Restricted to contract owner (admin) via onlyOwner.
     * Allowed resolution states: RESOLVED or REJECTED.
     * Note on UNDER_REVIEW: The frozen enum includes UNDER_REVIEW for off-chain/indexer state,
     * but the frozen interface does not expose an intermediate transition function.
     */
    function resolveDispute(
        string calldata registrationId,
        DisputeStatus status
    ) external onlyOwner nonReentrant {
        VersionProof storage proof = _versions[registrationId];
        if (!proof.exists) {
            revert VersionNotFound(registrationId);
        }
        if (status != DisputeStatus.RESOLVED && status != DisputeStatus.REJECTED) {
            revert InvalidDisputeResolutionStatus(status);
        }

        proof.disputeState = status;

        emit DisputeResolved(
            registrationId,
            status,
            msg.sender,
            block.timestamp
        );
    }

    // =========================================================================
    // PUBLIC RECORD INSPECTION HELPERS
    // =========================================================================

    /**
     * @notice Returns the total number of project versions anchored in this registry.
     */
    function totalRecords() external view returns (uint256) {
        return _recordCounter;
    }

    /**
     * @notice Returns the registration ID associated with a sequential recordId.
     * @param recordId The sequential record index.
     */
    function getRegistrationIdByRecordId(uint256 recordId) external view returns (string memory) {
        return _recordIdToRegistrationId[recordId];
    }
}
