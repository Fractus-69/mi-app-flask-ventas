from flask import Flask, render_template
import pyodbc
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

DB_CONFIG = {
    'server': 'practica-teamb.database.windows.net',
    'database': 'db-teamb',
    'username': 'misesion-practica-teamb',
    'password': '666-equipob-999',
}

def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']},1433;"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

def generar_grafico(productos, valores, tipo='barh', titulo=''):
    fig, ax = plt.subplots()
    if tipo == 'barh':
        ax.barh(productos, valores, color='skyblue')
        ax.set_xlim(0, 800)
        for i, v in enumerate(valores):
            ax.text(v, i, f"${v:.2f}", va='center')
        ax.set_xlabel('Total vendido (USD)')
        ax.set_ylabel('Producto')
    elif tipo == 'pie':
        ax.pie(valores, labels=productos, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
    elif tipo == 'line':
        x = list(range(len(productos)))
        ax.plot(x, valores, marker='o', linestyle='-', color='green')
        ax.set_xticks(x)
        ax.set_xticklabels(productos, rotation=45, ha='right')
        ax.set_xlabel('Producto')
        ax.set_ylabel('Total vendido (USD)')
    elif tipo == 'hist':
        ax.bar(productos, valores, color='orange', edgecolor='black')
        ax.set_xlabel('Producto')
        ax.set_ylabel('Unidades vendidas')
        plt.xticks(rotation=45, ha='right')
    ax.set_title(titulo)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return image_base64

@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 20 ID, Fecha, Cliente, Producto, Cantidad, Precio FROM Ventas ORDER BY Fecha DESC")
    ventas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', ventas=ventas)

@app.route('/estadisticas')
def estadisticas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(Cantidad * Precio), AVG(Precio) FROM Ventas")
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("estadisticas.html", total=data[0], suma=data[1], promedio=data[2])

@app.route('/graficos')
def graficos():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT Producto, SUM(Cantidad * Precio) FROM Ventas GROUP BY Producto")
    datos = cursor.fetchall()
    productos = [row[0] for row in datos]
    totales = [float(row[1]) for row in datos]

    barh_img = generar_grafico(productos, totales, tipo='barh', titulo='Total de ventas por unidad (USD)')

    cursor.execute("SELECT Producto, SUM(Cantidad) FROM Ventas GROUP BY Producto")
    datos_hist = cursor.fetchall()
    productos_hist = [row[0] for row in datos_hist]
    unidades_hist = [int(row[1]) for row in datos_hist]
    hist_img = generar_grafico(productos_hist, unidades_hist, tipo='hist', titulo='Distribución de unidades vendidas por producto')

    top5 = sorted(zip(productos, totales), key=lambda x: x[1], reverse=True)[:5]
    pie_img = generar_grafico([x[0] for x in top5], [x[1] for x in top5], tipo='pie', titulo='Participación por producto (TOP 5)')
    line_img = generar_grafico(productos, totales, tipo='line', titulo='Tendencia de ventas por producto')
    cursor.close()
    conn.close()

    return render_template("graficos.html",
        barh_img=barh_img,
        hist_img=hist_img,
        pie_img=pie_img,
        line_img=line_img,
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
