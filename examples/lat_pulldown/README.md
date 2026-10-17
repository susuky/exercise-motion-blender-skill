先在 skill 根目錄執行 `blender -b --python rebuild_human.py`，此範例會使用共用的 `assets/improved_human.blend`。

# 坐姿寬握滑輪下拉

960 × 960，80 幀、20 fps、4 秒無限循環。白底，畫面沒有文字。

## 檔案

- `output/lat_pulldown.gif`：完整動畫
- `output/representative.png`：拉到上胸位置的代表幀
- `output/lat_pulldown.blend`：完整人體、器材與動畫
- `output/qa_hand_*`：左右手在上端、中段與下端的握持特寫
- `output/qa_seat_thigh_contact.png`：座墊與膝墊接觸特寫
- `output/qa_chest_bar_clearance.png`：胸前槓距側視圖
- `output/animation_contact_sheet.jpg`、`output/all_80_frames.jpg`：動作檢視圖
- `output/all_frame_geometry_validation.json`、`output/gif_validation.json`：逐幀檢查數值

## 重製

環境：Blender 4.3.2；Python 3、Pillow、NumPy。

    blender -b -t 3 --python build_scene.py
    blender -b -t 3 --python scripts/render.py
    blender -b -t 3 --python scripts/render.py -- --qa
    blender -b -t 2 --python scripts/validate_all.py
    python package.py

已有完整 `.blend` 時，可直接從第二行重新渲染。

## 模型與動作

使用共用連續蒙皮人體，保留 856,194 個皮膚頂點、胸腹與四肢肌肉浮雕、肌束紋理和獨立厚度短褲。本版本將主要紅色標示配置到背闊肌與側腹背部區域。

人體固定坐在座墊上，雙腳落地，兩側膝墊靠近大腿上表面。雙手寬握 87 公分，指骨沿 29 mm 握把圓周求解；手掌方向隨前臂旋轉。兩節手臂保留原始骨長，回到上方時肘角約 168 度，往下拉至上胸前方。向下與回程各 2 秒，端點速度為零。

器材包含座椅、膝墊、上方滑輪、牽引鋼索、導桿、固定配重與升起的配重。活動鋼索保持拉直，配重升降依鋼索實際長度變化連動。

全身與器材保持在同一固定視角內。使用 Workbench 渲染，所有材質與頂點顏色保存在 Blender 檔，無外部貼圖或網路相依。

## 資產

基礎人體為 MPFB 衍生 CC0 資產，授權全文位於 `../../assets/LICENSE.ASSETS.md`。`assets/improved_human.blend` 保存已改善的人體、衣物與肌肉細節，`build_scene.py` 從該檔重建此次器材與動作。
