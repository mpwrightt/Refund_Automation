# Security Assessment - TCGPlayer Refund Automation

**Document Version:** 1.0
**Last Updated:** 2025-11-13
**Classification:** Internal Use Only

---

## Executive Summary

This document provides a security assessment of the automated refund processing system for TCGPlayer inventory discrepancies. The system uses browser automation (Playwright) to process refunds at scale (~600 refunds/hour) while maintaining security controls and audit trails.

**Risk Level:** Medium (with mitigations in place)
**Recommendation:** Approve with conditions outlined in Section 8

---

## 1. System Architecture Overview

### 1.1 Technology Stack
- **Runtime:** Python 3.8+ (asyncio-based)
- **Browser Automation:** Playwright 1.49.0+ (Chromium)
- **Authentication:** Browser session persistence via Chrome profile
- **Credentials Storage:** Environment variables (.env.local)

### 1.2 Data Flow
```
CSV File (Refund Log)
    ↓
Python Script (Direct Selectors)
    ↓
Playwright Browser Automation
    ↓
TCGPlayer Admin Panel (HTTPS)
    ↓
Audit Trail (Console + CSV)
```

### 1.3 Authentication Method
- Uses existing Chrome browser profile for SSO session reuse
- Supports Google SSO (enterprise authentication)
- No password storage in automation scripts (manual login on first run)
- Session cookies stored in Chrome profile directory

---

## 2. Security Controls

### 2.1 Access Controls

**Who Can Run This Automation:**
- Requires access to production TCGPlayer admin credentials
- Requires access to TCGPlayer seller portal admin panel
- Requires physical access to machine running automation
- Should be limited to CSR team leads or inventory specialists

**Principle of Least Privilege:**
- Script only has permissions granted to logged-in user
- No elevated privileges required
- No database access (operates through web UI only)

### 2.2 Data Protection

**Credentials Management:**
- `.env.local` contains TCGPlayer login credentials
- ⚠️ **RISK:** File stored in plaintext on disk
- **MITIGATION:** File excluded from git via `.gitignore` (verify this exists)
- **RECOMMENDATION:** Use OS keychain or secrets manager instead

**Customer PII Exposure:**
- CSV input contains: Order numbers, card names, quantities
- May contain: Customer names/emails (if in Order Link)
- Browser displays full customer information during processing
- **MITIGATION:** Operator must follow data handling policies

**Session Token Storage:**
- Chrome profile contains authentication cookies
- Location: `~/Library/Application Support/Google/Chrome/Default`
- ⚠️ **RISK:** If compromised, attacker gains admin access
- **MITIGATION:** Disk encryption required, screen lock policy enforced

### 2.3 Audit Trail

**What Is Logged:**
- Console output: Order number, card name, refund amount, timestamp
- Script output: Success/failure per refund, elapsed time
- Browser keeps request logs (Network tab)

**What Is NOT Logged:**
- ❌ No persistent log file (only console output)
- ❌ No database audit trail
- ❌ No change tracking (who ran what when)

**⚠️ GAP:** Insufficient audit trail for SOX/PCI compliance
**RECOMMENDATION:** Add structured logging to file or SIEM

---

## 3. Threat Model

### 3.1 Threat: Credential Theft

**Attack Vector:** Unauthorized access to `.env.local` file
**Impact:** Full TCGPlayer admin access
**Likelihood:** Medium (requires local file access)
**Mitigations:**
- File permissions (600) - owner read/write only
- Disk encryption (FileVault on macOS)
- EDR monitoring file access
- Credential rotation policy

**Residual Risk:** Low-Medium

### 3.2 Threat: Session Hijacking

**Attack Vector:** Steal Chrome profile cookies
**Impact:** Full TCGPlayer admin access (until session expires)
**Likelihood:** Low (requires local access + know where to look)
**Mitigations:**
- Disk encryption
- Screen lock after inactivity
- Regular session expiration (TCGPlayer SSO policy)

**Residual Risk:** Low

### 3.3 Threat: Malicious CSV Injection

**Attack Vector:** Attacker modifies CSV to refund wrong orders
**Impact:** Financial loss, customer complaints, reputation damage
**Likelihood:** Medium (if CSV source is shared drive)
**Mitigations:**
- CSV source from trusted inventory team only
- Dry-run mode for validation before production
- Manual spot-check of first 5-10 refunds

**Residual Risk:** Medium

**⚠️ RECOMMENDATION:** Add CSV validation (checksums, digital signatures)

### 3.4 Threat: Code Tampering

**Attack Vector:** Modify script to refund wrong amounts or customers
**Impact:** Financial loss, fraud
**Likelihood:** Low (requires access to codebase)
**Mitigations:**
- Code review before deployment
- Git version control (if used)
- File integrity monitoring (checksums)

**Residual Risk:** Low

**RECOMMENDATION:** Sign scripts with digital signature, verify before execution

### 3.5 Threat: Insider Abuse

**Attack Vector:** Authorized operator processes fraudulent refunds
**Impact:** Financial loss, fraud
**Likelihood:** Low (requires malicious insider)
**Mitigations:**
- Dual control (manager approval for CSV batches)
- Post-processing audit (compare CSV to actual refunds)
- Background checks for operators

**Residual Risk:** Low-Medium

**⚠️ GAP:** No dual control mechanism
**RECOMMENDATION:** Require manager signature on CSV before processing

---

## 4. Compliance Considerations

### 4.1 PCI-DSS
**Question:** Does this system touch cardholder data?
**Answer:** No - refunds processed through TCGPlayer admin panel (PCI-compliant)
**Status:** ✓ No direct PCI scope

### 4.2 SOX (if publicly traded)
**Question:** Does this impact financial reporting?
**Answer:** Yes - refunds affect revenue recognition
**Requirements:**
- ❌ Audit trail of who processed refunds
- ❌ Change control for script modifications
- ❌ Segregation of duties (developer ≠ operator)

**⚠️ GAP:** Insufficient controls for SOX compliance
**RECOMMENDATION:** Add logging, approval workflow, separate dev/prod

### 4.3 GDPR/Privacy
**Question:** Is customer PII processed?
**Answer:** Yes - names, emails, order history visible during processing
**Requirements:**
- ✓ Legitimate business purpose (refund processing)
- ✓ Minimal data exposure (only what's needed)
- ⚠️ Data retention policy unclear (CSV storage)

**RECOMMENDATION:** Define CSV retention/deletion policy

---

## 5. Operational Security

### 5.1 Deployment Security

**Current State:**
- Script run from operator's laptop
- No centralized deployment
- No version control enforcement

**Recommendations:**
1. Deploy from locked-down admin workstation (not personal laptop)
2. Use Git tags for versioned releases
3. Require code review + approval before production use

### 5.2 Monitoring & Alerting

**Current State:**
- No monitoring
- No alerting on failures
- No anomaly detection

**Recommendations:**
1. Alert on >X failed refunds in a row
2. Alert on refund amounts exceeding threshold
3. Daily summary report to manager

### 5.3 Incident Response

**Scenario:** Script refunds wrong customer
**Current Procedure:** Unknown

**Recommendations:**
1. Document rollback procedure
2. Maintain list of all processed refunds (CSV archive)
3. Escalation path (who to contact)

---

## 6. Code Security Review

### 6.1 Input Validation
**CSV Parsing:**
```python
with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    refunds = list(reader)
```
- ⚠️ No validation of CSV structure
- ⚠️ No sanitization of inputs before DOM manipulation
- ⚠️ Trusts CSV data implicitly

**RECOMMENDATION:** Add schema validation, sanitize inputs

### 6.2 Error Handling
**Current Behavior:**
- Try/catch blocks present
- Failed refunds skipped (not retried)
- Error printed to console only

**⚠️ GAP:** Silent failures could go unnoticed
**RECOMMENDATION:** Fail loudly, require manual review of errors

### 6.3 Secrets Management
**Current:**
```python
TCGPLAYER_EMAIL = os.getenv('TCGPLAYER_EMAIL')
TCGPLAYER_PASSWORD = os.getenv('TCGPLAYER_PASSWORD')
```
- Environment variables from `.env.local` file
- Plaintext storage

**RECOMMENDATION:** Use OS keychain (macOS Keychain, Windows Credential Manager)

### 6.4 Dependency Security
**Dependencies:**
- `playwright==1.49.0` (or 1.49.1)
- `python-dotenv==1.0.1`

**Security Checks:**
```bash
pip3 audit  # Check for known vulnerabilities
```

**RECOMMENDATION:**
- Pin exact versions (already done ✓)
- Regular dependency updates
- Vulnerability scanning in CI/CD

---

## 7. Dry-Run Mode Security

### 7.1 Current Implementation
**Lines 534 & 551:**
```python
await submit_refund(page, dry_run=True)
await add_international_store_credit(page, order_number)  # defaults to dry_run=True
```

**Risk Assessment:**
- ✓ Dry-run default prevents accidental production runs
- ⚠️ Easy to change (just flip boolean)
- ⚠️ No confirmation prompt before production mode

**RECOMMENDATION:**
```python
if not dry_run:
    print("⚠️  PRODUCTION MODE - SUBMIT REAL REFUNDS")
    print("Type 'CONFIRM' to proceed: ")
    if input().strip() != 'CONFIRM':
        print("Aborted")
        return False
```

---

## 8. Risk Acceptance & Recommendations

### 8.1 Critical (Must Fix Before Production)
1. ❌ **Add comprehensive logging** - File-based audit trail with timestamps, operator ID, order details
2. ❌ **Implement dual control** - Manager approval required for CSV batches
3. ❌ **Add confirmation prompt** - Require explicit confirmation before production mode

### 8.2 High (Fix Within 30 Days)
1. ⚠️ **Move credentials to keychain** - Stop using plaintext .env.local
2. ⚠️ **Add CSV validation** - Schema validation, checksum verification
3. ⚠️ **Implement monitoring** - Alert on failures, daily summary reports
4. ⚠️ **Document incident response** - Rollback procedure, escalation path

### 8.3 Medium (Fix Within 90 Days)
1. ⚠️ **Centralized deployment** - Dedicated admin workstation
2. ⚠️ **Version control enforcement** - Git tags, code review process
3. ⚠️ **Post-processing audit** - Compare CSV to actual refunds processed
4. ⚠️ **Define data retention policy** - CSV archival and deletion

### 8.4 Low (Nice to Have)
1. ℹ️ Code signing for tamper detection
2. ℹ️ Automated dependency scanning
3. ℹ️ Integration with SIEM for centralized logging

---

## 9. Approval Checklist

Before authorizing production use, verify:

- [ ] Credentials stored securely (keychain or approved secrets manager)
- [ ] Audit logging implemented (who, what, when)
- [ ] Dual control process documented and enforced
- [ ] Incident response plan documented
- [ ] CSV retention policy defined
- [ ] Operator training completed
- [ ] First production run supervised by manager
- [ ] Post-processing audit procedure established
- [ ] Monitoring and alerting configured
- [ ] Code review completed by engineering team

---

## 10. Sign-Off

**Prepared By:** _________________________ Date: _________
**Security Review:** _________________________ Date: _________
**Engineering Approval:** _________________________ Date: _________
**Business Owner Approval:** _________________________ Date: _________

---

## Appendix A: Security Contacts

**Security Incidents:** [security@tcgplayer.com]
**Privacy Questions:** [privacy@tcgplayer.com]
**Engineering Support:** [engineering-lead@tcgplayer.com]

## Appendix B: Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-13 | Initial | First security assessment |
