# DeFi / Web3 glossary

A compact cheat-sheet of terms you'll meet everywhere in crypto research.

## Market and trading

- **TVL (Total Value Locked)**: USD value of assets deposited in a
  protocol. Tracked at https://defillama.com.
- **AMM (Automated Market Maker)**: a smart contract that prices assets
  algorithmically from a liquidity pool instead of an order book.
  Uniswap v2 uses `x * y = k`; Uniswap v3 adds *concentrated liquidity*.
- **Slippage**: the price difference between quote and execution, caused
  by the trade's own impact on the pool.
- **Impermanent loss**: the loss an LP suffers when the pool ratio
  changes vs. simply holding the two assets.
- **Stablecoin**: a token designed to track $1. Fiat-backed (USDC, USDT),
  crypto-backed (DAI), or algorithmic (risky; Terra/UST collapsed in
  May 2022).

## Lending

- **Money market**: a pool-based lending protocol (Aave, Compound).
  Depositors earn interest; borrowers must post collateral above the
  borrow value (over-collateralization).
- **Liquidation**: if a borrow position's collateral ratio falls below a
  threshold, a liquidator repays part of the debt and seizes collateral
  at a discount.

## Security and MEV

- **MEV (Maximal Extractable Value)**: profit a block producer can extract
  by reordering, inserting, or censoring transactions in a block.
  Classic examples: sandwich attacks on AMM swaps.
- **Flashbots / MEV-Boost**: off-chain auction where validators sell
  blockspace to searchers/builders.
- **Reentrancy**: a classic smart-contract bug where an external call
  re-enters the contract before state is finalized (the 2016 DAO hack).
  Mitigations: checks-effects-interactions, reentrancy guards.

## Scaling and infrastructure

- **Rollup**: an L2 that batches many transactions into one L1 proof.
  Optimistic (fraud proofs, 7-day withdrawal) vs. ZK (validity proofs,
  fast withdrawal).
- **Data availability (DA)**: guaranteeing that the underlying tx data
  of a rollup is published somewhere verifiable. EIP-4844 (blobs) cut
  L2 fees by ~10x in March 2024.
- **Bridge**: lets assets move between chains. Bridges are historically
  the #1 hack target — prefer canonical L1↔L2 bridges over third-party
  ones when possible.

## Governance and tokenomics

- **Governance token**: grants voting rights over a protocol's parameters
  (UNI, AAVE, COMP).
- **veToken model**: lock a token for N years to get boosted voting
  power and fee share (Curve's `veCRV`, Balancer's `veBAL`).
- **Airdrop**: free distribution of a new token to past users of a
  protocol, often as a launch and decentralization mechanism.

## Wallets and keys

- **Seed phrase (mnemonic)**: 12 or 24 BIP-39 words that deterministically
  derive every private key in your wallet. Whoever has the phrase owns
  the funds. Never type it into a website.
- **Hardware wallet**: device that stores private keys offline (Ledger,
  Trezor) and signs transactions when confirmed on its screen.
- **Multisig**: a contract wallet that requires M of N signers to
  approve a transaction (Safe, formerly Gnosis Safe).
