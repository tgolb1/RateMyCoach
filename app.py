from flask import Flask, render_template, request, redirect, session, flash, url_for, Response
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret_test_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db", "database.db")

conn = sqlite3.connect(db_path, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

@app.route('/')
def home():
    cursor.execute("""
        SELECT c.coach_ID, c.name, c.team, c.avg_rating, COUNT(r.r_ID) AS review_count
        FROM Coach c
        JOIN Review r ON c.coach_ID = r.coach_ID
        GROUP BY c.coach_ID
        HAVING COUNT(r.r_ID) >= 3
        ORDER BY avg_rating DESC
        LIMIT 10
    """)
    featured_coaches = cursor.fetchall()
    return render_template('index.html', featured_coaches=featured_coaches)

@app.route('/coaches')
def coaches():
    search_query = request.args.get('search', '')

    if search_query:
        cursor.execute("""
            SELECT c.coach_ID, c.name, c.team, c.avg_rating,
              (
                SELECT r.comment
                FROM Review r
                JOIN User u ON r.u_ID = u.u_ID
                WHERE r.coach_ID = c.coach_ID
                  AND r.is_deleted = FALSE
                  AND u.is_deleted = FALSE
                ORDER BY r.date DESC
                LIMIT 1
              ) AS review_text
            FROM Coach c
            WHERE c.name LIKE ? OR c.team LIKE ?
        """, (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("""
            SELECT c.coach_ID, c.name, c.team, c.avg_rating,
              (
                SELECT r.comment
                FROM Review r
                JOIN User u ON r.u_ID = u.u_ID
                WHERE r.coach_ID = c.coach_ID
                  AND r.is_deleted = FALSE
                  AND u.is_deleted = FALSE
                ORDER BY r.date DESC
                LIMIT 1
              ) AS review_text
            FROM Coach c
        """)
    coaches = cursor.fetchall()
    return render_template('coaches.html', coaches=coaches, search_query=search_query)

@app.route('/coach/<int:coach_id>')
def coach_detail(coach_id):
    cursor.execute("SELECT * FROM Coach WHERE coach_ID = ?", (coach_id,))
    coach = cursor.fetchone()

    cursor.execute("SELECT AVG(rating) AS avg_rating FROM Review WHERE coach_ID = ? AND is_deleted = FALSE", (coach_id,))
    avg_rating = cursor.fetchone()['avg_rating']

    cursor.execute("""
        SELECT r.r_ID, r.coach_ID, r.u_ID, r.rating, r.comment, r.date, u.username, r.is_deleted
        FROM Review r
        JOIN User u ON r.u_ID = u.u_ID
        WHERE r.coach_ID = ?
        AND r.is_deleted = FALSE
        AND u.is_deleted = FALSE
        ORDER BY r.date DESC
    """, (coach_id,))
    reviews = cursor.fetchall()
    return render_template("coach.html", coach=coach, avg_rating=avg_rating, reviews=reviews)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        flash("You must be logged in to leave a review.")
        return redirect('/login')

    coach_id = request.form['coach_id']
    rating = request.form['rating']
    comment = request.form['comment']
    u_ID = session['user_id']

    cursor.execute("""
        INSERT INTO Review (u_ID, coach_ID, rating, comment, date)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (u_ID, coach_id, rating, comment))
    conn.commit()
    return redirect(f'/coach/{coach_id}')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM User WHERE username = ? AND passw = ? AND is_deleted = FALSE", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['u_ID']
            session['username'] = user['username']
            return redirect('/')
        else:
            flash('Invalid username or password')
            return redirect('/login')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            cursor.execute("INSERT INTO User (username, email, passw, creation_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (username, email, password))
        except:
            return redirect('/login')
        conn.commit()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/delete_review/<int:r_ID>', methods=['POST'])
def delete_review(r_ID):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    cursor.execute("SELECT u_ID FROM Review WHERE r_ID = ?", (r_ID,))
    result = cursor.fetchone()

    if result and result['u_ID'] == user_id:
        cursor.execute("UPDATE Review SET is_deleted = TRUE WHERE r_ID = ?", (r_ID,))
        conn.commit()
    return redirect(request.referrer or '/')

@app.route('/edit_review/<int:r_ID>', methods=['GET'])
def edit_review(r_ID):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    cursor.execute("SELECT * FROM Review WHERE r_ID = ? AND is_deleted = FALSE", (r_ID,))
    review = cursor.fetchone()

    if not review or review['u_ID'] != user_id:
        return redirect('/')
    return render_template('edit_review.html', review=review)

@app.route('/edit_review/<int:r_ID>', methods=['POST'])
def update_review(r_ID):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    rating = request.form.get('rating')
    comment = request.form.get('comment')

    cursor.execute("SELECT u_ID FROM Review WHERE r_ID = ?", (r_ID,))
    result = cursor.fetchone()

    if result and result['u_ID'] == user_id:
        cursor.execute("""
            UPDATE Review
            SET rating = ?, comment = ?, date = CURRENT_TIMESTAMP
            WHERE r_ID = ?
        """, (rating, comment, r_ID))
        conn.commit()
    return redirect(f"/coach/{request.form.get('coach_id')}")

@app.route('/export_reviews/<int:coach_id>')
def export_reviews(coach_id):
    cursor.execute("SELECT name FROM Coach WHERE coach_ID = ?", (coach_id,))
    coach = cursor.fetchone()
    coach_name = coach['name'].replace(" ", "_")

    cursor.execute("""
        SELECT u.username, r.rating, r.comment, r.date
        FROM Review r
        JOIN User u ON r.u_ID = u.u_ID
        WHERE r.coach_ID = ?
        AND r.is_deleted = FALSE
        AND u.is_deleted = FALSE
    """, (coach_id,))
    rows = cursor.fetchall()

    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Rating', 'Comment', 'Date'])
    for row in rows:
        writer.writerow([row['username'], row['rating'], row['comment'], row['date']])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={coach_name}_reviews.csv"}
    )

@app.route('/delete_account', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    try:
        cursor.execute("UPDATE User SET is_deleted = TRUE WHERE u_ID = ?", (user_id,))
        cursor.execute("UPDATE Review SET is_deleted = TRUE WHERE u_ID = ?", (user_id,))
        conn.commit()
        session.clear()
        flash("Your account has been deactivated.")
    except Exception as e:
        conn.rollback()
        flash("Account deletion failed. Please try again.")
        print("DELETE ACCOUNT ERROR:", e)

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
