# Thin transport only. Geometry and ownership guards stay in K Studio ProjectRuby.
require 'json'
require 'digest'
require 'openssl'
require 'fileutils'

module KStudioPublicConnector
  ROOT = File.join(ENV.fetch('LOCALAPPDATA'), 'KStudio', 'connectors', 'public').tr('\\', '/').freeze
  class << self
    def atomic_json(path, data)
      temporary = path + ".#{Process.pid}.tmp"
      File.open(temporary, 'wb') { |f| f.write(JSON.generate(data)); f.flush; f.fsync }
      File.rename(temporary, path)
    end

    def envelope(body, token)
      text = JSON.generate(body)
      { 'body' => text, 'mac' => OpenSSL::HMAC.hexdigest('SHA256', token, text) }
    end

    def equal_mac?(a, b)
      return false unless a.is_a?(String) && b.is_a?(String) && a.bytesize == b.bytesize
      a.bytes.zip(b.bytes).inject(0) { |sum, pair| sum | (pair[0] ^ pair[1]) } == 0
    end

    def document_matches?(args)
      model = Sketchup.active_model
      path = args['expected_model_path']
      guid = args['expected_model_guid']
      path.is_a?(String) && !path.empty? && guid.is_a?(String) && !guid.empty? &&
        File.expand_path(model.path).tr('\\', '/').downcase == File.expand_path(path).tr('\\', '/').downcase && model.guid == guid
    end

    def quarantine(path)
      folder = File.join(ROOT, 'rejected')
      FileUtils.mkdir_p(folder)
      # Keep malformed evidence private; never retry it or print its contents.
      File.rename(path, File.join(folder, File.basename(path) + ".#{Process.pid}.#{Time.now.to_f}.invalid"))
    end

    def dispatch(name, args, config)
      raise 'Not on SketchUp main thread' unless Thread.current == Thread.main
      model = Sketchup.active_model
      case name
      when 'sketchup_health', 'sketchup_get_model_context'
        { connected: true, connector: 'kstudio-public', version: '2026.11.04',
          sketchup_version: Sketchup.version, ruby_version: RUBY_VERSION,
          model_path: model.path, model_guid: model.guid, model_name: model.title,
          active_context: !model.active_path.nil?, main_thread: true,
          entity_count: model.entities.length }
      when 'sketchup_eval_project_file'
        root = File.realpath(config.fetch('script_root')).tr('\\', '/').downcase
        script = File.realpath(args.fetch('script_path')).tr('\\', '/')
        raise 'Script is outside paired directory' unless script.downcase.start_with?(root + '/') && File.extname(script).downcase == '.rb'
        raise 'Script exceeds maximum size' if File.size(script) > 16 * 1024 * 1024
        code = File.binread(script)
        raise 'Script changed after dispatch' unless Digest::SHA256.hexdigest(code) == args.fetch('script_sha256')
        raise 'Unmarked script refused' unless code.lines.first.to_s.include?('ARCHFLOW_GENERATED_SCRIPT')
        result = eval(code.force_encoding('UTF-8'), TOPLEVEL_BINDING.dup, script)
        { result: result }
      when 'sketchup_set_camera'
        raise 'Active document identity changed; camera not moved' unless document_matches?(args)
        eye = args.fetch('eye_m').map { |v| Float(v).m }
        target = args.fetch('target_m').map { |v| Float(v).m }
        model.active_view.camera = Sketchup::Camera.new(eye, target, args.fetch('up', [0, 0, 1]))
        { camera_set: true }
      when 'sketchup_export_view_image'
        raise 'Active document identity changed; image not captured' unless document_matches?(args)
        output = File.expand_path(args.fetch('output_path')).tr('\\', '/')
        parent = File.realpath(File.dirname(output)).tr('\\', '/').downcase
        allowed = config.fetch('workspace_roots', []).any? do |folder|
          base = File.realpath(folder).tr('\\', '/').downcase
          parent == base || parent.start_with?(base + '/')
        end
        raise 'Image destination is outside paired workspaces' unless allowed && File.extname(output).downcase == '.png'
        raise 'Image destination must not be a symlink' if File.symlink?(output)
        width, height = Integer(args.fetch('width', 1500)), Integer(args.fetch('height', 950))
        raise 'Invalid capture dimensions' unless width.between?(64, 4096) && height.between?(64, 4096)
        model.active_view.zoom_extents if args.fetch('zoom_extents', false)
        ok = model.active_view.write_image(filename: output, width: width, height: height, antialias: true)
        raise 'Native image export failed' unless ok
        { saved: true, path: output }
      else
        raise 'Unsupported connector operation'
      end
    end

    def tick
      return if @busy
      return unless File.directory?(ROOT)
      @busy = true
      lock = nil
      begin
        lock = File.open(File.join(ROOT, 'writer.lock'), 'a')
        return unless lock.flock(File::LOCK_EX | File::LOCK_NB)
        process_tick
      rescue StandardError => error
        warn("K Studio connector lock: #{error.class}")
      ensure
        lock.close if lock
        @busy = false
      end
    end

    def process_tick
      config_path = File.join(ROOT, 'pairing.json')
      return unless File.file?(config_path)
      config = JSON.parse(File.read(config_path, encoding: 'UTF-8'))
      return unless config['enabled']
      # Validate before counting the two completed items. Invalid requests cannot
      # permanently occupy the head of the queue and starve health/model checks.
      processed = 0
      Dir.glob(File.join(ROOT, 'requests', '*.json')).sort.first(128).each do |path|
        break if processed >= 2
        begin
          if File.size(path) > 1024 * 1024
            quarantine(path)
            next
          end
          signed = JSON.parse(File.read(path, encoding: 'UTF-8'))
          unless signed.is_a?(Hash)
            quarantine(path)
            next
          end
          expected = OpenSSL::HMAC.hexdigest('SHA256', config.fetch('token'), signed.fetch('body'))
          unless equal_mac?(expected, signed['mac'])
            quarantine(path)
            next
          end
          request = JSON.parse(signed['body'])
          unless request.is_a?(Hash)
            quarantine(path)
            next
          end
          id = request.fetch('operation_id')
          unless id.is_a?(String) && id.match?(/\A[a-zA-Z0-9]{1,80}\z/) && File.basename(path) == id + '.json'
            quarantine(path)
            next
          end
          args = request.fetch('arguments', {})
          expired = Time.now.to_f > request.fetch('expires_at')
          # Let the instance/document selected by the host consume its request.
          # Other SU instances must not turn it into a cached mismatch failure.
          if !expired && ['sketchup_set_camera', 'sketchup_export_view_image'].include?(request['name']) && !document_matches?(args)
            next
          end
          journal = File.join(ROOT, 'journal', id + '.json')
          response = File.join(ROOT, 'responses', id + '.json')
          if File.exist?(response)
            File.delete(path)
            processed += 1
            next
          end
          previous = File.exist?(journal) ? JSON.parse(File.read(journal, encoding: 'UTF-8')) : nil
          # Preserve initial identity and request hash through every terminal
          # transport state. RETURNED does not certify native commit or save.
          evidence = previous || { operation_id: id, state: 'STARTED', at: Time.now.to_f,
            model_path: Sketchup.active_model.path, model_guid: Sketchup.active_model.guid,
            script_sha256: args['script_sha256'], request_digest: request['request_digest'], tool: request['name'] }
          if previous
            result = { operation_id: id, error: 'Prior native operation is unresolved; reconcile model before continuing.' }
          elsif expired
            result = { operation_id: id, error: 'Request expired before native execution; no operation started.' }
          else
            atomic_json(journal, evidence)
            begin
              value = dispatch(request.fetch('name'), args, config)
              result = { operation_id: id, result: value }
            rescue StandardError, SyntaxError => error
              result = { operation_id: id, error: error.message }
            end
          end
          result[:request_digest] = request['request_digest']
          atomic_json(response, envelope(result, config.fetch('token')))
          final_state = expired && !previous ? 'NOT_STARTED' : result[:error] ? 'ERROR_OR_UNKNOWN' : 'RETURNED'
          # JSON parses string keys; normalize before merging to avoid duplicate keys.
          evidence = evidence.each_with_object({}) { |(key, value), memo| memo[key.to_s] = value }
          atomic_json(journal, evidence.merge('state' => final_state, 'finished_at' => Time.now.to_f))
          File.delete(path)
          processed += 1
        rescue JSON::ParserError, KeyError, TypeError, ArgumentError => error
          quarantine(path) if File.exist?(path)
          warn("K Studio connector rejected request: #{error.class}")
        end
      end
    rescue StandardError => error
      # Token and source are never logged. Keep the previous journal intact.
      warn("K Studio connector: #{error.class}")
    end

    def start
      return if @timer
      @timer = UI.start_timer(0.15, true) { tick }
    end

    def stop
      UI.stop_timer(@timer) if @timer
      @timer = nil
    end
  end
  unless @menu_added
    menu = UI.menu('Extensions').add_submenu('K Studio Connector')
    menu.add_item('Start paired local connector') { start }
    menu.add_item('Stop connector') { stop }
    @menu_added = true
  end
  start
end
