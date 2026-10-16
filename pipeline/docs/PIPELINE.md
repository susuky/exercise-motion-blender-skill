# 建議流程

## A. 不要做的流程

### 不建議
`來源 GIF -> pose estimation -> 完整重建 -> 換個模型重渲染`

原因：
- 太像原素材的衍生重製
- 逐幀擬合會把原始創作表達一起帶進去
- 難保開源與商業化風險

## B. 建議流程

### Step 1. 動作理解（semantic understanding）
把來源資料理解成「動作規格」，而不是畫面本身。

#### 需要抽出的資訊
- exercise_id / canonical_name
- equipment_type
- body_setup（站、坐、臥、跪、俯身）
- laterality（雙側 / 單側 / 交替）
- movement_pattern（hinge / squat / horizontal press / vertical pull ...）
- start_pose
- end_pose
- phase breakdown（向心、頂點、離心、停頓）
- primary joints used
- contact points
- range-of-motion intent
- camera preference

這一層可以由：
- Codex 根據文字資料生成初版
- 使用者提供 GIF / 影片輔助理解
- 人工校正

### Step 2. 動作規格（motion spec）
產生一份中立、可重複利用的 JSON。

這份 JSON 不應該包含「每一幀長怎樣」，而應該描述：
- 關節軌跡目標
- 節奏與 phase
- 接觸點與約束
- 鏡頭與渲染偏好

### Step 3. Rig 與器材生成
- 人體：MPFB / 自有 rig
- 器材：Blender Python 建模（槓鈴、啞鈴、長椅、滑輪、拉把）
- 接觸點：手掌 / 足底 / 背部 / 臀部

### Step 4. 求姿勢
優先建議：
1. phase-by-phase target poses
2. IK 求解
3. 限制關節角度
4. 必要時做簡單碰撞修正

### Step 5. 驗證
每一幀驗證：
- 抓握點距離是否超標
- 關節是否超範圍
- 器材是否穿模
- 左右是否對稱（雙側動作）
- 動作週期是否閉環（做成循環 GIF 時）

### Step 6. 渲染
- PNG sequence
- MP4（預設主輸出）
- GIF / Animated WebP（預覽）

## C. 最務實的開發順序

### Phase 1: Human-in-the-loop
給 Codex 一段影片 / GIF，再由它輸出 motion spec 草稿，最後人工修正。

### Phase 2: Template families
針對一整族動作共用模板：
- curl family
- lateral raise family
- squat family
- press family
- row family
- deadlift family

### Phase 3: Full generation
Codex 自動產生動作規格 + Blender 批次輸出。

## D. 為什麼這條路比直接抓 GIF 更好
- 技術上更穩定
- 法務上更乾淨
- 未來可切換不同人體模型與視角
- 可同時輸出 GIF、MP4、骨架資料、教學圖
