# Testing Guide - Navigate413

## Quick Test with Sample Documents

### Sample Financial Aid Letter (FINANCE Domain)

Create a test file `test_finance.txt`:
```
FINANCIAL AID AWARD LETTER - Spring 2026

Dear Student,

This letter confirms your financial aid package for the 2026 academic year.

GRANT AWARD: $5,000
- Academic Achievement Grant: $3,000
- Need-Based Grant: $2,000

LOAN OPTIONS:
- Federal Subsidized Loan: $3,500 (annual limit)
- Federal Parent PLUS Loan: $25,000 (program limit)

IMPORTANT CONDITIONS:
1. Failure to maintain enrollment in at least 12 credit hours will result in 
   immediate cancellation of all grants and aid.

2. Your FAFSA must be submitted by March 1, 2026, or you will lose eligibility 
   for the need-based portion of your aid.

3. Academic Standing Requirement: Maintain a minimum GPA of 2.0. Failure to meet 
   this standard will trigger a financial hold and suspension of future aid.

4. Work Study Position Available: Up to 20 hours/week at $15.50/hour through the 
   Campus Employment Office.

PENALTIES FOR NON-COMPLIANCE:
- Late FAFSA submission: Loss of $2,000 need-based grant
- Dropping below full-time: Prorated aid reduction
- GPA below 2.0: All aid suspended until academic probation lifted

Please contact the Financial Aid Office with questions.
```

Expected Analysis:
- Domain: `finance`
- Risk Level: `HIGH` (risk_score > 0.7)
- Key obligations: Full-time enrollment, FAFSA by March 1, maintain 2.0 GPA
- Key deadline: March 1, 2026

---

### Sample Housing Lease (HOUSING Domain)

Create a test file `test_housing.txt`:
```
RESIDENTIAL LEASE AGREEMENT - 2026 Academic Year

PARTIES: University Housing and Student

LEASE TERM: August 1, 2026 - May 31, 2027 (10 months)

MONTHLY RENT: $800
SECURITY DEPOSIT: $500
TOTAL: $8,500

EARLY TERMINATION CLAUSE:
If the student wishes to terminate this lease before the end date, the following 
penalties apply:

1. Base Termination Fee: $500 (non-refundable)
2. Per-Month Penalty: $200 per month remaining on lease
   Example: Leaving after 3 months = $500 + (7 months × $200) = $1,900

LIABILITY AND DAMAGES:
The student is responsible for all damages to the unit beyond normal wear and tear.
Damages are charged at actual repair/replacement cost. Examples:
- Broken window: $250-500
- Stains/marks on carpet: $25-100 per sq ft
- Missing furniture: Full replacement cost ($400+)

ROOMMATE DISPUTES:
In case of roommate conflict, the Housing Office may reassign students. 
If reassignment is not possible, students remain jointly liable for rent.

PAYMENT TERMS:
- Rent due by the 1st of each month
- $50 late fee if payment is 5+ days late
- Failure to pay for 30 days may result in eviction proceedings

PROHIBITED ITEMS:
Hot plates, candles, incense, pets (except service animals)
Violation may result in $200 fine and item confiscation.
```

Expected Analysis:
- Domain: `housing`
- Risk Level: `HIGH` (early termination penalties)
- Key obligations: Pay $800/month, no prohibited items
- Extracted parameters: base_penalty=$500, penalty_rate_per_month=$200

---

### Sample Visa/Compliance Document (VISA Domain)

Create a test file `test_visa.txt`:
```
FORM I-20 - CERTIFICATE OF ELIGIBILITY FOR NONIMMIGRANT STUDENT STATUS

Student Name: [Redacted]
SEVIS ID: N123456789

SCHOOL: University of Massachusetts Amherst
Program: Master of Science in Computer Science
Academic Period: January 2026 - December 2027

ELIGIBILITY REQUIREMENTS:
1. Full-Time Enrollment: F-1 students MUST be enrolled in at least 12 credit 
   hours per semester. Dropping below full-time without approval will result 
   in automatic status violation.

2. Work Authorization: 
   - On-Campus Employment: Up to 20 hours/week during school, full-time during 
     official breaks
   - Curricular Practical Training (CPT): Requires prior DSO approval
   - Optional Practical Training (OPT): Available upon graduation with I-20 
     amendment

3. Travel: Any travel outside the US requires proper I-20 signature and 
   re-entry documentation. Traveling without signature may result in 
   inability to return to the US.

4. Academic Progress: Must maintain satisfactory academic progress. Failing 
   grades may impact visa status.

5. Reporting Requirements:
   - Immediately report any change of address to International Programs Office
   - Report any employment changes to DSO
   - Annual visa status review required

PENALTIES FOR VIOLATIONS:
- Dropping below full-time without approval: Status violation, possible deportation
- Unauthorized employment: Criminal penalties + deportation
- Failure to report changes: Compliance violation
- Academic failure: Loss of visa status

Your current authorized status expires: December 31, 2027
```

Expected Analysis:
- Domain: `visa`
- Risk Level: `AT_RISK` (strict compliance requirements)
- Key obligations: Full-time enrollment, report changes, authorized work only
- Risk factors: Multiple compliance requirements, potential visa violation risks

---

## Testing Workflow

### 1. Manual API Testing with cURL

```bash
# Save test document
cat > test_finance.txt << 'EOF'
FINANCIAL AID AWARD LETTER...
EOF

# Convert to PDF (on macOS):
textutil -convert pdf test_finance.txt -output test_finance.pdf

# Upload
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/upload \
  -F "file=@test_finance.pdf" | jq -r '.session_id')

echo "Session ID: $SESSION_ID"

# Wait for processing (check status)
sleep 5
curl http://localhost:8000/api/session/$SESSION_ID | jq '.processed_flag'

# Analyze
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}" | jq '.'

# Translate
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"target_language\": \"Spanish\"}" | jq '.'
```

### 2. Frontend Testing

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Upload test PDF
5. View analysis results
6. Test translation dropdown
7. Test scenario simulator (for housing)

### 3. Verify Key Features

**Checklist:**
- [ ] Upload accepts PDF files
- [ ] Session status updates (processed_flag changes)
- [ ] Correct domain classification
- [ ] Risk score generates (0-1 range)
- [ ] Clauses extracted with flags
- [ ] Obligations list populated
- [ ] Translation dropdown works
- [ ] Scenario simulator appears for housing/finance
- [ ] Campus resources show (max 3)
- [ ] Plain language summary is understandable

---

## Expected Results

### Finance Document
```
domain: "finance"
risk_score: 0.65-0.75 (HIGH)
risk_level: "HIGH"
clauses: [
  {flag: "ENROLLMENT_REQUIREMENT", risk_contribution: 0.35},
  {flag: "FAFSA_DEADLINE", risk_contribution: 0.25},
  {flag: "GPA_REQUIREMENT", risk_contribution: 0.15}
]
obligations: ["Maintain full-time enrollment", "File FAFSA by March 1", "Keep 2.0+ GPA"]
deadlines: ["March 1, 2026"]
```

### Housing Document
```
domain: "housing"
risk_score: 0.70-0.80 (HIGH)
risk_level: "HIGH"
clauses: [
  {flag: "EARLY_TERMINATION_PENALTY", risk_contribution: 0.40},
  {flag: "LIABILITY_CLAUSE", risk_contribution: 0.30}
]
obligations: ["Pay rent by 1st of month", "Maintain unit condition"]
scenario parameters: {base_penalty: 500, penalty_rate_per_month: 200}
```

### Visa Document
```
domain: "visa"
risk_score: 0.5 (AT_RISK)
risk_level: "AT_RISK"
clauses: [
  {flag: "ENROLLMENT_REQUIREMENT", explanation: "Must maintain full-time status"},
  {flag: "WORK_AUTHORIZATION", explanation: "Work limited to approved positions"}
]
```

---

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Verify MongoDB connection
python3 -c "import pymongo; print('MongoDB driver OK')"
```

### Frontend Components Not Showing
- Check browser console for errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS configuration in backend

### Gemini API Errors
- Verify API key in `.env`
- Check Gemini API quota and rate limits
- Check for typos in prompt structure

### MongoDB Connection Issues
- Verify `MONGODB_URI` in `.env`
- Test connection: `mongo "{MONGODB_URI}"`
- Check IP whitelist in MongoDB Atlas

---

## Performance Notes

- Text extraction: 2-5 seconds (depends on PDF size)
- Gemini API calls: 1-3 seconds each (3 agents run sequentially)
- Total analysis time: 10-20 seconds
- Translation: 2-3 seconds
- Scenario simulation: <100ms (deterministic)

---

## Next Testing Priorities

1. ✅ Single document upload and analysis
2. ⏳ Multiple document types (finance, housing, visa)
3. ⏳ Translation accuracy
4. ⏳ Scenario calculations
5. ⏳ Frontend UX polish
6. ⏳ Error handling (bad files, timeouts)
7. ⏳ Performance optimization
