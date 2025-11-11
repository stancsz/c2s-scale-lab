# example.py - minimal reproducible example for c2s-scale
# Usage:
#   python example.py
# The script will:
#  - try to import the c2s_scale package and use a typical Client/run pattern
#  - if not installed, attempt to run the `c2s-scale --help` CLI if present on PATH
import subprocess
import sys

def main():
    try:
        import c2s_scale
    except Exception:
        print("c2s-scale not installed in this environment.")
        print("Install with: pip install c2s-scale")
        print("Attempting to run 'c2s-scale --help' from PATH...")
        try:
            subprocess.run(["c2s-scale", "--help"], check=False)
        except FileNotFoundError:
            print("c2s-scale CLI not found on PATH. Exiting.")
        return

    # Best-effort example using a common API shape. Adjust to real API as needed.
    try:
        Client = getattr(c2s_scale, "Client", None)
        if Client is None:
            print("c2s_scale module imported but no Client class detected.")
            print("Available attributes:", [a for a in dir(c2s_scale) if not a.startswith('_')][:50])
            return

        client = Client()
        if hasattr(client, "run"):
            print("Calling client.run('example-config.yaml') as a demo...")
            try:
                result = client.run("example-config.yaml")
                print("Run result:", result)
            except Exception as e:
                print("client.run raised an exception:", e)
        else:
            print("Client exists but has no run() method. Inspect client:", dir(client))
    except Exception as e:
        print("Unexpected error while using c2s-scale:", e)

if __name__ == "__main__":
    main()
