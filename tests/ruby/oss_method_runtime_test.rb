# frozen_string_literal: true
require_relative '../../app/oss_method_runtime'

module StubADAIConstructionGeometry
  def self.profile(*args)
    'shape-' + args.length.to_s
  end

  def self.loft_sections(*args)
    raise 'SketchUp face generation failed'
  end
end

events = []
proxy = KStudioOSSMethodRuntime::ADAIProxy.new(StubADAIConstructionGeometry, events)
raise 'Expected delegated real call return' unless proxy.profile(:entities, :name) == 'shape-2'
raise 'Actual call was not recorded' unless events.length == 1 &&
                                             events[0]['method_id'] == 'adai.profile' &&
                                             events[0]['status'] == 'returned'
begin
  proxy.loft_sections(:bad)
  raise 'Expected downstream Ruby error'
rescue RuntimeError => e
  raise e unless e.message == 'SketchUp face generation failed'
end
raise 'Real failed call should be recorded as raised' unless
  events[1]['method_id'] == 'adai.loft_sections' &&
  events[1]['status'] == 'raised'
raise 'Method proxy must not expose arbitrary module methods' if proxy.respond_to?(:arbitrary_mutation)
raise 'No untracked fake product usage' if events.any? { |e| e['method_id'].nil? }

puts 'OSS Ruby host wrapper contract PASS'
