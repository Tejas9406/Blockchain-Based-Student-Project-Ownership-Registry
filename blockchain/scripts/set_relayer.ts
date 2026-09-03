/**
 * Reusable Hardhat Administrative Utility: Set Relayer Address
 * 
 * Synchronizes the relayer address on the deployed ProjectRegistry smart contract
 * with the designated deployer/owner account for local development and testing.
 * 
 * Usage: npx hardhat run scripts/set_relayer.ts --network localhost
 */

import { ethers } from "hardhat";

async function main() {
  const [owner] = await ethers.getSigners();
  const contractAddress = process.env.PROJECT_REGISTRY_CONTRACT_ADDRESS || "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const contract = await ethers.getContractAt("ProjectRegistry", contractAddress);
  console.log("Current Owner:", await contract.owner());
  console.log("Current Relayer:", await contract.relayer());
  const tx = await contract.connect(owner).setRelayer(owner.address);
  await tx.wait();
  console.log("Updated Relayer:", await contract.relayer());
}

main().catch(console.error);
