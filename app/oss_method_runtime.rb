# frozen_string_literal: true
#
# K AI Studio owns this tiny instrumentation wrapper. Third-party geometry
# implementations stay untouched, with their respective upstream licenses.
# A record exists only when the wrapped method ran in the guarded transaction.
module KStudioOSSMethodRuntime
  MAX_CALLS = 128

  def self.record(events, method_id)
    raise 'Invalid OSS method ledger' unless events.is_a?(Array)
    raise 'Too many OSS helper calls in one write' if events.length >= MAX_CALLS
    started = Time.now.to_f
    begin
      result = yield
      event = {
        'method_id' => method_id, 'status' => 'returned',
        'elapsed_ms' => ((Time.now.to_f - started) * 1000).round,
        'returned_nil' => result.nil?
      }
      # Some upstream constructors return SketchUp Group/ComponentInstance,
      # while others return Arrays or nil. Do not invent an entity PID.
      if result.respond_to?(:persistent_id)
        event['result_entity_pid'] = result.persistent_id
        event['result_entity_name'] = result.name if result.respond_to?(:name)
      end
      events << event
      result
    rescue StandardError => error
      events << {
        'method_id' => method_id, 'status' => 'raised',
        'elapsed_ms' => ((Time.now.to_f - started) * 1000).round,
        'error_class' => error.class.name
      }
      raise
    end
  end

  class ADAIProxy
    ALLOWED = %w[profile profile_with_holes loft_sections shell_grid closed_band].freeze

    def initialize(mod, events)
      @delegate = mod
      @events = events
    end

    ALLOWED.each do |method_name|
      define_method(method_name) do |*args, &block|
        KStudioOSSMethodRuntime.record(@events, 'adai.' + method_name) do
          @delegate.public_send(method_name, *args, &block)
        end
      end
    end
  end
end
