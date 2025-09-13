"""
Blockchain validation utilities for wallet connections
"""

import re

import requests
from mnemonic import Mnemonic
from eth_account import Account
from web3 import Web3
from hdwallet import HDWallet


class BlockchainValidator:
    def __init__(self):
        # Multiple RPC endpoints for redundancy
        self.rpc_endpoints = [
            "https://cloudflare-eth.com",
            "https://rpc.ankr.com/eth",
            "https://eth-mainnet.public.blastapi.io",
        ]
        self.web3 = None
        self.connect_to_blockchain()

    def connect_to_blockchain(self):
        """Connect to Ethereum blockchain using available RPC endpoints"""
        for endpoint in self.rpc_endpoints:
            try:
                w3 = Web3(Web3.HTTPProvider(endpoint))
                if w3.is_connected():
                    self.web3 = w3
                    print(f"Connected to blockchain via {endpoint}")
                    return True
            except Exception as e:
                print(f"Failed to connect to {endpoint}: {e}")
                continue
        return False

    def validate_private_key(self, private_key):
        """Validate private key format and derive address"""
        try:
            # Remove 0x prefix if present
            if private_key.startswith("0x"):
                private_key = private_key[2:]

            # Check if it's 64 hex characters
            if not re.match(r"^[0-9a-fA-F]{64}$", private_key):
                return {"valid": False, "error": "Invalid private key format"}

            # Derive account from private key
            account = Account.from_key("0x" + private_key)
            address = account.address

            # Get balance
            balance = self.get_balance(address)

            return {
                "valid": True,
                "address": address,
                "balance_wei": balance,
                "balance_eth": Web3.from_wei(balance, "ether"),
                "balance_usd": self.get_eth_price()
                * float(Web3.from_wei(balance, "ether")),
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def validate_mnemonic(self, mnemonic):
        """Validate BIP39 mnemonic phrase"""
        try:
            # Clean and normalize mnemonic
            words = mnemonic.strip().lower().split()

            # Check word count (12, 15, 18, 21, or 24 words)
            if len(words) not in [12, 15, 18, 21, 24]:
                return {"valid": False, "error": "Invalid mnemonic length"}

            # Validate mnemonic using mnemonic
            mnemo = Mnemonic("english")
            if not mnemo.check(" ".join(words)):
                return {"valid": False, "error": "Invalid mnemonic phrase"}

            # Derive first account from mnemonic using BIP44 path m/44'/60'/0'/0/0
            
            hdwallet = HDWallet(symbol="ethereum")
            hdwallet.from_mnemonic(mnemonic=" ".join(words))
            private_key = hdwallet.private_key
            account = Account.from_key(private_key)
            address = account.address

            # Get balance
            balance = self.get_balance(address)

            return {
                "valid": True,
                "address": address,
                "mnemonic": " ".join(words),
                "balance_wei": balance,
                "balance_eth": Web3.from_wei(balance, "ether"),
                "balance_usd": self.get_eth_price()
                * float(Web3.from_wei(balance, "ether")),
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def get_balance(self, address):
        """Get ETH balance for an address"""
        try:
            if not self.web3:
                return 0

            balance = self.web3.eth.get_balance(address)
            return balance
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0

    def get_eth_price(self):
        """Get current ETH price in USD"""
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
                timeout=5,
            )
            data = response.json()
            return data["ethereum"]["usd"]
        except (requests.RequestException, KeyError, ValueError):
            return 3000  # Fallback price

    def validate_wallet_address(self, address):
        """Validate Ethereum wallet address"""
        try:
            if not Web3.is_address(address):
                return {"valid": False, "error": "Invalid address format"}

            # Get balance
            balance = self.get_balance(address)

            return {
                "valid": True,
                "address": Web3.to_checksum_address(address),
                "balance_wei": balance,
                "balance_eth": Web3.from_wei(balance, "ether"),
                "balance_usd": self.get_eth_price()
                * float(Web3.from_wei(balance, "ether")),
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}
