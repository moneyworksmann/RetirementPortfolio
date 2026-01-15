# Retirement Portfolio Calculator

def _monthly_rate(annual_return_rate):
    return annual_return_rate / 12.0

def simulate_buckets_monthly(current_pre_tax, current_after_tax, monthly_pre_tax, monthly_after_tax, annual_return_rate, months):
    """
    Simulate two buckets (pre-tax and after-tax) monthly and return:
      - yearly_totals: list of total balances at each year (including year 0)
      - final_pre_tax_balance, final_after_tax_balance
      - pre_tax_principal_total, after_tax_principal_total (principals contributed, including starting amounts)
    """
    monthly_rate = _monthly_rate(annual_return_rate)
    pre = current_pre_tax
    after = current_after_tax

    yearly_totals = [pre + after]  # year 0
    # Track principal amounts: starting amounts count towards principal
    # We'll compute principal totals analytically (starting + monthly contributions * months)
    for month in range(1, months + 1):
        pre += monthly_pre_tax
        after += monthly_after_tax
        pre *= (1 + monthly_rate)
        after *= (1 + monthly_rate)
        if month % 12 == 0:
            yearly_totals.append(pre + after)

    pre_tax_principal_total = current_pre_tax + monthly_pre_tax * months
    after_tax_principal_total = current_after_tax + monthly_after_tax * months

    return {
        "yearly_totals": yearly_totals,
        "final_pre_tax_balance": pre,
        "final_after_tax_balance": after,
        "pre_tax_principal_total": pre_tax_principal_total,
        "after_tax_principal_total": after_tax_principal_total,
    }

def calculate_portfolio(current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate,
                        contribution_is_after_tax=True, current_tax_rate=0.22, percent_current_pre_tax=100.0,
                        tax_model="all_withdrawals_taxed", retirement_tax_rate=0.22):
    """
    Calculate yearly balances and after-tax outcomes for Roth and Traditional interpretations.

    Parameters:
      - contribution_is_after_tax: True if the slider value represents after-tax dollars (you pay tax now).
        If False, the slider represents a pre-tax deductible contribution.
      - current_tax_rate: current marginal tax rate (0..1)
      - percent_current_pre_tax: percent (0..100) of current_savings that is pre-tax (the rest is after-tax)
      - tax_model: "all_withdrawals_taxed" or "tax_gains_only"
      - retirement_tax_rate: tax rate at withdrawal time (0..1)

    Returns a dict containing yearly series and summary metrics.
    """
    years_to_retirement = max(0, retirement_age - current_age)
    months = years_to_retirement * 12

    # Interpret the input monthly_contribution according to contribution_is_after_tax:
    # If the input is after-tax:
    #   - Roth monthly = input
    #   - Traditional monthly (pre-tax) = input / (1 - current_tax_rate)  (because pre_tax * (1-current_tax_rate) = after-tax cash outflow)
    # If the input is pre-tax:
    #   - Traditional monthly (pre-tax) = input
    #   - Roth monthly (after-tax) = input * (1 - current_tax_rate) (because you'd pay tax now)
    denom = max(1e-9, 1.0 - current_tax_rate)
    if contribution_is_after_tax:
        roth_monthly_after_tax = monthly_contribution
        trad_monthly_pre_tax = monthly_contribution / denom
    else:
        trad_monthly_pre_tax = monthly_contribution
        roth_monthly_after_tax = monthly_contribution * (1.0 - current_tax_rate)

    # Split current savings into pre-tax and after-tax portions
    current_pre_tax = current_savings * (percent_current_pre_tax / 100.0)
    current_after_tax = current_savings - current_pre_tax

    # Simulate Roth: everything in Roth is after-tax
    roth_sim = simulate_buckets_monthly(
        current_pre_tax=0.0,  # Roth held after-tax bucket only for this model (user can set percent_current_pre_tax to move funds between)
        current_after_tax=current_pre_tax + current_after_tax if False else current_after_tax + current_pre_tax if False else current_after_tax,
        # Note: to keep semantics sane, treat current_savings as after-tax for Roth only if user indicates it's after-tax.
        # We'll instead model Roth as receiving only after-tax contributions; starting after-tax portion is current_after_tax.
        monthly_pre_tax=0.0,
        monthly_after_tax=roth_monthly_after_tax,
        annual_return_rate=annual_return_rate,
        months=months,
    )
    # The above has intentionally conservative assumption: current_pre_tax is treated not in Roth (unless user sets percent_current_pre_tax accordingly).
    # For clarity, simpler approach: treat current_after_tax as starting after-tax in Roth; ignore current_pre_tax for Roth unless user explicitly converted.
    roth_sim = simulate_buckets_monthly(
        current_pre_tax=0.0,
        current_after_tax=current_after_tax,
        monthly_pre_tax=0.0,
        monthly_after_tax=roth_monthly_after_tax,
        annual_return_rate=annual_return_rate,
        months=months,
    )

    # Simulate Traditional: contributions typically pre-tax; allow any after-tax contributions too (but by default monthly_after_tax=0)
    trad_sim = simulate_buckets_monthly(
        current_pre_tax=current_pre_tax,
        current_after_tax=current_after_tax if False else 0.0,  # assume current_after_tax isn't inside Traditional unless user placed it there
        monthly_pre_tax=trad_monthly_pre_tax,
        monthly_after_tax=0.0,
        annual_return_rate=annual_return_rate,
        months=months,
    )

    # Build yearly series (we want same length for both; for Roth we used starting after-tax only)
    # For readability, we'll return gross balances (sum of buckets) for each account:
    years = list(range(0, years_to_retirement + 1))
    roth_yearly = roth_sim["yearly_totals"]
    trad_yearly = trad_sim["yearly_totals"]

    # Final gross balances
    final_roth_gross = roth_yearly[-1] if roth_yearly else (current_after_tax if current_after_tax else 0.0)
    final_trad_gross = trad_yearly[-1] if trad_yearly else (current_pre_tax if current_pre_tax else 0.0)

    # Compute after-tax final values according to tax_model
    def compute_traditional_after_tax(sim):
        pre_tax_final = sim["final_pre_tax_balance"]
        after_tax_final = sim["final_after_tax_balance"]
        pre_tax_principal = sim["pre_tax_principal_total"]
        after_tax_principal = sim["after_tax_principal_total"]
        gross = pre_tax_final + after_tax_final
        principal_total = pre_tax_principal + after_tax_principal
        gains = gross - principal_total
        # Under "all_withdrawals_taxed": tax the pre-tax bucket (which includes pre-tax principal + earnings on it)
        if tax_model == "all_withdrawals_taxed":
            # Tax only the pre-tax bucket at retirement_tax_rate; after-tax bucket not taxed again
            taxed_part = pre_tax_final
            return after_tax_final + taxed_part * (1.0 - retirement_tax_rate)
        elif tax_model == "tax_gains_only":
            # Tax only the gains portion at retirement_tax_rate
            taxable_gains = max(0.0, gains)
            return gross - taxable_gains * retirement_tax_rate
        else:
            # Fallback to conservative "all taxed"
            taxed_part = pre_tax_final
            return after_tax_final + taxed_part * (1.0 - retirement_tax_rate)

    final_roth_after_tax = final_roth_gross  # Roth withdrawals assumed tax-free
    final_trad_after_tax = compute_traditional_after_tax(trad_sim)

    # Net monthly cash outflows (what user actually pays each month from pocket)
    if contribution_is_after_tax:
        net_monthly_roth = roth_monthly_after_tax
        # Traditional pre-tax contribution -> out-of-pocket is pre_tax * (1 - current_tax_rate)
        net_monthly_trad = trad_monthly_pre_tax * (1.0 - current_tax_rate)
    else:
        # input is pre-tax amount: user pays pre-tax * (1 - current_tax_rate) out-of-pocket for Traditional
        net_monthly_trad = trad_monthly_pre_tax * (1.0 - current_tax_rate)
        # Roth monthly after-tax is computed above
        net_monthly_roth = roth_monthly_after_tax

    metrics = {
        "final_roth_gross": final_roth_gross,
        "final_roth_after_tax": final_roth_after_tax,
        "final_trad_gross": final_trad_gross,
        "final_trad_after_tax": final_trad_after_tax,
        "net_monthly_roth": net_monthly_roth,
        "net_monthly_trad": net_monthly_trad,
        "years_to_retirement": years_to_retirement,
    }

    return {
        "years": years,
        "roth_yearly": roth_yearly,
        "trad_yearly": trad_yearly,
        "metrics": metrics,
        "assumptions": {
            "contribution_is_after_tax": contribution_is_after_tax,
            "current_tax_rate": current_tax_rate,
            "retirement_tax_rate": retirement_tax_rate,
            "percent_current_pre_tax": percent_current_pre_tax,
            "tax_model": tax_model,
            "roth_monthly_after_tax": roth_monthly_after_tax,
            "trad_monthly_pre_tax": trad_monthly_pre_tax,
        }
    }

def find_equivalent_roth_monthly(current_age, retirement_age, current_savings, input_monthly, annual_return_rate,
                                contribution_is_after_tax, current_tax_rate, percent_current_pre_tax,
                                tax_model, retirement_tax_rate, tol=1.0):
    """
    Find the after-tax monthly Roth contribution (the amount invested into Roth each month)
    that yields approximately the same after-tax retirement value as the Traditional account
    given the input_monthly interpreted according to contribution_is_after_tax.

    Returns the after-tax monthly Roth contribution (dollars out of pocket per month).
    """
    # Compute the target (Traditional after-tax final value) using the provided interpretation of input_monthly
    comp_trad = calculate_portfolio(
        current_age, retirement_age, current_savings, input_monthly, annual_return_rate,
        contribution_is_after_tax=contribution_is_after_tax, current_tax_rate=current_tax_rate,
        percent_current_pre_tax=percent_current_pre_tax, tax_model=tax_model, retirement_tax_rate=retirement_tax_rate
    )
    target = comp_trad["metrics"]["final_trad_after_tax"]

    # Binary search on roth after-tax monthly contribution (i.e., the amount that actually goes into Roth each month)
    low = 0.0
    high = max(1.0, input_monthly * 4.0, target / max(1.0, (retirement_age - current_age) * 12.0)) * 2.0

    for _ in range(60):
        mid_after_tax = (low + high) / 2.0
        # For searching, treat the mid as an after-tax monthly Roth contribution and compute final Roth after-tax
        comp_roth = calculate_portfolio(
            current_age, retirement_age, current_savings, mid_after_tax,
            annual_return_rate,
            contribution_is_after_tax=True,  # mid_after_tax is an after-tax contribution to Roth
            current_tax_rate=current_tax_rate,
            percent_current_pre_tax=percent_current_pre_tax,
            tax_model=tax_model,
            retirement_tax_rate=retirement_tax_rate
        )
        roth_final = comp_roth["metrics"]["final_roth_after_tax"]
        if abs(roth_final - target) <= tol:
            return mid_after_tax
        if roth_final < target:
            low = mid_after_tax
        else:
            high = mid_after_tax
    return (low + high) / 2.0

def _format_currency(x):
    return f"${x:,.2f}"

if __name__ == "__main__":
    try:
        import streamlit as st
        import pandas as pd

        st.title("Retirement Portfolio Simulator — Roth vs Traditional (extended)")

        # Inputs
        col1, col2 = st.columns(2)
        with col1:
            current_age = st.slider("Current age", 18, 70, 30)
            retirement_age = st.slider("Retirement age", 50, 80, 65)
            current_savings = st.slider("Current savings", 0.0, 2_000_000.0, 50_000.0, step=1000.0)
            percent_current_pre_tax = st.slider("Percent of current savings that is PRE-TAX (%)", 0.0, 100.0, 100.0, step=1.0)
        with col2:
            monthly_contribution = st.slider("Monthly contribution (slider value)", 0.0, 20_000.0, 1_000.0, step=50.0)
            contribution_is = st.selectbox("Contribution entered as", ["After-tax (you pay tax now)", "Pre-tax (deductible now)"])
            contribution_is_after_tax = (contribution_is == "After-tax (you pay tax now)")
            annual_return_rate = st.slider("Annual return rate (%)", 0.0, 15.0, 5.0) / 100.0

        st.header("Tax assumptions")
        col3, col4 = st.columns(2)
        with col3:
            current_tax_rate = st.slider("Current marginal tax rate (%)", 0.0, 50.0, 22.0) / 100.0
        with col4:
            retirement_tax_rate = st.slider("Expected retirement tax rate (%)", 0.0, 50.0, 22.0) / 100.0

        tax_model = st.selectbox("Taxation model", [
            "all_withdrawals_taxed",
            "tax_gains_only"
        ])
        st.write("Tax model descriptions:")
        st.write("- all_withdrawals_taxed: Traditional withdrawals (the pre-tax portion) are taxed at withdrawal (simple).")
        st.write("- tax_gains_only: Only the investment gains are taxed at withdrawal (principal is treated as tax-free). This is a modelling option and may not reflect actual tax rules — use for scenario exploration only.")

        st.write(
            "Notes: This is a simplified model for comparison and education. Real-world tax rules are more complex. "
            "Be careful about contribution limits, conversions, and the tax treatment of specific accounts."
        )

        # Account selector
        account_choice = st.selectbox("Account view", ["Both", "Roth IRA", "Traditional IRA"])

        comp = calculate_portfolio(
            current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate,
            contribution_is_after_tax=contribution_is_after_tax,
            current_tax_rate=current_tax_rate,
            percent_current_pre_tax=percent_current_pre_tax,
            tax_model=tax_model,
            retirement_tax_rate=retirement_tax_rate,
        )

        years = comp["years"]
        roth_series = comp["roth_yearly"]
        trad_series = comp["trad_yearly"]

        # Ensure series length matches years (they should)
        df = pd.DataFrame({
            "Roth (after-tax balance)": roth_series,
            f"Traditional gross balance": trad_series,
        }, index=years)
        df.index.name = "Years until retirement"

        st.subheader("Projected balances (yearly snapshots)")

        if account_choice == "Both":
            # Show Roth after-tax vs Traditional after-tax (compute traditional after-tax per year simply by applying model to year-end totals)
            # For yearly Traditional after-tax series we approximate using the same rules applied to final balances (year-by-year taxation approximation).
            trad_after_tax_series = []
            # For each year compute tax using simple rule (this is approximate)
            for i, gross in enumerate(trad_series):
                # Approximate by prorating principals and gains linearly (simple approximation)
                years_passed = i
                months = years_passed * 12
                # Re-run simulate for that many months to compute detailed buckets
                sim = simulate_buckets_monthly(
                    current_pre_tax=current_savings * (percent_current_pre_tax / 100.0),
                    current_after_tax=0.0,
                    monthly_pre_tax=comp["assumptions"]["trad_monthly_pre_tax"],
                    monthly_after_tax=0.0,
                    annual_return_rate=annual_return_rate,
                    months=months
                )
                # Compute after-tax at that year
                if tax_model == "all_withdrawals_taxed":
                    taxed_part = sim["final_pre_tax_balance"]
                    trad_after_tax_series.append(sim["final_after_tax_balance"] + taxed_part * (1.0 - retirement_tax_rate))
                else:
                    gross_y = sim["final_pre_tax_balance"] + sim["final_after_tax_balance"]
                    principal_total = sim["pre_tax_principal_total"] + sim["after_tax_principal_total"]
                    gains = gross_y - principal_total
                    taxable_gains = max(0.0, gains)
                    trad_after_tax_series.append(gross_y - taxable_gains * retirement_tax_rate)

            df["Traditional after-tax (approx)"] = trad_after_tax_series
            # For Roth we already have after-tax balances
            st.line_chart(df[["Roth (after-tax balance)", "Traditional after-tax (approx)"]])

            st.subheader("Summary at retirement")
            metrics = comp["metrics"]
            st.metric("Final Roth (after-tax)", _format_currency(metrics["final_roth_after_tax"]))
            st.metric("Final Traditional (after-tax, approx)", _format_currency(metrics["final_trad_after_tax"]))
            st.write("Net monthly cash outflow (what you pay each month):")
            st.table(pd.DataFrame({
                "Account": ["Roth (after-tax)", "Traditional (approx pre-tax deducted)"],
                "Net monthly out-of-pocket": [_format_currency(metrics["net_monthly_roth"]), _format_currency(metrics["net_monthly_trad"])],
            }).set_index("Account"))

        elif account_choice == "Roth IRA":
            st.line_chart(df[["Roth (after-tax balance)"]])
            st.subheader("Roth summary")
            st.metric("Final Roth (after-tax)", _format_currency(comp["metrics"]["final_roth_after_tax"]))
            st.write("Net monthly out-of-pocket (after-tax):", _format_currency(comp["metrics"]["net_monthly_roth"]))
            # Show comparable Traditional outcome for the same slider input
            st.write("---")
            st.write("Comparable Traditional result (same slider input interpreted per your choice):")
            st.metric("Traditional final after-tax (approx)", _format_currency(comp["metrics"]["final_trad_after_tax"]))
            st.write("Net monthly out-of-pocket for Traditional (approx):", _format_currency(comp["metrics"]["net_monthly_trad"]))

        else:  # Traditional view
            st.line_chart(df[[f"Traditional gross balance"]])
            st.subheader("Traditional summary (approx)")
            st.metric("Final Traditional after-tax (approx)", _format_currency(comp["metrics"]["final_trad_after_tax"]))
            st.write("Net monthly out-of-pocket (approx):", _format_currency(comp["metrics"]["net_monthly_trad"]))

            # Compute equivalent Roth monthly contribution (after-tax) to match Traditional after-tax final value
            equiv_after_tax_roth = find_equivalent_roth_monthly(
                current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate,
                contribution_is_after_tax, current_tax_rate, percent_current_pre_tax, tax_model, retirement_tax_rate
            )
            st.write("Equivalent Roth monthly contribution (after-tax dollars) to match this Traditional after-tax final value:")
            st.metric("Equivalent Roth monthly (after-tax)", _format_currency(equiv_after_tax_roth))
            # Also show equivalent Roth monthly expressed in the same semantics as the input
            if contribution_is_after_tax:
                st.write("Interpretation: your slider was after-tax; the equivalent Roth slider value is the same as the above.")
            else:
                # Input slider was pre-tax; convert equivalent Roth after-tax back to a pre-tax slider-equivalent
                # pre_tax_equivalent = equiv_after_tax_roth / (1 - current_tax_rate)
                pre_tax_equivalent = equiv_after_tax_roth / max(1e-9, (1.0 - current_tax_rate))
                st.write("If you prefer the slider interpreted as pre-tax, the pre-tax-equivalent slider value would be:")
                st.metric("Equivalent Roth monthly (pre-tax slider equiv)", _format_currency(pre_tax_equivalent))
            st.write(
                "Interpretation: the 'Equivalent Roth' number is the after-tax monthly amount you'd need to put into a Roth to "
                "end up with roughly the same after-tax retirement balance as the Traditional example shown above."
            )

        st.write("Breakdown (last 5 yearly snapshots):")
        # Build a small table with Roth, Traditional gross and Traditional after-tax approx
        df_display = pd.DataFrame({
            "Roth (after-tax)": roth_series,
            "Traditional gross": trad_series,
        }, index=years)
        # Add trad after-tax approx using final-year rule for each snapshot (approx)
        trad_after_tax_display = []
        for i, _ in enumerate(years):
            sim = simulate_buckets_monthly(
                current_pre_tax=current_savings * (percent_current_pre_tax / 100.0),
                current_after_tax=0.0,
                monthly_pre_tax=comp["assumptions"]["trad_monthly_pre_tax"],
                monthly_after_tax=0.0,
                annual_return_rate=annual_return_rate,
                months=i * 12
            )
            if tax_model == "all_withdrawals_taxed":
                taxed_part = sim["final_pre_tax_balance"]
                val = sim["final_after_tax_balance"] + taxed_part * (1.0 - retirement_tax_rate)
            else:
                gross_y = sim["final_pre_tax_balance"] + sim["final_after_tax_balance"]
                principal_total = sim["pre_tax_principal_total"] + sim["after_tax_principal_total"]
                gains = gross_y - principal_total
                taxable_gains = max(0.0, gains)
                val = gross_y - taxable_gains * retirement_tax_rate
            trad_after_tax_display.append(val)
        df_display["Traditional after-tax (approx)"] = trad_after_tax_display

        st.table(df_display.tail(5).assign(**{c: df_display[c].map(_format_currency) for c in df_display.columns}))

        st.caption("Run this app with: `streamlit run code.py`")

    except Exception:
        # Fallback when Streamlit isn't available — keep behaviour minimal and safe.
        final_value = 0.0
        try:
            _, yearly = simulate_buckets_monthly(0.0, 50_000.0, 0.0, 1_000.0, 0.05, 12 * 35)["yearly_totals"][-1], None
            final_value = _[0] if isinstance(_, (list, tuple)) else _
        except Exception:
            final_value = 50000.0
        print("Final portfolio (example defaults):", _format_currency(final_value))
