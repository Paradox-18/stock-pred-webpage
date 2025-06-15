from flask import Flask, request, jsonify
import yfinance as yf
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['GET'])
def analyze_stock():
    symbol = request.args.get('symbol')
    user_sector = request.args.get('sector', '').lower()  # Optional override

    if not symbol:
        return jsonify({"error": "Missing symbol parameter"}), 400

    if not symbol.endswith(".NS"):
        symbol += ".NS"

    try:
        stock = yf.Ticker(symbol)
        data = stock.info

        sector = user_sector if user_sector else (data.get('sector') or '').lower()
        print(f"[INFO] Detected sector for {symbol}: {sector}")

        price = data.get('regularMarketPrice', 0)
        pe = data.get('trailingPE') or 20
        pb = data.get('priceToBook') or 2.5
        roe = (data.get('returnOnEquity') or 0) * 100
        eps = data.get('trailingEps') or 0
        market_cap = data.get('marketCap', 0)
        debt_to_equity = data.get('debtToEquity') or 0
        current_ratio = data.get('currentRatio') or 0
        profit_margin = (data.get('profitMargins') or 0) * 100
        free_cash_flow = data.get('freeCashflow', 0)

        # Default metrics
        sector_pe_pb_roe_eps = {"ideal_pe": 15, "ideal_pb": 3, "ideal_roe": 12, "ideal_eps": 25}
        sector_metrics = {}

        # Sector-wise logic from Money Pechu
        if 'bank' in sector or 'finance' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 10, "ideal_pb": 1.5, "ideal_roe": 15, "ideal_eps": 40}
            sector_metrics = {
                "Net_Interest_Margin": data.get('netInterestMargin', 'N/A'),
                "Gross_NPA": data.get('grossNPA', 'N/A'),
                "Capital_Adequacy_Ratio": data.get('capitalAdequacy', 'N/A'),
                "Loan_to_Deposit_Ratio": data.get('loanToDepositRatio', 'N/A')
            }

        elif 'it' in sector or 'software' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 25, "ideal_pb": 5, "ideal_roe": 20, "ideal_eps": 60}
            sector_metrics = {
                "EBIT_Margin": data.get('ebitMargins', 'N/A'),
                "Revenue_from_Digital": data.get('revenueGrowth', 'N/A'),
                "Employee_Count": data.get('fullTimeEmployees', 'N/A')
            }

        elif 'pharma' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 20, "ideal_pb": 3, "ideal_roe": 18, "ideal_eps": 30}
            sector_metrics = {
                "R&D_to_Sales": data.get('researchDevelopment', 'N/A'),
                "Regulatory_Approvals": "Check news manually",
                "Export_Revenue": "Check manually"
            }

        elif 'fmcg' in sector or 'retail' in sector or 'consumer' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 40, "ideal_pb": 10, "ideal_roe": 25, "ideal_eps": 20}
            sector_metrics = {
                "Inventory_Turnover": data.get('inventoryTurnover', 'N/A'),
                "Revenue_Growth": data.get('revenueGrowth', 'N/A')
            }

        elif 'auto' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 20, "ideal_pb": 3, "ideal_roe": 15, "ideal_eps": 30}
            sector_metrics = {
                "Volume_Growth": "Check company reports",
                "Export_Contribution": "Check manually"
            }

        elif 'real estate' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 10, "ideal_pb": 1.5, "ideal_roe": 10, "ideal_eps": 15}
            sector_metrics = {
                "Debt_Level": debt_to_equity,
                "Order_Book_Value": "Check investor presentation"
            }

        elif 'oil' in sector or 'gas' in sector or 'energy' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 8, "ideal_pb": 1.5, "ideal_roe": 12, "ideal_eps": 20}
            sector_metrics = {
                "Crude_Price_Impact": "High",
                "Refining_Margin": "Check industry data"
            }

        elif 'capital goods' in sector or 'engineering' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 15, "ideal_pb": 3, "ideal_roe": 12, "ideal_eps": 25}
            sector_metrics = {
                "Order_Backlog": "Check latest filings",
                "Execution_Cycle": "Check annual report"
            }

        elif 'telecom' in sector:
            sector_pe_pb_roe_eps = {"ideal_pe": 20, "ideal_pb": 2.5, "ideal_roe": 10, "ideal_eps": 20}
            sector_metrics = {
                "ARPU": "Check investor deck",
                "Subscriber_Growth": "Check TRAI reports"
            }

        # Estimate intrinsic value and decision
        intrinsic = price * 1.3 if pe < sector_pe_pb_roe_eps["ideal_pe"] else price * 0.9
        buy_below = intrinsic * 0.8
        sell_above = intrinsic * 1.1

        if price < buy_below:
            recommendation = "BUY"
            reason = "Stock is trading significantly below its estimated intrinsic value."
        elif price > sell_above:
            recommendation = "SELL"
            reason = "Stock is trading significantly above its estimated intrinsic value."
        else:
            recommendation = "HOLD"
            reason = "Stock is trading near its fair value."

        result = {
            "symbol": symbol,
            "sector": sector,
            "price": round(price, 2),
            "pe": round(pe, 2),
            "pb": round(pb, 2),
            "roe": round(roe, 2),
            "eps": round(eps, 2),
            "market_cap": market_cap,
            "debt_to_equity": round(debt_to_equity, 2),
            "current_ratio": round(current_ratio, 2),
            "profit_margin": round(profit_margin, 2),
            "free_cash_flow": free_cash_flow,
            "intrinsic": round(intrinsic, 2),
            "buy_below": round(buy_below, 2),
            "sell_above": round(sell_above, 2),
            "recommendation": recommendation,
            "reason": reason,
            "sector_metrics": sector_metrics,
            "sector_ideal_ratios": sector_pe_pb_roe_eps
        }

        return jsonify(result)

    except Exception as e:
        print(f"[ERROR] Could not analyze stock {symbol}: {e}")
        return jsonify({"error": "Unable to fetch stock data."}), 500

if __name__ == '__main__':
    print("[INFO] Stock Analyzer running on http://127.0.0.1:5000")
    app.run(debug=True)  