from flask import Flask, render_template, request, redirect, session
from db import db
from bson.objectid import ObjectId
import pandas as pd

app = Flask(__name__)
app.secret_key = "secret123"

# ======================
# PUBLIC ROUTES
# ======================

@app.route('/')
def home():
    return render_template('public/home.html')


@app.route('/services')
def services():
    services = list(db.services.find())
    return render_template('public/services.html', services=services)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    services = list(db.services.find())

    if request.method == 'POST':
        data = {
            "name": request.form.get('name'),
            "phone": request.form.get('phone'),
            "whatsapp": request.form.get('whatsapp'),
            "service": request.form.get('service'),
            "requirement": request.form.get('requirement'),
            "source_page": request.form.get('source_page'),
            "status": "New"
        }

        db.leads.insert_one(data)

        your_number = "918919492376"
        message = f"Hi, I am {data['name']}. I need help with {data['service']}. Requirement: {data['requirement']}"

        return render_template(
            'public/success.html',
            message=message,
            your_number=your_number
        )

    return render_template(
        'public/contact.html',
        services=services,
        source_page="Contact Page"
    )


# ======================
# LOGIN SYSTEM
# ======================

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == "admin" and request.form['password'] == "1234":
            session['user'] = "admin"
            return redirect('/admin')
        else:
            return "Invalid Credentials"

    return render_template('admin/login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/admin/login')


# ======================
# ADMIN DASHBOARD
# ======================

@app.route('/admin')
def admin_dashboard():
    if 'user' not in session:
        return redirect('/admin/login')

    return render_template(
        'admin/dashboard.html',
        clients=db.clients.count_documents({}),
        services=db.services.count_documents({}),
        leads=db.leads.count_documents({}),
        job_clients=db.job_clients.count_documents({}),
        placed=db.job_clients.count_documents({"status": "Placed"}),
        new_jobs=db.job_clients.count_documents({"status": "New"})
    )


# ======================
# ADMIN SERVICES
# ======================

@app.route('/admin/services')
def admin_services():
    if 'user' not in session:
        return redirect('/admin/login')

    services = list(db.services.find())
    return render_template('admin/services.html', services=services)


@app.route('/admin/add_service', methods=['POST'])
def add_service():
    name = request.form['service_name']
    if not db.services.find_one({"service_name": name}):
        db.services.insert_one({"service_name": name})
    return redirect('/admin/services')


@app.route('/admin/delete_service/<id>')
def delete_service(id):
    db.services.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/services')


# ======================
# ADMIN LEADS
# ======================

@app.route('/admin/leads')
def admin_leads():
    if 'user' not in session:
        return redirect('/admin/login')

    leads = list(db.leads.find().sort("_id", -1))
    return render_template('admin/leads.html', leads=leads)


# ======================
# ADMIN CLIENTS
# ======================

@app.route('/admin/clients')
def clients():
    if 'user' not in session:
        return redirect('/admin/login')

    clients = list(db.clients.find())
    services = list(db.services.find())

    service_map = {str(s['_id']): s['service_name'] for s in services}

    for c in clients:
        sid = c.get('service_id')
        c['service_name'] = service_map.get(str(sid), "N/A")

    return render_template('admin/clients.html', clients=clients, services=services)


@app.route('/admin/client_form', methods=['GET', 'POST'])
@app.route('/admin/client_form/<id>', methods=['GET', 'POST'])
def client_form(id=None):
    if 'user' not in session:
        return redirect('/admin/login')

    client = db.clients.find_one({"_id": ObjectId(id)}) if id else None

    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "phone": request.form['phone'],
            "service_id": request.form['service_id'],
            "requirement": request.form['requirement']
        }

        if client:
            db.clients.update_one({"_id": ObjectId(id)}, {"$set": data})
        else:
            data["status"] = "Pending"
            db.clients.insert_one(data)

        return redirect('/admin/clients')

    return render_template(
        'admin/client_form.html',
        client=client,
        services=list(db.services.find())
    )


@app.route('/admin/delete_client/<id>')
def delete_client(id):
    db.clients.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/clients')


@app.route('/admin/update_status/<id>')
def update_status(id):
    client = db.clients.find_one({"_id": ObjectId(id)})
    new_status = "Completed" if client.get("status") == "Pending" else "Pending"

    db.clients.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": new_status}}
    )
    return redirect('/admin/clients')


# ======================
# ADMIN JOB CLIENTS
# ======================
@app.route('/admin/job_clients')
def job_clients():
    if 'user' not in session:
        return redirect('/admin/login')

    search = request.args.get('search')

    if search:
        data = list(db.job_clients.find({
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
                {"skills": {"$regex": search, "$options": "i"}},
                {"qualification": {"$regex": search, "$options": "i"}},
                {"experience": {"$regex": search, "$options": "i"}}
            ]
        }))
    else:
        data = list(db.job_clients.find())

    return render_template('admin/job_clients.html', job_clients=data)
@app.route('/test')
def test():
    return "Working"
@app.route('/admin/shortlist/<id>')
def shortlist(id):
    db.job_clients.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"shortlisted": True}}
    )
    return redirect('/admin/job_clients')
@app.route('/admin/add_job_client', methods=['POST'])
def add_job_client():
    db.job_clients.insert_one({
        "name": request.form['name'],
        "phone": request.form['phone'],
        "qualification": request.form['qualification'],
        "skills": request.form['skills'],
        "experience": request.form['experience'],
        "status": "New"
    })
    return redirect('/admin/job_clients')
@app.route('/delete_all_jobs')
def delete_all_jobs():
    db.job_clients.delete_many({})
    return "All deleted"

# ✅ EXCEL UPLOAD FEATURE
@app.route('/admin/upload_job_clients', methods=['GET', 'POST'])
def upload_job_clients():
    if 'user' not in session:
        return redirect('/admin/login')

    if request.method == 'POST':
        file = request.files['file']

        if file:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip()

            for _, row in df.iterrows():
                db.job_clients.insert_one({
                    "name": str(row.get('Full Name', '')),
                    "phone": "91" + str(row.get('Mobile Number', '')),
                    "qualification": str(row.get('Qualification(s)', '')),
                    "skills": str(row.get('Are you a...?', '')),
                    "experience": str(row.get('Years of experience?', '')),
                    "status": "New"
                })

            return "✅ Data Uploaded Successfully"

    return render_template('admin/upload.html')

@app.route('/admin/delete_job_client/<id>')
def delete_job_client(id):
    db.job_clients.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/job_clients')


@app.route('/admin/update_job_status/<id>')
def update_job_status(id):
    job = db.job_clients.find_one({"_id": ObjectId(id)})
    cycle = ["New", "In Progress", "Placed", "Rejected"]

    next_status = cycle[(cycle.index(job.get("status", "New")) + 1) % len(cycle)]

    db.job_clients.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": next_status}}
    )

    return redirect('/admin/job_clients')


# ======================
# RUN
# ======================

if __name__ == '__main__':
    app.run(debug=True)