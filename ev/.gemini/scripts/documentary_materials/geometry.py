"""Small real 3D mesh renderer: vertices, faces, perspective, lighting and depth."""
import math
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
F = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 24)
SMALL = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 17)


def mesh(kind):
    if kind == "threaded_rod":
        from .thread_mesh import threaded_rod_mesh
        return threaded_rod_mesh()
    if kind == "box":
        vertices = np.array([[x,y,z] for x in (-.5,.5) for y in (-.5,.5) for z in (-.5,.5)])
        faces = [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
    else:
        sides = 6 if kind == "nut" else 24
        vertices = np.array([[r*math.cos(2*math.pi*i/sides), y, r*math.sin(2*math.pi*i/sides)]
                             for r in (.5,.25) for y in (-.5,.5) for i in range(sides)])
        faces = []
        for i in range(sides):
            j=(i+1)%sides
            faces.extend([[i,j,j+sides,i+sides], [2*sides+i,3*sides+i,3*sides+j,2*sides+j],
                          [i,2*sides+i,2*sides+j,j], [sides+i,sides+j,3*sides+j,3*sides+i]])
    return vertices, faces


import os as _os
# Richer silhouettes for scenes the five engineering primitives cannot draw
# (terrain, rivers, peaks, rubble, houses). DOCUMENTARY_THREE_RICH=0 turns the
# extra types off: they fall back to "box" exactly as before.
_EXTRA_TYPES = () if _os.environ.get("DOCUMENTARY_THREE_RICH", "1") == "0" else ("terrain", "water", "cone", "sphere", "house")
_PROFILES = ("valley", "peak", "ridge", "slope", "flat")


def validate(spec):
    if not isinstance(spec, dict):
        raise ValueError("Need a dictionary mesh spec")
    if not isinstance(spec.get("title"), str):
        spec["title"] = "Structural Analysis"
    objects = spec.get("objects")
    if not isinstance(objects, list) or len(objects) == 0:
        spec["objects"] = [{"type": "box", "position": [0, 0, 0], "size": [2.0, 1.0, 1.0], "color": "#8398a3"}]
    elif len(objects) > 24:
        spec["objects"] = objects[:24]
    
    cleaned_objects = []
    for obj in spec["objects"]:
        if not isinstance(obj, dict):
            continue
        otype = obj.get("type")
        if otype not in ("box", "cylinder", "tube", "nut", "threaded_rod") + _EXTRA_TYPES:
            otype = "box"
        
        # position
        pos = obj.get("position")
        if not isinstance(pos, list) or len(pos) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) for x in pos):
            pos = [0.0, 0.0, 0.0]
        else:
            pos = [max(-8.0, min(8.0, float(x))) for x in pos]
            
        # size
        size = obj.get("size")
        if not isinstance(size, list) or len(size) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in size):
            size = [1.0, 1.0, 1.0]
        else:
            size = [max(0.05, min(10.0, float(x))) for x in size]
            
        # end_position
        end_pos = obj.get("end_position")
        if end_pos is None or not isinstance(end_pos, list) or len(end_pos) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) for x in end_pos):
            end_pos = list(pos)
        else:
            end_pos = [max(-8.0, min(8.0, float(x))) for x in end_pos]
            
        # rotation in degrees: a cylinder or tube is vertical until turned,
        # and a tunnel bore or a pipe run lies on its side.
        rot = obj.get("rotation")
        if not isinstance(rot, list) or len(rot) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) for x in rot):
            rot = [0.0, 0.0, 0.0]
        else:
            rot = [max(-360.0, min(360.0, float(x))) for x in rot]

        # color
        color = obj.get("color")
        if not isinstance(color, str):
            color = "#8398a3"
        elif re.fullmatch(r"#[0-9a-fA-F]{3}", color):
            color = "#" + "".join(c * 2 for c in color[1:])
        elif not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            color = "#8398a3"
            
        profile = obj.get("profile")
        extra = {"profile": profile} if profile in _PROFILES and otype == "terrain" else {}
        cleaned_objects.append({
            **extra,
            "type": otype,
            "position": pos,
            "size": size,
            "end_position": end_pos,
            "rotation": rot,
            "color": color
        })
        
    if not cleaned_objects:
        cleaned_objects = [{"type": "box", "position": [0, 0, 0], "size": [2.0, 1.0, 1.0], "color": "#8398a3"}]
    spec["objects"] = cleaned_objects
    return spec



def frame(spec,t):
    im=Image.new("RGB",(W,H),"#eff2ef");d=ImageDraw.Draw(im)
    yaw=math.radians(float(spec.get("camera_yaw",-26))+18*t)
    pitch=math.radians(-16)
    ry=np.array([[math.cos(yaw),0,math.sin(yaw)],[0,1,0],[-math.sin(yaw),0,math.cos(yaw)]])
    rx=np.array([[1,0,0],[0,math.cos(pitch),-math.sin(pitch)],[0,math.sin(pitch),math.cos(pitch)]])
    rotation=rx@ry
    polygons=[]
    all_camera=[]
    prepared=[]
    for obj in spec["objects"]:
        vertices,faces=mesh(obj["type"])
        start=np.array(obj["position"]);end=np.array(obj.get("end_position",obj["position"]))
        vertices=vertices*np.array(obj["size"])+start+(end-start)*t
        camera=vertices@rotation.T
        prepared.append((obj,camera,faces));all_camera.extend(camera)
    extent=np.array(all_camera)
    center=(extent.max(axis=0)+extent.min(axis=0))/2
    fit=max(1.,float(np.ptp(extent[:,0]))/8.5,float(np.ptp(extent[:,1]))/4.7)
    for obj,camera,faces in prepared:
        camera=(camera-center)/fit
        # Models describe the visible/front cutaway at +Z; the camera must face it.
        depth=14-camera[:,2]
        if np.any(depth<=1):raise ValueError("Mesh intersects camera")
        points=np.column_stack([W/2+camera[:,0]*1230/depth,H/2-camera[:,1]*1230/depth])
        color=tuple(int(obj.get("color","#8398a3")[i:i+2],16) for i in (1,3,5))
        for face in faces:
            p=camera[face];normal=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(normal)
            illumination=.55+.4*abs(float(normal@np.array([.4,.7,.6]))/length) if length else .65
            polygons.append((float(depth[face].mean()),[tuple(x) for x in points[face]],tuple(min(255,int(c*illumination)) for c in color)))
    for _,points,color in sorted(polygons,reverse=True,key=lambda x:x[0]):
        d.polygon(points,fill=color,outline="#394850")
    d.text((36,26),spec["title"][:85],fill="#122a34",font=F)
    subtitle=str(spec.get("caption","Qualitative geometry and motion; no computed stress values"))[:125]
    d.text((36,73),subtitle,fill="#334e59",font=SMALL)
    if "bedrock" in (str(spec.get("title", ""))+" "+str(spec.get("caption", ""))).lower():
        d.text((36,H-70),"BEDROCK STRATUM / FOOTINGS SOCKETED BELOW GRADE",fill="#5b4638",font=SMALL)
    d.text((36,H-44),"3D MESH ILLUSTRATION - NOT FEA / NOT HISTORICAL FOOTAGE",fill="#8d382b",font=SMALL)
    return im
