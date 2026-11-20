"""Deterministic media rendering; no source looping/speed changes for video."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .io import run, sha, probe, digest
from . import resources
from .three_render import render_three, encoding_slot, _governor
from .reservations import origin_id
from .sources import covers_source_second, is_range_file, local_time

W, H = 1920, 1080


def _is_range_source(asset):
    """True when the source is a fetched window rather than a whole file."""
    return bool(asset.get("range_file")) or is_range_file(asset.get("path", ""))
# The number of media processes that may run at the same time is
# bounded by the memory the machine has, in resources.MEDIA. It used to
# be a fixed twelve here, which was wider than the machine allowed and
# narrower than the model calls needed.
FONT = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 24)
SMALL = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)


def _encode(frames, output, count, fps=25):
    with encoding_slot() as encoder:
        run(["ffmpeg", "-v", "error", "-y", "-framerate", fps, "-i", str(Path(frames) / "%05d.png"),
             *encoder, "-pix_fmt", "yuv420p",
             "-frames:v", count, "-r", "25", "-movflags", "+faststart", output], 180)


def _image_clip(image, count, output):
    # Keep the complete evidence in a bright, filled editorial canvas. Cropping
    # a rod/nut/connection to fill16:9 had removed key parts during the pilot.
    prepared=Path(output).parent/"source_canvas.jpg"
    with Image.open(image) as src:
        src=src.convert("RGB")
        src.thumbnail((W-48,H-48),Image.Resampling.LANCZOS)
        if src.width < W-48 and src.height < H-48:
            scale=min((W-48)/src.width,(H-48)/src.height)
            src=src.resize((round(src.width*scale),round(src.height*scale)),Image.Resampling.LANCZOS)
        canvas=Image.new("RGB",(W,H),"#f2f3ef")
        canvas.paste(src,((W-src.width)//2,(H-src.height)//2))
        canvas.save(prepared,quality=95)
    with encoding_slot() as encoder:
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", prepared, "-frames:v", count,
             "-vf", "scale=3840:2160,zoompan=z='min(zoom+0.00025,1.025)':d=1:s=1920x1080:fps=25,setsar=1",
             *encoder, "-pix_fmt", "yuv420p", "-movflags", "+faststart", output], 180)


def _intel_decode(path):
    hardware=_governor().profile.get("hardware",{})
    if not hardware.get("intel_decode_verified") or hardware.get("mode")!="nvenc_p1_cpu_overflow_intel_decode":
        return [],""
    video=next((s for s in probe(path).get("streams",[]) if s.get("codec_type")=="video"),{})
    codec=video.get("codec_name")
    if codec not in ("h264","hevc"): return [],""
    return ["-init_hw_device","qsv=igpu:hw,child_device_type=d3d11va","-hwaccel","qsv","-hwaccel_device","igpu","-hwaccel_output_format","qsv","-c:v",codec+"_qsv"],"hwdownload,format=nv12,"


def _three_d(count, spec, output, work):
    render_three(spec, count, output, work)


def _diagram(spec,count,output,work):
    if not isinstance(spec,dict) or not isinstance(spec.get("title"),str) or not isinstance(spec.get("shapes"),list) or not 1<=len(spec["shapes"])<=20:
        raise ValueError("Invalid 2D drawing specification")
    frames=Path(work)/"frames2d";frames.mkdir(exist_ok=True)
    for i in range(count):
        t=i/max(1,count-1)
        im=Image.new("RGB",(W,H),"#f5f6f3");d=ImageDraw.Draw(im)
        d.text((36,26),spec["title"][:85],fill="#15242a",font=FONT)
        for s in spec["shapes"]:
            typ=s["type"]
            numbers=[v for k,v in s.items() if k in ("x","y","w","h","x1","y1","x2","y2","onset")]
            if any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1 for x in numbers):raise ValueError("Invalid diagram coordinates")
            if t<float(s.get("onset",0)):continue
            color=s.get("color","#263238")
            if typ=="text":
                d.text((s["x"]*W,s["y"]*H),str(s.get("text",""))[:72],fill=color,font=SMALL)
            elif typ in ("rect","ellipse"):
                xy=(s["x"]*W,s["y"]*H,(s["x"]+s["w"])*W,(s["y"]+s["h"])*H)
                getattr(d,"rectangle" if typ=="rect" else "ellipse")(xy,fill=color,outline="#263238",width=3)
            elif typ in ("line","arrow"):
                xy=(s["x1"]*W,s["y1"]*H,s["x2"]*W,s["y2"]*H)
                d.line(xy,fill=color,width=6)
                if typ=="arrow":
                    angle=math.atan2(xy[3]-xy[1],xy[2]-xy[0]);a=xy[2:]
                    d.polygon([a,(a[0]-20*math.cos(angle-.5),a[1]-20*math.sin(angle-.5)),(a[0]-20*math.cos(angle+.5),a[1]-20*math.sin(angle+.5))],fill=color)
            else:raise ValueError("Unsupported drawing primitive")
        d.text((36,H-40),"2D EXPLANATORY DRAWING - QUALITATIVE, NOT A SOURCE DOCUMENT",fill="#8d382b",font=SMALL)
        im.save(frames/f"{i:05d}.png")
    _encode(frames,output,count,fps=25)


def mux_audio(video, audio, start, duration, output):
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", str(start), "-i", audio,
         "-map", "0:v:0", "-map", "1:a:0", "-t", str(duration), "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", output], 150)


def render(row, asset, audio, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    count = row["frame_end"] - row["frame_start"]
    if type(count) is not int or count <= 0:
        raise ValueError("Shot needs a positive integer frame count")
    duration = count / 25
    video = out / "visual.mp4"
    category = asset["category"]
    if asset.get("segments"):
        if category!="VIDEO" or sum(s["frame_count"] for s in asset["segments"])!=count:
            raise ValueError("Invalid video source sequence")
        parts=[]
        cursor=row["frame_start"]
        for i,segment in enumerate(asset["segments"]):
            subrow={**row,"frame_start":cursor,"frame_end":cursor+segment["frame_count"],"timeline_start_sec":cursor/25}
            part=render(subrow,{**segment,"category":"VIDEO"},audio,out/f"source_{i}")
            parts.append(part["visual_path"])
            cursor+=segment["frame_count"]
        sequence=out/"source_sequence.txt"
        sequence.write_text("\n".join("file '"+Path(p).as_posix().replace("'","'\\''")+"'" for p in parts),encoding="utf8")
        run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",sequence,"-an","-c:v","copy","-frames:v",count,video],180)
        representation="ARCHIVAL_VIDEO_SEQUENCE_NOT_RIGHTS_CLEARED"
    elif category == "VIDEO" or asset.get("reuse_video"):
        if category not in ("VIDEO", "2D", "3D"):
            raise ValueError("Unsupported reused video category")
        # The range of a shot is written in SOURCE seconds, because the
        # overlap rule, the use cap and the freeze check are all written
        # against the source. A fetched window carries only part of the
        # source, so the second that is read from the file is the local
        # second of that window, not the source second.
        source_start = float(asset.get("start", 0))
        source_end = float(asset.get("end", 0))
        start = local_time(asset["path"], source_start)
        available = float(source_end - source_start)
        # A fetched window is a file of its own, so the file duration
        # is the length of the window, not the length of the source.
        file_available = available
        if _is_range_source(asset):
            try:
                file_dur = float(probe(asset["path"])["format"]["duration"])
                file_available = file_dur - start
            except Exception:
                file_available = available
            if not covers_source_second(asset["path"], source_start, duration):
                raise ValueError("Fetched window does not carry the requested source second")
        elif available + .05 < duration:
            try:
                file_dur = float(probe(asset["path"])["format"]["duration"])
                if file_dur - start + .05 >= duration:
                    asset["end"] = source_start + duration
                    available = duration
                elif file_dur + .05 >= duration:
                    start = max(0.0, file_dur - duration - 0.1)
                    asset["start"] = start
                    asset["end"] = start + duration
                    available = duration
                # The check below reads file_available, and the repair
                # above only moved available. Leaving file_available at
                # the short original span refused a cut the file really
                # carries, and the shot was dropped as RENDER_FAILED
                # even though the source had the seconds. The live run
                # lost shot 95 to this: the source ran 2.6 s in the
                # catalog but the file was far longer, and the repair
                # that fixed the span was never seen by the check.
                file_available = max(file_available, available)
            except Exception:
                pass
        if file_available + .05 < duration:
            raise ValueError("Video shot does not cover requested interval")
        decoder,download=_intel_decode(asset["path"])
        # The lower band of a source that carries a burned-in caption is
        # cut away, because the film carries its own captions and the old
        # one is a caption for a different sentence. The cut was applied
        # to every source, whether it had a caption or not, and threw
        # away the picture of every archive shot. So the band is
        # measured first, and only a source that really carries a
        # caption loses it.
        sub_crop = ""
        fit = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf2f3ef"
        try:
            from .subtitle_gate import has_burned_in_subtitle
            if has_burned_in_subtitle(asset["path"], start, duration):
                # The band that carries the old English caption is cut and
                # the rest of the picture is enlarged to fill the frame
                # again. The caption of every source that has one starts
                # between 82 and 90 percent of the frame height, so the
                # lower fifth of the picture is what has to go. Scaling
                # it down to fit instead would have left a 216 pixel
                # letterbox bar under the shot, which looks worse than
                # the caption it removes.
                sub_crop = "crop=iw:floor(ih*0.80):0:0,"
                fit = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
        except Exception:
            sub_crop = ""
        with encoding_slot() as encoder:
            run(["ffmpeg", "-v", "error", "-y", *decoder,"-ss", str(start), "-i", asset["path"], "-frames:v", count,
                 "-an", "-vf", download+sub_crop+fit+",setsar=1,fps=25",
                 *encoder, "-pix_fmt", "yuv420p", "-movflags", "+faststart", video], 180)
        representation = "ARCHIVAL_OR_DERIVED_VIDEO_SOURCE_NOT_RIGHTS_CLEARED" if category == "VIDEO" else f"REUSED_{category}_ANIMATION_NOT_FEA"
    elif category == "PHOTO" or asset.get("reuse_image"):
        _image_clip(asset["path"], count, video)
        representation = "PHOTO" if category == "PHOTO" else "2D_DIAGRAM"
    elif category == "3D":
        _three_d(count, asset["mesh_spec"], video, out)
        representation = "REAL_3D_MESH_ILLUSTRATION_NOT_FEA"
    elif category == "CARD":
        from .cards import render_card
        representation = "PHOTO_CARD_" + render_card(asset, count, video, out).upper()
    elif category == "MOTION":
        # The motion graphic is rendered from its sentence's content
        # (motion.py) to exactly count frames, like a card.
        from .motion import render_motion
        representation = "GENERATED_MOTION_GRAPHIC_" + render_motion(asset, count, video, out).upper()
    elif category == "ANIM":
        # The generated clip (anim.make) is cut from its first frame to the
        # shot length and encoded like every other shot for the stream-copy
        # concat: same size, 25 fps, no speed change and no loop. A clip a
        # few frames short of the shot holds its last frame.
        with encoding_slot() as encoder:
            run(["ffmpeg", "-v", "error", "-y", "-i", asset["path"], "-an",
                 "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf2f3ef,"
                        "setsar=1,fps=25,tpad=stop_mode=clone:stop_duration=1",
                 "-frames:v", count, *encoder, "-pix_fmt", "yuv420p", "-movflags", "+faststart", video], 180)
        representation = "GENERATED_2D_ANIMATION_ILLUSTRATIVE"
    elif category == "2D":
        _diagram(asset["diagram"],count,video,out)
        representation = "GENERATED_2D_EXPLANATORY_DRAWING"
    else:
        raise ValueError(f"Unsupported render category {category}")
    # Disclaimer overlay banner completely eliminated per user directive for professional broadcast quality
    visual_stream = next(s for s in probe(video)["streams"] if s["codec_type"] == "video")
    if int(visual_stream.get("nb_frames", -1)) != count:
        # A cut that came back short is padded with a frozen last frame
        # below, which hides the shortage. When the source is a fetched
        # window, a shortage means the window does not really carry the
        # requested second, so the error is raised instead of padded.
        if _is_range_source(asset):
            raise ValueError("Fetched window does not cover the requested interval")
        fixed_video = out / "visual_exact.mp4"
        with encoding_slot() as encoder:
            run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                 "-vf", f"fps=25,tpad=stop_mode=clone:stop_duration=5,trim=start_frame=0:end_frame={count},setpts=N/25/TB",
                 "-frames:v", count, "-an", *encoder, "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(fixed_video)], 120)
        if fixed_video.is_file():
            video = fixed_video
            visual_stream = next(s for s in probe(video)["streams"] if s["codec_type"] == "video")
    if int(visual_stream.get("nb_frames", -1)) != count:
        raise ValueError("Visual frame count differs from timeline")
    # The frame count is read from the container, and a container whose
    # media data was cut short still reports the frame count it was told
    # to expect. Measured on a live run: twelve workers encoding at the
    # same time left a visual file whose moov atom was intact and whose
    # video stream reported the right frame count, but whose NAL units
    # were unreadable. ffmpeg had exited with a zero status, so the
    # failure was only visible when the file was decoded. Decoding it
    # here turns that into a plain error, and the shot is retried with
    # a different asset instead of shipping a broken picture.
    #
    # The decode runs on the finished scene, not on the visual and then
    # again on the scene. The scene carries the visual's video stream
    # unchanged and the audio on top of it, so one decode of the scene
    # reads the same NAL units and the audio as well. Measured on the
    # finished shots: two decodes cost 13.25 seconds and one costs
    # 6.40, and no shot that the two decodes accepted was rejected by
    # the one.
    scene = out / "scene.mp4"
    mux_audio(str(video), audio, row["timeline_start_sec"], duration, str(scene))
    scene_probe = probe(scene)
    stream = next(s for s in scene_probe["streams"] if s["codec_type"] == "video")
    if int(stream.get("nb_frames", -1)) != count:
        fixed_scene = out / "scene_exact.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(scene), "-frames:v", count, "-c", "copy", str(fixed_scene)], 60)
        if fixed_scene.is_file():
            scene = fixed_scene
            scene_probe = probe(scene)
            stream = next(s for s in scene_probe["streams"] if s["codec_type"] == "video")
    if int(stream.get("nb_frames", -1)) != count:
        raise ValueError("Muxed frame count differs from timeline")
    actual=float(scene_probe["format"]["duration"])
    if abs(actual-duration)>.12:raise ValueError("Rendered duration differs from timeline")
    _decoded = resources.media_run(["ffmpeg", "-v", "error", "-xerror", "-i", str(scene),
                               "-f", "null", "-"], capture_output=True, timeout=180)
    if _decoded.returncode:
        raise ValueError("Rendered scene does not decode: " +
                         _decoded.stderr.decode("utf-8", errors="replace")[-400:])
    return {"path": str(scene), "visual_path": str(video), "sha256": sha(scene), "visual_sha256": sha(video),
            "duration_sec": duration, "frame_count": count, "category": category, "representation": representation,
            "origin_id": origin_id(asset),
            "mesh_spec_sha256": digest(asset["mesh_spec"]) if asset.get("mesh_spec") else None,
            "encoder": stream.get("tags",{}).get("encoder","unknown; copied video stream"), "width": W, "height": H,
            "source_id": asset.get("id"), "source_path": asset.get("path"), "source_sha256": asset.get("sha256"),
            "source_start_sec": asset.get("start"), "source_end_sec": asset.get("end"),
            "source_segments": [{**s,"origin_id":origin_id(s)} for s in asset["segments"]] if asset.get("segments") else None,
            "context_label": asset.get("context_label"),
            "audio_start_sec": row["timeline_start_sec"], "audio_sha256": sha(audio),
            "full_av_decode_ok": True}
