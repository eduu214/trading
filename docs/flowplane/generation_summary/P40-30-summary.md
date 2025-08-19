# Batch Processing Summary

**Generation Date:** 2025-08-15T05:08:08.582Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/alphastrat/40-design
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Create Feature Technical Architecture

## Processing Statistics

- **Total Items:** 6
- **Successful:** 6
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 82.9 seconds
- **Processing Speed:** 4.3 items/minute
- **Token Throughput:** 141.527 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 78
- **Total Output Tokens:** 11,659
- **Total Tokens:** 11,737

### Cache Performance
- **Cache Creation Tokens:** 17,435
- **Cache Read Tokens:** 87,175
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 78,457.5 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 13
- **Average Output Tokens:** 1,943

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 20-2001-architecture.md | Project | ✅ Yes | 6 | 83% reuse |
| 30-2001-design-system.yaml | Project | ✅ Yes | 6 | 83% reuse |
| 30-3001-infrastructure-registry.yaml | Project | ✅ Yes | 6 | 83% reuse |
| 30-4001-requirements-catalog.md | Project | ✅ Yes | 6 | 83% reuse |
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 6 | 83% reuse |

### Cache Statistics
- **Documents Processed:** 5
- **Cacheable Documents:** 5 (100%)
- **Total Document Uses:** 30
- **Cached Document Uses:** 30 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.1749
- **Cache Write Cost:** $0.0654
- **Cache Read Cost:** $0.0262

### Total Cost
- **Total Cost:** $0.2664
- **Average Cost per Item:** $0.0444

### Cache Savings
- **Input Cost Without Caching:** $0.3138
- **Input Cost With Caching:** $0.0915
- **Cache Savings:** $0.2223 (70.8%)
- **Note:** Output costs ($0.1749) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0710
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0118

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.2664
- **Comparison:** Baseline
- **Per Item:** $0.0444

### Claude 4 Opus
- **Cost:** $1.3321
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.2220

## File Processing Details

### Input Files Used
- ./docs/alphastrat/20-scope/20-2001-architecture.md
- ./docs/alphastrat/30-refinement/30-1001-feature-registry.yaml
- ./docs/alphastrat/30-refinement/30-2001-design-system.yaml
- ./docs/alphastrat/30-refinement/30-3001-infrastructure-registry.yaml
- ./docs/alphastrat/30-refinement/30-4001-requirements-catalog.md

### Output Files Created
- 40-3001-F001-technical.md
- 40-3001-F002-technical.md
- 40-3001-F003-technical.md
- 40-3001-F004-technical.md
- 40-3001-F005-technical.md
- 40-3001-F006-technical.md

### Expected vs Actual Output
**Files created as expected (6):**
- ✓ 40-3001-F001-technical.md
- ✓ 40-3001-F002-technical.md
- ✓ 40-3001-F003-technical.md
- ✓ 40-3001-F004-technical.md
- ✓ 40-3001-F005-technical.md
- ✓ 40-3001-F006-technical.md

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 6 items


Each result contains the generated content based on your prompts and input items.
