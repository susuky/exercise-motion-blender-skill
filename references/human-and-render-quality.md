# 人體與畫質設定

## 可重用的人體

在根目錄執行 `blender -b --python rebuild_human.py`，會從隨附基礎網格產生 `assets/improved_human.blend`，保留本次 xhigh 的肌肉與短褲設定。從範例載入方式取得 Human、Human.rig 與短褲相關物件，清除舊動作和器材後重新設定。保留蒙皮權重與 rest pose；不要用圓球、膠囊或分段人偶替代。

人體製作來源保留於 `examples/xhigh/build_render.py` 與 `examples/battle_rope/rebuild_improved_human.py`。基礎人體與 CC0 授權文字隨範例附上。已改善模型約 856,194 個皮膚頂點；載入既有資產比每個動作重新細分雕刻更有效率。

胸肌是淺扇形起伏，腹肌是三對寬平肌腹，肩臂及大腿有沿局部骨骼方向的纖維。線條與陰影應隨皮膚變形。紅色肌群標示需依動作重新配置，目前範例使用程序化區域遮罩，不是完整的解剖肌群分割。避免把整片肩胸或側腹直接當成精確肌群。

短褲為獨立蒙皮殼體，保持厚度、腰口和褲管。屈髖屈膝時檢查衣物與大腿交界。

## 已使用的渲染參數

- engine: BLENDER_WORKBENCH
- resolution: 960 × 960，100%
- light: STUDIO；studio_light: studio.sl
- studio light rotation Z: 0.25
- color_type: VERTEX
- background: WORLD，白色；film_transparent: false
- shadows、cavity、specular highlights: enabled
- cavity_type: BOTH
- curvature ridge/valley: 0.45 / 0.55
- cavity ridge/valley: 0.4 / 0.5
- object outline: disabled
- render_aa: 8
- view_transform: Standard；exposure: 0.28
- 單幀 PNG；GIF 使用一致調色盤與合理的影格時間，確認無閃爍。

這是現成側平舉的實際參數。每個新場景仍需檢查取景和局部對比。鏡頭需涵蓋全身與動作的最大器材範圍，不能靠縮小人體到難以辨認來塞入器材。
