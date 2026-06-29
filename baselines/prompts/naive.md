You are evaluating a procurement compliance task.

Read the documents and bidder/protester action log. Determine whether the action is procedurally valid.

Return JSON only using this schema:

{
  "governing_clause_id": "...",
  "operative_deadline": "...",
  "action_datetime": "...",
  "required_bid_security_validity_through": "...",
  "submitted_bid_security_validity_through": "...",
  "precondition_status": "satisfied | unsatisfied | not_evaluated | unknown",
  "verdict": "VALID | INVALID",
  "failure_reason_code": "...",
  "citation": {...}
}

Do not include prose outside JSON.
