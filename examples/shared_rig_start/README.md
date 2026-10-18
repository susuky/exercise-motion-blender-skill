# 共用肌肉人體起點

先在 repo 根目錄建立一次人體，之後每個新動作共用同一資產：

```bash
blender -b --python rebuild_human.py
blender -b --python examples/shared_rig_start/build_scene.py
```

已有 `improved_human.blend` 時可用 `HUMAN_BLEND=/path/to/improved_human.blend`；不會重新生成人體。這個範例保存中立姿勢 `.blend` 與資產驗證 JSON，尚未包含器材、動作或成品渲染。

新動作使用根目錄 `shared_human.load_shared_human()`，只需另外定義：

1. 動作：從 `human.rest` 複製完整骨骼矩陣，以 armature object space 求解後傳入 `human.apply(pose)`；逐幀插入 keyframe。`human.bones` 提供原骨架尺寸。
2. 器材：在同一場景加入網格、鋼索、握把與相應接觸求解。
3. 肌群：loader 先把舊紅／藍遮罩恢復灰色並保留肌束明暗，再依動作設定經核對的 rest-space 遮罩。完整解剖分割與自動肌群映射尚未提供。

Loader append 原始 `Human`、`Human.rig`、`Black shorts`，保留網格、權重、材質、肌束頂點色與衣物厚度；不清空現有場景，遇到同名人體會報錯。人體與短褲沿用同一 Armature，短褲的 preserve-volume 設定會與人體對齊。`expected_sha256=` 可固定經檢查的資產版本，回傳 `human.report` 記錄實際 checksum、頂點色屬性及逐頂點有效變形權重覆蓋。只使用可信任的 `.blend`。

每個動作仍需完整高模接觸、衣物、握持與視覺檢查。這些結構檢查不代表動畫驗收通過。

## 低模代理實驗

可選預覽：

```bash
blender -b --python examples/shared_rig_start/build_scene.py -- --preview-proxy
```

`experiments/shared_proxy.py` 的 `create_shared_proxy(human, ratio=0.01)` 從原始rest網格複製再減面，權重經 Blender 減面插值；回傳代理物件與實測建置統計。預設代理在viewport及render均隱藏；上述範例只切換viewport為低模，渲染仍用原高模。產生時保留原選取、active物件、網格與可見性。對代理有需求時才建立一次並重用；不會加速本身的高模碰撞檢查。

低模代理若用於預覽或碰撞候選篩選，必須與高模引用同一個 `human.rig`，使用一致的權重傳遞與蒙皮方法。不能另建骨架複製姿勢後假定等價。低模表面不是高模的保守包絡，單靠低模無交疊不能判定高模無穿模；未剔除候選仍須回到原始高模精查。目前不將代理碰撞或任何加速比列為正式預設。

另有三個代表姿勢的高模三角分群粗查實驗：含共用場景更新／網格提取約1.58倍；加上一次低模建置約1.31倍，結果與原法相同。收益來自高模保守分群粗查，並非低模取代高模；完整81姿勢尚未驗證。本共用起點只收入可獨立使用的預覽代理，未接入該碰撞加速器。

## 測試

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s pipeline/tests -v
blender -b --python-exit-code 1 --python tests/blender_shared_human.py
# 可選：會建置一次低模代理，驗證共用骨架及屈肘變形
blender -b --python-exit-code 1 --python tests/blender_shared_proxy.py
```

Blender 測試使用已存在的人體資產，檢查 checksum、載入時保留既有場景、單一骨架、rest/平移姿勢、65°屈肘與25°屈髖、全骨骼矩陣、evaluated 人體／短褲與原姿勢介面的數值一致性，以及錯誤輸入；不重建人體。`pipeline/` 的規格資料仍未自動對接到此骨架。
