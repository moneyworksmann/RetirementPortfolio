# Retirement Portfolio Evaluator

A beginner-friendly tool to evaluate and improve your retirement accounts and portfolio.

## Overview

The Retirement Portfolio Evaluator helps you understand whether your current retirement accounts (401(k), IRA, Roth IRA, taxable accounts, etc.) are well allocated for your goals and time horizon. It provides simple, actionable guidance, clear projections, and plain-English explanations so beginners can make better decisions.

## Features

- Evaluate multiple retirement accounts and balances
- Suggest age-appropriate asset allocations (stocks vs bonds)
- Show projected balances to retirement under simple assumptions
- Provide a risk score and plain-language recommendations
- Beginner-friendly explanations and next steps

## Who this is for

This project is for people who:
- Are new to investing or retirement planning
- Want a quick sanity-check of their account allocations
- Prefer clear, actionable advice rather than jargon

## Quick Start

Prerequisites:
- Python 3.10+ (or the runtime used by the project)

To get started (example commands — adapt to the project's actual entrypoint):

1. Clone the repo:

```bash
git clone https://github.com/moneyworksmann/RetirementPortfolio.git
cd RetirementPortfolio
```

2. (Optional) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run the evaluator (example):

```bash
python evaluate.py --input example_portfolio.json
```

Replace the command above with the actual script or UI entrypoint provided by the project.

## Usage (what to provide)

- Account types: 401(k), Traditional IRA, Roth IRA, Taxable
- Current balances for each account
- Your age and planned retirement age
- Annual contributions (optional)
- Risk tolerance (conservative / moderate / aggressive) — optional

The evaluator will return:
- Suggested target allocation (e.g., 70% stocks / 30% bonds)
- A risk score (0–100) with interpretation
- Projected retirement balances under baseline assumptions
- Plain-language recommendations (rebalance, increase contributions, tax-smart moves)

## Interpreting results (beginner-friendly)

- Suggested allocation: A recommended mix of stocks and bonds tailored to your time horizon.
- Risk score: Higher means more exposure to stock-market swings — good for long horizons, risky if retirement is near.
- Projection: An estimate, not a guarantee. It assumes constant returns and does not account for taxes, market crashes, or changing contributions.

Example actions you might take after seeing results:
- Rebalance your accounts to the suggested allocation gradually.
- Increase your monthly contributions if projections look short.
- Consider tax-advantaged moves (Roth conversions, catch-up contributions) with a tax advisor.

## Example

Sample input (JSON):

```json
{
	"age": 35,
	"retirement_age": 67,
	"accounts": [
		{"type": "401k", "balance": 45000, "contribution_annually": 6000},
		{"type": "Roth IRA", "balance": 12000, "contribution_annually": 6000}
	],
	"risk_tolerance": "moderate"
}
```

Sample output (plain text):

```
Suggested allocation: 80% stocks / 20% bonds
Risk score: 64 (Moderate)
Projected balance at 67: $1,200,000 (assumes 6% annual returns)
Recommendations: Increase 401(k) contributions to employer match; rebalance quarterly.
```

## FAQ

- Q: Is this financial advice?
- A: No. This tool provides educational estimates and suggestions. Consult a licensed financial advisor for personalized advice.

- Q: How accurate are the projections?
- A: Projections use simplifying assumptions (constant returns, no taxes). Use them as directional guidance only.

## Contributing

Contributions are welcome. If you'd like to help:

1. Open an issue describing the improvement.
2. Fork the repo, make changes on a feature branch, and open a pull request.

Please follow standard open-source etiquette and include tests for new features when possible.

## License

Provide license information here (e.g., MIT). If no license is specified, include one or clarify terms.

## Contact

Questions or feedback: open an issue or contact the repository owner.

---

If you'd like, I can (1) tailor the Quick Start commands to the project's actual entrypoint, (2) add a sample `example_portfolio.json`, or (3) implement a minimal `evaluate.py` runner to demonstrate the workflow. Which would you prefer?