import { ethers } from "hardhat";

async function main() {
  console.log("================================================================");
  console.log("ProjectRegistry Contract Deployment");
  console.log("================================================================");

  const signers = await ethers.getSigners();
  const deployer = signers[0];
  const network = await ethers.provider.getNetwork();

  console.log("Network Name:", network.name);
  console.log("Chain ID:", network.chainId.toString());
  console.log("Deployer Account (Initial Owner):", deployer.address);

  const deployerBalance = await ethers.provider.getBalance(deployer.address);
  console.log("Deployer Balance:", ethers.formatEther(deployerBalance), "ETH");

  // Determine authorized relayer address
  // Use RELAYER_ADDRESS env variable if provided, or default to signers[1] for local dev
  let relayerAddress = process.env.RELAYER_ADDRESS;
  if (!relayerAddress) {
    if (signers.length > 1) {
      relayerAddress = signers[1].address;
      console.log("Notice: RELAYER_ADDRESS env unset. Using local account[1]:", relayerAddress);
    } else {
      relayerAddress = deployer.address;
      console.log("Notice: Single signer available. Using deployer as relayer:", relayerAddress);
    }
  } else {
    console.log("Configured Relayer Address:", relayerAddress);
  }

  // Deploy ProjectRegistry
  const ProjectRegistryFactory = await ethers.getContractFactory("ProjectRegistry");
  const projectRegistry = await ProjectRegistryFactory.deploy(
    deployer.address,
    relayerAddress
  );

  await projectRegistry.waitForDeployment();
  const contractAddress = await projectRegistry.getAddress();

  console.log("----------------------------------------------------------------");
  console.log("ProjectRegistry Contract successfully deployed!");
  console.log("Contract Address:", contractAddress);
  console.log("Owner Address:", await projectRegistry.owner());
  console.log("Relayer Address:", await projectRegistry.relayer());
  console.log("Total Records Anchored:", (await projectRegistry.totalRecords()).toString());
  console.log("================================================================");
}

main().catch((error) => {
  console.error("Deployment failed with error:", error);
  process.exitCode = 1;
});
