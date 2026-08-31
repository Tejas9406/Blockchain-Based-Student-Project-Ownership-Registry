import { ethers } from "hardhat";

async function main() {
  console.log("Starting HealthCheck contract deployment on local network...");

  const [deployer] = await ethers.getSigners();
  console.log("Deploying contract with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  const HealthCheckFactory = await ethers.getContractFactory("HealthCheck");
  const healthCheck = await HealthCheckFactory.deploy("Blockchain Environment Healthy (Local Node)");

  await healthCheck.waitForDeployment();
  const contractAddress = await healthCheck.getAddress();

  console.log("HealthCheck contract successfully deployed to:", contractAddress);
  const [status, deployedAt, owner] = await healthCheck.getContractStatus();
  console.log("Contract State -> Status:", status, "| Timestamp:", deployedAt.toString(), "| Owner:", owner);
}

main().catch((error) => {
  console.error("Deployment failed:", error);
  process.exitCode = 1;
});
