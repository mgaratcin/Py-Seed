from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from concurrent.futures import ProcessPoolExecutor
from typing import List
import threading
import time
import itertools

# Global counter to keep track of addresses checked
address_counter = 0
counter_lock = threading.Lock()

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


def worker_dynamic_search(seed_words: List[str], target_address: str, permutations_queue):
    """Worker function that pulls from a queue and checks for the target address."""
    global address_counter
    while True:
        try:
            # Get the next permutation from the queue
            permutation = next(permutations_queue)
        except StopIteration:
            # No more permutations, stop the worker
            return None

        mnemonic = " ".join(permutation)

        # Validate the mnemonic before attempting to generate an address
        if not is_valid_mnemonic(mnemonic):
            continue  # Skip invalid mnemonics

        generated_address = generate_btc_address_from_mnemonic(mnemonic)

        # Update the global counter for addresses checked
        with counter_lock:
            address_counter += 1

        if generated_address == target_address:
            return mnemonic, generated_address


def print_address_counter():
    """Thread function to print the address counter every 10 seconds."""
    while True:
        time.sleep(10)
        with counter_lock:
            print(f"Addresses checked: {address_counter}")


def find_btc_address(seed_words: List[str], target_address: str, max_workers=256):
    """Main function to find the target BTC address using multiprocessing."""
    # Start the address counter thread
    counter_thread = threading.Thread(target=print_address_counter, daemon=True)
    counter_thread.start()

    # Create an iterator for all permutations of the seed words
    permutations_iterator = iter(itertools.permutations(seed_words))

    # Create a process pool to manage permutation search
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_dynamic_search, seed_words, target_address, permutations_iterator) for _ in range(max_workers)]

        # Wait for tasks to complete
        for future in futures:
            result = future.result()
            if result:
                mnemonic, address = result
                print(f"Found matching mnemonic: {mnemonic}")
                print(f"Matching address: {address}")
                return

    print("No matching address found.")


# Example usage
seed_words = ["dentist", "injury", "ability", "amount", "december", "opinion", "bag", "cigar", "screen", "december", "trim", "heavy"]
target_address = "12tabzW1X7hHggJPm6xxQ6cmBtEmirPt26"

find_btc_address(seed_words, target_address, max_workers=256)
