# Ethereum — a minimal primer

Ethereum, proposed by Vitalik Buterin in 2013 and launched in July 2015,
is a general-purpose blockchain. Where Bitcoin's scripting language is
intentionally limited, Ethereum's **Ethereum Virtual Machine (EVM)** is
Turing-complete: anyone can deploy programs (called **smart contracts**)
that run deterministically on every node.

## Accounts vs. UTXOs

Unlike Bitcoin, Ethereum uses an **account model**:
- **Externally Owned Account (EOA)**: controlled by a private key. Has an
  ETH balance and a nonce.
- **Contract account**: controlled by code. Has a balance, code, and
  storage.

This is why `eth_getBalance(address)` returns a single number — no UTXO
set to sum up.

## Consensus

- 2015-2022: Proof-of-Work (same family as Bitcoin, different hash).
- September 2022: **The Merge** — Ethereum switched to **Proof-of-Stake**.
  Validators stake 32 ETH each and are randomly selected to propose and
  attest to blocks. Dishonest validators get **slashed** (lose stake).
- Slots are 12s; an epoch is 32 slots (~6.4 min). Finality arrives ~2
  epochs later, so practical finality is ~12-15 minutes.

## Gas

Every EVM operation has a gas cost. A transaction specifies a
`maxFeePerGas` and `maxPriorityFeePerGas` (post-EIP-1559). The base fee is
burned; the priority tip goes to the validator. This is why ETH can be
*deflationary* during heavy use.

## Layer 2s

Ethereum L1 settles only a few dozen tx/s. To scale, most activity has
moved to **rollups**:
- **Optimistic rollups** (Optimism, Arbitrum, Base): assume transactions
  are valid; anyone can post a fraud proof within a challenge window.
- **ZK rollups** (zkSync, Starknet, Linea, Scroll): post a cryptographic
  validity proof with every batch. Faster finality, more compute to
  generate the proof.

## Key ecosystem concepts

- **ERC-20**: fungible token standard (USDC, DAI, LINK, UNI).
- **ERC-721**: NFT standard (CryptoPunks, BAYC).
- **DeFi**: on-chain finance. Core primitives: AMMs (Uniswap),
  money markets (Aave, Compound), stablecoins (DAI, USDC), derivatives.
- **Vitalik's public address**: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`.
- **ETH ticker on CoinGecko**: `ethereum`.
