import argparse


def main():
    parser = argparse.ArgumentParser(description="Run Papertrail locally")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run("paper_agent.app:create_app", factory=True, host="127.0.0.1", port=args.port)
