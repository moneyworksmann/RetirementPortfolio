# Retirement Portfolio Calculator

def calculate_retirement_portfolio(current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate):
    years_to_retirement = retirement_age - current_age
    months_to_retirement = years_to_retirement * 12
    monthly_rate = annual_return_rate / 12.0

    total_savings = current_savings
    balances_monthly = [total_savings]

    for month in range(months_to_retirement):
        total_savings += monthly_contribution
        total_savings *= (1 + monthly_rate)
        balances_monthly.append(total_savings)

    # Create yearly snapshots for charting (including year 0)
    yearly_balances = [balances_monthly[i * 12] for i in range(years_to_retirement + 1)]
    return total_savings, yearly_balances

def calculate_traditional_ira(current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate, tax_rate):
    # For Traditional IRA: contributions are pre-tax, so effective contribution is higher for same after-tax cost
    # Then final value is taxed at withdrawal
    effective_monthly_contribution = monthly_contribution / (1 - tax_rate)
    final_value, yearly_balances = calculate_retirement_portfolio(
        current_age, retirement_age, current_savings, effective_monthly_contribution, annual_return_rate
    )
    final_value *= (1 - tax_rate)  # Tax on withdrawal
    return final_value, yearly_balances

def calculate_roth_ira(current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate, tax_rate):
    # For Roth IRA: contributions are after-tax, growth is tax-free
    final_value, yearly_balances = calculate_retirement_portfolio(
        current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate
    )
    # No tax on final value
    return final_value, yearly_balances

def _format_currency(x):
    return f"${x:,.2f}"


if __name__ == "__main__":
    try:
        import streamlit as st

        st.title("Retirement Portfolio Simulator")

        col1, col2, col3 = st.columns(3)

        with col1:
            current_age = st.slider("Current age", 18, 70, 30)
            retirement_age = st.slider("Retirement age", 50, 80, 65)
            current_savings = st.slider("Current savings", 0.0, 2000000.0, 50000.0, step=1000.0)

        with col2:
            monthly_contribution = st.slider("Monthly contribution", 0.0, 20000.0, 1000.0, step=50.0)
            annual_return_rate = st.slider("Annual return rate (%)", 0.0, 15.0, 5.0) / 100.0

        with col3:
            ira_type = st.selectbox("IRA Type", ["Traditional", "Roth"])
            tax_rate = st.slider("Tax rate (%)", 0.0, 50.0, 25.0) / 100.0

        if ira_type == "Traditional":
            final_value, balances = calculate_traditional_ira(
                current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate, tax_rate
            )
        else:
            final_value, balances = calculate_roth_ira(
                current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate, tax_rate
            )

        st.metric(f"Estimated {ira_type} IRA portfolio at retirement", _format_currency(final_value))

        # Show yearly growth chart
        years = list(range(0, retirement_age - current_age + 1))
        import pandas as pd

        df = pd.DataFrame({"Balance": balances}, index=years)
        df.index.name = "Years until retirement"
        st.line_chart(df)

        st.write("Breakdown:")
        st.table(df.tail(5).assign(Balance=df["Balance"].map(_format_currency)))

        # Comparison section
        st.write("### Comparison: Traditional vs Roth IRA")
        trad_value, _ = calculate_traditional_ira(
            current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate, tax_rate
        )
        roth_value, _ = calculate_roth_ira(
            current_age, retirement_age, current_savings, monthly_contribution, annual_return_rate, tax_rate
        )
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Traditional IRA", _format_currency(trad_value))
        with col2:
            st.metric("Roth IRA", _format_currency(roth_value))
        difference = roth_value - trad_value
        st.write(f"Difference (Roth - Traditional): {_format_currency(difference)}")

        st.caption("Run this app with: `streamlit run code.py`")

    except Exception:
        # Fallback when Streamlit isn't available — keep behaviour minimal and safe.
        final_value, _ = calculate_retirement_portfolio(30, 65, 50000, 10000, 0.05)
        print("Final portfolio (example defaults):", _format_currency(final_value))