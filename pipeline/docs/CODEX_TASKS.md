# 推薦交給 Codex 的工作順序

## Task 1. 建立動作資料規格
- 整理 canonical exercise names
- 建立 variation taxonomy
- 對應 equipment / muscles / movement patterns

## Task 2. 建立 motion spec 產生器
輸入：
- 動作名稱
- 器材
- 文字說明
- optional: GIF / 影片

輸出：
- motion spec JSON
- confidence / assumptions

## Task 3. 建立 Blender adapter
- motion spec -> rig controls
- equipment builders
- camera / light presets
- render settings

## Task 4. 驗證工具
- joint limits
- object penetration check
- grasp distance check
- cycle continuity check

## Task 5. 批次生成
- 先 20 個動作
- 再擴到 100
- 最後再到 1324

## 成功標準
- 同一族動作可以共用模板
- 不需逐幀手工修 keyframe
- 新動作只要調整 spec，不必重寫整個腳本
