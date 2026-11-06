# K Studio public connector. Uses the official SketchUp extension API.
require 'sketchup.rb'
require 'extensions.rb'
unless file_loaded?(__FILE__)
  extension = SketchupExtension.new('K Studio Local Connector', 'kstudio_connector/main')
  extension.description = 'Paired local-only K Studio bridge; no network listener.'
  extension.version = '2026.11.05-r2'
  extension.creator = 'K Studio'
  Sketchup.register_extension(extension, true)
  file_loaded(__FILE__)
end
