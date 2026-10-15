from copy import deepcopy
import math
from app.modeling_quality import verified_camera_match,capture_camera_receipt
import pytest


def camera():
    return {'eye_m':[1,2,3],'target_m':[4,5,6],'up':[0,0,1],'perspective':True,'fov_deg':35,'aspect_ratio':0,'height_m':None}


def test_missing_camera_is_not_matched_camera_evidence():
    for value in [None,{}, {'eye_m':[1,2,3]}]:
        assert not verified_camera_match(value,value)
    assert not capture_camera_receipt(None,None)['camera_verified_during_capture']


@pytest.mark.parametrize('key,value',[('eye_m',[1,2,4]),('fov_deg',40),('fov_deg',float('nan')),('aspect_ratio',1.5),('perspective',False)])
def test_geometry_view_and_projection_changes_are_detected(key,value):
    a=camera();b=deepcopy(a);b[key]=value
    assert not verified_camera_match(a,b)


def test_actual_native_identity_and_projection_required():
    a={'collector':'KStudioNativeCamera/1','model_path':'same.skp','model_guid':'native-guid','camera':camera()}
    assert capture_camera_receipt(a,deepcopy(a))['camera_verified_during_capture']
    b=deepcopy(a);b['model_guid']='other'
    assert not capture_camera_receipt(a,b)['camera_verified_during_capture']
    a['camera'].update(perspective=False,fov_deg=None,height_m=30)
    assert verified_camera_match(a['camera'],deepcopy(a['camera']))
    b=deepcopy(a);b['camera']['height_m']=31
    assert not capture_camera_receipt(a,b)['camera_verified_during_capture']
