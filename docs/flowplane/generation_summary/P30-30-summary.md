# Batch Processing Summary

**Generation Date:** 2025-08-15T04:57:51.926Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/alphastrat/30-refinement
**Model:** claude-3-5-haiku-20241022
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Create Infrastructure Registry

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 31.8 seconds
- **Processing Speed:** 1.9 items/minute
- **Token Throughput:** 59.865 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 15
- **Total Output Tokens:** 1,886
- **Total Tokens:** 1,901

### Cache Performance
- **Cache Creation Tokens:** 13,338
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 15
- **Average Output Tokens:** 1,886

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 20-2001-architecture.md | Project | ✅ Yes | 1 | First use |
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-1002-story-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-1003-scope-overview.md | Project | ✅ Yes | 1 | First use |
| 30-2001-design-system.yaml | Project | ✅ Yes | 1 | First use |

### Cache Statistics
- **Documents Processed:** 5
- **Cacheable Documents:** 5 (100%)
- **Total Document Uses:** 5
- **Cached Document Uses:** 5 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.0075
- **Cache Write Cost:** $0.0133
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.0209
- **Average Cost per Item:** $0.0209

### Cache Savings
- **Input Cost Without Caching:** $0.0107
- **Input Cost With Caching:** $0.0133
- **Cache Savings:** $-0.0027 (-25.0%)
- **Note:** Output costs ($0.0075) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0209
- **Comparison:** 1.0x current run cost
- **Per Item:** $0.0209

### Claude 4 Sonnet
- **Cost:** $0.0783
- **Comparison:** 3.8x current run cost
- **Per Item:** $0.0783

### Claude 4 Opus
- **Cost:** $0.3915
- **Comparison:** 18.8x current run cost
- **Per Item:** $0.3915

## File Processing Details

### Input Files Used
- ./docs/alphastrat/20-scope/20-2001-architecture.md
- ./docs/alphastrat/30-refinement/30-1001-feature-registry.yaml
- ./docs/alphastrat/30-refinement/30-1002-story-registry.yaml
- ./docs/alphastrat/30-refinement/30-1003-scope-overview.md
- ./docs/alphastrat/30-refinement/30-2001-design-system.yaml

### Output Files Created
- 30-3001-infrastructure-registry.yaml

### Expected vs Actual Output
**Files created as expected (1):**
- ✓ 30-3001-infrastructure-registry.yaml

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
