from flask import Flask, render_template, request, redirect, session, flash, url_for, Response
import mysql.connector

app = Flask(__name__)
app.secret_key = 'secret_test_key'

# MySQL connection setup
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='CPSC408!',
    database='RateMyCoach'

)
cursor = conn.cursor(dictionary=True)

# home
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
    featured_coaches = cursor.fetchall() # returns ten highest rated coachs, having 3 or more reviews

    return render_template('index.html', featured_coaches=featured_coaches)

# Coaches, allows for searching, by default just shows all coaches listed by ID
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
            WHERE MATCH(c.name, c.team) AGAINST (%s IN NATURAL LANGUAGE MODE)
        """, (search_query,))
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


# Site route for a specific coach, queries all information about the coach and reviews
@app.route('/coach/<int:coach_id>')
def coach_detail(coach_id):
    cursor.execute("SELECT * FROM Coach WHERE coach_ID = %s", (coach_id,))
    coach = cursor.fetchone()

    cursor.execute("SELECT AVG(rating) AS avg_rating FROM Review WHERE coach_ID = %s AND is_deleted = FALSE", (coach_id,))
    avg_rating = cursor.fetchone()['avg_rating']

    cursor.execute("""
        SELECT r.r_ID, r.coach_ID, r.u_ID, r.rating, r.comment, r.date, u.username, r.is_deleted
        FROM Review r
        JOIN User u ON r.u_ID = u.u_ID
        WHERE r.coach_ID = %s
        AND r.is_deleted = FALSE
        AND u.is_deleted = FALSE
        ORDER BY r.date DESC
    """, (coach_id,))
    reviews = cursor.fetchall()

    return render_template("coach.html", coach=coach, avg_rating=avg_rating, reviews=reviews)

# inserts review into db
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
        VALUES (%s, %s, %s, %s, NOW())
    """, (u_ID, coach_id, rating, comment))
    conn.commit()

    return redirect(f'/coach/{coach_id}')

# checks validity of login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM User WHERE username = %s AND passw = %s AND is_deleted = FALSE", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['u_ID']
            session['username'] = user['username']
            return redirect('/')
        else:
            flash('Invalid username or password')
            return redirect('/login')
    
    return render_template('login.html')


# creates new account
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        try:
            cursor.execute("INSERT INTO User (username, email, passw, creation_date) VALUES (%s, %s, %s, NOW())",
                (username, email, password))
        except:
            return redirect('/login')
        conn.commit()

        
        return redirect('/login')
    
    return render_template('signup.html')


#clears session, logs out
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))

# remove review (soft delete)
@app.route('/delete_review/<int:r_ID>', methods=['POST'])
def delete_review(r_ID):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    # Only allow user to delete their own review
    cursor.execute("SELECT u_ID FROM Review WHERE r_ID = %s", (r_ID,))
    result = cursor.fetchone()

    if result and result['u_ID'] == user_id:
        cursor.execute("UPDATE Review SET is_deleted = TRUE WHERE r_ID = %s", (r_ID,))
        conn.commit()

    return redirect(request.referrer or '/')


@app.route('/edit_review/<int:r_ID>', methods=['GET'])
def edit_review(r_ID):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    cursor.execute("SELECT * FROM Review WHERE r_ID = %s AND is_deleted = FALSE", (r_ID,))
    review = cursor.fetchone()

    if not review or review['u_ID'] != user_id:
        return redirect('/')

    return render_template('edit_review.html', review=review)

# allows user to update review. Trigger activated upon update, recalculating coach's average
@app.route('/edit_review/<int:r_ID>', methods=['POST'])
def update_review(r_ID):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    rating = request.form.get('rating')
    comment = request.form.get('comment')

    cursor.execute("SELECT u_ID FROM Review WHERE r_ID = %s", (r_ID,))
    result = cursor.fetchone()

    if result and result['u_ID'] == user_id:
        cursor.execute("""
            UPDATE Review
            SET rating = %s, comment = %s, date = NOW()
            WHERE r_ID = %s
        """, (rating, comment, r_ID))
        conn.commit()

    return redirect(f"/coach/{request.form.get('coach_id')}")

#export reviews to CSV
@app.route('/export_reviews/<int:coach_id>')
def export_reviews(coach_id):
    cursor.execute("SELECT name FROM Coach WHERE coach_ID = %s", (coach_id,))
    coach = cursor.fetchone()
    coach_name = coach['name'].replace(" ", "_")

    # Fetch reviews
    cursor.execute("""
        SELECT u.username, r.rating, r.comment, r.date
        FROM Review r
        JOIN User u ON r.u_ID = u.u_ID
        WHERE r.coach_ID = %s
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

# Soft deletes user's account. Unable to log back in, but adminstrator could reinstate acount if necessary
@app.route('/delete_account', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    try:
        cursor.execute("UPDATE User SET is_deleted = TRUE WHERE u_ID = %s", (user_id,))
        cursor.execute("UPDATE Review SET is_deleted = TRUE WHERE u_ID = %s", (user_id,))
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
