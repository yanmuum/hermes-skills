# NDA / Confidentiality Agreement Review Framework

When reviewing an NDA (保密协议) or similar contract, especially for individual/natural-person signatories, use the following structured analysis format with 🔴/🟡/🟢 risk indicators.

## Risk Indicator System

| Icon | Meaning | Action |
|------|---------|--------|
| 🔴 | **High Risk** — must negotiate/change | Core issue that creates significant legal or financial exposure |
| 🟡 | **Medium Risk** — strongly advise negotiation | Concerning but may be negotiable or partially acceptable |
| 🟢 | **Low/No Risk** — standard practice | Normal industry language, no change needed |

## Standard Analysis Dimensions (in order)

### 1. Intellectual Property Ownership (知识产权归属)
**Red flags:**
- All成果 unconditionally belong to the company (甲方) — "一网打尽" clause
- Short or no window to declare pre-existing IP (e.g., 30 days) — burden-shifting to individual
- Personal background IP treated as company confidential information (paradox: company claims individual's own pre-existing IP as its "confidential information")
- No distinction between: work product (company resources + project) vs. independent creation
- No license-back provision: company can use individual's background IP beyond project scope without restriction
- Broad catch-all scope ("技术成果、软件代码、研究报告、课程体系、通证经济设计方案等")
- **Web3/crypto context**: watch for "智能合约代码","私钥管理方案","多签钱包地址","链上治理策略","通证经济模型" — these are core IP, loss of ownership is costly

**Typical ask:** Clarify that (a) project-specific work using company resources → company IP, (b) independent work outside project scope → individual IP, (c) remove punitive declaration deadlines (negotiate 90 days instead of 30), (d) add license-back: company gets limited license to individual's Background IP for project only, not perpetual.

### 2. Liquidated Damages / Penalty Clauses (违约金)
**Red flags:**
- Fixed amount penalties (e.g., ¥1,000,000) on individuals — disproportionate
- "Plus all actual losses" on top of penalty — double punishment
- No cap or proportionality to actual damages

**Legal basis:** Under PRC Civil Code Art. 585, courts can reduce penalties exceeding 30% of actual loss. But the clause alone creates litigation leverage against the individual.

**Typical ask:** Reduce to reasonable amount (e.g., ¥50k–¥100k) or peg to actual damages only; add mutual liability cap.

### 3. Confidential Information Scope (保密范围)
**Red flags:**
- Overly broad definition ("including but not limited to") without exclusions
- Individual's own personal information or background IP listed as "company confidential"
- No carve-out for: publicly available info, independently developed info, info received from third parties without restriction

**Typical ask:** Add exclusions list; remove personal info/background IP from company's confidential information.

### 4. Dispute Resolution / Venue (争议解决)
**Red flags:**
- Arbitration in a third location (not either party's domicile)
- Company's home city vs. individual's remote city → significant cost disadvantage

**Typical ask:** Negotiate venue to individual's domicile or a mutually convenient location; or change to court litigation in individual's city.

### 5. Duration / Term (保密期限)
**Red flags:**
- Excessively long post-termination period (5+ years for general info)
- No distinction between trade secrets (indefinite) and general confidential info

**Note:** 2-5 years is common for NDAs. Flag only if unusually long or if it restricts the individual's future work in the same field.

### 6. One-Sided Obligations
**Red flags:**
- Company has no reciprocal confidentiality obligations
- Individual must return materials but no mention of company deleting individual's personal data
- No limitation on company's use of individual's personal information

## Output Format Template

### Chat Output (Quick Review)

```markdown
## 🔴 风险：[Clause Title]（第X条）

> [Exact quote from contract]

**风险分析：**
- [Risk description point 1]
- [Risk description point 2]

**修改建议：**
- [Suggestion 1]
- [Suggestion 2]
```

Then a summary table:

| 优先级 | 条款 | 问题 |
|--------|------|------|
| **必须改** 🔴 | [Clause] | [Why] |
| **建议改** 🟡 | [Clause] | [Why] |
| **注意即可** 🟢 | [Clause] | [Why] |

### Professional Document Output (User Request for Download)

When user asks for a downloadable professional report, generate a `.docx` file:

**Structure:**
1. **封面/标题**: 法律审查意见书（居中）
2. **基本信息**: 委托方、审阅文件、相对方、日期、保密等级
3. **审查结论概要**: Risk summary table (🔴/🟡/🟢 per clause)
4. **逐条详细审查意见**: Each clause analyzed with:
   - 原条款摘录（灰色斜体引用）
   - 风险分析（bullet points）
   - 修改建议（绿色突出）
5. **谈判优先级及策略建议**: 第一优先级（必须改）→ 第二优先级（尽力争取）→ 谈判底线
6. **免责声明**

**Technical setup for python-docx:**
```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

# Chinese font setup
style = doc.styles['Normal']
style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

# Page margins (A4)
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.17)
section.right_margin = Cm(3.17)
```

Save to `/tmp/法律审查意见书_<协议名>.docx` and send via: `MEDIA:/tmp/法律审查意见书_<协议名>.docx`
