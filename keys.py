from bip_utils import Bip39MnemonicValidator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from concurrent.futures import ProcessPoolExecutor
from itertools import permutations, islice
import multiprocessing
import threading
import time


# Global counter to keep track of addresses checked
address_counter = multiprocessing.Value('i', 0)

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


def worker_dynamic_search(seed_words: list, target_address: str, batch_size: int):
    """Worker function to generate and check BTC addresses in batches."""
    global address_counter
    valid_mnemonics = []
    
    # Get all permutations of the seed words
    perm_iterator = permutations(seed_words)

    while True:
        # Process a batch of permutations at once to reduce overhead
        batch = list(islice(perm_iterator, batch_size))
        if not batch:
            return None

        for perm in batch:
            mnemonic = " ".join(perm)
            if is_valid_mnemonic(mnemonic):
                generated_address = generate_btc_address_from_mnemonic(mnemonic)

                # Update the global counter atomically
                with address_counter.get_lock():
                    address_counter.value += 1

                if generated_address == target_address:
                    return mnemonic, generated_address
    return None


def print_address_counter():
    """Thread function to print the address counter every 10 seconds."""
    while True:
        time.sleep(10)
        print(f"Addresses checked: {address_counter.value}")


def find_btc_address(seed_words: list, target_address: str, max_workers=64, batch_size=1000):
    """Main function to find the target BTC address using multiprocessing."""
    # Start the address counter thread
    counter_thread = threading.Thread(target=print_address_counter, daemon=True)
    counter_thread.start()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_dynamic_search, seed_words, target_address, batch_size) for _ in range(max_workers)]

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
seed_words = ["coffee", "order", "black", "bridge", "battle", "liberty", "shadow", "anger", "secret", "pyramid", "network", "market"]
target_address = "1KfZGvwZxsvSmemoCmEV75uqcNzYBHjkHZ"

# Increasing batch size can improve performance by reducing overhead
find_btc_address(seed_words, target_address, max_workers=64, batch_size=1000)
