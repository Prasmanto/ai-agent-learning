# Bitcoin — a minimal primer

Bitcoin is a peer-to-peer electronic cash system launched in January 2009 by
a pseudonymous author, Satoshi Nakamoto. It introduced the first working
solution to the **double-spend problem** for digital money without relying
on a central authority.

## Core ideas

- **Proof-of-Work (PoW)**: miners compete to find a nonce that makes the
  SHA-256 hash of the current block header fall below a target value. The
  winner appends the next block and earns the *block reward* (newly minted
  BTC) plus transaction fees.
- **Block time**: ~10 minutes on average. Difficulty is retargeted every
  2016 blocks (~two weeks) to keep this steady regardless of total
  hash power.
- **Supply cap**: 21,000,000 BTC. The block reward halves every 210,000
  blocks (~4 years). After halving #4 in April 2024, the subsidy is
  3.125 BTC/block.
- **UTXO model**: a Bitcoin wallet does not hold an "account balance".
  It holds a collection of **Unspent Transaction Outputs**. Sending BTC
  means consuming some UTXOs as inputs and creating new ones as outputs.

## What Bitcoin is *good* at

- Settling large value globally without a custodian.
- Predictable, rules-based monetary policy.
- A censorship-resistant store of value: no one can freeze your coins if
  you hold the private key.

## What Bitcoin is *not* designed for

- Arbitrary programmability. Script is intentionally limited.
- High-throughput retail payments (~7 tx/s on L1). This is what Layer 2s
  such as the **Lightning Network** address.
- Privacy by default. All transactions are public; privacy requires
  techniques like CoinJoin.

## Key addresses / tokens to know

- **Genesis block**: block 0, mined 3 Jan 2009. Famous coinbase message:
  "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks."
- **BTC ticker on CoinGecko**: `bitcoin`.
