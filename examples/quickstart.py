"""Minimal quickstart: create a session, poll until ready, stop it."""

from sprntrl import Sprntrl


def main() -> None:
    with Sprntrl() as client:
        session = client.sessions.create(os="macos", location="us-east")
        print(f"created {session['id']} (status={session['status']})")

        session = client.sessions.wait_until_ready(session["id"])
        print(f"ready: cdp_url={session['cdp_url']}")

        client.sessions.stop(session["id"])
        print("stopped")


if __name__ == "__main__":
    main()
