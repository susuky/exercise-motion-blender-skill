# 深蹲：肌群分工配色

紅色＝主要目標／主動肌群；藍色＝協同與穩定肌群；其餘灰色。肌群分類維持整個動作循環；色彩明暗來自原有肌束、浮雕與光照。

## 深蹲

- **紅：股四頭肌。** 前側與前外側大腿肌腹。下蹲時控制膝屈曲，上蹲時伸膝；膝蓋與肌腱末端保留灰色。
- **紅：臀大肌。** 後側臀部肌腹。下蹲控制髖屈曲，上蹲伸髖。獨立黑短褲自然遮住此區。
- **藍：大收肌。** 後內側大腿區域，協助本片深蹲的髖伸展。肌腹大部分在短褲下；深蹲深度與髖角度會改變它的角色。
- **藍：腿後肌群。** 後側大腿肌腹，作為髖膝協調與穩定的協同肌群。
- **藍：豎脊肌。** 脊柱兩側狹長區域，整段動作抵抗軀幹前屈。
- **藍：腹直肌與腹外斜肌。** 腹前與側前方，維持軀幹支撐；胸肌保留灰色。
- **藍：小腿蹠屈協同肌群。** 小腿中下段後側的腓腸肌下部與比目魚肌區域，協助踝部控制；比目魚肌上部位於腓腸肌深層。跟腱、腳踝與脛骨前側保留灰色。

代表幀位於深蹲底部。原場景檢查的髖部比膝部低 4.49 公分，因此將大收肌列為髖伸展協同肌群。

## 遮罩與重製

所有遮罩以人體未變形的綁定座標建立。四肢以骨頭起點、骨軸比例與前後／內外側角度定位；軀幹使用綁定姿勢的解剖區域。每個語意遮罩保留為 Blender 的 role_* 頂點屬性。

重製程式只更新皮膚的 Anatomical fibres 顏色與新增語意遮罩。人體網格、肌肉浮雕、衣物、器材、骨架、所有動畫曲線、攝影機與渲染設定維持原值。黑短褲是獨立、具有厚度的物件。

共同線性 RGB 色票：紅 [0.72, 0.045, 0.03]；藍 [0.035, 0.18, 0.72]；灰 [0.73, 0.75, 0.76]。

## 參考資料

- Robertson 等，Lower extremity muscle functions during full squats：完整深蹲中的臀大肌、股四頭肌、比目魚肌及雙關節肌功能。https://pubmed.ncbi.nlm.nih.gov/19075302/
- Ko 等，Comparison of hip extensor muscle activity including the adductor magnus during three prone hip extension exercises：大收肌的髖伸展功能。https://pubmed.ncbi.nlm.nih.gov/29601221/
- Myer 等，The back squat: A proposed assessment of functional deficits and technical factors that limit performance：深蹲中的臀肌與脊柱旁肌群功能。https://pmc.ncbi.nlm.nih.gov/articles/PMC4262933/
