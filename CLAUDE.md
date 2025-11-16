# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TCGPlayer refund automation tool that processes inventory refunds using Playwright browser automation with direct DOM selectors. It processes refunds 10-30x faster than AI-based approaches (~600 refunds/hour vs ~60-120/hour) by using direct browser selectors instead of LLM inference.

**Performance**: ~6 seconds per refund (domestic), ~25 seconds (international with store credit)
**Approach**: XPath/CSS selectors + JavaScript widget isolation

## Running the Automation

### Installation
```bash
pip3 install playwright python-dotenv
playwright install chromium
```

### Test Mode (Safe - Does NOT Submit)
```bash
python3 tcgplayer_direct_selectors.py path/to/your_refund_log.csv
```
Test mode fills forms but stops before clicking "Give Refund" and "Save" buttons.

**Note:** Create your own CSV with the required columns (see CSV Format section below). Test data is not included in the repository for security reasons.

### Production Mode
**WARNING: Submits real refunds!**

Edit [tcgplayer_direct_selectors.py](tcgplayer_direct_selectors.py):
- Line 534: Change `dry_run=True` to `dry_run=False` (refund submission)
- Line 551: Change `dry_run=True` to `dry_run=False` (international store credit)

Then run:
```bash
python3 tcgplayer_direct_selectors.py path/to/refund_log.csv
```

## Architecture

### Core Automation Flow
The script follows this pattern for each refund:

1. **Navigate to order** → Load order page from CSV's "Order Link"
2. **Country detection** → Read shipping country code from XPath to determine domestic vs international
3. **Widget isolation** → Hide all cards except target card using JavaScript DOM manipulation
4. **Click Partial Refund** → Find and click the correct "Partial Refund" button within isolated widget
5. **Fill refund form** → Use CSS selectors for dropdowns/inputs (all have stable IDs)
6. **Submit refund** → Click "Give Refund" (production mode only)
7. **Store credit** → Apply $1 checkbox (domestic) OR navigate to buyer dashboard and add $5.99 (international)

### Key Techniques

**JavaScript Widget Isolation** ([tcgplayer_direct_selectors.py:164-243](tcgplayer_direct_selectors.py#L164-L243)):
- Matches card by name + set + condition (handles duplicates)
- Hides all non-matching widgets via `display: 'none'`
- Normalizes condition codes (CSV abbreviations → full text, e.g., "NMF" → "Near Mint Foil")
- Returns match result to Python for validation

**Scoped Button Clicking** ([tcgplayer_direct_selectors.py:245-287](tcgplayer_direct_selectors.py#L245-L287)):
- Finds the ONE visible widget (all others hidden)
- Queries for `a[href*="partialrefund"]` WITHIN that widget only
- Avoids clicking wrong button when page has 40+ "Partial Refund" buttons

**Multi-Card Sub-Order Handling** ([tcgplayer_direct_selectors.py:344-393](tcgplayer_direct_selectors.py#L344-L393)):
- Searches refund form table for row containing card name
- Fills quantity input in that specific row (not always `RefundProducts[0]`)

### Business Logic (SOP Compliance)

**Store Credit Rules** (see [docs/SOP_Pull_Discrep_Refunds.md](docs/SOP_Pull_Discrep_Refunds.md)):
- **Domestic**: $1.00 checkbox on refund form (first card per order only)
- **International**: $5.99 manual credit via buyer dashboard (NOT checkbox)
- **Duplicate cards**: No store credit for 2nd+ cards in SAME order

**Refund Messages**:
- First card (domestic): Mentions $1.00 credit
- Duplicate card (domestic): No credit mentioned
- International: Always mentions $5.99 (no separate duplicate message)

**Order Tracking** ([tcgplayer_direct_selectors.py:594-612](tcgplayer_direct_selectors.py#L594-L612)):
- `is_first_card` flag resets when `Order Link` changes
- Ensures correct store credit application per order

### Browser Session Management

Uses Chrome Default profile (`~/Library/Application Support/Google/Chrome/Default`):
- Preserves SSO login sessions across runs
- Avoids repeated authentication prompts
- Supports enterprise login flows (Google SSO)

First run will pause and prompt for manual login if not already logged in.

### International Order Workflow

Detection ([tcgplayer_direct_selectors.py:27-47](tcgplayer_direct_selectors.py#L27-L47)):
- Reads country code from shipping address table via XPath
- Returns `True` if country != "US"

Store Credit Addition ([tcgplayer_direct_selectors.py:49-138](tcgplayer_direct_selectors.py#L49-L138)):
1. Navigate to buyer dashboard (click link on order page)
2. Click "Add/Remove Store Credit" button
3. Fill amount: 5.99
4. Fill reason: "Product not in Direct Inventory Order #[ORDER_NUMBER]"
5. Click Save (production mode only)

## CSV Format

Required columns:
- `Order Link`: Full URL to TCGPlayer admin order page
- `Order Number`: Order ID (e.g., "251024-EB1A")
- `Card Name`: Full card name including variants (e.g., "Temporal Manipulation (Extended Art)")
- `Set Name`: Product set/expansion name
- `Cond.`: Condition code (NM, LP, MP, HP, DM, NMF, LPF, NMH, etc.)
- `Quant.`: Quantity to refund (script uses absolute value)

## Security Considerations

**Credentials**:
- `.env.local` contains production TCGPlayer email/password
- This file is protected by [.gitignore](.gitignore)
- Template is [.env.example](.env.example)

**Browser Profile**:
- Chrome profile contains auth cookies and session tokens
- Located at `~/Library/Application Support/Google/Chrome/Default`

## Known Limitations

**Not Yet Implemented**:
- Full refund workflow (single-card orders currently use Partial Refund)
- Error recovery (script skips failed refunds, no retry logic)
- Detailed logging to file (only console output)

**Form Field Assumptions**:
- Inventory Changes dropdown is optional (gracefully skipped if missing)
- Quantity input assumes `RefundProducts_0__RefundQuantity` format, but has fallback to search table by card name

## Troubleshooting

**"Not logged in" on first run**:
- Script will pause and prompt for manual login
- Log in via SSO in the Chrome window
- Press Enter to continue

**Widget isolation fails**:
- Check card name/set/condition match exactly between CSV and page
- Script normalizes conditions (e.g., "NMF" → "Near Mint Foil") but card names must match

**Form fields not found**:
- Some orders have different layouts
- Check console output for which field failed
- Inventory Changes is optional (script continues if missing)

**International order not detected**:
- Run [scripts/test_country_detection.js](scripts/test_country_detection.js) in browser console on order page
- Verify country code appears at XPath `/html/body/div[4]/div/div[6]/div[1]/div[1]/table/tbody/tr[8]/td[2]`
