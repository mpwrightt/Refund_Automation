# Pull Discrep Refunds (Confirmed Missing Cards) - SOP

**Source:** https://tcgplayer.atlassian.net/wiki/spaces/CSR/pages/5226627217/Pull+Discrep+Refunds+Confirmed+Missing+Cards

**Last Retrieved:** 2025-11-12

---

## Overview

Refunding cards not found in the pulling process by Shipping Generalists, or in discrepancy solving process by Inventory Specialists.

## Required Access
- [Inventory Refund Log](https://docs.google.com/spreadsheets/d/1raaUEsPoMl5dEZwilnHtBwdR0wOV2JRqYzdlVYMdohI/edit?gid=1331496674#gid=1331496674)
- [Discrepancy Help Docs](https://docs.google.com/spreadsheets/d/1hrKt4XvlxytyY2ZqYVXjCOAS97WzNWnxaHOzLc0kv_c/edit?gid=0#gid=0)
- [Discrepancy Log](https://docs.google.com/spreadsheets/d/1m0dSOA2VogToEpAo6Jj7FEEsfJbWi1W48xiyTHkBNyY/edit?pli=1&gid=1984354615#gid=1984354615)
- [Admin Panel](https://store.tcgplayer.com/admin/Direct)

---

## CRITICAL REFUND RULES

### 1. Refund Macros (Messages)

**First card in an order (Domestic):**
```
TCGplayer is fully refunding this card due to an unfortunate inventory issue. We have applied an additional $1.00 in store credit to your TCGplayer account so you can purchase it from another Seller on our site. We're sorry for any inconvenience this may cause you.
```

**Second/additional cards in SAME order (Duplicate refund):**
```
TCGplayer is fully refunding this card due to an unfortunate inventory issue. We're sorry for any inconvenience this may cause you.
```

**International orders:**
```
TCGplayer is fully refunding this card due to an unfortunate inventory issue. We have applied an additional $5.99 in store credit to your TCGplayer account so you can purchase it from another Seller on our site. We're sorry for any inconvenience this may cause you.
```

### 2. Store Credit Rules

**Domestic Orders:**
- ✅ Apply $1.00 store credit via checkbox on refund form
- ✅ Only for FIRST card in each order
- ❌ NOT for second/additional cards in SAME order
- ✅ If same customer but DIFFERENT orders = apply again

**International Orders:**
- ❌ Do NOT check $1.00 store credit box on refund form
- ✅ Instead: Navigate to customer page → Add $5.99 store credit manually
- ✅ Note: "Product not in Direct Inventory Order #XXXXXXXX"

### 3. Refund Reason Dropdown
**Always select:** `Product - Inventory Issue`

---

## Setup for Refunds

1. Log into the old Seller Portal Admin Panel
2. Open the Refund Log spreadsheet
3. Check for entries older than today's date
   - Any entries from today's date are ignored (cards might still be found)

---

## Solving Refunds - Step by Step

### 1. Claim Your Batch
- Go to first unsolved order in Refund Log
- Type your initials in "Initials" column (e.g., "HiO")
- Solved orders have initials + monetary value in "Original Amount" column

### 2. Open the Order
- Click the order hyperlink in the Refund Log
- Opens in Admin Panel

### 3. Find the Card
- Use Ctrl/Cmd + F to search for the card name
- ⚠️ **CRITICAL:** Verify correct condition and set match
  - Check: Card name, Set name, Condition (NM, LP, etc.)
  - If multiple copies exist, verify printing type (Extended Art, etc.)

### 4. Click Partial Refund
- Find the section containing YOUR card
- ⚠️ **CRITICAL:** There may be 40+ "Partial Refund" buttons on the page
- Click "Partial Refund" for THAT specific section only
- **Tip:** Right-click → Open in new window

### 5. Fill Refund Form

**Bottom of page:**
1. Find your card in the list
2. Enter quantity in "Refund Quantity" box

**Top of page:**
3. **Refund Reason dropdown:** Select `Product - Inventory Issue`
4. **Message box:** Enter appropriate macro (see CRITICAL REFUND RULES above)
5. **Store Credit checkbox:**
   - ✅ Check if FIRST card in order (domestic only)
   - ❌ Uncheck if second/additional card in same order
   - ❌ Do NOT check for international orders

### 6. Submit Refund
- Enter refund amount in "Original Amount" column in Refund Log
- Click "Give Refund" button
- Confirm "Are you sure?" prompt

### 7. Full Refund (One Card Orders)
- If ENTIRE order is being refunded, use "Full Refund" button instead
- Refunds card price + shipping
- **Still apply $1.00 store credit checkbox** (domestic orders)

---

## International Refund Process

### Differences from Domestic:
1. ❌ **Do NOT check $1.00 store credit box** on refund form
2. ✅ Use "International Refund" macro (includes $5.99 mention)
3. ✅ Manually add $5.99 store credit:
   - Click button beside customer email
   - Find "Store Credit" box → "Add/Remove Store Credit"
   - Enter: Amount = 5.99
   - Note: "Product not in Direct Inventory Order #XXXXXXXX"
   - Click Save
4. Proceed with rest of refund normally

---

## Bot Implementation Checklist

### ✅ Currently Implemented:
- Navigate to order page
- Find card by name, set, condition
- Click correct Partial Refund button (DOM traversal to find card's section)
- Enter quantity
- Select "Product - Inventory Issue" from dropdown
- Enter refund message
- Apply $1.00 store credit (first card only)
- Track order changes (reset store credit flag per order)

### ⚠️ VERIFY Against SOP:

**Message Macros:**
- [ ] First card message matches SOP exactly
- [ ] Second card uses "Duplicate refund" macro (currently using same message)
- [ ] International message included $5.99 (not yet implemented)

**Store Credit Logic:**
- [x] $1.00 for first card in each order
- [x] NOT for second card in same order
- [ ] International: Do NOT check box, add $5.99 manually instead

**Refund Reason:**
- [x] Uses "Product - Inventory Issue" dropdown

**Missing Features:**
- [ ] International order detection (yellow highlight)
- [ ] International $5.99 manual store credit workflow
- [ ] Full refund logic (one card orders)
- [ ] Duplicate order handling (blue highlight)

---

## Automation Gaps Identified

### 1. Message Macro Issue
**SOP says:** Use different message for 2nd+ cards in same order
**Bot does:** Uses same message for all cards

**Fix needed:** Detect if this is 2nd+ card in SAME order, use "Duplicate refund" macro

### 2. International Orders
**SOP says:**
- Do NOT check $1.00 store credit box
- Add $5.99 manually to customer account
- Use different message

**Bot does:** Not yet implemented

**Fix needed:**
- Detect international orders (yellow highlight in CSV or order page?)
- Skip $1.00 checkbox
- Navigate to customer page, add $5.99 credit
- Use international message

### 3. Full Refund
**SOP says:** Use "Full Refund" button for one-card orders

**Bot does:** Always uses Partial Refund

**Fix needed:** Detect if order has only one card, use Full Refund button instead

---

## Testing Checklist

Before running on 15,000 refunds, verify:
- [ ] Correct Partial Refund button clicked (not first, but card's specific section)
- [ ] First card in order gets $1.00 store credit
- [ ] Second card in SAME order does NOT get store credit
- [ ] Different order from same customer DOES get $1.00 again
- [ ] Message matches SOP exactly
- [ ] "Product - Inventory Issue" selected
- [ ] Quantity filled correctly
- [ ] Form submitted successfully

---

**Notes:**
- Our bot currently uses a single message template (from REFUND_MESSAGE variable)
- SOP specifies TWO different messages (first vs duplicate)
- International workflow not yet automated
- Full refund logic not implemented
