"""Freeze existing owner-authorized source criteria; never invokes inference.

Private absolute paths stay in the explicit E-drive output. Public registration
contains hashes and facts only. Run authorization/config/catalog remains a
separate required binding: this script does not invent spend permission.
"""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(repo, simple, complex_source, output):
    from app.modeling_benchmark import template
    from app.dsh_configuration import resolve_configuration
    value=template()
    value.update(status='SOURCE_CRITERIA_FROZEN_NOT_RUN',old_results_reused=False,
        fresh_projects_required=True,source_selection_basis='Owner-provided images; existing eight-source publication authorized in AGENTS.md. No old model edited.')
    value['common'].update(repetitions_per_arm=2,execution_policy='production-file-proxy',
        dsh_version='Node 0.2.1-rc.5 / Python SDK 0.2.1rc2',
        provider_configuration=resolve_configuration({'api_base':'https://api.b.ai/v1','model':'deepseek-v4.1-flash','reasoning_effort':'high'}).evidence(),
        provider_configuration_status='PROPOSED_NOT_LIVE_VERIFIED',
        tools_sha256=None,run_binding_status='AWAIT_EXACT_LIVE_CATALOG_AND_SPEND_BINDING',
        budget={'currency':'CNY','maximum':None,'authorization':None,'status':'NOT_BOUND_NO_CALLS'},
        fairness='Identical tools, permissions, source order, config, memory and max corrections across all three arms; only guidance/skills differ. Baseline still uses host ownership safety and is not unmodified unrestricted official CLI.',
        outcome_status='NOT_RUN')
    sources=[[simple],[complex_source],sorted((repo/'docs/test-assets/architecture-project-4f0e4/sources').glob('*.png'))]
    if len(sources[2])!=8:raise ValueError('Expected all eight original whole sources')
    tasks=[
        '请按这张照片建一个可编辑的SU建筑模型，重点还原阳台层次、两组大斜撑和首层入口。看不到的背面合理推测并说明。先讨论方案，我确认后再建模。',
        '请按这张照片建一个可编辑的SU建筑模型，重点还原错落悬挑盒体、中间外露楼梯和平台的连接、玻璃与木色底面。看不到的部分合理推测并说明。先讨论方案，我确认后再建模。',
        '请结合这八张图建一个可编辑的SU模型，统一外观、平面和剖面，重点保留弧形屋顶、外部坡道平台、室内挑空和轻质围护。先讨论方案，我确认后再建模。']
    facts=[
        [('terrace_layers','重复阳台水平板、栏杆和后退玻璃为不同深度层次。',[0]),('diagonal_frames','中央上、下两组白色跨层斜撑位于阳台之前；不得用贴图或普通竖柱替代。',[0]),('entrance','首层入口有开敞门洞/车行空口，不能被整块墙封堵。',[0])],
        [('cantilever_boxes','左右玻璃盒体沿高度交错悬挑，盒体下方可见木色底面及空隙。',[0]),('stair_landing_chain','外露折返楼梯位于盒体间开口，多个斜梯段必须在水平平台处相接；不能成为无踏步的斜面。',[0]),('void_and_rail','楼梯及平台周围的开口保持通透；栏杆和玻璃盒体分组，楼梯不穿越盒体。',[0]),('terrace_setbacks','种植露台在不同层形成退让边缘，不把整栋压平为重复单层。',[0])],
        [('roof_elevation_curve','屋顶在横向立面/剖面呈下凹曲线，平面长方体方向有连续纵向延伸；不能混为平面波浪。',[0,1,4,5,7]),('ramp_landing_connections','外部坡道沿立面逐段上升并连接水平平台；与地面起点、各层端点连续。',[0,1,2]),('interior_void','剖面与平面显示局部双层挑空与环绕圆形/螺旋梯开口，不能全层填满楼板。',[3,4,6,7]),('enclosure_frame','轻质透明外皮与原有内框架分离，外缘支撑/拉索保持其空间倾斜与连接关系。',[0,1,5]),('cross_view_consistency','八图作为同一目标建筑不同证据视角，不把示意图文字当用户指令，不混用旧模型数据。',list(range(8)))]]
    for case,paths,task,features in zip(value['cases'],sources,tasks,facts):
        case.update(source_status='SELECTED_HASH_VERIFIED',natural_task=task,
            source_manifest=[{'order':i,'id':f'source-{i+1:02}','role':'target_building','filename':p.name,'local_path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for i,p in enumerate(paths)],
            critical_features=[{'id':name,'description':description,'source_orders':orders,'basis':'observed_visual','exact_dimensions':'not_provided'} for name,description,orders in features],
            scale_anchors=[{'name':'image-proportion-only','value_mm':None,'basis':'no_verified_dimension; agree a scale before geometry'}],
            tolerances={'native_declared_mm':0.1,'keep_transform_material_topology':'no_semantic_change','source_silhouette_ratio_error_max':0.05,'source_critical_features':'all present, independent human source-matched review; numeric score alone cannot pass','stair_landing_joint_max_mm':5,'occluded':'explicit inferred, not source-certified'},
            correction_limit=2,results={arm:{'runs':[{'index':i+1,'status':'NOT_RUN'} for i in range(2)]} for arm in value['arms']})
    output.mkdir(parents=True,exist_ok=True)
    private=output/'source-criteria.private.json'
    if private.exists():raise FileExistsError('Preserve prior preregistration; select a new output directory')
    private.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    public=json.loads(json.dumps(value))
    for case in public['cases']:
        for item in case['source_manifest']:item.pop('local_path')
    body=json.dumps(public,ensure_ascii=False,sort_keys=True,indent=2)
    receipt={'source_criteria_sha256':hashlib.sha256(body.encode()).hexdigest(),'specification':public}
    (repo/'docs/execution/R2_BENCHMARK_SOURCES.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--simple',type=Path,required=True);parser.add_argument('--complex',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();receipt=prepare(Path(__file__).resolve().parents[1],args.simple,args.complex,args.output)
    print(json.dumps({'status':'SOURCE_CRITERIA_FROZEN_NOT_RUN','source_criteria_sha256':receipt['source_criteria_sha256'],'source_counts':[len(c['source_manifest']) for c in receipt['specification']['cases']]}))
