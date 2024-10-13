import sys
import os
import psycopg2
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
                             QWidget, QHeaderView, QTextEdit, QPushButton, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from multiprocessing import Manager
import threading
import time

# import QAbstractItemView
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtGui import QColor, QFont


from dataclasses import dataclass

@dataclass
class customColors:
    green = QColor(33, 255, 129)#(84, 255, 110)
    yellow_green = QColor(204, 255, 84)
    yellow = QColor(255, 249, 84)
    orange = QColor(255, 189, 84)
    red = QColor(255, 84, 84)



load_dotenv()
sys.path.append(os.getcwd())

from core.database import models
from core.ai import ratings

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value):
        super().__init__(str(value))
        self.value = value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)

import matplotlib.pyplot as plt

class PieChartWidget(FigureCanvas):
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(121)
        super().__init__(fig)
        self.setParent(parent)
        self.plot_empty_chart()

    def plot_empty_chart(self):
        self.figure.clear()
        self.axes = self.figure.add_subplot(121)
        self.axes.pie([1], labels=['No Data'], colors=['#f0f0f0'])
        self.axes.axis('equal')
        self.draw()

    def update_chart(self, labels, data, title):
        self.figure.clear()
        
        # Pie chart subplot
        self.axes = self.figure.add_subplot(121)
        wedges, texts, autotexts = self.axes.pie(data, autopct='%1.1f%%', startangle=90)
        self.axes.axis('equal')
        
        # Legend subplot
        legend_ax = self.figure.add_subplot(122)
        legend_ax.axis('off')
        legend = legend_ax.legend(wedges, labels, title=title, loc="center left")
        
        # Adjust the font size
        plt.setp(legend.get_texts(), fontsize=15, fontweight='bold')
        plt.setp(legend.get_title(), fontsize=18, fontweight='bold')
        
        self.figure.tight_layout()
        self.draw()

class TableWindow(QMainWindow):
    def __init__(self, cur, records, industry_records, shared_dict):
        super().__init__()
        big_font=QFont()
        big_font.setPointSize(15)
        big_font.setBold(True)
        self.ai_thread=None
        self.cur=cur
        self.records = records
        self.industry_records={}
        self.high_rank_rows=[]
        self.prev_high_rank_rows=[]
        for industry_record in industry_records:
            self.industry_records[industry_record[0]]=self.industry_records.get(industry_record[0],[])+[industry_record[1]]

        self.shared_dict = shared_dict
        self.setWindowTitle("PyQt Table Example")
        self.chart_mode="employees"
        self.chart_modes=["employees", "industries", "last_funding_status"]
        self.setGeometry(100, 100, 1400, 800)

        # Table header
        self.table_headers = {
            "company_name": "TEXT",
            "cb_rank": "INTEGER",
            "employees": "INTEGER",
            "short_description": "TEXT",
            "industries": "TEXT",
            "founded_date": "DATE",
            "long_description": "TEXT",
            "headquarters_location": "TEXT",
            "last_funding_type": "TEXT",
            "most_recent_valuation": "TEXT",
            "funding_status": "TEXT",
            "acquisition_status": "TEXT",
            "actively_hiring": "TEXT",
            "linkedin": "TEXT",
            "estimated_revenue": "TEXT",
            "website": "TEXT",
            "total_funding_amount": "DECIMAL(15, 2)",
            "primary_key": "SERIAL PRIMARY KEY"
        }  

        # Periodic update timer and variables
        self.update_index=0
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.periodic_updates)
        self.timer.start(100) # Timer Duration


        ### CREATION OF GUI ELEMENTS
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        ## LEFT PANEL
        #  Create left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Pie Chart to left panel
        self.pie_chart = PieChartWidget(self, width=7, height=5)
        left_layout.addWidget(self.pie_chart)

        # Switch Chart button
        button_layout = QHBoxLayout()
        self.button1 = QPushButton("Switch Chart Mode")
        self.button1.setFont(big_font)
        def switch_chart_mode():
            self.chart_mode=self.chart_modes[(self.chart_modes.index(self.chart_mode)+1)%len(self.chart_modes)]
            self.refresh_chart()
        self.button1.clicked.connect(switch_chart_mode)
        button_layout.addWidget(self.button1)
        left_layout.addLayout(button_layout)

        # add title to the text box
        self.text_box_title = QTextEdit()
        self.text_box_title.setText("Insert AI prompt below")
        self.text_box_title.setFont(big_font)
        self.text_box_title.setReadOnly(True)
        left_layout.addWidget(self.text_box_title)
        self.text_box_title.setAlignment(Qt.AlignCenter)
        self.text_box_title.setFixedHeight(30)

        # add a text box entry
        self.text_box = QTextEdit()
        self.text_box.setFont(big_font)
        left_layout.addWidget(self.text_box)

        # ai processing button called Rate Companies, below the text box entry
        self.button2 = QPushButton("Rate Companies")
        self.button2.setFont(big_font)
        self.button2.clicked.connect(self.rate_companies)
        left_layout.addWidget(self.button2)

        # add button to clear ranks
        self.button3 = QPushButton("Clear Ranks")
        self.button3.setFont(big_font)
        self.button3.clicked.connect(self.clear_ranks)
        left_layout.addWidget(self.button3)


        ## RIGHT PANEL
        # Create right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # Table to right panel
        self.table = QTableWidget()
        right_layout.addWidget(self.table)

        # Create splitter and add panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 900])  # Set initial sizes of the panels
        main_layout.addWidget(splitter)

        # Set up the table
        self.setup_table()
        self.table.sortItems(0)  # Initially sort by CB_Rank
        self.refresh_chart()

    def setup_table(self):
        # Set table dimensions
        self.records=self.records
        self.table.setRowCount(len(self.records))
        self.table.setColumnCount(len(models.crunchbase_fields.keys())+1)

        # Setup headers
        data_headers = ["rating"]+list(models.crunchbase_fields.keys())
        headers=["rating"]+list(self.table_headers.keys())
        self.table.setHorizontalHeaderLabels(headers)

        # Set larger font for horizontal header
        header_font = QFont()
        header_font.setPointSize(16)  # Increase font size for headers
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)
        content_font = QFont()
        content_font.setPointSize(15)
        content_font.setBold(True)

        # Set table data
        for i, row in enumerate(self.records):
            self.table.setItem(i, 0, NumericTableWidgetItem(0))
            for j, item in enumerate(row):
                header=headers[j+1]
                data_index=data_headers.index(header)
                item=row[data_index-1]
                if isinstance(item, (int, float)):
                    table_item = NumericTableWidgetItem(item)
                else:
                    table_item = QTableWidgetItem(str(item))
                if isinstance(item, (int, float)):
                    table_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table_item.setFont(content_font)
                self.table.setItem(i, j+1, table_item)

        # Reset columns, set sorting, configure
        self.cb_rank_column = headers.index('cb_rank')
        self.employee_count_column = headers.index('employees')
        self.industries_column = headers.index('industries')
        self.funding_series = headers.index('last_funding_type')#'funding_status')
        self.company_name_column = headers.index('company_name')
        self.long_description_column = headers.index('long_description')
        self.RANK_column=headers.index('rating')  
        self.table.setSortingEnabled(True)
        self.table.sortItems(self.cb_rank_column)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().setFixedWidth(50)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(self.company_name_column, 200) 
        self.table.setColumnWidth(self.long_description_column, 200)
        self.table.horizontalHeader().sectionClicked.connect(self.refresh_chart)

    def rate_companies(self):
        """Starts the thread to rate companies"""
        user_input=self.text_box.toPlainText()
        records, companies_context_prompt=ratings.get_companies_prompt(self.cur)
        self.records=records
        self.setup_table()
        self.setup_table()
        self.shared_dict["ratings"]=[]
        thread=threading.Thread(target=ratings.stream_data_processing_thread, args=(self.shared_dict, companies_context_prompt, user_input))
        thread.start()
        self.ai_thread=thread

    def clear_ranks(self):
        """Stops the thread and clears the ranks"""
        if self.ai_thread:
            self.shared_dict["stop_llm"]=True
            self.ai_thread.join()
            self.ai_thread=None
            self.high_rank_rows=[]
            self.shared_dict["ratings"]=[]

        # loop over table rows and clear the ranks
        for row in range(self.table.rowCount()):
            index = self.table.model().index(row, 0)
            self.table.setItem(row, 0, NumericTableWidgetItem(0))
            self.table.model().setData(index, 0)
            self.table.item(row, 0).setBackground(Qt.darkRed)

        self.update_index=0

    def periodic_updates(self):
        # Update every row with rating data
        shared_dict_length=len(shared_dict["ratings"])
        if self.update_index>shared_dict_length:
            self.update_index=0
        if (shared_dict_length>0) and (shared_dict_length!=len(self.records)):
            while self.update_index<shared_dict_length:
                rating=shared_dict["ratings"][self.update_index]
                self.table.setItem(self.update_index, 0, NumericTableWidgetItem(rating))
                self.update_index+=1
                self.table.sortItems(self.RANK_column, Qt.DescendingOrder)

        # apply color schema to all rows
        for row in range(self.table.rowCount()):
            item=self.table.item(row, 0)
            if item.value==5: #light green
                self.table.item(row, 0).setBackground(customColors.green)
                if row not in self.high_rank_rows:
                    self.high_rank_rows.append(row)
            elif item.value==4: #light blue
                self.table.item(row, 0).setBackground(customColors.yellow_green)
            elif item.value==3: #light yellow
                self.table.item(row, 0).setBackground(customColors.yellow)
            elif item.value==2: #light red
                self.table.item(row, 0).setBackground(customColors.orange)
            elif item.value==1: #light orange
                self.table.item(row, 0).setBackground(customColors.red)
            else:
                self.table.item(row, 0).setBackground(Qt.darkRed)

        # Update chart
        if (self.high_rank_rows!=[] or self.prev_high_rank_rows!=[]) and (self.high_rank_rows!=self.prev_high_rank_rows):
            self.refresh_chart()
        self.prev_high_rank_rows=self.high_rank_rows.copy()



    ## REFRESH CHART FUNCTIONS
    def refresh_chart(self):
        """Refreshes the pie chart with the most recent data"""
        rank_5_notice_str=""
        if self.high_rank_rows!=[]:
            rank_5_notice_str=",\nRank 5 companies"
        match self.chart_mode:
            case "employees":
                keys, values=self.loop_over_rows(self.process_employees)
                print(keys, values)
                self.pie_chart.update_chart(keys, values, "Employee Count"+rank_5_notice_str)
            case "industries":
                keys, values=self.loop_over_rows(self.process_industries)
                x=15
                values_keys_list=sorted(list(zip(values, keys)), reverse=True)
                values, keys=zip(*values_keys_list[:x])

                self.pie_chart.update_chart(keys, values, "Industry"+rank_5_notice_str)
            case "last_funding_status":
                keys, values=self.loop_over_rows(self.process_funding_status)
                self.pie_chart.update_chart(keys, values, "Last Funding Type"+rank_5_notice_str)
    def loop_over_rows(self, parsing_function):
        n=100
        self.top_n_pie_data={}
        if self.high_rank_rows!=[]:
            for row in self.high_rank_rows:
                parsing_function(row)
        else:
            for row in range(min(n, self.table.rowCount())):
                parsing_function(row)
        return list(self.top_n_pie_data.keys()), list(self.top_n_pie_data.values())
    def process_industries(self, row):
        company_name=self.table.item(row, self.company_name_column).text()
        industries=self.industry_records.get(company_name, [])
        if industries!=[]:
            for industry in industries:
                self.top_n_pie_data[industry]=self.top_n_pie_data.get(industry,0)+1
        else:
            industry="No Industry"
            self.top_n_pie_data[industries[0]]=self.top_n_pie_data.get(industry,0)+1
    def process_employees(self, row):
        employee_count = self.table.item(row, self.employee_count_column).value
        self.top_n_pie_data[employee_count]=self.top_n_pie_data.get(employee_count,0)+1
    def process_funding_status(self, row):
        total_funding = self.table.item(row, self.funding_series).text()
        self.top_n_pie_data[total_funding]=self.top_n_pie_data.get(total_funding,0)+1


if __name__ == "__main__":
    # Connect to postgresql database
    conn = psycopg2.connect(
        dbname="startup_database",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    # Get all crunchbase records
    cur.execute("SELECT * FROM crunchbase")
    crunchbase_records = cur.fetchall()


    # get the best companies
    funding_search_values=["'Series A'", "'Series B'","'Series C'", "'Angel'", "'Post-IPO Equity'", "'Seed'"]
    fuding_search_string=" OR last_funding_type=".join(funding_search_values)
    best_companies_query = """WITH top_200_companies AS (
        SELECT primary_key, cb_rank, company_name, last_funding_type
        FROM crunchbase
        ORDER BY cb_rank
        LIMIT 200
    ),
    seed_companies AS (
        SELECT primary_key, cb_rank, company_name, last_funding_type
        FROM crunchbase
        WHERE last_funding_type = {fuding_search_string}
    ),
    large_companies AS (
        SELECT primary_key, cb_rank, company_name, last_funding_type
        FROM crunchbase
        WHERE (employees > 10 AND cb_rank <100000)
    ),
    automation_companies AS (
        SELECT DISTINCT c.primary_key, c.cb_rank, c.company_name, c.last_funding_type
        FROM crunchbase c
        JOIN industry_connections ic ON c.primary_key = ic.crunchbase_primary_key
        WHERE ic.industry_name = 'Automation'
    ),
    chemical_companies AS (
        SELECT DISTINCT c.primary_key
        FROM crunchbase c
        JOIN industry_connections ic ON c.primary_key = ic.crunchbase_primary_key
        WHERE ic.industry_name = 'Chemical'
    )
    SELECT DISTINCT c.*
    FROM (
        SELECT * FROM top_200_companies
        UNION
        SELECT * FROM large_companies
        UNION
        SELECT * FROM automation_companies
        UNION
        SELECT * FROM seed_companies

    ) c
    WHERE c.primary_key NOT IN (SELECT primary_key FROM chemical_companies)
    """.format(fuding_search_string=fuding_search_string)
    # cur.execute(best_companies_query)
    # best_companies=cur.fetchall()

    # Get all industry connections
    cur.execute("""
    SELECT crunchbase.company_name, industry_connections.industry_name
    FROM crunchbase
    LEFT JOIN industry_connections ON crunchbase.primary_key = industry_connections.crunchbase_primary_key"""
    )
    industry_records=cur.fetchall()

    # Create a shared dictionary
    manager = Manager()
    shared_dict = manager.dict()
    shared_dict["ratings"]=[]
    shared_dict["stop_llm"]=False

    # Start the application
    app = QApplication(sys.argv)
    window = TableWindow(cur, crunchbase_records, industry_records, shared_dict)
    window.show()
    sys.exit(app.exec_())