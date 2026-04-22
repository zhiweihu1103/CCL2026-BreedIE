<div align="center">
<img src='https://github.com/user-attachments/assets/38baa5b6-b6c4-42a3-96ae-f5a300013b5c' alt='MGBIE' height='150px'>
</div>

# <p align="center"><font size=50><strong>[CCL2026 第一届杂粮育种信息抽取评测](https://github.com/zhiweihu1103/CCL2026-MGBIE)</strong></font></p>

<div align="center"> <img src='https://github.com/user-attachments/assets/aa11d15e-f55a-4b48-af90-b8be6e101a87' alt='山西省后稷实验室' height='90px'> &emsp;&emsp;&emsp;&emsp; <!-- Adds extra spacing between images --> <img src='https://github.com/user-attachments/assets/4d0aa98e-8b86-4d34-b8cd-1f65ec6256ed' alt='山西农业大学' height='90px'> &emsp;&emsp;&emsp;&emsp; <!-- Adds extra spacing between images --> <img src='https://github.com/user-attachments/assets/94aeaa28-45dc-446c-9a8d-9f39fc51bd44' alt='山西大学' height='90px'> &emsp;&emsp;&emsp;&emsp; <!-- Adds extra spacing between images --> <img src='https://github.com/user-attachments/assets/ebbb1edd-21db-4d6f-83b1-a161904461bd' alt='武汉大学' height='90px'> </div>

## 评测组织者
* 胡志伟（山西省后稷实验室、山西农业大学）
* 孔照胜（山西省后稷实验室、山西农业大学）
* 高建华（山西省后稷实验室、山西农业大学）
* 谭红叶（山西大学）
* 闫智超（山西大学）
* 李茹（山西大学）
* 谢倩倩（武汉大学）

## 联系人及联系方式
* 杨森杰（山西大学硕士生，yangsenjie1@sxu.edu.cn）

第二十五届中国计算语言学大会（The 25th China National Conference on Computational Linguistics, CCL 2026）将于2026年10月15至18日在湖北省宜昌市举行。中国计算语言学大会创办于1991年，由中国中文信息学会计算语言学专业委员会主办。经过30余年的发展，中国计算语言学大会已成为国内自然语言处理领域权威性最高、规模和影响最大的学术会议。作为中国中文信息学会（国内一级学会）的旗舰会议，CCL聚焦于中国境内各类语言的智能计算和信息处理，为研讨和传播计算语言学最新学术和技术成果提供了最广泛的高层次交流平台。

## 1 任务介绍
杂粮（如谷子、黍稷、高粱、燕麦、荞麦、各种食用豆等）育种领域相关信息长期以自然语言形式沉淀在论文、品种审定与登记材料、区域试验报告、栽培技术规程等文本中。这些文本记录了材料来源与系谱演化、目标性状及其测定结果，同时包含栽培管理与胁迫处理条件及其分子标记、基因位点和QTL等分子证据。由于杂粮育种文本专业术语密集，同一概念存在多种表述，材料名称与试验要素还会嵌套表达，导致关键信息难以稳定抽取并统一结构化，进而限制了知识检索、跨文献证据汇总与育种决策支持等应用。为推动信息抽取技术在杂粮育种知识管理与数据资源建设中的落地应用，提升育种信息整理与证据汇总的自动化水平，我们提出面向杂粮育种的信息抽取评测任务，并构建标注数据集，用于评估模型在育种语境理解、术语识别与结构化表达方面的能力。数据集来源于公开论文、品种认定与登记材料、区域试验报告和栽培技术文档等多类型文本，重点标注育种材料、系谱信息、关键性状指标、试验条件、对照关系及分子证据等核心要素，以评估系统对育种要素的识别能力与跨句信息组织能力。具体来说，本次杂粮育种信息抽取评测主要包含以下两个子任务：
* **子任务1：命名实体识别**：该任务要求从杂粮育种文本中自动识别并抽取关键实体，输出实体边界及实体类型标签，为后续结构化抽取提供基础。
* **子任务2：关系抽取**：该任务要求在已识别实体基础上抽取实体间语义关系，输出关系三元组，用于刻画育种知识链条中的系谱、性状表现、试验条件及其分子证据等内容。

## 2 评测数据
本次评测数据来自科研论文、育种报告等文本信息源，总规模为2,000条样本。为确保评估的科学性与可复现性，数据集划分为训练集、验证集和测试集三部分，样本数量分别为1,000条、400条和600条；评测流程分为A榜与B榜两个阶段，其中验证集用于A榜阶段的模型调试与初步排名，测试集用于B榜阶段的最终性能评估与结果确认。命名实体识别与关系抽取任务的数据标注字段说明如下：

### 2.1 命名实体识别任务

| 类型 | 英文（缩写） | 说明 | 示例 |
|------|-------------|------|------|
| 作物 | Crop (CROP) | 杂粮作物的物种或类别名称，用于指明研究对象 | 谷子 |
| 品种 | Variety / Cultivar (VAR) | 审定/登记/推广的具体品种名称或代号 | 晋谷21 |
| 性状 | Trait (TRT) | 表型/农艺/品质/抗性等性状名称 | 株高、千粒重 |
| 生育时期 | Growth Stage (GST) | 作物生长发育阶段节点 | 出苗期、拔节期 |
| 基因 | Gene (GENE) | 与性状相关的功能基因/候选基因名称 | Waxy |
| 数量性状位点 | QTL (QTL) | 与数量性状相关的遗传位点/区间标识 | qPH3.1 |
| 分子标记 | Molecular Marker (MRK) | 用于定位/选择的 SSR/SNP/Indel/KASP 等标记 | SSR-Xgwm20 |
| 染色体 | Chromosome (CHR) | 染色体编号或名称 | Chr1 |
| 育种方法 | Breeding Method (BM) | 育种或选择的技术路线/方法 | 杂交育种 |
| 亲本/杂交组合 | Parent / Cross (CROSS) | 父本/母本材料及其杂交组合表达 | A×B |
| 非生物胁迫 | Abiotic Stress (ABS) | 非生命因素引起的胁迫条件 | 干旱胁迫 |
| 生物胁迫 | Biotic Stress (BIS) | 生物因素引起的胁迫类型 | 螟虫、蚜虫 |

### 2.2 关系抽取任务（六类语义关系）

| 关系名称 | 英文（缩写） | 关系类型 | 说明 | 示例 |
|----------|-------------|----------|------|------|
| 包含 | CONTAINS (CON) | (CROP, VAR) | 品种属于某作物 | 晋谷21号属于谷子 |
| 采用 | USES (USE) | (VAR, BM) | 品种选育所用方法 | 晋谷21号采用杂交育种 |
| 具有 | HAS (HAS) | (VAR, TRT) | 品种具备或关注某性状 | 晋谷21号具有抗倒伏 |
| 影响 | AFFECTS (AFF) | (ABS/GENE/MRK/QTL, TRT) | 非生物胁迫、基因、分子标记或QTL对性状产生影响 | 干旱胁迫影响产量 |
| 发生于 | OCCURS_IN (OCI) | (TRT/ABS/BIS, GST) | 性状或胁迫发生于某生育时期 | 千粒重测定于成熟期 |
| 定位于 | LOCATED_IN (LOI) | (MRK/QTL/GENE, CHR) | 分子标记、QTL或基因定位于染色体或区间 | KASP_Chr2_15Mb定位于qYLD2.2 |

### 2.3 数据样例

本次评测提供了JSON 格式的数据集。以下为相应的数据样例：
```json
{
    "text": "A genome-wide association study analyzed 425 foxtail millet samples from Xinjiang Academy using 1,304,248 SNPs. 77 QTL regions were detected across three environments. Analysis of LD, genetic structure, clustering, and phylogeny showed regional differences among foxtail millet subgroups.",
    "entities": [
        {
            "start": 2,
            "end": 31,
            "text": "genome-wide association study",
            "label": "BM"
        },
        {
            "start": 45,
            "end": 59,
            "text": "foxtail millet",
            "label": "CROP"
        },
        {
            "start": 106,
            "end": 110,
            "text": "SNPs",
            "label": "MRK"
        },
        {
            "start": 115,
            "end": 126,
            "text": "QTL regions",
            "label": "QTL"
        }
    ],
    "relations": [
        {
            "head": "foxtail millet",
            "head_start": 45,
            "head_end": 59,
            "head_type": "CROP",
            "tail": "QTL regions",
            "tail_start": 115,
            "tail_end": 126,
            "tail_type": "QTL",
            "label": "CON"
        },
        {
            "head": "SNPs",
            "head_start": 106,
            "head_end": 110,
            "head_type": "MRK",
            "tail": "QTL regions",
            "tail_start": 115,
            "tail_end": 126,
            "tail_type": "QTL",
            "label": "LOI"
        }
    ]
}
```

### 2.4 数据说明
| 字段名称 | 类型 | 描述 |
|----------|------|------|
| `text` | string | 原始输入文本，用于实体识别和关系抽取 |
| `entities` | list | 文本中识别出的实体列表，每个对象包含以下属性： |
| `start` | int | 实体在文本中的起始字符索引 |
| `end` | int | 实体在文本中的结束字符索引 |
| `text` | string | 实体文本内容 |
| `label` | string | 实体类别，如 `CROP`、`QTL` 等 |
| `relations` | list | 文本中实体之间的关系，每个对象包含以下属性： |
| `head` | string | 关系起始实体文本 |
| `head_start` / `head_end` | int | 关系起始实体在文本中的索引 |
| `head_type` | string | 关系起始实体类别 |
| `tail` | string | 关系目标实体文本 |
| `tail_start` / `tail_end` | int | 关系目标实体在文本中的索引 |
| `tail_type` | string | 关系目标实体类别 |
| `label` | string | 关系类型，如 `CON`（包含）、`LOI`（定位于）等 |


### 2.5 结果提交：

1. 提交的结果文件必须遵循数据样例的 JSON 格式，文件中每一条数据都应是一个 JSON 对象，并且包含样例中列出的所有字段。如下：
```json
{
    "text": "A genome-wide association study analyzed 425 foxtail millet samples from Xinjiang Academy using 1,304,248 SNPs. 77 QTL regions were detected across three environments. Analysis of LD, genetic structure, clustering, and phylogeny showed regional differences among foxtail millet subgroups.",
    "entities": [
        {
            "start": 2,
            "end": 31,
            "text": "genome-wide association study",
            "label": "BM"
        },
        ...
    ],
    "relations": [
        {
            "head": "foxtail millet",
            "head_start": 45,
            "head_end": 59,
            "head_type": "CROP",
            "tail": "QTL regions",
            "tail_start": 115,
            "tail_end": 126,
            "tail_type": "QTL",
            "label": "CON"
        },
        ...
    ]
}
```
2. 将结果文件直接压缩为 `submit.zip`。  
3. 提交时请确保上传的文件名为 `submit.zip`。
   
## 3 赛道设置

本次评测设置两个赛道，分为不微调和微调赛道。两条赛道的评分指标相同，最终榜单各自独立排名。

| 赛道        | 允许资源/方法 |
|------------|----------------|
| Track-A（不微调） | 不允许对模型参数进行微调，可以使用的方法包括 Prompt Engineering、In-Context Learning、RAG 等|
| Track-B（微调）   | 允许在官方提供的数据集上微调模型参数 |

**注意**：
- 两个赛道对于模型参数要求如下：
- Track-A 赛道不限制模型选型和参数规模；
- Track-A 赛道允许使用外部的数据，但最后必须确切的提供数据源以及对应外部数据；
- Track-B 赛道限制模型参数不超过7B，按通常认知的7B级别计算，而非绝对数值严格限制，因此选手可选择主流的7B级开源模型进行微调；
- Track-B 赛道要求在开发阶段采用的策略不会改变最终提交模型的单模型属性和参数规模。

## 4 评价标准

本次评测的两个任务（命名实体识别和关系抽取）均采用 **Precision**、**Recall** 和 **F1-Score** 作为评价指标，具体说明如下：

- **Precision（精确率）**  
  表示模型预测为正样本的实体或关系中，真正正确的比例。  
  计算公式：Precision = TP / (TP + FP)
- **Recall（召回率）**  
  表示模型正确预测出的实体或关系占所有实际存在正样本的比例。  
  计算公式：Recall = TP / (TP + FN)

- **F1-Score（F1 分数）**  
  Precision 与 Recall 的调和平均值，用于综合衡量模型的准确性和完整性。  
  计算公式：F1 = 2 * (Precision * Recall) / (Precision + Recall)

## 5 榜单说明

#### NER 评分：
$$
\text{Score}_{\text{NER}} = 0.5 \times F1 + 0.25 \times Precision + 0.25 \times Recall
$$

#### RE 评分：
$$
\text{Score}_{\text{RE}} = 0.5 \times F1 + 0.25 \times Precision + 0.25 \times Recall
$$

#### 最终榜单分数：
$$
\text{Total Score} = 0.4 \times \text{Score}_{\text{NER}} + 0.6 \times \text{Score}_{\text{RE}}
$$

**注意** ： 
- Track-A 和 Track-B 将分别发布综合榜单。每条赛道的奖项设置如下：一等奖 1 个，二等奖 2 个，三等奖 3 个。

## 6 Baseline
Baseline性能表现：
| Track   | Score  |
|---------|--------|
| Track-A | 0.351  |
| Track-B | 0.340  |

## 7 评测报名
- 本次评测任务将通过阿里天池平台进行-[报名入口](https://tianchi.aliyun.com/competition/entrance/532465)

## 8 评测赛程

- **2026年2月**：评测任务发布 & 宣传  
- **2026年4月6日**：训练集、测试A榜（验证集）数据发布
- **2026年6月18日**：测试A榜 Leaderboard 发布  
- **2026年6月24日**：测试B榜（测试集）数据发布、Leaderboard 发布  
- **2026年6月30日**：评测任务结束  
- **2026年7月1日–9日**：任务组织者、获奖队伍撰写技术报告  
- **2026年7月10日**：提交技术报告  
- **2026年7月25日**：评测论文审稿 & 录用通知  
- **2026年8月15日**：Camera-ready 版本提交  
- **2026年9月15日**：论文排版 & 提交 ACL/CCL Anthology  
- **2026年10月**：会议召开

## 9 论文格式

- 提交论文的格式统一使用 CCL 2026 的论文模版（[直接下载](http://cips-cl.org/static/CCL2026/templates/ccl2026_chinese_template.zip)）。
- 论文可由中文或英文撰写，最多 6 页正文，参考文献页数不限。
- 采用双盲审稿，不可出现作者姓名和单位的信息，不符合要求会被拒稿。
- 报告应至少包含以下四个部分：
  1. 模型介绍
  2. 评测结果
  3. 结果分析与讨论
  4. 参考文献
  
## 10 资助情况
本届评测将设置一、二、三等奖，由中国中文信息学会提供荣誉证书。

## 微信交流群

欢迎各位参赛同学加入微信交流群
<div align="center">
  <img src="./微信交流群.png" alt="Logo" width="300"/>
</div>
