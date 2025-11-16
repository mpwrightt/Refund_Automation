# TCGPlayer Refund Automation

Automated refund processing for TCGPlayer using Playwright browser automation.

## Performance

- **Speed:** ~6 seconds per refund (~600 refunds/hour)
- **Accuracy:** Direct DOM selectors (no AI inference)
- **Features:** Automatic international detection, SOP-compliant store credit, dry-run mode

## Installation

```bash
pip3 install -r requirements.txt
playwright install chromium
```

## Configuration

1. Copy `.env.example` to `.env.local`
2. Add your TCGPlayer credentials to `.env.local`

## Usage

### Dry Run (Safe - No Submissions)
```bash
python3 tcgplayer_direct_selectors.py path/to/refund_log.csv
```

### Production Mode
Edit `tcgplayer_direct_selectors.py`:
- Line 534: Set `dry_run=False`
- Line 551: Set `dry_run=False`

Then run:
```bash
python3 tcgplayer_direct_selectors.py path/to/refund_log.csv
```

## CSV Format

Required columns:
- `Order Link` - TCGPlayer admin order URL
- `Order Number` - Order ID
- `Card Name` - Full card name with variants
- `Set Name` - Product set/expansion
- `Cond.` - Condition code (NM, LP, MP, HP, DM, NMF, LPF, etc.)
- `Quant.` - Quantity to refund

## How It Works

1. Reads shipping country to detect international orders
2. Uses JavaScript to isolate target card widget on page
3. Fills refund form using direct CSS selectors
4. Applies store credit ($1 domestic, $5.99 international)
5. Submits refund (production mode only)

## License

MIT License - See LICENSE file for details
