// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title HealthCheck
 * @dev Minimal placeholder smart contract to verify the Hardhat development, compilation,
 *      deployment, and testing environment for the Student Project Ownership Registry.
 *
 * NOTE: Real business contracts (ProjectRegistry, OwnershipVerifier, CertificateIssuer)
 *       will be developed in Phase 1 and Phase 2.
 */
contract HealthCheck {
    string private status;
    uint256 public deploymentTimestamp;
    address public owner;

    event StatusUpdated(string oldStatus, string newStatus, address updatedBy);

    constructor(string memory initialStatus) {
        owner = msg.sender;
        status = initialStatus;
        deploymentTimestamp = block.timestamp;
    }

    /**
     * @notice Simple diagnostic function returning pong.
     */
    function ping() external pure returns (string memory) {
        return "pong";
    }

    /**
     * @notice Returns the current health status and deployment metadata.
     */
    function getContractStatus()
        external
        view
        returns (
            string memory currentStatus,
            uint256 deployedAt,
            address contractOwner
        )
    {
        return (status, deploymentTimestamp, owner);
    }

    /**
     * @notice Updates the health status string.
     */
    function updateStatus(string memory newStatus) external {
        require(msg.sender == owner, "Only owner can update status");
        string memory oldStatus = status;
        status = newStatus;
        emit StatusUpdated(oldStatus, newStatus, msg.sender);
    }
}
