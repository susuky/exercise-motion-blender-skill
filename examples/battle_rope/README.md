先在 skill 根目錄執行 `blender -b --python rebuild_human.py`，此範例會使用共用的 `assets/improved_human.blend`。

# 交替甩戰繩 · xhigh

960 × 960 白底全身動畫，4 秒無限循環。左右手以相反相位上下揮動，波形沿繩向固定地錨傳遞。

人體沿用改良版連續皮膚網格：856,194 個頂點、立體肌肉起伏與肌纖維細節、獨立黑色短褲、逐指握把姿勢。腳掌固定，屈膝站姿與軀幹保持穩定。兩段工作繩以同一條繩的 U 形中段繞過地錨柱。

## 交付檔案

- output/battle_rope_xhigh.gif：96 個影格，總長 4,000 ms，無限循環
- output/battle_rope_representative.png：代表影格
- output/battle_rope_xhigh.blend：完整模型、動畫、相機與材質
- qa/QA_summary.md：實際檢查項目與數值
- qa/all_24_frames.jpg：24 個獨特姿勢的檢查總覽
- qa/scene_validation.json：逐影格握把與繩索接點檢查

## 從小型來源包重建

需要 Blender 4.3.2、Python 3、Pillow 與 NumPy。先在來源包的目錄執行：

    blender -b -t 4 --python rebuild_improved_human.py
    blender -b -t 4 --python build_battle_ropes.py
    blender -b -t 1 --python validate_battle_ropes.py
    python package.py

第一步會由 assets/base_human.blend 重建帶有肌肉細節的 assets/improved_human.blend。第二步建立器材與動作並輸出 24 個獨特影格。GIF 包裝會重複四次；Blender 檔案則以循環曲線播放 96 個影格。

若已有完整 Blender 檔案，可直接執行：

    blender -b -t 4 --python render_saved.py
    python package.py

## 動作與幾何

- 24 fps，每秒一個左右交替週期
- 逐影格肩、肘、腕位置解算，保留骨段長度
- 指節依圓柱握把彎曲；手、握把與繩端共用同一組姿勢資料
- 繩波相位隨距離延遲，波峰持續朝地錨方向移動
- 波幅在地錨處收斂，固定端位置不變
- 第 25 個控制影格與第 1 個完全相同，以 24 影格週期循環

## 資產授權

基礎人體來源與授權記錄保留於 assets/LICENSE.ASSETS.md。
