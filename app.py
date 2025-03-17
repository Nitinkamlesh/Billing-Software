from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, 
                               QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout)
import mysql.connector
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

class BillingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billing Application")
        self.setGeometry(100, 100, 600, 700)

        layout = QVBoxLayout()

        # Customer Details
        self.name_label = QLabel("Customer Name:")
        self.name_input = QLineEdit()
        
        self.contact_label = QLabel("Contact Number:")
        self.contact_input = QLineEdit()

        # Items
        self.items_label = QLabel("Items:")
        self.items_input = QTextEdit()

        self.total_label = QLabel("Total Amount:")
        self.total_input = QLineEdit()

        # Buttons
        self.submit_button = QPushButton("Save Bill")
        self.submit_button.clicked.connect(self.save_bill)

        self.retrieve_button = QPushButton("Retrieve Bills")
        self.retrieve_button.clicked.connect(self.retrieve_bills)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by customer name")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_bills)

        self.generate_pdf_button = QPushButton("Generate Invoice PDF")
        self.generate_pdf_button.clicked.connect(self.generate_invoice_pdf)
        
        # Table to display bills
        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(5)
        self.bills_table.setHorizontalHeaderLabels(["ID", "Customer", "Items", "Total", "Delete"])
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.contact_label)
        layout.addWidget(self.contact_input)
        layout.addWidget(self.items_label)
        layout.addWidget(self.items_input)
        layout.addWidget(self.total_label)
        layout.addWidget(self.total_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.retrieve_button)
        
        # Search Layout
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)
        
        layout.addWidget(self.generate_pdf_button)
        layout.addWidget(self.bills_table)
        self.setLayout(layout)

    def connect_db(self):
        return mysql.connector.connect(host="localhost", user="root", password="", database="BillingDB")

    def save_bill(self):
        name = self.name_input.text().strip()
        contact = self.contact_input.text().strip()
        items = self.items_input.toPlainText().strip()
        total = self.total_input.text().strip()

        if not name or not contact or not items or not total:
            QMessageBox.warning(self, "Input Error", "All fields are required!")
            return

        try:
            total = float(total)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Total must be a number!")
            return

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Customers WHERE contact = %s", (contact,))
        customer = cursor.fetchone()

        if not customer:
            cursor.execute("INSERT INTO Customers (name, contact) VALUES (%s, %s)", (name, contact))
            conn.commit()
            customer_id = cursor.lastrowid
        else:
            customer_id = customer[0]

        cursor.execute("INSERT INTO Bills (customer_id, items, total_amount) VALUES (%s, %s, %s)", 
                       (customer_id, items, total))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Bill saved successfully!")
        self.clear_fields()
        self.retrieve_bills()

    def retrieve_bills(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""SELECT Bills.id, Customers.name, Bills.items, Bills.total_amount FROM Bills 
                        JOIN Customers ON Bills.customer_id = Customers.id""")
        bills = cursor.fetchall()
        conn.close()

        self.bills_table.setRowCount(len(bills))

        for row_idx, (bill_id, customer_name, items, total) in enumerate(bills):
            self.bills_table.setItem(row_idx, 0, QTableWidgetItem(str(bill_id)))
            self.bills_table.setItem(row_idx, 1, QTableWidgetItem(customer_name))
            self.bills_table.setItem(row_idx, 2, QTableWidgetItem(items))
            self.bills_table.setItem(row_idx, 3, QTableWidgetItem(str(total)))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, bid=bill_id: self.delete_bill(bid))
            self.bills_table.setCellWidget(row_idx, 4, delete_button)

    def delete_bill(self, bill_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Bills WHERE id = %s", (bill_id,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Success", "Bill deleted successfully!")
        self.retrieve_bills()

    def search_bills(self):
        name = self.search_input.text().strip()
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""SELECT Bills.id, Customers.name, Bills.items, Bills.total_amount FROM Bills
                        JOIN Customers ON Bills.customer_id = Customers.id WHERE Customers.name LIKE %s""", ("%" + name + "%",))
        bills = cursor.fetchall()
        conn.close()
        self.bills_table.setRowCount(len(bills))
        for row_idx, (bill_id, customer_name, items, total) in enumerate(bills):
            self.bills_table.setItem(row_idx, 0, QTableWidgetItem(str(bill_id)))
            self.bills_table.setItem(row_idx, 1, QTableWidgetItem(customer_name))
            self.bills_table.setItem(row_idx, 2, QTableWidgetItem(items))
            self.bills_table.setItem(row_idx, 3, QTableWidgetItem(str(total)))

    def generate_invoice_pdf(self):
        bill_id = self.bills_table.item(self.bills_table.currentRow(), 0).text()
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""SELECT Bills.id, Customers.name, Bills.items, Bills.total_amount FROM Bills 
                        JOIN Customers ON Bills.customer_id = Customers.id WHERE Bills.id = %s""", (bill_id,))
        bill = cursor.fetchone()
        conn.close()
        pdf_path = f"Invoice_{bill[0]}.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, f"Invoice ID: {bill[0]}")
        c.drawString(100, 730, f"Customer: {bill[1]}")
        c.drawString(100, 710, f"Items: {bill[2]}")
        c.drawString(100, 690, f"Total: ${bill[3]}")
        c.save()
        os.system(f"start {pdf_path}")

if __name__ == "__main__":
    app = QApplication([])
    window = BillingApp()
    window.show()
    app.exec()
