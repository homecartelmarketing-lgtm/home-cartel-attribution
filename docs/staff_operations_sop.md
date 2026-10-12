# Standard Operating Procedure (SOP): Sales & Support Staff Compliance

**System**: Ad-to-Sale Attribution System  
**Audience**: Sales Representatives, Customer Support Agents, Order Entry Staff  
**Mandatory Compliance**: Go-live and attribution accuracy strictly depend on adhering to these 5 rules.

---

## Rule 1: Mandatory Customer Contact Details Capture (T13)
*Goal: Ensure at least 80% of all Sales Orders have real email AND phone numbers.*

- When entering a quote or converting an order in Zoho Books, **always record both**:
  1. **Customer Email Address** (valid, active email)
  2. **Customer Mobile Number** formatted in standard Philippine format (`09XXXXXXXXX` or `+63 9XXXXXXXXX`)
- **Why this matters**: Meta Conversions API uses cryptographic SHA-256 hashes of email and phone to link offline cash payments back to the exact ad impression. If contact details are missing, Meta cannot optimize ad bidding.

---

## Rule 2: Sales Order Creation Within 24 Hours of Payment (T14)
*Goal: Preserve algorithmic attribution window.*

- Every confirmed payment or deposit must have a formal **Sales Order created in Zoho Books within 24 hours**.
- Do not accumulate orders to batch-create at the end of the week.
- Orders created late degrade ad bidding responsiveness and skew weekly attribution analysis.

---

## Rule 3: Never Fabricate or Tamper With Tracking Fields (T18)
*Goal: Preserve data integrity.*

- Custom fields (`Session Token`, `FB Click ID`, `UTM Source`, etc.) are auto-populated by the system.
- If a walk-in, returning customer, or organic referral contacts the store directly without clicking an ad:
  - **Leave tracking fields completely blank**.
  - **Do NOT invent fake tokens** (e.g. do not enter "N/A", "NONE", or random numbers).
  - The system is built to measure true incremental ad performance; fabricated tokens contaminate algorithmic training.

---

## Rule 4: Strict Multi-Brand Channel Separation (T17)
*Goal: Prevent cross-brand data contamination.*

- Each brand must operate on its own independent communication channels:
  - Distinct WhatsApp Business phone numbers
  - Distinct Facebook Business Pages
  - Distinct Viber Business accounts
  - Distinct inquiry email addresses
- Never direct customers of Brand B to Home Cartel's messaging channels.

---

## Rule 5: Channel Inbound Discipline (T32)
*Goal: Avoid bypassing Zendesk.*

- All customer inquiries from messaging channels must route into Zendesk tickets.
- Do not conduct transactions purely through personal chat apps without generating an official Zendesk inquiry record and Zoho Books order.
- Bypassing Zendesk causes untracked sales leaks where Meta cannot receive attribution feedback.
