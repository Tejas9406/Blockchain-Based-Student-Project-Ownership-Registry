import { expect } from "chai";
import { ethers } from "hardhat";
import { ProjectRegistry } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("ProjectRegistry Smart Contract", function () {
  // Common test fixture data
  const SAMPLE_REG_ID = "REG-2026-A8F92";
  const SAMPLE_COMPOSITE_HASH = "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
  const SAMPLE_IPFS_ROOT_CID = "bafybeirootdirectorydagcidabcdefghijklmnopqrstuvwxyz234567";
  const SAMPLE_VERSION_INDEX = 1;
  const SAMPLE_STAGE = 0; // LifecycleStage.IDEA

  let owner: SignerWithAddress;
  let relayer: SignerWithAddress;
  let studentAuthor: SignerWithAddress;
  let contributor1: SignerWithAddress;
  let contributor2: SignerWithAddress;
  let claimant: SignerWithAddress;
  let unauthorizedAccount: SignerWithAddress;
  let newRelayer: SignerWithAddress;
  let newOwner: SignerWithAddress;

  async function deployProjectRegistryFixture() {
    const signers = await ethers.getSigners();
    owner = signers[0];
    relayer = signers[1];
    studentAuthor = signers[2];
    contributor1 = signers[3];
    contributor2 = signers[4];
    claimant = signers[5];
    unauthorizedAccount = signers[6];
    newRelayer = signers[7];
    newOwner = signers[8];

    const Factory = await ethers.getContractFactory("ProjectRegistry");
    const registry = await Factory.deploy(owner.address, relayer.address);
    await registry.waitForDeployment();

    return { registry };
  }

  // ===========================================================================
  // 1. DEPLOYMENT & INITIAL STATE
  // ===========================================================================
  describe("Deployment & Initialization", function () {
    it("1. should deploy successfully", async function () {
      const { registry } = await deployProjectRegistryFixture();
      expect(await registry.getAddress()).to.properAddress;
    });

    it("2. should record the correct owner via Ownable2Step", async function () {
      const { registry } = await deployProjectRegistryFixture();
      expect(await registry.owner()).to.equal(owner.address);
    });

    it("3. should record the correct initial relayer address", async function () {
      const { registry } = await deployProjectRegistryFixture();
      expect(await registry.relayer()).to.equal(relayer.address);
    });

    it("should reject deployment if initial relayer is address(0)", async function () {
      const Factory = await ethers.getContractFactory("ProjectRegistry");
      await expect(
        Factory.deploy(owner.address, ethers.ZeroAddress)
      ).to.be.revertedWithCustomError(Factory, "InvalidRelayerAddress");
    });
  });

  // ===========================================================================
  // 2. REGISTRATION AUTHORIZATION & VALIDATION
  // ===========================================================================
  describe("Registration Authorization & Validation", function () {
    it("4. should allow owner to register a project version", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(owner).registerProjectVersion(
          SAMPLE_REG_ID,
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          SAMPLE_VERSION_INDEX,
          SAMPLE_STAGE,
          studentAuthor.address,
          [contributor1.address, contributor2.address]
        )
      ).to.emit(registry, "ProjectVersionRegistered");
    });

    it("5. should allow authorized relayer to register a project version", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(relayer).registerProjectVersion(
          "REG-2026-REL01",
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          [contributor1.address]
        )
      ).to.emit(registry, "ProjectVersionRegistered");
    });

    it("6. should reject registration attempt by unauthorized account", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(unauthorizedAccount).registerProjectVersion(
          "REG-2026-UNAUTH",
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "UnauthorizedRelayer")
        .withArgs(unauthorizedAccount.address);
    });

    it("7. should reject registration if registrationId is empty string", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(relayer).registerProjectVersion(
          "",
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "EmptyRegistrationId");
    });

    it("8. should reject duplicate registration of identical registrationId", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      await expect(
        registry.connect(relayer).registerProjectVersion(
          SAMPLE_REG_ID,
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          2,
          1,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "RegistrationIdAlreadyExists")
        .withArgs(SAMPLE_REG_ID);
    });

    it("9. should reject registration if compositeHash is bytes32(0)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(relayer).registerProjectVersion(
          "REG-2026-ZEROHASH",
          ethers.ZeroHash,
          SAMPLE_IPFS_ROOT_CID,
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "ZeroCompositeHash");
    });

    it("10. should reject registration if ipfsRootCID is empty string", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(relayer).registerProjectVersion(
          "REG-2026-EMPTYCID",
          SAMPLE_COMPOSITE_HASH,
          "",
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "EmptyIpfsRootCID");
    });

    it("11. should reject registration if versionIndex is 0", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(relayer).registerProjectVersion(
          "REG-2026-VERZERO",
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          0,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "InvalidVersionIndex");
    });

    it("12. should increment record IDs sequentially", async function () {
      const { registry } = await deployProjectRegistryFixture();

      const tx1 = await registry.connect(relayer).registerProjectVersion(
        "REG-2026-SEQ01",
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        0,
        studentAuthor.address,
        []
      );
      await tx1.wait();

      const tx2 = await registry.connect(relayer).registerProjectVersion(
        "REG-2026-SEQ02",
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        2,
        1,
        studentAuthor.address,
        []
      );
      await tx2.wait();

      const proof1 = await registry.getProjectVersion("REG-2026-SEQ01");
      const proof2 = await registry.getProjectVersion("REG-2026-SEQ02");

      expect(proof1.recordId).to.equal(1);
      expect(proof2.recordId).to.equal(2);
      expect(await registry.totalRecords()).to.equal(2);
    });

    it("13. should store all VersionProof fields accurately and immutably", async function () {
      const { registry } = await deployProjectRegistryFixture();
      const tx = await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        SAMPLE_VERSION_INDEX,
        SAMPLE_STAGE,
        studentAuthor.address,
        [contributor1.address, contributor2.address]
      );
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      const proof = await registry.getProjectVersion(SAMPLE_REG_ID);

      expect(proof.recordId).to.equal(1);
      expect(proof.registrationId).to.equal(SAMPLE_REG_ID);
      expect(proof.compositeHash).to.equal(SAMPLE_COMPOSITE_HASH);
      expect(proof.ipfsRootCID).to.equal(SAMPLE_IPFS_ROOT_CID);
      expect(proof.versionIndex).to.equal(SAMPLE_VERSION_INDEX);
      expect(proof.lifecycleStage).to.equal(SAMPLE_STAGE);
      expect(proof.author).to.equal(studentAuthor.address);
      expect(proof.coAuthors).to.deep.equal([contributor1.address, contributor2.address]);
      expect(proof.anchoredTimestamp).to.equal(block!.timestamp);
      expect(proof.blockNumber).to.equal(receipt!.blockNumber);
      expect(proof.exists).to.be.true;
    });

    it("14. should initialize disputeState as DisputeStatus.NONE (0)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      const proof = await registry.getProjectVersion(SAMPLE_REG_ID);
      expect(proof.disputeState).to.equal(0); // DisputeStatus.NONE
    });

    it("15. should emit ProjectVersionRegistered event with exact canonical parameters", async function () {
      const { registry } = await deployProjectRegistryFixture();
      const tx = await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        [contributor1.address]
      );
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      await expect(tx)
        .to.emit(registry, "ProjectVersionRegistered")
        .withArgs(
          1, // recordId
          SAMPLE_REG_ID,
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          1, // versionIndex
          SAMPLE_STAGE,
          studentAuthor.address,
          relayer.address, // relayer (msg.sender)
          block!.timestamp
        );
    });

    it("16. should correctly maintain reverse lookup by recordId", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      expect(await registry.getRegistrationIdByRecordId(1)).to.equal(SAMPLE_REG_ID);
    });
  });

  // ===========================================================================
  // 3. TRUSTLESS VERIFICATION ENDPOINT
  // ===========================================================================
  describe("Trustless Verification Endpoint", function () {
    it("17. should return isValid = true when registration exists and hash matches", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      const [isValid, timestamp, cid, author, disputeState] =
        await registry.verifyProjectVersion(SAMPLE_REG_ID, SAMPLE_COMPOSITE_HASH);

      expect(isValid).to.be.true;
      expect(timestamp).to.be.gt(0);
      expect(cid).to.equal(SAMPLE_IPFS_ROOT_CID);
      expect(author).to.equal(studentAuthor.address);
      expect(disputeState).to.equal(0);
    });

    it("18. should return isValid = false without reverting when hash does not match", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      const wrongHash = "0x1111111111111111111111111111111111111111111111111111111111111111";
      const [isValid, timestamp, cid, author, disputeState] =
        await registry.verifyProjectVersion(SAMPLE_REG_ID, wrongHash);

      expect(isValid).to.be.false;
      expect(timestamp).to.be.gt(0);
      expect(cid).to.equal(SAMPLE_IPFS_ROOT_CID);
      expect(author).to.equal(studentAuthor.address);
      expect(disputeState).to.equal(0);
    });

    it("19. should return isValid = false with zero/empty values for non-existent registration", async function () {
      const { registry } = await deployProjectRegistryFixture();
      const [isValid, timestamp, cid, author, disputeState] =
        await registry.verifyProjectVersion("REG-2026-NONEXISTENT", SAMPLE_COMPOSITE_HASH);

      expect(isValid).to.be.false;
      expect(timestamp).to.equal(0);
      expect(cid).to.equal("");
      expect(author).to.equal(ethers.ZeroAddress);
      expect(disputeState).to.equal(0);
    });

    it("20. should verify without mutating contract state (pure view)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      const totalBefore = await registry.totalRecords();
      await registry.verifyProjectVersion(SAMPLE_REG_ID, SAMPLE_COMPOSITE_HASH);
      const totalAfter = await registry.totalRecords();

      expect(totalBefore).to.equal(totalAfter);
    });

    it("21. should return active dispute state accurately during verification", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, "bafybeievidencecid");

      const [, , , , disputeState] =
        await registry.verifyProjectVersion(SAMPLE_REG_ID, SAMPLE_COMPOSITE_HASH);

      expect(disputeState).to.equal(1); // DisputeStatus.OPEN
    });
  });

  // ===========================================================================
  // 4. GET PROJECT VERSION
  // ===========================================================================
  describe("Get Project Version", function () {
    it("22. should return complete VersionProof struct for valid registrationId", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        [contributor1.address]
      );

      const proof = await registry.getProjectVersion(SAMPLE_REG_ID);
      expect(proof.registrationId).to.equal(SAMPLE_REG_ID);
      expect(proof.compositeHash).to.equal(SAMPLE_COMPOSITE_HASH);
      expect(proof.author).to.equal(studentAuthor.address);
      expect(proof.exists).to.be.true;
    });

    it("23. should revert with VersionNotFound when queried with missing registrationId", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.getProjectVersion("REG-2026-MISSING")
      ).to.be.revertedWithCustomError(registry, "VersionNotFound")
        .withArgs("REG-2026-MISSING");
    });
  });

  // ===========================================================================
  // 5. DISPUTES & ADJUDICATION
  // ===========================================================================
  describe("Disputes & Adjudication Lifecycle", function () {
    const EVIDENCE_CID = "bafybeievidencecidforpriorartcheck1234567890abcdefghijklmn";

    it("24. should allow valid claimant to raise a dispute", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      await expect(
        registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID)
      ).to.emit(registry, "DisputeLogged");
    });

    it("25. should reject raising dispute on non-existent registrationId", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(claimant).raiseDispute("REG-2026-NONEXISTENT", EVIDENCE_CID)
      ).to.be.revertedWithCustomError(registry, "VersionNotFound");
    });

    it("26. should reject raising dispute with empty evidence CID", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      await expect(
        registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, "")
      ).to.be.revertedWithCustomError(registry, "EmptyDisputeEvidence");
    });

    it("27. should transition disputeState from NONE (0) to OPEN (1)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);
      const proof = await registry.getProjectVersion(SAMPLE_REG_ID);
      expect(proof.disputeState).to.equal(1); // DisputeStatus.OPEN
    });

    it("28. should emit DisputeLogged with exact claimant and evidence values", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      const tx = await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      await expect(tx)
        .to.emit(registry, "DisputeLogged")
        .withArgs(
          SAMPLE_REG_ID,
          claimant.address,
          EVIDENCE_CID,
          block!.timestamp
        );
    });

    it("29. should prevent raising a new dispute while one is already active (OPEN)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );

      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);

      await expect(
        registry.connect(unauthorizedAccount).raiseDispute(SAMPLE_REG_ID, "bafybeiotherproof")
      ).to.be.revertedWithCustomError(registry, "ActiveDisputeExists")
        .withArgs(SAMPLE_REG_ID, 1);
    });

    it("30. should allow owner to resolve dispute as RESOLVED (3)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );
      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);

      await registry.connect(owner).resolveDispute(SAMPLE_REG_ID, 3); // DisputeStatus.RESOLVED

      const proof = await registry.getProjectVersion(SAMPLE_REG_ID);
      expect(proof.disputeState).to.equal(3);
    });

    it("31. should allow owner to resolve dispute as REJECTED (4)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );
      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);

      await registry.connect(owner).resolveDispute(SAMPLE_REG_ID, 4); // DisputeStatus.REJECTED

      const proof = await registry.getProjectVersion(SAMPLE_REG_ID);
      expect(proof.disputeState).to.equal(4);
    });

    it("32. should reject dispute resolution by non-owner account", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );
      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);

      await expect(
        registry.connect(unauthorizedAccount).resolveDispute(SAMPLE_REG_ID, 3)
      ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
        .withArgs(unauthorizedAccount.address);
    });

    it("33. should reject invalid resolution target status (NONE, OPEN, UNDER_REVIEW)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );
      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);

      for (const invalidStatus of [0, 1, 2]) {
        await expect(
          registry.connect(owner).resolveDispute(SAMPLE_REG_ID, invalidStatus)
        ).to.be.revertedWithCustomError(registry, "InvalidDisputeResolutionStatus")
          .withArgs(invalidStatus);
      }
    });

    it("34. should emit DisputeResolved event with exact metadata", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        []
      );
      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);

      const tx = await registry.connect(owner).resolveDispute(SAMPLE_REG_ID, 3);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      await expect(tx)
        .to.emit(registry, "DisputeResolved")
        .withArgs(
          SAMPLE_REG_ID,
          3, // DisputeStatus.RESOLVED
          owner.address,
          block!.timestamp
        );
    });

    it("35. should leave cryptographic proof content completely unchanged after dispute resolution", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(relayer).registerProjectVersion(
        SAMPLE_REG_ID,
        SAMPLE_COMPOSITE_HASH,
        SAMPLE_IPFS_ROOT_CID,
        1,
        SAMPLE_STAGE,
        studentAuthor.address,
        [contributor1.address]
      );
      const proofBefore = await registry.getProjectVersion(SAMPLE_REG_ID);

      await registry.connect(claimant).raiseDispute(SAMPLE_REG_ID, EVIDENCE_CID);
      await registry.connect(owner).resolveDispute(SAMPLE_REG_ID, 3);

      const proofAfter = await registry.getProjectVersion(SAMPLE_REG_ID);

      expect(proofAfter.compositeHash).to.equal(proofBefore.compositeHash);
      expect(proofAfter.ipfsRootCID).to.equal(proofBefore.ipfsRootCID);
      expect(proofAfter.anchoredTimestamp).to.equal(proofBefore.anchoredTimestamp);
      expect(proofAfter.blockNumber).to.equal(proofBefore.blockNumber);
      expect(proofAfter.author).to.equal(proofBefore.author);
      expect(proofAfter.coAuthors).to.deep.equal(proofBefore.coAuthors);
      expect(proofAfter.disputeState).to.equal(3);
    });
  });

  // ===========================================================================
  // 6. RELAYER ADMINISTRATION
  // ===========================================================================
  describe("Relayer Administration", function () {
    it("36. should allow owner to change relayer address", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(registry.connect(owner).setRelayer(newRelayer.address))
        .to.emit(registry, "RelayerUpdated")
        .withArgs(relayer.address, newRelayer.address);

      expect(await registry.relayer()).to.equal(newRelayer.address);
    });

    it("37. should reject relayer update from non-owner account", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(unauthorizedAccount).setRelayer(newRelayer.address)
      ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
        .withArgs(unauthorizedAccount.address);
    });

    it("38. should reject setting relayer to address(0)", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await expect(
        registry.connect(owner).setRelayer(ethers.ZeroAddress)
      ).to.be.revertedWithCustomError(registry, "InvalidRelayerAddress");
    });

    it("39. should allow newly configured relayer to register project versions", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(owner).setRelayer(newRelayer.address);

      await expect(
        registry.connect(newRelayer).registerProjectVersion(
          SAMPLE_REG_ID,
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.emit(registry, "ProjectVersionRegistered");
    });

    it("40. should prevent replaced old relayer from registering project versions", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(owner).setRelayer(newRelayer.address);

      await expect(
        registry.connect(relayer).registerProjectVersion(
          SAMPLE_REG_ID,
          SAMPLE_COMPOSITE_HASH,
          SAMPLE_IPFS_ROOT_CID,
          1,
          SAMPLE_STAGE,
          studentAuthor.address,
          []
        )
      ).to.be.revertedWithCustomError(registry, "UnauthorizedRelayer")
        .withArgs(relayer.address);
    });
  });

  // ===========================================================================
  // 7. OWNABLE2STEP OWNERSHIP BEHAVIOR
  // ===========================================================================
  describe("Ownable2Step Two-Step Ownership", function () {
    it("41. should require two-step acceptance before ownership is transferred", async function () {
      const { registry } = await deployProjectRegistryFixture();

      // Step 1: Owner initiates transfer
      await registry.connect(owner).transferOwnership(newOwner.address);
      expect(await registry.owner()).to.equal(owner.address);
      expect(await registry.pendingOwner()).to.equal(newOwner.address);

      // Step 2: New owner accepts transfer
      await registry.connect(newOwner).acceptOwnership();
      expect(await registry.owner()).to.equal(newOwner.address);
      expect(await registry.pendingOwner()).to.equal(ethers.ZeroAddress);
    });

    it("42. should prevent non-pending owner from accepting ownership or bypassing authorization", async function () {
      const { registry } = await deployProjectRegistryFixture();
      await registry.connect(owner).transferOwnership(newOwner.address);

      await expect(
        registry.connect(unauthorizedAccount).acceptOwnership()
      ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
        .withArgs(unauthorizedAccount.address);
    });
  });
});
