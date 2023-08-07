from substrateinterface import Keypair
import sys
import multiprocessing
import signal

MAX_THREAD = multiprocessing.cpu_count()
MUTEX = multiprocessing.Lock()

PROCESSES = []


# Input: "Test"
# Return: ["Test", "Tes", "Te", "t"]
def decompose_string(s: str) -> list[str]:
    l = []
    for i in range(len(s)):
        l.append(s[:len(s) - i])
    return l


# Colorize the first occurrence of a substring in a string
def colorize(string: str, substring: str) -> str:
    index = string.find(substring)
    if index == -1:
        return string
    return f"{string[:index]}\033[0;32m{substring}\033[m{string[index + len(substring):]}"


def thread_finder(last_address_found, last_address_sub_len, decomposed_search):
    while True:
        mnemonic = Keypair.generate_mnemonic()
        keypair = Keypair.create_from_mnemonic(mnemonic)
        found = [s for s in decomposed_search if s in keypair.ss58_address]
        with MUTEX:
            if len(found) > 0 and len(found[0]) >= last_address_sub_len.value:
                if last_address_found.value.find(found[0]) == -1 or (
                        keypair.ss58_address.find(found[0]) <= last_address_found.value.find(found[0])):
                    last_address_sub_len.value = len(found[0])
                    print(f"{colorize(keypair.ss58_address, found[0])} {mnemonic}")
                    last_address_found.value = keypair.ss58_address


def main():
    global PROCESSES
    signal.signal(signal.SIGINT, signal_handler)
    if len(sys.argv) < 2:
        print("Please provide the search string as a command-line argument.")
        print("Example:")
        print("\tpython3 main.py \"Some\"")
        return

    search = sys.argv[1]
    decomposed_search = decompose_string(search)

    manager = multiprocessing.Manager()
    last_address_sub_len = manager.Value('i', 0)
    last_address_found = manager.Value('c', '')
    PROCESSES = [multiprocessing.Process(target=thread_finder, args=(last_address_found, last_address_sub_len, decomposed_search,))
               for _ in range(MAX_THREAD)]

    for p in PROCESSES:
        p.start()
        
    for p in PROCESSES:
        p.join()


def signal_handler(sig, frame):
    global PROCESSES
    for p in PROCESSES:
        p.terminate()
    sys.exit(0)


if __name__ == "__main__":
    main()