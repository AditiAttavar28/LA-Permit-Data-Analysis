# LA Permit Data Analysis (Snowflake + Python)

## 📌 Project Overview
This project analyzes building permit activity in **Los Angeles from 2020 to 2024**, a period that includes the COVID-19 pandemic, recovery phase, and subsequent construction boom. Using permit-level data stored in Snowflake, the analysis examines how construction activity evolved over time, where it concentrated geographically, what types of projects dominated, how investment was distributed across project sizes, and which contractors were most active.

The findings show that LA’s construction growth during this period was driven largely by **alterations, repairs, and infrastructure upgrades rather than new construction**. While permit activity is highly concentrated in a small number of ZIP codes, total investment is uneven—many neighborhoods generate high permit counts from small projects, while a small share of large-scale projects accounts for a disproportionate amount of total project value. Contractor activity further reveals a highly fragmented industry, with thousands of firms contributing to overall volume and a smaller group handling high-value developments.

Together, these insights provide a data-driven view of how everyday home improvements and a limited number of capital-intensive projects collectively shape Los Angeles’s built environment.

---

## 🗄️ Data Source
- **Database:** `LA_PERMIT_DATA`
- **Platform:** Snowflake

> Note: The database itself is not included in this repository.  
> This project assumes access to the Snowflake database.

---

## 🧪 Tools & Technologies
- Snowflake
- Python
- Jupyter Notebook
- Matplotlib
- Conda (environment management)
- Git & GitHub

---

## 📂 Repository Structure
```text
LA-Permit-Data-Analysis/
│── notebooks/
│   └── la_permit_analysis.ipynb
│── environment.yml
│── docs/
│   └── project_writeup.pdf
│── README.md
│── .gitignore
