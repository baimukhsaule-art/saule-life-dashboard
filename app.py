import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path("saule_life.db")

st.set_page_config(page_title="Штаб Сауле", page_icon="🧭", layout="wide")


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS incomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        source TEXT,
        category TEXT,
        amount REAL,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        category TEXT,
        amount REAL,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creditor TEXT,
        balance REAL,
        monthly_payment REAL,
        payment_day INTEGER,
        interest_rate REAL,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS body_weight (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        weight REAL,
        waist REAL,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS health (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        sleep_hours REAL,
        energy INTEGER,
        mood INTEGER,
        stress INTEGER,
        symptoms TEXT,
        food_triggers TEXT,
        meds TEXT,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beauty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        area TEXT,
        action TEXT,
        cost REAL,
        result TEXT,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        sphere TEXT,
        status TEXT,
        priority INTEGER,
        potential_income REAL,
        next_step TEXT,
        comment TEXT
    )
    """)

    conn.commit()
    conn.close()


def read_table(table):
    conn = connect()
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


def add_row(table, data):
    conn = connect()
    cur = conn.cursor()
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    cur.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()


def delete_by_id(table, row_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()


init_db()

# Стартовые данные, если база пустая
if read_table("incomes").empty:
    add_row("incomes", {
        "entry_date": str(date.today()),
        "source": "Зарплата",
        "category": "Основной доход",
        "amount": 300000,
        "comment": "Стартовая запись"
    })
    add_row("incomes", {
        "entry_date": str(date.today()),
        "source": "Подработка",
        "category": "Дополнительный доход",
        "amount": 200000,
        "comment": "Стартовая запись"
    })

st.title("🧭 Штаб Сауле")
st.caption("Личная ERP: деньги, долги, вес, здоровье, красота, психика, проекты и дом.")

menu = st.sidebar.radio(
    "Разделы",
    [
        "Сегодня",
        "Доходы",
        "Расходы",
        "Банковские выписки",
        "Долги",
        "Вес",
        "Здоровье и настроение",
        "Красота",
        "Проекты и дом",
    ]
)

incomes = read_table("incomes")
expenses = read_table("expenses")
debts = read_table("debts")
weights = read_table("body_weight")
health_df = read_table("health")
projects = read_table("projects")

if menu == "Сегодня":
    total_income = incomes["amount"].sum() if not incomes.empty else 0
    total_expense = expenses["amount"].sum() if not expenses.empty else 0
    total_debt = debts["balance"].sum() if not debts.empty else 0
    monthly_debt_payments = debts["monthly_payment"].sum() if not debts.empty else 0
    balance = total_income - total_expense - monthly_debt_payments

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Доходы", f"{total_income:,.0f} тг".replace(",", " "))
    c2.metric("Расходы", f"{total_expense:,.0f} тг".replace(",", " "))
    c3.metric("Платежи по долгам", f"{monthly_debt_payments:,.0f} тг".replace(",", " "))
    c4.metric("Остаток", f"{balance:,.0f} тг".replace(",", " "))

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("📉 Долги")
        st.metric("Общий остаток долгов", f"{total_debt:,.0f} тг".replace(",", " "))
        if not debts.empty:
            st.dataframe(debts[["creditor", "balance", "monthly_payment", "payment_day"]], use_container_width=True)
        else:
            st.info("Добавь первый долг в разделе 'Долги'.")

        st.subheader("⚖️ Вес")
        if not weights.empty:
            weights_chart = weights.copy()
            weights_chart["entry_date"] = pd.to_datetime(weights_chart["entry_date"])
            st.line_chart(weights_chart.set_index("entry_date")[["weight"]])
        else:
            st.info("Добавь первый вес в разделе 'Вес'.")

    with right:
        st.subheader("🧠 Последнее состояние")
        if not health_df.empty:
            latest = health_df.tail(1).iloc[0]
            st.write(f"Настроение: **{latest['mood']}/10**")
            st.write(f"Энергия: **{latest['energy']}/10**")
            st.write(f"Стресс: **{latest['stress']}/10**")
            st.write(f"Сон: **{latest['sleep_hours']} ч**")
            st.write(f"Симптомы: {latest['symptoms'] or 'нет записи'}")
        else:
            st.info("Заполни дневник здоровья и настроения.")

        st.subheader("🎯 Активные проекты")
        if not projects.empty:
            active = projects.sort_values("priority", ascending=False).head(5)
            st.dataframe(active[["name", "sphere", "status", "priority", "next_step"]], use_container_width=True)
        else:
            st.info("Добавь проект: фасады, 1С, дом, калькуляторы, отель.")

elif menu == "Доходы":
    st.header("💰 Доходы")
    with st.form("income_form"):
        entry_date = st.date_input("Дата", value=date.today())
        source = st.text_input("Источник", value="Зарплата")
        category = st.selectbox("Категория", ["Основной доход", "Дополнительный доход", "Сделка", "Возврат долга", "Другое"])
        amount = st.number_input("Сумма", min_value=0.0, step=1000.0)
        comment = st.text_area("Комментарий")
        submitted = st.form_submit_button("Добавить доход")
        if submitted:
            add_row("incomes", {"entry_date": str(entry_date), "source": source, "category": category, "amount": amount, "comment": comment})
            st.success("Доход добавлен")
            st.rerun()
    st.dataframe(read_table("incomes"), use_container_width=True)

elif menu == "Расходы":
    st.header("🧾 Расходы")
    with st.form("expense_form"):
        entry_date = st.date_input("Дата", value=date.today())
        category = st.selectbox("Категория", ["Еда", "Коммунальные", "Коты", "Транспорт", "Здоровье", "Красота", "Дом", "Долги", "Другое"])
        amount = st.number_input("Сумма", min_value=0.0, step=1000.0)
        comment = st.text_area("Комментарий")
        submitted = st.form_submit_button("Добавить расход")
        if submitted:
            add_row("expenses", {"entry_date": str(entry_date), "category": category, "amount": amount, "comment": comment})
            st.success("Расход добавлен")
            st.rerun()
    st.dataframe(read_table("expenses"), use_container_width=True)

elif menu == "Банковские выписки":
    st.header("📥 Банковские выписки")

    uploaded_files = st.file_uploader(
        "Выбери выписки Excel",
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            df = pd.read_excel(file)

            st.subheader(file.name)
            st.write(f"Строк: {len(df)}")
            st.dataframe(df, use_container_width=True)

elif menu == "Долги":
    st.header("📉 Долги")
    with st.form("debt_form"):
        creditor = st.text_input("Кредитор")
        balance = st.number_input("Остаток долга", min_value=0.0, step=10000.0)
        monthly_payment = st.number_input("Ежемесячный платёж", min_value=0.0, step=1000.0)
        payment_day = st.number_input("День платежа", min_value=1, max_value=31, step=1)
        interest_rate = st.number_input("Процентная ставка, если знаешь", min_value=0.0, step=0.1)
        comment = st.text_area("Комментарий")
        submitted = st.form_submit_button("Добавить долг")
        if submitted:
            add_row("debts", {"creditor": creditor, "balance": balance, "monthly_payment": monthly_payment, "payment_day": payment_day, "interest_rate": interest_rate, "comment": comment})
            st.success("Долг добавлен")
            st.rerun()
    st.dataframe(read_table("debts"), use_container_width=True)

elif menu == "Вес":
    st.header("⚖️ Вес и замеры")
    with st.form("weight_form"):
        entry_date = st.date_input("Дата", value=date.today())
        weight = st.number_input("Вес, кг", min_value=0.0, step=0.1)
        waist = st.number_input("Талия, см", min_value=0.0, step=0.5)
        comment = st.text_area("Комментарий")
        submitted = st.form_submit_button("Добавить запись")
        if submitted:
            add_row("body_weight", {"entry_date": str(entry_date), "weight": weight, "waist": waist, "comment": comment})
            st.success("Запись добавлена")
            st.rerun()
    df = read_table("body_weight")
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"])
        st.line_chart(df.set_index("entry_date")[["weight"]])

elif menu == "Здоровье и настроение":
    st.header("❤️ Здоровье и психологическая поддержка")
    with st.form("health_form"):
        entry_date = st.date_input("Дата", value=date.today())
        sleep_hours = st.number_input("Сон, часов", min_value=0.0, max_value=24.0, step=0.5)
        energy = st.slider("Энергия", 1, 10, 5)
        mood = st.slider("Настроение", 1, 10, 5)
        stress = st.slider("Стресс", 1, 10, 5)
        symptoms = st.text_area("Симптомы")
        food_triggers = st.text_area("Еда / возможные триггеры")
        meds = st.text_area("Лекарства / добавки")
        comment = st.text_area("Мысли, поддержка, что сегодня важно")
        submitted = st.form_submit_button("Сохранить день")
        if submitted:
            add_row("health", {
                "entry_date": str(entry_date), "sleep_hours": sleep_hours, "energy": energy,
                "mood": mood, "stress": stress, "symptoms": symptoms,
                "food_triggers": food_triggers, "meds": meds, "comment": comment
            })
            st.success("День сохранён")
            st.rerun()
    df = read_table("health")
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        chart = df.copy()
        chart["entry_date"] = pd.to_datetime(chart["entry_date"])
        st.line_chart(chart.set_index("entry_date")[["energy", "mood", "stress"]])

elif menu == "Красота":
    st.header("✨ Красота и уход")
    with st.form("beauty_form"):
        entry_date = st.date_input("Дата", value=date.today())
        area = st.selectbox("Зона", ["Волосы", "Кожа", "Лицо", "Тело", "Ногти", "Одежда/стиль", "Другое"])
        action = st.text_input("Что сделано")
        cost = st.number_input("Стоимость", min_value=0.0, step=1000.0)
        result = st.text_area("Эффект / результат")
        comment = st.text_area("Комментарий")
        submitted = st.form_submit_button("Добавить")
        if submitted:
            add_row("beauty", {"entry_date": str(entry_date), "area": area, "action": action, "cost": cost, "result": result, "comment": comment})
            st.success("Запись добавлена")
            st.rerun()
    st.dataframe(read_table("beauty"), use_container_width=True)

elif menu == "Проекты и дом":
    st.header("🎯 Проекты и дом")
    with st.form("project_form"):
        name = st.text_input("Название")
        sphere = st.selectbox("Сфера", ["Работа", "Дом", "Фасады", "1С", "Отель", "Финансы", "Здоровье", "Другое"])
        status = st.selectbox("Статус", ["Идея", "В работе", "Ждёт", "Сделано", "Заморожено"])
        priority = st.slider("Приоритет", 1, 10, 5)
        potential_income = st.number_input("Потенциальный доход/экономия", min_value=0.0, step=10000.0)
        next_step = st.text_input("Следующий шаг")
        comment = st.text_area("Комментарий")
        submitted = st.form_submit_button("Добавить проект")
        if submitted:
            add_row("projects", {"name": name, "sphere": sphere, "status": status, "priority": priority, "potential_income": potential_income, "next_step": next_step, "comment": comment})
            st.success("Проект добавлен")
            st.rerun()
    st.dataframe(read_table("projects"), use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("Версия 0.1. Сначала учёт. Потом добавим аналитику и умные подсказки.")
