# Load and start the user's already-installed Kongxing SketchUp extension.
# SketchUp executes this file in its own Ruby/API context via -RubyStartup.
require "sketchup.rb"

version_folder = "SketchUp #{Sketchup.version.to_i + 2000}"
plugin_main = File.join(
  ENV.fetch("APPDATA"),
  "SketchUp",
  version_folder,
  "SketchUp",
  "Plugins",
  "kongxing_ai_sketchup",
  "main.rb"
)
log_path = File.join(ENV["TEMP"] || File.dirname(plugin_main), "ai-architecture-studio-sketchup-startup.log")

UI.start_timer(2.0, false) do
  begin
    raise "Existing Kongxing AI extension not found: #{plugin_main}" unless File.file?(plugin_main)

    load plugin_main unless defined?(KongxingAI::Bridge)
    bridge = KongxingAI::Bridge.instance
    status = bridge.running? ? bridge.public_status : bridge.start
    File.write(log_path, "Bridge ready at #{status.fetch("host")}:#{status.fetch("port")}\n")
  rescue StandardError => error
    File.write(log_path, "#{error.class}: #{error.message}\n#{error.backtrace&.first(8)&.join("\n")}\n")
  end
end
