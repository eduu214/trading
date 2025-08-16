# Batch Processing Summary

**Generation Date:** 2025-08-15T05:06:22.038Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/flowplane/40-design
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Create Story UX Specification

## Processing Statistics

- **Total Items:** 20
- **Successful:** 20
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 164.7 seconds
- **Processing Speed:** 7.3 items/minute
- **Token Throughput:** 284.994 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 320
- **Total Output Tokens:** 46,619
- **Total Tokens:** 46,939

### Cache Performance
- **Cache Creation Tokens:** 20,507
- **Cache Read Tokens:** 389,633
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 350,669.7 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 16
- **Average Output Tokens:** 2,330

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 20 | 95% reuse |
| 30-2001-design-system.yaml | Project | ✅ Yes | 20 | 95% reuse |
| 30-4001-requirements-catalog.md | Project | ✅ Yes | 20 | 95% reuse |
| 40-1001-shared-components.yaml | Project | ✅ Yes | 20 | 95% reuse |
| 40-1002-token-contributions.yaml | Project | ✅ Yes | 20 | 95% reuse |

### Cache Statistics
- **Documents Processed:** 5
- **Cacheable Documents:** 5 (100%)
- **Total Document Uses:** 100
- **Cached Document Uses:** 100 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.6993
- **Cache Write Cost:** $0.0769
- **Cache Read Cost:** $0.1169

### Total Cost
- **Total Cost:** $0.8931
- **Average Cost per Item:** $0.0447

### Cache Savings
- **Input Cost Without Caching:** $1.2304
- **Input Cost With Caching:** $0.1938
- **Cache Savings:** $1.0366 (84.3%)
- **Note:** Output costs ($0.6993) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.2382
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0119

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.8931
- **Comparison:** Baseline
- **Per Item:** $0.0447

### Claude 4 Opus
- **Cost:** $4.4654
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.2233

## File Processing Details

### Input Files Used
- ./docs/flowplane/30-refinement/30-1001-feature-registry.yaml
- ./docs/flowplane/30-refinement/30-2001-design-system.yaml
- ./docs/flowplane/30-refinement/30-4001-requirements-catalog.md
- ./docs/flowplane/40-design/40-1001-shared-components.yaml
- ./docs/flowplane/40-design/40-1002-token-contributions.yaml

### Output Files Created
- 40-2001-F001-US001-ux-spec.md
- 40-2001-F001-US002-ux-spec.md
- 40-2001-F001-US003-ux-spec.md
- 40-2001-F001-US004-ux-spec.md
- 40-2001-F001-US005-ux-spec.md
- 40-2001-F002-US001-ux-spec.md
- 40-2001-F002-US002-ux-spec.md
- 40-2001-F002-US003-ux-spec.md
- 40-2001-F003-US001-ux-spec.md
- 40-2001-F003-US002-ux-spec.md
- 40-2001-F003-US003-ux-spec.md
- 40-2001-F004-US001-ux-spec.md
- 40-2001-F004-US002-ux-spec.md
- 40-2001-F004-US003-ux-spec.md
- 40-2001-F005-US001-ux-spec.md
- 40-2001-F005-US002-ux-spec.md
- 40-2001-F005-US003-ux-spec.md
- 40-2001-F006-US001-ux-spec.md
- 40-2001-F006-US002-ux-spec.md
- 40-2001-F006-US003-ux-spec.md
- 40-2002-F001-US001-token-contributions.yaml
- 40-2002-F001-US002-token-contributions.yaml
- 40-2002-F001-US003-token-contributions.yaml
- 40-2002-F001-US004-token-contributions.yaml
- 40-2002-F001-US005-token-contributions.yaml
- 40-2002-F002-US001-token-contributions.yaml
- 40-2002-F002-US002-token-contributions.yaml
- 40-2002-F002-US003-token-contributions.yaml
- 40-2002-F003-US001-token-contributions.yaml
- 40-2002-F003-US002-token-contributions.yaml
- 40-2002-F003-US003-token-contributions.yaml
- 40-2002-F004-US001-token-contributions.yaml
- 40-2002-F004-US002-token-contributions.yaml
- 40-2002-F004-US003-token-contributions.yaml
- 40-2002-F005-US001-token-contributions.yaml
- 40-2002-F005-US002-token-contributions.yaml
- 40-2002-F005-US003-token-contributions.yaml
- 40-2002-F006-US001-token-contributions.yaml
- 40-2002-F006-US002-token-contributions.yaml
- 40-2002-F006-US003-token-contributions.yaml

### Expected vs Actual Output
**Files created as expected (40):**
- ✓ 40-2001-F001-US001-ux-spec.md
- ✓ 40-2001-F001-US002-ux-spec.md
- ✓ 40-2001-F001-US003-ux-spec.md
- ✓ 40-2001-F001-US004-ux-spec.md
- ✓ 40-2001-F001-US005-ux-spec.md
- ✓ 40-2001-F002-US001-ux-spec.md
- ✓ 40-2001-F002-US002-ux-spec.md
- ✓ 40-2001-F002-US003-ux-spec.md
- ✓ 40-2001-F003-US001-ux-spec.md
- ✓ 40-2001-F003-US002-ux-spec.md
- ✓ 40-2001-F003-US003-ux-spec.md
- ✓ 40-2001-F004-US001-ux-spec.md
- ✓ 40-2001-F004-US002-ux-spec.md
- ✓ 40-2001-F004-US003-ux-spec.md
- ✓ 40-2001-F005-US001-ux-spec.md
- ✓ 40-2001-F005-US002-ux-spec.md
- ✓ 40-2001-F005-US003-ux-spec.md
- ✓ 40-2001-F006-US001-ux-spec.md
- ✓ 40-2001-F006-US002-ux-spec.md
- ✓ 40-2001-F006-US003-ux-spec.md
- ✓ 40-2002-F001-US001-token-contributions.yaml
- ✓ 40-2002-F001-US002-token-contributions.yaml
- ✓ 40-2002-F001-US003-token-contributions.yaml
- ✓ 40-2002-F001-US004-token-contributions.yaml
- ✓ 40-2002-F001-US005-token-contributions.yaml
- ✓ 40-2002-F002-US001-token-contributions.yaml
- ✓ 40-2002-F002-US002-token-contributions.yaml
- ✓ 40-2002-F002-US003-token-contributions.yaml
- ✓ 40-2002-F003-US001-token-contributions.yaml
- ✓ 40-2002-F003-US002-token-contributions.yaml
- ✓ 40-2002-F003-US003-token-contributions.yaml
- ✓ 40-2002-F004-US001-token-contributions.yaml
- ✓ 40-2002-F004-US002-token-contributions.yaml
- ✓ 40-2002-F004-US003-token-contributions.yaml
- ✓ 40-2002-F005-US001-token-contributions.yaml
- ✓ 40-2002-F005-US002-token-contributions.yaml
- ✓ 40-2002-F005-US003-token-contributions.yaml
- ✓ 40-2002-F006-US001-token-contributions.yaml
- ✓ 40-2002-F006-US002-token-contributions.yaml
- ✓ 40-2002-F006-US003-token-contributions.yaml

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 20 items


Each result contains the generated content based on your prompts and input items.
