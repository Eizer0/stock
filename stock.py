import sys
import json
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QMessageBox
from PyQt5.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class Account:
    def __init__(self, balance):
        self.balance = balance
        self.holdings = {}
        self.transaction_history = {}
        self.stocks = [Stock("AAPL", 100), Stock("GOOG", 200), Stock("MSFT", 150), Stock("AWS", 60)]

    def buy_stock(self, stock_index, quantity):
        selected_stock = self.stocks[stock_index]
        cost = round(selected_stock.price[-1] * quantity, 2)
        if cost > self.balance:
            return False
        self.holdings[selected_stock.symbol] = self.holdings.get(selected_stock.symbol, 0) + quantity
        self.balance = round(self.balance - cost, 2)
        transaction = f"매수: {selected_stock.symbol} {quantity}주, 가격: {selected_stock.price[-1]}"
        self.transaction_history[selected_stock.symbol] = self.transaction_history.get(selected_stock.symbol, [])
        self.transaction_history[selected_stock.symbol].append(transaction)
        # 거래 내역 15개만 표시
        if len(self.transaction_history[selected_stock.symbol]) > 15:
            self.transaction_history[selected_stock.symbol] = self.transaction_history[selected_stock.symbol][-15:]
        return True

    def sell_stock(self, stock_index, quantity):
        selected_stock = self.stocks[stock_index]
        if selected_stock.symbol not in self.holdings or self.holdings[selected_stock.symbol] < quantity:
            return False
        self.holdings[selected_stock.symbol] -= quantity
        proceeds = round(selected_stock.price[-1] * quantity, 2)
        self.balance = round(self.balance + proceeds, 2)
        transaction = f"매도: {selected_stock.symbol} {quantity}주, 가격: {selected_stock.price[-1]}"
        self.transaction_history[selected_stock.symbol] = self.transaction_history.get(selected_stock.symbol, [])
        self.transaction_history[selected_stock.symbol].append(transaction)
        # 거래 내역 15개만 표시
        if len(self.transaction_history[selected_stock.symbol]) > 15:
            self.transaction_history[selected_stock.symbol] = self.transaction_history[selected_stock.symbol][-15:]
        return True

class Stock:
    def __init__(self, symbol, initial_price):
        self.symbol = symbol
        self.initial_price = initial_price
        self.price = [initial_price]

    def update_price(self):
        new_price = round(self.price[-1] * random.uniform(0.9, 1.1), 2)
        self.price.append(new_price)
        return new_price

    def calculate_profit_rate(self):
        current_price = self.price[-1]
        profit_rate = ((current_price - self.initial_price) / self.initial_price) * 100
        return round(profit_rate, 2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("주식 거래 프로그램")
        self.setGeometry(100, 100, 800, 600)
        self.load_saved_data()

        self.balance_label = QLabel(f"잔액: {self.account.balance}원", self)
        self.balance_label.setGeometry(10, 10, 200, 30)

        self.stock_combobox = QComboBox(self)
        self.stock_combobox.setGeometry(10, 50, 200, 30)
        for stock in self.account.stocks:
            self.stock_combobox.addItem(stock.symbol)

        self.stock_quantity_label = QLabel("수량:", self)
        self.stock_quantity_label.setGeometry(10, 90, 50, 30)
        self.stock_quantity_entry = QLineEdit(self)
        self.stock_quantity_entry.setGeometry(60, 90, 150, 30)

        self.buy_button = QPushButton("매수", self)
        self.buy_button.setGeometry(10, 130, 100, 30)
        self.buy_button.clicked.connect(self.buy_stock)

        self.sell_button = QPushButton("매도", self)
        self.sell_button.setGeometry(120, 130, 100, 30)
        self.sell_button.clicked.connect(self.sell_stock)

        self.transaction_history_display = QTextEdit(self)
        self.transaction_history_display.setGeometry(240, 50, 300, 150)
        self.transaction_history_display.setReadOnly(True)

        self.holdings_display = QTextEdit(self)
        self.holdings_display.setGeometry(240, 210, 300, 150)
        self.holdings_display.setReadOnly(True)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setGeometry(550, 50, 220, 310)
        self.canvas.setParent(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_balance)
        self.timer.start(10000)

        self.price_timer = QTimer(self)
        self.price_timer.timeout.connect(self.update_all_stock_prices)
        self.price_timer.start(5000)

        self.stock_value_label = QLabel("", self)
        self.stock_value_label.setGeometry(10, 170, 200, 30)

        self.reset_button = QPushButton("초기화", self)
        self.reset_button.setGeometry(10, 250, 100, 30)
        self.reset_button.clicked.connect(self.reset_account)

        self.update_balance()
        self.update_graph()

        # 주식 선택 시 해당 주식 정보 업데이트
        self.stock_combobox.currentIndexChanged.connect(self.update_selected_stock_info)

        # 가격 타이머가 호출될 때마다 그래프 업데이트
        self.price_timer.timeout.connect(self.update_all_stock_prices)
        self.price_timer.timeout.connect(self.update_graph)
        self.price_timer.start(5000)

    def closeEvent(self, event):
        self.save_data()
        event.accept()

    def save_data(self):
        user_data = {
            "balance": self.account.balance,
            "holdings": self.account.holdings,
            "transaction_history": self.account.transaction_history
        }
        with open("user_data.json", "w") as file:
            json.dump(user_data, file)

    def load_saved_data(self):
        try:
            with open("user_data.json", "r") as file:
                user_data = json.load(file)
                if "balance" in user_data and "holdings" in user_data and "transaction_history" in user_data:
                    self.account = Account(user_data["balance"])
                    self.account.holdings = user_data["holdings"]
                    self.account.transaction_history = user_data["transaction_history"]
                else:
                    raise ValueError("잘못된 데이터 형식입니다.")
        except (FileNotFoundError, ValueError):
            QMessageBox.warning(self, "오류", "사용자 데이터를 불러올 수 없습니다. 새로운 계정으로 시작합니다.")
            self.account = Account(10000)

    def update_all_stock_prices(self):
        for stock in self.account.stocks:
            stock.update_price()
        self.update_graph()

    def buy_stock(self):
        stock_index = self.stock_combobox.currentIndex()
        stock_quantity_text = self.stock_quantity_entry.text()
        try:
            stock_quantity = int(stock_quantity_text)
            if stock_quantity <= 0:
                raise ValueError("주식 수량은 양의 정수여야 합니다.")
        except ValueError:
            QMessageBox.warning(self, "오류", "올바른 수량을 입력하세요.")
            return
        if self.account.buy_stock(stock_index, stock_quantity):
            self.update_balance()
            self.update_holdings()
            self.update_transaction_history()

    def sell_stock(self):
        stock_index = self.stock_combobox.currentIndex()
        stock_quantity_text = self.stock_quantity_entry.text()
        if not stock_quantity_text.isdigit() or int(stock_quantity_text) <= 0:
            QMessageBox.warning(self, "오류", "올바른 수량을 입력하세요.")
            return
        stock_quantity = int(stock_quantity_text)
        if self.account.sell_stock(stock_index, stock_quantity):
            self.update_balance()
            self.update_holdings()
            self.update_transaction_history()

    def update_balance(self):
        self.balance_label.setText(f"잔액: {self.account.balance}원")
        self.update_graph()
        self.update_selected_stock_info()

    def update_graph(self):
        stock_index = self.stock_combobox.currentIndex()
        selected_stock = self.account.stocks[stock_index]
        new_price = selected_stock.update_price()
        self.ax.clear()
        if new_price > selected_stock.price[-2]:
            self.ax.plot(selected_stock.price, label=selected_stock.symbol, color='red')
        else:
            self.ax.plot(selected_stock.price, label=selected_stock.symbol, color='blue')
        self.ax.legend()
        self.canvas.draw()

    def update_selected_stock_info(self):
        stock_index = self.stock_combobox.currentIndex()
        selected_stock = self.account.stocks[stock_index]
        current_price = selected_stock.price[-1]
        self.stock_value_label.setText(f"주가: {current_price}원")
        self.update_holdings()
        self.update_transaction_history()

    def update_holdings(self):
            holdings_text = "보유 주식:\n"
            # 모든 주식의 가격을 업데이트
            self.update_all_stock_prices()
            for symbol, quantity in self.account.holdings.items():
                stock_index = self.account.stocks.index(next(stock for stock in self.account.stocks if stock.symbol == symbol))
                selected_stock = self.account.stocks[stock_index]
                profit_rate = 0  # Default profit rate
                if quantity > 0:  # Check if the user has holdings of the stock
                    profit_rate = selected_stock.calculate_profit_rate()
                holdings_text += f"{symbol}: {quantity}주 / 수익률: {profit_rate}%\n"
            self.holdings_display.setText(holdings_text)

    def update_transaction_history(self):
        transaction_history_text = "거래 내역:\n"
        for symbol, transactions in self.account.transaction_history.items():
            for transaction in transactions:
                transaction_history_text += f"{transaction}원\n"
        self.transaction_history_display.setText(transaction_history_text)

        scroll_bar = self.transaction_history_display.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def reset_account(self):
        reply = QMessageBox.question(self, '초기화', '계정을 초기화하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.account = Account(10000)
            self.update_balance()
            self.update_holdings()
            self.update_transaction_history()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
