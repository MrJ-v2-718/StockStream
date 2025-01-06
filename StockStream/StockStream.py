import yfinance as yf
import tkinter as tk
from tkinter import StringVar
from threading import Thread
import time
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Function to get stock data
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    try:
        # Use the '1d' period, which gets data for the past 1 day
        stock_data = stock.history(period="1d")
        # Get the last closing price (which is the most recent data point)
        current_price = stock_data['Close'].iloc[-1]
        # Format price to currency with two decimal places
        formatted_price = f"${current_price:,.2f}"
        return symbol, formatted_price
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return symbol, None


# Function to get historical data for plotting
def get_historical_data(symbol, years):
    stock = yf.Ticker(symbol)
    try:
        # Fetch data for the specified period of years
        stock_data = stock.history(period=f"{years}y")
        # Return dates and closing prices for the plot
        return stock_data.index, stock_data['Close']
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return [], []


# Thread for updating stock prices concurrently
def update_stock_prices():
    global ticker_text
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            futures = []
            # Submit all stock fetch tasks to the executor
            for symbol, _ in stock_symbols:
                futures.append(executor.submit(get_stock_data, symbol))

            # Wait for all futures to complete and get the results
            stock_data = []
            for future in futures:
                symbol, price = future.result()
                if price is not None:
                    stock_data.append((symbol, price))

            # Generate the ticker text with a separator at the end
            ticker_text = " | ".join([f"{symbol}: {price}" for symbol, price in stock_data]) + " | "
            ticker_label.config(text=ticker_text)

            time.sleep(60)  # Update every 60 seconds


# Function to display the selected stock's price
def show_selected_stock_price(selected_company):
    # Extract the stock symbol from the selected company name (before the "-")
    symbol = selected_company.split(" - ")[0]
    symbol, price = get_stock_data(symbol)
    if price is not None:
        selected_stock_price_label.config(text=f"{selected_company}: {price}")
    else:
        selected_stock_price_label.config(text=f"{selected_company}: Error fetching data")


# Function to plot the historical data (1 year) of the selected stock
def plot_stock_history(selected_company, years):
    symbol = selected_company.split(" - ")[0]
    dates, prices = get_historical_data(symbol, years)

    # Clear the previous plot
    ax.clear()

    # Check if the data is non-empty before plotting
    if not dates.empty and not prices.empty:
        # Plot the closing prices over time
        ax.plot(dates, prices, color='#f28ad1', label=f"{symbol} - {years} Year")
        ax.set_title(f"{selected_company} - Daily Closing Prices ({years} Year)",
                     color='#f28ad1')
        ax.set_xlabel("Date", color='#f28ad1')
        ax.set_ylabel("Closing Price (USD)", color='#f28ad1')
        ax.legend()
        ax.grid(True)
    else:
        # Handle empty data (this shouldn't happen unless there's an error with the API request)
        ax.text(0.5, 0.5, "No Data Available", ha='center', va='center', fontsize=16, color="red")

    # Redraw the canvas to update the plot
    canvas.draw()


# Function to create the stock price UI
def create_ui():
    global ticker_text, ticker_label, selected_stock_price_label, ax, canvas

    root = tk.Tk()
    root.title("StockStream")
    root.geometry("1000x650")  # Increase height for the chart
    root.config(bg="#100e4f")  # Set background color for root window

    # Create a frame for the scrolling ticker banner
    ticker_frame = tk.Frame(root, bg="#100e4f")
    ticker_frame.pack(fill=tk.X, side=tk.TOP, pady=10)

    # Initialize the ticker text with placeholders (will be updated later)
    ticker_text = " | ".join([f"{symbol}: Loading..." for symbol, _ in stock_symbols]) + " |"
    ticker_label = tk.Label(ticker_frame, text=ticker_text, font=("Courier New", 16), bg="#100e4f", fg="#f28ad1")
    ticker_label.pack(side=tk.LEFT, padx=10)

    # Create a frame for the custom stock dropdown
    dropdown_frame = tk.Frame(root, bg="#100e4f")
    dropdown_frame.pack(side=tk.TOP, pady=20)

    # Create a list of formatted strings combining symbol and name for the dropdown
    display_options = [f"{name}" for _, name in stock_symbols]  # Use the second index for display (company name)

    # Set the dummy default selection (AAPL - Apple)
    selected_symbol_var = StringVar(root)
    selected_symbol_var.set(display_options[0])  # Set default stock symbol to the first company name (AAPL)

    # Create the dropdown menu using the company names for display, but use the stock symbol for internal value
    stock_dropdown_menu = tk.OptionMenu(
        dropdown_frame,
        selected_symbol_var,
        *display_options,  # Use the company name (second index) for display
        command=show_selected_stock_price  # Call the function to show selected stock price
    )
    stock_dropdown_menu.config(
        font=("Courier New", 14),
        bg="#100e4f",
        fg="#f28ad1",
        activebackground="#f28ad1",
        activeforeground="#100e4f",
        width=40,
        relief="flat")  # Set color and width

    stock_dropdown_menu["menu"].config(
        bg="#100e4f",
        fg="#f28ad1",
        activebackground="#f28ad1",
        activeforeground="#100e4f",
        font=("Courier New", 14))  # Customize the dropdown menu

    stock_dropdown_menu.pack(side=tk.LEFT, padx=10)

    # Create a dropdown for selecting the number of years for historical data
    years_options = [1, 2, 5, 10]  # Options for 1, 2, 5, or 10 years
    selected_year_var = StringVar(root)
    selected_year_var.set(str(years_options[0]))  # Default to 1 year

    years_dropdown_menu = tk.OptionMenu(
        dropdown_frame,
        selected_year_var,
        *years_options,  # Options for the number of years
        command=lambda *args: plot_stock_history(selected_symbol_var.get(), int(selected_year_var.get()))
    )
    years_dropdown_menu.config(font=("Courier New", 14), bg="#100e4f", fg="#f28ad1", activebackground="#f28ad1",
                               activeforeground="#100e4f", width=5,
                               relief="flat")
    years_dropdown_menu["menu"].config(bg="#100e4f", fg="#f28ad1", activebackground="#f28ad1",
                                       activeforeground="#100e4f",
                                       font=("Courier New", 14))
    years_dropdown_menu.pack(side=tk.LEFT, padx=10)

    # Label to display the selected stock's price below the dropdown
    selected_stock_price_label = tk.Label(root, text=f"{display_options[0]}: Loading...", font=("Courier New", 14),
                                          fg="#f28ad1", bg="#100e4f")
    selected_stock_price_label.pack(side=tk.TOP, pady=20)

    # Fetch the price for the default selection immediately after starting the UI
    show_selected_stock_price(display_options[0])  # Fetch price for "AAPL - Apple"

    # Create a Matplotlib figure and axis for the stock price chart
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.set_facecolor('#100e4f')  # Set figure background color
    ax.set_facecolor('#100e4f')  # Set chart background color to match the UI
    ax.tick_params(axis='both', colors='#f28ad1')  # Set tick label color
    ax.set_xlabel('X-axis Label', color='#f28ad1')
    ax.set_ylabel('Y-axis Label', color='#f28ad1')
    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)  # Increase padding

    # Create a canvas to display the Matplotlib figure inside the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(pady=20)

    # Plot the initial data for the default stock (AAPL)
    plot_stock_history(display_options[0], int(selected_year_var.get()))

    # Start the ticker animation in a separate thread
    def move_ticker():
        while True:
            # Get the current text of the ticker
            current_text = ticker_label.cget("text")

            # Only scroll the actual stock symbols and prices (don't add extra separators)
            if len(current_text) < 300:  # Check if the ticker text is too short to scroll
                # Ensure the ticker text is long enough by repeating it
                current_text = ticker_text + " | " + ticker_text

            # Move the first character (symbol) to the end to create a scrolling effect
            new_text = current_text[1:] + current_text[0]

            # Update the label with the new text
            ticker_label.config(text=new_text)
            time.sleep(0.15)  # Adjust scroll speed (faster speed)

    # Start a separate thread for updating stock prices
    thread_update_prices = Thread(target=update_stock_prices, daemon=True)
    thread_update_prices.start()

    # Start the scrolling ticker animation
    thread_move_ticker = Thread(target=move_ticker, daemon=True)
    thread_move_ticker.start()

    # Update the chart when the user selects a different stock
    def on_dropdown_change(*args):
        selected_company = selected_symbol_var.get()
        show_selected_stock_price(selected_company)
        plot_stock_history(selected_company, selected_year_var.get())

    selected_symbol_var.trace("w", on_dropdown_change)  # Trace changes to the dropdown variable

    def on_closing():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


# List of stock symbols and company names (2nd index to show both symbol and name in the dropdown)
stock_symbols = [
    ("AAPL", "AAPL - Apple"),
    ("ADBE", "ADBE - Adobe"),
    ("AMD", "AMD - Advanced Micro Devices"),
    ("AMZN", "AMZN - Amazon"),
    ("ARM", "ARM - ARM Holdings"),
    ("AVGO", "AVGO - Broadcom"),
    ("BABA", "BABA - Alibaba"),
    ("CSCO", "CSCO - Cisco"),
    ("GOOG", "GOOG - Alphabet (Google)"),
    ("IBM", "IBM - International Business Machines"),
    ("INTC", "INTC - Intel"),
    ("META", "META - Meta (Facebook)"),
    ("MSFT", "MSFT - Microsoft"),
    ("NFLX", "NFLX - Netflix"),
    ("NVDA", "NVDA - Nvidia"),
    ("ORCL", "ORCL - Oracle"),
    ("PYPL", "PYPL - PayPal"),
    ("QCOM", "QCOM - QUALCOMM"),
    ("RBLX", "RBLX - Roblox"),
    ("SHOP", "SHOP - Shopify"),
    ("T", "T - AT&T"),
    ("TMUS", "T-Mobile US"),
    ("TSLA", "TSLA - Tesla"),
    ("TSM", "TSM - Taiwan Semiconductor Manufacturing"),
    ("TX", "TX - Texas Instruments"),
    ("VZ", "VZ - Verizon Communications")
]

# Start the application
if __name__ == "__main__":
    create_ui()
