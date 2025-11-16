#!/usr/bin/env python3
"""
TCGPlayer refund automation using direct Playwright selectors
Replaces AI with JavaScript widget isolation + CSS selectors for speed
"""

import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import csv

load_dotenv('.env.local')

# Browser profile directory - separate from browser-use to avoid conflicts
USER_DATA_DIR = Path.home() / '.config' / 'tcgplayer_bot' / 'direct_selectors_profile'
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

STORAGE_STATE_FILE = USER_DATA_DIR / 'storage_state.json'

TCGPLAYER_EMAIL = os.getenv('TCGPLAYER_EMAIL')
TCGPLAYER_PASSWORD = os.getenv('TCGPLAYER_PASSWORD')


async def check_if_international(page):
    """
    Check if order is international by reading shipping country from order page
    Returns True if international, False if domestic (US)
    """
    try:
        # Get country code from shipping address table (td[2] contains the actual country code)
        country_xpath = '/html/body/div[4]/div/div[6]/div[1]/div[1]/table/tbody/tr[8]/td[2]'
        country_element = await page.query_selector(f'xpath={country_xpath}')

        if country_element:
            country_text = await country_element.text_content()
            country_code = country_text.strip()

            # Check if country code is US or international (CA, UK, etc.)
            return country_code.upper() != 'US'

        return False  # Default to domestic if can't determine
    except:
        return False  # Default to domestic on error


async def add_international_store_credit(page, order_number, dry_run=True):
    """
    Add $5.99 store credit for international orders
    Navigates to buyer dashboard and adds credit with note

    Args:
        page: Playwright page object
        order_number: Order number for the note (e.g., "251020-402C")
        dry_run: If True, don't actually click Save (for testing)

    Returns:
        True if successful, False otherwise
    """
    try:
        print("→ Adding $5.99 international store credit...")

        # Get the buyer dashboard link
        buyer_link_xpath = '/html/body/div[4]/div/div[6]/div[3]/div[1]/table/tbody/tr[2]/td[2]/a[2]'
        buyer_link = await page.query_selector(f'xpath={buyer_link_xpath}')

        if not buyer_link:
            print("✗ Could not find buyer dashboard link")
            return False

        # Click the buyer dashboard link
        await buyer_link.click()

        # Wait specifically for the "Add/Remove Store Credit" button to load
        add_credit_button_xpath = '/html/body/div[4]/div/div[5]/div[4]/div[2]/div/div[2]/div/div[1]/div[2]/input[2]'
        add_credit_button = await page.wait_for_selector(f'xpath={add_credit_button_xpath}', timeout=10000)
        print("✓ Buyer dashboard loaded")

        if not add_credit_button:
            print("✗ Could not find 'Add/Remove Store Credit' button")
            return False

        await add_credit_button.click()

        # Wait specifically for the amount input field to load
        amount_input_xpath = '/html/body/div[4]/div/form/div/div[2]/div[3]/div[1]/input'
        await page.wait_for_selector(f'xpath={amount_input_xpath}', timeout=10000)
        print("✓ Store credit form loaded")

        # Select purpose from dropdown (if needed - you may need to specify the value)
        purpose_dropdown_xpath = '/html/body/div[4]/div/form/div/div[2]/div[2]/div[1]/select'
        purpose_dropdown = await page.query_selector(f'xpath={purpose_dropdown_xpath}')
        if purpose_dropdown:
            # TODO: What value should be selected? For now, leaving it as default
            # await page.select_option(f'xpath={purpose_dropdown_xpath}', 'value_here')
            print("✓ Purpose dropdown found (using default)")

        # Fill in the amount
        amount_input_xpath = '/html/body/div[4]/div/form/div/div[2]/div[3]/div[1]/input'
        amount_input = await page.query_selector(f'xpath={amount_input_xpath}')
        if amount_input:
            await amount_input.fill('5.99')
            print("✓ Amount: 5.99")
        else:
            print("✗ Could not find amount input field")
            return False

        # Fill in the reason/note
        reason_textarea_xpath = '/html/body/div[4]/div/form/div/div[2]/div[4]/div[1]/textarea'
        reason_textarea = await page.query_selector(f'xpath={reason_textarea_xpath}')
        if reason_textarea:
            await reason_textarea.fill(f'Product not in Direct Inventory Order #{order_number}')
            print(f"✓ Reason: Product not in Direct Inventory Order #{order_number}")
        else:
            print("✗ Could not find reason textarea")
            return False

        # Click Save button (or skip in dry run mode)
        if dry_run:
            print("⚠️  DRY RUN - Would click Save button to add $5.99 credit")
            return True
        else:
            # Use exact XPath for Save button
            save_button_xpath = '/html/body/div[4]/div/form/input[2]'
            save_button = await page.query_selector(f'xpath={save_button_xpath}')
            if save_button:
                print("→ Clicking Save button to add store credit...")
                await save_button.click()

                # Wait for page to process and reload
                print("→ Waiting for page to process store credit...")
                await page.wait_for_load_state("networkidle", timeout=60000)
                await asyncio.sleep(2)  # Extra buffer for stability

                print("✓ $5.99 store credit added")
                return True
            else:
                print("✗ Could not find Save button")
                return False

    except Exception as e:
        print(f"✗ Error adding store credit: {e}")
        return False


async def login_to_tcgplayer(page):
    """Check if already logged in, otherwise prompt for manual login"""
    print("→ Checking login status...")

    # Navigate to a TCGPlayer admin page to check auth
    await page.goto("https://store.tcgplayer.com/admin")
    await asyncio.sleep(2)

    # If redirected to login page, need to log in
    if 'login' in page.url.lower():
        print("✗ Not logged in\n")
        print("=" * 80)
        print("MANUAL LOGIN REQUIRED")
        print("=" * 80)
        print("Please log in to TCGPlayer in the browser window")
        print("Press Enter when logged in and ready to continue...")
        print("=" * 80)

        input()  # Wait for user to press Enter
        print("\n✓ Continuing with automation...\n")
    else:
        print("✓ Already logged in\n")


async def isolate_widget(page, card_name, set_name, condition):
    """
    Isolate widget containing the target card using JavaScript
    Matches on card name, set name, and condition to handle duplicate cards
    Returns True if widget found and isolated, False otherwise
    """
    # Pass all identifying info as parameters to avoid string escaping issues
    isolation_script = """
    ({cardName, setName, condition}) => {
        const widgets = document.querySelectorAll('.widget');
        let targetWidget = null;

        // Normalize condition text (CSV uses abbreviations, page uses full text)
        const conditionMap = {
            'NM': 'Near Mint',
            'LP': 'Lightly Played',
            'MP': 'Moderately Played',
            'HP': 'Heavily Played',
            'DM': 'Damaged',
            // Foil variants
            'NMF': 'Near Mint Foil',
            'LPF': 'Lightly Played Foil',
            'MPF': 'Moderately Played Foil',
            'HPF': 'Heavily Played Foil',
            'DMF': 'Damaged Foil',
            // Pokemon holofoil variants
            'NMH': 'Near Mint Holofoil',
            'LPH': 'Lightly Played Holofoil',
            'MPH': 'Moderately Played Holofoil',
            'HPH': 'Heavily Played Holofoil',
            'DMH': 'Damaged Holofoil'
        };
        const fullCondition = conditionMap[condition] || condition;

        widgets.forEach(w => {
            const text = w.textContent.toLowerCase();
            const cardMatch = text.includes(cardName.toLowerCase());
            const setMatch = text.includes(setName.toLowerCase());
            const conditionMatch = text.includes(fullCondition.toLowerCase());

            if (cardMatch && setMatch && conditionMatch) {
                targetWidget = w;
            }
        });

        if (!targetWidget) {
            return {
                success: false,
                message: `No widget found with card="${cardName}", set="${setName}", condition="${fullCondition}"`
            };
        }

        // Hide all other widgets
        widgets.forEach(w => {
            if (w !== targetWidget) {
                w.style.display = 'none';
            }
        });

        // Hide order information
        const orderInfo = document.querySelector('.orderInformation');
        if (orderInfo) orderInfo.style.display = 'none';

        return { success: true, message: 'Widget isolated' };
    }
    """

    result = await page.evaluate(isolation_script, {
        'cardName': card_name,
        'setName': set_name,
        'condition': condition
    })

    if result['success']:
        print(f"✓ {result['message']}")
        return True
    else:
        print(f"✗ {result['message']}")
        return False


async def click_partial_refund(page):
    """
    Click the Partial Refund button in the isolated widget
    Uses scoped query to find button within isolated widget only
    """
    click_script = """
    (function() {
        // Find the visible widget (all others are hidden)
        const widgets = document.querySelectorAll('.widget');
        let targetWidget = null;

        for (const w of widgets) {
            if (w.style.display !== 'none') {
                targetWidget = w;
                break;
            }
        }

        if (!targetWidget) {
            return { success: false, message: 'No visible widget found' };
        }

        // Find Partial Refund button WITHIN the target widget
        const partialRefundButton = targetWidget.querySelector('a[href*="partialrefund"]');

        if (!partialRefundButton) {
            return { success: false, message: 'Partial Refund button not found in widget' };
        }

        partialRefundButton.click();
        return { success: true, message: 'Clicked Partial Refund button' };
    })();
    """

    result = await page.evaluate(click_script)

    if result['success']:
        print(f"✓ {result['message']}")
        return True
    else:
        print(f"✗ {result['message']}")
        return False


async def fill_refund_form(page, refund_data):
    """
    Fill refund form using direct Playwright selectors
    No AI needed - all elements have stable IDs

    Args:
        refund_data: dict with keys:
            - refund_origin: str (dropdown value)
            - refund_reason: str (dropdown value)
            - inventory_changes: str (dropdown value)
            - message: str (textarea text)
            - store_credit: bool (checkbox)
            - quantity: int (number of cards to refund)
    """
    print("→ Filling refund form...")

    # Wait for form to load
    await page.wait_for_selector('select#refundOrigin', timeout=5000)

    # Fill Refund Origin dropdown
    await page.select_option('select#refundOrigin', refund_data['refund_origin'])
    print(f"  ✓ Refund Origin: {refund_data['refund_origin']}")

    # Fill Refund Reason dropdown
    await page.select_option('select#refundReason', refund_data['refund_reason'])
    print(f"  ✓ Refund Reason: {refund_data['refund_reason']}")

    # Fill Inventory Changes dropdown (optional - skip if not present)
    try:
        await page.select_option('select#inventoryChanges', refund_data['inventory_changes'], timeout=2000)
        print(f"  ✓ Inventory Changes: {refund_data['inventory_changes']}")
    except:
        print("  ⚠ Inventory Changes: field not available, skipping")

    # Fill message textarea
    await page.fill('textarea#Message', refund_data['message'])
    print(f"  ✓ Message: {refund_data['message'][:50]}...")

    # Store credit checkbox
    if refund_data['store_credit']:
        await page.check('input#AddCsrStoreCredit')
        print("  ✓ Store credit: checked")
    else:
        await page.uncheck('input#AddCsrStoreCredit')
        print("  ✓ Store credit: unchecked")

    # Fill quantity for first row (RefundProducts[0].RefundQuantity)
    # Note: If multiple cards in sub-order, need to find correct row by card name
    quantity_input = 'input#RefundProducts_0__RefundQuantity'
    await page.fill(quantity_input, str(refund_data['quantity']))
    print(f"  ✓ Quantity: {refund_data['quantity']}")

    print("✓ Form filled\n")


async def find_card_row_and_fill_quantity(page, card_name, quantity):
    """
    Find the table row containing the card name and fill its quantity input
    Also extracts the total cost from the Cost column (td[5])
    Note: Cost column already includes quantity calculation (qty × unit price)
    Handles sub-orders with multiple cards by searching table for card name

    Returns:
        tuple: (success: bool, total_cost: float or None)
    """
    # Pass card name as parameter to avoid string escaping issues
    script = """
    ({cardName, quantity}) => {
        // Find all table rows
        const rows = document.querySelectorAll('form table tbody tr');

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const cardCell = row.querySelector('td:nth-child(2)');

            if (!cardCell) continue;

            const cellText = cardCell.textContent.toLowerCase();
            if (cellText.includes(cardName.toLowerCase())) {
                // Found the card row - extract total cost from td[5]
                // Note: This is the total (qty × unit price), not unit price
                const costCell = row.querySelector('td:nth-child(5)');
                let totalCost = null;
                if (costCell) {
                    // Extract cost - format is typically "$1.23"
                    const costText = costCell.textContent.trim();
                    const costMatch = costText.match(/\$?([0-9]+\.[0-9]{2})/);
                    if (costMatch) {
                        totalCost = parseFloat(costMatch[1]);
                    }
                }

                // Fill quantity input (Column 8: "Refund Quantity")
                const quantityInput = row.querySelector('td:nth-child(8) input');

                if (quantityInput) {
                    quantityInput.value = quantity;
                    // Trigger change event
                    quantityInput.dispatchEvent(new Event('change', { bubbles: true }));
                    return {
                        success: true,
                        message: `Found card in row ${i + 1}, set quantity to ${quantity}, total cost: $${totalCost}`,
                        inputName: quantityInput.name,
                        totalCost: totalCost
                    };
                } else {
                    return { success: false, message: `Card found in row ${i + 1} but no quantity input`, totalCost: null };
                }
            }
        }

        return { success: false, message: `Card "${cardName}" not found in table`, totalCost: null };
    }
    """

    result = await page.evaluate(script, {'cardName': card_name, 'quantity': quantity})

    if result['success']:
        print(f"  ✓ {result['message']}")
        return True, result.get('totalCost')
    else:
        print(f"  ✗ {result['message']}")
        return False, None


async def submit_refund(page, dry_run=True):
    """
    Submit the refund form

    Args:
        dry_run: If True, don't actually click submit (for testing)
    """
    if dry_run:
        print("⚠️  DRY RUN - Would click submit button here")
        print("→ Simulating 5 second processing delay...")
        await asyncio.sleep(5)
        print("✓ Simulated refund submission complete")
        return True

    try:
        # Find and click submit button using exact XPath
        submit_button_xpath = '/html/body/div[4]/div/form/div[4]/input'
        print("→ Clicking Give Refund button...")

        # Set up ONE-TIME dialog handler BEFORE clicking the button
        # The dialog asks: "Are you sure you want to give a partial refund for this order?"
        async def handle_dialog(dialog):
            await dialog.accept()
            print("✓ Confirmation dialog accepted")

        page.once('dialog', handle_dialog)

        await page.click(f'xpath={submit_button_xpath}')

        # Wait a moment for dialog to appear and be handled
        await asyncio.sleep(1)

        # Wait for page to refresh back to order page after submission
        # The page automatically navigates back and shows a success banner
        print("→ Waiting for refund to process and page to refresh...")
        await page.wait_for_load_state("networkidle", timeout=60000)
        await asyncio.sleep(2)  # Extra buffer to ensure everything is stable

        print("✓ Refund submitted and page refreshed")
        return True
    except Exception as e:
        print(f"✗ Error during refund submission: {e}")
        return False


async def process_single_refund(page, refund, is_first_card=True):
    """
    Process a single refund from CSV row

    Args:
        refund: dict with keys from CSV (Order Link, Card Name, Quant., etc.)
        is_first_card: bool - True if this is the first card in the order (gets $1 credit)

    Returns:
        tuple: (success: bool, elapsed_time: float, error_reason: str or None)
    """
    start_time = time.time()

    order_url = refund.get('Order Link', '').strip()

    # Skip rows with invalid or missing order URLs
    if not order_url or '#REF!' in order_url or not order_url.startswith('http'):
        return True, 0, None, False, None, None

    # Handle different CSV formats - find card name column
    card_name = None
    for key in refund.keys():
        if 'Card Name' in key:
            card_name = refund[key]
            break

    if not card_name or not card_name.strip():
        # Skip empty rows
        return True, 0, None, False, None, None

    # Extract set name and condition from CSV
    set_name = refund['Set Name']
    condition = refund['Cond.']

    # Skip rows with empty quantity
    quant_str = refund.get('Quant.', '').strip()
    if not quant_str:
        # Skip rows with empty quantity
        return True, 0, None, False, None, None

    try:
        quantity = abs(int(float(quant_str)))
    except (ValueError, TypeError):
        # Skip rows with invalid quantity
        return True, 0, None, False, None, None

    print(f"\n{'='*80}")
    print(f"Order: {order_url}")
    print(f"Card: {card_name}")
    print(f"Set: {set_name}")
    print(f"Condition: {condition}")
    print(f"Quantity: {quantity}")
    print('='*80 + '\n')

    # Navigate to order page
    print(f"→ Opening order page...")
    try:
        await page.goto(order_url, timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(1)  # Let dynamic content load
        print("✓ Order page loaded\n")
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e).lower()

        # Categorize the error
        if 'timeout' in error_msg:
            if 'net::err' in error_msg or 'navigation' in error_msg:
                reason = "Already Refunded"
                print(f"✗ ALREADY REFUNDED - Order page failed to load ({elapsed:.1f}s)\n")
            else:
                reason = "Page Timeout"
                print(f"✗ PAGE TIMEOUT - Order page took too long to load ({elapsed:.1f}s)\n")
        else:
            reason = "Page Load Error"
            print(f"✗ PAGE LOAD ERROR - {e} ({elapsed:.1f}s)\n")

        return False, elapsed, reason, False

    # Check if order is international by reading shipping country
    is_international = await check_if_international(page)
    if is_international:
        print("→ International order detected\n")
    else:
        print("→ Domestic order detected\n")

    # Isolate widget containing the card (match on name, set, condition)
    # Retry up to 3 times in case page hasn't fully loaded
    widget_found = False
    for attempt in range(3):
        if await isolate_widget(page, card_name, set_name, condition):
            widget_found = True
            break
        else:
            if attempt < 2:  # Don't wait after last attempt
                print(f"  ⚠ Widget not found, waiting 2s and retrying (attempt {attempt + 1}/3)...")
                await asyncio.sleep(2)

    if not widget_found:
        elapsed = time.time() - start_time
        print(f"✗ CARD NOT FOUND - Widget isolation failed after 3 attempts ({elapsed:.1f}s)\n")
        return False, elapsed, "Card Not Found", is_international, None, None

    # Click Partial Refund button
    if not await click_partial_refund(page):
        elapsed = time.time() - start_time
        print(f"✗ ALREADY REFUNDED - Partial Refund button missing (card already processed) ({elapsed:.1f}s)\n")
        return False, elapsed, "Already Refunded", is_international, None, None

    # Wait for refund form to load - give extra time for page transition
    await page.wait_for_load_state("networkidle", timeout=30000)
    await asyncio.sleep(2)  # Extra wait for dynamic content

    # Wait for form elements to be present and visible
    # Only require the critical fields - inventory changes is optional
    try:
        await page.wait_for_selector('select#refundOrigin', state='visible', timeout=10000)
        await page.wait_for_selector('select#refundReason', state='visible', timeout=10000)
        print("✓ Refund form loaded\n")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ FORM LOAD ERROR - Refund form did not load properly ({elapsed:.1f}s)\n")
        return False, elapsed, "Form Load Error", is_international, None, None

    # Prepare refund data based on domestic vs international
    # Dropdown values are numeric IDs or exact text strings
    if is_international:
        # International orders: $5.99 credit (added manually, not via form checkbox)
        # Always use international message (no separate message for duplicate cards)
        message = "TCGplayer is fully refunding this card due to an unfortunate inventory issue. We have applied an additional $5.99 in store credit to your TCGplayer account so you can purchase it from another Seller on our site. We're sorry for any inconvenience this may cause you."
        store_credit = False  # Do NOT check box - manual credit needed

        if is_first_card:
            print("⚠️  INTERNATIONAL ORDER - Manual $5.99 store credit required!")
            print("   After refund completes, navigate to customer page and add $5.99")
            print("   Note: 'Product not in Direct Inventory Order #[ORDER_NUMBER]'\n")
    else:
        # Domestic orders: $1.00 credit via checkbox for first card only
        if is_first_card:
            message = "TCGplayer is fully refunding this card due to an unfortunate inventory issue. We have applied an additional $1.00 in store credit to your TCGplayer account so you can purchase it from another Seller on our site. We're sorry for any inconvenience this may cause you."
            store_credit = True
        else:
            message = "TCGplayer is fully refunding this card due to an unfortunate inventory issue. We're sorry for any inconvenience this may cause you."
            store_credit = False

    refund_data = {
        'refund_origin': '0',  # 0 = CSR Initiated, 1 = Seller Initiated, 2 = Buyer Initiated
        'refund_reason': 'Product - Inventory Issue',  # Exact text from dropdown
        'inventory_changes': 'True',  # True = Adjust Inventory, False = Do Not Adjust
        'message': message,
        'store_credit': store_credit,
        'quantity': quantity
    }

    # Fill form using card name to find correct row
    await fill_refund_form(page, refund_data)

    # Override generic quantity fill with card-specific row finding
    # Also extract total cost (qty already calculated in Cost column)
    success, total_cost = await find_card_row_and_fill_quantity(page, card_name, quantity)
    if not success:
        elapsed = time.time() - start_time
        print(f"✗ QUANTITY ERROR - Failed to fill quantity field ({elapsed:.1f}s)\n")
        return False, elapsed, "Quantity Fill Error", is_international, None, None

    # Calculate financial amounts
    # Note: card_price from Column 5 is already the total (quantity × unit price)
    original_amount = None
    cost_to_fix = None

    if total_cost is not None:
        # Original Amount = total from "Cost" column (already includes quantity)
        original_amount = total_cost

        # Cost to Fix = Original Amount + Store Credit
        if is_international and is_first_card:
            store_credit_amount = 5.99
        elif not is_international and is_first_card:
            store_credit_amount = 1.00
        else:
            store_credit_amount = 0.00

        cost_to_fix = original_amount + store_credit_amount

        print(f"  💰 Original Amount: ${original_amount:.2f} (from Cost column)")
        print(f"  💰 Store Credit: ${store_credit_amount:.2f}")
        print(f"  💰 Cost to Fix: ${cost_to_fix:.2f}\n")
    else:
        print("  ⚠️  Warning: Could not extract cost for calculation\n")

    # Submit refund (PRODUCTION MODE - WILL ACTUALLY SUBMIT!)
    submit_success = await submit_refund(page, dry_run=False)
    if not submit_success:
        elapsed = time.time() - start_time
        print(f"✗ SUBMIT ERROR - Failed to submit refund ({elapsed:.1f}s)\n")
        return False, elapsed, "Submit Error", is_international, original_amount, cost_to_fix

    # For international orders, add $5.99 store credit after refund
    if is_international and is_first_card:
        # Extract order number from URL or CSV
        order_number = refund.get('Order Number', '')
        if not order_number:
            # Try to extract from URL if not in CSV
            # URL format: https://store.tcgplayer.com/admin/Direct/Order/251020-402C
            order_number = order_url.split('/')[-1]

        # Navigate back to order page first (we may have navigated away during refund)
        await page.goto(order_url)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        # Add the $5.99 credit (PRODUCTION MODE - WILL ACTUALLY SAVE!)
        credit_success = await add_international_store_credit(page, order_number, dry_run=False)
        if not credit_success:
            elapsed = time.time() - start_time
            print(f"✗ STORE CREDIT ERROR - Failed to add international store credit ({elapsed:.1f}s)\n")
            return False, elapsed, "Store Credit Error", is_international, original_amount, cost_to_fix

    elapsed = time.time() - start_time
    print(f"✓ Refund processed successfully ({elapsed:.1f}s)\n")
    return True, elapsed, None, is_international, original_amount, cost_to_fix


async def save_csv_progress(csv_path, refunds, fieldnames):
    """
    Save updated CSV with current progress

    Args:
        csv_path: Path to CSV file
        refunds: List of refund dicts with updated status
        fieldnames: Original CSV column names
    """
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(refunds)
    print("✓ CSV progress saved")


async def main(csv_file):
    """Main automation flow"""

    # Read CSV
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_file}")
        return

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        refunds = list(reader)

    print(f"Found {len(refunds)} refunds to process\n")

    async with async_playwright() as p:
        # Use Chrome with your default profile for SSO support
        # Chrome profile location on macOS: ~/Library/Application Support/Google/Chrome
        chrome_user_data = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'

        context = await p.chromium.launch_persistent_context(
            str(chrome_user_data / 'Default'),  # Use Default profile, or change to 'Profile 1', 'Profile 2', etc.
            headless=False,
            channel='chrome',
            viewport={'width': 1280, 'height': 1080},
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # Login once
        await login_to_tcgplayer(page)

        # Process each refund
        success_count = 0
        failed_count = 0
        domestic_count = 0
        international_count = 0
        domestic_times = []
        international_times = []
        processed_orders = set()  # Track ALL orders we've seen (not just previous)
        times = []
        error_categories = {}  # Track error reasons
        script_start = time.time()

        try:
            for i, refund in enumerate(refunds, 1):
                print(f"\n{'#'*80}")
                print(f"Refund {i}/{len(refunds)}")
                print('#'*80)

                # Check if this is the first card in this order
                # Orders may not be consecutive in CSV, so track all seen orders
                current_order = refund.get('Order Link', '')
                is_first_card = (current_order not in processed_orders)
                if current_order:
                    processed_orders.add(current_order)

                success, elapsed, error_reason, is_international, original_amount, cost_to_fix = await process_single_refund(page, refund, is_first_card)
                if success and elapsed > 0:  # elapsed > 0 means it was actually processed
                    success_count += 1
                    times.append(elapsed)
                    # Track domestic vs international
                    if is_international:
                        international_count += 1
                        international_times.append(elapsed)
                    else:
                        domestic_count += 1
                        domestic_times.append(elapsed)

                    # Update CSV: Mark as solved and add financial data
                    refund['Solved?'] = 'TRUE'
                    if original_amount is not None:
                        refund['Original Amount'] = f'${original_amount:.2f}'
                    if cost_to_fix is not None:
                        refund['Cost to Fix'] = f'${cost_to_fix:.2f}'
                    await save_csv_progress(csv_path, refunds, fieldnames)

                elif not success:
                    failed_count += 1
                    # Track error category
                    if error_reason:
                        error_categories[error_reason] = error_categories.get(error_reason, 0) + 1

                    # Update CSV: Mark as failed with error reason
                    refund['Solved?'] = f'FAILED: {error_reason}' if error_reason else 'FAILED'
                    await save_csv_progress(csv_path, refunds, fieldnames)

                # Small delay between refunds
                await asyncio.sleep(2)
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user (Ctrl+C)")

        total_time = time.time() - script_start
        skipped_count = len(refunds) - success_count - failed_count

        print(f"\n{'='*80}")
        print(f"SUMMARY:")
        print(f"  Success: {success_count}/{len(refunds)} refunds processed")

        # Domestic vs International breakdown
        if domestic_count > 0 or international_count > 0:
            print(f"\n  Order Type Breakdown:")
            if domestic_count > 0:
                print(f"    - Domestic: {domestic_count}")
            if international_count > 0:
                print(f"    - International: {international_count}")

        if failed_count > 0:
            print(f"\n  Failed: {failed_count} refunds")
            if error_categories:
                print(f"\n  Failure Breakdown:")
                for error_type, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {error_type}: {count}")
        if skipped_count > 0:
            print(f"\n  Skipped: {skipped_count} invalid rows")

        print(f"\nTiming Statistics:")
        print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f}m)")

        if times:
            avg_time = sum(times) / len(times)
            print(f"  Overall average: {avg_time:.1f}s per refund")
            print(f"  Overall rate: {3600/avg_time:.0f} refunds/hour")

        if domestic_times:
            domestic_avg = sum(domestic_times) / len(domestic_times)
            print(f"\n  Domestic average: {domestic_avg:.1f}s per refund")
            print(f"  Domestic rate: {3600/domestic_avg:.0f} refunds/hour")

        if international_times:
            intl_avg = sum(international_times) / len(international_times)
            print(f"\n  International average: {intl_avg:.1f}s per refund")
            print(f"  International rate: {3600/intl_avg:.0f} refunds/hour")

        print('='*80)

        # Keep browser open for inspection
        print("\nBrowser left open - press Ctrl+C to close")
        try:
            await asyncio.sleep(3600)
        except KeyboardInterrupt:
            print("\n\n✓ Closing browser...")

        await context.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 tcgplayer_direct_selectors.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    asyncio.run(main(csv_file))
