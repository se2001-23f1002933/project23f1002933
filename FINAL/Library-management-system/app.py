from flask import Flask,render_template,request,redirect,flash,url_for,jsonify
from flask_migrate import Migrate
from models import db,Book,student,rent,fee
from datetime import datetime,timedelta
import requests 
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

import random


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///library.db'
app.config['SECRET_KEY']='af9d4e10d142994285d0c1f861a70925'
db.init_app(app)
migrate=Migrate(app,db)

@app.route('/')
def index():
    borrowed_books = db.session.query(rent).filter(rent.status == "Approved").count()
    total_books = Book.query.count()
    total_members = student.query.count()
    total_rent_current_month = round(db.session.query(func.sum(fee.rent_fee)).scalar() or 0, 2)
    recent_transactions  =  db.session.query(rent,Book).join(Book).order_by(rent.date.desc()).limit(5).all()

    return render_template('index.html', borrowed_books=borrowed_books, total_books=total_books,total_members=total_members,recent_transactions=recent_transactions,total_rent_current_month=total_rent_current_month)

def calculate_total_rent_current_month():
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    start_date = datetime.datetime(current_year, current_month, 1)
    end_date = datetime.datetime(current_year, current_month + 1, 1) - datetime.timedelta(days=1)

    total_rent = db.session.query(db.func.sum(rent.rent_fee)).filter(rent.issue_date >= start_date,rent.issue_date <= end_date).scalar()

    return total_rent if total_rent else 0

@app.route('/add_book',methods=['GET','POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        page = request.form.get('page')
        copies = request.form.get('stock')
        new_book = Book(title=title, author=author, isbn=isbn, publisher=publisher, page=page,copies=copies,rented=0)
        db.session.add(new_book)
        db.session.flush()
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_book.html')


@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        id = request.form.get('id')
        password = request.form.get('password')

        try:
            new_member = student(name=name, id=id, password=password)
            db.session.add(new_member)
            db.session.commit()
            flash('Member added successfully!', 'success')
            return redirect(url_for('add_member'))
        except IntegrityError as e:
            db.session.rollback()
            flash('Error adding member. ID may already exist.', 'danger')
            app.logger.error(f"Error adding member: {str(e)}")
    return render_template('add_member.html')


@app.route('/view_books', methods=['GET', 'POST'])
def book_list():
    if request.method == 'POST':
        if 'searcht'and 'searcha' in request.form:
            title = request.form.get('searcht')
            author=request.form.get('searcha')
            books = db.session.query(Book).filter((Book.title.like(f'%{title}%')),(Book.author.like(f'%{author}%'))).all()
        elif 'searcht' in request.form:
             title=request.form.get('searcht')
             books = db.session.query(Book).filter(Book.title.like(f'%{title}%')).all()
        elif 'searcha' in request.form:
             author=request.form.get('searcha')
             books = db.session.query(Book).filter(Book.author.like(f'%{author}%')).all()
    else:
        books= db.session.query(Book).all()

    return render_template('view_books.html', books=books)

@app.route('/view_members', methods=['GET','POST'])
def member_list():
    if request.method == 'POST':
        search = request.form.get('search')
        member = db.session.query(student).filter(student.name.like(f'%{search}%')).all()
        return render_template('view_members.html', member=member)

    else:
        member=db.session.query(student).all()
        print([ i.name for i in member])
        return render_template('view_members.html', member=member)

@app.route('/edit_book/<int:id1>',methods=['GET','POST'])
def edit_book(id1):
    print(id1)
    book=Book.query.get(id1)
   
    try:
        if request.method == 'POST':
            rented=book.rented
            to_be_updated=int(request.form.get('stock'))-rented
            if to_be_updated<0:
                flash("Quantity decrease failed!books are on rent",'error')
            else:
                book.title = request.form.get('title')
                book.author = request.form.get('author')
                book.isbn = request.form.get('isbn')
                book.publisher = request.form.get('publisher')
                book.page = request.form.get('page')
                book.copies=request.form.get('stock')
                db.session.commit()
                flash("Updated Sucessfully",'success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error ocuured \n{e}",'error')
    return render_template('edit_book.html',book=book)

@app.route('/edit_member/<int:id>',methods=['GET','POST'])
def edit_member(id):
    member=student.query.get(id)
    try:
        if request.method=="POST":
            member.name=request.form['name']
            member.password=request.form['password']
            db.session.commit()
            flash("Updated Sucessfully","success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error ocuured \n{e}",'error') 
    return render_template('edit_member.html',member=student)

@app.route('/delete_member/<int:id>',methods=['GET','POST'])
def delete_member(id):
    try:
        member=student.query.get(id)
        db.session.delete(member)
        db.session.commit()
        flash("Member removed successfully","success")
    except Exception as e:
        flash(f"An error ocuured \n{e}",'error')
    return redirect('/view_members')

@app.route('/delete_book/<int:id>',methods=['GET','POST'])
def delete_book(id):
    try:
        book=Book.query.get(id)
        stock=Book.query.get(book.id)
        db.session.delete(book)
        db.session.delete(stock)
        db.session.commit()
        flash("Book removed successfully","success")
    except Exception as e:
        flash(f"An error ocuured \n{e}",'error')
    return redirect('/view_members')

@app.route('/view_book/<int:id>')
def view_book(id):
    book = Book.query.get(id)
    transactions = rent.query.filter_by(book_id=id).all()
    return render_template('view_book.html', book=book, trans=transactions)


@app.route('/view_member/<int:id>')
def view_member(id):
    member=Member.query.get(id)
    transaction=Transaction.query.filter_by(member_id=member.id).all()
    dbt=calculate_dbt(member)
    return render_template('view_member.html',member=member,trans=transaction,debt=dbt)


def calculate_dbt(member):
    dbt = 0
    charge = db.session.query(Charges).first()
    transactions = db.session.query(Transaction).filter_by(member_id=member.id, return_date=None).all()

    for transaction in transactions:
        days_difference = (datetime.date.today() - transaction.issue_date.date()).days
        if days_difference > 0: 
            dbt += days_difference * charge.rentfee
    return dbt




@app.route('/issuebook', methods=['GET', 'POST'])
def issue_book():
    if request.method == "POST":
        stuname = request.form.get('name')
        book_id = request.form.get('book_id')

        # Retrieve the book based on the book_id
        book = db.session.query(Book).filter(Book.id == book_id).first()

        # Retrieve the student based on the stu_id
        student_obj = db.session.query(student).filter(student.name).first()

        if book and student_obj:
            # Create a new rent entry
            rent_date = dt.now()  # Use the 'dt' alias for the datetime class
            new_rent = rent(book_id=book, borrowed_quantity=1, stuname=student_obj, date=rent_date, status='Pending')
            db.session.add(new_rent)
            db.session.commit()

            flash('Book issued successfully!', 'success')
        else:
            flash('Book or student not found. Please check the details and try again.', 'danger')

    return render_template('issuebook.html')





@app.route('/issuebookconfirm', methods=['GET', 'POST'])
def issue_book_confirm():
    if request.method == "POST":
        memberid = request.form['memberid']
        bookid = request.form['bookid']

        stock = db.session.query(Stock).filter_by(book_id=bookid).first()
        if stock.available_quantity <= 0:
            flash("Book is not available for issuance.", "error")
            return redirect('/issuebook')

        new_transaction = Transaction(book_id=bookid, member_id=memberid, issue_date=datetime.date.today())
        print(new_transaction)

        stock.available_quantity -= 1
        stock.borrowed_quantity += 1
        stock.total_borrowed += 1

        db.session.add(new_transaction)
        db.session.commit()

        flash("Transaction added successfully", "success")
        return redirect('/issuebook')

    return render_template('issuebook.html')


@app.route('/transactions', methods=['GET', 'POST'])
def view_borrowings():
    # Query the necessary columns from rent and aggregated fee tables
    subquery = db.session.query(
        fee.stu_id.label('stu_id'),
        fee.book_id.label('book_id'),
        func.max(fee.issue_date).label('max_issue_date'),
        func.max(fee.return_date).label('max_return_date'),
        func.sum(fee.rent_fee).label('total_rent_fee')
    ).group_by(fee.stu_id, fee.book_id).subquery()

    transactions = db.session.query(
        rent.rid.label('Transaction Id'),
        Book.title.label('Book Title'),
        student.name.label('Student Name'),
        rent.date.label('Issue Date'),
        subquery.c.max_return_date.label('Return Date'),
        subquery.c.total_rent_fee.label('Rent Fee'),
    ).join(student, rent.stu_id == student.id).join(Book, rent.book_id == Book.id).outerjoin(subquery, (subquery.c.stu_id == rent.stu_id) & (subquery.c.book_id == rent.book_id)).all()

    if request.method == "POST":
        search = request.form['search']
        
        transactions_by_name = db.session.query(
            rent.rid.label('Transaction Id'),
            Book.title.label('Book Title'),
            student.name.label('Student Name'),
            rent.date.label('Issue Date'),
            subquery.c.max_return_date.label('Return Date'),
            subquery.c.total_rent_fee.label('Rent Fee'),
        ).join(student, rent.stu_id == student.id).join(Book, rent.book_id == Book.id).outerjoin(subquery, (subquery.c.stu_id == rent.stu_id) & (subquery.c.book_id == rent.book_id)).filter(student.name.ilike(f'%{search}%')).all()
        
        transaction_by_id = db.session.query(
            rent.rid.label('Transaction Id'),
            Book.title.label('Book Title'),
            student.name.label('Student Name'),
            rent.date.label('Issue Date'),
            subquery.c.max_return_date.label('Return Date'),
            subquery.c.total_rent_fee.label('Rent Fee'),
        ).join(student, rent.stu_id == student.id).join(Book, rent.book_id == Book.id).outerjoin(subquery, (subquery.c.stu_id == rent.stu_id) & (subquery.c.book_id == rent.book_id)).filter(rent.rid == search).all()
        
        if transactions_by_name:
            transactions = transactions_by_name
        elif transaction_by_id:
            transactions = transaction_by_id
        else:
            transactions = []

    return render_template('transactions.html', fees=transactions)


@app.route('/returnbookconfirm', methods=['POST'])
def return_book_confirm():
    if request.method == "POST":
        id = request.form["id"]
        trans, member = db.session.query(Transaction, Member).join(Member).filter(Transaction.id == id).first()
        stock = Stock.query.filter_by(book_id=trans.book_id).first()
        charge=Charges.query.first()
        rent=(datetime.date.today() - trans.issue_date.date() ).days * charge.rentfee
        if stock:
            stock.available_quantity += 1
            stock.borrowed_quantity -= 1

            trans.return_date = datetime.date.today()
            trans.rent_fee =rent
            db.session.commit()
            flash(f"{member.name} Returned book successfully", 'success')
        else:
            flash("Error updating stock information", 'error')

    return redirect('transactions')

def calculate_rent(transaction):
    charge=Charges.query.first()
    rent=(datetime.date.today() - transaction.Transaction.issue_date.date() ).days * charge.rentfee
    return rent

API_BASE_URL = "https://frappe.io/api/method/frappe-library"


@app.route('/import_book', methods=['GET', 'POST'])
def imp():
    if request.method == 'POST':
        title = request.form.get('title', default='', type=str)
        num_books = request.form.get('num_books', default=20, type=int)
        num_pages = (num_books + 19) // 20
        all_books = []
        for page in range(1, num_pages + 1):
            url = f"{API_BASE_URL}?page={page}&title={title}"
            response = requests.get(url)
            data = response.json()
            all_books.extend(data.get('message', []))  
        return render_template('imp.html', data=all_books[:num_books], title=title, num_books=num_books)


    return render_template('imp.html', data=[], title='', num_books=20)

@app.route('/save_all_books', methods=['POST'])
def save_all_books():
    data = request.json

    for book_data in data:
        book_id = book_data['id']
        existing_book = Book.query.get(book_id)

        if existing_book is None:
            book = Book(
                id=book_id,
                title=book_data['title'],
                author=book_data['authors'],
                isbn=book_data['isbn'],
                publisher=book_data['publisher'],
                page=book_data['numPages']
            )
            st = book_data['stock']

            try:
                db.session.add(book)
                stock = Stock(book_id=book_id, total_quantity=st, available_quantity=st)
                db.session.add(stock)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()  
                print(f"Error adding book with ID {book_id}: {str(e)}")
        else:
            print(f"Book with ID {book_id} already exists, skipping.")

    flash("Books added successfully", "success")
    return redirect('/import_book')

@app.route('/stockupdate/<int:id>',methods=['GET','POST'])
def stock_update(id):
    stock,book=db.session.query(Stock,Book).join(Book).filter(Stock.book_id == id).first()
    if request.method=="POST":
        qty=int(request.form['qty'])
        if qty > stock.total_quantity:
            stock.available_quantity+=qty
            stock.total_quantity+=qty
        else:
            stock.available_quantity-=qty
            stock.total_quantity-=qty
        db.session.commit()
        flash("Stock Updated" , "success")
    return render_template('stockupdate.html',stock=stock,book=book)
app.run(debug=True,use_reloader=True)




@app.route('/userlogin')
def login():
    return render_template('userlogin.html')


@app.route('/logout', methods=['POST'])
def logout():
    # Add any necessary logout logic here, such as clearing session data
    flash('You have been successfully logged out', 'success')
    return jsonify({'redirect': url_for('login')})


@app.route('/dashboard', methods=['POST'])
def dashboard():
    username = request.form['username']
    password = request.form['password']

    if username == '1234' and password == '1234':
        return redirect('http://127.0.0.1:5000/')  # Redirect to the specified URL

    # Rest of your existing code for normal login
    try:
        user = student.query.filter_by(id=username, password=password).one()
    except:
        user = None

    if user:
        # Fetch user's name
        user_name = user.name

        # Fetch all books from the 'Book' model
        books = Book.query.all()

        # Pass 'user_id' to the template as a string
        return render_template('dashboard.html', username=user_name, books=books, user_id=str(username))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('dashboard'))
    
    
@app.route('/request', methods=['POST'])
def request_book():
    user_id = request.form.get('user_id')
    book_id = request.form.get('book_id')

    # Generate a random RID (4 digits)
    rid = str(random.randint(1000, 9999))

    # Fetch book and student information
    book = Book.query.get(book_id)
    student_info = student.query.get(user_id)

    # Add entry to Rent table
    new_rent = rent(rid=rid, book_id=book_id, borrowed_quantity=1, stu_id=user_id,
                    date=datetime.utcnow(), status='Pending')

    try:
        db.session.add(new_rent)
        db.session.commit()
        flash('Book request submitted successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error submitting request. Please try again.', 'error')

    return redirect(url_for('dashboard'))

@app.route('/approve_requests')
def approve_requests():
    # Fetch rent objects from the database using SQLAlchemy
    rent_objects = db.session.query(rent, student, Book).\
        join(student).join(Book).order_by(desc(rent.date)).all()

    return render_template('approve_requests.html', rent_objects=rent_objects)


@app.route('/rents_page')
def rents_page():
    # Assuming rents is a list of rent objects fetched from the database
    rents = rent.query.all()  # You may need to adjust this query based on your actual data
    return render_template('rents_page.html', rents=rents)


@app.route('/approve_request/<int:rid>', methods=['GET', 'POST'])
def approve_request(rid):
    if request.method == 'POST':
        # Fetch the rent object by RID
        rent_object = rent.query.get(rid)

        if rent_object:
            # Check if the book is available
            if rent_object.status == 'Pending':
                # Fetch the corresponding book
                book = Book.query.get(rent_object.book_id)

                # Check if there are available copies to approve the request
                if book.copies - book.rented > 0:
                    # Update the status to 'Approved'
                    rent_object.status = 'Approved'

                    # Update the book's rented and copies columns
                    book.rented += 1
                    

                    try:
                        db.session.commit()
                        flash('Request approved successfully!', 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash('Error approving request. Please try again.', 'error')
                else:
                    flash('No available copies to approve the request.', 'warning')
            else:
                flash('This request has already been approved.', 'warning')
        else:
            flash('Request not found.', 'error')

        return redirect(url_for('approve_requests'))
    else:
        # Handle GET request (if needed)
        return render_template('approve_request.html', rid=rid)
    

@app.route('/returnbook')
def return_book():
    # Fetch data from the 'rent' table
    data = rent.query.order_by(desc(rent.date)).all()

    return render_template('returnbook.html', data=data)

@app.route('/process_return', methods=['POST'])
def process_return():
    rent_id = request.form.get('rent_id')
    rent_record = rent.query.get(rent_id)

    if rent_record:
        # Update the status to "Returned"
        rent_record.status = 'Returned'

        # Fetch the corresponding book
        book = Book.query.get(rent_record.book_id)

        # Increase the "copies" column for the returned book
        book.copies += 1

        try:
            db.session.commit()

            # Assuming rent_record.date is already a datetime object
            issue_date = rent_record.date

            # Create a new entry in the fee table
            fee_entry = fee(
                stu_id=rent_record.stu_id,
                book_id=rent_record.book_id,
                issue_date=issue_date,
                return_date=datetime.now(),  # Current date and time
                rent_fee=calculate_rent_fee(issue_date)  # Calculate rent fee
            )
            db.session.add(fee_entry)
            db.session.commit()

            flash('Book returned successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Error processing return. Please try again.', 'error')

    return redirect(url_for('return_book'))

def calculate_rent_fee(issue_date):
    # Assuming issue_date is a datetime object
    return_date = datetime.now()
    time_difference = return_date - issue_date
    hours_difference = time_difference.total_seconds() / 3600  # Convert seconds to hours

    # Assuming rent_fee is 2 rupees per hour
    return max(0, hours_difference) * 2.0  # Minimum rent_fee is 0


def calculate_total_rent_current_month():
    # Get the current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Calculate the sum of rent_fee for the current month
    total_rent_current_month = db.session.query(func.sum(fee.rent_fee)).\
        filter(func.strftime("%m", fee.return_date) == str(current_month)).\
        filter(func.strftime("%Y", fee.return_date) == str(current_year)).scalar()

    # If there are no entries for the current month, set total_rent_current_month to 0
    total_rent_current_month = total_rent_current_month or 0

    return total_rent_current_month

if __name__ == '__main__':
    app.run(debug=True)