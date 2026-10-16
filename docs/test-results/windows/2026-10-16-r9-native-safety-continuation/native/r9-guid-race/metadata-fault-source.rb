# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise "Wrong fault-copy identity" unless m.guid=="63a34460-717a-49e9-bff8-18d5f4246226" && File.expand_path(m.path)==File.expand_path("E:\\K AI 产品建模网站\\runtime\\projects\\architecture-project-4f0e4\\outputs\\model\\blank-disposable-r9-guid-race-20261016.skp")
r=m.entities.find{|e| e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise "Wrong owned revision" unless r && r.get_attribute("sketchup_architect","revision")==9
r.set_attribute("kstudio_disposable_fault","guid_race",1792122930537754300)
{metadata_only_on_disposable_copy:true}
