import json
import subprocess

graph = {
    "nodes": [
        {
            "id": "1792333503704",
            "type": "custom",
            "position": {"x": -100, "y": 280},
            "positionAbsolute": {"x": -100, "y": 280},
            "sourcePosition": "right",
            "targetPosition": "left",
            "zIndex": 0,
            "width": 242,
            "height": 109,
            "selected": False,
            "data": {
                "type": "start",
                "title": "Başlat",
                "variables": [
                    {
                        "variable": "folder_path",
                        "required": True,
                        "hint": "",
                        "type": "text-input",
                        "label": "Proje Klasörü (folder_path)",
                        "options": [],
                        "placeholder": "",
                        "default": r"C:\Users\meteh\Downloads\07_Hyatt_Regency_Collapse-20261017T183530Z-1-001\07_Hyatt_Regency_Collapse",
                    }
                ],
                "selected": False,
            },
        },
        {
            "id": "node_stage_1",
            "type": "custom",
            "position": {"x": 300, "y": 280},
            "positionAbsolute": {"x": 300, "y": 280},
            "sourcePosition": "right",
            "targetPosition": "left",
            "zIndex": 0,
            "width": 242,
            "height": 108,
            "selected": False,
            "data": {
                "type": "http-request",
                "title": "1 • Sopro GPU Ses Sentezi & Flash Denetimi",
                "method": "post",
                "url": "http://host.docker.internal:8099/run",
                "headers": "Content-Type:application/json",
                "params": "",
                "body": {
                    "type": "json",
                    "data": [
                        {
                            "id": "kv-node_stage_1",
                            "key": "",
                            "type": "text",
                            "value": '{\n  "stage": 1,\n  "folder_path": "{{#1792333503704.folder_path#}}"\n}',
                        }
                    ],
                },
                "authorization": {"type": "no-auth", "config": None},
                "variables": [],
                "timeout": {
                    "connect": 60,
                    "read": 1800,
                    "write": 1800,
                    "max_connect_timeout": 1800,
                    "max_read_timeout": 1800,
                    "max_write_timeout": 1800,
                },
                "retry_config": {"retry_enabled": False, "max_retries": 0, "retry_interval": 100},
                "ssl_verify": True,
                "selected": False,
            },
        },
        {
            "id": "node_stage_2",
            "type": "custom",
            "position": {"x": 700, "y": 280},
            "positionAbsolute": {"x": 700, "y": 280},
            "sourcePosition": "right",
            "targetPosition": "left",
            "zIndex": 0,
            "width": 242,
            "height": 108,
            "selected": False,
            "data": {
                "type": "http-request",
                "title": "2 • Belgesel Sahne & Beat Zaman Çizelgesi",
                "method": "post",
                "url": "http://host.docker.internal:8099/run",
                "headers": "Content-Type:application/json",
                "params": "",
                "body": {
                    "type": "json",
                    "data": [
                        {
                            "id": "kv-node_stage_2",
                            "key": "",
                            "type": "text",
                            "value": '{\n  "stage": 2,\n  "folder_path": "{{#1792333503704.folder_path#}}"\n}',
                        }
                    ],
                },
                "authorization": {"type": "no-auth", "config": None},
                "variables": [],
                "timeout": {
                    "connect": 60,
                    "read": 1800,
                    "write": 1800,
                    "max_connect_timeout": 1800,
                    "max_read_timeout": 1800,
                    "max_write_timeout": 1800,
                },
                "retry_config": {"retry_enabled": False, "max_retries": 0, "retry_interval": 100},
                "ssl_verify": True,
                "selected": False,
            },
        },
        {
            "id": "node_stage_3",
            "type": "custom",
            "position": {"x": 1100, "y": 280},
            "positionAbsolute": {"x": 1100, "y": 280},
            "sourcePosition": "right",
            "targetPosition": "left",
            "zIndex": 0,
            "width": 242,
            "height": 108,
            "selected": False,
            "data": {
                "type": "http-request",
                "title": "3 • Görsel Materyaller & 2D/3D Animasyonlar",
                "method": "post",
                "url": "http://host.docker.internal:8099/run",
                "headers": "Content-Type:application/json",
                "params": "",
                "body": {
                    "type": "json",
                    "data": [
                        {
                            "id": "kv-node_stage_3",
                            "key": "",
                            "type": "text",
                            "value": '{\n  "stage": 3,\n  "folder_path": "{{#1792333503704.folder_path#}}"\n}',
                        }
                    ],
                },
                "authorization": {"type": "no-auth", "config": None},
                "variables": [],
                "timeout": {
                    "connect": 60,
                    "read": 1800,
                    "write": 1800,
                    "max_connect_timeout": 1800,
                    "max_read_timeout": 1800,
                    "max_write_timeout": 1800,
                },
                "retry_config": {"retry_enabled": False, "max_retries": 0, "retry_interval": 100},
                "ssl_verify": True,
                "selected": False,
            },
        },
        {
            "id": "node_stage_4",
            "type": "custom",
            "position": {"x": 1500, "y": 280},
            "positionAbsolute": {"x": 1500, "y": 280},
            "sourcePosition": "right",
            "targetPosition": "left",
            "zIndex": 0,
            "width": 242,
            "height": 108,
            "selected": False,
            "data": {
                "type": "http-request",
                "title": "4 • NVENC Final Video Render",
                "method": "post",
                "url": "http://host.docker.internal:8099/run",
                "headers": "Content-Type:application/json",
                "params": "",
                "body": {
                    "type": "json",
                    "data": [
                        {
                            "id": "kv-node_stage_4",
                            "key": "",
                            "type": "text",
                            "value": '{\n  "stage": 4,\n  "folder_path": "{{#1792333503704.folder_path#}}"\n}',
                        }
                    ],
                },
                "authorization": {"type": "no-auth", "config": None},
                "variables": [],
                "timeout": {
                    "connect": 60,
                    "read": 1800,
                    "write": 1800,
                    "max_connect_timeout": 1800,
                    "max_read_timeout": 1800,
                    "max_write_timeout": 1800,
                },
                "retry_config": {"retry_enabled": False, "max_retries": 0, "retry_interval": 100},
                "ssl_verify": True,
                "selected": False,
            },
        },
        {
            "id": "1792334372173",
            "type": "custom",
            "position": {"x": 1900, "y": 280},
            "positionAbsolute": {"x": 1900, "y": 280},
            "sourcePosition": "right",
            "targetPosition": "left",
            "zIndex": 0,
            "width": 242,
            "height": 170,
            "selected": False,
            "data": {
                "type": "end",
                "title": "Çıktı",
                "outputs": [
                    {"variable": "ses_durumu", "value_selector": ["node_stage_1", "body"], "value_type": "string"},
                    {"variable": "sahne_cizelgesi", "value_selector": ["node_stage_2", "body"], "value_type": "string"},
                    {"variable": "materyaller", "value_selector": ["node_stage_3", "body"], "value_type": "string"},
                    {"variable": "nihai_video", "value_selector": ["node_stage_4", "body"], "value_type": "string"},
                ],
                "selected": False,
            },
        },
    ],
    "edges": [
        {
            "id": "1792333503704-source-node_stage_1-target",
            "source": "1792333503704",
            "sourceHandle": "source",
            "target": "node_stage_1",
            "targetHandle": "target",
            "type": "custom",
            "zIndex": 0,
            "data": {"sourceType": "start", "targetType": "http-request", "isInIteration": False, "iteration_id": None, "isInLoop": False, "loop_id": None},
        },
        {
            "id": "node_stage_1-source-node_stage_2-target",
            "source": "node_stage_1",
            "sourceHandle": "source",
            "target": "node_stage_2",
            "targetHandle": "target",
            "type": "custom",
            "zIndex": 0,
            "data": {"sourceType": "http-request", "targetType": "http-request", "isInIteration": False, "iteration_id": None, "isInLoop": False, "loop_id": None},
        },
        {
            "id": "node_stage_2-source-node_stage_3-target",
            "source": "node_stage_2",
            "sourceHandle": "source",
            "target": "node_stage_3",
            "targetHandle": "target",
            "type": "custom",
            "zIndex": 0,
            "data": {"sourceType": "http-request", "targetType": "http-request", "isInIteration": False, "iteration_id": None, "isInLoop": False, "loop_id": None},
        },
        {
            "id": "node_stage_3-source-node_stage_4-target",
            "source": "node_stage_3",
            "sourceHandle": "source",
            "target": "node_stage_4",
            "targetHandle": "target",
            "type": "custom",
            "zIndex": 0,
            "data": {"sourceType": "http-request", "targetType": "http-request", "isInIteration": False, "iteration_id": None, "isInLoop": False, "loop_id": None},
        },
        {
            "id": "node_stage_4-source-1792334372173-target",
            "source": "node_stage_4",
            "sourceHandle": "source",
            "target": "1792334372173",
            "targetHandle": "target",
            "type": "custom",
            "zIndex": 0,
            "data": {"sourceType": "http-request", "targetType": "end", "isInIteration": False, "iteration_id": None, "isInLoop": False, "loop_id": None},
        },
    ],
    "viewport": {"x": 100, "y": 200, "zoom": 0.65},
}

features = {
    "file": {"image": {"enabled": False, "number_limits": 3, "transfer_methods": ["local_file", "remote_url"]}},
    "opening_statement": "",
    "suggested_questions": [],
    "speech_to_text": {"enabled": False},
    "text_to_speech": {"enabled": False, "language": "", "voice": ""},
    "retriever_resource": {"enabled": False},
    "sensitive_word_avoidance": {"enabled": False, "type": "", "configs": []},
}

graph_str = json.dumps(graph).replace("'", "''")
features_str = json.dumps(features).replace("'", "''")

sql = f"""
UPDATE workflows 
SET graph = '{graph_str}', features = '{features_str}', updated_at = NOW() 
WHERE app_id = 'ec7c95a5-7d4e-4fd4-b7e6-1b7ff6de8155';
"""

res = subprocess.run(
    ["docker", "exec", "-i", "docker-db_postgres-1", "psql", "-U", "postgres", "-d", "dify"],
    input=sql,
    capture_output=True,
    text=True,
    check=True,
)
print("Updated workflows:", res.stdout)
