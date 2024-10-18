# routes.py
from app import app
from models import db, WalkieTalkie, Department, Rental, get_ist_now
from datetime import datetime, timedelta
from sqlalchemy import func
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import or_
import json


@app.route('/')
def index():
    walkie_talkies = WalkieTalkie.query.all()
    total_wt = len(walkie_talkies)
    available_wt = WalkieTalkie.query.filter_by(is_lent=False).count()
    lent_wt = WalkieTalkie.query.filter_by(is_lent=True).count()
    charged_wt = WalkieTalkie.query.filter_by(is_lent=False, is_charged=True).count()
    return render_template('index.html', walkie_talkies=walkie_talkies, total_wt=total_wt,
                           available_wt=available_wt, lent_wt=lent_wt, charged_wt=charged_wt)

@app.route('/toggle_charge_status/<int:wt_id>', methods=['POST'])
def toggle_charge_status(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    wt.is_charged = not wt.is_charged
    db.session.commit()
    flash(f'Walkie-Talkie ID {wt.id} charge status updated.')
    return redirect(url_for('index'))

# routes.py

@app.route('/add_walkie_talkie', methods=['GET', 'POST'])
def add_walkie_talkie():
    if request.method == 'POST':
        id_input = request.form.get('id')
        channel_input = request.form.get('channel')
        
        # Handle ID
        if id_input:
            try:
                id_value = int(id_input)
                if WalkieTalkie.query.get(id_value):
                    error = 'A walkie-talkie with this ID already exists.'
                    return render_template('add_walkie_talkie.html', error=error)
            except ValueError:
                error = 'Invalid ID entered.'
                return render_template('add_walkie_talkie.html', error=error)
        else:
            # Auto-increment ID
            last_wt = WalkieTalkie.query.order_by(WalkieTalkie.id.desc()).first()
            id_value = last_wt.id + 1 if last_wt else 1
        
        # Handle Channel
        if channel_input:
            try:
                channel = int(channel_input)
            except ValueError:
                error = 'Invalid channel number.'
                return render_template('add_walkie_talkie.html', error=error)
        else:
            channel = 1  # Default channel
        
        # Set is_charged to False (discharged) by default
        wt = WalkieTalkie(id=id_value, channel=channel, is_charged=False)
        db.session.add(wt)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_walkie_talkie.html')


@app.route('/walkie_talkie/<int:wt_id>')
def view_walkie_talkie(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    rentals = Rental.query.filter_by(walkie_talkie_id=wt_id).all()
    return render_template('walkie_talkie.html', wt=wt, rentals=rentals)

@app.route('/lend_walkie_talkie/<int:wt_id>', methods=['GET', 'POST'])
def lend_walkie_talkie(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    departments = Department.query.all()
    if not departments:
        return render_template('lend_walkie_talkie.html', wt=wt, departments=[])
    if request.method == 'POST':
        department_id = request.form['department']
        department = Department.query.get(department_id)
        rental = Rental(walkie_talkie_id=wt_id, department_id=department_id)
        wt.is_lent = True
        wt.current_holder = department.name
        db.session.add(rental)
        db.session.commit()
        return redirect(url_for('view_walkie_talkie', wt_id=wt_id))
    return render_template('lend_walkie_talkie.html', wt=wt, departments=departments)

@app.route('/return_walkie_talkie/<int:wt_id>')
def return_walkie_talkie(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    rental = Rental.query.filter_by(walkie_talkie_id=wt_id, return_time=None).first()
    if rental:
        rental.return_time = get_ist_now()  # Set return_time in IST
        wt.is_lent = False
        wt.current_holder = None
        wt.is_charged = False  # Set to discharged upon return
        db.session.commit()
    return redirect(url_for('view_walkie_talkie', wt_id=wt_id))


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form['name'].strip()
        # Convert name to title case for consistent storage
        normalized_name = name.title()
        # Case-insensitive duplicate check
        existing_department = Department.query.filter(func.lower(Department.name) == func.lower(name)).first()
        if existing_department:
            error = 'Department/Person already exists.'
            return render_template('add_department.html', error=error)
        department = Department(name=normalized_name)
        db.session.add(department)
        db.session.commit()
        return redirect(url_for('departments'))
    return render_template('add_department.html')

@app.route('/edit_walkie_talkie/<int:wt_id>', methods=['GET', 'POST'])
def edit_walkie_talkie(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    if request.method == 'POST':
        id_input = request.form.get('id')
        channel_input = request.form.get('channel')
        
        # Handle ID change
        if id_input:
            try:
                new_id = int(id_input)
                if new_id != wt.id and WalkieTalkie.query.get(new_id):
                    error = 'A walkie-talkie with this ID already exists.'
                    return render_template('edit_walkie_talkie.html', wt=wt, error=error)
            except ValueError:
                error = 'Invalid ID entered.'
                return render_template('edit_walkie_talkie.html', wt=wt, error=error)
        else:
            error = 'ID is required.'
            return render_template('edit_walkie_talkie.html', wt=wt, error=error)
        
        # Update Rentals if ID changes
        if new_id != wt.id:
            # Update foreign keys in Rental
            rentals = Rental.query.filter_by(walkie_talkie_id=wt.id).all()
            for rental in rentals:
                rental.walkie_talkie_id = new_id
            wt.id = new_id  # Update the walkie-talkie's ID
        
        # Handle Channel
        if channel_input:
            try:
                wt.channel = int(channel_input)
            except ValueError:
                error = 'Invalid channel number.'
                return render_template('edit_walkie_talkie.html', wt=wt, error=error)
        else:
            wt.channel = 1  # Default channel

        wt.is_charged = 'is_charged' in request.form

        db.session.commit()
        return redirect(url_for('view_walkie_talkie', wt_id=wt.id))
    return render_template('edit_walkie_talkie.html', wt=wt)

@app.route('/delete_walkie_talkie/<int:wt_id>', methods=['POST'])
def delete_walkie_talkie(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    if wt.rental_history:
        flash('Cannot delete walkie-talkie with rental history.')
        return redirect(url_for('index'))
    db.session.delete(wt)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/departments')
def departments():
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/delete_department/<int:dept_id>', methods=['POST'])
def delete_department(dept_id):
    department = Department.query.get_or_404(dept_id)
    # Check if any walkie-talkies are currently lent to this department/person
    lent_walkie_talkies = Rental.query.filter_by(department_id=dept_id, return_time=None).all()
    if lent_walkie_talkies:
        flash('Cannot delete department/person with walkie-talkies currently lent to them.')
        return redirect(url_for('departments'))
    # Delete the department/person
    db.session.delete(department)
    db.session.commit()
    flash('Department/Person deleted successfully.')
    return redirect(url_for('departments'))

@app.route('/analytics', methods=['GET'])
def analytics():
    # Get the time range from the request arguments
    time_filter = request.args.get('time_filter', '7_days')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    now = get_ist_now()

    # Handle custom date range
    if time_filter == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
            if start_date >= end_date:
                flash('Start date must be before end date.')
                start_date = now - timedelta(days=7)
                end_date = now
        except ValueError:
            flash('Invalid date format.')
            start_date = now - timedelta(days=7)
            end_date = now
    else:
        # Predefined time ranges
        if time_filter == '6_hours':
            start_date = now - timedelta(hours=6)
        elif time_filter == '12_hours':
            start_date = now - timedelta(hours=12)
        elif time_filter == '24_hours':
            start_date = now - timedelta(hours=24)
        elif time_filter == '1_day':
            start_date = now - timedelta(days=1)
        elif time_filter == '2_days':
            start_date = now - timedelta(days=2)
        elif time_filter == '3_days':
            start_date = now - timedelta(days=3)
        elif time_filter == '7_days':
            start_date = now - timedelta(days=7)
        else:
            # Default to last 7 days
            start_date = now - timedelta(days=7)
        end_date = now

    # Total walkie-talkies
    total_wt = WalkieTalkie.query.count()
    # Walkie-talkies currently lent out
    lent_wt = WalkieTalkie.query.filter_by(is_lent=True).count()
    # Walkie-talkies available
    available_wt = WalkieTalkie.query.filter_by(is_lent=False).count()
    # Fully charged walkie-talkies available
    charged_wt = WalkieTalkie.query.filter_by(is_lent=False, is_charged=True).count()

    # Number of lent walkie-talkies by department/person within the time range
    lent_by_department = db.session.query(
        Department.name,
        func.count(Rental.id)
    ).join(Rental).filter(
        Rental.return_time == None,
        Rental.lend_time <= end_date,
        Rental.lend_time >= start_date
    ).group_by(Department.name).all()

    # Most frequent borrowers within the time range
    frequent_borrowers = db.session.query(
        Department.name,
        func.count(Rental.id)
    ).join(Rental).filter(
        Rental.lend_time <= end_date,
        Rental.lend_time >= start_date
    ).group_by(Department.name).order_by(func.count(Rental.id).desc()).limit(5).all()

    # Average duration of rentals within the time range
    average_rental_duration = db.session.query(
        func.avg(func.julianday(Rental.return_time) - func.julianday(Rental.lend_time))
    ).filter(
        Rental.return_time != None,
        Rental.lend_time <= end_date,
        Rental.lend_time >= start_date
    ).scalar()

    # Rentals and Returns Over the selected time range
    rental_trends = []
    utilization_data = []

    delta = end_date - start_date
    # Decide on the time granularity
    if delta <= timedelta(days=2):
        # Hourly data
        num_periods = int(delta.total_seconds() // 3600) + 1
        for i in range(num_periods):
            period_start = start_date + timedelta(hours=i)
            period_end = period_start + timedelta(hours=1)

            rentals = Rental.query.filter(
                Rental.lend_time >= period_start,
                Rental.lend_time < period_end
            ).count()

            returns = Rental.query.filter(
                Rental.return_time >= period_start,
                Rental.return_time < period_end
            ).count()

            rental_trends.append({
                'date': period_start.strftime('%Y-%m-%d %H:%M'),
                'rentals': rentals,
                'returns': returns
            })

            lent = Rental.query.filter(
                Rental.lend_time <= period_end,
                (Rental.return_time == None) | (Rental.return_time >= period_start)
            ).count()
            utilization_rate = (lent / total_wt) * 100 if total_wt else 0
            utilization_data.append({
                'date': period_start.strftime('%Y-%m-%d %H:%M'),
                'utilization_rate': utilization_rate
            })
    else:
        # Daily data
        num_periods = delta.days + 1
        for i in range(num_periods):
            day = start_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            rentals = Rental.query.filter(
                Rental.lend_time >= day,
                Rental.lend_time < next_day
            ).count()

            returns = Rental.query.filter(
                Rental.return_time >= day,
                Rental.return_time < next_day
            ).count()

            rental_trends.append({
                'date': day.strftime('%Y-%m-%d'),
                'rentals': rentals,
                'returns': returns
            })

            lent = Rental.query.filter(
                Rental.lend_time <= next_day,
                (Rental.return_time == None) | (Rental.return_time >= day)
            ).count()
            utilization_rate = (lent / total_wt) * 100 if total_wt else 0
            utilization_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'utilization_rate': utilization_rate
            })

    # Most frequently used walkie-talkies within the time range
    frequent_walkie_talkies = db.session.query(
        WalkieTalkie.id,
        func.count(Rental.id)
    ).join(Rental).filter(
        Rental.lend_time >= start_date,
        Rental.lend_time <= end_date
    ).group_by(WalkieTalkie.id).order_by(func.count(Rental.id).desc()).limit(5).all()

    return render_template('analytics.html',
                           total_wt=total_wt,
                           lent_wt=lent_wt,
                           available_wt=available_wt,
                           charged_wt=charged_wt,
                           lent_by_department=lent_by_department,
                           frequent_borrowers=frequent_borrowers,
                           average_rental_duration=average_rental_duration,
                           rental_trends=rental_trends,
                           utilization_data=utilization_data,
                           frequent_walkie_talkies=frequent_walkie_talkies,
                           time_filter=time_filter,
                           start_date=start_date,
                           end_date=end_date)

# routes.py

@app.route('/walkie_talkie/<int:wt_id>/delete_rental_history', methods=['POST'])
def delete_rental_history(wt_id):
    wt = WalkieTalkie.query.get_or_404(wt_id)
    rental_history = Rental.query.filter_by(walkie_talkie_id=wt_id).all()
    
    if not rental_history:
        flash('No rental history found for this walkie-talkie.', 'info')
        return redirect(url_for('view_walkie_talkie', wt_id=wt_id))
    
    try:
        for rental in rental_history:
            db.session.delete(rental)
        db.session.commit()
        flash('Rental history deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting rental history: {str(e)}', 'danger')
    
    return redirect(url_for('view_walkie_talkie', wt_id=wt_id))


@app.route('/walkie_talkies', methods=['GET'])
def list_walkie_talkies():
    """
    Renders the walkie-talkies listing page.
    Initially loads all walkie-talkies; subsequent filtering is handled via AJAX.
    """
    return render_template('list_walkie_talkies.html')



@app.route('/api/walkie_talkies', methods=['GET'])
def api_walkie_talkies():
    """
    API endpoint to fetch walkie-talkie data based on search and filter parameters.
    Returns JSON data.
    """
    # Retrieve query parameters
    search_query = request.args.get('search', '').strip()
    filter_status = request.args.get('status', 'all').lower()
    filter_channel = request.args.get('channel', '').strip()

    # Start building the query
    walkie_talkies_query = WalkieTalkie.query

    # Apply search filter (e.g., by ID)
    if search_query:
        if search_query.isdigit():
            walkie_talkies_query = walkie_talkies_query.filter(WalkieTalkie.id == int(search_query))
        else:
            return jsonify({'error': 'Please enter a valid numeric ID for searching.'}), 400

    # Apply status filter
    if filter_status in ['lent', 'available', 'charged', 'available_and_charged']:
        if filter_status == 'lent':
            walkie_talkies_query = walkie_talkies_query.filter_by(is_lent=True)
        elif filter_status == 'available':
            walkie_talkies_query = walkie_talkies_query.filter_by(is_lent=False)
        elif filter_status == 'charged':
            walkie_talkies_query = walkie_talkies_query.filter_by(is_charged=True)
        elif filter_status == 'available_and_charged':
            walkie_talkies_query = walkie_talkies_query.filter_by(is_lent=False, is_charged=True)
    elif filter_status != 'all':
        return jsonify({'error': 'Invalid status selected.'}), 400

    # Apply channel filter
    if filter_channel:
        if filter_channel.isdigit() and int(filter_channel) > 0:
            walkie_talkies_query = walkie_talkies_query.filter_by(channel=int(filter_channel))
        else:
            return jsonify({'error': 'Please enter a valid positive integer for channel number.'}), 400

    # Execute the query
    walkie_talkies = walkie_talkies_query.all()

    # Serialize data
    walkie_talkies_data = []
    for wt in walkie_talkies:
        walkie_talkies_data.append({
            'id': wt.id,
            'channel': wt.channel,
            'is_lent': wt.is_lent,
            'is_charged': wt.is_charged,
            'current_holder': wt.current_holder if wt.current_holder else 'N/A'
        })

    return jsonify({'walkie_talkies': walkie_talkies_data}), 200