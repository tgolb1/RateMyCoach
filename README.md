Title: Rate My Coach Database
Assignment: SQL Final Project
Name: Tommy Golbranson

## Description
RateMyCoach is a full-stack web application allowing users to read and write reviews of D3 Baseball Coaches nationwide.
In the future, this project will be expanded for all of college baseball coaches, then other sports/other levels.


## IMPORTANT NOTES
- Currently only has a couple fake test coaches and most division 3 assistant baseball coaches, pulled from a website for free (cited)
- Creating duplicate users can break login process
- I had to completely remake the database today, because a huge chunk of it was lost/damaged


## Software Requirements:
- Python 3
- Flask
- MySQL
- HTML, CSS
- Jinja2 (templating)


## Execution instructions:
- Navigate to RateMyCoach directory 
- install flask, python3 if necessary
- command line input:
    python3 app.py
- visit the link (Should be http://127.0.0.1:5000)
- Works best on Chrome, also tested and functional on Safari. Unsure about other web browsers


## Navigating the website
- Create an account by clicking "Sign Up" at the top of the page
- You will be redirected to login with that information you just provided
- Straightforward Navigation from there, but here is some more info:
    - From there, see Featured coaches, or select "Coaches" to view them all
    - Search functions available for coach name and team name
    - To publish a review, select stars and write a comment
    - To edit or delete a review, select button next to your review
    - To delete your account, select "Delete My Account" at the top of the page
        - This will delete all of your reviews and account information
        - You will need to create a new account to write more reviews



## Requirements:
1. Print/display records from your database/tables.
    - Coaches, reviews seen on webpage
2. Query for data/results with various parameters/filters
    - Search bar allows for searching by coach name or school name
3. Create a new record
    - Account creation and writing reviews supported
4. Delete records (soft delete function would be ideal)
    - Account deletion, review deletion supported (Both implemented as soft deletes)
5. Update records
    - Editing Reviews
6. Make use of transactions (commit & rollback)
    - As seen in app.py, deleting account is either completed or rolled back
7. Generate reports that can be exported (excel or csv format)
    - Download all reviews of a coach in csv format supported
8. One query must perform an aggregation/group-by clause
    - Average rating per coach is calculated using AVG(rating) with GROUP BY coach_ID in both routes and a database view.
9. One query must contain a subquery.
    - used in getting the coaches most recent review on their card
10. Two queries must involve joins across at least 3 tables
    - Coach --> Conference --> Division: used in the CoachWithDivision view
11. Enforce referential integrality (PK/FK Constraints)
    - Seen with PKs and FKs in the database structure (e.g. con_ID)
12. Include Database Views, Indexes
    - View for viewing coaches with their conference and division
    - FULLTEXT implemented as an index
13. Use at least 5 entities
    - Division, Conference, Coach, User, Review, ReviewLog, and more


## Future Work
- Expand to D1/D2/NAIA/Juco and other sports (e.g. football, basketball)
- Add admin dashboard for review moderation and user management
- Add star display component (rating visualization) using JavaScript
- Implement hashed passwords and email verification
- Allow image uploads for coaches or schools
- Display review timestamps and reviewer history


## Sources/References/Links:
- Credit to my friend and teammate Brady Altman for the idea
- https://fonts.google.com/specimen/Space+Grotesk
- https://www.datacamp.com/doc/mysql/mysql-fulltext
- https://hevodata.com/learn/flask-mysql/
- https://flask-mysql.readthedocs.io/en/stable/
- https://www.recruitref.com/sports/baseball
