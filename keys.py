from bip_utils import Bip39MnemonicValidator, Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List


def generate_btc_address_from_mnemonic(mnemonic: str) -> str:
    """Generate a Bitcoin P2PKH address from a mnemonic seed phrase."""
    # Generate seed from mnemonic
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    # Create a Bip44 object for Bitcoin
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    
    # Generate the first Bitcoin P2PKH address
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    return bip44_acc.PublicKey().ToAddress()


def is_valid_mnemonic(mnemonic: str) -> bool:
    """Check if the mnemonic is valid by BIP39 standards."""
    try:
        Bip39MnemonicValidator().Validate(mnemonic)
        return True
    except:
        return False


def worker_permutation_search(seed_words: List[str], target_address: str, permutations):
    """Thread worker function to search through a chunk of permutations."""
    for permutation in permutations:
        mnemonic = " ".join(permutation)
        
        # Validate the mnemonic before attempting to generate an address
        if not is_valid_mnemonic(mnemonic):
            continue  # Skip invalid mnemonics
        
        generated_address = generate_btc_address_from_mnemonic(mnemonic)
        
        if generated_address == target_address:
            return mnemonic, generated_address
    return None


def find_btc_address(seed_words: List[str], target_address: str, max_workers=200):
    """Main function to find the target BTC address using multithreading."""
    # Get all permutations of the seed words
    permutations = list(itertools.permutations(seed_words))
    
    # Divide the permutations into chunks for each thread
    chunk_size = len(permutations) // max_workers
    chunks = [permutations[i:i + chunk_size] for i in range(0, len(permutations), chunk_size)]

    # Create a thread pool to manage permutation search
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Generate tasks for each chunk of permutations
        futures = [executor.submit(worker_permutation_search, seed_words, target_address, chunk) for chunk in chunks]
        
        # Wait for tasks to complete
        for future in as_completed(futures):
            result = future.result()
            if result:
                mnemonic, address = result
                print(f"Found matching mnemonic: {mnemonic}")
                print(f"Matching address: {address}")
                return
    print("No matching address found.")


# Example usage
seed_words = ["dentist", "injury", "amount", "ability", "december", "opinion", "bag", "cigar", "screen", "december", "trim", "heavy"]
target_address = "12tabzW1X7hHggJPm6xxQ6cmBtEmirPt26"

find_btc_address(seed_words, target_address, max_workers=200)
