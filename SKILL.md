---
name: exercise-motion-blender-pipeline
description: 從健身動作描述或參考媒體建立 Blender 人體與器材動畫，使用連續蒙皮肌肉人體，輸出白底全身 GIF。適用於健身動作示範、人體姿勢與器材連動製作。
---
# 健身動作 Blender Pipeline

## 本版的視覺基準

先在根目錄執行 `blender -b --python rebuild_human.py`，再沿用產生的 `assets/improved_human.blend` 的人體、骨架、肌肉浮雕、頂點色與獨立短褲。先看 `assets/*_reference.png` 的三張成品。本版視覺水準是交付底線；提高速度應靠重用資產、快取與排程，不能自行降低成品畫質。

- 全身連續蒙皮人體，有頭部、臉、手掌、五指與腳趾。
- 灰白皮膚、自然肌肉體積及方向性肌束細紋；胸肌寬平扇形，腹肌三組淺肌腹。
- 黑色短褲具獨立網格、蒙皮、厚度及褲管邊緣。
- 手指真正握住器材，手腕與前臂方向連續。
- 白底、固定鏡頭、全身與主要器材完整入鏡，圖片無文字。
- GIF 預設 960×960，約 3–4 秒循環，依動作選擇足夠的獨特影格。側平舉現成例為 12 fps，滑輪下拉為 20 fps，戰繩為 24 fps。

製作前讀 [人體與畫質設定](references/human-and-render-quality.md)。動作與驗收讀 [動作接觸檢查](references/motion-and-contact.md)。

## 選擇起點

1. 新動作優先載入已改善人體，保留網格、材質、頂點色、骨架與短褲，重建器材及動作。
2. 手持器材：參照 `examples/xhigh/build_render.py` 的手指圓柱求解、左右手及骨架設定。
3. 繩索波動：參照 `examples/battle_rope/build_battle_ropes.py`，及其人體重建腳本。
4. 坐姿滑輪器材：參照 `examples/lat_pulldown_xhigh/build_scene.py` 的座椅、膝墊、鋼索與配重連動。
5. 舊版動作規格、插值與驗證工具保留於 `pipeline/`。其預覽人體不是本版視覺交付路徑。舊說明位於 `references/legacy-motion-pipeline.md`，其中通用能力敘述需按實際程式與個別動作測試確認。

## 製作與交付

- 先用完整畫質檢查起點、中段、終點及手部近照，再渲染完整循環，減少返工。
- 檢查全部影格總覽、關鍵幀與握持近照；針對本動作檢查穿模、腳底接地及器材連動。
- 渲染、GIF 編碼、封裝分開，避免改封裝就重新建模或渲染。
- 交付 GIF、代表 PNG、可重建來源；需要編輯時附完整 `.blend`。
- QA 記錄測試範圍及數值；只有已執行檢查才標示通過。

## 使用現成範例

環境基準：Blender 4.3.2、Python 3、Pillow、NumPy。每個範例的 README 提供其執行命令。先在範例目錄執行，路徑以腳本所在目錄解析。現成資產包含於 ZIP，無須重新下載人體。
