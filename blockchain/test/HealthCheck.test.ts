import { expect } from "chai";
import { ethers } from "hardhat";

describe("Blockchain Environment HealthCheck", function () {
  const INITIAL_STATUS = "Blockchain Environment Healthy";

  async function deployHealthCheckFixture() {
    const [owner, otherAccount] = await ethers.getSigners();
    const HealthCheckFactory = await ethers.getContractFactory("HealthCheck");
    const healthCheck = await HealthCheckFactory.deploy(INITIAL_STATUS);
    await healthCheck.waitForDeployment();

    return { healthCheck, owner, otherAccount };
  }

  describe("Deployment & Initialization", function () {
    it("should deploy successfully and record correct owner and initial status", async function () {
      const { healthCheck, owner } = await deployHealthCheckFixture();
      const [status, deployedAt, contractOwner] = await healthCheck.getContractStatus();

      expect(status).to.equal(INITIAL_STATUS);
      expect(contractOwner).to.equal(owner.address);
      expect(deployedAt).to.be.gt(0);
    });
  });

  describe("Diagnostic Functions", function () {
    it("should respond to ping with pong", async function () {
      const { healthCheck } = await deployHealthCheckFixture();
      expect(await healthCheck.ping()).to.equal("pong");
    });

    it("should allow owner to update status and emit StatusUpdated event", async function () {
      const { healthCheck, owner } = await deployHealthCheckFixture();
      const newStatus = "Status Updated Successfully";

      await expect(healthCheck.updateStatus(newStatus))
        .to.emit(healthCheck, "StatusUpdated")
        .withArgs(INITIAL_STATUS, newStatus, owner.address);

      const [status] = await healthCheck.getContractStatus();
      expect(status).to.equal(newStatus);
    });

    it("should reject status update from non-owner account", async function () {
      const { healthCheck, otherAccount } = await deployHealthCheckFixture();
      await expect(
        healthCheck.connect(otherAccount).updateStatus("Unauthorized update")
      ).to.be.revertedWith("Only owner can update status");
    });
  });
});
