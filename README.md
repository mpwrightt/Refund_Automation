# TCGPlayer Refund Automation

Fast, reliable automated refund processing using direct Playwright selectors.

## Overview

This automation processes TCGPlayer inventory refunds 10-30x faster than AI-based approaches by using direct browser selectors instead of LLM inference.

**Performance**: ~600 refunds/hour (~6 seconds per refund)  
**Cost**: Minimal (no LLM API costs)  
**Accuracy**: 100% success rate in testing (23/23 refunds)

## Features

- ✅ Automatic domestic/international order detection
- ✅ Correct store credit application ($1 domestic, $5.99 international)
- ✅ SOP-compliant messaging and form filling
- ✅ First card vs duplicate detection per order
- ✅ Foil/holofoil condition support
- ✅ Multi-card sub-order handling
- ✅ Graceful handling of missing form fields
- ✅ Dry-run mode for safe testing

## Requirements

- Python 3.8+
- Chrome browser (for SSO login support)
- Dependencies: `playwright`, `python-dotenv`

## Installation

1. Install Python dependencies:
```bash
pip3 install playwright python-dotenv
playwright install chromium
```

2. Copy `.env.example` to `.env.local` and fill in credentials:
```bash
cp .env.example .env.local
# Edit .env.local with your TCGPlayer email/password
```

3. Ensure Chrome profile exists at `~/Library/Application Support/Google/Chrome/Default`

## Usage

### Test Mode (Dry Run - Safe)
```bash
python3 tcgplayer_direct_selectors.py path/to/your_refund_log.csv
```

This will:
- Fill all forms correctly
- NOT submit refunds (stops before clicking "Give Refund")
- NOT add store credits (stops before clicking "Save")
- Show exactly what would happen in production

### Production Mode
**⚠️ WARNING: This will submit real refunds!**

Edit `tcgplayer_direct_selectors.py` and change:
- Line 513: `dry_run=False`
- Line 530: `dry_run=False`

Then run:
```bash
python3 tcgplayer_direct_selectors.py path/to/refund_log.csv
```

## CSV Format

Expected columns:
- `Order Link`: URL to TCGPlayer admin order page
- `Order Number`: Order ID (e.g., "251024-EB1A")
- `Card Name`: Full card name (including variants like "Extended Art")
- `Set Name`: Product set/expansion name
- `Cond.`: Condition code (NM, LP, MP, HP, DM, or foil variants like LPF, NMH)
- `Quant.`: Quantity to refund (can be negative)

## How It Works

1. **Country Detection**: Reads shipping country code to identify international orders
2. **Card Matching**: Uses JavaScript to isolate widget by card name + set + condition
3. **Form Filling**: Direct selectors for all dropdown/input fields
4. **Store Credit**: 
   - Domestic: $1 checkbox for first card in each order
   - International: Navigates to buyer dashboard, adds $5.99 manually
5. **Submission**: Clicks "Give Refund" (in production mode only)

## Architecture

### Direct Selector Approach
Instead of using AI to interpret the page, this script uses:
- **XPath selectors** for stable element targeting
- **JavaScript widget isolation** to hide non-target cards
- **CSS selectors** for form fields with stable IDs

This eliminates LLM costs and reduces latency from 30-60s to ~6s per refund.

### Browser Profile
Uses Chrome Default profile (`~/Library/Application Support/Google/Chrome/Default`) to:
- Preserve SSO login sessions
- Avoid repeated authentication
- Support enterprise login flows

## SOP Compliance

Implements TCGPlayer Pull Discrep Refunds SOP:
- ✅ Correct refund messages (domestic vs international, first vs duplicate)
- ✅ Store credit rules ($1 domestic first card, $5.99 international)
- ✅ Refund reason: "Product - Inventory Issue"
- ✅ Inventory adjustment handling
- ⚠️ Full refund workflow (single-card orders) - not yet implemented

See `docs/SOP_Pull_Discrep_Refunds.md` for complete SOP details.

## Security Considerations

**Credentials**: `.env.local` contains production credentials
- Never commit this file to version control
- Rotate credentials before sharing codebase
- Use environment-specific credentials (dev vs prod)

**Session Management**: Browser profile directory contains auth cookies
- Located at: `~/.config/tcgplayer_bot/` (not used if using Chrome profile)
- Contains session tokens for TCGPlayer

**CSV Data**: May contain customer PII
- Handle refund logs securely
- Do not commit test data with real customer info

## Troubleshooting

### "Not logged in" on first run
- The script will pause and prompt you to log in manually
- Log in via SSO in the Chrome window
- Press Enter to continue
- Subsequent runs will reuse the session

### International order not detected
- Run `scripts/test_country_detection.js` in browser console on the order page
- Verify country code appears in shipping address table

### Form fields not found
- Some orders have different form layouts
- Check console output for which field failed
- Script gracefully skips optional fields (like Inventory Changes)

## Testing

Before production use:
1. Run with test CSV in dry-run mode
2. Verify all form fields fill correctly
3. Check store credit logic (first card vs duplicates)
4. Test international order (if available)
5. Enable production mode for 1-2 test refunds
6. Monitor browser to ensure correct submission

## Files

- `tcgplayer_direct_selectors.py` - Main automation script
- `.env.example` - Template for credentials
- `docs/SOP_Pull_Discrep_Refunds.md` - Business logic documentation
- `scripts/test_country_detection.js` - Browser console test for international detection

## Performance Metrics

From testing on 23 refunds:
- **Success rate**: 100% (23/23)
- **Average time**: 6.1s per refund
- **Estimated rate**: 589 refunds/hour
- **International refunds**: 24.6s (includes $5.99 credit workflow)

For comparison:
- Manual processing: ~5 minutes per refund (~12 refunds/hour)
- AI-based automation: ~30-60s per refund (~60-120 refunds/hour)
- Direct selectors: ~6s per refund (~600 refunds/hour)

## License

Internal TCGPlayer use only.
