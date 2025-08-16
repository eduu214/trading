# Batch Processing Summary

**Generation Date:** 2025-08-15T05:02:46.545Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/flowplane/40-design
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Create Shared UX Components

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 101.3 seconds
- **Processing Speed:** 0.6 items/minute
- **Token Throughput:** 82.096 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 17
- **Total Output Tokens:** 8,296
- **Total Tokens:** 8,313

### Cache Performance
- **Cache Creation Tokens:** 13,523
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 17
- **Average Output Tokens:** 8,296

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-2001-design-system.yaml | Project | ✅ Yes | 1 | First use |
| 30-3001-infrastructure-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-4001-requirements-catalog.md | Project | ✅ Yes | 1 | First use |

### Cache Statistics
- **Documents Processed:** 4
- **Cacheable Documents:** 4 (100%)
- **Total Document Uses:** 4
- **Cached Document Uses:** 4 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.1244
- **Cache Write Cost:** $0.0507
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.1752
- **Average Cost per Item:** $0.1752

### Cache Savings
- **Input Cost Without Caching:** $0.0406
- **Input Cost With Caching:** $0.0507
- **Cache Savings:** $-0.0101 (-25.0%)
- **Note:** Output costs ($0.1244) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0467
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0467

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.1752
- **Comparison:** Baseline
- **Per Item:** $0.1752

### Claude 4 Opus
- **Cost:** $0.8758
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.8758

## File Processing Details

### Input Files Used
- ./docs/flowplane/30-refinement/30-1001-feature-registry.yaml
- ./docs/flowplane/30-refinement/30-2001-design-system.yaml
- ./docs/flowplane/30-refinement/30-3001-infrastructure-registry.yaml
- ./docs/flowplane/30-refinement/30-4001-requirements-catalog.md

### Output Files Created
- 40-1001-shared-components.yaml
- 40-1002-token-contributions.yaml

### Expected vs Actual Output
**Files created as expected (2):**
- ✓ 40-1001-shared-components.yaml
- ✓ 40-1002-token-contributions.yaml

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
