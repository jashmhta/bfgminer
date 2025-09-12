#!/usr/bin/env python3
"""
Flask wrapper for BFGMiner Node.js application.
This serves as a deployment wrapper to make the app compatible with Flask deployment.
"""

import os
import signal
import subprocess
import time

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)


# Global variable to store the Node.js process
node_process = None


def start_node_server():
    """Start the Node.js server in the background"""
    global node_process
    try:
        # Change to the app directory
        os.chdir("/home/ubuntu/bfgminer-app")

        # Start the Node.js server
        node_process = subprocess.Popen(
            ["node", "server.js"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        print(f"Node.js server started with PID: {node_process.pid}")

        # Wait a moment for the server to start
        time.sleep(2)

        return True
    except (ProcessLookupError, OSError) as e:
        print(f"Failed to start Node.js server: {e}")
        return False


def stop_node_server():
    """Stop the Node.js server"""
    global node_process
    if node_process:
        try:
            # Kill the process group to ensure all child processes are terminated
            os.killpg(os.getpgid(node_process.pid), signal.SIGTERM)
            node_process.wait(timeout=5)
        except (ProcessLookupError, OSError) as e:
            print(f"Error stopping Node.js server: {e}")
            try:
                os.killpg(os.getpgid(node_process.pid), signal.SIGKILL)
            except:
                pass
        finally:
            node_process = None


# Start Node.js server when Flask app starts


def init_app():
    """Initialize the application"""
    if start_node_server():
        print("BFGMiner application initialized successfully")
    else:
        print("Failed to initialize BFGMiner application")


# Routes
@app.route("/")
def index():
    """Serve the main application"""
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(".", filename)


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "BFGMiner Web Application",
            "node_server": (
                "running" if node_process and node_process.poll() is None else "stopped"
            ),
        }
    )


# Cleanup on shutdown
import atexit

atexit.register(stop_node_server)

if __name__ == "__main__":
    # Initialize the app
    init_app()

    # Run Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
