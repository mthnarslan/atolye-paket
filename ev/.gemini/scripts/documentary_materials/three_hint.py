"""Extra guidance appended to the 3D mesh_spec instruction (runner._work_shot: prompt=three_hint.apply(shot,prompt)).

New module: not part of any _CATEGORY_CODE list, so editing it never changes a
shot key. DOCUMENTARY_THREE_RICH=0 returns "" (old prompt, old scene types).
"""
import os


def text():
    if os.environ.get("DOCUMENTARY_THREE_RICH", "1") == "0":
        return ""
    return (
        "Extra object types (use them whenever the sentence is about land, water, a mountain, a settlement, rubble or ice, "
        "because stacked boxes and cylinders are rejected as unreadable): "
        "terrain {size:[10,3,8], profile:valley|peak|ridge|slope|flat, position:[0,-1.5,0]} is a coloured heightmap landscape "
        "(green lowland, brown slopes, grey rock, white snow); size[0]=width x, size[1]=highest relief, size[2]=depth z; a valley "
        "profile carves a river channel along z with steep walls, peak makes one mountain, ridge a mountain wall, slope a hillside. "
        "water {size:[w,0.2,d], color:\"#2f86c4\"} is a translucent river, lake or flood slab: lay it low in a valley channel "
        "(about 0.15 to 0.4 above the terrain position y); give end_position a higher y to make the flood rise. "
        "cone {size:[d,h,d]} is a peak, pine, funnel (rotate or invert with rotation [180,0,0]) or spoil heap; sphere {size:[x,y,z]} is a boulder, "
        "ice block, debris ball, tank or dome; house {size:[w,h,d]} is a small building with a roof. "
        "For a place, valley, glacier, flood, river or map-like sentence build ONE terrain as the base plus 5 to 14 small recognisable "
        "things on it (water, houses, cones, spheres, a thin box road or dam); use real colours (blue water, white ice or snow, brown rock, "
        "green land, red/orange for the hazard), not one grey for everything. A scene may use up to 24 objects. "
    )


def apply(shot, prompt):
    """Return prompt with text() inserted before the SHOT: block of a 3D selection prompt.

    Lives here (not as a `+three_hint.text()+` inside the runner prompt) because a split string constant in
    _work_shot/_select_shot changes the prompt-literal hash of EVERY category (measured: all finished shots
    of EP02-05 would be redone)."""
    if shot.get("category") != "3D":
        return prompt
    extra = text()
    if not extra:
        return prompt
    i = prompt.find("SHOT:{")
    return prompt + extra if i < 0 else prompt[:i] + extra + prompt[i:]
