# Archive: Traefik Docker API Version Mismatch

**Date:** 2025-11-27
**Classified As:** ERROR-010
**Total Occurrences:** 144 duplicate errors

## Summary
All 144 draft errors were **identical** - same Traefik Docker API version mismatch issue detected during first production DebLLM scan.

## Error Pattern
```
Error response from daemon: client version 1.24 is too old.
Minimum supported API version is 1.44, please upgrade your client to a newer version
```

**Source:** `github.com/traefik/traefik/v3/pkg/provider/docker/pdocker.go:85` and `:156`

## Classification Decision
- **error_id:** ERROR-010
- **title:** Traefik Docker API Version Mismatch
- **service:** traefik
- **error_domain:** config
- **severity:** medium (not critical - Traefik retrying, system functional)
- **resolution_group:** tech-devops
- **auto_fix:** false (requires config file modification)
- **in_kb:** true

## Resolution
See: `debllm/notes/traefik/ERROR-010-docker-api-version-mismatch.md`

**Recommended Fix:**
```bash
# Update Docker Compose API version
sed -i 's/version: "3.8"/version: "3.9"/' compose/helix-core/core-stack.yml
make down && make up
```

## Auto-Classification Trigger
This archive demonstrates the **10+ duplicate error auto-classification workflow**:
1. DebLLM detected 144 errors during first scan
2. All errors matched same pattern
3. Classified as single KB note (ERROR-010)
4. Drafts archived with reference

## Files Archived
- DRAFT-1764240087-1.md through DRAFT-1764240104-144.md (144 files)

## Signed-Off By
- **angel** (2025-11-27) - Manual review and classification
- **debllm** (2025-11-27) - Auto-detection and grouping
