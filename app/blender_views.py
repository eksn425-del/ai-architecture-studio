"""Review cameras fitted to world bounds; legacy oblique poses are retained."""
import math
REVIEW_CAMERAS={'front':(17,-23,18),'rear':(-17,23,18),'front_elevation':(0,-1,0),'rear_elevation':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'top':(0,0,1),'bottom':(0,0,-1)}
def fitted_axis_camera(view,bounds):
    if view not in REVIEW_CAMERAS or len(bounds)!=3 or any(len(p)!=2 or any(type(v) not in(int,float) or not math.isfinite(v) for v in p) or p[0]>p[1] for p in bounds):raise ValueError('Invalid camera bounds')
    if view in ('front','rear'):return REVIEW_CAMERAS[view],(0,0,2.5),21,1000
    center=tuple((a+b)/2 for a,b in bounds);span=max(.1,max(b-a for a,b in bounds));direction=REVIEW_CAMERAS[view]
    return tuple(center[i]+direction[i]*span*3 for i in range(3)),center,span*1.12,span*10
