import mysql.connector
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
import uuid  # لتوليد رموز جلسة فريدة



app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='sql.freedb.tech',
            user='freedb_11111',           # Change this to your MySQL username
            password='Q5rB!Q$Ur4trJYQ',    # Change this to your MySQL password
            database='freedb_ahmedsabah1998ah@gmail.com'   # Change this to your database name
        )

          # ← أضف هنا لضبط المنطقة الزمنية لجميع الجلسات
        cursor = conn.cursor()
        cursor.execute("SET time_zone = '+03:00'")
        cursor.close()

        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def create_tables_if_not_exist():
    conn = get_db_connection()
    cursor = conn.cursor()
    

    cursor.execute("SHOW COLUMNS FROM kitchens LIKE 'image'")
    if not cursor.fetchone():
         cursor.execute("ALTER TABLE kitchens ADD COLUMN image VARCHAR(255)")
    cursor.execute("SHOW COLUMNS FROM kitchens LIKE 'initial_quantity'")
    if not cursor.fetchone():
         cursor.execute("ALTER TABLE kitchens ADD COLUMN initial_quantity INT DEFAULT 0")




    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        table_id VARCHAR(10),
        discount FLOAT,
        discount_type VARCHAR(20),
        total_before INT,
        total_after INT,
        customer_name VARCHAR(100),
        customer_phone VARCHAR(20),
        customer_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # After creating the table, then check and add columns
    cursor.execute("SHOW COLUMNS FROM orders LIKE 'notes'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE orders ADD COLUMN notes TEXT")

    cursor.execute("SHOW COLUMNS FROM orders LIKE 'is_saved'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE orders ADD COLUMN is_saved TINYINT DEFAULT 0")
    
    cursor.execute("SHOW COLUMNS FROM orders LIKE 'customer_name'")
    if not cursor.fetchone():
      cursor.execute("ALTER TABLE orders ADD COLUMN customer_name VARCHAR(100)")

    cursor.execute("SHOW COLUMNS FROM orders LIKE 'customer_phone'")
    if not cursor.fetchone():
      cursor.execute("ALTER TABLE orders ADD COLUMN customer_phone VARCHAR(20)")

    cursor.execute("SHOW COLUMNS FROM orders LIKE 'is_paid'")
    if not cursor.fetchone():
      cursor.execute("ALTER TABLE orders ADD COLUMN is_paid TINYINT DEFAULT 0")

    cursor.execute("SHOW COLUMNS FROM orders LIKE 'invoice_name'")
    if not cursor.fetchone():
      cursor.execute("ALTER TABLE orders ADD COLUMN invoice_name VARCHAR(255)")

    cursor.execute("SHOW COLUMNS FROM orders LIKE 'customer_address'")
    if not cursor.fetchone():
         cursor.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT")

    cursor.execute("SHOW COLUMNS FROM orders LIKE 'invoice_number'")
    if not cursor.fetchone():
         cursor.execute("ALTER TABLE orders ADD COLUMN invoice_number INT DEFAULT 1")

    # Create expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        expense_name VARCHAR(255),
        supplier_name VARCHAR(255),
        amount DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute("SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME = 'tables' AND COLUMN_NAME = 'hall_id' AND REFERENCED_TABLE_NAME = 'halls'")
    constraint = cursor.fetchone()
    if constraint:
           cursor.execute(f"ALTER TABLE tables DROP FOREIGN KEY {constraint[0]}")
    cursor.execute("""
    ALTER TABLE tables
    ADD CONSTRAINT fk_tables_hall
    FOREIGN KEY (hall_id) REFERENCES halls(id)
    ON DELETE CASCADE
""")


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            item_name VARCHAR(100),
            quantity INT,
            total_price INT,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    """)



# ✅ إنشاء جدول بيانات المحل إذا لم يكن موجودًا
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS business_info (
        id INT AUTO_INCREMENT PRIMARY KEY,
        shop_name VARCHAR(255),
        phone VARCHAR(100),
        social VARCHAR(255)
    )
''')
    cursor.execute("SHOW COLUMNS FROM business_info LIKE 'logo'")
    if not cursor.fetchone():
           cursor.execute("ALTER TABLE business_info ADD COLUMN logo VARCHAR(255)")


    conn.commit()
    cursor.close()
    conn.close()


@app.route('/halls', methods=['GET'])
def get_halls():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM halls')
    halls = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(halls)



@app.route('/halls', methods=['POST'])
def add_hall():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO halls (name) VALUES (%s)', (data['name'],))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({'id': new_id, 'message': 'تمت إضافة الصالة'})
@app.route('/expenses/filter', methods=['POST'])
def filter_expenses():
    data = request.json
    from_date = data.get('from_date')
    to_date = data.get('to_date')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM expenses WHERE created_at BETWEEN %s AND %s ORDER BY created_at DESC"
    cursor.execute(query, (from_date, to_date))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)


@app.route('/tables', methods=['GET'])
def get_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tables')
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tables)


@app.route('/report/profits')
def report_profits():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT oi.item_name, oi.quantity, oi.total_price, k.cost_price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN kitchens k ON oi.item_name = k.name
        WHERE o.is_paid = 1
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

    
@app.route('/report/profits/filter', methods=['POST'])
def report_profits_filtered():
    data = request.get_json()
    from_date = data.get('from_date')
    to_date = data.get('to_date')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT oi.item_name, oi.quantity, oi.total_price, k.cost_price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN kitchens k ON oi.item_name = k.name
        WHERE o.is_paid = 1 AND o.created_at BETWEEN %s AND %s
    """, (from_date, to_date))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)
@app.route('/report/sales-summary', methods=['POST'])
def sales_summary():
    data = request.get_json()
    from_date = data.get('from_date')
    to_date = data.get('to_date')
    status = data.get('status', 'all')
    hall_id = data.get('hall_id')
    table_id = data.get('table_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    condition = "WHERE o.created_at BETWEEN %s AND %s"
    params = [from_date, to_date]

    if status == 'paid':
        condition += " AND o.is_paid = 1"
    elif status == 'unpaid':
        condition += " AND o.is_paid = 0"

    if hall_id and str(hall_id).isdigit():
        condition += " AND t.hall_id = %s"
        params.append(int(hall_id))

    if table_id and str(table_id).isdigit():
        condition += " AND o.table_id = %s"
        params.append(int(table_id))

    try:
        # الإحصائيات العامة
        cursor.execute(f"""
            SELECT 
                COUNT(*) AS invoice_count,
                SUM(o.total_before) AS total_before,
                SUM(o.total_after) AS total_after,
                SUM(o.total_before - o.total_after) AS total_discounts
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            {condition}
        """, params)
        stats = cursor.fetchone() or {}

        # المواد حسب الطلبات
        cursor.execute(f"""
            SELECT 
                oi.item_name,
                SUM(oi.quantity) AS quantity,
                SUM(oi.total_price) AS total_price,
                SUM(oi.quantity * k.cost_price) AS total_cost,
                SUM(oi.total_price - oi.quantity * k.cost_price) AS profit
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN kitchens k ON oi.item_name = k.name
            LEFT JOIN tables t ON o.table_id = t.id
            {condition}
            GROUP BY oi.item_name
        """, params)
        items = cursor.fetchall()

        # حسب المطبخ
        cursor.execute(f"""
            SELECT 
                k.type AS kitchen_name,
                COUNT(DISTINCT oi.item_name) AS item_count,
                SUM(oi.total_price) AS total_price,
                SUM(oi.quantity * k.cost_price) AS total_cost,
                SUM(oi.total_price - oi.quantity * k.cost_price) AS profit
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN kitchens k ON oi.item_name = k.name
            LEFT JOIN tables t ON o.table_id = t.id
            {condition}
            GROUP BY k.type
        """, params)
        kitchens = cursor.fetchall()

        return jsonify({
            'stats': stats,
            'items': items,
            'kitchens': kitchens
        })

    except Exception as e:
        print("🔥 خطأ:", e)
        return jsonify({'error': 'خطأ داخلي في الخادم'}), 500
    finally:
        cursor.close()
        conn.close()


# تحديث صالة
@app.route('/halls/<int:hall_id>', methods=['PUT'])
def update_hall(hall_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE halls SET name=%s WHERE id=%s', (data['name'], hall_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم تعديل الصالة بنجاح'})

# حذف صالة
@app.route('/halls/<int:hall_id>', methods=['DELETE'])
def delete_hall(hall_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM halls WHERE id=%s', (hall_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم حذف الصالة بنجاح'})

# تحديث طاولة
@app.route('/tables/<int:table_id>', methods=['PUT'])
def update_table(table_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tables SET name=%s WHERE id=%s', (data['name'], table_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم تعديل الطاولة بنجاح'})

# حذف طاولة
@app.route('/tables/<int:table_id>', methods=['DELETE'])
def delete_table(table_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tables WHERE id=%s', (table_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم حذف الطاولة بنجاح'})
@app.route('/delete-order/<table_id>', methods=['DELETE'])
def delete_order(table_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # نحصل على أحدث طلب غير مدفوع
    cursor.execute("""
        SELECT id FROM orders
        WHERE table_id = %s AND is_paid = 0
        ORDER BY created_at DESC
        LIMIT 1
    """, (table_id,))
    row = cursor.fetchone()

    if row:
        order_id = row[0]
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    else:
        cursor.close()
        conn.close()
        return jsonify({'success': False})

@app.route('/attendance', methods=['GET', 'POST'])
def handle_attendance():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("""
            SELECT a.*, e.name as employee_name
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            ORDER BY a.timestamp DESC
        """)
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(logs)

    elif request.method == 'POST':
        try:
            data = request.json
            print("📥 البيانات المستلمة:", data)

            employee_id = data.get('employee_id')
            action = data.get('action')
            rating = data.get('rating')
            penalty = int(data.get('penalty', 0))

            if not all([employee_id, action, rating]):
                return jsonify({'error': '⚠️ بيانات ناقصة'}), 400

            cursor.execute("""
                INSERT INTO attendance (employee_id, action, rating, penalty)
                VALUES (%s, %s, %s, %s)
            """, (employee_id, action, rating, penalty))

            conn.commit()
            print("✅ تم حفظ الحضور بنجاح")
            return jsonify({'message': 'تم تسجيل الحضور/الانصراف'})
        except Exception as e:
            print("🔥 خطأ في attendance:", e)
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()


@app.route('/expenses', methods=['GET', 'POST'])
def handle_expenses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM expenses ORDER BY created_at DESC")
        expenses = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(expenses)

    elif request.method == 'POST':
        data = request.json
        cursor.execute('INSERT INTO expenses (expense_name, supplier_name, amount) VALUES (%s, %s, %s)', 
                       (data['expense_name'], data['supplier_name'], data['amount']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'تمت إضافة المصروف بنجاح'})



@app.route('/orders-by-table/<int:table_id>')
def get_orders_by_table(table_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM orders WHERE table_id = %s AND is_paid = 0 ORDER BY invoice_number", (table_id,))
        orders = cursor.fetchall()

        if not orders:
            cursor.execute("SELECT MAX(invoice_number) FROM orders WHERE table_id = %s", (table_id,))
            result = cursor.fetchone()
            next_invoice = (result['MAX(invoice_number)'] or 0) + 1

            cursor.execute("""
    INSERT INTO orders (table_id, discount, discount_type, total_before, total_after, invoice_number, is_paid, is_saved, invoice_name)
    VALUES (%s, 0, 'مقطوع', 0, 0, %s, 0, 0, %s)
""", (table_id, next_invoice, f"فاتورة {next_invoice}"))


            conn.commit()

            cursor.execute("SELECT * FROM orders WHERE table_id = %s AND is_paid = 0 ORDER BY invoice_number", (table_id,))
            orders = cursor.fetchall()

        formatted = []
        for order in orders:
            cursor.execute("SELECT item_name, quantity, total_price FROM order_items WHERE order_id = %s", (order['id'],))
            items = cursor.fetchall()

            formatted.append({
                "id": order["invoice_number"],
                "name": order.get("invoice_name") or f"فاتورة {order['invoice_number']}",


                "orders": [
                    {
                        "name": item["item_name"],
                        "quantity": item["quantity"],
                        "total": item["total_price"]
                    }
                    for item in items
                ]
            })

        cursor.close()
        conn.close()
        return jsonify(formatted)

    except Exception as e:
        print("🔥 خطأ في orders-by-table:", e)
        return jsonify({'error': 'خطأ في السيرفر', 'details': str(e)}), 500

 
@app.route('/save-order', methods=['POST'])
def save_order():
    data = request.get_json()
    raw_invoice = data.get('invoice_number', 1)
    try:
         invoice_number = int(raw_invoice)
    except (ValueError, TypeError):
         invoice_number = 1





    table_id = data.get('table_id')
    discount = data.get('discount')
    discount_type = data.get('discount_type')
    total_before = data.get('total_before')
    total_after = data.get('total_after')
    orders = data.get('orders', [])
    is_paid = data.get('is_paid', 0)
    customer_name = data.get('customer_name')
    customer_phone = data.get('customer_phone')
    customer_address = data.get('customer_address')
    invoice_name = data.get('invoice_name')

    notes = data.get('notes', '')


    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)


    # تحقق من وجود طلب سابق غير مدفوع
    cursor.execute("""
    SELECT id FROM orders
    WHERE table_id = %s AND invoice_number = %s AND is_paid = 0
""", (table_id, invoice_number))


    existing = cursor.fetchone()

    if existing:
        order_id = existing[0]
        cursor.execute("""
    UPDATE orders
    SET discount=%s, discount_type=%s, total_before=%s, total_after=%s,
        customer_name=%s, customer_phone=%s, customer_address=%s,
        is_paid=%s, notes=%s, invoice_name=%s, is_saved=1


    WHERE id=%s
""", (discount, discount_type, total_before, total_after,
      customer_name, customer_phone, customer_address,
      is_paid, notes, invoice_name, order_id))


        # حذف العناصر القديمة
        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
    else:
        cursor.execute("""
    INSERT INTO orders (table_id, discount, discount_type, total_before, total_after, invoice_number,
customer_name, customer_phone, customer_address, is_paid, notes, invoice_name, is_saved)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)

""", (table_id, discount, discount_type, total_before, total_after, invoice_number,
      customer_name, customer_phone, customer_address, is_paid, notes, invoice_name))
        conn.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        order_id = cursor.fetchone()[0]




    # حفظ العناصر مهما كان الطلب جديد أو قديم
    for item in orders:
        cursor.execute(
            "INSERT INTO order_items (order_id, item_name, quantity, total_price) VALUES (%s, %s, %s, %s)",
            (order_id, item['name'], item['quantity'], item['total'])
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'ok', 'order_id': order_id})

   




 
@app.route('/tables/<int:hall_id>', methods=['GET'])
def get_tables(hall_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tables WHERE hall_id = %s', (hall_id,))
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tables)

@app.route('/update-invoice-name/<int:invoice_id>', methods=['PUT'])
def update_invoice_name(invoice_id):
    data = request.get_json()
    new_name = data.get('name')
    if not new_name:
        return jsonify({'success': False, 'message': 'اسم غير صالح'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET invoice_name = %s WHERE invoice_number = %s", (new_name, invoice_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


@app.route('/update-invoice-name', methods=['POST'])
def update_invoice_name_post():
    data = request.json
    invoice_number = data.get("invoice_number")
    invoice_name = data.get("invoice_name")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE orders SET invoice_name = %s WHERE invoice_number = %s AND is_paid = 0", (invoice_name, invoice_number))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("❌ خطأ في تحديث اسم الفاتورة:", e)
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()



@app.route('/tables', methods=['POST'])
def add_table():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tables (name, hall_id) VALUES (%s, %s)', (data['name'], data['hall_id']))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({'id': new_id, 'message': 'تمت إضافة الطاولة'})




@app.route('/kitchens', methods=['GET'])
def get_kitchens():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM kitchens') 
    kitchens = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(kitchens)

@app.route('/kitchens', methods=['POST'])
def add_kitchen():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # احصل على initial_quantity مع قيمة افتراضية 0 إذا لم تكن موجودة
        initial_quantity = data.get('initial_quantity', 0)
        # تأكد أنها رقم صحيح
        try:
            initial_quantity = int(initial_quantity) if initial_quantity is not None else 0
        except ValueError:
            initial_quantity = 0 # قيمة افتراضية إذا كان التحويل غير صالح

        cursor.execute(
            '''INSERT INTO kitchens 
            (name, type, group_name, cost_price, hall_price, takeaway_price, initial_quantity, note, favorite, image) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', # <-- تمت إضافة %s
            (data.get('name'), data.get('type'), data.get('group_name'), 
             data.get('cost_price'), data.get('hall_price'), 
             data.get('takeaway_price'), initial_quantity, # <-- تم إضافة initial_quantity هنا
             data.get('note'), data.get('favorite', 0), data.get('image', ''))
        )
        
        new_id = cursor.lastrowid
        conn.commit()
        return jsonify({'message': 'المادة حفظت بنجاح', 'id': new_id})
        
    except Exception as e:
        print(f"Error saving kitchen: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()
@app.route("/profits", methods=["GET"])
def get_profits():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ✅ استخدم العمود الموجود فعلياً في قاعدة البيانات
        cursor.execute("SELECT SUM(total_after) AS total_sales FROM orders WHERE is_paid = 1")
        result = cursor.fetchone()

        return jsonify({
            "total_sales": result["total_sales"] or 0
        })

    except Exception as e:
        print("❌ خطأ:", e)
        return jsonify({"error": "❌ الملف غير متاح"}), 500

@app.route('/profits/filter', methods=['POST'])
def get_filtered_profits():
    data = request.get_json()
    from_date = data.get('from_date')
    to_date = data.get('to_date')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # إجمالي المبيعات خلال الفترة
        cursor.execute("""
            SELECT SUM(total_after) AS total_sales
            FROM orders
            WHERE is_paid = 1 AND created_at BETWEEN %s AND %s
        """, (from_date, to_date))
        sales_result = cursor.fetchone()
        total_sales = sales_result['total_sales'] or 0

        # إجمالي المصروفات خلال الفترة
        cursor.execute("""
            SELECT SUM(amount) AS total_expenses
            FROM expenses
            WHERE created_at BETWEEN %s AND %s
        """, (from_date, to_date))
        expenses_result = cursor.fetchone()
        total_expenses = expenses_result['total_expenses'] or 0

        # حساب صافي الأرباح
        net_profit = total_sales - total_expenses

        return jsonify({
            "total_sales": total_sales,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        })

    except Exception as e:
        print("❌ خطأ:", e)
        return jsonify({"error": "خطأ أثناء حساب الأرباح"}), 500


@app.route('/active-invoices-count/<int:table_id>')
def get_active_invoice_count(table_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM orders
        WHERE table_id = %s AND is_paid = 0
    """, (table_id,))
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return jsonify({'count': count})

@app.route('/kitchens/<int:kitchen_id>', methods=['DELETE'])
def delete_kitchen(kitchen_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM kitchens WHERE id = %s', (kitchen_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'المادة حُذفت بنجاح'})

@app.route('/kitchens/<int:kitchen_id>', methods=['PUT'])
def update_kitchen(kitchen_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        initial_quantity = data.get('initial_quantity')
        try:
            initial_quantity = int(initial_quantity) if initial_quantity not in (None, '', 'null') else 0
        except ValueError:
            initial_quantity = 0

        cursor.execute("""
            UPDATE kitchens SET 
                name=%s,
                type=%s,
                group_name=%s,
                cost_price=%s,
                hall_price=%s,
                takeaway_price=%s,
                initial_quantity=%s,
                note=%s,
                favorite=%s,
                image=%s
            WHERE id=%s
        """, (
            data.get('name'),
            data.get('type'),
            data.get('group_name'),
            data.get('cost_price'),
            data.get('hall_price'),
            data.get('takeaway_price'),
            initial_quantity,
            data.get('note'),
            data.get('favorite', 0),
            data.get('image', ''),
            kitchen_id
        ))

        conn.commit()
        return jsonify({'message': 'تم تعديل المادة بنجاح'})

    except Exception as e:
        print(f"❌ Error updating kitchen: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.route('/groups', methods=['GET'])
def get_groups():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `groups`")
    groups = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(groups)


@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم إرسال صورة'})

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'اسم الملف فارغ'})

    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)  # ينشئ المجلد إذا لم يكن موجودًا

    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)

    return jsonify({'success': True, 'filename': file.filename})


@app.route('/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    try:
        data = request.json
        name = data.get('name')

        if not name:
            return jsonify({'error': 'الاسم مطلوب'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE `groups` SET name=%s WHERE id=%s',
            (name, group_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'تم تعديل المجموعة بنجاح'})

    except Exception as e:
        print("🔥 خطأ أثناء تعديل المجموعة:", e)
        return jsonify({'error': str(e)}), 500


    except Exception as e:
        print("🔥 خطأ أثناء التعديل:", e)
        return jsonify({'error': 'خطأ داخلي في السيرفر'}), 500


@app.route('/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM `groups` WHERE id=%s', (group_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/delete-invoice/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # نجلب كل الطلبات المرتبطة بالفاتورة
        cursor.execute('SELECT id FROM orders WHERE invoice_number = %s', (invoice_id,))
        order_ids = cursor.fetchall()

        if not order_ids:
            return jsonify({"success": False, "message": "لا توجد فواتير بهذا الرقم"})

        # نحذف العناصر المرتبطة بكل طلب
        for (order_id,) in order_ids:
            cursor.execute('DELETE FROM order_items WHERE order_id = %s', (order_id,))

        # نحذف الطلبات نفسها
        cursor.execute('DELETE FROM orders WHERE invoice_number = %s', (invoice_id,))
        conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/kitchen-types/<int:type_id>', methods=['DELETE'])
def delete_kitchen_type(type_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM kitchen_types WHERE id = %s', (type_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم حذف المطبخ بنجاح'})


@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, created_at FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data['username']
    password = generate_password_hash(data['password'])
    role = data.get('role', 'user')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                   (username, password, role))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم إنشاء المستخدم'})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'تم حذف المستخدم'})


@app.route('/reset-db', methods=['DELETE'])
def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        # فقط جلب الجداول الحقيقية (لا تشمل العروض/Views)
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE `{table}`")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        return jsonify({'message': 'تم حذف جميع البيانات بنجاح'})
    except Exception as e:
        conn.rollback()
        print("Error resetting DB:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        # 🟢 توليد رمز جلسة جديد
        session_token = str(uuid.uuid4())
        user_ip = request.remote_addr
        cursor.execute("INSERT INTO sessions (user_id, session_token, user_ip) VALUES (%s, %s, %s)", (user['id'], session_token, user_ip))

        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'token': session_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        })
    else:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'بيانات الدخول غير صحيحة'})


# ✅ أضف هنا:
@app.route('/kitchen-types', methods=['GET', 'POST'])
def handle_kitchen_types():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute('SELECT * FROM kitchen_types')
        kitchen_types = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(kitchen_types)

    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'اسم المطبخ مفقود'}), 400

        try:
            cursor.execute('INSERT INTO kitchen_types (name) VALUES (%s)', (name,))
            conn.commit()
            return jsonify({'message': 'تم حفظ اسم المطبخ بنجاح'})
        except mysql.connector.IntegrityError:
            return jsonify({'message': 'اسم المطبخ موجود مسبقًا'})
        finally:
            cursor.close()
            conn.close()

@app.route('/employees', methods=['GET', 'POST'])
def handle_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM employees")
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)

    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO employees (name, daily_salary) VALUES (%s, %s)",
                       (data['name'], data['daily_salary']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'تمت إضافة الموظف بنجاح'})





@app.route('/kitchen-types/<int:type_id>', methods=['PUT'])
def update_kitchen_type(type_id):
    data = request.json
    name = data.get('name')

    if not name:
        return jsonify({'error': 'الاسم مطلوب'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE kitchen_types SET name=%s WHERE id=%s', (name, type_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'تم تعديل اسم المطبخ بنجاح'})



 


@app.route('/')
def root():
    return send_from_directory('.', 'index.html')
# ✅ دالة التحقق من صحة الجلسة
def is_valid_token(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_ip FROM sessions WHERE session_token = %s", (token,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        stored_ip = result[0]
        current_ip = request.remote_addr
        print("📡 IP Check:", stored_ip, "==", current_ip)

        return stored_ip == current_ip  # ✅ يتحقق أن الـ IP نفس المسجل
    return False

@app.route('/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.json
    name = data.get('name')
    daily_salary = data.get('daily_salary')

    if not name or not daily_salary:
        return jsonify({'error': '❌ الاسم والراتب مطلوبان'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE employees SET name = %s, daily_salary = %s WHERE id = %s",
            (name, daily_salary, employee_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'تم تعديل الموظف بنجاح'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/attendance/<int:att_id>', methods=['DELETE'])
def delete_attendance(att_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE id = %s", (att_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/groups', methods=['POST'])
def add_group():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'error': 'اسم المجموعة مطلوب'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO `groups` (name) VALUES (%s)", (name,))
        conn.commit()
        group_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'message': '✅ تم حفظ المجموعة بنجاح', 'id': group_id})
    except Exception as e:
        print("🔥 خطأ أثناء إضافة المجموعة:", e)
        return jsonify({'error': str(e)}), 500
@app.route("/business-info", methods=["POST", "GET"])
def handle_business_info():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        data = request.get_json()
        cursor.execute("DELETE FROM business_info")  # مسح القديم
        cursor.execute("""
            INSERT INTO business_info (shop_name, phone, social, logo)
            VALUES (%s, %s, %s, %s)
        """, (data["shop_name"], data["phone"], data["social"], data.get("logo", "")))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "تم حفظ البيانات بنجاح"})
    
    elif request.method == "GET":
        cursor.execute("SELECT * FROM business_info LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify(row or {})

@app.route('/<path:filename>')
def serve_file(filename):
    from flask import request
    import mimetypes

    token = request.args.get('token') or request.headers.get('Authorization')

    public_files = (
        filename.endswith('.css') or
        filename.endswith('.js') or
        filename.endswith('.png') or
        filename.endswith('.jpg') or
        filename.endswith('.jpeg') or
        filename.endswith('.svg') or
        filename.endswith('.ico')
    )

    if filename == 'index.html' or public_files:
        pass
    else:
        if not token or not is_valid_token(token):
            return "🚫 الوصول مرفوض. سجّل الدخول أولاً.", 403

    file_path = os.path.join('.', filename)
    if os.path.exists(file_path):
        mimetype = mimetypes.guess_type(file_path)[0]
        return send_from_directory('.', filename, mimetype=mimetype)
    else:
        return f"❌ الملف غير موجود: {filename}", 404




if __name__ == '__main__':
    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ أضف عمود user_ip إذا غير موجود
    cursor.execute("SHOW COLUMNS FROM sessions LIKE 'user_ip'")
    if not cursor.fetchone():
       cursor.execute("ALTER TABLE sessions ADD COLUMN user_ip VARCHAR(255)")


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kitchen_types (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) UNIQUE
        )
    ''')
    

    cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    daily_salary DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        employee_id INT,
        action ENUM('in', 'out'),
        rating ENUM('ممتاز', 'جيد', 'ضعيف'),
        penalty INT DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    )
    ''')

        # تأكد من وجود الأعمدة المهمة
    cursor.execute("SHOW COLUMNS FROM attendance LIKE 'rating'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE attendance ADD COLUMN rating ENUM('ممتاز', 'جيد', 'ضعيف') DEFAULT 'ممتاز'")

    cursor.execute("SHOW COLUMNS FROM attendance LIKE 'penalty'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE attendance ADD COLUMN penalty INT DEFAULT 0")


    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        role VARCHAR(50) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

    

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        session_token VARCHAR(255),
        user_ip VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kitchens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            type VARCHAR(255),
            group_name VARCHAR(255),
            cost_price DECIMAL(10, 2) DEFAULT 0.00,  
            hall_price DECIMAL(10, 2) DEFAULT 0.00,  
            takeaway_price DECIMAL(10, 2) DEFAULT 0.00, 
            initial_quantity INT DEFAULT 0,      
            note TEXT,  
            favorite TINYINT,
            image VARCHAR(255)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `groups` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) UNIQUE
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS halls (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            hall_id INT,
            FOREIGN KEY (hall_id) REFERENCES halls(id)
        )
    ''')
    create_tables_if_not_exist()
    conn.commit()
    cursor.close()
    conn.close()
@app.route('/next-invoice-number/<int:table_id>')
def get_next_invoice_number(table_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(invoice_number) FROM orders WHERE table_id = %s", (table_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    max_invoice = result[0] or 0
    return jsonify({'next': max_invoice + 1})

from flask import send_from_directory

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/orders/<int:table_id>', methods=['GET'])
def get_order_for_timer(table_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM orders
        WHERE table_id = %s AND is_paid = 0 AND is_saved = 1
         ORDER BY created_at ASC  # <--- التغيير هنا

        LIMIT 1
    """, (table_id,))
    order = cursor.fetchone()

    if order and 'created_at' in order:
        order['created_at'] = order['created_at'].isoformat()

    cursor.close()
    conn.close()
    return jsonify({'order': order})



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=3306)

