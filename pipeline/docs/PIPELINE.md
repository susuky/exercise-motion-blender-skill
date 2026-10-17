# 動作資料工具

提供動作規格驗證、關節軌跡插值、運動學與器材分類，供製作動作時參考。這些資料尚未自動套用到肌肉人體骨架；動畫製作使用根目錄 SKILL.md 與 examples/ 的流程。

在儲存庫根目錄執行：

```bash
python pipeline/python/validate_motion_spec.py pipeline/samples/dumbbell_lateral_raise.motion_spec.json
python pipeline/python/interpolate_motion.py pipeline/samples/dumbbell_lateral_raise.motion_spec.json /tmp/lateral_raise.expanded.json
python -m unittest discover -s pipeline/tests -v
```

- `schemas/motion_spec.schema.json`：動作規格欄位
- `samples/`：三個動作規格範例
- `python/validate_motion_spec.py`：時序、關節範圍、接觸與循環檢查
- `python/interpolate_motion.py`：展開逐幀資料
- `python/kinematics_engine.py`：正向與反向運動學
- `python/equipment_registry.py`：器材類別
