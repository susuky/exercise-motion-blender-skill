# 側平舉肌肉模型樣本：xhigh

## 成品

- `output/lateral_raise_xhigh.gif`：960 × 960，36 幀循環動畫
- `output/representative.png`：抬臂頂端代表幀
- `output/lateral_raise_xhigh.blend`：完整連續蒙皮人體、骨架、手指、短褲、啞鈴與動畫
- `output/torso_check.png`、`output/hand_l_check.png`、`output/hand_r_check.png`：胸腹及左右手近照
- `output/animation_contact_sheet.jpg`：動作檢視圖
- `output/scene_validation.json`、`output/frame_bounds.json`：逐幀幾何與畫面邊界檢查

## 重新製作

環境：Blender 4.3.2；Python 套件 Pillow、NumPy。

    blender -b -t 8 --python build_render.py
    python package.py

只製作關鍵幀與近照：

    blender -b -t 8 --python build_render.py -- --stills
    python package.py

直接重新渲染已儲存的場景：

    blender -b -t 8 --python render_saved.py
    python package.py

重新檢查全部 36 幀的抓握幾何：

    blender -b -t 2 --python validate_scene.py

## 模型與動畫

人體使用連續蒙皮表面，胸肌為淺扇形浮雕，腹肌為三組寬平肌腹，肩臂與大腿肌束沿各自骨骼方向變形。纖維顏色與微小起伏直接保存在模型中。黑色短褲是有厚度、具有獨立邊緣的蒙皮衣物。

動畫為 12 fps、3 秒的側平舉，保留完整關鍵影格。四指依照共同圓柱求解各節指骨位置，配合 29 mm 直徑握把。左右手以鏡像方式處理，手腕與前臂保持連續。

使用 Workbench CPU 渲染。檔案不依賴外部材質貼圖或網路服務，所有路徑皆相對於本目錄。

## 資產來源

基礎人體為 MPFB 衍生資產。授權為 CC0 1.0，全文保留於 `assets/LICENSE.ASSETS.md`。本樣本的肌肉浮雕、纖維、短褲、握持與渲染設定均可由隨附腳本重現。
