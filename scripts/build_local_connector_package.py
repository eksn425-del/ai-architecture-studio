"""Build a private local trial bundle from the owner's installed connector.

No credential files, project files, chat panels or public distribution are included.
Unresolved source redistribution rights remain an explicit release gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-dir", type=Path, required=True)
    parser.add_argument("--mcp-server", type=Path, required=True)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--node-license", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Output must be a fresh directory; existing packages are preserved.")
    source_hashes = {}
    ruby = {}
    profile = 'File.join(ENV.fetch("LOCALAPPDATA"), "KStudio", "connectors", "kongxing")'
    for name in ("errors.rb", "state.rb", "geometry_tools.rb", "schema_validator.rb", "bridge.rb"):
        path = args.plugin_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing reviewed connector source: " + name)
        raw = path.read_bytes()
        source_hashes[name] = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8")
        text = text.replace('"C:/ProgramData/archflow-mcp/generated_scripts"', f'File.join({profile}, "generated_scripts")')
        text = text.replace('"C:/ProgramData/archflow-mcp/screenshots"', f'File.join({profile}, "screenshots")')
        ruby["kongxing_ai_sketchup/" + name] = text
    ruby["kongxing_ai_sketchup.rb"] = '''require "sketchup.rb"
require "extensions.rb"
module KongxingAI
  unless file_loaded?(__FILE__)
    extension = SketchupExtension.new("K Studio Connector (Kongxing)", "kongxing_ai_sketchup/main")
    extension.description = "Local K Studio connector trial. Compatibility requires validation."
    extension.version = "0.1.0"
    extension.creator = "K Studio / Kongxing local trial"
    Sketchup.register_extension(extension, true)
    file_loaded(__FILE__)
  end
end
'''
    ruby["kongxing_ai_sketchup/main.rb"] = '''# encoding: UTF-8
require "sketchup.rb"
require "json"
require "fileutils"
require_relative "errors"
require_relative "state"
require_relative "geometry_tools"
require_relative "schema_validator"
require_relative "bridge"
module KongxingAI
  VERSION = "0.1.0-kstudio-local1"
  module Panel
    def self.save_connection_info
      root = File.join(ENV.fetch("LOCALAPPDATA"), "KStudio", "connectors", "kongxing")
      FileUtils.mkdir_p(root)
      path = File.join(root, "connection.json")
      File.write(path, JSON.generate(Bridge.instance.connection_info), :encoding => "UTF-8")
    end
  end
  module Commands
    def self.start_bridge
      Bridge.instance.start
      Panel.save_connection_info
      UI.messagebox("K Studio local bridge started. Return to K Studio and check MCP.")
    rescue StandardError => error
      UI.messagebox("K Studio connector: #{error.message}")
    end
  end
  unless file_loaded?(__FILE__)
    menu = UI.menu("Extensions").add_submenu("Kongxing AI")
    menu.add_item("Start Local Bridge") { Commands.start_bridge }
    menu.add_item("Stop Local Bridge") { Bridge.instance.stop }
    menu.add_item("Save Connection Info") { Panel.save_connection_info }
    begin
      Bridge.instance.start
      Panel.save_connection_info
    rescue StandardError
      # The app must report an unresponsive bridge, never pretend installation is connectivity.
    end
    file_loaded(__FILE__)
  end
end
'''
    server_bytes = args.mcp_server.read_bytes()
    server = server_bytes.decode("utf-8")
    source_hashes["kongxing_sketchup_mcp.mjs"] = hashlib.sha256(server_bytes).hexdigest()
    server = server.replace('path.resolve("C:/ProgramData/archflow-mcp/kongxing_connection.json")',
                            'path.join(process.env.LOCALAPPDATA || os.homedir(), "KStudio", "connectors", "kongxing", "connection.json")')
    server = server.replace('path.resolve("C:/ProgramData/archflow-mcp/kongxing_mcp.log")',
                            'path.join(path.dirname(connectionFile), "connector.log")')
    license_text = args.node_license.read_bytes()
    if len(license_text) < 1000 or b"Node.js" not in license_text or b"Permission is hereby granted" not in license_text:
        raise ValueError("Node license receipt missing.")
    output.mkdir(parents=True)
    with zipfile.ZipFile(output / "KStudio-SketchUp-Connector.rbz", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, text in ruby.items():
            archive.writestr(name, text.encode("utf-8"))
    (output / "kongxing_sketchup_mcp.mjs").write_text(server, encoding="utf-8")
    shutil.copyfile(args.node, output / "node.exe")
    (output / "LICENSE.Node.txt").write_bytes(license_text)
    (output / "README.txt").write_text(
        "K Studio connector PRIVATE LOCAL TRIAL\n"
        "1. Select your installed SketchUp version in K Studio.\n"
        "2. Download RBZ and install through that SketchUp version's Extension Manager.\n"
        "3. Install the local connection program from K Studio, then start Kongxing AI > Start Local Bridge.\n"
        "4. Check MCP separately; installation is not native compatibility acceptance.\n"
        "Node runtime is bundled with its license; Codex and API credentials are not included.\n"
        "No public redistribution: legacy connector source provenance requires review.\n", encoding="utf-8")
    files = {path.name: {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
             for path in output.iterdir() if path.is_file()}
    manifest = {"schema": 1, "version": "0.1.0-kstudio-local1", "publication": "private_local_trial",
                "source_provenance": "owner_installed_source_redistribution_not_verified", "clean_machine_acceptance": "not_run",
                "files": files, "source_sha256": source_hashes}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"package_built": True, "publication": manifest["publication"], "payload_count": len(files)}))


if __name__ == "__main__":
    main()
